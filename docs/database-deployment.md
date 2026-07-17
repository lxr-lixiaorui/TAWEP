# Database Deployment And Migration

TAWEP supports two different database workflows:

1. Fresh deployment: create the schema and import only the versioned public question bank.
2. Instance migration: transfer the complete existing PostgreSQL database, including users, answers, reports, foreign keys, indexes, and migration history.

Do not commit `.env` or database dumps. A full dump can contain password hashes, answer text, authentication sessions, encrypted personal API keys, and email addresses.

## Fresh Ubuntu Deployment

Install the runtime packages:

```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib python3 python3-venv nodejs npm git
```

Create a dedicated application role and database. Run this as the PostgreSQL administrator; do not run the web application as the `postgres` superuser:

```bash
sudo -u postgres psql
```

```sql
CREATE ROLE tawep LOGIN PASSWORD 'replace-with-a-long-random-password';
CREATE DATABASE tawep OWNER tawep;
\q
```

If the `tawep` role already exists, update it with `\password tawep` instead of recreating it.

Clone and configure the application:

```bash
git clone https://github.com/lxr-lixiaorui/TAWEP.git
cd TAWEP
cp .env.example .env
nano .env
```

At minimum, configure:

```env
DATABASE_URL=postgresql+asyncpg://tawep:URL_ENCODED_PASSWORD@127.0.0.1:5432/tawep
APP_ENV=production
PUBLIC_APP_URL=https://tawep.org
AUTH_SECRET_KEY=at-least-32-random-characters
BYOK_ENCRYPTION_KEY=your-fernet-key
AUTH_COOKIE_SECURE=true
```

Percent-encode reserved URL characters in the database password. Generate the Fernet key with:

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Install dependencies, apply schema/migrations, import the public question seed, and build Vue:

```bash
bash scripts/bootstrap_ubuntu.sh
```

To create the first administrator during the same interactive bootstrap, provide its email; the script will securely prompt for its password:

```bash
TAWEP_ADMIN_EMAIL=admin@tawep.org bash scripts/bootstrap_ubuntu.sh
```

Start the application:

```bash
bash scripts/run_production.sh
```

This starts both the FastAPI web process and the durable evaluation worker. The server listens on `0.0.0.0:1145` by default. Put it behind the deployment's HTTPS reverse proxy.

`python app.py` starts only FastAPI. FastAPI also owns the Resend outbox worker, but AI evaluation jobs require a separate process:

```bash
python -m backend.workers.evaluation
```

The built Vue application is served from `frontend/dist` by FastAPI, so production does not require a separate Node/Vite process.

## Run With systemd

After `bootstrap_ubuntu.sh` succeeds, install the API and evaluation worker as separate systemd services:

```bash
sudo bash scripts/install_systemd.sh
```

The selected service account must be able to read the repository and `.env`. A typical secure setup is:

```bash
sudo chown -R "$USER":"$USER" /path/to/TAWEP
chmod 600 /path/to/TAWEP/.env
```

The installer uses the account that invoked `sudo` and the repository's current absolute path. To use a different non-root account:

```bash
sudo TAWEP_SERVICE_USER=tawep bash scripts/install_systemd.sh
```

It installs and enables:

- `tawep-api.service`: FastAPI, built Vue frontend, and Resend outbox worker.
- `tawep-worker.service`: durable AI evaluation worker.
- `tawep.target`: starts both services at boot.

Useful commands:

```bash
sudo systemctl status tawep-api tawep-worker
sudo systemctl restart tawep-api tawep-worker
sudo systemctl stop tawep.target
sudo systemctl start tawep.target
sudo journalctl -u tawep-api -u tawep-worker -f
curl http://127.0.0.1:1145/health
```

After deploying new code, apply migrations and rebuild before restarting the units:

```bash
git pull
bash scripts/bootstrap_ubuntu.sh
sudo systemctl restart tawep-api tawep-worker
```

Do not run `scripts/run_production.sh` at the same time as the systemd units, or both processes will compete for port `1145`.

## Bootstrap Behavior

`python -m backend.db.bootstrap` performs these steps:

1. Applies `backend/db/schema.sql` idempotently.
2. Runs each migration not recorded in `schema_migrations`.
3. Stores the SHA-256 checksum of every applied migration.
4. Imports missing entries from `backend/db/seed/question_bank.json`.
5. Verifies core tables, foreign keys, and accepted-question count.

Run it after every deployment:

```bash
git pull
bash scripts/bootstrap_ubuntu.sh
```

Never edit a migration that has been deployed. Add a new migration module and register it in `backend/db/bootstrap.py`; checksum mismatch is treated as a deployment error.

## Transfer The Existing Database

Use this path when the Ubuntu server must contain the current accounts, credits, answer sessions, reports, feedback, and all other runtime data.

On the source machine, create a consistent custom-format backup:

```bash
pg_dump \
  --host=127.0.0.1 \
  --port=5432 \
  --username=tawep \
  --dbname=tawep \
  --format=custom \
  --no-owner \
  --no-acl \
  --file=tawep.dump
```

Transfer `tawep.dump` over an encrypted channel such as `scp`. Restore into a newly created, empty target database:

```bash
pg_restore \
  --host=127.0.0.1 \
  --port=5432 \
  --username=tawep \
  --dbname=tawep \
  --no-owner \
  --no-acl \
  --exit-on-error \
  tawep.dump
```

Do not run the fresh bootstrap before restoring into an empty target. After restore, run it once to add any schema changes newer than the dump:

```bash
python -m backend.db.bootstrap
```

The custom dump includes table data, primary keys, foreign keys, indexes, constraints, PostgreSQL enums, and sequences. PostgreSQL roles and `.env` secrets are not included.

For a true instance migration, transfer these secret values securely from the old deployment:

- `AUTH_SECRET_KEY`: otherwise existing access/refresh sessions become invalid.
- `BYOK_ENCRYPTION_KEY`: otherwise stored personal API keys cannot be decrypted.
- Provider keys such as `OPENAI_API_KEY` and `RESEND_API_KEY`.

Rotating `AUTH_SECRET_KEY` and intentionally forcing every user to sign in again is also valid. Losing `BYOK_ENCRYPTION_KEY` is not recoverable for already stored personal API keys.

## Verification And Administration

Verify the database at any time by rerunning:

```bash
python -m backend.db.bootstrap
```

Create or reset the first administrator after initialization:

```bash
export TAWEP_BOOTSTRAP_ADMIN_PASSWORD='replace-with-a-long-random-password'
python -m backend.db.bootstrap_admin --email admin@tawep.org --alias 'TAWEP Administrator'
unset TAWEP_BOOTSTRAP_ADMIN_PASSWORD
```

Alternatively, omit `TAWEP_BOOTSTRAP_ADMIN_PASSWORD`; the command will request the password securely without echoing it. The public seed deliberately contains no users, so every fresh installation must run this command once.
