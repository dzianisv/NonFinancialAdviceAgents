---
name: analyse-smartmoney
description: "The conductor lens for the smart-money skill family — routes to 8 specialist spokes (13F, 13D, Form 4, PTR, positioning, options flow, dark pool, prediction markets), collects per-signal verdicts, applies a reliability-weighted synthesis, and emits one structured verdict per asset: ACCUMULATING / DISTRIBUTING / NEUTRAL with a conviction level and confirmation count. Smart money is defined operationally as informed capital — what informed players DO (disclosed flows) and what informed money PRICES (market-implied signals) — never what they say. Use when asked \"is smart money buying X\", \"what are insiders doing in TICKER\", \"what is Congress trading\", \"follow the smart money\", \"13F plus insider plus options read on X\", \"accumulation or distribution signal\", \"dark pool activity in SPY\", \"unusual options flow\", \"smart money vs dumb money divergence\". Educational, not advice; a lens, not gospel."
license: MIT
compatibility: opencode
metadata:
  audience: equity-and-macro-allocators
  domain: smart-money-flow-analysis
  role: smart-money-synthesis-conductor
  source: "Multi-source smart-money synthesis — disclosed flows (SEC EDGAR, House/Senate disclosures) + market-implied positioning (CFTC COT, options flow, dark pools, prediction markets) + Wyckoff structure (distilled 2026-06)"
---

# Analyst: Smart Money (disclosed flows + market-implied → synthesized verdict)

This skill is the **conductor lens** of the smart-money family. It does **not** fetch raw data. It **routes** to the eight specialist spoke skills, **collects** each spoke's per-signal verdict, and **synthesizes** one actionable read per asset. The synthesis logic is explicit: signals are reliability-weighted, cross-class confirmation is required, and when signals conflict the default is NEUTRAL rather than a forced call.

## The unifying worldview (everything connects to this)

**Smart money is what informed players DO, not what they say.** The worldview splits into two independent windows onto informed capital:

**Disclosed flows** follow real money through regulatory filings — these are binding, legally reported transactions with known lags. Form 4 insider buys (2-day lag) are the fastest and highest-conviction real-money signal in public markets; 13F institutional clustering (45-day lag) reveals the long-only consensus of the largest allocators; 13D/13G activist filings (near-real-time) reveal concentrated positions with explicit change-of-control intent; congressional PTR filings (30–45-day lag) reveal elected officials' trades but carry contested alpha post-STOCK Act.

**Market-implied signals** reveal what informed money *prices* through positioning and order flow — but these are **risk-neutral probability estimates**, not real-world odds or directional bets. COT commercial positioning in commodities reflects the hedging behavior of the best-informed industry participants; dark-pool DIX (counterintuitively: high DIX = institutional buying, not selling, because market makers short to hedge institutional buys); single-name options sweeps reveal urgency-driven directional bets; prediction-market event odds embed the market's consensus probability on specific dated catalysts.

The unifying discipline is **cross-class confirmation**: five options prints agreeing = ONE signal from ONE class, not five confirmations. A Form 4 cluster buy plus 13F accumulation plus COT extreme = THREE independent mechanisms pointing the same direction — that is real confirmation. **Hedge-as-signal is the dominant failure mode**: a 13F put, a block print, a market-maker short, or a put sweep may be one leg of a hedge whose offsetting position is invisible. Always ask: *what position can't I see?*

## Core mental models (the load-bearing ones)

1. **Real-money / low-lag hierarchy.** The reliability of a signal scales with (a) whether it represents real capital at risk and (b) how close in time it is to the observation. Form 4 cluster buys are the fastest real-money feed (2-day lag). 13D filings are near-real-time for large activist stakes. 13F is 45-day lagged long-only. PTR is 30–45 days lagged and alpha is contested. → `references/01-disclosed-flows.md`

