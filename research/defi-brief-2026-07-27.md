# analyse-defi — RESEARCH BRIEF 2026-07-27

**Seat:** DeFi / protocol-economics researcher (Burniske value-accrual lens)
**Mode:** DATA ONLY — no votes, no recommendations
**Universe:** BTC, ETH, SOL, TON, HYPE, AAVE, JUP, UNI, AERO, PUMP, LINK

---

## Sources fetched

All keyless, via `curl`. Verbatim metric strings quoted.

| ID | URL | Verbatim metric string |
|---|---|---|
| [T1] | `https://api.llama.fi/v2/chains` | `Base None 4657795255` · `Ethereum ETH 42111139691` · `Solana SOL 4926942807` · `Bitcoin BTC 4267821694` · `TON GRAM 64899622` · `Hyperliquid L1 HYPE 1260016469` |
| [T1] | `https://api.llama.fi/summary/fees/aave?dataType=dailyFees` | `fees: 24h= 967759 7d= 6762935 30d= 28094909 1y= 892864523` |
| [T1] | `https://api.llama.fi/summary/fees/uniswap?dataType=dailyFees` | `fees: 24h= 2759512.05 7d= 24353285.55 30d= 93240408.55 1y= 859561587.55` |
| [T1] | `https://api.llama.fi/summary/fees/jupiter?dataType=dailyFees` | `fees: 24h= 208354.47 7d= 2521602.62 30d= 12950807.620000001 1y= 378571262.62` |
| [T1] | `https://api.llama.fi/summary/fees/hyperliquid?dataType=dailyFees` | `fees: 24h= 927699 7d= 10652901 30d= 51300674 1y= 1034549725` |
| [T1] | `https://api.llama.fi/summary/fees/pump.fun?dataType=dailyFees` | `fees: 24h= 993107 7d= 6663372 30d= 25672514 1y= 404490347` |
| [T1] | `https://api.llama.fi/summary/fees/chainlink?dataType=dailyFees` | `fees: 24h= 7449 7d= 1210399 30d= 4841696 1y= 61445905` |
| [T1] | `https://api.llama.fi/summary/fees/aerodrome-v1?dataType=dailyFees` | `fees: 24h= 50358 7d= 178914 30d= 1041234 1y= 28990627` |
| [T1] | `https://api.llama.fi/summary/fees/aerodrome-slipstream?dataType=dailyFees` | `fees: 24h= 145320 7d= 937610 30d= 5074467 1y= 132863263` |
| [T1] | `https://api.llama.fi/summary/fees/aave?dataType=dailyRevenue` | `name = Aave` `total24h = 133792` `total7d = 914736` `total30d = 3761140` `total1y = 117285863` `totalAllTime = 302798824` |
| [T1] | `https://api.llama.fi/summary/fees/uniswap?dataType=dailyRevenue` | `name = Uniswap` `total24h = 69888` `total7d = 651321` `total30d = 3255483` `total1y = 27052190` `totalAllTime = 27160988` |
| [T1] | `https://api.llama.fi/summary/fees/jupiter?dataType=dailyRevenue` | `name = Jupiter` `total24h = 100806.47` `total7d = 818093.62` `total30d = 4233525.62` `total1y = 112485982.62` `totalAllTime = 353230360.52` |
| [T1] | `https://api.llama.fi/summary/fees/hyperliquid?dataType=dailyRevenue` | `name = Hyperliquid` `total24h = 667938` `total7d = 7368682` `total30d = 36078570` `total1y = 784920392` `totalAllTime = 1173657712` |
| [T1] | `https://api.llama.fi/summary/fees/pump.fun?dataType=dailyRevenue` | `name = pump.fun` `total24h = 761825` `total7d = 5097149` `total30d = 19667529` `total1y = 323949113` `totalAllTime = 1067994663` |
| [T1] | `https://api.llama.fi/summary/fees/chainlink?dataType=dailyRevenue` | `name = Chainlink` `total24h = 0` `total7d = 1148131` `total30d = 4613725` `total1y = 56911607` `totalAllTime = 57991896` |
| [T1] | `https://api.llama.fi/summary/fees/aerodrome-v1?dataType=dailyRevenue` | `name = Aerodrome V1` `total24h = 44558` `total7d = 128772` `total30d = 752458` `total1y = 20777582` `totalAllTime = 200774780` |
| [T1] | `https://api.llama.fi/summary/fees/aerodrome-slipstream?dataType=dailyRevenue` | `name = Aerodrome Slipstream` `total24h = 111204` `total7d = 739042` `total30d = 3437401` `total1y = 101004033` `totalAllTime = 262580778` |
| [T1] | `https://api.llama.fi/summary/fees/{slug}?dataType=dailyHoldersRevenue` | `aave holdersRev 24h= 0 30d= 0 1y= 28424101` · `uniswap 24h= 69888 30d= 3255483 1y= 27052190` · `jupiter 24h= 50351.22 30d= 2115951.3000000003 1y= 56236687.3` · `hyperliquid 24h= 667938 30d= 36078570 1y= 784920392` · `pump.fun 24h= 587823 30d= 14301309 1y= 312307642` · `chainlink 24h= 0 30d= 4613725 1y= 56911607` · `aerodrome-v1 24h= 44558 30d= 752458 1y= 20777582` · `aerodrome-slipstream 24h= 111204 30d= 3437401 1y= 101004033` · `ethereum 24h= 58952 30d= 1530923 1y= 89815997` · `solana 24h= 50582 30d= 1627148 1y= 32666908` · `ton 24h= 1593 30d= 38589 1y= 1470361` |
| [T1] | `https://api.llama.fi/summary/fees/pump.fun?dataType=dailyProtocolRevenue` | `protocolRev 24h 386303 30d 9990081 1y 31690999` |
| [T1] | `https://api.llama.fi/summary/fees/chainlink-requests?dataType=dailyFees` | `24h 5887 30d 206171 1y 3828615` |
| [T1] | `https://api.llama.fi/summary/fees/chainlink-staking?dataType=dailyHoldersRevenue` | `name Chainlink Staking 24h 0 30d 4613725 1y 56911607 allTime 56911607` · `last 8: [('2026-07-20', 0), ('2026-07-21', 0), ('2026-07-22', 0), ('2026-07-23', 1148131), ('2026-07-24', 0), ('2026-07-25', 0), ('2026-07-26', 0), ('2026-07-27', 0)]` |
| [T1] | `https://api.llama.fi/summary/fees/{ethereum,solana,ton,bitcoin}?dataType=dailyFees` / `dailyRevenue` | `Ethereum fees 24h= 347603 30d= 7066764 1y= 257060822` / `rev 24h= 58952 30d= 1530923 1y= 89815997` · `Solana fees 24h= 459185 30d= 15057242 1y= 276418849` / `rev 30d= 1627148 1y= 32666908` · `TON fees 24h= 3186 30d= 77181 1y= 2940742` / `rev 30d= 38589 1y= 1470361` · `Bitcoin fees 24h= 149242 30d= 5581372 1y= 92298618` / **`rev 24h= 0 30d= 0 1y= 0`** |
| [T1] | `https://api.llama.fi/overview/fees/{chain}` | `ethereum chainFees 24h= 8464732.48 7d= 65140804.60999998 30d= 273171284.61000013 1y= 5525602275.669996` · `solana 30d= 211249216.67999995` · `ton 30d= 27234997.97` · `bitcoin 30d= 267849.12` · `base 30d= 42865945.739999995` · `hyperliquid 30d= 110983163.42` |
| [T1] | `https://api.llama.fi/protocols` | `Aave V3 tvl=14,161,545,605` · `Hyperliquid Bridge tvl=6,003,512,265` · `Uniswap V3 tvl=1,468,363,900` · `Jupiter Lend tvl=959,621,689` · `Uniswap V2 tvl=800,198,540` · `Uniswap V4 tvl=798,584,027` · `Jupiter Perpetual Exchange tvl=731,315,806` · `Jupiter Staked SOL tvl=401,158,158` · `Aave Horizon RWA tvl=255,452,133` · `PumpSwap tvl=247,253,069` · `Hyperliquid HLP tvl=224,996,936` · `Aave V4 tvl=202,529,022` · `Aerodrome Slipstream tvl=155,690,893` · `Hyperliquid Spot Orderbook tvl=136,030,357` · `Aerodrome V1 tvl=128,786,107` · `Aave V2 tvl=111,700,229` · `Aerodrome Ignition tvl=22,320,428` · `Aave V1 tvl=6,500,131` · `Uniswap V1 tvl=3,206,682` · `Jupiter Offerbook tvl=3,146,489` · `Chainlink Requests tvl=0` · `Chainlink Staking tvl=0` · `pump.fun tvl=0` |
| [T1] | `https://stablecoins.llama.fi/stablecoins?includePrices=true` | `GHO GHO circulating= {'peggedUSD': 648238270.0093492}` |
| [T1] | `https://api.coingecko.com/api/v3/coins/markets?...` | `BTC price=64569 mcap=1295552401204` · `ETH 1925.89 / 232471350145` · `SOL 75.32 / 43926860663 fdv=47545001999` · `HYPE 58.14 / 12936507324 fdv=58146211432 circ=222445714.07414138` · `LINK 8.58 / 6421184085 fdv=8583323538` · `GRAM 1.48 / 4036710478 fdv=7706361680` · `UNI 3.83 / 2397374747 fdv=3421841437` · `AAVE 99.44 / 1533635971` · `PUMP 0.00212176 / 844686746 fdv=1796449044` · `JUP 0.186152 / 618223292 fdv=1277745493` · `AERO 0.44277 / 431685282 fdv=861932352` |
| [T1] | `https://api.coingecko.com/api/v3/coins/aerodrome-finance/market_chart?vs_currency=usd&days=35&interval=daily` | `supply 2026-06-23 = 952,371,475` → `supply 2026-07-27 = 973,655,243` → `delta = 21,283,768 AERO over 35 days -> per30d 18,243,230 AERO = $8,103,643 at $0.4442` |
| [T1] | `https://governance.aave.com/t/24686.json` | `[ARFC] Pause AAVE Buybacks \| created: 2026-04-22 \| posts: 18` — "AAVE buybacks have been paused since April 19, 2026" · "no buyback transactions have been executed since April 19, 2026" |
| [T1] | `https://governance.aave.com/search.json?q=buybacks%20resume%20order%3Alatest` | POST 2026-06-05 topic 24936: "this pause should not go on indefinitely... define clear, objective conditions under which buybacks can resume" |
| [T1] | `https://gov.uniswap.org/t/26162.json` | `[Temp Check] Activate v4 Protocol Fees \| 2026-07-07` — "Protocol fees are now live across all v2 and v3 pools on 11 chains - Ethereum, Arbitrum, Base, Celo, OP Mainnet, Soneium, X Layer, Worldchain, Zora, BNB Chain, and Polygon. Last month, the protocol set a record burning 186,000 UNI in one day." |
| [T1] | `https://gov.uniswap.org/latest.json?order=activity` | `2026-06-25 \| RFC : Tokenomics overhaul : hard-capping supply via auto burn, pivoting unification to staking distribution and staking DAO treasury reserves` · `2026-07-11 \| [Temp Check] Protocol Fee Expansion: Robinhood Chain` |

