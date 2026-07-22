# Daily opportunity runner — scheduling

The runner `.agents/scripts/jobs/daily_opportunity_scan.ts` is a silent-unless-hit daily radar: regime → dip scanner → narrative velocity → convergence, posting to ntfy only when an actionable condition fires. It runs the DAILY tier only, places no orders, and only notifies.

## Where it runs: the mkt daemon VM (systemd timer)

A laptop `crontab`/`launchd` is useless (machine sleeps, not prod) and a GitHub Actions runner throttles yfinance from CI IP ranges. The scheduler lives on the always-on **mkt daemon VM** (GCP e2-micro, `mkt-daemon-alerts` project), which fetches market data cleanly and is already the fund's alert host.

- **Service:** `/etc/systemd/system/daily-opportunity-scan.service` (`Type=oneshot`, runs as `engineer`, `WorkingDirectory=/home/engineer/agents`).
- **Timer:** `/etc/systemd/system/daily-opportunity-scan.timer` — `OnCalendar=Mon-Fri 08:10:00 UTC`, `Persistent=true`.
- **Delivery:** ntfy topic `mkt-dz-wl-eb53ce91` (public, no auth). Poll it: `curl -s "https://ntfy.sh/mkt-dz-wl-eb53ce91/json?poll=1&since=12h"`.

### VM environment (baked into the service unit)

| Env | Value | Why |
|---|---|---|
| `SCAN_PYTHON` | `/home/engineer/daily-scan-venv/bin/python` | dedicated venv with yfinance (the mkt stack venv does not carry it) |
| `SCAN_REPO_ROOT` | `/home/engineer/agents` | repo checkout on the VM (old name `financial-advisor-agents`, redirects to NonFinancialAdviceAgents) |
| `NTFY_TOPIC` | `mkt-dz-wl-eb53ce91` | alert delivery topic |

### Operate it (SSH)

```bash
gcloud compute ssh mkt-daemon --account=bisonte.amigable@gmail.com --zone=us-central1-a --project=mkt-daemon-alerts

sudo systemctl start daily-opportunity-scan.service        # run once now (blocks ~70s)
systemctl list-timers daily-opportunity-scan.timer         # next elapse
sudo journalctl -u daily-opportunity-scan.service -n 40    # last run output
```

`--account=bisonte.amigable@gmail.com` is mandatory — the `bisonte` gcloud config is repointed to the wrong account.

## Delivery channels

- **ntfy** — the working channel. Zero auth, verified end-to-end from the VM.
- **Telegram** — the runner has a `postTelegram()` path gated on `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID`. It is dormant: the mkt Telegram bot token (in `~/.mkt.env` and Bitwarden `mkt-daemon/telegram-bot-token`) returns **Unauthorized** — revoked. Set a fresh bot token in the service `EnvironmentFile` to activate it.

## Running it by hand (any host with Bun + a yfinance-capable python)

```bash
SCAN_PYTHON=python3 bun .agents/scripts/jobs/daily_opportunity_scan.ts            # posts to ntfy on a hit
SCAN_PYTHON=python3 bun .agents/scripts/jobs/daily_opportunity_scan.ts --no-notify --json   # print only
```

## Known data caveat

`dip-scanner` reports yfinance **auto-adjusted** prices, so absolute levels and 52-week-high drawdowns look deflated versus raw quotes (e.g. ORCL shown near $125 / -64%). This is consistent between local and the VM — existing scanner behavior, not a deployment artifact. Percentage drawdowns are internally consistent for the dip logic; treat absolute $ as adjusted, and confirm any name against a live quote before acting.

The WEEKLY committee tier (`hedge-fund-committee-workflow`) is a separate agent-runtime job and is not part of this headless runner.
