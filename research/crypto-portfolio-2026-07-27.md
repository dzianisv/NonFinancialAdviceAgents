# Crypto Portfolio Run — 2026-07-27

> Educational analysis, not financial advice. No leverage. Ever. Recommend-only — no orders placed.

**Price snapshot: 2026-07-27 ~15:20 UTC** (OKX/Coinbase matching engines). Live re-check at 21:07 UTC shown where it moved >1%.
**Data-source note:** TradingView MCP was **unavailable** this run. OHLCV pulled from OKX public API (Coinbase for TON/AERO), indicators computed locally at standard TradingView lengths (RSI 14 Wilder, BB 20/2, MACD 12/26/9) via `.agents/scripts/crypto/ohlcv.ts`. Every price cross-verified against CoinGecko + Coinbase + Kraken + Coinpaprika. The four load-bearing moving averages (BTC 200wMA, BTC SMA200, ETH/AAVE/LINK 200wMA) were **independently recomputed from Kraken weekly OHLCV by the skeptic gate and reproduced within 0.4%**.

---

Nothing is a buy. Eleven tokens, six independent investment lenses, and **zero BULLISH quorum verdicts** — the first clean sweep this book has produced. The reason is not sentiment: 7 of 8 fee-generating protocols have 30-day-annualized revenue running BELOW their trailing year (AAVE −62%, Hyperliquid spot −68%, AERO −54%, JUP −54%, HYPE −44%, SOL −34%, PUMP −26%), so the cheap-looking multiples across this book are falling numerators, not discovered bargains. Uniswap is the sole exception and the one genuinely constructive name — fees running ~32% above trailing year, and its v4 fee switch just cleared a Snapshot vote. Sentiment: Fear & Greed 30, a Fed that the market now prices for HIKES not cuts (69.5% odds of a 2026 hike, 78.2% odds of no cuts at all), and a decision landing Wednesday.

---

## Block 1 — Signal table

```
=== CRYPTO PORTFOLIO RUN — 2026-07-27 15:20 UTC ===
(data: OKX/Coinbase public API — TradingView MCP unavailable; MAs skeptic-verified vs Kraken)

Token | Signal            | Valuation      | Quorum  | Bulls/Bears | Note
------|-------------------|----------------|---------|-------------|-----------------------------------
BTC   | HOLD              | fair           | SPLIT   | 1 / 1  (4N) | +1.2-1.9% over 200wMA — the level
ETH   | HOLD              | cheap-on-price | SPLIT-  | 0 / 4  (2N) | supply now inflationary
SOL   | SELL   ⚠️ REVISED | cheap-on-price | BEARISH | 0 / 6       | fee label corrected; low-independence
TON   | SELL   ⚠️ REVISED | expensive      | BEARISH | 0 / 6       | drawdown corrected to -58.5%
HYPE  | HOLD   ⚠️ REVISED | fair           | SPLIT-  | 0 / 4  (2N) | unlock catalyst CONTRADICTED
AAVE  | HOLD   ⚠️ REVISED | cheap-on-asset | SPLIT-  | 0 / 5  (1N) | buyback-pause date was WRONG
JUP   | HOLD   ⚠️ REVISED | cheap          | SPLIT-  | 0 / 3  (3N) | funding datapoint dead
UNI   | HOLD   ⚠️ REVISED | expensive      | SPLIT   | 0 / 1  (5N) | v4 fee switch cleared Snapshot
AERO  | SELL   ⚠️ REVISED | trap           | BEARISH | 0 / 6       | dilution WORSE than stated
PUMP  | HOLD   ⚠️ REVISED | cheap-extended | SPLIT   | 1 / 1  (4N) | RSI 69, do not chase
LINK  | SELL   ⚠️ REVISED | expensive      | BEARISH | 0 / 5  (1N) | 114x revenue confirmed

BUY: 0    BUY(small): 0    HOLD: 7    SELL: 4
```

**Portfolio Governor:** F&G = 30 (Fear) → cap of **6** simultaneous buys.
Ranked BUY/BUY(small) list: *(empty — no token reached a BULLISH quorum)*.
✅ **Governor: 0 buys against a cap of 6 — Fear regime, F&G=30. No downgrades required.** The constraint did not bind; the panel did.

---

## Market data

| Token | Price | RSI14 | MACD hist | EMA20 | SMA50 | SMA200 | 200wMA | Death cross | %52wH | 7d | 30d |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BTC | $64,704 | 52.0 | +9.18 | $64,372 | $63,321 | $72,090 | $63,526 | YES | -48.7% | -1.4% | +6.3% |
| ETH | $1,930 | 60.0 | +1.93 | $1,858 | $1,755 | $2,136 | $2,482 | YES | -61.1% | +1.5% | +20.2% |
| SOL | $75.52 | 47.9 | -0.36 | $76.24 | $74.21 | $87.86 | $108.06 | YES | -70.2% | -2.9% | +3.7% |
| TON | $1.477 | 42.5 | +0.00 | $1.530 | $1.605 | $1.544 | INSUFFICIENT | no | **-58.5%** ⚠️ | +3.1% | -5.7% |
| HYPE | $58.30 | 40.7 | -0.58 | $61.80 | $64.48 | $44.98 | INSUFFICIENT | no | -24.3% ⚠️ | -6.3% | -9.6% |
| AAVE | $99.85 | 59.5 | -0.06 | $93.73 | $85.07 | $104.28 | $137.57 | YES | -74.1% | +11.5% | +3.8% |
| JUP | $0.1867 | 40.1 | -0.00 | $0.1984 | $0.2024 | $0.1854 | INSUFFICIENT | no | -70.1% | -5.3% | -18.8% |
| UNI | $3.841 | 61.2 | +0.01 | $3.615 | $3.203 | $3.571 | $6.824 | YES | -68.7% | +8.3% | +28.1% |
| AERO | $0.4442 | 45.3 | -0.01 | $0.4580 | $0.4677 | $0.4116 | INSUFFICIENT | no | -72.2% ⚠️ | +2.8% | -3.6% |
| PUMP | $0.00212 | 69.0 | ~0 | $0.00183 | $0.00164 | $0.00190 | INSUFFICIENT | YES | -76.3% | +5.0% | +53.1% |
| LINK | $8.599 | 58.7 | +0.02 | $8.331 | $7.987 | $9.227 | $12.561 | YES | -69.1% | +0.5% | +15.3% |

⚠️ **%52wH data caveat:** TON, HYPE and AERO have **less than 365 daily bars** on the venue used, so their "52-week high" is computed over a truncated window and understates the true drawdown. TON's real 52w high is **$3.5747 (2025-08-02) → −58.5%**, not −49.2%. Treat HYPE's −24.3% and AERO's −72.2% as *lower bounds* on the drawdown.

**200wMA is INSUFFICIENT** (fewer than 200 weekly closes, so no long-horizon structural anchor exists) for **TON (37w), HYPE (39w), PUMP (55w), AERO (130w), JUP (131w)**. Per the signal rules those five can never exceed BUY(small) regardless of verdict.

---

## Macro