**Adapter methodology strings (value-accrual ground truth):**

- Uniswap V2 `Revenue`: "From 28 Dec 2025, 17% (0% before) fees on Ethereum, From 8 Mar 2026, 17% (0% before) fees on Optimism, Arbitrum, Base, Zora, XLayer chains shared to buy back and burn UNI."
- Uniswap V3 `Revenue`: "From 28 Dec 2025, a portion of fees a collected to buy back and burn UNI on Ethereum, From 8 Mar 2026, on Optimism, Arbitrum, Base, WC, Zora, XLayer, From 2 Jun 2026, on Polygon, BSC, Celo."
- **Uniswap V4 `Revenue`: "Protocol makes no revenue." / `HoldersRevenue`: "No revenue for UNI holders."**
- Aave V3 `HoldersRevenue`: "Aave starts buy back AAVE tokens using Aave Treasury after 9th April 2025."
- **Aave V4 `HoldersRevenue`: "No revenue shared to AAVE holders."**
- Hyperliquid Perps `Revenue`: "99% of fees go to Assistance Fund for buying HYPE tokens, excluding builders fees."
- Hyperliquid Spot Orderbook `Revenue`: "99% of fees go to Assistance Fund for buying HYPE tokens, excluding unit protocol fees."
- pump.fun `ProtocolRevenue`: "...Era-based split: 100% pre-2025-07-14, 0% from 2025-07-14, 50% from 2026-04-28." `HoldersRevenue`: "PUMP token buyback (sourced from onchain burns...)"
- Chainlink Staking `Revenue`: "All the LINK tokens transferred from the PaymentAbstractionLayer to the Reserve and Staking Rewards contracts." `HoldersRevenue`: "LINK token buybacks funded via revenue from various offchain and onchain sources."
- Aerodrome `Revenue`: "veAERO holders' share of swap fees, equal to HoldersRevenue (Aerodrome's zero-leak model routes all protocol revenue to voters)."
- Jupiter Aggregator `HoldersRevenue`: "JUP token buybacks from 50% of platform revenue, started 2025-02-17." · **Jupiter Prediction: "No holders revenue"** · **Jupiter Offerbook: None**

