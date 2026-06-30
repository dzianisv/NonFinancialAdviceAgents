# 09 — Does Bottom-Up Stock Selection Beat the Index? (Evidence)

*Should the fund's analyst pick individual undervalued stocks — e.g., using Morningstar
fair-value & moat ratings? Results from `backtests/fundamental_screens_backtest.py`. Educational.*

## The question

The earlier repo backtests labelled "Morningstar" / "value" actually used a **price proxy**
(a stock is "undervalued" if it's down ≥20% from its 52-week high). That crude screen **lost to
VOO in 19 of 20 quarters (−4.3%/yr)** — it just bought falling knives. So we tested it properly,
using the **investable versions** of each real methodology: strategy/factor ETFs whose index rules
*are* the screen, applied live in real time (which avoids the look-ahead and survivorship traps of
DIY fundamental backtests).

The most direct test of "use Morningstar to pick stocks" is **MOAT** — the VanEck Morningstar Wide
Moat ETF — which buys attractively-priced stocks with wide economic moats using Morningstar's own
analyst **fair-value estimates + moat ratings**.

## Result: each strategy vs SPY, over its own full live history

| Methodology (ETF) | Since | CAGR | SPY CAGR | Beat? | Sharpe | SPY Sharpe |
|---|---|:--:|:--:|:--:|:--:|:--:|
| **Morningstar wide-moat + fair value (MOAT)** | 2012 | 13.5% | 14.7% | **no** | 0.70 | 0.79 |
| FCF yield "cash cows" (COWZ) | 2016 | 12.8% | 15.4% | no | 0.61 | 0.77 |
| S&P 500 Pure Value (RPV) | 2006 | 9.2% | 11.2% | no | 0.40 | 0.54 |
| MSCI Value Factor (VLUE) | 2013 | 13.7% | 14.8% | no | 0.68 | 0.78 |
| S&P 500 Quality (SPHQ) | 2005 | 10.1% | 11.1% | no | 0.49 | 0.54 |
| MSCI Quality (QUAL) | 2013 | 13.6% | 14.2% | no | 0.72 | 0.75 |
| **MSCI Momentum (MTUM)** | 2013 | **16.3%** | 14.8% | **YES** | 0.76 | 0.78 |
| Quality Dividend (SCHD) | 2011 | 13.3% | 15.3% | no | 0.76 | 0.82 |
| Dividend Aristocrats (NOBL) | 2013 | 10.2% | 14.4% | no | 0.57 | 0.76 |
| Min Volatility (USMV) | 2011 | 11.7% | 15.3% | no | 0.74 | 0.82 |

**Only 1 of 10 beat SPY on return (momentum); 0 of 10 beat it on Sharpe.** Even Morningstar's own
stock-picking process (MOAT) lagged the index over 14 years. This matches SPIVA: most selection
methods underperform a cheap index — especially in a mega-cap/AI-led bull where the index *is* the
winning bet.

## But the screens DO add drawdown defense

| Crisis | SPY | best defensive screens |
|--------|:---:|------------------------|
| **2022 bear** | −24.5% | **COWZ −7.6%, RPV −11%, SCHD −15%, NOBL −16%, USMV −17%** |
| 2023-26 AI bull (max DD) | −19% | **USMV −9%** |
| COVID 2020 | −34% | SPHQ −31%, MOAT −33% (small edge) |
| GFC 2007-09 | −55% | SPHQ −57%, RPV −73% (value got crushed) |

So value/quality/dividend/low-vol screens are **defensive sleeves**, not alpha engines: they lose
less in inflation-driven equity bears (2022) and grind with lower volatility — at the cost of
**lagging badly in bull markets** (MOAT +62% vs SPY +106% in 2023-26).

## What this means for the fund

1. **Don't build a Morningstar/value stock-picker as the core alpha source** — the investable version
   of exactly that underperformed. The index is a high bar in a concentration bull.
2. **Get "value/quality" exposure via cheap ETFs** (USMV/QUAL/COWZ/AVUV) as the *defensive equity
   sleeve* in `portfolio-construction` — that's where these screens earn their keep (2022 defense).
3. **The fund's real edge is structural, not stock-selection:** asset-class diversification + regime/
   trend overlays + risk management (note 03), where the all-weather mix beat the S&P on Sharpe and
   survived the lost decade. Stock-picking is a low-probability satellite at best.
4. **If you still want a stock-picking sleeve:** cap it small, use **point-in-time survivorship-safe
   data** (Sharadar/SimFin/EDGAR — never yfinance's current snapshot), and require it to clear the
   backtest gate (`.agents/skills/analyse-fundamental`). Most don't.
5. **Momentum is the one factor with a real edge here** — but it's already captured by the
   `trend-following` skill and MTUM; note MTUM is long-only and gives no crash protection (it fell
   with the market in 2020).

## The named strategies (rule, ETF, honest evidence)

| Strategy | Rule | ETF (inception) | Beats S&P? |
|----------|------|-----------------|------------|
| **Magic Formula** (Greenblatt) | rank by earnings yield (EBIT/EV) + return on capital; buy top 20-30 | no clean ETF; DEEP (deep-value cousin) | strong in book (1988-04) but small/mid + turnover; replications modest |
| **Acquirer's Multiple** (Carlisle) | cheapest EV/EBIT only (drop the quality screen) | ZIG (2019) | EV/EBIT is the best single value ratio academically; brutal 2017-20 |
| **Piotroski F-Score** | 9-pt fundamental quality filter on *cheapest* B/M quintile | (filter, not an ETF) | +23%/yr 1976-96 in paper; **decayed in large caps** |
| **Morningstar moat + fair value** | wide-moat names, cheapest vs analyst fair value | **MOAT (2012)** | **~tie / slight lag** (≈13.98% vs SPY 14.41%) |
| **FCF yield "cash cows"** | top 100 Russell-1000 by FCF/EV | COWZ (2016) | beat R1000 Value; **+0.2% in 2022 vs S&P −18%**; energy/cyclical tilt |
| **Quality** | high ROE, low leverage, low earnings variability | QUAL (2013), SPHQ (2005) | ~matched index; edge is *risk-adjusted*, not absolute |
| **Shareholder yield** (O'Shaughnessy) | dividends + net buybacks (+ debt paydown) | SYLD (2013) | beats pure dividend yield; value/quality tilt |
| **Dividend growth/quality** | long dividend history + FCF/ROE screen | SCHD (2011), DGRO, NOBL | trailed S&P on total return; defensive/income |
| **GARP** | P/E ÷ expected growth (PEG ~1) | thin products | mixed/weak; garbage-in from estimate errors |

**SPIVA reality check:** over **15 years, >90% of US large-cap active funds lag the S&P 500**, and
**0 of 22 US equity categories** had a majority of managers beat their benchmark over 15 years.
Past winners rarely persist. The factor *premia* (value/quality/profitability/shareholder yield) are
real and academically documented, but each has multi-year droughts, and the **live ETFs that
implement them mostly matched or slightly lagged a cheap S&P over the last decade** because that
decade was dominated by a handful of mega-cap growth names.

## "Is it going to use Morningstar reports to pick stocks?" — the data reality

Short answer: **practically, no — you can't get Morningstar's fair-value/moat data cheaply, and even
if you could, MOAT shows it wouldn't beat the index.**

| Source | Provides | Cost | Safe for backtests? |
|--------|----------|------|---------------------|
| **Morningstar Direct / Web Services** | fair value, moat, star ratings, fundamentals | **institutional, ~$17-30k+/seat/yr**; retail "Investor" $199-249/yr = reports only, **no API** | historical point-in-time FV not exposed; not retail-accessible |
| **yfinance** | current P/E, P/B, ROE, statements (~4 yrs) | free | **NO** — current/restated values, delisted names dropped (look-ahead + survivorship) |
| **SEC EDGAR companyfacts** | all XBRL facts, as-filed since ~2009 | **free** | **YES** (genuinely as-filed/point-in-time); you normalize concepts + map ticker→CIK |
| **Financial Modeling Prep / Tiingo / SimFin** | statements, ratios, EV/EBIT, FCF | ~$22-99/mo | mostly **restated** → verify PIT before trusting |
| **Sharadar SF1** (Nasdaq Data Link) | 25 yrs US fundamentals, ~10k delisted firms, PIT + historical index members | ~$100-150/mo | **YES — best-in-class** (point-in-time, survivorship-free) |

**The two silent killers of fundamental backtests** (which the repo's old price-proxy "Morningstar"
backtest fell into): **look-ahead bias** (using today's/restated fundamentals on a past date) and
**survivorship bias** (testing only still-listed / current index members). Avoid both by using a
**point-in-time, survivorship-safe** DB (Sharadar) for research; yfinance/FMP are fine for *live*
screening only.

**Practical conclusion for the fund:** don't license Morningstar. If you ever run a fundamental
sleeve, **approximate moat/quality with computable proxies** (sustained high ROIC, gross
profitability, low capital intensity, pricing-power margins) on point-in-time data, and make it clear
the backtest gate (`.agents/skills/analyse-fundamental`) before any capital. The default remains the cheap
ETF.

**Even if you already have a Morningstar account:** use it only as a *manual context lens* (a
quality/valuation gut-check on individual names), never as automated infrastructure. Its ratings are
**public → already in the price** (semi-strong EMH; Bogle's *Common Sense Investing*, Malkiel's
*Random Walk*), which is precisely why the productized version (MOAT ETF) lagged SPY. And your
account only shows *today's* rating — no point-in-time history — so a Morningstar-driven screen can
never clear the backtest gate. It's a sanity-check, not a strategy.

## Caveats
- Strategy ETFs include real expense ratios but not the investor's trading costs/taxes.
- Each ETF is judged over its own window vs SPY in that window; rows aren't cross-comparable (RPV/SPHQ
  include the GFC, the 2013 cohort doesn't).
- ETFs approximate (not exactly replicate) the pure academic strategies (Magic Formula, Piotroski).
- See `fundamental_screens_summary.txt` and `report/img/fundamental_screens_backtest.png`.

## Sources
`backtests/fundamental_screens_backtest.py` (this repo); VanEck MOAT, Pacer COWZ, Invesco RPV/SPHQ, iShares
VLUE/QUAL/MTUM/USMV, Schwab SCHD, ProShares NOBL fact sheets; S&P SPIVA scorecards.
