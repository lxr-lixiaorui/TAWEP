from html import escape
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


COPY = {
    "verify_email": {
        "en": {
            "preheader": "Verify your email to finish creating your TAWEP account.",
            "heading": "Verify your email",
            "intro": "One more step, {alias}. Confirm this address to activate your account and start practicing.",
            "button": "Verify email",
            "expiry": "This link expires in 24 hours and can only be used once.",
            "ignore": "If you did not create a TAWEP account, you can safely ignore this email.",
        },
        "zh": {
            "preheader": "验证邮箱以完成 TAWEP 账户注册。",
            "heading": "验证你的邮箱",
            "intro": "{alias}，只差最后一步。请确认此邮箱地址以激活账户并开始练习。",
            "button": "验证邮箱",
            "expiry": "此链接将在 24 小时后失效，且只能使用一次。",
            "ignore": "如果你没有注册 TAWEP 账户，可以忽略此邮件。",
        },
    },
    "reset_password": {
        "en": {
            "preheader": "Use this secure link to reset your TAWEP password.",
            "heading": "Reset your password",
            "intro": "We received a password reset request for your TAWEP account, {alias}.",
            "button": "Reset password",
            "expiry": "This link expires in 60 minutes and can only be used once.",
            "ignore": "If you did not request this change, ignore this email. Your password remains unchanged.",
        },
        "zh": {
            "preheader": "使用安全链接重置你的 TAWEP 密码。",
            "heading": "重置密码",
            "intro": "{alias}，我们收到了你的 TAWEP 账户密码重置请求。",
            "button": "重置密码",
            "expiry": "此链接将在 60 分钟后失效，且只能使用一次。",
            "ignore": "如果这不是你的操作，请忽略此邮件。你的密码不会发生变化。",
        },
    },
    "password_changed": {
        "en": {
            "preheader": "The password for your TAWEP account has been changed.",
            "heading": "Password changed",
            "intro": "The password for your TAWEP account was changed successfully, {alias}.",
            "button": "Review account settings",
            "expiry": "All previous sign-in sessions have been revoked.",
            "ignore": "If you did not make this change, contact us immediately and reset your password.",
        },
        "zh": {
            "preheader": "你的 TAWEP 账户密码已修改。",
            "heading": "密码已修改",
            "intro": "{alias}，你的 TAWEP 账户密码已成功修改。",
            "button": "检查账户设置",
            "expiry": "此前登录的所有会话均已撤销。",
            "ignore": "如果这不是你的操作，请立即联系我们并重新设置密码。",
        },
    },
}


def _action_url(template_key: str, token: str) -> str:
    settings = get_settings()
    route = "/verify-email" if template_key == "verify_email" else "/reset-password"
    return f"{settings.public_app_url}{route}?token={quote(token, safe='')}"


def _plain_text(template_key: str, locale: str, alias: str, action_url: str) -> str:
    copy = COPY[template_key][locale]
    support = get_settings().auth_support_email
    fallback = (
        f"\n\n{copy['button']}: {action_url}"
        if action_url
        else ""
    )
    support_line = (
        f"Need help? Email {support}."
        if locale == "en"
        else f"如需帮助，请发送邮件至 {support}。"
    )
    return (
        f"{copy['heading']}\n\n"
        f"{copy['intro'].format(alias=alias)}"
        f"{fallback}\n\n"
        f"{copy['expiry']}\n"
        f"{copy['ignore']}\n\n"
        f"{support_line}\n\n"
        "TOEFL Academic Discussion Evaluation Project\n"
        "tawep.org"
    )


def _html_email(template_key: str, locale: str, alias: str, action_url: str) -> str:
    copy = COPY[template_key][locale]
    safe_url = escape(action_url, quote=True)
    support = escape(get_settings().auth_support_email)
    support_intro = "Need help?" if locale == "en" else "如需帮助，"
    fallback_intro = (
        "If the button does not work, paste this address into your browser:"
        if locale == "en"
        else "如果按钮无法打开，请将以下地址复制到浏览器："
    )
    action = ""
    if action_url:
        action = f"""
          <tr><td style="padding:8px 40px 24px">
            <a href="{safe_url}" style="display:inline-block;background:#087f79;color:#ffffff;text-decoration:none;font-size:15px;font-weight:700;padding:13px 22px;border-radius:6px">{escape(copy['button'])}</a>
          </td></tr>
          <tr><td style="padding:0 40px 24px;color:#66727c;font-size:13px;line-height:1.6">
            {escape(fallback_intro)}<br>
            <a href="{safe_url}" style="color:#087f79;word-break:break-all">{safe_url}</a>
          </td></tr>
        """
    return f"""<!doctype html>
<html lang="{locale}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;background:#f2f6f5;font-family:Arial,'Microsoft YaHei',sans-serif;color:#17232d">
  <div style="display:none;max-height:0;overflow:hidden;opacity:0">{escape(copy['preheader'])}</div>
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f2f6f5;padding:32px 12px">
    <tr><td align="center">
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:600px;background:#ffffff;border:1px solid #d8e2e0;border-radius:8px;overflow:hidden">
        <tr><td style="padding:22px 40px;background:#087f79;color:#ffffff;font-size:22px;font-weight:800">TAWEP</td></tr>
        <tr><td style="padding:38px 40px 12px">
          <h1 style="margin:0;font-size:27px;line-height:1.25;letter-spacing:0">{escape(copy['heading'])}</h1>
        </td></tr>
        <tr><td style="padding:8px 40px 22px;color:#384751;font-size:16px;line-height:1.7">{escape(copy['intro'].format(alias=alias))}</td></tr>
        {action}
        <tr><td style="padding:20px 40px;background:#f8faf9;border-top:1px solid #e3eae8;color:#52616b;font-size:14px;line-height:1.65">
          <strong>{escape(copy['expiry'])}</strong><br>{escape(copy['ignore'])}
        </td></tr>
        <tr><td style="padding:24px 40px;color:#748088;font-size:12px;line-height:1.6">
          {escape(support_intro)} <a href="mailto:{support}" style="color:#087f79">{support}</a><br>
          TOEFL Academic Discussion Evaluation Project<br>tawep.org
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def render_outbox_email(email: EmailOutbox) -> dict[str, object]:
    if email.template_key not in COPY:
        raise ValueError(f"Unsupported email template: {email.template_key}")
    locale = email.locale if email.locale in {"en", "zh"} else "en"
    payload = email.payload or {}
    alias = str(payload.get("alias") or "TAWEP user")
    action_url = str(payload.get("action_url") or "")
    settings = get_settings()
    return {
        "from": f"{settings.mail_from_name} <{settings.mail_from_email}>",
        "to": [email.recipient_email],
        "reply_to": settings.mail_reply_to,
        "subject": email.subject,
        "html": _html_email(email.template_key, locale, alias, action_url),
        "text": _plain_text(email.template_key, locale, alias, action_url),
        "tags": [
            {"name": "category", "value": email.template_key},
            {"name": "locale", "value": locale},
        ],
    }


async def queue_account_email(
    db: AsyncSession,
    user: User,
    template_key: str,
    locale: str,
    token: str | None = None,
) -> EmailOutbox:
    if template_key not in SUBJECTS:
        raise ValueError(f"Unsupported email template: {template_key}")
    selected_locale = locale if locale in {"en", "zh"} else "en"
    payload = {"alias": user.alias}
    if token is not None:
        payload["action_url"] = _action_url(template_key, token)
    elif template_key == "password_changed":
        payload["action_url"] = f"{get_settings().public_app_url}/settings"
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
