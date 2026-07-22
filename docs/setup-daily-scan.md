# Daily opportunity runner

The runner `.agents/scripts/jobs/daily_opportunity_scan.ts` is a silent-unless-hit daily radar: regime → dip scanner → narrative velocity → convergence, posting to ntfy only when an actionable condition fires. It runs the DAILY tier only, places no orders, and only notifies.

## Scheduling rule: Hermes only — never an OS/system scheduler

Do NOT schedule this (or any) job with cron, systemd timers, launchd, or a CI cron (GitHub Actions). All of those were tried and rejected. The only sanctioned scheduler is the **Hermes AI agent** (`@AflredAiBot`), driven via `telegram-cli`.

Hermes cannot execute this scan itself (no Bun on its host; its market-data fetches fail provider-auth). So scheduling and execution are split:

- **Scheduler:** a Hermes cron (the sanctioned surface).
- **Executor:** a host with Bun + a yfinance-capable Python, triggered on demand by Hermes — never self-scheduled by an OS timer.

The on-demand trigger from Hermes to the executor is the open design item. Until it is wired, run the scan by hand (below).

## Running it by hand (any host with Bun + a yfinance-capable python)

```bash
SCAN_PYTHON=python3 bun .agents/scripts/jobs/daily_opportunity_scan.ts            # posts to ntfy on a hit
SCAN_PYTHON=python3 bun .agents/scripts/jobs/daily_opportunity_scan.ts --no-notify --json   # print only
```

Env: `SCAN_PYTHON` (yfinance-capable interpreter), `SCAN_REPO_ROOT` (repo root, for `universe.txt`), `NTFY_TOPIC` (default `mkt-dz-wl-eb53ce91`).

## Delivery channels

- **ntfy** — the working channel. Zero auth. Subscribe: `https://ntfy.sh/mkt-dz-wl-eb53ce91`.
- **Telegram** — the runner has a `postTelegram()` path gated on `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID`. Dormant: the mkt Telegram bot token (`~/.mkt.env` and Bitwarden `mkt-daemon/telegram-bot-token`) returns Unauthorized (revoked). Set a fresh token to activate.

## Known data caveat

`dip-scanner` reports yfinance **auto-adjusted** prices, so absolute levels and 52-week-high drawdowns look deflated versus raw quotes (e.g. ORCL near $125 / -64%). This is consistent across hosts — existing scanner behavior, not a runner artifact. Percentage drawdowns are internally consistent; treat absolute $ as adjusted and confirm any name against a live quote before acting.

The WEEKLY committee tier (`hedge-fund-committee-workflow`) is a separate agent-runtime job and is not part of this headless runner.
