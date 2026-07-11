# Crypto Signal Report — 2026-07-09

**Data source:** TradingView MCP (live desktop chart), pulled sequentially per token in this session. Real-time quotes, daily RSI(14)/MACD(12,26,9)/EMA(20)/SMA(50), and weekly SMA(200) ("200-week MA") — no fabricated values. See per-token notes below for the two symbol substitutions required.

**Fear & Greed Index: 22 — Extreme Fear.** Governor cap: **max 4 active BUY signals.**

---

## 1. Signal Table

| Token | Price | RSI(14) D | Zone (vs 200wMA) | Signal | Rationale |
|---|---:|---:|---|:---:|---|
| BTC | $62,948.00 | 49.05 | FAIR_VALUE (+0.13%) | HOLD | Sitting right on the 200wMA test; MACD hist turning positive but price still below daily SMA50 — governor cap (4) filled by deeper-discount names |
| ETH | $1,754.47 | 53.11 | DEEP_VALUE (−29.0%) | **BUY** | Fresh daily MACD bullish cross (MACD −0.10→ crossed above signal), price back above EMA20, 29% below 200wMA |
| SOL | $78.09 | 54.49 | DEEP_VALUE (−39.3%) | **BUY** | MACD bullish (hist +0.53), price above EMA20, 39% discount to 200wMA |
| TON | $1.593 | 47.47 | INSUFFICIENT (only 74 weekly bars) | HOLD | Price below both EMA20 and SMA50; can't compute a valid 200-week MA — zone guard blocks BUY |
| HYPE | $67.791 | 53.00 | INSUFFICIENT (only 36 weekly bars) | HOLD | MACD histogram essentially flat/turning negative; too young for 200wMA — zone guard blocks BUY |
| AAVE | $88.48 | 56.22 | DEEP_VALUE (−46.9%) | **BUY** | MACD bullish, price above EMA20 and at/above SMA50, 47% below 200wMA — deepest discount of the set |
| JUP | $0.2131 | 48.49 | INSUFFICIENT (only 128 weekly bars) | HOLD | Daily MACD bearish (hist −0.0023, MACD below signal); price below SMA50; zone unknown |
| UNI | $3.344 | 66.14 | DEEP_VALUE (−38.2%) | **BUY** | Strongest daily structure in the set: price above both EMA20 and SMA50, MACD bullish, RSI warm (66) but not overbought |
| AERO | $0.53445 | 56.18 | INSUFFICIENT (only 127 weekly bars) | HOLD | Mild bullish MACD but price roughly at SMA50; too young for 200wMA |
| PUMP | $0.001512 | 49.95 | INSUFFICIENT (only 52 weekly bars) | HOLD | MACD bullish cross just forming but price still below both EMA20 and SMA50; down 62% since IPO week |
| LINK | $7.728 | 47.02 | DEEP_VALUE (−42.1%) | HOLD | MACD hist turning positive but price still below both EMA20 ($8.154) and SMA50 ($7.822) — no trend confirmation yet despite deep discount; watch for EMA20 reclaim |

---

## 2. Governor Decision

- Fear & Greed = 22 (Extreme Fear) → cap = **4 active buys**.
- Qualifying BUY setups (zone DEEP_VALUE/FAIR_VALUE, not UNKNOWN, confirmed bullish daily structure — MACD histogram positive AND price above EMA20): **BTC, ETH, SOL, AAVE, UNI = 5 candidates**, one over cap.
- BTC was the weakest of the 5 on the zone-discount dimension (FAIR_VALUE, ~flat vs 200wMA, and still below its daily SMA50) versus the other four, which are all 29–47% below their 200-week MA with confirmed bullish daily MACD/EMA structure. BTC is demoted to **HOLD/watch** so the cap is respected exactly at 4.
- Final governor-approved BUYs: **ETH, SOL, AAVE, UNI** (4/4 slots used).

## 3. Top Picks (with live prices)

| Rank | Token | Price | Discount to 200wMA | Why |
|---|---|---:|---:|---|
| 1 | AAVE | $88.48 | −46.9% | Deepest discount + confirmed bullish daily structure |
| 2 | SOL | $78.09 | −39.3% | Confirmed bullish structure, high-liquidity L1 |
| 3 | UNI | $3.344 | −38.2% | Strongest technical structure (price above both MAs) |
| 4 | ETH | $1,754.47 | −29.0% | Fresh MACD bullish cross, most liquid of the four |

## 4. Per-Token TradingView Data (raw pulls)