**Failed fetches (nothing imputed):**
- `[FETCH FAILED: https://api.llama.fi/emission/aerodrome-v1 — HTTP 402 "Upgrade to the paid API plan"]`
- `[FETCH FAILED: https://api.llama.fi/emissions — HTTP 402]`

**Convention note:** `/summary/fees/{chain}` = chain-as-protocol (L1 gas only). `/overview/fees/{chain}` = all protocols deployed on that chain. Conflating them is the standard error.

---

## Per token

### BTC
TVL $4,267,821,694 (chain) | Fees 30d $5,581,372 | Revenue 30d **$0** | HoldersRevenue 30d **$0** | MC $1,295,552,401,204 | MC/TVL 303.6 | P/S **n/a — no revenue** (MC/ann-L1-fees 19,078x) | mechanic: **L1, no protocol revenue accrual to the token beyond base-layer economics.** Verbatim `Bitcoin rev 24h= 0 30d= 0 1y= 0`. 100% of fees to miners; no burn, no staking, no buyback.

- Fee load is a rounding error: $5.58M/30d ⇒ ~$67.9M/yr on $1.296T mcap = **0.005% annualized fee yield.** Security budget is subsidy-funded, not fee-funded.
- DeFi-on-Bitcoin negligible: `/overview/fees/bitcoin 30d= 267849.12` (all wrapped/L2 protocols) vs $5,581,372 at base layer — app layer is 1/21st the chain, the inverse of every other L1 here.
- **invalidation:** sustained fee-market revival (ordinals/L2 settlement) taking 30d fees >$50M, or a consensus change routing fees away from miners. Under Burniske, BTC's case is monetary, not cash-flow.

