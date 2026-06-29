# Infrastructure — mkt daemon

## Overview

`mkt daemon` runs on a free-tier GCP e2-micro VM, exposed publicly at
`https://mkt.agentlabs.cc` via a Cloudflare Tunnel (no open firewall ports needed).

---

## Accounts

| Resource | Account | Notes |
|---|---|---|
| Cloudflare (agentlabs.cc) | bisonte.amigable@gmail.com | zone `5fbeec0aa0dca842ab3b62fafb948fe9`, account `c52033a95d560a9a183b016ceb1c107a` |
| GCP project | bisonte.amigable@gmail.com | project `mkt-daemon-alerts`, billing `01BFB1-83821D-942EE8` |

**Important:** these are separate from the primary dev accounts (`vibeteaichnologies@gmail.com` GCP). Use `--configuration=bisonte` on all `gcloud` commands.

---

## GCP VM

| Field | Value |
|---|---|
| Name | `mkt-daemon` |
| Zone | `us-central1-a` |
| Machine | `e2-micro` (free tier — us-central1 only) |
| OS | Debian 12 (Bookworm) |
| External IP | `8.34.215.229` (ephemeral) |
| SSH | `gcloud compute ssh mkt-daemon --zone=us-central1-a --project=mkt-daemon-alerts --configuration=bisonte` |

---

## Cloudflare Tunnel

| Field | Value |
|---|---|
| Tunnel name | `mkt-daemon` |
| Tunnel ID | `160e0def-c30f-40d6-9528-49dc9f23b7c3` |
| Public URL | `https://mkt.agentlabs.cc` |
| DNS record | `mkt.agentlabs.cc CNAME 160e0def-c30f-40d6-9528-49dc9f23b7c3.cfargotunnel.com` (proxied) |
| Ingress | `mkt.agentlabs.cc → http://localhost:8080` |

Token stored in Bitwarden under `dev` collection (name: `mkt-daemon-cf-tunnel-token`).

---

## Services on VM

| Service | Description |
|---|---|
| `cloudflared.service` | Cloudflare Tunnel daemon — routes `mkt.agentlabs.cc` → `:8080` |
| `mkt-http.service` | `mkt --listen :8080 daemon` — price engine + HTTP API |
| `mkt-check.timer` | Every 5 min: `bun run check.ts` — evaluates alert jobs, fires notifications |

```bash
# Check status
gcloud compute ssh mkt-daemon --zone=us-central1-a --project=mkt-daemon-alerts --configuration=bisonte \
  --command="sudo systemctl status cloudflared mkt-http mkt-check.timer --no-pager"
```

---

## mkt HTTP API (internal + public)

| Endpoint | Description |
|---|---|
| `GET /metrics` | Prometheus metrics (uptime, symbols cached, alert rules) |
| `GET /quotes` | All cached quotes |
| `GET /quotes/{sym}` | Single symbol quote |
| `GET /alerts` | Current alert rules |
| `POST /webhook/tradingview` | TradingView webhook receiver |

Verify: `curl https://mkt.agentlabs.cc/metrics`

---

## File layout on VM

```
~/agents/                     # financial-advisor-agents repo (git pull to update)
  .agents/skills/mkt/scripts/
    check.ts                  # alert checker (run by mkt-check.timer)
    store.ts                  # AlertJob store
    mkt-alert.ts              # CLI to add/list/remove alert jobs
~/mkt/                        # mkt source (stxkxs/mkt@0207dda)
~/.local/bin/mkt              # compiled binary
~/.mkt.env                    # secrets (TELEGRAM_BOT_TOKEN, etc.)
```

---

## Deploy / Redeploy

```bash
bash infra/mkt-daemon/deploy.sh
```

Script is idempotent — skips already-created resources.  
Source: `infra/mkt-daemon/deploy.sh`

---

## Alert jobs

Stored in `~/.config/mkt/agent-alerts.json` on the VM (and locally in `.cache/mkt/agent-alerts.json`).  
To sync local jobs to VM:

```bash
gcloud compute scp .cache/mkt/agent-alerts.json mkt-daemon:~/.config/mkt/agent-alerts.json \
  --zone=us-central1-a --project=mkt-daemon-alerts --configuration=bisonte
```

To add a new alert from the VM:
```bash
gcloud compute ssh mkt-daemon --zone=us-central1-a --project=mkt-daemon-alerts --configuration=bisonte \
  --command="cd ~/agents/.agents/skills/mkt/scripts && bun mkt-alert.ts add --symbol BTC-USD ..."
```
