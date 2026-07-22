# Daily opportunity runner — scheduling

The runner `.agents/scripts/jobs/daily_opportunity_scan.ts` is a silent-unless-hit daily radar: regime → dip scanner → narrative velocity → convergence, posting to ntfy only when an actionable condition fires. It runs the DAILY tier only, places no orders, and only notifies.

## Where it runs: GitHub Actions (not a laptop cron)

A local `crontab`/`launchd` job on a dev laptop is useless — the machine sleeps and is not production. The scheduler lives in the repo as a GitHub Actions workflow:

- **File:** `.github/workflows/daily-opportunity-scan.yml`
- **Schedule:** `10 8 * * 1-5` (~08:10 UTC, weekdays). GitHub runs scheduled workflows on the **default branch (`main`) only**, so the workflow is inert until merged — safe to commit on a feature branch.
- **Manual run:** `workflow_dispatch` (Actions tab → "Run workflow"), with a `no_notify` toggle for print-only smoke tests.

### First run: smoke-test before trusting the schedule

yfinance/crypto fetches can be rate-limited from cloud/CI IP ranges. Before relying on the cron, trigger it manually once (`workflow_dispatch`) and read the run log:

- All four steps `ok` → schedule is trustworthy.
- `[DEGRADED] regime`/`dip_scanner` (regime falls back to `UNKNOWN`) → GitHub runner IPs are being throttled. Move the job to an always-on host that fetches cleanly (e.g. the mkt daemon VM) instead of leaving a blind daily run.

## Configuration

| Where | Key | Default | Purpose |
|---|---|---|---|
| repo secret | `NTFY_TOPIC` | `mkt-dz-wl-eb53ce91` | ntfy topic for alert delivery |
| repo variable | `SCAN_WATCHLIST` | _(unset → semiconductor/AI core list)_ | comma-separated narrative watchlist override |
| workflow env | `SCAN_PYTHON` | `python3` | Python interpreter (the script defaults to the laptop venv locally) |
| workflow env | `SCAN_REPO_ROOT` | repo checkout | only used to locate `universe.txt` |

## Running it by hand (any host with Bun + a yfinance-capable python)

```bash
SCAN_PYTHON=python3 bun .agents/scripts/jobs/daily_opportunity_scan.ts            # posts to ntfy on a hit
SCAN_PYTHON=python3 bun .agents/scripts/jobs/daily_opportunity_scan.ts --no-notify --json   # print only
```

The WEEKLY committee tier (`hedge-fund-committee-workflow`) is a separate agent-runtime job — see `docs/setup-openclaw.md` — and is not part of this headless runner.
