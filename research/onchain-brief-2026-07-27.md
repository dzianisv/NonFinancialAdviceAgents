# analyse-onchain — RESEARCH BRIEF 2026-07-27

**Seat:** on-chain researcher (analyse-onchain lens)
**Scope:** 11 tokens — BTC, ETH, SOL, TON, HYPE, AAVE, JUP, UNI, AERO, PUMP, LINK
**Mode:** DATA ONLY — no votes, no zone verdicts, no buy/sell recommendations
**Skill:** `.claude/skills/analyse-onchain/SKILL.md`

---

## Sources fetched

All URLs below were fetched live via `curl` on 2026-07-27. Quotes are verbatim from the response bodies.

| Tier | URL | Verbatim quote | Why this tier |
|---|---|---|---|
| T1 | `https://api.alternative.me/fng/?limit=1` | `"value": "30", "value_classification": "Fear", "timestamp": "1785110400"` | Canonical publisher of the Crypto Fear & Greed index, raw JSON straight from source. |
| T1 | `https://bitcoin-data.com/api/v1/mvrv/last` | `{"d":"2026-07-26","unixTs":1785024000,"mvrv":1.2465}` | Dedicated BTC on-chain API computing MVRV from UTXO-set realized cap, dated asof field. |
| T1 | `https://bitcoin-data.com/api/v1/mvrv-zscore/last` | `{"d":"2026-07-26","unixTs":1785024000,"mvrvZscore":0.3954}` | Same primary on-chain source; headline cycle-phase metric with explicit as-of date. |
| T1 | `https://bitcoin-data.com/api/v1/nupl/last` | `{"d":"2026-07-26","unixTs":1785024000,"nupl":0.1977}` | Derived directly from the UTXO cost-basis ledger, not a media summary. |
| T1 | `https://bitcoin-data.com/api/v1/realized-price/last` | `{"d":"2026-07-26","unixTs":1785024000,"realizedPrice":52468.49}` | Aggregate on-chain cost basis computed from realized cap / supply. |
| T1 | `https://bitcoin-data.com/api/v1/puell-multiple/last` | `{"d":"2026-07-26","unixTs":1785024000,"puellMultiple":0.7521}` | Miner-issuance-value metric computed from coinbase emission. |
| T1 | `https://bitcoin-data.com/api/v1/lth-sopr/last` | `{"d":"2026-07-26","unixTs":1785024000,"lthSopr":0.8875}` | Spent-output realized-profit ratio for >155d coins, computed from spent UTXOs. |
| T1 | `https://bitcoin-data.com/api/v1/sth-sopr/last` | `{"d":"2026-07-26","unixTs":1785024000,"sthSopr":1.0008}` | Same primary spent-output ledger, short-term-holder cohort. |
| T1 | `https://bitcoin-data.com/api/v1/sopr/last` | `{"d":"2026-07-26","unixTs":1785024000,"sopr":1.0001}` | Aggregate spent-output profit ratio direct from chain data. |
| T1 | `https://api.blockchain.info/stats` | `"hash_rate":8.596753089052123E11,"n_tx":708382,"n_blocks_mined":137,"minutes_between_blocks":9.8456,"totalbc":2006202812500000,"n_blocks_total":959849,"difficulty":126231507121868` | Node-derived network statistics served by a full-node operator. |
| T1 | `https://mempool.space/api/v1/mining/hashrate/1m` | `{"timestamp":1782604800,"avgHashrate":1.100452340139307e+21}` | mempool.space runs its own indexed Bitcoin full node. |
| T1 | `https://api.blockchain.info/charts/miners-revenue?timespan=7days&format=json` | `"name":"Miners Revenue","unit":"USD","period":"day","description":"Total value of coinbase block rewards and transaction fees paid to miners.","values":[{"x":1784505600,"y":3.257994641959805E7}` | Computed from coinbase outputs on-chain. |
| T1 | `https://api.mainnet-beta.solana.com` (RPC `getSupply`) | `"value":{"circulating":583094795123112751,"nonCirculating":48027972032456600,"total":631122767155569351}` | Response from a Solana mainnet validator RPC node — the chain is the source. |
| T1 | `https://api.mainnet-beta.solana.com` (RPC `getInflationRate`) | `"result":{"epoch":1008,"foundation":0.0,"total":0.03724738633549205,"validator":0.03724738633549205}` | Live protocol inflation parameter read directly from a mainnet node. |
| T1 | `https://tonapi.io/v2/blockchain/masterchain-head` | `{"tx_quantity":3,"value_flow":{"from_prev_blk":{"grams":2451466944953454016` | TON masterchain block data served from an indexed TON node. |
| T1 | `https://ultrasound.money/api/v2/fees/supply-over-time` | `{"block_number":25583423,"d1":[],"d30":[{"supply":121815680.95592187,"timestamp":"2026-06-27T15:00:00Z"}` … last `{"supply":121884168.13268945,"timestamp":"2026-07-21T20:14:35Z"}` | ETH supply computed from execution-layer state by ultrasound.money's own node. |
| T1 | `https://www.okx.com/api/v5/market/ticker?instId=LINK-USDT` | `{'instId': 'LINK-USDT', 'last': '8.594', 'open24h': '8.534', 'high24h': '8.917', 'low24h': '8.516', 'ts': '1785165505229'}` | Exchange matching-engine last-trade price. |
| T1 | `https://api.coinbase.com/v2/prices/LINK-USD/spot` | `{"data":{"amount":"8.5815","base":"LINK","currency":"USD"}}` | Exchange's own spot price endpoint. |
| T1 | `https://api.kraken.com/0/public/Ticker?pair=LINKUSD` | `LINKUSD last= 8.584810 open= 8.816060` | Exchange matching-engine ticker. |
| T2 | `https://api.llama.fi/v2/chains` | `{"gecko_id": "ethereum", "tvl": 42111139691.4687, "name": "Ethereum"}`; `{"gecko_id": "solana", "tvl": 4926942807.291301}`; `{"gecko_id": "hyperliquid", "tvl": 1260016468.8594227}`; `{"gecko_id": "the-open-network", "tvl": 64899622.331019685, "tokenSymbol": "GRAM"}`; `{"tvl": 4657795255.2597685, "name": "Base"}` | Open-methodology aggregator indexing many contracts, one layer removed from chains. |
| T2 | `https://api.llama.fi/summary/fees/{...}?dataType=dailyFees` | Aave `{'total24h': 967759, 'total7d': 6762935, 'total30d': 28094909, 'total1y': 892864523, 'totalAllTime': 2238158297}`; Uniswap `{'total24h': 2759512.05, 'total7d': 24353285.55, 'total30d': 93240408.55, 'total1y': 859561587.55}`; Jupiter Aggregator `{'total30d': 2569241, 'total1y': 35614965}`; Aerodrome Slipstream `{'total30d': 5074467, 'total1y': 132863263}`; pump.fun `{'total30d': 25672514, 'total1y': 404490347}`; Chainlink `{'total24h': 7449, 'total7d': 1210399, 'total30d': 4841696, 'total1y': 61445905, 'totalAllTime': 64661554}`; Hyperliquid Perps `{'total30d': 49575738, 'total1y': 971797890}`; Solana `{'total30d': 15057242, 'total1y': 276418849}`; Jito `{'total30d': 6555618, 'total1y': 233299225}`; TON `{'total24h': 3186, 'total7d': 20249, 'total30d': 77181, 'total1y': 2940742, 'totalAllTime': 17262440}` | Adapter-based aggregation with published methodology, not the protocols' own accounting. |
| T2 | `https://api.llama.fi/summary/fees/hyperliquid-perps?dataType=dailyHoldersRevenue` | `{'total24h': 651931, 'total7d': 7190707, 'total30d': 35019624, 'total1y': 745821450}` | DefiLlama's own classification of which fee share reaches token holders. |
| T2 | `https://api.llama.fi/protocol/{aave,uniswap,jupiter,aerodrome,chainlink,lido}` | `name Aave \| tvl_sum=14967111216 \| staking= 227643135`; `name Uniswap \| tvl_sum=3070334357 \| staking= None`; `name Jupiter \| tvl_sum=1569707406`; `name Aerodrome \| tvl_sum=306797426`; `name Chainlink \| tvl_sum=1988167982 \| staking= 378955286`; `Lido TVL: {'Ethereum': 18366374866.25202, 'Solana': 3789757.09145}` | Aggregator-computed TVL across contract sets. |
| T2 | `https://api.coingecko.com/api/v3/coins/markets?...` | `BTC mcap=$1,294,850,556,738 circ=20,062,009`; `ETH mcap=$232,325,802,625 circ=120,682,636`; `SOL mcap=$43,948,540,501 fdv=$47,568,466,053`; `HYPE mcap=$12,944,226,563 fdv=$55,589,793,334 circ=222,445,714 total=955,307,079`; `LINK mcap=$6,422,717,699 fdv=$8,585,373,550`; `GRAM mcap=$4,032,924,325 fdv=$7,699,146,976`; `UNI mcap=$2,397,946,126 fdv=$3,422,656,983`; `AAVE mcap=$1,535,069,335 fdv=$1,593,047,221`; `PUMP mcap=$845,012,859 fdv=$1,797,142,608`; `JUP mcap=$617,642,222 fdv=$1,276,544,534`; `AERO mcap=$429,667,845 fdv=$857,904,327` | Market-data aggregator; supply figures curated, not read from chain. |
| T2 | `https://api.coingecko.com/api/v3/simple/price?ids=chainlink&vs_currencies=usd` | `{"chainlink":{"usd":8.6,"usd_24h_change":0.9243603795812764,"last_updated_at":1785165420}}` | Aggregator mid-price across venues. |

