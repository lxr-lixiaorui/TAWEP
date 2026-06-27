from functools import lru_cache
from os import getenv


class Settings:
    app_name = "TAWEP API"
    api_prefix = "/api/v1"
    cors_origins = [
        origin.strip()
        for origin in getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
        if origin.strip()
    ]
    database_url = getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://tawep:tawep@localhost:2345/tawep",
    )
    deepseek_api_key = getenv("OPENAI_API_KEY")
    deepseek_base_url = getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    deepseek_model = getenv("DEEPSEEK_MODEL", "deepseek-reasoner")
    initial_credit = int(getenv("INITIAL_CREDIT", "180"))
    weekly_credit_limit = int(getenv("WEEKLY_CREDIT_LIMIT", "60"))
    evaluation_credit_cost = int(getenv("EVALUATION_CREDIT_COST", "3"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
