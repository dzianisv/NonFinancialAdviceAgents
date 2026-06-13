---
name: superforecasting
description: Use when the question is a near-term MARKET-OUTCOME forecast under a dated catalyst — any asset (crypto, equities, indices, rates, macro). "Is now a good time to buy X", "where does X go by [date]", "what happens after CPI/FOMC/earnings/the unlock/the ETF decision", "make a prediction", "what are the odds", "will X hold $Y". Distinct from multi-lens-quorum (which renders a buy/hold verdict): this produces a CALIBRATED PROBABILISTIC FORECAST — scenarios with probabilities, anchored to prediction-market + options-implied odds, with measurable invalidation triggers, logged to be scored. Educational, not advice; a forecast is a probability, not a promise.
license: MIT
compatibility: opencode
metadata:
  audience: anyone-forecasting-a-dated-market-outcome
  domain: probabilistic-market-forecasting
  role: forecasting-method
  source: codifies the superforecasting-on-market-odds method run 2026-06-10/11 (BTC/SOL/CPI/FOMC + equity positioning)
---

# Superforecasting the Market

Turn a "what happens next / is now the time" question into a **calibrated probabilistic forecast** you
can be **scored** on later. Not a vibe, not a single verdict — a **base case with a probability**, the
alternates with theirs, the **measurable triggers** that flip it, and a **ledger entry** so it gets
graded. Asset-agnostic: crypto, stocks, indices, rates, macro — same method, different lenses & venues.

Lineage (name it when asked): **Tetlock & Gardner, *Superforecasting* (2015)** — dragonfly-eye
aggregation, base rates, calibration; **Hayek (1945) / Hanson / Wolfers & Zitzewitz** — markets aggregate
dispersed info (the odds anchor); **Soros, *Alchemy of Finance* (1987)** — reflexivity for price
mechanics. `multi-lens-quorum` is the *verdict* sibling; this is the *forecast* method on top of it.

## When to use vs not (cost gate)

**Use when ALL hold:** the output wanted is a **prediction about a market outcome** (not a buy/hold
opinion); there's a **dated catalyst/horizon** a market can price (CPI/FOMC, earnings, unlock, ETF ruling,
"by month-end"); the probability **matters**.

**Do NOT use when:** it's a fact/lookup/definition; it's a pure allocation/buy-hold verdict → `multi-lens-quorum`
or a domain lens; or there's **no observable resolution** to score (then it's storytelling).

## The method (6 steps)

1. **Frame as a scored question.** Restate with a resolution date + observable outcome
   (`P(SPX ≤ 7000 before 2026-07-18)`), not "is it a good time". Ungradable = opinion.
2. **Convene the lenses — delegate, don't reinvent.** **REQUIRED SUB-SKILL: `multi-lens-quorum`** for the
   convene/synthesize mechanics (independent context-firewall subagents, one lens each, identical facts,
   preserve dissent). Prefer **real subagents** over inline role-play — independence is the point.
3. **Anchor to market-implied odds — first-class input, not a footnote.**
   - **REQUIRED: `prediction-market-odds`** — discrete dated events (Fed cut? CPI bucket? ETF approval?).
   - **REQUIRED: `analyst-derivatives-positioning`** — the **continuous** options-implied distribution +
     positioning (implied move, skew, max-pain, gamma; funding/OI/COT). 
   Anchor your probabilities to these; deviate only with a **stated reason** (you know something the
   market is slow on). This is the step a naive analyst skips.
4. **Synthesize without averaging away dissent.** State a **base case + probability**, then alternates.
   Lenses+odds **agree** → high conviction; **split** → that spread IS the forecast. Don't blend bull+bear
   into a shrug.
5. **Emit invalidation triggers.** The **single observable that flips the call** + the **measurable de-risk
   level**. Falsifiable or worthless.
6. **Log to be scored.** **REQUIRED: `forecast-ledger`** — the `Q (scored)` line has a probability + date;
   log at emission, resolve on the date. Unscored forecasting is cosplay.

## Lens selection (the forecast-specific rule)

Pick **outcome-relevant** seats — ones with a view on *where price goes by the date*:

- **Crypto:** technical, macro/liquidity (`analyst-crypto`), on-chain/regime, derivatives-positioning,
  prediction-market, reflexivity, risk/skeptic.
- **Equities/index:** technical, macro/liquidity (`macro-panel`), derivatives-positioning (COT/VIX/GEX),
  prediction-market, reflexivity, risk/skeptic.

**Exclude pure-value seats (Graham/Buffett) for short-horizon price forecasts** — they answer *should I
own this / how much*, not *where does price go in 3 weeks*. They belong in an allocation quorum, not a
dated price forecast. **Always include the risk/skeptic seat** — it red-teams the anchor and catches stale
premises.

## Output shape (always)

```
Q (scored):   P(<outcome> by <date>)            ← also the forecast-ledger entry
Base case:    <claim> — ~XX%   (market/options price YY%; deviate because ...)
Alternates:   <up scenario> ~A% | <down scenario> ~B%
Flip trigger: <single observable that turns the call>  (low odds: market gives Z%)
De-risk:      <measurable level / event that confirms the bear>
Confidence:   high where lenses+odds agree; flag the splits
Caveats:      thin/illiquid markets, frozen snapshots, risk-neutral≠real, stale data
Logged:       forecast-ledger id <...>
```

## Common mistakes

| Mistake | Fix |
|---|---|
| Skip the market odds, guess the probability | Pull prediction-market + options-implied first; they're the anchor |
| "Cautious, scale in" with no number | Emit an actual probability + scenario split |
| Pure-value seat on a 3-week price forecast | Exclude it — wrong tool for short-horizon price |
| One lens (usually TA) carries the call | Delegate to quorum; mandatory skeptic + odds seats |
| Forecast with no flip trigger | Name the single observable that invalidates it |
| Emit and forget | Log to forecast-ledger or it can't be scored |
| Quote options-implied prob as real odds | It's risk-neutral — haircut and label it |

## Red flags — you're doing it wrong if

- Verdict with **no probability**. No **prediction-market / options** pull. No **dated resolution**. No
  **flip trigger**. One lens, **no skeptic**. **Not logged** to forecast-ledger.

> Educational, not advice. A forecast is a calibrated probability, not a promise; each lens is a lens.
> Re-pull odds before acting — they drift.
