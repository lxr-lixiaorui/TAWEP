import asyncio

from sqlalchemy import text

from backend.db.session import engine


DDL_STATEMENTS = [
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified_at timestamptz",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at timestamptz",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_changed_at timestamptz",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS token_version integer NOT NULL DEFAULT 0",
    "ALTER TABLE users ALTER COLUMN status SET DEFAULT 'pending'",
    """
    CREATE TABLE IF NOT EXISTS auth_sessions (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        refresh_token_hash varchar(64) UNIQUE NOT NULL,
        user_agent varchar(500),
        ip_address varchar(64),
        expires_at timestamptz NOT NULL,
        revoked_at timestamptz,
        last_used_at timestamptz,
        created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_auth_sessions_user_id ON auth_sessions (user_id)",
    "CREATE INDEX IF NOT EXISTS ix_auth_sessions_refresh_token_hash ON auth_sessions (refresh_token_hash)",
    """
    CREATE TABLE IF NOT EXISTS account_tokens (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        purpose varchar(32) NOT NULL,
        token_hash varchar(64) UNIQUE NOT NULL,
        expires_at timestamptz NOT NULL,
        consumed_at timestamptz,
        created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_account_tokens_user_id ON account_tokens (user_id)",
    "CREATE INDEX IF NOT EXISTS ix_account_tokens_purpose ON account_tokens (purpose)",
    "CREATE INDEX IF NOT EXISTS ix_account_tokens_token_hash ON account_tokens (token_hash)",
    """
    CREATE TABLE IF NOT EXISTS email_outbox (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id uuid REFERENCES users(id) ON DELETE SET NULL,
        recipient_email citext NOT NULL,
        template_key varchar(64) NOT NULL,
        locale varchar(8) NOT NULL DEFAULT 'en',
        subject varchar(200) NOT NULL,
        payload jsonb NOT NULL DEFAULT '{}'::jsonb,
        status varchar(24) NOT NULL DEFAULT 'pending',
        attempts integer NOT NULL DEFAULT 0,
        error_message text,
        sent_at timestamptz,
        created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_email_outbox_template_key ON email_outbox (template_key)",
    "CREATE INDEX IF NOT EXISTS ix_email_outbox_status ON email_outbox (status)",
    "UPDATE users SET email_verified_at = created_at WHERE status = 'active' AND email_verified_at IS NULL",
]


async def main() -> None:
    async with engine.begin() as connection:
        for statement in DDL_STATEMENTS:
            await connection.execute(text(statement))
    await engine.dispose()
    print("Authentication schema is ready")


if __name__ == "__main__":
    asyncio.run(main())