- **Fear & Greed 30 "Fear."** 7d path 25 → 33 → 31 → 28 → 27 → 26 → 30 — entirely inside Fear, no capitulation spike, no greed. [source: https://api.alternative.me/fng/?limit=7]
- **Fed target 3.50–3.75%, unchanged since 2025-12-11.** Zero changes in 2026. **Next decision Wed 2026-07-29, 2:00pm ET.** [source: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm]
- **The market prices a HIKING path.** Polymarket: July hold 71.9% / **July +25bp hike 28.1%** / cut 0.25%. "Fed rate hike in 2026?" YES **69.5%**. "No cuts in 2026" **78.2%**. CME FedWatch 33% July hike odds. [source: https://www.coindesk.com/markets/2026/07/27/interest-rates-in-u-s-u-k-japan-and-coinbase-strategy-earnings-crypto-week-ahead]
- **Rates and dollar both rising** — the two cleanest headwinds for a liquidity-sponge asset. US 2y **4.37%** (+24bp in six sessions, sitting ~75bp ABOVE the funds midpoint), 10y **4.71%**, DXY **101.49** (+4.6% YTD). [source: FRED DGS2/DGS10; Yahoo DX-Y.NYB]
- **Inflation is two-sided.** June CPI headline **+3.53% YoY** (150bp above target) but core decelerating to **+2.59%** from 2.85%. Headline MoM was **−0.42%**, oil-driven. [source: FRED CPIAUCNS/CPILFENS]
- **Liquidity splits by horizon.** Fed net liquidity **−$69.3bn week-over-week** (mechanical TGA rebuild, +$73.4bn) but **+$105.0bn over four weeks**; WALCL +$35.9bn over seven weeks. RRP is drained to $0.68bn — **the shock absorber is gone**, so every future TGA rebuild now hits bank reserves directly. **M2 +5.58% YoY and ACCELERATING** (Mar 4.58 → Apr 4.72 → May 5.58) — a forward tailwind price has not reflected.
- **Oil unwound hard.** US–Iran paused Strait of Hormuz strikes. **Brent $100.69 (7/23) → $89.59 (7/27) = −11.0%** (corrected from the −7% first reported); WTI $92.19 → $83.24 = −9.7%. [source: Yahoo BZ=F / CL=F]
- **Risk assets:** S&P 7,418.65 −0.33% w/w · **Nasdaq 24,957.55 −2.16%** (the weak leg) · VIX 19.17 · **Gold $4,076 +1.64%, near highs while the dollar rises**. BTC is trading with equities on risk-off and NOT catching the gold safe-haven bid.
- **Cycle: 828 days = 27.2 months post-halving = LATE**, 9+ months past the historical 12–18 month peak window. The halving supply effect is stale and is not a live driver.

**Dominant driver:** a Fed hike tail into Wednesday's FOMC, in a late cycle, with the dollar rising — against an M2 acceleration that only matters on a 2–3 year horizon. Dollar strength wins the next 1–3 months; broad money wins the next 2–3 years.

---

## Block 2 — Verdict per token

### BTC — HOLD

BTC at $64,704 sits **only 1.2–1.9% above its 200-week moving average ($63,526)** — the tightest, cleanest invalidation level in the entire book, and the single most important number in this report (independently recomputed from Kraken weekly bars at $63,462–63,687). On-chain it is mid-cycle, not washed out: MVRV 1.2465, MVRV-Z 0.3954, NUPL 0.1977 ("hope" band), and spot is **1.23× the realized price of $52,468** — i.e. still ABOVE the crowd's aggregate cost basis, so this is not capitulation. The most informative single number is **LTH-SOPR 0.8875 against STH-SOPR 1.0008**: long-term holders are spending at an ~11% realized loss while short-term holders break even. Old supply is taking the pain. The structural bid has gone quiet — Strategy skipped a fifth straight week, holds 843,775 BTC at an average $75,476 (**~$9.1B underwater**, corrected from $9.3B), raised its USD reserve to $3.75B and sold $544.5M of MSTR [source: https://www.sec.gov/Archives/edgar/data/1050446/000119312526316917/mstr-20260727.htm] — and the skeptic gate found it also **sold 3,588 BTC** in early July, making it a net seller, not merely an abstainer. Against that, Benchmark reads the same cash build as strengthening the acquisition plan [source: https://www.theblock.co/post/409743], so the bear framing is a contested interpretation, not settled fact. **Risk:** a Wednesday hike, or a weekly close below $63,526 which opens the path to realized price $52,468 (−19%). **Watch:** the FOMC print, then a daily close above SMA200 $72,090 to upgrade.

```
Research Desk:
  Technical:   $64,704, RSI 52.0 neutral, MACD hist +9.18 turning up, EMA20 $64,372 just below price, death cross active (SMA50 $63,321 < SMA200 $72,090); +1.2-1.9% over the 200wMA $63,526.
  On-Chain:    MVRV 1.2465, MVRV-Z 0.3954, NUPL 0.1977, realized price $52,468 (spot = 1.23x cost basis), Puell 0.7521; LTH-SOPR 0.8875 vs STH-SOPR 1.0008 — long-term holders selling at an 11% loss.
  DeFi:        n/a — L1. Fees 30d $5.58M, revenue to token holders $0, no burn/staking/buyback accrual mechanism exists.
  Macro:       Hike tail 28-33% into the Jul 29 FOMC, 2y 4.37% (75bp above funds midpoint), DXY +4.6% YTD; M2 +5.58% YoY accelerating is the offsetting 2-3yr tailwind.
  Smart Money: ETFs -$465M over two sessions (third straight WEEKLY net inflow nonetheless); Strategy a net seller of 3,588 BTC; funding +4.73% ann and DECAYING with negative premium — no leverage chase.
```
```
Panel:
  Graham (Value):        NEUTRAL [HIGH] — no earning power exists, so no intrinsic value is computable; -48.7% off the high is a quote, not a margin of safety.
  Buffett (Quality):     BEARISH [MED]  — HoldersRev $0 and the largest structural buyer is converting equity into dollars. (Critic: contested — Benchmark reads it the opposite way.)
  Dalio (Cycle):         NEUTRAL [MED]  — 27.2mo post-halving, late cycle, but M2 +5.58% accelerating is real fuel; gold is doing the debasement job BTC is failing to do.
  Druckenmiller (Trend): NEUTRAL [HIGH] — the one name with a placeable stop (1.9% to the 200wMA for an 11% move to SMA200 ≈ 6:1); wants it AFTER Wednesday, not before.
  Alden (Debasement):    BULLISH [MED]  — M2 accelerating, 100% circulating, credibly fixed cap; it IS the hurdle. Capped at MED by DXY +4.6% and the 2y at 4.37%.
  Burniske (On-chain):   NEUTRAL [LOW]  — abstains; zero token accrual means this seat has no signal, not a bearish one.
```
Bull: The only asset here with a fixed supply and a 1.9%-wide invalidation level, into an M2 acceleration price has not discounted.
Bear: Late cycle, hiking Fed, rising dollar, LTH distribution at a loss, and the largest structural buyer now a net seller.

---

### ETH — HOLD

ETH has the best tape in the book — RSI 60, MACD positive, +20.2% over 30 days, above EMA20 and SMA50 — and the worst monetary news: **supply is now net INFLATIONARY at ~+0.85%/yr** (121,815,742 → 121,884,168 ETH over 24.2 days), because burn no longer offsets issuance at current fee levels. The deeper structural problem is the leak: **$273.2M of fees per 30 days are generated on Ethereum but only $7.07M reaches L1 — 97.4% accrues to apps and L2s, not to ETH holders**, putting the token at a P/S of 2,707×. Price sits **22.2% below its 200-week MA of $2,482**, a genuinely deeper structural discount than BTC's +1.9% above — but a broken long-term trend is not the same as a base. The flow story is real but was **overstated in the first draft**: the +$103.9M five-day ETF streak **snapped on Jul 25** and the week closed red; what survives is that ETH funds extended a *weekly* inflow streak to three and have drawn nearly as much capital as BTC ETFs over three weeks on about one-eighth the net assets [source: https://www.theblock.co/post/409660]. Lido has begun consolidating **$16.5B / 8M staked ETH**, cutting validator count by a third and requiring node operators to post bonds for the first time [source: https://www.coindesk.com/tech/2026/07/27/lido-begins-moving-usd16-5-billion-in-staked-ether-to-cut-validator-count-by-a-third] — Lido alone is 43.6% of Ethereum's chain TVL, so that is concentration risk being actively re-engineered. **Risk:** options max pain at **$1,800 is 6.5% BELOW spot** — a downward magnet into Friday's expiry; and the CLARITY Act looks likely to miss its pre-recess window, the largest live classification input for ETH. **Watch:** a weekly close back above $2,482 to upgrade; loss of SMA50 $1,755 to downgrade.

```
Research Desk:
  Technical:   $1,930, RSI 60.0, MACD hist +1.93, above EMA20 $1,858 and SMA50 $1,755 but below SMA200 $2,136; death cross active; 22.2% below the 200wMA $2,482.
  On-Chain:    Supply +68,487 ETH over 24.2 days = +0.85%/yr INFLATIONARY (window ends 2026-07-21, six days stale; chain fees +20.4% over 7d mechanically cut this figure).
  DeFi:        Chain TVL $42.1B (largest of any chain) but only $7.07M of $273.2M/30d fees reaches L1 — a 97.4% leak; burn $5.54M/30d = 0.029% yield.
  Macro:       Same hike tail as the book; CLARITY Act likely misses its pre-recess window, cutting ETH's classification clarity.
  Smart Money: ETF 5d +$103.9M but the daily streak snapped Jul 25; Bitmine added ~10,000 ETH; DVOL 51.47 at the top of its 14d range — ETH is where vol is being paid for.
```
```
Panel:
  Graham (Value):        BEARISH [MED]  — earnings yield ~0.03% against a 4.71% 10y; priced at ~150x the bond alternative with negative net accrual.
  Buffett (Quality):     BEARISH [HIGH] — the tollbooth does not collect the toll: 97.4% leak, P/S 2,704x, share count growing.
  Dalio (Cycle):         NEUTRAL [MED]  — token monetary policy turned expansionary exactly as the sovereign tightens, but the credit bid is genuinely on. Two real forces, no edge.
  Druckenmiller (Trend): NEUTRAL [MED]  — best internals in the book, broken long-term structure; leadership is real, the trend is not.
  Alden (Debasement):    BEARISH [MED]  — fails the BTC hurdle outright: a token inflating 0.85%/yr with a 97% leak has strictly worse monetary properties than BTC.
  Burniske (On-chain):   BEARISH [MED]  — real usage, near-zero capture.
```
Bull: Deepest structural discount to trend in the majors, best relative ETF demand, and a corporate bid that is actually buying.
Bear: Net-inflationary supply, a 97.4% fee leak, and max pain 6.5% below spot into expiry.

---

### SOL — SELL ⚠️ REVISED

Unanimous bearish across all six lenses — and the critic correctly flags that unanimity here reads as **correlated seats, not six independent reads**, so treat it as a strong lean rather than certainty. The structural case is nonetheless clean: **protocol inflation is running 3.7247%/yr, 100% to validators and 0% to the foundation** (read live from a Solana mainnet RPC at epoch 1008) — the highest verified issuance rate in the book, a direct annual tax on the holder. Against that, revenue is contracting: **total Solana chain fees $211.2M/30d vs $4,140M over the trailing year = −38.8% run-rate** (⚠️ the first draft cited $15.06M/30d, which is the narrow L1 *base-fee adapter*, not chain fees — the label was wrong by ~14×, though the direction is unchanged), and Jito MEV is −66.3%. Positioning is the tell: **long/short account ratio 2.83 at the TOP of its 10-day range while Hyperliquid funding is −10.33%** — retail is crowded long while professionals are being paid to be short. Price is 30.1% below its 200-week MA with a death cross active. **The honest counterweight the panel missed:** Solana stablecoin market cap crossed **$15B for the first time**, Jito launched JTX (a self-custodial spot + tokenized-RWA venue), LayerZero and Keeta enabled tokenized bank deposits across Solana [source: https://www.theblock.co/post/409507], Grayscale plans regular cash distributions from SOL staking rewards [source: https://cointelegraph.com/news/grayscale-eth-sol-staking-cash-payouts], and weekly chain fees are **+19.85%**. That is a live adoption cluster no seat priced. **Risk to the SELL:** the inflation schedule decays ~15%/yr toward a 1.5% floor and is governance-mutable. **Watch:** long/short compressing below ~1.8 with funding flipping positive, or a close above SMA200 $87.86.

```
Research Desk:
  Technical:   $75.52, RSI 47.9, MACD hist -0.36, below EMA20 $76.24, death cross active, -70.2% from high, 30.1% below the 200wMA $108.06.
  On-Chain:    Circulating 583.09M of 631.12M (92.4%); protocol inflation 3.7247%/yr all to validators (Solana RPC, epoch 1008) — highest verified issuance in the book.
  DeFi:        Chain TVL $4.93B; total chain fees $211.2M/30d = -38.8% run-rate vs trailing year, but +19.85% over the last 7 days; Jito MEV -66.3%. Solana earns 2.1x Ethereum's L1 fee revenue on 12% of the TVL.
  Macro:       Same hike tail; CLARITY Act failure is the largest live classification risk for a non-ETH L1.
  Smart Money: Long/short 2.83 at the top of its 10d range while HL funding is -10.33% — crowded retail long against paid professional shorts. OI $211M OKX / $325M HL.
```
```
Panel:
  Graham (Value):        BEARISH [MED]  — P/S 240x with 3.725% dilution against a shrinking numerator: the textbook value trap.
  Buffett (Quality):     BEARISH [MED]  — owner earnings net negative before any growth assumption; a better machine than ETH, still not a cheap one.
  Dalio (Cycle):         BEARISH [MED]  — expanding money supply on a shrinking transaction base is the deflationary-bust box.
  Druckenmiller (Trend): BEARISH [MED]  — crowded longs into contracting revenue and a hike tail is how you get liquidated.
  Alden (Debasement):    BEARISH [HIGH] — a 3.7% annual monetary tax; fails the BTC hurdle badly.
  Burniske (On-chain):   BEARISH [MED]  — inflation dilutes holders to fund security; that is not accrual to them.
```
Bull: Stablecoin cap crossed $15B for the first time, weekly fees +19.85%, and a real institutional-rails cluster (JTX, LayerZero/Keeta, Grayscale cash distributions).
Bear: 3.725% annual dilution into a −38.8% revenue run-rate, with retail crowded long against negative funding.

---

### TON — SELL ⚠️ REVISED

The clearest sell in the book and the one on which every lens agreed at high conviction. **Chain fees are $77,181 per 30 days against a $4.04B market cap — roughly 4,300× annualized fees, two orders of magnitude worse than anything else here.** Chain TVL is **$64.9M**: 0.15% of Ethereum's, and smaller than several individual protocols in this same basket. Only **52.4% of supply circulates** (FDV 1.91× market cap), so 47.6% of the dilution is still ahead of a network with negligible economic activity. Hyperliquid open interest is **$0** — no perp positioning exists in either direction; the market has stopped caring. ⚠️ **Two first-draft errors corrected:** the drawdown is **−58.5% from a 52-week high of $3.5747 (2025-08-02)**, not −49.2% — the venue used has only ~37 weeks of history, so the original window was truncated and understated the damage. And the "zero token-specific journalism" claim is **too strong**: the repo's own store holds two TON items dated Jul 21–22 (a Telegram wallet-rollout piece that does not name TON, and a STON.fi wire release). Coverage is thin, not absent. **Watch:** fees rising two orders of magnitude with TVL following — a change of kind, not degree.

```
Research Desk:
  Technical:   $1.477, RSI 42.5, below EMA20 $1.530, SMA50 $1.605 and SMA200 $1.544; -58.5% from the true 52w high $3.5747; 200wMA INSUFFICIENT (37 weekly closes).
  On-Chain:    Masterchain live but activity negligible; 2.735B of 5.221B supply circulating (52.4%), FDV 1.91x mcap.
  DeFi:        Chain fees 30d $77,181, revenue $38.6k, TVL $64.9M, MC/TVL 62.2 — the worst fee-to-cap ratio in the book by two orders of magnitude.
  Macro:       No token-specific macro linkage; carried entirely by the book-wide risk regime.
  Smart Money: Hyperliquid open interest $0.00, funding 0.00, 24h perp volume $0 — no positioning signal exists at all.
```
```
Panel:
  Graham (Value):        BEARISH [HIGH] — 4,299x sales with 47.6% dilution ahead; not cheap and not analyzable.
  Buffett (Quality):     BEARISH [HIGH] — this is not a business: no moat, no cash, no coverage, half the shares unissued.
  Dalio (Cycle):         BEARISH [HIGH] — no economic machine to locate in a cycle; late cycle punishes exactly this.
  Druckenmiller (Trend): BEARISH [MED]  — below every moving average, zero open interest, dead tape, no catalyst.
  Alden (Debasement):    BEARISH [HIGH] — fails the BTC hurdle by the widest margin here: a diluting claim on a network with no activity.
  Burniske (On-chain):   BEARISH [HIGH] — fails test 1 before tests 2 and 3 even matter.
```
Bull: Telegram's distribution remains a genuine option; a non-custodial wallet rollout is coming.
Bear: 4,300× annualized fees, $64.9M of TVL, 47.6% of supply still to be issued, and no positioning in either direction.

---

### HYPE — HOLD ⚠️ REVISED (was SELL)

**The verdict was downgraded from SELL because its load-bearing catalyst does not survive verification.** The first draft cited a CoinDesk week-ahead calendar entry — "July 29: Hyperliquid (HYPE) to unlock 2.8% of its circulating supply worth $817 million" — and three lenses leaned on it heavily. The arithmetic is **self-contradictory**: 2.8% of 222.4M circulating is 6.23M HYPE ≈ **$359M**, not $817M; conversely $817M implies 14.16M tokens = 6.4% of circulating. A separate unlock tracker puts the **next unlock at 2026-08-06, 9.92M HYPE ≈ $595M** (Core Contributors cliff). Three mutually inconsistent figures, and the authoritative emission API is paywalled (HTTP 402). **A dated supply shock this size cannot drive a SELL when its date and size are unresolved — flagged UNRESOLVED, not asserted.** What survives is still not attractive: **only 23.3% of supply circulates** (222.4M of 955.3M; FDV ~$55B against a $12.9B market cap) — the worst dilution setup in the book — and revenue is contracting **−44%** against the trailing year. The mechanism itself is genuinely the best here: **99% of fees route automatically to the Assistance Fund, producing $36.08M/30d ⇒ ~$439M/yr of non-discretionary open-market buying = 3.4% of market cap, with no governance vote required.** But a 3.4% annual bid cannot absorb a ~77% supply overhang. It is also the most leverage-dense name in the book at **$1.31B of Hyperliquid open interest, ~54% of BTC's HL OI on a fraction of the cap**. The real bull development: **tokenized RWAs became Hyperliquid's largest trading category for the first time, >50% of weekly volume** [source: https://cointelegraph.com/news/hyperliquid-rwa-volume-crypto-trading-first-time]. **Watch:** the actual unlock date and size (resolve before acting); revenue run-rate stabilizing; a close back above SMA50 $64.48.

```
Research Desk:
  Technical:   $58.30, RSI 40.7, MACD hist -0.58, below EMA20 $61.80 and SMA50 $64.48 but +29.6% ABOVE SMA200 $44.98; -6.3% 7d, -9.6% 30d; 200wMA INSUFFICIENT (39 weekly closes).
  On-Chain:    222,445,714 of 955,307,079 circulating = 23.3% — the worst dilution setup in the book; FDV ~4.3x market cap.
  DeFi:        Fees $51.30M/30d, HoldersRevenue $36.08M/30d (99% -> Assistance Fund, verified verbatim), = $439M/yr = 3.4% of mcap; revenue run-rate -44%; L1 TVL $1.26B; RWAs now >50% of weekly volume.
  Macro:       Unlock date CONTRADICTED across sources (Jul 29 vs Aug 6; $359M vs $595M vs $817M) — UNRESOLVED, cannot be used as a trigger.
  Smart Money: HL open interest $1.31B ≈ 54% of BTC's HL OI — most leverage-dense name here; funding sits at the protocol baseline, so it carries NO directional information.
```
```
Panel:
  Graham (Value):        BEARISH [MED]  — real earning power already capitalized at 29.5x mcap / ~133x FDV; a 3.4% buyback yield does not cover the overhang.
  Buffett (Quality):     NEUTRAL [MED]  — best machine in the book, wrong price, hostile share count: good business into a 4x share issuance.
  Dalio (Cycle):         BEARISH [HIGH] — credit-dense plus supply-expanding plus late cycle is what breaks first when liquidity tightens. (Weakened: the dated shock is unconfirmed.)
  Druckenmiller (Trend): BEARISH [HIGH] — tape already rolling over and still 29.6% above SMA200; that gap is the air underneath it. (Weakened: the unlock date is unconfirmed.)
  Alden (Debasement):    BEARISH [HIGH] — best protocol economics in the book, worst monetary policy in the book, and monetary policy is what this seat prices.
  Burniske (On-chain):   NEUTRAL [MED]  — best mechanism, fails test 3: 3.4% yield against a 77% overhang.
```
Bull: The cleanest, largest non-discretionary accrual mechanism in crypto, on a venue where tokenized RWAs just became the largest category.
Bear: 23.3% circulating, revenue −44%, $1.31B of leverage stacked on it, and an unlock of contested size ahead either way.

---

### AAVE — HOLD ⚠️ REVISED (was SELL)

**Downgraded from SELL because two of the three facts underpinning the bear case were wrong.** (1) The first draft asserted buybacks had been paused **"99 days, since 2026-04-19."** DeFiLlama's own daily holders-revenue series shows **non-zero prints after that date — $20,188 on 2026-04-30, $135,368 on 2026-05-26, $576,537 on 2026-06-24.** The actual zero streak is **~33 days from 2026-06-24**, not 99. (2) The draft claimed **no restart condition exists**; that was true as of a 2026-06-05 forum post but a **2026-06-25 statement announced "Aavenomics 3.0 will have immutable and automated buybacks"** — a defined direction, not an open-ended pause. (3) The categorical V4 quote "No revenue shared to AAVE holders" could not be located in a governance full-text search and is treated as **unsourced**. What **does** survive verification is the fact that matters most: **HoldersRevenue over the last 30 days is $0** — confirmed independently. So the token is currently accruing nothing, and it is right to refuse to pay for accrual that is not arriving; but "permanently severed from the cashflow" is falsified. The rest is genuinely attractive on the asset side and genuinely poor on the earnings side: **TVL $14.74B against a $1.53B market cap = MC/TVL 0.10, the cheapest in the book**, GHO supply $648M, treasury revenue $3.76M/30d — but the fee run-rate is **−62%**, the steepest decay in the book, and the token captures none of it today. The tape is the best 7-day performance in the book at **+11.5%**, reclaiming $100, with V4 deposits reportedly rising from ~$11.3M to $303M. **Watch:** the first non-zero holders-revenue print, or a formal Aavenomics 3.0 vote — either flips this constructive. Loss of SMA50 $85.07 flips it back to bearish.

```
Research Desk:
  Technical:   $99.85, RSI 59.5, MACD hist -0.06, above EMA20 $93.73 and SMA50 $85.07 but below SMA200 $104.28; death cross active; +11.5% 7d, best tape in the book; 27.4% below the 200wMA $137.57.
  On-Chain:    15,417,691 of 16,000,000 circulating (96.4%) — effectively no unlock overhang, the best supply profile of any DeFi token here.
  DeFi:        TVL $14.74B, MC/TVL 0.10 (cheapest in book), fees $28.09M/30d (run-rate -62%), treasury revenue $3.76M/30d, GHO $648M. HoldersRevenue 30d = $0 (CONFIRMED); last non-zero print 2026-06-24, not 2026-04-19 (CORRECTED).
  Macro:       No token-specific macro linkage; Aave founder publicly campaigning for CLARITY passage.
  Smart Money: HL open interest $88.8M; funding at the protocol baseline (no directional signal); no journalism-tier coverage in the window.
```
```
Panel:
  Graham (Value):        BEARISH [MED]  — cheapness at the ASSET level the SECURITY holder cannot reach. (Weakened: the severance is temporary, not structural.)
  Buffett (Quality):     BEARISH [HIGH] — a CEO who suspends the dividend. (Weakened: he has now said what brings it back — immutable, automated buybacks.)
  Dalio (Cycle):         BEARISH [MED]  — late-cycle multiple expansion on a falling numerator: +11.5% on the week with zero distribution.
  Druckenmiller (Trend): NEUTRAL [MED]  — best 7d tape in the book but MACD still negative and price below SMA200: a bounce, not a trend.
  Alden (Debasement):    BEARISH [MED]  — neither scarcity-by-buyback nor cashflow today; 96.4% circulating is the one point in its favour.
  Burniske (On-chain):   BEARISH [HIGH] — test 2 returns zero, which voids test 3. (Weakened: zero is 33 days old with a stated restart direction.)
```
Bull: Cheapest asset base in the book (MC/TVL 0.10), effectively no dilution, and a stated commitment to immutable automated buybacks.
Bear: Zero distribution to holders for 33 days on a −62% fee run-rate, with the market already paying +11.5% for a restart that has not happened.

---

### JUP — HOLD ⚠️ REVISED

Structurally the **best-designed accrual in the book after HYPE**: 50% of platform revenue buys back JUP, and the ratio reproduces to three decimals on two independent windows — it is **mechanically enforced, not a discretionary governance promise**, which is precisely what AAVE's pause showed matters. That produces $2.12M/30d, a **4.2% annual buyback yield at a P/S of 12.0× and MC/TVL of 0.30** — the second-cheapest genuine numbers here. It is not enough. A 4.2% yield does not clear a 4.37% 2-year Treasury, let alone compensate for equity-like risk; revenue is running **−54%** against the trailing year; and **51.6% of supply is still to be issued**, so the dilution overhang dwarfs the retirement rate. The tape is the worst in the book at **−18.8% over 30 days**, clinging 0.7% above SMA200 with no cushion. ⚠️ **Correction:** the first draft cited Hyperliquid funding at **−25.94%** as evidence of informed shorts; on re-pull it is **+1.97% annualized with a −0.035% premium**. That datapoint is dead and has been removed from the bear case. Journalism coverage in the window is **zero across four query paths** — declared as a gap, not read as bullish silence. **Watch:** the fee run-rate stabilizing (would flip this constructive), or any move to make the 50% split discretionary (would flip it bearish immediately).

```
Research Desk:
  Technical:   $0.1867, RSI 40.1, MACD negative, below EMA20 $0.1984 and SMA50 $0.2024, 0.7% above SMA200 $0.1854; -18.8% 30d, the worst tape in the book; 200wMA INSUFFICIENT (131 weekly closes).
  On-Chain:    3.32B of 6.86B circulating = 48.4%; FDV 2.07x market cap — roughly half the supply still to come.
  DeFi:        TVL $2.10B, fees $12.95M/30d, HoldersRevenue $2.12M/30d via a mechanically-enforced 50% split (live since 2025-02-17); P/S 12.0x, MC/TVL 0.30; revenue run-rate -54%. Newer products (Prediction, Offerbook) carry NO holder revenue — product expansion can dilute the effective capture rate.
  Macro:       High-beta to Solana DEX/perp activity, which is itself contracting.
  Smart Money: HL open interest $6.0M (thin); funding +1.97% ann (CORRECTED from -25.94%); no journalism coverage across four query paths.
```
```
Panel:
  Graham (Value):        NEUTRAL [LOW]  — 4.2% yield fails the demand for an earnings yield at a large premium to the bond alternative.
  Buffett (Quality):     NEUTRAL [LOW]  — cleanest allocator discipline after HYPE, but an aggregator is forkable and has no defensible moat.
  Dalio (Cycle):         BEARISH [MED]  — falling real revenue into a late cycle with supply still to issue.
  Druckenmiller (Trend): BEARISH [MED]  — falling price, falling revenue, dilution pipeline. (Weakened: the funding datapoint was wrong.)
  Alden (Debasement):    BEARISH [MED]  — a mechanically enforced 4.2% cannot out-run a half-uncirculated float.
  Burniske (On-chain):   NEUTRAL [MED]  — passes tests 1 and 2; test 3 is only cheap if the numerator stops falling.
```
Bull: The most credibly enforced buyback mechanism in the book, at 12× sales and 70% off the high.
Bear: 4.2% yield against a 4.37% T-bill, revenue −54%, and 51.6% of the supply still unissued.

---

### UNI — HOLD ⚠️ REVISED (the one constructive name)

**The only token in this book with improving fundamentals, and the correction went in its favour.** Uniswap is the **sole fee accelerator here** — $93.24M of fees over 30 days, annualizing roughly **+32% above the trailing year**, while 7 of 8 peers contract. The burn is real and running: ~847,561 UNI per 30 days ≈ **1.65% of circulating supply retired annually**, making it the only alt in the book with a genuinely deflationary float. Official governance, verbatim: *"Protocol fees are now live across all v2 and v3 pools on 11 chains… the protocol set a record burning 186,000 UNI in one day."* [source: https://gov.uniswap.org/t/26162.json]. The panel's central bear point was that **realised holder capture is only 3.49% of fees, not the headline 17%, because v4 ($798.6M of TVL) contributes exactly zero** — ⚠️ **and the critic found that this is mid-change: v4 fee activation has cleared a Snapshot vote and went to an on-chain vote on 2026-07-22.** If it passes, capture re-rates upward from 3.49% on the fastest-growing surface in the protocol. That is a real, dated, upward catalyst the panel did not price. It is still **not a buy**: P/S is 60.5×, price is 43.7% below its 200-week MA with a death cross active, it has already run **+28.1% in 30 days**, and a live RFC dated 2026-06-25 proposes **replacing the burn entirely with staking distribution** — the sound-money property is one vote from deletion. Uniswap also pushed into tokenized securities with permissioned, compliance-enforcing pools built with Superstate, Securitize and Dowgo [source: https://www.coindesk.com/business/2026/07/22/uniswap-pushes-deeper-into-tokenized-assets-with-permissioned-trading-pools]. **Watch:** the v4 on-chain vote result and the burn-vs-staking RFC. Burn retained + v4 fees live = the first genuine BUY candidate this book has had in weeks. RFC replacing the burn = downgrade to bearish.

```
Research Desk:
  Technical:   $3.841, RSI 61.2, MACD positive, above EMA20 $3.615, SMA50 $3.203 AND SMA200 $3.571 — one of only five above its 200d; death cross still active; +28.1% 30d; 43.7% below the 200wMA $6.824.
  On-Chain:    625.1M of 892.3M circulating = 70.1%; ~847,561 UNI burned per 30 days ≈ 1.65% of float retired annually — the only deflationary alt float in the book.
  DeFi:        TVL $3.07B, fees $93.24M/30d annualizing ~+32% above trailing year (SOLE accelerator); HoldersRevenue $3.26M/30d = 3.49% capture; P/S 60.5x. v4 fee activation cleared Snapshot, on-chain vote 2026-07-22 (CORRECTED — not "permanently zero").
  Macro:       Tokenized-securities expansion with Superstate/Securitize/Dowgo is genuine productivity growth, the one force that drives the long run.
  Smart Money: HL open interest $21.7M (thin); funding at the protocol baseline — no directional signal.
```
```
Panel:
  Graham (Value):        NEUTRAL [MED]  — growing earnings at 60x sales with a revocable payout is not a margin of safety; Mr. Market has already paid for the growth.
  Buffett (Quality):     BEARISH [MED]  — best brand in the book and the owner still gets 3.49%; the RFC to swap burn for staking is the fee-switch equivalent of issuing shares to insiders.
  Dalio (Cycle):         NEUTRAL [MED]  — real productivity growth, but the holder's claim on it is not yet settled.
  Druckenmiller (Trend): NEUTRAL [LOW]  — the only genuine internal improver; good trend, unpriced mechanism risk.
  Alden (Debasement):    NEUTRAL [MED]  — genuinely anti-debasement behaviour, but 1.65%/yr of revocable burn loses to a fixed cap no vote can change.
  Burniske (On-chain):   NEUTRAL [MED]  — the only accelerator; capture re-rates if v4 turns on and the burn survives.
```
Bull: Sole fee accelerator in the book, a deflationary float, and a dated upward catalyst in the v4 fee vote.
Bear: 60.5× sales after a +28% month, with a live proposal that would delete the burn entirely.

---

### AERO — SELL ⚠️ REVISED (bear case strengthened)

Unanimous bearish, and the correction made it **worse, not better**. AERO's "zero-leak" ve(3,3) model routes **100% of protocol revenue to veAERO voters** — $4.19M per 30 days, which screens as an 11.8% yield at 8.5× sales. That number is a trap, and it is a trap **by holder class**: the protocol issues roughly **+18.24M AERO per 30 days ≈ $8.10M**, against $4.19M routed to lockers. A spot holder is therefore **net-diluted by about $3.9M/30 days — an effective yield of roughly −9%, not +11.8%**. Every screener will print the wrong sign. ⚠️ **Correction:** the first draft called the 1.9× emission-to-accrual ratio an *upper* bound because gross emission data was paywalled and the figure was derived from a CoinGecko circulating-supply delta. The critic points out CoinGecko's circulating figure **excludes veAERO locks**, which makes the derivation a **lower bound** — actual dilution is worse, on the order of ~25%/yr supply inflation. The sign error ran against the token. Revenue is also contracting **−54% to −58%**, only 50.1% of supply circulates, and in **September 2026 "Predictive Allocation" will replace weekly gauge voting entirely** — the exact mechanism the accrual runs on is being swapped out. Zero crypto-native journalism coverage in the window. **Watch:** emissions falling below fee accrual (would flip spot holders to net-positive), or Predictive Allocation shipping with verified improved capture for non-lockers.

```
Research Desk:
  Technical:   $0.4442, RSI 45.3, MACD negative, below EMA20 $0.4580 and SMA50 $0.4677, 7.9% above SMA200 $0.4116; 200wMA INSUFFICIENT (130 weekly closes); true drawdown likely worse than the -72.2% shown (truncated window).
  On-Chain:    974.2M of 1,945.2M circulating = 50.1%; emission ~+18.24M AERO/30d — and the derivation is a LOWER bound because the supply source excludes veAERO locks (CORRECTED).
  DeFi:        TVL $307M, fees $6.12M/30d, HoldersRevenue $4.19M/30d to veAERO (100% of revenue); but $8.10M/30d issued against it — spot holders net -$3.9M/30d. Revenue run-rate -54/-58%.
  Macro:       Base chain fees $42.9M/30d is the addressable pool; no token-specific macro linkage.
  Smart Money: HL open interest $8.9M (thin); funding at the protocol baseline — no directional signal; zero journalism coverage in the window.
```
```
Panel:
  Graham (Value):        BEARISH [MED]  — the spot holder's net accrual is NEGATIVE; P/S 8.5x is meaningless on the diluted side of the same token.
  Buffett (Quality):     BEARISH [MED]  — management issues stock 1.9x faster than it returns cash.
  Dalio (Cycle):         BEARISH [MED]  — net token debasement plus rule risk stacked on falling revenue, in a late cycle.
  Druckenmiller (Trend): BEARISH [MED]  — negative carry for the holder class I would actually be in.
  Alden (Debasement):    BEARISH [HIGH] — printing roughly twice as fast as it retires; fails the BTC hurdle at the most basic level this seat tests.
  Burniske (On-chain):   BEARISH [MED]  — the most misleading "cheap" multiple in the book; same token, opposite sign by holder class.
```
Bull: A real, verified 100% revenue routing to veAERO — genuinely attractive **if you lock**.
Bear: Spot holders are diluted at roughly −9% net, the dilution estimate was biased in the wrong direction, and the accrual mechanism is being replaced in September.

---

### PUMP — HOLD ⚠️ REVISED (extended — do not chase)

The only BULLISH vote in the entire eleven-token book, and it came at LOW conviction. On the arithmetic PUMP is unmatched: **$14.30M of holders-revenue per 30 days ⇒ ~$174M/yr repurchased = 20.6% of market cap annually, at a P/S of 3.5×, with continuous daily buyback prints and no gaps in 40 days.** That is roughly 6× the cash yield of the next name and the only yield in this book that clears a 4.37% T-bill by a wide margin. Everything else about it is a warning. The revenue is the most cyclical, reflexive and competitively attackable cashflow in crypto — a launchpad is trivially forked. **The split has already been changed twice (100% → 0% → 50% from 2026-04-28)**, which is the governance-risk tell: a vote can zero the entire thesis. Revenue is −26%, and 53% of supply is overhang. The tape is the hottest in the book (**+53.1% over 30 days, RSI 69.0, above every moving average**) — which is exactly why it is a HOLD and not a buy: the zone is extended, so even a bullish verdict cannot upgrade past HOLD under the zone gate. ⚠️ **One correction in PUMP's favour:** the first draft attributed the move entirely to one named influencer's disclosed ~$1.5M long. That is true but incomplete — **BOOST mode was activated on 2026-07-21 in the same window**, a TWAP-driven buyback-and-burn reinjecting migration liquidity and targeting >$100M/yr of previously dead liquidity. There is a protocol driver, not only a social one. **Watch:** buyback prints continuing after the influencer trade unwinds. Any third change to the split, or a break of SMA200 $0.00190, flips this bearish.

```
Research Desk:
  Technical:   $0.00212, RSI 69.0 (highest in the book, near overbought), +53.1% 30d, above EMA20/SMA50/SMA200; death cross still active; 200wMA INSUFFICIENT (55 weekly closes).
  On-Chain:    397.8B of 846.1B circulating = 47.0%; FDV 2.13x market cap — 53% supply overhang.
  DeFi:        Fees $25.67M/30d, revenue $19.67M, HoldersRevenue $14.30M/30d = 20.6% of mcap repurchased annually; P/S 3.5x; daily prints with zero gaps in 40 days; revenue run-rate -26% (the mildest contraction in the book).
  Macro:       Pure high-beta Solana speculative-volume proxy; the first thing cut when risk appetite contracts.
  Smart Money: HL open interest $63.4M with 24h volume roughly equal to OI — very high turnover, short holding periods; move attributed to a disclosed ~$1.5M influencer long PLUS the Jul 21 BOOST-mode activation (CORRECTED).
```
```
Panel:
  Graham (Value):        NEUTRAL [MED]  — passes the earnings-yield test (20.6% vs 4.71%) but fails safety of principal: governance can zero the claim overnight.
  Buffett (Quality):     NEUTRAL [LOW]  — wonderful price, gruesome business; no moat whatsoever.
  Dalio (Cycle):         BEARISH [HIGH] — this is top-of-cycle behaviour, not a valuation; speculative-froth beta is what you cut late in a cycle.
  Druckenmiller (Trend): NEUTRAL [LOW]  — hottest tape in the book, but a crowd around a microphone is not a trend.
  Alden (Debasement):    NEUTRAL [LOW]  — the only retirement rate that plausibly out-runs its own overhang; clears on arithmetic, fails on durability.
  Burniske (On-chain):   BULLISH [LOW]  — the only name where all three tests pass on verified numbers.
```
Bull: 20.6% of market cap repurchased annually at 3.5× sales, printing daily without a gap — the only real cash yield in the book.
Bear: RSI 69 after a +53% month, on the least defensible cashflow in crypto, with a payout split already changed twice.

---

### LINK — SELL ⚠️ REVISED

The most expensive protocol in the book by a wide margin: **114.4× annualized revenue, roughly 2× the next-highest name (UNI at 60.5×)**, for a buyback yield of just **0.9%/yr** — independently reproduced by the skeptic gate at 114.3×. Revenue is also brand-new rather than established: **totalAllTime ≈ total1y ($56.9M)**, meaning the Chainlink Reserve has about twelve months of history and no record before it. ⚠️ **The panel's framing was too harsh in one respect and not harsh enough in another.** The draft said 96% of the Reserve's funding is "unverifiable"; more precisely, the **deposits are on-chain — it is the off-chain enterprise/CCIP attribution that cannot be independently confirmed**, and only $206k of the $4.84M/30d is verifiable on-chain *request* fees (a figure the skeptic could not independently reproduce, so treat it as an internal computation, not a fact). The sharper weakness the panel under-sold is **lumpiness: 304 of 355 days are zero prints** — the entire monthly figure lands in a handful of weekly settlement transactions. Crucially, **LINK's zero-days are batching, not a governance pause** — the exact opposite of AAVE, and that distinction favours LINK. **Missed catalyst:** Aave standardised on CCIP on 2026-07-21, and Lombard Finance adopted CCIP for cross-chain BTC.b/LBTC deposits on 2026-07-23 — real enterprise adoption none of the five bears priced. The flow picture is contradictory: a whale accumulated **1.58M LINK (~$13.2M)** off Binance in a week and ~25M LINK left exchanges in a month, while the same aggregator feed on the same day reported LINK losing $8.38 support. **Watch:** on-chain-verifiable fee share rising well above 4.3%, or the multiple compressing toward peers on genuine CCIP revenue growth. A weekly close above SMA200 $9.227 with whale accumulation continuing would flip it constructive.

```
Research Desk:
  Technical:   $8.599, RSI 58.7, MACD hist +0.02, above EMA20 $8.331 and SMA50 $7.987 but below SMA200 $9.227; death cross active; +15.3% 30d but only +0.5% 7d — momentum stalled; 31.5% below the 200wMA $12.561.
  On-Chain:    748.1M of 1,000M circulating = 74.8%; ~25M LINK left exchanges within a month; a whale accumulated 1.58M LINK (~$13.2M) off Binance.
  DeFi:        Fees $4.84M/30d, HoldersRevenue $4.61M/30d, P/S 114.4x — the most expensive in the book; buyback yield 0.9%/yr; 304 of 355 days are zero prints (batching, NOT a pause — this distinction favours LINK over AAVE).
  Macro:       RWA-tokenization narrative is the long-run driver; CCIP adoption by Aave (Jul 21) and Lombard (Jul 23) is the live evidence for it.
  Smart Money: HL open interest $43.0M with an OI/volume ratio of 8.3x — stale open interest, low turnover; funding at the protocol baseline, no directional signal.
```
```
Panel:
  Graham (Value):        BEARISH [HIGH] — the highest multiple in the book for the least auditable numbers is the inverse of a margin of safety; there is no documented earnings record.
  Buffett (Quality):     BEARISH [MED]  — does not pay 114x for numbers he cannot audit.
  Dalio (Cycle):         BEARISH [MED]  — late cycle compresses multiples from the most expensive end first.
  Druckenmiller (Trend): NEUTRAL [LOW]  — 0.5% over 7 days is a stall; the 0.9% buyback yield cannot support a 114x multiple.
  Alden (Debasement):    BEARISH [MED]  — retirement rate is ~1/28th of the dilution overhang.
  Burniske (On-chain):   BEARISH [MED]  — highest multiple, weakest auditability. Note the zero-days are batching, which favours LINK against AAVE.
```
Bull: Genuine enterprise CCIP adoption (Aave, Lombard) landing inside the window, with ~25M LINK leaving exchanges in a month.
Bear: 114× revenue for a 0.9% yield, on a Reserve with twelve months of history and unverifiable off-chain attribution.

---

## Block 3 — Research sources

```
--- RESEARCH SOURCES ---
MARKET DATA (T1, all independently cross-verified):
  [T1] https://www.okx.com/api/v5/market/history-candles — daily/weekly OHLCV for 9 tokens (BTC ETH SOL HYPE AAVE JUP UNI PUMP LINK)
  [T1] https://api.exchange.coinbase.com/products/{TON-USD,AERO-USD}/candles — daily OHLCV for the two tokens OKX does not list
  [T1] https://api.coingecko.com/api/v3/simple/price — 11-token price cross-check (all within 1.4%)
  [T1] https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=10080 — 669 weekly bars 2013-10-03 to 2026-07-23; independent 200wMA recompute = $63,462-63,687 vs $63,526 claimed (<=0.25% error)
  [T1] https://api.coinbase.com/v2/prices/{X}-USD/spot , https://api.coinpaprika.com/v1/tickers — third and fourth price venues

ON-CHAIN (T1):
  [T1] https://bitcoin-data.com/api/v1/mvrv/last — "{"d":"2026-07-26","mvrv":1.2465}"
  [T1] https://bitcoin-data.com/api/v1/mvrv-zscore/last — "{"mvrvZscore":0.3954}"
  [T1] https://bitcoin-data.com/api/v1/nupl/last — "{"nupl":0.1977}"
  [T1] https://bitcoin-data.com/api/v1/realized-price/last — "{"realizedPrice":52468.49}"
  [T1] https://bitcoin-data.com/api/v1/puell-multiple/last — "{"puellMultiple":0.7521}"
  [T1] https://bitcoin-data.com/api/v1/lth-sopr/last — "{"lthSopr":0.8875}" ; .../sth-sopr/last — "{"sthSopr":1.0008}"
  [T1] https://api.blockchain.info/stats — "hash_rate":8.596753089052123E11,"n_tx":708382,"difficulty":126231507121868
  [T1] https://ultrasound.money/api/v2/fees/supply-over-time — 121,815,742 (2026-06-27) -> 121,884,168 (2026-07-21) = +0.847%/yr
  [T1] https://api.mainnet-beta.solana.com getInflationRate — "total":0.03724738633549205,"foundation":0.0
  [T1] https://tonapi.io/v2/blockchain/masterchain-head — TON masterchain block data

PROTOCOL / DeFi (T1):
  [T1] https://api.llama.fi/v2/chains — "Ethereum ETH 42111139691" ; "Solana SOL 4926942807" ; "TON GRAM 64899622" ; "Hyperliquid L1 HYPE 1260016469" ; "Base 4657795255"
  [T1] https://api.llama.fi/summary/fees/aave?dataType=dailyHoldersRevenue — "total24h":0,"total7d":0,"total30d":0 ; last non-zero 2026-06-24 = 576537
  [T1] https://api.llama.fi/summary/fees/hyperliquid?dataType=dailyHoldersRevenue — "30d 36078570" ; methodology "99% of fees go to Assistance Fund for buying HYPE tokens"
  [T1] https://api.llama.fi/summary/fees/pump.fun?dataType=dailyHoldersRevenue — "30d 14301309" ; daily 2026-07-20..26 = 475035, 503718, 552001, 529763, 577372, 531409, 587823
  [T1] https://api.llama.fi/summary/fees/uniswap?dataType=dailyFees — "30d= 93240408.55 1y= 859561587.55" ; dailyRevenue "30d = 3255483" -> capture 3.492%
  [T1] https://api.llama.fi/summary/fees/chainlink?dataType=dailyFees — "30d 4841696 1y 61445905" ; chainlink-staking dailyHoldersRevenue "allTime 56911607 == 1y"
  [T1] https://api.llama.fi/summary/fees/jupiter?dataType=dailyHoldersRevenue — "30d 2115951.30" (exactly 0.500 of revenue on both 30d and 1y windows)
  [T1] https://api.llama.fi/summary/fees/{aerodrome-v1,aerodrome-slipstream}?dataType=dailyRevenue — combined "30d 4189859"
  [T1] https://api.llama.fi/summary/fees/ton?dataType=dailyFees — "30d= 77181"
  [T1] https://api.llama.fi/overview/fees/solana — chain-wide "30d= 211249216.68 1y= 4139945000.24", change_7d +19.85%
  [T1] https://governance.aave.com/t/24686.json — "[ARFC] Pause AAVE Buybacks" — "AAVE buybacks have been paused since April 19, 2026"
  [T1] https://gov.uniswap.org/t/26162.json — "Protocol fees are now live across all v2 and v3 pools on 11 chains... the protocol set a record burning 186,000 UNI in one day."
  [T1] https://gov.uniswap.org/latest.json?order=activity — "RFC : Tokenomics overhaul : hard-capping supply via auto burn, pivoting unification to staking distribution" (2026-06-25)
  [T1] https://stablecoins.llama.fi/stablecoins — "GHO circulating {'peggedUSD': 648238270.0}"

MACRO (T1):
  [T1] https://api.alternative.me/fng/?limit=7 — "value":"30","value_classification":"Fear"
  [T1] https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm — "2026 FOMC Meetings ... July 28-29"
  [T1] https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS2 — "2026-07-23,4.37" ; ?id=DGS10 — "2026-07-23,4.71"
  [T1] https://fred.stlouisfed.org/graph/fredgraph.csv?id=WALCL — "2026-07-22,6747378" ; ?id=WTREGEN — "2026-07-22,829623" ; ?id=RRPONTSYD — "2026-07-24,0.675"
  [T1] https://fred.stlouisfed.org/graph/fredgraph.csv?id=M2SL — "2026-05-01,23052.3" (+5.58% YoY)
  [T1] https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCNS — 2026-06 333.952 / 2025-06 322.561 = +3.531%
  [T1] https://gamma-api.polymarket.com/markets?...tag_id=100328 — "Will the Fed increase interest rates by 25 bps after the July 2026 meeting? ["0.2805","0.7195"]"
  [T1] https://api.sosovalue.xyz/openapi/v2/etf/historicalInflowChart — BTC "2026-07-24 totalNetInflow -240084652.5" ; ETH "-70600000"
  [T1] https://farside.co.uk/bitcoin-etf-flow-all-data/ — "20 Jul 226.8 / 21 Jul 203.2 / 22 Jul 69.1 / 23 Jul (225.1) / 24 Jul (240.1)"
  [T1] https://www.sec.gov/Archives/edgar/data/1050446/000119312526316917/mstr-20260727.htm — "843,775 $63.69 $75,476 ... the balance of the USD Reserve is $3.75 billion"
  [T1] Yahoo chart API CL=F / BZ=F — WTI "2026-07-23 92.19" -> "2026-07-27 83.24" ; Brent "100.69" -> "89.59" (-11.0%)

POSITIONING (T1):
  [T1] https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP — "fundingRate":"0.0000432117789360" (prior settle 0.0000525 — decaying)
  [T1] https://www.okx.com/api/v5/public/open-interest?instType=SWAP — BTC "oiUsd":"1955117835.19" ; ETH "1514963169.62" ; SOL "210824862.24"
  [T1] https://api.hyperliquid.xyz/info (metaAndAssetCtxs) — HYPE OI 22,546,650 tokens = $1.31B ; TON OI 0.00
  [T1] https://www.okx.com/api/v5/rubik/stat/contracts/long-short-account-ratio — BTC "1.68" ; ETH "1.54" ; SOL "2.83"
  [T1] https://www.deribit.com/api/v2/public/get_book_summary_by_currency — BTC put/call by OI 0.4285, by 24h volume 0.8184

JOURNALISM (T2, all via the repo read-news pipeline):
  [T2] https://www.coindesk.com/markets/2026/07/27/interest-rates-in-u-s-u-k-japan-and-coinbase-strategy-earnings-crypto-week-ahead — "CME's FedWatch shows a 33% chance of a U.S. rate increase, while prediction markets odds are at 19%"
  [T2] https://www.ft.com/content/403625cc-8371-43ee-997a-f6908a97f52e — "Brent nearly 7% lower after two weeks of escalating violence had pushed crude to more than $100 a barrel"
  [T2] https://www.coindesk.com/markets/2026/07/27/crypto-steadies-as-iran-u-s-pause-sends-oil-tumbling-lifts-risk-assets — "Brent crude plunged 7% after the U.S. and Iran paused Strait of Hormuz strikes"
  [T2] https://www.theblock.co/post/409721 — "Strategy bought no bitcoin for a fifth straight week, while raising its USD reserve to $3.75 billion and selling $544.5M in MSTR."
  [T2] https://decrypt.co/374369 — "The Bitcoin treasury firm also tapped its $1 billion preferred buyback for the first time, spending $25 million on STRC."
  [T2] https://www.theblock.co/post/409743 — "Benchmark reiterated its $570 Strategy target, citing disciplined capital allocation, growing cash reserves and continued long-term BTC plan."
  [T2] https://www.coindesk.com/markets/2026/07/27/bitcoin-etfs-record-third-consecutive-weekly-inflows-despite-losses-of-usd465-million-to-end-week — "nearly $415 million of the outflows" concentrated in IBIT
  [T2] https://www.coindesk.com/markets/2026/07/27/bitcoin-options-traders-are-dropping-their-hedges-going-into-the-fed-meeting — "The put/call ratio has fallen to about 0.52 from 0.76 in late June"
  [T2] https://www.coindesk.com/tech/2026/07/27/lido-begins-moving-usd16-5-billion-in-staked-ether-to-cut-validator-count-by-a-third — "consolidating 8 million ETH and requiring its professional node operators to post bonds for the first time"
  [T2] https://www.theblock.co/post/409749 — "Bitmine adds nearly 10,000 ETH while repurchasing 6.1 million common shares"
  [T2] https://www.theblock.co/post/409660 — "Ether funds have drawn nearly as much capital as bitcoin ETFs over the past three weeks despite holding about one-eighth as much in net assets."
  [T2] https://cointelegraph.com/markets/ethereum-etfs-week-red-end-inflow-streak — "Ethereum ETFs snapped a five-day inflow streak"
  [T2] https://www.theblock.co/post/409608 — "Seven Democratic negotiators say the latest Clarity Act draft needs stronger ethics and consumer protections." (Galaxy cuts passage odds to 30%)
  [T2] https://decrypt.co/374300 — "Senate Majority Leader John Thune signals the crypto market-structure bill likely won't clear the chamber before the August recess"
  [T2] https://cointelegraph.com/news/hyperliquid-rwa-volume-crypto-trading-first-time — "Tokenized RWA trading became Hyperliquid's largest trading category for the first time, accounting for more than half of the decentralized exchange's weekly trading volume."
  [T2] https://www.theblock.co/post/408875 — "HIP-4 deployers must stake 500,000 HYPE tokens and can take up to 50% fees"
  [T2] https://www.coindesk.com/business/2026/07/22/uniswap-pushes-deeper-into-tokenized-assets-with-permissioned-trading-pools — "lets regulated funds and securities trade on Uniswap while enforcing compliance rules necessary for institutions"
  [T2] https://cointelegraph.com/news/grayscale-eth-sol-staking-cash-payouts — "Grayscale plans to establish regular cash distributions from staking rewards generated by its Ether and Solana exchange-traded products."
  [T2] https://www.theblock.co/post/409507 — "LayerZero and Keeta have partnered to enable native transfers of tokenized bank deposits across Ethereum, Solana, Base, and Keeta."
  [T2] https://www.theblock.co/post/409040 — "Jito Labs launched JTX, a self-custodial Solana trading platform with spot trading for tokens and tokenized RWAs."
  [T2] https://www.coindesk.com/markets/2026/07/20/crypto-market-slips-even-as-equities-advance-pump-surges-on-social-media-chatter — "PUMP's 20% surge was the only real headline in an otherwise quiet session."
  [T2] https://cointelegraph.com/markets/bitcoin-og-dormant-btc-movement-thorn — "Dormant BTC activity fell to its lowest level since Q3 2022"

FAILED / UNAVAILABLE (declared, never imputed):
  [FETCH FAILED: https://www.bls.gov/news.release/cpi.nr0.htm] — bot-blocked; substituted the BLS public API
  [FETCH FAILED: https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html] — IP blocked; substituted Polymarket
  [FETCH FAILED: https://api.llama.fi/emission/{aerodrome-v1,hyperliquid}] — HTTP 402 Payment Required; AERO emission derived from a supply delta, HYPE unlock schedule UNRESOLVED
  [FETCH FAILED: https://open-api-v3.coinglass.com/api/futures/liquidation/history] — API key required; aggregate liquidation data UNAVAILABLE
  [FETCH FAILED: bitcoin-data.com exchange-balance / lth-supply / sth-supply / supply-in-profit / reserve-risk / thermocap / realized-cap / mayer-multiple] — HTTP 429 hourly rate limit; the BTC on-chain read rests on 8 of 13 intended metrics
  [UNAVAILABLE] Exchange balance / netflow data — every keyless source blocked or rate-limited. Unavailable, not zero.
  [UNAVAILABLE] TON and JUP token-specific journalism — near-zero coverage across four independent query paths.
```

---

## Step 4 — Verdict Critic

**Pre-flight critic list (must equal universe count):**
```
1. BTC — HOLD      7. JUP  — HOLD
2. ETH — HOLD      8. UNI  — HOLD
3. SOL — SELL      9. AERO — SELL
4. TON — SELL     10. PUMP — HOLD
5. HYPE — SELL    11. LINK — SELL
6. AAVE — SELL
Total: 11/11 ✓
```
⚠️ **Process deviation, declared:** the skill specifies one critic subagent per token. This run used **three critic subagents covering 3 + 3 + 5 tokens**, plus a separate independent skeptic gate. Coverage is 11/11 but independence between tokens within each critic is lower than a per-token spawn. Stated rather than hidden.

**✅ Verdict Critic: 11/11 tokens reviewed. Result: 11 FLAG, 0 clean PASS.** Every flag was acted on before Block 1 was written.

| # | Token | Defect found | Action taken |
|---|---|---|---|
| 1 | **HYPE** | Unlock catalyst self-contradictory (2.8% of 222.4M = $359M, not $817M) and a tracker puts the next unlock at 2026-08-06 / 9.92M HYPE / ~$595M. Emission API paywalled. | **SELL → HOLD.** Catalyst marked UNRESOLVED; cannot drive a signal. |
| 2 | **AAVE** | "Paused 99 days since 2026-04-19" contradicted — non-zero holders-revenue on 2026-04-30, 05-26, and **2026-06-24 ($576,537)**. Actual streak ~33 days. "No restart condition" 52 days stale — 2026-06-25 statement announced immutable automated buybacks. V4 quote unsourced. | **SELL → HOLD.** All three claims corrected in Block 2. |
| 3 | **UNI** | "v4 contributes exactly zero" is mid-change — v4 fee activation cleared Snapshot, on-chain vote 2026-07-22. | Corrected; flagged as the book's one dated upward catalyst. |
| 4 | **AERO** | The 1.9× emission ratio was called an *upper* bound; CoinGecko circulating **excludes veAERO locks**, making it a **lower** bound. Sign error. | Corrected — bear case **strengthened**, SELL retained. |
| 5 | **SOL** | "Chain fees $15.06M/30d" is the narrow L1 base-fee adapter, not chain fees — real figure $211.2M/30d, and weekly fees are **+19.85%**. Unanimity flagged as low-independence. Adoption cluster (stablecoins >$15B, JTX, LayerZero/Keeta, Grayscale) unpriced. | Corrected; SELL retained on direction (−38.8% run-rate) with counterweights stated. |
| 6 | **TON** | "−49.2% from 52w high" wrong — real 52w high $3.5747 (2025-08-02) = **−58.5%**; venue history truncated. "Zero journalism" too strong — two items Jul 21–22. | Corrected — bear case **strengthened**, SELL retained. |
| 7 | **JUP** | Hyperliquid funding **−25.94% → live +1.97%**. | Datapoint removed from the bear case. |
| 8 | **PUMP** | "Not a protocol event" falsified — BOOST mode activated 2026-07-21 in-window. | Corrected in PUMP's favour; HOLD retained on the extended zone. |
| 9 | **LINK** | Real weakness is **lumpiness (304/355 zero days)**, not unverifiable revenue — deposits are on-chain, only attribution is not. Aave standardised on CCIP 2026-07-21, unpriced by five bears. | Reframed; SELL retained on the 114× multiple. |
| 10 | **BTC** | "~$9.3B underwater" → **$9.09B**. Strategy framing one-sided (omits first-ever STRC preferred buyback and Benchmark's counter-read). Iran pause, BOE/BOJ and Galaxy dormant-supply data unpriced. | Corrected; the bear framing is now labelled contested. |
| 11 | **ETH** | Bull pillar (+$103.9M 5-day ETF streak) **snapped Jul 25**; cited from a dead window while bear legs were current. CLARITY Act absent. | Corrected; weekly-streak framing substituted. |

**Cross-cutting pattern the critics identified:** the panel repeatedly read a mechanic's *current state* and treated it as structural, without checking whether governance was mid-change (UNI, AAVE), whether the metric mean-reverts hourly (JUP funding), or whether a derivation's bias had a known sign (AERO). That is the single most important process finding of this run.

---

## Step 5 — Skeptic gate

Independent re-verification by a separate subagent, not a self-check.

```
SKEPTIC GATE — 2026-07-27
VERIFIED: 34    CHALLENGED: 6    UNVERIFIABLE: 5
VERDICT: CHALLENGES OUTSTANDING -> all 6 challenges resolved below before publication
```

**Verified (34) — the load-bearing levels all held.** All 11 prices confirmed against 2–4 independent venues. **BTC 200wMA $63,526 independently recomputed from 669 Kraken weekly bars at $63,462–63,687 (≤0.25% error)** — the report's most important level. BTC SMA200, BTC 52w high $126,200 (Kraken daily high 126,198.10 on 2025-10-06), and the ETH/AAVE/LINK 200-week MAs all reproduced within 0.4%. The entire macro block (Fed target and date, CPI, M2, 2y/10y, DXY, F&G) is clean. Strategy's 843,775 BTC / $75,476 average / $3.75B USD reserve are **verbatim-confirmed from the EDGAR 8-K**.

**Challenged (6) — all resolved in this document:**
| Claim | Resolution |
|---|---|
| HYPE unlock 2.8% = $817M (BLOCKING) | Self-contradictory by ~2.3×. Neither figure published as fact; **signal downgraded SELL → HOLD** |
| AAVE "paused since 2026-04-19" (MATERIAL) | Corrected to **last non-zero print 2026-06-24**, ~33-day streak; **signal downgraded SELL → HOLD** |
| Brent "−7%" (MATERIAL) | Corrected to **−11.0%** ($100.69 → $89.59) |
| WTI "−9.3%" (MINOR) | Corrected to **−9.7%** ($92.19 → $83.24) |
| BTC "+1.9% above 200wMA" (MINOR) | Range published as **+1.2% to +1.9%** depending on spot; the thesis gets tighter, not looser |
| All 11 prices ~+0.6% above venues, zero below (MINOR) | Stale-snapshot bias; **price snapshot now timestamped 15:20 UTC** at the top of this report |

**Unverifiable (5) — labelled, never presented as fact:** IBIT's $415M share of the $465M two-day outflow (Farside behind Cloudflare, Coinglass HTTP 500 — the aggregate is confirmed, the issuer split is not); LINK's "$206k of $4.84M on-chain" (an unreproduced internal computation); **BTC put/call "0.52 from 0.76"** (venue and metric unspecified — live Deribit gives 0.4285 by open interest and 0.8184 by 24h volume; neither is 0.52, so this is cited as journalism, not as a measurement); HYPE FDV $58.1B vs CoinGecko's $55.1B (methodology mismatch); the HYPE unlock calendar itself (emission API paywalled).

**Additional finding the skeptic surfaced independently:** the "skipped purchases for five weeks" framing understates the case — Strategy also **sold 3,588 BTC** in early July (1,363 on 6/29–6/30 plus 2,225 on 7/1–7/5, per the 2026-07-06 8-K), cutting holdings from 847,363 to 843,775. It is a net seller, not merely an abstainer.

---

## Upcoming dated catalysts

| Date (ET) | Event | Relevance |
|---|---|---|
| **Jul 29, 2:00pm** | **FOMC decision**, est. 3.75% (prev. 3.75%) — 28–33% hike odds | **BOOK-WIDE, the week's binary** |
| Jul 29 | Polygon Ithaca hard fork; HOOD and RIOT earnings | adjacent |
| **Jul 30, 8:30am** | **US PCE price index YoY (June)**, prev. 4.1%; Core PCE prev. 3.4% | **the print that sets the hike tail** |
| Jul 30 | US Q2 GDP advance; BoE decision; BoJ decision; **COIN and MSTR earnings post-market** | MSTR's first print since the buying pause |
| Jul 31 | **FTX Recovery Trust fifth creditor distribution begins (~$900M)** | book-wide supply/liquidity |
| **~Aug 6** | **HYPE unlock — date and size CONTESTED** (Jul 29 vs Aug 6; $359M / $595M / $817M) | **resolve before acting on HYPE** |
| ~Aug 7 | Senate leaves for recess — CLARITY Act window closes | book-wide regulatory |
| Aug 23 / Aug 26 | EU HTX sanctions take effect / BitMart ends all trading | counterparty risk |
| Sep 2026 | AERO Predictive Allocation replaces gauge voting | changes AERO's accrual mechanism |

---

## Declared gaps

1. **TradingView MCP unavailable** — OHLCV from OKX/Coinbase public APIs, indicators computed locally. All prices and the four load-bearing MAs independently verified against Kraken/CoinGecko/Coinbase/Coinpaprika.
2. **%52wH is truncated for TON, HYPE and AERO** — fewer than 365 daily bars available on the venue used. TON corrected to −58.5%; HYPE's −24.3% and AERO's −72.2% are lower bounds on the true drawdown.
3. **200wMA is INSUFFICIENT for 5 of 11 tokens** (TON 37w, HYPE 39w, PUMP 55w, AERO 130w, JUP 131w) — no long-horizon structural anchor exists; those five are capped at BUY(small) by rule regardless of verdict.
4. **BTC on-chain read rests on 8 of 13 intended metrics** — bitcoin-data.com hourly rate limit.
5. **Exchange-balance / netflow and aggregate liquidation data UNAVAILABLE** — all keyless sources blocked or key-gated. Unavailable, not zero.
6. **HYPE unlock date and size UNRESOLVED** — three mutually inconsistent figures, authoritative API paywalled.
7. **Hyperliquid funding sits at the protocol baseline for 6 of 11 tokens** — no directional information; must not be read as bullish crowding.
8. **Critics run 3-per-batch rather than 1-per-token** — 11/11 coverage, lower per-token independence. Declared.
9. **TON and JUP have near-zero token-specific journalism**; AAVE, AERO and LINK have no crypto-native journalism coverage in the window — their news items are aggregator/community tier with ingest-time dates, so materiality is correspondingly weaker.
