# Market-Implied Signals: COT / Positioning / Options Flow / Dark Pools / Prediction Markets

Market-implied signals reveal what informed capital **prices** through positioning and order flow. Unlike disclosed flows, these signals are real-time or near-real-time — but they are **risk-neutral probability estimates**, not real-money disclosures. The hedge-as-signal failure mode (reading one leg of a hedge as a directional bet) is most dangerous here because the offsetting position is invisible.

---

## COT — Commitments of Traders (commodities: smart money = commercials)

**What it is.** The CFTC publishes weekly Commitments of Traders reports every Friday for all regulated futures markets. Three categories: **Commercials** (hedgers with physical business exposure), **Non-Commercials** (large speculators), and **Non-Reportables** (small speculators). The Disaggregated COT further splits Producer/Merchant/Processor/User vs. Swap Dealer.

**Official free source.** https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm — updated every Friday for positions as of Tuesday.

**The smart-money read in commodities.** Stephen Briese's canonical method (*The Commitments of Traders Bible*, 2008, Wiley): **Commercials are the smart side in commodity futures** because they hedge physical exposure and have superior knowledge of supply, demand, and seasonal patterns. When commercials are at an extreme net long position (>90th percentile of their net position over a 3-year rolling lookback, normalized 0–100), they are providing unusual price support — **contrarian bullish**. When commercials are at an extreme net short (top-decile net short), they are hedging aggressively — **contrarian bearish** (implying they expect prices to fall in their physical markets).

**Normalization method (Briese).** Raw COT net position swings with open interest. Normalize: `COT Index = (current net - 3yr low net) / (3yr high net - 3yr low net) × 100`. Index >90 = bullish extreme; Index <10 = bearish extreme. Mid-range (20–80) = no signal.

**Important limits:**
- **COT does not translate to equity futures.** In equity index futures (ES, NQ, RTY), "commercials" are often index-arbitrageurs and portfolio hedgers — not informed directional traders. The commercial-as-smart-money logic is commodity-specific.
- **3-day publication lag.** Positions are as of Tuesday; published Friday. Approximately 3-day lag.
- **COT extremes are a timing indicator, not a trigger.** Extremes can persist for weeks before reversing. Combine with price action (breaking out of the base) before acting.

**Funding rates, open interest, and basis (crypto/perpetuals).** For crypto perpetual futures: elevated funding (positive) means longs are paying shorts — crowded long, risk of flush. Negative funding = shorts paying longs — crowded short, squeeze risk. Rising OI into a price move confirms conviction; falling OI into a move = short covering or stop-outs, not new positioning. Basis (spot vs. futures spread) reflects carry demand — persistent premium = institutional demand for long exposure.

---

## Options Flow — Single-Name Unusual Activity

**What it is.** Options prints are public via OPRA (Options Price Reporting Authority). Unusual activity = options volume significantly above open interest + large size + aggressive fill (paid at or above ask). Three dimensions:

- **Sweeps vs. blocks.** A sweep is an order that takes liquidity aggressively across multiple exchanges to fill immediately — associated with urgency and directional intent. A block is a large negotiated print, often done off-exchange — frequently a hedge against an existing position.
- **Put/call skew.** Elevated put implied volatility relative to calls (put skew up) = demand for downside protection, bearish signal. Call skew = bullish demand. Watch the 25-delta skew (risk reversal).
- **Aggregate ratio vs. single prints.** Pan and Poteshman (2006, *Journal of Finance*) is the key academic reference: **the aggregate put/call volume ratio — especially in customer-initiated trades — is a statistically reliable predictor of next-day returns.** Single unusual prints are low signal-to-noise. The actionable signal is the aggregate directional tilt in customer-initiated flow, not any one print.
- **Gamma and max-pain.** Dealer gamma positioning creates predictable price magnetism around high-OI strikes (max-pain / gamma-pin effect). This is mechanical, not directional smart-money signal.

**Honesty flags.** The Najarian brothers' *Follow The Smart Money* (2018) is the most widely cited retail options-flow book — but it is promotional and provides weak evidence on false-positive rates. Single sweeps are frequently hedges, market-maker delta-hedging, or automated arbitrage. Do **not** treat every large print as a directed bet; classify as sweep (urgency-plausible) vs. block (hedge-plausible) first.

