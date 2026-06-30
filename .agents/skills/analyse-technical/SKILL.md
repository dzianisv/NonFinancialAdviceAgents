---
name: analyse-technical
description: A disciplined technical-analysis lens for TIMING LONG-TERM / SWING ENTRIES on daily/weekly charts — trend & stage (Weinstein Stage 1-4), the 200-day / 30-week trend filter, entry zones (pullback to a rising MA, base breakouts, support/resistance), with RSI/MACD/volume as CONFIRMATION (never standalone triggers) and multi-timeframe confluence where the weekly trend gates the daily entry. Works for stocks AND crypto; computes all indicators via `scripts/ta.py` (yfinance/ccxt, no Chrome) and emits a structured trend/structure/momentum/verdict read with a structure-based invalidation level. Use when the user asks "is now a good entry", "should I buy here or wait", "where do I accumulate", "what's the entry zone", "is this a good level to add", "pullback or breakout", "is the trend up", "what stage is this in", "should I buy this pullback", "where do I put my accumulation zone", or "is this a base breakout". NOT for intraday day-trading (use `investor-bernstein-intraday`) and NOT for crypto on-chain valuation (use `analyse-onchain-lens`). Educational, not advice; a lens, not gospel — TA has a weak/mixed empirical base, validate with backtests via `analyse-systematic-trading` before sizing.
license: MIT
compatibility: opencode
metadata:
  audience: long-term-investors-and-swing-traders
  domain: technical-analysis-entry-timing
  role: long-term-swing-entry-timing-lens
  source: "Public technical-analysis frameworks — Weinstein stage analysis, Grimes (evidence-based), Murphy (CMT canon); summarized, not verbatim-distilled."
---

# Research: The Long-Term Entry-Timing Lens (Technical Analysis)

This lens **TIMES entries for positions you intend to HOLD**. It is the daily/weekly counterpart to the
intraday `investor-bernstein-intraday` skill: where that skill executes sub-daily day-trades, this one
answers a slower question — *given that you already want to own this for fundamental/macro reasons, is
NOW a good level to start a position, or should you wait for a better one?* It reads the **trend and
Weinstein Stage**, finds the **entry zone / structure**, demands **momentum & volume CONFIRMATION**, and
states a **verdict + entry zone + structure-based invalidation level**.

> **For intraday / day-trading execution, use `investor-bernstein-intraday`. This skill is long-term/swing entry timing only.**

## What this lens does

**Times entries for positions you intend to HOLD.** It does **NOT** judge valuation (that is fundamental
analysis / `multi-lens-quorum`) and it does **NOT** day-trade (`investor-bernstein-intraday`). It answers
one narrow question: **accumulate now / buy this zone / wait for a pullback / wait for a breakout / avoid
(downtrend).** It always **times a decision already justified on fundamentals/macro** — TA is not
standalone alpha here. Use it to *improve the entry* on something you already want to own, never as the
sole reason to buy.

## The engine — run the script FIRST

Run the script, **then** interpret its output. The script pulls **daily + weekly OHLCV** from yfinance
(stocks) / ccxt (crypto), computes the indicators (200d/30wk/50d MAs and slopes, RSI(14) daily+weekly,
MACD(12,26,9), OBV, volume-vs-20avg, support/resistance distances, Weinstein Stage), and prints a
verdict you then reason over.

**Hard rule: never eyeball or recall prices — the script is the single source of truth.** If it cannot
fetch (e.g. the network is down), it prints `DATA: DEGRADED` and lists which fields are missing. In that
case you must **NOT fabricate any price or indicator value** — degrade loudly, report exactly which
fields are unavailable, and stop short of a confident verdict.

```bash
# stocks
python .agents/skills/analyse-technical/scripts/ta.py AAPL
python .agents/skills/analyse-technical/scripts/ta.py AAPL --json

# crypto
python .agents/skills/analyse-technical/scripts/ta.py BTC --asset crypto
python .agents/skills/analyse-technical/scripts/ta.py BTC --asset crypto --json
```

Flags: `--asset auto|stock|crypto` (default `auto` — infers from the symbol), `--json` (machine-readable
output for piping into a report). No Chrome and no TradingView are required.

## TradingView (optional, charts only)

**The SCRIPT does the analysis.** The TradingView MCP is **OPTIONAL** and used **ONLY** when the
deliverable needs a rendered chart IMAGE for a report (`tradingview-capture_screenshot`). Funding rate
and open interest come from **ccxt inside the script**, NOT from TradingView. **Do not make the analysis
depend on Chrome** — if TradingView is unavailable, the read is still complete from the script alone.

## The four reads (in order)

A layered method — work top-down; each read points to a reference file. The higher read gates the lower:
a great-looking entry zone in a Stage-4 downtrend is still an AVOID.

