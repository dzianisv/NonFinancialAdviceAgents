# Crypto Portfolio Run — 2026-07-21

**Universe (custom token-override):** BTC, ETH, SOL, TON, HYPE, AAVE, JUP, UNI, AERO, PUMP, LINK
**Run timestamp:** 2026-07-21 (data: TradingView MCP + live FRED/DeFiLlama/OKX/read-news fetches this run)
**Recommend-only. No trades executed.**

---

## Exec Recap

Highest-conviction buys: ETH, SOL and UNI clear the full-size bar — each roughly a quarter or more below its long-run trend average with an expanding Fed liquidity backdrop behind it. HYPE and AAVE take small starter positions: HYPE because it's a young token with too little price history for a full-size call, AAVE because real cash-flow fundamentals are strong but a genuine contributor exodus (three core teams have quit over an unresolved revenue dispute, with one insider publicly confirming he sold his own holdings) is a live execution risk worth respecting. JUP and PUMP, both flagged as buy/sell candidates in the first draft, are downgraded to hold once independently fact-checked: JUP's bull case rested on a buyback narrative that already produced a brief pop and fully reversed earlier this cycle, and PUMP's sell case rested on a token unlock that has already happened — smaller than feared, with the price rising afterward, not falling. AERO is the one clear sell: its locked deposits have fallen roughly 70% from last year's peak, a decline confirmed current, not a stale story. Narrative: Fear & Greed reads 25 (Fear) while Fed liquidity has expanded for four straight weeks — a tug-of-war between cautious sentiment and improving conditions that explains why more than half the book still sits at hold or small-size rather than full conviction.

**Verdict Critic (Step 4, all 11 tokens):** Every single token was independently fact-checked by a fresh subagent with no memory of the quorum synthesis, reading today's news and DeFiLlama data fresh. **All 11 tokens returned OVERALL: FLAG** — see the `critic_note=` line under each token's quorum block for the exact correction applied. Three FLAGs were material enough to change the signal (AAVE: BUY→BUY(small); JUP: BUY(small)→HOLD; PUMP: SELL→HOLD); the remaining eight were factual/framing corrections that did not change the final call. ✅ Verdict Critic: 11/11 tokens reviewed.

**Portfolio Governor:** Fear & Greed = 25. The index provider's own label is "Extreme Fear," but the skill's numeric band table places 25 inside the FEAR band (25–49, not Extreme Fear 0–24) — cap = 6 buys (not the Extreme Fear cap of 4). Buy-tier signals after Verdict Critic revisions: ETH, SOL, UNI (full BUY) + HYPE, AAVE (BUY small) = **5 of 6** — under the cap, no downgrade required. SELL and HOLD signals are not subject to the buy-side cap.

---

## Block 1 — Signal table (one-glance summary)

```
=== CRYPTO PORTFOLIO RUN — 2026-07-21 ===   (data: TradingView MCP)

Token | Signal                    | Valuation | Quorum    | Bulls/Bears | Critic
------|---------------------------|-----------|-----------|-------------|----------------
BTC   | HOLD ⚠️ CITATION_FAILED   | fair      | SPLIT     | 2 / 1       | ⚠️ FLAG (no chg)
ETH   | BUY             | cheap     | BULLISH   | 2 / 0       | ⚠️ FLAG (no chg)
SOL   | BUY             | cheap     | BULLISH   | 2 / 1       | ⚠️ FLAG (no chg)
TON   | HOLD            | cheap*    | UNCERTAIN | 2 / 2       | ⚠️ FLAG (no chg)
HYPE  | BUY (small)     | fair      | BULLISH   | 4 / 0       | ⚠️ FLAG (no chg)
AAVE  | BUY (small)     | cheap     | SPLIT     | 2 / 2       | ⚠️ REVISED (was BUY)
JUP   | HOLD            | cheap*    | SPLIT     | 2 / 2       | ⚠️ REVISED (was BUY small)
UNI   | BUY             | cheap     | BULLISH   | 3 / 1       | ⚠️ FLAG (no chg)
AERO  | SELL            | cheap*    | BEARISH   | 1 / 4       | ⚠️ FLAG (no chg)
PUMP  | HOLD            | rich      | SPLIT     | 1 / 2       | ⚠️ REVISED (was SELL)
LINK  | HOLD            | cheap*    | UNCERTAIN | 1 / 1       | ⚠️ FLAG (no chg)

* = valuation read vs a long-run average built on fewer than 200 weekly bars (thin/unconfirmed history — see Block 2 for exact bar counts). fair/cheap/rich are plain-English translations of the trend-vs-price read, not a formal band. "Critic" = Verdict Critic (Step 4) outcome — all 11 tokens FLAGGED; 3 required an actual signal change (⚠️ REVISED), 8 were factual/framing corrections with no change to the final call (⚠️ FLAG, no chg). BTC's Signal column carries ⚠️ CITATION_FAILED from Step 5 (Citation Validator): 2 of its cited sources did not support their paired claim on re-fetch (see Block 2 narrative and the Step 5 report in Block 3) — both have been corrected in-place; the HOLD call itself is unchanged.
```

**Governor note on corrections vs each sub-analyst's initial draft label:** SOL and AAVE(original) were initially drafted as scaled-down entries by their respective research passes; re-applying the skill's literal quorum rule (a CORE-lens dissent only forces a hedge at HIGH conviction — both were MEDIUM or absent) resolved them to full BUY in the first normalization pass. JUP was initially drafted HOLD; the decision table's second BUY(small) path (`quorum=SPLIT, zone=cheap, bull-leaning`) was met and missed in the first pass, so it was corrected to BUY(small) in the first normalization pass. PUMP was initially drafted HOLD (SPLIT); the CORE dissent opposing the bearish lean was only MEDIUM conviction, not HIGH, so the rule did not cap it at SPLIT and the clearly negative CORE-driven lean (9 vs 4, ~2:1) stood as BEARISH/SELL in the first normalization pass. **These were mechanical rule-application corrections (SKILL.md lines 432–470), not re-litigations of the panel votes.** Subsequently, the mandatory Step 4 Verdict Critic pass (11/11 fresh, independent fact-checks against live news/DeFiLlama data) FLAGGED all 11 tokens and produced three further, substantively different corrections: AAVE was downgraded from full BUY to BUY(small) after the critic surfaced a genuine, current 3-contributor governance exodus (BGD Labs, Aave Chan Initiative, Chaos Labs) plus public insider selling that the original "core_dissent=NONE" call missed entirely; JUP was downgraded from BUY(small) to HOLD after the critic showed its bull-lean catalyst (the buyback narrative) had already fired and fully reversed once this cycle; PUMP was downgraded from SELL to HOLD after the critic showed the unlock cited as the core bear catalyst had already completed at a smaller-than-forecast size with a positive, not negative, price reaction. See each token's `critic_note=` line in Block 2 for full detail.

---

## Block 2 — Plain-English verdict per token

### BTC — HOLD ⚠️ REVISED (Verdict Critic FLAG — see below)

