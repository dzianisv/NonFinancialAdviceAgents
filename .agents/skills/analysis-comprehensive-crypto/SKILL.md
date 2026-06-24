---
name: analysis-comprehensive-crypto
description: "Full-stack crypto analysis orchestrator — pulls live price/indicator data via TradingView MCP tools across multiple timeframes, then spawns all five analysis seats (analysis-onchain, analysis-sentiment, analysis-macro, analysis-orderflow, analysis-narrative) as parallel subagents, and synthesizes their verdicts into a quorum brief: zone, posture, key tensions, and the one dominant risk. Use when asked to do a complete crypto analysis, 'full analysis of BTC', 'comprehensive read', 'what does everything say', 'run the panel', or 'multi-lens crypto brief'. Requires TradingView MCP + Chrome CDP on port 9222. Educational, not advice."
license: MIT
compatibility: opencode
metadata:
  audience: crypto-allocators-and-active-traders
  domain: crypto-comprehensive-analysis
  role: orchestrator
  source: "TradingView MCP + analysis-* panel (distilled 2026-06)"
---

# analysis-comprehensive-crypto (the full-stack orchestrator)

Pull live data from TradingView MCP, distribute it to five specialist analysis seats running in parallel,
then synthesize their fixed-shape verdicts into a single quorum brief. The seats disagree with each other
on purpose — the spread is the signal.

**Prerequisite:** Chrome must be running with `--remote-debugging-port=9222` and TradingView open.
If CDP fails, run:
```bash
mkdir -p /tmp/chrome-cdp-profile && nohup /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-cdp-profile --no-first-run \
  "https://www.tradingview.com/chart/?symbol=BTCUSDT" > /tmp/chrome-cdp.log 2>&1 &
sleep 10
```

---

## Step 1 — Pull TradingView data (do this BEFORE spawning subagents)

Call these TradingView MCP tools to collect the raw data package. Make ALL calls in parallel.

### Symbol + state
```
tradingview-chart_set_symbol   symbol="BINANCE:BTCUSDT"
tradingview-chart_get_state    → symbol, resolution, studies list
```

### Price data — three timeframes
```
tradingview-chart_set_timeframe  timeframe="D"
tradingview-data_get_ohlcv       count=100  summary=true   → daily OHLCV + last 5 bars
tradingview-chart_set_timeframe  timeframe="W"
tradingview-data_get_ohlcv       count=52   summary=true   → weekly OHLCV + last 5 bars
tradingview-chart_set_timeframe  timeframe="240"
tradingview-data_get_ohlcv       count=60   summary=true   → 4H OHLCV + last 5 bars
```
Reset to Daily after: `tradingview-chart_set_timeframe timeframe="D"`

### Indicators — add if missing, read values
Add these via `tradingview-chart_manage_indicator` (action=add) if not already present:
- `"Relative Strength Index"` — RSI(14)
- `"Moving Average Convergence Divergence"` — MACD(12,26,9)
- `"Bollinger Bands"` — BB(20,2)
- `"Volume"` — already present by default

Then read:
```
tradingview-data_get_study_values   → current values for all visible indicators
tradingview-chart_get_state         → entity_id list for indicators
```

### Screenshot (optional but useful)
```
tradingview-capture_screenshot   → save to /tmp/btc_analysis.png
```

### Assemble the data package