1. **Trend & Stage** — Weinstein **Stage 1 basing / 2 advancing / 3 topping / 4 declining**; the 200-day
   & 30-week MA and their slopes. Only buy in **late Stage 1** (a completed base) or **Stage 2** (a
   confirmed advance). → `references/01-trend-and-stage.md`
2. **Entry zone & structure** — support/resistance, a pullback to a **rising** 50/200d MA, a base
   breakout on **expanding volume**, and multi-timeframe confluence where the **weekly trend gates the
   daily entry**. → `references/02-entry-zones-and-structure.md`
3. **Momentum & volume CONFIRMATION** — RSI(14) daily/weekly regime + divergence; MACD(12,26,9); OBV /
   volume. These **CONFIRM** the trend/structure read; they are **NOT standalone triggers**. Don't buy a
   weekly-overbought tape. → `references/03-momentum-and-volume-confirmation.md`
4. **Asset-class specifics** — **stocks:** relative strength vs SPX/sector, base patterns, earnings-gap
   caution; **crypto:** the 4-year halving-cycle stage on the weekly, funding rate & open interest as
   froth gauges, 24/7 = no session gaps. Cross-ref `analyse-onchain-lens` for MVRV/NUPL/realized-price
   VALUATION, which lives THERE, not here. → `references/04-asset-class-stocks-and-crypto.md`

## Decision procedure

1. **Run the script:** `python .agents/skills/analyse-technical/scripts/ta.py {SYMBOL} [--json]`.
2. **Read Stage.** Stage 4 (declining) → **AVOID-DOWNTREND.** Stage 3 (topping) → no new entries; tighten
   stops on anything held.
3. **Locate price vs entry zone / structure** — is price in a base, pulling back to a **rising** MA, or
   extended far above it?
4. **Require momentum / volume CONFIRMATION** — RSI not weekly-overbought, MACD histogram consistent with
   the trend direction, volume confirming (expansion on a breakout, contraction on a healthy pullback).
5. **State the verdict + entry zone + INVALIDATION level** — structure-based (below the base / swing low
   / key MA), **never an arbitrary dollar figure**.
6. **Apply the honesty overlay** — this is a *timing hypothesis*, not a validated edge.
7. **Route to `analyse-systematic-trading`** to validate the entry rule before sizing; pair with
   `regime-detection` + `risk-management`.

## Routing table

| Question is about… | Load |
|---|---|
| **Trend, Weinstein stages, 200d/30wk MA** | **`references/01-trend-and-stage.md`** + run `scripts/ta.py` |
| Entry zones, support/resistance, base breakouts, invalidation levels | `references/02-entry-zones-and-structure.md` |
| RSI, MACD, OBV, volume confirmation | `references/03-momentum-and-volume-confirmation.md` |
| Stock-specific: relative strength, base patterns, earnings gaps | `references/04-asset-class-stocks-and-crypto.md` |
| Crypto-specific: halving cycle, funding rate, OI, 24/7 | `references/04-asset-class-stocks-and-crypto.md` |
| Crypto on-chain VALUATION (MVRV, NUPL, realized price) | → `analyse-onchain-lens` (not this skill) |
| Day-trading / intraday execution | → `investor-bernstein-intraday` (not this skill) |
| Validate an entry rule before sizing | → `analyse-systematic-trading` |
| Risk-on / risk-off regime check | → `regime-detection` |
| Position sizing / drawdown rules | → `risk-management` |

## Example

<example>
User: "BTC pulled back to its rising 200-day after a Stage-2 advance — is this a good level to accumulate or should I wait?"

Lens response:
1. Run `python .agents/skills/analyse-technical/scripts/ta.py BTC --asset crypto`
2. **Stage read**: Weekly 30wk-MA is rising, price above 200d MA — confirmed Stage 2 (advancing). No AVOID-DOWNTREND signal.
3. **Structure**: Price is at a pullback to the rising 200d MA (classic first-test entry zone), not extended. The 200d MA is structural support; a daily close back above the 5-day MA after this touch confirms the pullback ended.
4. **Confirmation**: RSI(14) daily pulled back toward 52 (above 50, healthy). MACD histogram turning up from below — early momentum confirmation. Daily volume on the pullback below average (healthy; sellers not aggressive). OBV holding its rising trend — accumulation confirmed.
5. **Verdict**: **ACCUMULATE** — Stage-2 pullback to rising 200d MA, rsi_w below 70, and OBV rising (confirmation present) → highest-conviction add.
6. **Entry zone**: current 200d MA level ±2% — accumulate in tranches.
7. **Invalidation**: daily close meaningfully (>3%) below the 200d MA and MA rolling over → pullback became a Stage 3/4 change → stop and re-evaluate.
8. Cross-ref `analyse-onchain-lens` for on-chain valuation (MVRV, NUPL) before sizing — this lens is price/volume only.

