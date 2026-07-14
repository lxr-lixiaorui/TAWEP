from datetime import datetime, timedelta, timezone
from hashlib import sha256
import secrets
from uuid import UUID, uuid4

import jwt
from jwt import InvalidTokenError
from pwdlib import PasswordHash

from backend.core.config import get_settings
from backend.models import User


password_hash = PasswordHash.recommended()
DUMMY_PASSWORD_HASH = password_hash.hash("not-a-real-user-password")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        return password_hash.verify(password, encoded_hash)
    except Exception:
        return False


def verify_dummy_password(password: str) -> None:
    verify_password(password, DUMMY_PASSWORD_HASH)


def create_opaque_token() -> str:
    return secrets.token_urlsafe(48)


def digest_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def create_access_token(user: User, session_id: UUID) -> tuple[str, int]:
    settings = get_settings()
    issued_at = now_utc()
    lifetime = timedelta(minutes=settings.auth_access_token_minutes)
    payload = {
        "sub": str(user.id),
        "sid": str(session_id),
        "ver": user.token_version,
        "type": "access",
        "jti": str(uuid4()),
        "iat": issued_at,
        "nbf": issued_at,
        "exp": issued_at + lifetime,
        "iss": settings.auth_issuer,
        "aud": settings.auth_audience,
    }
    token = jwt.encode(payload, settings.auth_secret_key, algorithm=settings.auth_algorithm)
    return token, int(lifetime.total_seconds())


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.auth_secret_key,
            algorithms=[settings.auth_algorithm],
            audience=settings.auth_audience,
            issuer=settings.auth_issuer,
            options={"require": ["sub", "sid", "ver", "type", "exp", "iat"]},
        )
    except InvalidTokenError as exc:
        raise ValueError("Invalid access token") from exc
    if payload.get("type") != "access":
        raise ValueError("Invalid token type")
    return payload
