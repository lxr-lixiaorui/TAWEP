import argparse
import asyncio
from getpass import getpass
from os import getenv

from sqlalchemy import update

from backend.db.session import AsyncSessionLocal, engine
from backend.models import AuthSession, User, UserRole, UserStatus
from backend.services.authentication import hash_password, normalize_email, now_utc
from backend.services.practice import ensure_user_wallet


async def main(email: str, alias: str, password: str) -> None:
    normalized_email = normalize_email(email)
    async with AsyncSessionLocal() as db:
        async with db.begin():
            from sqlalchemy import select

            user = await db.scalar(select(User).where(User.email == normalized_email).with_for_update())
            if user is None:
                user = User(
                    email=normalized_email,
                    password_hash=hash_password(password),
                    alias=alias,
                    role=UserRole.admin,
                    status=UserStatus.active,
                    email_verified_at=now_utc(),
                    preferred_locale="zh",
                    theme="light",
                )
                db.add(user)
                await db.flush()
            else:
                user.password_hash = hash_password(password)
                user.alias = alias
                user.role = UserRole.admin
                user.status = UserStatus.active
                user.email_verified_at = user.email_verified_at or now_utc()
                user.password_changed_at = now_utc()
                user.token_version += 1
                await db.execute(
                    update(AuthSession)
                    .where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))
                    .values(revoked_at=now_utc())
                )
            await ensure_user_wallet(db, user.id)
    await engine.dispose()
    print(f"Administrator ready: {normalized_email}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create or reset a local TAWEP administrator")
    parser.add_argument("--email", required=True)
    parser.add_argument("--alias", default="TAWEP Administrator")
    args = parser.parse_args()
    admin_password = getenv("TAWEP_BOOTSTRAP_ADMIN_PASSWORD") or getpass("Administrator password: ")
    if len(admin_password) < 10:
        raise SystemExit("Administrator password must contain at least 10 characters")
    asyncio.run(main(args.email, args.alias, admin_password))
