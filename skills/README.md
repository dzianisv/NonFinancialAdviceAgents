# Skills — Agentic Hedge-Fund Team (opencode)

opencode-compatible `SKILL.md` modules for an automated, agent-driven portfolio.
Each is self-contained with YAML frontmatter (`name`, `description`, `license`,
`compatibility: opencode`). The descriptions are written so the right skill triggers
from a natural-language request.

**All skills are educational frameworks, not personalized financial advice.**

## The team & how they connect

```
                 regime-detection ──exposure──┐
trend-following ──signals──┐                  ▼
                           ▼          portfolio-construction ──targets──┐
                  (analyst inputs)                                      ▼
                                                              risk-management (VETO)
                                                                        │ risk_scale / approve
                                          ┌─────────────────────────────┤
                                          ▼                             ▼
                                    rebalancing                 dip-tranches-strategy
                                          │                             │ (deploys dry powder)
                                          ▼                             │
                                  tax-loss-harvesting ◄─────────────────┘
                                          │
                                          ▼
                                     execution (notification-first)
```

`agentic-fund-orchestration` is the top-level playbook that wires the daily loop together.

## Index

| Skill | Role | What it does |
|-------|------|--------------|
| [strategy-discovery-backtest](strategy-discovery-backtest/SKILL.md) | **the gate** | hypothesis→backtest(no look-ahead, real costs)→walk-forward→deflate→stress→PASS/FAIL. Runs FIRST on any "trade X" (backtest-before-trade invariant) |
| [crypto-daytrading](crypto-daytrading/SKILL.md) | day-trade desk | crypto intraday income (BTC/ETH/SOL/HYPE+), 24/7, fees/funding, Coinbase CDP — gated by the above |
| [stock-daytrading](stock-daytrading/SKILL.md) | day-trade desk | equity intraday income, RTH/PDT rule, Robinhood — gated by the above |
| [agentic-fund-orchestration](agentic-fund-orchestration/SKILL.md) | orchestrator | the daily decision loop, shared state, guardrails |
| [regime-detection](regime-detection/SKILL.md) | regime analyst | risk-on/off → gross-exposure dial (+ runnable `regime_monitor.py`) |
| [fundamental-analysis](fundamental-analysis/SKILL.md) | research analyst | what data/sources the analyst reads, screens, and the mandatory backtest gate (honest verdict: stock-picking ≠ alpha) |
| [trend-following](trend-following/SKILL.md) | signal analyst | 200d-MA / dual-momentum / managed-futures crisis alpha |
| [portfolio-construction](portfolio-construction/SKILL.md) | portfolio manager | bubble-aware all-weather target weights (3 risk tiers) |
| [risk-management](risk-management/SKILL.md) | risk manager | vol target, drawdown de-risk, CPPI, caps — deterministic veto |
| [rebalancing](rebalancing/SKILL.md) | portfolio manager | calendar-check / threshold-act, tax-aware, no-trade bands |
| [dip-tranches-strategy](dip-tranches-strategy/SKILL.md) | cash deployer | tiered dip-buying of dry powder (+ runnable `check_drawdown.py`) |
| [tax-loss-harvesting](tax-loss-harvesting/SKILL.md) | tax agent | harvest losses without tripping wash-sale rules |

## Runnable helpers
- `regime-detection/regime_monitor.py` — daily regime score → exposure multiplier (yfinance).
- `dip-tranches-strategy/check_drawdown.py` — drawdown-from-52w-high → which dip tranche fires.
- `dip-tranches-strategy/dip_tranches_strategy.pine` — TradingView indicator.

## Provenance
The backtest evidence behind these skills lives in `../research/` (notes 02-05) and the
scripts in `../backtests/` (`backtests/crash_protection_backtest.py`, etc.). The strategy these skills
implement is written up in `../strategy/` (v3 is current). Run notification-first; paper-trade
before live; keep hard caps in code outside the LLM.
