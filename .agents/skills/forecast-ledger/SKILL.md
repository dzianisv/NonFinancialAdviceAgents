---
name: forecast-ledger
description: "Use when a dated, probabilistic market call is made and should be SCORED later, or when reviewing past forecast accuracy/calibration — \"log this forecast\", \"track this prediction\", \"how calibrated are my calls\", \"score my forecasts\", \"what's my Brier\", \"which lens/source forecasts best\", \"did our BTC/FOMC/CPI calls hit\". Closes the feedback loop for superforecasting: log a call with its probability + resolution date, resolve it on the date, and score Brier + calibration by lens/source. Educational, not advice; a forecast ungraded is just an opinion."
license: MIT
compatibility: opencode
metadata:
  audience: forecasters-tracking-their-own-accuracy
  domain: forecast-scoring-and-calibration
  role: feedback-loop-tooling
  source: "Tetlock & Gardner, Superforecasting (2015) — scoring + calibration as the only path to improvement"
---

# Forecast Ledger (score your calls or they're just opinions)

A probabilistic forecast you never grade teaches you nothing. **Superforecasting's** core finding:
forecasters improve **only** through scored feedback — **Brier scores** and **calibration**. This skill is
that loop: every dated call made by `superforecasting` (or any market call) gets **logged
with its probability**, **resolved on its date**, and **scored**.

## When to use

- **Log** — right after emitting any forecast with a probability + a resolution date ("70% SOL tags $60
  by Jul 1"). If it has a `P` and a `by-when`, it goes in the ledger.
- **Resolve** — on/after the horizon date, mark hit/miss against what actually happened.
- **Score** — to review calibration: are your 70%s actually right ~70% of the time? Which lens/source is
  sharpest?

**Don't use** for undated opinions or non-probabilistic takes — nothing to score.

## The loop

```bash
L="python3 .agents/skills/forecast-ledger/ledger.py"   # ledger at $FORECAST_LEDGER or ./forecasts/ledger.jsonl

# 1. LOG every dated call, the moment it's made (p = your probability, 0..1)
$L add --asset BTC --q "BTC <=\$50k before 2026-07-01" --p 0.65 --by 2026-07-01 \
       --source "superforecasting; Polymarket \$42M" --lens macro,onchain,prediction-market,derivatives

# 2. find what's due, then RESOLVE against reality
$L list --due
$L resolve <id> yes|no [--on YYYY-MM-DD] [--note "actual: tagged \$49.2k on 6/24"]

# 3. SCORE — Brier + calibration table; --by lens|source to rank what forecasts best
$L score --by source
```

## Reading the score

- **Brier** = mean `(p − outcome)²`. **0 = perfect, 0.25 = coin-flip, lower is better.** Beating 0.25
  means your probabilities carry information.
- **Calibration table** — bins forecasts by predicted probability vs observed hit-rate. If your "70%"
  bucket hits 45%, you're **overconfident** (the tool flags it); if it hits 90%, **underconfident**.
- **`--by lens|source`** — Brier per lens/source. This is how you learn *which seat to trust*: if the
  prediction-market seat scores 0.12 and the technical seat 0.30, weight accordingly next time.

## Habit (make it automatic)

`superforecasting` emits a "Q (scored)" line with a probability and a date — **that line IS
a ledger entry.** Log it immediately; don't trust memory. The point is the *standing record* across many
calls — a single forecast can't be calibrated, fifty can.

## Common mistakes

| Mistake | Fix |
|---|---|
| Log only the calls you got right | Log at emission, before you know — survivorship bias kills calibration |
| Resolve from memory weeks later | Resolve on the date with the actual figure in `--note` |
| One forecast, declare yourself good/bad | Calibration needs n; Brier on n=1 is noise. Accumulate. |
| Score Brier but ignore calibration | Brier conflates calibration + resolution; read the bin table too |
| Vague question with no clean resolution | `--q` must be objectively gradable (a level + a date) |

## Fit

The scoring backend for `superforecasting` and any `multi-lens-quorum` call that emits a
dated probability. Cross-asset (crypto + equities) — it only stores `(question, p, date, outcome)`.

> Educational, not advice. A forecast ungraded is an opinion. Log at emission; resolve on the date.
