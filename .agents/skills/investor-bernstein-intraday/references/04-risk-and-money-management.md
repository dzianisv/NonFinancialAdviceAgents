# Risk & Money Management — Bernstein

> Source: Jacob Bernstein, *The Ultimate Day Trader* (2009, F+W Media) — Ch. 14–16 (risk control, multi-unit trading, the Pareto principle, capital adequacy / six-loss test, scaling up, market-selection filters, margins & forex risk). Distilled 2026-06-07. **Thresholds preserved verbatim, including the internal inconsistencies.**

## Core thesis
"**Risk control and management of losses are the two most important aspects of trading.**" The set-ups and triggers are secondary; survival is primary. The most common cause of failure is **undercapitalization combined with arbitrary stops.** Profits are radically skewed (Pareto), so the structure must (a) **survive a losing streak**, (b) **size on risk, not reward**, and (c) **scale out across multiple units** so the rare big winner is ridden, not cut short. "**An investment is a day trade that ended the day at a loss**" — i.e., never let a day trade become a "hold."

## Key frameworks / mental models
- **Pareto skew of profits.** "**At least 80 percent of your profits will be made on 20 percent of your trades**" — stated elsewhere as **80–90% of profits from 10–20% of trades** (both phrasings preserved). Implication: do not cut winners; the few big ones pay for everything.
- **Multi-unit trading.** A **single unit** is structurally disadvantaged (you must choose between exiting and riding). Trade **2, preferably 3 units.** The **preferred 3-unit plan**: take profit on the **first third** at the target; hold **one third with a break-even stop**; hold **one third with a trailing stop**.
- **Capital adequacy — the six-loss test.** "You **must be prepared to take at least six consecutive losses**." Example: avg loss **$2,000** → a **$12,000 account could be entirely lost** → starting capital must be **far greater than 6× the average loss**.
- **Size on risk, not reward.** Position size is a function of the stop distance / dollar risk, never the hoped-for gain.
- **Scale up only after +50%.** Increase size only after the account is up **50%**.

## Specific claims, mechanisms & data (PRESERVE EXACT — including inconsistencies)
- **Stops.** Arbitrary dollar stops are **rejected**. Too-small stops "cut off the big move"; too-large stops produce larger losses. Stops must be **market-based** (range/volatility/structure). "The size of your losses will be a function of the stop losses you are using."
- **Market-selection — liquidity filters (INTERNALLY INCONSISTENT, both preserved):**
  - **Stocks: ≥ 2 million** shares/day in one place, **≥ 5 million** shares/day elsewhere in the book.
  - **Futures: ≥ 5,000** contracts/day in one place, **≥ 10,000** contracts/day elsewhere — measured **over the last 10 sessions**.
- **Market-selection — range filters.** Stocks: **minimum daily range $0.50**, prefer **$1–$2**. Commodities: prefer **~$200** daily range. **Avoid excess volatility** — the **full S&P at ~$10,000/day** is too big → **trade the E-Mini (1/5 the size)** instead.
- **Margins & leverage.** Day-trade margins are **lower, sometimes interest-free intraday**, BUT "**risk is unlimited in terms of price.**"
- **FOREX is especially risky** — "you are competing with the biggest banks."
- **Diversify** across an **uncorrelated basket** of markets, across **methods**, and across **time frames**.

## How to APPLY (decision rules for an agent using this lens)
1. **Check capital adequacy first**: starting capital must comfortably absorb **6 consecutive losses** at the average loss size. If not, do not trade.
2. **Size on risk** (stop distance × units), never on the target.
3. **Use a market-based stop**; reject any arbitrary dollar stop ("the market has no respect for such stops").
4. **Trade 3 units** when possible: first third → target; second third → break-even stop; third → trailing stop. Ride winners (Pareto).
5. **Filter the instrument** for liquidity and daily range before trading it; flag the **2M-vs-5M shares** and **5,000-vs-10,000 contracts** inconsistency rather than picking one silently. Prefer the **E-Mini** over the full S&P.
6. **Never let a day trade become an investment** — close losers by session end; don't "marry" a position.
7. **Scale up only after +50%** account growth.

## Caveats / where he hedges
- The two **liquidity thresholds contradict each other** (2M vs 5M shares; 5,000 vs 10,000 contracts) — surface both, treat as ranges, don't pretend precision.
- The two **Pareto phrasings** (80/20 vs 80–90 / 10–20) likewise differ; both are preserved.
- Capital figures are illustrative examples, not calibrated to any specific edge or hit rate.
- Lower intraday margins **amplify** the unlimited-price risk — a leverage warning, not a benefit.

## Memorable quotes
- "Risk control and management of losses are the two most important aspects of trading."
- "An investment is a day trade that ended the day at a loss."
- "At least 80 percent of your profits will be made on 20 percent of your trades."
- "You must be prepared to take at least six consecutive losses."
- "The size of your losses will be a function of the stop losses you are using."
- "risk is unlimited in terms of price." (on day-trade margin)
