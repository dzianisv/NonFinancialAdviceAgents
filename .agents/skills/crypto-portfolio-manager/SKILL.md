---
name: crypto-portfolio-manager
description: "Manages the crypto portfolio — runs analysis on every token in the universe (BTC/ETH/SOL/UNI/HYPE/AAVE/LINK) and outputs a BUY/SELL/HOLD decision per token. Run on demand or via /loop. Educational, not advice."
license: MIT
compatibility: opencode
metadata:
  audience: crypto-allocators
  domain: crypto-portfolio-management
  role: portfolio-manager
---

# Crypto Portfolio Manager

Analyze every token in the universe **sequentially** → decide BUY/SELL/HOLD per token → print the signal table.

> Educational analysis, not financial advice. No leverage. Ever.

## Token universe

BTC, ETH, SOL, UNI, HYPE, AAVE, LINK — edit this list to add/remove tokens.

---

## Hard constraints — read before running (these dictate the whole design)

1. **TradingView MCP tools live ONLY in the orchestrator (you).** Subagents spawned via the task tool get a fresh toolset with **no** `tradingview-*` tools — verified. So **YOU** must pull every chart datum yourself. Never tell a subagent to "pull TradingView data" — it cannot. Subagents may only *receive* an already-assembled data package and reason over it (they can still web-fetch F&G / on-chain).
2. **The chart is a single shared symbol slot.** `chart_set_symbol` changes the one global chart, so two tokens cannot be pulled at once. **Therefore the data loop is strictly sequential, one token at a time.** Track progress in the `todos` table so a `/loop` or an interrupted run resumes cleanly.
3. **MCP cannot set MA length.** `chart_manage_indicator` ignores the `length` input (an added EMA stays length-9) and has no `update` action → EMA50/EMA200/SMA200 are unreadable from the chart. **Compute MAs from the MCP's returned OHLCV closes** via `scripts/indicators.py`. RSI(14), Bollinger(20,2), MACD(12,26,9) and Volume *do* read correctly from `data_get_study_values` at their defaults — use those directly.

TradingView symbol mapping: `BINANCE:{TOKEN}USDT` (e.g. `BINANCE:BTCUSDT`). If a symbol is missing on Binance, try `OKX:{TOKEN}USDT`.

---

## Step 0 — Seed the todo list (one row per token)

```sql
INSERT INTO todos (id, title, description) VALUES
 ('tok-BTC','Analyzing BTC','Pull TradingView D/W OHLCV+studies, compute pkg, run 5-seat quorum, decide signal'),
 ('tok-ETH','Analyzing ETH','idem'), ('tok-SOL','Analyzing SOL','idem'),
 ('tok-UNI','Analyzing UNI','idem'), ('tok-HYPE','Analyzing HYPE','idem'),
 ('tok-AAVE','Analyzing AAVE','idem'), ('tok-LINK','Analyzing LINK','idem');
```

Create the verdict tracker once:

```sql
CREATE TABLE IF NOT EXISTS token_analysis (
  symbol TEXT PRIMARY KEY, quorum_verdict TEXT, dominant_zone TEXT,
  seats_bull INTEGER, seats_bear INTEGER, key_support REAL, key_resistance REAL,
  confidence TEXT, signal TEXT, status TEXT DEFAULT 'pending');
```

---

## Step 1 — Sequential per-token loop (orchestrator does this; do NOT parallelize the data pull)

Pick the next `pending` todo and `UPDATE todos SET status='in_progress'`. Then, for that token:

**1a. Pull TradingView data (MCP, in this session):**
```
tradingview-chart_set_symbol     symbol="BINANCE:{TOKEN}USDT"
tradingview-chart_set_timeframe  timeframe="D"
tradingview-data_get_ohlcv       count=365 summary=true   → 52w high/low + avg volume
tradingview-data_get_ohlcv       count=210 summary=false  → >=200 daily closes (for SMA200)
tradingview-data_get_study_values                          → RSI(14), BB(20,2), MACD, Volume (defaults are correct)
tradingview-chart_set_timeframe  timeframe="W"
tradingview-data_get_ohlcv       count=210 summary=false  → weekly closes (for 200-week MA)
tradingview-chart_set_timeframe  timeframe="D"             → reset
```
Add the RSI / Bollinger Bands / MACD studies once at the start via `chart_manage_indicator action=add`. Do NOT add length-N EMAs — the length input is ignored (constraint 3).

**1b. Compute the moving averages from the returned closes** (computed MAs match TradingView's own values):
```bash
/Users/engineer/.venv/bin/python3 .agents/skills/crypto-portfolio-manager/scripts/indicators.py /tmp/{TOKEN}.json
```
Input JSON shape: `{"symbol","daily_closes":[...],"weekly_closes":[...],"hi52","lo52","vol_last","vol_avg30"}`. Death cross is the classic SMA50/SMA200 (exact, no warmup error).

**1c. Assemble the data package** (merge 1a study values + 1b computed MAs): price, %from-52wh, EMA20, SMA50, SMA200, death_cross, RSI, MACD line/signal/hist, BB upper/mid/lower + position, volume vs 30d avg, 200-week MA + %vs it.

**1d. Run the 5-seat quorum on the package.** Either reason through the 5 seats inline, or spawn the five `analysis-*` seat subagents **in parallel** (on-chain, sentiment, macro, order-flow, narrative) with the package **injected** — seats per token may be parallel because they share nothing; only the *data pull* must be serial. Each seat returns: zone, posture (BULLISH|NEUTRAL|BEARISH), confidence, 1-line bull, 1-line bear, invalidation.

**1e. Aggregate into the compact verdict and persist:**
```json
{"symbol":"BTC","quorum_verdict":"BULLISH|SPLIT|BEARISH|UNCERTAIN",
 "dominant_zone":"DEEP_VALUE|FAIR_VALUE|ELEVATED|EXTREME|UNKNOWN",
 "seats_bull":3,"seats_bear":2,"key_support":60000,"key_resistance":66000,"confidence":"HIGH|MED|LOW"}
```
```sql
UPDATE token_analysis SET quorum_verdict=?, dominant_zone=?, seats_bull=?, seats_bear=?,
  key_support=?, key_resistance=?, confidence=?, signal=?, status='done' WHERE symbol=?;
UPDATE todos SET status='done' WHERE id='tok-{TOKEN}';
```

**1f. Repeat** for the next `pending` todo until none remain.

---

## Step 2 — Decide per token

| Signal | Condition |
|---|---|
| **BUY** | `quorum_verdict = BULLISH`, seats_bull ≥ 3 |
| **BUY (small)** | `quorum_verdict = SPLIT`, `dominant_zone = DEEP_VALUE` |
| **SELL** | `quorum_verdict = BEARISH`, seats_bear ≥ 4 |
| **HOLD** | everything else |

## Step 3 — Print signal table

```
=== PORTFOLIO RUN — {timestamp} ===   (data: TradingView MCP)

Token | Quorum    | Zone       | Signal
------|-----------|------------|------------
BTC   | SPLIT     | FAIR_VALUE | HOLD
ETH   | UNCERTAIN | DOWNTREND  | HOLD
SOL   | SPLIT     | DEEP_VALUE | BUY (small)
...
```

Self-check before printing: every token has `status='done'` in both `todos` and `token_analysis`, and `seats_bull + seats_bear <= 5` for each.

## Running continuously

```
/loop interval=6h
/stop
```

On each loop, re-seed any `pending`/missing todos and resume the sequential pull — never start a second data pull while one is in flight.