### Fetch failures (nothing imputed)

```
[FETCH FAILED: https://bitcoin-data.com/api/v1/exchange-balance-btc/last]      HTTP 429 RATE_LIMIT_HOUR_EXCEEDED (hourly limit 10; retried after 20s, still 429)
[FETCH FAILED: https://bitcoin-data.com/api/v1/mayer-multiple/last]            HTTP 429 RATE_LIMIT_HOUR_EXCEEDED
[FETCH FAILED: https://bitcoin-data.com/api/v1/lth-supply/last]                HTTP 404 Not Found
[FETCH FAILED: https://bitcoin-data.com/api/v1/bitcoin-supply-in-profit/last]  HTTP 429
[FETCH FAILED: https://bitcoin-data.com/api/v1/reserve-risk/last]              HTTP 429
[FETCH FAILED: https://beaconcha.in/api/v1/epoch/latest]                       "Unauthorized: a valid API key is required."
[FETCH FAILED: https://ultrasound.money/api/fees/supply-growth]                "Not Found"
```

---

## PRICE RECONCILIATION — LINK (skeptic gate)

The pre-pulled desk price for LINK was **$8.599**. Verified against four independent venues:

| Source | Price | Timestamp |
|---|---|---|
| OKX LINK-USDT (matching engine) | **$8.594** | ts 1785165505229 |
| Kraken LINKUSD (matching engine) | **$8.5848** | live |
| Coinbase LINK-USD spot | **$8.5815** | live |
| CoinGecko simple/price (aggregate) | **$8.60** | last_updated_at 1785165420 |

