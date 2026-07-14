from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import AsyncSessionLocal
from backend.models import AuthSession, User, UserRole, UserStatus
from backend.services.authentication import decode_access_token, now_utc


bearer_scheme = HTTPBearer(auto_error=False)


async def get_auth_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


def _unauthorized(detail: str = "Authentication required") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_auth_db),
) -> User | None:
    if credentials is None:
        return None
    try:
        claims = decode_access_token(credentials.credentials)
        user_id = UUID(claims["sub"])
        session_id = UUID(claims["sid"])
    except (ValueError, TypeError, KeyError):
        raise _unauthorized("Invalid or expired access token")

    row = (
        await db.execute(
            select(User, AuthSession)
            .join(AuthSession, AuthSession.user_id == User.id)
            .where(User.id == user_id, AuthSession.id == session_id)
        )
    ).one_or_none()
    if row is None:
        raise _unauthorized("Session is no longer valid")
    user, auth_session = row
    if auth_session.revoked_at is not None or auth_session.expires_at <= now_utc():
        raise _unauthorized("Session is no longer valid")
    if user.status != UserStatus.active or user.token_version != int(claims["ver"]):
        raise _unauthorized("Account is not active")
    return user


async def get_current_user(user: User | None = Depends(get_optional_user)) -> User:
    if user is None:
        raise _unauthorized()
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access required")
    return user
