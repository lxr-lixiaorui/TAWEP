import asyncio

from sqlalchemy import text

from backend.db.session import engine


DDL = """
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
)
"""


async def main() -> None:
    async with engine.begin() as connection:
        await connection.execute(text(DDL))
        await connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_evaluation_jobs_claim "
                "ON evaluation_jobs (status, next_attempt_at, created_at)"
            )
        )
    print("Evaluation job schema is ready")


if __name__ == "__main__":
    asyncio.run(main())
