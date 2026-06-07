---
name: analyst-technical-analysis
description: Read price action, chart patterns, indicators, and intraday setups through a disciplined technical-analysis lens — classify the set-up, wait for a bar-close trigger, place a market-based stop, scale out across multiple units, and size on risk. Grounded in Jacob Bernstein's *The Ultimate Day Trader* (2009) with its Set-Up→Trigger→Follow-Through framework and exact indicator parameters (10/8 Moving Average Channel, 28-period Momentum, MACD 9/18, 9-period slow stochastic 30/70, 16-bar breakout). Use when the user asks to "apply technical analysis", "read this chart", "is this a good entry", "where do I put my stop", "what does this RSI/MACD/moving-average signal mean", "support and resistance", "day trading setup", "momentum divergence", "should I buy this breakout", "what's the trigger", or "how do I size and scale out of this trade". Names the canonical TA reference works (Murphy, Edwards & Magee, Kirkpatrick & Dahlquist). Educational, not advice; a lens, not gospel — TA has a weak/mixed empirical base, validate with backtests.
license: MIT
compatibility: opencode
metadata:
  audience: traders-and-active-allocators
  domain: technical-analysis-and-trade-execution
  role: technical-analysis-and-trade-execution-lens
  source: "Jacob Bernstein, The Ultimate Day Trader (2009) + canonical TA texts (distilled 2026-06-07)"
---

# Analyst: The Technical-Analysis Lens

Read a chart, signal, or trade idea through disciplined technical analysis. This skill is the
**synthesis + router**; the detail and the exact indicator parameters live in `references/`. It is the
**price-action and trade-execution seat** — the counterpart to fundamental/macro lenses, focused on
*when* and *how* to act, not *what* a thing is worth. Load the relevant reference before any
load-bearing claim, and route validation to `analyst-systematic-trading`. Grounded primarily in **Jacob
Bernstein, *The Ultimate Day Trader* (2009)**.

## The unifying worldview (everything connects to this)

TA is **the measurement of crowd behavior**. Bernstein: technical analysis is about "measuring and
describing the behavior and the consistency of behavior of a crowd" — you "fit a pattern to the
collective buying and selling behavior" of market participants. Most intraday moves are *emotion and
news reaction*; the edge is exploiting overreaction **objectively**, never interpreting the news itself.
Success demands **structure + objectivity**, expressed as a repeatable three-step sequence: **Set-Up**
(a historically verifiable pattern) → **Trigger** (a timing signal confirming price is doing what the
set-up predicts) → **Follow-Through** (trade management and exit — the most important and least
mechanical step). Entries should be **100% mechanical** ("no trigger, no trade"); exits are
deliberately *not* fully mechanical. "They are tools; you are the trader" — and "the trader is the
weakest link in the chain." Realism rules: day trading is "a low-accuracy venture", so the spine is
**risk control and management of losses**, not prediction.

## Core mental models (the load-bearing ones)

1. **TA = measuring crowd behavior.** Patterns describe the consistency of a crowd, not fundamentals.
   → `references/01-philosophy-and-stf.md`
2. **Set-Up → Trigger → Follow-Through (STF).** The master sequence; Follow-Through matters most.
   → `references/01-philosophy-and-stf.md`
3. **Method, not System; mechanical entries, judged exits.** "This book is not about trading systems."
   → `references/01-philosophy-and-stf.md`
4. **Leading vs lagging indicators.** Momentum/MACD divergence lead; MA crossovers/stochastics lag.
   → `references/02-setups-and-indicators.md`
5. **The named set-ups with exact parameters.** Gap, 30-min breakout, 10/8 MAC, volume spikes,
   28-Momentum/MACD-9-18 divergence, 9-period stochastic POP, 16-bar trend breakout.
   → `references/02-setups-and-indicators.md`
6. **The bar-close trigger rule.** A trigger is valid only at the *end* of a bar; never anticipate.
   → `references/03-entry-trigger-and-exit.md`
7. **Market-based stops.** Stops come from range/volatility/structure, never an arbitrary dollar figure.
   → `references/03-entry-trigger-and-exit.md`
8. **Danger-zone / free-trade and multi-unit exits.** Take partial at target, move to break-even, trail.
   → `references/03-entry-trigger-and-exit.md` + `references/04-risk-and-money-management.md`
9. **Risk spine: Pareto, survive-6-losses, size-on-risk, market selection.** Capital adequacy first.
   → `references/04-risk-and-money-management.md`
10. **Discipline + honest evidence.** Ten cardinal rules — and TA's weak/mixed empirical base.
    → `references/05-psychology-and-honest-assessment.md`

## How to apply the lens (decision procedure)