BTC just closed in on $67,000 [source: https://bitcoinmagazine.com/news/bitcoin-price-67000-lifting-crypto-stocks], and Fed liquidity is genuinely expanding (balance sheet growing, Treasury cash draining, reverse repo drained, money supply growth accelerating) while on-chain data shows holders are only in modest profit, not euphoric — both real tailwinds. But the price is still running below its 200-day trend average with a death-cross pattern in effect, so the longer-term chart hasn't confirmed a turn yet. **Citation-validator correction (Step 5):** an earlier draft of this section cited a JPMorgan analysis as flagging elevated structural risk in Bitcoin-proxy stocks like Strategy; on reference-check, the source actually says the opposite — JPMorgan explicitly states it does **not** see Strategy/MSTR as bitcoin's main structural risk, even accounting for pending CLARITY Act uncertainty [source: https://stocktwits.com/news-articles/markets/cryptocurrency/mstr-isnt-bitcoin-biggest-risk-even-clarity-act-may-not-fix-it-jp-morgan/cZmY2Z2R7nl — ⚠️ CITATION_FAILED, claim reversed vs. cited source]. This removes an overstated bearish data point; the HOLD call was never solely dependent on it. **Critic correction:** a 21-day/50-day golden cross has just formed alongside the still-active 50/200 death cross, and price is testing 7-week highs against the 21-week SMA (~$69,720) that the bear-market thesis is contingent on reclaiming [source: https://cointelegraph.com/markets/bitcoin-nears-seven-week-high-as-stocks-ignore-iran-strikes-trump-10-tariff-plans] — the technical picture is more dynamic/contested than a flat "death cross" label implies. The critic also surfaced real context the macro section omitted: Morgan Stanley launching BTC/ETH/SOL trading on E*Trade [source: https://decrypt.co/373681/morgan-stanley-launches-bitcoin-ethereum-solana-trading-etrade], plus an active geopolitical risk (Iran strikes, Strait of Hormuz tension, new 10% Trump tariffs) not previously weighed. **Citation-validator correction (Step 5):** a "BlackRock exec calling BTC 'too big to ignore' / new Bitcoin Premium Income ETF" claim was previously attributed to a Coindesk daybook piece; on re-fetch that article contains no mention of BlackRock, Morgan Stanley, or E*Trade at all — it covers ETF inflows, whale accumulation, options activity, and T-bill-issuance liquidity risk only. The BlackRock claim has been removed as unverifiable; the T-bill liquidity-drain risk point is retained, correctly attributed to that same source [source: https://www.coindesk.com/daybook-us/2026/07/21/bitcoin-rally-has-broad-based-support-as-institutions-whales-options-traders-pile-in — ⚠️ CITATION_FAILED, BlackRock/ETF-launch detail not present in source, corrected]. None of this reverses the HOLD call (news was assessed by the critic itself as mixed, consistent with a hold), but it makes the picture fuller and more accurately sourced. Watch for price to reclaim and hold above roughly $72,850 (the 200-day average) to confirm an uptrend, or a reversal of the recent Fed liquidity expansion, which would argue for more caution.

Research Desk:
  Technical:   Price $66,708.56 is above the 20/50-day averages but below the 200-day average with an active death cross; momentum (MACD, RSI 62) is turning up but hasn't reclaimed the long-term trend.
  On-Chain:    MVRV-Z 0.4071 [source: https://bitcoin-data.com/v1/mvrv-zscore/last] and NUPL 0.1958 [source: https://bitcoin-data.com/v1/nupl/last] show holders in modest, non-euphoric profit — an accumulation-style reading, not a cycle-top warning.
  DeFi:        n/a — L1 (no protocol revenue accrual)
  Macro:       Fed balance sheet up, Treasury cash draining, reverse repo drained, and money-supply growth accelerating are real liquidity tailwinds [source: FRED WALCL/RRPONTSYD/WTREGEN/M2SL series, fetched live this run], tempered by a firming dollar and a 27-month-old halving cycle that's now later than the typical bullish post-halving window; ETF flow data [UNAVAILABLE — farside.co.uk table is JS-rendered, no numbers returned this run] and Lyn Alden's latest macro commentary [UNAVAILABLE — no macro-relevant posts in the last 30 days] were unavailable this run.
  Smart Money: Perpetual funding is slightly negative (-0.0000310) [source: https://www.okx.com/api/v5/public/funding-rate] (mild bearish leverage skew) and the Fear & Greed index (25) [source: https://api.alternative.me/fng/?limit=5&format=json] sits in "Fear," not "Extreme Fear," despite the index provider's own extreme label; exchange whale-flow data [UNAVAILABLE — no accessible free on-chain exchange-flow API this run].

Panel:
  Graham (Value):          NEUTRAL — on-chain cheapness is real but BTC has no earnings/book value to apply a classic margin-of-safety test to.
  Buffett (Quality):       NEUTRAL — no cash flows or traditional moat; sits out rather than betting against a multi-cycle, now institutionally-adopted asset.
  Dalio (Cycle):           BULLISH — four straight weeks of rising net liquidity is a real tailwind, tempered by a firming dollar and a later-than-usual point in the halving cycle.
  Druckenmiller (Trend):   BEARISH — the death cross is still active and price remains meaningfully below its 200-day average; short-term momentum isn't enough yet to call the downtrend broken.
  Alden (Debasement):      BULLISH — balance-sheet growth, Treasury cash draining, and accelerating money supply are a classic debasement tailwind for a hard-capped scarce asset.
  Burniske (On-chain):     NEUTRAL — this lens targets protocol fee/revenue accrual, which doesn't exist for the base monetary asset; largely inapplicable to BTC.

Bull: Every liquidity gauge (balance sheet, Treasury cash, reverse repo, money supply) is pointing up while on-chain valuation is nowhere near cycle-top froth, leaving real room to re-rate higher once the trend confirms.
Bear: The death cross is still active and price sits meaningfully below its 200-day average, so trend-followers should treat the recent bounce as unconfirmed until that long-term line is reclaimed.

quorum_verdict=SPLIT (HIGH-conviction CORE dissent: Alden BULLISH-HIGH vs Druckenmiller BEARISH-HIGH; +4 numeric lean capped by the rule) | dominant_zone=FAIR_VALUE (+5.3% vs 200wMA, 210 weekly closes) | seats_bull=2 seats_bear=1 | signal=HOLD
critic_note=FLAG — golden-cross nuance + missing institutional/geopolitical context added; does not change signal (Q1 DIRECTION assessed as consistent with HOLD)
citation_note=⚠️ CITATION_FAILED (Step 5) — 2 of 4 BTC-specific sources failed re-verification: the JPMorgan/stocktwits citation stated the opposite of its source, and the Coindesk daybook citation attributed a BlackRock/Bitcoin-ETF claim the article does not contain. Both corrected in-place in the narrative above; the T-bill liquidity-risk portion of the Coindesk citation and the Morgan Stanley/E*Trade claim (re-attributed to the correct decrypt.co source) stand VERIFIED. HOLD signal unaffected — no source removal changes the underlying decision-table inputs.

---

### ETH — BUY ⚠️ REVISED (Verdict Critic FLAG — see below)

ETH is bouncing off a statistically deep discount (-22.1% below its 200-week MA) with short-term momentum turning up (RSI 64.6, rising MACD histogram), but the 50/200-day death cross is still active and price remains under the 200-day SMA, so the larger trend hasn't confirmed a reversal yet. Expanding Fed net liquidity (drained reverse repo, falling Treasury cash balance, accelerating M2) is a real debasement tailwind. **Critic correction:** live chain revenue is actually fetchable and is thin — $51,637/24h (≈$18.9M annualized) against a ~$233B market cap, a roughly 12,300x revenue multiple [source: https://defillama.com/chain/ethereum] — this weakens rather than confirms the fee-burn value-accrual case, and a "bear_weight=0" framing understates real risk given the concurrent active death cross. The critic also flagged that Bitmine now holds 4.8% of total ETH supply (5.78M ETH) while simultaneously buying back its own shares under a $4B program [source: https://www.theblock.co/post/408913/bitmine-expands-ethereum-treasury-5-78-million-eth-repurchases-5-5-million-shares] — a NAV-discount signal (the market prefers buying Bitmine's own stock over ETH-proxy exposure) that compounds the Cambridge node-concentration risk already on file. This does not flip the call (DEEP_VALUE zone and weekly_closes≥200 still support BUY under the decision table), but the "zero dissent" framing is corrected: real, if non-CORE, bear considerations exist. Main risk: unresolved network scaling/finality questions flagged by Vitalik's own team [source: https://www.newsbtc.com/news/vitalik-buterin-s-single-slot-finality-plan-shows-ethereum-still-has-a/]; a separate ETF-outflow headline could not be verified to a specific dollar figure or source URL this run and is disclosed as unconfirmed rather than cited. Watch for a weekly close back above the SMA200 ($2,173.51) to confirm the reversal, or a break below the SMA50 ($1,732.80) to invalidate the bounce.

Research Desk:
  Technical:   Price ($1,931.01) is above EMA20/SMA50 but below SMA200 with an active death cross and -22.1% below the 200wMA, while RSI (64.6) and rising MACD histogram (+13.62) show short-term bullish momentum building.
  On-Chain:    [UNAVAILABLE — no live MVRV-Z/NUPL/Puell equivalent source for ETH this run; the only live on-chain source (bitcoin-data.com) covers BTC exclusively]
  DeFi:        ETH's EIP-1559 base-fee burn is a real value-accrual mechanism; live chain revenue is $51,637/24h (≈$18.9M annualized) [source: https://defillama.com/chain/ethereum, verified by Verdict Critic] — a thin, ~12,300x-revenue-multiple accrual relative to market cap, weakening rather than confirming the fee-burn bull case.
  Macro:       Fed net liquidity is expanding ($5.82T→$5.99T over 3 weeks) [source: FRED WALCL/RRPONTSYD/WTREGEN series] with RRP drained and TGA releasing — a tailwind — though a headline separately alleged ETF outflows for ETH; no verifiable article URL or dollar figure could be confirmed this run [UNAVAILABLE].
  Smart Money: OKX ETH perpetual funding is essentially flat (+0.0000080) [source: https://www.okx.com/api/v5/public/funding-rate], showing no meaningful leverage skew from longs or shorts.

Panel:
  Graham (Value):          HOLD — no intrinsic-value anchor (earnings/book value) to underwrite a margin of safety; -22.1% discount to 200wMA is suggestive but not decision-grade for this framework.
  Buffett (Quality):       HOLD — real ecosystem moat, but Cambridge node-concentration research and Vitalik's own unresolved finality roadmap raise durability questions [source: https://www.theblock.co/post/407909/cambridge-research-puts-ethereum-node-activity-in-us-where-third-offline-can-stall-finalization].
  Dalio (Cycle):           BUY — expanding net liquidity, drained RRP, draining TGA, and accelerating M2 form a classic expansionary backdrop favoring risk assets.
  Druckenmiller (Trend):   HOLD — short-term trend has turned up but the death cross is still live and price is under SMA200; waiting for confirmation before adding size.
  Alden (Debasement):      BUY — debasement backdrop (Fed balance sheet growth, M2 acceleration) supports scarce digital assets, and ETH's fee-burn adds a quasi-deflationary supply mechanic, though ETH remains secondary to BTC in this framework.
  Burniske (On-chain):     HOLD — the EIP-1559 fee-burn is the right value-accrual lens for ETH, but with no live-verified chain-revenue data this run, conviction can't be upgraded past neutral.

Bull: Expanding Fed net liquidity, accelerating M2, a drained reverse repo, and ETH's genuine EIP-1559 fee-burn mechanism support a bounce from a statistically deep 200wMA discount, with Tom Lee flagging current levels as "interesting" for a possible bottom [source: https://stocktwits.com/news-articles/markets/cryptocurrency/ethereum-bottom-in-sight-tom-lee-shares-interesting-chart-to-recovery/cZmYE2eR7ns].
Bear: The 50/200-day death cross remains active with price still under the 200-day SMA, Ethereum's own core team flags unresolved finality/scaling risk [source: https://www.newsbtc.com/news/vitalik-buterin-s-single-slot-finality-plan-shows-ethereum-still-has-a/], live chain revenue is thin (~12,300x multiple) not confirming strong fee-burn accrual [source: https://defillama.com/chain/ethereum], Bitmine's own-share buyback over adding ETH is a NAV-discount signal [source: https://www.theblock.co/post/408913/bitmine-expands-ethereum-treasury-5-78-million-eth-repurchases-5-5-million-shares], and an alleged ETF-outflow headline remains unverified this run [UNAVAILABLE].

quorum_verdict=BULLISH (bull_weight=10, bear_weight=0 as scored by the panel; Verdict Critic FLAGGED this as understating real bear considerations — thin chain revenue and a Bitmine NAV-discount signal exist, though neither rises to a CORE-seat dissent) | dominant_zone=DEEP_VALUE (-22.1% vs 200wMA, 210 weekly closes) | seats_bull=2 seats_bear=0 | signal=BUY
critic_note=FLAG — "not re-verified" DeFi framing corrected to a real, thin $51,637/24h figure; bear_weight=0 softened with disclosed non-CORE risks. Signal unchanged: BULLISH+DEEP_VALUE+weekly≥200 still maps to BUY per the decision table.

---

### SOL — BUY ⚠️ REVISED (Verdict Critic FLAG — see below)

SOL is trading about 28% below its 4-year (200-week) average price, a discount large enough to clear this framework's full-size buy bar once the panel is weighted by conviction rather than headcount. The macro backdrop (Fed balance sheet growing, cash reserves draining into markets, M2 accelerating) is a tailwind for risk assets generally, and two of the three core lenses for an L1 (macro cycle, debasement) back the trade at moderate conviction. **Critic correction:** Solana chain-level DeFiLlama data is actually fetchable and was wrongly marked UNAVAILABLE this run — it shows 7-day DEX volume down -13.64% WoW ($10.316B, from $523,745/24h in chain fees) [source: https://defillama.com/chain/solana] — a real, if incremental, bearish ecosystem-activity signal that reinforces (not reverses) the already-disclosed death-cross/negative-MACD dissent. The critic also flagged that Fed Chair Warsh explicitly ruled out any crypto-specific backstop ("We do not want to be in the bailout business, full stop... including crypto") on July 14 [source: https://bitcoinmagazine.com/news/fed-chair-warsh-no-bailout-for-crypto], which tempers (without negating) the generic Fed-liquidity tailwind argument. The main dissent remains the trend lens: an active "death cross" and still-slightly-negative momentum — a real, disclosed risk, but only moderate conviction, not high enough under this framework's rule to force a smaller position. On the positive side, Morgan Stanley just added Solana trading via E*Trade [source: https://decrypt.co/373681/morgan-stanley-launches-bitcoin-ethereum-solana-trading-etrade] and Jito launched a new self-custodial trading platform for Solana tokens [source: https://www.theblock.co/post/409040/jito-rolls-out-jtx-self-custodial-trading-platform-for-solana-tokens-and-rwas], both signs of real institutional plumbing being built. Watch for a close back above the 200-day SMA (~$89.61) to confirm the trend has turned, or a break below the 50-day SMA (~$73.27), which would argue for cutting the position.

Research Desk:
  Technical:   Price ($78.08) is above EMA20/SMA50 but in an active death cross vs SMA200 ($89.61) and 27.6% below the 200wMA ($107.79); RSI neutral (54.89), MACD histogram slightly negative (-0.17).
  On-Chain:    [UNAVAILABLE — no live on-chain valuation source for SOL this run; the only live on-chain source (bitcoin-data.com) covers BTC exclusively]
  DeFi:        Chain-level Solana DeFiLlama data IS fetchable (corrected by Verdict Critic, previously mismarked UNAVAILABLE): 24h DEX volume $1.687B, 7d volume $10.316B (down -13.64% WoW), 24h chain fees $523,745, bridged TVL $30.533B [source: https://defillama.com/chain/solana].
  Macro:       Fed balance sheet and M2 expanding, TGA draining, RRP near zero, net liquidity proxy up $5.82T→$5.99T — a tailwind partly offset by a firming DXY; Fed Chair Warsh explicitly ruled out any crypto-specific backstop on July 14 ("full stop... including crypto") [source: https://bitcoinmagazine.com/news/fed-chair-warsh-no-bailout-for-crypto, added by Verdict Critic], tempering the generic liquidity-tailwind read.
  Smart Money: OKX perpetual funding mildly positive (+0.0000460) [source: https://www.okx.com/api/v5/public/funding-rate] — slight long-leaning leverage bias, not extreme.

Panel:
  Graham (Value):          HOLD — no earnings/FCF anchor exists for an L1 token; -27.6% vs 200wMA is suggestive but not a true margin-of-safety metric.
  Buffett (Quality):       HOLD — no quality/earnings metric applies, but institutional distribution (Morgan Stanley/E*Trade, Jito JTX) is a tentative moat signal.
  Dalio (Cycle):           BUY — expanding net liquidity, draining TGA, accelerating M2 = liquidity-cycle tailwind for risk assets.
  Druckenmiller (Trend):   AVOID (MED conviction) — active death cross + negative MACD histogram = broken long-term trend; short-term bounce insufficient to re-engage.
  Alden (Debasement):      BUY — debasement backdrop supports scarce assets broadly, but SOL's ongoing issuance is a weaker "hard money" case than BTC, capping conviction at MED.
  Burniske (On-chain):     NEUTRAL — no live TVL/fee data this run; Jito JTX shows real activity but not enough to drive a valuation call.

Bull: Deeply discounted vs the 200wMA (-27.6%) inside an expanding-liquidity macro backdrop, plus real institutional distribution momentum (Morgan Stanley/E*Trade, Jito JTX).
Bear: The death cross is active and MACD histogram is still negative — the trend lens dissents at moderate conviction — and Fear & Greed at 25 plus a "record bearish sentiment" headline [source: https://coinmarketcap.com/community/articles/6a51289b73c24151361ad41f] show the crowd already nervous, raising downside-continuation risk below the $73 SMA50. Verdict Critic add: 7d Solana DEX volume is down -13.64% WoW [source: https://defillama.com/chain/solana], a real (if incremental) ecosystem-activity confirmation of the same caution.

quorum_verdict=BULLISH (bull_weight=8, bear_weight=4; CORE trend dissent is MED not HIGH conviction, so per SKILL.md rule it does not cap the verdict at SPLIT — corrected from the research pass's initial SPLIT-leaning "BUY(small)" draft) | dominant_zone=DEEP_VALUE (-27.6% vs 200wMA, 210 weekly closes) | seats_bull=2 seats_bear=1 | signal=BUY
critic_note=FLAG — DeFi pillar wrongly marked UNAVAILABLE (now corrected: -13.64% WoW DEX volume); Fed liquidity framing tempered by Warsh no-bailout remark. Both reinforce the already-counted trend dissent at MED conviction; signal unchanged (BULLISH+DEEP_VALUE+weekly≥200 = BUY).

---

### TON — HOLD ⚠️ REVISED (Verdict Critic FLAG — see below)

TON is down about 34% from a long-term reference average, but that reference is built from only ~76 weeks of price history (roughly a year and a half), so the usual 4-year-cycle comparison isn't statistically reliable yet — treat "deep discount" as suggestive, not proven. Momentum is soft: price sits below its short- and medium-term moving averages with a mildly negative MACD reading, though no death cross has formed. **Critic correction:** Pavel Durov's arrest was 24 August 2024 — roughly 23 months ago, not "5 days" as the original NewsBTC-sourced framing implied; he has been permitted to leave France since March 2025, and for up to two weeks at a time since July 2025 [source: https://en.wikipedia.org/wiki/Arrest_and_indictment_of_Pavel_Durov] — a de-escalating, stale overhang, not a fresh one. The critic also found DeFiLlama TON chain data IS fetchable (previously mismarked UNAVAILABLE): TVL is a thin $66.3M [source: https://defillama.com/chain/ton] — itself a mild bear signal for a network with TON's market cap, showing weak DeFi usage, not a data gap. Separately, a real and current negative was omitted: a 6-hour TON network outage on 2026-07-15 that required validator restarts [source: https://www.theblock.co/post/313367/ton-blockchain-now-down-six-hours]. None of this changes the HOLD call — the weekly_closes=76<200 gate caps the signal at HOLD regardless of verdict direction — but the underlying risk picture is corrected: less "arrest overhang," more "thin DeFi usage + a recent outage." Watch for a reclaim of the $1.63 SMA50 level to confirm a real trend turn, and watch for a longer track record (200+ weekly closes) before treating any TON discount as buyable.

Research Desk:
  Technical:   Price ($1.544) sits below EMA20/SMA50/SMA200 with soft RSI and negative MACD momentum, and the "200-week MA" is actually only a 76-week substitute (~1.5 years of data), not a valid long-term average.
  On-Chain:    [UNAVAILABLE — no live on-chain valuation source for TON this run]
  DeFi:        DeFiLlama TON chain data IS fetchable (corrected by Verdict Critic, previously mismarked UNAVAILABLE): TVL is a thin $66.3M as of 2026-07-21 [source: https://defillama.com/chain/ton] — weak DeFi usage relative to TON's market cap, itself a mild bear signal rather than a pure data gap.
  Macro:       Fed balance-sheet expansion, RRP/TGA draining, and accelerating M2 (4.72%→5.58%) form a net liquidity tailwind for risk assets, only mildly offset by a firming DXY.
  Smart Money: [UNAVAILABLE — OKX has no TON-USDT-SWAP perpetual instrument this run]

Panel:
  Graham (Value):          AVOID — no earnings/cash-flow/book-value basis exists; a discount to a thin reference average isn't a margin of safety.
  Buffett (Quality):       AVOID — Telegram distribution is a real moat, but Pavel Durov's ~23-month-old arrest [source: https://en.wikipedia.org/wiki/Arrest_and_indictment_of_Pavel_Durov, corrected by Verdict Critic — he has had travel freedom since Mar/Jul 2025] is a de-escalating, not fresh, key-person risk; a 6-hour TON network outage on 2026-07-15 [source: https://www.theblock.co/post/313367/ton-blockchain-now-down-six-hours] is the more current governance/reliability concern.
  Dalio (Cycle):           BUY (small) — Fed/M2 liquidity backdrop favors risk assets broadly; TON benefits as beta, not on TON-specific strength.
  Druckenmiller (Trend):   HOLD — price below all near-term MAs with negative MACD; no confirmed trend to press, though no breakdown either (CORE dissent, moderate conviction).
  Alden (Debasement):      HOLD / small BUY — macro debasement tailwind is real, but TON isn't a hard-capped, BTC-grade scarce asset, and the regulatory cloud weakens the "sound money" case further.
  Burniske (On-chain):     N/A (half-weight, abstains) — no TVL/fee/protocol-revenue data available this run to apply the value-accrual framework.

Bull: Book-wide liquidity tailwind (Fed BS/M2 acceleration) plus a deep (if statistically unproven) discount and Fear-zone sentiment could reward a small starter position if the regulatory cloud clears.
Bear: A 6-hour TON network outage on 2026-07-15 [source: https://www.theblock.co/post/313367/ton-blockchain-now-down-six-hours], thin $66.3M DeFi TVL relative to network size [source: https://defillama.com/chain/ton], soft below-all-MAs momentum, and no live smart-money data (2 of 5 research pillars still dark this run) argue for staying on the sidelines until the picture clears. The Durov-arrest overhang cited in earlier drafts is stale (~23 months old, de-escalating) and has been corrected out of the current bear case.

quorum_verdict=UNCERTAIN (2 of 5 Research Desk pillars — On-Chain, Smart Money — are [UNAVAILABLE] this run; DeFi corrected from UNAVAILABLE to a thin, verified $66.3M TVL by the Verdict Critic; per SKILL.md "key briefs are thin/UNAVAILABLE; do not manufacture a verdict," this remains UNCERTAIN given the still-thin data picture, not a genuine two-sided disagreement) | dominant_zone=DEEP_VALUE (unconfirmed — 76 weekly closes, below the 200 needed for a valid read) | seats_bull=2 seats_bear=2 | signal=HOLD (weekly_closes=76 <200, gate fails regardless of verdict)
critic_note=FLAG — Durov "5 days" framing was off by ~23 months (corrected); DeFi pillar wrongly marked UNAVAILABLE (corrected to $66.3M TVL); a 2026-07-15 six-hour outage was omitted (now added). Signal unchanged: weekly_closes=76<200 gate locks HOLD regardless of verdict label.

---

### HYPE — BUY (small) ⚠️ REVISED (Verdict Critic FLAG — see below)

Hyperliquid's HYPE token is backed by a real, live, and fast-growing business: the exchange generated $41.25M in revenue over the last 30 days and $1.17B all-time, with fees automatically funneled into a confirmed token buyback [source: https://defillama.com/protocol/hyperliquid] — DeFiLlama's live fees API confirms these figures almost to the dollar, so the mechanism check passes. That's rare — most crypto tokens have no real cash flow behind them at all. **Critic correction:** framing the price pullback as tied to "a broader market rout" is misleading — total crypto market cap stayed roughly flat the same week HYPE fell 8-10%, making HYPE the top-10 laggard of the week, i.e. idiosyncratic weakness, not market beta [source: https://beincrypto.com/hype-etf-first-weekly-outflow/]. The critic also flagged that a "bull_weight=13, bear_weight=0" framing is not fully credible given the verdict's own cited risks: the tracked whale's Hyperliquid book has grown to $5.38B (not shrinking), HYPE ETF net assets fell ~12.7% for the week (price + outflow combined, a bigger signal than the bare outflow dollar figure), Glassnode has not confirmed any on-chain reversal, and Fear & Greed sits at 25. None of this changes the BUY(small) call — the mechanism (revenue + buyback) is real and confirmed, and the signal is already capped at "small" by the 38-week (<200) history gate regardless of verdict strength — but the "zero bear weight" framing is corrected to acknowledge real, disclosed risk. A large trader on the platform has also been unwinding a leveraged ETH short, withdrawing 7,863 ETH [source: https://www.binance.com/en/square/post/343067222325858]. Important caveat: HYPE is still a young token with only about 38 weeks of price history, so there's no multi-year average to measure it against yet — any "cheap vs. its own history" claim can't honestly be made for this one, which is why the signal is capped at a small position rather than a full buy.

Research Desk:
  Technical:   Price ($61.63) is pulling back below its 20/50-day averages with negative MACD momentum (RSI 44), but stays ~40% above its 200-day SMA with no death cross; only 38 weeks of history exist, so no 200-week MA or long-term comparison is available.
  On-Chain:    [UNAVAILABLE — no live on-chain valuation source for HYPE this run]
  DeFi:        $6.36B TVL with $41.25M in 30-day revenue ($1.17B all-time) flowing through a confirmed live token-buyback mechanism [source: https://defillama.com/protocol/hyperliquid].
  Macro:       Net liquidity tailwind (Fed balance sheet +$114B/19wks, TGA -$162B/3wks, M2 accelerating) tempered by a mildly firming DXY and this week's first HYPE ETF outflow since May.
  Smart Money: OKX perpetual funding is mildly positive (+0.00008) [source: https://www.okx.com/api/v5/public/funding-rate]; a large platform trader withdrew 7,863 ETH amid a suspected sell-off and holds $5.38B in whale positions with an $11.1M unrealized loss on an ETH short [source: https://www.binance.com/en/square/post/343067222325858, https://www.binance.com/en/square/post/345197985045361].

Panel:
  Graham (Value):          BUY (weak, MED) — real, large revenue with a confirmed buyback is genuine margin-of-safety material, but no market cap/supply data this run means a P/S cushion can't be quantified.
  Buffett (Quality):       BUY — a toll-booth business earning fees on every trade regardless of direction, backed by $6.36B TVL, though still young (38 weeks) in a contested perp-DEX space.
  Dalio (Cycle):           HOLD — the liquidity backdrop is a supportive tailwind 6-12mo out, but Fear & Greed at 25 and this week's rout say we're mid-drawdown now, not at a confirmed low.
  Druckenmiller (Trend):   HOLD — near-term trend is soft (below EMA20/SMA50, negative MACD) but the longer 200-day uptrend is intact; wait for a reclaim of $64-65 before adding.
  Alden (Debasement):      BUY (weak/small, LOW) — real cash flow plus a live buyback clears the BTC-hurdle qualitatively, since BTC itself has none, but the short track record means sizing small versus a BTC core position.
  Burniske (On-chain):     BUY (HIGH) — one of DeFi's cleanest fee-capture-to-token-holder setups, with $41.25M/30d revenue and a live-confirmed buyback, intact regardless of this week's price pullback.

Bull: Real, large, live-verified revenue and an automatic buyback give HYPE a genuine cash-flow-backed thesis most tokens lack, and the token remains ~40% above its 200-day trend despite the near-term dip.
Bear: Only 38 weeks of history means no long-term valuation anchor exists yet; near-term momentum is negative, driven by idiosyncratic HYPE-specific weakness (not broad market beta — total crypto market cap stayed roughly flat the same week HYPE fell 8-10% [source: https://beincrypto.com/hype-etf-first-weekly-outflow/, added by Verdict Critic]); the tracked whale's book grew to $5.38B (not shrinking), HYPE ETF net assets fell ~12.7% for the week, Glassnode has not confirmed an on-chain reversal, and Fear & Greed sits at 25 — real, current risks that a "bear_weight=0" framing understated.

quorum_verdict=BULLISH (bull_weight=13, bear_weight=0 as scored by the panel; Verdict Critic FLAGGED this as overconfident given idiosyncratic underperformance, a growing whale position, and unconfirmed on-chain reversal — none rise to a CORE-seat dissent) | dominant_zone=FAIR_VALUE (qualitative — no 200wMA anchor available, only 38 weekly closes) | seats_bull=4 seats_bear=0 | signal=BUY (small) (weekly_closes=38 <200, gate caps size regardless of verdict strength)
critic_note=FLAG — "market rout" framing corrected to idiosyncratic underperformance; bear_weight=0 softened with disclosed non-CORE risks. Signal unchanged: gate already caps at BUY (small) regardless of verdict strength.

---

### AAVE — BUY (small) ⚠️ REVISED — Verdict Critic FLAG changed the signal from BUY to BUY (small)

Aave is DeFi's biggest lending protocol ($14.64B TVL) and it actually pays real cash to token holders — $3.85M in revenue over the last 30 days, $302M all-time, funneled through a confirmed live buyback [source: https://defillama.com/protocol/aave] — the mechanism check passes and is current, not stale. **Critic correction (material):** the "single token holder proposed a poison pill" framing badly understates the governance risk. The Dec 2025 poison-pill proposal was followed by the sequential departure of three core Aave contributors — BGD Labs, the Aave Chan Initiative (Marc Zeller), and Chaos Labs, the DAO's risk manager since 2022 — all over the same unresolved Aave Labs/DAO revenue-and-risk-management dispute [source: https://www.theblock.co/post/396458/top-aave-risk-manager-chaos-labs-exits-amid-governance-dispute]. Zeller has since publicly stated he sold his AAVE holdings after leaving. This is a genuine, still-unresolved execution/governance risk — not a stale or single-actor event — that a pure price-and-cash-flow read misses; it directly threatens the quality/durability of the business a value-and-moat framework should weigh. Because this constitutes real, current dissent that the original "core_dissent=NONE" call did not capture, the signal is downgraded from a full-size entry to a small starter position: cash-flow fundamentals remain genuinely strong, but governance/execution risk is real enough to caution against full sizing until the contributor situation stabilizes. Watch: whether more contributors depart or the dispute settles, whether the death cross (SMA50 $81 vs SMA200 $106) gets reclaimed, and whether the currently negative funding rate (crowded shorts) flips or triggers a squeeze.

Research Desk:
  Technical:   Price ($96.03) is bouncing above its EMA20/SMA50 but still sits below the SMA200 ($106.30) under an active death cross, with MACD momentum cooling (-0.7159 histogram).
  On-Chain:    [UNAVAILABLE — no live on-chain valuation source for AAVE this run]
  DeFi:        $14.64B TVL and $3.85M in 30-day revenue ($302M all-time) flow through a confirmed live token-buyback mechanism [source: https://defillama.com/protocol/aave]; V4 has expanded to Avalanche [source: https://cointelegraph.com/news/aave-brings-v4-to-avalanche-laying-groundwork-for-tokenized-asset-lending] with founder commentary on RWA growth [source: https://www.theblock.co/post/408366/stani-kulechov-on-aave-v4-avalanche-and-why-rwas-will-hit-100-billion-this-year]. Verdict Critic addition: BGD Labs, the Aave Chan Initiative (Marc Zeller), and Chaos Labs (risk manager since 2022) have all departed over an unresolved Aave Labs/DAO revenue-split dispute, and Zeller has publicly stated he sold his AAVE holdings [source: https://www.theblock.co/post/396458/top-aave-risk-manager-chaos-labs-exits-amid-governance-dispute] — a real, current governance/execution risk, not the single-proposal framing originally reported.
  Macro:       Net liquidity tailwind (Fed balance sheet +$114B/19wks, TGA -$162B/3wks, M2 accelerating) partially offset by a mildly firming DXY.
  Smart Money: OKX perpetual funding is -0.0001189 [source: https://www.okx.com/api/v5/public/funding-rate], the most negative of all 11 tokens screened, showing a notably bearish leveraged-positioning skew.

Panel:
  Graham (Value):          BUY — real $3.85M/30d, $302M all-time revenue with a confirmed buyback, plus a 30% discount to trend, is a genuine margin of safety.
  Buffett (Quality):       HOLD → AVOID-leaning (Verdict Critic revision) — the moat (largest lending protocol, V4/Avalanche expansion) is real, but the confirmed departure of THREE core contributors (BGD Labs, Aave Chan Initiative, Chaos Labs — the DAO's own risk manager) over an unresolved revenue dispute, plus Zeller's public confirmation he sold his AAVE, is a material, current crack in the business-quality story, not a live-but-contained single proposal.
  Dalio (Cycle):           HOLD — macro liquidity is supportive, but the daily death cross is still active and unconfirmed as reversed.
  Druckenmiller (Trend):   AVOID — price still under SMA200 with cooling momentum and the most crowded-short funding rate in the book; no trend worth chasing.
  Alden (Debasement):      AVOID — against a liquidity tailwind that lifts BTC too, AAVE doesn't clear the BTC hurdle while governance risk over its own revenue is unresolved.
  Burniske (On-chain):     BUY — $14.64B TVL plus a confirmed buyback is textbook value-accrual, though the governance fight directly threatens that mechanism and must be watched.

Bull: $14.64B TVL, $302M all-time revenue and a confirmed buyback funding a 30%-below-trend entry make this one of the few DeFi tokens with real, current cash-flow backing.
Bear: An active death cross, the book's most negative funding rate, and — per Verdict Critic correction — a confirmed multi-contributor exodus (BGD Labs, Aave Chan Initiative/Zeller, Chaos Labs) over an unresolved DAO/Aave-Labs revenue-split dispute, with Zeller publicly confirming he sold his AAVE holdings [source: https://www.theblock.co/post/396458/top-aave-risk-manager-chaos-labs-exits-amid-governance-dispute], are real, current, structural risks — not a single contained proposal as originally framed.

quorum_verdict=SPLIT (bull_weight=4, bear_weight=2 as originally scored, but Verdict Critic surfaced a genuine CORE-relevant dissent — Buffett's quality/moat lens is directly undermined by a confirmed 3-contributor exodus including the DAO's own risk manager and public insider selling, which the original "core_dissent=NONE" call missed; this is a real disagreement between the value/cash-flow case and the quality/execution-risk case, not a mechanical rule error) | dominant_zone=DEEP_VALUE (-30.0% vs 200wMA, 210 weekly closes) | seats_bull=2 seats_bear=2 | signal=BUY (small) (revised from BUY: SPLIT + DEEP_VALUE + bull-leaning weight maps to BUY (small) per the decision table's second path)
critic_note=FLAG — MATERIAL: contributor exodus (BGD Labs, ACI/Zeller, Chaos Labs) + insider selling was previously downplayed as a single "poison pill" proposal. This constitutes real, current CORE-relevant dissent → signal downgraded BUY → BUY (small).

---

### JUP — HOLD ⚠️ REVISED — Verdict Critic FLAG changed the signal from BUY (small) to HOLD

JUP is Jupiter, Solana's dominant swap-routing app — its $0 TVL on DeFiLlama just means it doesn't lock up user deposits like a lending market or AMM would; it's a router, so that number is structurally near-zero and is not a red flag by itself [source: https://defillama.com/protocol/jupiter-aggregator]. Underneath that $0, the business generated a real $40,909 in fees in the last 24h and $2.52M over 30 days, with confirmed token-holder buybacks funded by that revenue [source: https://api.llama.fi/summary/fees/jupiter-aggregator?dataType=dailyRevenue] — the mechanism check is live and current. **Critic correction (material):** the exact "buyback + supply fix" catalyst narrative used to justify the bull lean already fired once this cycle and failed — JUP popped +8% on 2026-06-24 on this narrative [source: https://coinmarketcap.com/community/articles/6a3bcc9e2b91f8497edc3032/], then reversed within days, with JUP underperforming rival Hyperliquid by 2026-06-27. The critic also flagged that JUP's token-supply/unlock schedule is never sized anywhere in the verdict, and a $2.52M/30d buyback is trivial against JUP's circulating/FDV supply. Since the thin bull lean (bull_weight=3 vs bear_weight=2) that qualified this for the decision table's "SPLIT + DEEP_VALUE + bull-leaning" BUY(small) path rested substantially on this now-shown-to-have-failed catalyst, the lean is downgraded to neutral and the signal reverts to HOLD. Price is 66.9% below its long-run weekly average, but that average is built on only 130 weeks of data (not a true 200-week MA), so the discount is directionally real but not fully calibrated. Watch for a reclaim of the $0.206 EMA20 / $0.201 SMA50, evidence the buyback catalyst is holding for more than a few days this time, and unlock-schedule sizing before reconsidering a starter position.

Research Desk:
  Technical:   Price sits below EMA20/SMA50 but above the daily SMA200 (no death cross), RSI neutral (43.83), MACD mildly negative; the -66.9% discount is vs. only 130 weekly bars, not a genuine 200-week MA.
  On-Chain:    [UNAVAILABLE — no live on-chain valuation source for JUP this run]
  DeFi:        $0 TVL is a genuine aggregator-model outcome (Jupiter doesn't hold deposits, it routes through other protocols' liquidity), not a data failure; real revenue ($40,909/24h, $2.52M/30d, $109.1M all-time) flows to a confirmed token-holder buyback [source: https://defillama.com/protocol/jupiter-aggregator]. Verdict Critic addition: this exact buyback narrative already drove an 8% pop on 2026-06-24 [source: https://coinmarketcap.com/community/articles/6a3bcc9e2b91f8497edc3032/] that reversed within days as JUP underperformed Hyperliquid by 2026-06-27 — a previously-failed catalyst, not fresh confirmation; unlock/supply dynamics are not sized against the buyback anywhere in this run.
  Macro:       Net liquidity tailwind (Fed balance sheet expanding, RRP/TGA draining, M2 accelerating) partly offset by a mildly firming DXY.
  Smart Money: OKX funding mildly positive (+0.00005) [source: https://www.okx.com/api/v5/public/funding-rate] — slight long lean, not an extreme skew.

Panel:
  Graham (Value):          HOLD — Real cash flow + confirmed buyback are constructive, but no market cap/circ-supply data this run means no true margin-of-safety multiple can be computed; the discount is price-vs-average, not intrinsic value.
  Buffett (Quality):       HOLD — Dominant aggregator with diversified revenue, but low-switching-cost business model and confirmed relative underperformance vs. Hyperliquid in June pressure the moat.
  Dalio (Cycle):           BUY (small) — Liquidity tailwind + F&G=25 (FEAR) is a historically favorable backdrop, tempered by mild DXY firming.
  Druckenmiller (Trend):   AVOID (short-term) — No momentum edge: below EMA20/SMA50, negative MACD, underperforming HYPE; no trend to ride yet.
  Alden (Debasement):      AVOID (fails BTC-hurdle) — Liquidity tailwind is generic to risk assets, not JUP-specific; BTC captures the debasement thesis more directly. Real cash-flow/buyback differentiator, but not enough alone to beat holding BTC.
  Burniske (On-chain):     BUY (small) — $0 TVL is a red herring for an aggregator; real fee capture ($2.52M/30d, $109.1M all-time) flows to a confirmed buyback. No trend data available to confirm acceleration, so sizing stays small.

Bull: Real, confirmed fee revenue and buyback mechanics plus a steep (if imperfectly benchmarked) price discount and a supportive liquidity backdrop give JUP a legitimate cash-flow-based accumulation case, though this exact catalyst has already failed to hold once this cycle (see critic correction below).
Bear: Thin aggregator-model moat, confirmed relative underperformance vs. Hyperliquid, soft short-term momentum, a failed BTC-hurdle test, and — per Verdict Critic — a buyback narrative that already produced a temporary +8% pop on 2026-06-24 which fully reversed within days mean JUP does not clearly earn a spot over just holding BTC right now.

quorum_verdict=SPLIT (bull_weight=3, bear_weight=2 as originally scored; Verdict Critic FLAGGED the bull-lean's load-bearing catalyst — the buyback narrative — as already tested and failed once this cycle (2026-06-24 pop fully reversed by 2026-06-27), which neutralizes the thin 3-vs-2 lean rather than confirming it) | dominant_zone=DEEP_VALUE (caveated — 130 weekly closes, below the 200 needed for a valid read) | seats_bull=2 seats_bear=2 | signal=HOLD (revised from BUY (small): with the bull-lean neutralized, SPLIT + DEEP_VALUE without a defensible bull lean does not qualify for the decision table's BUY(small) path, so it defaults to HOLD)
critic_note=FLAG — MATERIAL: the buyback/supply-fix catalyst justifying the bull lean already fired and reversed once (2026-06-24 to 2026-06-27); unlock schedule never sized. Signal downgraded BUY (small) → HOLD.

---

### UNI — BUY ⚠️ REVISED (Verdict Critic FLAG — see below)

Uniswap's tokenholder fee switch is now confirmed live — the protocol is actually burning UNI and paying real fees to holders for the first time in its history [source: https://www.binance.com/en/square/post/344010882116209], on top of $3.12B in TVL and near-total (99.5%) DEX market share [source: https://www.binance.com/en/square/post/343747869147121]. Price has already climbed back above both its 50-day and 200-day averages even though a lagging "death cross" indicator hasn't caught up yet — that's a stale signal, not evidence the token is still falling. **Critic correction:** the "$5.2M/day vs $147,263/24h, unreconciled" framing overstated the mystery. DeFiLlama's own gross Fees metric is actually $3.84M/24h [source: https://defillama.com/protocol/uniswap] — the same order of magnitude as founder Hayden Adams' $5.2M claim — and the much smaller $147,263 figure is specifically "Token Holder Net Income," which is low because Uniswap V4 pools currently pay UNI holders $0 by DeFiLlama's own published methodology ("No revenue for UNI holders"). The real, still-open near-term risk the critic surfaced: a governance vote on routing V4/Robinhood-Chain fees into the burn closes 2026-07-26 — five days after this report — so the "burn poised to grow" thesis is contingent on an outcome not yet decided, and a "UNI Surges 35%" headline shows part of this move may have already happened on the announcement of the vote, not its result [source: https://www.theblock.co/post/408836/uni-burn-poised-to-grow-as-uniswap-governance-votes-on-v4-fees-and-robinhood-chain-expansion]. This doesn't reverse the call (DEEP_VALUE zone and weekly_closes≥200 still support BUY), but treat the burn-growth catalyst as conditional on the July 26 vote, not settled. Watch for: the vote outcome on July 26, the 30-60 day fee run-rate holding up, and whether price can hold above the $3.63 (200-day) level.

Research Desk:
  Technical:   Price ($3.674) is above both the 50-day ($3.059) and 200-day ($3.6282) averages despite a still-active but lagging death-cross flag, with RSI 64.94 firm and MACD histogram just turning positive — a recovering trend, not a still-falling one.
  On-Chain:    [UNAVAILABLE — no live on-chain valuation source for UNI this run]
  DeFi:        TVL $3.12B and a newly-live tokenholder fee switch ($147,263/24h, $3.72M/30d confirmed by DeFiLlama) [source: https://defillama.com/protocol/uniswap] mark real cash-flow accrual. Verdict Critic correction: this is largely explained, not unreconciled — DeFiLlama's own gross Fees metric is $3.84M/24h, in the same order of magnitude as the founder's $5.2M/day claim [source: https://www.binance.com/en/square/post/343978933786993]; the low $147K figure is the narrower "Token Holder Net Income" metric, which is near-zero specifically because Uniswap V4 pools currently pay $0 to holders per DeFiLlama's own methodology — and V4/Robinhood-Chain fee activation is exactly what's being voted on through 2026-07-26 [source: https://www.theblock.co/post/408836/uni-burn-poised-to-grow-as-uniswap-governance-votes-on-v4-fees-and-robinhood-chain-expansion].
  Macro:       Same book-wide net liquidity tailwind applies (Fed balance sheet expanding, RRP/TGA draining, M2 accelerating), tempered by a mildly firming DXY.
  Smart Money: OKX perpetual funding is positive (+0.0001) [source: https://www.okx.com/api/v5/public/funding-rate], one of the more notably long-leaning skews among the tokens screened this run, though Fear & Greed (25) shows broader sentiment still runs cold.

Panel:
  Graham (Value):          NEUTRAL — real cash flow finally exists, but the confirmed figure is small relative to market cap and the revenue discrepancy blocks a clean margin-of-safety read; the -46% discount to the 200wMA is the only solid cushion.
  Buffett (Quality):       BULLISH — near-monopoly DEX share plus a live fee switch is the closest thing to a real "business" DeFi produces, but no audited financials keeps conviction low.
  Dalio (Cycle):           NEUTRAL — benefits from the same book-wide liquidity tailwind as everything else, but that's a shared macro read-through, not a UNI-specific edge.
  Druckenmiller (Trend):   BULLISH — price has reclaimed both key averages and momentum is turning up, but the move is young and not yet strongly confirmed.
  Alden (Debasement):      BEARISH — fails the BTC-hurdle test for now: a -46% multi-year discount and a fee-switch catalyst only weeks old haven't yet proven UNI beats simply holding BTC through this liquidity cycle.
  Burniske (On-chain):     BULLISH — the live, confirmed fee switch and burn is the single biggest structural change to UNI's value-accrual story to date, layered on dominant TVL and volume share.

Bull: A live tokenholder fee switch and burn, near-monopoly DEX share, and a price recovery back above both key moving averages make this the strongest fundamental catalyst UNI has had in years.
Bear: The revenue-figure gap is now explained (V4 pools pay $0 to holders by design, not a genuine discrepancy) but the fee-switch growth thesis hinges on a governance vote not resolved until 2026-07-26, part of the recent rally may have already priced in the vote's announcement rather than its outcome [source: https://www.theblock.co/post/408836/uni-burn-poised-to-grow-as-uniswap-governance-votes-on-v4-fees-and-robinhood-chain-expansion], and the golden cross hasn't confirmed on the daily chart.

quorum_verdict=BULLISH (bull_weight=9, bear_weight=2, no CORE-vs-CORE dissent — Graham neutral, not opposed to Burniske) | dominant_zone=DEEP_VALUE (-46.0% vs 200wMA, 210 weekly closes) | seats_bull=3 seats_bear=1 | signal=BUY
critic_note=FLAG — revenue-gap "unreconciled" framing corrected (V4 pools pay $0 to holders by design); pending 2026-07-26 governance vote added as a real, near-term binary risk. Signal unchanged: BULLISH+DEEP_VALUE+weekly≥200 = BUY.

---

### AERO — SELL ⚠️ REVISED (Verdict Critic FLAG — see below)

AERO is trading 36% below its (short, 85-week) historical average, and Aerodrome genuinely distributes real trading-fee and bribe revenue to ve(3,3) stakers [source: https://defillama.com/protocol/aerodrome-v1], with lifetime fees near $500M corroborated independently [source: https://coinmarketcap.com/community/articles/6a401ee09d2d2133c1796c0f]. But combined TVL across its two DeFiLlama listings has fallen to about $305M, confirmed still at that level as of this run [source: https://defillama.com/protocol/aerodrome-v1] — down sharply from an older report of Aerodrome topping $1 billion in deposits [source: https://www.theblock.co/post/319258/aerodrome-tops-1-billion-in-deposits-dominating-defi-on-base] — a real, current decline in protocol scale, not just a cheaper price. **Critic correction:** the governance red flag cited in earlier drafts — two contributors suspended over alleged VVV-launch front-running — dates to 28 January 2025, roughly 18 months ago, and was resolved via suspension at the time [source: https://www.theblock.co/post/337521/two-contributors-suspended-from-venices-vvv-token-launch-on-aerodrome]; it should not be weighted as a live, current risk. The critic also flagged a real, un-weighed positive: Binance listed AERO with a "Seed Tag" on 2026-07-17, four days before this report — though Binance's own Seed Tag explicitly signals "higher risk conditions," making this a two-sided signal (visibility gain, not a clean bullish catalyst), not something to ignore. The core, current, verified bear driver remains the TVL collapse (-70% from the prior $1B+ level to ~$305M today) — this alone, not the stale governance citation, is what keeps this a SELL. Watch for combined TVL to stabilize and reverse before treating this discount as a genuine opportunity rather than a value trap.

Research Desk:
  Technical:   Price ($0.4529) is below EMA20 ($0.4838) but above SMA50 ($0.4582)/SMA200 ($0.4161) with no death cross; RSI neutral-soft (43.37), MACD negative and falling (-0.012); the "200wMA" is really only 85 weeks of data.
  On-Chain:    [UNAVAILABLE — no live on-chain valuation source for AERO this run]
  DeFi:        Combined TVL (aerodrome-v1 + aerodrome-slipstream) ~$305M, 24h fees ~$139.6K, 30d fees ~$4.55M, distributed to stakers via a ve(3,3) model [source: https://defillama.com/protocol/aerodrome-v1] — but down from an older $1B+ TVL headline [source: https://www.theblock.co/post/319258/aerodrome-tops-1-billion-in-deposits-dominating-defi-on-base].
  Macro:       Fed balance sheet, M2, and net liquidity proxy all expanding ($5.82T→$5.99T/3wks) — a tailwind, partly offset by a firming DXY.
  Smart Money: OKX perpetual funding mildly positive (+0.0000361) [source: https://www.okx.com/api/v5/public/funding-rate] — slight long-leaning leverage, not extreme.

Panel:
  Graham (Value):          BUY (small, LOW) — real ve(3,3) fee distribution + steep discount, but LOW conviction given only 85 weeks of history and no FDV to compute a true multiple.
  Buffett (Quality):       AVOID — real moat, but the contributor-suspension/front-running incident (dated 28 Jan 2025, ~18 months old and already resolved via suspension — corrected by Verdict Critic from an earlier "live scandal" framing) plus the TVL collapse itself are the durability concerns; a fresh, un-weighed Binance Seed-Tag listing on 2026-07-17 [source: https://coinmarketcal.com/event/binance-listing-44704192-1] is a two-sided signal (visibility gain, explicit "higher risk" tag), not a clean offset.
  Dalio (Cycle):           HOLD — macro liquidity tailwind is real but not AERO-specific; doesn't offset the protocol's own declining TVL trend.
  Druckenmiller (Trend):   SELL — price back below EMA20, MACD negative and falling; no confirmed uptrend to ride.
  Alden (Debasement):      AVOID — fails the BTC-hurdle test; debasement backdrop favors BTC itself over an altcoin carrying TVL-collapse and governance risk.
  Burniske (On-chain):     SELL (HIGH) — TVL collapse from $1B+ to ~$305M is the dominant on-chain signal, outweighing the still-real fee-accrual mechanism.

Bull: Genuine, corroborated fee revenue (~$500M lifetime) flows directly to ve(3,3) stakers, and the price sits 36% below its historical average, a real discount if the TVL decline stabilizes.
Bear: Combined TVL has collapsed roughly 70% from a prior $1B+ level to ~$305M (confirmed current, not stale) and momentum has turned down. The governance/insider-trading scandal cited in earlier drafts is ~18 months old and already resolved (Verdict Critic correction) — it is downweighted here, not treated as a live risk — but the TVL collapse alone is enough to keep this a SELL rather than a clean discount.

quorum_verdict=BEARISH (bull_weight=2, bear_weight=12; CORE-vs-CORE dissent — Graham LOW-conviction buy vs Burniske HIGH-conviction sell — Burniske's HIGH conviction is the dominant, unrebutted CORE view driving the lean, not a dissent against it; bear_weight driven primarily by the confirmed-current TVL collapse, with the stale governance citation downweighted per Verdict Critic) | dominant_zone=DEEP_VALUE (unconfirmed / value-trap risk — 85 weekly closes, below the 200 needed for a valid read) | seats_bull=1 seats_bear=4 | signal=SELL
critic_note=FLAG — governance-scandal citation was 18 months stale (corrected); a 2026-07-17 Binance Seed-Tag listing was un-weighed (now added as a two-sided signal). Signal unchanged: TVL collapse alone (confirmed current) sustains SELL.

---

### PUMP — HOLD ⚠️ REVISED — Verdict Critic FLAG changed the signal from SELL to HOLD

Pump.fun's buyback engine is real: the platform has generated over $1 billion in all-time fees and pays token holders back through a live, confirmed buyback mechanism [source: https://defillama.com/protocol/pump.fun], and price has bounced hard enough to push RSI to the highest reading of any token in this run. **Critic correction (material):** the load-bearing bear catalyst — a feared 57.3B-token unlock creating "$127-130M in fresh sell pressure" — has already happened and resolved positively, not negatively. The unlock completed 2026-07-15 (6 days before this report) at ~$86.49M realized across 121 wallets, meaningfully below the $127-130M forecast, and PUMP rose +13% the same day and has continued higher since [source: https://99bitcoins.com/news/altcoins/pump-fun-token-vesting-cliff-unlock/]. The market has already absorbed this exact overhang without the feared selloff. Separately, no airdrop was ever officially announced by Pump.fun [source: https://beincrypto.com/pumpfun-airdrop-pump-token-unlock/], so the "airdrop-fueled rally" framing in earlier drafts was an unverified causal claim. With the primary directional bear catalyst falsified by fresh data, the remaining case for caution is narrower: RSI14 at 68.21 (cohort-high) signals a hot, possibly overbought bounce, and the 50/200-day death cross technically remains active even though price has reclaimed the 200-day line. That combination argues for a wait-and-see HOLD — avoid chasing an extended bounce — rather than an active SELL built on a stale, already-resolved dilution narrative. Watch whether buyback pace keeps absorbing supply without a fresh leg down, and whether price holds ~$0.0015 (50-day) support.

Research Desk:
  Technical:   Price $0.00198 is back above the 20/50/200-day averages, but the 50/200 death cross remains active and RSI14 68.21 (cohort-high) signals a hot, possibly overbought bounce with only 54 weeks of history on record.
  On-Chain:    [UNAVAILABLE — no live on-chain valuation source for PUMP this run]
  DeFi:        pump.fun booked $680,735 (24h), $18,727,961 (30d), and $1,063,578,249 (all-time) in fees with a confirmed live token-buyback mechanism [source: https://defillama.com/protocol/pump.fun], while TVL reads N/A by design since a bonding-curve launchpad doesn't hold deposits. Verdict Critic correction: the feared 57.3B-token unlock completed 2026-07-15 at ~$86.49M realized (below the $127-130M forecast) and PUMP rose +13% same day, continuing higher since [source: https://99bitcoins.com/news/altcoins/pump-fun-token-vesting-cliff-unlock/] — the overhang has already been absorbed, not merely pending.
  Macro:       Fed liquidity is expanding as a mild broad tailwind, but PUMP's price action is almost certainly dominated by idiosyncratic unlock/buyback/airdrop narrative factors, not macro conditions.
  Smart Money: OKX funding is mildly positive (+0.00005) [source: https://www.okx.com/api/v5/public/funding-rate] and Fear & Greed reads 25 ("Fear," despite the API's own "Extreme Fear" label) — no crowded positioning signal either way.

Panel:
  Graham (Value):          SELL (HIGH) → NEUTRAL (Verdict Critic revision) — the 57.3B-token unlock already completed 2026-07-15 at a smaller-than-feared ~$86.49M with a positive (+13%) price reaction, not the "$127-130M pressure overwhelms margin of safety" case originally scored; the dilution event is resolved, not pending.
  Buffett (Quality):       NEUTRAL — a genuinely rare real revenue/buyback model for this category, but only 54 weeks old, far too short a track record for durable-moat conviction.
  Dalio (Cycle):           NEUTRAL — macro liquidity tailwind is real, but PUMP's own token-specific cycle is in a distributive (unlock) phase, netting to neutral.
  Druckenmiller (Trend):   NEUTRAL — cohort-high RSI and a reclaimed SMA200 show a real bounce, but the death cross is still active — a directly conflicting signal he wouldn't size into yet.
  Alden (Debasement):      SELL (HIGH) — applying the BTC-hurdle test skeptically, a 54-week-old, TVL-less, unlock-exposed token doesn't clear the bar over just holding BTC.
  Burniske (On-chain):     BUY (MED) — $1.06B all-time fees and a live confirmed buyback is a rare, genuine value-accrual case, tempered by the same unlock diluting the per-token claim.

Bull: pump.fun's live buyback mechanism and $1.06B all-time fee total are a real, rare value-accrual story for a launchpad token, and RSI/price action show genuine near-term momentum; per Verdict Critic, the once-feared unlock has already completed at a smaller-than-forecast size with a positive price reaction, removing the primary bear catalyst.
Bear: RSI14 at 68.21 (cohort-high) signals an overbought bounce, and the 50/200 death cross is still technically active despite price reclaiming the 200-day line — momentum-fade risk remains even though the unlock-driven sell-pressure thesis is now stale.

quorum_verdict=SPLIT (bull_weight=4, bear_weight=9 as originally scored, but Verdict Critic FALSIFIED the load-bearing Graham [CORE, HIGH] SELL rationale — the unlock it was based on has already completed with a smaller-than-forecast size and a positive, not negative, price reaction; with that CORE vote's premise removed, the bearish lean is no longer defensible at HIGH conviction) | dominant_zone=ELEVATED (RSI 68 cohort-high bounce against an active death cross; the 54-week pseudo-average is explicitly not used as the primary zone read) | seats_bull=1 seats_bear=2 | signal=HOLD (revised from SELL: with the CORE bear vote's factual basis falsified, the remaining case rests only on technical overextension — insufficient for an active SELL, but RSI 68 + active death cross argue against a BUY too)
critic_note=FLAG — MATERIAL: the unlock cited as the primary SELL rationale already completed 2026-07-15 at $86.49M (below $127-130M forecast) with a +13% same-day price reaction, directly contradicting the bearish direction call. No airdrop was ever confirmed (the "airdrop-fueled rally" framing is corrected). Signal downgraded SELL → HOLD.

---

### LINK — HOLD ⚠️ REVISED (Verdict Critic FLAG — see below)

Chainlink's price has bounced back above its short-term averages with firm momentum (RSI 64, rising MACD). **Critic correction (material):** the original framing — "DTCC adopted Chainlink to power a 24/7 collateral management network" — conflates two separate things. DTCC's Chainlink integration is only planned, targeting a Q4 2026 launch, per Cointelegraph's own sourcing ("ahead of a planned fourth-quarter 2026 launch") [source: https://cointelegraph.com/news/dtcc-to-use-chainlink-to-power-247-collateral-management-network] — not a completed integration. DTCC's actually-live milestone (production trades beginning 2026-07-15, involving JPMorgan, BlackRock, and Goldman) runs on Hyperledger Besu or Canton Network, not Chainlink [source: https://www.theblock.co/post/408419/dtcc-begins-first-tokenized-stock-and-treasury-production-trades-involving-jpmorgan-blackrock-and-goldman-wsj]. The case for actually buying here is further undercut by messy fee data: DeFiLlama shows $0 in fees over the last 24 hours against $4.58M over the last 30 days — numbers that don't add up — so we can't currently confirm the token-buyback mechanism is doing what it's supposed to do [source: https://defillama.com/protocol/chainlink]; the critic confirmed this exact inconsistency is still live as of this run (not a stale, already-corrected glitch), though it may be a fee-adapter reporting-lag artifact rather than proof of a genuine zero-revenue day. Main risk: the still-unresolved fee-data inconsistency and premature framing of a not-yet-live DTCC integration, on top of a still-active death cross (50-day average below the 200-day). Watch: the next DeFiLlama fee print for a consistent 24h number, actual confirmation (not announcement) of the DTCC Chainlink integration going live in Q4 2026, and whether price can hold above the $7.91 support and eventually reclaim the $9.37 SMA200.

Research Desk:
  Technical:   Price ($8.675) has recovered above its EMA20 ($8.17) and SMA50 ($7.91) with firm RSI (64.33) and rising positive MACD momentum, but a daily death cross (SMA50 < SMA200 $9.37) is still active. Network activity reportedly hit an 8-month high [source: https://coinpedia.org/price-analysis/link-price-eyes-15-as-chainlink-network-activity-hits-8-month-high/].
  On-Chain:    [UNAVAILABLE — no live on-chain valuation source for LINK this run]
  DeFi:        Chainlink shows $1.57B in value secured and $4.58M in 30-day revenue ($56.8M all-time), but the 24h figure is reported as exactly $0 — an unexplained inconsistency that makes the fee-accrual signal weak and unconfirmed this run [source: https://defillama.com/protocol/chainlink].
  Macro:       Net liquidity tailwind (Fed balance sheet expanding, RRP/TGA draining, M2 accelerating) partially offset by a mildly firming DXY.
  Smart Money: OKX perpetual funding on LINK-USDT-SWAP is +0.0001 [source: https://www.okx.com/api/v5/public/funding-rate], a mild long-leaning skew in leveraged positioning.

Panel:
  Graham (Value):          HOLD — no confirmed margin of safety; the $0/24h vs $4.58M/30d gap means the thin $56.8M all-time fee base can't be trusted this run, despite the price already being statistically cheap.
  Buffett (Quality):       HOLD — the DTCC relationship is real but is a planned Q4 2026 integration, not yet live [source: https://cointelegraph.com/news/dtcc-to-use-chainlink-to-power-247-collateral-management-network, corrected by Verdict Critic — DTCC's actually-live 2026-07-15 production trades run on Hyperledger Besu/Canton Network, not Chainlink]; token-holder value capture (the buyback) remains unconfirmed, so this is a promising future headline, not yet a "wonderful investment."
  Dalio (Cycle):           HOLD — macro liquidity is a supportive tailwind, but LINK's own cycle position is unresolved with the death cross still active and Fear & Greed at 25.
  Druckenmiller (Trend):   BUY (small) — RSI 64 and rising MACD are genuinely constructive momentum; size small with a stop under the $7.91 SMA50 given the death cross overhang.
  Alden (Debasement):      AVOID (fails hurdle) — LINK hasn't cleared the BTC hurdle: -30.8% below its 200wMA with unconfirmed accrual, while BTC captures the same liquidity tailwind with none of that data-quality overhang.
  Burniske (On-chain):     HOLD — $1.57B is value secured, not revenue; the internally inconsistent fee print means the buyback can't be confirmed as active — this is not a confirmed strong-accrual case like AAVE/HYPE/PUMP.

Bull: A firm momentum recovery (RSI 64, rising MACD) plus a real but not-yet-live DTCC integration (planned Q4 2026, corrected by Verdict Critic) give LINK a legitimate future catalyst and a statistically deep price discount.
Bear: An internally inconsistent fee print ($0/24h vs $4.58M/30d, confirmed still live by the critic) means the core value-accrual case can't be confirmed this run, the marquee DTCC catalyst is not yet live (actual 2026-07-15 DTCC production trades run on non-Chainlink infrastructure), and LINK still fails Alden's BTC-hurdle test with an active death cross underneath the bounce.

quorum_verdict=UNCERTAIN (both CORE seats — Graham, Burniske — explicitly withhold conviction on contradictory DeFiLlama fee data, not a genuine two-sided disagreement; per SKILL.md this is UNCERTAIN, not SPLIT) | dominant_zone=DEEP_VALUE (fundamentally unconfirmed — -30.8% vs 200wMA on a full 210-week sample is statistically solid, but the fee-accrual data needed to confirm it's a genuine discount vs. a value trap is internally contradictory) | seats_bull=1 seats_bear=1 | signal=HOLD
critic_note=FLAG — "DTCC adopted Chainlink" corrected to "DTCC plans a Q4 2026 Chainlink integration; its actual live 2026-07-15 milestone runs on Besu/Canton, not Chainlink." $0/24h fee inconsistency confirmed still live (not stale). Signal unchanged: HOLD.

---

## Block 3 — News & sources used by the Research Desk

```
--- RESEARCH SOURCES ---
(Only URLs actually fetched this run via web_fetch, DeFiLlama API, FRED, OKX, or read_news.ts /
the read-news SQLite articles table appear here. No URL = no entry.)

Shared/book-wide sources (used across multiple tokens' Macro / Smart Money / Sentiment lines):
  [T1] https://fred.stlouisfed.org/graph/fredgraph.csv (series: WALCL, RRPONTSYD, WTREGEN, M2SL, DTWEXBGS, DGS2, DGS10) — Fed balance sheet, RRP, TGA, M2 YoY, DXY, 2Y/10Y yields, fetched live 2026-07-21 → T1: primary official macro data
  [T1] https://api.alternative.me/fng/?limit=5&format=json — "value: 25, value_classification: Extreme Fear" (skill's own numeric band places 25 in FEAR 25-49) → T1: hard numeric index with timestamp
  [T1] https://www.okx.com/api/v5/public/funding-rate — OKX perpetual funding rates, 10 of 11 tokens (TON has no instrument), fetched live 2026-07-21, used as smart-money/leverage proxy since Binance futures API returned HTTP 451 (geo-blocked) from this environment → T1: exchange-reported numeric data
  [T1] https://bitcoin-data.com/v1/mvrv-zscore/last, https://bitcoin-data.com/v1/nupl/last, https://bitcoin-data.com/v1/puell-multiple/last, https://bitcoin-data.com/v1/realized-price/last — BTC on-chain valuation metrics, fetched live 2026-07-21 (BTC only; no equivalent live source found for ETH/SOL/other tokens this run) → T1: on-chain metric API
  [UNAVAILABLE] https://farside.co.uk/btc/ — ETF flow table is JS-rendered; both markdown and raw-HTML fetch modes returned only page scaffolding, no flow numbers this run
  [UNAVAILABLE] Lyn Alden current macro commentary — no macro-relevant posts in the last 30 days; all recent posts were personal/book-promotion/fiction content per the skill's own filter rule

BTC research sources:
  [T2] https://bitcoinmagazine.com/news/bitcoin-price-67000-lifting-crypto-stocks — "Bitcoin price nears $67,000, lifting crypto stocks" → T2: named-source journalism
  [T2] https://stocktwits.com/news-articles/markets/cryptocurrency/mstr-isnt-bitcoin-biggest-risk-even-clarity-act-may-not-fix-it-jp-morgan/cZmY2Z2R7nl — JPMorgan flags Strategy/MSTR-specific risk beyond pending crypto legislation → T2: named-source journalism

ETH research sources:
  [T2] https://www.theblock.co/post/407909/cambridge-research-puts-ethereum-node-activity-in-us-where-third-offline-can-stall-finalization — Cambridge research on US node concentration risk → T2: named-source journalism citing academic research
  [T2] https://www.newsbtc.com/news/vitalik-buterin-s-single-slot-finality-plan-shows-ethereum-still-has-a/ — Vitalik Buterin's own team flags unresolved Single Slot Finality issues → T2: named-source journalism
  [T3] https://stocktwits.com/news-articles/markets/cryptocurrency/ethereum-bottom-in-sight-tom-lee-shares-interesting-chart-to-recovery/cZmYE2eR7ns — Tom Lee analyst opinion on ETH bottom → T3: analyst opinion, no hard data
  [UNAVAILABLE] ETF outflow headline for ETH — referenced in a prior handoff without a captured source URL or confirmed dollar figure; excluded from citation per the hard sourcing rule (no URL = no claim)

SOL research sources:
  [T2] https://decrypt.co/373681/morgan-stanley-launches-bitcoin-ethereum-solana-trading-etrade — Morgan Stanley adds BTC/ETH/SOL trading via E*Trade → T2: named-source journalism
  [T2] https://www.theblock.co/post/409040/jito-rolls-out-jtx-self-custodial-trading-platform-for-solana-tokens-and-rwas — Jito launches JTX self-custodial trading platform → T2: named-source journalism
  [T3] https://coinmarketcap.com/community/articles/6a51289b73c24151361ad41f — community-sourced "record bearish sentiment" (Santiment) claim → T3: community/aggregator article, lower rank

TON research sources:
  [T2] https://www.newsbtc.com/toncoin-ton/toncoin-ton-price-performance-5-days-post-durov-arrest-whats-next/ — TON price performance 5 days post-Durov-arrest → T2: named-source journalism
  [UNAVAILABLE] OKX TON-USDT-SWAP — no perpetual instrument exists for TON on OKX; error "Instrument ID ... doesn't exist"

HYPE research sources:
  [T1] https://defillama.com/protocol/hyperliquid — TVL $6.36B, 24h/30d/all-time fee and confirmed buyback mechanism data → T1: exact tracked metric, primary source
  [T2] https://www.cryptoprowl.com/releases/hyperliquid-falls-10-amid-market-rout-6189 — HYPE falls 10% amid broader market rout → T2: named-source journalism
  [T3] https://www.binance.com/en/square/post/343067222325858 — large trader withdraws 7,863 ETH amid suspected sell-off → T3: exchange social-post, unverified beyond platform self-report
  [T3] https://www.binance.com/en/square/post/345197985045361 — whale $5.38B position, $11.1M unrealized loss on ETH short → T3: exchange social-post

AAVE research sources:
  [T1] https://defillama.com/protocol/aave — TVL $14.64B, fees $3.85M/30d $302M all-time, confirmed "Token Holder Net Income (Token Buyback)" mechanism → T1: primary tracked metric
  [T2] https://cointelegraph.com/news/aave-brings-v4-to-avalanche-laying-groundwork-for-tokenized-asset-lending — Aave V4 expands to Avalanche → T2: named-source journalism
  [T2] https://www.theblock.co/post/382865/aave-token-holder-poison-pill-dao-absorb-aave-labs-revenue-debate — token holder "poison pill" proposal, DAO/Aave Labs revenue dispute → T2: named-source journalism
  [T2] https://www.theblock.co/post/408366/stani-kulechov-on-aave-v4-avalanche-and-why-rwas-will-hit-100-billion-this-year — founder commentary on RWA growth → T2: named-source journalism, founder-sourced

JUP research sources:
  [T1] https://defillama.com/protocol/jupiter-aggregator — $0 TVL (genuine aggregator methodology), confirmed buyback mechanism → T1: primary tracked metric
  [T1] https://api.llama.fi/summary/fees/jupiter-aggregator?dataType=dailyRevenue — $40,909/24h, $2.52M/30d, $109.1M all-time revenue → T1: primary API data
  [T3] https://www.binance.com/en/square/post/330576990249170 — JUP underperformance vs. Hyperliquid through June → T3: exchange social-post

UNI research sources:
  [T1] https://defillama.com/protocol/uniswap — TVL $3.12B, confirmed live tokenholder fee switch, $147,263/24h $3.72M/30d $26.65M all-time → T1: primary tracked metric
  [T3] https://www.binance.com/en/square/post/343747869147121 — ~99.5% DEX volume share claim → T3: exchange social-post
  [T3] https://www.binance.com/en/square/post/343978933786993 — founder Hayden Adams claims ~$5.2M/day in fees (unreconciled vs. DeFiLlama figure) → T3: exchange social-post, founder-sourced but unreconciled
  [T3] https://www.binance.com/en/square/post/344010882116209 — founder confirms fee switch live, UNI being burned → T3: exchange social-post, founder-sourced
  [T2] https://www.theblock.co/post/408836/uni-burn-poised-to-grow-as-uniswap-governance-votes-on-v4-fees-and-robinhood-chain-expansion — governance voting to grow burn via v4 fees → T2: named-source journalism

AERO research sources:
  [T1] https://defillama.com/protocol/aerodrome-v1 — combined TVL ~$305M (aerodrome-v1 + aerodrome-slipstream), ve(3,3) fee-distribution mechanism → T1: primary tracked metric
  [T2] https://www.theblock.co/post/319258/aerodrome-tops-1-billion-in-deposits-dominating-defi-on-base — historical $1B+ TVL headline, basis for the ~70% decline disclosure → T2: named-source journalism
  [T2] https://www.theblock.co/post/337521/two-contributors-suspended-from-venices-vvv-token-launch-on-aerodrome — governance/front-running scandal → T2: named-source journalism
  [T3] https://coinmarketcap.com/community/articles/6a401ee09d2d2133c1796c0f — independent corroboration of ~$500M lifetime fees → T3: community/aggregator article

PUMP research sources:
  [T1] https://defillama.com/protocol/pump.fun — $680,735 (24h), $18.7M (30d), $1.06B (all-time) fees, confirmed buyback mechanism → T1: primary tracked metric
  [T2] https://defi-planet.com/2026/07/pump-fun-unlocks-57-3b-pump-tokens-as-team-and-investor-vesting-begins/ — 57.3B token unlock, team/investor vesting begins → T2: named-source journalism
  [T2] https://invezz.com/news/2026/07/13/pump-fun-pump-price-analysis-can-buybacks-offset-127m-unlock-pressure/ — $127-130M estimated unlock sell-pressure analysis → T2: named-source journalism
  [T2] https://beincrypto.com/pumpfun-airdrop-pump-token-unlock/ — airdrop-fueled rally vs. unlock overhang → T2: named-source journalism

LINK research sources:
  [T1] https://defillama.com/protocol/chainlink — $1.57B value secured, $4.58M/30d revenue, $0/24h internally-inconsistent fee print → T1: primary tracked metric (flagged data-quality issue disclosed, not hidden)
  [T2] https://cointelegraph.com/news/dtcc-to-use-chainlink-to-power-247-collateral-management-network — DTCC plans Chainlink integration for 24/7 collateral management, targeting Q4 2026 (not yet live — corrected by Verdict Critic) → T2: named-source journalism
  [T2] https://coinpedia.org/price-analysis/link-price-eyes-15-as-chainlink-network-activity-hits-8-month-high/ — network activity hits 8-month high → T2: named-source journalism

Verdict Critic sources (Step 4 — fresh, independent fact-checks; new URLs surfaced beyond the original Research Desk pull):
  BTC:  [T2] https://cointelegraph.com/markets/bitcoin-nears-seven-week-high-as-stocks-ignore-iran-strikes-trump-10-tariff-plans — golden-cross/7wk-high context, Iran/tariff geopolitical risk
        [T2] https://www.coindesk.com/daybook-us/2026/07/21/bitcoin-rally-has-broad-based-support-as-institutions-whales-options-traders-pile-in — Morgan Stanley/E*Trade, BlackRock ETF commentary, T-bill liquidity-drain risk
  ETH:  [T1] https://defillama.com/chain/ethereum — live chain revenue $51,637/24h, $293,155/24h fees
        [T2] https://www.theblock.co/post/408913/bitmine-expands-ethereum-treasury-5-78-million-eth-repurchases-5-5-million-shares — Bitmine treasury/buyback NAV-discount signal
  SOL:  [T1] https://defillama.com/chain/solana — DEX volume -13.64% WoW, chain fees $523,745/24h
        [T2] https://bitcoinmagazine.com/news/fed-chair-warsh-no-bailout-for-crypto — Fed Chair Warsh no-crypto-bailout remark
  TON:  [T1] https://en.wikipedia.org/wiki/Arrest_and_indictment_of_Pavel_Durov — corrected Durov arrest/travel-freedom timeline
        [T1] https://defillama.com/chain/ton — TON DeFi TVL $66.3M (corrected from UNAVAILABLE)
        [T2] https://www.theblock.co/post/313367/ton-blockchain-now-down-six-hours — 2026-07-15 six-hour network outage
  HYPE: [T2] https://beincrypto.com/hype-etf-first-weekly-outflow/ — idiosyncratic underperformance vs. flat market cap, ETF net-assets -12.7%
        [T2] https://www.coindesk.com/markets/2026/07/17/ether-falls-twice-as-hard-as-bitcoin-and-hype-drops-10-as-the-chip-trade-unwinds — unconfirmed Glassnode on-chain reversal, F&G=25
  AAVE: [T2] https://www.theblock.co/post/396458/top-aave-risk-manager-chaos-labs-exits-amid-governance-dispute — BGD Labs/ACI/Chaos Labs contributor exodus, Zeller insider-sale confirmation
  JUP:  [T3] https://coinmarketcap.com/community/articles/6a317d8df8dfac4e8991dcfb/ — $3T cumulative volume vs. sub-$0.20 price context
        [T3] https://coinmarketcap.com/community/articles/6a3bcc9e2b91f8497edc3032/ — 2026-06-24 buyback-narrative pop that reversed by 2026-06-27
  UNI:  [T2] https://cryptonews.com/news/uniswap-uni-crypto-buybacks-burns-protocol-fees/ — Hayden Adams $5.2M/day fee claim, cross-checked against DeFiLlama gross fees
  AERO: [T2] https://coinmarketcal.com/event/binance-listing-44704192-1 — Binance Seed-Tag AERO listing, 2026-07-17
  PUMP: [T2] https://99bitcoins.com/news/altcoins/pump-fun-token-vesting-cliff-unlock/ — unlock completed 2026-07-15 at $86.49M (below $127-130M forecast), +13% same-day price reaction
  LINK: [T2] https://www.theblock.co/post/408419/dtcc-begins-first-tokenized-stock-and-treasury-production-trades-involving-jpmorgan-blackrock-and-goldman-wsj — DTCC's actually-live 2026-07-15 milestone runs on Hyperledger Besu/Canton Network, not Chainlink
```

## Step 5 — Citation Validation (reference-validator subagent output, printed verbatim, non-skippable)

56 citations were split into two batches of 28 and run through independent `reference-validator` subagents in parallel. Raw output below, unedited:

### Batch 1 (28 citations: SHARED, BTC, ETH, SOL, TON, HYPE, AAVE, JUP, UNI, AERO T1-only)

```
=== CITATION VALIDATION REPORT ===

Token | Tier | Status          | URL                                                                                                   | Evidence
------|------|-----------------|--------------------------------------------------------------------------------------------------------|----------
SHARED| T1   | ✅ VERIFIED      | api.alternative.me/fng/?limit=5&format=json                                                            | Found: "value":"25","value_classification":"Extreme Fear" (latest entry)
SHARED| T1   | 🚫 FETCH_FAILED  | okx.com/api/v5/public/funding-rate                                                                      | Cited URL (no instId param) returns HTTP 400. Endpoint exists but requires instId=INSTRUMENT to return data — as cited it is non-functional.
BTC   | T2   | ✅ VERIFIED      | bitcoinmagazine.com/.../bitcoin-price-67000-lifting-crypto-stocks                                       | Found: price "$66,886" (≈$67k), "Nasdaq-listed Strategy (MSTR)...jumped", COIN +11%, MARA +6% — "lifting crypto stocks" confirmed
BTC   | T2   | ❌ NOT_FOUND     | stocktwits.com/.../mstr-isnt-bitcoin-biggest-risk-.../jp-morgan/...                                     | Page headline/body CONTRADICTS the quote: "We do not see Strategy as the main structural threat to bitcoin" — JPMorgan explicitly downplays MSTR-specific risk, opposite of "flags Strategy/MSTR-specific risk"
ETH   | T2   | ✅ VERIFIED      | theblock.co/.../cambridge-research-puts-ethereum-node-activity-in-us...                                | Found: "31% of Ethereum node activity in the US... a third offline can stall finalization" — exact match
ETH   | T2   | ⚠️ PARTIAL       | newsbtc.com/.../vitalik-buterin-s-single-slot-finality-plan-shows-ethereum-still-has-a/                | Found: "Single Slot Finality," "Ethereum," "still has a [problem]" — confirms unresolved SSF issue, but it's Vitalik's own proposal/post, not "his team" flagging it (attribution nuance)
ETH   | T3   | ✅ VERIFIED      | stocktwits.com/.../ethereum-bottom-in-sight-tom-lee-shares-interesting-chart-to-recovery/               | Found: "Tom Lee...suggesting Ethereum...may be forming a short-term bottom"
SOL   | T2   | ✅ VERIFIED      | decrypt.co/373681/morgan-stanley-launches-bitcoin-ethereum-solana-trading-etrade                       | Found: "Morgan Stanley has launched spot cryptocurrency trading on its E*TRADE platform...Bitcoin, Ethereum, and Solana"
SOL   | T2   | ✅ VERIFIED      | theblock.co/.../jito-rolls-out-jtx-self-custodial-trading-platform-for-solana-tokens-and-rwas          | Found: "Jito rolls out JTX self-custodial trading platform for Solana tokens and RWAs" (title match)
SOL   | T3   | ✅ VERIFIED      | coinmarketcap.com/community/articles/6a51289b73c24151361ad41f                                          | Fetched via redirect target (trailing slash); title: "Solana News: Santiment Flags Record Bearish Sentiment, Analyst Eyes $127"
TON   | T2   | ✅ VERIFIED      | newsbtc.com/toncoin-ton/toncoin-ton-price-performance-5-days-post-durov-arrest-whats-next/              | Found: "Toncoin (TON)...following the arrest of Telegram co-founder...Durov...TON's price plummeting over 25%...five days"
HYPE  | T1   | ✅ VERIFIED      | defillama.com/protocol/hyperliquid                                                                      | Found (raw fetch): "TVL, Fees, Revenue"..."Gross Protocol Revenue (Perp Fees, Spot Fees...)"..."Token Holder Net Income (Token Buyback)" — TVL $6.114B shown
HYPE  | T2   | ✅ VERIFIED      | cryptoprowl.com/releases/hyperliquid-falls-10-amid-market-rout-6189                                     | Found: "price of Hyperliquid...is down 10% on July 17...leading cryptocurrencies lower as stock markets...retreat"
HYPE  | T3   | 🚫 FETCH_FAILED  | binance.com/en/square/post/343067222325858                                                              | Fetched but returned "No more content available" (JS-rendered/blocked) — cannot confirm quote
HYPE  | T3   | 🚫 FETCH_FAILED  | binance.com/en/square/post/345197985045361                                                              | Same — "No more content available"
AAVE  | T1   | ✅ VERIFIED      | defillama.com/protocol/aave                                                                              | Found: og:image "tvl=$14.668b" (≈$14.64B claimed), description: "Token Holder Net Income (Token Buyback)"
AAVE  | T2   | ✅ VERIFIED      | cointelegraph.com/.../aave-brings-v4-to-avalanche-...                                                   | Found: "Aave has launched V4 on Avalanche, marking the first expansion...beyond Ethereum"
AAVE  | T2   | ✅ VERIFIED      | theblock.co/.../aave-token-holder-poison-pill-dao-absorb-aave-labs-revenue-debate                       | Found: title exact match "poison pill for DAO to absorb Aave Labs amid contentious revenue debate"
AAVE  | T2   | ✅ VERIFIED      | theblock.co/.../stani-kulechov-on-aave-v4-avalanche-and-why-rwas-will-hit-100-billion-this-year         | Found: "Aave Labs Founder Stani Kulechov...why RWAs will double to $100 billion by December"
JUP   | T1   | ✅ VERIFIED      | defillama.com/protocol/jupiter-aggregator                                                               | Found: "Gross Protocol Revenue (Aggregator Swap Fees)"..."Token Holder Net Income (Token Buyback)"; no TVL figure shown (consistent with "$0 TVL" aggregator claim)
JUP   | T1   | ✅ VERIFIED      | api.llama.fi/summary/fees/jupiter-aggregator?dataType=dailyRevenue                                      | Found exact: "total24h":40909, "total30d":2517406 (~$2.52M), "totalAllTime":109108404 (~$109.1M)
JUP   | T3   | 🚫 FETCH_FAILED  | binance.com/en/square/post/330576990249170                                                              | "No more content available" — cannot confirm quote
UNI   | T1   | ✅ VERIFIED      | defillama.com/protocol/uniswap                                                                          | Found: og:image "tvl=$3.123b" (≈$3.12B claimed), description: "Token Holder Net Income (Tokenholder fees)"
UNI   | T3   | 🚫 FETCH_FAILED  | binance.com/en/square/post/343747869147121                                                              | "No more content available"
UNI   | T3   | 🚫 FETCH_FAILED  | binance.com/en/square/post/343978933786993                                                              | "No more content available"
UNI   | T3   | 🚫 FETCH_FAILED  | binance.com/en/square/post/344010882116209                                                              | "No more content available"
UNI   | T2   | ✅ VERIFIED      | theblock.co/.../uni-burn-poised-to-grow-as-uniswap-governance-votes-on-v4-fees-and-robinhood-chain...   | Found: "voting scheduled to run from July 19 through July 26" — exact match
AERO  | T1   | ⚠️ PARTIAL       | defillama.com/protocol/aerodrome-v1                                                                      | Cited URL is the V1 sub-page only, TVL shown = $127.42M, not "$305M combined." Parent page defillama.com/protocol/aerodrome shows combined TVL $326.69M (close order-of-magnitude to $305M claim, but not on the cited URL). ve(3,3)-style fee distribution confirmed on both pages.

--- SUMMARY ---
VERIFIED: 18/28 (64%)  PARTIAL: 2/28 (7%)  NOT_FOUND: 1/28 (4%)  FETCH_FAILED: 7/28 (25%)
```

### Batch 2 (28 citations: AERO T2/T3, PUMP, LINK, BTC-macro, ETH/SOL chain-level, TON, HYPE, AAVE, JUP T3, UNI, AERO-listing)

```
=== CITATION VALIDATION REPORT ===

# | Token | Tier | Status        | URL (short)                              | Evidence
1 | AERO  | T2   | VERIFIED      | theblock.co/post/319258                  | "Aerodrome tops $1 billion in deposits, dominating DeFi on Base" — exact match
2 | AERO  | T2   | PARTIAL       | theblock.co/post/337521                  | Confirms suspension + VVV token launch (Jan 2025); article describes flagged/suspicious activity, not literal "front-running"
3 | AERO  | T3   | VERIFIED      | coinmarketcap.com/.../6a401ee0...        | "Aerodrome Has Now Generated More Than HALF A BILLION In Total Fees" — matches ~$500M claim
4 | PUMP  | T1   | VERIFIED      | defillama.com/protocol/pump.fun          | Exact: Revenue 24h $680,735; 30d $18.73m; all-time $1.064b; buyback mechanism confirmed
5 | PUMP  | T2   | VERIFIED      | defi-planet.com                          | Exact: 57.279B tokens, 1yr lockup, 3yr vesting
6 | PUMP  | T2   | VERIFIED      | invezz.com                               | Title match: "$127M unlock pressure" (body blocked by fetcher, title sufficient)
7 | PUMP  | T2   | VERIFIED      | beincrypto.com/pumpfun-airdrop...        | Exact: "has not announced any airdrop plans"
8 | LINK  | T1   | VERIFIED      | defillama.com/protocol/chainlink         | Exact: TVL $1.572b; Revenue 30d $4.58m; Revenue 24h $0 (label reads "Total Value Locked" not "secured" — numeric claim confirmed)
9 | LINK  | T2   | VERIFIED      | cointelegraph.com (DTCC)                 | Exact: "24/7 collateral management...fourth quarter of 2026"
10| LINK  | T2   | VERIFIED      | coinpedia.org                            | "highest daily address activity...since September 2025" (~8mo)
11| BTC   | T2   | VERIFIED      | cointelegraph.com (7-week high)          | Exact: "seven-week highs," golden cross, Iran strikes, 10% tariff plans
12| BTC   | T2   | ❌ NOT_FOUND  | coindesk.com/daybook-us/...              | Full article confirms ETF inflows, whale accumulation, options activity, T-bill liquidity risk — but ZERO mentions of "Morgan Stanley," "E*Trade," or "BlackRock" anywhere. Only the T-bill/liquidity portion is supported.
13| ETH   | T1   | VERIFIED      | defillama.com/chain/ethereum             | Exact: Revenue $51,637/24h; Fees $293,155/24h
14| ETH   | T2   | VERIFIED      | theblock.co (Bitmine)                    | Exact: 5.78M ETH treasury, share repurchases
15| SOL   | T1   | VERIFIED      | defillama.com/chain/solana                | Exact: DEX volume -13.64% WoW; fees $523,745/24h
16| SOL   | T2   | VERIFIED      | bitcoinmagazine.com (Warsh)               | Exact: "We do not want to be in the bailout business, full stop"
17| TON   | T1   | VERIFIED      | en.wikipedia.org (Durov)                  | Exact: Aug 2024 arrest; permitted to leave France Mar/Jul 2025
18| TON   | T1   | PARTIAL       | defillama.com/chain/ton                   | Live TVL read $66.08M vs claimed "~$66.3M" — same ballpark (real-time drift)
19| TON   | T2   | VERIFIED      | theblock.co (TON outage)                  | Exact: six-hour outage, validators restart
20| HYPE  | T2   | VERIFIED      | beincrypto.com (ETF outflow)               | Exact: underperformed flat market cap; "net assets fell 12.7%"
21| HYPE  | T2   | VERIFIED      | coindesk.com (chip trade unwind)          | Exact: Glassnode reversal language, F&G=25
22| AAVE  | T2   | VERIFIED      | theblock.co (Chaos Labs)                  | Exact: Chaos Labs exit, BGD Labs + ACI departures cited
23| JUP   | T3   | VERIFIED      | coinmarketcap.com/.../6a317d8d...         | Exact: "$3 trillion cumulative volume," price below $0.20
24| JUP   | T3   | PARTIAL       | coinmarketcap.com/.../6a3bcc9e...         | Meta confirms "up 8% today" + buyback narrative; "later reversed" is the report's own forward annotation, unverifiable from this contemporaneous source
25| UNI   | T2   | VERIFIED      | cryptonews.com                            | Exact: Hayden Adams, ~$5.2M daily fees
26| AERO  | T2   | 🚫 FETCH_FAILED| coinmarketcal.com/event/...              | 403 Forbidden on repeated attempts (bot-blocked); content could not be retrieved
27| PUMP  | T2   | VERIFIED      | 99bitcoins.com                            | Exact: 57.279B tokens, ~$86.49M, July 15 2026, +13%
28| LINK  | T2   | VERIFIED      | theblock.co (DTCC tokenized trades)       | Exact: JPMorgan/BlackRock/Goldman, Hyperledger Besu/Canton Network

SUMMARY: VERIFIED 22/28 (78.6%)  PARTIAL 4/28 (14.3%)  NOT_FOUND 1/28 (3.6%)  FETCH_FAILED 1/28 (3.6%)
```

### Combined result (56 citations across both batches)

VERIFIED: 40/56 (71.4%) · PARTIAL: 6/56 (10.7%) · NOT_FOUND: 2/56 (3.6%) · FETCH_FAILED: 8/56 (14.3%)

**Step 5d actions taken (per SKILL.md's literal rule — NOT_FOUND ⇒ `⚠️ CITATION_FAILED` on that token; all-FETCH_FAILED ⇒ `ℹ️ UNVERIFIED`):**
- **BTC → ⚠️ CITATION_FAILED** (Block 1 signal tagged, Block 2 narrative corrected in-place, audit line added): both of BTC's NOT_FOUND sources (stocktwits/JPMorgan — claim reversed; coindesk daybook — BlackRock/Morgan-Stanley detail not present in source) have been fixed by removing/re-attributing the unsupported claims. No other token had a NOT_FOUND source.
- **No token qualifies for `ℹ️ UNVERIFIED`** under the skill's literal "only FETCH_FAILED sources" rule — every token with a FETCH_FAILED source (HYPE, JUP, UNI, AERO) also has multiple independently-VERIFIED sources, so the strict threshold isn't met. Flagging here for transparency anyway: 6 `binance.com/en/square` T3 posts (2×HYPE, 1×JUP, 3×UNI) returned "No more content available" (JS-rendered/blocked) and could not be confirmed — the specific whale-flow and DEX-share figures sourced only from those posts should be treated as soft/unconfirmed color, not hard fact. The SHARED OKX funding-rate URL (cited across most tokens' Smart Money lines) is FETCH_FAILED as written (missing required `instId` param) — funding-rate figures quoted from this endpoint could not be independently re-confirmed this run and should be read as indicative, not verified. AERO's Binance Seed-Tag listing citation (coinmarketcal.com) is bot-blocked (403) and unconfirmed by an alternate source.
- **ETH, SOL, TON, AAVE, PUMP, LINK: ✅ all citations VERIFIED or PARTIAL** — no signal tag required.

⚠️ **This step is not self-attested** — both reports above are the verbatim, unedited output of two independent `general-purpose` subagents instructed to run `.agents/skills/reference-validator/SKILL.md`'s procedure and fetch every URL live.

---

⛔ Self-check performed before printing (per SKILL.md Step 3 checklist):
- All 11 tokens have a complete Block 2 section — 5 Research Desk lines (Technical/On-Chain/DeFi/Macro/Smart Money) + 6 Panel lines (Graham/Buffett/Dalio/Druckenmiller/Alden/Burniske) + Bull/Bear — confirmed present for all 11.
- seats_bull + seats_bear <= 6 for every token — confirmed (max is AERO at 5, all others <=4).
- Every research source entry starts with https:// — confirmed; the two non-URL "[source: newsbtc]"/"[source: tradingview/stocktwits feed...]" shorthand tags found in the raw per-token working files (TON, ETH) were corrected to full URLs or marked [UNAVAILABLE] before inclusion here.
- read-news citations verified against the underlying SQLite `articles` table URLs (not the top-level event-cluster JSON, which has no URL field) — confirmed.
- No source cited that was not actually fetched this run — confirmed against the underlying JSON artifacts (DEFI_data.json, funding_rates.json, MACRO_data.json, news_by_token.json, BTC_onchain.json) assembled this run.
- TradingView screenshots: [UNAVAILABLE] for all 11 tokens — `capture_screenshot` timed out (MCP error -32001) and the 2-indicator-slot limit was consumed by RSI+MACD; disclosed honestly rather than omitted or faked.
- Bollinger Bands: [UNAVAILABLE] for all 11 tokens — same 2-indicator-slot limit as above.
- ETF flow data (farside.co.uk): [UNAVAILABLE] — JS-rendered table, no numeric data returned in either markdown or raw-HTML fetch mode.
- Lyn Alden current macro commentary: [UNAVAILABLE] — no macro-relevant posts in the last 30 days.
- On-chain valuation metrics (MVRV-Z/NUPL/Puell/realized price): live and complete for BTC only; [UNAVAILABLE] for all other 10 tokens — no equivalent free live on-chain API source found this run for ETH/SOL/etc.
- TON smart-money proxy: [UNAVAILABLE] — no OKX perpetual instrument exists for TON.
- Step 5 Citation Validator: executed as two independent parallel subagent calls (56 total citations), verbatim report printed above — non-skippable, not self-attested. 2 NOT_FOUND (both BTC) triggered ⚠️ CITATION_FAILED and were corrected in-place; 8 FETCH_FAILED (6× binance.com/square T3 posts, 1× OKX funding-rate endpoint as cited, 1× coinmarketcal.com bot-block) did not meet the "all-FETCH_FAILED" threshold for ℹ️ UNVERIFIED on any single token but are disclosed above as soft/unconfirmed color.
