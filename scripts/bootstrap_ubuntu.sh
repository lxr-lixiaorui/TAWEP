#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example. Configure DATABASE_URL and secrets, then run this script again."
  exit 1
fi

command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 1; }
command -v npm >/dev/null || { echo "npm is required" >&2; exit 1; }

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m backend.db.bootstrap

npm --prefix frontend ci
npm --prefix frontend run build

if [[ -n "${TAWEP_ADMIN_EMAIL:-}" ]]; then
  .venv/bin/python -m backend.db.bootstrap_admin \
    --email "$TAWEP_ADMIN_EMAIL" \
    --alias "${TAWEP_ADMIN_ALIAS:-TAWEP Administrator}"
fi

echo
echo "TAWEP is initialized. Start it with:"
echo "  bash scripts/run_production.sh"
echo "Or install persistent systemd services with:"
echo "  sudo bash scripts/install_systemd.sh"
if [[ -z "${TAWEP_ADMIN_EMAIL:-}" ]]; then
  echo
  echo "Create or reset the first administrator with:"
  echo "  .venv/bin/python -m backend.db.bootstrap_admin --email you@example.com --alias 'TAWEP Administrator'"
fi