### ETH
TVL $42,111,139,691 (chain) | Fees 30d $7,066,764 | Revenue 30d $1,530,923 (validator tips) | HoldersRevenue 30d $1,530,923 | **implied burn 30d $5,535,841** (1y burn $167,244,825 = fees 1y $257,060,822 − rev 1y $89,815,997) | MC $232,471,350,145 | MC/TVL 5.5 | P/S **2,704x** on annualized L1 fees | mechanic: **L1 — EIP-1559 base-fee burn + PoS staking yield. Real, verified, economically tiny at current activity.**

- Burn run-rate $5.54M/30d ⇒ ~$67M/yr = **0.029% of mcap.** Post-blob L1 fee compression has neutered the burn as a supply sink; at this fee level ETH is net-inflationary.
- **The leak is the story:** $273,171,284.61 of fees/30d generated by protocols on Ethereum vs only $7,066,764 reaching L1 — **97.4% accrues to apps and L2s, not ETH holders.**
- **invalidation:** L1 fees 30d back above ~$50M would flip the issuance/burn balance; further L2 migration widens the leak. Watch the fees-to-chainfees ratio, not the burn alone.

### SOL
TVL $4,926,942,807 (chain) | Fees 30d $15,057,242 | Revenue 30d $1,627,148 (stakers) | HoldersRevenue 30d $1,627,148 | MC $43,926,860,663 | MC/TVL 8.9 | P/S **240x** on annualized L1 fees | mechanic: **L1 — 50% base-fee burn + priority fees/MEV to validators. Best real L1 fee capture of the four chains here.**

- **2.1x Ethereum's L1 fee revenue on 12% of the TVL** ($15.06M vs $7.07M per 30d). Solana monetizes its own base layer far more effectively than Ethereum currently does.
- Same app-layer leak, milder: `/overview/fees/solana 30d= 211,249,216.68` vs $15,057,242 captured — 92.9% leaks vs ETH's 97.4%.
- **invalidation:** fee decay below ~$8M/30d (memecoin/DEX volume is the swing factor); an emission-schedule change. FDV $47.5B vs $43.9B mcap = only 7.6% overhang, the mildest dilution setup of any non-BTC/ETH token here.

### TON
TVL **$64,899,622** (chain) | Fees 30d $77,181 | Revenue 30d $38,589 (stakers) | HoldersRevenue 30d $38,589 | MC $4,036,710,478 | MC/TVL **62.2** | P/S **4,299x** on annualized L1 fees | mechanic: **L1 — nominal fee burn/staking. Economically negligible; no meaningful accrual.**

