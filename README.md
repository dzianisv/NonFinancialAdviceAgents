# Bubble-Aware All-Weather — deploy $1M with crash protection

A research + backtest lab answering one question:

> **"I have $1M in cash. The market looks like an AI bubble (à la dot-com). How do I deploy it so I
> participate in upside but survive a crash — and automate that with an agentic team?"**

> ⚠️ **Educational analysis only — not financial advice.** Past backtest performance does not guarantee
> future results. Validate with a fee-only fiduciary before deploying real capital.

## What this project is

Two missions, one north-star ([`GOAL.md`](GOAL.md)):

1. **The agentic hedge-fund** (core). An automated, recommend-only team that runs the loop
   **discover → backtest → human-approve → execute → report** over a **$1M tradfi book** + a separate
   **~$177k crypto book**, AI-bubble-defended, behind a hard backtest-before-trade gate. The agent
   proposes; the human approves every order.

2. **AI Agent Investment Advisor** (new sub-project). A **proactive, notification-first** advisor that
   watches markets *daily* and DMs the owner the moment a quality, time-sensitive setup appears —
   catching the next Google −30% / SanDisk / BTC-dip the owner keeps missing for lack of research time.
   It is **not a new runtime**: it's a portable skill+config layer deployed onto existing agentic
   systems (**openclaw, hermes-ai, claude-code**) using their **native primitives** — openclaw
   `heartbeat` + `HEARTBEAT.md`, claude-code `/loop` + `/goal` + dynamic workflows + Routines, the
   hermes scheduler. Same skills on all three; only the scheduling/notification wiring differs.
   **Recommend-only** — it never places a trade.

   | Read | For |
   |---|---|
   | [`docs/GOAL.md`](docs/GOAL.md) | the advisor north-star (the missed-opportunity mandate) |
   | [`docs/prd.md`](docs/prd.md) | **what** — gaps → features, cadence, personas |
   | [`docs/tdd.md`](docs/tdd.md) | **how** — architecture + full wiring diagrams + data contracts (§8 = the committee) |
   | [`docs/setup-*.md`](docs/) | per-backend deployment (openclaw / claude-code / hermes) |
   | [`.agents/workflows/hedge-fund-committee.workflow.js`](.agents/workflows/) | the weekly hedge-fund committee → ranked next-buy memo |

   Status: fast-tier daily scanners deployed live on openclaw (cron + liveness); the slow-tier weekly
   committee workflow is built + validated (3 iterations) but not yet on a weekly schedule (see tdd §8).

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
