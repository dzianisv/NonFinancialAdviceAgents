---
name: investor-bernstein-intraday
description: Execute intraday day-trades in stocks, forex, and commodities using Jacob Bernstein's *The Ultimate Day Trader* (2009) method — classify the Set-Up, wait for the bar-close Trigger, manage Follow-Through. Exact non-standard params: 10/8 Moving Average Channel (SMA of highs/lows), 28-period Momentum, MACD 9/18 line-only, 9-period slow stochastic 30/70, 16-bar breakout, gap/Oops, 30-min opening-range breakout, volume spikes (4×). Strictly SHORT-TERM execution — not for long-term or swing entry timing (use `research-technical` for that). Use when the user asks "where do I put my stop", "day trading setup", "momentum divergence", "should I buy this breakout", "what's the trigger", "how do I size and scale out". Fetches live OHLCV from TradingView MCP and computes Bernstein's exact params, then emits a structured set-up/trigger/stop/target/size read. Educational, not advice; a lens, not gospel — TA has a weak/mixed empirical base, validate with backtests.
license: MIT
compatibility: opencode
metadata:
  audience: day-traders-and-short-term-executors
  domain: intraday-day-trading-execution
  role: intraday-day-trading-execution-lens
  source: "Jacob Bernstein, The Ultimate Day Trader (2009) + canonical TA texts (distilled 2026-06-07)"
---

# Investor: Bernstein's Intraday Day-Trading Lens

Execute intraday day-trades using the disciplined method from **Jacob Bernstein, *The Ultimate Day
Trader* (2009)**. This skill is the **short-term execution seat** — the synthesis + router for
*when and how to enter and exit a day-trade*, not long-term valuation or position timing. It classifies
the Set-Up, waits for the bar-close Trigger, places a market-based stop, and manages Follow-Through
across multiple units. The detail and exact indicator parameters live in `references/`; load them before
any load-bearing claim, and route all validation to `analyst-systematic-trading`.

> **⚠ SCOPE: INTRADAY / SHORT-TERM EXECUTION ONLY.**
> For **long-term / swing / position entry timing on daily/weekly charts**, use **`research-technical`**
> instead. This skill is strictly intraday day-trading execution — Set-Up→Trigger→Follow-Through on
> sub-daily bars.
>
> **⚠ REPO HONESTY:** The fund's house finding is that **hold / mid-risk beats day-trading after
> costs**. Use this lens for **idea generation and hypothesis formation**, not as validated alpha. Any
> setup must clear `analyst-systematic-trading` (walk-forward, full costs) before real capital is
> risked.

## The unifying worldview (everything connects to this)

TA is **the measurement of crowd behavior**. Bernstein: technical analysis is about "measuring and
describing the behavior and the consistency of behavior of a crowd" — you "fit a pattern to the
collective buying and selling behavior" of market participants. Most intraday moves are *emotion and
news reaction*; the edge is exploiting overreaction **objectively**, never interpreting the news itself.
Success demands **structure + objectivity**, expressed as a repeatable three-step sequence: **Set-Up**
(a historically verifiable pattern) → **Trigger** (a timing signal confirming price is doing what the
set-up predicts) → **Follow-Through** (trade management and exit — the most important and least
mechanical step). Entries should be **100% mechanical** ("no trigger, no trade"); exits are
deliberately *not* fully mechanical. "They are tools; you are the trader" — and "the trader is the
weakest link in the chain." Realism rules: day trading is "a low-accuracy venture", so the spine is
**risk control and management of losses**, not prediction.

## Core mental models (the load-bearing ones)

1. **TA = measuring crowd behavior.** Patterns describe the consistency of a crowd, not fundamentals.
   → `references/01-philosophy-and-stf.md`
2. **Set-Up → Trigger → Follow-Through (STF).** The master sequence; Follow-Through matters most.
   → `references/01-philosophy-and-stf.md`
3. **Method, not System; mechanical entries, judged exits.** "This book is not about trading systems."
   → `references/01-philosophy-and-stf.md`
4. **Leading vs lagging indicators.** Momentum/MACD divergence lead; MA crossovers/stochastics lag.
   → `references/02-setups-and-indicators.md`