**Verdict: pre-pulled $8.599 is CONFIRMED.** Max spread across venues is $0.0185 (0.22%) — normal venue dispersion, not a data error. **Authoritative: OKX $8.594** (matching-engine last trade, same venue family as the rest of the desk pull, tightest timestamp).

**Separate discrepancy found — flagged to CIO:** `research/crypto-portfolio-2026-07-24.md:211` and `:242` state LINK **"spot $8.80 as of Jul 27"**. Four venues at 15:18 UTC on Jul 27 say **$8.58–8.60**. The $8.80 figure in that report is **stale or wrong by ~2.4%** and should be corrected before that report is published. That report's own reconciliation of the earlier `$16.73` bogus print (line 211) is sound and independently consistent with my pull — LINK never crashed 50%; it is trading in the $8.5–8.6 band.

---

## Per token

### BTC
- **Cost basis:** realized price **$52,468.49** (asof 2026-07-26) vs spot $64,704 → spot is **1.233x** aggregate cost basis. MVRV **1.2465**, MVRV-Z **0.3954**. Price is ABOVE realized price, so the market is **NOT** in classic sub-cost-basis capitulation despite −48.7% from the 52w high.
- **Crowd psychology:** NUPL **0.1977** → "hope" band (0–0.25), thin aggregate unrealized profit. F&G **30 "Fear"**. Aggregate SOPR 1.0001 and STH-SOPR 1.0008 = coins moving at roughly break-even, but LTH-SOPR **0.8875** → long-term holders (>155d) spending at an average **~11% realized loss**. This LTH/STH divergence is the single most informative number in the pull: **old supply, not new supply, is taking the pain.**
- **Miners:** Puell **0.7521** — below 1.0 (issuance value under its 365d average) but above the <0.5 capitulation threshold. Miner revenue ~$25.2M–$36.3M/day over the sampled week. Difficulty 126,231,507,121,868. blockchain.info hash_rate 8.5968e11 GH/s ≈ **860 EH/s**; mempool.space 1-month daily series ~1.10e21 H/s ≈ **1,100 EH/s** — different windows/estimators, **do not average them**. No hashrate collapse either way.
- **Chain use:** 708,382 tx in the sample window, 137 blocks, 9.8456 min between blocks, 20,062,028.125 BTC mined of 21M.
- **Cycle position:** MVRV-Z 0.395 sits between the <0 capitulation floor and the 1–4 mid-cycle band — the low-but-not-yet-washed-out shelf. Spot $64,704 vs 200wMA $63,526 = **only +1.9% above it**.
- **Invalidation anchors:** realized price **$52,468** (spot below = true on-chain capitulation regime); MVRV-Z crossing **<0**; Puell **<0.5**; 200wMA **$63,526** losing on a weekly close.
- `[UNAVAILABLE]` exchange balances, LTH supply level, supply-in-profit, reserve risk, Mayer multiple — rate-limited out this hour; not imputed.