After pulling, compute the following from OHLCV bars in Python (if study_values doesn't return indicator values):

```python
# RSI(14), MACD(12,26,9), BB(20,2), EMA20/50/200
# Key levels: 52w high/low, current vs EMA20/50/200
# Volume: current vs 30d avg
```

Format the data package as a structured block — this gets injected verbatim into every subagent prompt:

```
BTCUSDT DATA PACKAGE — {timestamp}
Price:        $XX,XXX (+X.X%)
52w High:     $XX,XXX  ({X}% from ATH)
52w Low:      $XX,XXX
Daily OHLC:   O={} H={} L={} C={}
Weekly OHLC:  O={} H={} L={} C={}
EMA20:        $XX,XXX  (price is ABOVE/BELOW)
EMA50:        $XX,XXX  (price is ABOVE/BELOW)
EMA200:       $XX,XXX  (price is ABOVE/BELOW)
RSI(14):      {value}
MACD:         line={} signal={} hist={} (BULLISH/BEARISH)
BB(20,2):     upper={} mid={} lower={} (price in {zone})
Volume:       {current} vs {30d avg} ({+/-X}% vs avg)
```

---

## Step 2 — Spawn the five analysis seats in parallel (subagents)

Spawn **five subagents simultaneously**, each reading exactly one analysis skill and judging the same
question on the identical data package. Do NOT run them sequentially.

**The shared question for all seats:**
> "Given this data package for BTCUSDT, what is your analysis? State: (1) your zone/posture verdict,
> (2) your confidence level HIGH/MED/LOW, (3) the single biggest bullish signal from your lens,
> (4) the single biggest bearish signal from your lens, (5) what would change your verdict."

**Seat assignments:**

| Seat | Skill | Focus |
|---|---|---|
| On-chain | `analysis-onchain` | MVRV-Z, NUPL, realized price, Puell, LTH behavior |
| Sentiment | `analysis-sentiment` | F&G index, funding rates, long/short ratio, social volume |
| Macro | `analysis-macro` | GLI direction, Fed liquidity, DXY, M2, halving cycle, ETF flows |
| Order Flow | `analysis-orderflow` | OI, liquidation clusters, CVD, CME gap, spot vs perp |
| Narrative | `analysis-narrative` | Latest catalysts, ETF flow news, regulatory state, dominant story |

**Subagent prompt template (inject data package + seat assignment):**
```
You are the {SEAT_NAME} analysis seat.

Load skill: analysis-{seat}

DATA PACKAGE:
{data_package}

QUESTION: {shared_question}

Return a fixed-shape verdict:
{
  "seat": "{seat}",
  "zone": "DEEP_VALUE | FAIR_VALUE | ELEVATED | EXTREME | UNKNOWN",
  "posture": "BULLISH | NEUTRAL | BEARISH",
  "confidence": "HIGH | MED | LOW",
  "bull_signal": "...",
  "bear_signal": "...",
  "invalidation": "..."
}
Then 2–4 sentences of supporting reasoning.
```

Each seat should also call its own data-fetch tools (on-chain script, F&G API, liquidity data, etc.)
to supplement the TradingView data with its domain-specific live metrics.

---

## Step 3 — Synthesize the quorum

Collect all five verdict blocks. Then produce the synthesis:

### Quorum table
| Seat | Zone | Posture | Confidence | Key bull | Key bear |
|---|---|---|---|---|---|
| On-chain | … | … | … | … | … |
| Sentiment | … | … | … | … | … |
| Macro | … | … | … | … | … |
| Order Flow | … | … | … | … | … |
| Narrative | … | … | … | … | … |

### Consensus extraction rules
- **Strong consensus (4–5 agree):** state it plainly. This is the signal.
- **Split (3–2):** name both camps and which lenses are in each. Do NOT average — preserve the dissent.
- **Full disagreement:** diagnose why the lenses diverge (usually: short-term vs long-term horizon, or data lag). State the dominant risk.
- **Never manufacture a blended non-view.** "Cautiously optimistic with some concerns" is not a synthesis.

### Final brief format

```
=== BTCUSDT COMPREHENSIVE ANALYSIS — {date} ===

PRICE: ${price} ({change}%)

QUORUM VERDICT: {BULLISH / SPLIT / BEARISH / UNCERTAIN}
DOMINANT ZONE:  {zone}  (N/5 seats agree)

CONSENSUS:
  {1–2 sentences on what the majority of seats see}

DISSENT:
  {which seat(s) disagree and why — this is often the most important line}

TOP BULL SIGNAL: {the single most compelling bullish data point across all seats}
TOP BEAR SIGNAL: {the single most compelling bearish data point across all seats}

DOMINANT RISK:  {the one thing most likely to invalidate the consensus}
INVALIDATION:   {what price/event would flip the majority verdict}

KEY LEVELS:
  Resistance: ${level} ({reason})
  Support:    ${level} ({reason})

SEAT POSTURES:  on-chain={} sentiment={} macro={} orderflow={} narrative={}
```

---

## Routing table

| Question type | What to do |
|---|---|
| Full analysis ("comprehensive read") | Run full Steps 1–3 |
| Single lens ("what does on-chain say?") | Spawn only that seat with TradingView data |
| Pure price/chart question | TradingView MCP only — no panel needed |
| Buy/sell/allocation decision | After this analysis, route to [[crypto-desk]] or [[multi-lens-quorum]] |
| Historical backtesting | Route to [[strategy-discovery-backtest]] |

---

## Hard rules

- **Always pull live TradingView data first** — never analyze stale or recalled prices.
- **All five seats spawn in parallel** — sequential execution defeats the purpose.
- **Preserve disagreement** — a 3-bull / 2-bear split is more informative than a blended neutral.
- **No buy/sell call** — this skill produces a zone + posture; [[crypto-desk]] turns it into a sizing decision.
- **Mark data gaps loudly** — if a seat returns `[UNAVAILABLE]` metrics, note it in the brief; don't silently skip.
- **TradingView MCP requires Chrome CDP on port 9222** — if connection fails, launch Chrome first (see top).

---

## Done when

(1) TradingView data package is assembled with prices, EMAs, RSI, MACD, BB across at least Daily timeframe.
(2) All five seats have returned verdict blocks (or are marked `[UNAVAILABLE]` with reason).
(3) The synthesis quorum table is produced.
(4) The final brief is printed with: quorum verdict, consensus, dissent, top bull/bear signal, dominant risk, key levels.
