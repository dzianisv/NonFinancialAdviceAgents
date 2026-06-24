---
name: analysis-macro
description: "Analyst lens for crypto macro fundamentals — global liquidity (Howell GLI), Fed balance sheet, M2 money supply, DXY, interest rates, BTC correlation with equities, halving cycle position, ETF flow regime. Interprets macro tailwinds/headwinds for BTC. Use when asked \"what does macro say about BTC\", \"is global liquidity bullish\", \"Fed impact on crypto\", \"DXY and bitcoin\", \"macro environment for crypto\", \"halving cycle\", \"ETF flows\". Grounded in Howell Capital Wars (2020) — liquidity leads risk assets 6–12 months. Depends on [[crypto-liquidity-data]]. Educational, not advice."
license: MIT
compatibility: opencode
metadata:
  audience: crypto-allocators-and-macro-watchers
  domain: crypto-macro-analysis
  role: macro-tailwind-headwind-lens
  source: "Howell Capital Wars (2020) + ETF flow/halving-cycle practice (distilled 2026-06)"
---

# Analysis: The Crypto-Macro Lens (liquidity → dollar → cycle → ETF flows)

Apply the **macro lens** to interpret global liquidity conditions, the Fed balance sheet, the dollar, and the
halving cycle as *tailwinds or headwinds for BTC*. This is a **reading lens**, not a trade signal. Grounded
in **Michael J. Howell, *Capital Wars: The Rise of Global Liquidity* (Palgrave Macmillan, 2020)** for the
liquidity pillar, and in post-2024 ETF flow data for the institutional demand pillar. Depends on
**[[crypto-liquidity-data]]** for live numbers.

## The unifying worldview

BTC is the **highest-beta global liquidity sponge**. Howell's core insight: *"it is the capacity of capital
— more important than the cost of capital"* — meaning balance sheet expansion, not rate cuts, is what drives
risk assets. **Global liquidity leads equities by 6–12 months** and BTC by a similar or shorter lag. The DXY
is the denominator: a falling dollar inflates all dollar-denominated assets. The halving cycle compresses
supply issuance every ~4 years and historically marks the start of bull phases — but it works *through*
liquidity, not independently. ETF flows (since 2024) are the **dominant marginal demand signal**: institutional
buying via IBIT/FBTC creates a new structural demand floor that prior cycles lacked.

The honest analytical baseline: **macro direction is forecastable in direction, not in magnitude or timing.**
Output posture (TAILWIND / HEADWIND) and dominant risk — never a precise price target.

## Core mental models (the load-bearing ones)

1. **GLI direction is the governor.** Expanding GLI (Rebound/Calm Howell phases) = green light for BTC.
   Contracting (Turbulence/Post-peak) = headwind regardless of on-chain cheapness. The lead is *months*,
   so the GLI reads the environment ahead of price.
2. **Fed net liquidity = WALCL − RRP − TGA.** Rising = liquidity injection into the system; falling = drainage.
   This is more important than the rate *level* — a rate pause with active QT is still a headwind.
3. **DXY: dollar is the denominator.** Falling DXY = tailwind for BTC and commodities. DXY > 105 and rising =
   structural headwind. Watch for DXY trend change as an early macro signal.
4. **US M2 YoY: expansion with ~6mo lag.** M2 acceleration correlates with BTC appreciation approximately
   6 months later (Lyn Alden thesis). M2 contraction = watch for deferred headwind.
5. **Halving cycle position.** Apr 2024 halving = BTC is now ~14 months post-halving; historically peak comes
   12–18 months after halving (Q2–Q3 2025 window). Current position: mid-cycle. The halving reduces miner
   sell pressure but only matters if liquidity supports the move.
6. **ETF net flows (IBIT/FBTC/aggregate): 5-day direction is the institutional demand signal.** Sustained
   outflows = institutional distribution; sustained inflows = demand floor and potential squeeze. This signal
   did not exist before January 2024 — it is the single biggest structural change vs prior cycles.
7. **BTC–S&P correlation in risk-off.** When S&P sells off and DXY spikes simultaneously, BTC behaves like
   a risk asset, not a safe haven. Watch for de-correlation events as a potential macro narrative shift
   (BTC re-rated as digital gold).

## How to apply the lens (decision procedure)

1. **Fetch liquidity data via [[crypto-liquidity-data]].** Pull WALCL, RRP, TGA → compute Fed net liquidity
   direction. Pull GLI proxy or CrossBorder Capital phase if available.
2. **Get halving cycle position.** Apr 14, 2024 = halving date. Compute months elapsed → map to historical
   phase (pre-halving / early post-halving 0–6mo / mid-cycle 6–18mo / late-cycle 18–24mo).
3. **Fetch ETF flows.** WebFetch `farside.co.uk/btc/` or CoinGlass aggregate ETF flow table.
   Compute 5-day net and trailing 30-day net. Classify regime: ACCUMULATION / NEUTRAL / DISTRIBUTION.