### ETH
- **Supply is INFLATIONARY, not "ultrasound":** 121,815,680.96 ETH at 2026-06-27T15:00:00Z → 121,884,168.13 ETH at 2026-07-21T20:14:35Z (block 25,583,423). That is **+68,487.18 ETH over a 24.2-day window** = +0.056% for the window ≈ **+0.85%/yr annualized**. Burn is not offsetting issuance at current fee levels.
- No verifiable MVRV/NUPL/realized-price equivalent was fetched for ETH — `[UNAVAILABLE]`. **Do not port BTC cycle thresholds onto ETH.**
- **Ecosystem:** Ethereum chain TVL **$42,111,139,691** — largest of any chain in the pull (Solana $4,926,942,807, Base $4,657,795,255, Bitcoin $4,267,821,694, Hyperliquid L1 $1,260,016,469, TON $64,899,622). Lido alone holds **$18,366,374,866** on Ethereum ≈ **43.6% of Ethereum chain TVL** — large single-protocol concentration.
- **Market:** mcap $232,325,802,625 on 120,682,636 circulating; no unlock overhang (fdv = mcap). Spot $1,930 vs 200wMA $2,482 → **22.2% BELOW** the 200-week mean, a deeper structural discount than BTC's +1.9% above.
- **Invalidation anchors:** supply growth flipping negative (burn > issuance); Ethereum chain TVL losing ~$42B; 200wMA $2,482 reclaim.

### SOL
- **Supply direct from mainnet validator RPC:** circulating 583,094,795.12 SOL, non-circulating 48,027,972.03, total 631,122,767.16. Circulating is **92.4%** of total — low locked overhang.
- **Protocol inflation live at epoch 1008:** total **3.725%/yr**, all to validators (foundation 0.0). Real ongoing dilution — **highest verified issuance rate of any token in this brief.**
- **Fee generation falling:** chain fees 30d $15,057,242 (≈$183.2M annualized) vs trailing 1y $276,418,849 → run-rate ≈**34% below** trailing-year pace. Jito 30d $6,555,618 vs 1y $233,299,225 → MEV-tip revenue down ≈**66%**. Raydium 30d $3,421,313 vs 1y $165,346,272.
- **Valuation context:** mcap $43,948,540,501 / ≈$183.2M annualized chain fees ≈ **240x fees** (chain fees only; excludes MEV and app layer). Chain TVL $4,926,942,807. Spot $75.52 is **30.1% below** 200wMA $108.06.
- **Invalidation anchors:** chain fee run-rate reclaiming ~$23M/30d; inflation schedule change; TVL below ~$4.9B.