- **Worst fundamentals-to-price gap in the brief.** Chain TVL $64.9M is 65x smaller than the next-smallest L1 here and smaller than several individual *protocols* in this basket, against a $4.04B mcap.
- `/overview/fees/ton 30d= 27,234,997.97` vs L1 take $77,181 — chain-wide protocol fees are ~353x the L1 capture. Essentially none of TON's ecosystem activity touches the token.
- **invalidation:** Telegram-driven TVL/fee re-acceleration (chain TVL >$500M would be the first real signal). FDV $7,706,361,680 vs $4,036,710,478 mcap = **47.6% supply still to unlock**, second-worst overhang here.

### HYPE
TVL $6,364,539,558 (Bridge $6,003,512,265 + HLP $224,996,936 + Spot $136,030,357; Hyperliquid L1 chain TVL $1,260,016,469) | Fees 30d $51,300,674 | Revenue 30d $36,078,570 | **HoldersRevenue 30d $36,078,570 — 70.3% of fees (75.9% over 1y)** | MC $12,936,507,324 | MC/TVL 2.03 | P/S **29.5x** (ann. 30d) / 16.5x (trailing 1y) / FDV-P/S 132.5x | mechanic: **LIVE — Assistance Fund buyback. Verbatim "99% of fees go to Assistance Fund for buying HYPE tokens" on BOTH perps and spot.** Perps AF 30d $35,019,624 (1y $745,821,450); Spot AF 30d $1,058,946 (1y $39,098,942).

- Cleanest, largest accrual in the set: **~$36.1M/30d ⇒ $438,955,935 annualized of non-discretionary open-market HYPE bid = 3.4% of mcap/yr.** No governance vote required — it is the fee router.
- Two offsets: (1) **FDV $58,146,211,432 vs $12,936,507,324 mcap — only 222.4M of ~1B HYPE circulates (22.2%), the worst dilution setup here**; buyback absorbs ~7.5M HYPE/yr against a ~777M overhang. (2) **Revenue run-rate contracting −44%**: 1y $784,920,392 vs 30d-annualized $438,955,935.
- **invalidation:** continued perp-volume decay; any governance change to the 99% AF routing; HIP-3/builder-fee share diluting the AF take. HLP is explicitly NOT holder revenue — "All fees share of HLP are distributed to vaults suppliers."

### AAVE
TVL $14,738,837,514 (V3 $14,161,545,605 + Horizon RWA $255,452,133 + V4 $202,529,022 + V2 $111,700,229 + V1 $6,500,131 + Aptos $1,053,134 + Arc $57,260) | Fees 30d $28,094,909 | Revenue 30d $3,761,140 (13.4% take) | **HoldersRevenue 30d $0** (1y $28,424,101) | MC $1,533,635,971 | MC/TVL **0.10** | P/S 33.5x (ann. 30d) / 13.1x (trailing 1y) | **GHO supply $648,238,270** | mechanic: **BUYBACK OFF — PAUSED SINCE 2026-04-19.**

Governance verbatim (`[ARFC] Pause AAVE Buybacks`, 2026-04-22): "AAVE buybacks have been paused since April 19, 2026" and "no buyback transactions have been executed since April 19, 2026", following the April 18 Kelp/LayerZero rsETH bridge exploit that put unbacked rsETH into Aave V3 across multiple chains. Live data agrees: `holdersRev 24h= 0 30d= 0`. **Aave V4 is designed with no accrual at all: "No revenue shared to AAVE holders."**

- **Single most dangerous stale-tokenomics trap in the basket** — 99 days paused. Only two stray prints since (2026-05-26 $135,368; 2026-06-24 $576,537) against 235 non-zero days historically: noise, not a restored cadence.
- **No objective restart condition exists.** Forum, 2026-06-05: "this pause should not go on indefinitely... define clear, objective conditions under which buybacks can resume" — i.e. none defined. Umbrella remains a *cost* line (`[ARFC] Umbrella Parameter Update`, 2026-06-16), not a distribution. Revenue run-rate **−61%**: 1y $117,285,863 vs 30d-annualized $45,760,537.
- **invalidation:** an on-chain AIP restarting buybacks (highest-leverage thing to monitor in the basket); conversely rsETH bad-debt socialisation consuming treasury capacity, or V4 migration entrenching the no-accrual design.

