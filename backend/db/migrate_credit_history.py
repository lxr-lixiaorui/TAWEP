import asyncio

from sqlalchemy import text

from backend.db.session import engine


STATEMENTS = [
    "ALTER TABLE credit_wallets ALTER COLUMN balance SET DEFAULT 45",
    "ALTER TABLE credit_wallets ALTER COLUMN weekly_limit SET DEFAULT 0",
    "ALTER TABLE credit_wallets ALTER COLUMN total_planned_credit SET DEFAULT 45",
    "UPDATE credit_wallets SET weekly_limit = 0, weekly_used = 0",
    "ALTER TABLE credit_ledger ADD COLUMN IF NOT EXISTS question_id uuid REFERENCES questions(id) ON DELETE SET NULL",
    "ALTER TABLE inbox_messages ADD COLUMN IF NOT EXISTS action_url varchar(300)",
    "ALTER TABLE inbox_messages ADD COLUMN IF NOT EXISTS action_label varchar(100)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_credit_ledger_question_reward ON credit_ledger (question_id, reason) WHERE question_id IS NOT NULL",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_credit_ledger_initial_credit ON credit_ledger (user_id, reason) WHERE reason = 'initial_credit'",
    """
    INSERT INTO credit_ledger (user_id, delta, reason, created_at)
    SELECT wallet.user_id, wallet.total_planned_credit, 'initial_credit', users.created_at
    FROM credit_wallets AS wallet
    JOIN users ON users.id = wallet.user_id
    WHERE NOT EXISTS (
        SELECT 1
        FROM credit_ledger AS ledger
        WHERE ledger.user_id = wallet.user_id
          AND ledger.reason = 'initial_credit'
    )
    """,
]


async def migrate() -> None:
    async with engine.begin() as connection:
        for statement in STATEMENTS:
            await connection.execute(text(statement))
    await engine.dispose()
    print("Credit history migration complete")


if __name__ == "__main__":
    asyncio.run(migrate())
