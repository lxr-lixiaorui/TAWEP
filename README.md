# TAWEP

**TAWEP** (TOEFL Academic Discussion Evaluation Project) is being rebuilt from the original Flask prototype into a platform-style TOEFL Academic Discussion writing evaluation website.

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

Create an empty PostgreSQL database, configure `DATABASE_URL` in `.env`, then run the idempotent bootstrap command:

```powershell
python -m backend.db.bootstrap
```

This single command applies the current schema, runs every unapplied migration, records migration checksums, imports missing public question-bank data, and verifies the resulting relationships. It is safe to run again after each `git pull`.

The deployable seed currently contains 99 accepted public questions and their messages, topics, and recommendation profiles. It intentionally excludes accounts, answers, reports, tokens, email, and API credentials.

On a fresh Ubuntu server, after preparing `.env`, the complete backend/frontend bootstrap is:

```bash
bash scripts/bootstrap_ubuntu.sh
bash scripts/run_production.sh
```

`run_production.sh` starts both FastAPI and the durable AI evaluation worker. `python app.py` starts FastAPI and its email worker only; run `python -m backend.workers.evaluation` separately when not using the production script. The built Vue frontend is served by FastAPI and needs no production Node process.

To run both backend processes at boot under systemd:

```bash
sudo bash scripts/install_systemd.sh
```

For transferring an existing database with all relationships and runtime data, use PostgreSQL custom-format `pg_dump`/`pg_restore`, then run the same bootstrap command to apply code versions newer than the backup. See [Database deployment and migration](docs/database-deployment.md).

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

For a single-process production-style run, build the frontend first and then start FastAPI:

```powershell
cd frontend
npm run build
cd ..
python app.py
```

FastAPI automatically serves `frontend/dist` at `http://127.0.0.1:1145`, including Vue history-route fallback.

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
- `/score-report`
- `/agreements`
- `/creditexplanation`
- `/login`
- `/verify-email`
- `/reset-password`
- `/manage`
- `/manage/questionbank`
- `/manage/reviewquestion`
- `/manage/feedback`
- `/manage/outcomes`
- `/manage/accounts`
- `/manage/settings`

Backend API routes are under `/api/v1`.

## Credit Rules

- Initial account credit: `45`
- Weekly usage limit: none
- One AI evaluation: `3` credits
- Evaluations cost `2` credits when the user's planned exam is `0–7` days away, including exam day.
- If credit is insufficient, submit returns HTTP `402` with an `INSUFFICIENT_CREDIT` style error payload.

## Account And Email Development

Accounts use Argon2 password hashing, short-lived JWT access tokens, rotating refresh tokens in an HttpOnly cookie, and single-use email verification/password-reset tokens. Configure a random `AUTH_SECRET_KEY` in `.env` before starting the backend.

Authenticated users can change their password or permanently delete their account from Settings. A password change revokes every active login session. Self-service account deletion requires the current password and an exact email confirmation, then removes account-owned sessions, reports, credits, inbox messages, consent records, and personal API credentials through PostgreSQL cascades. Published user-created questions remain available with their creator reference cleared. Administrator accounts must be removed by another administrator.

The standalone cross-border notice is controlled from `/manage/settings` and is hidden by default. Each transition from hidden to visible creates a new activation version, so every user must explicitly accept that version before continuing. User-reported official Writing outcomes are available to administrators at `/manage/outcomes` for future aggregate improvement analysis.

Account emails are always written to the PostgreSQL `email_outbox` table first. In local development, inspect the latest verification or reset link with:

```powershell
python -m backend.db.show_email_outbox user@example.com
```

Keep `EMAIL_DELIVERY_MODE=outbox` during local development. To enable real Resend delivery, verify `tawep.org` in Resend and configure:

```env
EMAIL_DELIVERY_MODE=resend
MAIL_FROM_EMAIL=auth@tawep.org
MAIL_FROM_NAME=TAWEP Accounts
MAIL_REPLY_TO=authissue@tawep.org
RESEND_API_KEY=re_...
RESEND_WEBHOOK_SECRET=whsec_...
```

Then apply the email migration and restart FastAPI:

```powershell
python -m backend.db.migrate_resend_email
python app.py
```

The application runs a durable outbox worker with retry and Resend idempotency keys. Register the public webhook URL `https://tawep.org/api/v1/webhooks/resend` for `email.sent`, `email.delivered`, `email.delivery_delayed`, `email.bounced`, `email.complained`, `email.failed`, `email.suppressed`, and `email.received`. Incoming mail is verified, fetched from Resend, and stored as `auth`, `feedback`, or `unrouted` according to its recipient. Administrators can inspect metadata at `GET /api/v1/admin/emails/outbox` and incoming content at `GET /api/v1/admin/emails/inbound` plus `GET /api/v1/admin/emails/inbound/{email_id}`.

To receive mail at `@tawep.org`, configure the MX record supplied by Resend. This makes Resend the inbound handler for the domain, so review any existing mailbox provider records before changing DNS.

Personal OpenAI-compatible API keys are encrypted before database storage. Generate a separate Fernet key before production deployment:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Set the result as `BYOK_ENCRYPTION_KEY`. Development derives a local key from `AUTH_SECRET_KEY` when this value is omitted; production refuses to start without an explicit key.

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