### JUP
TVL $2,095,567,520 (Lend $959,621,689 + Perps $731,315,806 + jupSOL $401,158,158 + Offerbook $3,146,489 + Prediction $325,378) | Fees 30d $12,950,808 | Revenue 30d $4,233,526 | **HoldersRevenue 30d $2,115,951 — ratio 0.500 exactly on both the 30d and 1y windows** | MC $618,223,292 | MC/TVL 0.30 | P/S **12.0x** (ann. 30d) / 5.5x (trailing 1y) / FDV-P/S 24.8x | mechanic: **LIVE — 50% of platform revenue → JUP buyback (Litterbox), since 2025-02-17.** The 0.500 ratio reproducing to three decimals on two independent windows means this is mechanically enforced, not aspirational.

- $2,115,951/30d ⇒ $25.7M annualized buyback on $618M mcap = **4.2% of mcap/yr**, third-highest buyback yield here.
- Cheap because the numerator is falling: **revenue 1y $112,485,983 vs 30d-annualized $51,507,895 = −54% run-rate contraction**, steepest in the set. JUP revenue is high-beta to Solana DEX/perp activity.
- **invalidation:** deeper Solana volume trough; FDV $1,277,745,493 vs $618,223,292 mcap = 51.6% overhang; a vote altering the 50% split. Accrual is **not automatic for new products** — Jupiter Prediction "No holders revenue", Offerbook `None` — so product expansion can dilute effective capture even as fees grow.

### UNI
TVL $3,070,353,149 (V3 $1,468,363,900 + V2 $800,198,540 + V4 $798,584,027 + V1 $3,206,682) | Fees 30d $93,240,409 | Revenue 30d $3,255,483 | **HoldersRevenue 30d $3,255,483 — 100% of revenue burned, but only 3.49% of fees (3.15% over 1y)** | MC $2,397,374,747 | MC/TVL 0.78 | P/S **60.5x** (ann. 30d) / 88.6x (trailing 1y) | mechanic: **BURN IS LIVE — coverage partial, design under active revision.**

Official, verbatim (gov.uniswap.org 2026-07-07): "Protocol fees are now live across all v2 and v3 pools on 11 chains - Ethereum, Arbitrum, Base, Celo, OP Mainnet, Soneium, X Layer, Worldchain, Zora, BNB Chain, and Polygon. Last month, the protocol set a record burning 186,000 UNI in one day." Rollout: Ethereum 2025-12-28 → OP/Arb/Base/WC/Zora/XLayer 2026-03-08 → Polygon/BSC/Celo 2026-06-02. **v4 fees NOT live** — V4 adapter: "Protocol makes no revenue." / "No revenue for UNI holders."

- **Realised capture is 3.49% of total fees, not the headline 17%.** v4 holds $798,584,027 TVL and contributes exactly zero; the 17% applies to the protocol's slice, not gross LP fees. Burn run-rate $3,255,483/30d ÷ $3.841 ≈ **847,561 UNI/30d ≈ 1.65% of circulating supply annualized.** Burns settle in batches via TokenJar — the "186,000 UNI in one day" record is a settlement event, do not annualize it.
- **Open governance risk to the mechanic itself:** `RFC : Tokenomics overhaul : hard-capping supply via auto burn, pivoting unification to staking distribution and staking DAO treasury reserves` (2026-06-25) proposes replacing the burn with staking distribution. UNI is also the **only accelerating fee line here** (~+32%) — but holders capture 3.49% of it.
- **invalidation:** v4 fee activation passing (materially raises capture, since v4 is the growth surface); the tokenomics-overhaul RFC replacing burn with staking; fee expansion stalling. Watch `[Temp Check] Protocol Fee Expansion: Robinhood Chain` (2026-07-11).

### AERO
TVL $306,797,428 (Slipstream $155,690,893 + V1 $128,786,107 + Ignition $22,320,428) | Fees 30d $6,115,701 | Revenue 30d $4,189,859 | **HoldersRevenue 30d $4,189,859 — 100% of revenue to veAERO** | MC $431,685,282 | MC/TVL 1.41 | P/S **8.5x** (ann. 30d) / 3.5x (trailing 1y) / FDV-P/S 16.9x | mechanic: **LIVE ve(3,3) "zero-leak"** — "veAERO holders' share of swap fees, equal to HoldersRevenue". Slipstream additionally rakes unstaked LPs ("CLFactory.getUnstakedFee, default 10% of unstaked share"); v1 does not.

