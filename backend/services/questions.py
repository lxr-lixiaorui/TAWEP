from pathlib import Path
from re import sub

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from backend.models import (
    Question,
    QuestionMessage,
    QuestionSource,
    ReviewStatus,
    Topic,
    UploadedQuestionReview,
)
from backend.schemas import QuestionCreate
from backend.schemas import QuestionMessageOut, QuestionOut


TOPICS = [
    "Education",
    "Environment",
    "Policy",
    "Business",
    "Technology",
    "Consumer Behavior",
    "Health",
    "Culture",
    "Lifelong Learning",
]

EXAM_TYPES = {
    "classic": "Classic",
    "reform_2026": "26 Reform",
}

def _clean_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    lines = [line.strip() for line in path.read_text(encoding="utf-8", errors="replace").splitlines()]
    cleaned = []
    for line in lines:
        if not line:
            continue
        cleaned.append(line[:-1] if line.endswith(":") else line)
    return cleaned


def _summary_from_prompt(prompt: str) -> str:
    compact = sub(r"\s+", " ", prompt).strip()
    if "?" in compact:
        compact = compact.split("?")[0] + "?"
    return compact[:150]


def submission_summary(prompt: str) -> str:
    compact = sub(r"\s+", " ", prompt).strip()
    questions = [part.strip() for part in compact.split("?") if part.strip()]
    if "?" in compact and questions:
        compact = f"{questions[-1]}?"
    return compact[:240]


async def resolve_topic(session: AsyncSession, topic_value: str) -> Topic | None:
    normalized = topic_value.strip().lower()
    return await session.scalar(
        select(Topic).where(
            (func.lower(Topic.name_en) == normalized) | (func.lower(Topic.key) == normalized)
        )
    )


async def next_question_number(session: AsyncSession) -> int:
    await session.execute(text("SELECT pg_advisory_xact_lock(72649301)"))
    current = await session.scalar(select(func.max(Question.question_no)))
    return int(current or 0) + 1


def apply_question_messages(question: Question, payload: QuestionCreate) -> None:
    values = {
        "professor": (payload.professor_name.strip(), payload.professor_content.strip(), 1),
        "student_a": (payload.student_a_name.strip(), payload.student_a_content.strip(), 2),
        "student_b": (payload.student_b_name.strip(), payload.student_b_content.strip(), 3),
    }
    existing = {message.speaker_role: message for message in question.messages}
    for role, (name, content, sort_order) in values.items():
        message = existing.get(role)
        if message is None:
            question.messages.append(
                QuestionMessage(
                    speaker_role=role,
                    speaker_name=name,
                    content=content,
                    sort_order=sort_order,
                )
            )
        else:
            message.speaker_name = name
            message.content = content
            message.sort_order = sort_order
    question.word_count = sum(len(content.split()) for _, content, _ in values.values())


async def create_uploaded_question(
    session: AsyncSession,
    creator_user_id,
    payload: QuestionCreate,
) -> Question:
    topic = await resolve_topic(session, payload.topic)
    if topic is None:
        raise ValueError("Unknown topic")
    question = Question(
        question_no=await next_question_number(session),
        source=QuestionSource.user,
        creator_user_id=creator_user_id,
        topic_id=topic.id,
        exam_type=payload.exam_type,
        difficulty=payload.difficulty,
        summary=submission_summary(payload.professor_content),
        status=ReviewStatus.pending,
        messages=[],
    )
    apply_question_messages(question, payload)
    session.add(question)
    await session.flush()
    session.add(UploadedQuestionReview(question_id=question.id, status=ReviewStatus.pending))
    return question


