import asyncio

from sqlalchemy import text

from backend.db.session import engine


DDL = [
    "ALTER TABLE grammar_analysis_items "
    "ADD COLUMN IF NOT EXISTS occurrence_index integer NOT NULL DEFAULT 1",
    "ALTER TABLE grammar_analysis_items ADD COLUMN IF NOT EXISTS start_offset integer",
    "ALTER TABLE grammar_analysis_items ADD COLUMN IF NOT EXISTS end_offset integer",
]


async def main() -> None:
    async with engine.begin() as connection:
        for statement in DDL:
            await connection.execute(text(statement))
    print("Grammar annotation offsets are ready")


if __name__ == "__main__":
    asyncio.run(main())
