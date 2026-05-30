---
name: agentic-fund-orchestration
description: Top-level playbook for running a small systematic "hedge fund" as a team of specialized opencode agents — regime analyst, portfolio manager, risk manager (with deterministic veto), execution — coordinated through a shared state object, a notification-first daily loop, paper-trading before live, and hard caps enforced in code outside the LLM. Use this whenever the user wants to orchestrate multiple investing agents, build an automated/agentic portfolio-management system or "AI hedge fund", asks how the regime/portfolio/risk/rebalancing/dip skills fit together, wants a daily decision pipeline, or asks about guardrails for automated trading. Trigger when the user describes wanting an agent team to manage money. Always stress human-in-the-loop and notification-first operation; this is educational, not advice.
license: MIT
compatibility: opencode
metadata:
  audience: builders
  domain: systematic-trading
  role: orchestrator
---

# Agentic Fund Orchestration

Coordinates the other skills in this repo into a single, governed decision loop. Reference design:
TauricResearch **TradingAgents** (analyst → debate → PM → risk → execution).

## Mandatory framing
- **Notification-first.** Run for **6+ months proposing trades to a human** before any automated
  execution. Automated trading bugs are expensive bugs.
- **Hard caps and the kill switch live in deterministic code, outside any LLM.** Agents propose;
  the deterministic risk layer disposes.
- Educational; not investment advice. Paper-trade everything first.

## The team

| Agent | Skill | Authority |
|-------|-------|-----------|
| **Regime Analyst** | `regime-detection` | sets gross exposure multiplier |
| **Research Analyst** | `fundamental-analysis` | data sources, valuation context, defensive-sleeve choice, **backtest gate** |
| **Signal Analysts** | `trend-following` (+ factor/macro analysts) | per-asset in/out & ranks |
| **Portfolio Manager** | `portfolio-construction` | proposes target weights |
| **Risk Manager** | `risk-management` | **veto + de-risk**; final say on size |
| **Rebalancer** | `rebalancing` | computes minimal trade deltas |
| **Cash Deployer** | `dip-tranches-strategy` | deploys dry powder on drawdowns |
| **Tax Agent** | `tax-loss-harvesting` | harvests losses on taxable sleeves |
| **Execution** | (broker API) | places approved orders |

## The daily loop (notification-first)
```
1. INGEST    pull EOD prices (yfinance) + macro (FRED).            [data-sources]
2. REGIME    regime-detection -> exposure_multiplier.
3. ANALYZE   fundamental-analysis -> valuation context + defensive-sleeve ETF choice;
             any NEW candidate signal must clear the backtest gate before it can trade.
4. SIGNALS   trend-following + analysts -> per-asset signals.
5. CONSTRUCT portfolio-construction -> target weights (× exposure_multiplier).
6. RISK      risk-management -> vol target, drawdown de-risk, CPPI, caps -> risk_scale / veto.
7. DIP       dip-tranches-strategy -> any reserve tranche firing today?
8. REBALANCE rebalancing -> minimal trade deltas (calendar check, threshold act, no-trade bands).
9. TAX       tax-loss-harvesting -> swap any underwater taxable lots.
10. NOTIFY   email/Telegram the proposed trades + plain-English rationale + risk report.
11. EXECUTE  human approves -> execution agent places orders (Alpaca/IBKR).
12. LOG      append every signal/decision/order to an immutable audit log; update metrics.
```

## Shared state (cuts tokens & drift)
Agents read/write a single structured **state object** (JSON) rather than re-deriving facts through long
dialogue. Use structured outputs for facts; reserve natural-language debate (bull vs bear) for the steps
where reasoning genuinely adds value.

```json
{
  "date": "2026-05-29",
  "nav": 1000000,
  "regime": {"exposure_multiplier": 0.7, "score": 0.32},
  "signals": {"SPY": "in", "VXUS": "out", "GLD": "in"},
  "targets": {"RSP": 0.18, "VXUS": 0.12, "...": "..."},
  "risk": {"verdict": "scale", "risk_scale": 0.7, "current_drawdown": -0.04},
  "dip": {"tier_fired": null},
  "trades": [],
  "audit_log_ref": "logs/2026-05-29.jsonl"
}
```

## Non-negotiable guardrails
- Human approval for: any new live strategy, trades above a notional threshold, any leverage change.
- Paper-trade for weeks; require live-paper Sharpe/drawdown to match backtest within tolerance.
- Deterministic **kill switch** + hard exposure caps the agents cannot override.
- Full, immutable **audit trail** (Git-committed logs or append-only store).

## Pitfalls to design against
Overfitting (walk-forward, deflate Sharpe for # of trials), look-ahead bias (point-in-time data, decide
on prior close), survivorship bias (yfinance lacks delisted names), transaction costs (#1 killer of
paper-profitable strategies), regime change (test across 2008/2020/2022), LLM overconfidence (bound by
the deterministic risk layer).

## Metrics contract (every agent reports, net of costs)
CAGR, Sharpe, Sortino, Calmar, max & current drawdown, realized vs target vol, gross/net exposure,
turnover, win rate + payoff, effective # of bets, time-in-drawdown, per-sleeve attribution.

## Starter stack
yfinance + FRED → vectorbt / `bt` research → Alpaca **paper** → human-approved go-live with hard caps in code.
See the `research/` notes 05 and 06 for the full architecture and data/API details.
