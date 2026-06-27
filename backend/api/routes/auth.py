from fastapi import APIRouter

from backend.api.deps import get_current_user
from backend.schemas import APIMessage, AuthResponse, LoginRequest, RegisterRequest


router = APIRouter()


@router.post("/captcha", response_model=APIMessage)
async def create_captcha() -> APIMessage:
    return APIMessage(message="captcha-issued")


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest) -> AuthResponse:
    user = get_current_user()
    return AuthResponse(access_token=f"demo-token-for-{payload.identifier}", user=user)


@router.post("/register", response_model=APIMessage)
async def register(payload: RegisterRequest) -> APIMessage:
    return APIMessage(message=f"Initial password email queued for {payload.email}")


@router.post("/logout", response_model=APIMessage)
async def logout() -> APIMessage:
    return APIMessage(message="logged-out")


@router.post("/refresh", response_model=AuthResponse)
async def refresh() -> AuthResponse:
    return AuthResponse(access_token="demo-token-refreshed", user=get_current_user())


@router.post("/password/forgot", response_model=APIMessage)
async def forgot_password(payload: RegisterRequest) -> APIMessage:
    return APIMessage(message=f"Password reset email queued for {payload.email}")


@router.post("/password/reset", response_model=APIMessage)
async def reset_password() -> APIMessage:
    return APIMessage(message="password-reset")
