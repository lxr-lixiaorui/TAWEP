import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
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
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.active)
    preferred_locale: Mapped[str] = mapped_column(String(8), default="en")
    theme: Mapped[str] = mapped_column(String(16), default="light")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    wallet: Mapped["CreditWallet"] = relationship(back_populates="user", uselist=False)


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
    creator_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    topic_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("topics.id"))
    exam_type: Mapped[str] = mapped_column(String(32), default="classic")
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    summary: Mapped[str] = mapped_column(String(240))
    status: Mapped[ReviewStatus] = mapped_column(Enum(ReviewStatus), default=ReviewStatus.accepted)
    avg_score: Mapped[float | None] = mapped_column(Numeric(4, 1), nullable=True)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    messages: Mapped[list["QuestionMessage"]] = relationship(back_populates="question", cascade="all, delete-orphan")
    topic: Mapped[Topic] = relationship()


class QuestionMessage(Base):
    __tablename__ = "question_messages"

    id: Mapped[uuid.UUID] = uuid_pk()
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questions.id"))
    speaker_role: Mapped[str] = mapped_column(String(40))
    speaker_name: Mapped[str] = mapped_column(String(120))
    content: Mapped[str] = mapped_column(Text())
    sort_order: Mapped[int] = mapped_column(Integer)

    question: Mapped[Question] = relationship(back_populates="messages")


class UploadedQuestionReview(Base):
    __tablename__ = "uploaded_question_reviews"

    id: Mapped[uuid.UUID] = uuid_pk()
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questions.id"))
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[ReviewStatus] = mapped_column(Enum(ReviewStatus), default=ReviewStatus.pending)
    comment: Mapped[str | None] = mapped_column(Text(), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AnswerSession(Base):
    __tablename__ = "answer_sessions"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
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
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("answer_sessions.id"))
    status: Mapped[str] = mapped_column(String(32), default="queued")
    stage: Mapped[str] = mapped_column(String(48), default="queued")
    report_locale: Mapped[str] = mapped_column(String(16), default="en")
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
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("answer_sessions.id"))
    model_provider: Mapped[str] = mapped_column(String(80), default="deepseek")
    model_name: Mapped[str] = mapped_column(String(120))
    total_score: Mapped[float] = mapped_column(Numeric(4, 1))
    raw_response: Mapped[dict] = mapped_column(JSONB(), default=dict)
    rewrite_comparison: Mapped[dict] = mapped_column(JSONB(), default=dict)
    report_html_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ScoreComponent(Base):
    __tablename__ = "score_components"
    __table_args__ = (UniqueConstraint("report_id", name="uq_score_components_report_id"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    report_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("evaluation_reports.id"))
    content_relevance: Mapped[float] = mapped_column(Numeric(3, 1))
    perspective_expansion: Mapped[float] = mapped_column(Numeric(3, 1))
    linguistic_expression: Mapped[float] = mapped_column(Numeric(3, 1))
    logical_structure: Mapped[float] = mapped_column(Numeric(3, 1))


class GrammarAnalysisItem(Base):
    __tablename__ = "grammar_analysis_items"

    id: Mapped[uuid.UUID] = uuid_pk()
    report_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("evaluation_reports.id"))
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
    report_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("evaluation_reports.id"))
    metric_key: Mapped[str] = mapped_column(String(80))
    score: Mapped[float] = mapped_column(Numeric(3, 1))


class CreditWallet(Base):
    __tablename__ = "credit_wallets"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    balance: Mapped[int] = mapped_column(Integer, default=180)
    weekly_limit: Mapped[int] = mapped_column(Integer, default=60)
    weekly_used: Mapped[int] = mapped_column(Integer, default=0)
    weekly_window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    total_planned_credit: Mapped[int] = mapped_column(Integer, default=180)

    user: Mapped[User] = relationship(back_populates="wallet")


class CreditLedger(Base):
    __tablename__ = "credit_ledger"
    __table_args__ = (UniqueConstraint("session_id", "reason", name="uq_credit_ledger_session_reason"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    delta: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(120))
    session_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("answer_sessions.id"), nullable=True)
    admin_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class InboxMessage(Base):
    __tablename__ = "inbox_messages"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(Text())
    type: Mapped[str] = mapped_column(String(40), default="system")
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class LegalDocument(Base):
    __tablename__ = "legal_documents"

    id: Mapped[uuid.UUID] = uuid_pk()
    slug: Mapped[str] = mapped_column(String(80), index=True)
    locale: Mapped[str] = mapped_column(String(8), default="en")
    version: Mapped[str] = mapped_column(String(40))
    content_html: Mapped[str] = mapped_column(Text())
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"

    id: Mapped[uuid.UUID] = uuid_pk()
    admin_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(120))
    target_type: Mapped[str] = mapped_column(String(80))
    target_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB(), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
