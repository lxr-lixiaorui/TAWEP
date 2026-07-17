#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -x .venv/bin/uvicorn ]]; then
  echo "Run bash scripts/bootstrap_ubuntu.sh first." >&2
  exit 1
fi

cleanup() {
  [[ -n "${api_pid:-}" ]] && kill "$api_pid" 2>/dev/null || true
  [[ -n "${worker_pid:-}" ]] && kill "$worker_pid" 2>/dev/null || true
  wait "${api_pid:-}" "${worker_pid:-}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

.venv/bin/python -m backend.workers.evaluation &
worker_pid=$!

.venv/bin/uvicorn backend.main:app \
  --host "${HOST:-0.0.0.0}" \
  --port "${PORT:-1145}" \
  --workers "${WEB_WORKERS:-1}" &
api_pid=$!

set +e
wait -n "$api_pid" "$worker_pid"
status=$?
set -e
exit "$status"
