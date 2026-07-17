import argparse
import asyncio
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import asyncpg
from sqlalchemy import func, select

from backend.core.config import get_settings


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "backend" / "db" / "schema.sql"
MIGRATION_MODULES = (
    "backend.db.migrate_rewrite_comparison",
    "backend.db.migrate_grammar_offsets",
    "backend.db.migrate_evaluation_jobs",
    "backend.db.migrate_auth",
    "backend.db.migrate_admin_accounts",
    "backend.db.migrate_question_moderation",
    "backend.db.migrate_report_feedback",
    "backend.db.migrate_legal_byok",
    "backend.db.migrate_report_shares",
    "backend.db.migrate_credit_history",
    "backend.db.migrate_question_skill_profiles",
    "backend.db.migrate_exam_outcomes",
    "backend.db.migrate_platform_settings",
    "backend.db.migrate_practice_persistence",
    "backend.db.migrate_resend_email",
)


def _asyncpg_dsn() -> str:
    database_url = get_settings().database_url
    if database_url.startswith("postgresql+asyncpg://"):
        return "postgresql://" + database_url.removeprefix("postgresql+asyncpg://")
    if database_url.startswith("postgres://") or database_url.startswith("postgresql://"):
        return database_url
    raise RuntimeError("DATABASE_URL must use a PostgreSQL URL")


def _module_path(module: str) -> Path:
    return ROOT / Path(*module.split(".")).with_suffix(".py")


def _checksum(module: str) -> str:
    return hashlib.sha256(_module_path(module).read_bytes()).hexdigest()


async def _apply_schema(connection: asyncpg.Connection) -> None:
    await connection.execute(SCHEMA_PATH.read_text(encoding="utf-8-sig"))
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            name varchar(160) PRIMARY KEY,
            checksum varchar(64) NOT NULL,
            applied_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )


async def _apply_migrations(connection: asyncpg.Connection) -> tuple[int, int]:
    applied = 0
    skipped = 0
    for module in MIGRATION_MODULES:
        checksum = _checksum(module)
        existing = await connection.fetchrow(
            "SELECT checksum FROM schema_migrations WHERE name = $1",
            module,
        )
        if existing is not None:
            if existing["checksum"] != checksum:
                raise RuntimeError(
                    f"Applied migration {module} has changed. Add a new migration instead of editing an applied one."
                )
            skipped += 1
            continue
        print(f"Applying {module}...", flush=True)
        subprocess.run(
            [sys.executable, "-m", module],
            cwd=ROOT,
            check=True,
        )
        await connection.execute(
            "INSERT INTO schema_migrations (name, checksum) VALUES ($1, $2)",
            module,
            checksum,
        )
        applied += 1
    return applied, skipped


async def _verify_database(expected_questions: int | None) -> None:
    from backend.db.question_seed import SEED_PATH
    from backend.db.session import AsyncSessionLocal, engine
    from backend.models import Question, ReviewStatus

    required_tables = {
        "users",
        "topics",
        "questions",
        "question_messages",
        "answer_sessions",
        "evaluation_reports",
        "grammar_analysis_items",
        "credit_wallets",
        "email_outbox",
    }
    required_foreign_keys = {
        "questions_topic_id_fkey",
        "question_messages_question_id_fkey",
        "answer_sessions_user_id_fkey",
        "answer_sessions_question_id_fkey",
        "evaluation_reports_session_id_fkey",
        "grammar_analysis_items_report_id_fkey",
        "credit_wallets_user_id_fkey",
        "email_outbox_user_id_fkey",
    }
    connection = await asyncpg.connect(_asyncpg_dsn())
    try:
        rows = await connection.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname = current_schema()"
        )
        actual_tables = {row["tablename"] for row in rows}
        constraint_rows = await connection.fetch(
            """
            SELECT conname
            FROM pg_constraint
            WHERE contype = 'f'
              AND connamespace = (SELECT oid FROM pg_namespace WHERE nspname = current_schema())
            """
        )
        actual_foreign_keys = {row["conname"] for row in constraint_rows}
    finally:
        await connection.close()
    missing = required_tables - actual_tables
    if missing:
        raise RuntimeError(f"Database bootstrap is incomplete; missing tables: {sorted(missing)}")
    missing_foreign_keys = required_foreign_keys - actual_foreign_keys
    if missing_foreign_keys:
        raise RuntimeError(
            f"Database bootstrap is incomplete; missing foreign keys: {sorted(missing_foreign_keys)}"
        )

    async with AsyncSessionLocal() as db:
        accepted = int(
            await db.scalar(
                select(func.count()).select_from(Question).where(Question.status == ReviewStatus.accepted)
            )
            or 0
        )
    if expected_questions is not None and accepted < expected_questions:
        raise RuntimeError(
            f"Question seed is incomplete: expected at least {expected_questions}, found {accepted}"
        )
    await engine.dispose()
    print(
        "Database verification passed "
        f"({accepted} accepted questions, {len(actual_foreign_keys)} foreign keys, seed={SEED_PATH.name})"
    )


async def bootstrap(skip_seed: bool) -> None:
    connection = await asyncpg.connect(_asyncpg_dsn())
    try:
        print("Applying current schema...", flush=True)
        await _apply_schema(connection)
        applied, skipped = await _apply_migrations(connection)
    finally:
        await connection.close()
    print(f"Schema migrations ready: {applied} applied, {skipped} already present")

    expected_questions = None
    if not skip_seed:
        from backend.db.question_seed import SEED_PATH, import_seed

        payload = json.loads(SEED_PATH.read_text(encoding="utf-8"))
        expected_questions = int(payload["question_count"])
        inserted, existing = await import_seed()
        print(f"Public question seed ready: {inserted} inserted, {existing} already present")
    await _verify_database(expected_questions)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create or upgrade the TAWEP PostgreSQL database")
    parser.add_argument("--skip-seed", action="store_true", help="Apply schema and migrations without public questions")
    args = parser.parse_args()
    asyncio.run(bootstrap(args.skip_seed))
