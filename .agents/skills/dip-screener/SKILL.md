---
name: dip-screener
description: Screen S&P 100 for quality stocks trading >= 20%/25%/30% below their 52-week ATH. Fires an immediate alert when a HIGH-conviction dip (>= -30%) aligns with a RISK_ON regime. Use when asked "what quality stocks are on sale", "what fell from highs", "any big dips in the market", "catch the next Google dip", "fallen angels", or on the daily proactive schedule. Never re-proposes the same alert within the same calendar week.
license: MIT
compatibility: opencode
metadata:
  audience: equity-investors
  domain: dip-screening
  role: quality-stock-dip-detector
---

# Dip Screener (S&P 100 quality stocks below 52-week ATH)

Scans the S&P 100 daily for stocks meaningfully below their 52-week high. The goal: catch the next **Google -30% from ATH** or **Meta -40% from ATH** — quality names, temporary dislocation, opportunity.

## Why this matters

Most opportunities are missed because no one was watching. Google dropped -30% from its ATH in Spring 2025 while journalists were writing about AI doom. SanDisk (WDC) appeared in FT/WSJ as AI supply chain in Sept 2025. Both were obvious in hindsight. This screener runs before you wake up and surfaces them.

## Hard rule

**RECOMMEND ONLY.** No trades, no orders. Output = candidates for quorum review. Educational analysis, not advice.

## Run the screener

```bash
python3 .agents/skills/dip-screener/dip_screener.py --threshold 20
```

Output fields: `ticker`, `pct_from_ath`, `ath_52w`, `current`, `sma200`, `pct_vs_200d`, `conviction`.

Conviction tiers:
- `HIGH`: >= -30% from ATH (immediate alert if RISK_ON)
- `MEDIUM`: -25% to -30% (add to weekly pool)
- `WATCH`: -20% to -25% (note, don't alert)

## Decision logic after running

**Step 1: Check regime first.**
```bash
python3 .agents/skills/regime-detection/regime_monitor.py --json
```
If `regime = RISK_OFF`: no new buys. Still run screener to build watchlist for when regime recovers.

**Step 2: For each HIGH hit in RISK_ON regime → immediate DM:**
```
🚨 DIP ALERT — [TICKER] [pct]% below 52w ATH
  ATH: $[ath]  Now: $[price]  200dMA: $[sma] ([pct_vs_200d]% [above/below])
  Regime: RISK_ON (score [score])
  → Route to /multi-lens-quorum for verdict? Reply YES to run full analysis.
```

**Step 3: For MEDIUM hits → add to weekly candidate pool.**
Write to `/tmp/dip_candidates.jsonl` (read by `signal-convergence-alert` at 08:30 UTC).

**Step 4: Cross-check with trend-stock-research.**
If a HIGH/MEDIUM ticker also appears in recent FT/WSJ coverage → CONVERGENCE signal. Elevate conviction.

## Success criteria

- [ ] Script ran and produced output (or confirmed no hits).
- [ ] Regime checked before any alert.
- [ ] HIGH hits in RISK_ON regime: DM sent immediately.
- [ ] MEDIUM hits: written to candidate pool.
- [ ] No alert sent for RISK_OFF regime (watchlist only).

## Schedule

Run **daily 07:45 UTC (Mon–Fri)** so alerts arrive before US market open (09:30 ET).
