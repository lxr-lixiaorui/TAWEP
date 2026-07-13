import asyncio

from sqlalchemy import text

from backend.db.session import AsyncSessionLocal, engine
from backend.services.practice import ensure_demo_account


DDL_STATEMENTS = [
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_evaluation_reports_session_id ON evaluation_reports (session_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_score_components_report_id ON score_components (report_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_language_metric_report_key ON language_metric_scores (report_id, metric_key)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_credit_ledger_session_reason ON credit_ledger (session_id, reason)",
]


async def main() -> None:
    async with engine.begin() as connection:
        for statement in DDL_STATEMENTS:
            await connection.execute(text(statement))

    async with AsyncSessionLocal() as session:
        async with session.begin():
            await ensure_demo_account(session)

    print("Practice persistence constraints and demo wallet are ready")


if __name__ == "__main__":
    asyncio.run(main())
