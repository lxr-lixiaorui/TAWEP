import asyncio

from sqlalchemy import text

from backend.db.session import engine


STATEMENTS = [
    """
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
    )
    """,
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_question_skill_profiles_question_id ON question_skill_profiles (question_id)",
]


async def migrate() -> None:
    async with engine.begin() as connection:
        for statement in STATEMENTS:
            await connection.execute(text(statement))
    await engine.dispose()
    print("Question skill profile migration complete")


if __name__ == "__main__":
    asyncio.run(migrate())
