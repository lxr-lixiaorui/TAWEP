from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import AnswerSession, EvaluationReport, ReportFeedback
from backend.schemas import ReportFeedbackCreate, ReportFeedbackStatusOut
from backend.services.practice import build_report_out


class FeedbackAlreadySubmittedError(Exception):
    pass


class FeedbackValidationError(Exception):
    pass


async def submit_report_feedback(
    db: AsyncSession,
    user_id: UUID,
    session_id: UUID,
    payload: ReportFeedbackCreate,
) -> ReportFeedback | None:
    comment = payload.comment.strip() if payload.comment else None
    if payload.feedback_type == "other" and not comment:
        raise FeedbackValidationError("Please describe the issue when choosing Other")
    async with db.begin():
        row = (
            await db.execute(
                select(AnswerSession, EvaluationReport)
                .join(EvaluationReport, EvaluationReport.session_id == AnswerSession.id)
                .where(AnswerSession.id == session_id, AnswerSession.user_id == user_id)
            )
        ).one_or_none()
        if row is None:
            return None
        answer_session, report = row
        existing = await db.scalar(
            select(ReportFeedback.id).where(ReportFeedback.report_id == report.id)
        )
        if existing is not None:
            raise FeedbackAlreadySubmittedError
        report_out = await build_report_out(db, report)
        feedback = ReportFeedback(
            report_id=report.id,
            user_id=user_id,
            feedback_type=payload.feedback_type,
            comment=comment,
            consent_to_share=True,
            answer_snapshot=answer_session.answer_text,
            report_snapshot=report_out.model_dump(mode="json"),
        )
        db.add(feedback)
        await db.flush()
        return feedback


async def get_report_feedback_status(
    db: AsyncSession,
    user_id: UUID,
    session_id: UUID,
) -> ReportFeedbackStatusOut | None:
    report_id = await db.scalar(
        select(EvaluationReport.id)
        .join(AnswerSession, AnswerSession.id == EvaluationReport.session_id)
        .where(AnswerSession.id == session_id, AnswerSession.user_id == user_id)
    )
    if report_id is None:
        return None
    feedback = await db.scalar(select(ReportFeedback).where(ReportFeedback.report_id == report_id))
    if feedback is None:
        return ReportFeedbackStatusOut(submitted=False)
    return ReportFeedbackStatusOut(
        submitted=True,
        feedback_type=feedback.feedback_type,
        created_at=feedback.created_at,
    )
