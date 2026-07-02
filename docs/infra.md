# infra: mkt daemon

## What

`mkt daemon` — headless price + alert engine. Watches 160+ symbols, evaluates alert jobs every 5 min, sends Telegram notifications.

Public API: `https://mkt.agentlabs.cc` (Cloudflare Tunnel — no open VM ports).

---

## Accounts

Both GCP and Cloudflare use **bisonte.amigable@gmail.com** (separate from primary vibeteaichnologies@gmail.com).

| Resource | Account | ID |
|---|---|---|
| GCP project | bisonte.amigable@gmail.com | `mkt-daemon-alerts` |
| Cloudflare zone | bisonte.amigable@gmail.com | zone `5fbeec0aa0dca842ab3b62fafb948fe9`, account `c52033a95d560a9a183b016ceb1c107a` |

---

## VM

| Field | Value |
|---|---|
| Name | `mkt-daemon` |
| Zone | `us-central1-a` |
| Type | `e2-micro` (free tier) |
| OS | Debian 12 |
| External IP | `8.34.215.229` (ephemeral) |

---

## SSH access

No separate SSH keys. gcloud manages keys automatically.

```bash
gcloud compute ssh mkt-daemon \
  --zone=us-central1-a \
  --project=mkt-daemon-alerts \
  --configuration=bisonte
```

`--configuration=bisonte` is required — isolates from the default gcloud account.

---

## Cloudflare Tunnel

- Tunnel name: `mkt-daemon`  
- Tunnel ID: `160e0def-c30f-40d6-9528-49dc9f23b7c3`  
- DNS: `mkt.agentlabs.cc CNAME → 160e0def-...cfargotunnel.com` (proxied)  
- Ingress: all traffic to `mkt.agentlabs.cc` → `http://localhost:8080` on VM  
- Token: in Bitwarden dev collection as `mkt-daemon-cf-tunnel-token`

---

## Services on VM

