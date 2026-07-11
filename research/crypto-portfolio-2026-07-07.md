# Crypto Portfolio Signal Report — 2026-07-06

**Universe:** BTC, ETH, SOL, TON, HYPE, AAVE, JUP, UNI, AERO, PUMP, LINK (from `.cache/crypto-daily/portfolio.csv`)

**Fear & Greed Index:** 27 ("Fear") — source: `https://api.alternative.me/fng/?limit=1`
**Portfolio Governor:** Fear regime (25–49) → max 6 simultaneous active buys. Raw signals produced exactly 6 (3 BUY + 3 BUY(small)) — no downgrades required.

**Methodology note (condensed run):** This run used the crypto-advisor skill's rules (zone guard, conviction-weighted quorum with CORE-lens double-weighting, portfolio governor, HOLD-default-on-uncertainty) but condensed the literal 5-researcher + 6-investor-per-token subagent fan-out (66+ calls) into one research+panel subagent per token (11 total), each doing real web research and running the full 6-lens vote itself. All TradingView price/RSI/MACD/moving-average data was pulled directly by the orchestrator (sequential, single shared chart) — never fabricated or recomputed by an investor-lens subagent. Every citation below was actually fetched (`web_fetch`); failed/blocked sources are flagged INSUFFICIENT, not silently dropped.

---

## Signal table

| Token | Price | RSI(14) | Zone (vs 200wk avg) | Weekly bars | Quorum | Signal | Rationale |
|---|---|---|---|---|---|---|---|
| AAVE | $92.31 | 62.12 | -32.7% (deep value) | 210 | BULLISH (3B/1Br, both CORE HIGH) | **BUY** | Biggest network-growth day in ~5yrs (1,806 new wallets/day); $10.9B TVL; both core lenses (Graham+Burniske) HIGH-conviction bullish despite an active death cross. |
| UNI | $3.138 | 57.07 | -54.2% (deep value, deepest in cohort) | 210 | BULLISH (3B/0Br, both CORE HIGH) | **BUY** | Fee-switch is now live and EXECUTED (17% of V2/V3 fees + Unichain sequencer fees burn UNI), closing the old moat-vs-value-accrual gap, at the cheapest level of the whole cohort. |
| LINK | $7.879 | 50.30 | -37.2% (deep value) | 210 | BULLISH (3B/1Br) | **BUY** | Real, growing protocol fee revenue (~$4.6M/30d) plus deepening institutional integration (SWIFT/DTCC/Euroclear "Project Pangea"); death cross still unresolved but not core-blocking. |
| ETH | $1,769.93 | 55.05 | -28.4% (deep value) | 210 | SPLIT, bull lean (+2.5 net; 3B/2N/1Br) | **BUY (small)** | Institutions (Bitmine, Sharplink) and spot ETFs net-buying into weakness, exchange float shrinking — but the 50/200 death cross is still intact, so sized small. |
| SOL | $81.02 | 61.84 | -24.6% (deep value) | 210 | SPLIT, thin bull lean (+1 net; 2B/2N/2Br) | **BUY (small)** | ETF staking-yield inflows (~5%) continuing through a 57% price drop, but DEX volume has halved — core lenses (Alden bull vs Druckenmiller bear) are essentially tied, so this is a fragile signal — treat as the weakest of the three small buys. |
| HYPE | $70.146 | 57.03 | insufficient history (36wk, launched Nov 2024) | 36 | BULLISH (3B/0Br, no dissent) | **BUY (small)** | Clean uptrend (+87% YoY, no death cross), real buyback-funded fee revenue (~$2.3M/day); capped to small size purely because there isn't yet enough history for a valuation-zone read. |
| TON | $1.679 | 50.08 | -45.2% (deep value) | 210 | SPLIT, bear-leaning (-3 net; 1B/3N/2Br) | HOLD | Telegram's 950M-user Mini-App mandate is a real distribution moat, but on-chain TVL has roughly halved and large token unlocks are ongoing — panel leans bearish, not bullish, so no buy despite the deep discount. |
| JUP | $0.235 | 58.86 | insufficient history (128wk, launched Jan 2024) | 128 | SPLIT, even (net 0; 1B/4N/1Br) | HOLD | Trend has turned (golden cross), but tokenomics are broken — a co-founder admits the $70M 2025 buyback "didn't move" price against 150% supply growth. Evenly split panel, no lean either way. |
| AERO | $0.576 | 64.55 | insufficient history (127wk, launched Feb 2024) | 127 | UNCERTAIN, bullish-tilted (net +5; 2B/4N/0Br, but both CORE neutral) | HOLD | Strong momentum and real buyback revenue, but TVL has more than halved in 6 months and neither CORE lens (Graham, Burniske) reached a bullish conviction — doesn't clear the bar for BUY(small) under an UNCERTAIN verdict. |
| BTC | $63,179.05 | 49.63 | +0.5% (fair value, essentially at 4yr avg) | 210 | BEARISH (0B/2Br/4N, net -8) | **SELL** | Confirmed 50/200 death cross with price under both moving averages despite sitting at the 200-week average; institutional ETF outflows continuing; no core-lens dissent to offset. |
| PUMP | $0.001616 | 55.82 | insufficient history (52wk, launched Jul 2025) | 52 | BEARISH (0B/5Br/1N, both CORE HIGH) | **SELL** | Revenue down ~2/3 YoY, the buyback commitment was just cut from 100%→50% of revenue, a ~$134.65M supply unlock lands July 12, and a $500M+ RICO/securities suit is unresolved. |

