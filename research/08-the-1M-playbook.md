# 08 — The $1M Playbook (Synthesis)

*A concrete framework for deploying $1,000,000 in a possible AI bubble.
**This is educational analysis, not personalized financial advice.** Before
deploying real capital at this size, talk to a fee-only fiduciary CFP and write
a one-page Investment Policy Statement you'll actually follow through a −40% drawdown.*

## The decision in one paragraph

The evidence (notes 01, 03) says cap-weight S&P/QQQ at CAPE ~41 with ~40% top-10 AI concentration
carries a fat left tail: the base rate for bursting concentration bubbles is **−50% to −78% and
7-15 years to recover**, and 2000-2009 was a *lost decade* for the index. The fix is **not** to
predict the crash or sit in cash (a loser's game), and **not** to abandon equities (you'd forfeit the
upside if AI delivers). The fix is to **(a) de-concentrate the equity core, (b) add uncorrelated
diversifiers and crisis-alpha that don't depend on a market call, and (c) keep dry powder to deploy
*into* a decline by rule.** You participate if the bull continues, and you survive — with ammo — if it
breaks.

## Three things this plan is built to avoid

1. **Concentration:** owning ~40% in ten AI-correlated mega-caps by default.
2. **Single-regime fragility:** betting everything on "growth keeps rising" (or on bonds as the only hedge — 2022 broke that).
3. **Behavioral failure:** a portfolio so volatile you panic-sell the bottom, or so cash-heavy you never get invested.

## The recommended portfolio — "Bubble-Aware Growth"

Pick a risk tier. Each is a **target allocation** for the fully-deployed portfolio; the
deployment *schedule* (next section) is how you get there from $1M cash.

| Sleeve | ETF examples | Defensive (cautious) | **Balanced (default)** | Growth-tilt |
|--------|--------------|:-----:|:-----:|:-----:|
| US large cap | VOO / RSP (equal-wt) | 12% | 18% | 26% |
| International | VXUS / VEA+VWO | 10% | 12% | 12% |
| US small/mid **value** | AVUV / VBR | 6% | 8% | 10% |
| Min-vol / quality equity | USMV / QUAL | 8% | 7% | 6% |
| **Gold** | GLD / IAU | 12% | 10% | 8% |
| **Trend / managed futures** | DBMF / KMLM | 12% | 10% | 8% |
| Long/intermediate Treasuries | TLT / IEF | 8% | 7% | 4% |
| TIPS / commodities (inflation) | SCHP / PDBC | 5% | 3% | 2% |
| **Dry powder (T-bills)** for dip reserve | SGOV / BIL | 25% | 22% | 22% |
| Tail / anti-beta (optional, small) | TAIL / BTAL | 2% | 3% | 2% |
| **Total equity beta** | | ~36% | ~45% | ~54% |

**Why this shape (tying to the evidence):**
- Equity is **de-concentrated** (equal-weight option, international, value, min-vol) rather than ~40%
  AI mega-caps — directly addresses note 01's concentration risk.
- **Gold + trend** are the two diversifiers that *worked in 2022* when bonds failed (note 02). Trend is
  "crisis alpha" that was positive in 8 of 10 worst 60/40 drawdowns.
- **Treasuries kept modest** (not the 40% of classic All-Weather) because of the 2022 duration lesson and
  today's starting point (note 04).
- **~22-25% dry powder** is deployed *into* declines via the dip-tranche rules (below), turning a crash
  from a threat into an opportunity — and earning ~4-5% in T-bills while it waits.
- The optional small **tail/anti-beta** sleeve covers the *fast* crash (2020-style) that breaks trend.

Backtest sanity check (note 03): diversified all-weather mixes earned ~7-8%/yr 2000-2026 with **−16% to
−24% max drawdowns vs the S&P's −55% / QQQ's −83%**, and roughly *doubled* through the 2000-2009 lost
decade while the index went nowhere — without any market-timing call.

## The deployment schedule (cash → invested)

Don't dump $1M in one day at all-time highs (regret risk is high here). Use a tranche structure on the
**whole portfolio**, layering the dip-tranche skill on top:

| Bucket | % of $1M | How |
|--------|:--------:|-----|
| **Foundation** | 50% ($500K) | Buy the target allocation now (or spread over 4-8 weeks). Time-in-market. |
| **Systematic DCA** | 28% ($280K) | Equal monthly buys of the target mix over 12-18 months. Removes timing stress. |
| **Dip Reserve** | 22% ($220K) | Held in SGOV; deployed on S&P drawdowns by tier (below). |

**Dip-reserve tiers** (from the `dip-tranches-strategy` skill), measured from the 52-week high, each tier
split into sub-tranches with a time-based catch-all:

| Tier | Trigger (from 52-wk high) | % of reserve | Sub-tranches |
|------|:--:|:--:|:--:|
| Tier 1 | −7% | 20% | −7% / −8.5% / −10% / time |
| Tier 2 | −12% | 30% | −12% / −14% / −16% / time |
| Tier 3 | −20%+ | 50% | −20% / −25% / −30% / time |

Use **weekly closes**, not intraday wicks. Don't skip tiers. If 18-24 months pass with no dip, fold the
unused reserve into the DCA stream (cash drag is a real cost). Deploy dip cash into the **de-concentrated
mix** (or tilt slightly toward whatever fell hardest), not just into QQQ.

## Operating rules (rebalancing & discipline)

- **Rebalance** on a calendar check (quarterly) but **act only on threshold breach** (a sleeve drifts
  > ±20% relative, or > ±5% absolute). Low turnover, tax-aware (harvest losses — see the TLH skill).
- **Trend sleeve** does its own switching; you just hold the ETF.
- **Sell discipline (write it down now):** you are *not* selling on headlines. You rebalance mechanically;
  you let trend/min-vol do the de-risking. The only discretionary "pause" is the last dip sub-tranche if
  it's a genuine 2008-style systemic event (VIX > 40, credit spreads blowing out, rising unemployment) —
  then reassess rather than catch a falling knife.
- **What would change the thesis:** AI capex starts earning clear ROI and breadth broadens durably →
  you can drift toward the Growth-tilt column. Concentration and CAPE keep rising on debt-funded capex →
  stay Defensive and keep the trend/gold/dry-powder weights up.

## Automating it (the agentic team — note 05)
Encode this as the `skills/` SKILL.md set: **regime-detection** (sets exposure), **portfolio-construction**
(targets above), **risk-management** (deterministic caps + drawdown de-risking), **dip-tranches** (reserve
deployment), **rebalancing**, **tax-loss-harvesting**. Run notification-first daily; paper-trade before
live; keep hard caps in code outside the LLM; log everything.

## The honest trade-off
In a continued AI bull, this portfolio **will** lag a 100% QQQ holder — possibly by a lot (note 03:
+282% vs +3187% in the 2009-2026 bull). That underperformance is the **premium you pay** to not lose
50-80% and a decade if the bubble bursts. If your honest answer is "I have a 20-year horizon, I'll never
sell, and I can stomach −80%," then a larger cap-weight equity slice is defensible. For most people
deploying a $1M windfall who are *already worried about a bubble*, capping the left tail is worth the
premium. Choose the column that matches the drawdown you can actually live through.

---
*Educational only. Not investment, tax, or legal advice. Past backtest performance does not guarantee
future results. Consult a licensed fiduciary before acting.*