5. **The named set-ups with exact parameters.** Gap, 30-min breakout, 10/8 MAC, volume spikes,
   28-Momentum/MACD-9-18 divergence, 9-period stochastic POP, 16-bar trend breakout.
   → `references/02-setups-and-indicators.md`
6. **The bar-close trigger rule.** A trigger is valid only at the *end* of a bar; never anticipate.
   → `references/03-entry-trigger-and-exit.md`
7. **Market-based stops.** Stops come from range/volatility/structure, never an arbitrary dollar figure.
   → `references/03-entry-trigger-and-exit.md`
8. **Danger-zone / free-trade and multi-unit exits.** Take partial at target, move to break-even, trail.
   → `references/03-entry-trigger-and-exit.md` + `references/04-risk-and-money-management.md`
9. **Risk spine: Pareto, survive-6-losses, size-on-risk, market selection.** Capital adequacy first.
   → `references/04-risk-and-money-management.md`
10. **Discipline + honest evidence.** Ten cardinal rules — and TA's weak/mixed empirical base.
    → `references/05-psychology-and-honest-assessment.md`
11. **Two-layer read: Context (Layer 1) gates Trigger (Layer 2).** Standard RSI/MACD/Volume/OBV set the
    regime; Bernstein's exact params are the entry mechanic. → `## The two-layer read` below.

## The two-layer read — Market Context (Layer 1) gates the Bernstein Trigger (Layer 2)

Run the two layers **in order.** Layer 1 says whether the environment favors a trade at all; Layer 2 is
the precise entry mechanic. The same Bernstein divergence reads very differently at RSI 78 with falling
OBV than at RSI 45 with rising OBV — **establish context before hunting a trigger.**

**Layer 1 — Market Context (universal indicators, check FIRST):**
- **RSI(14)** — overbought **>70** / oversold **<30** (crypto trends harder: tighten to **>80 / <20**).
  **Centerline 50** = trend filter (above → bull regime, below → bear). **RSI/price divergence** is the
  same logic as Bernstein's Momentum divergence and often fires earlier.
- **MACD(12,26,9) standard** — the TradingView default, *distinct* from Bernstein's 9/18 line-only in
  Layer 2: **histogram expanding** = momentum accelerating, **contracting** = fading; **signal-line
  cross** = momentum trigger; **zero-line cross** = trend confirmation.
- **Volume vs 20-period average** — a breakout / close beyond a level is valid only on **above-average
  volume**; on below-average volume it is suspect (likely a fakeout).
- **OBV (On-Balance Volume)** — its direction confirms the trend; **price new high + OBV/volume
  declining = exhaustion** (bearish divergence), and the mirror at bottoms.

**Layer 2 — Bernstein Set-Up / Trigger (exact params, the entry mechanic):**
28-period Momentum, 10/8 MAC, 9-period Stochastic POP (30/70), 16-bar breakout, MACD(9,18) single-line
divergence, 4× volume spikes. → `references/02-setups-and-indicators.md`.

**Interaction rule:** act on a Layer-2 trigger **only when Layer 1 does not contradict its direction.**
Long trigger + RSI<30 + rising OBV + above-avg volume = high-confidence. Long trigger + RSI>75 + falling
OBV + thin volume = low-confidence → stand aside or halve size. **Report the Layer-1 context with every
Layer-2 call.**

## Data Retrieval — fetch the chart FIRST (TradingView MCP)

**Never analyze recalled or stale prices. Pull live data first**, then run the framework on it. The
set-ups below are computed from real OHLCV bars and indicator values fetched through the TradingView MCP.

### 0. Prerequisite & graceful degradation
The TradingView MCP needs Chrome running with CDP on port 9222. Probe with `tradingview-tv_health_check`
(or `tradingview-chart_get_state`). If it fails, launch Chrome, then retry:
```bash
mkdir -p .cache/chrome-cdp-profile && nohup /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 --user-data-dir=.cache/chrome-cdp-profile --no-first-run \
  "https://www.tradingview.com/chart/?symbol=BTCUSDT" > .cache/chrome-cdp.log 2>&1 &
sleep 10
```
If the MCP is still unavailable: **degrade loudly** — apply the framework only to values the user
supplies, mark every missing field `[UNAVAILABLE]`, set `DATA: DEGRADED` in the output, and **never
fabricate a price or indicator value.**

