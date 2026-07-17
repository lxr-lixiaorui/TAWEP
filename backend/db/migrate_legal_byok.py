import asyncio

from sqlalchemy import text

from backend.db.session import engine


STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS user_consent_events (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        consent_key varchar(80) NOT NULL,
        document_version varchar(40) NOT NULL,
        granted boolean NOT NULL,
        resource_type varchar(40),
        resource_id uuid,
        ip_address varchar(64),
        user_agent varchar(500),
        details jsonb NOT NULL DEFAULT '{}'::jsonb,
        created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_user_consent_events_user_id ON user_consent_events (user_id)",
    "CREATE INDEX IF NOT EXISTS ix_user_consent_events_key ON user_consent_events (consent_key)",
    """
    CREATE TABLE IF NOT EXISTS user_ai_configs (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id uuid UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        enabled boolean NOT NULL DEFAULT false,
        provider_name varchar(80) NOT NULL DEFAULT 'OpenAI-compatible',
        endpoint varchar(500) NOT NULL,
        model_name varchar(160) NOT NULL,
        encrypted_api_key text NOT NULL,
        key_last_four varchar(4) NOT NULL,
        consent_version varchar(40) NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_user_ai_configs_user_id ON user_ai_configs (user_id)",
    "ALTER TABLE evaluation_jobs ADD COLUMN IF NOT EXISTS api_source varchar(24) NOT NULL DEFAULT 'platform'",
    "ALTER TABLE evaluation_jobs ADD COLUMN IF NOT EXISTS ai_config_id uuid REFERENCES user_ai_configs(id) ON DELETE SET NULL",
]


async def migrate() -> None:
    async with engine.begin() as connection:
        for statement in STATEMENTS:
            await connection.execute(text(statement))
    await engine.dispose()
    print("Legal consent and personal API migration complete")


if __name__ == "__main__":
    asyncio.run(migrate())
