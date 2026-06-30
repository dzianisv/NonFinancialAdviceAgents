---
name: analyse-onchain
description: "The repo's expert lens for analyzing the crypto market and deciding whether to buy BTC (or an alt) now — a four-pillar methodology, not a single-author lens. Fuses (1) global liquidity (Michael Howell, Capital Wars 2020), (2) on-chain valuation (MVRV-Z, realized price, NUPL, Puell, 200-week MA), (3) sentiment/cycle (Fear & Greed, four-phase cycle), and (4) execution via valuation-tilted DCA + vol-target sizing, plus BTC-as-hurdle token selection for alts. Encodes the honest core finding: pure TA timing does not beat DCA after costs; the defensible best practice is valuation-and-sentiment-tilted DCA governed by the liquidity cycle. Use when the user asks \"should I buy bitcoin now\", \"is BTC cheap or expensive\", \"analyze the crypto market\", \"MVRV / on-chain valuation\", \"global liquidity and bitcoin\", \"crypto DCA strategy\", \"is this altcoin worth it\", \"BTC-as-hurdle\", or \"when to deploy into crypto\". Educational, not advice; a lens, not gospel."
license: MIT
compatibility: opencode
metadata:
  audience: crypto-allocators-and-treasury-managers
  domain: crypto-market-analysis
  role: crypto-analysis-and-deployment-lens
  source: "Howell Capital Wars (2020) + on-chain/liquidity practice (distilled 2026-06)"
---

# Analyst: The Crypto-Market Lens (liquidity → valuation → sentiment → execution)

Apply a **four-pillar lens-stack** to *how the crypto market is read and how capital is actually deployed*.
This skill is the **synthesis + router**; detail lives in `references/`, grounded in **Michael J. Howell,
*Capital Wars: The Rise of Global Liquidity* (Palgrave Macmillan, 2020)** for the liquidity pillar and in
on-chain/execution practice for the rest. It is the **analysis brain** for the repo's live ~$177k
conservative crypto treasury (`crypto/`), and the rigorous answer to the discretionary
`analyse-technical` lens. Load the relevant reference before any load-bearing claim or number.

## The unifying worldview (everything connects to this)

Crypto price is set, in order, by **the tide, the level, the mood, and the discipline**. The **tide is
global liquidity** — Howell's insight that "it is the capacity of capital… more important than the cost of
capital," and that liquidity *leads* risk assets by months (FX/bonds ~3–6mo, equities ~6–12mo). BTC is the
highest-beta liquidity sponge, so liquidity is the **governor** over every deploy decision. The **level is
on-chain valuation** — MVRV-Z, realized price, NUPL place price within its own cost-basis history (zone, not
day-timing). The **mood is sentiment** — Fear & Greed as a *contrarian modulator* (extreme fear =
accumulate). The **discipline is execution** — and the honest finding is blunt: **pure TA timing does not
beat dollar-cost-averaging after costs; the defensible best practice is valuation-and-sentiment-tilted DCA,
governed by the liquidity cycle, sized by volatility.** When the pillars conflict (on-chain cheap *but*
liquidity rolling over) the resolution is **steady tilted DCA over tranches, never conviction lump-sum**.
For alts, the worldview is harsher still: price everything **in BTC** and demand it clear the **BTC-as-hurdle**.

## Core mental models (the load-bearing ones)

1. **Liquidity is the tide and it leads.** Capacity of capital > cost of capital; markets are refinancing
   mechanisms; GLI leads equities ~6–12mo. The liquidity governor sits above everything. → `references/01-global-liquidity-and-btc.md`
2. **Four-phase liquidity cycle.** Rebound → Calm → Speculation → Turbulence; risk assets peak in Turbulence,
   bottom in Calm. Maps onto the crypto cycle. → `references/01-global-liquidity-and-btc.md`
3. **On-chain valuation = zone, not clock.** MVRV-Z >7 tops / <0 capitulation; realized price = aggregate
   cost-basis floor; NUPL >0.75 euphoria / <0; Puell = miner stress. → `references/02-onchain-valuation.md`
4. **Stock-to-Flow is discredited.** Projected ~$500k vs ~$66k actual; auto-correlation flaw. Citing it is a
   **red flag**, not a signal. → `references/02-onchain-valuation.md`
