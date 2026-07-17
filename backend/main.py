import asyncio
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.api.router import api_router
from backend.core.config import get_settings
from backend.workers.email_delivery import run_email_worker


settings = get_settings()
settings.validate_security()


@asynccontextmanager
async def lifespan(_: FastAPI):
    email_worker = None
    if settings.email_delivery_mode == "resend":
        email_worker = asyncio.create_task(run_email_worker(), name="resend-email-worker")
    try:
        yield
    finally:
        if email_worker is not None:
            email_worker.cancel()
            with suppress(asyncio.CancelledError):
                await email_worker


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_prefix)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "tawep-api"}


frontend_dist = Path(__file__).resolve().parents[1] / "frontend" / "dist"
if frontend_dist.is_dir():
    assets_dir = frontend_dist / "assets"
    media_dir = frontend_dist / "media"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")
    if media_dir.is_dir():
        app.mount("/media", StaticFiles(directory=media_dir), name="frontend-media")

    @app.get("/", include_in_schema=False)
    async def frontend_index() -> FileResponse:
        return FileResponse(frontend_dist / "index.html")

    @app.get("/{path:path}", include_in_schema=False)
    async def frontend_route(path: str) -> FileResponse:
        if path.startswith(("api/", "static/")):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = (frontend_dist / path).resolve()
        if frontend_dist.resolve() in candidate.parents and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(frontend_dist / "index.html")
