from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import get_settings
from backend.db.session import get_db
from backend.models import AccountToken, AuthSession, CreditWallet, InboxMessage, User, UserStatus
from backend.schemas import (
    APIMessage,
    AuthResponse,
    EmailRequest,
    LoginRequest,
    PasswordResetRequest,
    RegisterRequest,
    UserPublic,
    VerifyEmailRequest,
)
from backend.services.authentication import (
    create_access_token,
    create_opaque_token,
    digest_token,
    hash_password,
    normalize_email,
    now_utc,
    verify_dummy_password,
    verify_password,
)
from backend.services.email_delivery import queue_account_email


router = APIRouter()
settings = get_settings()


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.auth_refresh_cookie,
        value=token,
        max_age=settings.auth_refresh_token_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        domain=settings.auth_cookie_domain,
        path=f"{settings.api_prefix}/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.auth_refresh_cookie,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        domain=settings.auth_cookie_domain,
        path=f"{settings.api_prefix}/auth",
    )


async def _create_auth_session(db: AsyncSession, user: User, request: Request) -> tuple[AuthSession, str]:
    refresh_token = create_opaque_token()
    auth_session = AuthSession(
        user_id=user.id,
        refresh_token_hash=digest_token(refresh_token),
        user_agent=(request.headers.get("user-agent") or "")[:500] or None,
        ip_address=_client_ip(request),
        expires_at=now_utc() + timedelta(days=settings.auth_refresh_token_days),
    )
    db.add(auth_session)
    await db.flush()
    return auth_session, refresh_token


async def _issue_account_token(
    db: AsyncSession,
    user: User,
    purpose: str,
    lifetime: timedelta,
    locale: str,
) -> None:
    now = now_utc()
    recent = await db.scalar(
        select(AccountToken)
        .where(
            AccountToken.user_id == user.id,
            AccountToken.purpose == purpose,
            AccountToken.consumed_at.is_(None),
        )
        .order_by(AccountToken.created_at.desc())
    )
    if recent is not None and recent.created_at >= now - timedelta(seconds=60):
        return
    await db.execute(
        update(AccountToken)
        .where(
            AccountToken.user_id == user.id,
            AccountToken.purpose == purpose,
            AccountToken.consumed_at.is_(None),
        )
        .values(consumed_at=now)
    )
    raw_token = create_opaque_token()
    db.add(
        AccountToken(
            user_id=user.id,
            purpose=purpose,
            token_hash=digest_token(raw_token),
            expires_at=now + lifetime,
        )
    )
    await queue_account_email(db, user, purpose, locale, raw_token)


def _auth_response(user: User, auth_session: AuthSession) -> AuthResponse:
    access_token, expires_in = create_access_token(user, auth_session.id)
    return AuthResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=UserPublic.model_validate(user),
    )


