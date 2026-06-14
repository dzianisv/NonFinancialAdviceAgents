# Proactive Advisor on Claude Code

Native primitives: **`claude -p` headless** (one-shot agent run) + **system crontab** (schedule) +
**dynamic workflows** (the heavy weekly fan-out). Claude Code has no daemon — cron is the wake-up.

## 1. Install skills

```bash
npx -y skills add dzianisv/backtest --agent claude-code
ls ~/.claude/skills/   # dip-screener, crypto-dip-scanner, regime-detection, ... present
```

## 2. The wake-up pattern: cron → `claude -p`

Each scheduled job is a headless run with a `/skill` in the prompt and a pre-approved toolset.
`--bare` keeps it deterministic (skips local hook/MCP discovery).

```bash
# scripts/run-skill.sh
#!/usr/bin/env bash
set -euo pipefail
cd "$HOME/workspace/backtest"
PROMPT="$1"
claude --bare -p "$PROMPT" \
  --allowedTools "Bash,Read,Write,WebFetch,WebSearch" \
  --append-system-prompt "You are a RECOMMEND-ONLY investment advisor. Never trade. Never fabricate a number — emit [UNAVAILABLE] on failure. DM-style output only when an alert condition fires; otherwise print SILENT." \
  --output-format text
```

## 3. crontab (the schedule)

```cron
# m  h  dom mon dow   command   (all UTC — set CRON_TZ=UTC)
CRON_TZ=UTC
45  7  *   *   1-5   ~/workspace/backtest/scripts/run-skill.sh "/dip-screener: scan S&P100, check regime first, alert only HIGH dips in RISK_ON"            >> ~/advisor.log 2>&1
50  7  *   *   1-5   ~/workspace/backtest/scripts/run-skill.sh "/crypto-dip-scanner: alert only if a coin >=-30% from ATH AND Fear&Greed<25"               >> ~/advisor.log 2>&1
0   8  *   *   1-5   ~/workspace/backtest/scripts/run-skill.sh "/regime-detection + /fomc-monitor: DM one paragraph only if regime flipped or Fed moved"   >> ~/advisor.log 2>&1
15  8  *   *   1-5   ~/workspace/backtest/scripts/run-skill.sh "/trend-stock-research broad: append catalyst tickers to /tmp/narrative.jsonl. No alert."   >> ~/advisor.log 2>&1
30  8  *   *   1-5   ~/workspace/backtest/scripts/run-skill.sh "/signal-convergence-alert: DM if any ticker hit by >=2 independent signals today"          >> ~/advisor.log 2>&1
30  9  *   *   1     ~/workspace/backtest/scripts/weekly-brief.sh                                                                                          >> ~/advisor.log 2>&1
```

`SILENT` lines are dropped by a wrapper; any non-SILENT output is piped to your notifier (Telegram CLI,
`osascript` notification, email — your choice). Example tail of `run-skill.sh`:
```bash
OUT=$(claude --bare -p "$PROMPT" ...)
[ "${OUT//[[:space:]]/}" = "SILENT" ] || python3 ~/.claude/skills/telegram-cli-tool/telegram-cli.py send @you "$OUT"
```

## 4. The weekly brief = a dynamic workflow (fan-out)

The weekly synthesis is heavy (quorum = N independent lenses). Use a **workflow** so the lenses run in
parallel and only the verdict returns. `weekly-brief.sh`:
```bash
#!/usr/bin/env bash
cd "$HOME/workspace/backtest"
claude -p "Run the weekly investment brief as a workflow: collect regime+fed+13F+congress+narrative
pool, cross-reference candidates, run multi-lens-quorum on the top 5 IN PARALLEL (one agent per lens),
apply risk-management veto, synthesize the INVESTMENT BRIEF. ultracode" \
  --allowedTools "Bash,Read,Write,WebFetch,WebSearch" --output-format text \
  | python3 ~/.claude/skills/telegram-cli-tool/telegram-cli.py send @you -
```
The `ultracode` keyword makes Claude author + run a workflow (parallel quorum lenses, adversarial
cross-check) instead of a serial pass. Save the run as `/weekly-brief` (`/workflows` → `s`) to reuse it.

A reference workflow script is in `.agents/setup/weekly-brief.workflow.js` — load via
`/workflows` or `claude` Workflow tool with `{scriptPath}`.

## 5. Auth for headless

`claude -p` on a schedule needs non-interactive auth: `ANTHROPIC_API_KEY` in the cron environment
(or an `apiKeyHelper` in `--settings`). Subscription-plan headless usage draws from the Agent SDK
credit (effective 2026-06-15).

## Done when
- [ ] `~/.claude/skills/` has all skills.
- [ ] `run-skill.sh` returns SILENT or a real alert (test: `bash scripts/run-skill.sh "/dip-screener ..."`).
- [ ] crontab installed (`crontab -l` shows 6 jobs, CRON_TZ=UTC).
- [ ] Weekly job runs a workflow and DMs the brief.
