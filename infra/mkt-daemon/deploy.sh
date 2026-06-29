#!/usr/bin/env bash
# deploy.sh — provisions a free-tier GCP e2-micro VM running mkt daemon
# behind a Cloudflare Tunnel at mkt.agentlabs.cc.
#
# Usage:  bash infra/mkt-daemon/deploy.sh
#
# Idempotent: safe to re-run. Skips steps that are already done.
# Prereqs (local): gcloud (bisonte config), cloudflared, bun, python3, openssl
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# ── Config ────────────────────────────────────────────────────────────────────
GCLOUD_CONFIG="bisonte"
GCP_BILLING="01BFB1-83821D-942EE8"   # bisonte billing account
GCP_REGION="us-central1"              # only free-tier e2-micro region
GCP_ZONE="us-central1-a"
GCP_PROJECT="mkt-daemon-alerts"
VM_NAME="mkt-daemon"
VM_TYPE="e2-micro"
VM_IMAGE_FAMILY="debian-12"
VM_IMAGE_PROJECT="debian-cloud"

CF_ZONE_ID="5fbeec0aa0dca842ab3b62fafb948fe9"
CF_ACCOUNT_ID="c52033a95d560a9a183b016ceb1c107a"
TUNNEL_NAME="mkt-daemon"
TUNNEL_HOST="mkt.agentlabs.cc"

MKT_COMMIT="0207dda"
MKT_LISTEN="127.0.0.1:9999"
SKILLS_DIR="$REPO_ROOT/.agents/skills/mkt/scripts"
ALERTS_JSON="$REPO_ROOT/.cache/mkt/agent-alerts.json"

# ── Helpers ───────────────────────────────────────────────────────────────────
G() { gcloud --configuration="$GCLOUD_CONFIG" "$@"; }

log()  { echo "▶ $*"; }
ok()   { echo "  ✓ $*"; }
fail() { echo "  ✗ $*" >&2; exit 1; }

cf_api() {
  local method="$1" path="$2"; shift 2
  curl -sf -X "$method" \
    "https://api.cloudflare.com/client/v4$path" \
    -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
    -H "Content-Type: application/json" \
    "$@"
}

# ── Phase 0: Secrets ──────────────────────────────────────────────────────────
log "Phase 0: loading secrets"

# Cloudflare API token
if [[ -f ~/.env.d/cloudflare.env ]]; then
  # shellcheck source=/dev/null
  source ~/.env.d/cloudflare.env
fi
[[ -n "${CLOUDFLARE_API_TOKEN:-}" ]] || fail "CLOUDFLARE_API_TOKEN not set (check ~/.env.d/cloudflare.env)"

# Telegram bot token (optional; falls back to ntfy if missing)
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
if [[ -z "$TELEGRAM_BOT_TOKEN" ]]; then
  # Try bitwarden
  if command -v bw &>/dev/null; then
    source ~/.env.d/bitwarden.env 2>/dev/null || true
    TELEGRAM_BOT_TOKEN=$(bw get password "telegram-bot-token" 2>/dev/null || true)
  fi
fi
if [[ -z "$TELEGRAM_BOT_TOKEN" ]]; then
  log "  ⚠ TELEGRAM_BOT_TOKEN not found — alerts will use ntfy:mkt-agentlabs as fallback"
  NOTIFY_CHANNEL="ntfy:mkt-agentlabs"
else
  ok "Telegram bot token loaded"
  NOTIFY_CHANNEL="telegram-bot:@CryptoAiInvestor"
fi

# ── Phase 1: GCP Project ──────────────────────────────────────────────────────
log "Phase 1: GCP project $GCP_PROJECT"

if ! G projects describe "$GCP_PROJECT" &>/dev/null; then
  G projects create "$GCP_PROJECT" --name="mkt-daemon"
  G billing projects link "$GCP_PROJECT" --billing-account="$GCP_BILLING"
  ok "project created"
else
  ok "project exists"