@router.post("/register", response_model=APIMessage, status_code=status.HTTP_202_ACCEPTED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> APIMessage:
    email = normalize_email(str(payload.email))
    encoded_password = hash_password(payload.password)
    async with db.begin():
        user = await db.scalar(select(User).where(User.email == email).with_for_update())
        if user is None:
            user = User(
                email=email,
                password_hash=encoded_password,
                alias=payload.alias.strip(),
                status=UserStatus.pending,
                preferred_locale=payload.preferred_locale,
                theme="light",
            )
            db.add(user)
            await db.flush()
            db.add(
                CreditWallet(
                    user_id=user.id,
                    balance=settings.initial_credit,
                    weekly_limit=settings.weekly_credit_limit,
                    weekly_used=0,
                    weekly_window_start=now_utc(),
                    total_planned_credit=settings.initial_credit,
                )
            )
        elif user.status == UserStatus.pending:
            user.password_hash = encoded_password
            user.alias = payload.alias.strip()
            user.preferred_locale = payload.preferred_locale
        else:
            return APIMessage(message="If the address can be registered, a verification email has been queued.")

        await _issue_account_token(
            db,
            user,
            "verify_email",
            timedelta(hours=settings.auth_email_verify_hours),
            payload.preferred_locale,
        )
    return APIMessage(message="If the address can be registered, a verification email has been queued.")


@router.post("/email/resend", response_model=APIMessage, status_code=status.HTTP_202_ACCEPTED)
async def resend_verification(payload: EmailRequest, db: AsyncSession = Depends(get_db)) -> APIMessage:
    async with db.begin():
        user = await db.scalar(select(User).where(User.email == normalize_email(str(payload.email))))
        if user is not None and user.status == UserStatus.pending:
            await _issue_account_token(
                db,
                user,
                "verify_email",
                timedelta(hours=settings.auth_email_verify_hours),
                payload.preferred_locale,
            )
    return APIMessage(message="If the account is awaiting verification, a new email has been queued.")


@router.post("/email/verify", response_model=AuthResponse)
async def verify_email(
    payload: VerifyEmailRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    now = now_utc()
    async with db.begin():
        account_token = await db.scalar(
            select(AccountToken)
            .where(
                AccountToken.token_hash == digest_token(payload.token),
                AccountToken.purpose == "verify_email",
            )
            .with_for_update()
        )
        if account_token is None or account_token.consumed_at is not None or account_token.expires_at <= now:
            raise HTTPException(status_code=400, detail={"code": "INVALID_TOKEN", "message": "Verification link is invalid or expired."})
        user = await db.get(User, account_token.user_id, with_for_update=True)
        if user is None or user.status == UserStatus.banned:
            raise HTTPException(status_code=400, detail={"code": "INVALID_TOKEN", "message": "Verification link is invalid or expired."})
        account_token.consumed_at = now
        user.email_verified_at = user.email_verified_at or now
        user.status = UserStatus.active
        user.last_login_at = now
        db.add(
            InboxMessage(
                user_id=user.id,
                title="Welcome to TAWEP",
                body=f"Your account includes {settings.initial_credit} initial credits.",
                type="system",
            )
        )
        auth_session, refresh_token = await _create_auth_session(db, user, request)
        result = _auth_response(user, auth_session)
    _set_refresh_cookie(response, refresh_token)
    return result


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    identifier = payload.identifier.strip()
    async with db.begin():
        user: User | None = None
        try:
            user_id = UUID(identifier)
        except ValueError:
            user_id = None
        if user_id is not None:
            user = await db.get(User, user_id)
        elif "@" in identifier:
            user = await db.scalar(select(User).where(User.email == normalize_email(identifier)))

        if user is None:
            verify_dummy_password(payload.password)
            raise HTTPException(status_code=401, detail={"code": "INVALID_CREDENTIALS", "message": "Email or password is incorrect."})
        if not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail={"code": "INVALID_CREDENTIALS", "message": "Email or password is incorrect."})
        if user.status == UserStatus.pending:
            raise HTTPException(status_code=403, detail={"code": "EMAIL_NOT_VERIFIED", "message": "Verify your email before signing in."})
        if user.status != UserStatus.active:
            raise HTTPException(status_code=403, detail={"code": "ACCOUNT_DISABLED", "message": "This account is not available."})
        user.last_login_at = now_utc()
        auth_session, refresh_token = await _create_auth_session(db, user, request)
        result = _auth_response(user, auth_session)
    _set_refresh_cookie(response, refresh_token)
    return result


@router.post("/refresh", response_model=AuthResponse)
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=settings.auth_refresh_cookie),
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token is missing")
    now = now_utc()
    async with db.begin():
        auth_session = await db.scalar(
            select(AuthSession)
            .where(AuthSession.refresh_token_hash == digest_token(refresh_token))
            .with_for_update()
        )
        if auth_session is None or auth_session.revoked_at is not None or auth_session.expires_at <= now:
            _clear_refresh_cookie(response)
            raise HTTPException(status_code=401, detail="Refresh token is invalid or expired")
        user = await db.get(User, auth_session.user_id)
        if user is None or user.status != UserStatus.active:
            auth_session.revoked_at = now
            _clear_refresh_cookie(response)
            raise HTTPException(status_code=401, detail="Account is not active")
        rotated_token = create_opaque_token()
        auth_session.refresh_token_hash = digest_token(rotated_token)
        auth_session.last_used_at = now
        auth_session.expires_at = now + timedelta(days=settings.auth_refresh_token_days)
        result = _auth_response(user, auth_session)
    _set_refresh_cookie(response, rotated_token)
    return result


@router.post("/logout", response_model=APIMessage)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=settings.auth_refresh_cookie),
    db: AsyncSession = Depends(get_db),
) -> APIMessage:
    if refresh_token:
        async with db.begin():
            auth_session = await db.scalar(
                select(AuthSession).where(AuthSession.refresh_token_hash == digest_token(refresh_token)).with_for_update()
            )
            if auth_session is not None and auth_session.revoked_at is None:
                auth_session.revoked_at = now_utc()
    _clear_refresh_cookie(response)
    return APIMessage(message="logged-out")


@router.post("/password/forgot", response_model=APIMessage, status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(payload: EmailRequest, db: AsyncSession = Depends(get_db)) -> APIMessage:
    async with db.begin():
        user = await db.scalar(select(User).where(User.email == normalize_email(str(payload.email))))
        if user is not None and user.status == UserStatus.active:
            await _issue_account_token(
                db,
                user,
                "reset_password",
                timedelta(minutes=settings.auth_password_reset_minutes),
                payload.preferred_locale,
            )
    return APIMessage(message="If the account exists, a password reset email has been queued.")


@router.post("/password/reset", response_model=APIMessage)
async def reset_password(payload: PasswordResetRequest, db: AsyncSession = Depends(get_db)) -> APIMessage:
    encoded_password = hash_password(payload.password)
    now = now_utc()
    async with db.begin():
        account_token = await db.scalar(
            select(AccountToken)
            .where(
                AccountToken.token_hash == digest_token(payload.token),
                AccountToken.purpose == "reset_password",
            )
            .with_for_update()
        )
        if account_token is None or account_token.consumed_at is not None or account_token.expires_at <= now:
            raise HTTPException(status_code=400, detail={"code": "INVALID_TOKEN", "message": "Reset link is invalid or expired."})
        user = await db.get(User, account_token.user_id, with_for_update=True)
        if user is None or user.status != UserStatus.active:
            raise HTTPException(status_code=400, detail={"code": "INVALID_TOKEN", "message": "Reset link is invalid or expired."})
        user.password_hash = encoded_password
        user.password_changed_at = now
        user.token_version += 1
        account_token.consumed_at = now
        await db.execute(
            update(AuthSession)
            .where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await db.execute(
            update(AccountToken)
            .where(
                AccountToken.user_id == user.id,
                AccountToken.purpose == "reset_password",
                AccountToken.consumed_at.is_(None),
            )
            .values(consumed_at=now)
        )
        await queue_account_email(db, user, "password_changed", user.preferred_locale)
    return APIMessage(message="password-reset")
