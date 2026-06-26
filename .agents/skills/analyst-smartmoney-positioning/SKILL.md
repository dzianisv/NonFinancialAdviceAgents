---
name: analyst-smartmoney-positioning
description: Use when a market read needs to know how traders are POSITIONED and what derivatives are PRICING — futures funding/basis/open-interest, options put/call, skew, implied vol, max pain, dealer gamma, COT, VIX term structure, options-implied probability of a move. The positioning/market-implied seat for a quorum or forecast. Works for CRYPTO (Coinglass/Deribit/CME) and EQUITIES/indices (CBOE/VIX/COT/OCC). Use for "how is the market positioned", "what are options pricing", "funding/skew/gamma read", "is leverage crowded", "options-implied move", "max pain". Educational, not advice; positioning is necessary-not-sufficient, and options odds are risk-neutral, not real-world.
license: MIT
compatibility: opencode
metadata:
  audience: forecasters-and-traders-reading-market-positioning
  domain: derivatives-and-options-positioning
  role: positioning-lens-and-data-recipe
  source: "futures/options positioning practice; data recipes verified vs Deribit/Coinglass/CBOE 2026-06"
---

# Analyst: Derivatives Positioning (how the market is positioned + what it prices)

This skill is part of the `analyst-smartmoney` family; the parent `analyst-smartmoney` skill synthesizes its output with the other spokes.

Read the market *beneath spot*: where leverage sits, what options price, who is offside. Two halves —
**futures/flow** and **options/implied** — read **together** (funding without skew is half a picture).
This is the **positioning / market-implied seat**. Cross-asset: same lens, different venues for crypto vs
equities.

**Two caveats up front (the blind spot):** positioning is **necessary-not-sufficient** — crowded can stay
crowded for weeks. And options-implied probabilities are **risk-neutral**, inflated by the vol risk
premium — they are *not* real-world odds. Never quote an options-implied prob as if it were a true
probability; state both.

## When to use vs not

**Use when** the question is about **positioning, leverage, or what derivatives price** — direction
conviction, squeeze/cascade risk, an implied move around a catalyst, a max-pain pin into expiry.

**Do NOT use when** there's no liquid derivatives market (most alts/small-caps — say "no positioning
signal"), or the question is pure spot fundamentals/valuation.

## Signal cheat-sheet (the judgment this lens brings)

**Futures / flow**
| Signal | Read |
|---|---|
| Funding >0 persistent + OI rising + price flat | Crowded longs → **squeeze-DOWN** risk |
| Funding deeply <0 + OI flushed + spot bid returns | Capitulation/exhaustion → **contrarian up** |
| Basis: wide contango | Leverage/carry demand (late-bull froth) |
| Basis: backwardation (futures < spot) | **Stress/fear** — rare, often marks bottoms |
| OI↑+price↑ / OI↑+price↓ / OI↓ | New longs (trend) / new shorts / deleveraging |
| Equity COT: large specs extreme long, small traders euphoric | Crowded — fade; commercials (hedgers) = smart money |

**Options / implied**
| Signal | Read |
|---|---|
| Put/call high + 25Δ put skew steep + IV rising | Fear/hedging priced; **extreme = contrarian bottom** |
| Call skew + low IV / IV-rank low | Complacency/chase; topping fuel; convexity cheap |
| Max pain strike | Expiry **magnet** — price pulled there if dealers long gamma |
| Dealer gamma: long (GEX+) / short (GEX−) | Vol-**dampening pin** / vol-**amplifying** trends & cascades |
| VIX (or DVOL) term: contango / backwardation | Complacency / acute stress |
| ATM straddle price | Market's priced **1-SD move** to expiry — the implied range |

## Data recipe

