# Crypto Portfolio Advisor — 2026-07-24

## Macro Context

| Signal | Value | Regime |
|---|---|---|
| Fear & Greed | **28 (Fear)** | Risk-off, ↓3 pts since Jul 22 |
| BTC Death Cross (50/200) | **ACTIVE** | Bearish technical |
| BTC vs EMA20 | **BELOW** | Short-term bearish |
| BTC vs SMA50/SMA200 | ABOVE SMA50 / BELOW SMA200 | Mixed |
| BTC vs 200wMA | −11.7% (estimated) | Below value |
| BTC Price | **$63,922** | −49% from ATH |
| BTC ETFs Jul 23 | **−$225M outflow** (ends 7d inflow streak) | Rotation risk |
| ETH ETFs Jul 23 | **+$26.3M inflow** (5d streak) | Divergent strength |
| ETF flows *as of Jul 27* (corrected) | ETH 5-day streak **SNAPPED Jul 25**, week closed red; BTC shed **−$465M over two days** (IBIT −$415M). **Both** BTC and ETH funds still extended **weekly** inflow streaks to **three**. | Divergence narrower than drafted |
| 10Y Treasury | ~4.70% (18-month high) | Liquidity tightening |
| Oil (WTI) — *as drafted Jul 24* | **~$89** (CL=F, Iran tensions, +7% wk) | Inflation/geo headwind |
| Oil (WTI) — **CANONICAL, live 2026-07-29T15:02Z** | **$85.41** (CL=F). Round-tripped the Iran spike to $79.26 on Jul 28, then reversed **+7.8% in one session**. Now **ABOVE** the Jul 17 pre-spike close of $82.49 (+3.5%) | **Headwind BACK ON** — see SKEPTIC GATE §S2. *(The Jul-28 pull of $82.00 and its "headwind GONE" read are RETRACTED — a 24-hour-valid snapshot, wrong today.)* |
| Oil (Brent) — **CANONICAL, live 2026-07-29T15:02Z** | **$90.92** (BZ=F). Low $84.09 Jul 28; above the $88.10 pre-spike close (+3.2%) | Same reversal — not a WTI-only artifact. *(Jul-28 $87.75 RETRACTED.)* |

