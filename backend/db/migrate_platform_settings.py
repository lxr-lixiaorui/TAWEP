import asyncio
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import text

from backend.db.session import engine


STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS platform_settings (
        key varchar(120) PRIMARY KEY,
        value jsonb NOT NULL DEFAULT '{}'::jsonb,
        updated_by uuid REFERENCES users(id) ON DELETE SET NULL,
        updated_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    INSERT INTO platform_settings (key, value)
    VALUES ('legal.cross_border', '{"visible": false, "activation": 0, "consent_version": null}'::jsonb)
    ON CONFLICT (key) DO NOTHING
    """,
]


async def migrate() -> None:
    async with engine.begin() as connection:
        for statement in STATEMENTS:
            await connection.execute(text(statement))
    await engine.dispose()
    print("Platform settings migration complete")


if __name__ == "__main__":
    asyncio.run(migrate())