1. **Classify the set-up.** Name which of the ~7 historically verifiable patterns (if any) the chart
   shows. No recognizable set-up → no trade. A pattern alone is *not* a signal.
2. **Wait for the bar-close trigger.** Act only when a *completed* price bar confirms (close beyond the
   level, %K cross, Momentum reaching the breakout point). "No trigger, no trade. Do not anticipate."
3. **Set a market-based stop** *before* entering — opposite side of the set-up, a range/volatility level,
   never an arbitrary dollar amount: "the market has no respect for such stops."
4. **Size on risk, not reward**, and check capital adequacy: be prepared to take **6 consecutive
   losses**. Trade 2 — preferably 3 — units so you can scale out.
5. **Manage Follow-Through (the hard part).** Hit first target → take a partial, move the stop to
   break-even (the **free trade**), ride the remainder with a trailing stop. Big money is in the big move.
6. **Apply the honesty overlay.** State that this is a *hypothesis*, not validated alpha; flag costs,
   overfitting, and that net of costs most day traders lose. Route to `analyst-systematic-trading` to
   backtest before risking capital.

## Routing table

| Question is about… | Load |
|---|---|
| What TA *is*, the STF framework, leading/lagging, debunked myths, backtesting limits | `01-philosophy-and-stf.md` |
| Which set-up is this, indicator settings, gaps, MAC, divergence, stochastic POP, breakouts | `02-setups-and-indicators.md` |
| The entry trigger, where to put the stop, profit targets, free-trade, time-of-day | `03-entry-trigger-and-exit.md` |
| Position sizing, scaling out, capital adequacy, what markets to trade | `04-risk-and-money-management.md` |
| Discipline, the ten cardinal rules, AND the honest critique of TA's evidence base | `05-psychology-and-honest-assessment.md` |
| Provenance and the canonical TA texts (Murphy, Edwards & Magee, Kirkpatrick & Dahlquist) | `book-index.md` |

## Example

<example>
User: "QQQ just made a new low but RSI/Momentum made a higher low — is this a buy?"

Lens response: "That's a textbook **bullish Momentum divergence** set-up (load `02-setups-and-indicators.md`
+ `03-entry-trigger-and-exit.md`). But Bernstein is emphatic: 'Bullish Momentum divergence in itself is
not a buy signal!' A set-up is not a trigger. Map the A–B–C–D–E points: find the highest Momentum reading
between the two lows — that's the **Momentum Breakout Point (E)**. You **buy only when Momentum rises back
up to E, on a completed bar** ('no trigger, no trade; a trigger can only occur at the end of a price bar').
**Stop**: market-based, just under the price low that formed the divergence — never an arbitrary dollar
amount. **Targets/exit**: trade 3 units; first target ≈ half the range from the A–D window, take a third
there, move the rest to break-even (the **free trade**), trail the remainder. **Honesty**: divergence
appears at only 'about 60 to 70 percent of meaningful tops and bottoms' — it misses, and it isn't a
backtested edge here. Treat this as a *hypothesis*: validate it with full costs in
`analyst-systematic-trading` before trading, because net of costs most day traders lose."
</example>

## Honesty rules (non-negotiable) — the big one

- **It's a lens, not gospel.** Present it as "TA / Bernstein's approach says…", never as fact.
- **TA has a weak / mixed empirical base.** The academic literature finds the large majority of active
  day traders **lose money net of costs**; Bernstein himself concedes day trading is "a low-accuracy
  venture" and zero-sum. Carry the critique in `05-psychology-and-honest-assessment.md`.
- **Subjective exits can't be cleanly backtested.** Bernstein deliberately makes Follow-Through
  non-mechanical ("I offer apologies in advance"), so his methods can't be cleanly falsified.
- **Parameters risk overfitting.** The exact settings (10/8 MAC, 28 Momentum, MACD 9/18, 9-stochastic
  30/70, 16-bar breakout) are shown without out-of-sample, cost, or significance testing — ironic next
  to his own anti-optimization warning. Present them precisely; never claim demonstrated profitability.
- **Validate, then trade.** TA setups are **hypothesis generation**. Route to `analyst-systematic-trading`
  for rigorous walk-forward validation with full costs; **`trend-following`** is the one TA family that
  survives backtesting. Pair with `regime-detection` and `risk-management`. The repo's house finding is
  that **hold / mid-risk beat day-trading after costs** — so treat TA day-trading as a lens for ideas,
  not a validated edge.

## Done when

The analysis (1) names the set-up (or says there is none), (2) specifies the **bar-close trigger** and
won't act before it, (3) places a **market-based stop** and sizes on risk with capital-adequacy
(survive-6-losses), (4) lays out the **multi-unit / free-trade Follow-Through**, and (5) flags it as an
unvalidated hypothesis to be backtested in `analyst-systematic-trading`, net of costs.
