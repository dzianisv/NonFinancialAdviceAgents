# Automation & Implementation — Spreadsheets, Python, IB, and the TradingView Trap

> Source: Carver, *Systematic Trading* (Harriman House, 2015), ch. on implementation/automation (spreadsheet vs automation, Python + Interactive Brokers, data/continuous futures, vol estimation, rebalancing cadence, the no-trade buffer / position inertia, execution). Plus practical modern guidance the 2015 book predates (clearly flagged as extrapolation). Distilled 2026-06-07.

## Core thesis
**Systematic ≠ automated.** Every module in the framework is **spreadsheet arithmetic**; full automation is *desirable, not required*, and matters most for fast, complex, or many-instrument systems. Carver runs his own strategy in **Python wrapped around the Interactive Brokers C++ API** — the only amateur-accessible broker he recommends for full automation — and later authored the open-source **`pysystemtrade`** (which postdates the book). The implementation rules that actually protect you: **never round intermediate values, round only the final target position, then apply a 10% no-trade buffer** (position inertia). And the governing principle: **"A system which is fully automated but not completely trusted is potentially lethal."** Automate only what you trust.

## Key frameworks / mental models
- **Spreadsheet-first.** You can trade this entire framework manually; automation is an optimisation, not a prerequisite.
- **Python + Interactive Brokers** for full automation; **pysystemtrade** = Carver's later open-source reference implementation.
- **Continuous futures series** are required — back-adjust/stitch with the **Panama method** (parallel-shift prior contracts at each roll).
- **Vol estimation:** 25-day simple MA or 36-day EWMA; slower for expensive instruments; never beyond 20 weeks.
- **Rebalancing cadence scales with risk** — faster vol target → more frequent checks.
- **No-trade buffer (position inertia):** only trade when the rounded target is far enough from current.
- **Execution cost prior for small traders:** assume cost = half the bid-offer spread (market order).

## Specific claims, mechanisms & data (PRESERVE EXACTLY)
- **Daily prices suffice** for these rules; futures need **back-adjusted/stitched continuous series** via the **Panama method** (parallel-shift at rolls).
- **EWMA spec matches pandas EWMA `span`.**
- **Vol estimation:** **25-day simple MA** or **36-day EWMA**; slow up to **20 weeks** for expensive instruments; **never beyond 20 weeks**.
- **Rebalancing cadence:** Carver's automation re-checks account value & adjusts risk **HOURLY**; manual with >15% vol target → **daily**; levered → **weekly**.
- **No-trade buffer:** round the portfolio position to whole blocks; **don't trade unless the target is >10% away from the current position.**
- **Execution:** small traders assume **cost = half the bid-offer spread** (market order).
- **Order of operations:** never round intermediate values; **round only the final target position**, apply inertia, then **trade = rounded target − current position**.

## Modern implementation guidance (post-2015 extrapolation — flag as such)
- **Python backtesting libraries:** `backtrader`, `vectorbt`, `zipline-reloaded` are common modern engines for prototyping these rules; **`pysystemtrade`** is Carver's own and most faithful to this framework. None remove the over-fitting risk — they make it *easier* to over-search, so apply ref 06 discipline.
- **TradingView / Pine Script** is excellent for *alerts* and quick prototyping, but its **strategy backtester is indicative only**: it can **repaint** (signals shift after the bar closes), it does **not model realistic slippage/partial fills**, and default fills are optimistic. **TradingView strategy results MUST be re-validated with real costs** before risking money.
- **Tie back to Carver's speed limit:** any TradingView/library backtest must pass the standardised-cost × turnover ≤ ⅓-of-Sharpe gate (ref 06) using *realistic* costs — not the platform's defaults. This is the GOAL.md pre-trade gate.

## How to APPLY (decision rules)
1. **Start in a spreadsheet** (or Python) — prove the arithmetic and trust the system before automating.
2. **For automation, use Python + Interactive Brokers**, or start from **pysystemtrade**.
3. **Build continuous futures** with the Panama method; daily prices are enough.
4. **Estimate vol with 25-day MA / 36-day EWMA** (slower, ≤20 weeks, for expensive instruments).
5. **Rebalance in proportion to risk** (hourly automated / daily if manual & >15% / weekly if levered).
6. **Round only the final position**, then apply the **10% no-trade buffer**; trade = rounded target − current.
7. **If you prototype in TradingView/backtrader/vectorbt, re-validate with realistic costs** and re-run the speed limit before going live. Never trust a platform's default-cost backtest.
8. **Automate only what you fully trust** — an untrusted automated system is the dangerous case.

## Caveats / where he hedges
- **Automation is optional**, not a virtue in itself — it adds operational risk (the "lethal" untrusted system).
- **Vol estimates and the Panama method are approximations** — back-adjusted series distort absolute price levels (fine for these % / vol-based rules, not for level-based ones).
- **Modern libs/TradingView** make over-fitting *easier*; convenience is not validity. Their backtests are a starting point, not proof.

## Memorable quotes
- "It's possible to trade systematically using an entirely manual process with just a spreadsheet… automation is not necessary."
- "A system which is fully automated but not completely trusted is potentially lethal."
- Round only the final target, then trade only if it moves you **more than 10%** from where you are.