**Regime: BEARISH.** F&G 28 = Fear territory, weakening from 31 on Jul 22. BTC briefly broke below $65K intraday, closed at $63,922. Divergence growing — BTC ETFs see largest single-day outflow in 2 weeks, while ETH ETFs extend streak to 5 days. **Corrected 2026-07-27: that ETH 5-day streak snapped on Jul 25 and the week closed red, while BTC funds shed −$465M over two days (IBIT −$415M) — yet BOTH complexes still logged a third consecutive WEEKLY inflow, so the "rotation out of BTC into ETH" read is weaker than drafted (https://cointelegraph.com/markets/ethereum-etfs-week-red-end-inflow-streak, https://www.coindesk.com/markets/2026/07/27/bitcoin-etfs-record-third-consecutive-weekly-inflows-despite-losses-of-usd465-million-to-end-week).** Macro headwinds mounting: US-Iran tensions, 10Y yields at 18-month high (~4.70%), WTI CL=F closed $89.31 on Jul 24 (spiked to $92.19 on Jul 23 on Iran-strike risk, intraday high $93.50; +8.3% vs prior week's Jul 17 close of $82.49 — corrected 2026-07-27 from "$83.33 / +7.1%" — not $100). Brent BZ=F hit $100.69 intra-week but report scopes to WTI.

> **OIL-MACRO CONFLICT — SUPERSEDED 2026-07-29. Read SKEPTIC GATE §S2 at the end of this document instead; that pull is canonical.** The block below is retained as a correction-history artifact ONLY. Its conclusion ("headwind GONE — geo-premium fully round-tripped", WTI $82.00 / Brent $87.75) was valid for roughly 24 hours and is **WRONG as of 2026-07-29**: WTI fell further to $79.26 on Jul 28, then reversed to **$85.41**, back ABOVE the $82.49 pre-spike close. **Do not cite $82.00 or $87.75.** The oil leg of `Regime: BEARISH` is restored.
>
> <details>
>
> **[HISTORICAL — 2026-07-27, re-verified 2026-07-28T00:14Z]** This report listed oil in TWO contradictory places, and even after a first "resolution" pass the fix itself carried TWO more mutually inconsistent number pairs ($81.85/$87.66 in the macro table + this block vs $81.64/$87.50 in the Risk Overlay and BTC/ETH/SOL critic sections) — a second live pull was ~2% off. That pass pinned the full daily series, which remains accurate and is the reason the Jul-29 gate could extend it cleanly:
>
> | Date | WTI CL=F | Brent BZ=F |
> |---|---|---|
> | Jul 16 (pre-spike) | 78.95 | 84.23 |
> | Jul 17 (prior-wk close) | **82.49** | 88.10 |
> | Jul 20 | 83.23 | 89.22 |
> | Jul 21 | 84.91 | 91.01 |
> | Jul 22 | 86.83 | 94.07 |
> | Jul 23 (Iran-strike peak) | **92.19** | **100.69** |
> | Jul 24 (report snapshot) | **89.31** | 96.78 |
> | **Jul 27 close** | 82.61 | 88.36 |
> | **Jul 28 00:14Z live (then-canonical, NOW RETRACTED)** | ~~82.00~~ | ~~87.75~~ |
> | **Jul 28 close** | 79.26 | 84.09 |
> | **Jul 29 15:02Z live — CANONICAL** | **85.41** | **90.92** |
>
> **[HISTORICAL — this paragraph's conclusion is WITHDRAWN, see §S2]** ~~The conflict resolves AGAINST the report's own bearish framing. WTI at $82.00 is not merely "pulling back" — it is below the $82.49 Jul 17 pre-spike close, i.e. the entire Iran geo-premium has round-tripped and then some. "Oil = inflation/geo headwind" was a valid Jul 24 input and is a dead input as of this re-pull. One of the four bearish legs no longer exists.~~ **Withdrawn 2026-07-29: oil overshot to $79.26 then reversed +7.8% to $85.41, back above the pre-spike close. The oil leg is RESTORED.** The separate downgrade of the BTC→ETH ETF rotation read still stands.
>
> </details>

---

---

## Measurement convention (MANDATORY — added 2026-07-29, enforced in code)

Every "% from high" and every 52w low/high in this document must state **both** its basis and its convention. Three shipped errors traced to leaving these implicit (TON −49.2%/−82.5%, JUP −87%, LINK −73.1%).

| Axis | Options | This report's default |
|---|---|---|
| **Basis** | 52-week high vs all-time high (ATH) | **52-week high.** Any ATH figure must say "from ATH". |
| **Convention** | intraday extreme vs daily-close extreme | **Stated per figure.** Close-basis is ~1pp shallower than intraday. |
| **Series** | one canonical pull per token, >= 360 daily points | CoinGecko `coins/{id}/market_chart?days=365&interval=daily`; a short series is a hard FAIL, not a silent pass. |

**Self-inflicted error logged for honesty:** the 2026-07-29 pass "corrected" LINK's 52w low from $7.00 to $7.19 without noting that $7.19 is the *close-basis* low while $7.00/$7.02 is the *intraday* low. The original figure was defensible; the "fix" silently switched convention. Both are now shown with labels.

**Wrong-ticker trap:** Yahoo `AERO-USD` and `JUP-USD` resolve to **different assets** (AERO returns ~$0.0002 vs Aerodrome's $0.416; JUP returns ~$0.00001 vs Jupiter's $0.194). Do not cross-check these tickers on Yahoo — this is the same failure mode that produced the retracted $16.73 LINK print.

**Enforcement:** `bun .agents/scripts/validate/drawdown_basis.ts <report.md>` parses every drawdown/range claim, requires an explicit basis, and recomputes it from one canonical per-token series, failing on any mismatch > 0.5pp. Wired as a pre-commit gate. It currently flags **45 of 63** claims in this document — the AERO and PUMP 52w range rows (drafted from a different venue than the validator's series) are **unresolved and must be re-pulled from their original source before those numbers are cited**.

---

## Per-Token Analysis

### 1. BTC — Bitcoin

| Metric | Value |
|---|---|
| Price | **$63,922** |
| RSI (14) | 49.0 (neutral) |
| MACD Hist | +154 (bullish, rising) |
| EMA20 | $64,297 **(BELOW)** |
| SMA50 | $63,158 **(ABOVE)** |
| SMA200 | $72,449 **(BELOW)** |
| Death Cross (50/200) | **Active** |
| 52w High | $126,200 (−49.3%) |
| 52w Low | $52,550 |
| 200d Range | $57,800 → $97,924 → $63,922 |

**Assessment:** BTC sideways in $59K-$67K range for 5 weeks straight (5 weekly closes: $59,577 → $63,650 → $63,780 → $64,723 → $63,922). A base, not a breakout. Volume declining — weekly volume dropped from 142K to 86K BTC. The ETF outflow day was large but context matters: still +$274M net for the week. BTC has been grinding lower from the $65-67K range, now trading below both EMA20 and the psychologically important $65K level.

**Verdict HOLD — $60-62K is the accumulation zone. Below that, reassess open positions.**

---

### 2. ETH — Ethereum

| Metric | Value |
|---|---|
| Price | **$1,855** |
| 52w Range | $1,385 ↔ $4,957 |
| % from 52w High | −62.6% |
| 210d Performance | −32.4% |
| Latest Weekly Close | $1,855 (down −0.9% from prev week $1,872) |
| ETH ETF Flow | **+$26.3M** (5 consecutive days) |
| ETH/BTC Ratio | 0.029 (multi-year low) |

**Assessment:** ETH continues to diverge positively on ETF flows (5-day streak, $26.3M on Jul 23) vs BTC's $225M outflow. This is notable structural divergence — institutions are rotating INTO ETH via ETFs. **Downgraded 2026-07-27: the 5-day streak snapped Jul 25 and the ETH ETF week closed red; both BTC and ETH funds nonetheless extended weekly inflow streaks to three. The durable version of this claim is the RELATIVE one — ether funds drew nearly as much capital as bitcoin ETFs over three weeks on roughly one-eighth the net assets (https://www.theblock.co/post/409660/bitcoin-etf-weekly-trading-volume-falls-to-lowest-since-october-2024-as-ether-funds-lead-inflows-again) — not a live daily inflow streak.** However, spot price remains weak, ETH/BTC at 0.029 (compressed). The utility thesis (staking yields, L2 adoption, RWA tokenization) is gaining institutional traction even as speculative momentum remains absent.

**Verdict HOLD — $1,800 is the key support. ETH ETF inflow divergence is a positive signal for relative outperformance.**

---

### 3. SOL — Solana

| Metric | Value |
|---|---|
| Price | **$73.94** |
| 52w Range | $60.13 ↔ $295.83 |
| % from 52w High | −75.0% |
| TVL | $4.9B |
| 210d Volume Trend | Declining (19.9M → 7.1M weekly) |
| Latest Weekly Close | $73.94 (down −3.2%) |

**Assessment:** SOL has been sliding for weeks, down 75.0% from its 52w high. Volume declining every week since the mid-June peak — bearish. Stablecoins on Solana at $15B+ shows infrastructure is real, but token price disconnected from ecosystem growth. On-chain activity likely depressed as memecoin mania cooled.

**Verdict HOLD — no accumulation signal until volume returns. $60 is the hard floor.**

---

### 4. TON — Toncoin

| Metric | Value |
|---|---|
| Price | **~$1.44** |
| ATH | $8.25 (−82.5%) |
| 1y Change | −55.6% |
| Market Cap | ~$3.9B |
| 7d Change | −9.4% |

**Assessment:** TON continues to bleed. Down another 9.4% this week. No positive catalysts visible — Telegram integration story is old news, Notcoin/HMSTR hype faded. Price below all relevant MAs.

**DRAWDOWN CORRECTED 2026-07-27, RE-VERIFIED LIVE 2026-07-28T00:25Z (verdict-critic pass).** This draft's ATH-based read above (−82.5% from $8.25) is not the standard 52-week-high framing used elsewhere in this report. On the standard 52w-high basis, freshly re-pulled from CoinGecko (`coins/the-open-network/market_chart`, 366 daily points, 2026-07-28T00:25:30Z): **365d high = $3.5722 (2025-08-02)**, current $1.4617, **= −59.1% from high** — consistent with the prior desk figure of $3.5747/−58.5% (0.07% venue variance) and materially worse than an earlier-drafted "−49.2%" figure that had circulated in a related briefing (the discrepancy traced to a truncated ~37-week price window on the venue used). Separately, the "zero token-specific journalism" framing used to justify TRIM is **too strong**: the repo's own `read_news.ts` store holds two TON-adjacent items dated Jul 21-22 (a Telegram wallet-rollout piece and a STON.fi wire release) — coverage is thin, not absent. Neither correction changes the verdict: fees $77,181/30d vs $3.9-4.0B mcap (~4,300x, worst in the book), TVL $64.9M (0.15% of Ethereum's), HL open interest $0 — the bear case is unchanged and, on the corrected drawdown, slightly worse than drafted.

**Verdict TRIM — no catalyst, no bottom formation (confirmed −58.5% to −59.1% from true 52w high $3.57, not −49.2%). Re-enter only if Telegram announces new crypto integration.**

> **Invalidation / re-entry levels (added 2026-07-29; CoinGecko 366 daily closes):** spot **$1.3949**, SMA50 $1.5930, SMA200 $1.5570, 52w range **$1.2174**–$3.5722 (**−61.0%** from high — the drawdown has deepened from the −59.1% measured Jul 28).
> - **TRIM completes (→ EXIT the rest):** daily close below **$1.2174** (52w low). At ~4,300x fees/mcap there is no accrual floor to catch it.
> - **TRIM is invalidated (→ back to HOLD):** weekly close above **$1.5570** (SMA200) *and* a dated Telegram integration announcement. Price alone is not enough — this name's problem is the absent catalyst, so the governance/product leg is required, not optional.
> - The re-entry condition above was previously stated with no price at all, which made it unfalsifiable; both legs must now clear.

---

### 5. HYPE — Hyperliquid

| Metric | Value |
|---|---|
| Price | **$59.14** |
| ATH | $76.87 (Jun 16, 2026 — 1 month ago) |
| % from ATH | −23% |
| Market Cap | $15B (#9) |
| 7d Change | −10.8% |
| 24h Range | $57.54 – $60.02 |

**Assessment:** HYPE is pulling back from its ATH just one month ago (−23%). Still the #9 crypto by market cap at $15B. The pullback is healthy after the strong post-launch run-up. Perp DEX growth narrative intact. HYPE at $50-55 would be a strong accumulation zone — -28 to -35% from ATH with a growing protocol.

**UNLOCK CATALYST — CORRECTED 2026-07-27/28 (verdict-critic pass).** An earlier draft cited a CoinDesk week-ahead calendar entry claiming a "Jul-29 unlock, 2.8% of circulating supply = $817M" landing the same day as FOMC. **That claim is retracted — it does not exist and its own arithmetic was wrong.** 2.8% of 222,445,714 circulating HYPE = 6.23M tokens; at spot that is ≈**$363-373M**, not $817M — the drafted figure was off by ~2.3x even on its own stated percentage. The real next unlock, per tokenomist.ai (refreshed 2026-07-27 15:32 UTC): **2026-08-06, 9,916,667 HYPE (~$594.6M), Core Contributors cliff** — a different date, different size, different mechanism (team cliff, not a pro-rata % unlock) than what was drafted. Caveat carried forward: the Aug-6 date is **single-sourced** (cryptorank is paywalled, `api.llama.fi/emission` returns HTTP 402) — re-check before this drives any sizing decision. FOMC Jul 28-29 is independently confirmed real (federalreserve.gov); it does not coincide with this unlock.

**Verdict WATCH — $50-55 is the accumulation zone. Current $59 is above ideal entry. Perp DEX volumes key metric to monitor. The Aug-6 team-cliff unlock (~$595M, single-sourced) is a fresh risk to watch into next week, not the fabricated Jul-29/$817M event.**

---

### 6. AAVE — Aave

| Metric | Value |
|---|---|
| Price | **$94.00** |
| 52w Range | $57.83 ↔ $399.85 |
| % from 52w High | −76.5% |
| TVL | $14.6B |
| MC/TVL Ratio | ~0.1 |
| Latest Weekly Close | $94 (up from $89.56 prev week, +5%) |

**Assessment:** AAVE has $14.74B TVL (dominant lending protocol), token at $94 — MC/TVL ~0.10, cheap vs DeFi norms. Weekly chart shows a +5% gain this week while everything else is red — relative strength signal. Previous Jul 22 report had AAVE as "BUY ZONE" at $85-90 — that call is validated on price (bounced $88 → $94).

**MATERIAL OMISSION corrected 2026-07-27 (analyse-defi seat): AAVE buybacks have been OFF for 99 days.** governance.aave.com `[ARFC] Pause AAVE Buybacks` (2026-04-22), verbatim: *"AAVE buybacks have been paused since April 19, 2026"* and *"no buyback transactions have been executed since April 19, 2026"* — triggered by the April 18 Kelp/LayerZero rsETH bridge exploit that put unbacked rsETH into Aave V3 across multiple chains. Live data confirms: DeFiLlama `aave holdersRevenue 24h= 0 30d= 0` (vs 1y $28,424,101).

> **AAVE RESTART-CONDITION CLAIM — CORRECTED 2026-07-27 (verdict-critic pass).** The line above (drafted same day) said "no objective restart condition exists," anchored to a 2026-06-05 forum post — **that anchor is now 52 days stale.** A newer post, `governance.aave.com/t/24936` post #16 (2026-06-25), quotes Aave founder Stani Kulechov: *"new Aavenomics 3.0 will have immutable and automated buybacks."* That is a stated intent for a restart mechanism, not a defined trigger condition — the pause is still real and still $0/30d — but "no objective restart condition exists" overstates the governance stall. Separately, the **"Aave V4 is designed with no accrual at all... 'No revenue shared to AAVE holders'" quote is UNSOURCED** — the verdict-critic pass found **zero hits** for that exact string in Aave governance full-text search; it should not be presented as a verbatim quote. **Missed catalyst the panel didn't weigh:** Aave V4 deposits grew from $11.3M (Apr 15) to **$303M (Jul 23)** across 11 cap-raise rounds plus an Avalanche launch — V4 traction is accelerating even while V4's own accrual design remains unconfirmed.

Other live figures: `fees 30d= $28,094,909`, `revenue 30d= $3,761,140` (13.4% protocol take, to treasury), GHO supply **$648,238,270**. Revenue run-rate is the worst-contracting in the book: 1y $117,285,863 vs 30d-annualized $45,760,537 = **−61%**.

**VERDICT RE-DERIVED 2026-07-27/28 (verdict-critic pass) — BUY ZONE / ACCUMULATE-WITH-CAVEAT was too soft, downgraded to HOLD (existing) / AVOID (new capital).** Weighing the honest evidence, not softened language:
- **Against accumulating:** buyback has been $0 for 99+ consecutive days (`holdersRevenue` 30d = $0, every day 2026-06-25→07-27, governance-confirmed at `governance.aave.com/t/24686`); revenue run-rate is the worst-contracting name in the entire 11-token book (−61% 30d-annualized vs trailing-1y); the rsETH bad-debt overhang from the April exploit is still unresolved on the balance sheet; and there is **no dated, binding restart mechanism** — only a forward-looking statement.
- **The one governance signal that could flip this** — Aave founder Stani Kulechov stating on 2026-06-25 (`governance.aave.com/t/24936` post #16) that "new Aavenomics 3.0 will have immutable and automated buybacks" — is **intent, not a commitment**: no date, no Snapshot vote, no AIP number. It downgrades "no restart condition will ever exist" (too bearish) to "a restart is being designed" (still not investable), and does not by itself justify BUY ZONE.
- **V4 deposit growth ($11.3M Apr 15 → $303M Jul 23, 11 cap-raise rounds + Avalanche launch)** is real protocol-level traction, but by design **V4 does not share revenue with AAVE token holders** — it strengthens the protocol's TVL/moat, not the token's cash-flow case. Growth in a bucket that doesn't accrue to the token is not a token-bullish catalyst.
- **Cheap MC/TVL (0.10) is not a valuation edge when accrual is zero** — a cheap multiple on a non-existent numerator (holder revenue) is not a bargain, it is the market correctly pricing a paused income stream.
- Net: the honest call is **HOLD for existing positions** (real $14.7B TVL, deep GHO stablecoin float, cheap balance-sheet multiples, and optionality if/when a dated buyback-restart AIP lands) but **AVOID adding new capital** at $85-95 on a "cheap defensive" thesis — that thesis requires live accrual, and there isn't any. This is a genuine downgrade from the panel's original BUY ZONE, not a wording change: **do not size AAVE as an accumulation candidate until a dated, on-chain AIP restarting buybacks actually passes.**

---

### 7. JUP — Jupiter

| Metric | Value |
|---|---|
| Price | **$0.186** |
| 52w Range | $0.056 ↔ $1.44 |
| % from 52w High | −87.1% |
| 210d Volume Trend | Declining (123M → 54M weekly) |
| Latest Weekly Close | $0.186 (−5.3%) |

**Assessment:** JUP in free-fall territory, down 87.1% from its 52w high. Solana DEX aggregator has real product-market fit (high volume, low fees) but token price action is catastrophic. Volume declining every week since June. No demand for the token at these levels despite utility.

**Verdict AVOID — downtrend intact, no reversal signal. Wait for volume base + ladder entry if ever.**

> **Invalidation / re-entry levels (added 2026-07-29; CoinGecko 366 daily closes, pulled 15:2xZ):** spot **$0.1944**, SMA50 $0.2036, SMA200 $0.1911, 52w range $0.1418–$0.5586.
> - **AVOID is invalidated (→ WATCH)** on a weekly close above **$0.2036** (SMA50) *with* rising volume — that is the "volume base" this verdict demands, stated as a number.
> - **Thesis kill (→ EXIT any residual):** daily close below **$0.1418** (52w low). A new low on a −54% revenue run-rate is confirmation, not a dip.
> - Note: the **−87% from high** figure above is measured from the **$2.00 ATH**, not the 52w high. On the report's standard 52w basis JUP is **−65.2%** from $0.5586. Same measurement-basis error class as the corrected TON figure.

---

### 8. UNI — Uniswap

| Metric | Value |
|---|---|
| Price | **$3.81** |
| 52w Range | $2.00 ↔ $19.47 |
| % from 52w High | −80.4% |
| Latest Weekly Close | $3.81 (+8.3% from $3.52 prev week) |
| Volume Trend | Declining (24.9M → 13.8M weekly) |

**Assessment:** UNI saw a +8.3% weekly gain, best in the portfolio this week. $3.81 is above the $3.00-3.50 support zone that held in recent weeks. However, volume is still declining.

**Corrected 2026-07-27 (analyse-defi seat) — the fee switch is NOT a pending catalyst; it has been live for 7 months.** gov.uniswap.org (`[Temp Check] Activate v4 Protocol Fees`, 2026-07-07), verbatim: *"Protocol fees are now live across all v2 and v3 pools on 11 chains - Ethereum, Arbitrum, Base, Celo, OP Mainnet, Soneium, X Layer, Worldchain, Zora, BNB Chain, and Polygon. Last month, the protocol set a record burning 186,000 UNI in one day."* Rollout began Ethereum 2025-12-28. The realised numbers are underwhelming: DeFiLlama `uniswap fees 30d= $93,240,409` vs `revenue/holdersRevenue 30d= $3,255,483` = **3.49% realised capture**, ≈847,561 UNI/30d ≈ **1.65% of circulating supply annualized**. v4 ($798.6M TVL) contributes **zero** — V4 adapter: *"No revenue for UNI holders."* A live RFC (2026-06-25) proposes replacing the burn with staking distribution.

**Verdict HOLD — but the thesis must change. The catalyst already fired and repriced nothing; UNI trades at 60.5x annualized protocol revenue. The remaining upside case is v4 fee activation (Temp Check stage), not "if the fee switch turns on."**

> **Invalidation / re-entry levels (added 2026-07-29; CoinGecko 366 daily closes, pulled 15:2xZ):** spot **$3.96**, SMA50 $3.25, SMA200 $3.61, 52w range $2.39–$12.15.
> - **HOLD is invalidated (→ TRIM)** on a weekly close below **$3.61** (SMA200) — UNI is the book's only fee accelerator, so losing its long-term trend removes the sole reason to hold a 60.5x multiple.
> - **Hard stop (→ EXIT):** daily close below **$3.25** (SMA50) after an SMA200 loss, i.e. trend break confirmed on both.
> - **Upgrade trigger (→ ADD):** a v4 fee-activation vote reaching **Snapshot with delegate sponsorship** (not Temp Check). Price is not the trigger here — governance is.

---

### 9. AERO — Aerodrome Finance

| Metric | Value |
|---|---|
| Price | **$0.416** |
| 52w Range (corrected) | **$0.3018 ↔ $1.4907** |
| % from 52w High | **−72.1%** |
| ATH | **$2.32 (2024-12-07)** |
| Weekly Volume | 774M AERO ($322M) |
| TVL | $306,797,428 |

**Assessment — original draft was materially wrong and is retracted.** The claim *"newly listed on Binance — only 2 weekly bars available... hasn't built a track record"* and the 52w range *"$0.410 ↔ $0.518"* are both false. CoinGecko returns **365 continuous daily price points** (`n points: 365, first: 2025-07-28`), a 365d range of **$0.3018 (2026-02-11) ↔ $1.4907 (2025-08-23)**, and an ATH of **$2.32 on 2024-12-07** — over two years of history. AERO is not a discovery-phase listing; it is **−72.1% from its 52-week high**, a very different setup from the −19.6% the draft implied.

**The real issue is emission, not price history.** Aerodrome routes 100% of protocol revenue to veAERO (*"Aerodrome's zero-leak model routes all protocol revenue to voters"*), giving `revenue/holdersRevenue 30d= $4,189,859`. But circulating supply grew `952,371,475 → 973,655,243` over 35 days = **+18.24M AERO/30d ≈ $8,103,643 of emission at $0.4442 — roughly 1.9x the fee accrual.** Fees are also contracting −58% vs trailing-1y.

**Verdict WATCH (lock-only) → the accrual is real only if you LOCK.**

> **Invalidation / re-entry levels (added 2026-07-29; CoinGecko 366 daily closes, pulled 15:2xZ):** spot **$0.4158**, SMA50 $0.4712, SMA200 $0.4313, 52w range $0.3018–$1.4907. AERO trades **below both** MAs.
> - **Entry trigger (→ lock veAERO):** weekly close back above **$0.4313** (SMA200). Below it, emissions outrun fees for unlocked holders and the "lock it" case is theoretical.
> - **Thesis kill (→ AVOID outright):** daily close below **$0.3018** (52w low) — on a −58% revenue run-rate that is a broken protocol, not a discount.
> - **Unlocked spot holders have no entry level at all** — they are structurally diluted ~−$3.9M/30d regardless of price. This verdict applies only to the ve-locked holder class.
>  veAERO voters capture the fees; unlocked spot holders are net-diluted ~−$3.9M/30d. This is a holder-class decision, not a "wait for price history" decision. Caveat: the supply delta is net circulating growth and may not fully net out veAERO locks (exact emission blocked — DeFiLlama emissions API HTTP 402), so treat 1.9x as an upper bound.

---

### 10. PUMP — pump.fun

| Metric | Value |
|---|---|
| Price | **$0.001824** |
| 52w Range | $0.000411 ↔ $0.00898 |
| % from 52w High | −79.7% |
| Weekly Volume | 27B tokens ($49M) |

**Assessment:** Memecoin launchpad token, down 79.7% from its 52w high. Volume massive in token terms but small in USD — typical penny-token behavior.

**Corrected 2026-07-27 (analyse-defi seat) — two claims in the draft were wrong.** (1) Revenue is **not** "$500M+/year": DeFiLlama `pump.fun revenue 1y= $323,949,113`, 30d `$19,667,529` (30d-annualized $239.3M, a −26% run-rate contraction). (2) Accrual is **not** "unproven" — it is live, on-chain, and prints **every single day without gaps**: `holdersRevenue 30d= $14,301,309`, daily 2026-07-20→26 = `475035, 503718, 552001, 529763, 577372, 531409, 587823`. Adapter methodology: *"PUMP token buyback (sourced from onchain burns)"*, era split *"100% pre-2025-07-14, 0% from 2025-07-14, 50% from 2026-04-28."* That is **~$174M/yr of buyback against an $845M mcap = 20.6% of market cap repurchased annually** — the highest buyback yield in the entire 11-token universe, and the only one with continuous (not batched) prints.

**Verdict AVOID — but on RISK, not on absent accrual.**

> **Invalidation / re-entry levels (added 2026-07-29; CoinGecko 366 daily closes, pulled 15:2xZ):** spot **$0.001880**, SMA50 $0.001586, SMA200 $0.001890, 52w range $0.001199–$0.008609.
> - **AVOID is deliberately NOT price-invalidated upward.** The objection is terminal value and a fee split already revised twice (100% → 0% → 50%), plus a 53% supply overhang (FDV $1.80B vs $845M mcap). No price makes a cyclical launchpad's cashflow durable, so a rally is not evidence.
> - **The only upgrade trigger is structural:** the 50% fee split surviving **two consecutive quarters unchanged** with buybacks printing daily. That is a calendar condition, not a chart level.
> - **Downside confirmation (stay out, do not bottom-fish):** daily close below **$0.001199** (52w low).
> - Stated for completeness so this verdict is falsifiable: it would be **wrong** if PUMP holds above SMA200 **$0.001890** *and* the split is untouched at the next revision window. At 3.5x annualized revenue with a 20.6% buyback yield, PUMP is the cheapest verified cashflow in the book. The AVOID stands because launchpad revenue is the most cyclical and competitively-attackable cashflow in crypto, terminal value is genuinely uncertain, the fee split has already been revised twice (100% → 0% → 50%), and FDV $1.80B vs $845M mcap = 53% supply overhang. That is a defensible risk call — "accrual unproven" was not.

---

### 11. LINK — Chainlink

| Metric | Value |
|---|---|
| Price | **$8.32** |
| 52w Range (intraday) | **$7.02 ↔ $27.74** — *corrected 2026-07-29; the drafted $30.94 high is unsupported by any pulled series (Yahoo LINK-USD 1y intraday max = $27.74, close max = $26.75). The $6.996 low was ~right on an intraday basis ($7.02).* |
| % from 52w High | **−69.9% (intraday basis) / −68.8% (close basis)** — *−73.1% was derived from the bad $30.94 high* |
| Latest Weekly Close | $8.32 (−0.8% from $8.39) |
| Volume Trend | Declining (13.8M → 5.7M weekly) |

**Assessment:** LINK price as of 2026-07-24:
| Source | Price | Type |
|---|---|---|
| OKX LINK-USDT (matching engine) | **$8.594** | spot (Jul 27 15:18 UTC) |
| Kraken LINKUSD (matching engine) | **$8.5848** | spot (Jul 27 15:18 UTC) |
| Coinbase LINK-USD | **$8.5815** | spot (Jul 27 15:18 UTC) |
| CoinGecko (live) | **$8.60** | aggregate (Jul 27 15:17 UTC) |
| Yahoo close Jul 24 | **$8.33** | daily close |

**Corrected 2026-07-27 (analyse-onchain seat):** an earlier draft of this row listed Jul 27 spot as **$8.80**; four independent venues at 15:18 UTC say **$8.58–8.60** (max spread 0.22%). The $8.80 figure was stale/wrong by ~2.4% and has been replaced.

> **LINK PRICE DISCREPANCY — RESOLVED 2026-07-27 21:08Z.** This report carried **three mutually inconsistent "Jul 27 spot" figures** and asserted a false-precision winner:
>
> | Where in this doc | OKX | Kraken | Coinbase | Stamp |
> |---|---|---|---|---|
> | LINK section table (above) | 8.594 | 8.5848 | 8.5815 | 15:18Z |
> | Skeptic-gate table (Claim #1) | 8.611 | 8.6051 | 8.597 | 15:22Z |
> | Panel verdict line | — | — | — | quoted **$8.599** |
>
> **These are not conflicting data — they are three different ticks of a continuously-trading 24/7 market, taken minutes apart.** The actual error was declaring `Authoritative = OKX $8.594`: a single venue's single tick is not authoritative for a spot asset, and the 15:18Z and 15:22Z rows differ by only 0.2%, which is inside normal cross-venue spread.
>
> **Authoritative form going forward — a timestamped RANGE across ≥5 venues, never a single print.** Re-pulled 2026-07-27T21:08Z:
>
> | Venue | LINK/USD |
> |---|---|
> | OKX LINK-USDT | 8.622 |
> | Kraken LINKUSD | 8.605 |
> | Coinbase LINK-USD | 8.611 |
> | CoinGecko (aggregate) | 8.60 |
> | CoinPaprika | 8.6075 |
> | Hyperliquid oracle | 8.6215 |
>
> **LINK = $8.60–8.622 @ 2026-07-27T21:08Z (6 venues, max spread 0.26%).** All three earlier figures ($8.594 / $8.599 / $8.611) are consistent with this band and none was wrong; only the "authoritative single tick" framing was. The one figure that WAS wrong — $8.80 — remains retracted. Any downstream verdict may cite the band; no verdict may cite a single venue tick as *the* price.

The ~$0.27 gap between Jul 24 close ($8.33) and the Jul 27 $8.60–8.62 band is a Monday bounce, not a data error. The $16.73 in the Jul 22 report was a bogus/glitched print (wrong-ticker or stale quote); no −50% crash occurred. Yahoo 5-day closes were smooth ($8.46 → $8.33 → $8.37 → $8.594 Jul 23-27). LINK is grinding near its 52w low (**$7.02 intraday / $7.19 close basis**), **down 69.9% from its 52w high on an intraday basis (−68.8% close basis)** — the drafted "down 73%" came from an unsupported $30.94 high and is retracted. Real institutional thesis (CCIP, DTCC/Swift pilots) intact but token price has no demand at these levels.

**Verdict WATCH — $8.33 Jul 24 close confirmed; $16.73 from Jul 22 was bad data. Spot $8.26–8.28 as of 2026-07-29T15:12Z (3 venues, max spread 0.06%). Oversold candidate but no reversal signal yet.**

> **Invalidation / re-entry levels (added 2026-07-29; CoinGecko 366 daily closes, pulled 15:2xZ):** spot **$8.28**, SMA50 $7.99, SMA200 $9.44, 52w range **$7.19**–$26.73 (the "$7.00 52w low" used above is approximate; the pulled series low is **$7.19**).
> - **WATCH → BUY (ladder start)** on a weekly close above **$9.44** (SMA200), which would end a 69% downtrend. Absent that, CCIP adoption is real but bids nothing.
> - **WATCH → AVOID** on a daily close below **$7.19** (52w low). Fees settle in weekly lumps (304 of 355 days print $0), so a new low with no accrual floor is capitulation, not value.
> - **Do not size on the Aave-CCIP headline alone** — it is an integration datapoint, not a token-demand mechanism.

---

## CIO Synthesis

### Tier Scoring (1-5)

| Token | Fundamental | Technical | Macro | Catalyst | Conviction |
|---|---|---|---|---|---|
| **BTC** | ✅ (scarce) | ⚠️ (below EMA20/200) | ⚠️ (F&G 28) | ETF rotation uncertainty | **WAIT $60K** |
| **ETH** | ✅ (TVL $41B) | ⚠️ (downtrend) | ⚠️ | ETH ETF streak diverging | **HOLD** |
| **SOL** | ⚠️ (TVL real) | ❌ (volume dying) | ⚠️ | None visible | **HOLD** |
| **TON** | ❌ | ❌ (below MAs) | ⚠️ | None | **TRIM** |
| **HYPE** | ✅ (perp DEX) | ⚠️ (−23% from ATH) | ⚠️ | Pullback, healthy | **WATCH $50-55** |
| **AAVE** | ⚠️ (TVL $14.6B, but 0% accrual) | ⚠️ (base building) | ⚠️ | buyback restart UNDATED | **HOLD (existing) / AVOID (new)** |
| **UNI** | ⚠️ (burn live, 3.49% capture) | ✅ (+8.3% wk) | ⚠️ | v4 fee vote (burn already live) | **HOLD** |
| **JUP** | ⚠️ (product OK) | ❌ (**−65.2% from 52w high**; −87% is the ATH basis) | ⚠️ | None | **AVOID** |
| **AERO** | ⚠️ (fees real, emission 1.9x) | ❌ (−72% from 52w high) | ⚠️ | veAERO lock required | **WATCH (lock-only)** |
| **PUMP** | ✅ (20.6% buyback yield) | ❌ (penny token) | ⚠️ | Buyback live daily | **AVOID (risk, not accrual)** |
| **LINK** | ✅ (institutional) | ❌ (**−69.9% from 52w high**, intraday basis) | ⚠️ | Oversold candidate | **WATCH** |
### Key Portfolio Decisions

1. **AAVE re-derived, no longer the primary accumulator (2026-07-27/28, verdict-critic pass).** $14.74B TVL at MC/TVL ~0.10, GHO $648M, price up +5% this week while everything else red — but buybacks have been OFF since 2026-04-19 (governance-confirmed, `holdersRevenue 30d= $0`, 99+ days), revenue run-rate is the worst-contracting name in the book (−61% vs trailing-1y), and the only restart signal is an undated founder statement of intent, not a committed AIP. V4 deposit growth ($11.3M→$303M) is real but does not accrue to the token by design. **HOLD existing / AVOID adding new capital** — cheap multiples on zero accrual are not a bargain. This is a downgrade from the panel's original BUY ZONE call, not a caveat on it.

2. **Secondary watch:** HYPE pullback to $50-55 (−28-35% from ATH). Perp DEX growth narrative intact. Not time yet — wait for lower.

3. **Trimming:** TON at $1.44 with −58.5% to −59.1% from its true 52w high ($3.57, corrected 2026-07-27/28 from a drafted −49.2%) and no catalyst. Cut position size.

4. **No action:** BTC/ETH/SOL — hold. JUP/AERO/PUMP — avoid. LINK — WATCH (**$8.26 @ 2026-07-29T15:12Z**, 3 venues, max spread 0.06% — see SKEPTIC GATE §S1; the $8.33 Jul 24 close is confirmed and Jul 22's $16.73 was bad data). *Per §11, never cite a single venue tick as "the" price — the $8.594 OKX figure previously quoted here is retracted as a framing error.*

5. **New insight (downgraded 2026-07-27):** ETH ETF divergence (+$26.3M, 5-day streak vs BTC's −$225M outflow) looked like the most interesting signal this week, but the streak snapped Jul 25 and ETH's week closed red while BTC shed −$465M over two days — **both** complexes still booked a third straight WEEKLY inflow. Keep the relative claim (ether funds ≈ bitcoin funds' capital on ~1/8 the assets over three weeks); drop the "live streak" framing. ETH may still be a relative outperformer, but this is no longer the week's cleanest signal.

6. **New insight (analyse-defi seat, 2026-07-27) — value accrual is contracting across the whole book.** Every protocol token here has 30d-annualized revenue *below* its trailing-1y: **AAVE −61%, AERO −58%, JUP −54%, HYPE −44%, PUMP −26%.** UNI is the sole fee accelerator (~+32%), but holders capture only 3.49% of it. Ranked by *verified* buyback yield on market cap: **PUMP 20.6% > AERO 11.8% (ve-locked only) > JUP 4.2% > HYPE 3.4% > UNI 1.65% > LINK 0.9% > AAVE 0.0% (paused).** The book's cheap multiples are falling numerators, not discovered bargains — size for that.

7. **Mechanic-verification discipline.** Three of this report's protocol claims were stale and have been corrected in-line (UNI "fee switch pending" → live since 2025-12-28; PUMP "accrual unproven" → $14.3M/30d live daily; AAVE buyback → paused 99 days). **A zero in `holdersRevenue` is ambiguous**: LINK's zeros are batching (settles in lumps, last print $1,148,131 on 2026-07-23), AAVE's zeros are a governance pause. Only a governance-forum fetch distinguishes them — the API cannot. Re-verify mechanics every run; do not carry them forward from memory.

### Risk Overlay

- F&G 28 (Fear), ↓3 pts from Jul 22. Market getting more scared.
- BTC death cross active — alts highly correlated.
- BTC ETF outflow day (−$225M) was large but BlackRock dominated (−$202.5M) — likely one large account rotating, not a structural shift.
- Macro headwinds: US-Iran tensions, 10Y yields at 18-month high (~4.70%), tariffs escalating, and **oil back ON as a headwind — WTI $85.41 / Brent $90.92 live 2026-07-29T15:02Z**, above their pre-spike closes after a full round-trip and reversal (see SKEPTIC GATE §S2).
- ETH ETF divergence offers a potential rotation hedge within crypto — **but sized down 2026-07-27: the daily inflow streak broke Jul 25 and both complexes still posted a third weekly inflow, so this is a relative-strength tilt, not an active rotation signal.**
- **Oil round-tripped, then reversed — net headwind RESTORED.** WTI $89.31 (Jul 24) → $79.26 (Jul 28) → **$85.41** (Jul 29 live); Brent $96.78 → $84.09 → **$90.92**. The Jul-28 claim that this was "a bigger macro tailwind against the report's bearish framing" is **RETRACTED** — it held for one session. Treat oil as a high-volatility, low-conviction leg in either direction, not as a durable input.
- No single asset should exceed 5-10% of crypto book at current regime.
- **AAVE-specific:** unresolved rsETH bad-debt allocation is a live balance-sheet risk, not just a paused-buyback issue. The pause exists precisely to preserve treasury capacity for a possible DAO-level response.

### Skeptic-gate correction log (2026-07-27)

| # | Claim as drafted | Verified value | Source |
|---|---|---|---|
| 1 | LINK spot Jul 27 **$8.80**; then three inconsistent venue sets ($8.594 / $8.599 / $8.611) with "Authoritative = OKX $8.594" | **$8.60–8.622 @ 21:08Z** (OKX 8.622, Coinbase 8.611, HL oracle 8.6215, CoinPaprika 8.6075, Kraken 8.605, CoinGecko 8.60; max spread 0.26%). $8.80 retracted; the three earlier prints were all in-band ticks — the ERROR was naming a single tick authoritative | 6 venues, 2026-07-27T21:08Z — see **LINK PRICE DISCREPANCY — RESOLVED** block in §11 |
| 2 | WTI Jul 27 **$84.75**, then **$83.28**, then **$81.64**, then **$81.85**, then **$82.00** | **$85.41 — canonical, live 2026-07-29T15:02Z.** Five prior "resolved" values in this doc were each wrong by 0.2-2% *at the time*; the Jul-28 $82.00 was accurate but went stale in one session (Jul 28 close $79.26 → Jul 29 $85.41). **Cite $85.41 only** | Yahoo `CL=F`, live 2026-07-29T15:02Z — see **SKEPTIC GATE §S2** |
| 2b | Brent Jul 27 **$89.56**, then **$87.50**, then **$87.66**, then **$87.75** | **$90.92 — canonical, live 2026-07-29T15:02Z**; low was $84.09 on Jul 28. The Jul-28 $87.75 is RETRACTED as stale | Yahoo `BZ=F`, live 2026-07-29T15:02Z — see **SKEPTIC GATE §S2** |
| 3 | WTI prior-week close **$83.33** (+7.1%) | **$82.49** Jul 17 (+8.3%) | Yahoo `CL=F` daily |
| 4 | AERO "only 2 weekly bars", 52w range **$0.410↔$0.518** | **365 daily points**, 365d range **$0.3018↔$1.4907**, ATH $2.32 (2024-12-07) | CoinGecko market_chart |
| 5 | UNI fee switch "if activated" | **Live since 2025-12-28**, 11 chains, 3.49% realised capture | gov.uniswap.org t/26162 |
| 6 | PUMP "accrual unproven", "$500M+/yr" | **$14,301,309/30d buyback, daily**; revenue 1y **$323,949,113** | DeFiLlama dailyHoldersRevenue |
| 7 | AAVE "best risk/reward", buyback implied live | **Paused since 2026-04-19**, `holdersRevenue 30d= $0` | governance.aave.com t/24686 |
| 8 | ETH ETF "5-day inflow streak" / BTC "−$225M" as live rotation signal | **Streak SNAPPED Jul 25**, ETH week closed red; BTC shed **−$465M over 2 days** (IBIT −$415M); **both** complexes still logged a **third consecutive weekly inflow** | cointelegraph.com/markets/ethereum-etfs-week-red-end-inflow-streak; coindesk.com/markets/2026/07/27/bitcoin-etfs-record-third-consecutive-weekly-inflows-despite-losses-of-usd465-million-to-end-week |
| 9 | HYPE "Jul-29 unlock, 2.8% of circ = $817M, same day as FOMC" | **Fabricated / arithmetically wrong.** 2.8% × 222,445,714 circ = 6.23M tokens ≈ $363-373M, not $817M. Real next unlock: **2026-08-06, 9,916,667 HYPE (~$594.6M), Core Contributors cliff** — single-sourced, re-check before sizing | tokenomist.ai (refreshed 2026-07-27 15:32 UTC); cryptorank paywalled, `api.llama.fi/emission` HTTP 402 |
| 10 | TON "−49.2% from 52w high" | **−58.5% to −59.1%** from true 52w high **$3.5722-3.5747 (2025-08-02)**, re-pulled live | CoinGecko `coins/the-open-network/market_chart`, 366 daily pts, 2026-07-28T00:25:30Z |
| 11 | AAVE "BUY ZONE" / "ACCUMULATE-WITH-CAVEAT" | **Downgraded to HOLD (existing) / AVOID (new capital)** — 99+ days $0 buyback, worst revenue contraction in book (−61%), restart is undated intent (Stani, t/24936 post 16) not a committed AIP, V4 growth ($11.3M→$303M) doesn't accrue to token by design | governance.aave.com t/24686 + t/24936; DeFiLlama `holdersRevenue` |
| — | Binance LINK/AERO cross-check | **[FETCH FAILED: api.binance.com — HTTP 451 geo-restricted]** | not imputed |
| — | AERO exact gross emission | **[FETCH FAILED: api.llama.fi/emission/aerodrome-v1 — HTTP 402]** → net-supply-delta proxy used, labelled | not imputed |

**Gate status: PASS after correction.** 11 claims challenged, 11 resolved with live fetches, 2 failures recorded verbatim rather than guessed. Claims #9-11 were added/re-verified in this 2026-07-27/28 correction+republish pass (HYPE unlock fabrication, TON drawdown, AAVE verdict re-derivation) — WTI/Brent (#2/#2b) also re-verified a 3rd time in this same pass to eliminate a lingering internal inconsistency ($81.85/$87.66 vs $81.64/$87.50) between two earlier "resolved" values.

### Verdict-critic pass (2026-07-27) — BTC / ETH / SOL

Adversarial re-verification of the current BTC-HOLD / ETH-HOLD / SOL-SELL verdicts against live primaries:

| Claim | Live check | Result |
|---|---|---|
| ETH net-inflationary +0.85%/yr | 121,815,730 (06-27 15:00Z) → 121,884,168 (07-21 20:14Z), 24.22d = **+0.8467%/yr** (ultrasound.money) | **Reproduces exactly**; window ends 07-21 (6d stale) and burn is demand-dependent — chain fees are **+20.38% 7d** |
| ETH 97.4% fee leak, $7.07M to L1 | L1 fees 30d **$7,066,764** vs chain fees 30d **$273,171,285** = 2.59% captured (DeFiLlama) | **Reproduces exactly**; P/S ≈ 2,707x |
| SOL inflation 3.725%/yr, all to validators | Solana RPC `getInflationRate` epoch 1008: total **0.03724738633549205**, validator same, foundation **0.0** | **Reproduces exactly** — but it is a point on a ~−15%/yr disinflation schedule to a 1.5% floor, and is governance-mutable |
| SOL "chain fees 30d $15.06M vs 1y $276.4M" | That is DeFiLlama's **L1 base-fee adapter** ($15,057,242 / $276,418,849). True **chain** fees are **$211,249,217/30d vs $4,139,945,000/1y**, change_7d **+19.85%** | **MISLABELLED** — understates network economics ~14x and hides rising weekly fees |
| SOL Jito MEV −66% | $6,555,618/30d vs $233,299,225/1y = **−66.3%** run-rate | **Reproduces** — but Jito Labs just launched **JTX**, changing forward revenue base |
| BTC Strategy 843,775 BTC @ $75,476, "~$9.3B underwater" | 843,775 × ($75,476 − $64,704) = **$9.089B** | Overstated ~$0.2B |
| BTC Strategy cash build read as bearish | Strategy also tapped its $1B preferred buyback for the **first time** ($25M STRC); **Benchmark reiterates $570**, calling the cash reserve a *strengthening* of the BTC acquisition plan | **Contested interpretation**, not settled fact |

**Missed catalysts flagged:** US-Iran strike pause repricing risk assets; BOE + BOJ decisions and Strategy earnings this week (not just the Jul 29 FOMC); Galaxy's dormant-BTC-at-4-year-low (rebuts the LTH distribution framing); **CLARITY Act collapse risk before the August recess** (largest live classification input for ETH and SOL); and for SOL a live adoption cluster — stablecoin supply crossing **$15Bn** first time, Jito JTX, LayerZero/Keeta tokenized bank deposits, Grayscale SOL staking cash distributions — which makes a **unanimous 6/6 bearish** quorum look correlated rather than independent.

---

### Verdict-critic pass (2026-07-27) — JUP / UNI / AERO / PUMP / LINK

Second adversarial pass, run by a critic with no prior knowledge of the panel run. Every figure below was re-pulled live from DeFiLlama, CoinGecko, Hyperliquid `metaAndAssetCtxs`, `gov.uniswap.org`, and the repo `read_news.ts` pipeline. **All five verdicts FLAGGED.** The arithmetic in the original panel reproduced almost everywhere — the failures are of *freshness*, *sign*, and *coverage*, not of maths.

#### What reproduced exactly (panel was right)

| Token | Claim | Live value | Source |
|---|---|---|---|
| JUP | HoldersRevenue $2.12M/30d | **$2,115,951** | `api.llama.fi/summary/fees/jupiter?dataType=dailyHoldersRevenue` |
| JUP | 4.2% buyback yield, P/S 12.0x, 48.4% circulating | **4.14%**, **12.1x**, **48.38%** (3.320B/6.862B) | DeFiLlama + CoinGecko |
| UNI | burn ≈1.65% of circulating annualized; 43.7% below 200wMA | **1.65%** (10.31M/625.1M); **−43.7%** | CoinGecko |
| AERO | holdersRevenue $4.19M/30d; 50.1% circulating | **$4,189,859**; **50.08%** | DeFiLlama + CoinGecko |
| PUMP | $14.30M/30d, 20.6% of mcap, P/S 3.5x, 53% overhang, daily prints no gaps | **$14,301,309**; **20.2%**; **3.59x**; **53.0%**; **40/40 non-zero days** | DeFiLlama + CoinGecko |
| LINK | $4.84M/30d revenue; 0.9% buyback yield; `totalAllTime ≈ total1y` | **$4,841,696**; **0.87%**; **$56,911,607 == $56,911,607**, series starts 2025-08-07 | `fees/chainlink`, `fees/chainlink-staking` |

#### The five FLAGs

| # | Token | Failure | Correction + source |
|---|---|---|---|
| **F1** | **UNI** | **STALE MECHANIC — thesis-invalidating.** Verdict: "Uniswap v4 ($798.6M TVL) contributes exactly zero", used to cut realised holder capture from 17% → 3.49%. | v4 fees contribute zero *today only*. **[Temp Check] Activate v4 Protocol Fees** (UniswapLabs, opened 2026-07-07, 21 posts / 1,587 views) **cleared the offchain vote and is at the ON-CHAIN stage** — L2BEAT, 2026-07-22: *"We supported activating protocol fees for Uniswap v4 during the offchain vote, and we continue to support it at the on-chain stage."* → https://gov.uniswap.org/t/26162.json. The 3.49% is a **floor with a dated in-flight catalyst**, not a ceiling. |
| **F2** | **JUP** | **STALE DATA — headline bear input is dead.** Verdict: "Hyperliquid funding −25.94% (deepest real negative premium)", stacked as a bear datapoint. | Live `api.hyperliquid.xyz/info` `metaAndAssetCtxs`, 2026-07-27: JUP `funding` = 2.2485e-06/hr = **+1.97% annualized (POSITIVE)**, premium −0.00035. Funding is an hourly mean-reverting print, never a regime. **And the sign was inverted anyway** — deeply negative funding means shorts pay longs (crowded short / squeeze fuel), a contrarian *bullish* signal. Also **MC/TVL is 0.40**, not 0.30 (mcap $622,546,764 / TVL $1,548,754,731, `api.llama.fi/protocol/jupiter`). |
| **F3** | **AERO** | **SIGN ERROR in a derived bound.** Verdict: "+18.24M AERO/30d … the 1.9x figure is a DERIVED upper bound" (from a CoinGecko net-circulating delta, after DeFiLlama emissions returned HTTP 402). | The delta **reproduces** (953,472,860 on 06-23 → 974,205,039 on 07-27 = +20.73M/34d ≈ +18.3M/30d) but the bound is **inverted**: CoinGecko circulating **excludes veAERO locks**, so net delta = gross mint − net new locks; with 50.08% of supply locked, positive net locking makes +18.24M a **LOWER** bound on gross emission. Separately, the "1.9x" compares two **different claimants** (emissions pay LPs to source TVL; fees+bribes pay veAERO) — that is ve(3,3) by design, not a discovered defect. **Restate as supply inflation: ≈ +1.87%/30d ≈ +25%/yr.** Context: total fees **$6,115,701**/30d vs holdersRevenue **$4,189,859**/30d = **68.5% capture**. |
| **F4** | **PUMP** | **MISSING CATALYST — claim falsified in its own window.** Verdict: "the +20-40% move is attributed to ONE named influencer (Ansem) … **not a protocol or flow event**." | Ansem is confirmed (entry ~$0.001675, volume +500% to ~$131M — https://coinpedia.org/price-analysis/pump-price-jumps-22-as-open-interest-surges-can-bulls-break-0-0022/) **but the move is over-determined**: Pump.fun **activated BOOST mode ~2026-07-21** — TWAP-driven buyback-and-burn on *every* newly bonded token, targeting >$100M/yr of dead migration liquidity (https://coinmarketcap.com/community/articles/6a5f98b6cb03952702fe3a38) — a **protocol** event; and moved **81.7K SOL ($6.15M) to Kraken on 2026-07-20** (https://coinmarketcap.com/community/articles/6a5e4e37c82f037e072a00ba) — a **flow** event. Also: run-rate decay is understated — `totalAllTime` fees $1,150,549,001 vs `total1y` $404,490,347 means **65% of all fees ever were earned before the trailing year**. |
| **F5** | **LINK** | **COVERAGE GAP + overstated unverifiability.** Verdict: "96% is off-chain enterprise/CCIP revenue DeFiLlama cannot independently verify"; SELL on 5 bears. | (a) **Aave standardised its entire cross-chain infrastructure on Chainlink CCIP on 2026-07-21** — already routing GHO transfers and multi-chain governance via a.DI (https://www.binance.com/en/square/post/344880926843026); plus **Lombard Finance CCIP adoption 2026-07-23** (https://coinmarketcal.com/event/ccip-cross-chain-deposits-04495272-1). Largest DeFi integration datapoints in the window, absent from all 6 seats. (b) The **deposits are on-chain observable** — that is precisely what DeFiLlama charts; what is unverifiable is the **attribution** to enterprise billing, not their existence. (c) The **stronger** verified point the panel missed: **304 of 355 days print exactly $0** (and `total24h` = 0) — the Reserve is funded in ~weekly lumps, a materially weaker "buyback" than PUMP's continuous daily prints. (d) The cited bear TA ("LINK lost $8.38 support") **already invalidated** — LINK is $8.60–8.622 as of 21:08Z; and the 5 sanctioned crypto feeds returned `INSUFFICIENT_DATA` for "Chainlink" over 10 days, so both legs of that contradiction are low-tier aggregator content. |

#### Systemic pattern

Three of five (**UNI, JUP, AERO**) fail the *same* way: the panel reads a mechanic's **current state** and treats it as structural, without asking (i) is governance mid-change, (ii) does this metric mean-revert on an hourly clock, (iii) does my derivation's bias have a known sign. Add these as standing pre-checks before any mechanic is used as a verdict driver.

Two (**AERO 6/6 bearish, LINK 5/6 bearish**) show the **correlated-quorum** signature already flagged for SOL above — unanimity on a name that is holding its 200d after a fresh Binance spot listing (AERO, 2026-07-17, AERO/USDT + AERO/BNB + AERO/FDUSD, Seed Tag — https://coinmarketcal.com/event/binance-listing-44704192-1) is not independent confirmation.

#### Net verdict changes

> **READ THIS BEFORE THE TABLE (reconciliation added 2026-07-29).** The `Was`/`Now` columns grade **what the 6-seat analyst panel output**, before and after the verdict-critic pass. They are *not* the book's position. Earlier revisions of this document left the two side by side unlabelled, so JUP read "HOLD" here and "AVOID" in §7, AERO "SELL" here and "WATCH" in §9, PUMP "HOLD" here and "AVOID" in §10. Those were never disagreements about the trade — they are two different objects. **The `CANONICAL BOOK VERDICT` column is the only one that governs a position.** Where the panel and the book differ, the book wins and the reason is stated.

| Token | Panel: was | Panel: after critic | **CANONICAL BOOK VERDICT** | Why the book differs (or doesn't) |
|---|---|---|---|---|
| JUP | HOLD | HOLD (bear stack thinned) | **AVOID** (§7) | Panel graded the *analysis* as reproducing; the book still refuses new capital on a −54% revenue run-rate and no reversal. "Bear case is thinner" ≠ "buy it." |
| UNI | HOLD | HOLD → constructive bias | **HOLD** (§8) | Aligned. The constructive bias is a *tilt within* HOLD (sole fee accelerator, +27.3% vs 1y), not an upgrade to ADD — holders still capture only 3.49%. |
| AERO | SELL | SELL (rationale restated) | **WATCH — lock-only** (§9) | Book is *less* bearish than the panel, deliberately: the panel priced a spot holder (structurally diluted, SELL is right for them); the book's WATCH applies **only to the ve-locked class**, which does capture fees. Holder-class split, not a contradiction. |
| PUMP | HOLD, do not chase | HOLD, do not chase | **AVOID** (§10) | Book is *more* bearish than the panel. Panel judged accrual (real, 20.6% buyback yield); book vetoes on terminal-value risk + a fee split revised twice + 53% supply overhang. Risk veto beats accrual. |
| LINK | SELL | SELL → WATCH | **WATCH** (§11) | Aligned after the critic pass. 109x revenue justifies "don't add"; it does not justify liquidating into the Aave CCIP standardisation the panel never saw. |
| BTC | — | — | **HOLD, accumulate $60–62K** (§1) | The Tier-Scoring table's "WAIT $60K" is the same call stated as an entry level, not a second verdict. |
| SOL | — | — | **HOLD** (§3) | A seat-level SELL lean appears in the critic notes; the book holds — volume decay is a reason not to *add*, and $60 is the stated floor. |

**Net: the book runs BTC/ETH/SOL HOLD · TON TRIM · HYPE/LINK WATCH · AERO WATCH (lock-only) · AAVE HOLD-existing/AVOID-new · UNI HOLD · JUP/PUMP AVOID.** Every one of those now carries a price or governance invalidation level in its section.

> **Corrected accelerator figure:** UNI `dailyFees` total30d = **$89,567,655** vs total1y $855,888,834 ($2.986M/d vs $2.345M/d) = **+27.3%**, not the drafted +32% (https://api.llama.fi/summary/fees/uniswap?dataType=dailyFees). Also missed for UNI: **Robinhood Chain** — Uniswap live at the 2026-07-01 mainnet debut, **>$1B cumulative swap volume by 2026-07-10**, fee expansion at on-chain stage (https://gov.uniswap.org/t/26168.json); and the 2026-07-23 **permissioned tokenized-asset pool framework** with Superstate / Securitize / Dowgo (https://www.coindesk.com/business/2026/07/22/uniswap-pushes-deeper-into-tokenized-assets-with-permissioned-trading-pools). And the "live RFC replacing the burn with staking" cited as a UNI risk is an **unsponsored community post** — gov.uniswap.org topic 26132, author `Mr.Vock`, 4 posts / 169 views, no delegate backing, no Snapshot, dormant since 2026-07-10, and its sole substantive reply *opposes* it.

---

## SKEPTIC GATE — 2026-07-29T15:12Z (pre-publish, fresh pulls)

Two prior "RESOLVED" blocks were re-tested against live data before publishing. One holds, one is now **STALE**.

### S1. LINK price — HOLDS as-of, superseded by fresh tick

| Venue | LINK/USD | Timestamp |
|---|---|---|
| Coinbase LINK-USD | **$8.264** | 2026-07-29T15:12:47Z |
| Kraken LINKUSD | **$8.2592** | 2026-07-29T15:11Z |
| CoinGecko | **$8.26** | 2026-07-29T15:11:30Z |

Max spread **0.06%**. The §11 resolution ($8.60–8.622 @ 2026-07-27T21:08Z, 6 venues) was correct **for its timestamp** and is not retracted. LINK has since drifted **−4.0%** to **$8.26 @ 2026-07-29T15:12Z**. Verdict **WATCH is unchanged** — the name is grinding closer to its 52w low ($7.00), which strengthens "oversold, no demand," not weakens it. Any downstream cite must use $8.26 @ Jul 29, not the Jul 27 band.

### S2. Oil macro — "headwind GONE" is **INVALIDATED**

The Jul 28 canonical block concluded the Iran geo-premium had "fully round-tripped" and instructed readers not to cite oil as a bear input. Fresh Yahoo pull extends the series:

| Date | WTI CL=F | Brent BZ=F |
|---|---|---|
| Jul 17 (pre-spike close) | 82.49 | 88.10 |
| Jul 23 (Iran peak) | 92.19 | 100.69 |
| Jul 24 (report snapshot) | 89.31 | 96.78 |
| Jul 27 close | 82.61 | 88.36 |
| **Jul 28 close** | **79.26** | **84.09** |
| **Jul 29 live (15:02Z)** | **85.41** | **90.92** |

The unwind overshot to **$79.26 on Jul 28** (deeper round-trip than the Jul 28 block captured), then **reversed +7.8% in one session to $85.41**. WTI is now **ABOVE** the $82.49 pre-spike close (+3.5%); Brent $90.92 is **above** its $88.10 pre-spike close (+3.2%). **The oil leg of `Regime: BEARISH` is back on.** The Jul 28 instruction "do not cite oil as a bear input" is **withdrawn** — it was correct for a 24-hour window and is wrong today.

**Net effect on the regime call:** `BEARISH` was built on four legs (F&G 28, BTC death cross, 10Y ~4.70%, oil shock). The Jul 28 pass knocked out the oil leg and downgraded the ETF-rotation read; this pass **restores the oil leg**. Regime label **BEARISH stands, on firmer footing than the Jul 28 revision implied** — but note the whipsaw: a macro input that round-trips ±10% in three sessions is a low-conviction leg in either direction. Size for volatility, not for direction.

**No token verdict changes.** BTC/ETH/SOL HOLD, TON TRIM, LINK WATCH, JUP/AERO/PUMP AVOID all stand.

---

*Report generated 2026-07-24. Corrections and verdict-critic passes appended 2026-07-27. Pre-publish skeptic gate appended 2026-07-29. Data: TradingView MCP, CoinGecko, DeFiLlama, Hyperliquid, gov.uniswap.org, Yahoo Finance, SoSoValue, repo `read_news.ts` pipeline. Educational only.*
