from uuid import UUID
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.core.config import get_settings
from backend.db.session import get_db
from backend.models import AccountToken, AuthSession, CreditLedger, EmailOutbox, InboxMessage, User, UserAIConfig, UserExamResult, UserRole
from backend.schemas import (
    AccountDeleteRequest,
    AIConfigOut,
    AIConfigUpdate,
    APIMessage,
    ConsentStatusOut,
    ConsentUpdate,
    CrossBorderConsentCreate,
    CreditLedgerOut,
    ExamOutcomeContext,
    ExamReminderAcknowledge,
    ExamReminderOut,
    ExamResultCreate,
    ExamResultOut,
    InboxMessageOut,
    PasswordChangeRequest,
    RequiredConsentsOut,
    RequiredCrossBorderConsentOut,
    UsageSummary,
    UserPublic,
    UserUpdate,
)
from backend.services.authentication import hash_password, normalize_email, now_utc, verify_password
from backend.services.email_delivery import queue_account_email
from backend.services.practice import get_usage
from backend.services.ai_provider import AIConfigError, encrypt_api_key, get_user_ai_config, touch_config, validate_endpoint
from backend.services.consents import add_consent_event, latest_consent
from backend.services.legal_documents import (
    MODEL_IMPROVEMENT_VERSION,
    THIRD_PARTY_AI_VERSION,
    require_version,
    get_document,
)
from backend.services.platform_settings import get_cross_border_config


router = APIRouter()
settings = get_settings()


def _hong_kong_today():
    return datetime.now(ZoneInfo("Asia/Hong_Kong")).date()


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.auth_refresh_cookie,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        domain=settings.auth_cookie_domain,
        path=f"{settings.api_prefix}/auth",
    )


@router.get("/me", response_model=UserPublic)
async def read_me(user: User = Depends(get_current_user)) -> User:
    return user


