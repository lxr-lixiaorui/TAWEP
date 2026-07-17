from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.api.deps import get_current_user, get_optional_user
from backend.models import User
from backend.schemas import QuestionBankStats, RecommendationOut, QuestionOut, QuestionSubmissionOut, QuestionUploadCreate, SessionCreate, SessionOut
from backend.services.questions import (
    EXAM_TYPES,
    filter_database_questions,
    create_uploaded_question,
    get_question_bank_stats,
    get_database_question_by_no,
    list_database_topics,
)
from backend.services.practice import create_session
from backend.services.practice import InsufficientCreditError
from backend.services.consents import add_consent_event
from backend.services.legal_documents import QUESTION_RIGHTS_VERSION, require_version
from backend.services.recommendations import recommend_questions


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


@router.get("/stats", response_model=QuestionBankStats)
async def question_bank_stats(db: AsyncSession = Depends(get_db)) -> QuestionBankStats:
    question_count, topic_count = await get_question_bank_stats(db)
    return QuestionBankStats(question_count=question_count, topic_count=topic_count)


@router.get("/recommendations", response_model=list[RecommendationOut])
async def question_recommendations(
    limit: int = Query(default=1, ge=1, le=10),
    locale: str = Query(default="en", pattern="^(en|zh)$"),
    difficulty: str | None = Query(default=None, pattern="^(easy|medium|hard)$"),
    source: str | None = Query(default=None, pattern="^(official|user)$"),
    topic: str | None = Query(default=None),
    exam_type: str | None = Query(default=None, pattern="^(classic|reform_2026)$"),
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> list[RecommendationOut]:
    return await recommend_questions(
        db,
        user.id if user else None,
        limit=limit,
        locale=locale,
        difficulty=difficulty,
        source=source,
        topic=topic,
        exam_type=exam_type,
    )


@router.post("/upload", response_model=QuestionSubmissionOut, status_code=201)
async def upload_question(
    payload: QuestionUploadCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QuestionSubmissionOut:
    try:
        require_version(payload.rights_statement_version, QUESTION_RIGHTS_VERSION, "question publication statement")
        async with db.begin():
            question = await create_uploaded_question(db, user.id, payload)
            add_consent_event(
                db,
                user.id,
                "question_publication",
                payload.rights_statement_version,
                True,
                request,
                resource_type="question",
                resource_id=question.id,
                details={"question_no": question.question_no},
            )
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
    try:
        session = await create_session(db, user.id, question_no, payload.mode)
    except InsufficientCreditError as exc:
        raise HTTPException(
            status_code=402,
            detail={"code": "INSUFFICIENT_CREDIT", "message": "Credit is not enough to start a scored session."},
        ) from exc
    if session is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return session
