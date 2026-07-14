from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.api.deps import get_current_user
from backend.models import User
from backend.schemas import QuestionCreate, QuestionOut, QuestionSubmissionOut, SessionCreate, SessionOut
from backend.services.questions import (
    EXAM_TYPES,
    filter_database_questions,
    create_uploaded_question,
    get_database_question_by_no,
    list_database_topics,
)
from backend.services.practice import create_session


router = APIRouter()


@router.get("", response_model=list[QuestionOut])
async def list_questions(
    db: AsyncSession = Depends(get_db),
    difficulty: str | None = Query(default=None),
    source: str | None = Query(default=None),
    topic: str | None = Query(default=None),
    exam_type: str | None = Query(default=None),
) -> list[QuestionOut]:
    return await filter_database_questions(db, difficulty, source, topic, exam_type)


@router.get("/topics")
async def list_topics(db: AsyncSession = Depends(get_db)) -> list[str]:
    return await list_database_topics(db)


@router.get("/exam-types")
async def list_exam_types() -> dict[str, str]:
    return EXAM_TYPES


@router.post("/upload", response_model=QuestionSubmissionOut, status_code=201)
async def upload_question(
    payload: QuestionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QuestionSubmissionOut:
    try:
        async with db.begin():
            question = await create_uploaded_question(db, user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return QuestionSubmissionOut(
        id=question.id,
        question_no=question.question_no,
        status=question.status.value,
        message="Question submitted for administrator review",
    )


@router.get("/{question_no}", response_model=QuestionOut)
async def read_question(question_no: int, db: AsyncSession = Depends(get_db)) -> QuestionOut:
    question = await get_database_question_by_no(db, question_no)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.post("/{question_no}/sessions", response_model=SessionOut, status_code=201)
async def create_question_session(
    question_no: int,
    payload: SessionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionOut:
    session = await create_session(db, user.id, question_no, payload.mode)
    if session is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return session
