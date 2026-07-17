import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Question, QuestionSkillProfile
from backend.schemas import QuestionSkillProfileOut


PROFILE_VERSION = "v1"
POSITION_RELATIONS = {
    "opposed",
    "complementary",
    "partially_overlapping",
    "similar",
    "independent",
}
REASONING_MODES = {
    "compare",
    "causal",
    "tradeoff",
    "evaluation",
    "policy",
    "problem_solving",
    "prioritization",
    "prediction",
    "ethical",
    "example_application",
}


def _clamp(value: float, minimum: float = 1, maximum: float = 5) -> float:
    return max(minimum, min(maximum, value))


def _integer_score(value: Any, field: str) -> int:
    try:
        score = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be an integer") from exc
    if not 1 <= score <= 5:
        raise ValueError(f"{field} must be between 1 and 5")
    return score


def derive_opportunities(values: dict[str, Any]) -> dict[str, float]:
    relation_weight = {
        "opposed": 5,
        "partially_overlapping": 4,
        "complementary": 3.5,
        "independent": 3,
        "similar": 2,
    }[values["position_relation"]]
    complex_modes = {
        "causal",
        "tradeoff",
        "evaluation",
        "policy",
        "problem_solving",
        "prioritization",
        "ethical",
    }
    mode_complexity = 1 + min(4, len(set(values["reasoning_modes"]) & complex_modes))
    content = 0.62 * values["constraint_density"] + 0.38 * (6 - values["scope_width"])
    perspective = (
        0.58 * values["perspective_gap"]
        + 0.22 * values["stakeholder_count"]
        + 0.20 * relation_weight
    )
    structure = (
        0.50 * values["argument_steps"]
        + 0.30 * mode_complexity
        + 0.20 * values["constraint_density"]
    )
    return {
        "content_opportunity": round(_clamp(content), 2),
        "perspective_opportunity": round(_clamp(perspective), 2),
        "structure_opportunity": round(_clamp(structure), 2),
    }


def normalize_annotation(raw: dict[str, Any]) -> dict[str, Any]:
    relation = str(raw.get("position_relation", "independent")).strip().lower()
    if relation not in POSITION_RELATIONS:
        raise ValueError(f"Unknown position_relation: {relation}")
    modes = raw.get("reasoning_modes", [])
    if not isinstance(modes, list):
        raise ValueError("reasoning_modes must be an array")
    normalized_modes = list(dict.fromkeys(str(item).strip().lower() for item in modes))
    if not normalized_modes or any(item not in REASONING_MODES for item in normalized_modes):
        raise ValueError(f"Invalid reasoning_modes: {normalized_modes}")
    values = {
        field: _integer_score(raw.get(field), field)
        for field in (
            "constraint_density",
            "scope_width",
            "perspective_gap",
            "stakeholder_count",
            "argument_steps",
            "abstractness",
            "knowledge_load",
            "lexical_load",
        )
    }
    values["position_relation"] = relation
    values["reasoning_modes"] = normalized_modes
    try:
        confidence = float(raw.get("confidence", 0.7))
    except (TypeError, ValueError) as exc:
        raise ValueError("confidence must be numeric") from exc
    values["confidence"] = round(max(0, min(1, confidence)), 2)
    values.update(derive_opportunities(values))
    return values


