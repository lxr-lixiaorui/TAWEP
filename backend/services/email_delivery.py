from urllib.parse import quote

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import get_settings
from backend.models import EmailOutbox, User


SUBJECTS = {
    "verify_email": {
        "en": "Verify your TAWEP email",
        "zh": "验证你的 TAWEP 邮箱",
    },
    "reset_password": {
        "en": "Reset your TAWEP password",
        "zh": "重置你的 TAWEP 密码",
    },
    "password_changed": {
        "en": "Your TAWEP password was changed",
        "zh": "你的 TAWEP 密码已修改",
    },
}


def _action_url(template_key: str, token: str) -> str:
    settings = get_settings()
    route = "/verify-email" if template_key == "verify_email" else "/reset-password"
    return f"{settings.public_app_url}{route}?token={quote(token, safe='')}"


async def queue_account_email(
    db: AsyncSession,
    user: User,
    template_key: str,
    locale: str,
    token: str | None = None,
) -> EmailOutbox:
    selected_locale = locale if locale in {"en", "zh"} else "en"
    payload = {
        "alias": user.alias,
        "from_email": get_settings().mail_from_email,
        "from_name": get_settings().mail_from_name,
    }
    if token is not None:
        payload["action_url"] = _action_url(template_key, token)
    email = EmailOutbox(
        user_id=user.id,
        recipient_email=user.email,
        template_key=template_key,
        locale=selected_locale,
        subject=SUBJECTS[template_key][selected_locale],
        payload=payload,
        status="pending",
    )
    db.add(email)
    await db.flush()
    return email
