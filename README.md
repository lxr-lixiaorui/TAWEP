# TAWEP

**TAWEP** (TOEFL Academic Writing Evaluation Project) is being rebuilt from the original Flask prototype into a platform-style TOEFL Academic Discussion writing evaluation website.

The current structure is:

- `backend/`: FastAPI REST API, SQLAlchemy models, service layer, Postgres schema
- `frontend/`: Vue 3 + TypeScript + Naive UI + Pinia + vue-i18n SPA
- `static/table/2023_AcaTalk.txt`: legacy official prompt bank used as the temporary question source
- `static/table/2023_AcaTalk_Answer.txt`: legacy reference-answer data
- `static/table/Record/`: historical generated HTML reports, kept as local artifacts

The old Flask template runtime has been removed. `app.py` now starts the FastAPI app for compatibility with the previous entry command.

## Requirements

Backend:

```powershell
python -m pip install -r requirements.txt
```

Frontend:

```powershell
cd frontend
npm install
```

Postgres is expected locally on port `5432`. Default connection string:

```text
postgresql+asyncpg://tawep:tawep@localhost:5432/tawep
```

Create `.env` from `.env.example` and set `OPENAI_API_KEY` to your Deepseek key when live evaluation is wired in.

## Database

Initialize the schema with your Postgres client:

```powershell
psql -h localhost -p 5432 -U tawep -d tawep -f backend/db/schema.sql
```

For an existing development database, apply the AI Rewrite comparison column with:

```powershell
python -m backend.db.migrate_rewrite_comparison
python -m backend.db.migrate_grammar_offsets
python -m backend.db.migrate_auth
python -m backend.db.migrate_admin_accounts
python -m backend.db.migrate_question_moderation
python -m backend.db.migrate_report_feedback
```

The schema includes users, topics, questions, uploaded-question review, answer sessions, evaluation reports, grammar analysis, language metrics, credit wallets, credit ledger, inbox messages, legal documents, and admin audit logs.

## Run

Backend:

```powershell
python app.py
```

or:

```powershell
uvicorn backend.main:app --host 0.0.0.0 --port 1145 --reload
```

Frontend:

```powershell
cd frontend
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

The Vite dev server proxies `/api` to `http://127.0.0.1:1145`.

## Main Routes

Frontend routes include:

- `/`
- `/dashboard`
- `/questionbank`
- `/createyourown`
- `/{questionNo}/prepare`
- `/{sessionId}/answerpage`
- `/{sessionId}/report`
- `/{sessionId}/rewrite`
- `/{sessionId}/grammaranalysis`
- `/{sessionId}/download`
- `/examplereport`
- `/settings`
- `/inbox`
- `/agreements`
- `/creditexplanation`
- `/login`
- `/verify-email`
- `/reset-password`
- `/manage`
- `/manage/questionbank`
- `/manage/reviewquestion`
- `/manage/feedback`
- `/manage/accounts`

Backend API routes are under `/api/v1`.

## Credit Rules

- Initial account credit: `180`
- Weekly rolling usage limit: `60`
- One AI evaluation: `3` credits
- If credit is insufficient, submit returns HTTP `402` with an `INSUFFICIENT_CREDIT` style error payload.

## Account And Email Development

Accounts use Argon2 password hashing, short-lived JWT access tokens, rotating refresh tokens in an HttpOnly cookie, and single-use email verification/password-reset tokens. Configure a random `AUTH_SECRET_KEY` in `.env` before starting the backend.

Until a mail provider and public domain are configured, account email is written to the PostgreSQL `email_outbox` table. Inspect the latest local verification or reset link with:

```powershell
python -m backend.db.show_email_outbox user@example.com
```

Keep `EMAIL_DELIVERY_MODE=outbox` during local development. The email transport can later consume the same outbox records without changing the authentication endpoints.

## Administrator Accounts

Create the first administrator, or reset an existing administrator password, without storing the password in the repository:

```powershell
$env:TAWEP_BOOTSTRAP_ADMIN_PASSWORD="use-a-long-random-password"
python -m backend.db.bootstrap_admin --email admin@example.com --alias "TAWEP Administrator"
Remove-Item Env:TAWEP_BOOTSTRAP_ADMIN_PASSWORD
```

Sign in through `/login`, then open `/manage/accounts`. Administrators can create user or administrator accounts, change account availability, send inbox messages, adjust credits, and permanently delete users. Destructive deletion requires typing the target email and cannot delete the current administrator or the final active administrator.

Question submissions are stored as `pending` and remain hidden from public question and session APIs until an administrator accepts them. Use `/manage/reviewquestion` for full-content review and `/manage/questionbank` to create official questions or maintain official and user-created records. Questions with existing answer sessions can be archived but cannot be permanently deleted.

Authenticated users can submit one consent-backed feedback record per completed report. The feedback stores immutable answer and report snapshots for administrator review at `/manage/feedback`; example reports do not accept feedback.

## Development Notes

- Authentication, account-owned practice sessions, credits, reports, dashboard history, account administration, question upload, moderation, and question-bank management use PostgreSQL. Some recommendation content remains placeholder data.
- Do not commit API keys or user private data.
- Keep `static/table/*.txt` content unchanged unless the task explicitly requires data edits.
- Historical files under `static/table/Record/` are generated report artifacts, not source requirements.
