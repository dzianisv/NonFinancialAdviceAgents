---
name: hedge-strategy-builder
description: "Three-step hedge-fund-quant pipeline for building trading strategies from scratch: (1) generate 3 candidate strategies for a market (crypto/stocks/forex) with exact indicator settings, entry/exit rules, stop-loss/take-profit logic, best-fit market conditions, and stated edge; (2) backtest each over 5-10 years of historical data reporting CAGR, Sharpe, max drawdown, win rate; (3) risk-reward analysis with drawdown patterns, 3 risk-reduction improvements, and 2 return-enhancing tweaks. Use when the user says \"build a hedge fund strategy\", \"generate trading strategies\", \"design a strategy and backtest it\", \"strategy from scratch\", or wants an idea-to-validated-strategy loop rather than analysis of an existing position. Composes with strategy-discovery-backtest (execution), risk-management (sizing), and skeptic (challenge). Educational, not advice."
license: MIT
compatibility: opencode
metadata:
  audience: systematic-investors
  domain: quantitative-finance
  role: strategy-designer
  source: instagram.com/p/DaLeqmyjs8n (@artificialntellligence)
---

# Hedge Strategy Builder

Idea → validated strategy pipeline. Run all 3 stages in order; never skip backtesting. Full
source transcript: `references/source-post.md`.

## Inputs (ask if missing)

- **Market**: crypto / stocks / forex
- **Timeframe**: e.g. 1D or 1H
- **Capital**: e.g. $10,000
- **Risk per trade**: 1-2%

## Stage 1 — Strategy Generation

Act as a hedge fund quant. Generate **3** distinct strategies for the chosen market. For each:

1. Indicators used with exact settings
2. Step-by-step entry and exit rules
3. Stop-loss and take-profit logic
4. Market conditions where it works best
5. Why the strategy has an edge

Reject candidates whose "edge" is just a restated indicator (e.g. "buy when RSI oversold" with no
reason it isn't arbitraged away). Each edge must name a structural cause: risk premium, behavioral
bias, flow/liquidity effect, or slow-moving information.

## Stage 2 — Backtesting

Backtest each strategy against historical data — in this repo, prefer real runs via
`strategy-discovery-backtest` / `backtests/` over LLM-estimated numbers; label estimates as
estimates.

Requirements:

- **Time period**: last 5-10 years (must span at least one bear market)
- **Metrics**: CAGR, Sharpe ratio, max drawdown, win rate
- **Output**: table + summary

Also explain per strategy:

- When it performs best and worst
- What market conditions break it

## Stage 3 — Risk-Reward Analysis

For each surviving strategy, break down:

- Risk per trade
- Reward-to-risk ratio
- Drawdown patterns (depth, duration, clustering)

Then:

- Suggest **3 improvements to reduce risk**
- Suggest **2 ways to increase returns without increasing risk**

## Output contract

One markdown report: inputs recap → 3 strategy specs → backtest table → risk-reward breakdown →
final ranking with the single strategy you would fund, and why the other two lost. Hand sizing to
`risk-management` and challenge the winner with `skeptic` before any live use.
