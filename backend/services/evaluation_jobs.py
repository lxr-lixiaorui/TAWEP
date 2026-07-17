from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import get_settings
from backend.models import (
    AnswerSession,
    CreditLedger,
    CreditWallet,
    EvaluationJob,
    EvaluationReport,
    SessionStatus,
    User,
    UserAIConfig,
)
from backend.schemas import EvaluationJobOut
from backend.services.evaluation_contract import normalize_locale
from backend.services.practice import InsufficientCreditError, ensure_user_wallet, evaluation_credit_cost_for_user


EVALUATION_LEDGER_REASON = "writing_evaluation"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _available_sections(partial: dict) -> list[str]:
    sections: list[str] = []
    if "problems" in partial:
        sections.append("problems")
    if "components" in partial:
        sections.extend(["scores", "total_score", "strongest_part"])
    if "improvements" in partial:
        sections.append("improvements")
    if "ai_rewrite" in partial:
        sections.append("ai_rewrite")
    if "rewrite_comparison" in partial:
        sections.append("rewrite_comparison")
    if "grammar_analysis" in partial:
        sections.append("grammar_analysis")
    return sections


def evaluation_job_out(job: EvaluationJob) -> EvaluationJobOut:
    started = job.started_at or job.created_at
    ended = job.completed_at or _now()
    elapsed = max(0, int((ended - started).total_seconds()))
    partial = job.partial_result or {}
    return EvaluationJobOut(
        id=job.id,
        session_id=job.session_id,
        status=job.status,
        stage=job.stage,
        report_locale=job.report_locale,
        available_sections=_available_sections(partial),
        partial_report=partial,
        elapsed_seconds=elapsed,
        estimated_min_seconds=job.estimated_min_seconds,
        estimated_max_seconds=job.estimated_max_seconds,
        attempt=job.attempt,
        max_attempts=job.max_attempts,
        error_code=job.error_code,
        error_message=job.error_message,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


async def enqueue_evaluation(
    db: AsyncSession,
    user_id: UUID,
    session_id: UUID,
    answer_text: str,
    report_locale: str,
) -> EvaluationJobOut | None:
    settings = get_settings()
    locale = normalize_locale(report_locale)
    async with db.begin():
        await ensure_user_wallet(db, user_id)
        session = await db.scalar(
            select(AnswerSession)
            .where(AnswerSession.id == session_id, AnswerSession.user_id == user_id)
            .with_for_update()
        )
        if session is None:
            return None

        existing_job = await db.scalar(
            select(EvaluationJob).where(EvaluationJob.session_id == session_id)
        )
        if existing_job is not None:
            return evaluation_job_out(existing_job)

        existing_report = await db.scalar(
            select(EvaluationReport).where(EvaluationReport.session_id == session_id)
        )
        if existing_report is not None:
            raw = existing_report.raw_response or {}
            job = EvaluationJob(
                session_id=session_id,
                status="completed",
                stage="completed",
                report_locale=raw.get("locale", locale),
                partial_result=raw.get("partial_report", {}),
                attempt=1,
                max_attempts=settings.evaluation_max_attempts,
                started_at=existing_report.created_at,
                completed_at=existing_report.created_at,
                heartbeat_at=existing_report.created_at,
                created_at=existing_report.created_at,
                updated_at=existing_report.created_at,
            )
            db.add(job)
            await db.flush()
            return evaluation_job_out(job)

        wallet = await db.scalar(
            select(CreditWallet).where(CreditWallet.user_id == user_id).with_for_update()
        )
        if wallet is None:
            raise RuntimeError("Credit wallet could not be created")
        user = await db.get(User, user_id)
        if user is None:
            raise RuntimeError("User could not be loaded")
        cost = evaluation_credit_cost_for_user(user)
        if wallet.balance < cost:
            raise InsufficientCreditError

        wallet.balance -= cost
        session.answer_text = answer_text
        session.word_count = len(answer_text.split())
        session.status = SessionStatus.submitted
        session.submitted_at = _now()
        db.add(
            CreditLedger(
                user_id=user_id,
                delta=-cost,
                reason=EVALUATION_LEDGER_REASON,
                session_id=session.id,
            )
        )
        personal_config = await db.scalar(
            select(UserAIConfig).where(
                UserAIConfig.user_id == user_id,
                UserAIConfig.enabled.is_(True),
            )
        )
        job = EvaluationJob(
            session_id=session.id,
            status="queued",
            stage="queued",
            report_locale=locale,
            api_source="user" if personal_config is not None else "platform",
            ai_config_id=personal_config.id if personal_config is not None else None,
            partial_result={},
            attempt=0,
            max_attempts=settings.evaluation_max_attempts,
            created_at=_now(),
            updated_at=_now(),
        )
        db.add(job)
        await db.flush()
        return evaluation_job_out(job)


async def get_evaluation_job(db: AsyncSession, user_id: UUID, job_id: UUID) -> EvaluationJobOut | None:
    job = await db.scalar(
        select(EvaluationJob)
        .join(AnswerSession, AnswerSession.id == EvaluationJob.session_id)
        .where(EvaluationJob.id == job_id, AnswerSession.user_id == user_id)
    )
    return evaluation_job_out(job) if job is not None else None


async def get_session_evaluation(db: AsyncSession, user_id: UUID, session_id: UUID) -> EvaluationJobOut | None:
    job = await db.scalar(
        select(EvaluationJob)
        .join(AnswerSession, AnswerSession.id == EvaluationJob.session_id)
        .where(EvaluationJob.session_id == session_id, AnswerSession.user_id == user_id)
    )
    return evaluation_job_out(job) if job is not None else None
