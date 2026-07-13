from fastapi import APIRouter

from backend.api.routes import admin, auth, dashboard, evaluations, legal, questions, sessions, users


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, tags=["me"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(questions.router, prefix="/questions", tags=["questions"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(evaluations.router, prefix="/evaluations", tags=["evaluations"])
api_router.include_router(legal.router, prefix="/legal", tags=["legal"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
