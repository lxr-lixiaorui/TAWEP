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

Postgres is expected locally on port `2345`. Default connection string:

```text
postgresql+asyncpg://tawep:tawep@localhost:2345/tawep
```

Create `.env` from `.env.example` and set `OPENAI_API_KEY` to your Deepseek key when live evaluation is wired in.

## Database

Initialize the schema with your Postgres client:

```powershell
psql -h localhost -p 2345 -U tawep -d tawep -f backend/db/schema.sql
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
- `/{sessionId}/grammaranalysis`
- `/{sessionId}/download`
- `/examplereport`
- `/settings`
- `/inbox`
- `/agreements`
- `/creditexplanation`
- `/login`
- `/manage`
- `/manage/questionbank`
- `/manage/reviewquestion`
- `/manage/accounts`

Backend API routes are under `/api/v1`.

## Credit Rules

- Initial account credit: `180`
- Weekly rolling usage limit: `60`
- One AI evaluation: `3` credits
- If credit is insufficient, submit returns HTTP `402` with an `INSUFFICIENT_CREDIT` style error payload.

## Development Notes

- The current backend routes return demo data or legacy-file-derived data where database queries are not wired yet.
- Do not commit API keys or user private data.
- Keep `static/table/*.txt` content unchanged unless the task explicitly requires data edits.
- Historical files under `static/table/Record/` are generated report artifacts, not source requirements.
