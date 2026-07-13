import asyncio

from sqlalchemy import text

from backend.db.session import engine


DDL = """
ALTER TABLE evaluation_reports
ADD COLUMN IF NOT EXISTS rewrite_comparison jsonb NOT NULL DEFAULT '{}'::jsonb
"""


async def main() -> None:
    async with engine.begin() as connection:
        await connection.execute(text(DDL))
    print("Rewrite comparison schema is ready")


if __name__ == "__main__":
    asyncio.run(main())
