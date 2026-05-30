# Strategy v3 — Bubble-Aware All-Weather (current)

> **Status: CURRENT recommendation.** Educational analysis, not financial advice. Before deploying
> real capital at this size, talk to a fee-only fiduciary and write a one-page Investment Policy
> Statement you'll actually follow through a −40% drawdown.

## The thesis

v1 showed entry timing barely matters. v2 showed selection doesn't reliably beat the index. So the
edge isn't *when* you buy or *what* you pick — it's **structure**:

1. **De-concentrate the equity core** (away from ~40% AI-correlated mega-caps).
2. **Add uncorrelated diversifiers and crisis-alpha** that don't depend on a market call (gold, trend).
3. **Keep dry powder** and deploy it *into* declines by rule.
4. **Govern it with deterministic risk management** and an agentic team.

You participate if the bull continues, and you survive — with ammo — if it breaks. No prediction required.

## The evidence it's built on

`backtests/crash_protection_backtest.py`, $1M, 2000-2026:

| Strategy | CAGR | Sharpe | Max DD | 2000-09 "lost decade" |
|---|:--:|:--:|:--:|:--:|
| S&P 500 Buy&Hold | 8.3% | 0.38 | **−55%** | **−9%** |
| QQQ Buy&Hold | 8.7% | 0.35 | **−83%** | **−50%** |
| 60/40 | 7.4% | 0.49 | −30% | +38% |
| Permanent Portfolio | 7.2% | **0.69** | **−16%** | +94% |
| Golden Butterfly | 8.0% | 0.67 | −22% | +104% |
| All-Weather (proxy) | 7.3% | 0.65 | −24% | +94% |
| Dual Momentum (GEM) | **9.9%** | 0.49 | −34% | +156% |
| Trend-Following (200d) | 9.1% | 0.57 | −23% | +115% |

Diversified / trend mixes beat the index on **risk-adjusted** terms and **roughly doubled through the
lost decade** while the index went nowhere — and in the dot-com bust (2000-02) the permanent/all-weather
portfolios were **flat-to-positive** while the S&P fell −47% and QQQ −83%. The cost: they lag in a
roaring bull (the premium for capping the tail). Full context:
[`../research/03-backtest-evidence.md`](../research/03-backtest-evidence.md),
[`../research/08-the-1M-playbook.md`](../research/08-the-1M-playbook.md).

## The portfolio — pick a risk tier

Each column is a **target allocation** for the fully-deployed portfolio. **Balanced is the default.**

| Sleeve | ETF examples | Defensive | **Balanced** | Growth-tilt |
|--------|--------------|:-----:|:-----:|:-----:|
| US large cap | VOO / RSP (equal-wt) | 12% | 18% | 26% |
| International | VXUS / VEA+VWO | 10% | 12% | 12% |
| US small/mid **value** | AVUV / VBR | 6% | 8% | 10% |
| Min-vol / quality equity | USMV / QUAL | 8% | 7% | 6% |
| **Gold** | GLD / IAU | 12% | 10% | 8% |
| **Trend / managed futures** | DBMF / KMLM | 12% | 10% | 8% |
| Long/intermediate Treasuries | TLT / IEF | 8% | 7% | 4% |
| TIPS / commodities | SCHP / PDBC | 5% | 3% | 2% |
| **Dry powder (T-bills)** | SGOV / BIL | 25% | 22% | 22% |
| Tail / anti-beta (optional) | TAIL / BTAL | 2% | 3% | 2% |
| **Total equity beta** | | ~36% | **~45%** | ~54% |

**Why this shape:** equity is de-concentrated (equal-weight, international, value, min-vol) instead of
~40% AI mega-caps; **gold + trend** are the two diversifiers that *worked in 2022 when bonds failed*;
Treasuries are kept modest (the 2022 duration lesson); ~22-25% dry powder is deployed into declines and
earns ~4-5% in T-bills while it waits; the optional tail sleeve covers the *fast* crash that breaks trend.

