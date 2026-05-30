# 02 — The Crash-Protection Playbook

*How to protect $1M through an AI-bubble unwind while keeping reasonable upside.
Educational analysis, not advice. Sources at the end.*

## The core principle

**There is no free lunch in crash protection — only different cost structures.**
Every hedge costs you something (cash drag, bull-market underperformance, premium bleed,
or whipsaw). The goal is not to eliminate the cost but to **pick hedges whose costs are
tolerable and whose payoffs are uncorrelated**, so no single regime breaks the whole book.

Three families:

| Family | Examples | How it earns / costs you |
|--------|----------|--------------------------|
| **Convergent / diversifying** | trend-following, risk parity, defensive factors, gold | earns its own return, happens to be uncorrelated; cost = tracking error in bull markets |
| **Convex / insurance** | tail-risk puts, long vol, anti-beta | loses slowly, pays violently in crashes; cost = premium "bleed" |
| **Static all-weather** | Permanent Portfolio, Golden Butterfly, All-Weather | survives by never betting everything on one regime; cost = capped upside |

**Each major crash humbles a *different* strategy** — so test every candidate against all four:
- **2000-2002** (slow tech unwind) — punishes concentration; rewards trend, gold, diversification.
- **2008** (credit/deflation) — punishes equity beta; rewards trend, long Treasuries, gold.
- **Feb-Mar 2020** (fast V-shape) — **breaks trend-following** (too fast for monthly signals);
  rewards tail puts, long Treasuries.
- **2022** (inflation, stocks+bonds both fall) — **breaks 60/40 and risk parity**; rewards trend,
  gold, commodities, low-vol, T-bills.

## 1. Trend-Following / Managed Futures — "crisis alpha"