fi
G config set project "$GCP_PROJECT" --configuration="$GCLOUD_CONFIG"

log "  enabling Compute API"
G services enable compute.googleapis.com --project="$GCP_PROJECT" --quiet

# ── Phase 2: VM ───────────────────────────────────────────────────────────────
log "Phase 2: VM $VM_NAME ($VM_TYPE, $GCP_ZONE)"

if ! G compute instances describe "$VM_NAME" --zone="$GCP_ZONE" --project="$GCP_PROJECT" &>/dev/null; then
  G compute instances create "$VM_NAME" \
    --project="$GCP_PROJECT" \
    --zone="$GCP_ZONE" \
    --machine-type="$VM_TYPE" \
    --image-family="$VM_IMAGE_FAMILY" \
    --image-project="$VM_IMAGE_PROJECT" \
    --boot-disk-size=20GB \
    --boot-disk-type=pd-standard \
    --tags=mkt-daemon \
    --metadata=serial-port-enable=false
  log "  waiting 25s for boot..."
  sleep 25
  ok "VM created"
else
  # Start if terminated (free-tier VMs are sometimes stopped)
  STATUS=$(G compute instances describe "$VM_NAME" \
    --zone="$GCP_ZONE" --project="$GCP_PROJECT" \
    --format="value(status)")
  if [[ "$STATUS" == "TERMINATED" || "$STATUS" == "STOPPED" ]]; then
    G compute instances start "$VM_NAME" --zone="$GCP_ZONE" --project="$GCP_PROJECT"
    sleep 20
    ok "VM started (was $STATUS)"
  else
    ok "VM exists ($STATUS)"
  fi
fi

VM_IP=$(G compute instances describe "$VM_NAME" \
  --zone="$GCP_ZONE" --project="$GCP_PROJECT" \
  --format="value(networkInterfaces[0].accessConfigs[0].natIP)")
ok "VM external IP: $VM_IP"

SSH() {
  G compute ssh "$VM_NAME" \
    --zone="$GCP_ZONE" --project="$GCP_PROJECT" \
    --ssh-flag="-o ConnectTimeout=30 -o StrictHostKeyChecking=no" \
    --command="$1" 2>&1
}
SCP() {
  G compute scp "$1" "$VM_NAME:$2" \
    --zone="$GCP_ZONE" --project="$GCP_PROJECT" 2>&1
}

# ── Phase 3: Cloudflare Tunnel ────────────────────────────────────────────────
log "Phase 3: Cloudflare Tunnel $TUNNEL_NAME → $TUNNEL_HOST"

# Check for existing tunnel
TUNNEL_ID=$(cf_api GET \
  "/accounts/$CF_ACCOUNT_ID/cfd_tunnel?name=$TUNNEL_NAME&is_deleted=false" | \
  python3 -c "
import json,sys
d=json.load(sys.stdin)
r=d.get('result',[])
print(r[0]['id'] if r else '')
" 2>/dev/null || true)

if [[ -z "$TUNNEL_ID" ]]; then
  TUNNEL_SECRET=$(openssl rand -base64 32)
  RESP=$(cf_api POST "/accounts/$CF_ACCOUNT_ID/cfd_tunnel" \
    -d "{\"name\":\"$TUNNEL_NAME\",\"tunnel_secret\":\"$(echo -n "$TUNNEL_SECRET" | base64 | tr -d '\n')\"}")
  TUNNEL_ID=$(echo "$RESP" | python3 -c "import json,sys; print(json.load(sys.stdin)['result']['id'])")
  ok "Tunnel created: $TUNNEL_ID"
else
  ok "Tunnel exists: $TUNNEL_ID"
fi

# Configure tunnel ingress via API (no config file needed on VM)
cf_api PUT \
  "/accounts/$CF_ACCOUNT_ID/cfd_tunnel/$TUNNEL_ID/configurations" \
  -d "{
    \"config\": {
      \"ingress\": [
        {\"hostname\": \"$TUNNEL_HOST\", \"service\": \"http://$MKT_LISTEN\"},
        {\"service\": \"http_status:404\"}
      ]
    }
  }" > /dev/null
