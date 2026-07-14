from functools import lru_cache
from os import environ, getenv
from pathlib import Path
from urllib.parse import quote


def load_env_file(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def database_url_from_env() -> str:
    database_url = getenv("DATABASE_URL")
    if database_url:
        return database_url
    password = quote(getenv("DATABASE_PASSWORD", "tawep"))
    return f"postgresql+asyncpg://tawep:{password}@localhost:5432/tawep"


load_env_file()


class Settings:
    app_name = "TAWEP API"
    api_prefix = "/api/v1"
    cors_origins = [
        origin.strip()
        for origin in getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
        if origin.strip()
    ]
    database_url = database_url_from_env()
    deepseek_api_key = getenv("OPENAI_API_KEY")
    deepseek_base_url = getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    deepseek_model = getenv("DEEPSEEK_MODEL", "deepseek-reasoner")
    deepseek_max_tokens = int(getenv("DEEPSEEK_MAX_TOKENS", "16384"))
    deepseek_audit_model = getenv("DEEPSEEK_AUDIT_MODEL", "deepseek-chat")
    deepseek_audit_max_tokens = int(getenv("DEEPSEEK_AUDIT_MAX_TOKENS", "8192"))
    evaluation_provider = getenv("EVALUATION_PROVIDER", "deepseek")
    evaluation_worker_poll_seconds = float(getenv("EVALUATION_WORKER_POLL_SECONDS", "2"))
    evaluation_timeout_seconds = float(getenv("EVALUATION_TIMEOUT_SECONDS", "360"))
    evaluation_max_attempts = int(getenv("EVALUATION_MAX_ATTEMPTS", "3"))
    initial_credit = int(getenv("INITIAL_CREDIT", "180"))
    weekly_credit_limit = int(getenv("WEEKLY_CREDIT_LIMIT", "60"))
    evaluation_credit_cost = int(getenv("EVALUATION_CREDIT_COST", "3"))
    app_env = getenv("APP_ENV", "development").lower()
    public_app_url = getenv("PUBLIC_APP_URL", "http://127.0.0.1:5173").rstrip("/")
    auth_secret_key = getenv("AUTH_SECRET_KEY", "dev-only-secret-change-before-production-please")
    auth_algorithm = "HS256"
    auth_issuer = getenv("AUTH_ISSUER", "tawep-api")
    auth_audience = getenv("AUTH_AUDIENCE", "tawep-web")
    auth_access_token_minutes = int(getenv("AUTH_ACCESS_TOKEN_MINUTES", "15"))
    auth_refresh_token_days = int(getenv("AUTH_REFRESH_TOKEN_DAYS", "30"))
    auth_email_verify_hours = int(getenv("AUTH_EMAIL_VERIFY_HOURS", "24"))
    auth_password_reset_minutes = int(getenv("AUTH_PASSWORD_RESET_MINUTES", "60"))
    auth_refresh_cookie = getenv("AUTH_REFRESH_COOKIE", "tawep_refresh")
    auth_cookie_secure = getenv("AUTH_COOKIE_SECURE", "false").lower() == "true"
    auth_cookie_samesite = getenv("AUTH_COOKIE_SAMESITE", "lax").lower()
    auth_cookie_domain = getenv("AUTH_COOKIE_DOMAIN") or None
    email_delivery_mode = getenv("EMAIL_DELIVERY_MODE", "outbox").lower()
    mail_from_email = getenv("MAIL_FROM_EMAIL", "no-reply@localhost")
    mail_from_name = getenv("MAIL_FROM_NAME", "TAWEP")

    def validate_security(self) -> None:
        if len(self.auth_secret_key) < 32:
            raise RuntimeError("AUTH_SECRET_KEY must contain at least 32 characters")
        if self.app_env == "production" and self.auth_secret_key.startswith("dev-only"):
            raise RuntimeError("A production AUTH_SECRET_KEY must be configured")
        if self.auth_cookie_samesite not in {"lax", "strict", "none"}:
            raise RuntimeError("AUTH_COOKIE_SAMESITE must be lax, strict, or none")
        if self.auth_cookie_samesite == "none" and not self.auth_cookie_secure:
            raise RuntimeError("AUTH_COOKIE_SECURE must be true when AUTH_COOKIE_SAMESITE=none")
        if self.email_delivery_mode != "outbox":
            raise RuntimeError("Only EMAIL_DELIVERY_MODE=outbox is available until a mail provider is configured")


@lru_cache
def get_settings() -> Settings:
    return Settings()
