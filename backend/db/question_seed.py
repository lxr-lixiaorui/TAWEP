import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from backend.db.session import AsyncSessionLocal, engine
from backend.models import (
    Question,
    QuestionMessage,
    QuestionSkillProfile,
    QuestionSource,
    ReviewStatus,
    Topic,
)


SEED_PATH = Path(__file__).resolve().parent / "seed" / "question_bank.json"
SEED_VERSION = 1
PROFILE_FIELDS = (
    "constraint_density",
    "scope_width",
    "perspective_gap",
    "position_relation",
    "reasoning_modes",
    "stakeholder_count",
    "argument_steps",
    "abstractness",
    "knowledge_load",
    "lexical_load",
    "content_opportunity",
    "perspective_opportunity",
    "structure_opportunity",
    "annotation_source",
    "confidence",
    "profile_version",
)


def _profile_payload(profile: QuestionSkillProfile | None) -> dict[str, Any] | None:
    if profile is None:
        return None
    payload: dict[str, Any] = {}
    for field in PROFILE_FIELDS:
        value = getattr(profile, field)
        payload[field] = float(value) if field.endswith("_opportunity") or field == "confidence" else value
    return payload


def _load_seed(path: Path = SEED_PATH) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("version") != SEED_VERSION:
        raise RuntimeError(f"Unsupported question seed version: {payload.get('version')}")
    questions = payload.get("questions")
    if not isinstance(questions, list) or not questions:
        raise RuntimeError("Question seed is empty or malformed")
    numbers = [int(item["question_no"]) for item in questions]
    if len(numbers) != len(set(numbers)):
        raise RuntimeError("Question seed contains duplicate question numbers")
    for item in questions:
        if item.get("source") not in {"official", "user"}:
            raise RuntimeError(f"Question {item.get('question_no')} has an invalid source")
        if item.get("exam_type") not in {"classic", "reform_2026"}:
            raise RuntimeError(f"Question {item.get('question_no')} has an invalid exam type")
        messages = item.get("messages")
        if not isinstance(messages, list) or len(messages) < 3:
            raise RuntimeError(f"Question {item.get('question_no')} has incomplete messages")
    return sorted(questions, key=lambda item: int(item["question_no"]))


async def export_seed(path: Path = SEED_PATH) -> int:
    async with AsyncSessionLocal() as db:
        questions = list(
            (
                await db.scalars(
                    select(Question)
                    .options(
                        joinedload(Question.topic),
                        selectinload(Question.messages),
                        joinedload(Question.skill_profile),
                    )
                    .where(Question.status == ReviewStatus.accepted)
                    .order_by(Question.question_no)
                )
            ).all()
        )
    serialized = []
    for question in questions:
        serialized.append(
            {
                "question_no": question.question_no,
                "source": question.source.value,
                "exam_type": question.exam_type,
                "difficulty": question.difficulty,
                "summary": question.summary,
                "word_count": question.word_count,
                "topic": {
                    "key": question.topic.key,
                    "name_en": question.topic.name_en,
                    "name_zh": question.topic.name_zh,
                    "sort_order": question.topic.sort_order,
                },
                "messages": [
                    {
                        "speaker_role": message.speaker_role,
                        "speaker_name": message.speaker_name,
                        "content": message.content,
                        "sort_order": message.sort_order,
                    }
                    for message in sorted(question.messages, key=lambda item: item.sort_order)
                ],
                "skill_profile": _profile_payload(question.skill_profile),
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"version": SEED_VERSION, "question_count": len(serialized), "questions": serialized},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return len(serialized)


async def import_seed(path: Path = SEED_PATH) -> tuple[int, int]:
    questions = _load_seed(path)
    inserted = 0
    skipped = 0
    async with AsyncSessionLocal() as db:
        async with db.begin():
            topics = {topic.key: topic for topic in (await db.scalars(select(Topic))).all()}
            for raw in questions:
                raw_topic = raw["topic"]
                topic = topics.get(raw_topic["key"])
                if topic is None:
                    topic = Topic(
                        key=raw_topic["key"],
                        name_en=raw_topic["name_en"],
                        name_zh=raw_topic["name_zh"],
                        sort_order=int(raw_topic["sort_order"]),
                    )
                    db.add(topic)
                    topics[topic.key] = topic
            await db.flush()

            existing = {
                question.question_no: question
                for question in (
                    await db.scalars(
                        select(Question).options(joinedload(Question.skill_profile))
                    )
                ).all()
            }
            for raw in questions:
                question_no = int(raw["question_no"])
                question = existing.get(question_no)
                if question is not None:
                    profile = raw.get("skill_profile")
                    if question.skill_profile is None and profile:
                        db.add(QuestionSkillProfile(question_id=question.id, **profile))
                    skipped += 1
                    continue
                question = Question(
                    question_no=question_no,
                    source=QuestionSource(raw["source"]),
                    creator_user_id=None,
                    topic=topics[raw["topic"]["key"]],
                    exam_type=raw["exam_type"],
                    difficulty=raw["difficulty"],
                    summary=raw["summary"],
                    status=ReviewStatus.accepted,
                    avg_score=None,
                    word_count=int(raw["word_count"]),
                )
                question.messages = [QuestionMessage(**message) for message in raw["messages"]]
                if raw.get("skill_profile"):
                    question.skill_profile = QuestionSkillProfile(**raw["skill_profile"])
                db.add(question)
                inserted += 1
    return inserted, skipped


async def main(export: bool, path: Path) -> None:
    if export:
        count = await export_seed(path)
        print(f"Exported {count} public questions to {path}")
    else:
        inserted, skipped = await import_seed(path)
        print(f"Question seed ready: {inserted} inserted, {skipped} already present")
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export or import the deployable public question bank")
    parser.add_argument("--export", action="store_true", help="Export accepted public questions from the current database")
    parser.add_argument("--path", type=Path, default=SEED_PATH)
    args = parser.parse_args()
    asyncio.run(main(args.export, args.path))
