# Setup: AI Investment Advisor on OpenClaw

**How to use this:** paste the prompt block below to your openclaw **investor** agent in one message.
The *agent* installs its own skills and registers its own cron jobs using its native tools. You do not
run anything yourself, and nobody hand-edits the bot's internals.

> Recommend-only / educational. The agent never trades. Native primitive = **agent cron** (the agent's
> own `cron create` tool — NOT by editing `jobs.json`); heartbeat is only a light stuck-task nudge.

---

## 📋 PASTE THIS TO YOUR OPENCLAW INVESTOR AGENT

```text
Set yourself up as my AI investment advisor (recommend-only, educational, never trade). Do each step,
then report what you did. Use YOUR OWN native cron tool to register jobs — do NOT hand-edit jobs.json.

STEP 1 — INSTALL SKILLS. One command pulls every skill + its .py helpers (openclaw is a first-class
target of the skills installer; --copy ships the Python files, not just SKILL.md):
  npx -y skills add dzianisv/backtest --agent openclaw --copy --dangerously-accept-openclaw-risks
  Confirm the install listed dip-screener, crypto-dip-scanner, signal-convergence-alert,
  liveness-monitor, trend-stock-research, regime-detection (and the rest).
  Then create the durable pool dir the cron sessions share (NOT /tmp):
  mkdir -p ~/.openclaw/workspace/investor/pools
  (Skills install under your openclaw skills dir; reference the .py helpers there in the cron jobs below
  — adjust $S to that path.)

STEP 2 — VERIFY one skill actually runs (don't just trust the file). Run:
  python3 $S/crypto-dip-scanner/crypto_dip_scanner.py --json
  Expect real JSON with high_52w_usd + pct_from_high + a fear_greed value. If it fabricates a number
  or errors, STOP and tell me — do not schedule a broken skill.

STEP 3 — REGISTER CRON JOBS with your native cron tool (all UTC, SILENT-unless-alert). Each daily scan
must end by logging a heartbeat so a silent outage is detectable:
  • "Daily stock dip scan"  45 7 * * 1-5 :
      Run python3 $S/dip-screener/dip_screener.py --json --emit-pool AND regime-detection.
      DM me ONLY if a HIGH dip (pct_from_high<=-30) AND regime=RISK_ON. Else NO_REPLY.
      Then: python3 $S/liveness-monitor/liveness.py log --job dip-screener --detail "<summary>".
  • "Daily crypto dip scan"  50 7 * * * :
      Run python3 $S/crypto-dip-scanner/crypto_dip_scanner.py --json. DM ONLY if any coin
      pct_from_high<=-30 AND fear_greed.value<25. Else NO_REPLY. Then liveness log --job crypto-dip-scanner.
  • "Daily narrative velocity"  10 8 * * 1-5 :
      Run python3 $S/trend-stock-research/mention_velocity.py --json (auto-feeds the convergence pool).
      Collect only, do NOT DM. Then liveness log --job narrative-velocity.
  • "Daily signal convergence"  30 8 * * 1-5 :
      Run python3 $S/signal-convergence-alert/convergence.py --json --min-sources 2. DM ONLY if any
      ticker n_sources>=2 (note: sources may be correlated). Else NO_REPLY. Then liveness log --job signal-convergence.
  • "Advisor health check"  0 9 * * 1-5 :
      Run python3 $S/liveness-monitor/liveness.py check --expect dip-screener,crypto-dip-scanner,signal-convergence,narrative-velocity --max-age-hours 26.
      If STALE, DM me "⚠️ advisor jobs stale:" + the list. If ALL_FRESH, NO_REPLY.
  • "Weekly hedge-fund committee"  30 9 * * 1 :  (the main decision engine — find next buys)
      Run the WEEKLY HEDGE-FUND COMMITTEE: (1) ANALYSTS gather (regime+fomc, analyse-smartmoney-13f new buys,
      analyse-smartmoney-ptr 90d, trend-stock-research themes, dip_screener.py --json, crypto-dip-scanner
      --json) — real evidence, mark [unverified], never fabricate. (2) AGGREGATE by ticker; n_sources =
      crowdedness NOT independence; flag flow_only (13F/congress-only = 30-45d lagged, down-weight); top 5.
      (3) PANEL: each top-5 gets an INDEPENDENT verdict from investor-warren-buffett,
      investor-stanley-druckenmiller, research-lacy-hunt (deflation/dissent), analyse-fundamental (verdict+conviction+
      reason+invalidation; no anchoring). (4) DISSENT: quote the strongest opposing vote per name verbatim;
      never average it away; unanimous = a flag. (5) RISK: risk-management VETO if RISK_OFF or >10% book;
      else PASS with a size CEILING (no portfolio supplied → never invent existing weights). (6) DM a RANKED
      BUY LIST: per name decision/conviction/size-ceiling/invalidation + the dissent + a "could not verify"
      section; state 13F 45d / STOCK Act 30-45d lag. (7) forecast-ledger add each idea (+90d), then
      forecast-ledger score+report and include the hit-rate-by-source scorecard. (8) liveness log --job weekly-committee.

STEP 4 — CONFIRM: list your registered cron jobs (with ids) and the installed skills. Tell me anything
that failed. Do not claim a job is registered unless your cron tool returned an id for it.
```

---

## Notes (for you, the operator — not part of the paste)

- **Why the agent self-registers:** using the agent's native `cron create` tool registers jobs in the
  scheduler properly (returns an id). Hand-editing `~/.openclaw/cron/jobs.json` from outside can leave the
  in-memory scheduler stale until a gateway restart — avoid it.
- **Agent sandbox vs `kubectl exec`:** the agent's bash (`HOME=/home/node`) has python3.12 + yfinance +
  Yahoo. The `kubectl exec` container does not — never validate skills there.
- **heartbeat:** leave `agents.defaults.heartbeat` as a light nudge; do NOT put the scans in a `HEARTBEAT.md`
  (cron owns the schedule; a scan-running heartbeat double-fires).
- **Two tiers:** the daily jobs are the FAST alert tier; the weekly committee is the SLOW decision engine
  (the ranked next-buy memo). See `docs/tdd.md` §8.

## Done when
- [ ] Agent reports skills installed + one verified `--json` run (no fabrication).
- [ ] Agent's cron tool returned ids for all 6 jobs (5 daily + weekly committee).
- [ ] Health check is registered (so a silent outage is caught within ~26h).
- [ ] Weekly committee logs to forecast-ledger.
