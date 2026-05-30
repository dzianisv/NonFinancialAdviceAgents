# Bubble-Aware All-Weather — deploy $1M with crash protection

A research + backtest lab answering one question:

> **"I have $1M in cash. The market looks like an AI bubble (à la dot-com). How do I deploy it so I
> participate in upside but survive a crash — and automate that with an agentic team?"**

> ⚠️ **Educational analysis only — not financial advice.** Past backtest performance does not guarantee
> future results. Validate with a fee-only fiduciary before deploying real capital.

## Start here

| If you want… | Read |
|---|---|
| **The mission** + bubble evidence + done/not-done checklist | [`GOAL.md`](GOAL.md) |
| **The recommended strategy** (and how our thinking got there) | [`strategy/`](strategy/README.md) → [`v3`](strategy/v3-bubble-aware-all-weather.md) |
| **The research** behind it (9 cited notes) | [`research/`](research/README.md) |
| **The backtest evidence** (runnable scripts + results) | [`backtests/`](backtests/README.md) |
| **The agent team** that runs it (opencode skills) | [`skills/`](skills/README.md) |
| **Repo conventions** (for agents/contributors) | [`AGENTS.md`](AGENTS.md) |

## The answer in three lines

1. **Don't bet the whole $1M on cap-weight S&P/QQQ at CAPE ~41.** In our 2000-2026 backtest the S&P fell −55% and QQQ −83%; 2000-2009 was a lost decade.
2. **Selection isn't the edge.** Bottom-up stock-picking (incl. Morningstar's MOAT) doesn't reliably beat a cheap index (our backtests + SPIVA).
3. **The edge is structural.** De-concentrated diversification + a trend/regime overlay (crisis alpha) + risk management + a dip-reserve, run by an agentic team — caps the left tail without a market call. → [`strategy/v3`](strategy/v3-bubble-aware-all-weather.md).

## Repository layout

```
GOAL.md          # the mission
strategy/        # v1 (entry timing) → v2 (selection) → v3 (Bubble-Aware All-Weather, current)
research/        # 9 cited research notes (AI bubble, crash protection, frameworks, $1M playbook)
backtests/       # all backtest + publisher scripts; results/ holds cached summaries
report/          # generated charts (img/) + published write-ups (writeups/)
skills/          # opencode SKILL.md modules for the agentic hedge-fund team
archive/         # session log + skills.zip backup
```

Tracking issue: https://github.com/dvashchuk/backtest/issues/1