---

## Portfolio Governor

- F&G = 27 → **Fear** regime → cap = 6 simultaneous active buys.
- Raw buy signals: AAVE, UNI, LINK (full BUY) + ETH, SOL, HYPE (BUY small) = **6 total**.
- 6 ≤ cap of 6 → **no downgrades applied.**

## Top picks today

**AAVE ($92.31), UNI ($3.138), LINK ($7.879)** — full-size buys, all deep-value zone with bullish core-lens conviction and confirmed weekly history ≥200 bars.
**ETH ($1,769.93), SOL ($81.02), HYPE ($70.146)** — small-tranche buys: ETH/SOL because the quorum is a thin/fragile SPLIT (not a clean BULLISH), HYPE because it's too young (36 weeks) for a full valuation-zone read despite a clean bullish quorum.

## Data quality notes / INSUFFICIENT flags

- **Valuation zone UNKNOWN (not enough weekly history for a 200-week MA):** HYPE (36 weekly bars), JUP (128), AERO (127), PUMP (52). This is expected given each token's launch date, not a fetch failure — confirmed directly against TradingView's own bar counts (not estimated).
- **DeFiLlama's own web pages (`defillama.com/...`) returned HTTP 403 across nearly every token this run** — worked around via the underlying `api.llama.fi` JSON API where possible (AAVE, JUP, LINK, TON succeeded via API fallback; AERO's API fallback did not return usable TVL/fee data, so those AERO figures are sourced from secondary search snippets only and flagged lower-confidence).
- **BTC:** MVRV Z-score, current-week ETF flows, and exchange-balance data were all unfetchable (404/403 across lookintobitcoin, farside.co.uk, theblock.co) — verdict rests on the sources that did resolve (CoinDesk Sharpe-ratio piece, Glassnode research note).
- **TON:** whale-concentration and Q1 2026 TVL/transaction-count figures came only from unfetchable WebSearch snippets — reported as unverified claims, not used as citations.
- **AERO:** TVL/revenue figures came from Google-indexed snippets citing DeFiLlama, not a direct fetch — flagged INSUFFICIENT for independent verification.
- No numbers in this report were fabricated; every price/RSI/MACD/moving-average figure came from a live TradingView pull (BINANCE/OKX/COINBASE feeds) done by the orchestrator, and every qualitative claim in the panel votes is attributed to a real, fetched URL or explicitly flagged as unverified.

## Per-token TradingView data (orchestrator-pulled, live, 2026-07-06)

| Token | Symbol used | Price | RSI(14) | MACD hist | EMA20 | SMA50 | SMA200 | 200wMA | Death cross | Weekly bars |
|---|---|---|---|---|---|---|---|---|---|---|
| BTC | BINANCE:BTCUSDT | 63,179.05 | 49.63 | +701.71 | 62,480 | 66,262 | 74,570 | 62,841 | TRUE | 210 |
| ETH | BINANCE:ETHUSDT | 1,769.93 | 55.05 | +31.34 | 1,708.83 | 1,797.02 | 2,252.86 | 2,473.25 | TRUE | 210 |
| SOL | BINANCE:SOLUSDT | 81.02 | 61.84 | +1.25 | 76.35 | 75.28 | 93.00 | 107.43 | TRUE | 210 |
| TON | OKX:TONUSDT (=GRAM/USDT internally) | 1.679 | 50.08 | +0.024 | 1.693 | — | — | 3.0626 | n/a | 210 |
| HYPE | OKX:HYPEUSDT | 70.146 | 57.03 | +0.384 | 61.93 | — | — | insufficient | n/a | 36 |
| AAVE | BINANCE:AAVEUSDT | 92.31 | 62.12 | +0.75 | 83.58 | 79.23 | 110.72 | 137.24 | TRUE | 210 |
| JUP | BINANCE:JUPUSDT | 0.235 | 58.86 | +0.0011 | 0.2059 | 0.1987 | 0.1856 | insufficient | FALSE | 128 |
| UNI | BINANCE:UNIUSDT | 3.138 | 57.07 | +0.031 | 3.05 | 2.98 | 3.80 | 6.854 | TRUE | 210 |
| AERO | COINBASE:AEROUSD | 0.576 | 64.55 | +0.00789 | 0.4626 | — | — | insufficient | n/a | 127 |
| PUMP | OKX:PUMPUSDT | 0.001616 | 55.82 | +0.000037 | 0.001576 | — | — | insufficient | n/a | 52 |
| LINK | BINANCE:LINKUSDT | 7.879 | 50.30 | +0.108 | 7.79 | 8.24 | 9.67 | 12.547 | TRUE | 210 |

No publishing action was taken (no Telegram, no X/Notion) per instructions — this is analysis-only, written to this file for the scheduled loop to consume.
