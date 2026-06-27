from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from backend.api.deps import demo_usage
from backend.schemas import AnswerUpdate, GrammarItemOut, ReportOut, SessionCreate, SessionOut, SubmitAnswer
from backend.services.evaluation import build_debug_grammar, build_debug_report
from backend.services.questions import get_question_by_no
from backend.services.session_store import (
    create_demo_session,
    get_demo_answer,
    get_demo_session,
    submit_demo_answer,
    update_demo_answer,
)


router = APIRouter()


@router.post("/from-question/{question_no}", response_model=SessionOut, status_code=201)
async def create_session(question_no: int, payload: SessionCreate) -> SessionOut:
    if get_question_by_no(question_no) is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return create_demo_session(question_no, payload.mode)


@router.get("/{session_id}", response_model=SessionOut)
async def read_session(session_id: UUID) -> SessionOut:
    session = get_demo_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.patch("/{session_id}/answer", response_model=SessionOut)
async def update_answer(session_id: UUID, payload: AnswerUpdate) -> SessionOut:
    updated = update_demo_answer(session_id, payload.answer_text)
    if updated is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return updated


@router.post("/{session_id}/submit", response_model=ReportOut)
async def submit_answer(session_id: UUID, payload: SubmitAnswer) -> ReportOut:
    usage = demo_usage()
    if usage.balance < 3 or usage.weekly_used + 3 > usage.weekly_limit:
        raise HTTPException(status_code=402, detail={"code": "INSUFFICIENT_CREDIT", "message": "Credit is not enough."})
    if submit_demo_answer(session_id, payload.answer_text) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return build_debug_report(session_id, payload.answer_text)


@router.get("/{session_id}/report", response_model=ReportOut)
async def read_report(session_id: UUID) -> ReportOut:
    await read_session(session_id)
    return build_debug_report(session_id, get_demo_answer(session_id))


@router.get("/{session_id}/grammar-analysis", response_model=list[GrammarItemOut])
async def grammar_analysis(session_id: UUID) -> list[GrammarItemOut]:
    await read_session(session_id)
    return build_debug_grammar(get_demo_answer(session_id))


@router.get("/{session_id}/download", response_class=HTMLResponse)
async def download_report(session_id: UUID) -> str:
    report = await read_report(session_id)
    return f"""
    <html>
      <head><meta charset="UTF-8"><title>TAWEP Report {session_id}</title></head>
      <body>
        <h1>TAWEP Evaluation Report</h1>
        <p>Total Score: {report.total_score} / {report.total_score_30}</p>
        <h2>AI Rewrite</h2>
        <p>{report.ai_rewrite}</p>
      </body>
    </html>
    """