4. **Classify Howell cycle phase.** Using GLI direction + rate environment: **Rebound** (liquidity rising from
   trough) / **Calm** (expanding, below-trend) / **Speculation** (above-trend, momentum) / **Turbulence**
   (peak + rolling over). Rebound and Calm = constructive; Speculation = late-but-running; Turbulence = exit.
5. **Score each macro pillar:**
   - GLI / Fed net liquidity: EXPANDING / FLAT / CONTRACTING
   - DXY: FALLING / FLAT / RISING (with level vs 100/105 anchors)
   - M2 YoY: ACCELERATING / FLAT / DECELERATING
   - Halving cycle: EARLY / MID / LATE (months elapsed)
   - ETF regime: ACCUMULATION / NEUTRAL / DISTRIBUTION
6. **Derive macro posture.** Aggregate pillar scores into:
   **STRONG TAILWIND / TAILWIND / NEUTRAL / HEADWIND / STRONG HEADWIND**
7. **State the dominant risk.** Name the single macro factor most threatening the constructive thesis
   (e.g., "Fed restarting QT while RRP refills" or "DXY breakout above 107" or "ETF 30-day outflow streak").

## Routing table

| Question is about… | Action |
|---|---|
| GLI, Howell phases, liquidity leading equities, "is liquidity expanding" | Fetch [[crypto-liquidity-data]], classify Howell phase |
| Fed balance sheet, QT/QE, WALCL, RRP, TGA, "Fed net liquidity" | Fetch WALCL−RRP−TGA via [[crypto-liquidity-data]] |
| DXY, dollar strength, "DXY and BTC", dollar milkshake | Pull DXY level + trend; score vs 100/105 anchors |
| M2 money supply, "is money printing bullish", Lyn Alden debasement thesis | Pull US M2 YoY; note ~6mo lag |
| Halving cycle, "where are we in the cycle", supply issuance | Compute months since Apr 14 2024 halving |
| ETF flows, IBIT, FBTC, institutional demand, "are ETFs buying" | WebFetch farside.co.uk/btc/ or CoinGlass |
| BTC–S&P correlation, risk-off, "is BTC a safe haven" | Note correlation regime; flag de-correlation watch |
| Macro posture synthesis, "what does macro say" | Run full 7-step decision procedure above |

## Output contract

Return a structured block:

```
MACRO PILLARS
─────────────────────────────────────────────
GLI / Fed net liquidity : {EXPANDING|FLAT|CONTRACTING}  (WALCL−RRP−TGA: {value}, asof {date}, source: https://fred.stlouisfed.org/series/WALCL)
DXY                     : {FALLING|FLAT|RISING} @ {level}  (asof {date}, source: https://fred.stlouisfed.org/series/DTWEXBGS)
US M2 YoY               : {ACCELERATING|FLAT|DECELERATING} ({pct}%, asof {date}, source: https://fred.stlouisfed.org/series/M2SL)
Halving cycle           : {N} months post-halving (Apr 2024) → {EARLY|MID|LATE} cycle
ETF net flows (5d)      : {value} → regime: {ACCUMULATION|NEUTRAL|DISTRIBUTION}  (source: https://farside.co.uk/btc/)

SYNTHESIS
─────────────────────────────────────────────
Howell phase            : {Rebound|Calm|Speculation|Turbulence}
Macro posture           : {STRONG TAILWIND|TAILWIND|NEUTRAL|HEADWIND|STRONG HEADWIND}
Dominant risk           : {one-line description of the biggest macro threat}

DISCLAIMER: Macro analysis only. Not investment advice.
```

All metrics must include `asof` date. If a live fetch fails, state `[STALE — manual refresh needed]`.
Do not output buy/sell signals or price targets.

## Citation rule — no URL = not a source

Every external claim (news event, data point, quote, analysis) MUST include ALL THREE:
1. **Full URL** fetched: `https://exact-page-url` (specific article, not homepage or search page)
2. **Date** (ISO): `YYYY-MM-DD` (publication or as-of date)
3. **Verbatim quote**: exact words from the page, copied not paraphrased

Format in output: `[TIER] https://exact-url (YYYY-MM-DD) — "verbatim quote"`

**Never write:**
- Source name alone (`CoinDesk`, `Bloomberg`) — without URL it is hallucination bait
- A quote without its URL
- A URL without a date
- Anything paraphrased from memory without a prior web_fetch call

**If fetch failed:** `[FETCH FAILED: https://...] — not counted toward minimum`
**If < 2 real sources:** output `INSUFFICIENT_DATA — do not guess`

## Done when

The analysis (1) classifies the **Howell liquidity phase** from live data, (2) scores each **macro pillar**
with a direction tag and recency date, (3) classifies the **ETF flow regime** from the latest 5-day net,
(4) states the **halving cycle position** in months, (5) derives a single **macro posture** label, and
(6) names the **dominant risk** threatening the thesis. All metrics sourced from [[crypto-liquidity-data]]
or WebFetch with explicit `asof` dates — no stale or recalled numbers.
