from datetime import datetime

from backend.schemas import SessionOut
from backend.services.example_data import EXAMPLE_ANSWER, EXAMPLE_SESSION_ID


def build_example_session() -> SessionOut:
    return SessionOut(
        id=EXAMPLE_SESSION_ID,
        question_no=8,
        mode="example",
        status="submitted",
        time_limit_seconds=None,
        answer_text=EXAMPLE_ANSWER,
        started_at=datetime(2026, 6, 8, 8, 45, 40),
        submitted_at=datetime(2026, 6, 8, 8, 45, 40),
    )
