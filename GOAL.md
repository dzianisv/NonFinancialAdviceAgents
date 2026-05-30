# GOAL

> **Educational analysis only — not financial advice.** Past backtest performance does not
> guarantee future results. Validate with a fee-only fiduciary before deploying real capital.

## The mission

Deploy **$1,000,000 in cash** into the market **now (mid-2026)** in a way that:

1. **Participates in upside** if the AI/tech bull keeps running,
2. **Survives a bubble burst** like the dot-com crash — we appear to be in an AI bubble, and
3. **Runs as an automated, agentic system** — a small "hedge fund" of specialized
   [opencode](https://opencode.ai) agents, notification-first and human-in-the-loop — not hand-managed.

The question that started this: **why not just buy the S&P 500 or QQQ?** — and what to do instead.

## Why we're cautious (the motivation)

We appear to be in an AI bubble — bubble-level valuations, though *not* a carbon copy of 2000
(full evidence in [`research/01-ai-bubble-vs-dotcom.md`](research/01-ai-bubble-vs-dotcom.md)):

- Shiller **CAPE ~41.6** — 2nd-highest in 144 years (the 2000 peak was 44).
- **Buffett indicator ~220-235%** — *worse* than 2000's ~140%.
- **Top-10 stocks ≈ 40% of the S&P** vs ~27% at the dot-com peak — more concentrated than 2000.
- **But** the leaders (NVIDIA et al.) have real, large earnings, unlike 2000 — so it's
  *expensive + dangerously concentrated*, riding an unresolved bet on whether ~$500B/yr of AI capex pays off.
- GMO / Vanguard / Goldman all forecast **below-average 10-year returns** for cap-weight US equity.

The left tail is the thing we are defending against. In our 2000–2026 backtest the S&P fell **−55%**
and QQQ **−83%**, and 2000–2009 was a **"lost decade"** (S&P −0.9%/yr, QQQ −6.8%/yr) while diversified
all-weather mixes compounded at +7–10%/yr. You don't have to predict the crash to be protected from it.

## What "done" looks like

- [x] **Research** the bubble, crash-protection strategies, automated PM, and stock selection — cited notes in [`research/`](research/README.md).
- [x] **Backtest** the candidate strategies across dot-com / GFC / COVID / 2022 — scripts in [`backtests/`](backtests/README.md).
- [x] **Decide a strategy** and write it up — the evolution and current recommendation in [`strategy/`](strategy/README.md).
- [x] **Build the agent team** — opencode `SKILL.md` modules in [`skills/`](skills/README.md).
- [ ] **Point-in-time backtest harness** (SEC EDGAR companyfacts) so the analyst's gate runs on individual stocks.
- [ ] **Transaction-cost + tax modeling** in the backtests (current results are gross).
- [ ] **Alpaca paper-trading loop** wired to the daily decision loop — notification-first, no auto-execution.
- [ ] **Live broker integration** — only after paper validation + explicit human sign-off, with the kill switch + hard caps in code outside the LLM.

## The current answer (one paragraph)

Don't bet the whole $1M on cap-weight S&P/QQQ at CAPE ~41. Bottom-up stock-picking doesn't reliably
beat a cheap index (SPIVA + our own backtests), so the edge isn't *selection* — it's **structural**:
broad diversification across macro regimes, a trend / regime overlay for "crisis alpha," disciplined
risk management, and a cash reserve deployed into drawdowns. We hold this as the
**Bubble-Aware All-Weather** portfolio, deployed on a staged cash schedule, run by an agentic team.
Full spec: [`strategy/v3-bubble-aware-all-weather.md`](strategy/v3-bubble-aware-all-weather.md).

See also: the tracking issue — https://github.com/dvashchuk/backtest/issues/1
