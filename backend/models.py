import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import CITEXT, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class UserStatus(str, enum.Enum):
    active = "active"
    banned = "banned"
    pending = "pending"


class QuestionSource(str, enum.Enum):
    official = "official"
    user = "user"


class ReviewStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class SessionMode(str, enum.Enum):
    timed = "timed"
    unlimited = "unlimited"


class SessionStatus(str, enum.Enum):
    created = "created"
    in_progress = "in_progress"
    submitted = "submitted"
    evaluated = "evaluated"
    failed = "failed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_pk()
    email: Mapped[str] = mapped_column(CITEXT(), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    alias: Mapped[str] = mapped_column(String(80))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.user)
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.pending)
    preferred_locale: Mapped[str] = mapped_column(String(8), default="en")
    theme: Mapped[str] = mapped_column(String(16), default="light")
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    token_version: Mapped[int] = mapped_column(Integer, default=0)
    baseline_writing_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    planned_exam_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    exam_reminder_shown_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    wallet: Mapped["CreditWallet"] = relationship(back_populates="user", uselist=False, passive_deletes=True)


class UserConsentEvent(Base):
    __tablename__ = "user_consent_events"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    consent_key: Mapped[str] = mapped_column(String(80), index=True)
    document_version: Mapped[str] = mapped_column(String(40))
    granted: Mapped[bool] = mapped_column(Boolean)
    resource_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    details: Mapped[dict] = mapped_column(JSONB(), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class UserAIConfig(Base):
    __tablename__ = "user_ai_configs"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    provider_name: Mapped[str] = mapped_column(String(80), default="OpenAI-compatible")
    endpoint: Mapped[str] = mapped_column(String(500))
    model_name: Mapped[str] = mapped_column(String(160))
    encrypted_api_key: Mapped[str] = mapped_column(Text())
    key_last_four: Mapped[str] = mapped_column(String(4))
    consent_version: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    refresh_token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class AccountToken(Base):
    __tablename__ = "account_tokens"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    purpose: Mapped[str] = mapped_column(String(32), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class EmailOutbox(Base):
    __tablename__ = "email_outbox"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    recipient_email: Mapped[str] = mapped_column(CITEXT())
    template_key: Mapped[str] = mapped_column(String(64), index=True)
    locale: Mapped[str] = mapped_column(String(8), default="en")
    subject: Mapped[str] = mapped_column(String(200))
    payload: Mapped[dict] = mapped_column(JSONB(), default=dict)
    status: Mapped[str] = mapped_column(String(24), default="pending", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[uuid.UUID] = uuid_pk()
    key: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name_en: Mapped[str] = mapped_column(String(120))
    name_zh: Mapped[str] = mapped_column(String(120))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (UniqueConstraint("question_no", name="uq_questions_question_no"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    question_no: Mapped[int] = mapped_column(Integer, index=True)
    source: Mapped[QuestionSource] = mapped_column(Enum(QuestionSource), default=QuestionSource.official)
    creator_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    topic_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("topics.id"))
    exam_type: Mapped[str] = mapped_column(String(32), default="classic")
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    summary: Mapped[str] = mapped_column(String(240))
    status: Mapped[ReviewStatus] = mapped_column(Enum(ReviewStatus), default=ReviewStatus.accepted)
    avg_score: Mapped[float | None] = mapped_column(Numeric(4, 1), nullable=True)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    messages: Mapped[list["QuestionMessage"]] = relationship(back_populates="question", cascade="all, delete-orphan")
    skill_profile: Mapped["QuestionSkillProfile | None"] = relationship(
        back_populates="question", cascade="all, delete-orphan", uselist=False
    )
    topic: Mapped[Topic] = relationship()


class QuestionMessage(Base):
    __tablename__ = "question_messages"

    id: Mapped[uuid.UUID] = uuid_pk()
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"))
    speaker_role: Mapped[str] = mapped_column(String(40))
    speaker_name: Mapped[str] = mapped_column(String(120))
    content: Mapped[str] = mapped_column(Text())
    sort_order: Mapped[int] = mapped_column(Integer)

    question: Mapped[Question] = relationship(back_populates="messages")


class QuestionSkillProfile(Base):
    __tablename__ = "question_skill_profiles"
    __table_args__ = (UniqueConstraint("question_id", name="uq_question_skill_profiles_question_id"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
    constraint_density: Mapped[int] = mapped_column(Integer, default=3)
    scope_width: Mapped[int] = mapped_column(Integer, default=3)
    perspective_gap: Mapped[int] = mapped_column(Integer, default=3)
    position_relation: Mapped[str] = mapped_column(String(40), default="independent")
    reasoning_modes: Mapped[list] = mapped_column(JSONB(), default=list)
    stakeholder_count: Mapped[int] = mapped_column(Integer, default=2)
    argument_steps: Mapped[int] = mapped_column(Integer, default=3)
    abstractness: Mapped[int] = mapped_column(Integer, default=3)
    knowledge_load: Mapped[int] = mapped_column(Integer, default=2)
    lexical_load: Mapped[int] = mapped_column(Integer, default=3)
    content_opportunity: Mapped[float] = mapped_column(Numeric(3, 2), default=3)
    perspective_opportunity: Mapped[float] = mapped_column(Numeric(3, 2), default=3)
    structure_opportunity: Mapped[float] = mapped_column(Numeric(3, 2), default=3)
    annotation_source: Mapped[str] = mapped_column(String(32), default="heuristic")
    confidence: Mapped[float] = mapped_column(Numeric(3, 2), default=0.5)
    profile_version: Mapped[str] = mapped_column(String(40), default="v1")
    annotated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    question: Mapped[Question] = relationship(back_populates="skill_profile")


class UploadedQuestionReview(Base):
    __tablename__ = "uploaded_question_reviews"
    __table_args__ = (UniqueConstraint("question_id", name="uq_uploaded_question_reviews_question_id"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[ReviewStatus] = mapped_column(Enum(ReviewStatus), default=ReviewStatus.pending)
    comment: Mapped[str | None] = mapped_column(Text(), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AnswerSession(Base):
    __tablename__ = "answer_sessions"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questions.id"))
    mode: Mapped[SessionMode] = mapped_column(Enum(SessionMode))
    status: Mapped[SessionStatus] = mapped_column(Enum(SessionStatus), default=SessionStatus.created)
    time_limit_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    answer_text: Mapped[str] = mapped_column(Text(), default="")
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EvaluationJob(Base):
    __tablename__ = "evaluation_jobs"
    __table_args__ = (UniqueConstraint("session_id", name="uq_evaluation_jobs_session_id"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("answer_sessions.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(32), default="queued")
    stage: Mapped[str] = mapped_column(String(48), default="queued")
    report_locale: Mapped[str] = mapped_column(String(16), default="en")
    api_source: Mapped[str] = mapped_column(String(24), default="platform")
    ai_config_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("user_ai_configs.id", ondelete="SET NULL"), nullable=True
    )
    partial_result: Mapped[dict] = mapped_column(JSONB(), default=dict)
    attempt: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    estimated_min_seconds: Mapped[int] = mapped_column(Integer, default=120)
    estimated_max_seconds: Mapped[int] = mapped_column(Integer, default=210)
    worker_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class EvaluationReport(Base):
    __tablename__ = "evaluation_reports"
    __table_args__ = (UniqueConstraint("session_id", name="uq_evaluation_reports_session_id"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("answer_sessions.id", ondelete="CASCADE"))
    model_provider: Mapped[str] = mapped_column(String(80), default="deepseek")
    model_name: Mapped[str] = mapped_column(String(120))
    total_score: Mapped[float] = mapped_column(Numeric(4, 1))
    raw_response: Mapped[dict] = mapped_column(JSONB(), default=dict)
    rewrite_comparison: Mapped[dict] = mapped_column(JSONB(), default=dict)
    report_html_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ReportShare(Base):
    __tablename__ = "report_shares"

    id: Mapped[uuid.UUID] = uuid_pk()
    report_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evaluation_reports.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ReportFeedback(Base):
    __tablename__ = "report_feedback"
    __table_args__ = (UniqueConstraint("report_id", name="uq_report_feedback_report_id"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    report_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evaluation_reports.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    feedback_type: Mapped[str] = mapped_column(String(32), index=True)
    comment: Mapped[str | None] = mapped_column(Text(), nullable=True)
    consent_to_share: Mapped[bool] = mapped_column(Boolean, default=False)
    answer_snapshot: Mapped[str] = mapped_column(Text())
    report_snapshot: Mapped[dict] = mapped_column(JSONB(), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ScoreComponent(Base):
    __tablename__ = "score_components"
    __table_args__ = (UniqueConstraint("report_id", name="uq_score_components_report_id"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    report_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("evaluation_reports.id", ondelete="CASCADE"))
    content_relevance: Mapped[float] = mapped_column(Numeric(3, 1))
    perspective_expansion: Mapped[float] = mapped_column(Numeric(3, 1))
    linguistic_expression: Mapped[float] = mapped_column(Numeric(3, 1))
    logical_structure: Mapped[float] = mapped_column(Numeric(3, 1))


class GrammarAnalysisItem(Base):
    __tablename__ = "grammar_analysis_items"

    id: Mapped[uuid.UUID] = uuid_pk()
    report_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("evaluation_reports.id", ondelete="CASCADE"))
    sentence_index: Mapped[int] = mapped_column(Integer)
    occurrence_index: Mapped[int] = mapped_column(Integer, default=1)
    start_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    original_text: Mapped[str] = mapped_column(Text())
    issue_type: Mapped[str] = mapped_column(String(40))
    explanation: Mapped[str] = mapped_column(Text())
    suggestion: Mapped[str] = mapped_column(Text())


class LanguageMetricScore(Base):
    __tablename__ = "language_metric_scores"
    __table_args__ = (UniqueConstraint("report_id", "metric_key", name="uq_language_metric_report_key"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    report_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("evaluation_reports.id", ondelete="CASCADE"))
    metric_key: Mapped[str] = mapped_column(String(80))
    score: Mapped[float] = mapped_column(Numeric(3, 1))


class CreditWallet(Base):
    __tablename__ = "credit_wallets"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    balance: Mapped[int] = mapped_column(Integer, default=45)
    weekly_limit: Mapped[int] = mapped_column(Integer, default=0)
    weekly_used: Mapped[int] = mapped_column(Integer, default=0)
    weekly_window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    total_planned_credit: Mapped[int] = mapped_column(Integer, default=45)

    user: Mapped[User] = relationship(back_populates="wallet")


class CreditLedger(Base):
    __tablename__ = "credit_ledger"
    __table_args__ = (UniqueConstraint("session_id", "reason", name="uq_credit_ledger_session_reason"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    delta: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(120))
    session_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("answer_sessions.id", ondelete="CASCADE"), nullable=True)
    question_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("questions.id", ondelete="SET NULL"), nullable=True)
    admin_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class InboxMessage(Base):
    __tablename__ = "inbox_messages"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(Text())
    type: Mapped[str] = mapped_column(String(40), default="system")
    action_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    action_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class UserExamResult(Base):
    __tablename__ = "user_exam_results"
    __table_args__ = (UniqueConstraint("user_id", "exam_date", name="uq_user_exam_results_user_date"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    exam_date: Mapped[date] = mapped_column(Date)
    writing_score: Mapped[int] = mapped_column(Integer)
    baseline_writing_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    improvement: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class LegalDocument(Base):
    __tablename__ = "legal_documents"

    id: Mapped[uuid.UUID] = uuid_pk()
    slug: Mapped[str] = mapped_column(String(80), index=True)
    locale: Mapped[str] = mapped_column(String(8), default="en")
    version: Mapped[str] = mapped_column(String(40))
    content_html: Mapped[str] = mapped_column(Text())
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class PlatformSetting(Base):
    __tablename__ = "platform_settings"

    key: Mapped[str] = mapped_column(String(120), primary_key=True)
    value: Mapped[dict] = mapped_column(JSONB(), default=dict)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"

    id: Mapped[uuid.UUID] = uuid_pk()
    admin_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(120))
    target_type: Mapped[str] = mapped_column(String(80))
    target_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB(), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