### 1. Map the symbol
- **Crypto:** `BINANCE:{TOKEN}USDT` (fallback `OKX:{TOKEN}USDT`)
- **US stocks:** `NASDAQ:{TICKER}` or `NYSE:{TICKER}`
- Unsure → `tradingview-symbol_search query="{name}"` and take the most-liquid match.

### 2. Pick the timeframe by analysis type — and always pull a higher TF for confluence
| Analysis | Primary TF (trigger fires here) | Confluence TF (trend/context) | Notes |
|---|---|---|---|
| Day-trade / intraday | `10` (10-min) or `30` | `60` / `240` | Volume spikes → `10`; 30-min opening-range breakout → `30` |
| Swing | `D` (daily) | `W` (weekly) | Daily MAC trigger = 57-period Momentum-MA *or* Williams A/D + 57-MA |
| Position | `W` (weekly) | `M` (monthly) | |

Name the set-up using the **higher TF for context**; the **bar-close trigger fires on the primary TF**.
Reset the chart to `D` after any intraday pull.

### 3. Fetch the bars (sequential — there is one chart slot)
```
tradingview-chart_get_state                               → current symbol + existing studies
tradingview-chart_set_symbol     symbol="{TV_SYMBOL}"
tradingview-chart_set_timeframe  timeframe="{PRIMARY_TF}"
tradingview-data_get_ohlcv       count=300 summary=false  → highs[], lows[], closes[], volume[]
tradingview-quote_get                                     → live last price (for entry/stop/target math)
# repeat chart_set_timeframe + data_get_ohlcv on the confluence TF, then reset to "D"
```
`count` must be **≥ 2× the longest lookback** (daily 57-period Momentum-MA → ≥ 150 bars; intraday
28-Momentum + 28-MA → ≥ 80). `count=300` is safe for every set-up.

### 4. Compute BOTH layers' indicators — Layer 1 is standard, Layer 2 (Bernstein) is NON-STANDARD
> **Layer 1** (RSI 14, MACD 12/26/9, Volume vs 20-avg, OBV) are TradingView defaults. **Layer 2** is
> Bernstein's custom set: TradingView's built-in MACD is 12/26/9 and its Stochastic is 14, but Bernstein
> uses a **9/18 MACD line-only** and a **9-period** stochastic, and his MAC is SMAs of **highs and lows**,
> not closes. **Fetch both layers. Do not accept defaults for Layer 2 — an unconfigured study is WRONG.**

