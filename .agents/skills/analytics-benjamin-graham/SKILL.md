---
name: analytics-benjamin-graham
description: Analyze a stock, portfolio, or market through Benjamin Graham's framework — the original value-investing discipline from *The Intelligent Investor* and *Security Analysis*. Distinguish investment from speculation (safety of principal + adequate return after thorough analysis), demand a margin of safety, treat the market as manic-depressive Mr. Market (serve, don't obey), and pick a program — the defensive investor (a simple, rules-based, low-maintenance portfolio with quantitative screens) or the enterprising investor (statistical bargains: net-nets / NCAV, the Graham number). Hold a deliberate stock/bond split (25–75% bounds, ~50/50 default) and rebalance mechanically. Use when the user asks "what would Graham do", "apply the Graham / Intelligent Investor lens", asks about margin of safety, Mr. Market, intrinsic value the Graham way, net-nets / net current asset value, the Graham number, defensive vs enterprising investing, the 7 stock-selection criteria, investment vs speculation, or a rules-based deep-value / quantitative-value screen. Distilled from Graham's books, FAJ articles, and 1976 interview (references/). Educational, not advice; a lens, not gospel — classic net-nets are nearly extinct and pure statistical value lagged growth for long stretches.
license: MIT
compatibility: opencode
metadata:
  audience: long-term-investors
  domain: value-investing-and-security-analysis
  role: value-discipline-lens
  source: Graham's The Intelligent Investor + Security Analysis + FAJ essays (distilled 2026-06-07)
  panel-seat: value-origin-and-rules-based-margin-of-safety
---

# Analytics: The Benjamin Graham Lens

Apply Benjamin Graham's framework to a question. This skill is the **synthesis + router**; the detail
lives in `references/`. Graham is the **father of value investing** and Buffett's teacher — the
**rules-based, statistical** value seat. Where `analytics-warren-buffett` buys a *qualitative moat at a
fair price*, Graham buys a *quantitative bargain with a margin of safety* and protects the investor from
their own temperament with mechanical rules. Pair the two; load the relevant reference before a
load-bearing claim.

## The unifying worldview (everything connects to this)

Graham's project is **defense, not brilliance**: most investors lose money not to bad analysis but to bad
behavior, so build a discipline that makes you safe even when you're average and even when you're wrong.
Start by separating **investment from speculation** — an investment "promises safety of principal and an
adequate return"; everything else is speculation, fine in size you can afford to lose, fatal when
mistaken for investing. Buy securities only at a **margin of safety**: a price far enough below
conservative value that error, bad luck, and the future's unknowability can't ruin you. Source those
prices from **Mr. Market**, a manic-depressive partner who quotes a price every day — use his foolish
prices, ignore his moods. Then pick the **program that fits your temperament and effort**: the
**defensive investor** runs a simple, rules-screened, low-turnover portfolio and accepts adequate
results; the **enterprising investor** does the work to find **statistical bargains** (net-nets,
sub-Graham-number stocks) and earns a premium for it. Hold a deliberate **stock/bond allocation** inside
25–75% bounds (default ~50/50) and **rebalance mechanically** so volatility becomes your servant. The
"intelligent" investor is defined by **temperament and framework, not IQ**.

## Core mental models (the load-bearing ones)

1. **Investment vs speculation.** "An investment operation is one which, upon thorough analysis, promises
   safety of principal and an adequate return. Operations not meeting these requirements are
   speculative." → `references/01-investment-vs-speculation.md`
2. **The intelligent investor is temperament, not intellect.** The enemy is in the mirror; rules exist to
   bind the emotional investor. → `references/01-investment-vs-speculation.md`
3. **Mr. Market.** A manic-depressive partner quoting prices daily; he's there to serve you, not guide
   you — act only on his foolish prices. → `references/02-mr-market-and-margin-of-safety.md`
4. **Margin of safety — the central concept.** Buy well below conservative value; the gap absorbs error.
   "The function of the margin of safety is… rendering unnecessary an accurate estimate of the future."
   → `references/02-mr-market-and-margin-of-safety.md`
5. **Defensive investor program + the 7 stock-selection criteria.** Adequate size, strong financials,
   dividend & earnings record, moderate P/E (≤15) and P/B (≤1.5), P/E×P/B ≤22.5.
   → `references/03-defensive-vs-enterprising.md`
6. **Enterprising investor & statistical bargains.** Net-nets / NCAV (buy below ⅔ of net current assets),
   the **Graham number** = √(22.5 × EPS × BVPS) as a defensive upper-bound on price.
   → `references/03-defensive-vs-enterprising.md`
7. **Stock/bond allocation 25–75% bounds, ~50/50 default.** Never all-in or all-out; the split is policy,
   not a forecast. → `references/04-asset-allocation-and-rebalancing.md`
