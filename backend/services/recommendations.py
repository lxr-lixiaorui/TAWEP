from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from backend.models import (
    AnswerSession,
    EvaluationReport,
    Question,
    QuestionSource,
    ReviewStatus,
    ScoreComponent,
    Topic,
)
from backend.schemas import RecommendationOut
from backend.services.question_profiles import heuristic_annotation


DIMENSIONS = (
    "content_relevance",
    "perspective_expansion",
    "linguistic_expression",
    "logical_structure",
)


@dataclass
class Candidate:
    question: Question
    focus_dimension: str
    score: float
    weighted_average: float | None
    profile_values: dict


def _profile_values(question: Question) -> dict:
    profile = question.skill_profile
    if profile is None:
        return {**heuristic_annotation(question), "annotation_source": "heuristic"}
    return {
        "content_opportunity": float(profile.content_opportunity),
        "perspective_opportunity": float(profile.perspective_opportunity),
        "structure_opportunity": float(profile.structure_opportunity),
        "lexical_load": profile.lexical_load,
        "confidence": float(profile.confidence),
        "annotation_source": profile.annotation_source,
    }


def _reason(
    candidate: Candidate,
    locale: str,
) -> str:
    labels = {
        "en": {
            "content_relevance": "Content Relevance",
            "perspective_expansion": "Perspectives Expansion",
            "linguistic_expression": "Linguistic Expression",
            "logical_structure": "Logical Structure",
        },
        "zh": {
            "content_relevance": "内容切题",
            "perspective_expansion": "观点拓展",
            "linguistic_expression": "语言表达",
            "logical_structure": "逻辑结构",
        },
    }
    language = "zh" if locale.lower().startswith("zh") else "en"
    label = labels[language][candidate.focus_dimension]
    difficulty = candidate.question.difficulty
    if language == "zh":
        difficulty_label = {"easy": "较低", "medium": "适中", "hard": "较高"}.get(difficulty, "适中")
        if candidate.weighted_average is None:
            return f"这道题提供较强的{label}训练机会，语言与认知负担{difficulty_label}。"
        if candidate.focus_dimension == "linguistic_expression":
            return f"你近期的{label}加权均分为 {candidate.weighted_average:.1f}；这道题的词汇负担与当前水平匹配，适合集中改善表达准确性。"
        return f"你近期的{label}加权均分为 {candidate.weighted_average:.1f}；这道题针对该能力提供训练机会，整体难度{difficulty_label}。"
    difficulty_phrase = {"easy": "an accessible", "medium": "a moderate", "hard": "a challenging"}.get(difficulty, "a moderate")
    if candidate.weighted_average is None:
        return f"This prompt offers a strong {label} practice opportunity with {difficulty_phrase} overall load."
    if candidate.focus_dimension == "linguistic_expression":
        return f"Your recent weighted {label} score is {candidate.weighted_average:.1f}; this prompt keeps lexical load manageable so you can focus on accurate expression."
    return f"Your recent weighted {label} score is {candidate.weighted_average:.1f}; this prompt targets that skill with {difficulty_phrase} overall load."