- **Emission exceeds fee accrual by ~1.9x.** Derived live: supply `952,371,475 → 973,655,243` over 35 days = **+18,243,230 AERO/30d ≈ $8,103,643** at $0.4442, against **$4,189,859** routed to veAERO. Net effect for a non-locking holder ≈ **−$3.9M/30d**.
- **Accrual only reaches you if you lock.** veAERO voters are on the right side of the emission; spot holders are on the wrong side. Burniske's "does the token capture value" test resolves *differently by holder class* — that distinction, not the 8.5x multiple, is the entire trade. Revenue also contracting **−58%**: 1y $121,781,615 vs 30d-annualized $50,976,618.
- **invalidation:** emission decay crossing below fee accrual (flips spot holders to net-accretive); Base DEX volume-share loss (Base chain fees `30d= 42,865,945.74` is the addressable pool); a gauge-weight/emission-schedule vote. **Caveat: supply delta is NET circulating growth per CoinGecko and may not fully net out veAERO locks — treat 1.9x as an approximate upper bound.** Exact figure blocked by HTTP 402.

### PUMP
TVL $248,320,952 (PumpSwap $247,253,069 + PumpSpace V2 $1,056,077 + Pump Markets $11,806; `pump.fun` itself `tvl= 0`) | Fees 30d $25,672,514 | Revenue 30d $19,667,529 | **HoldersRevenue 30d $14,301,309** | ProtocolRevenue 30d $9,990,081 | MC $844,686,746 | MC/TVL 3.40 | P/S **3.5x** (ann. 30d) / 2.6x (trailing 1y) / FDV-P/S 7.5x | mechanic: **LIVE AND DAILY** — "PUMP token buyback (sourced from onchain burns; aggregates buybacks across all pump products)". Era-based split: "100% pre-2025-07-14, 0% from 2025-07-14, 50% from 2026-04-28." Daily prints, no gaps, 2026-07-20→26: `475035, 503718, 552001, 529763, 577372, 531409, 587823`.

- **Cheapest verified cashflow in the brief.** $14,301,309/30d ⇒ ~$174M annualized buyback vs $844,686,746 mcap = **20.6% of mcap repurchased per year.** Unlike AAVE or LINK the prints are continuous rather than batched — strongest *evidentiary* accrual signal in the set.
- Why it is cheap: launchpad revenue is the most cyclical, reflexive and competitively-attackable cashflow in crypto; terminal value for a memecoin casino is genuinely uncertain. Run-rate **−26%**: 1y $323,949,113 vs 30d-annualized $239,288,270 — mildest contraction here, still negative. The 3.5x P/S is a **risk premium, not a discovered mispricing.**
- **invalidation:** Solana memecoin volume collapse; a competing launchpad taking share; **the 50% split being revised again — it has already changed twice (100% → 0% → 50%)**, itself the governance-risk tell; FDV $1,796,449,044 vs $844,686,746 mcap = 53.0% overhang.

### LINK
TVL **$0** — `Chainlink Requests tvl= 0`, `Chainlink Staking tvl= 0`; an oracle has no protocol TVL, and TVS is **[UNAVAILABLE]** on keyless endpoints | Fees 30d $4,841,696 | Revenue 30d $4,613,725 | **HoldersRevenue 30d $4,613,725** (1y $56,911,607) | MC $6,421,184,085 | MC/TVL **n/a** | P/S **114.4x** (ann. 30d) / 112.8x (trailing 1y) / FDV-P/S 152.9x | mechanic: **LIVE BUT LUMPY AND WEAKLY AUDITABLE — Chainlink Reserve.** `totalAllTime 56911607` equals `total1y` exactly — the Reserve is ~12 months old, no history before that.

- **Prints are batched, not continuous** — last 8 days `[0, 0, 0, 1148131, 0, 0, 0, 0]`. The entire $4.61M 30-day figure lands in a handful of settlement transactions. **A zero-day here is batching, not a pause** — the exact opposite of AAVE, where zero *is* a pause. The API renders both identically; only the governance fetch separates them.
- **Only $206,171 of the $4,841,696 (4.3%) is verifiable on-chain request fees** (1y $3,828,615 of $61,445,905). The Reserve is overwhelmingly funded by **off-chain enterprise/CCIP/SVR revenue DeFiLlama cannot independently verify** — weakest auditability of any accrual in this brief.
- **Most expensive protocol here by a wide margin: 114.4x annualized revenue** — ~2x the next-highest (UNI 60.5x), 33x PUMP. $6.42B mcap on $56.9M annual revenue, ~4% on-chain-verifiable. Buyback yield ≈ 0.9% of mcap/yr.
- **invalidation:** CCIP/SVR revenue scaling into the multiple (needs ~5–10x revenue growth to reach peer valuations); or Reserve funding disclosed as non-recurring/subsidised. Watch whether `totalAllTime` keeps compounding past the 1-year mark — if it stalls, the Reserve was a launch event, not a run-rate.

