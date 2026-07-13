from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.db.session import get_db
from backend.schemas import APIMessage, InboxMessageOut, UsageSummary, UserPublic, UserUpdate
from backend.services.practice import get_usage


router = APIRouter()


@router.get("/me", response_model=UserPublic)
async def read_me() -> UserPublic:
    return get_current_user()


@router.patch("/me", response_model=UserPublic)
async def update_me(payload: UserUpdate) -> UserPublic:
    user = get_current_user()
    return user.model_copy(update=payload.model_dump(exclude_none=True))


@router.get("/me/usage", response_model=UsageSummary)
async def read_usage(db: AsyncSession = Depends(get_db)) -> UsageSummary:
    return await get_usage(db)


@router.get("/me/inbox", response_model=list[InboxMessageOut])
async def read_inbox() -> list[InboxMessageOut]:
    return [
        InboxMessageOut(
            id=UUID("00000000-0000-4000-8000-000000000101"),
            title="Welcome to TAWEP",
            body="Your account includes 180 initial credits and a 60-credit weekly usage limit.",
            type="system",
            read_at=None,
            created_at=datetime.utcnow(),
        )
    ]


@router.patch("/me/inbox/{message_id}/read", response_model=APIMessage)
async def mark_message_read(message_id: UUID) -> APIMessage:
    return APIMessage(message=f"{message_id} marked as read")
