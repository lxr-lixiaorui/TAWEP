CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS schema_migrations (
    name varchar(160) PRIMARY KEY,
    checksum varchar(64) NOT NULL,
    applied_at timestamptz NOT NULL DEFAULT now()
);

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
    status userstatus NOT NULL DEFAULT 'pending',
    preferred_locale varchar(8) NOT NULL DEFAULT 'en',
    theme varchar(16) NOT NULL DEFAULT 'light',
    email_verified_at timestamptz,
    last_login_at timestamptz,
    password_changed_at timestamptz,
    token_version integer NOT NULL DEFAULT 0,
    baseline_writing_score integer CHECK (baseline_writing_score BETWEEN 0 AND 30),
    planned_exam_date date,
    exam_reminder_shown_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified_at timestamptz;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at timestamptz;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_changed_at timestamptz;
ALTER TABLE users ADD COLUMN IF NOT EXISTS token_version integer NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS baseline_writing_score integer;
ALTER TABLE users ADD COLUMN IF NOT EXISTS planned_exam_date date;
ALTER TABLE users ADD COLUMN IF NOT EXISTS exam_reminder_shown_at timestamptz;
ALTER TABLE users ALTER COLUMN status SET DEFAULT 'pending';

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_users_baseline_writing_score') THEN
        ALTER TABLE users ADD CONSTRAINT ck_users_baseline_writing_score
            CHECK (baseline_writing_score BETWEEN 0 AND 30);
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS auth_sessions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash varchar(64) UNIQUE NOT NULL,
    user_agent varchar(500),
    ip_address varchar(64),
    expires_at timestamptz NOT NULL,
    revoked_at timestamptz,
    last_used_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_auth_sessions_user_id ON auth_sessions (user_id);
CREATE INDEX IF NOT EXISTS ix_auth_sessions_refresh_token_hash ON auth_sessions (refresh_token_hash);

