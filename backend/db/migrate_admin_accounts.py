import asyncio

from sqlalchemy import text

from backend.db.session import engine


FOREIGN_KEYS = [
    ("questions", "questions_creator_user_id_fkey", "creator_user_id", "users(id)", "SET NULL"),
    ("uploaded_question_reviews", "uploaded_question_reviews_reviewer_id_fkey", "reviewer_id", "users(id)", "SET NULL"),
    ("answer_sessions", "answer_sessions_user_id_fkey", "user_id", "users(id)", "CASCADE"),
    ("evaluation_jobs", "evaluation_jobs_session_id_fkey", "session_id", "answer_sessions(id)", "CASCADE"),
    ("evaluation_reports", "evaluation_reports_session_id_fkey", "session_id", "answer_sessions(id)", "CASCADE"),
    ("score_components", "score_components_report_id_fkey", "report_id", "evaluation_reports(id)", "CASCADE"),
    ("grammar_analysis_items", "grammar_analysis_items_report_id_fkey", "report_id", "evaluation_reports(id)", "CASCADE"),
    ("language_metric_scores", "language_metric_scores_report_id_fkey", "report_id", "evaluation_reports(id)", "CASCADE"),
    ("credit_wallets", "credit_wallets_user_id_fkey", "user_id", "users(id)", "CASCADE"),
    ("credit_ledger", "credit_ledger_user_id_fkey", "user_id", "users(id)", "CASCADE"),
    ("credit_ledger", "credit_ledger_session_id_fkey", "session_id", "answer_sessions(id)", "CASCADE"),
    ("credit_ledger", "credit_ledger_admin_id_fkey", "admin_id", "users(id)", "SET NULL"),
    ("inbox_messages", "inbox_messages_user_id_fkey", "user_id", "users(id)", "CASCADE"),
    ("admin_audit_logs", "admin_audit_logs_admin_id_fkey", "admin_id", "users(id)", "SET NULL"),
]


async def main() -> None:
    async with engine.begin() as connection:
        await connection.execute(text("ALTER TABLE admin_audit_logs ALTER COLUMN admin_id DROP NOT NULL"))
        for table, constraint, column, target, delete_rule in FOREIGN_KEYS:
            await connection.execute(text(f'ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {constraint}'))
            await connection.execute(
                text(
                    f'ALTER TABLE {table} ADD CONSTRAINT {constraint} '
                    f'FOREIGN KEY ({column}) REFERENCES {target} ON DELETE {delete_rule}'
                )
            )
    await engine.dispose()
    print("Administrator account deletion constraints are ready")


if __name__ == "__main__":
    asyncio.run(main())