### TON
- Chain is live and producing — masterchain head returned `"tx_quantity":3`. Activity is extremely thin.
- **Fees near-zero in absolute terms:** 30d **$77,181**, 7d $20,249, 24h $3,186, 1y $2,940,742, all-time $17,262,440. Against mcap $4,032,924,325 that is ≈**4,300x annualized fees** — worst fee-to-cap ratio in the basket by two orders of magnitude.
- **TVL $64,899,622** — smallest chain TVL in the pull, 0.15% of Ethereum's and 1.3% of Solana's, despite a $4.03B market cap.
- **Supply overhang:** 2,735,044,545 circulating of 5,221,399,719 total → only **52.4% circulating**; FDV $7,699,146,976 = **1.91x mcap**. No 200wMA (37w of history) → no long-horizon on-chain anchor.
- **Invalidation anchors:** monthly fees breaking meaningfully above ~$77k/30d; TVL exiting the ~$65M range.
- **Honest note:** no cycle/valuation on-chain metric (MVRV/NUPL/realized price) exists for TON. The above is activity and supply, **not valuation**.

### HYPE
- **Real, verifiable revenue — strongest of the DeFi names.** Perps fees 30d $49,575,738; **holders' revenue 30d $35,019,624** (≈$426.1M annualized), 1y $745,821,450. Total Hyperliquid (perps + spot) fees 30d $51,300,674, all-time $1,446,775,640.
- **Revenue decelerating:** perps 30d annualized ≈$603.2M vs trailing 1y $971,797,890 → ≈**38% below** trailing-year pace. Spot orderbook 30d $1,360,509 vs 1y $52,186,519 → down ~68% annualized.
- **Valuation:** mcap $12,944,226,563 / $426.1M annualized holders' revenue ≈ **30x**. On FDV $55,589,793,334 ≈ **130x**.
- **Supply overhang is the dominant hard fact:** 222,445,714 circulating of 955,307,079 total = **only 23.3% circulating**. FDV is **4.29x mcap** — largest dilution gap in the basket. HYPE is also the least drawn-down token here (−24.3% vs BTC −48.7%).
- Chain TVL $1,260,016,469. No 200wMA (39w history) — no long-horizon structural anchor.
- **Invalidation anchors:** holders' revenue below ~$35M/mo; unlocks moving circulating toward total; L1 TVL breaking $1.26B.
- **Honest note:** no MVRV/NUPL/realized-price equivalent exists for HYPE. Above is revenue and supply, not on-chain valuation.

### AAVE
- **Fees:** 30d $28,094,909 (≈$341.8M annualized), 7d $6,762,935, 24h $967,759, 1y $892,864,523, all-time $2,238,158,297. Run-rate ≈**62% BELOW** trailing-year pace — **steepest fee decay of any protocol in this pull.**
- **TVL $14,967,111,216** across chains, of which $227,643,135 is staking (Safety Module). TVL is **9.75x market cap** — highest TVL-to-mcap ratio here.
- **Supply nearly fully diluted:** 15,417,691 circulating of 16,000,000 max = **96.4%**. FDV $1,593,047,221 vs mcap $1,535,069,335 = 1.04x. Effectively no unlock overhang.
- **Valuation context:** mcap / ≈$341.8M annualized protocol fees ≈ **4.5x**. Protocol fees ≠ token-holder revenue for Aave — the split was not fetched, so **do not treat 4.5x as a P/E**.
- Spot $99.85 is **27.4% below** 200wMA $137.57; −74.1% from 52w high; −85.0% from ATH.
- **Invalidation anchors:** 30d fees below ~$28M; TVL losing ~$15B; fee-decay reversing toward the $74M/mo trailing-year pace.
- **Honest note:** no on-chain cycle-valuation metric exists for AAVE.