8. **Mechanical rebalancing & formula investing.** Sell into strength, buy into weakness on a rule, not a
   feeling; dollar-cost-average. → `references/04-asset-allocation-and-rebalancing.md`
9. **Don't forecast; analyze and diversify.** Adequate diversification + margin of safety beats market
   timing and prophecy. → `references/03-defensive-vs-enterprising.md`
10. **Where the rules break today.** Classic net-nets are nearly extinct; pure statistical value lagged
    quality/growth for long stretches; Graham himself endorsed indexing late in life.
    → `references/05-applying-graham-today.md`

## How to apply the lens (decision procedure)

1. **Classify the operation.** Is this investment (thorough analysis + safety of principal + adequate
   return) or speculation? Name it honestly; size speculation as a small, losable sleeve.
2. **Pick the program.** Defensive (rules, low effort, adequate return) or enterprising (real work for a
   premium)? Don't half-do the enterprising path — partial effort earns speculative results.
3. **Screen.** Defensive → run the 7 criteria. Enterprising → hunt statistical bargains (NCAV net-nets,
   price below the Graham number) with a diversified basket, not single bets.
4. **Demand a margin of safety** on every buy: price well below conservative value. No margin → don't
   buy; cash and bonds are legitimate positions.
5. **Use Mr. Market, don't obey him.** Treat the quote as an offer; act only when it's absurdly cheap or
   rich relative to your independent value.
6. **Set and hold the allocation.** Choose a stock/bond split in 25–75% bounds; rebalance mechanically on
   a schedule or threshold, not on a market call.
7. **Separate the timeless rule from the dated number.** The framework is evergreen; specific screen
   thresholds and the scarcity of net-nets are time-bound — see `05-applying-graham-today.md`.

## Routing table

| Question is about… | Load |
|---|---|
| Is this investing or gambling, "the intelligent investor", behavior/temperament, diversification basics | `01-investment-vs-speculation.md` |
| Mr. Market, market volatility/sentiment, margin of safety, price vs value | `02-mr-market-and-margin-of-safety.md` |
| How to actually pick stocks, the 7 criteria, net-nets / NCAV, the Graham number, defensive vs enterprising | `03-defensive-vs-enterprising.md` |
| Stock/bond mix, rebalancing, formula investing, dollar-cost averaging, bonds & inflation | `04-asset-allocation-and-rebalancing.md` |
| Does Graham still work, net-net scarcity, value vs growth, screening today, indexing | `05-applying-graham-today.md` |

## Example

<example>
User: "Apply the Graham lens: a profitable small-cap trades at 0.8× net current assets. Buy?"

Lens response: "Graham's lens (load `02-mr-market-and-margin-of-safety.md` + `03-defensive-vs-enterprising.md`):
this is the classic **net-net** setup — price below net current asset value (current assets − all
liabilities), the purest margin of safety because you're paying less than liquidation-grade working
capital and getting the business for free. Graham's rule was to buy below **two-thirds of NCAV**, so at
0.8× it's cheap but past his strict ⅔ threshold — borderline, not a screaming bargain. Critically, he
never bet on one net-net: the edge is **statistical**, realized across a *diversified basket* of 20–30
such names where the winners cover the value-traps. So: only as an **enterprising** position, in a
basket, sized small, and confirm it's not a melting ice cube burning the working capital. Hedge: genuine
net-nets are nearly extinct in large/mid caps today (see `05-applying-graham-today.md`) and a single one
at 0.8× with deteriorating cash flow can still be a trap — the margin of safety is in the basket and the
balance sheet, not this one screen."
</example>

## Honesty rules (non-negotiable)

- **It's a lens, not gospel.** Present it as "Graham's approach says…".
- **It has real limits.** Classic net-nets are nearly extinct in developed large/mid caps; strict
  statistical value lagged quality/growth for long stretches (notably the 2010s); the 7-criteria
  thresholds are 1970s-calibrated and screen out most modern asset-light compounders; Graham endorsed
  low-cost index funds for most people late in life. Carry each reference's Caveats.
- **Graham's frameworks are fixed (he died 1976); the application decays.** There is no "current views"
  file — `05-applying-graham-today.md` is how the timeless rules map to today's market, time-stamped.
- **Ground load-bearing claims** in a specific reference/source (via `references/article-index.md`).
- This skill is the **rules-based deep-value discipline** that pairs with `analytics-warren-buffett` (the
  qualitative-moat evolution of the same school) and complements `fundamental-analysis` +
  `hedge-fund-13f-analysis`; it does not replace the backtest/valuation gate.

## Done when

The analysis (1) classifies investment vs speculation, (2) picks the defensive or enterprising program,
(3) applies the right screen (7 criteria, or net-nets / Graham number) with diversification, (4) demands
a margin of safety and uses Mr. Market rather than obeying him, sets a rules-based stock/bond allocation,
and (5) flags any dated threshold or net-net-scarcity claim as time-stamped against today's market.
