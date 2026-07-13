CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole') THEN
        CREATE TYPE userrole AS ENUM ('user', 'admin');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userstatus') THEN
        CREATE TYPE userstatus AS ENUM ('active', 'banned', 'pending');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'questionsource') THEN
        CREATE TYPE questionsource AS ENUM ('official', 'user');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'reviewstatus') THEN
        CREATE TYPE reviewstatus AS ENUM ('pending', 'accepted', 'rejected');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sessionmode') THEN
        CREATE TYPE sessionmode AS ENUM ('timed', 'unlimited');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sessionstatus') THEN
        CREATE TYPE sessionstatus AS ENUM ('created', 'in_progress', 'submitted', 'evaluated', 'failed');
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email citext UNIQUE NOT NULL,
    password_hash varchar(255) NOT NULL,
    alias varchar(80) NOT NULL,
    role userrole NOT NULL DEFAULT 'user',
    status userstatus NOT NULL DEFAULT 'active',
    preferred_locale varchar(8) NOT NULL DEFAULT 'en',
    theme varchar(16) NOT NULL DEFAULT 'light',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);

CREATE TABLE IF NOT EXISTS topics (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    key varchar(80) UNIQUE NOT NULL,
    name_en varchar(120) NOT NULL,
    name_zh varchar(120) NOT NULL,
    sort_order integer NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS ix_topics_key ON topics (key);

CREATE TABLE IF NOT EXISTS questions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    question_no integer NOT NULL,
    source questionsource NOT NULL DEFAULT 'official',
    creator_user_id uuid REFERENCES users(id),
    topic_id uuid NOT NULL REFERENCES topics(id),
    exam_type varchar(32) NOT NULL DEFAULT 'classic',
    difficulty varchar(20) NOT NULL DEFAULT 'medium',
    summary varchar(240) NOT NULL,
    status reviewstatus NOT NULL DEFAULT 'accepted',
    avg_score numeric(4, 1),
    word_count integer NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_questions_question_no UNIQUE (question_no)
);

ALTER TABLE questions
    ADD COLUMN IF NOT EXISTS exam_type varchar(32) NOT NULL DEFAULT 'classic';

CREATE INDEX IF NOT EXISTS ix_questions_question_no ON questions (question_no);
CREATE INDEX IF NOT EXISTS ix_questions_exam_type ON questions (exam_type);

CREATE TABLE IF NOT EXISTS question_messages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id uuid NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    speaker_role varchar(40) NOT NULL,
    speaker_name varchar(120) NOT NULL,
    content text NOT NULL,
    sort_order integer NOT NULL
);

CREATE TABLE IF NOT EXISTS uploaded_question_reviews (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id uuid NOT NULL REFERENCES questions(id),
    reviewer_id uuid REFERENCES users(id),
    status reviewstatus NOT NULL DEFAULT 'pending',
    comment text,
    reviewed_at timestamptz
);

CREATE TABLE IF NOT EXISTS answer_sessions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id),
    question_id uuid NOT NULL REFERENCES questions(id),
    mode sessionmode NOT NULL,
    status sessionstatus NOT NULL DEFAULT 'created',
    time_limit_seconds integer,
    answer_text text NOT NULL DEFAULT '',
    word_count integer NOT NULL DEFAULT 0,
    started_at timestamptz NOT NULL DEFAULT now(),
    submitted_at timestamptz
);

CREATE TABLE IF NOT EXISTS evaluation_jobs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id uuid NOT NULL REFERENCES answer_sessions(id),
    status varchar(32) NOT NULL DEFAULT 'queued',
    stage varchar(48) NOT NULL DEFAULT 'queued',
    report_locale varchar(16) NOT NULL DEFAULT 'en',
    partial_result jsonb NOT NULL DEFAULT '{}'::jsonb,
    attempt integer NOT NULL DEFAULT 0,
    max_attempts integer NOT NULL DEFAULT 3,
    estimated_min_seconds integer NOT NULL DEFAULT 120,
    estimated_max_seconds integer NOT NULL DEFAULT 210,
    worker_id varchar(120),
    error_code varchar(80),
    error_message text,
    next_attempt_at timestamptz,
    heartbeat_at timestamptz,
    started_at timestamptz,
    completed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_evaluation_jobs_session_id UNIQUE (session_id),
    CONSTRAINT ck_evaluation_jobs_status CHECK (status IN ('queued', 'evaluating', 'retrying', 'completed', 'failed'))
);