### JUP
- **Fees:** 30d $2,569,241 (≈$31.3M annualized), 7d $506,658, 24h $69,178, 1y $35,614,965, all-time $109,574,153 (Jupiter Aggregator adapter only). Run-rate ≈**12% below** trailing-year pace — **mildest fee decay in the basket.**
- **TVL $1,569,707,406** = 2.54x its $617,642,222 market cap.
- **Supply overhang severe:** 3,320,312,968 circulating of 6,862,431,393 total = **48.4% circulating**. FDV $1,276,544,534 = **2.07x mcap**. Roughly half the supply still to come.
- **Valuation context:** mcap / ≈$31.3M annualized fees ≈ **19.7x**. Fees are aggregator take, not necessarily distributed to holders — distribution mechanics not fetched, **do not assume accrual**.
- No 200wMA (131w history). −70.1% from 52w high, −90.7% from ATH. Weakest 30d tape in the basket at **−18.8%**.
- **Invalidation anchors:** 30d fees below ~$2.5M; TVL breaking ~$1.57B; unlock cadence on the remaining 3.54B tokens.
- **Honest note:** no on-chain cycle-valuation metric exists for JUP.

### UNI
- **The only protocol in this basket with fees ACCELERATING.** 30d $93,240,408 (≈$1,134.5M annualized) and 7d $24,353,285.55 (≈$1,270M annualized) vs trailing 1y $859,561,588 → run-rate **~32–48% ABOVE** trailing-year pace. All-time fees $5,703,782,889, largest in the basket.
- **Critical caveat:** these are **LP fees**. Whether any reaches UNI holders was not verified — fee-switch state is `[UNAVAILABLE]`. **Do not compute a holder yield from the $1.13B figure.**
- TVL $3,070,334,357, staking None.
- **Supply:** 625,127,562 circulating of 892,262,420 total = **70.1% circulating**; FDV $3,422,656,983 = 1.43x mcap $2,397,946,126 — moderate overhang.
- Spot $3.841 is **43.7% below** 200wMA $6.824 and **−91.5% from ATH** — deepest ATH drawdown in this brief. Strongest 30d tape at **+28.1%**.
- **Invalidation anchors:** 7d fee run-rate falling below ~$16.5M/wk trailing-year pace; TVL losing ~$3.07B; any change in fee-switch status.
- **Honest note:** no on-chain cycle-valuation metric exists for UNI.

### AERO
- **Fees (Slipstream):** 30d $5,074,467 (≈$61.7M annualized), 7d $937,610, 24h $145,320, 1y $132,863,263, all-time $306,441,108. Run-rate ≈**54% below** trailing-year pace.
- **Incomplete-coverage warning:** I fetched the **Slipstream adapter ONLY**. Aerodrome's classic/v2 AMM fees are NOT included, so total protocol fees are higher by an unfetched amount. Any P/F built on this is an **upper bound on the multiple**.
- Protocol TVL $306,797,426 against Base chain TVL $4,657,795,255 → Aerodrome is ~**6.6% of its host chain's TVL**.
- **Supply overhang:** 974,205,039 circulating of 1,945,164,684 total = **50.1% circulating**; FDV $857,904,327 = 2.00x mcap $429,667,845. Aerodrome uses continuous emissions, so total supply is **not a fixed cap** — treat 50.1% as a snapshot, not a schedule.
- **Valuation context:** mcap / ≈$61.7M annualized Slipstream fees ≈ **7.0x** (upper bound per coverage gap).
- No 200wMA (130w history). −72.2% from 52w high, −80.9% from ATH.
- **Invalidation anchors:** TVL breaking ~$307M; Slipstream 30d fees below ~$5.0M; Base chain TVL losing ~$4.66B.
- **Honest note:** no on-chain cycle-valuation metric exists for AERO.

