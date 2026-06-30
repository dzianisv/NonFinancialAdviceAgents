# Setup: AI Investment Advisor on Hermes-AI

**How to use this:** paste the prompt block below to your Hermes investor agent in one message. The
*agent* installs its skills and registers its own cron jobs via Hermes' native cron (`/cron add` /
`hermes cron create`). Same recommend-only skills as the other backends.

> Recommend-only / educational. Native primitive = **hermes cron** (`~/.hermes/cron/jobs.json`, ticks
> every 60s, fresh agent session per job, `[SILENT]` suppresses delivery on healthy runs).

---

## 📋 PASTE THIS TO YOUR HERMES INVESTOR AGENT

```text
Set yourself up as my AI investment advisor (recommend-only, educational, never trade). Do each step,
then report. Use Hermes' native cron (/cron add) to register jobs — they run in fresh sessions, so each
prompt must be self-contained. Emit [SILENT] when a job has nothing to report.

STEP 1 — INSTALL SKILLS (include the .py helpers, not just SKILL.md):
  npx -y skills add dzianisv/backtest --agent hermes-agent --copy
  Then: hermes skills list  — confirm dip-screener, crypto-dip-scanner, signal-convergence-alert,
  liveness-monitor, trend-stock-research, regime-detection, feed-fomc, analyse-smartmoney-13f,
  analyse-smartmoney-ptr, multi-lens-quorum, risk-management, forecast-ledger appear.
  Create a durable pool dir: mkdir -p ~/.openclaw/workspace/investor/pools
  (or set $DIP_POOL/$NARRATIVE_POOL env to a persistent path your cron sessions share — NOT /tmp).

STEP 2 — VERIFY one runs: python3 <skills>/crypto-dip-scanner/crypto_dip_scanner.py --json
  Expect real JSON (high_52w_usd, pct_from_high, fear_greed). If it fabricates/errors, STOP and tell me.

STEP 3 — REGISTER CRON (all UTC; each daily job ends by logging liveness; [SILENT] unless it fires):
  • dip "45 7 * * 1-5":  run dip_screener.py --json --emit-pool + regime-detection; alert only HIGH dip
    (pct_from_high<=-30) in RISK_ON; else [SILENT]; then liveness.py log --job dip-screener.
  • crypto "50 7 * * *":  crypto_dip_scanner.py --json; alert only if coin pct_from_high<=-30 AND
    fear_greed.value<25; else [SILENT]; then liveness.py log --job crypto-dip-scanner.
  • narrative "10 8 * * 1-5":  mention_velocity.py --json (auto-feeds pool); collect only; liveness log.
  • convergence "30 8 * * 1-5":  convergence.py --json --min-sources 2; alert only if n_sources>=2
    (sources may be correlated); else [SILENT]; liveness log --job signal-convergence.
  • health "0 9 * * 1-5":  liveness.py check --expect dip-screener,crypto-dip-scanner,signal-convergence,narrative-velocity --max-age-hours 26; alert only if STALE.
  • weekly committee "30 9 * * 1":  run the WEEKLY HEDGE-FUND COMMITTEE — analysts gather (regime+fomc,
    analyse-smartmoney-13f, analyse-smartmoney-ptr 90d, trend-stock-research, dip + crypto scanners) → aggregate by
    ticker (n_sources=crowdedness; flag flow_only 13F/congress as 30-45d lagged) → top 5 → each gets an
    INDEPENDENT verdict from buffett/druckenmiller/lacy-hunt(dissent)/fundamental → quote the strongest
    opposing vote verbatim → risk-management VETO (RISK_OFF or >10% book) else size CEILING (never invent
    book weights) → DM a RANKED BUY LIST + dissent + "could not verify" + 13F/STOCK-Act lag → forecast-ledger
    add+score+report. Then liveness.py log --job weekly-committee.

STEP 4 — SET THE MANDATE: load the contents of .agents/templates/AGENTS.template.md into your standing
system prompt so the recommend-only mandate + committee pipeline persists across fresh cron sessions.

STEP 5 — CONFIRM: hermes cron list + hermes skills list; report anything that failed.
```

---

## Notes (operator — not part of the paste)
- Hermes cron runs each job in a **fresh session** with no chat history → every prompt is self-contained
  (the block above is written that way). `context_from` can chain jobs if you want the committee to read a
  prior job's output.
- `--copy` is required so the `.py` helpers install (URL/`hermes skills install` pulls SKILL.md only).
- Pools must be on a path the separate cron sessions share — a durable home dir, never `/tmp`.

## Done when
- [ ] `hermes skills list` shows the skills as slash-commands; one verified `--json` run.
- [ ] `hermes cron list` shows all 6 jobs (5 daily + weekly committee).
- [ ] AGENTS.template.md mandate is in the system prompt.
- [ ] Health check registered; weekly committee logs to forecast-ledger.
