# 03 — Backtest Evidence: Why Not Just S&P/QQQ?

*Results from `backtests/crash_protection_backtest.py` in this repo. $1,000,000 start,
2000-01-01 → 2026-05-27. Total-return data (Vanguard index mutual funds + gold
futures + a T-bill cash index). Educational; see caveats.*

## Full period 2000-2026

| Strategy | CAGR | Sharpe | Sortino | Max DD | Calmar | Final $ |
|----------|:----:|:------:|:-------:|:------:|:------:|:-------:|
| S&P 500 Buy&Hold | 8.3% | 0.38 | 0.48 | **−55.3%** | 0.15 | $8.1M |
| Nasdaq-100 (QQQ) Buy&Hold | 8.7% | 0.35 | 0.46 | **−83.0%** | 0.11 | $9.1M |
| 60/40 (S&P/LT Bond) | 7.4% | 0.49 | 0.66 | −30.3% | 0.24 | $6.5M |
| Permanent Portfolio | 7.2% | **0.69** | **0.95** | **−15.8%** | **0.46** | $6.3M |
| Golden Butterfly | 8.0% | 0.67 | 0.90 | −21.7% | 0.37 | $7.6M |
| All-Weather (proxy) | 7.3% | 0.65 | 0.92 | −23.6% | 0.31 | $6.4M |
| Dual Momentum (GEM) | **9.9%** | 0.49 | 0.65 | −33.8% | 0.29 | **$12.0M** |
| Trend-Following S&P (200d) | 9.1% | 0.57 | 0.63 | −23.0% | 0.39 | $9.9M |

**Read this carefully.** Over a full 26-year cycle, the all-equity portfolios did **not** win
on risk-adjusted terms. QQQ has the highest CAGR-ish but the **worst Sharpe (0.35)** and an −83%
drawdown. The Permanent Portfolio earned nearly the same money as the S&P with **less than a third
of the drawdown** and nearly double the Sharpe. Trend-following and dual momentum *beat* buy-and-hold
outright with lower drawdowns — because they sidestepped the lost decade.

## The "lost decade" 2000-2009 — the heart of the matter

| Strategy | CAGR | Total | Max DD |
|----------|:----:|:-----:|:------:|
| S&P 500 Buy&Hold | −0.9% | **−9.0%** | −55.3% |
| Nasdaq-100 (QQQ) | −6.8% | **−50.3%** | −83.0% |
| 60/40 | +3.3% | +38.4% | −30.3% |
| Permanent Portfolio | +6.9% | +94.2% | −15.8% |
| Golden Butterfly | +7.4% | +104.4% | −21.7% |
| All-Weather | +6.9% | +94.3% | −14.3% |
| Dual Momentum (GEM) | +9.9% | +155.7% | −29.7% |
| Trend-Following S&P (200d) | +8.0% | +115.3% | −11.1% |

**If you had lump-summed $1M into the S&P at the 2000 top, you had *less* money 10 years later.**
QQQ holders were down 50%. Meanwhile every diversified/trend strategy roughly *doubled*. This is the
single most important table in the repo: **a bursting concentration bubble can erase a decade**, and
diversification + trend is how you avoid it — *without* having to call the top.

## Crisis windows — total return & max drawdown

**Dot-com bust (2000-03-24 → 2002-10-09):**
| | Total Return | Max DD |
|--|:--:|:--:|
| S&P 500 | −47.4% | −47.5% |
| QQQ | **−82.9%** | −83.0% |
| Permanent Portfolio | **+2.5%** | −5.9% |
| Golden Butterfly | +3.5% | −10.3% |
| All-Weather | +5.7% | −6.4% |
| Dual Momentum | +20.5% | −29.7% |
| Trend-Following 200d | −4.0% | −11.1% |

**Global Financial Crisis (2007-10 → 2009-03):** S&P −55%, QQQ −52%, Permanent −6%, All-Weather −7%,
Dual Momentum −2%, Trend −5.7%.

**COVID (2020-02-19 → 2020-03-23):** S&P −34%, QQQ −28%, Permanent −6%, All-Weather −5%, Trend −13%.
*Note:* Dual Momentum was caught long (−34%) — the **fast V-shape that breaks monthly trend signals**.

**2022 stocks+bonds (2022-01 → 2022-10):** S&P −25%, QQQ −34%, **60/40 −26% (bonds didn't help)**,
Permanent −14%, Golden Butterfly −15%, Trend −15%. *The 60/40 / risk-parity failure is visible here.*

## What the evidence says

1. **Concentration + valuation = fat left tail.** The S&P's −55% and QQQ's −83% max drawdowns are the
   risk you're underwriting at CAPE ~41 with ~40% top-10 concentration (note 01).
2. **You don't need to predict the crash.** Mechanical diversification (Permanent/Golden/All-Weather)
   and trend rules cut drawdowns to −10% to −24% **without any market call.**
3. **No single hedge is enough.** 2020 broke trend (too fast); 2022 broke 60/40/risk-parity (inflation).
   Only a *combination* of orthogonal hedges was robust across all four windows.
4. **The cost is real:** in the 2009-2026 bull, buy-and-hold S&P/QQQ blew the doors off (S&P +1398%,
   QQQ +3187% vs Permanent +282%). Defense underperforms in bull markets — that's the premium you pay.
   The right mix depends on how much bull-market upside you'll trade for crash survival (note 08).

## Caveats
- Mutual-fund proxies (VFINX/VUSTX/VISVX/VFITX) are total-return; gold (GC=F) has no yield so price = TR.
- Gold futures data starts 2000-08-30, so gold sleeves miss the first ~5 months of the dot-com decline
  (results for those sleeves are if anything *conservative* for the dot-com window).
- CASH accrues a piecewise-constant T-bill estimate, not actual prints. No transaction costs/taxes.
- Static portfolios rebalance annually; Dual Momentum & Trend trade monthly (modest turnover).
- The 2000-2009 all-weather edge benefited from the bond + gold bull markets, which start from a
  *lower-yield* base today — don't assume the same bond tailwind repeats. (This is exactly why note 08
  leans on *trend + gold + low-vol* rather than just long bonds.)
- See also the prior-session backtests (`backtests/era_2005_2020_backtest.py`, `backtests/tldr_chart.py`) and `AGENTS.md`
  for the full strategy index and known biases (survivorship in hindsight-picked universes, etc.).
