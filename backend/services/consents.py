from uuid import UUID

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import UserConsentEvent


def request_metadata(request: Request) -> tuple[str | None, str | None]:
    ip_address = request.client.host if request.client else None
    user_agent = (request.headers.get("user-agent") or "")[:500] or None
    return ip_address, user_agent


def add_consent_event(
    db: AsyncSession,
    user_id: UUID,
    consent_key: str,
    document_version: str,
    granted: bool,
    request: Request,
    *,
    resource_type: str | None = None,
    resource_id: UUID | None = None,
    details: dict | None = None,
) -> UserConsentEvent:
    ip_address, user_agent = request_metadata(request)
    event = UserConsentEvent(
        user_id=user_id,
        consent_key=consent_key,
        document_version=document_version,
        granted=granted,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details or {},
    )
    db.add(event)
    return event


async def latest_consent(db: AsyncSession, user_id: UUID, consent_key: str) -> UserConsentEvent | None:
    return await db.scalar(
        select(UserConsentEvent)
        .where(UserConsentEvent.user_id == user_id, UserConsentEvent.consent_key == consent_key)
        .order_by(UserConsentEvent.created_at.desc(), UserConsentEvent.id.desc())
        .limit(1)
    )
