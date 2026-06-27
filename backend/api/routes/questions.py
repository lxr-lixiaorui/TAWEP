from fastapi import APIRouter, HTTPException, Query

from backend.schemas import APIMessage, QuestionCreate, QuestionOut, SessionCreate, SessionOut
from backend.services.questions import TOPICS, filter_questions, get_question_by_no
from backend.services.session_store import create_demo_session


router = APIRouter()


@router.get("", response_model=list[QuestionOut])
async def list_questions(
    difficulty: str | None = Query(default=None),
    source: str | None = Query(default=None),
    topic: str | None = Query(default=None),
) -> list[QuestionOut]:
    return filter_questions(difficulty=difficulty, source=source, topic=topic)


@router.get("/topics")
async def list_topics() -> list[str]:
    return TOPICS


@router.post("/upload", response_model=APIMessage, status_code=201)
async def upload_question(payload: QuestionCreate) -> APIMessage:
    return APIMessage(message=f"Question upload accepted for review in topic {payload.topic}")


@router.get("/{question_no}", response_model=QuestionOut)
async def read_question(question_no: int) -> QuestionOut:
    question = get_question_by_no(question_no)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.post("/{question_no}/sessions", response_model=SessionOut, status_code=201)
async def create_question_session(question_no: int, payload: SessionCreate) -> SessionOut:
    if get_question_by_no(question_no) is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return create_demo_session(question_no, payload.mode)
