import asyncio

from sqlalchemy import text

from backend.db.session import engine


DDL_STATEMENTS = [
    """
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
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_report_feedback_report_id ON report_feedback (report_id)",
    "CREATE INDEX IF NOT EXISTS ix_report_feedback_user_id ON report_feedback (user_id)",
    "CREATE INDEX IF NOT EXISTS ix_report_feedback_type ON report_feedback (feedback_type)",
    "CREATE INDEX IF NOT EXISTS ix_report_feedback_created_at ON report_feedback (created_at DESC)",
]


async def main() -> None:
    async with engine.begin() as connection:
        for statement in DDL_STATEMENTS:
            await connection.execute(text(statement))
    await engine.dispose()
    print("Report feedback schema is ready")


if __name__ == "__main__":
    asyncio.run(main())
