# intraday-bot deploy — GCP e2-micro (artifacts only, nothing deployed by this task)

This directory delivers the deploy artifacts for running `bot/runner.py` as a systemd
service on a GCP e2-micro Debian instance. **Nothing in this repo actually provisions or
touches a real GCP instance or real broker credentials** — `setup_gcp.sh` is meant to be
copied to and run ON the target VM by a human operator, deliberately, after review.

## Files

- `setup_gcp.sh` — provisions Python venv, installs deps, creates a dedicated non-root
  `intraday-bot` service user, installs (but does not start) the `intraday-bot.service`
  systemd unit. Run as root on the VM: `REPO_DIR=/opt/intraday-bot bash setup_gcp.sh`.
- `requirements.txt` — minimal pinned-floor deps for the runner (pandas, numpy, requests,
  pyyaml, alpaca-py, ccxt). Deliberately smaller than the full backtest dev environment —
  e2-micro has 1GB RAM / a shared vCPU.
- This file.

## Default mode: `notify` — no secrets required

The systemd unit runs `bot/runner.py --config bot/config.yaml`, and `bot/config.yaml`
defaults to `mode: notify`. In `notify` mode the runner:
- fetches PUBLIC market data only (Alpaca crypto market data is public, no keys required;
  ccxt public REST as fallback)
- computes signals and proposed orders
- runs every order through `connectors/hard_caps.py` (deterministic, hardcoded $500-book
  caps — see `bot/caps.py`)
- writes an audit-logged, human-approvable ticket via `connectors/notify_executor.py`
- **never contacts a broker, never needs credentials**

You can run the whole pipeline on a fresh e2-micro with zero secrets configured.

## Env vars (only needed for `mode: paper` / `mode: live`)

None of these are read by `notify` mode. Set them in `/etc/intraday-bot.env` (created by
`setup_gcp.sh`, root-owned, `chmod 600`) — **never** in `config.yaml`, never committed to
git, never hardcoded in any script here.

| Var | Used by | Notes |
|---|---|---|
| `ALPACA_PAPER_KEY` / `ALPACA_PAPER_SECRET` | `mode: paper` | Alpaca **paper** account keys. No real funds. |
| `ALPACA_LIVE_KEY` / `ALPACA_LIVE_SECRET` | `mode: live` | Real Alpaca account keys. Gated — see below. |
| `CONFIRM_LIVE` | `mode: live` | Must equal today's UTC date (`YYYY-MM-DD`), set fresh each day you intend to run live. |

### Secrets convention (per house rule)

Every secret's source of truth is Bitwarden, collection `dev`. Create/rotate the Alpaca
paper/live API keys there first, then mirror into `/etc/intraday-bot.env` on the VM (or
into a local gitignored `.env` for dev). Never paste a key into a tracked file. See the
repo's `docs/secrets.md` runbook for the full process (`source ~/.env.d/bitwarden.env`
before any `bw` CLI command).

## `mode: live` — deliberately hard-gated

`bot/executor.py` reuses `connectors/notify_executor.py`'s live gate verbatim
(`_live_gate_blocks`). Live orders are refused unless **all** of:
1. `ALPACA_LIVE_KEY` env var present (checked via `VENUE_CREDS["alpaca"]`),
2. `CONFIRM_LIVE` env var equals today's UTC date (explicit daily opt-in — stale by design),
3. the order carries a `strategy_ref` naming a strategy module (backtest-before-trade),
4. `connectors/hard_caps.py` caps pass (deterministic, cannot be overridden by config/LLM).

Even when all four hold, actual live order placement in `bot/executor.py` still routes
through the SAME caps + audit path as paper/notify — there is no separate unaudited live
code path.

## Systemd unit

Installed at `/etc/systemd/system/intraday-bot.service` by `setup_gcp.sh`. Runs as the
dedicated `intraday-bot` system user (never root), working directory
`${REPO_DIR}/intraday-bot`, `EnvironmentFile=-/etc/intraday-bot.env` (the leading `-` makes
the file optional — the unit still starts in `notify` mode if it's absent/empty).

```bash
sudo systemctl enable --now intraday-bot.service   # start + enable on boot
journalctl -u intraday-bot -f                       # tail logs
sudo systemctl stop intraday-bot.service            # stop
touch /opt/intraday-bot/intraday-bot/.KILL          # emergency kill switch (checked every cycle)
```

## State / journal

`bot/state/{orders,positions,cycles}.jsonl` — append-only, survives restarts, gives
idempotent replay (see `bot/state_store.py`). Back this up or ship it off-instance
periodically if you care about historical audit continuity; it is not required for
correctness (the runner reconstructs current state by replaying it on every boot).

## What this deploy does NOT do

- Does not create a GCP project, VM, or firewall rule — provisioning the actual instance
  (`gcloud compute instances create ...`) is an explicit, separate operator action outside
  this task's scope.
- Does not create or touch any real Alpaca account.
- Does not set `mode: live` or `CONFIRM_LIVE` for you — that is a deliberate, daily,
  human action.

Educational analysis, not financial advice.
