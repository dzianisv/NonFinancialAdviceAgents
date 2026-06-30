# Synthesis Rules, Reliability Ranking, and Failure Modes

This reference contains the load-bearing decision logic for synthesizing across all eight spokes into a single ACCUMULATING / DISTRIBUTING / NEUTRAL verdict. Read this before producing any output from `analyse-smartmoney`.

---

## Reliability ranking (high to low)

The following order governs conflict resolution. When signals conflict, trust higher-ranked signals over lower-ranked ones, and downgrade conviction rather than forcing a verdict.

| Rank | Signal / Spoke | Why this rank | Lag |
|---|---|---|---|
| 1 | **Form 4 cluster buys** (`analyse-smartmoney-form4`) | Real money, binding disclosure, highest-information insiders, buy-side asymmetry proven academically (Seyhun 1998, Lakonishok-Lee 2001) | 2 business days |
| 2 | **13F institutional clustering** (`analyse-smartmoney-13f`) | Real money at scale, many independent funds increasing = breadth signal, but 45-day lag and long-only limits apply | 45 days |
| 2 | **13D activist filings** (`analyse-smartmoney-13d`) | Real money, concentrated stake, stated change-of-control intent — near-real-time for initial crossing | 10 calendar days |
| 3 | **COT extremes in commodities** (`analyse-smartmoney-positioning`) | Commercials are physically informed; 3-year normalized extreme (>90 or <10) is the contrarian smart-money signal; does not apply to equity futures | 3 days |
| 4 | **DIX / dark-pool tilt** (`analyse-smartmoney-darkpool`) | Counterintuitively high DIX = institutional buying; but it is an index-level signal only, not single-name, and is a vendor data product | 1 day |
| 5 | **Wyckoff structure** (`references/03-wyckoff-accumulation-distribution.md`) | Useful structural context for accumulation or distribution; discretionary and interpretive — confirms after the fact | N/A (price-based) |
| 6 | **Options flow — unusual sweeps/aggregate ratio** (`analyse-smartmoney-options`) | Pan-Poteshman aggregate ratio is academically supported; single sweeps are low signal-to-noise and frequently hedges | Real-time |
| 7 | **Congressional PTR** (`analyse-smartmoney-ptr`) | Empirical alpha contested post-STOCK Act; 45-day lag; treat as background color only | 45 days |
| 8 | **Prediction-market event odds** (`analyse-smartmoney-polymarket`) | Risk-neutral prices, not real-world probabilities; thin liquidity; useful for dated event catalysts only | Real-time (but thin) |

---

## Confirmation logic: independent classes, not independent feeds

The central synthesis rule: **count independent signal classes, not individual feed confirmations.**

**Two classes exist:**
- **Disclosed flows class:** Form 4 + 13F + 13D + PTR. All of these are regulatory filings disclosing real-money transactions.
- **Market-implied class:** Positioning (COT/funding/OI) + Options flow + Dark pool (DIX) + Polymarket. All of these are derived from pricing or order flow data.

**Counting rules:**
- Multiple feeds from the same class pointing the same direction = **one signal**, not N signals. Three 13F filers all reducing = one data point from the disclosed-flows class (though breadth across many filers increases confidence within the class).
- A disclosed-flows signal and a market-implied signal pointing the same direction = **two independent signals** (different mechanisms, different data sources, different actor types).
- Wyckoff is a structural overlay — count it as confirmatory context within market-implied, not as an independent class.

**Conviction thresholds:**
- **HIGH:** ≥3 independent signal classes aligned in the same direction, including at least one Rank 1–2 signal (Form 4 cluster or 13F/13D)
- **MED:** 2 independent classes aligned (e.g., disclosed + implied), or strong consensus within one class (e.g., Form 4 cluster + 13F both ACC, implied neutral)
- **LOW:** 1 class with directional signal, the other class neutral or unavailable
- **NEUTRAL output:** Active conflict between classes (disclosed ACC vs. implied DIST), or no directional signal in either class

---

## Conflict resolution procedure

When signals conflict:

1. **Check the hedge-as-signal failure mode first** (see below). Can the conflicting signal be explained as a hedge leg? If yes, discount it and reassess.

2. **Weight by reliability rank.** Rank 1–2 signals (Form 4, 13F/13D) outweigh Rank 6–8 signals (options flow, PTR, Polymarket). If Form 4 cluster buys say ACC and a single options sweep says DIST, the Form 4 read dominates.

3. **Check for lag-driven stale signal.** A 13F ACC reading is 45 days old. If recent market-implied signals are strongly DIST, the 13F may describe a prior-quarter position that has since been reversed. Reduce 13F weight in fast-moving situations.

4. **If genuine conflict persists after (1)–(3), output NEUTRAL.** Do not manufacture a verdict by cherry-picking the signal that supports a pre-existing view. NEUTRAL + LOW conviction + clear invalidation statement is the honest and analytically correct output when the evidence is genuinely mixed.

---

## The six failure modes (mandatory check before every verdict)

These failure modes must be checked in order before finalizing the structured output block.

### 1. Lag — filings describe possibly-unwound portfolios