**Route A — compute from OHLCV (preferred: exact params, no UI-state to fight).** Run on the fetched bars:
```python
import numpy as np
def sma(x, n): x = np.asarray(x, float); return np.convolve(x, np.ones(n)/n, "valid")
def ema(x, n):
    x = np.asarray(x, float); k = 2/(n+1); out = [x[0]]
    for v in x[1:]: out.append(out[-1] + k*(v - out[-1]))
    return np.array(out)
def mom(c, n): c = np.asarray(c, float); return c[n:] - c[:-n]   # Momentum(N) = close - close N bars ago

# === Layer 1 — standard market context (check FIRST) ===
def rsi(c, n=14):                                        # Wilder RSI(14)
    c = np.asarray(c, float); d = np.diff(c)
    up, dn = np.where(d > 0, d, 0.0), np.where(d < 0, -d, 0.0)
    au, ad = [up[:n].mean()], [dn[:n].mean()]
    for i in range(n, len(d)):
        au.append((au[-1]*(n-1) + up[i])/n); ad.append((ad[-1]*(n-1) + dn[i])/n)
    rs = np.array(au) / np.where(np.array(ad) == 0, 1e-9, ad)
    return 100 - 100/(1 + rs)                            # OB>70/<30 (crypto >80/<20); 50 = trend filter
rsi14 = rsi(close)
macd_std = ema(close, 12) - ema(close, 26)               # standard MACD(12,26,9): line / signal / hist
macd_sig = ema(macd_std, 9); macd_hist = macd_std - macd_sig
vol_avg20 = sma(volume, 20); vol_ratio = volume[-1] / vol_avg20[-1]   # breakout needs vol_ratio > 1
obv = np.concatenate([[0.0], np.cumsum(np.sign(np.diff(close)) * np.asarray(volume, float)[1:])])  # OBV

# === Layer 2 — Bernstein's exact (non-standard) params ===
# 10/8 MAC — 10-SMA of HIGHS (upper), 8-SMA of LOWS (lower). NOT closes, NOT EMA.
mac_up, mac_lo = sma(high, 10), sma(low, 8)
# Momentum trigger — 28 intraday (MA 28), 57-period MA on daily; 14/14 for the trend filter
mom28, mom28_ma = mom(close, 28), sma(mom(close, 28), 28)
# MACD(9,18) SINGLE LINE only — difference of EMAs; ignore signal line and histogram
macd_line = ema(close, 9) - ema(close, 18)
# 9-period SLOW stochastic %K, 3-bar smoothing, bands at 30/70
def slow_k(h, l, c, n=9, s=3):
    h, l, c = (np.asarray(z, float) for z in (h, l, c)); k = []
    for i in range(n-1, len(c)):
        hh, ll = h[i-n+1:i+1].max(), l[i-n+1:i+1].min()
        k.append(100*(c[i]-ll)/(hh-ll) if hh > ll else 50.0)
    return sma(k, s)
k9 = slow_k(high, low, close)
# 16-bar breakout — buy on a new prior-16 high, sell on a new prior-16 low
buy_lvl, sell_lvl = max(high[-17:-1]), min(low[-17:-1])
# 14-Momentum trend filter — take BUYS only when mom14 is above its 14-MA (mirror for sells)
mom14 = mom(close, 14); filter_up = mom14[-1] > sma(mom14, 14)[-1]
# Volume spike (10-min chart) — current bar ≥ 4× the avg of the prior ~4 bars
vspike = volume[-1] >= 4*np.mean(volume[-5:-1])
```

**Route B — configure studies on the chart, then read** (use when a rendered chart/screenshot is the deliverable):
```
# --- Layer 1: standard context (TradingView defaults are already correct) ---
tradingview-chart_manage_indicator action=add name="Relative Strength Index"  → length=14
tradingview-chart_manage_indicator action=add name="MACD"           → indicator_set_inputs fast=12 slow=26 signal=9  (line+signal+hist)
tradingview-chart_manage_indicator action=add name="Volume"         → reads vol; compare to its 20-period MA
tradingview-chart_manage_indicator action=add name="On Balance Volume"
# --- Layer 2: Bernstein's exact params (MUST override defaults) ---
tradingview-chart_manage_indicator action=add name="MACD"           → indicator_set_inputs fast=9  slow=18      (read LINE only)
tradingview-chart_manage_indicator action=add name="Stochastic"     → indicator_set_inputs k=9  smooth=3        (bands 30/70)
tradingview-chart_manage_indicator action=add name="Momentum"       → indicator_set_inputs length=28            (14 for trend filter)
tradingview-chart_manage_indicator action=add name="Moving Average" → indicator_set_inputs type=SMA source=high length=10
tradingview-chart_manage_indicator action=add name="Moving Average" → indicator_set_inputs type=SMA source=low  length=8     (this pair = the MAC)
tradingview-data_get_study_values         → current values for every visible study
tradingview-data_get_indicator   id=...   → one study's series (e.g. fetch RSI or OBV directly)
tradingview-data_get_pine_tables / data_get_pine_labels → read any Pine-script study outputs
```
Two MACDs coexist — the 12/26/9 (Layer 1) and the 9/18 line-only (Layer 2); label them so you don't
confuse the signals.
Dedup first via `chart_get_state` — do not add a study that is already present. **Override every
default input.** Prefer Route A for analysis rigor; use Route B only when the on-chart render or a
`tradingview-capture_screenshot` is the actual output.

