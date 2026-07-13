import argparse
import asyncio
import json
import re
from pathlib import Path
from typing import Any

from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.core.config import get_settings
from backend.db.session import AsyncSessionLocal
from backend.models import Question, QuestionMessage, QuestionSource, ReviewStatus, Topic
from backend.services.questions import load_legacy_questions


SOURCE_PATH = Path("static/table/2023_AcaTalk.txt")
CACHE_PATH = Path("backend/db/question_metadata.json")
BATCH_SIZE = 12

TOPIC_DEFINITIONS = {
    "Education": ("education", "教育"),
    "Environment": ("environment", "环境"),
    "Policy": ("policy", "公共政策"),
    "Business": ("business", "商业"),
    "Technology": ("technology", "科技"),
    "Consumer Behavior": ("consumer_behavior", "消费者行为"),
    "Health": ("health", "健康"),
    "Culture": ("culture", "文化"),
    "Lifelong Learning": ("lifelong_learning", "终身学习"),
}


def _word_count(value: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*", value))


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

    validated: list[dict[str, Any]] = []
    seen: set[int] = set()
    for raw_item in items:
        question_no = int(raw_item["question_no"])
        summary = str(raw_item["summary"]).strip().strip('"').rstrip(".")
        topic = str(raw_item["topic"]).strip()
        if question_no not in expected_numbers or question_no in seen:
            raise ValueError(f"Unexpected or duplicate question number: {question_no}")
        if not summary or _word_count(summary) > 20 or len(summary) > 240:
            raise ValueError(f"Question {question_no} has an invalid summary: {summary!r}")
        if topic not in TOPIC_DEFINITIONS:
            raise ValueError(f"Question {question_no} has an invalid topic: {topic!r}")
        validated.append({"question_no": question_no, "summary": summary, "topic": topic})
        seen.add(question_no)

    if seen != expected_numbers:
        raise ValueError(f"Missing question numbers: {sorted(expected_numbers - seen)}")
    return sorted(validated, key=lambda item: item["question_no"])


def generate_metadata(questions: list[Any]) -> list[dict[str, Any]]:
    settings = get_settings()
    if not settings.deepseek_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured in .env")

    client = OpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)
    topic_names = ", ".join(TOPIC_DEFINITIONS)
    system_prompt = f"""You extract the core question from TOEFL Academic Discussion professor prompts.
For every input item, return one object with question_no, summary, and topic.
The summary must be an English phrase of at most 20 words that captures only the core question itself.
Do not summarize background context or student responses. Do not end summaries with a period.
Classify topic as exactly one of: {topic_names}.
Return only JSON in this shape: {{"items":[{{"question_no":1,"summary":"...","topic":"Education"}}]}}.
Example core question: "In industries where remote work is possible, what is the most important factor for employers to consider when deciding where employees should work, and why?"
Example summary: "Key employer factor for remote-work location picks"""

    generated: list[dict[str, Any]] = []
    for offset in range(0, len(questions), BATCH_SIZE):
        batch = questions[offset : offset + BATCH_SIZE]
        inputs = [
            {
                "question_no": question.question_no,
                "professor_prompt": question.messages[0].content,
            }
            for question in batch
        ]
        expected_numbers = {item["question_no"] for item in inputs}
        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                response = client.chat.completions.create(
                    model=settings.deepseek_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": json.dumps(inputs, ensure_ascii=False)},
                    ],
                )
                content = response.choices[0].message.content or ""
                generated.extend(_validate_batch(_parse_json_response(content), expected_numbers))
                print(f"Generated {min(offset + len(batch), len(questions))}/{len(questions)} summaries", flush=True)
                break
            except Exception as exc:
                last_error = exc
                print(f"Batch {offset // BATCH_SIZE + 1} attempt {attempt} failed: {exc}", flush=True)
        else:
            raise RuntimeError(f"Could not generate valid metadata for batch {offset // BATCH_SIZE + 1}") from last_error

    CACHE_PATH.write_text(json.dumps(generated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return generated


def load_or_generate_metadata(questions: list[Any], regenerate: bool) -> list[dict[str, Any]]:
    expected_numbers = {question.question_no for question in questions}
    if CACHE_PATH.exists() and not regenerate:
        cached = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        return _validate_batch({"items": cached}, expected_numbers)
    return generate_metadata(questions)


async def import_questions(questions: list[Any], metadata: list[dict[str, Any]]) -> None:
    metadata_by_number = {item["question_no"]: item for item in metadata}
    async with AsyncSessionLocal() as session:
        async with session.begin():
            existing_topics = {topic.name_en: topic for topic in (await session.scalars(select(Topic))).all()}
            for sort_order, (name_en, (key, name_zh)) in enumerate(TOPIC_DEFINITIONS.items(), start=1):
                topic = existing_topics.get(name_en)
                if topic is None:
                    topic = Topic(key=key, name_en=name_en, name_zh=name_zh, sort_order=sort_order)
                    session.add(topic)
                    existing_topics[name_en] = topic
                else:
                    topic.key = key
                    topic.name_zh = name_zh
                    topic.sort_order = sort_order
            await session.flush()

            statement = select(Question).options(selectinload(Question.messages))
            existing_questions = {
                question.question_no: question for question in (await session.scalars(statement)).all()
            }
            for legacy in questions:
                item = metadata_by_number[legacy.question_no]
                question = existing_questions.get(legacy.question_no)
                if question is None:
                    question = Question(question_no=legacy.question_no)
                    session.add(question)
                question.source = QuestionSource.official
                question.topic = existing_topics[item["topic"]]
                question.exam_type = "classic"
                question.difficulty = "medium"
                question.summary = item["summary"]
                question.status = ReviewStatus.accepted
                question.avg_score = None
                question.word_count = sum(len(message.content.split()) for message in legacy.messages)
                question.messages.clear()
                question.messages.extend(
                    QuestionMessage(
                        speaker_role=message.speaker_role,
                        speaker_name=message.speaker_name,
                        content=message.content,
                        sort_order=message.sort_order,
                    )
                    for message in legacy.messages
                )


async def main(regenerate: bool) -> None:
    questions = load_legacy_questions(str(SOURCE_PATH))
    if not questions:
        raise RuntimeError(f"No questions parsed from {SOURCE_PATH}")
    metadata = load_or_generate_metadata(questions, regenerate)
    await import_questions(questions, metadata)
    print(f"Imported {len(questions)} questions and {sum(len(item.messages) for item in questions)} messages")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import the legacy TOEFL question bank into PostgreSQL")
    parser.add_argument("--regenerate", action="store_true", help="Regenerate DeepSeek metadata instead of using cache")
    args = parser.parse_args()
    asyncio.run(main(args.regenerate))
