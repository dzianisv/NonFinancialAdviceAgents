# Book Index & Provenance — Dark Pool / Off-Exchange Accumulation Lens

> Source materials for the `analyst-smartmoney-darkpool` skill. The three books below provide
> institutional history, regulatory context, and market-structure backdrop. The analytical methodology
> of this skill — the DIX inversion, the accumulation signal — comes from the SqueezeMetrics data
> product and white paper described first. Do not conflate the two.

## Primary data source (data product + white paper, NOT a book)

**SqueezeMetrics, "Short is Long"** (white paper, SqueezeMetrics.com, ~2019).
The Dark Pool Index (DIX) and Gamma Exposure (GEX) are proprietary data products built by SqueezeMetrics
from FINRA TRF daily short-volume files. The "Short is Long" white paper describes the core empirical
finding — elevated dark-pool short volume correlates with higher forward S&P 500 returns — and the
market-maker hedging mechanic that explains why. Freely downloadable at squeezemetrics.com.

**This is a data product and white paper — NOT a book. Do not cite it as a book, assign ISBNs to it,
or attribute page numbers to it. Do not reconstruct its formula; the algorithm is proprietary.**

The live DIX chart and downloadable CSV are at: `https://squeezemetrics.com/monitor/dix`

## Books — contextual background (NOT grounded in the skill's analytical methodology)

These three books provide the institutional history, regulatory debate, and market-structure context in
which dark pools operate. They are background for a reader who wants to understand *why* off-exchange
venues exist and who the participants are. They are **not** the source of the DIX methodology or the
accumulation signal used in this skill. Do not attribute any specific analytical claim from the skill
to these books; that would be a provenance error.

---

**Scott Patterson, *Dark Pools: The Rise of the Machine Traders and the Rigging of the U.S. Stock Market***
(Crown Business, 2012).

Narrative history of the rise of electronic dark pools, algorithmic trading, and high-frequency market
makers from the 1990s through the Flash Crash of 2010. Useful for understanding why off-exchange venues
were created, who the early liquidity providers were, and how the fragmented U.S. market structure emerged.
Not a quantitative analytics text — no DIX, no GEX, no TRF methodology.

---

**Michael Lewis, *Flash Boys: A Wall Street Revolt***
(W. W. Norton, 2014).

Exposé centered on IEX's founding and the argument that HFT firms systematically front-run institutional
orders on lit exchanges. Provides the public debate backdrop for why institutions route large blocks to
dark pools in the first place — to avoid adverse selection. Less about dark-pool analytics, more about
lit-market predation and the regulatory response. Not a quantitative reference; no DIX or TRF analysis.

---

**Sal Arnuk & Joseph Saluzzi, *Broken Markets: How High Frequency Trading and Predatory Practices on
Wall Street Are Destroying Investor Confidence and Your Portfolio***
(FT Press / Pearson, 2012).

Practitioner critique of HFT and market fragmentation written by two broker-dealer traders. Covers
dark-pool opacity concerns, internalization of retail order flow, and the argument that the current
market structure disadvantages institutional and retail investors alike. Useful for the regulatory and
structural context of FINRA TRF reporting rules.

---

## What is NOT cited here

- No titles have been invented. The three books above are real published works; authors, publishers, and
  years are accurate to available knowledge. Verify before citing in formal research.
- The SqueezeMetrics DIX formula and exact weighting algorithm are **not publicly disclosed**. Do not
  attempt to reconstruct them from first principles or claim specific formula details.
- No claim in the SKILL.md body is attributed to any of the three books above. All analytical mechanics
  (MM hedging, the DIX inversion, the 45% threshold) are grounded in the SqueezeMetrics white paper
  and the FINRA TRF data practice. If a user wants the market-structure history contextualized, cite
  Patterson/Lewis/Arnuk as background — never as the source of the signal.

## Cross-references within this skill family

| Skill | Relationship |
|---|---|
| `analyst-smartmoney-positioning` | GEX is also a SqueezeMetrics product; shares the same data source; must be read alongside DIX for regime context |
| `analyst-smartmoney` | Parent conductor skill that routes across the full smart-money family |
| `analysis-orderflow` | Lit-market flow counterpart — tape reading, order-flow imbalance, volume-at-price; distinct from off-exchange dark-pool volume |
| `analyst-smartmoney-13f` / `analyst-smartmoney-13d` | Public SEC disclosures of institutional positions; named-party attribution that dark-pool data cannot provide |
