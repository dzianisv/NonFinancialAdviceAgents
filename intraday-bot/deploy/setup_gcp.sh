#!/usr/bin/env bash
# setup_gcp.sh — provisions intraday-bot/bot on a GCP e2-micro Debian instance.
#
# Run this AS ROOT (or via sudo) on a fresh e2-micro (Debian 12 "bookworm") VM, after
# cloning/copying the repo to the instance. Installs Python venv, pip deps, and a systemd
# unit that runs the runner in mode=notify by default — NO secrets are baked into this
# script or into any file it writes. Deploy is DELIVER-ONLY: this script is provided as an
# artifact; nothing in this task suite actually provisions a real GCP instance.
#
# Usage (on the target VM, as root):
#   REPO_DIR=/opt/intraday-bot bash setup_gcp.sh
#
set -euo pipefail

REPO_DIR="${REPO_DIR:-/opt/intraday-bot}"
SERVICE_USER="${SERVICE_USER:-intraday-bot}"
VENV_DIR="${REPO_DIR}/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "==> intraday-bot GCP e2-micro setup"
echo "    REPO_DIR=${REPO_DIR}"
echo "    SERVICE_USER=${SERVICE_USER}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "This script must be run as root (sudo)." >&2
  exit 1
fi

# 1. OS packages (Debian 12 e2-micro image)
echo "==> apt: python3-venv, python3-pip"
apt-get update -y
apt-get install -y python3-venv python3-pip

# 2. dedicated non-root service user (least privilege — never run the bot as root)
if ! id -u "${SERVICE_USER}" >/dev/null 2>&1; then
  echo "==> creating service user ${SERVICE_USER}"
  useradd --system --create-home --home-dir "/home/${SERVICE_USER}" --shell /usr/sbin/nologin "${SERVICE_USER}"
fi

# 3. expects the repo already copied to REPO_DIR (e.g. via `gcloud compute scp` or git clone
#    by a human operator out-of-band — this script does not fetch source itself)
if [[ ! -d "${REPO_DIR}" ]]; then
  echo "ERROR: ${REPO_DIR} does not exist. Copy the repo there first (git clone / scp)." >&2
  exit 1
fi

# 4. venv + deps (intraday-bot/deploy/requirements.txt only — minimal footprint for e2-micro's
#    1GB RAM / shared vCPU)
echo "==> creating venv at ${VENV_DIR}"
"${PYTHON_BIN}" -m venv "${VENV_DIR}"
"${VENV_DIR}/bin/pip" install --upgrade pip
"${VENV_DIR}/bin/pip" install -r "${REPO_DIR}/intraday-bot/deploy/requirements.txt"

chown -R "${SERVICE_USER}:${SERVICE_USER}" "${REPO_DIR}"

# 5. env file (secrets NEVER live in this script or in git — see README-DEPLOY.md).
#    Creates an EMPTY, root-owned, 0600 env file the operator fills in by hand (or via a
#    secrets manager) AFTER this script runs. mode=notify needs NO keys at all.
ENV_FILE="/etc/intraday-bot.env"
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "==> creating empty ${ENV_FILE} (fill in via Bitwarden 'dev' collection if mode=paper/live)"
  cat > "${ENV_FILE}" <<'EOF'
# intraday-bot env — populate from Bitwarden 'dev' collection (never commit real values).
# mode=notify (default) needs NONE of these.
# ALPACA_PAPER_KEY=
# ALPACA_PAPER_SECRET=
# ALPACA_LIVE_KEY=
# ALPACA_LIVE_SECRET=
# CONFIRM_LIVE=
EOF
  chmod 600 "${ENV_FILE}"
  chown root:root "${ENV_FILE}"
fi

# 6. systemd unit
UNIT_PATH="/etc/systemd/system/intraday-bot.service"
echo "==> installing ${UNIT_PATH}"
cat > "${UNIT_PATH}" <<EOF
[Unit]
Description=intraday-bot live/paper runner (default mode=notify)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${SERVICE_USER}
Group=${SERVICE_USER}
WorkingDirectory=${REPO_DIR}/intraday-bot
EnvironmentFile=-${ENV_FILE}
ExecStart=${VENV_DIR}/bin/python3 bot/runner.py --config bot/config.yaml
Restart=on-failure
RestartSec=30
# hardening (best-effort; e2-micro/Debian defaults)
NoNewPrivileges=true
ProtectSystem=full
ProtectHome=true

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo "==> systemd unit installed. NOT started automatically by this script."
echo ""
echo "Next steps (manual, deliberate):"
echo "  1. Review ${REPO_DIR}/intraday-bot/bot/config.yaml (mode should stay 'notify' until"
echo "     you've watched it run and reviewed the audit log)."
echo "  2. If/when moving to mode=paper: fill ${ENV_FILE} with ALPACA_PAPER_KEY/SECRET"
echo "     from the Bitwarden 'dev' collection (see README-DEPLOY.md)."
echo "  3. sudo systemctl enable --now intraday-bot.service"
echo "  4. journalctl -u intraday-bot -f    # tail logs"
echo ""
echo "==> done."
