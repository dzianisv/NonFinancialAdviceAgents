# Knowledgebase — Investing in a Possible AI Bubble

A research library built to answer one question:

> **"I have $1M in cash. The market looks like an AI bubble (à la dot-com). How
> do I deploy it so I participate in upside but survive a crash — and how do I
> automate that with an agentic team?"**

Everything here is **educational analysis, not financial advice.** Numbers come
from cited public sources (May 2026) and from our own backtests in this repo.

## Index

| Note | What it answers |
|------|-----------------|
| [01-ai-bubble-vs-dotcom.md](01-ai-bubble-vs-dotcom.md) | Are we in an AI bubble like 2000? (CAPE, Buffett indicator, concentration, bull/bear case, base rates) |
| [02-crash-protection-playbook.md](02-crash-protection-playbook.md) | The menu of downside-protection strategies (trend, tail hedge, risk parity, permanent portfolio, defensive factors, safe havens) |
| [03-backtest-evidence.md](03-backtest-evidence.md) | What our own 2000-2026 backtests show — the data behind "why not just S&P/QQQ" |
| [04-asset-allocation-frameworks.md](04-asset-allocation-frameworks.md) | The canonical all-weather portfolios, side by side, with CAGR/drawdown |
| [05-automated-pm-architecture.md](05-automated-pm-architecture.md) | How to build the agentic systematic fund: regime detection, signals, sizing, risk, data/APIs, agent roles |
| [06-data-sources.md](06-data-sources.md) | Data feeds, broker APIs, backtest frameworks (free → paid) |
| [07-reading-list.md](07-reading-list.md) | The books/papers behind the strategies, distilled |
| [08-the-1M-playbook.md](08-the-1M-playbook.md) | **The synthesis: a concrete $1M deployment plan** |
| [09-stock-selection-evidence.md](09-stock-selection-evidence.md) | Does bottom-up stock-picking (Morningstar moat/fair-value, value, quality) beat the index? Backtest says mostly no — they're defensive sleeves, not alpha |

## How the pieces fit

```
        AI-bubble risk (note 01)
                 │
                 ▼
   "Don't bet the whole $1M on cap-weight S&P/QQQ at CAPE 41"
                 │
       ┌─────────┴──────────┐
       ▼                    ▼
  Diversify the core    Add crisis-alpha overlays
  (notes 02, 04)        (trend / tail hedge — note 02)
       │                    │
       └─────────┬──────────┘
                 ▼
   Backtested across dot-com, GFC, COVID, 2022 (note 03)
                 │
                 ▼
   Automate & govern it with agents (notes 05, 06)
                 │
                 ▼
        The $1M playbook (note 08)
```

## TL;DR of the whole library

1. **The valuation case for caution is real.** Shiller CAPE ~41.6 (2nd-highest
   in 144 years, vs 44 at the 2000 peak); Buffett indicator ~220-235% (*worse*
   than 2000's ~140%); top-10 stocks ≈40% of the S&P (vs ~27% in 2000). GMO,
   Vanguard and Goldman all forecast below-average 10-yr US equity returns.
2. **But it is *not* a carbon copy of 2000.** Today's leaders (NVIDIA et al.)
   have real, huge earnings; the valuation *premium* of the top-10 over the rest
   is half what it was in 2000. The swing factor is whether ~$500B/yr of AI capex
   earns a return — genuinely unresolved.
3. **The base-rate risk is severe enough to plan around.** In 2000-2002 the
   Nasdaq fell ~78% and took ~15 years to recover; the S&P fell ~49%. Our
   backtest reproduces this: 2000-2009 was a "lost decade" — S&P −0.9%/yr, QQQ
   −6.8%/yr — while diversified all-weather portfolios compounded at +7-10%/yr.
4. **You don't have to predict the crash to be protected.** Mechanical,
   rules-based diversification (permanent portfolio, golden butterfly, all-weather)
   and trend-following ("crisis alpha") cut max drawdowns from ~−55% to ~−15%
   *without* requiring a market call — at a cost of some bull-market upside.
5. **It can be automated and governed** by a small team of specialized agents
   (regime analyst, portfolio manager, risk manager with a deterministic veto,
   execution) — paper-traded first, with hard caps enforced in code outside the LLM.

_Last updated: 2026-05-29._
