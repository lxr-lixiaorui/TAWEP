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


@lru_cache
def get_settings() -> Settings:
    return Settings()
