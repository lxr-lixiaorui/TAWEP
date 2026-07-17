import argparse
import asyncio
import json
import re
from pathlib import Path
from typing import Any

from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from backend.core.config import get_settings
from backend.db.session import AsyncSessionLocal
from backend.models import Question, QuestionSkillProfile, QuestionSource, ReviewStatus
from backend.services.question_profiles import (
    PROFILE_VERSION,
    apply_profile_values,
    heuristic_annotation,
    normalize_annotation,
)


CACHE_PATH = Path("backend/db/question_skill_profiles.json")
BATCH_SIZE = 8


def _parse_json_response(content: str) -> dict[str, Any]:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end < start:
        raise ValueError("DeepSeek response did not contain a JSON object")
    return json.loads(cleaned[start : end + 1])


def _validate_batch(payload: dict[str, Any], expected_numbers: set[int]) -> list[dict[str, Any]]:
    items = payload.get("items")
    if not isinstance(items, list):
        raise ValueError("DeepSeek response must contain an items array")
    validated = []
    seen: set[int] = set()
    for raw in items:
        question_no = int(raw["question_no"])
        if question_no not in expected_numbers or question_no in seen:
            raise ValueError(f"Unexpected or duplicate question number: {question_no}")
        values = normalize_annotation(raw)
        validated.append({"question_no": question_no, **values})
        seen.add(question_no)
    if seen != expected_numbers:
        raise ValueError(f"Missing question numbers: {sorted(expected_numbers - seen)}")
    return sorted(validated, key=lambda item: item["question_no"])


def generate_annotations(questions: list[Question]) -> list[dict[str, Any]]:
    settings = get_settings()
    if not settings.deepseek_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured in .env")
    client = OpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)
    system_prompt = """You annotate observable task demands in TOEFL Academic Discussion prompts.
Do not predict student scores, empirical difficulty, or learning outcomes. Rate each field from 1 (low) to 5 (high):
- constraint_density: how many explicit conditions a relevant answer must satisfy
- scope_width: how broad the valid response space is
- perspective_gap: how much meaningful room remains beyond the two student posts
- stakeholder_count: number and diversity of affected perspectives, capped at 5
- argument_steps: reasoning layers normally needed for a complete answer
- abstractness: conceptual rather than concrete/personal reasoning
- knowledge_load: external domain knowledge burden
- lexical_load: topic-specific and abstract vocabulary burden
position_relation must be exactly one of: opposed, complementary, partially_overlapping, similar, independent.
reasoning_modes must contain one or more of: compare, causal, tradeoff, evaluation, policy, problem_solving, prioritization, prediction, ethical, example_application.
confidence is 0 to 1 and reflects how clearly the text supports the annotation.
Return JSON only: {"items":[{"question_no":1,"constraint_density":3,"scope_width":3,"perspective_gap":4,"position_relation":"opposed","reasoning_modes":["tradeoff","evaluation"],"stakeholder_count":3,"argument_steps":3,"abstractness":2,"knowledge_load":1,"lexical_load":2,"confidence":0.86}]}.
Judge task structure, not topic popularity. Do not add opportunity scores; they are derived deterministically by the application."""
    generated: list[dict[str, Any]] = []
    for offset in range(0, len(questions), BATCH_SIZE):
        batch = questions[offset : offset + BATCH_SIZE]
        inputs = []
        for question in batch:
            messages = {message.speaker_role: message.content for message in question.messages}
            inputs.append(
                {
                    "question_no": question.question_no,
                    "professor_prompt": messages.get("professor", ""),
                    "student_a": messages.get("student_a", ""),
                    "student_b": messages.get("student_b", ""),
                }
            )
        expected = {item["question_no"] for item in inputs}
        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                response = client.chat.completions.create(
                    model=settings.deepseek_audit_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": json.dumps(inputs, ensure_ascii=False)},
                    ],
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content or ""
                generated.extend(_validate_batch(_parse_json_response(content), expected))
                print(f"Annotated {min(offset + len(batch), len(questions))}/{len(questions)} questions", flush=True)
                break
            except Exception as exc:
                last_error = exc
                print(f"Batch {offset // BATCH_SIZE + 1} attempt {attempt} failed: {exc}", flush=True)
        else:
            raise RuntimeError(f"Could not annotate batch {offset // BATCH_SIZE + 1}") from last_error
    CACHE_PATH.write_text(json.dumps(generated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return generated


async def load_questions() -> list[Question]:
    async with AsyncSessionLocal() as db:
        return list(
            (
                await db.scalars(
                    select(Question)
                    .options(joinedload(Question.topic), selectinload(Question.messages))
                    .where(Question.status == ReviewStatus.accepted)
                    .order_by(Question.question_no)
                )
            ).all()
        )


async def save_profiles(questions: list[Question], annotations: list[dict[str, Any]]) -> None:
    by_number = {item["question_no"]: item for item in annotations}
    async with AsyncSessionLocal() as db:
        async with db.begin():
            existing = {
                profile.question_id: profile
                for profile in (await db.scalars(select(QuestionSkillProfile))).all()
            }
            for question in questions:
                profile = existing.get(question.id)
                if profile is None:
                    profile = QuestionSkillProfile(question_id=question.id)
                    db.add(profile)
                raw = by_number.get(question.question_no)
                if raw is not None and question.source == QuestionSource.official:
                    values = {key: value for key, value in raw.items() if key != "question_no"}
                    apply_profile_values(profile, values, source="llm", version=PROFILE_VERSION)
                else:
                    apply_profile_values(profile, heuristic_annotation(question), source="heuristic", version=PROFILE_VERSION)


async def main(regenerate: bool, heuristic_only: bool) -> None:
    questions = await load_questions()
    official_questions = [question for question in questions if question.source == QuestionSource.official]
    annotations: list[dict[str, Any]] = []
    if not heuristic_only:
        expected = {question.question_no for question in official_questions}
        if CACHE_PATH.exists() and not regenerate:
            cached = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            annotations = _validate_batch({"items": cached}, expected)
        else:
            annotations = generate_annotations(official_questions)
    await save_profiles(questions, annotations)
    print(f"Stored {len(questions)} question skill profiles ({len(annotations)} LLM, {len(questions) - len(annotations)} heuristic)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Annotate question task demands and seed recommendation profiles")
    parser.add_argument("--regenerate", action="store_true", help="Regenerate DeepSeek annotations instead of using cache")
    parser.add_argument("--heuristic-only", action="store_true", help="Seed local heuristic profiles without calling DeepSeek")
    args = parser.parse_args()
    asyncio.run(main(args.regenerate, args.heuristic_only))