def load_legacy_questions(path: str = "static/table/2023_AcaTalk.txt") -> list[QuestionOut]:
    lines = _clean_lines(Path(path))
    questions: list[QuestionOut] = []
    for index in range(0, len(lines) - 5, 6):
        group = lines[index : index + 6]
        question_no = len(questions) + 1
        topic = TOPICS[(question_no - 1) % len(TOPICS)]
        professor_name, professor_content, student_a_name, student_a_content, student_b_name, student_b_content = group
        messages = [
            QuestionMessageOut(
                speaker_role="professor",
                speaker_name=professor_name,
                content=professor_content,
                sort_order=1,
            ),
            QuestionMessageOut(
                speaker_role="student_a",
                speaker_name=student_a_name,
                content=student_a_content,
                sort_order=2,
            ),
            QuestionMessageOut(
                speaker_role="student_b",
                speaker_name=student_b_name,
                content=student_b_content,
                sort_order=3,
            ),
        ]
        word_count = sum(len(message.content.split()) for message in messages)
        questions.append(
            QuestionOut(
                question_no=question_no,
                source="official",
                topic=topic,
                exam_type="classic",
                difficulty=["easy", "medium", "hard"][question_no % 3],
                summary=_summary_from_prompt(professor_content),
                avg_score=round(3.2 + (question_no % 14) / 10, 1),
                word_count=word_count,
                messages=messages,
            )
        )
    return questions


def filter_questions(
    difficulty: str | None = None,
    source: str | None = None,
    topic: str | None = None,
    exam_type: str | None = None,
) -> list[QuestionOut]:
    questions = load_legacy_questions()
    if difficulty:
        questions = [item for item in questions if item.difficulty == difficulty]
    if source:
        questions = [item for item in questions if item.source == source]
    if topic:
        questions = [item for item in questions if item.topic == topic]
    if exam_type:
        questions = [item for item in questions if item.exam_type == exam_type]
    return questions


def get_question_by_no(question_no: int) -> QuestionOut | None:
    return next((item for item in load_legacy_questions() if item.question_no == question_no), None)

def _question_out(question: Question) -> QuestionOut:
    return QuestionOut(
        id=question.id,
        question_no=question.question_no,
        source=question.source.value,
        topic=question.topic.name_en,
        exam_type=question.exam_type,
        difficulty=question.difficulty,
        summary=question.summary,
        avg_score=float(question.avg_score) if question.avg_score is not None else None,
        word_count=question.word_count,
        messages=[
            QuestionMessageOut(
                speaker_role=message.speaker_role,
                speaker_name=message.speaker_name,
                content=message.content,
                sort_order=message.sort_order,
            )
            for message in sorted(question.messages, key=lambda item: item.sort_order)
        ],
    )


def _question_statement():
    return select(Question).options(joinedload(Question.topic), selectinload(Question.messages))


async def filter_database_questions(
    session: AsyncSession,
    difficulty: str | None = None,
    source: str | None = None,
    topic: str | None = None,
    exam_type: str | None = None,
) -> list[QuestionOut]:
    statement = _question_statement().where(Question.status == ReviewStatus.accepted).order_by(Question.question_no)
    if difficulty:
        statement = statement.where(Question.difficulty == difficulty)
    if source:
        statement = statement.where(Question.source == source)
    if topic:
        statement = statement.join(Topic).where(Topic.name_en == topic)
    if exam_type:
        statement = statement.where(Question.exam_type == exam_type)
    questions = (await session.scalars(statement)).all()
    return [_question_out(question) for question in questions]


async def get_database_question_by_no(session: AsyncSession, question_no: int) -> QuestionOut | None:
    statement = _question_statement().where(
        Question.question_no == question_no,
        Question.status == ReviewStatus.accepted,
    )
    question = await session.scalar(statement)
    return _question_out(question) if question is not None else None


async def list_database_topics(session: AsyncSession) -> list[str]:
    statement = select(Topic.name_en).order_by(Topic.sort_order, Topic.name_en)
    return list((await session.scalars(statement)).all())


async def get_question_bank_stats(session: AsyncSession) -> tuple[int, int]:
    accepted = Question.status == ReviewStatus.accepted
    question_count = await session.scalar(select(func.count(Question.id)).where(accepted))
    topic_count = await session.scalar(
        select(func.count(func.distinct(Question.topic_id))).where(accepted)
    )
    return int(question_count or 0), int(topic_count or 0)