### PUMP
- **Fees:** 30d $25,672,514 (≈$312.4M annualized), 7d $6,663,372, 24h $993,107, 1y $404,490,347, all-time $1,150,549,001. Run-rate ≈**23% below** trailing-year pace — real, large, only moderately decaying cash generation.
- **Valuation context:** mcap $845,012,859 / ≈$312.4M annualized fees ≈ **2.7x**; on FDV $1,797,142,608 ≈ **5.8x**. Numerically the cheapest fee multiple in this basket.
- **Explicit caution:** I did **NOT** fetch any revenue-share, buyback, or token-accrual mechanism for PUMP. Whether ANY of that $312M reaches token holders is `[UNAVAILABLE]`. **A 2.7x "P/F" with no verified accrual path is not a valuation** — treat it as an activity statistic.
- **Supply:** 397,831,270,680 circulating of 846,093,074,351 total = **47.0% circulating**; FDV 2.13x mcap. No protocol TVL recorded in this pull.
- **Tape:** RSI 69.0 (highest in basket, approaching overbought), 30d **+53.1%** (strongest move), yet still −76.3% from 52w high. No 200wMA (55w history).
- **Two sources only** (llama fees, coingecko markets) — thinnest evidence base in the brief; weight accordingly.
- **Invalidation anchors:** 30d fees below ~$25.7M; the unverified holder-accrual question resolving either way.
- **Honest note:** no on-chain cycle-valuation metric exists for PUMP.

### LINK
- **Price confirmed 4x** — see PRICE RECONCILIATION above. OKX $8.594 / Kraken $8.5848 / Coinbase $8.5815 / CoinGecko $8.60. Pre-pulled $8.599 valid.
- **The valuation outlier.** Fees 30d $4,841,696 (≈$58.9M annualized), 7d $1,210,399, 24h $7,449, 1y $61,445,905, all-time $64,661,554. Against mcap $6,422,717,699 that is ≈**109x annualized fees**; on FDV $8,585,373,550 ≈**146x** — by far the most expensive fee multiple among tokens with measurable revenue.
- **Revenue is brand-new, not established:** total1y $61,445,905 vs totalAllTime $64,661,554 → **95.0% of all fees Chainlink has ever recorded on this adapter were generated in the last 12 months.** Run-rate roughly flat vs trailing year (≈$58.9M vs $61.4M). Note the 24h print of $7,449 vs 7d of $1,210,399 — **fee arrival is extremely lumpy, single-day figures are meaningless here.**
- TVL $1,988,167,982 of which $378,955,286 is staking.
- **Supply:** 748,099,970 circulating of 1,000,000,000 total = **74.8% circulating**; FDV = 1.34x mcap — moderate overhang.
- **Structure:** spot $8.599 is **31.5% below** 200wMA $12.561; −69.1% from 52w high; −83.7% from ATH.
- **Invalidation anchors:** annualized fee run-rate breaking above/below ~$59M; staked LINK moving off ~$379M; 200wMA $12.561.
- **Honest note:** no on-chain cycle-valuation metric exists for LINK.

---

## Cross-token honesty notes

- **Genuine on-chain CYCLE valuation (MVRV-Z, NUPL, realized price, Puell, SOPR cohorts) exists in this pull for BTC ONLY.** ETH got verified supply/issuance but no cost-basis metrics. Everything from SOL down is activity, revenue, supply and TVL — **NOT on-chain valuation**. No substitutes were invented.
- BTC exchange balances, LTH supply level, supply-in-profit, reserve risk and Mayer multiple were all rate-limited out. **The BTC read rests on 8 metrics, not the full 13** — weaker than a complete pull.
- **Fee run-rate direction (30d annualized vs trailing 1y) is falling for 7 of 8 fee-generating protocols:** AAVE −62%, HL spot −68%, Jito MEV −66%, AERO −54%, HYPE perps −38%, SOL chain −34%, PUMP −23%, JUP −12%. **UNI is the sole accelerator at +32% to +48%.** A broad, verifiable revenue contraction across the basket.
- **Circulating-supply overhang ranks** (circ % of total, lowest = worst dilution risk): HYPE 23.3% < PUMP 47.0% < JUP 48.4% < AERO 50.1% < TON 52.4% < UNI 70.1% < LINK 74.8% < SOL 92.4% < AAVE 96.4% < BTC/ETH 100%.
- ETH's inflationary supply print (+68,487 ETH / ~24d) is measured over a **24.2-day window, not a clean 30 days**, because the API's d30 series ended at 2026-07-21T20:14:35Z. The annualization scales that actual window; it is not a full-month figure.
- **DATA ONLY** — no votes, no zone verdicts, no buy/sell. All metrics decay; re-pull before any decision.