def heuristic_annotation(question: Question) -> dict[str, Any]:
    messages = {message.speaker_role: message.content for message in question.messages}
    professor = messages.get("professor", "")
    student_text = f"{messages.get('student_a', '')} {messages.get('student_b', '')}"
    full_text = f"{professor} {student_text}"
    lowered = full_text.lower()
    prompt_lower = professor.lower()
    words = re.findall(r"[A-Za-z]+(?:-[A-Za-z]+)?", full_text)

    constraint_markers = (
        "most important",
        "main reason",
        "and why",
        "keeping in mind",
        "what factor",
        "which one",
        "should first",
        "in your opinion",
    )
    constraint_density = int(_clamp(1 + sum(marker in prompt_lower for marker in constraint_markers)))
    scope_width = 2 if any(marker in prompt_lower for marker in ("which", "most important", "best way")) else 4
    if len(professor.split()) > 90:
        scope_width = max(1, scope_width - 1)

    reasoning_modes: list[str] = []
    keyword_modes = {
        "compare": ("compare", "rather than", "or "),
        "causal": ("why", "cause", "effect", "result"),
        "tradeoff": ("advantage", "disadvantage", "benefit", "cost", "balance"),
        "evaluation": ("most important", "best", "effective", "valuable"),
        "policy": ("government", "policy", "public", "tax", "regulation"),
        "problem_solving": ("solve", "address", "reduce", "improve", "prevent"),
        "prioritization": ("first", "priority", "prioritize", "most important"),
        "prediction": ("future", "will", "likely"),
        "ethical": ("fair", "responsibility", "right", "wrong"),
        "example_application": ("example", "experience", "situation"),
    }
    for mode, markers in keyword_modes.items():
        if any(marker in prompt_lower for marker in markers):
            reasoning_modes.append(mode)
    if not reasoning_modes:
        reasoning_modes = ["evaluation"]

    stakeholder_markers = ("student", "employee", "employer", "government", "business", "community", "consumer", "teacher", "parent")
    stakeholder_count = int(_clamp(sum(marker in lowered for marker in stakeholder_markers) or 2))
    perspective_gap = int(_clamp(2 + ("however" in lowered) + ("on the other hand" in lowered) + ("but" in student_text.lower())))
    position_relation = "partially_overlapping" if perspective_gap >= 4 else "independent"
    argument_steps = int(_clamp(2 + (len(reasoning_modes) >= 2) + (len(reasoning_modes) >= 4) + (professor.count("?") > 1)))
    abstractness = int(_clamp(2 + sum(marker in lowered for marker in ("society", "culture", "policy", "responsibility", "value", "economy"))))
    knowledge_load = int(_clamp(1 + sum(marker in lowered for marker in ("tax", "economic", "scientific", "regulation", "infrastructure"))))
    average_length = sum(len(word) for word in words) / max(1, len(words))
    long_ratio = sum(len(word) > 6 for word in words) / max(1, len(words))
    lexical_load = int(_clamp(round(1 + average_length / 2.2 + long_ratio * 2)))

    values = {
        "constraint_density": constraint_density,
        "scope_width": scope_width,
        "perspective_gap": perspective_gap,
        "position_relation": position_relation,
        "reasoning_modes": reasoning_modes,
        "stakeholder_count": stakeholder_count,
        "argument_steps": argument_steps,
        "abstractness": abstractness,
        "knowledge_load": knowledge_load,
        "lexical_load": lexical_load,
        "confidence": 0.42,
    }
    values.update(derive_opportunities(values))
    return values


def apply_profile_values(
    profile: QuestionSkillProfile,
    values: dict[str, Any],
    *,
    source: str,
    version: str = PROFILE_VERSION,
) -> None:
    for field, value in values.items():
        setattr(profile, field, value)
    profile.annotation_source = source
    profile.profile_version = version
    profile.annotated_at = datetime.now(timezone.utc)


async def ensure_heuristic_profile(
    db: AsyncSession,
    question: Question,
    *,
    force: bool = False,
) -> QuestionSkillProfile:
    profile = await db.scalar(
        select(QuestionSkillProfile).where(QuestionSkillProfile.question_id == question.id)
    )
    if profile is None:
        profile = QuestionSkillProfile(question_id=question.id)
        db.add(profile)
    if force or profile.annotation_source == "heuristic":
        apply_profile_values(profile, heuristic_annotation(question), source="heuristic")
    return profile


def profile_out(question: Question, profile: QuestionSkillProfile) -> QuestionSkillProfileOut:
    return QuestionSkillProfileOut(
        question_no=question.question_no,
        constraint_density=profile.constraint_density,
        scope_width=profile.scope_width,
        perspective_gap=profile.perspective_gap,
        position_relation=profile.position_relation,
        reasoning_modes=list(profile.reasoning_modes or []),
        stakeholder_count=profile.stakeholder_count,
        argument_steps=profile.argument_steps,
        abstractness=profile.abstractness,
        knowledge_load=profile.knowledge_load,
        lexical_load=profile.lexical_load,
        content_opportunity=float(profile.content_opportunity),
        perspective_opportunity=float(profile.perspective_opportunity),
        structure_opportunity=float(profile.structure_opportunity),
        annotation_source=profile.annotation_source,
        confidence=float(profile.confidence),
        profile_version=profile.profile_version,
    )
