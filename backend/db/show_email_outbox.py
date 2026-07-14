import argparse
import asyncio

from sqlalchemy import select

from backend.core.config import get_settings
from backend.db.session import AsyncSessionLocal, engine
from backend.models import EmailOutbox


async def main(recipient: str) -> None:
    if get_settings().app_env == "production":
        raise SystemExit("Email outbox previews are disabled in production")
    async with AsyncSessionLocal() as db:
        email = await db.scalar(
            select(EmailOutbox)
            .where(EmailOutbox.recipient_email == recipient.strip().lower())
            .order_by(EmailOutbox.created_at.desc())
        )
        if email is None:
            raise SystemExit(f"No queued email found for {recipient}")
        print(f"Template: {email.template_key}")
        print(f"Subject: {email.subject}")
        print(f"Status: {email.status}")
        action_url = (email.payload or {}).get("action_url")
        if action_url:
            print(f"Action URL: {action_url}")
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Show the latest development outbox email for one recipient")
    parser.add_argument("recipient")
    args = parser.parse_args()
    asyncio.run(main(args.recipient))
