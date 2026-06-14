---
name: regime-detection
description: Detect market regime (risk-on vs risk-off, bull vs bear) from a weighted ensemble of robust signals — price vs 200-day moving average, VIX term structure, credit spreads, breadth, and the yield curve — and map the result to a target gross-exposure multiplier. Use this whenever the user asks "should I be in or out of the market right now", wants to know if it's risk-on or risk-off, asks about a market-timing or de-risking signal, mentions the 200-day moving average / death cross / golden cross, VIX backwardation, credit spreads widening, yield-curve inversion, market breadth, or wants an agent that decides how much equity exposure to run. Trigger even if the user only describes the situation ("the market feels toppy, should I cut exposure?"). Always frame outputs as a rules-based exposure dial, not a crash prediction.
license: MIT
compatibility: opencode
metadata:
  audience: systematic-investors
  domain: quantitative-finance
  role: regime-analyst
---

# Regime Detection

Sets the top-of-funnel decision for a systematic portfolio: **how much gross equity
exposure to run right now** (e.g., 0.3× to 1.0× of target). It does NOT predict crashes
and it does NOT bottom-tick. It is a slow, robust, ensemble dial.

## Mandatory framing
- This is a **rules-based exposure dial**, not a forecast or personalized advice.
- Every individual signal is noisy. Use a **weighted ensemble** and require **persistence**
  (a signal must hold for N days) before acting, to avoid whipsaw.
- Regime tools reduce drawdowns at the cost of **whipsaw and lag**; they will sometimes cut
  exposure right before a rebound. That is the price of the protection.

## The signal ensemble

Score each signal −1 (risk-off) / 0 / +1 (risk-on). Weight the robust core higher.

| Signal | Weight | Risk-on (+1) | Risk-off (−1) | Notes |
|--------|:------:|--------------|---------------|-------|
| **Price vs 200-day MA** (S&P) | 3 | price > MA (+ ~1% band) | price < MA (− ~1% band) | most robust trend filter; band cuts whipsaw |
| **VIX term structure** (VIX / VIX3M) | 2 | ratio < 1 (contango) | ratio > 1 (backwardation) | robust *stress* detector; do NOT use to bottom-tick |
| **Credit spreads** (HYG/LQD ratio, or FRED HY OAS) | 2 | ratio rising / OAS tightening | ratio falling / OAS widening | credit *leads* equities |
| **Breadth** (% S&P > 200dma) | 1 | > 55-60% | < 40% | confirmatory; divergence flag |
| **Yield curve** (10y−2y, 10y−3m) | 1 | positive | inverted | slow (6-18mo lead); strategic only |
| Hindenburg Omen | 0.5 | — | only if **clustered** (2-3 in 30d) | mostly noise standalone; raises vigilance |

**Aggregate → exposure multiplier.** Normalize the weighted score to [−1, +1] and map:

```
score >=  0.5  -> 1.0x   (full target exposure)
0.0 to 0.5     -> 0.7x
-0.5 to 0.0    -> 0.5x
score < -0.5   -> 0.3x   (defensive minimum; never 0 unless a hard risk rule fires)
```

Keep a **floor** (e.g., 0.3×) so you never fully exit — full exits maximize whipsaw and
guarantee you miss V-shaped rebounds (2020).

## Persistence & hysteresis
- Require the new regime to hold **≥ 3-5 trading days** (or use weekly closes) before changing the dial.
- Use **asymmetric bands**: turn defensive faster than you turn aggressive (protect first, re-risk slowly).

## What each signal is good/bad at
- **200-day MA:** the workhorse. Robust over a century of data; laggy by construction. Best on the
  *index*, not noisy single names.
- **VIX term structure:** flips to backwardation in ~20% of days (acute stress). Great to *de-risk*,
  terrible to *time the bottom* — it can stay inverted for weeks past the low.
- **Credit spreads:** the best cross-asset confirmation; credit markets sniff trouble before equities.
- **Yield curve:** a real recession predictor but with a long, variable lead — use for strategic tilt only.
- **Breadth:** strong *divergence* signal (index highs on deteriorating breadth = weak internals); weak
  as a standalone trigger.