## The deployment schedule (cash → invested)

Don't dump $1M in at all-time highs. Tranche the whole portfolio:

| Bucket | % of $1M | How |
|--------|:--------:|-----|
| **Foundation** | 50% ($500K) | Buy the target mix now (or spread over 4-8 weeks). |
| **Systematic DCA** | 28% ($280K) | Equal monthly buys over 12-18 months. |
| **Dip Reserve** | 22% ($220K) | Held in SGOV; deployed on S&P drawdowns by tier (below). |

**Dip-reserve tiers** (from the 52-week high, weekly closes, don't skip tiers):

| Tier | Trigger | % of reserve | Sub-tranches |
|------|:--:|:--:|:--:|
| Tier 1 | −7% | 20% | −7% / −8.5% / −10% / time |
| Tier 2 | −12% | 30% | −12% / −14% / −16% / time |
| Tier 3 | −20%+ | 50% | −20% / −25% / −30% / time |

If 18-24 months pass with no dip, fold the unused reserve into the DCA stream (cash drag is real).
Deploy dip cash into the **de-concentrated mix**, not just into QQQ.

## Operating rules

- **Rebalance** on a calendar check (quarterly) but **act only on threshold breach** (sleeve drifts
  >±20% relative or >±5% absolute). Low turnover, tax-aware (harvest losses).
- **Sell discipline (write it down now):** you do *not* sell on headlines — you rebalance mechanically
  and let trend/min-vol do the de-risking. The only discretionary pause is the last dip sub-tranche in a
  genuine 2008-style systemic event (VIX > 40, credit spreads blowing out) — then reassess.
- **What would change the thesis:** AI capex starts earning clear ROI and breadth broadens durably →
  drift toward Growth-tilt. Concentration + CAPE keep rising on debt-funded capex → stay Defensive.

## How it runs — the agentic team

Implemented as the [`../skills/`](../skills/README.md) `SKILL.md` set, coordinated by
`agentic-fund-orchestration` in a daily, **notification-first** loop:

```
INGEST (yfinance+FRED) → REGIME (exposure dial) → ANALYZE (context + backtest gate)
→ SIGNALS (trend) → CONSTRUCT (target weights) → RISK (veto/de-risk, deterministic)
→ DIP (deploy reserve) → REBALANCE → TAX → NOTIFY (human approves) → EXECUTE → LOG
```

| Role | Skill |
|---|---|
| Regime analyst | `regime-detection` |
| Research analyst | `fundamental-analysis` (sources + mandatory backtest gate) |
| Signal analyst | `trend-following` |
| Portfolio manager | `portfolio-construction` + `rebalancing` |
| Risk manager (veto) | `risk-management` |
| Cash deployer | `dip-tranches-strategy` |
| Tax agent | `tax-loss-harvesting` |
| Orchestrator | `agentic-fund-orchestration` |

**Guardrails (non-negotiable):** notification-first for 6+ months; paper-trade before live; human
approval for go-live, large trades, and leverage changes; the kill switch + hard exposure caps live in
**deterministic code outside any LLM** — agents propose, the risk layer disposes; full immutable audit log.

## The honest trade-off

In a continued AI bull, this **will** lag a 100% QQQ holder — possibly by a lot (research note 03:
+282% vs +3187% in the 2009-2026 bull). That underperformance is the **premium you pay** to not lose
50-80% and a decade if the bubble bursts. If your honest answer is "20-year horizon, I'll never sell,
I can stomach −80%," a larger cap-weight slice is defensible. For a $1M windfall when you're *already
worried about a bubble*, capping the left tail is worth the premium. Choose the column that matches the
drawdown you can actually live through.

## Provenance
`backtests/crash_protection_backtest.py` + `backtests/results/crash_protection_summary.txt`;
`research/` notes 01-08; the agent team in `skills/`.
