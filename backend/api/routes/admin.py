from fastapi import APIRouter

from backend.schemas import APIMessage, AdminAccountAction, AdminMessageCreate


router = APIRouter()


@router.post("/login", response_model=APIMessage)
async def admin_login() -> APIMessage:
    return APIMessage(message="admin-login-ok")


@router.get("/questions")
async def manage_questions() -> list[dict]:
    return [{"question_no": 1, "status": "accepted", "source": "official"}]


@router.patch("/questions/{question_id}", response_model=APIMessage)
async def update_question(question_id: str) -> APIMessage:
    return APIMessage(message=f"question {question_id} updated")


@router.get("/review-questions")
async def review_questions() -> list[dict]:
    return [{"id": "demo-upload", "topic": "Education", "status": "pending"}]


@router.post("/review-questions/{question_id}/accept", response_model=APIMessage)
async def accept_question(question_id: str, payload: AdminAccountAction) -> APIMessage:
    return APIMessage(message=f"{question_id} accepted; inbox notice and credits queued")


@router.post("/review-questions/{question_id}/reject", response_model=APIMessage)
async def reject_question(question_id: str, payload: AdminAccountAction) -> APIMessage:
    return APIMessage(message=f"{question_id} rejected; inbox notice queued")


@router.get("/accounts")
async def accounts() -> list[dict]:
    return [{"id": "demo-user", "email": "demo@tawep.local", "status": "active", "credit": 180}]


@router.patch("/accounts/{user_id}/ban", response_model=APIMessage)
async def ban_account(user_id: str, payload: AdminAccountAction) -> APIMessage:
    return APIMessage(message=f"{user_id} banned")


@router.patch("/accounts/{user_id}/unban", response_model=APIMessage)
async def unban_account(user_id: str) -> APIMessage:
    return APIMessage(message=f"{user_id} unbanned")


@router.post("/accounts/{user_id}/messages", response_model=APIMessage)
async def send_account_message(user_id: str, payload: AdminMessageCreate) -> APIMessage:
    return APIMessage(message=f"message sent to {user_id}: {payload.title}")


@router.post("/accounts/{user_id}/credits", response_model=APIMessage)
async def adjust_account_credits(user_id: str) -> APIMessage:
    return APIMessage(message=f"credits adjusted for {user_id}")
