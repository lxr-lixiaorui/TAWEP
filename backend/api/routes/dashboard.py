from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.db.session import get_db
from backend.schemas import BreakdownPoint, DashboardSummary, MatrixRow, RecommendationOut
from backend.services.practice import get_usage


router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def summary(db: AsyncSession = Depends(get_db)) -> DashboardSummary:
    user = get_current_user()
    return DashboardSummary(
        alias=user.alias,
        user_id=user.id,
        average_score=4.0,
        practice_count=18,
        credit=await get_usage(db),
    )


@router.get("/recommendations", response_model=list[RecommendationOut])
async def recommendations() -> list[RecommendationOut]:
    return [
        RecommendationOut(
            question_no=24,
            summary="Should governments support public transportation with tax revenue?",
            topic="Policy",
            reason="Logical Structure is your lowest recent dimension in Policy prompts.",
        ),
        RecommendationOut(
            question_no=17,
            summary="What is the biggest mistake people make when buying tech products?",
            topic="Technology",
            reason="Technology questions expose recurring perspective expansion gaps.",
        ),
    ]


@router.get("/records")
async def records() -> list[dict]:
    now = datetime.utcnow()
    return [
        {
            "session_id": f"00000000-0000-4000-8000-{index:012d}",
            "question_no": 10 + index,
            "topic": ["Education", "Policy", "Technology"][index % 3],
            "score": round(3.5 + index * 0.1, 1),
            "submitted_at": now - timedelta(days=index),
        }
        for index in range(1, 8)
    ]


@router.get("/language-profile")
async def language_profile() -> dict[str, float]:
    return {
        "clarity": 4.1,
        "precision": 3.7,
        "variety": 3.6,
        "cohesion": 3.9,
        "academic_tone": 3.8,
        "sentence_control": 3.5,
    }


@router.get("/score-breakdown", response_model=list[BreakdownPoint])
async def score_breakdown() -> list[BreakdownPoint]:
    now = datetime.utcnow()
    return [
        BreakdownPoint(
            submitted_at=now - timedelta(days=10 - index),
            content_relevance=round(3.4 + index * 0.07, 1),
            perspective_expansion=round(3.2 + index * 0.08, 1),
            linguistic_expression=round(3.1 + index * 0.05, 1),
            logical_structure=round(3.3 + index * 0.06, 1),
        )
        for index in range(10)
    ]


@router.get("/topic-score-matrix", response_model=list[MatrixRow])
async def topic_score_matrix() -> list[MatrixRow]:
    return [
        MatrixRow(topic="Education", content_relevance=4.2, perspective_expansion=3.8, linguistic_expression=3.9, logical_structure=4.0),
        MatrixRow(topic="Environment", content_relevance=3.7, perspective_expansion=3.4, linguistic_expression=3.8, logical_structure=3.5),
        MatrixRow(topic="Policy", content_relevance=3.9, perspective_expansion=3.6, linguistic_expression=3.7, logical_structure=3.3),
        MatrixRow(topic="Technology", content_relevance=4.0, perspective_expansion=3.5, linguistic_expression=3.6, logical_structure=3.7),
    ]