5. **Sentiment is a contrarian modulator.** Fear & Greed: extreme fear = accumulate, extreme greed = trim
   tilt. Maps to Howell's phases. → `references/03-sentiment-and-market-cycle.md`
6. **DCA beats lump-sum risk-adjusted; tilt it.** Buy more when MVRV-Z low / F&G extreme-fear; deploy measured
   when liquidity rolling over. Lump only wins with perfect bottom-timing nobody achieves. → `references/04-execution-dca-and-sizing.md`
7. **Vol-target the size; trend only caps drawdown.** Size from market volatility (borrow
   `analyse-systematic-trading`); optional 200d-MA risk-cap is drawdown control, not alpha. → `references/04-execution-dca-and-sizing.md`
8. **BTC-as-hurdle for every alt.** Price in BTC; 6-point value-accrual filter; base rate brutal (0 of 20 top
   alts beat BTC 2017→2021). → `references/05-token-selection-btc-as-hurdle.md`
9. **TA day-timing doesn't beat DCA after costs.** Most active traders lose net; the analytical tension
   resolves to *tilted DCA, not conviction lump*; every metric decays — re-pull live. → `references/06-risks-and-honest-assessment.md`

## How to apply the lens (decision procedure — the lens-stack)

1. **Liquidity governor (the tide).** Read the GLI / its proxies (CB balance sheets, USD, cross-border).
   Rising & below-trend (Rebound/Calm) → green light to deploy faster. High & falling (Turbulence) → throttle
   to defensive tranches and raise cash. Remember the lead is *months*, so act ahead of the economy. (`01`)
   **REQUIRED INPUTS for liquidity pillar:**
   - `feed-fomc` → Fed tone (HAWKISH/DOVISH), actual statement language, next meeting date.
     A hawkish Fed = liquidity headwind; dovish = tailwind. Read the primary source, not just FedWatch odds.
   - `analyse-smartmoney-polymarket` → CME FedWatch rate-path probabilities (market-implied, anchors your base case).
   - CPI/PCE: fetch latest from https://www.bls.gov/cpi/ (headline + core). Above-trend inflation →
     Fed stays hawkish → liquidity headwind. Confirm the number before using it.
2. **On-chain valuation (the level).** Place price in its cost-basis history: MVRV-Z, realized price, NUPL,
   Puell, 200-week MA. Output a **zone** (cheap / fair / rich), never a precise top/bottom call. (`02`)
3. **Sentiment (the contrarian modulator).** Overlay Fear & Greed and the four-phase cycle. Extreme fear at a
   cheap on-chain zone = widen the buy tilt; extreme greed at a rich zone = shrink it. (`03`) For a real-time
   positioning/catalyst read, pull **`analyse-smartmoney-positioning`** (funding/OI, options skew/max-pain/
   gamma) and **`analyse-smartmoney-polymarket`** (dated events) — harder sentiment signal than Fear & Greed alone.
4. **Execution (the discipline).** Translate the three reads into a **valuation-and-sentiment-tilted DCA
   schedule over tranches**, sized by a vol target (Half-Kelly via `analyse-systematic-trading`), optionally
   with a 200d-MA risk-cap for drawdown. Never lump-sum on conviction. (`04`)
5. **If it's an alt, route to BTC-as-hurdle.** Price it in BTC and run the 6-point filter before any tilt at
   all; if it can't beat BTC in BTC-denominated trend, default to BTC. (`05`)
6. **Honesty pass + re-pull.** State the pillar tensions plainly, flag discredited metrics (S2F), and note
   every reading decays — confirm live data before acting. (`06`)

## Routing table

| Question is about… | Load |
|---|---|
| Global liquidity, the tide, GLI, Howell's phases, lead-lag, "is liquidity rolling over", USD as tightening | `references/01-global-liquidity-and-btc.md` |
| On-chain valuation, MVRV-Z, realized price, NUPL, Puell, 200-week MA, Pi Cycle, Stock-to-Flow red flag | `references/02-onchain-valuation.md` |
| Sentiment, Fear & Greed, market-cycle / rainbow charts, the four-phase cycle mapping | `references/03-sentiment-and-market-cycle.md` |
| DCA vs lump-sum, valuation-tilted DCA, vol-target sizing, 200d trend cap, "how should I deploy" | `references/04-execution-dca-and-sizing.md` |
| Alts, "is this altcoin worth it", BTC-as-hurdle, value-accrual filter, alt base rates | `references/05-token-selection-btc-as-hurdle.md` |
| Risks, why TA day-timing fails, DeFi failure modes, custody, the on-chain-vs-liquidity tension | `references/06-risks-and-honest-assessment.md` |
| Provenance, the Capital Wars link, live-data tools, what's distilled vs not, later-Howell scope | `references/book-index.md` |

