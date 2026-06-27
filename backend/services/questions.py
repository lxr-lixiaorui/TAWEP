from pathlib import Path
from re import sub

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
) -> list[QuestionOut]:
    questions = load_legacy_questions()
    if difficulty:
        questions = [item for item in questions if item.difficulty == difficulty]
    if source:
        questions = [item for item in questions if item.source == source]
    if topic:
        questions = [item for item in questions if item.topic == topic]
    return questions


def get_question_by_no(question_no: int) -> QuestionOut | None:
    return next((item for item in load_legacy_questions() if item.question_no == question_no), None)
