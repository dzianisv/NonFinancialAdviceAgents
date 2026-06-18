# Strategy — the evolution of our thinking

> **Educational analysis only — not financial advice.**

This folder tracks how our strategy evolved as the evidence came in. Each version answers a
different question, and each was killed or absorbed by the next when the backtests said so.
**v3 is the current recommendation.** v1 and v2 are kept because the *reasons* they fell short
are what justify v3 — read them in order and the conclusion is earned, not asserted.

| Version | The question it asked | The verdict | Status |
|---------|----------------------|-------------|--------|
| [**v1**](v1-deploy-into-index.md) — Deploy into the index | *How* should we time entry of $1M into VOO/QQQ/VXUS — lump sum, DCA, or buy-the-dips? | Entry timing barely matters; lump-sum usually wins. This solved the wrong problem — it never asked *what to hold* or *what if the index itself crashes 50%.* | superseded |
| [**v2**](v2-factor-selection.md) — Beat the index by selection | Can we beat the S&P by *picking* — value, quality, momentum, sector rotation, congressional/insider trades, options wheel? | Mostly no. 1/10 factor ETFs beat SPY on return, 0/10 on Sharpe; the exotic signals were worse. Selection isn't a reliable edge. | superseded |
| [**v3**](v3-bubble-aware-all-weather.md) — Bubble-Aware All-Weather | If selection doesn't win and the index has a fat left tail, where's the edge? | **Structural**: de-concentrated diversification + a trend/regime overlay (crisis alpha) + risk management + a dip-reserve, run by an agentic team. Caps the −55%/−83% tail without a market call. | **current** |

## The arc in one line

**v1 asked *when* to buy, v2 asked *what* to pick, v3 asked *how to survive* — and only the third
question had an edge worth having.** The journey: *timing → selection → structure.*

## How this maps to the rest of the repo

- The **evidence** behind each verdict lives in [`../research/`](../research/README.md) (cited notes)
  and [`../backtests/`](../backtests/README.md) (runnable scripts + saved results).
- The **current strategy (v3)** is implemented as the agent team in [`../.agents/skills/`](../.agents/skills/README.md)
  and deployed via the plan in [`v3-bubble-aware-all-weather.md`](v3-bubble-aware-all-weather.md).
- The **mission** these all serve is in [`../GOAL.md`](../GOAL.md).