ok "Tunnel ingress configured: $TUNNEL_HOST → $MKT_LISTEN"

# Get run token (used by cloudflared on the VM — no credentials file needed)
TUNNEL_TOKEN=$(cf_api GET \
  "/accounts/$CF_ACCOUNT_ID/cfd_tunnel/$TUNNEL_ID/token" | \
  python3 -c "import json,sys; print(json.load(sys.stdin)['result'])")
ok "Tunnel token retrieved"

# Create/update DNS CNAME
EXISTING_DNS=$(cf_api GET \
  "/zones/$CF_ZONE_ID/dns_records?type=CNAME&name=mkt.agentlabs.cc" | \
  python3 -c "
import json,sys
r=json.load(sys.stdin).get('result',[])
print(r[0]['id'] if r else '')
" 2>/dev/null || true)

DNS_PAYLOAD="{\"type\":\"CNAME\",\"name\":\"mkt\",\"content\":\"$TUNNEL_ID.cfargotunnel.com\",\"proxied\":true,\"ttl\":1}"
if [[ -z "$EXISTING_DNS" ]]; then
  cf_api POST "/zones/$CF_ZONE_ID/dns_records" -d "$DNS_PAYLOAD" > /dev/null
  ok "DNS created: $TUNNEL_HOST → $TUNNEL_ID.cfargotunnel.com"
else
  cf_api PUT "/zones/$CF_ZONE_ID/dns_records/$EXISTING_DNS" -d "$DNS_PAYLOAD" > /dev/null
  ok "DNS updated: $TUNNEL_HOST → $TUNNEL_ID.cfargotunnel.com"
fi

# ── Phase 4: Upload files to VM ───────────────────────────────────────────────
log "Phase 4: uploading files"

# Prepare alerts JSON with correct channel
TMP_ALERTS="/tmp/agent-alerts-vm.json"
python3 - "$ALERTS_JSON" "$NOTIFY_CHANNEL" > "$TMP_ALERTS" << 'PYEOF'
import json, sys
path, channel = sys.argv[1], sys.argv[2]
with open(path) as f:
    jobs = json.load(f)
for j in jobs:
    # keep existing channel if it's already a supported non-Telethon channel
    ch = j.get("channel", "stdout")
    if ch.startswith("telegram:"):
        j["channel"] = channel  # rewrite to bot or ntfy
out = [j for j in jobs if not j.get("fired")]  # only active jobs
print(json.dumps(out, indent=2))
PYEOF
ok "alerts JSON prepared ($(python3 -c "import json; print(len(json.load(open('$TMP_ALERTS'))))" ) active jobs)"

# Write env file for the VM
TMP_ENV="/tmp/mkt-daemon.env"
cat > "$TMP_ENV" << EOF
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
NTFY_TOPIC=mkt-agentlabs
EOF

# Upload
SCP "$TMP_ALERTS" "/tmp/agent-alerts.json"
SCP "$TMP_ENV"    "/tmp/mkt-daemon.env"
SCP "$SKILLS_DIR/check.ts"      "/tmp/check.ts"
SCP "$SKILLS_DIR/store.ts"      "/tmp/store.ts"
SCP "$SKILLS_DIR/indicators.ts" "/tmp/indicators.ts"
SCP "$SKILLS_DIR/mkt-alert.ts"  "/tmp/mkt-alert.ts"
ok "files uploaded"

# ── Phase 5: Remote setup ─────────────────────────────────────────────────────
log "Phase 5: remote setup"

SSH "bash -s" << REMOTE
set -euo pipefail

# ── Go ────────────────────────────────────────────────────────────────────────
if ! command -v go &>/dev/null || [[ "\$(go version 2>/dev/null | grep -oP '[\d]+\.[\d]+' | head -1)" < "1.24" ]]; then
  echo "  installing Go 1.24..."
  wget -q https://go.dev/dl/go1.24.4.linux-amd64.tar.gz -O /tmp/go.tar.gz
  sudo tar -C /usr/local -xzf /tmp/go.tar.gz
  echo 'export PATH=\$PATH:/usr/local/go/bin:\$HOME/.local/bin:\$HOME/.bun/bin' >> ~/.bashrc
fi
export PATH=\$PATH:/usr/local/go/bin:\$HOME/.local/bin:\$HOME/.bun/bin
go version

# ── mkt binary ────────────────────────────────────────────────────────────────
mkdir -p ~/.local/bin ~/.local/src
if [[ ! -f ~/.local/bin/mkt ]]; then
  echo "  building mkt..."
  git clone --quiet https://github.com/stxkxs/mkt ~/.local/src/mkt
  cd ~/.local/src/mkt && git checkout ${MKT_COMMIT} -q
  go build -o ~/.local/bin/mkt . && echo "  mkt built: \$(~/.local/bin/mkt version)"
else
  echo "  mkt exists: \$(~/.local/bin/mkt version)"
fi

# ── Bun ───────────────────────────────────────────────────────────────────────
if ! command -v bun &>/dev/null && [[ ! -f ~/.bun/bin/bun ]]; then
  echo "  installing Bun..."
  curl -fsSL https://bun.sh/install | bash -s -- --no-modify-path 2>/dev/null
fi
export PATH=\$PATH:\$HOME/.bun/bin
bun --version

# ── mkt skill scripts ─────────────────────────────────────────────────────────
MKT_DIR="\$HOME/.agents/skills/mkt/scripts"
CACHE_DIR="\$HOME/.cache/mkt"
mkdir -p "\$MKT_DIR" "\$CACHE_DIR"
cp /tmp/check.ts /tmp/store.ts /tmp/indicators.ts /tmp/mkt-alert.ts "\$MKT_DIR/"
cp /tmp/agent-alerts.json "\$CACHE_DIR/agent-alerts.json"
echo "  skill scripts installed"

# ── mkt config ────────────────────────────────────────────────────────────────
mkdir -p ~/.config/mkt
cat > ~/.config/mkt/config.yaml << 'CFG'
watchlist:
  - BTC-USD
  - ETH-USD
  - CRM
  - META
  - NVDA
  - MSFT

poll_interval: 30s
sparkline_len: 20
CFG

# ── env file ─────────────────────────────────────────────────────────────────
sudo cp /tmp/mkt-daemon.env /etc/mkt-daemon.env
sudo chmod 600 /etc/mkt-daemon.env

# ── systemd: mkt daemon ───────────────────────────────────────────────────────
CURRENT_USER=\$(whoami)
cat > /tmp/mkt-daemon.service << SVC
[Unit]
Description=mkt price daemon
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=\${CURRENT_USER}
EnvironmentFile=/etc/mkt-daemon.env
Environment=PATH=/usr/local/go/bin:/home/\${CURRENT_USER}/.local/bin:/home/\${CURRENT_USER}/.bun/bin:/usr/bin:/bin
ExecStart=/home/\${CURRENT_USER}/.local/bin/mkt daemon --listen ${MKT_LISTEN}
Restart=on-failure
RestartSec=15s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SVC

sudo cp /tmp/mkt-daemon.service /etc/systemd/system/mkt-daemon.service
sudo sed -i "s/\\\${CURRENT_USER}/\$CURRENT_USER/g" /etc/systemd/system/mkt-daemon.service
sudo systemctl daemon-reload
sudo systemctl enable mkt-daemon
sudo systemctl restart mkt-daemon
sleep 3
sudo systemctl is-active mkt-daemon && echo "  ✓ mkt-daemon running"

# ── systemd: check.ts cron (every 15 min) ─────────────────────────────────────
CURRENT_USER=\$(whoami)
cat > /tmp/mkt-check.service << SVC
[Unit]
Description=mkt alert check (one-shot)
After=network-online.target

[Service]
Type=oneshot
User=\${CURRENT_USER}
EnvironmentFile=/etc/mkt-daemon.env
Environment=PATH=/usr/local/go/bin:/home/\${CURRENT_USER}/.local/bin:/home/\${CURRENT_USER}/.bun/bin:/usr/bin:/bin
WorkingDirectory=/home/\${CURRENT_USER}/.agents/skills/mkt/scripts
ExecStart=/home/\${CURRENT_USER}/.bun/bin/bun check.ts
StandardOutput=journal
StandardError=journal
SVC

cat > /tmp/mkt-check.timer << TMR
[Unit]
Description=mkt alert check every 15 min

[Timer]
OnBootSec=2min
OnUnitActiveSec=15min
Unit=mkt-check.service

[Install]
WantedBy=timers.target
TMR

sudo cp /tmp/mkt-check.service /etc/systemd/system/mkt-check.service
sudo cp /tmp/mkt-check.timer   /etc/systemd/system/mkt-check.timer
sudo sed -i "s/\\\${CURRENT_USER}/\$CURRENT_USER/g" /etc/systemd/system/mkt-check.service
sudo systemctl daemon-reload
sudo systemctl enable --now mkt-check.timer
sudo systemctl list-timers mkt-check.timer --no-pager | head -3

# ── cloudflared ───────────────────────────────────────────────────────────────
if ! command -v cloudflared &>/dev/null; then
  echo "  installing cloudflared..."
  curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | \
    sudo gpg --dearmor -o /usr/share/keyrings/cloudflare-main.gpg
  echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared bookworm main" | \
    sudo tee /etc/apt/sources.list.d/cloudflared.list
  sudo apt-get update -qq && sudo apt-get install -y -qq cloudflared
fi
cloudflared --version

# Install tunnel as system service using token (no credentials file needed)
sudo cloudflared service install ${TUNNEL_TOKEN}
sudo systemctl restart cloudflared || sudo systemctl start cloudflared
sleep 3
sudo systemctl is-active cloudflared && echo "  ✓ cloudflared running"

echo "=== remote setup complete ==="
REMOTE

ok "remote setup done"

# ── Phase 6: Verify ───────────────────────────────────────────────────────────
log "Phase 6: verify"

# Check services on VM
SSH "sudo systemctl is-active mkt-daemon mkt-check.timer cloudflared 2>&1"

# Check tunnel is healthy via Cloudflare API
sleep 5
TUNNEL_STATUS=$(cf_api GET \
  "/accounts/$CF_ACCOUNT_ID/cfd_tunnel/$TUNNEL_ID" | \
  python3 -c "import json,sys; print(json.load(sys.stdin)['result']['status'])" 2>/dev/null || echo "unknown")
ok "Tunnel status: $TUNNEL_STATUS"

echo ""
echo "═══════════════════════════════════════════════"
echo "  ✅  mkt daemon deployed"
echo ""
echo "  API:    https://$TUNNEL_HOST"
echo "  Health: https://$TUNNEL_HOST/metrics"
echo "  Alerts: https://$TUNNEL_HOST/alerts"
echo ""
echo "  Services on VM:"
echo "    mkt-daemon      — mkt price feed + REST API"
echo "    mkt-check.timer — alert evaluation every 15 min"
echo "    cloudflared     — tunnel to $TUNNEL_HOST"
echo ""
echo "  To check logs:"
echo "    gcloud --configuration=bisonte compute ssh $VM_NAME \\"
echo "      --zone=$GCP_ZONE --project=$GCP_PROJECT \\"
echo "      --command='sudo journalctl -u mkt-daemon -n 50 --no-pager'"
echo "═══════════════════════════════════════════════"

# Cleanup
rm -f "$TMP_ALERTS" "$TMP_ENV"
