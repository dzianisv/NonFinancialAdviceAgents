# Strategy v2 — Beat the index by selection

> **Status: superseded by [v3](v3-bubble-aware-all-weather.md).** Educational analysis, not advice.

## The question

If we're worried about cap-weight S&P/QQQ, can we just **pick better** — tilt into a factor or
strategy that beats the index, ideally with less downside? We tested the whole menu: classic factors
(value, quality, momentum, low-vol, dividends), sector rotation, and the "edge" signals people claim
beat the market (congressional trades, insider buying, post-earnings drift, social-media momentum,
the options wheel).

## What we tested

Two layers:

1. **DIY strategy backtests** (`backtests/`): `value_factor_backtest.py`, `quality_factor_backtest.py`,
   `momentum_backtest.py`, `sector_rotation_backtest.py`, `congressional_backtest.py`,
   `insider_backtest.py`, `pead_backtest.py`, `social_momentum_backtest.py`, `wheel_strategy_backtest.py`,
   `tech_concentration_backtest.py`, `morningstar_backtest.py`, plus multi-era tests
   (`era_2005_2020_backtest.py`) and a master comparison (`tldr_chart.py`).
2. **The clean test** (`backtests/fundamental_screens_backtest.py`): the *investable* version of each
   real methodology — strategy ETFs whose index rules **are** the screen, applied live in real time.
   This avoids the two silent killers of DIY fundamental backtests: **look-ahead bias** (using today's
   restated fundamentals on a past date) and **survivorship bias** (testing only still-listed names).

## Result: selection mostly doesn't beat the index

Each ETF vs SPY over its own full live history (`fundamental_screens_backtest.py`):

| Methodology (ETF) | CAGR | SPY CAGR | Beat? | Sharpe | SPY Sharpe |
|---|:--:|:--:|:--:|:--:|:--:|
| Morningstar wide-moat + fair value (MOAT) | 13.5% | 14.7% | no | 0.70 | 0.79 |
| FCF yield "cash cows" (COWZ) | 12.8% | 15.4% | no | 0.61 | 0.77 |
| S&P 500 Pure Value (RPV) | 9.2% | 11.2% | no | 0.40 | 0.54 |
| MSCI Value (VLUE) | 13.7% | 14.8% | no | 0.68 | 0.78 |
| S&P 500 Quality (SPHQ) | 10.1% | 11.1% | no | 0.49 | 0.54 |
| MSCI Quality (QUAL) | 13.6% | 14.2% | no | 0.72 | 0.75 |
| **MSCI Momentum (MTUM)** | **16.3%** | 14.8% | **YES** | 0.76 | 0.78 |
| Quality Dividend (SCHD) | 13.3% | 15.3% | no | 0.76 | 0.82 |
| Dividend Aristocrats (NOBL) | 10.2% | 14.4% | no | 0.57 | 0.76 |
| Min Volatility (USMV) | 11.7% | 15.3% | no | 0.74 | 0.82 |

**Only 1 of 10 beat SPY on return (momentum); 0 of 10 beat it on Sharpe** — including MOAT, the ETF
that *literally* implements Morningstar's fair-value + moat stock-picking. This matches **SPIVA**:
>90% of US large-cap active funds lag the index over 15 years. The exotic signals (congressional,
insider, social, wheel) were noisier and weaker still. Full detail:
[`../research/09-stock-selection-evidence.md`](../research/09-stock-selection-evidence.md).

## But the screens DO add downside defense

| Crisis | SPY | Best defensive screens |
|--------|:---:|------------------------|
| **2022 bear** | −24.5% | COWZ −7.6%, RPV −11%, SCHD −15%, NOBL −16%, USMV −17% |
| 2023-26 AI bull (max DD) | −19% | USMV −9% |

So value/quality/low-vol/dividend screens are **defensive sleeves, not alpha engines**: they lose
less in inflation-driven equity bears and grind with lower volatility — at the cost of **lagging
badly in a mega-cap bull** (MOAT +62% vs SPY +106% in 2023-26).

## Why it was superseded

- **The premise failed.** "Pick better than the index" is a low-base-rate bet; the productized
  version of every method we'd actually use mostly lagged a cheap S&P over the last decade.
- **Even the one winner (momentum) gives no crash protection** — MTUM fell *with* the market in 2020.
  It's long-only equity beta with a tilt, not a hedge.
- The Morningstar question got a definitive answer: **don't license/scrape it.** Its ratings are
  public → already in the price (semi-strong EMH), which is exactly why MOAT lagged. Use it, if at
  all, as a manual context lens — never as automated infrastructure (see research note 09).

**What survived into v3:** (1) the defensive factor ETFs (USMV/QUAL/COWZ/AVUV) become the *defensive
equity sleeve*, where they earn their keep; (2) **momentum is absorbed as a trend/regime overlay**
(the `trend-following` skill) rather than a stock-picker; (3) the hard lesson — *the edge is not
selection* — is what points v3 at structure instead.

## Provenance
All `*_backtest.py` in `backtests/` and their `backtests/results/` summaries; the clean test is
`backtests/fundamental_screens_backtest.py`; the synthesis is `research/09-stock-selection-evidence.md`.