### 5. Asset class — stocks vs crypto
Asset-agnostic set-ups (work for both): **10/8 MAC, Momentum/MACD divergence, stochastic POP, 16-bar
breakout, volume spikes.** The session-bound set-ups Bernstein built for the cash equity S&P — **the
gap/Oops, the 30-minute opening-range breakout, and the day-of-week pattern** — assume a daily
open/close session and **do NOT map cleanly to 24/7 crypto.** For crypto, anchor "the open" to the UTC
daily boundary and treat these three as weak/low-confidence; say so when asked for a gap or
opening-range read on a 24/7 market.

## How to apply the lens (decision procedure)

0. **Fetch the data (see Data Retrieval above).** Map the symbol, pull OHLCV + quote on the primary and
   one higher timeframe, compute **both layers'** indicators. No live bars → degrade loudly, don't fabricate.
1. **Read Layer-1 context FIRST.** RSI(14) regime + OB/OS (crypto >80/<20), MACD(12,26,9) histogram +
   signal + zero-line, volume vs 20-avg, OBV direction. This fixes the bias and whether a trigger is even
   worth hunting — a set-up that fights the context is low-confidence.
2. **Classify the Layer-2 set-up.** Name which of the ~7 historically verifiable Bernstein patterns (if
   any) the chart shows. No recognizable set-up → no trade. A pattern alone is *not* a signal.
3. **Wait for the bar-close trigger.** Act only when a *completed* price bar confirms (close beyond the
   level, %K cross, Momentum reaching the breakout point) **and Layer 1 does not contradict it**. "No
   trigger, no trade. Do not anticipate."
4. **Set a market-based stop** *before* entering — opposite side of the set-up, a range/volatility level,
   never an arbitrary dollar amount: "the market has no respect for such stops."
5. **Size on risk, not reward**, and check capital adequacy: be prepared to take **6 consecutive
   losses**. Trade 2 — preferably 3 — units so you can scale out. Halve size when Layer 1 is mixed.
6. **Manage Follow-Through (the hard part).** Hit first target → take a partial, move the stop to
   break-even (the **free trade**), ride the remainder with a trailing stop. Big money is in the big move.
7. **Apply the honesty overlay.** State that this is a *hypothesis*, not validated alpha; flag costs,
   overfitting, and that net of costs most day traders lose. Route to `analyst-systematic-trading` to
   backtest before risking capital.

## Routing table

| Question is about… | Load |
|---|---|
| **How to fetch chart data — which TradingView MCP tool, timeframe, indicator params** | **`## Data Retrieval` above (this file)** |
| What TA *is*, the STF framework, leading/lagging, debunked myths, backtesting limits | `01-philosophy-and-stf.md` |
| Which set-up is this, indicator settings, gaps, MAC, divergence, stochastic POP, breakouts | `02-setups-and-indicators.md` |
| The entry trigger, where to put the stop, profit targets, free-trade, time-of-day | `03-entry-trigger-and-exit.md` |
| Position sizing, scaling out, capital adequacy, what markets to trade | `04-risk-and-money-management.md` |
| Discipline, the ten cardinal rules, AND the honest critique of TA's evidence base | `05-psychology-and-honest-assessment.md` |
| Provenance and the canonical TA texts (Murphy, Edwards & Magee, Kirkpatrick & Dahlquist) | `book-index.md` |

## Example

<example>
User: "QQQ just made a new low but RSI/Momentum made a higher low — is this a buy?"

Lens response: "That's a textbook **bullish Momentum divergence** set-up (load `02-setups-and-indicators.md`
+ `03-entry-trigger-and-exit.md`). But Bernstein is emphatic: 'Bullish Momentum divergence in itself is
not a buy signal!' A set-up is not a trigger. Map the A–B–C–D–E points: find the highest Momentum reading
between the two lows — that's the **Momentum Breakout Point (E)**. You **buy only when Momentum rises back
up to E, on a completed bar** ('no trigger, no trade; a trigger can only occur at the end of a price bar').
**Stop**: market-based, just under the price low that formed the divergence — never an arbitrary dollar
amount. **Targets/exit**: trade 3 units; first target ≈ half the range from the A–D window, take a third
there, move the rest to break-even (the **free trade**), trail the remainder. **Honesty**: divergence
appears at only 'about 60 to 70 percent of meaningful tops and bottoms' — it misses, and it isn't a
backtested edge here. Treat this as a *hypothesis*: validate it with full costs in
`analyst-systematic-trading` before trading, because net of costs most day traders lose."
</example>

