from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.db.session import get_db
from backend.models import InboxMessage, User
from backend.schemas import APIMessage, InboxMessageOut, UsageSummary, UserPublic, UserUpdate
from backend.services.authentication import now_utc
from backend.services.practice import get_usage


router = APIRouter()


@router.get("/me", response_model=UserPublic)
async def read_me(user: User = Depends(get_current_user)) -> User:
    return user


@router.patch("/me", response_model=UserPublic)
async def update_me(
    payload: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    async with db.begin():
        locked_user = await db.get(User, user.id, with_for_update=True)
        if locked_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        for key, value in payload.model_dump(exclude_none=True).items():
            setattr(locked_user, key, value)
        await db.flush()
        return locked_user


@router.get("/me/usage", response_model=UsageSummary)
async def read_usage(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UsageSummary:
    return await get_usage(db, user.id)


@router.get("/me/inbox", response_model=list[InboxMessageOut])
async def read_inbox(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[InboxMessage]:
    return list(
        (
            await db.scalars(
                select(InboxMessage)
                .where(InboxMessage.user_id == user.id)
                .order_by(InboxMessage.created_at.desc())
            )
        ).all()
    )


@router.patch("/me/inbox/{message_id}/read", response_model=APIMessage)
async def mark_message_read(
    message_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIMessage:
    async with db.begin():
        message = await db.scalar(
            select(InboxMessage)
            .where(InboxMessage.id == message_id, InboxMessage.user_id == user.id)
            .with_for_update()
        )
        if message is None:
            raise HTTPException(status_code=404, detail="Message not found")
        if message.read_at is None:
            message.read_at = now_utc()
    return APIMessage(message=f"{message_id} marked as read")