async def recommend_questions(
    db: AsyncSession,
    user_id: UUID | None,
    *,
    limit: int = 2,
    locale: str = "en",
    difficulty: str | None = None,
    source: str | None = None,
    topic: str | None = None,
    exam_type: str | None = None,
) -> list[RecommendationOut]:
    statement = (
        select(Question)
        .options(
            joinedload(Question.topic),
            joinedload(Question.skill_profile),
            selectinload(Question.messages),
        )
        .where(Question.status == ReviewStatus.accepted)
    )
    if difficulty:
        statement = statement.where(Question.difficulty == difficulty)
    if source:
        statement = statement.where(Question.source == QuestionSource(source))
    if topic:
        statement = statement.join(Topic).where(Topic.name_en == topic)
    if exam_type:
        statement = statement.where(Question.exam_type == exam_type)
    questions = list((await db.scalars(statement.order_by(Question.question_no))).all())
    if not questions:
        return []

    history_rows = []
    if user_id is not None:
        history_rows = list(
            (
                await db.execute(
                    select(
                        ScoreComponent,
                        EvaluationReport.created_at,
                        AnswerSession.question_id,
                        Question.topic_id,
                    )
                    .join(EvaluationReport, EvaluationReport.id == ScoreComponent.report_id)
                    .join(AnswerSession, AnswerSession.id == EvaluationReport.session_id)
                    .join(Question, Question.id == AnswerSession.question_id)
                    .where(AnswerSession.user_id == user_id)
                    .order_by(EvaluationReport.created_at.desc())
                    .limit(12)
                )
            ).all()
        )

    weighted_totals = {dimension: 0.0 for dimension in DIMENSIONS}
    weight_sum = 0.0
    topic_totals: dict[UUID, tuple[float, float]] = {}
    recent_ids: list[UUID] = []
    for index, (component, _, question_id, topic_id) in enumerate(history_rows):
        weight = 0.84**index
        weight_sum += weight
        scores = {dimension: float(getattr(component, dimension)) for dimension in DIMENSIONS}
        for dimension, value in scores.items():
            weighted_totals[dimension] += value * weight
        topic_total, topic_weight = topic_totals.get(topic_id, (0.0, 0.0))
        topic_totals[topic_id] = (topic_total + sum(scores.values()) / len(DIMENSIONS) * weight, topic_weight + weight)
        recent_ids.append(question_id)

    weighted_averages = {
        dimension: weighted_totals[dimension] / weight_sum
        for dimension in DIMENSIONS
    } if weight_sum else {}
    if weighted_averages:
        needs = {
            dimension: max(0.15, 4.3 - weighted_averages[dimension])
            for dimension in DIMENSIONS
        }
    else:
        needs = {
            "content_relevance": 1.0,
            "perspective_expansion": 1.0,
            "linguistic_expression": 0.35,
            "logical_structure": 1.0,
        }
    need_sum = sum(needs.values())
    need_weights = {dimension: value / need_sum for dimension, value in needs.items()}
    overall_average = sum(weighted_averages.values()) / len(weighted_averages) if weighted_averages else 3.5
    target_difficulty = "easy" if overall_average < 3.1 else "medium" if overall_average < 4.2 else "hard"
    target_lexical_load = 2 if weighted_averages.get("linguistic_expression", 3.5) < 3.1 else 3 if weighted_averages.get("linguistic_expression", 3.5) < 4.2 else 4
    weakest_topic_id = None
    if len(history_rows) >= 3 and topic_totals:
        weakest_topic_id = min(topic_totals, key=lambda item: topic_totals[item][0] / topic_totals[item][1])

    candidates: list[Candidate] = []
    recent_set = set(recent_ids[:5])
    for question in questions:
        profile = _profile_values(question)
        opportunities = {
            "content_relevance": float(profile["content_opportunity"]),
            "perspective_expansion": float(profile["perspective_opportunity"]),
            "logical_structure": float(profile["structure_opportunity"]),
            "linguistic_expression": max(1.0, 5.0 - abs(float(profile["lexical_load"]) - target_lexical_load)),
        }
        contributions = {
            dimension: need_weights[dimension] * opportunities[dimension] / 5
            for dimension in DIMENSIONS
        }
        focus_dimension = max(contributions, key=contributions.get)
        weakness_match = sum(contributions.values())
        topic_match = 1.0 if weakest_topic_id is not None and question.topic_id == weakest_topic_id else 0.45
        difficulty_match = 1.0 if question.difficulty == target_difficulty else 0.55
        novelty = 0.0 if question.id in recent_set else 1.0
        confidence = float(profile.get("confidence", 0.42))
        score = (
            0.55 * weakness_match
            + 0.15 * topic_match
            + 0.12 * difficulty_match
            + 0.10 * novelty
            + 0.08 * confidence
        )
        candidates.append(
            Candidate(
                question=question,
                focus_dimension=focus_dimension,
                score=score,
                weighted_average=weighted_averages.get(focus_dimension),
                profile_values=profile,
            )
        )

    selected: list[Candidate] = []
    remaining = candidates[:]
    while remaining and len(selected) < limit:
        def diversified_score(item: Candidate) -> float:
            topic_penalty = 0.08 if any(chosen.question.topic_id == item.question.topic_id for chosen in selected) else 0
            focus_penalty = 0.04 if any(chosen.focus_dimension == item.focus_dimension for chosen in selected) else 0
            return item.score - topic_penalty - focus_penalty

        chosen = max(remaining, key=diversified_score)
        remaining.remove(chosen)
        selected.append(chosen)

    return [
        RecommendationOut(
            question_no=item.question.question_no,
            summary=item.question.summary,
            topic=item.question.topic.name_en,
            exam_type=item.question.exam_type,
            difficulty=item.question.difficulty,
            reason=_reason(item, locale),
            focus_dimension=item.focus_dimension,
            match_score=round(item.score * 100, 1),
        )
        for item in selected
    ]
