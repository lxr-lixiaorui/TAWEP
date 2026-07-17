from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from svix.webhooks import Webhook, WebhookVerificationError

from backend.core.config import get_settings
from backend.db.session import get_db
from backend.models import EmailWebhookEvent
from backend.services.resend_webhooks import fetch_received_email, process_resend_event


router = APIRouter()
settings = get_settings()


@router.post("/resend", status_code=status.HTTP_200_OK)
async def resend_webhook(request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, bool]:
    if not settings.resend_webhook_secret:
        raise HTTPException(status_code=503, detail="Resend webhook secret is not configured")
    raw_body = await request.body()
    try:
        event = Webhook(settings.resend_webhook_secret).verify(raw_body, dict(request.headers))
    except WebhookVerificationError as exc:
        raise HTTPException(status_code=400, detail="Invalid Resend webhook signature") from exc

    svix_id = request.headers.get("svix-id")
    if not svix_id:
        raise HTTPException(status_code=400, detail="Missing svix-id header")
    event_type = str(event.get("type") or "")
    data = event.get("data") if isinstance(event.get("data"), dict) else {}
    provider_email_id = str(data.get("email_id") or "") or None

    async with db.begin():
        await db.execute(
            insert(EmailWebhookEvent)
            .values(
                svix_id=svix_id,
                event_type=event_type,
                provider_email_id=provider_email_id,
                payload=event,
            )
            .on_conflict_do_nothing(index_elements=[EmailWebhookEvent.svix_id])
        )
        event_record = await db.scalar(
            select(EmailWebhookEvent).where(EmailWebhookEvent.svix_id == svix_id).with_for_update()
        )
        if event_record is not None and event_record.processed_at is not None:
            return {"received": True}

    received_email = None
    try:
        if event_type == "email.received" and provider_email_id:
            received_email = await fetch_received_email(provider_email_id)
        async with db.begin():
            event_record = await db.scalar(
                select(EmailWebhookEvent).where(EmailWebhookEvent.svix_id == svix_id).with_for_update()
            )
            if event_record is None:
                raise RuntimeError("Webhook event record disappeared")
            if event_record.processed_at is None:
                await process_resend_event(db, event_record, event, received_email)
    except Exception as exc:
        async with db.begin():
            event_record = await db.scalar(
                select(EmailWebhookEvent).where(EmailWebhookEvent.svix_id == svix_id).with_for_update()
            )
            if event_record is not None:
                event_record.error_message = str(exc)[:4000]
        raise HTTPException(status_code=502, detail="Resend webhook processing failed") from exc
    return {"received": True}
