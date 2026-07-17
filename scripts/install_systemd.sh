#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this installer with sudo: sudo bash scripts/install_systemd.sh" >&2
  exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_USER="${TAWEP_SERVICE_USER:-${SUDO_USER:-}}"

if [[ "$ROOT" =~ [[:space:]%] ]]; then
  echo "Move the repository to a path without spaces or percent signs before installing systemd units." >&2
  exit 1
fi
if [[ -z "$SERVICE_USER" || "$SERVICE_USER" == "root" ]]; then
  echo "Set TAWEP_SERVICE_USER to a non-root Linux account." >&2
  exit 1
fi
SERVICE_GROUP="$(id -gn "$SERVICE_USER")"

[[ -f "$ROOT/.env" ]] || { echo "$ROOT/.env is missing" >&2; exit 1; }
[[ -x "$ROOT/.venv/bin/uvicorn" ]] || { echo "Run bash scripts/bootstrap_ubuntu.sh first" >&2; exit 1; }
runuser -u "$SERVICE_USER" -- test -r "$ROOT/.env" || {
  echo "$SERVICE_USER cannot read $ROOT/.env; fix its owner and permissions." >&2
  exit 1
}
runuser -u "$SERVICE_USER" -- test -x "$ROOT/.venv/bin/uvicorn" || {
  echo "$SERVICE_USER cannot execute the virtual environment." >&2
  exit 1
}

cat > /etc/systemd/system/tawep-api.service <<EOF
[Unit]
Description=TAWEP FastAPI application and email worker
Wants=network-online.target
After=network-online.target postgresql.service
PartOf=tawep.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$ROOT
Environment=APP_ENV=production
Environment=PYTHONUNBUFFERED=1
ExecStart=$ROOT/.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 1145 --workers 1
Restart=on-failure
RestartSec=5
TimeoutStopSec=30
KillSignal=SIGTERM
UMask=0027
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=tawep.target
EOF

cat > /etc/systemd/system/tawep-worker.service <<EOF
[Unit]
Description=TAWEP durable AI evaluation worker
Wants=network-online.target
Requires=tawep-api.service
After=network-online.target postgresql.service tawep-api.service
PartOf=tawep.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$ROOT
Environment=APP_ENV=production
Environment=PYTHONUNBUFFERED=1
ExecStart=$ROOT/.venv/bin/python -m backend.workers.evaluation
Restart=on-failure
RestartSec=5
TimeoutStopSec=30
KillSignal=SIGTERM
UMask=0027
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=tawep.target
EOF

cat > /etc/systemd/system/tawep.target <<'EOF'
[Unit]
Description=TAWEP application services
Requires=tawep-api.service tawep-worker.service
After=tawep-api.service tawep-worker.service

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now tawep.target

echo "TAWEP systemd services are enabled and started."
echo "Status:  systemctl status tawep-api tawep-worker"
echo "Logs:    journalctl -u tawep-api -u tawep-worker -f"
