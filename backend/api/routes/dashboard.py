from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.db.session import get_db
from backend.models import (
    AnswerSession,
    EvaluationReport,
    LanguageMetricScore,
    Question,
    ScoreComponent,
    Topic,
    User,
)
from backend.schemas import BreakdownPoint, DashboardSummary, MatrixRow, RecommendationOut
from backend.services.practice import get_usage
from backend.services.recommendations import recommend_questions


router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def summary(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardSummary:
    credit = await get_usage(db, user.id)
    average_score, practice_count = (
        await db.execute(
            select(func.coalesce(func.avg(EvaluationReport.total_score), 0), func.count(EvaluationReport.id))
            .join(AnswerSession, AnswerSession.id == EvaluationReport.session_id)
            .where(AnswerSession.user_id == user.id)
        )
    ).one()
    weekly_practice_count = int(
        await db.scalar(
            select(func.count(EvaluationReport.id))
            .join(AnswerSession, AnswerSession.id == EvaluationReport.session_id)
            .where(
                AnswerSession.user_id == user.id,
                EvaluationReport.created_at >= datetime.now(timezone.utc) - timedelta(days=7),
            )
        )
        or 0
    )
    return DashboardSummary(
        alias=user.alias,
        user_id=user.id,
        average_score=float(average_score),
        practice_count=int(practice_count),
        weekly_practice_count=weekly_practice_count,
        credit=credit,
    )


@router.get("/recommendations", response_model=list[RecommendationOut])
async def recommendations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[RecommendationOut]:
    return await recommend_questions(db, user.id, limit=2, locale=user.preferred_locale)


@router.get("/records")
async def records(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    rows = (
        await db.execute(
            select(
                AnswerSession.id,
                Question.question_no,
                Topic.name_en,
                EvaluationReport.total_score,
                AnswerSession.submitted_at,
            )
            .join(EvaluationReport, EvaluationReport.session_id == AnswerSession.id)
            .join(Question, Question.id == AnswerSession.question_id)
            .join(Topic, Topic.id == Question.topic_id)
            .where(AnswerSession.user_id == user.id)
            .order_by(AnswerSession.submitted_at.desc())
            .limit(20)
        )
    ).all()
    return [
        {
            "session_id": row.id,
            "question_no": row.question_no,
            "topic": row.name_en,
            "score": float(row.total_score),
            "submitted_at": row.submitted_at,
        }
        for row in rows
    ]


@router.get("/language-profile")
async def language_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, float]:
    rows = (
        await db.execute(
            select(LanguageMetricScore.metric_key, func.avg(LanguageMetricScore.score))
            .join(EvaluationReport, EvaluationReport.id == LanguageMetricScore.report_id)
            .join(AnswerSession, AnswerSession.id == EvaluationReport.session_id)
            .where(AnswerSession.user_id == user.id)
            .group_by(LanguageMetricScore.metric_key)
        )
    ).all()
    return {key: round(float(score), 1) for key, score in rows}


@router.get("/score-breakdown", response_model=list[BreakdownPoint])
async def score_breakdown(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[BreakdownPoint]:
    rows = (
        await db.execute(
            select(EvaluationReport.created_at, ScoreComponent)
            .join(ScoreComponent, ScoreComponent.report_id == EvaluationReport.id)
            .join(AnswerSession, AnswerSession.id == EvaluationReport.session_id)
            .where(AnswerSession.user_id == user.id)
            .order_by(EvaluationReport.created_at.desc())
            .limit(10)
        )
    ).all()
    return [
        BreakdownPoint(
            submitted_at=created_at,
            content_relevance=float(component.content_relevance),
            perspective_expansion=float(component.perspective_expansion),
            linguistic_expression=float(component.linguistic_expression),
            logical_structure=float(component.logical_structure),
        )
        for created_at, component in reversed(rows)
    ]


@router.get("/topic-score-matrix", response_model=list[MatrixRow])
async def topic_score_matrix(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MatrixRow]:
    rows = (
        await db.execute(
            select(
                Topic.name_en,
                func.avg(ScoreComponent.content_relevance),
                func.avg(ScoreComponent.perspective_expansion),
                func.avg(ScoreComponent.linguistic_expression),
                func.avg(ScoreComponent.logical_structure),
            )
            .join(Question, Question.topic_id == Topic.id)
            .join(AnswerSession, AnswerSession.question_id == Question.id)
            .join(EvaluationReport, EvaluationReport.session_id == AnswerSession.id)
            .join(ScoreComponent, ScoreComponent.report_id == EvaluationReport.id)
            .where(AnswerSession.user_id == user.id)
            .group_by(Topic.name_en)
            .order_by(Topic.name_en)
        )
    ).all()
    return [
        MatrixRow(
            topic=row[0],
            content_relevance=round(float(row[1]), 1),
            perspective_expansion=round(float(row[2]), 1),
            linguistic_expression=round(float(row[3]), 1),
            logical_structure=round(float(row[4]), 1),
        )
        for row in rows
    ]
