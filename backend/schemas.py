from datetime import date, datetime
from typing import Literal
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
    email_verified_at: datetime | None = None
    baseline_writing_score: int | None = None
    planned_exam_date: date | None = None

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=128)
    captcha_token: str | None = None


class RegisterRequest(BaseModel):
    email: EmailStr
    alias: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=10, max_length=128)
    preferred_locale: str = Field(default="en", pattern="^(en|zh)$")
    baseline_writing_score: int | None = Field(default=None, ge=0, le=30)
    planned_exam_date: date | None = None
    terms_accepted: Literal[True]
    terms_version: str = Field(min_length=1, max_length=40)
    privacy_accepted: Literal[True]
    privacy_version: str = Field(min_length=1, max_length=40)
    cross_border_accepted: bool = False
    cross_border_version: str | None = Field(default=None, min_length=1, max_length=40)
    model_improvement_accepted: bool = False
    model_improvement_version: str = Field(min_length=1, max_length=40)


class EmailRequest(BaseModel):
    email: EmailStr
    preferred_locale: str = Field(default="en", pattern="^(en|zh)$")


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=32, max_length=256)


class PasswordResetRequest(BaseModel):
    token: str = Field(min_length=32, max_length=256)
    password: str = Field(min_length=10, max_length=128)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserPublic


class UserUpdate(BaseModel):
    alias: str | None = Field(default=None, min_length=1, max_length=80)
    preferred_locale: str | None = Field(default=None, pattern="^(en|zh)$")
    theme: str | None = Field(default=None, pattern="^(light|dark|system)$")


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=10, max_length=128)


class AccountDeleteRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    confirm_email: EmailStr


class UsageSummary(BaseModel):
    balance: int
    weekly_limit: int = 0
    weekly_used: int = 0
    total_planned_credit: int
    next_reset_at: datetime | None = None
    evaluation_cost: int
    can_start_evaluation: bool
    unavailable_reason: str | None = None
    personal_api_enabled: bool = False
    exam_discount_active: bool = False
    planned_exam_date: date | None = None


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
    messages: list[QuestionMessageOut] = Field(default_factory=list)


class QuestionBankStats(BaseModel):
    question_count: int
    topic_count: int


class QuestionSkillProfileOut(BaseModel):
    question_no: int
    constraint_density: int
    scope_width: int
    perspective_gap: int
    position_relation: str
    reasoning_modes: list[str]
    stakeholder_count: int
    argument_steps: int
    abstractness: int
    knowledge_load: int
    lexical_load: int
    content_opportunity: float
    perspective_opportunity: float
    structure_opportunity: float
    annotation_source: str
    confidence: float
    profile_version: str


class QuestionCreate(BaseModel):
    topic: str = Field(min_length=1, max_length=120)
    exam_type: str = Field(default="classic", pattern="^(classic|reform_2026)$")
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")
    student_a_name: str = Field(min_length=1, max_length=120)
    student_a_content: str = Field(min_length=10, max_length=5000)
    student_b_name: str = Field(min_length=1, max_length=120)
    student_b_content: str = Field(min_length=10, max_length=5000)
    professor_name: str = Field(min_length=1, max_length=120)
    professor_content: str = Field(min_length=20, max_length=5000)


class QuestionUploadCreate(QuestionCreate):
    exam_type: str = Field(pattern="^(classic|reform_2026)$")
    rights_confirmed: Literal[True]
    rights_statement_version: str = Field(min_length=1, max_length=40)


class LegalDocumentSummaryOut(BaseModel):
    slug: str
    title: str
    summary: str
    version: str


class LegalSectionOut(BaseModel):
    heading: str
    paragraphs: list[str] = Field(default_factory=list)
    bullets: list[str] = Field(default_factory=list)


class LegalDocumentOut(LegalDocumentSummaryOut):
    updated_at: str
    sections: list[LegalSectionOut]