**Mechanism.** Hold assets in uptrends, exit/short downtrends. Retail-simple version: the
**200-day (10-month) moving-average rule** — own an index only while it's above its 200d MA,
else go to cash/bonds. **Dual Momentum (Antonacci GEM)** = relative momentum (pick the strongest
risk asset) + **absolute momentum** (only hold it if it's beating T-bills, else hold bonds).

**Why it works in crashes.** Crashes are usually *protracted* (months). Trend systems detect the
downtrend and step aside. AQR's *Century of Evidence* (1880-2016): time-series momentum was
positive in **8 of the 10 largest 60/40 drawdowns** in 137 years.

**Evidence:** 2008 — strongly positive while equities fell ~50%. 2022 — banner year: **KMLM +44.8%,
DBMF +31.6%** while S&P −18%, TLT −25%. **2020 — its weakness:** the crash was too fast; many CTAs
were caught long. Our own 200d-rule backtest: dot-com window −4% (vs S&P −47%), GFC −5.7% (vs −55%),
2022 −14.6% (vs −24.6%), and it still compounded **9.1%/yr 2000-2026** with a −23% max drawdown.

**ETFs:** DBMF, KMLM, CTA, RSST (return-stacked equity+trend). For the simple rule: SPY/VTI + BIL/SGOV.
⚠️ **MTUM is cross-sectional equity momentum — long-only, NO crash protection** (crashed in 2020). Don't confuse it with managed futures.

**Cost:** whipsaw in choppy markets; fails on overnight shocks; years of lagging in strong bulls.

## 2. Tail-Risk Hedging (put overlays / long vol)

**Mechanism.** Small persistent allocation to deep OTM S&P puts. Expire worthless most of the time
("bleed"); in a crash, convexity pays enormously. Spitznagel/Universa: a ~3.3% hedge sleeve alongside
~96.7% equities can *raise* the portfolio's **geometric** return by avoiding the compounding damage
of large drawdowns ("risk mitigation that pays").

**Evidence:** CBOE Eurekahedge Tail Risk index **+44.3% in Q1 2020**. **But** the same index *lost
~2.65%/yr 2008-2020* — naively holding it beat nothing. The protection is correctly priced most of
the time; it only adds value if you **size it small and monetize gains into equities** in the crash.

**ETFs (proxies):** TAIL (Treasuries + rolling OTM SPX puts), SWAN (~90% Treasuries + LEAP calls),
BTAL (anti-beta long-short — spikes when markets fall, low carry). Taleb's retail version is the
**barbell**, not active put-buying.

**Cost:** negative carry; behaviorally brutal; hard for retail to execute well. Use sparingly (≤5%).

## 3. Risk Parity / All-Weather (Dalio)

**Mechanism.** Allocate by *risk contribution*, not dollars — lever low-vol bonds so stocks, bonds,
gold, commodities each contribute equal volatility. Robust to all four macro regimes
(growth ↑/↓ × inflation ↑/↓).

**Evidence:** great 1990s-2021. **2022 failure: RPAR −22.8%, worse than equities** — first year since
1972 that US stocks, Treasuries *and* gold all fell, and leverage on long duration amplified it.
**Lesson: risk parity is short an inflation shock.**

**ETFs:** RPAR, UPAR (levered), NTSX (90/60 efficient core). DIY: equity + TLT + gold/commodity at lower leverage.

## 4. Permanent Portfolio & Golden Butterfly

**Permanent Portfolio (Harry Browne):** 25% each — total market / long Treasuries / gold / cash.
One asset thrives in each regime (prosperity / deflation / inflation / tight money). ~8.5% CAGR
1968-2026 at ~7% vol; long-run max drawdown ~16%; 2008 drawdown ~⅓ of the S&P's. Weak spot: Oct 2022.

**Golden Butterfly (Tyler):** 20% each — total market / **small-cap value** / long bonds / short
bonds / gold. ~10% CAGR over ~50 yrs at ~8% vol, **max drawdown ~−18%**; captured ~93% of the S&P's
CAGR at ~½ the vol and ~⅓ the max drawdown.

Our backtest confirms the shape: Permanent Portfolio **+2.5% through the dot-com bust** (vs S&P −47%),
−6% in the GFC (vs −55%), full-period Sharpe **0.69 vs the S&P's 0.38**, max drawdown −15.8% vs −55%.

**ETFs:** VTI / AVUV (SCV) / TLT / SGOV / GLD. Simple, no leverage, behaviorally easy to hold.
**Cost:** lean heavily on long bonds + gold (2022-vulnerable); lag in strong equity bulls.

## 5. Defensive equity factors (low-vol, quality, value, dividends)

**Low-vol anomaly:** low-volatility stocks have delivered market-like returns with lower risk.
They don't *avoid* crashes, they *cushion* them. 2008: min-vol ~−27% vs S&P −38%. **2022: USMV ~−9%
vs SPY −20%.** 2020: weak edge (indiscriminate crash). **Cost:** USMV ~45% vs SPY ~92% over the
5 yrs to 2026 — the price of defense in a tech bull.

**ETFs:** USMV (min vol), SPLV (low vol, more utilities/financials), QUAL (quality), NOBL (dividend
aristocrats), SCHD/VYM (dividend). Keeps you in equities with lower beta.

## 6. Safe-haven assets & the 2022 lesson

- **Long Treasuries (TLT):** the recession/deflation hedge. 2008 ~+40%; 2020 ~+20% in the crash.
  **2022: −25-30%** — bonds *caused* the 60/40 loss. **Treasuries hedge growth shocks, not inflation
  shocks**; their stock-correlation is regime-dependent.
- **Gold (GLD/IAU):** the inflation/debasement hedge and a more regime-agnostic diversifier. 2008
  +5.8% (with intra-crisis liquidation dips), 2020 ~flat-then-strong, **2022 ~flat** while stocks and
  bonds fell. Weakness: no yield, dead decades (1980-2000).
- **The 60/40 failure of 2022** (worst combined stock+bond year in modern history) is the strongest
  argument for adding **non-duration** diversifiers (trend, gold, commodities, low-vol).

## 7. Income & cash

- **Covered-call income (JEPI/JEPQ/SPYI):** sell upside for premium → smoother, higher-income, lower
  drawdown. 2022: **JEPI −3.5% vs SPY −18%.** But captures only ~38-50% of bull-year upside. An income/
  vol reducer, **not** a true crash hedge (still long beta).
- **Cash / T-bills (SGOV/BIL/USFR):** at ~4-5% yields the opportunity cost of dry powder is low; pure
  optionality to buy the dip (see the dip-tranche skill).

## Books behind the strategies (distilled — full list in note 07)
- **Dalio, *Big Debt Crises*:** debt cycles are predictable in mechanism; diversify across regimes
  ("~15 uncorrelated streams") → All-Weather.
- **Spitznagel, *Safe Haven*:** geometric returns compound; convex hedges sized small and monetized
  can be "risk mitigation that pays"; gold/bonds are *costly* safe havens.
- **Antonacci, *Dual Momentum*:** absolute (trend) momentum is the protective element — exit equities
  when they trail T-bills.
- **Taleb, *Antifragile*:** barbell (90% ultra-safe + 10% convex), avoid the fragile middle.
- **Faber, *GTAA / Ivy*:** apply the 10-month/200-day rule to each sleeve; equity-like returns at
  bond-like drawdowns; sidestepped most of 2008.

## Practical synthesis (feeds note 08)
Combine **orthogonal** hedges so no single regime breaks the book:
**trend/managed futures** (2008, 2022) + **gold** (2022) + **low-vol or covered-call equity**
(cushioned beta) + a small **convex tail / anti-beta** sleeve (2020) + **T-bills** (dry powder).

## Sources
- AQR *Century of Evidence on Trend-Following*; Antonacci optimalmomentum.com; quantifiedstrategies.com
- DBMF/KMLM/CTA 2022: pictureperfectportfolios.com, kraneshares.com, morningstar.com
- Spitznagel/Universa & tail bleed: quantifiedstrategies.com, institutionalinvestor.com, hedgeweek.com
- RPAR 2022: optimizedportfolio.com, sec.gov N-CSR FY2022
- Permanent / Golden Butterfly: portfoliocharts.com, optimizedportfolio.com, lazyportfolioetf.com
- Low-vol: mezzi.com, morningstar.com; Gold/TLT/60-40: gold.org, quantifiedstrategies.com
- JEPI: optimizedportfolio.com, quantflowlab.com; Faber: mebfaber.com/timing-model, SSRN id962461