| Token | Symbol used | Price | RSI(14) D | MACD / Signal / Hist (D) | EMA20 (D) | SMA50 (D) | SMA200 (Weekly = 200wMA) | Weekly bars available |
|---|---|---:|---:|---|---:|---:|---:|---:|
| BTC | BINANCE:BTCUSDT | 62,948.00 | 49.05 | −638.16 / −1,209.46 / +571.30 | 62,643.98 | 65,699.73 | 62,866.99 | 200 |
| ETH | BINANCE:ETHUSDT | 1,754.47 | 53.11 | 0.10 / −23.83 / +23.93 | 1,718.28 | 1,781.67 | 2,472.43 | 200 |
| SOL | BINANCE:SOLUSDT | 78.09 | 54.49 | 1.92 / 1.38 / +0.53 | 76.85 | 80.26 | 128.72 | 200 |
| TON | KRAKEN:TONUSDT [1] | 1.593 | 47.47 | −0.027 / −0.065 / +0.038 | 2.061 | 1.738 | INSUFFICIENT | 74 |
| HYPE | OKX:HYPEUSDT | 67.791 | 53.00 | 1.609 / 1.612 / −0.003 | 62.325 | 68.511 | INSUFFICIENT | 36 |
| AAVE | BINANCE:AAVEUSDT | 88.48 | 56.22 | 3.40 / 3.33 / +0.07 | 83.85 | 88.43 | 166.63 | 200 |
| JUP | BINANCE:JUPUSDT | 0.2131 | 48.49 | 0.0087 / 0.0109 / −0.0023 | 0.2066 | 0.2336 | INSUFFICIENT | 128 |
| UNI | BINANCE:UNIUSDT | 3.344 | 66.14 | 0.089 / 0.050 / +0.039 | 3.068 | 3.174 | 5.415 | 200 |
| AERO | COINBASE:AEROUSD | 0.53445 | 56.18 | 0.03134 / 0.03063 / +0.00071 | 0.46704 | 0.54444 | INSUFFICIENT | 127 |
| PUMP | OKX:PUMPUSDT | 0.001512 | 49.95 | 0.000007 / −0.000011 / +0.000018 | 0.001569 | 0.001547 | INSUFFICIENT | 52 |
| LINK | BINANCE:LINKUSDT | 7.728 | 47.02 | −0.077 / −0.145 / +0.068 | 8.154 | 7.822 | 13.353 | 200 |

**Data completeness:** 11/11 tokens (100%) got fresh live price/RSI/MACD/EMA20/SMA50 data. 6/11 (BTC, ETH, SOL, AAVE, UNI, LINK) have ≥200 weekly bars → valid 200wMA zone. 5/11 (TON, HYPE, JUP, AERO, PUMP) have <200 weekly bars (36–128) → zone marked INSUFFICIENT/UNKNOWN per the zone guard, signal forced to HOLD regardless of daily technicals. No token failed to return data; the INSUFFICIENT tags reflect genuinely short listing history, not fetch failures.

## 5. Critic (one line per token)

- **BTC** — Textbook 200wMA test; the miss here is treating "at fair value" as tradeable when it's really a coin-flip zone — needs a daily SMA50 reclaim before conviction.
- **ETH** — Bullish MACD cross is one day old; risk is this is a dead-cat bounce inside a still-DEEP_VALUE downtrend that started well above $2,472.
- **SOL** — Technicals line up cleanly, but 39% below 200wMA in extreme fear can still mean-revert lower before it mean-reverts up.
- **TON** — Only 74 weeks of Kraken history (symbol substituted, see note 1) makes the DEEP_VALUE-style read tempting but statistically unsupported — correctly gated to HOLD.
- **HYPE** — Flat MACD histogram (−0.003) is a coin-flip, not a signal; 36 weeks of history is far too short to trust any long-term zone call.
- **AAVE** — Best setup on paper (47% discount + full bullish confirmation), but also the most beaten-down large-cap DeFi name — worth sizing conservatively given no macro catalyst confirmed.
- **JUP** — Bearish MACD and price below SMA50 make this the weakest name in the set; correctly excluded from buys.
- **UNI** — RSI at 66 is the warmest in the table — still under the 70 overbought line, but leaves less room before a pullback than the other three buys.
- **AERO** — Price is basically pinned to its own SMA50 (0.534 vs 0.544) — no real trend signal either way, HOLD is the honest call.
- **PUMP** — Down 62% since its IPO week with only 52 weeks of trading history; a forming MACD cross here is noise until price reclaims EMA20.
- **LINK** — 42% discount to 200wMA is the deepest of the six tokens with valid history, but price is still under EMA20 *and* SMA50 — the zone alone isn't enough to override that structural weakness.

## 6. Citations

1. TON: `OKX:TONUSDT` (as specified in the task) resolved/redirected to `OKX:GRAMUSDT` via TradingView's own symbol handling, and a direct `symbol_search` for `TONUSDT` on 2026-07-09 returned no active OKX listing — substituted `Kraken:TONUSDT` ("TON / Tether USD", confirmed via `mcp__tradingview__symbol_search`) for real, current data instead of using a stale/wrong-asset symbol.
2. Fear & Greed Index value of 22 (Extreme Fear) and the resulting governor cap of 4 active buys were supplied as fixed inputs for this run, per the crypto-advisor skill's zone-guard/governor rules — not independently re-fetched in this session.
3. All price/RSI/MACD/EMA/SMA figures in Sections 1 and 4 were read directly from TradingView's live chart via `quote_get` and `data_get_study_values` (daily and weekly timeframes) on 2026-07-09; 200-week MA values were computed via a weekly-timeframe SMA(200) study, confirmed sufficient only when the underlying weekly bar count (`data_get_ohlcv`) reached 200.
