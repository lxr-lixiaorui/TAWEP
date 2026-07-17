from html import escape
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_optional_user
from backend.db.session import get_db
from backend.models import User
from backend.schemas import (
    AnswerUpdate,
    EvaluationJobOut,
    GrammarItemOut,
    ReportFeedbackCreate,
    ReportFeedbackStatusOut,
    ReportOut,
    SessionCreate,
    SessionOut,
    SubmitAnswer,
)
from backend.services.evaluation_jobs import enqueue_evaluation
from backend.services.example_data import (
    EXAMPLE_SESSION_ID,
    build_example_evaluation_job,
    build_example_grammar,
    build_example_report,
)
from backend.services.practice import (
    InsufficientCreditError,
    SessionClosedError,
    create_session as create_database_session,
    get_grammar,
    get_report,
    get_session,
    update_answer as update_database_answer,
)
from backend.services.report_feedback import (
    FeedbackAlreadySubmittedError,
    FeedbackValidationError,
    get_report_feedback_status,
    submit_report_feedback,
)
from backend.services.session_store import build_example_session


router = APIRouter()


@router.post("/from-question/{question_no}", response_model=SessionOut, status_code=201)
async def create_session(
    question_no: int,
    payload: SessionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionOut:
    try:
        session = await create_database_session(db, user.id, question_no, payload.mode)
    except InsufficientCreditError as exc:
        raise HTTPException(
            status_code=402,
            detail={"code": "INSUFFICIENT_CREDIT", "message": "Credit is not enough to start a scored session."},
        ) from exc
    if session is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return session


@router.get("/{session_id}", response_model=SessionOut)
async def read_session(
    session_id: UUID,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> SessionOut:
    if session_id == EXAMPLE_SESSION_ID:
        return build_example_session()
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    session = await get_session(db, user.id, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.patch("/{session_id}/answer", response_model=SessionOut)
async def update_answer(
    session_id: UUID,
    payload: AnswerUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionOut:
    if session_id == EXAMPLE_SESSION_ID:
        return build_example_session()
    try:
        updated = await update_database_answer(db, user.id, session_id, payload.answer_text)
    except SessionClosedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if updated is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return updated


@router.post("/{session_id}/submit", response_model=EvaluationJobOut, status_code=202)
async def submit_answer(
    session_id: UUID,
    payload: SubmitAnswer,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EvaluationJobOut:
    if session_id == EXAMPLE_SESSION_ID:
        return build_example_evaluation_job()
    if not payload.answer_text.strip():
        raise HTTPException(status_code=422, detail="Answer text cannot be empty")
    try:
        job = await enqueue_evaluation(db, user.id, session_id, payload.answer_text, payload.report_locale)
    except InsufficientCreditError as exc:
        raise HTTPException(
            status_code=402,
            detail={"code": "INSUFFICIENT_CREDIT", "message": "Credit is not enough."},
        ) from exc
    if job is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return job


@router.get("/{session_id}/report", response_model=ReportOut)
async def read_report(
    session_id: UUID,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> ReportOut:
    if session_id == EXAMPLE_SESSION_ID:
        return build_example_report()
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    report = await get_report(db, user.id, session_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/{session_id}/grammar-analysis", response_model=list[GrammarItemOut])
async def grammar_analysis(
    session_id: UUID,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> list[GrammarItemOut]:
    if session_id == EXAMPLE_SESSION_ID:
        return build_example_grammar()
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    grammar = await get_grammar(db, user.id, session_id)
    if grammar is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return grammar


@router.get("/{session_id}/feedback", response_model=ReportFeedbackStatusOut)
async def feedback_status(
    session_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReportFeedbackStatusOut:
    if session_id == EXAMPLE_SESSION_ID:
        raise HTTPException(status_code=422, detail="The example report does not accept feedback")
    result = await get_report_feedback_status(db, user.id, session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return result


@router.post("/{session_id}/feedback", response_model=ReportFeedbackStatusOut, status_code=201)
async def create_feedback(
    session_id: UUID,
    payload: ReportFeedbackCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReportFeedbackStatusOut:
    if session_id == EXAMPLE_SESSION_ID:
        raise HTTPException(status_code=422, detail="The example report does not accept feedback")
    try:
        feedback = await submit_report_feedback(db, user.id, session_id, payload)
    except FeedbackValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (FeedbackAlreadySubmittedError, IntegrityError) as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Feedback has already been submitted for this report") from exc
    if feedback is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return ReportFeedbackStatusOut(
        submitted=True,
        feedback_type=feedback.feedback_type,
        created_at=feedback.created_at,
    )


@router.get("/{session_id}/download", response_class=HTMLResponse)
async def download_report(
    session_id: UUID,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> str:
    if session_id == EXAMPLE_SESSION_ID:
        report = build_example_report()
    else:
        if user is None:
            raise HTTPException(status_code=401, detail="Authentication required")
        report = await get_report(db, user.id, session_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return f"""
    <html>
      <head><meta charset="UTF-8"><title>TAWEP Report {session_id}</title></head>
      <body>
        <h1>TAWEP Evaluation Report</h1>
        <p>Total Score: {report.total_score} / {report.total_score_30}</p>
        <h2>AI Rewrite</h2>
        <p>{escape(report.ai_rewrite)}</p>
      </body>
    </html>
    """
