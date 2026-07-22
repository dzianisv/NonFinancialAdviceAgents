# Daily opportunity runner (host-agnostic)

This runner executes a silent-unless-hit daily opportunity radar: regime → dip scanner → narrative velocity → convergence, then posts alerts to ntfy only when actionable conditions fire. It runs the DAILY tier only, does not place orders, and only notifies.

## Cron (weekdays, ~08:10 UTC)

```bash
mkdir -p logs
10 8 * * 1-5 cd /Users/engineer/workspace/backtest && /Users/engineer/.bun/bin/bun .agents/scripts/jobs/daily_opportunity_scan.ts >> logs/daily_opportunity_scan.log 2>&1
```

## macOS launchd (alternative to cron)

Cron is fine if the machine is always on. If you prefer launchd, use a plist like:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key><string>com.backtest.daily-opportunity-scan</string>
    <key>ProgramArguments</key>
    <array>
      <string>/Users/engineer/.bun/bin/bun</string>
      <string>/Users/engineer/workspace/backtest/.agents/scripts/jobs/daily_opportunity_scan.ts</string>
    </array>
    <key>WorkingDirectory</key><string>/Users/engineer/workspace/backtest</string>
    <!-- One dict per weekday: launchd fires only on the exact Weekday given,
         so Mon-Fri (1-5) needs five entries to match the cron `1-5` schedule. -->
    <key>StartCalendarInterval</key>
    <array>
      <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>8</integer><key>Minute</key><integer>10</integer></dict>
      <dict><key>Weekday</key><integer>2</integer><key>Hour</key><integer>8</integer><key>Minute</key><integer>10</integer></dict>
      <dict><key>Weekday</key><integer>3</integer><key>Hour</key><integer>8</integer><key>Minute</key><integer>10</integer></dict>
      <dict><key>Weekday</key><integer>4</integer><key>Hour</key><integer>8</integer><key>Minute</key><integer>10</integer></dict>
      <dict><key>Weekday</key><integer>5</integer><key>Hour</key><integer>8</integer><key>Minute</key><integer>10</integer></dict>
    </array>
    <key>StandardOutPath</key><string>/Users/engineer/workspace/backtest/logs/daily_opportunity_scan.log</string>
    <key>StandardErrorPath</key><string>/Users/engineer/workspace/backtest/logs/daily_opportunity_scan.log</string>
  </dict>
</plist>
```

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `NTFY_TOPIC` | `mkt-dz-wl-eb53ce91` | ntfy topic for alert POST delivery. |
| `SCAN_WATCHLIST` | _(unset)_ | Comma-separated ticker override for the narrative watchlist. |

The WEEKLY committee tier (`hedge-fund-committee-workflow`) is a separate agent-runtime job — see `docs/setup-openclaw.md` — and is not part of this headless runner.

This runs the DAILY tier only; it does not place orders; it only notifies.