**Crypto**
- **Coinglass** `https://www.coinglass.com` — aggregated funding, OI, liquidation heatmap, long/short ratio (free, start here; may 403 from sandbox — fall through to next).
- **Kraken Futures** `https://futures.kraken.com/derivatives/api/v3/tickers` — no key, 200 OK from sandbox; returns `fundingRate`, `lastTime`, `openInterest` per perp (`PI_XBTUSD`, `PI_ETHUSD`, `PI_SOLUSD`). **Primary fallback for funding when Binance/Bybit blocked.**
- **Hyperliquid** `POST https://api.hyperliquid.xyz/info` body `{"type":"metaAndAssetCtxs"}` — no key, 200 OK; `ctx.funding` and `ctx.openInterest` for all listed assets including SOL perps. Second primary fallback.
- **Deribit API** `https://www.deribit.com/api/v2` — options + DVOL + **25Δ skew**: `/public/get_book_summary_by_currency?currency=BTC&kind=option` (get all option summaries, find near-term 25Δ puts vs calls for skew); `/public/get_volatility_index_data?currency=BTC` for DVOL timeseries; `/public/get_index_price?index_name=btc_usd`. Dominant BTC/ETH options venue, all no-key.
- **CFTC Disaggregated COT (Socrata)** `https://publicreporting.cftc.gov/resource/gpe5-46if.json?$where=market_and_exchange_names%20LIKE%20'%25BITCOIN%25'&$limit=5&$order=report_date_as_yyyy_mm_dd%20DESC` — no key, returns leveraged-fund + asset-manager positions in BTC futures. **Institutional sentiment anchor; updated weekly (Fri ~15:30 ET).**
- **OKX** `https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USD-SWAP` — fallback for funding; may 451 geo-block.
- **Binance/Bybit** `fapi` — **BLOCKED** (HTTP 451 / 403 from sandbox); do not attempt.
- **CME** BTC/ETH futures for institutional basis (via Yahoo Finance `BTC=F` or CME data).

**Equities / indices**
- **CBOE** — equity & index put/call ratios, **VIX**, **SKEW** index; **VIX term** via vixcentral.
- **CME COT report** — weekly (Fri ~15:30 ET) futures positioning: commercials vs large specs vs small.
- **OCC** — total options volume. **Options-implied move / IV rank** — barchart, market-chameleon.
- Single stock around earnings: the **options-implied move** (ATM straddle) = the priced event range.

## The forecast-grade move (don't stop at "walls")

Convert options into a **distribution**, not just OI levels:
- **Implied move** = ATM straddle / spot → the 1-SD range by expiry.
- **Risk-neutral probability** from the strike's delta/price (e.g. 70k-call delta ≈ P(touch), roughly).
  Quote it as **risk-neutral** and haircut for the vol risk premium — it overstates tail odds.
- This is the **continuous** complement to `analyst-smartmoney-polymarket` (discrete event bets). Use both:
  prediction markets for "will the Fed cut", options for "where does price land by expiry".

## Output shape

```
Positioning:  funding <x> | OI <trend> | basis <contango/backw> | (equity: COT <lean>)
Options:      put/call <x> | 25Δ skew <dir> | IV/IV-rank <x> | max pain <strike> | gamma <long/short>
Implied:      1-SD move ±<x>% to <expiry>; risk-neutral P(<level>) ≈ <y>% (NOT real-world)
Read:         crowded-long / capitulation / pinned / complacent — and the directional lean
Triggers:     <level/funding flip/gamma flip that changes the read>
Blind spot:   positioning ≠ destiny; risk-neutral ≠ real odds
```

## Common mistakes

| Mistake | Fix |
|---|---|
| Quote options-implied prob as real probability | Label risk-neutral; haircut the vol risk premium |
| Read funding without skew (or vice versa) | Read both halves — they confirm or contradict |
| Stop at OI "walls", never compute the implied move | Convert straddle → 1-SD range; that's the forecast |
| Default to crypto gauges on a stock (or vice versa) | Equities = COT/VIX/SKEW/GEX; crypto = funding/DVOL |
| Skip max pain / gamma into expiry | Pin & amplification are the strongest near-expiry signals |
| Treat crowded positioning as an immediate signal | Necessary-not-sufficient; needs a trigger to fire |

## Fit

The **positioning seat** in `multi-lens-quorum` and `superforecasting`. **Feeds the
reflexivity seat** (supplies the liquidation/crowding data its cascades run on) — distinct from it (this
= gauge, reflexivity = theory). Complements `analyst-smartmoney-polymarket` (discrete) with the continuous
options-implied distribution. Don't double-count it against reflexivity in the same quorum.

> Educational, not advice. Positioning is necessary-not-sufficient; options odds are risk-neutral. Re-pull
> before acting — funding, gamma, and OI shift fast.
