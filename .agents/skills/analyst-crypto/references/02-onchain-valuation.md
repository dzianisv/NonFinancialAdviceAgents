# On-Chain Valuation — Placing Price in Its Own History (the level)
> Source: On-chain analytics practice (Glassnode, LookIntoBitcoin, CryptoQuant); MVRV/realized-cap concepts from Coinmetrics/Murad Mahmudov & David Puell lineage. Distilled 2026-06. These are LIVE-DATA tools, not a book — re-pull before use.

## Core thesis
On-chain valuation answers "**is BTC cheap or expensive relative to its own cost basis and behavior?**" — not by P/E (there are no earnings) but by comparing **market value to the aggregate price holders actually paid** (realized value) and to long-run moving averages. The signal is a **zone** (capitulation / cheap / fair / rich / euphoria), reliable at *cycle extremes* and weak for day-timing. Treat it as **the level** beneath the liquidity tide: it tells you *where in the valuation range* you are, while liquidity tells you *which way the water is moving*.

## Key frameworks / mental models
- **MVRV Z-score** — the most-cited valuation gauge. (Market cap − Realized cap) / σ(market cap). **>7 → historic tops; <0 → capitulation/deep value.** The flagship "cheap vs expensive" zone metric.
- **Realized price / cost-basis floor** — realized cap ÷ supply = the average price every coin last moved at. Price near/below realized price = market trading at/below aggregate cost basis (historically a durable floor).
- **NUPL (Net Unrealized Profit/Loss)** — aggregate paper P/L as a share of market cap. **>0.75 = euphoria/greed (top zone); <0 = capitulation (bottom zone).**
- **Puell Multiple** — daily miner issuance value ÷ 365d average. High = miner over-earning (top stress); low = miner capitulation (bottom zone).
- **200-week MA heatmap** — price vs the 200-week moving average; historically a cycle-floor band when price touches it.
- **Pi Cycle Top** — 111d-MA crossing 2×350d-MA; a **top-only** signal (no symmetric bottom call). Use as a confirmation flag, not a primary gauge.
- **Behavioral on-chain** — long-term-holder (LTH) supply (accumulation vs distribution) and exchange inflows/outflows (coins to exchanges = sell-pressure intent; off exchanges = HODL intent).

## Specific claims, mechanisms & data
- **MVRV-Z extremes** have bracketed every major BTC top (>7) and bottom (<0) to date — but the *exact* threshold drifts cycle-to-cycle as the asset matures (later cycles top at lower MVRV-Z), so read it as a **zone, not a fixed line.**
- **Realized price** has acted as the line that bear-market bottoms wick below only briefly (max-pain / capitulation), which is why it anchors the "deep value" read.
- **Stock-to-Flow (S2F) is DISCREDITED.** It projected BTC ~US$500k vs ~US$66k actual; the model is an **auto-correlation artifact** (price regressed on a deterministic, monotonically rising supply schedule — spurious by construction). **Citing S2F is a RED FLAG**, not a valuation signal. If a source leans on S2F, discount the whole analysis.

## How to APPLY (decision rules for the level)
1. **Lead with MVRV-Z** to set the coarse zone: <0 deep value, ~0–2 cheap, ~2–5 fair, ~5–7 rich, >7 euphoric/top.
2. **Confirm with realized price and NUPL.** Price below realized price + NUPL <0 = high-conviction *cheap* zone. NUPL >0.75 = high-conviction *rich* zone.
3. **Cross-check miner & long-run trend** with Puell and the 200-week MA heatmap for the bottom zone; use Pi Cycle only as a top-side confirmation.
4. **Read behavior** (LTH supply rising + exchange outflows = supply tightening, supportive) as a slower-moving tilt input.
5. **Output a zone, never a precise top/bottom or "buy today."** Hand the zone to the execution layer (`04`) as the *valuation tilt* in tilted-DCA.

## Caveals / where it hedges
- **Zone signal, not day-timing.** On-chain is reliable at extremes and mushy in the middle of a range.
- **Thresholds decay** as the asset matures and as supply concentrates (ETFs/custodians hold coins off-chain, blurring exchange-flow reads).
- **Most metrics are BTC-native** — ETH/alt equivalents exist but are noisier and shorter-history.
- **Auto-correlation / overfitting risk** plagues this whole field (S2F is the cautionary tale); prefer metrics grounded in real cost basis over fitted price models.

## Memorable quotes
- "Market value to realized value tells you what the average holder paid — and whether the market is in profit or pain."
- "MVRV Z-score above 7 has marked the danger zone; below zero has marked capitulation."
- "Stock-to-Flow predicted half a million dollars; the chart printed sixty-six thousand. The model wasn't early — it was auto-correlated."
- "On-chain gives you the zone, not the day."