CREATE TABLE IF NOT EXISTS account_tokens (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    purpose varchar(32) NOT NULL,
    token_hash varchar(64) UNIQUE NOT NULL,
    expires_at timestamptz NOT NULL,
    consumed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_account_tokens_user_id ON account_tokens (user_id);
CREATE INDEX IF NOT EXISTS ix_account_tokens_purpose ON account_tokens (purpose);
CREATE INDEX IF NOT EXISTS ix_account_tokens_token_hash ON account_tokens (token_hash);

CREATE TABLE IF NOT EXISTS email_outbox (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid REFERENCES users(id) ON DELETE SET NULL,
    recipient_email citext NOT NULL,
    template_key varchar(64) NOT NULL,
    locale varchar(8) NOT NULL DEFAULT 'en',
    subject varchar(200) NOT NULL,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    status varchar(24) NOT NULL DEFAULT 'pending',
    attempts integer NOT NULL DEFAULT 0,
    provider_message_id varchar(120) UNIQUE,
    provider_event varchar(40),
    error_message text,
    next_attempt_at timestamptz,
    claimed_at timestamptz,
    sent_at timestamptz,
    delivered_at timestamptz,
    failed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_email_outbox_template_key ON email_outbox (template_key);
CREATE INDEX IF NOT EXISTS ix_email_outbox_status ON email_outbox (status);
CREATE INDEX IF NOT EXISTS ix_email_outbox_provider_message_id ON email_outbox (provider_message_id);
CREATE INDEX IF NOT EXISTS ix_email_outbox_next_attempt_at ON email_outbox (next_attempt_at);

CREATE TABLE IF NOT EXISTS email_webhook_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    svix_id varchar(120) UNIQUE NOT NULL,
    event_type varchar(80) NOT NULL,
    provider_email_id varchar(120),
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    processed_at timestamptz,
    error_message text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_email_webhook_events_svix_id ON email_webhook_events (svix_id);
CREATE INDEX IF NOT EXISTS ix_email_webhook_events_event_type ON email_webhook_events (event_type);
CREATE INDEX IF NOT EXISTS ix_email_webhook_events_provider_email_id ON email_webhook_events (provider_email_id);

CREATE TABLE IF NOT EXISTS inbound_emails (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_email_id varchar(120) UNIQUE NOT NULL,
    sender_email varchar(320) NOT NULL,
    to_addresses jsonb NOT NULL DEFAULT '[]'::jsonb,
    cc_addresses jsonb NOT NULL DEFAULT '[]'::jsonb,
    bcc_addresses jsonb NOT NULL DEFAULT '[]'::jsonb,
    reply_to_addresses jsonb NOT NULL DEFAULT '[]'::jsonb,
    subject varchar(500) NOT NULL DEFAULT '',
    text_body text,
    html_body text,
    headers jsonb NOT NULL DEFAULT '{}'::jsonb,
    attachments jsonb NOT NULL DEFAULT '[]'::jsonb,
    route_key varchar(32) NOT NULL DEFAULT 'unrouted',
    received_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_inbound_emails_provider_email_id ON inbound_emails (provider_email_id);
CREATE INDEX IF NOT EXISTS ix_inbound_emails_sender_email ON inbound_emails (sender_email);
CREATE INDEX IF NOT EXISTS ix_inbound_emails_route_key ON inbound_emails (route_key);

CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);

CREATE TABLE IF NOT EXISTS user_consent_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    consent_key varchar(80) NOT NULL,
    document_version varchar(40) NOT NULL,
    granted boolean NOT NULL,
    resource_type varchar(40),
    resource_id uuid,
    ip_address varchar(64),
    user_agent varchar(500),
    details jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_user_consent_events_user_id ON user_consent_events (user_id);
CREATE INDEX IF NOT EXISTS ix_user_consent_events_key ON user_consent_events (consent_key);

CREATE TABLE IF NOT EXISTS user_ai_configs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    enabled boolean NOT NULL DEFAULT false,
    provider_name varchar(80) NOT NULL DEFAULT 'OpenAI-compatible',
    endpoint varchar(500) NOT NULL,
    model_name varchar(160) NOT NULL,
    encrypted_api_key text NOT NULL,
    key_last_four varchar(4) NOT NULL,
    consent_version varchar(40) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_user_ai_configs_user_id ON user_ai_configs (user_id);

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
    creator_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
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
CREATE INDEX IF NOT EXISTS ix_questions_source_status ON questions (source, status);

CREATE TABLE IF NOT EXISTS question_messages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id uuid NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    speaker_role varchar(40) NOT NULL,
    speaker_name varchar(120) NOT NULL,
    content text NOT NULL,
    sort_order integer NOT NULL
);

CREATE TABLE IF NOT EXISTS question_skill_profiles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id uuid NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    constraint_density integer NOT NULL DEFAULT 3 CHECK (constraint_density BETWEEN 1 AND 5),
    scope_width integer NOT NULL DEFAULT 3 CHECK (scope_width BETWEEN 1 AND 5),
    perspective_gap integer NOT NULL DEFAULT 3 CHECK (perspective_gap BETWEEN 1 AND 5),
    position_relation varchar(40) NOT NULL DEFAULT 'independent',
    reasoning_modes jsonb NOT NULL DEFAULT '[]'::jsonb,
    stakeholder_count integer NOT NULL DEFAULT 2 CHECK (stakeholder_count BETWEEN 1 AND 5),
    argument_steps integer NOT NULL DEFAULT 3 CHECK (argument_steps BETWEEN 1 AND 5),
    abstractness integer NOT NULL DEFAULT 3 CHECK (abstractness BETWEEN 1 AND 5),
    knowledge_load integer NOT NULL DEFAULT 2 CHECK (knowledge_load BETWEEN 1 AND 5),
    lexical_load integer NOT NULL DEFAULT 3 CHECK (lexical_load BETWEEN 1 AND 5),
    content_opportunity numeric(3, 2) NOT NULL DEFAULT 3 CHECK (content_opportunity BETWEEN 1 AND 5),
    perspective_opportunity numeric(3, 2) NOT NULL DEFAULT 3 CHECK (perspective_opportunity BETWEEN 1 AND 5),
    structure_opportunity numeric(3, 2) NOT NULL DEFAULT 3 CHECK (structure_opportunity BETWEEN 1 AND 5),
    annotation_source varchar(32) NOT NULL DEFAULT 'heuristic',
    confidence numeric(3, 2) NOT NULL DEFAULT 0.5 CHECK (confidence BETWEEN 0 AND 1),
    profile_version varchar(40) NOT NULL DEFAULT 'v1',
    annotated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_question_skill_profiles_question_id UNIQUE (question_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_question_skill_profiles_question_id
    ON question_skill_profiles (question_id);

CREATE TABLE IF NOT EXISTS uploaded_question_reviews (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id uuid NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    reviewer_id uuid REFERENCES users(id) ON DELETE SET NULL,
    status reviewstatus NOT NULL DEFAULT 'pending',
    comment text,
    reviewed_at timestamptz,
    CONSTRAINT uq_uploaded_question_reviews_question_id UNIQUE (question_id)
);

CREATE INDEX IF NOT EXISTS ix_uploaded_question_reviews_question_id ON uploaded_question_reviews (question_id);
CREATE INDEX IF NOT EXISTS ix_uploaded_question_reviews_status ON uploaded_question_reviews (status);

CREATE TABLE IF NOT EXISTS answer_sessions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
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
    session_id uuid NOT NULL REFERENCES answer_sessions(id) ON DELETE CASCADE,
    status varchar(32) NOT NULL DEFAULT 'queued',
    stage varchar(48) NOT NULL DEFAULT 'queued',
    report_locale varchar(16) NOT NULL DEFAULT 'en',
    api_source varchar(24) NOT NULL DEFAULT 'platform',
    ai_config_id uuid REFERENCES user_ai_configs(id) ON DELETE SET NULL,
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

ALTER TABLE evaluation_jobs ADD COLUMN IF NOT EXISTS api_source varchar(24) NOT NULL DEFAULT 'platform';
ALTER TABLE evaluation_jobs ADD COLUMN IF NOT EXISTS ai_config_id uuid REFERENCES user_ai_configs(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS ix_evaluation_jobs_claim
    ON evaluation_jobs (status, next_attempt_at, created_at);

CREATE TABLE IF NOT EXISTS evaluation_reports (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id uuid NOT NULL REFERENCES answer_sessions(id) ON DELETE CASCADE,
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

CREATE TABLE IF NOT EXISTS report_shares (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id uuid NOT NULL REFERENCES evaluation_reports(id) ON DELETE CASCADE,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash varchar(64) UNIQUE NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    revoked_at timestamptz
);

CREATE INDEX IF NOT EXISTS ix_report_shares_report_id ON report_shares (report_id);
CREATE INDEX IF NOT EXISTS ix_report_shares_user_id ON report_shares (user_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_report_shares_token_hash ON report_shares (token_hash);
CREATE INDEX IF NOT EXISTS ix_report_shares_active_token
    ON report_shares (token_hash) WHERE revoked_at IS NULL;

CREATE TABLE IF NOT EXISTS report_feedback (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id uuid NOT NULL REFERENCES evaluation_reports(id) ON DELETE CASCADE,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feedback_type varchar(32) NOT NULL,
    comment text,
    consent_to_share boolean NOT NULL DEFAULT false,
    answer_snapshot text NOT NULL,
    report_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_report_feedback_report_id UNIQUE (report_id),
    CONSTRAINT ck_report_feedback_type CHECK (feedback_type IN ('too_high', 'too_low', 'other')),
    CONSTRAINT ck_report_feedback_consent CHECK (consent_to_share = true)
);

CREATE INDEX IF NOT EXISTS ix_report_feedback_report_id ON report_feedback (report_id);
CREATE INDEX IF NOT EXISTS ix_report_feedback_user_id ON report_feedback (user_id);
CREATE INDEX IF NOT EXISTS ix_report_feedback_type ON report_feedback (feedback_type);
CREATE INDEX IF NOT EXISTS ix_report_feedback_created_at ON report_feedback (created_at DESC);

CREATE TABLE IF NOT EXISTS score_components (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id uuid NOT NULL REFERENCES evaluation_reports(id) ON DELETE CASCADE,
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
    report_id uuid NOT NULL REFERENCES evaluation_reports(id) ON DELETE CASCADE,
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
    report_id uuid NOT NULL REFERENCES evaluation_reports(id) ON DELETE CASCADE,
    metric_key varchar(80) NOT NULL,
    score numeric(3, 1) NOT NULL,
    CONSTRAINT uq_language_metric_report_key UNIQUE (report_id, metric_key)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_language_metric_report_key
    ON language_metric_scores (report_id, metric_key);

CREATE TABLE IF NOT EXISTS credit_wallets (
    user_id uuid PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    balance integer NOT NULL DEFAULT 45,
    weekly_limit integer NOT NULL DEFAULT 0,
    weekly_used integer NOT NULL DEFAULT 0,
    weekly_window_start timestamptz NOT NULL DEFAULT now(),
    total_planned_credit integer NOT NULL DEFAULT 45
);

CREATE TABLE IF NOT EXISTS credit_ledger (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    delta integer NOT NULL,
    reason varchar(120) NOT NULL,
    session_id uuid REFERENCES answer_sessions(id) ON DELETE CASCADE,
    question_id uuid REFERENCES questions(id) ON DELETE SET NULL,
    admin_id uuid REFERENCES users(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_credit_ledger_session_reason UNIQUE (session_id, reason)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_credit_ledger_session_reason
    ON credit_ledger (session_id, reason);

CREATE UNIQUE INDEX IF NOT EXISTS uq_credit_ledger_question_reward
    ON credit_ledger (question_id, reason)
    WHERE question_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_credit_ledger_initial_credit
    ON credit_ledger (user_id, reason)
    WHERE reason = 'initial_credit';

CREATE TABLE IF NOT EXISTS inbox_messages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title varchar(160) NOT NULL,
    body text NOT NULL,
    type varchar(40) NOT NULL DEFAULT 'system',
    action_url varchar(300),
    action_label varchar(100),
    read_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_exam_results (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    exam_date date NOT NULL,
    writing_score integer NOT NULL CHECK (writing_score BETWEEN 0 AND 30),
    baseline_writing_score integer CHECK (baseline_writing_score BETWEEN 0 AND 30),
    improvement integer,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_user_exam_results_user_date UNIQUE (user_id, exam_date)
);

CREATE INDEX IF NOT EXISTS ix_user_exam_results_user_id ON user_exam_results (user_id);

CREATE TABLE IF NOT EXISTS legal_documents (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    slug varchar(80) NOT NULL,
    locale varchar(8) NOT NULL DEFAULT 'en',
    version varchar(40) NOT NULL,
    content_html text NOT NULL,
    active boolean NOT NULL DEFAULT true
);

CREATE INDEX IF NOT EXISTS ix_legal_documents_slug ON legal_documents (slug);

CREATE TABLE IF NOT EXISTS platform_settings (
    key varchar(120) PRIMARY KEY,
    value jsonb NOT NULL DEFAULT '{}'::jsonb,
    updated_by uuid REFERENCES users(id) ON DELETE SET NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO platform_settings (key, value)
VALUES ('legal.cross_border', '{"visible": false, "activation": 0, "consent_version": null}'::jsonb)
ON CONFLICT (key) DO NOTHING;

CREATE TABLE IF NOT EXISTS admin_audit_logs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id uuid REFERENCES users(id) ON DELETE SET NULL,
    action varchar(120) NOT NULL,
    target_type varchar(80) NOT NULL,
    target_id uuid,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);