2. **COT commercials = the smart side in commodities.** CFTC Commitments of Traders: commercials hedge physical exposure and are informed about supply/demand; normalize the net position 0–100 over a 3-year lookback (Stephen Briese's method); readings at extremes (>90 or <10) are the contrarian signal, not the trend. COT does **not** translate cleanly to equity futures, where commercials are often index-rebalancers. → `references/02-market-implied.md`

3. **DIX is a dark-pool accumulation signal, not a selling signal.** High DIX means market makers are shorting to hedge large institutional buy flow — **bullish** for equities, counterintuitively. It is an index-level signal only (SqueezeMetrics data product). → `references/02-market-implied.md`

4. **Options flow: aggregate ratio > single prints.** The Pan-Poteshman (2006) finding is that the **aggregate put/call volume ratio** is a more reliable edge than individual unusual prints. Single sweeps are real-time but low signal-to-noise; classify them as urgency (sweep) vs. hedge-likely (block) before reading direction. → `references/02-market-implied.md`

5. **Wyckoff structure confirms after the fact, not before.** The Composite Operator is a useful mental model for reading price-volume sequences in a base (Accumulation phases A→E) or a top (Distribution phases A→E). The spring and upthrust are the key events. But Wyckoff is discretionary and interpretive — it belongs in the synthesis only as confirmatory context, never as a primary trigger. → `references/03-wyckoff-accumulation-distribution.md`

6. **Prediction markets are risk-neutral odds.** A Polymarket contract at 70% does **not** mean there is a 70% real-world probability of the event — it is a risk-neutral price that embeds a volatility risk premium. Haircut all prediction-market readings before treating them as base-case probabilities. → `references/02-market-implied.md`

7. **Confirmation across mechanisms beats depth in one class.** The synthesis rule is strict: independent signal *classes* (disclosed vs. implied) confirming each other is worth more than multiple feeds from the same class. A 13F cluster buy and a Form 4 cluster buy are two classes; five options sweep prints are one class. → `references/04-synthesis-and-failure-modes.md`

## How to apply the lens (decision procedure)

1. **Identify the asset class and question type.** Determine whether the question concerns a US-listed equity (all 8 spokes potentially relevant), a commodity (COT is the primary market-implied spoke), or a macro event (PTR and Polymarket most relevant). Spoke relevance varies by asset class — do not force an irrelevant spoke into the synthesis.

2. **Route to each relevant spoke and collect per-signal verdicts.** For a US equity, the full spoke sequence is: `analyse-smartmoney-form4` → `analyse-smartmoney-13f` → `analyse-smartmoney-13d` → `analyse-smartmoney-ptr` → `analyse-smartmoney-positioning` → `analyse-smartmoney-options` → `analyse-smartmoney-darkpool` → `analyse-smartmoney-polymarket`. Each spoke returns one verdict: **ACC** (accumulating / bullish) / **DIST** (distributing / bearish) / **NEUTRAL** / **UNAVAIL** (data not available or not applicable).

3. **Apply reliability weighting.** Weight verdicts in descending reliability order: Form 4 cluster buys (real money, 2-day lag) > 13F/13D institutional clustering (real money, 45-day / near-real-time) > COT extremes in commodities (3-day lag, best-informed hedgers) > DIX/dark-pool tilt (delayed, index-level only) > Wyckoff structure (discretionary, after-the-fact) > options flow (real-time but low signal-to-noise) > congressional PTR (45-day lag, alpha contested post-STOCK Act). A high-reliability ACC verdict outweighs two low-reliability DIST verdicts in the synthesis.

4. **Require cross-class confirmation.** Count how many **independent signal classes** agree — disclosed flows (Form 4 + 13F + 13D + PTR as one class) vs. market-implied (positioning + options + dark pool + polymarket as one class). Require at least two independent classes pointing the same direction before emitting ACC or DIST with MED or HIGH conviction. One class agreeing → LOW conviction. Zero classes in agreement or active conflict → NEUTRAL.

5. **Check for the hedge-as-signal failure mode before finalizing.** For every market-implied signal reading ACC or DIST, ask: *could this be one leg of a hedge whose offsetting position I cannot see?* A large put position in a 13F may be a protective put against a long equity book. A block on the options tape may be a market maker hedging a client's opposite position. If the hedge interpretation is plausible, downgrade conviction one notch.

6. **Emit the structured verdict.** Follow the output contract below exactly. State the invalidation condition — the specific signal flip that would reverse the verdict. Always include the NOTE line.

## Routing table

| Question is about… | Load / Route to |
|---|---|
| SEC Form 4 insider buys and sells, insider cluster buys, CEO/CFO transactions, opportunistic vs. routine insiders | `analyse-smartmoney-form4` |
| 13F institutional holdings, quarterly institutional positioning, sector/stock accumulation by large funds | `analyse-smartmoney-13f` |
| 13D / 13G activist filings, concentrated activist stakes, Schedule 13 near-real-time large-holder changes | `analyse-smartmoney-13d` |
| Congressional STOCK Act PTR filings, senator/representative stock trades, political insider trading | `analyse-smartmoney-ptr` |
| COT positioning, futures net positioning, funding rates, open interest, basis, options skew, IV, gamma, max-pain | `analyse-smartmoney-positioning` |
| Single-name unusual options flow, sweeps vs. blocks, put/call ratio, unusual volume/OI ratio | `analyse-smartmoney-options` |
| Dark pool prints, DIX dark-pool short volume ratio, block trades, off-exchange accumulation | `analyse-smartmoney-darkpool` |
| Prediction market event odds, Polymarket contract prices, risk-neutral event probabilities | `analyse-smartmoney-polymarket` |
| Wyckoff structure, accumulation/distribution phases, Composite Operator, VSA, spring / upthrust patterns | `references/03-wyckoff-accumulation-distribution.md` |
| Disclosed flows methodology, what 13F / 13D / Form 4 / PTR contain, official data sources, lags | `references/01-disclosed-flows.md` |
| Market-implied methodology, COT interpretation, DIX mechanics, options aggregate signal, prediction-market haircut | `references/02-market-implied.md` |
| Reliability ranking, confirmation logic, failure modes, conflict resolution, synthesis rules | `references/04-synthesis-and-failure-modes.md` |
| Book sources, academic papers, verified reading list, honesty flags on weak figures | `references/book-index.md` |

## Output contract

Every call to this skill must produce the following structured block, verbatim in structure:

```
SMART-MONEY READ: <TICKER>  (as-of <date>)
────────────────────────────────────────────────────────────
DISCLOSED FLOWS                        MARKET-IMPLIED
  Form 4  [ACC/DIST/NEUTRAL/UNAVAIL]    Positioning [ACC/DIST/NEUTRAL/UNAVAIL]
  13F     [ACC/DIST/NEUTRAL/UNAVAIL]    Options     [ACC/DIST/NEUTRAL/UNAVAIL]
  13D     [ACC/DIST/NEUTRAL/UNAVAIL]    Dark pool   [ACC/DIST/NEUTRAL/UNAVAIL]
  PTR     [ACC/DIST/NEUTRAL/UNAVAIL]    Polymarket  [ACC/DIST/NEUTRAL/UNAVAIL]
────────────────────────────────────────────────────────────
VERDICT:      [ACCUMULATING / DISTRIBUTING / NEUTRAL]
CONVICTION:   [HIGH / MED / LOW]
CONFIRMATION: [N independent signal classes agreeing — e.g., "2 of 2: disclosed + implied both ACC"]
INVALIDATION: [specific signal flip that changes the verdict — e.g., "Form 4 cluster sell or 13F net reduction >20% flips to DIST"]
NOTE: Educational only. Lag / crowding / hedge-as-signal caveats apply. Re-pull spoke data before acting.
```

**Conviction rules:** HIGH = ≥3 signal classes aligned including at least one high-reliability spoke; MED = 2 classes aligned; LOW = 1 class aligned or primary signals conflict; NEUTRAL = no directional signal or active conflict.

## Example

<example>
User: "What is the smart-money read on NVDA?"

<thinking>
NVDA is a large-cap US equity — all eight spokes are potentially relevant. Route each spoke, collect verdicts, then synthesize.
</thinking>

Route through all eight spokes and collect their verdicts (illustrative readings — re-pull all live data before acting):

- **Form 4** (`analyse-smartmoney-form4`): Three independent director/officer purchases clustered in the past 30 days, $2M–$8M each, open-market buys. → **ACC** (HIGH reliability: cluster buys, real money, 2-day lag)
- **13F** (`analyse-smartmoney-13f`): Latest 13F filings (45-day lag) show net institutional accumulation — 14 large funds increased positions, 6 reduced. Sector rotation into AI semis visible across multiple filers. → **ACC** (HIGH reliability: real money, but 45d lag means this may describe a prior quarter)
- **13D** (`analyse-smartmoney-13d`): No Schedule 13D/13G activist filing for NVDA (market-cap too large for most activists). → **UNAVAIL**
- **PTR** (`analyse-smartmoney-ptr`): No recent congressional PTR disclosures for NVDA in the past 60 days. → **UNAVAIL**
- **Positioning** (`analyse-smartmoney-positioning`): NVDA options skew slightly call-heavy; 30-day IV relatively compressed; gamma neutral near current price; no COT relevance (equity, not commodity). → **NEUTRAL**
- **Options** (`analyse-smartmoney-options`): Two large call sweeps in the past week (upside strikes, aggressive fills), but also a large protective put block — block is likely a hedge against the long. Net: one clean directional sweep vs. one hedge-likely block. → **NEUTRAL** (hedge-as-signal flag raised on the put block)
- **Dark pool** (`analyse-smartmoney-darkpool`): DIX elevated above 45% for three consecutive days — historically bullish at index level. NVDA-specific block prints above average. → **ACC** (MED reliability: index-level indicator, NVDA block prints are directional color only)
- **Polymarket** (`analyse-smartmoney-polymarket`): No active NVDA-specific contract; macro contracts (Fed pause odds at 74%) marginally supportive of risk assets. → **NEUTRAL**

**Synthesis:**
- Disclosed class: Form 4 ACC + 13F ACC = **disclosed flows pointing ACC** (two high-reliability real-money signals)
- Implied class: Dark pool ACC, Positioning NEUTRAL, Options NEUTRAL (hedge flag raised) = **implied signals mixed, lean ACC**
- Cross-class: Both classes lean ACC — confirmed across independent mechanisms
- Hedge-as-signal check: Put block on options tape downgraded to NEUTRAL; does not contaminate the Form 4 / 13F read

```
SMART-MONEY READ: NVDA  (as-of 2026-06-26)
────────────────────────────────────────────────────────────
DISCLOSED FLOWS                        MARKET-IMPLIED
  Form 4  [ACC]                          Positioning [NEUTRAL]
  13F     [ACC]                          Options     [NEUTRAL]
  13D     [UNAVAIL]                      Dark pool   [ACC]
  PTR     [UNAVAIL]                      Polymarket  [NEUTRAL]
────────────────────────────────────────────────────────────
VERDICT:      ACCUMULATING
CONVICTION:   MED
CONFIRMATION: 2 of 2 available classes — disclosed (Form 4 + 13F) and implied (dark pool) both ACC; options neutral after hedge-as-signal flag
INVALIDATION: Form 4 cluster sell by same officers, or 13F net reduction >20% next filing cycle, flips verdict to DIST
NOTE: Educational only. Lag / crowding / hedge-as-signal caveats apply. 13F data is 45 days stale. Re-pull spoke data before acting.
```
</example>

## Honesty rules (non-negotiable)

- **Output verdicts with explicit confidence, never certainty.** ACCUMULATING / DISTRIBUTING / NEUTRAL are analytical weights, not buy/sell instructions. Every verdict degrades as data ages.

- **Six failure modes — always check before finalizing:**
  1. **Lag.** 13F and PTR describe portfolios that may have been partially or fully unwound since the filing date. A 13F showing accumulation 45 days ago is a historical fact, not a current position.
  2. **Crowding.** Public guru trackers and congressional disclosure aggregators are widely arbitraged. Cloning a famous 13F or a senator's trade is consensus at best — the edge has likely been front-run by the time a retail-accessible signal fires.
  3. **Hedge-as-signal — the dominant failure mode.** A 13F put position, a large block on the tape, a market-maker short, or a put sweep may be one leg of a hedge whose offsetting position is invisible in the data. Always ask: *what position can't I see?* Never read a single leg as a clean directional bet.
  4. **False confidence from correlated signals.** Five options sweep prints from the same OPRA tape on the same day are ONE signal from ONE class, not five independent confirmations. Only count independent mechanisms.
  5. **Survivorship in vendor marketing.** Options flow vendors, dark-pool data services, and 13F clone products all market on their best backtested examples. Demand out-of-sample evidence. Najarian's options flow book is promotional with weak false-positive disclosure. The "retail 8–11% per insider cluster buy" figure is UNSOURCED — do not assert it.
  6. **Regime-dependence.** Congressional alpha was documented pre-STOCK Act (Ziobrowski +6–12%/yr pre-2008), but post-STOCK Act studies (Eggers-Hainmueller 2013, Chen-Sacerdote NBER 2024) find congressional trades resemble uninformed retail — edge now concentrated in leadership only, if at all. COT works in commodities; the commercial-as-smart-money logic does not apply cleanly to equity-index futures.

- **Ground load-bearing numbers in `references/book-index.md`.** Do not cite a figure without tracing it to a specific source. If a source is flagged CONTESTED or FLAG in the book index, say so explicitly in the output.

- **On conflict between signal classes, default to NEUTRAL.** Do not force a verdict by cherry-picking the highest-reliability signal that supports a directional read. A genuine conflict between disclosed (ACC) and implied (DIST) from different mechanisms is information — it means the smart-money signal is ambiguous, and NEUTRAL is the correct output.

- **Educational only.** This skill produces analytical outputs for research and learning. It is not financial advice. No verdict from this skill constitutes a recommendation to buy, sell, or hold any security.

## Done when

The analysis (1) routes to every **relevant spoke** for the asset class and collects a verdict from each, (2) applies the **reliability weighting** (Form 4 cluster buys > 13F/13D > COT extremes > DIX > Wyckoff > options flow > PTR), (3) requires **cross-class confirmation** across at least two independent signal mechanisms before emitting ACC or DIST, (4) checks the **hedge-as-signal failure mode** on every market-implied ACC or DIST verdict, (5) emits the **structured output contract** verbatim, and (6) states a clear **invalidation condition** and the educational NOTE.