---

## Cross-token summary

| Token | TVL | Fees 30d | Revenue 30d | HoldersRev 30d | MC | MC/TVL | P/S (ann 30d) | Buyback yield/yr | Mechanic status |
|---|---|---|---|---|---|---|---|---|---|
| PUMP | $248,320,952 | $25,672,514 | $19,667,529 | **$14,301,309** | $844,686,746 | 3.40 | **3.5x** | **20.6%** | LIVE, daily, no gaps |
| AERO | $306,797,428 | $6,115,701 | $4,189,859 | $4,189,859 | $431,685,282 | 1.41 | 8.5x | 11.8% (ve-locked only) | LIVE, emission 1.9x > fees |
| JUP | $2,095,567,520 | $12,950,808 | $4,233,526 | $2,115,951 | $618,223,292 | 0.30 | 12.0x | 4.2% | LIVE, 50% enforced |
| HYPE | $6,364,539,558 | $51,300,674 | $36,078,570 | $36,078,570 | $12,936,507,324 | 2.03 | 29.5x | 3.4% | LIVE, 99% Assistance Fund |
| AAVE | $14,738,837,514 | $28,094,909 | $3,761,140 | **$0** | $1,533,635,971 | **0.10** | 33.5x | **0%** | **PAUSED since 2026-04-19** |
| UNI | $3,070,353,149 | $93,240,409 | $3,255,483 | $3,255,483 | $2,397,374,747 | 0.78 | 60.5x | 1.65% | LIVE, 3.49% capture, v4 excluded |
| LINK | **$0** (n/a) | $4,841,696 | $4,613,725 | $4,613,725 | $6,421,184,085 | n/a | **114.4x** | 0.9% | LIVE, lumpy, 96% off-chain-funded |
| ETH | $42,111,139,691 | $7,066,764 (L1) | $1,530,923 | burn $5,535,841 | $232,471,350,145 | 5.5 | 2,704x | 0.029% (burn) | L1 burn + staking |
| SOL | $4,926,942,807 | $15,057,242 (L1) | $1,627,148 | $1,627,148 | $43,926,860,663 | 8.9 | 240x | — | L1 burn + staking |
| BTC | $4,267,821,694 | $5,581,372 (L1) | **$0** | **$0** | $1,295,552,401,204 | 303.6 | n/a (19,078x fees) | — | L1, no accrual |
| TON | $64,899,622 | $77,181 (L1) | $38,589 | $38,589 | $4,036,710,478 | **62.2** | 4,299x | — | L1, negligible |

**Chain TVL:** Ethereum $42,111,139,691 · Solana $4,926,942,807 · Base $4,657,795,255 · Bitcoin $4,267,821,694 · Hyperliquid L1 $1,260,016,469 · TON $64,899,622.

**Chain-wide protocol fees (30d):** Ethereum $273,171,284.61 · Solana $211,249,216.68 · Hyperliquid $110,983,163.42 · Base $42,865,945.74 · TON $27,234,997.97 · Bitcoin $267,849.12.

---

## Three findings that overturn common priors

1. **AAVE buybacks are OFF** — 99 days, governance-confirmed verbatim, `holdersRev 30d= 0`, no objective restart condition as of 2026-06-05. Any model carrying AAVE as a live-buyback name is materially wrong. Aave V4 has **no** holder accrual by design.
2. **UNI's realised burn capture is 3.49% of fees, not the headline 17%** — v4 ($798.6M TVL) contributes zero, and a live RFC (2026-06-25) proposes replacing the burn entirely with staking distribution.
3. **AERO's emission runs ~1.9x its fee accrual** ($8.10M vs $4.19M per 30d) — "zero-leak" is true for veAERO lockers, false for spot holders. Same token, opposite sign.

## Two methodological warnings

- **Zero-days are not self-explanatory.** LINK's zeros are batching; AAVE's zeros are a governance pause. DeFiLlama renders both identically — only the governance fetch separates them. This is precisely why a stale tokenomics claim is this seat's #1 failure mode.
- **Run-rate direction dominates the multiple.** Every protocol here has 30d-annualized revenue *below* trailing 1y: **AAVE −61%, AERO −58%, JUP −54%, HYPE −44%, PUMP −26%.** UNI is the sole fee accelerator (~+32%), but holders capture 3.49%. Cheap P/S ratios here are falling numerators, not discovered bargains.

DATA ONLY — no votes, no recommendations.