class CrossBorderConfigOut(BaseModel):
    visible: bool
    consent_version: str | None = None
    activation: int = 0
    updated_at: datetime | None = None


class CrossBorderConfigUpdate(BaseModel):
    visible: bool


class RequiredCrossBorderConsentOut(BaseModel):
    visible: bool
    required: bool
    consent_version: str | None = None
    title: str | None = None
    summary: str | None = None


class RequiredConsentsOut(BaseModel):
    cross_border: RequiredCrossBorderConsentOut


class CrossBorderConsentCreate(BaseModel):
    accepted: Literal[True]
    version: str = Field(min_length=1, max_length=40)


class ConsentStatusOut(BaseModel):
    model_improvement: bool
    version: str


class ConsentUpdate(BaseModel):
    granted: bool
    version: str = Field(min_length=1, max_length=40)


class AIConfigOut(BaseModel):
    enabled: bool
    provider_name: str
    endpoint: str
    model_name: str
    key_configured: bool
    key_hint: str | None = None
    consent_version: str | None = None


class AIConfigUpdate(BaseModel):
    enabled: bool
    provider_name: str = Field(default="OpenAI-compatible", min_length=2, max_length=80)
    endpoint: str = Field(min_length=8, max_length=500)
    model_name: str = Field(min_length=1, max_length=160)
    api_key: str | None = Field(default=None, min_length=8, max_length=1000)
    third_party_ai_accepted: Literal[True]
    third_party_ai_version: str = Field(min_length=1, max_length=40)


class QuestionSubmissionOut(BaseModel):
    id: UUID
    question_no: int
    status: str
    message: str


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


class ReportShareOut(BaseModel):
    token: str
    path: str
    created_at: datetime


class ReportFeedbackCreate(BaseModel):
    feedback_type: str = Field(pattern="^(too_high|too_low|other)$")
    comment: str | None = Field(default=None, max_length=4000)
    consent_to_share: Literal[True]


class ReportFeedbackStatusOut(BaseModel):
    submitted: bool
    feedback_type: str | None = None
    created_at: datetime | None = None


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


class PublicReportOut(BaseModel):
    session: SessionOut
    question: QuestionOut
    report: ReportOut
    grammar: list[GrammarItemOut]
    owner_alias: str
    generated_at: datetime


class InboxMessageOut(BaseModel):
    id: UUID
    title: str
    body: str
    type: str
    action_url: str | None = None
    action_label: str | None = None
    read_at: datetime | None
    created_at: datetime


class ExamReminderOut(BaseModel):
    show: bool
    exam_date: date | None = None


class ExamReminderAcknowledge(BaseModel):
    locale: str = Field(default="en", pattern="^(en|zh)$")


class ExamResultCreate(BaseModel):
    exam_date: date
    writing_score: int = Field(ge=0, le=30)
    baseline_writing_score: int | None = Field(default=None, ge=0, le=30)


class ExamResultOut(BaseModel):
    id: UUID
    exam_date: date
    writing_score: int
    baseline_writing_score: int | None = None
    improvement: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExamOutcomeContext(BaseModel):
    baseline_writing_score: int | None = None
    planned_exam_date: date | None = None
    latest_result: ExamResultOut | None = None


class CreditLedgerOut(BaseModel):
    id: UUID
    delta: int
    reason: str
    session_id: UUID | None = None
    question_id: UUID | None = None
    created_at: datetime


class DashboardSummary(BaseModel):
    alias: str
    user_id: UUID
    average_score: float
    practice_count: int
    weekly_practice_count: int
    credit: UsageSummary


class RecommendationOut(BaseModel):
    question_no: int
    summary: str
    topic: str
    exam_type: str
    difficulty: str
    reason: str
    focus_dimension: str
    match_score: float


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


class AdminUserCreate(BaseModel):
    email: EmailStr
    alias: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=10, max_length=128)
    role: str = Field(default="user", pattern="^(user|admin)$")
    preferred_locale: str = Field(default="en", pattern="^(en|zh)$")


