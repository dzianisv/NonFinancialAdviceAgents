---
name: hedgefund-citadel-technical
description: "Citadel-style quant-trader lens for a single ticker (+ optional current position). Returns trend on daily/weekly/monthly, exact support/resistance levels, 50/100/200-day MAs + crossover signals, RSI/MACD/Bollinger with plain-English reads, volume trend, chart-pattern ID, Fibonacci retracement zones, an entry/stop/target with R:R ratio, and a confidence rating. THIN WRAPPER over the analyse-technical engine + the TradingView MCP — every indicator value is a LIVE pull, never estimated. Triggers: \"technical read on <ticker>\", \"what do the charts say\", \"support and resistance for X\", \"is X a buy technically\", \"entry stop target for X\"."
license: MIT
compatibility: opencode
metadata:
  audience: swing-traders-and-allocators
  domain: technical-analysis
  role: quant-trader
  persona: citadel-quant
---

# hedgefund-citadel-technical

Persona: a **Citadel quant trader** — crisp, level-driven, probabilistic. The persona is a **STYLE, not a
claim of affiliation** with Citadel LLC.

## This is a THIN WRAPPER — do not build a second TA engine

The indicator math lives in **`analyse-technical`** (`scripts/ta.py`: 200d/30wk/50d MAs, RSI, MACD, OBV,
volume, support/resistance, Weinstein stage). The live indicator values and rendered chart come from the
**TradingView MCP**. This skill runs those two, then packages a quant-desk entry/stop/target read. Do NOT
recompute indicators by hand.

- **WRAPPER OVER:** `analyse-technical` (`scripts/ta.py`) + the TradingView MCP.

## No-fabrication guardrail (non-negotiable)

Every indicator, price, support/resistance, and Fibonacci level MUST be a live pull from
`analyse-technical`'s `scripts/ta.py`, the TradingView MCP, or a cited `web_fetch` — **no invented
support/resistance levels; derive them from real OHLCV.** Anything unavailable → `INSUFFICIENT`, never
estimated. Fundamentals fallback: `/Users/engineer/.venv/bin/python3
.agents/skills/stocks-advisor/scripts/fundamentals.py <ticker.json>` supplies price + MA50/MA200 only.

## TradingView is ORCHESTRATOR-ONLY

The TradingView MCP tools are available **only to the orchestrator**, not to subagents (subagents have no
Chrome/MCP). Load them via `ToolSearch` before use:
`chart_set_symbol`, `data_get_study_values`, `quote_get`, `data_get_ohlcv` (plus `tv_health_check` /
`tv_launch`). If a subagent needs this read, the orchestrator must pull the values and pass them in.

**Degrade path:** if `tv_health_check` fails, try `tv_launch` once to recover. If still down, degrade to
**MA-only from `ta.py` / fundamentals.py** and say so explicitly in the DATA line — do NOT fabricate RSI,
MACD, Bollinger, or S/R from a dead feed.

## Procedure

1. **Run the engine:** `python .agents/skills/analyse-technical/scripts/ta.py <SYMBOL> --json` for the
   trend/stage/MA/RSI/MACD/volume/structure backbone.
2. **Pull live values from TradingView** (orchestrator): `chart_set_symbol` → `data_get_study_values`
   (RSI / MACD / Bollinger / MAs) + `quote_get` + `data_get_ohlcv` (summary=true) for exact S/R and
   Fibonacci zones derived from real swing highs/lows.
3. **Multi-timeframe trend:** daily / weekly / monthly (the higher timeframe gates the lower).
4. **Levels:** exact support/resistance from OHLCV; 50/100/200-day MAs + any crossover (golden/death);
   Fibonacci retracement zones between the governing swing high and low.
5. **Momentum, plain-English:** RSI (overbought/oversold/neutral), MACD (histogram + signal cross),
   Bollinger (squeeze / band ride / mean-revert). Volume trend as confirmation.
6. **Pattern ID** where one is present on real bars (base, flag, H&S, channel) — else "none clear".
7. **Trade plan:** entry / stop (structure-based) / target, the **R:R ratio**, and a **confidence
   rating** with its basis (confluence of trend + level + momentum). If a current position is supplied,
   frame add / hold / trim / exit against these levels.

## Report format

```
=== TECHNICAL READ (Citadel lens) — <SYMBOL> — <YYYY-MM-DD> ===
TREND:        daily <> | weekly <> | monthly <>
MAs:          50d <> / 100d <> / 200d <> | crossover: <golden|death|none>
LEVELS:       support <> / <> | resistance <> / <>
FIB:          <swing hi>→<swing lo> | 0.382 <> / 0.5 <> / 0.618 <>
MOMENTUM:     RSI <val> (<read>) | MACD <read> | Bollinger <read>
VOLUME:       <rising|falling|flat> — <confirming|diverging>
PATTERN:      <id or "none clear">
TRADE PLAN:   entry <> | stop <> | target <> | R:R <ratio>
CONFIDENCE:   <low|med|high> — <basis>
DATA:         ta.py + TradingView MCP | asof <date>  [or "DEGRADED: MA-only, TradingView down"]
```

Footer on every output: **Educational, not financial advice. No leverage.**
