from datetime import datetime
from uuid import UUID, uuid4

from backend.schemas import SessionOut


_sessions: dict[UUID, SessionOut] = {}


def create_demo_session(question_no: int, mode: str) -> SessionOut:
    session = SessionOut(
        id=uuid4(),
        question_no=question_no,
        mode=mode,
        status="in_progress",
        time_limit_seconds=600 if mode == "timed" else None,
        answer_text="",
        started_at=datetime.utcnow(),
        submitted_at=None,
    )
    _sessions[session.id] = session
    return session


def get_demo_session(session_id: UUID) -> SessionOut | None:
    return _sessions.get(session_id)


def update_demo_answer(session_id: UUID, answer_text: str) -> SessionOut | None:
    session = _sessions.get(session_id)
    if session is None:
        return None
    updated = session.model_copy(update={"answer_text": answer_text})
    _sessions[session_id] = updated
    return updated


def submit_demo_answer(session_id: UUID, answer_text: str) -> SessionOut | None:
    session = _sessions.get(session_id)
    if session is None:
        return None
    submitted = session.model_copy(
        update={
            "answer_text": answer_text,
            "status": "submitted",
            "submitted_at": datetime.utcnow(),
        }
    )
    _sessions[session_id] = submitted
    return submitted


def get_demo_answer(session_id: UUID) -> str:
    session = _sessions.get(session_id)
    if session is None:
        return ""
    return session.answer_text