- **Hindenburg Omen:** ~20-25% hit rate; only informative when clustered. Never a direct sell trigger.

## Outputs (the contract this agent emits)
Return structured JSON the Portfolio Manager and Risk Manager can consume:
```json
{
  "date": "2026-05-29",
  "regime": "risk-on | neutral | risk-off",
  "exposure_multiplier": 0.7,
  "score": 0.32,
  "signals": {"sma200": 1, "vix_ts": 0, "credit": 1, "breadth": 0, "curve": -1, "hindenburg": 0},
  "rationale": "S&P above 200d MA, credit tightening, but curve inverted and breadth middling."
}
```

## WebFetch / LLM-agent procedure (no Python required)

Run these fetches in order. Parse the JSON inline — do NOT spawn a Python subprocess.

### 1. SPY price vs 200-day MA
```
WebFetch: https://query1.finance.yahoo.com/v8/finance/chart/SPY?range=1y&interval=1d
Parse: result[0].indicators.quote[0].close  → array of ~252 daily closes
200-day MA = average of last 200 values
Current price = last value in array
Signal: +1 if current > 200dMA * 1.01, -1 if current < 200dMA * 0.99, else 0
```
Fallback if Yahoo blocked:
```
WebFetch: https://stooq.com/q/l/?s=spy.us&f=sd2t2ohlcv&h&e=csv   (CSV, last row = today)
```

### 2. VIX (spot) and VIX term structure
```
WebFetch: https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX?range=5d&interval=1d
Parse: last close = VIX spot

WebFetch: https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX3M?range=5d&interval=1d
Parse: last close = VIX3M
Signal: +1 if VIX/VIX3M < 1 (contango), -1 if > 1 (backwardation)
```
Fallback: CBOE VIX page (scrape the number):
```
WebFetch: https://www.cboe.com/tradable_products/vix/
```

### 3. Credit spreads (HY OAS) — FRED public API, no key needed
```
WebFetch: https://fred.stlouisfed.org/graph/fredgraph.csv?id=BAMLH0A0HYM2&vintage_date=2026-06-14
Parse: last row = today's HY OAS in bps
Signal: +1 if OAS < 350bps (tight), -1 if OAS > 500bps (wide), else 0
```
Fallback HYG/LQD ratio:
```
WebFetch: https://query1.finance.yahoo.com/v8/finance/chart/HYG?range=30d&interval=1d
WebFetch: https://query1.finance.yahoo.com/v8/finance/chart/LQD?range=30d&interval=1d
Signal: +1 if HYG/LQD ratio is above its 30-day average, -1 if below
```

### 4. Yield curve — FRED public API
```
WebFetch: https://fred.stlouisfed.org/graph/fredgraph.csv?id=T10Y2Y&vintage_date=2026-06-14
Parse: last row = 10y-2y spread (positive = normal, negative = inverted)
Signal: +1 if spread > 0, -1 if spread < -0.25
```

### 5. Score → exposure multiplier
Weighted sum: SMA(×3) + VIX_TS(×2) + Credit(×2) + Curve(×1), max=8, min=-8.
Normalize to [-1, +1] by dividing by 8. Map per the table above.

## Implementation notes (Python / local runner)
- Data: yfinance for prices/VIX (`^VIX`, `^VIX3M`), HYG/LQD; **FRED** for HY OAS (`BAMLH0A0HYM2`),
  curve (`T10Y2Y`, `T10Y3M`). See `regime_monitor.py`.
- Compute SMA/momentum on **trailing** data only (no look-ahead). Decide on prior close, act next open.
- Backtest the ensemble across **2000-02, 2008, 2020, 2022** — each window stresses different signals
  (2020 punishes slow trend; 2022 punishes anything that assumed bonds hedge).

## Hand-off
Feed the `exposure_multiplier` to **portfolio-construction** (scales the risky sleeves) and to
**risk-management** (which can override downward but not upward). Pairs with **trend-following**
(per-asset version of the same idea).
