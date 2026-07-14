import asyncio

from sqlalchemy import text

from backend.db.session import engine


DDL_STATEMENTS = [
    """
    DELETE FROM uploaded_question_reviews older
    USING uploaded_question_reviews newer
    WHERE older.question_id = newer.question_id
      AND older.id < newer.id
    """,
    "ALTER TABLE uploaded_question_reviews DROP CONSTRAINT IF EXISTS uploaded_question_reviews_question_id_fkey",
    """
    ALTER TABLE uploaded_question_reviews
    ADD CONSTRAINT uploaded_question_reviews_question_id_fkey
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
    """,
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'uq_uploaded_question_reviews_question_id'
        ) THEN
            ALTER TABLE uploaded_question_reviews
            ADD CONSTRAINT uq_uploaded_question_reviews_question_id UNIQUE (question_id);
        END IF;
    END $$
    """,
    "CREATE INDEX IF NOT EXISTS ix_uploaded_question_reviews_question_id ON uploaded_question_reviews (question_id)",
    "CREATE INDEX IF NOT EXISTS ix_uploaded_question_reviews_status ON uploaded_question_reviews (status)",
    "CREATE INDEX IF NOT EXISTS ix_questions_source_status ON questions (source, status)",
]


async def main() -> None:
    async with engine.begin() as connection:
        for statement in DDL_STATEMENTS:
            await connection.execute(text(statement))
    await engine.dispose()
    print("Question moderation schema is ready")


if __name__ == "__main__":
    asyncio.run(main())
