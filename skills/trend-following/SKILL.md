---
name: trend-following
description: Rules-based trend-following / absolute-momentum overlay that provides "crisis alpha" — hold an asset only while it is above its long-term trend (200-day / 10-month moving average) or while its absolute momentum beats T-bills, otherwise rotate to bonds/cash. Covers the simple 200-day MA rule, dual momentum (Antonacci GEM), time-series momentum, and managed-futures ETFs (DBMF, KMLM). Use this whenever the user wants a mechanical "get me out before it gets worse" rule, asks about the 200-day moving-average strategy, dual/absolute momentum, managed futures, trend-following, GTAA / Meb Faber timing, or wants downside protection that doesn't require predicting the top. Trigger when the user describes wanting to exit downtrends automatically. Note its known weakness: fast V-shaped crashes (2020) and choppy whipsaw markets. Educational, not advice.
license: MIT
compatibility: opencode
metadata:
  audience: systematic-investors
  domain: quantitative-finance
  role: signal-analyst
---

# Trend-Following (Crisis Alpha)

A mechanical overlay that steps aside during **protracted** downtrends. Crashes are usually
months-long, so trend rules detect the downtrend and move to cash/bonds — historically positive in
8 of the 10 largest 60/40 drawdowns over 137 years (AQR). It is a *positive-expected-return*
diversifier, not just insurance.

## Mandatory framing
- Rules-based, not a forecast or personalized advice.
- **Known weaknesses:** (1) **fast V-shaped crashes** (Feb-Mar 2020) — monthly signals are too slow and
  get caught long; (2) **choppy/range-bound markets** — repeated whipsaw. Pair with a small convex tail
  sleeve (see `portfolio-construction`) to cover the fast-crash gap.
- Behaviorally hard: it lags for *years* in strong bull markets. Decide you'll hold it before you start.

## The three variants

### 1. Simple 200-day (10-month) MA rule — easiest
For each risk asset: hold it while `price > 200d SMA`, else hold T-bills/short bonds. Check on **weekly
or month-end closes** (not intraday). Add a small band (±1-2%) to cut whipsaw. This is Meb Faber's GTAA
core; it sidestepped most of 2008.

### 2. Dual Momentum (Antonacci GEM)
- **Relative momentum:** pick the stronger of two risk assets (e.g., US equities vs ex-US) by trailing
  12-month return.
- **Absolute momentum (the protective part):** only hold the winner if its 12-month return **beats
  T-bills**; otherwise hold bonds.
- Rebalance monthly. ~1.5 trades/year historically; beat buy-and-hold with ~half the drawdown — but can
  whipsaw and lag in choppy years.

### 3. Time-series momentum (managed futures)
Own-trailing-12m return predicts next month across asset classes; the alpha is **largely from volatility
scaling** (it's "vol-targeted trend"). For retail, access via **managed-futures ETFs** rather than
running a futures book.

## Implementation
- **DIY rule:** SPY/VTI/VXUS/sector ETFs + SGOV/BIL switch. Signal on prior close, trade next open.
- **Off-the-shelf trend ETFs:** **DBMF** (replicates CTA index), **KMLM** (commodities/FX/bonds trend),
  **CTA** (Simplify), **RSST** (return-stacked 100% equity + 100% trend).
- ⚠️ **MTUM is cross-sectional equity momentum — long-only, NO crash protection** (it fell with the
  market in 2020). Do not use it as a managed-futures substitute.

## Backtest evidence (this repo)
"Trend-Following S&P (200d)" 2000-2026: **9.1% CAGR, −23% max DD** (vs S&P 8.3%/−55%); dot-com window
−4% (vs −47%), GFC −5.7% (vs −55%), 2022 −14.6% (vs −24.6%). "Dual Momentum (GEM)" 9.9% CAGR but was
caught long in the 2020 V-shape (−34%) — illustrating weakness (1).

## Outputs (contract)
```json
{
  "as_of": "2026-05-29",
  "signals": {"SPY": "in (price 5% > 200dma)", "VXUS": "out (below 200dma)", "GLD": "in"},
  "target_when_out": "SGOV",
  "rationale": "VXUS closed below its 200d MA on weekly close -> rotate to T-bills."
}
```

## Hand-offs
Provides per-asset in/out signals to **portfolio-construction** (gates the equity/risky sleeves) and is
a per-asset cousin of **regime-detection** (which sets book-level gross exposure). Exit logic is the
"trend exit over fixed stop" rule used by **risk-management**.
