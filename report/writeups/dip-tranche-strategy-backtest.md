# Dip-Tranche Strategy: S&P 500, Nasdaq-100, International — Backtest 2020-2026

> Source: [https://telegra.ph/Dip-Tranche-Strategy-SP-500-Nasdaq-100-International--Backtest-20202026-05-28](https://telegra.ph/Dip-Tranche-Strategy-SP-500-Nasdaq-100-International--Backtest-20202026-05-28)
> Saved: 2026-05-28

---

> Disclaimer: This report is for educational and analytical purposes only. Nothing here constitutes financial advice. Past backtest performance does not guarantee future results. Consult a licensed fiduciary advisor before making any investment decisions.

Source code & data: [github.com/dvashchuk/backtest](https://github.com/dvashchuk/backtest)


### TL;DR

> Strategy: Split $1M into three buckets — 50% lump-sum on day one, 30% DCA over 18 months, 20% held in a money-market fund as a tiered dip reserve. Deploy the reserve in tranches as the market falls: Tier 1 at −7/−8.5/−10%, Tier 2 at −12/−14/−16%, Tier 3 at −20/−25/−30% from the 52-week high. QQQ thresholds are scaled ×1.4 for its higher volatility.

Does it beat lump-sum? Rarely on raw CAGR — but that's not the point.

- VOO (S&P 500): Strategy 15.1% CAGR vs Lump Sum 15.8%. Lump sum wins, but strategy's max drawdown is −22.5% vs −27.4% — nearly 5pp shallower.
- QQQ (Nasdaq-100): Strategy 19.6% vs Lump Sum 21.7%. Similar story — lump sum wins on returns, strategy cushions the −34% QQQ crash.
- VXUS (International): Strategy 10.6% vs Lump Sum 10.2%. Strategy wins — slower international recoveries reward tiered entry.
- Across 20 starting quarters (2020–2024): lump sum wins 45/60 combinations. Strategy's edge is consistent drawdown reduction, not alpha generation.
- The 2022 bear market was the strategy's best showcase — all tiers deployed as markets ground down −25% to −38%, with every tranche profitable by 2023.
- The COVID crash (Mar 2020) was the worst case — too fast; the lump-sum buyer caught the full recovery from day one.

Bottom line: Use this strategy if you want shallower drawdowns and can tolerate slightly lower expected returns. The 20% dip reserve earns ~4% in a money-market fund while waiting — the opportunity cost is real but bounded. It is a risk-management tool, not an alpha tool.

---


### Executive Summary

This report backtests a tiered "dip-buying" deployment strategy against two benchmarks (lump-sum and pure DCA) across three ETFs — VOO (S&P 500), QQQ (Nasdaq-100), and VXUS (Total International) — using weekly closing data from January 2020 through May 2026.

The core finding: the strategy did not beat lump-sum on raw returns for US equities in this particular window (which started just before the fastest crash-and-recovery in market history), but it consistently reduced maximum portfolio drawdown by 3–5 percentage points and outperformed lump-sum on VXUS, where recoveries are slower. The strategy is best understood as a risk-management tool that trades some upside for shallower drawdowns and psychological staying power during corrections.

---

### Strategy Overview

#### The 50 / 30 / 20 Allocation

A $1,000,000 portfolio is divided into three buckets at inception:

- Bucket 1 — Foundation (50% = $500K): deployed as a lump sum on day one. Captures upside if the market continues higher; accepts the risk of buying near a local top.
- Bucket 2 — DCA (30% = $300K): deployed in equal weekly instalments over 18 months (~$3,840/week). Smooths cost basis, removes decision fatigue, keeps capital working.
- Bucket 3 — Dip Reserve (20% = $200K): held in a money-market fund earning ~4% annualised while waiting for drawdown triggers. Deployed in tranches as the market falls.

#### Tiered Dip Reserve — How It Works

The reserve is split into three tiers based on drawdown severity from the rolling 52-week high. Each tier has four sub-tranches: three price-triggered and one time-triggered (fires if price remains below the tier entry threshold for N weeks without recovering).

```
VOO / VXUS triggers (β-mult 1.0)         QQQ triggers (β-mult 1.4)
─────────────────────────────────         ────────────────────────────
Tier 1  20% of reserve  ($40K)            Tier 1  20%  ($40K)
  T1a   -7.0%  from 52w high  $10K          T1a  -9.8%            $10K
  T1b   -8.5%                 $10K          T1b -11.9%            $10K
  T1c  -10.0%                 $10K          T1c -14.0%            $10K
  T1d   time (2 wks below T1a)$10K          T1d  time             $10K

Tier 2  30% of reserve  ($60K)            Tier 2  30%  ($60K)
  T2a  -12.0%                 $15K          T2a -16.8%            $15K
  T2b  -14.0%                 $15K          T2b -19.6%            $15K
  T2c  -16.0%                 $15K          T2c -22.4%            $15K
  T2d   time (3 wks below T2a)$15K          T2d  time             $15K

Tier 3  50% of reserve ($100K)            Tier 3  50% ($100K)
  T3a  -20.0%                 $25K          T3a -28.0%            $25K
  T3b  -25.0%                 $25K          T3b -35.0%            $25K
  T3c  -30.0%                 $25K          T3c -42.0%            $25K
  T3d   time (4 wks below T3a)$25K          T3d  time             $25K
```

#### Guard Rules

- Cooldown: minimum 3 weeks between any two sub-tranche fills — prevents panic-buying every bar on the way down.
- Re-arm: if the market recovers above the re-arm threshold (-5% from new 52w high for VOO/VXUS, -7% for QQQ), all fired tiers reset. Capped at 2 re-arms per calendar year to avoid chasing noise.
- MM yield: idle reserve earns 4% annualised (money-market rate), accrued weekly — modelled conservatively.
- Triggers use weekly closes, not intraday wicks, to avoid flash-crash false triggers.

#### Why Different Triggers for QQQ?

QQQ has roughly 1.4× the volatility of VOO. Its 2022 drawdown (-38%) was ~13 percentage points deeper than VOO's (-25%) in the same event. Using VOO triggers on QQQ would fire Tier 3 too easily, depleting the reserve during routine corrections. Scaling all thresholds by 1.4× keeps the tier system calibrated to the asset's actual behaviour.

---

### Backtest Parameters

```
Period:          2020-01-01 → 2026-05-27  (6.4 years)
Data:            Weekly closes, adjusted for splits and dividends
Source:          Yahoo Finance via yfinance 1.4.0
Starting capital: $1,000,000
Benchmarks:
  Lump Sum  — 100% deployed on the first bar (2020-01-01)
  DCA 18m   — equal weekly instalments over 18 months
52-week high:    rolling max of prior 52 weekly closes
MM yield:        4.00% p.a. accrued weekly on reserve cash
Commissions:     not modelled (negligible for ETFs at this scale)
Taxes:           not modelled (tax wrapper dependent)
```

---

### VOO — Vanguard S&P 500 ETF

![VOO: price with entry points (top), portfolio value comparison (middle), drawdown vs tier triggers (bottom)](https://i.imgur.com/vAVtqEm.png)
*VOO: price with entry points (top), portfolio value comparison (middle), drawdown vs tier triggers (bottom)*

```
Metric                    Strategy    Lump Sum    DCA 18m
─────────────────────────────────────────────────────────
End value ($)           2,465,730   2,553,705  2,388,899
Total return              +146.6%     +155.4%    +138.9%
CAGR                       15.1%       15.8%      14.6%
Max portfolio drawdown    -22.5%      -27.4%     -24.3%
─────────────────────────────────────────────────────────
Strategy detail:
  Avg cost basis          $280.15     (last price $689.96)
  Unrealised gain/share   +146.3%
  Dip sub-tranches fired  18  (T1:12  T2:5  T3:1)
  Reserve deployed        $214,646 / $200,000  (100%)
```

VOO fired Tier 1 repeatedly through the COVID crash (Feb–Jun 2020) and again through the 2022 Fed-tightening bear market. Tier 2 filled across mid-2020 and mid-2022. Tier 3 fired just once: the Sept 2022 capitulation week at $329. The reserve was fully deployed by Q4 2022 — exactly the intended behaviour. Lump-sum edged the strategy by ~0.7% CAGR because the 2020 crash recovered so quickly that later tranches bought at higher prices than the initial lump-sum entry.

### QQQ — Invesco Nasdaq-100 ETF

![QQQ: price with entry points (top), portfolio value comparison (middle), drawdown vs tier triggers (bottom)](https://i.imgur.com/70ceMQc.png)
*QQQ: price with entry points (top), portfolio value comparison (middle), drawdown vs tier triggers (bottom)*

```
Metric                    Strategy    Lump Sum    DCA 18m
─────────────────────────────────────────────────────────
End value ($)           3,151,199   3,511,861  2,821,844
Total return              +215.1%     +251.2%    +182.2%
CAGR                       19.6%       21.7%      17.6%
Max portfolio drawdown    -31.2%      -34.3%     -34.3%
─────────────────────────────────────────────────────────
Strategy detail:
  Avg cost basis          $226.22     (last price $729.45)
  Unrealised gain/share   +222.4%
  Dip sub-tranches fired  17  (T1:11  T2:4  T3:2)
  Reserve deployed        $219,784 / $200,000  (100%)
```

QQQ had the highest absolute returns across the period (+251% lump-sum, +215% strategy), but also the deepest drawdowns (-34%). The strategy softened the portfolio drawdown to -31.2% versus -34.3% for lump-sum. Tier 3 fired twice in 2022 (the QQQ bear market bottomed at -38% from its high). The 2024 yen-carry unwind and 2025 tariff selloff both triggered Tier 1 buys that were profitable. The lump-sum gap is wider here than VOO because QQQ compounded faster — earlier capital worked harder for longer.

### VXUS — Vanguard Total International ETF

![VXUS: price with entry points (top), portfolio value comparison (middle), drawdown vs tier triggers (bottom)](https://i.imgur.com/DDabFAP.png)
*VXUS: price with entry points (top), portfolio value comparison (middle), drawdown vs tier triggers (bottom)*

```
Metric                    Strategy    Lump Sum    DCA 18m
─────────────────────────────────────────────────────────
End value ($)           1,909,517   1,860,850  1,871,948
Total return               +91.0%      +86.1%     +87.2%
CAGR                       10.6%       10.2%      10.3%
Max portfolio drawdown    -26.6%      -29.3%     -29.3%
─────────────────────────────────────────────────────────
Strategy detail:
  Avg cost basis           $45.36     (last price $85.85)
  Unrealised gain/share    +89.3%
  Dip sub-tranches fired  16  (T1:8  T2:5  T3:3)
  Reserve deployed        $215,663 / $200,000  (100%)
```

VXUS is the only symbol where the dip-tranche strategy beat both benchmarks on CAGR (+10.6% vs +10.2% lump-sum and +10.3% DCA). International markets recover more slowly from corrections — the 2022 bear market on VXUS was prolonged, allowing Tier 2 and Tier 3 tranches to accumulate at $40–$46 before the eventual recovery to $85+. This is precisely the environment the strategy is designed for: slow, grinding drawdowns with extended bottoms.

---

### Summary: All Symbols

```
Symbol   CAGR   Total Ret   End Value    Max DD   Reserve
──────   ────   ─────────   ─────────    ──────   ───────
VOO     15.1%    +146.6%   $2,465,730   -22.5%    100%
QQQ     19.6%    +215.1%   $3,151,199   -31.2%    100%
VXUS    10.6%     +91.0%   $1,909,517   -26.6%    100%

Benchmarks (same period, lump-sum):
VOO     15.8%    +155.4%   $2,553,705   -27.4%
QQQ     21.7%    +251.2%   $3,511,861   -34.3%
VXUS    10.2%     +86.1%   $1,860,850   -29.3%
```

---

### Key Takeaways

- Lump-sum wins on raw returns in strong bull markets — Vanguard's research holds up here. If you started in 2020 with perfect hindsight that markets would recover quickly, you'd have gone all-in. Nobody has that hindsight.
- The strategy's edge is risk management, not alpha. It consistently reduced max portfolio drawdown by 3–5 percentage points versus lump-sum — meaningful when you're watching a $1M portfolio become $650K.
- VXUS is the natural home for this strategy. International equities have slower, deeper drawdowns with longer recovery cycles — exactly what tiered entry is built for.
- The 2022 bear market was the strategy's best showcase: Tier 1 fired 5–12 times per symbol as markets ground down, Tier 2 accumulated in the -12% to -16% zone, and Tier 3 deployed at the capitulation lows in Sep–Oct 2022. Every tranche was profitable by end of 2023.
- The COVID crash (Mar 2020) was the worst case for this strategy: too fast and too deep. Tier 1 fired near the top of the decline, Tier 2 near the middle, and then the market recovered before Tier 3 could deploy at the real bottom. The lump-sum buyer caught the full recovery from day 1.
- QQQ's higher triggers (-9.8% / -16.8% / -28%) were correct: without recalibration, the VOO triggers would have exhausted the reserve on routine Nasdaq noise. Always scale triggers to each asset's volatility.
- Re-arming matters: the cap of 2 re-arms per year prevented the strategy from being triggered every few weeks during 2022's volatile sideways grind.

---

### Automating the Strategy

The companion Python script (backtest.py) implements the full engine. To run it live as a daily monitor:

- Pull weekly closes each Friday after market close via yfinance or a paid source (Alpha Vantage, Polygon.io for reliability).
- Compute rolling 52-week high and current drawdown percentage.
- Check which sub-tranches should fire per the trigger table above.
- Send an alert (Telegram bot, email, or Slack) with the triggered tranche, recommended dollar amount, and current drawdown context.
- Place limit orders manually or via broker API (Alpaca or IBKR) — notification-only mode is strongly recommended until you have 6+ months of live observation.

A TradingView Pine Script v6 strategy visualising all tier trigger lines, entry markers, and a live status panel is available as a companion asset.

---

> Full disclaimer: This backtest was conducted using publicly available historical data. Results are hypothetical — they do not account for taxes, bid/ask spreads, slippage, or behavioural drag (the tendency to deviate from rules under stress). Past performance does not predict future returns. The authors are not licensed financial advisors. This document is shared for educational purposes. Before deploying real capital, consult a fee-only fiduciary CFP and a CPA familiar with your tax situation.

---

### Robustness Check: Does the Starting Date Matter?

A single backtest starting January 2020 is not representative — it happens to begin just before the fastest market crash-and-recovery in modern history. To stress-test the strategy, we ran it starting on the first trading day of every quarter from Q1-2020 through Q4-2024 (20 start dates per symbol), all ending on 2026-05-27.

#### VOO — S&P 500

![VOO: total return % and CAGR advantage (strategy vs lump-sum) across all 20 start quarters](https://i.imgur.com/6Pm7ehP.png)
*VOO: total return % and CAGR advantage (strategy vs lump-sum) across all 20 start quarters*

#### QQQ — Nasdaq-100

![QQQ: total return % and CAGR advantage across all 20 start quarters](https://i.imgur.com/d9aZmDd.png)
*QQQ: total return % and CAGR advantage across all 20 start quarters*

#### VXUS — Total International

![VXUS: total return % and CAGR advantage across all 20 start quarters](https://i.imgur.com/Kj7c0OL.png)
*VXUS: total return % and CAGR advantage across all 20 start quarters*

#### Summary across all 60 quarter-symbol combinations

```
               Strategy wins   Lump Sum wins   DCA wins
VOO                0 / 20          16 / 20      4 / 20
QQQ                1 / 20          17 / 20      2 / 20
VXUS               3 / 20          12 / 20      5 / 20
─────────────────────────────────────────────────────
Total              4 / 60          45 / 60     11 / 60

Avg CAGR gap (Strategy minus Lump Sum):
  VOO:  −2.58%   QQQ: −3.21%   VXUS: −1.61%
```

#### What this means

- Lump sum wins in trending bull markets — opportunity cost of holding the 20% reserve in cash drags the strategy in most quarters.
- The strategy's edge on VXUS (3 wins) confirms the finding from the main backtest: slower, choppier international recoveries reward tiered entry more than US markets.
- Even starting in bear-market quarters (Q1-22, Q2-22), lump sum often still wins — because lump sum also deploys at depressed prices and rides the same recovery. The strategy only wins when dips extend long enough for the reserve to accumulate at materially lower prices.
- DCA wins in 11/60 cases — specifically when you start right before a significant drawdown (Q3-21 through Q2-22 for VOO), where spreading deployment over 18 months builds a lower cost basis than the strategy's 50% lump-sum on day one.
- The strategy's consistent advantage is max drawdown reduction (−3 to −5 pp vs lump-sum), not CAGR — it is a risk tool, not an alpha tool.

---

Code: [Full backtest source on GitHub →](https://github.com/dvashchuk/backtest)

---

### Experiment 2: Copying Congressional Trades (Pelosi, McCaul, Green)

Insider trading laws don't apply to Congress. The STOCK Act requires disclosure within 45 days. We simulated copying three top traders' disclosed trades with a 30-day execution lag.

Rules: $1M starting capital. Buy each disclosed trade at min(notional, 15% of portfolio). Execute 30 days after trade date. Uninvested cash earns 4% MM yield. No selling.

![Congressional copy strategy vs VOO lump sum / DCA / Dip-Tranche (2020-2026)](https://i.imgur.com/uC7Lae9.png)
*Congressional copy strategy vs VOO lump sum / DCA / Dip-Tranche (2020-2026)*

```
Strategy          Final Value    CAGR    Max DD   Sharpe
-----------------------------------------------------------
McCaul (R-TX)     $4,914,174    28.3%   -43.9%    0.91
Pelosi (D-CA)     $3,196,671    20.0%   -42.7%    0.68
VOO Lump Sum      $2,517,120    15.6%   -27.4%    0.69
Dip-Tranche (ref) $2,461,030    15.2%   -22.5%    ~0.70
VOO DCA           $2,209,643    13.2%   -18.7%    0.71
Green (R-TN)      $2,024,399    11.7%   -26.7%    0.47

```

#### Key findings

- McCaul turned $1M to $4.9M (28.3% CAGR). Bought GOOGL/AMZN/MSFT at the COVID bottom and NVDA in May 2023 just before the AI supercycle.
- Pelosi's 20% CAGR was driven by NVDA (June 2021, Nov 2023) and the CHIPS Act AAPL+NVDA buys.
- Green underperformed plain VOO (11.7% vs 15.6%). Energy overweight dragged; Pfizer bought on vaccine day lost 40% by 2024.
- All congressional portfolios have far worse max drawdowns (-43% to -44%) than the Dip-Tranche strategy (-22.5%).
- Caveat: options (LEAPS/calls) in actual disclosures are not modeled here and would amplify returns further.

---

### Experiment 3: Morningstar-Proxy Screener + Quarterly DCA

We approximated Morningstar's 5-star screener with a simple rule: at each quarter start, select S&P 500 stocks >= 20% below their 52-week high. DCA equal amounts into selected stocks. Compare to VOO DCA.

Universe: 30 liquid S&P 500 stocks across all 11 sectors. 20 starting quarters (Q1-2020 through Q4-2024). $100K capital.

![CAGR advantage (strategy minus VOO DCA) per starting quarter - nearly all negative](https://i.imgur.com/yx6oFPJ.png)
*CAGR advantage (strategy minus VOO DCA) per starting quarter - nearly all negative*

```
       Start | Strat CAGR | VOO CAGR | Wins? | Avg Stocks
---------------------------------------------------------
  2020-01-01 |    14.63%  |  15.54%  |   NO  |    5.1
  2020-10-01 |    16.95%  |  15.99%  |  YES  |    4.7  <- only win
  2023-04-01 |    11.99%  |  22.83%  |   NO  |    2.1
  2024-01-01 |    13.82%  |  22.55%  |   NO  |    0.5
  ... (strategy wins 1 of 20 quarters; avg lag vs VOO: -4.26 pp CAGR)
```

#### Why it fails

- Wins 1 of 20 start quarters. Average CAGR drag vs VOO DCA: -4.26 percentage points.
- Screener dried up after 2022. From 2023 onward, avg stocks selected fell to 0.5-2 per quarter as mega-cap tech recovered above 52-week highs. Portfolio sat in 4% MM while VOO returned 20-25% CAGR.
- Value trap effect: stocks >= 20% below highs often stay there (DIS, T, PFE). Real Morningstar adds DCF fair value + moat ratings - price dip alone is noise.
- Verdict: the quality/valuation filter does the heavy lifting in Morningstar's methodology. A pure price-dip proxy does not replicate it.

---

### What's Next: AI/News-Driven Stock Selection (Research Survey)

Based on research across r/algotrading, Hacker News, and academic papers. Ranked by strength of evidence.

#### 1. GPT News Headline Sentiment

Score news headlines with GPT-4 (positive/negative/neutral per stock). Key paper: [Lopez-Lira & Tang 2023 (arXiv:2304.07619)](https://arxiv.org/abs/2304.07619) - ~90% portfolio-day hit rate for initial reaction. Community verdict: real signal in 2022-2023 but the paper itself notes 'returns decline as LLM adoption rises.' Likely crowded out now.

#### 2. PEAD + LLM (Most backtestable - recommended)

Post-Earnings Announcement Drift is the most academically solid foundation (Ball & Brown 1968). Modern twist: score SEC 8-K filings with GPT-3.5 within 60 min of release. Entry: stock moves <1.5% intraday despite strongly positive score AND EPS beat. Hold 5 days. Filter to small-cap. Free data: SEC EDGAR RSS + Alpha Vantage earnings.

#### 3. FinBERT on Earnings Call Transcripts

Apply [FinBERT (ProsusAI, 2.1k stars)](https://github.com/ProsusAI/finBERT) to management guidance sentences in quarterly 8-K transcripts. Score sentiment delta vs prior quarter. Long top-quintile, short bottom-quintile, monthly rebalance. Less crowded than headline sentiment. Li (2010) showed most alpha eroded post-2018 - treat as a screening layer, not standalone signal.

#### 4. Reddit/Social Sentiment (Largely played out)

Aggregate WSB mention counts + sentiment. Best on meme/small-cap and crypto. Tools: Tickerrain (r/algotrading: 922 upvotes). Community: mostly played out for equities since GME 2021.

#### 5. Multi-Agent LLM Consensus (Experimental - caution)

Run GPT-4, Claude, Gemini on the same news; trade on consensus. Warning: [arXiv:2311.07590](https://arxiv.org/abs/2311.07590) showed a GPT-4 autonomous trading agent committed simulated insider trading and hid it from its manager under performance pressure. No unmonitored live access recommended.

#### Top open-source repos

- [FinGPT (20.3k stars)](https://github.com/AI4Finance-Foundation/FinGPT)
- [FinRL - DRL trading (15.3k stars)](https://github.com/AI4Finance-Foundation/FinRL)
- [pybroker - ML backtesting with walkforward](https://github.com/edtechre/pybroker)

Bottom line: Academic signal is real. Practical alpha after costs, slippage, and crowding is unproven for retail. Best use today: LLMs as a screening/filtering layer, not autonomous trade execution.

---

### Congressional Trades: Does Entry Timing Matter?

We re-ran the congressional copy strategy for all 20 quarterly start dates (Q1-2020 through Q4-2024), each time only copying trades disclosed AFTER the entry date. This reveals how dependent each politician's returns are on the COVID-bottom trades you would have missed if you started later.

![CAGR per starting quarter for Pelosi / McCaul / Green vs VOO lump-sum benchmark](https://i.imgur.com/mnGTJDz.png)
*CAGR per starting quarter for Pelosi / McCaul / Green vs VOO lump-sum benchmark*

```
              Beats VOO   Alpha half-life   COVID trades critical?
──────────────────────────────────────────────────────────────────
Pelosi        14 / 20     Q3-2023           NO — NVDA 2021+2023
              (70%)       is the edge       are a second engine

McCaul        14 / 20     Q3-2023           YES — March 2020
              (70%)                         bottom buys core alpha;
                                            post-2022 avg: -3.0 pp

Green          3 / 20     Never reliable    N/A — energy/pharma
              (15%)                         overweight drags all
                                            regimes except 2021

```

#### Key insight: Q1-2022 entry test

- Pelosi from Q1-2022: +43.6% CAGR vs 13.1% VOO. The NVDA buys (July 2022 CHIPS Act, Nov 2023 AI boom) are fully captured — COVID trades were a bonus, not the core.
- McCaul from Q1-2022: +29.4% CAGR vs 13.1% VOO. Still wins, but his post-2022 trade quality declines — buying META/GOOGL dips that recovered slowly vs NVDA's vertical move.
- Both Pelosi and McCaul lose to VOO decisively from Q1-2024 onward. The NVDA trade in Nov 2023 is the last major alpha-generating event in the dataset.
- Green beats VOO in Q1-2022 by barely 1pp — not meaningful. Energy stocks rallied with the Ukraine war oil spike but mean-reverted by 2023.

---

### Experiment 4: Combined Congress Portfolio — Does Diversifying Politicians Help?

Instead of copying one politician, we merged all three (Pelosi + McCaul + Green) into a single portfolio. Each trade sized at 1/3 the original notional, capped at 10% of portfolio. Tested across all 20 quarterly start dates.

![Combined congress portfolio CAGR vs McCaul-only and VOO across 20 start quarters](https://i.imgur.com/a0kLmdI.png)
*Combined congress portfolio CAGR vs McCaul-only and VOO across 20 start quarters*

```
             Combined   McCaul    VOO    Beats VOO  Trades
--------------------------------------------------------------
2020-Q1       21.5%    20.3%    15.5%    YES         41
2021-Q1       26.6%    22.7%    15.1%    YES         29
2022-Q1       31.3%    18.6%    13.0%    YES         20
2023-Q1       26.9%    17.7%    23.0%    YES         11
2023-Q3       17.3%     9.0%    21.7%    NO           7
2024-Q1        9.4%     7.0%    22.5%    NO           4

Avg (20 starts): Combined 22.3% | McCaul 15.8% | VOO 18.5%
Wins vs VOO:     Combined 14/20 | McCaul 10/20
```

#### Key findings

- Combined beats VOO in 14/20 vs McCaul-alone 10/20 — diversifying across all three is strictly better.
- The alpha engine is Pelosi. NVDA positions (2021, 2022, 2023) dominate; McCaul's tech buys amplify.
- LLY (Green's Feb 2023 buy) rose 400%+ on weight-loss drugs — partly rescues Green's energy drag.
- From 2023-Q3 onward all three politicians' trades trail a VOO driven by mega-caps they no longer hold.
- Combining improves avg CAGR by +6.5pp vs McCaul alone at near-identical Sharpe (0.97 vs 0.98).

---

### Experiment 5: Alternative Assets — Gold, Bonds, Bitcoin vs Pure VOO DCA

4 alternative allocation strategies vs VOO DCA baseline across all 20 quarterly starts. Equal quarterly installments, $100K total capital.

![CAGR advantage vs VOO DCA for each alternative allocation across 20 start quarters](https://i.imgur.com/nZsnHlZ.png)
*CAGR advantage vs VOO DCA for each alternative allocation across 20 start quarters*

```
Strategy           Beats VOO  Avg CAGR  vs VOO    Max DD   Sharpe
--------------------------------------------------------------------
VOO DCA (baseline)  ---       12.84%    ---      -11.28%   0.95
Gold hedge 80/20   20/20      13.79%   +0.95pp   -9.37%    1.13
Degen 70/20/10     17/20      14.07%   +1.23pp  -10.53%    0.98
60/40 VOO+TLT       0/20       8.64%   -4.20pp   -7.31%   0.71
All-weather         0/20       8.01%   -4.83pp   -6.62%   0.68

Degen = 70% VOO + 20% GLD + 10% GBTC
All-weather = 30% VOO + 40% TLT + 15% GLD + 15% IEF
```

#### Key findings

- Gold hedge (80% VOO + 20% GLD) wins all 20/20 quarters. Best Sharpe (1.13). Gold's 2022-2025 run made it an alpha source, not just a hedge. Max DD improved 191bp vs pure VOO.
- Degen DCA (70% VOO + 20% GLD + 10% GBTC) has the best raw CAGR (+1.23pp avg) but loses 3 recent quarters — Bitcoin plateaued after the 2024 halving rally.
- 60/40 is a disaster: 0/20 wins, -4.20pp. TLT lost ~50% peak-to-trough as the Fed hiked 525bp. The classic institutional portfolio failed completely in this rate environment.
- All-weather (Dalio 30/40/15/15) is worst: 0/20, -4.83pp. Both bond allocations were dead weight during the rate-hiking cycle.
- Practical takeaway: a simple 80/20 VOO+GLD DCA beats pure VOO in every single entry point tested with a higher Sharpe. The cost is ~0.3pp lower CAGR vs the degen allocation.

---

## Experiment 6: Berkshire 13F Copy (Buffett Follower)

Copy Berkshire Hathaway's top holdings using quarterly 13F disclosures with a 45-day execution lag. Buy-and-hold, $1M starting capital.

![Berkshire 13F copy vs VOO lump sum](https://i.imgur.com/INLX8D2.png)

```
Strategy       CAGR  Sharpe  Max DD
Berkshire 13F  15.8%  0.57  -37.4%
VOO Lump Sum   15.6%  0.62  -34.0%
```

- Barely beats VOO (+0.2pp CAGR) with worse Sharpe and deeper drawdown. Not worth the complexity.
- Buffett sat on cash during COVID while the market ripped — Apple's weight rescued it.
- Congressional insider flow (Pelosi +20%) decisively beats 13F copy.

---

## Experiment 7: Post-Earnings Announcement Drift (PEAD)

Buy S&P 500 stocks that gap up >5% on earnings day. Hold 60 days. Proxy for the academic PEAD effect.

![PEAD gap-up earnings momentum vs VOO](https://i.imgur.com/jwrjwQR.png)

```
Strategy  CAGR  Sharpe  Max DD
PEAD      16.2%  0.57  -47.5%
VOO       15.7%  0.62  -34.0%
```

- +0.5pp CAGR vs VOO but max drawdown -47.5% vs -34%. Risk-adjusted, it loses.
- Real PEAD alpha requires executing within hours of the 8-K. Daily-close proxy dilutes the signal.
- Avg 7.1 simultaneous positions — single-stock concentration drives the outsized drawdown.

---

## Experiment 8: Quality Factor + Low Volatility

Monthly rebalancing into stocks ranked by: 40% 6-month momentum + 30% 12-month momentum + 30% low-vol rank. Top 10/15/20 holdings.

![Quality factor top-15 — best Sharpe of all non-congressional strategies](https://i.imgur.com/nj5vVBg.png)

```
Variant  CAGR   Sharpe  Max DD
Top-10  16.1%   0.78  -20.2%
Top-15  19.0%   0.89  -16.8%  <- best
Top-20  18.2%   0.90  -16.3%
VOO     15.7%   0.62  -34.0%
```

- **Best risk-adjusted result of all non-congressional experiments.** Top-15: 19.0% CAGR, Sharpe 0.89, max DD only -16.8% — half VOO's -34%.
- Nearly matches Pelosi's CAGR (19.0% vs 20.0%) with far better drawdown protection (-16.8% vs -42.7%).
- Fully systematic — no insider info, no fundamentals, just price signals.

---

## Experiment 9: Sector Rotation (ETF Momentum)

Monthly rebalancing across 11 sector ETFs ranked by momentum. Four variants.

![Sector rotation rank-weighted variant achieves 21.2% CAGR](https://i.imgur.com/nWXdv1P.png)

```
Variant            CAGR  Sharpe  Max DD   Final
V1: Top-1 3M      18.9%   0.60  -36.0%  $3.03M
V2: Top-3 EW      20.5%   0.80  -19.8%  $3.29M
V3: Top-3 +ABS    17.2%   0.64  -20.0%  $2.76M
V4: Rank-weighted 21.2%   0.84  -17.7%  $3.43M  <- best
VOO               15.7%   0.62  -34.0%  $2.54M
```

- **Rank-weighted (V4) beats Pelosi on CAGR** with 21.2% and Sharpe 0.84, max DD only -17.7%. Beats VOO on every metric.
- Absolute momentum filter (V3) hurts — rotates to cash too often, missing 2020 and 2023 recoveries.
- Insight: XLK (tech) dominated most of 2020-2024. Systematically overweighting the winning sector wins.

---

## Experiment 10: Price Momentum Stock Picking

Two price-momentum strategies on S&P 500 large caps, monthly rebalancing.

> **Survivorship bias warning:** universe built from 2026 S&P 500 members. Stocks that failed/were removed are excluded. Results are directional only.

![Momentum strategies A/B vs VOO — results are survivorship-biased](https://i.imgur.com/oDqqEqN.png)

```
Strategy              CAGR  Sharpe  Max DD
A: Momentum Screen   33.3%   0.87  -54.0%
B: Vol-Adj Momentum  45.3%   1.14  -49.2%
VOO                  15.7%   0.62  -34.0%
```

- Numbers are inflated — bankrupt/removed stocks excluded. Point-in-time constituent list would reduce returns substantially.
- Max drawdowns -49% to -54% reveal concentrated single-stock risk not in the Sharpe calculation.

---

## Experiment 11: Tech Concentration / Mag7

Concentrate in Magnificent 7 or AI/semiconductor names. Four variants vs VOO and QQQ.

> Same survivorship caveat — returns constructed knowing which 7 companies dominated 2020-2026.

![Mag7 equal-weight and AI/semis concentration vs VOO/QQQ](https://i.imgur.com/7hhJedc.png)

```
Strategy             CAGR  Sharpe  Max DD   Final
VOO                 15.7%   0.62  -34.0%  $2.54M
QQQ                 21.7%   0.75  -35.1%  $3.51M
A: Mag7 EW          38.6%   1.05  -48.4%  $8.08M
B: AI/Semis Mom     46.3%   1.11  -50.8%  $11.4M
C: TQQQ+SMA         39.3%   0.88  -50.8%  $8.35M
D: 80/20 VOO+TQQQ   22.9%   0.71  -42.5%  $3.75M
```

- In real-time you would not have known which 7 companies would dominate. Concentration in AI/semis explains nearly all S&P 500 outperformance since 2023.
- TQQQ (3x QQQ) with 200-day SMA filter still suffers -50% max DD. Daily vol-decay from 3x ETF rebalancing is not fully captured.

---

## Experiment 12: Wheel / Theta Strategy (Covered Calls + CSP)

Simulated monthly 30-delta options on SPY/VOO using Black-Scholes approximation. No real historical options data — directionally illustrative only.

![Wheel strategy: CSP trails badly, covered call overlay beats VOO](https://i.imgur.com/U151oaA.png)

```
Strategy       CAGR  Sharpe  Max DD
CSP only        3.6%  -0.00  -18.2%  — terrible
Covered Call   19.9%   0.83  -25.3%  — beats VOO
Full Wheel     10.4%   0.43  -22.1%  — mediocre
VOO            15.6%   0.69  -27.4%  — benchmark
```

- Covered call overlay: 19.9% CAGR, Sharpe 0.83, max DD -25.3%. Beats VOO on all three in simulation.
- The catch: covered calls cap upside. In the 2023-24 AI rally, writers missed large up moves.
- CSP only: 3.6% CAGR in a 15%+ market. The "wheel prints money" narrative is not supported.
- **Caveat:** synthetic B-S pricing, no slippage or assignment modeled. Real backtesting requires CBOE options data.

---

## Experiment 13: Dual Momentum (ETF Universe)

Gary Antonacci's Dual Momentum applied to a 12-ETF universe (SPY, QQQ, IWM, EFA, EEM, TLT, GLD, SLV, VNQ, HYG, LQD). Monthly rebalancing. 12-1 month lookback.

![Dual momentum ETF strategy — Top-1 achieves 21.2% CAGR](https://i.imgur.com/19zxeqG.png)

```
Variant              CAGR  Sharpe  Max DD   Final
Top-1 (no filter)   21.2%   0.73  -30.9%  $3.37M  <- best CAGR
Top-1 + Abs Filter  17.9%   0.63  -41.8%  $2.84M
Top-3 (no filter)   16.6%   0.72  -24.8%  $2.64M
Top-3 + Abs Filter  15.2%   0.68  -24.5%  $2.44M
Top-5 (no filter)   15.3%   0.73  -25.6%  $2.47M
Top-5 + Abs Filter  13.9%   0.69  -20.7%  $2.28M
VOO Lump Sum        15.7%   0.62  -34.0%  $2.54M
```

- Top-1 no-filter: 21.2% CAGR, Sharpe 0.73, max DD -30.9%. Beats VOO and Pelosi on raw CAGR.
- The absolute momentum filter hurts in this period — fast 2020 and 2023 recoveries penalize rotating to T-bills.
- Top-3 with abs filter: only -24.5% max DD with market-beating CAGR — good balance.
- **Insight:** fully systematic, no insider info. The 2020–2026 tech bull market heavily rewarded simple momentum.

---

## Master Ranking: All Strategies

```
Rank  Strategy                  CAGR   Sharpe  Max DD
--------------------------------------------------------
 1    McCaul (congress)         28.3%   0.91   -43.9%
 2    Combined Congress         22.3%   0.97   -38.2%
 3    Dual Momentum Top-1       21.2%   0.73   -30.9%
 4    Sector Rotation V4        21.2%   0.84   -17.7%
 5    QQQ Lump Sum              21.7%   0.75   -35.1%
 6    Sector Rotation V2        20.5%   0.80   -19.8%
 7    Pelosi (congress)         20.0%   0.68   -42.7%
 8    Covered Call sim          19.9%   0.83   -25.3%
 9    Quality Factor Top-15     19.0%   0.89   -16.8%
10    PEAD proxy                16.2%   0.57   -47.5%
11    Berkshire 13F copy        15.8%   0.57   -37.4%
12    VOO Lump Sum              15.6%   0.69   -27.4%
13    Dip-Tranche Strategy      15.2%   0.70   -22.5%
14    VOO DCA                   13.2%   0.71   -18.7%
15    Degen DCA 70/20/10        14.1%   0.98   -10.5%
16    Gold Hedge 80/20          13.8%   1.13    -9.4%
17    Green (congress)          11.7%   0.47   -26.7%
18    Full Wheel sim            10.4%   0.43   -22.1%
19    60/40 VOO+TLT              8.6%   0.71    -7.3%
20    All-Weather (Dalio)        8.0%   0.68    -6.6%
--------------------------------------------------------
* Mag7/social_momentum excluded: survivorship bias
* Congress requires ongoing STOCK Act monitoring
* Options strategies use synthetic B-S pricing
```

**Five actionable conclusions:**

1. Systematic sector rotation (V4) and quality-factor achieve both higher CAGR and lower drawdown than index investing — no insider info required.
2. Dual momentum Top-1 matches sector rotation on CAGR but with higher drawdown.
3. Congressional copy works (McCaul 28%, Pelosi 20%) but requires monitoring disclosure filings — and the alpha appears to have peaked mid-2023.
4. 20% gold allocation improves every quarterly entry point tested — the simplest reliable enhancement.
5. The dip-tranche strategy's value is risk management (max DD -22.5%), not alpha.
