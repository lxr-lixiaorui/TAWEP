from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import get_settings
from backend.core.constants import DEMO_USER_EMAIL, DEMO_USER_ID
from backend.models import (
    AnswerSession,
    CreditWallet,
    EvaluationReport,
    GrammarAnalysisItem,
    Question,
    ScoreComponent,
    SessionMode,
    SessionStatus,
    User,
    UserRole,
    UserStatus,
)
from backend.schemas import GrammarItemOut, ReportOut, ScoreComponentsOut, SessionOut, UsageSummary
from backend.services.evaluation import score_to_30


class InsufficientCreditError(Exception):
    pass


class SessionClosedError(Exception):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _word_count(answer_text: str) -> int:
    return len(answer_text.split())


async def ensure_demo_account(db: AsyncSession) -> None:
    settings = get_settings()
    user_insert = insert(User).values(
        id=DEMO_USER_ID,
        email=DEMO_USER_EMAIL,
        password_hash="!demo-account-no-password",
        alias="Demo Writer",
        role=UserRole.user,
        status=UserStatus.active,
        preferred_locale="en",
        theme="light",
    )
    await db.execute(
        user_insert.on_conflict_do_update(
            index_elements=[User.id],
            set_={"email": DEMO_USER_EMAIL},
        )
    )
    await db.execute(
        insert(CreditWallet)
        .values(
            user_id=DEMO_USER_ID,
            balance=settings.initial_credit,
            weekly_limit=settings.weekly_credit_limit,
            weekly_used=0,
            weekly_window_start=_now(),
            total_planned_credit=settings.initial_credit,
        )
        .on_conflict_do_nothing(index_elements=[CreditWallet.user_id])
    )


def _reset_weekly_window(wallet: CreditWallet) -> None:
    if _now() >= wallet.weekly_window_start + timedelta(days=7):
        wallet.weekly_used = 0
        wallet.weekly_window_start = _now()


def _usage_out(wallet: CreditWallet) -> UsageSummary:
    return UsageSummary(
        balance=wallet.balance,
        weekly_limit=wallet.weekly_limit,
        weekly_used=wallet.weekly_used,
        total_planned_credit=wallet.total_planned_credit,
        next_reset_at=wallet.weekly_window_start + timedelta(days=7),
    )


async def get_usage(db: AsyncSession) -> UsageSummary:
    async with db.begin():
        await ensure_demo_account(db)
        wallet = await db.scalar(
            select(CreditWallet).where(CreditWallet.user_id == DEMO_USER_ID).with_for_update()
        )
        if wallet is None:
            raise RuntimeError("Demo credit wallet could not be created")
        _reset_weekly_window(wallet)
        return _usage_out(wallet)


def _session_out(session: AnswerSession, question_no: int) -> SessionOut:
    return SessionOut(
        id=session.id,
        question_no=question_no,
        mode=session.mode.value,
        status=session.status.value,
        time_limit_seconds=session.time_limit_seconds,
        answer_text=session.answer_text,
        started_at=session.started_at,
        submitted_at=session.submitted_at,
    )


def _session_statement(session_id: UUID):
    return (
        select(AnswerSession, Question.question_no)
        .join(Question, Question.id == AnswerSession.question_id)
        .where(AnswerSession.id == session_id, AnswerSession.user_id == DEMO_USER_ID)
    )


async def create_session(db: AsyncSession, question_no: int, mode: str) -> SessionOut | None:
    async with db.begin():
        await ensure_demo_account(db)
        question = await db.scalar(select(Question).where(Question.question_no == question_no))
        if question is None:
            return None
        session = AnswerSession(
            user_id=DEMO_USER_ID,
            question_id=question.id,
            mode=SessionMode(mode),
            status=SessionStatus.in_progress,
            time_limit_seconds=600 if mode == SessionMode.timed.value else None,
            answer_text="",
            word_count=0,
            started_at=_now(),
        )
        db.add(session)
        await db.flush()
        return _session_out(session, question.question_no)


async def get_session(db: AsyncSession, session_id: UUID) -> SessionOut | None:
    row = (await db.execute(_session_statement(session_id))).one_or_none()
    return _session_out(row[0], row[1]) if row is not None else None


async def update_answer(db: AsyncSession, session_id: UUID, answer_text: str) -> SessionOut | None:
    async with db.begin():
        row = (await db.execute(_session_statement(session_id).with_for_update())).one_or_none()
        if row is None:
            return None
        session, question_no = row
        if session.status in {SessionStatus.submitted, SessionStatus.evaluated}:
            raise SessionClosedError("A submitted session cannot be edited")
        session.answer_text = answer_text
        session.word_count = _word_count(answer_text)
        session.status = SessionStatus.in_progress
        await db.flush()
        return _session_out(session, question_no)


async def _report_out(db: AsyncSession, report: EvaluationReport) -> ReportOut:
    component = await db.scalar(select(ScoreComponent).where(ScoreComponent.report_id == report.id))
    if component is None:
        raise RuntimeError(f"Report {report.id} is missing score components")
    raw = report.raw_response or {}
    total_score = float(report.total_score)
    return ReportOut(
        session_id=report.session_id,
        total_score=total_score,
        total_score_30=int(raw.get("total_score_30", score_to_30(total_score))),
        components=ScoreComponentsOut(
            content_relevance=float(component.content_relevance),
            perspective_expansion=float(component.perspective_expansion),
            linguistic_expression=float(component.linguistic_expression),
            logical_structure=float(component.logical_structure),
        ),
        problems=raw.get("problems", {}),
        improvements=raw.get("improvements", {}),
        ai_rewrite=raw.get("ai_rewrite", ""),
        rewrite_comparison=report.rewrite_comparison or raw.get("rewrite_comparison", {}),
        report_html_url=f"/api/v1/sessions/{report.session_id}/download",
    )


async def get_report(db: AsyncSession, session_id: UUID) -> ReportOut | None:
    report = await db.scalar(
        select(EvaluationReport)
        .join(AnswerSession, AnswerSession.id == EvaluationReport.session_id)
        .where(EvaluationReport.session_id == session_id, AnswerSession.user_id == DEMO_USER_ID)
    )
    return await _report_out(db, report) if report is not None else None


async def get_grammar(db: AsyncSession, session_id: UUID) -> list[GrammarItemOut] | None:
    report_id = await db.scalar(
        select(EvaluationReport.id)
        .join(AnswerSession, AnswerSession.id == EvaluationReport.session_id)
        .where(EvaluationReport.session_id == session_id, AnswerSession.user_id == DEMO_USER_ID)
    )
    if report_id is None:
        return None
    items = (
        await db.scalars(
            select(GrammarAnalysisItem)
            .where(GrammarAnalysisItem.report_id == report_id)
            .order_by(GrammarAnalysisItem.sentence_index, GrammarAnalysisItem.id)
        )
    ).all()
    return [
        GrammarItemOut(
            sentence_index=item.sentence_index,
            occurrence_index=item.occurrence_index,
            start_offset=item.start_offset,
            end_offset=item.end_offset,
            original_text=item.original_text,
            issue_type=item.issue_type,
            explanation=item.explanation,
            suggestion=item.suggestion,
        )
        for item in items
    ]