```
=== ENTRY READ — BTC (crypto) — 2026-06-29 ===
Horizon:     position/swing — weekly trend gates the daily entry
Price:       64210.00
TREND/STAGE: Weekly Stage 2 (advancing) | 200d above, MA rising | 30wk-MA slope up
STRUCTURE:   support 63800.00 / resistance 72000.00 | dist 50d -2.6% / 200d 2.1% | in base
MOMENTUM:    RSI14 D=52.0 W=58.0 (neutral) | MACD(12,26,9) hist rising, above zero | div none
VOLUME:      OBV rising | last vol 0.7x20avg | accumulation
CONFLUENCE:  weekly trend AGREES with the daily setup
VERDICT:     ACCUMULATE 63800.00
ENTRY ZONE:  63200.00–64800.00
INVALIDATION:62400.00 — sustained close beyond = thesis wrong
NOTES:       funding 0.0100%, OI rising
HONESTY:     Lens, not gospel. TA evidence base is weak/mixed; validate via analyse-systematic-trading before sizing.
DATA:        coinbase/ccxt | asof 2026-06-29
```
</example>

## Output format

Emit EXACTLY this schema (reproduce character-for-character, including spacing and field labels):

```
=== ENTRY READ — {SYMBOL} ({stock|crypto}) — {YYYY-MM-DD} ===
Horizon:     position/swing — weekly trend gates the daily entry
Price:       {last}
TREND/STAGE: Weekly Stage {n} ({basing|advancing|topping|declining}) | 200d {above|below}, MA {rising|falling} | 30wk-MA slope {up|flat|down}
STRUCTURE:   support {} / resistance {} | dist 50d {x%} / 200d {x%} | {in base|breakout|extended}
MOMENTUM:    RSI14 D={} W={} ({label}) | MACD(12,26,9) hist {rising|falling}, {above|below} zero | div {none|bullish|bearish}
VOLUME:      OBV {rising|falling|flat} | last vol {x}x20avg | {accumulation|distribution|neutral}
CONFLUENCE:  weekly trend {AGREES|CONFLICTS} with the daily setup
VERDICT:     {verdict} {level}
ENTRY ZONE:  {low}–{high}
INVALIDATION:{level} — sustained close beyond = thesis wrong
NOTES:       {crypto: funding {x%}, OI ...; stock: rel-str vs SPY ...}
HONESTY:     Lens, not gospel. TA evidence base is weak/mixed; validate via analyse-systematic-trading before sizing.
DATA:        {yfinance | coinbase/ccxt | ...} | asof {YYYY-MM-DD}{ | DEGRADED: ...}
```

`{verdict}` is exactly one of the engine's five: **`ACCUMULATE`** (Stage 2, near support, RSI_W < 70,
OBV rising or bullish divergence) · **`BUY-ZONE`** (same, confirmation mixed/absent) ·
**`WAIT-PULLBACK {level}`** (Stage 3, or Stage 2 extended >15% above the rising 50d, or Stage 2
RSI_W ≥ 70 — `{level}` = the 50d/support to wait for) · **`WAIT-BREAKOUT {level}`** (Stage 1 — `{level}`
= resistance) · **`AVOID-DOWNTREND`** (Stage 4). `{level}` on the VERDICT line is the engine's
numeric `level` field.

## Honesty rules (non-negotiable)

- **It's a lens, not gospel.** Present it as "technical analysis says…", never as fact.
- **TA has a weak / mixed empirical base.** Trend-following is the ONE TA family that robustly survives
  backtesting; most other TA has weak or mixed evidence.
- **This skill times a decision already justified on fundamentals/macro.** TA is not standalone alpha —
  use it to IMPROVE ENTRIES on positions you already want to own for fundamental/macro reasons.
- **Route to `analyse-systematic-trading`** for walk-forward validation with full costs before sizing.
- **Pair with `regime-detection` + `risk-management`.** In a Stage-4 decline or a risk-off regime, no
  technical entry looks good enough to overcome the headwind.
- **The repo house finding: hold / mid-risk beats trading after costs.** Use TA to time a hold decision,
  not as a trading system.
- **Never fabricate prices or indicator values.** If the script is unavailable, mark `DATA: DEGRADED`
  loudly.

## Done when

The analysis (0) **ran `scripts/ta.py` and interpreted its output** (or marked `DATA: DEGRADED` without
fabricating), (1) **identified the Weinstein Stage** and immediately discarded Stage 4 as AVOID, (2)
**located price vs entry zone / structure** (pullback-to-MA, base, breakout, extended), (3) **verified
momentum/volume CONFIRMATION** (RSI not weekly-overbought, MACD consistent, volume confirming), (4)
**stated the verdict + entry zone + structure-based INVALIDATION level**, (5) emitted the **structured
output block** verbatim, and (6) flagged it as an unvalidated timing hypothesis to be validated in
`analyse-systematic-trading` before sizing.
