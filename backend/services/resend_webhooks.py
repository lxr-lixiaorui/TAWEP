import asyncio
from datetime import datetime, timezone

import resend
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import get_settings
from backend.models import EmailOutbox, EmailWebhookEvent, InboundEmail
from backend.services.authentication import now_utc


settings = get_settings()


def _parse_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def _route_for(addresses: list[str]) -> str:
    recipients = {address.strip().lower() for address in addresses}
    if settings.auth_support_email in recipients:
        return "auth"
    if settings.feedback_email in recipients:
        return "feedback"
    return "unrouted"


def _fetch_received_email(provider_email_id: str) -> dict:
    if not settings.resend_api_key:
        raise RuntimeError("RESEND_API_KEY is required to retrieve received email content")
    resend.api_key = settings.resend_api_key
    return dict(resend.Emails.Receiving.get(provider_email_id))


async def fetch_received_email(provider_email_id: str) -> dict:
    return await asyncio.to_thread(_fetch_received_email, provider_email_id)


def _event_error(data: dict) -> str | None:
    for key in ("bounce", "failed", "suppressed"):
        detail = data.get(key)
        if isinstance(detail, dict) and detail.get("message"):
            return str(detail["message"])
    if data.get("error"):
        return str(data["error"])
    return None


async def process_resend_event(
    db: AsyncSession,
    event_record: EmailWebhookEvent,
    event: dict,
    received_email: dict | None = None,
) -> None:
    event_type = str(event.get("type") or "")
    data = event.get("data") if isinstance(event.get("data"), dict) else {}
    provider_email_id = str(data.get("email_id") or "")

    if event_type == "email.received":
        full = received_email or {}
        to_addresses = list(full.get("to") or data.get("to") or [])
        inbound = await db.scalar(
            select(InboundEmail).where(InboundEmail.provider_email_id == provider_email_id).with_for_update()
        )
        if inbound is None:
            db.add(
                InboundEmail(
                    provider_email_id=provider_email_id,
                    sender_email=str(full.get("from") or data.get("from") or ""),
                    to_addresses=to_addresses,
                    cc_addresses=list(full.get("cc") or data.get("cc") or []),
                    bcc_addresses=list(full.get("bcc") or data.get("bcc") or []),
                    reply_to_addresses=list(full.get("reply_to") or []),
                    subject=str(full.get("subject") or data.get("subject") or "")[:500],
                    text_body=full.get("text"),
                    html_body=full.get("html"),
                    headers=dict(full.get("headers") or {}),
                    attachments=list(full.get("attachments") or data.get("attachments") or []),
                    route_key=_route_for(to_addresses),
                    received_at=_parse_datetime(full.get("created_at") or data.get("created_at")),
                )
            )
    elif provider_email_id:
        outbox = await db.scalar(
            select(EmailOutbox).where(EmailOutbox.provider_message_id == provider_email_id).with_for_update()
        )
        if outbox is not None:
            now = now_utc()
            outbox.provider_event = event_type[:40]
            if event_type == "email.delivered":
                outbox.status = "delivered"
                outbox.delivered_at = _parse_datetime(event.get("created_at"))
                outbox.error_message = None
            elif event_type in {"email.bounced", "email.complained", "email.failed", "email.suppressed"}:
                outbox.status = "failed"
                outbox.failed_at = _parse_datetime(event.get("created_at"))
                outbox.error_message = (_event_error(data) or event_type)[:4000]
            elif event_type == "email.delivery_delayed" and outbox.status not in {"delivered", "failed"}:
                outbox.status = "delayed"
                outbox.error_message = "Delivery has been delayed by the recipient mail server"
            elif event_type == "email.sent" and outbox.status not in {"delivered", "failed"}:
                outbox.status = "sent"
                outbox.sent_at = outbox.sent_at or now

    event_record.processed_at = now_utc()
    event_record.error_message = None