## Example

<example>
User: "Should we buy BTC now?"

Lens response: "Run the lens-stack (load `01`, `02`, `03`, `04`):
(1) **Liquidity governor (the tide)** — say the GLI has just rolled from above-trend to *high-and-falling*:
that's the **Turbulence** phase, and since liquidity leads equities/BTC by ~6–12 months, the tide is turning
*against* us even if price is still firm. Governor verdict: **throttle, don't gun it.**
(2) **On-chain (the level)** — but suppose MVRV-Z is ~1.5 and price is barely above realized price with NUPL
near 0.3: on-chain says **cheap-to-fair**, nowhere near the >7 / >0.75 euphoria that marks tops. So the level
says accumulate.
(3) **Sentiment (the modulator)** — Fear & Greed at 'extreme fear' (say 18) *confirms* the cheap read and
argues to **widen** the buy tilt contrarily.
(4) **The tension is the whole point**: on-chain-cheap + extreme-fear says buy, but liquidity-rolling-over
says a deeper flush can still come (cheap can get cheaper while the tide ebbs). The defensible resolution is
**NOT a lump-sum** — it's a **valuation-and-sentiment-tilted DCA across tranches**: deploy a measured base
schedule now (the cheap zone earns a larger-than-neutral tilt), but keep dry powder and let the liquidity
governor cap the pace until the tide stops falling (watch for the GLI re-crossing into Rebound). Size each
tranche by a vol target (Half-Kelly via `analyse-systematic-trading`), and optionally gate with the 200d MA
for drawdown control — knowing that's risk-management, not alpha. And the honest baseline: this tilted-DCA
beats trying to TA-time the exact bottom, which doesn't survive costs. Re-pull every reading before acting —
they all decay."
</example>

## Honesty rules (non-negotiable)

- **It's a lens-stack, not a crystal ball.** Output **zones and tilts**, never precise tops/bottoms or "buy
  today" certainty. Present liquidity claims as "Howell's framework says…".
- **Pure TA timing does not beat DCA after costs.** The defensible best practice is valuation-and-sentiment-
  tilted DCA governed by liquidity. Don't dress up day-timing as edge (the repo house finding: hold/mid-risk
  beats day-trading after costs).
- **Flag discredited metrics.** Stock-to-Flow is broken (auto-correlation; ~$500k projection vs ~$66k actual);
  citing it is a red flag, not support.
- **Scope-flag later-Howell.** *Capital Wars* (2020) gives crises "every 8–10 years" + month-level leads and
  mentions crypto only as a "distrust" signal — it does **not** state a clean 5–6yr cycle or a Bitcoin
  liquidity-beta. Those are later Howell (CrossBorder Capital); cite as such, not from the book.
- **Ground load-bearing claims/numbers** in a specific reference (via `references/book-index.md`); for sizing
  defer to `analyse-systematic-trading`, for debasement/BTC-as-hurdle to `investor-lyn-alden`, for liquidity
  timing to `investor-stanley-druckenmiller`, for downside to `risk-management`.
- **Every metric decays — re-pull live readings** (LookIntoBitcoin, Glassnode, CryptoQuant, CoinGlass,
  Alternative.me) before any deploy decision.

## Done when

The analysis (1) sets the **liquidity governor** first (tide, with the months-long lead), (2) places price in
a **valuation zone** on-chain (not a precise call, no S2F), (3) overlays **sentiment** contrarily, (4) resolves
any pillar tension into a **valuation-and-sentiment-tilted DCA over tranches, vol-target-sized, not lump-sum**,
(5) routes any **alt through BTC-as-hurdle**, and (6) states the tensions honestly and re-pulls live data.
