from datetime import datetime, timedelta
from uuid import UUID

from backend.schemas import UsageSummary, UserPublic


DEMO_USER_ID = UUID("00000000-0000-4000-8000-000000000001")


def get_current_user() -> UserPublic:
    return UserPublic(
        id=DEMO_USER_ID,
        email="demo@tawep.local",
        alias="Demo Writer",
        role="user",
        status="active",
        preferred_locale="en",
        theme="light",
    )


def demo_usage() -> UsageSummary:
    return UsageSummary(
        balance=180,
        weekly_limit=60,
        weekly_used=12,
        total_planned_credit=180,
        next_reset_at=datetime.utcnow() + timedelta(days=4),
    )
