import asyncio
import logging
from datetime import timedelta

import resend
from sqlalchemy import and_, or_, select, update

from backend.core.config import get_settings
from backend.db.session import AsyncSessionLocal
from backend.models import EmailOutbox
from backend.services.authentication import now_utc
from backend.services.email_delivery import render_outbox_email


logger = logging.getLogger(__name__)
settings = get_settings()


async def _claim_next_email() -> EmailOutbox | None:
    now = now_utc()
    stale_claim = now - timedelta(minutes=10)
    async with AsyncSessionLocal() as db:
        async with db.begin():
            stale_conditions = or_(
                and_(
                    EmailOutbox.template_key == "verify_email",
                    EmailOutbox.created_at < now - timedelta(hours=settings.auth_email_verify_hours),
                ),
                and_(
                    EmailOutbox.template_key == "reset_password",
                    EmailOutbox.created_at < now - timedelta(minutes=settings.auth_password_reset_minutes),
                ),
                and_(
                    EmailOutbox.template_key == "password_changed",
                    EmailOutbox.created_at < now - timedelta(hours=24),
                ),
            )
            await db.execute(
                update(EmailOutbox)
                .where(EmailOutbox.status.in_(["pending", "retry"]), stale_conditions)
                .values(status="expired", error_message="Email action or notification window expired")
            )
            email = await db.scalar(
                select(EmailOutbox)
                .where(
                    EmailOutbox.attempts < settings.email_max_attempts,
                    or_(
                        and_(
                            EmailOutbox.status.in_(["pending", "retry"]),
                            or_(EmailOutbox.next_attempt_at.is_(None), EmailOutbox.next_attempt_at <= now),
                        ),
                        and_(EmailOutbox.status == "sending", EmailOutbox.claimed_at <= stale_claim),
                    ),
                )
                .order_by(EmailOutbox.created_at.asc())
                .with_for_update(skip_locked=True)
            )
            if email is None:
                return None
            email.status = "sending"
            email.attempts += 1
            email.claimed_at = now
            email.next_attempt_at = None
            email.error_message = None
            await db.flush()
            db.expunge(email)
            return email


def _send_with_resend(email: EmailOutbox) -> str:
    resend.api_key = settings.resend_api_key
    response = resend.Emails.send(
        render_outbox_email(email),
        {"idempotency_key": f"tawep-outbox-{email.id}"},
    )
    provider_id = response.get("id") if isinstance(response, dict) else getattr(response, "id", None)
    if not provider_id:
        raise RuntimeError("Resend returned no email id")
    return str(provider_id)


async def _mark_sent(email_id, provider_id: str) -> None:
    now = now_utc()
    async with AsyncSessionLocal() as db:
        async with db.begin():
            email = await db.get(EmailOutbox, email_id, with_for_update=True)
            if email is None:
                return
            email.status = "sent"
            email.provider_message_id = provider_id
            email.provider_event = "email.sent"
            email.sent_at = now
            email.claimed_at = None
            email.error_message = None


async def _mark_failed(email_id, message: str) -> None:
    now = now_utc()
    async with AsyncSessionLocal() as db:
        async with db.begin():
            email = await db.get(EmailOutbox, email_id, with_for_update=True)
            if email is None:
                return
            email.error_message = message[:4000]
            email.claimed_at = None
            if email.attempts >= settings.email_max_attempts:
                email.status = "failed"
                email.failed_at = now
                email.next_attempt_at = None
            else:
                email.status = "retry"
                email.next_attempt_at = now + timedelta(seconds=min(30 * (2 ** (email.attempts - 1)), 3600))


async def deliver_one() -> bool:
    email = await _claim_next_email()
    if email is None:
        return False
    try:
        provider_id = await asyncio.to_thread(_send_with_resend, email)
    except Exception as exc:
        logger.exception("Resend delivery failed for outbox email %s", email.id)
        await _mark_failed(email.id, str(exc))
    else:
        await _mark_sent(email.id, provider_id)
    return True


async def run_email_worker() -> None:
    if settings.email_delivery_mode != "resend":
        return
    logger.info("Resend email worker started")
    while True:
        try:
            handled = await deliver_one()
            if not handled:
                await asyncio.sleep(settings.email_worker_poll_seconds)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Email worker loop failed")
            await asyncio.sleep(settings.email_worker_poll_seconds)
