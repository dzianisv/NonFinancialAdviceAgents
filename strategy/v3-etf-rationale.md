# v3 — Why each ETF? (sourced rationale)

> **Status: design justification, NOT proof of performance.** This document explains *why each sleeve
> exists* (the investment principle, with a citation) and *why a specific ETF implements it* (verified
> fund facts, with the issuer source). It does **not** prove the assembled v3 portfolio survives a crash
> — that requires backtesting the actual allocation (see the note at the bottom). Educational analysis,
> not financial advice.

## How to read this / how it was verified

Every fund fact below (inception, expense ratio, what it holds, AUM) was pulled from the **issuer's own
page or filing** on **2026-05-30**, not from memory. Where an issuer site blocked automated fetching or a
figure came from a secondary aggregator, it is **flagged inline**. Point-in-time figures (AUM, duration)
drift daily. **Verify on the live issuer page before deploying real capital.**

The chain of reasoning is: the backtest ([`v3-bubble-aware-all-weather.md`](v3-bubble-aware-all-weather.md))
showed a *structure* works (de-concentrate + gold + trend + cash + deploy-on-dips). Each sleeve below is
one element of that structure; each ETF is a low-cost, liquid way to hold that sleeve today.

---

## The valuation backdrop (why de-risk at all)

The whole portfolio is a *response* to expensive, concentrated US equity. The trigger conditions, verified:

| Metric | Reading | Historical context | Source |
|---|---|---|---|
| **Shiller CAPE** | **42.66** (close 2026-05-29) | mean 17.38, median 16.09; prior peak 44.19 (Dec 1999) | [multpl.com](https://www.multpl.com/shiller-pe) (Shiller data series); [Shiller data](http://www.econ.yale.edu/~shiller/data.htm) |
| **Buffett Indicator** (mkt cap / GDP) | **~230–238%** (late May 2026) | Buffett's rule: 75–90% fair, >120% overvalued | [GuruFocus](https://www.gurufocus.com/stock-market-valuations.php); [Advisor Perspectives](https://www.advisorperspectives.com/dshort/updates/2026/05/06/buffett-valuation-indicator-april-2026) ⚠️ source-dependent (229–238%), no single primary source |
| **S&P 500 top-10 weight** | **~35–40%** (YE2025 ~40.7%; ~35.6% Apr 2026 per one tracker) | held ~18–23% from 1990–2015 | [RBC WM](https://www.rbcwealthmanagement.com/en-us/insights/the-great-narrowing-sp-500-concentration) ⚠️ date/basket-dependent |
| **Active-fund failure (SPIVA)** | **89.5%** of US large-cap active funds lagged the S&P 500 over the **15yr** to Dec 2024 | 0 of 22 US equity categories had a majority beating | [SPIVA US Year-End 2024](https://www.spglobal.com/spdji/en/documents/spiva/spiva-us-year-end-2024.pdf) ⚠️ S&P domain 403'd fetch; figure corroborated via multiple secondary citations |

CAPE near the dot-com peak + record concentration is the case for *not* holding cap-weight S&P/QQQ at full
size. SPIVA is the case for *not* trying to stock-pick your way out (→ [`v2`](v2-factor-selection.md)).
The answer is structural diversification, below.

---

## The model portfolios this is derived from

v3 is not invented from scratch — it's a modern, ETF-based blend of three well-documented all-weather designs:

- **Permanent Portfolio** (Harry Browne, *Inflation-Proofing Your Investments*, 1981): 25% stock / 25%
  long bond / 25% gold / 25% cash — one asset for each of four economic regimes (prosperity, deflation,
  inflation, tight money). [optimizedportfolio.com summary](https://www.optimizedportfolio.com/permanent-portfolio/)
  · [AAII](https://www.aaii.com/journal/article/the-permanent-portfolio-using-allocation-to-build-and-protect-wealth)
- **All Weather** (Ray Dalio / Bridgewater): balance *risk* (not dollars) across the four regimes — risk
  parity. Retail proxy ~30% equity / 55% Treasuries / 7.5% gold / 7.5% commodities. ⚠️ that split is a
  widely-cited *retail proxy* (Tony Robbins' *Money: Master the Game*), not an official Bridgewater
  disclosure. [optimizedportfolio.com](https://www.optimizedportfolio.com/all-weather-portfolio/)
- **Golden Butterfly** (Tyler, Portfolio Charts): five equal 20% slices — total market / small-cap value /
  long Treasury / short Treasury / gold. Raises equity to 40% vs the Permanent Portfolio via a value tilt.
  [portfoliocharts.com](https://portfoliocharts.com/portfolios/golden-butterfly-portfolio/)

In our own backtest ([`v3-bubble-aware-all-weather.md`](v3-bubble-aware-all-weather.md)) the Permanent
Portfolio (0.69 Sharpe, −16% max DD) and Golden Butterfly (0.67, −22%) crushed the S&P (0.38, −55%) on
risk-adjusted terms and were flat-to-positive through the dot-com bust. v3 keeps that DNA but **modernizes
the equity sleeve** (de-concentrate, not just cap-weight) and **swaps the trend mechanism** to managed
futures.

---

## Equity sleeves

### US large cap — **RSP** (equal-weight) over VOO
- **Role:** hold US large caps *without* the ~35–40% mega-cap concentration that makes cap-weight a
  concentrated AI bet. Equal-weight gives every S&P 500 name ~0.2%, adding a structural size + (mild)
  value tilt and a contrarian quarterly rebalance.
- **Why this fund:** Invesco S&P 500 Equal Weight ETF. Inception **2003-04-24**, expense ratio **0.20%**,
  holds **505** names equal-weighted, rebalanced quarterly, **~$89.5B** AUM (2026-05-29).
  [Invesco](https://www.invesco.com/us/en/financial-products/etfs/invesco-sp-500-equal-weight-etf.html)
- **Principle source:** [S&P DJI — Equal Weight Index FAQ](https://www.spglobal.com/spdji/en/education/article/sp-500-equal-weight-index-faq/)
  (same constituents, equal-weighted, size/anti-momentum tilt vs cap-weight). ⚠️ the often-cited
  "equal-weight beat cap-weight ~1.5%/yr 2003–2022" stat is from a search summary, not a primary doc —
  treat as approximate.

### International — **VXUS**
- **Role:** diversify away from a 100% US book; reduce single-country/single-regime risk. Especially
  relevant when US valuations are extreme and ex-US is cheaper.
- **Why this fund:** Vanguard Total International Stock ETF. Inception **2011-01-26**, expense ratio
  **0.05%**, tracks **FTSE Global All Cap ex US** (~8,800 stocks, developed + emerging), **~$133B** ETF
  net assets (2026-03-31). [Vanguard fact sheet](https://fund-docs.vanguard.com/F3369.pdf)
- **Principle source:** [Vanguard — *Global equity investing: benefits of diversification*](https://www.vanguardmexico.com/content/dam/intl/americas/documents/mexico/en/global-equity-investing-diversification-sizing.pdf);
  [*Making the case for international equity allocations*](https://corporate.vanguard.com/content/corporatesite/us/en/corp/articles/making-case-international-equity-allocations.html).

### US small-cap value — **AVUV**
- **Role:** harvest the **size + value premia** (and a profitability screen) — return sources academically
  distinct from the mega-cap growth driving the index, so it diversifies *and* tilts toward expected return.
- **Why this fund:** Avantis US Small Cap Value ETF. Inception **2019-09-24**, expense ratio **0.25%**,
  **actively managed** (does *not* track an index — selects low-valuation, higher-profitability small caps;
  Russell 2000 Value shown only as a benchmark), **799** holdings, **~$23.4B** AUM (2026-03-31).
  [Avantis fact sheet](https://res.avantisinvestors.com/docs/avantis-us-small-cap-value-avuv-etf-fact-sheet.pdf)
  ⚠️ one automated PDF read mis-printed inception as "April 2026"; the document text says **2019-09-24**.
- **Principle source:** Fama & French (1992) *The Cross-Section of Expected Stock Returns*, J. Finance
  47(2); Fama & French (1993) *Common Risk Factors in the Returns on Stocks and Bonds*, JFE 33(1)
  ([PDF](https://www.bauer.uh.edu/rsusmel/phd/Fama-French_JFE93.pdf)) — the size (SMB) and value (HML)
  factors. Avantis builds explicitly on this framework (price + book equity + expected profitability).

### Min-vol / quality — **USMV**
- **Role:** dampen equity drawdown via the **low-volatility anomaly** — low-vol stocks have historically
  delivered better risk-adjusted returns; this sleeve cushions the equity book in a selloff.
- **Why this fund:** iShares MSCI USA Min Vol Factor ETF. Inception **2011-10-18**, expense ratio
  **0.15%**, tracks **MSCI USA Minimum Volatility** (optimizer-weighted, not cap-weight), **169** holdings,
  **~$23.1B** AUM (2026-05-29). [iShares](https://www.ishares.com/us/products/239695/ishares-msci-usa-minimum-volatility-etf)
  ⚠️ iShares page 403'd direct fetch; figures read off the rendered official page.
- **Principle source:** Baker, Bradley & Wurgler (2011) *Benchmarks as Limits to Arbitrage: Understanding
  the Low-Volatility Anomaly*, Financial Analysts Journal 67(1)
  ([NYU Stern PDF](https://pages.stern.nyu.edu/~jwurgler/papers/faj-benchmarks.pdf)).

---

## Diversifiers & crisis-alpha

### Gold — **GLD**
- **Role:** the regime hedge for inflation / monetary stress and a low-to-negative equity correlation that
  *strengthens* when equities sell off. It was the single biggest reason the Permanent/All-Weather mixes
  were positive through 2000–02 (see backtest caveats — gold's 2000s bull was a real tailwind).
- **Why this fund:** SPDR Gold Shares (SPDR Gold Trust). Inception **2004-11-18**, expense ratio **0.40%**,
  holds **physical gold bullion** (grantor trust), **~$150B** net assets (2026-05-29).
  [SSGA](https://www.ssga.com/us/en/intermediary/etfs/spdr-gold-shares-gld) *(IAU at 0.25% is a cheaper
  alternative for the same exposure.)*
- **Principle source:** [World Gold Council — *Relevance of gold as a strategic asset (2025)*, Diversification](https://www.gold.org/goldhub/research/relevance-of-gold-as-a-strategic-asset-2025/diversification)
  (gold rose ~21% USD Dec 2007–Feb 2009 while equities fell).

### Trend / managed futures — **DBMF**
- **Role:** **"crisis alpha."** Trend-following goes short equities/bonds and long whatever's working, so it
  has historically *profited* in extended equity bear markets — the one diversifier that tends to pay off
  precisely when stocks *and* bonds fall together (e.g. 2022). This is the sleeve that replaces the
  backtest's crude "200d-SMA on the S&P" with a real, multi-asset managed-futures strategy.
- **Why this fund:** iMGP DBi Managed Futures Strategy ETF. Inception **2019-05-07** (SEC filing date; first
  reliable yfinance bar 2019-05-08, which is where the backtest splice seam sits), expense ratio
  **0.85%**, **actively managed replication** — the "Dynamic Beta Engine" reads the trailing 60-day returns
  of the largest CTAs and rebuilds a long/short futures book (equities, rates, FX, commodities) to match
  their *performance*; targets 8–10% vol. [SEC 497K (2026-04-30)](https://www.sec.gov/Archives/edgar/data/0001020425/000119312526197034/d62276d497k.htm)
  · [fact sheet](https://imgpfunds.com/wp-content/uploads/pdfs/holdings/DBMF_FACTSHEETS_EN.pdf)
  ⚠️ AUM ~$2.0B (issuer fact sheet 12/31/25) vs ~$3.5B (third-party 5/20/26) — verify live. DBMF does *not*
  "track the SG CTA Index" (that's only a comparison benchmark). Don't confuse with the separate Luxembourg
  UCITS "iMGP DBi Managed Futures Fund." Expense ratio is the highest in the portfolio — it buys an
  actively-replicated strategy, not an index.
- **Principle source:** Hurst, Ooi & Pedersen (AQR), *A Century of Evidence on Trend-Following Investing*,
  J. Portfolio Management 44(1), 2017 ([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2993026))
  — positive every decade 1880–2016, strong in 8 of the 10 largest 60/40 drawdowns. Term "crisis alpha":
  Greyserman & Kaminski, *Trend Following with Managed Futures* (Wiley, 2014). *KMLM is an alternative.*

### Long/intermediate Treasuries — **TLT**
- **Role:** flight-to-quality ballast in a *growth* shock / deflation (the classic recession hedge). Kept
  **modest** on purpose — see the flag.
- **Why this fund:** iShares 20+ Year Treasury Bond ETF. Inception **2002-07-22**, expense ratio **0.15%**,
  tracks **ICE US Treasury 20+ Year**, effective **duration ~15.3yr**, **~$42.6B** AUM (2026-03-31).
  [iShares](https://www.ishares.com/us/products/239454/ishares-20-year-treasury-bond-etf) *(IEF is the
  intermediate, lower-duration option.)*
- **⚠️ The 2022 lesson (why modest, why not the only diversifier):** in 2022 long Treasuries fell *with*
  equities — the worst year on record for US bonds — so duration is not a reliable crash hedge against an
  *inflation* shock. That failure is exactly why gold and trend (above) carry comparable weight.
  [CNBC](https://www.cnbc.com/2023/01/07/2022-was-the-worst-ever-year-for-us-bonds-how-to-position-for-2023.html)
  · [Callan](https://www.callan.com/blog/stock-and-bond-declines/). ⚠️ specific magnitude stats (e.g.
  "30yr −39%") were *not* confirmed to a primary source — the *fact* of the joint decline is well-sourced.

### TIPS — **SCHP**
- **Role:** explicit inflation protection — principal adjusts with CPI, covering the regime where both
  nominal bonds and equities can struggle.
- **Why this fund:** Schwab US TIPS ETF. Inception **2010-08-05**, expense ratio **0.03%** (cheapest sleeve),
  tracks **Bloomberg US Treasury Inflation-Linked Bond (Series-L)**, **~$15.5B** AUM.
  [Schwab](https://www.schwabassetmanagement.com/products/schp) ⚠️ Schwab pages 403'd direct fetch; facts
  verified via the Schwab-branded research report + consistent third-party data, not a direct primary read.
  Effective duration (~6.5yr) is secondary-sourced.
- **Principle source:** [US Treasury / TreasuryDirect — TIPS](https://www.treasurydirect.gov/marketable-securities/tips/)
  (the instrument's CPI-linked principal definition).

---

## Cash & tail

### Dry powder — **SGOV**
- **Role:** the dip reserve and rebalancing buffer. Earns ~4–5% T-bill yield while it waits, with
  essentially no duration or credit risk — so "keeping powder dry" is no longer a 0% drag.
- **Why this fund:** iShares 0–3 Month Treasury Bond ETF. Inception **2020-05-26**, expense ratio **0.09%**,
  holds 0–3 month T-bills, **~$85–91B** AUM (mid-May 2026).
  [iShares](https://www.ishares.com/us/products/314116/ishares-0-3-month-treasury-bond-etf) ⚠️ iShares
  403'd; figures corroborated via secondary aggregators — all consistent on 0.09% and 2020-05-26. *(BIL is
  an equivalent.)*

### Tail / anti-beta (optional) — **BTAL**
- **Role:** covers the *fast* crash that gaps down before trend-following can react. Structurally negative
  beta — tends to rise when markets fall — so a small sleeve hedges the gap between "market breaks" and
  "trend models flip short."
- **Why this fund:** AGF US Market Neutral Anti-Beta Fund. Inception **2011-09-13**, **0.45%** net expense
  ratio (post-waiver through 2028-11-01), goes **long low-beta / short high-beta** US equities, dollar- and
  sector-neutral; **~$300–350M** AUM. [AGF](https://www.agf.com/us/products/btal/index.jsp) ⚠️ objective /
  strategy / 0.45% net ER / inception read directly from AGF and verified; AUM is secondary-sourced; older
  sources cite gross fees of 1.4–1.5% — the relevant *net* figure is 0.45%. *(TAIL — long put options — is
  the alternative tail hedge.)*

---

## The gap — now closed

Everything above justifies each *piece*. The earlier open question was whether the *assembled* portfolio
(these weights, this dip ladder) survives a crash, since half these ETFs post-date the dot-com/GFC crashes
and the dip mechanic was never simulated.

**That backtest now exists:** [`../backtests/v3_proxy_backtest.py`](../backtests/v3_proxy_backtest.py) runs
the actual v3 Balanced weights — each sleeve return-spliced onto a long-history proxy — through 2000-2026
with the dip ladder simulated, plus a real-ETF-only 2019-2026 cross-check. Results
([`results/v3_proxy_summary.txt`](../backtests/results/v3_proxy_summary.txt), summarized in
[`v3-bubble-aware-all-weather.md`](v3-bubble-aware-all-weather.md)):

- **Crash protection holds:** v3 max DD −27% vs S&P −55%; +73% through the 2000-09 lost decade vs S&P −9%.
- **Bull lag is real:** lifetime 6.8% vs 8.3% CAGR; real funds 2019-26 8.6% vs S&P 16.8% / QQQ 23.3%.
- **Dip ladder adds return *and* drawdown** — a return enhancer, not a hedge.

**Residual caveat (not a gap, a limitation):** pre-2019 sleeves use proxies, several of which *understate*
v3's real protection (min-vol→S&P, anti-beta→cash) and the trend proxy is a 3-asset simplification of real
managed futures. The 2019-2026 real-ETF table is the no-proxy check. v3 now stands on its own numbers — read
with the proxy caveats in [`results/v3_proxy_summary.txt`](../backtests/results/v3_proxy_summary.txt).

## Provenance
ETF facts verified 2026-05-30 from issuer pages/filings (cited inline; flags preserved). Concept citations
are primary academic / issuer / index-provider sources. Model-portfolio lineage:
[`v3-bubble-aware-all-weather.md`](v3-bubble-aware-all-weather.md). Strategy evolution:
[`README.md`](README.md).
