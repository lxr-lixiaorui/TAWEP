import uvicorn

from backend.core.config import get_settings


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=1145,
        reload=settings.app_env == "development",
    )
