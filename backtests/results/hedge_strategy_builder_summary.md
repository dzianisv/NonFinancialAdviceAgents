# hedge-strategy-builder run — 2026-07-17

Inputs: US stocks/ETFs, 1D swing, $10k, 1-2% risk/trade. Costs 5 bps/side.
Data: yfinance daily adjusted 2016-01..2026-07. OOS split: 2022-01..2026-07.
Script: `backtests/hedge_strategy_builder_backtest.py` (+ refined variant inline in session).

## Candidates

| Strategy | Full CAGR | Full Sharpe | Full maxDD | OOS CAGR | OOS Sharpe | OOS maxDD | Trades | Win |
|---|---|---|---|---|---|---|---|---|
| S1 momentum rotation (SPY/QQQ/IWM/EFA→TLT) | 7.4% | 0.46 | -41.3% | -1.7% | 0.00 | -41.0% | 47 | 55% |
| S2 RSI(2) mean reversion SPY (>200MA) | 3.0% | 0.52 | -12.6% | 4.8% | 0.92 | -5.7% | 87 | 76% |
| S3 VIX spike fade | 1.4% | 0.18 | -28.4% | 1.4% | 0.20 | -8.4% | 43 | 74% |
| SPY buy & hold (benchmark) | 15.0% | 0.88 | -33.7% | 11.9% | 0.73 | -24.5% | — | — |
| **S2 refined: + idle cash in BIL** | **4.9%** | **0.82** | **-10.1%** | **8.4%** | **1.57** | **-4.8%** | 87 | 76% |

## Verdicts

- **S1 FAIL.** Broke OOS: 2022 rate shock killed TLT as the defensive leg — momentum rotated into
  a "safe" asset that drew down with equities. Structural flaw, not parameter noise.
- **S3 FAIL.** OOS Sharpe 0.20; VIX-stretch entry too early in vol regimes, no edge net of costs.
- **S2 PASS (risk-adjusted, as a sleeve).** OOS Sharpe 1.57 vs SPY 0.73, maxDD -4.8% vs -24.5%,
  ~11% market exposure, 8 trades/yr, 76% win rate. Does NOT beat SPY on raw CAGR — it is a
  low-drawdown cash-plus sleeve, not a SPY replacement.

## S2 funded spec

- Universe: SPY. Regime filter: close > 200-day SMA.
- Entry: RSI(2) < 10 at close → buy next open, full sleeve notional ($10k).
- Exit: close > 5-day SMA, or 10-trading-day time stop.
- Idle cash: BIL/SGOV.
- Observed per-trade risk ≈ 1-2% of sleeve; equity maxDD -10.1% full period.

## Improvements (Stage 3)

Risk reducers: (1) hard 3% stop per trade caps tail (2020-style gaps); (2) halve size when VIX>30;
(3) skip entries within 2 days of FOMC/CPI.
Return enhancers w/o added risk: (1) idle cash in BIL (done — +3.5% OOS CAGR); (2) add uncorrelated
second sleeve (e.g. QQQ variant, corr of trades low) rather than leverage.

## Caveats

Single-instrument, parameter set taken from literature (Connors RSI-2) not optimized here — low
overfit risk but also untuned. No deflated-Sharpe multiple-testing haircut applied to the 2-variant
comparison. Paper-trade gate per `strategy-discovery-backtest` before live. Educational, not advice.