**What to extract.** Screen for: (1) volume > 3× average daily volume for that strike/expiry, (2) volume > OI at print time (new position, not a roll), (3) fill at or above mid/ask (buyer taking liquidity), (4) expiry ≥ 2 weeks out (not a 0DTE mechanical play), (5) near-the-money or out-of-the-money (not ITM hedges). Then classify sweep vs. block, check for known earnings/catalyst schedule (increases hedge-as-signal probability), and assess aggregate directional skew across all unusual prints for the session.

---

## Dark Pools — DIX and Block Prints

**What it is.** Dark pools are off-exchange trading venues where large institutional orders execute without pre-trade transparency. SqueezeMetrics publishes the **Dark Pool Index (DIX)** — defined as the percentage of daily S&P 500 volume that is executed in dark pools as a short sale.

**The counterintuitive read.** High DIX (elevated dark-pool short-sale volume) is a **bullish** signal for equities. The mechanism: when institutions place large buy orders in dark pools, market makers hedge by shorting the same name in the same dark venue. High dark-pool short volume therefore reflects large institutional buying being hedged — not net short selling. SqueezeMetrics' own documentation confirms: DIX >45% has historically been associated with forward equity outperformance at the index level.

**Limits.**
- **DIX is an index-level signal only.** It measures aggregate S&P 500 dark-pool activity, not individual stock accumulation. It provides macro-level background color; do not use it as a single-name directional trigger.
- **It is a data product from SqueezeMetrics**, not a published academic indicator with independent validation. Treat accordingly — flag as vendor data.
- **Delayed and intraday noisy.** Daily data; intraday dark-pool prints from Level 2 vendors are real-time but require TRF/ADF designation and are incomplete (not all dark pools report to FINRA).
- **Block prints as single-name color.** Off-exchange block prints (reported via FINRA OTC and TRF) for individual stocks can signal institutional accumulation when they appear systematically above average on up-days. But single prints are easily hedges or crossing of client orders; look for persistence over 5+ sessions.

---

## Prediction Markets — Polymarket and Peers (risk-neutral event odds)

**What it is.** Prediction markets (Polymarket, Kalshi, PredictIt) aggregate crowd bets on specific binary or probabilistic events: election outcomes, Fed rate decisions, macro data releases, regulatory approvals. Prices clear at market between buyers and sellers of outcome shares.

**The smart-money read.** Prediction-market prices are not directly the same as real-world probability estimates. They are **risk-neutral prices** — they embed a **volatility risk premium** that must be haircut to convert to a real-world probability. A Polymarket contract at 70% is most accurately interpreted as "the market implies approximately 60–65% real-world probability after adjusting for the risk premium paid by risk-averse buyers of certainty."

**When prediction markets are useful.** They incorporate information faster than consensus polls or forecaster surveys for events with clear binary resolution dates. For macro-driven equity signals (Fed decisions, regulatory approvals, election outcomes with sector implications), they provide a cleaner probability estimate than most analyst forecasts.

**Limits.**
- **Liquidity-limited.** Thin markets produce noisy prices. Contracts with <$1M in total volume should be treated with low confidence.
- **Risk-premium haircut is necessary.** Do not assert a 70% Polymarket price as "70% probability" — state the risk-neutral price and note the real-world probability is lower.
- **Not a real-money smart-money signal.** Polymarket capital is a fraction of institutional capital; large positions move prices. This is the least reliable spoke in the family — use as color on dated event catalysts, not as a primary directional signal.

---

## Cross-signal reading for market-implied signals

| Pattern | Interpretation |
|---|---|
| COT commercial net long >90th percentile + bullish price break from base | Strongest commodity market-implied ACC signal — smart hedgers positioning long AND price confirming |
| High DIX (>45%) for 3+ consecutive days + aggregate options call skew | Index-level accumulation probable; sector or single-name confirmation needed |
| Aggregate customer put/call ratio at multi-month extreme low (all calls) | Pan-Poteshman aggregate signal — historically meaningful next-day return predictive |
| Single unusual sweep on one strike, one date | Low reliability; classify sweep vs. block, check for catalyst, do not count as independent confirmation |
| Prediction market event odds diverging from analyst consensus | Useful catalyst-timing color; haircut the probability; combine with disclosed flows before acting |

---

*Sources: Briese (2008), Pan-Poteshman (2006 Journal of Finance), SqueezeMetrics DIX documentation, Easley-O'Hara-Srinivas (1998). See `references/book-index.md` for full citations and honesty flags.*
