from backend.core.constants import DEMO_USER_EMAIL, DEMO_USER_ID
from backend.schemas import UserPublic


def get_current_user() -> UserPublic:
    return UserPublic(
        id=DEMO_USER_ID,
        email=DEMO_USER_EMAIL,
        alias="Demo Writer",
        role="user",
        status="active",
        preferred_locale="en",
        theme="light",
    )
