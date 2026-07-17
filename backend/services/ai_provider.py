import asyncio
import base64
import hashlib
import ipaddress
import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit
from uuid import UUID

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import get_settings
from backend.models import UserAIConfig


class AIConfigError(ValueError):
    pass


@dataclass(frozen=True)
class ModelCredentials:
    source: str
    provider_name: str
    endpoint: str
    model_name: str
    audit_model_name: str
    api_key: str


def _fernet() -> Fernet:
    settings = get_settings()
    if settings.byok_encryption_key:
        raw = settings.byok_encryption_key.encode("ascii")
        try:
            Fernet(raw)
        except (ValueError, TypeError) as exc:
            raise RuntimeError("BYOK_ENCRYPTION_KEY must be a valid Fernet key") from exc
        return Fernet(raw)
    derived = hashlib.sha256(f"{settings.auth_secret_key}:tawep-byok-v1".encode()).digest()
    return Fernet(base64.urlsafe_b64encode(derived))


def encrypt_api_key(api_key: str) -> str:
    return _fernet().encrypt(api_key.encode()).decode("ascii")


def decrypt_api_key(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode("ascii")).decode()
    except InvalidToken as exc:
        raise RuntimeError("The personal API key cannot be decrypted") from exc


def normalize_endpoint(endpoint: str) -> str:
    candidate = endpoint.strip().rstrip("/")
    parsed = urlsplit(candidate)
    if parsed.scheme.lower() != "https":
        raise AIConfigError("Personal API endpoints must use HTTPS.")
    if not parsed.hostname or parsed.username or parsed.password:
        raise AIConfigError("The endpoint must contain a valid public hostname without credentials.")
    if parsed.query or parsed.fragment:
        raise AIConfigError("The endpoint cannot contain a query string or fragment.")
    try:
        port = parsed.port
    except ValueError as exc:
        raise AIConfigError("The endpoint port is invalid.") from exc
    if port not in {None, 443}:
        raise AIConfigError("Personal API endpoints may use HTTPS port 443 only.")
    hostname = parsed.hostname.casefold().rstrip(".")
    if hostname == "localhost" or hostname.endswith(".localhost") or "." not in hostname:
        raise AIConfigError("The endpoint must use a public DNS hostname.")
    netloc = hostname if port is None else f"{hostname}:{port}"
    return urlunsplit(("https", netloc, parsed.path.rstrip("/"), "", ""))


def _resolve_public_addresses(hostname: str) -> None:
    try:
        addresses = socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise AIConfigError("The endpoint hostname could not be resolved.") from exc
    if not addresses:
        raise AIConfigError("The endpoint hostname did not resolve to an address.")
    for item in addresses:
        address = ipaddress.ip_address(item[4][0])
        if not address.is_global:
            raise AIConfigError("The endpoint resolves to a private or reserved network address.")


async def validate_endpoint(endpoint: str) -> str:
    normalized = normalize_endpoint(endpoint)
    hostname = urlsplit(normalized).hostname
    if hostname is None:
        raise AIConfigError("The endpoint hostname is missing.")
    await asyncio.to_thread(_resolve_public_addresses, hostname)
    return normalized


async def get_user_ai_config(db: AsyncSession, user_id: UUID) -> UserAIConfig | None:
    return await db.scalar(select(UserAIConfig).where(UserAIConfig.user_id == user_id))


async def credentials_for_job(
    db: AsyncSession,
    user_id: UUID,
    api_source: str,
    ai_config_id: UUID | None,
) -> ModelCredentials:
    settings = get_settings()
    if api_source != "user":
        if not settings.deepseek_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        return ModelCredentials(
            source="platform",
            provider_name="deepseek",
            endpoint=settings.deepseek_base_url,
            model_name=settings.deepseek_model,
            audit_model_name=settings.deepseek_audit_model,
            api_key=settings.deepseek_api_key,
        )
    config = await db.scalar(
        select(UserAIConfig).where(
            UserAIConfig.id == ai_config_id,
            UserAIConfig.user_id == user_id,
            UserAIConfig.enabled.is_(True),
        )
    )
    if config is None:
        raise RuntimeError("The personal API configuration is no longer enabled")
    endpoint = await validate_endpoint(config.endpoint)
    return ModelCredentials(
        source="user",
        provider_name=config.provider_name,
        endpoint=endpoint,
        model_name=config.model_name,
        audit_model_name=config.model_name,
        api_key=decrypt_api_key(config.encrypted_api_key),
    )


def touch_config(config: UserAIConfig) -> None:
    config.updated_at = datetime.now(timezone.utc)