| Unit | Command | Role |
|---|---|---|
| `cloudflared.service` | `cloudflared tunnel run --token ...` | Tunnel to Cloudflare edge |
| `mkt-http.service` | `mkt --listen :8080 daemon` | Price engine + HTTP API |
| `mkt-check.timer` | `bun run check.ts` every 5 min | Evaluate alerts, send notifications |
| `intraday-bot.service` | `/opt/intraday-bot/.venv/bin/python3 bot/runner.py --config bot/config.yaml` | Shadow forward-test, notify mode — see [intraday-bot section](#intraday-bot-shadow-notify-mode) |

Env/secrets: `/home/engineer/.mkt.env` (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID).

```bash
# Check all three
gcloud compute ssh mkt-daemon --zone=us-central1-a --project=mkt-daemon-alerts --configuration=bisonte \
  --command="sudo systemctl status cloudflared mkt-http mkt-check.timer --no-pager"
```

---

## API endpoints

No auth — Cloudflare proxies all traffic (HTTPS termination at CF edge). VM port 8080 is NOT exposed externally (no GCP firewall rule).

| Endpoint | Description |
|---|---|
| `GET /metrics` | Prometheus: uptime, symbols cached, alert count |
| `GET /quotes` | All cached quotes |
| `GET /quotes/{sym}` | Single symbol (e.g. `/quotes/BTC-USD`) |
| `GET /alerts` | Current mkt-native alert rules |

```bash
curl https://mkt.agentlabs.cc/metrics
curl https://mkt.agentlabs.cc/quotes/BTC-USD
```

---

## Managing alerts (add / list / remove)

Alert jobs live in `~/.config/mkt/agent-alerts.json` on the VM.  
Use `mkt-alert.ts` from the agents repo:

```bash
# SSH and run directly
gcloud compute ssh mkt-daemon --zone=us-central1-a --project=mkt-daemon-alerts --configuration=bisonte \
  --command="cd ~/agents/.agents/skills/mkt/scripts && bun mkt-alert.ts list"

# Add alert
gcloud compute ssh mkt-daemon ... \
  --command="cd ~/agents/.agents/skills/mkt/scripts && \
    bun mkt-alert.ts add \
      --symbol BTC-USD \
      --condition below \
      --threshold 90000 \
      --channel telegram-bot:@CryptoAiInvestor \
      --reasoning 'Support break — exit signal'"

# Remove alert by ID
gcloud compute ssh mkt-daemon ... \
  --command="cd ~/agents/.agents/skills/mkt/scripts && bun mkt-alert.ts remove <id>"

# Sync local alert jobs → VM
gcloud compute scp .cache/mkt/agent-alerts.json \
  mkt-daemon:~/.config/mkt/agent-alerts.json \
  --zone=us-central1-a --project=mkt-daemon-alerts --configuration=bisonte
```

---

## Security

- **No open ports on VM** — GCP firewall has no rules for port 9999. Only cloudflared (outbound QUIC to CF edge).
- **HTTPS only** — Cloudflare terminates TLS at edge; VM sees plain HTTP on loopback.
- **No API auth** — read-only metrics/quotes. Add `--listen-token` flag to `ExecStart` if needed.
- **Secrets in Bitwarden** (dev collection) — deploy.sh reads them at deploy time, writes to `/etc/mkt-daemon.env` (mode 600) on VM. Never in repo.

| Bitwarden item | Content |
|---|---|
| `mkt-daemon/cf-tunnel-token` | Cloudflare Tunnel token (tunnel ID: `160e0def-...`) |
| `mkt-daemon/telegram-bot-token` | Telegram bot token for alert notifications |

---

## Files on VM

```
~/.mkt.env                              secrets (600)
~/.local/bin/mkt                        binary (stxkxs/mkt@0207dda)
~/.local/src/mkt/                       source
~/agents/                               financial-advisor-agents (git pull to update)
  .agents/skills/mkt/scripts/check.ts   alert checker
~/.config/mkt/agent-alerts.json        active alert jobs
/etc/cloudflared/config.yml            tunnel ingress rules
/etc/systemd/system/mkt-http.service
/etc/systemd/system/mkt-check.service
/etc/systemd/system/mkt-check.timer
```

---

## Update / redeploy

```bash
# Pull latest agents code
gcloud compute ssh mkt-daemon --zone=us-central1-a --project=mkt-daemon-alerts --configuration=bisonte \
  --command="cd ~/agents && git pull && sudo systemctl restart mkt-http"

# Full redeploy from scratch
bash infra/mkt-daemon/deploy.sh
```

---

## intraday-bot (shadow, notify mode)

**IMPORTANT: this strategy FAILED its backtest gate.** It runs here ONLY as a forward
shadow/paper-free test — it fetches public market data, computes a signal, and LOGS a
proposed order to a local jsonl file. It holds no broker credentials and never contacts
a broker API. It must never be flipped to `mode: paper` or `mode: live` without a fresh
gate PASS and explicit human sign-off.

It shares the `mkt-daemon` VM (see [VM](#vm) above) but is a fully separate systemd unit,
separate service user, separate deploy path. It does not touch `cloudflared`, `mkt-http`,
`mkt-daemon`, `mkt-api`, or any of their config/timers.

| Field | Value |
|---|---|
| Unit | `intraday-bot.service` |
| Service user | `intraday-bot` (dedicated, `nologin` shell, least-privilege) |
| Deploy path | `/opt/intraday-bot` (`connectors/` and `intraday-bot/` as siblings — required by `bot/caps.py` / `bot/executor.py` path resolution) |
| Venv | `/opt/intraday-bot/.venv` |
| Mode | `notify` (market-data read + local log only, no broker calls) |
| Strategy | `regime_sma_maker`, `sma_window: 50`, symbols `[BTC/USD]` only |
| Cadence | `interval: 1d`, `poll_seconds: 3600` |
| Kill switch | `/opt/intraday-bot/intraday-bot/.KILL` (any file at that path — content ignored) |
| Drop-in | `/etc/systemd/system/intraday-bot.service.d/10-unbuffered.conf` sets `PYTHONUNBUFFERED=1` so cycle output reaches journalctl in real time (added post-`setup_gcp.sh`; recreate it on any redeploy) |

**ETH-dropped caveat:** `regime_sma_maker` reads `strategy_params` globally (one
`sma_window` applied to every symbol in the run), it does not support per-symbol
params. BTC's gate-selected/June-tested window is 50; ETH would need a different
window and can't coexist in the same config. ETH/USD was dropped from `symbols:`
rather than run it under BTC's window.

```bash
gcloud compute ssh mkt-daemon --zone=us-central1-a --project=mkt-daemon-alerts --configuration=bisonte \
  --command="journalctl -u intraday-bot -f"
```

External IP is ephemeral (see [VM](#vm)) — always connect via `gcloud compute ssh`
with `--configuration=bisonte`, never a hardcoded IP.

Kill switch usage (halts the next cycle, does not affect `mkt-*` units):

```bash
gcloud compute ssh mkt-daemon --zone=us-central1-a --project=mkt-daemon-alerts --configuration=bisonte \
  --command="sudo -u intraday-bot touch /opt/intraday-bot/intraday-bot/.KILL"

# resume
gcloud compute ssh mkt-daemon --zone=us-central1-a --project=mkt-daemon-alerts --configuration=bisonte \
  --command="sudo rm /opt/intraday-bot/intraday-bot/.KILL"
```

State/audit trail (both notify-only, no orders sent anywhere):

```
/opt/intraday-bot/intraday-bot/bot/state/cycles.jsonl   # every cycle's signal + status
/opt/intraday-bot/connectors/audit_log.jsonl            # only written when an order is proposed
```

Full deploy details: `intraday-bot/deploy/README-DEPLOY.md` and
`intraday-bot/deploy/setup_gcp.sh` in the backtest repo.
