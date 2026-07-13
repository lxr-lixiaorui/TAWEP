from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class APIMessage(BaseModel):
    message: str


class UserPublic(BaseModel):
    id: UUID
    email: EmailStr
    alias: str
    role: str
    status: str
    preferred_locale: str
    theme: str

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    identifier: str
    password: str
    captcha_token: str | None = None


class RegisterRequest(BaseModel):
    email: EmailStr
    alias: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class UserUpdate(BaseModel):
    alias: str | None = Field(default=None, min_length=1, max_length=80)
    preferred_locale: str | None = Field(default=None, pattern="^(en|zh)$")
    theme: str | None = Field(default=None, pattern="^(light|dark|system)$")


class UsageSummary(BaseModel):
    balance: int
    weekly_limit: int
    weekly_used: int
    total_planned_credit: int
    next_reset_at: datetime


class TopicOut(BaseModel):
    key: str
    name_en: str
    name_zh: str


class QuestionMessageOut(BaseModel):
    speaker_role: str
    speaker_name: str
    content: str
    sort_order: int


class QuestionOut(BaseModel):
    id: UUID | None = None
    question_no: int
    source: str
    topic: str
    exam_type: str = "classic"
    difficulty: str
    summary: str
    avg_score: float | None = None
    word_count: int
    messages: list[QuestionMessageOut] = []


class QuestionCreate(BaseModel):
    topic: str
    difficulty: str = "medium"
    student_a_name: str
    student_a_content: str
    student_b_name: str
    student_b_content: str
    professor_name: str
    professor_content: str


class SessionCreate(BaseModel):
    mode: str = Field(pattern="^(timed|unlimited)$")


class AnswerUpdate(BaseModel):
    answer_text: str


class SubmitAnswer(BaseModel):
    answer_text: str
    report_locale: str = Field(default="en", min_length=2, max_length=16, pattern="^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})?$")


class SessionOut(BaseModel):
    id: UUID
    question_no: int
    mode: str
    status: str
    time_limit_seconds: int | None
    answer_text: str
    started_at: datetime
    submitted_at: datetime | None = None


class ScoreComponentsOut(BaseModel):
    content_relevance: float
    perspective_expansion: float
    linguistic_expression: float
    logical_structure: float


class ReportOut(BaseModel):
    session_id: UUID
    total_score: float
    total_score_30: int
    components: ScoreComponentsOut
    problems: dict[str, str]
    improvements: dict[str, str]
    ai_rewrite: str
    rewrite_comparison: dict = Field(default_factory=dict)
    report_html_url: str | None = None


class EvaluationJobOut(BaseModel):
    id: UUID
    session_id: UUID
    status: str
    stage: str
    report_locale: str
    available_sections: list[str]
    partial_report: dict
    elapsed_seconds: int
    estimated_min_seconds: int
    estimated_max_seconds: int
    attempt: int
    max_attempts: int
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class GrammarItemOut(BaseModel):
    sentence_index: int
    occurrence_index: int = 1
    start_offset: int | None = None
    end_offset: int | None = None
    original_text: str
    issue_type: str
    explanation: str
    suggestion: str


class InboxMessageOut(BaseModel):
    id: UUID
    title: str
    body: str
    type: str
    read_at: datetime | None
    created_at: datetime


class DashboardSummary(BaseModel):
    alias: str
    user_id: UUID
    average_score: float
    practice_count: int
    credit: UsageSummary


class RecommendationOut(BaseModel):
    question_no: int
    summary: str
    topic: str
    reason: str


class BreakdownPoint(BaseModel):
    submitted_at: datetime
    content_relevance: float
    perspective_expansion: float
    linguistic_expression: float
    logical_structure: float


class MatrixRow(BaseModel):
    topic: str
    content_relevance: float
    perspective_expansion: float
    linguistic_expression: float
    logical_structure: float


class AdminAccountAction(BaseModel):
    comment: str | None = None


class AdminMessageCreate(BaseModel):
    title: str
    body: str