@router.patch("/me", response_model=UserPublic)
async def update_me(
    payload: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    async with db.begin():
        locked_user = await db.get(User, user.id, with_for_update=True)
        if locked_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        for key, value in payload.model_dump(exclude_none=True).items():
            setattr(locked_user, key, value)
        await db.flush()
        return locked_user


@router.put("/me/password", response_model=APIMessage)
async def change_password(
    payload: PasswordChangeRequest,
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIMessage:
    now = now_utc()
    async with db.begin():
        locked_user = await db.get(User, user.id, with_for_update=True)
        if locked_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        if not verify_password(payload.current_password, locked_user.password_hash):
            raise HTTPException(
                status_code=422,
                detail={"code": "INVALID_CURRENT_PASSWORD", "message": "The current password is incorrect."},
            )
        if verify_password(payload.new_password, locked_user.password_hash):
            raise HTTPException(
                status_code=422,
                detail={"code": "PASSWORD_REUSED", "message": "The new password must be different."},
            )
        locked_user.password_hash = hash_password(payload.new_password)
        locked_user.password_changed_at = now
        locked_user.token_version += 1
        await db.execute(
            update(AuthSession)
            .where(AuthSession.user_id == locked_user.id, AuthSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await db.execute(
            update(AccountToken)
            .where(
                AccountToken.user_id == locked_user.id,
                AccountToken.purpose == "reset_password",
                AccountToken.consumed_at.is_(None),
            )
            .values(consumed_at=now)
        )
        await queue_account_email(db, locked_user, "password_changed", locked_user.preferred_locale)
    _clear_refresh_cookie(response)
    return APIMessage(message="password-changed")


@router.delete("/me/account", response_model=APIMessage)
async def delete_own_account(
    payload: AccountDeleteRequest,
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIMessage:
    async with db.begin():
        locked_user = await db.get(User, user.id, with_for_update=True)
        if locked_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        if locked_user.role == UserRole.admin:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "ADMIN_SELF_DELETE_FORBIDDEN",
                    "message": "An administrator account must be removed by another administrator.",
                },
            )
        if not verify_password(payload.current_password, locked_user.password_hash):
            raise HTTPException(
                status_code=422,
                detail={"code": "INVALID_CURRENT_PASSWORD", "message": "The current password is incorrect."},
            )
        if normalize_email(str(payload.confirm_email)) != normalize_email(locked_user.email):
            raise HTTPException(
                status_code=422,
                detail={"code": "EMAIL_CONFIRMATION_MISMATCH", "message": "The confirmation email does not match."},
            )
        await db.execute(delete(EmailOutbox).where(EmailOutbox.user_id == locked_user.id))
        await db.delete(locked_user)
    _clear_refresh_cookie(response)
    return APIMessage(message="account-deleted")


@router.get("/me/usage", response_model=UsageSummary)
async def read_usage(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UsageSummary:
    return await get_usage(db, user.id)


@router.get("/me/consents", response_model=ConsentStatusOut)
async def read_consents(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConsentStatusOut:
    event = await latest_consent(db, user.id, "model_improvement")
    return ConsentStatusOut(
        model_improvement=bool(event and event.granted),
        version=MODEL_IMPROVEMENT_VERSION,
    )


@router.patch("/me/consents/model-improvement", response_model=ConsentStatusOut)
async def update_model_improvement_consent(
    payload: ConsentUpdate,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConsentStatusOut:
    try:
        require_version(payload.version, MODEL_IMPROVEMENT_VERSION, "model improvement notice")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail={"code": "LEGAL_VERSION_CHANGED", "message": str(exc)}) from exc
    async with db.begin():
        add_consent_event(db, user.id, "model_improvement", payload.version, payload.granted, request)
    return ConsentStatusOut(model_improvement=payload.granted, version=MODEL_IMPROVEMENT_VERSION)


@router.get("/me/required-consents", response_model=RequiredConsentsOut)
async def required_consents(
    locale: str = Query(default="en", pattern="^(en|zh)(?:-.+)?$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RequiredConsentsOut:
    config = await get_cross_border_config(db)
    if not config["visible"]:
        return RequiredConsentsOut(
            cross_border=RequiredCrossBorderConsentOut(visible=False, required=False)
        )
    event = await latest_consent(db, user.id, "cross_border")
    required = not (
        event
        and event.granted
        and event.document_version == config["consent_version"]
    )
    document = get_document("cross-border", locale)
    return RequiredConsentsOut(
        cross_border=RequiredCrossBorderConsentOut(
            visible=True,
            required=required,
            consent_version=config["consent_version"],
            title=document["title"] if document else None,
            summary=document["summary"] if document else None,
        )
    )


@router.post("/me/consents/cross-border", response_model=APIMessage)
async def accept_cross_border_consent(
    payload: CrossBorderConsentCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIMessage:
    async with db.begin():
        config = await get_cross_border_config(db, lock=True)
        if not config["visible"] or not config["consent_version"]:
            raise HTTPException(
                status_code=409,
                detail={"code": "CONSENT_NOT_ACTIVE", "message": "This consent is not currently active."},
            )
        try:
            require_version(payload.version, config["consent_version"], "cross-border notice")
        except ValueError as exc:
            raise HTTPException(status_code=409, detail={"code": "LEGAL_VERSION_CHANGED", "message": str(exc)}) from exc
        add_consent_event(db, user.id, "cross_border", payload.version, True, request)
    return APIMessage(message="cross-border-consent-recorded")


def _ai_config_out(config: UserAIConfig | None) -> AIConfigOut:
    if config is None:
        return AIConfigOut(
            enabled=False,
            provider_name="OpenAI-compatible",
            endpoint="https://api.deepseek.com",
            model_name="deepseek-reasoner",
            key_configured=False,
        )
    return AIConfigOut(
        enabled=config.enabled,
        provider_name=config.provider_name,
        endpoint=config.endpoint,
        model_name=config.model_name,
        key_configured=True,
        key_hint=f"...{config.key_last_four}",
        consent_version=config.consent_version,
    )


@router.get("/me/ai-config", response_model=AIConfigOut)
async def read_ai_config(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AIConfigOut:
    return _ai_config_out(await get_user_ai_config(db, user.id))


@router.put("/me/ai-config", response_model=AIConfigOut)
async def update_ai_config(
    payload: AIConfigUpdate,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AIConfigOut:
    try:
        require_version(payload.third_party_ai_version, THIRD_PARTY_AI_VERSION, "third-party AI notice")
        endpoint = await validate_endpoint(payload.endpoint)
    except (ValueError, AIConfigError) as exc:
        raise HTTPException(status_code=422, detail={"code": "INVALID_AI_CONFIG", "message": str(exc)}) from exc
    provider_name = payload.provider_name.strip()
    model_name = payload.model_name.strip()
    async with db.begin():
        config = await db.scalar(
            select(UserAIConfig).where(UserAIConfig.user_id == user.id).with_for_update()
        )
        if config is None:
            if not payload.api_key:
                raise HTTPException(status_code=422, detail={"code": "API_KEY_REQUIRED", "message": "An API key is required."})
            config = UserAIConfig(
                user_id=user.id,
                enabled=payload.enabled,
                provider_name=provider_name,
                endpoint=endpoint,
                model_name=model_name,
                encrypted_api_key=encrypt_api_key(payload.api_key),
                key_last_four=payload.api_key[-4:],
                consent_version=payload.third_party_ai_version,
            )
            db.add(config)
        else:
            config.enabled = payload.enabled
            config.provider_name = provider_name
            config.endpoint = endpoint
            config.model_name = model_name
            config.consent_version = payload.third_party_ai_version
            if payload.api_key:
                config.encrypted_api_key = encrypt_api_key(payload.api_key)
                config.key_last_four = payload.api_key[-4:]
            touch_config(config)
        await db.flush()
        add_consent_event(
            db,
            user.id,
            "third_party_ai",
            payload.third_party_ai_version,
            True,
            request,
            resource_type="ai_config",
            resource_id=config.id,
            details={"provider_name": provider_name, "endpoint": endpoint, "model_name": model_name},
        )
        return _ai_config_out(config)


@router.get("/me/credits/history", response_model=list[CreditLedgerOut])
async def credit_history(
    limit: int = Query(default=100, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CreditLedger]:
    return list(
        (
            await db.scalars(
                select(CreditLedger)
                .where(CreditLedger.user_id == user.id)
                .order_by(CreditLedger.created_at.desc())
                .limit(limit)
            )
        ).all()
    )


@router.get("/me/inbox", response_model=list[InboxMessageOut])
async def read_inbox(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[InboxMessage]:
    return list(
        (
            await db.scalars(
                select(InboxMessage)
                .where(InboxMessage.user_id == user.id)
                .order_by(InboxMessage.created_at.desc())
            )
        ).all()
    )


@router.get("/me/exam-reminder", response_model=ExamReminderOut)
async def read_exam_reminder(user: User = Depends(get_current_user)) -> ExamReminderOut:
    should_show = bool(
        user.planned_exam_date
        and user.planned_exam_date == _hong_kong_today()
        and user.exam_reminder_shown_at is None
    )
    return ExamReminderOut(show=should_show, exam_date=user.planned_exam_date)


@router.post("/me/exam-reminder/acknowledge", response_model=APIMessage)
async def acknowledge_exam_reminder(
    payload: ExamReminderAcknowledge,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIMessage:
    async with db.begin():
        locked_user = await db.get(User, user.id, with_for_update=True)
        if locked_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        if locked_user.planned_exam_date != _hong_kong_today():
            raise HTTPException(
                status_code=409,
                detail={"code": "EXAM_REMINDER_NOT_DUE", "message": "The exam reminder is not due today."},
            )
        if locked_user.exam_reminder_shown_at is None:
            locked_user.exam_reminder_shown_at = now_utc()
            existing = await db.scalar(
                select(InboxMessage).where(
                    InboxMessage.user_id == locked_user.id,
                    InboxMessage.type == "exam_day",
                )
            )
            if existing is None:
                if payload.locale == "zh":
                    title = "祝你考试顺利"
                    body = "祝你在今天的 TOEFL 考试中发挥出色，取得理想成绩。成绩公布后，欢迎点击下方链接登记写作成绩和提分情况，这将帮助我们进一步改进 TAWEP。"
                    action_label = "登记考试成绩"
                else:
                    title = "Good luck on your exam"
                    body = "We hope you perform at your best in today's TOEFL exam and achieve the score you are aiming for. When your scores are released, use the link below to report your Writing score and improvement. This helps us continue improving TAWEP."
                    action_label = "Report your score"
                db.add(
                    InboxMessage(
                        user_id=locked_user.id,
                        title=title,
                        body=body,
                        type="exam_day",
                        action_url="/score-report",
                        action_label=action_label,
                    )
                )
    return APIMessage(message="exam-reminder-acknowledged")


@router.get("/me/exam-outcome", response_model=ExamOutcomeContext)
async def read_exam_outcome(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExamOutcomeContext:
    latest_result = await db.scalar(
        select(UserExamResult)
        .where(UserExamResult.user_id == user.id)
        .order_by(UserExamResult.exam_date.desc(), UserExamResult.created_at.desc())
        .limit(1)
    )
    return ExamOutcomeContext(
        baseline_writing_score=user.baseline_writing_score,
        planned_exam_date=user.planned_exam_date,
        latest_result=ExamResultOut.model_validate(latest_result) if latest_result else None,
    )


@router.post("/me/exam-results", response_model=ExamResultOut)
async def save_exam_result(
    payload: ExamResultCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserExamResult:
    if payload.exam_date > _hong_kong_today():
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_EXAM_DATE", "message": "An exam result cannot be reported before the exam date."},
        )
    async with db.begin():
        locked_user = await db.get(User, user.id, with_for_update=True)
        if locked_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        baseline = locked_user.baseline_writing_score
        if baseline is None and payload.baseline_writing_score is not None:
            baseline = payload.baseline_writing_score
            locked_user.baseline_writing_score = baseline
        improvement = payload.writing_score - baseline if baseline is not None else None
        result = await db.scalar(
            select(UserExamResult)
            .where(UserExamResult.user_id == locked_user.id, UserExamResult.exam_date == payload.exam_date)
            .with_for_update()
        )
        if result is None:
            result = UserExamResult(
                user_id=locked_user.id,
                exam_date=payload.exam_date,
                writing_score=payload.writing_score,
                baseline_writing_score=baseline,
                improvement=improvement,
            )
            db.add(result)
        else:
            result.writing_score = payload.writing_score
            result.baseline_writing_score = baseline
            result.improvement = improvement
            result.updated_at = now_utc()
        await db.flush()
        return result


@router.patch("/me/inbox/{message_id}/read", response_model=APIMessage)
async def mark_message_read(
    message_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIMessage:
    async with db.begin():
        message = await db.scalar(
            select(InboxMessage)
            .where(InboxMessage.id == message_id, InboxMessage.user_id == user.id)
            .with_for_update()
        )
        if message is None:
            raise HTTPException(status_code=404, detail="Message not found")
        if message.read_at is None:
            message.read_at = now_utc()
    return APIMessage(message=f"{message_id} marked as read")
