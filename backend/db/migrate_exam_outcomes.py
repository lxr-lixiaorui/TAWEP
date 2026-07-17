import asyncio
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import text

from backend.db.session import engine


STATEMENTS = [
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS baseline_writing_score integer",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS planned_exam_date date",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS exam_reminder_shown_at timestamptz",
    """
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_users_baseline_writing_score') THEN
            ALTER TABLE users ADD CONSTRAINT ck_users_baseline_writing_score
                CHECK (baseline_writing_score BETWEEN 0 AND 30);
        END IF;
    END $$
    """,
    """
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
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_user_exam_results_user_id ON user_exam_results (user_id)",
]


async def migrate() -> None:
    async with engine.begin() as connection:
        for statement in STATEMENTS:
            await connection.execute(text(statement))
    await engine.dispose()
    print("Exam outcomes migration complete")


if __name__ == "__main__":
    asyncio.run(migrate())