13F and PTR disclose positions as of a past date. The filing is a historical snapshot. In fast-moving situations, a 13F ACC filing 45 days ago may describe a position that was partially or fully reduced the day after quarter-end. Always note the lag explicitly in the output, especially for Rank 2 signals (13F).

### 2. Crowding — public trackers are arbitraged

Dataroma, WhaleWisdom, GuruFocus, Quiver Quantitative, and similar aggregators publish 13F and PTR signals to a large retail audience simultaneously. The edge from a famous manager's 13F position or a senator's PTR trade has already been partially front-run by the time it appears in a consumer-facing feed. Cloning a public guru 13F is consensus tracking, not edge. The independent analysis of raw EDGAR filings — including breadth across filers and the opportunistic-vs-routine insider distinction — is where any remaining edge lives.

### 3. Hedge-as-signal — THE dominant failure mode

**This is the most important failure mode in the entire skill family.** Reading one leg of a multi-leg position as a clean directional bet is the most common and most damaging error in smart-money analysis.

Specific manifestations:
- **13F put position.** A large fund holds 500,000 puts on SPY in its 13F. This is widely reported as "bearish." But those puts may be portfolio insurance against a massive long equity book — the fund may be net bullish, and the puts are the hedge, not the view.
- **Options block print.** A $10M block on OTM puts appears on the tape. Likely a protective put purchase by a large long holder hedging earnings risk — not a speculative short bet.
- **Market maker short in dark pool.** High DIX (dark-pool short volume) = market maker shorting to hedge institutional buy flow. The short is the hedge; the institutional buying is the directional signal.
- **COT commercial short.** Wheat producer sells futures to lock in prices for the harvest. This is a commercial hedge, not a bear bet on wheat prices.

**The check:** For every market-implied ACC or DIST signal, ask: *What offsetting position could exist that would make this trade a hedge rather than a directional bet? Can I see that position in the available data?* If the hedge interpretation is plausible, downgrade conviction one notch before finalizing.

### 4. False confidence from correlated signals

Five options sweep prints on the same underlying, on the same day, from the same OPRA tape = **one signal from one class**, not five independent confirmations. Large institutions use algorithms that break large orders into multiple smaller prints — this is exactly what produces clusters of "unusual" options activity. Before counting confirmations, verify that the signals come from **mechanically different data sources** (regulatory filings vs. exchange data vs. off-exchange prints vs. prediction markets).

### 5. Survivorship in vendor marketing

Options flow services, dark-pool alert platforms, 13F clone products, and prediction-market analytics are all marketed based on their most impressive backtested examples. This is survivorship bias — the examples selected for marketing are the cases where the signal worked. Demand out-of-sample performance evidence before treating any vendor product as reliable alpha.

Specific honesty flags:
- Najarian (*Follow The Smart Money*, 2018) is the most widely read retail options-flow book and is promotional. It provides weak disclosure of false-positive rates. The signal framework is qualitatively reasonable, but the performance claims are not rigorously documented.
- The "retail 8–11% per insider cluster buy" figure cited in options-flow and insider-tracking marketing is **UNSOURCED**. Do not assert it. The Seyhun (1998) and Lakonishok-Lee (2001) figures (+4–6%/year alpha for insider buying generally) are from academic research; the higher retail-circulated figures are not.
- Congressional PTR alpha figures from Ziobrowski (2004, 2011) are pre-STOCK Act. The post-STOCK Act literature (Eggers-Hainmueller 2013, Chen-Sacerdote NBER 2024) finds substantially weaker or no significant edge.

### 6. Regime-dependence — signals work in some regimes, not others

Smart-money signals are not universal. Their effectiveness is regime-dependent:

- **Congressional alpha:** Pre-STOCK Act era (pre-2012) showed significant excess returns. Post-STOCK Act, the evidence is contested and the alpha has largely dissipated for most members. Residual edge may exist in specific leadership roles.
- **COT commercials as smart money:** Strong signal in physical commodity futures where commercials have genuine business exposure to the commodity. Weak or inapplicable signal in equity index futures, interest rate futures, and FX where "commercials" include financial intermediaries without physical exposure.
- **DIX as accumulation signal:** The SqueezeMetrics interpretation (high DIX = bullish) is specific to certain market-structure regimes. Extended periods of low volatility or unusual options market structure can break the assumed MM-hedging mechanism.
- **Insider buying alpha:** Most clearly documented in smaller-cap, less-followed stocks where information asymmetry is largest. In mega-cap stocks with enormous analyst coverage, insider buying alpha is attenuated.

---

## The bottom line

**Durable edge in smart-money analysis comes from disciplined cross-confirmation of real-money, low-lag disclosures — not from prediction using any single feed.**

The decision rule in all conflict or ambiguity cases is:
1. Check for hedge-as-signal
2. Weight by reliability rank
3. Require independent class confirmation
4. When confirmation is absent or evidence is genuinely mixed: **output NEUTRAL**

A NEUTRAL verdict with a clear invalidation condition is more useful than a forced ACC or DIST verdict built on a single signal class.

---

*Sources: Seyhun (1998), Lakonishok-Lee (2001), Cohen-Malloy-Pomorski (2012), Briese (2008), Pan-Poteshman (2006), Eggers-Hainmueller (2013), Chen-Sacerdote NBER (2024). See `references/book-index.md` for full citations and honesty flags.*
