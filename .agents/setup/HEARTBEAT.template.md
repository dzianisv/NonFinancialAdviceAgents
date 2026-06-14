# HEARTBEAT — Investor Agent (proactive advisor playbook)

> This file is read on **every** heartbeat tick (openclaw `agents.defaults.heartbeat.every`,
> currently 15m, `lightContext:true`). It is the proactive engine. On each tick: check the clock,
> run only the task whose slot is due, DM the owner only if an alert condition fires, then go silent.
> **RECOMMEND-ONLY. Educational, not advice. Never trade.**

## On every tick — do this

1. **Get UTC now.** `date -u +"%Y-%m-%d %H:%M %u"` (%u = weekday 1–7, Mon=1).
2. **Read state.** `cat ~/.openclaw/workspace/investor/.heartbeat-state.json` (may not exist → treat all `last_run` as empty). It maps `task → last_run_date`.
3. **Find the due task.** A task is DUE if: now ≥ its slot time today, its weekday matches, AND `last_run_date != today`. If two are due, run the earliest-slot one; the next tick (15m) catches the other.
4. **If nothing due → emit nothing. Stay silent.** Do not DM "all quiet". Silence is correct.
5. **Run the due task** per its row below. **Record** `task=today` into the state file before finishing (so it won't re-fire today).
6. **DM only on the stated alert condition.** No alert condition met → record the run, stay silent.

## Schedule (all times UTC)

| Slot | Days | Task | Skill | DM only if… |
|------|------|------|-------|-------------|
| 07:45 | Mon–Fri | Stock dip scan | `dip-screener` | a HIGH dip (≥−30% from 52w ATH) AND regime=RISK_ON |
| 07:50 | Mon–Fri | Crypto dip scan | `crypto-dip-scanner` | a coin ≥−30% from ATH AND Fear&Greed<25 |
| 08:00 | Mon–Fri | Regime + Fed | `regime-detection`, `fomc-monitor` | regime flipped vs yesterday OR new FOMC statement |
| 08:15 | Mon–Fri | Journalism scan | `trend-stock-research` (broad) | never DM — append tickers to `/tmp/narrative.jsonl` pool |
| 08:30 | Mon–Fri | Convergence check | `signal-convergence-alert` | any ticker hit by ≥2 independent signals today |
| 09:30 | Mon | **Weekly brief** | full STEP 2+3 pipeline (see AGENTS.md) | always DM the brief |

## Task procedures

**07:45 dip-screener**
```bash
python3 ~/.openclaw/workspace/investor/skills/dip-screener/dip_screener.py --json > /tmp/dips.json
python3 ~/.openclaw/workspace/investor/skills/regime-detection/regime_monitor.py --json > /tmp/regime.json
```
For each HIGH-tier hit AND regime=RISK_ON → DM the alert block from the dip-screener SKILL. Write MEDIUM hits to `/tmp/dip_candidates.jsonl`. RISK_OFF → no DM, watchlist only.

**07:50 crypto-dip-scanner**
```bash
python3 ~/.openclaw/workspace/investor/skills/crypto-dip-scanner/crypto_dip_scanner.py --json > /tmp/crypto.json
```
Primary trigger = any coin ≥−30% from ATH AND F&G<25 → DM immediately. Funding rate is bonus (geo-blocked → omit, never suppress alert).

**08:00 regime + fomc** — run both; DM one paragraph only if regime changed or Fed moved. Else record + silence.

**08:15 journalism** — broad FT/WSJ/SA scan; extract tickers with live catalysts; append to `/tmp/narrative.jsonl` (rolling). No DM.

**08:30 convergence** — run `signal-convergence-alert` over today's pools (`/tmp/dip_candidates.jsonl`, `/tmp/narrative.jsonl`, 13F/congress ledgers). ≥2 sources same ticker → DM.

**09:30 Mon weekly brief** — run the full pipeline in AGENTS.md → DM the INVESTMENT BRIEF.

## State file format
```json
{"dip-screener":"2026-06-14","crypto-dip-scanner":"2026-06-14","regime-fed":"2026-06-14","journalism":"2026-06-14","convergence":"2026-06-14","weekly-brief":"2026-06-08"}
```

## Hard rules
- Silence unless an alert condition fires. The owner must trust that a DM = something real.
- Never fabricate a price/number. Skill failed → say `[UNAVAILABLE]`, never invent.
- RISK_OFF → no buy alerts (dips still logged to watchlist).
- Never re-propose a ticker already in the 13F / congress dedup ledger.
