import asyncio

from sqlalchemy import text

from backend.db.session import engine


DDL_STATEMENTS = [
    "ALTER TABLE email_outbox ADD COLUMN IF NOT EXISTS provider_message_id varchar(120)",
    "ALTER TABLE email_outbox ADD COLUMN IF NOT EXISTS provider_event varchar(40)",
    "ALTER TABLE email_outbox ADD COLUMN IF NOT EXISTS next_attempt_at timestamptz",
    "ALTER TABLE email_outbox ADD COLUMN IF NOT EXISTS claimed_at timestamptz",
    "ALTER TABLE email_outbox ADD COLUMN IF NOT EXISTS delivered_at timestamptz",
    "ALTER TABLE email_outbox ADD COLUMN IF NOT EXISTS failed_at timestamptz",
    "ALTER TABLE email_outbox ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now()",
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_email_outbox_provider_message_id ON email_outbox (provider_message_id)",
    "CREATE INDEX IF NOT EXISTS ix_email_outbox_next_attempt_at ON email_outbox (next_attempt_at)",
    """
    CREATE TABLE IF NOT EXISTS email_webhook_events (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        svix_id varchar(120) UNIQUE NOT NULL,
        event_type varchar(80) NOT NULL,
        provider_email_id varchar(120),
        payload jsonb NOT NULL DEFAULT '{}'::jsonb,
        processed_at timestamptz,
        error_message text,
        created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_email_webhook_events_svix_id ON email_webhook_events (svix_id)",
    "CREATE INDEX IF NOT EXISTS ix_email_webhook_events_event_type ON email_webhook_events (event_type)",
    "CREATE INDEX IF NOT EXISTS ix_email_webhook_events_provider_email_id ON email_webhook_events (provider_email_id)",
    """
    CREATE TABLE IF NOT EXISTS inbound_emails (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        provider_email_id varchar(120) UNIQUE NOT NULL,
        sender_email varchar(320) NOT NULL,
        to_addresses jsonb NOT NULL DEFAULT '[]'::jsonb,
        cc_addresses jsonb NOT NULL DEFAULT '[]'::jsonb,
        bcc_addresses jsonb NOT NULL DEFAULT '[]'::jsonb,
        reply_to_addresses jsonb NOT NULL DEFAULT '[]'::jsonb,
        subject varchar(500) NOT NULL DEFAULT '',
        text_body text,
        html_body text,
        headers jsonb NOT NULL DEFAULT '{}'::jsonb,
        attachments jsonb NOT NULL DEFAULT '[]'::jsonb,
        route_key varchar(32) NOT NULL DEFAULT 'unrouted',
        received_at timestamptz NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_inbound_emails_provider_email_id ON inbound_emails (provider_email_id)",
    "CREATE INDEX IF NOT EXISTS ix_inbound_emails_sender_email ON inbound_emails (sender_email)",
    "CREATE INDEX IF NOT EXISTS ix_inbound_emails_route_key ON inbound_emails (route_key)",
]


async def main() -> None:
    async with engine.begin() as connection:
        for statement in DDL_STATEMENTS:
            await connection.execute(text(statement))
    await engine.dispose()
    print("Resend email schema is ready")


if __name__ == "__main__":
    asyncio.run(main())