## Output format

Emit this fixed-shape block (omit nothing; use `[UNAVAILABLE]` for any field you could not fetch):

```
=== TECHNICAL READ — {SYMBOL} ({stock|crypto}) — {YYYY-MM-DD} ===
Timeframe:   {primary} (trigger)  +  {confluence} (context)
Price:       {last}            (tradingview-quote_get)

CONTEXT(L1): RSI14={} ({OB|OS|neutral}, {above|below} 50)  MACD(12,26,9) hist={} ({rising|falling}, {above|below} zero)  Vol={}×20avg  OBV={rising|falling}  → bias {BULL|BEAR|NEUTRAL}
SET-UP:      {named Bernstein set-up | NONE}  — {why it qualifies, with the exact indicator readings}
TRIGGER:     {TRIGGERED on bar-close | NOT YET: waiting for {condition} | INVALID}
             {the precise bar-close condition required — e.g. "Momentum closes back up to E"}
ALIGNMENT:   {Layer-1 context AGREES / CONTRADICTS the set-up direction → full size / halve / stand aside}
STOP:        {market-based level}   ({structure/volatility basis — NEVER an arbitrary $ figure})
TARGETS:     T1 {level} → take 1/3, move stop to break-even (free trade) → trail the remainder
SIZE:        {units, sized so a stop-out risks ≤ X% of capital; capital must survive 6 losses}
CONFLUENCE:  {higher-TF trend up/down/flat — AGREES / CONFLICTS with the set-up}
SETUP(L2):   MAC[10/8]={up}/{lo}  Mom28={}  Mom28MA={}  MACD(9,18)line={}  %K9slow={}  16bar hi/lo={}/{}  vol-spike={}
HONESTY:     Hypothesis only — {e.g. divergence hits ~60–70% of turns; params untested for overfit/costs}.
             Backtest in analyst-systematic-trading before risking capital.
DATA:        {LIVE (TradingView MCP) | DEGRADED — {which fields [UNAVAILABLE] and why}}
```

## Honesty rules (non-negotiable) — the big one

- **It's a lens, not gospel.** Present it as "TA / Bernstein's approach says…", never as fact.
- **TA has a weak / mixed empirical base.** The academic literature finds the large majority of active
  day traders **lose money net of costs**; Bernstein himself concedes day trading is "a low-accuracy
  venture" and zero-sum. Carry the critique in `05-psychology-and-honest-assessment.md`.
- **Subjective exits can't be cleanly backtested.** Bernstein deliberately makes Follow-Through
  non-mechanical ("I offer apologies in advance"), so his methods can't be cleanly falsified.
- **Parameters risk overfitting.** The exact settings (10/8 MAC, 28 Momentum, MACD 9/18, 9-stochastic
  30/70, 16-bar breakout) are shown without out-of-sample, cost, or significance testing — ironic next
  to his own anti-optimization warning. Present them precisely; never claim demonstrated profitability.
- **Validate, then trade.** TA setups are **hypothesis generation**. Route to `analyst-systematic-trading`
  for rigorous walk-forward validation with full costs; **`trend-following`** is the one TA family that
  survives backtesting. Pair with `regime-detection` and `risk-management`. The repo's house finding is
  that **hold / mid-risk beat day-trading after costs** — so treat TA day-trading as a lens for ideas,
  not a validated edge.

## Done when

The analysis (0) **fetched live OHLCV + indicators from the TradingView MCP** (or marked `DATA: DEGRADED`
without fabricating), (1) **reads Layer-1 context** (RSI/MACD-12-26-9/Volume/OBV) to fix the bias,
(2) names the Layer-2 Bernstein set-up (or says there is none), (3) specifies the **bar-close trigger**,
won't act before it, and checks Layer 1 doesn't contradict it, (4) places a **market-based stop** and
sizes on risk with capital-adequacy (survive-6-losses), (5) lays out the **multi-unit / free-trade
Follow-Through**, and (6) emits the **structured output block** and flags it as an unvalidated hypothesis
to be backtested in `analyst-systematic-trading`, net of costs.
