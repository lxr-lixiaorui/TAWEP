import hashlib
import re
import secrets
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import (
    AnswerSession,
    EvaluationReport,
    GrammarAnalysisItem,
    Question,
    ReportShare,
    User,
)
from backend.schemas import (
    GrammarItemOut,
    PublicReportOut,
    ReportShareOut,
    SessionOut,
)
from backend.services.practice import build_report_out
from backend.services.questions import get_database_question_by_no


TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{40,128}$")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def create_report_share(
    db: AsyncSession,
    user_id: UUID,
    session_id: UUID,
) -> ReportShareOut | None:
    async with db.begin():
        report = await db.scalar(
            select(EvaluationReport)
            .join(AnswerSession, AnswerSession.id == EvaluationReport.session_id)
            .where(EvaluationReport.session_id == session_id, AnswerSession.user_id == user_id)
        )
        if report is None:
            return None

        created_at = _now()
        await db.execute(
            update(ReportShare)
            .where(
                ReportShare.report_id == report.id,
                ReportShare.user_id == user_id,
                ReportShare.revoked_at.is_(None),
            )
            .values(revoked_at=created_at)
        )
        token = secrets.token_urlsafe(32)
        db.add(
            ReportShare(
                report_id=report.id,
                user_id=user_id,
                token_hash=_token_hash(token),
                created_at=created_at,
            )
        )
        return ReportShareOut(
            token=token,
            path=f"/share/{token}/report",
            created_at=created_at,
        )


async def get_public_report(db: AsyncSession, token: str) -> PublicReportOut | None:
    if not TOKEN_PATTERN.fullmatch(token):
        return None

    row = (
        await db.execute(
            select(ReportShare, EvaluationReport, AnswerSession, User.alias, Question.question_no)
            .join(EvaluationReport, EvaluationReport.id == ReportShare.report_id)
            .join(AnswerSession, AnswerSession.id == EvaluationReport.session_id)
            .join(User, User.id == ReportShare.user_id)
            .join(Question, Question.id == AnswerSession.question_id)
            .where(
                ReportShare.token_hash == _token_hash(token),
                ReportShare.revoked_at.is_(None),
                AnswerSession.user_id == ReportShare.user_id,
            )
        )
    ).one_or_none()
    if row is None:
        return None

    _, report, answer_session, owner_alias, question_no = row
    question = await get_database_question_by_no(db, question_no)
    if question is None:
        return None

    grammar_items = (
        await db.scalars(
            select(GrammarAnalysisItem)
            .where(GrammarAnalysisItem.report_id == report.id)
            .order_by(GrammarAnalysisItem.sentence_index, GrammarAnalysisItem.id)
        )
    ).all()
    report_out = await build_report_out(db, report)
    report_out.report_html_url = None

    return PublicReportOut(
        session=SessionOut(
            id=answer_session.id,
            question_no=question_no,
            mode=answer_session.mode.value,
            status=answer_session.status.value,
            time_limit_seconds=answer_session.time_limit_seconds,
            answer_text=answer_session.answer_text,
            started_at=answer_session.started_at,
            submitted_at=answer_session.submitted_at,
        ),
        question=question,
        report=report_out,
        grammar=[
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
            for item in grammar_items
        ],
        owner_alias=owner_alias,
        generated_at=report.created_at,
    )
