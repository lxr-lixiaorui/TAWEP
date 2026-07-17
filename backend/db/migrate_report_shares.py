import asyncio

from sqlalchemy import text

from backend.db.session import engine


STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS report_shares (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        report_id uuid NOT NULL REFERENCES evaluation_reports(id) ON DELETE CASCADE,
        user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        token_hash varchar(64) UNIQUE NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now(),
        revoked_at timestamptz
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_report_shares_report_id ON report_shares (report_id)",
    "CREATE INDEX IF NOT EXISTS ix_report_shares_user_id ON report_shares (user_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_report_shares_token_hash ON report_shares (token_hash)",
    "CREATE INDEX IF NOT EXISTS ix_report_shares_active_token ON report_shares (token_hash) WHERE revoked_at IS NULL",
]


async def migrate() -> None:
    async with engine.begin() as connection:
        for statement in STATEMENTS:
            await connection.execute(text(statement))
    await engine.dispose()
    print("Report share migration complete")


if __name__ == "__main__":
    asyncio.run(migrate())