CREATE INDEX IF NOT EXISTS ix_evaluation_jobs_claim
    ON evaluation_jobs (status, next_attempt_at, created_at);

CREATE TABLE IF NOT EXISTS evaluation_reports (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id uuid NOT NULL REFERENCES answer_sessions(id),
    model_provider varchar(80) NOT NULL DEFAULT 'deepseek',
    model_name varchar(120) NOT NULL,
    total_score numeric(4, 1) NOT NULL,
    raw_response jsonb NOT NULL DEFAULT '{}'::jsonb,
    rewrite_comparison jsonb NOT NULL DEFAULT '{}'::jsonb,
    report_html_path varchar(500),
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_evaluation_reports_session_id UNIQUE (session_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_evaluation_reports_session_id
    ON evaluation_reports (session_id);

CREATE TABLE IF NOT EXISTS score_components (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id uuid NOT NULL REFERENCES evaluation_reports(id),
    content_relevance numeric(3, 1) NOT NULL,
    perspective_expansion numeric(3, 1) NOT NULL,
    linguistic_expression numeric(3, 1) NOT NULL,
    logical_structure numeric(3, 1) NOT NULL,
    CONSTRAINT uq_score_components_report_id UNIQUE (report_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_score_components_report_id
    ON score_components (report_id);

CREATE TABLE IF NOT EXISTS grammar_analysis_items (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id uuid NOT NULL REFERENCES evaluation_reports(id),
    sentence_index integer NOT NULL,
    occurrence_index integer NOT NULL DEFAULT 1,
    start_offset integer,
    end_offset integer,
    original_text text NOT NULL,
    issue_type varchar(40) NOT NULL,
    explanation text NOT NULL,
    suggestion text NOT NULL
);

CREATE TABLE IF NOT EXISTS language_metric_scores (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id uuid NOT NULL REFERENCES evaluation_reports(id),
    metric_key varchar(80) NOT NULL,
    score numeric(3, 1) NOT NULL,
    CONSTRAINT uq_language_metric_report_key UNIQUE (report_id, metric_key)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_language_metric_report_key
    ON language_metric_scores (report_id, metric_key);

CREATE TABLE IF NOT EXISTS credit_wallets (
    user_id uuid PRIMARY KEY REFERENCES users(id),
    balance integer NOT NULL DEFAULT 180,
    weekly_limit integer NOT NULL DEFAULT 60,
    weekly_used integer NOT NULL DEFAULT 0,
    weekly_window_start timestamptz NOT NULL DEFAULT now(),
    total_planned_credit integer NOT NULL DEFAULT 180
);

CREATE TABLE IF NOT EXISTS credit_ledger (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id),
    delta integer NOT NULL,
    reason varchar(120) NOT NULL,
    session_id uuid REFERENCES answer_sessions(id),
    admin_id uuid REFERENCES users(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_credit_ledger_session_reason UNIQUE (session_id, reason)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_credit_ledger_session_reason
    ON credit_ledger (session_id, reason);

CREATE TABLE IF NOT EXISTS inbox_messages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id),
    title varchar(160) NOT NULL,
    body text NOT NULL,
    type varchar(40) NOT NULL DEFAULT 'system',
    read_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS legal_documents (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    slug varchar(80) NOT NULL,
    locale varchar(8) NOT NULL DEFAULT 'en',
    version varchar(40) NOT NULL,
    content_html text NOT NULL,
    active boolean NOT NULL DEFAULT true
);

CREATE INDEX IF NOT EXISTS ix_legal_documents_slug ON legal_documents (slug);

CREATE TABLE IF NOT EXISTS admin_audit_logs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id uuid NOT NULL REFERENCES users(id),
    action varchar(120) NOT NULL,
    target_type varchar(80) NOT NULL,
    target_id uuid,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);