class AdminAccountDelete(BaseModel):
    confirm_email: EmailStr


class AdminCreditAdjustment(BaseModel):
    delta: int = Field(ge=-100000, le=100000)
    reason: str = Field(min_length=3, max_length=120)


class AdminAccountOut(BaseModel):
    id: UUID
    email: EmailStr
    alias: str
    role: str
    status: str
    credit: int
    email_verified_at: datetime | None
    created_at: datetime


class AdminReviewDecision(BaseModel):
    comment: str | None = Field(default=None, max_length=2000)


class AdminQuestionCreate(QuestionCreate):
    summary: str = Field(min_length=3, max_length=240)
    status: str = Field(default="accepted", pattern="^(accepted|rejected)$")


class AdminQuestionUpdate(BaseModel):
    topic: str | None = Field(default=None, min_length=1, max_length=120)
    exam_type: str | None = Field(default=None, pattern="^(classic|reform_2026)$")
    difficulty: str | None = Field(default=None, pattern="^(easy|medium|hard)$")
    summary: str | None = Field(default=None, min_length=3, max_length=240)
    status: str | None = Field(default=None, pattern="^(pending|accepted|rejected)$")
    student_a_name: str | None = Field(default=None, min_length=1, max_length=120)
    student_a_content: str | None = Field(default=None, min_length=10, max_length=5000)
    student_b_name: str | None = Field(default=None, min_length=1, max_length=120)
    student_b_content: str | None = Field(default=None, min_length=10, max_length=5000)
    professor_name: str | None = Field(default=None, min_length=1, max_length=120)
    professor_content: str | None = Field(default=None, min_length=20, max_length=5000)
    review_comment: str | None = Field(default=None, max_length=2000)


class AdminQuestionOut(BaseModel):
    id: UUID
    question_no: int
    source: str
    status: str
    topic: str
    topic_key: str
    exam_type: str
    difficulty: str
    summary: str
    avg_score: float | None
    word_count: int
    creator_id: UUID | None = None
    creator_alias: str | None = None
    creator_email: EmailStr | None = None
    session_count: int = 0
    messages: list[QuestionMessageOut] = Field(default_factory=list)
    created_at: datetime


class AdminQuestionReviewOut(BaseModel):
    review_id: UUID
    question: AdminQuestionOut
    reviewer_id: UUID | None = None
    reviewer_alias: str | None = None
    status: str
    comment: str | None = None
    reviewed_at: datetime | None = None


class AdminReportFeedbackOut(BaseModel):
    id: UUID
    session_id: UUID
    question_no: int
    user_id: UUID
    user_alias: str
    user_email: EmailStr
    feedback_type: str
    comment: str | None = None
    consent_to_share: bool
    answer_snapshot: str
    report_snapshot: dict
    total_score: float
    created_at: datetime


class AdminExamResultOut(BaseModel):
    id: UUID
    user_id: UUID
    user_alias: str
    user_email: EmailStr
    baseline_writing_score: int | None = None
    writing_score: int
    improvement: int | None = None
    exam_date: date
    submitted_at: datetime


class AdminEmailOutboxOut(BaseModel):
    id: UUID
    recipient_email: EmailStr
    template_key: str
    locale: str
    subject: str
    status: str
    attempts: int
    provider_message_id: str | None = None
    provider_event: str | None = None
    error_message: str | None = None
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    failed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class AdminInboundEmailOut(BaseModel):
    id: UUID
    provider_email_id: str
    sender_email: str
    to_addresses: list[str]
    subject: str
    route_key: str
    has_attachments: bool
    received_at: datetime
    created_at: datetime


class AdminInboundEmailDetail(AdminInboundEmailOut):
    cc_addresses: list[str]
    bcc_addresses: list[str]
    reply_to_addresses: list[str]
    text_body: str | None = None
    html_body: str | None = None
    headers: dict
    attachments: list[dict]
