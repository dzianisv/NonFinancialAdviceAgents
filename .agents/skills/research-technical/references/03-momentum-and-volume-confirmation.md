# Momentum & Volume Confirmation

> Source: Standard public technical-analysis indicators (RSI, MACD, OBV, volume analysis) — summarized from widely-known conventions, NOT verbatim-distilled from any proprietary source or specific book.

## Core thesis

Momentum and volume indicators **confirm** the trend and structure already identified in files 01 (stage/trend) and 02 (support/resistance/pattern) — they are **not standalone triggers**. You do NOT buy a stock because RSI is oversold or MACD just crossed bullish. You identify a valid Stage-2 breakout or pullback-to-MA setup first, then ask: does momentum support the entry? Is volume behaving correctly? If the answer to both is yes, conviction rises. If momentum is absent or volume is wrong, step back even if the structure looks clean. The single most dangerous misuse of these tools is treating a momentum signal as the primary reason to enter. A weekly-overbought tape is a hard caution flag — **do not add exposure when the weekly RSI is already extended (>70 equities, >80 crypto)** even if the daily chart looks like a fine pullback entry. Every rule below is a confirmation lens, not a trigger.

---

## Framework

- **RSI(14) — daily and weekly** (standard 14-period Wilder smoothing)
  - **Centerline 50 — trend/regime filter (primary use):** RSI persistently above 50 = bullish momentum regime; below 50 = bearish momentum regime. This threshold matters more than overbought/oversold for trend-following entries. Before any long entry, verify daily RSI is above 50 and trending up; a stock struggling to hold 50 on the daily is not in a healthy uptrend.
  - **Overbought/oversold — caution thresholds, NOT signals:**
    - Equities: **70 = overbought, 30 = oversold**
    - Crypto (trends harder): tighten to **>80 = overbought, <20 = oversold**
    - In a genuine Stage-2 uptrend, RSI can stay above 70 for weeks or months — **overbought is NOT a sell signal in Stage 2.** It IS a caution against chasing a new position at extended prices.
    - **Weekly RSI > 70 (equities) or > 80 (crypto) = do not buy, regardless of how clean the daily looks.** Wait for the weekly to reset below 60 before re-engaging.
  - **Bullish divergence:** price makes a new low, RSI makes a HIGHER low → momentum waning on the downside → early confirming clue that a base may be forming. This is an early alert, not a trigger; divergence can persist for weeks. Use it to sharpen attention, not to pull the trigger prematurely.
  - **Bearish divergence:** price makes a new high, RSI makes a LOWER high → distribution/exhaustion → early warning at tops; combine with volume and stage analysis before acting.
  - The `ta.py` script (`python .agents/skills/research-technical/scripts/ta.py {SYMBOL}`) outputs `rsi_d` and `rsi_w` fields; always read both before encoding a momentum verdict.

- **MACD(12,26,9)** (standard exponential-moving-average construction)
  - **Histogram (MACD line minus signal line):** rising histogram = momentum accelerating; falling = fading. A histogram **turning up from below zero** is early bullish confirmation that a pullback is losing downside momentum — the most actionable signal in this group.
  - **Signal-line cross:** MACD crossing above its signal line = momentum confirming to the upside; crossing below = rolling over. Useful but lagging; combine with histogram direction.
  - **Zero-line:** MACD above zero = bullish momentum regime; below zero = bearish. A zero-line cross confirms a trend shift but is the most lagging of the three MACD reads — treat as regime color, not entry timing.
  - **MACD lags by construction** (it is derived from EMAs of price). It confirms moves already in progress; it does not predict turns. Never use a MACD cross as a standalone buy signal.
  - The `ta.py` script outputs `macd_hist_trend` ('rising'/'falling') and `macd_hist_last` (the histogram's last value; ≥ 0 means above zero).

- **Volume confirmation (raw bar volume vs 20-period average)**
  - **Breakouts require above-average volume.** A price move through a key resistance level or pattern boundary on volume < 20-period average is suspect — fakeout risk is high. Valid breakouts typically see 1.5× to 2× average volume or more on the breakout bar.
  - **Healthy pullbacks in uptrends show contracting (below-average) volume.** Sellers are not aggressive; this is bullish. The pullback-to-MA entry (from file 02) is highest-conviction when daily pullback bars carry light volume.
  - **Heavy volume on a pullback = warning.** If a stock is retreating on volume above its 20-period average, large sellers may be distributing. Downgrade conviction until volume behavior normalizes.
  - **Base/consolidation volume pattern:** A constructive base shows declining or quiet volume throughout the consolidation, then **expanding volume on the breakout**. Erratic heavy volume inside the base suggests distribution.
  - The `ta.py` script outputs `vol_ratio` (last-bar volume ÷ 20-bar average; e.g. 1.4 = 40% above average) for the most recent bar.

- **OBV (On-Balance Volume) — accumulation/distribution trend**
  - OBV direction tracks the net balance of buying vs selling pressure. **`obv_trend` = 'rising'** with price rising = healthy accumulation — institutions are participating in the move.
  - OBV contributes as trend confirmation only: 'rising' = accumulation, 'falling' = distribution, 'flat' = neutral. It is a SEPARATE signal from the RSI/price `divergence` field.
  - **Note:** the engine's ACCUMULATE verdict uses `obv_trend == 'rising'` as one of two confirmation conditions (the other is `divergence == 'bullish'`). Either one elevates a BUY-ZONE to ACCUMULATE.
  - OBV is not precise enough for entry timing; use it for regime/health color only.
  - The `ta.py` script outputs `obv_trend` (rising/falling/flat).

- **Timeframe alignment — daily vs weekly synthesis**
  - This skill operates on **daily charts for entry timing, weekly charts for regime.** Weekly is the macro-lens; daily is the trigger-lens. Both must be read.
  - **Ideal setup:** weekly RSI 50-65 (momentum healthy, not extended), weekly MACD above zero and rising → daily RSI above 50, daily MACD histogram turning up from a pullback, pullback-bar volume contracting. This is the full-stack confirmation picture.
  - **Acceptable but lower conviction:** weekly RSI 40-50 (trend recovering), weekly MACD just crossed zero-line, daily indicators pointing up — the trend is early-stage, size smaller.
  - **Avoid:** weekly RSI > 70/80 (overextended), weekly MACD histogram turning down while daily still looks OK — **the daily is a trap in this configuration.** Momentum and volume CONFIRM the trend — but the weekly is the regime. If the weekly says overbought, the daily confirmation is noise.
  - On crypto specifically: weekly RSI has historically stayed above 70 for extended bull-market periods. This does NOT override the >80 gate; it means use 80 not 70 for crypto weekly, and be even more patient.

- **What "momentum confirms" means in practice**
  - **Structural entry identified (from files 01/02):** e.g., Stage-2 stock pulling back to rising 50d MA, prior base breakout level acting as support.
  - **Momentum confirmation checklist applied HERE (file 03):** weekly RSI not overbought → daily RSI above 50 → MACD histogram turning up → pullback volume light → OBV not diverging bearishly.
  - **Without the file 01/02 structural setup, NONE of these momentum signals matter.** An oversold RSI in a Stage-4 declining stock is not a buy — it is a falling knife. Momentum and volume CONFIRM the trend/structure read from files 01 and 02; they do not replace it.

---

## How to APPLY (decision rules for an agent)

**Preamble (mandatory):** All rules below are confirmation rules applied AFTER files 01 and 02 have already established a valid structural setup (correct stage, valid entry zone, key levels identified). Momentum and volume CONFIRM the structure read — they are NOT standalone triggers. If no valid structural setup exists from files 01/02, these rules do not generate an entry.

1. **Weekly RSI regime gate (hard filter — run this first):**
   Run `ta.py {SYMBOL}` and read `rsi_w`.
   - If `rsi_w >= 70` (equities) or `>= 80` (crypto): **STOP. Do not open or add a new position.** The weekly tape is overbought; the full verdict becomes **WAIT-PULLBACK {50d MA}**. Even a valid daily pullback entry is likely chasing extended prices. Re-evaluate when `rsi_w` drops below 60.
   - If `rsi_w < 30` (equities) or `< 20` (crypto): flag as potential accumulation zone; combine with stage and `divergence` before proceeding.

2. **Daily RSI regime check (trend filter):**
   Read `rsi_d`.
   - `rsi_d > 50` AND trending upward: bullish momentum regime confirmed. Proceed to step 3.
   - `rsi_d < 50` OR recently crossed below 50: momentum not confirming. Downgrade conviction; wait for RSI to reclaim 50 before entering a long.
   - Note bullish divergence (`divergence = 'bullish'`) if `rsi_d` makes a higher low while price makes a lower low — flag as early base-formation signal, not a trigger.

3. **MACD histogram confirmation:**
   Read `macd_hist_trend` and `macd_hist_last`.
   - For a pullback entry: look for `macd_hist_trend = 'rising'` (especially from near-zero or negative territory). This confirms the pullback is losing downside momentum.
   - If `macd_hist_trend = 'falling'` and `macd_hist_last < 0`: momentum is rolling over in a bearish regime. Do not enter; add to the wait list.
   - Zero-line: `macd_hist_last >= 0` (histogram above zero) adds regime confirmation for longs; not a standalone condition.

4. **Volume validation at the entry bar or breakout:**
   Read `vol_ratio`.
   - For a breakout entry (price clearing resistance): require `vol_ratio >= 1.3` (at least 30% above 20-period average). Below that, mark as `LOW-VOLUME BREAKOUT — suspect`.
   - For a pullback-to-MA entry: prefer `vol_ratio < 1.0` on the pullback bars (light volume = sellers not aggressive). If pullback volume is > 1.5× average, downgrade to `WAIT — distribution signal`.
   - If recent daily volume is erratic (alternating heavy/light) inside a base, flag as unclear; wait for a clean quiet-then-expand pattern.

5. **OBV trend alignment:**
   Read `obv_trend` and `divergence`.
   - `obv_trend = 'rising'` with price rising: accumulation confirmed — positive color. This is one of the two conditions that elevate a BUY-ZONE to ACCUMULATE.
   - `divergence = 'bearish'` (RSI making lower highs while price makes new highs): add a distribution warning to the verdict. Do not add new exposure at extended prices when this appears.
   - `divergence = 'bullish'` (RSI making higher lows while price makes lower lows) at a potential base: positive confirming clue; this is the second condition that elevates a BUY-ZONE to ACCUMULATE.

6. **Scoring: confirmation tally (not a scoring formula — qualitative)**
   Count how many of the following are aligned for a long entry:
   - [ ] Weekly RSI not overbought (passes gate in rule 1)
   - [ ] Daily RSI above 50 and rising
   - [ ] MACD histogram rising (ideally from below zero on a pullback entry)
   - [ ] Breakout volume above average OR pullback volume below average (context-dependent)
   - [ ] OBV trend rising, no bearish divergence
   All 5 aligned = high-conviction confirmation. 3-4 = proceed with normal sizing. ≤2 = wait; momentum is not confirming the structure, hold off.

7. **Do not buy a weekly-overbought tape** — this rule is repeated here deliberately. If step 1 (weekly RSI gate) flags extended, no amount of favorable daily momentum or volume changes the answer. The exit is time-based: wait for the weekly to reset.

8. **Route to `analyst-systematic-trading`** before encoding any new rule variation as a systematic policy (backtesting gate — no untested rule becomes operational logic). Intraday execution details route to `investor-bernstein-intraday`, not this skill.

9. **Cross-check regime context:** Pipe current momentum verdict into `regime-detection` and `risk-management` before sizing. Momentum confirmation at the individual ticker level does not override a bearish macro regime; in a risk-off environment, reduce position size even on high-conviction setups.

10. **When dual confirmation signals align:**
    - Dual confirmation (`divergence = 'bullish'` AND `obv_trend = 'rising'`) at a major support level identified in file 02 = elevated ACCUMULATE probability. Highest-conviction add; widen attention.
    - Dual bearish signal (`divergence = 'bearish'` AND `obv_trend = 'falling'`) at extended prices = distribution likely ongoing. Do not add new exposure; the structural entry from file 02 at resistance becomes a caution, not a buy.

11. **Verdict encoding for the agent:**
    After running `ta.py {SYMBOL}` and applying rules 1–10, encode a structured verdict:
    ```
    MOMENTUM_VERDICT:
      weekly_rsi_gate: PASS (rsi_w < 70) | WAIT-PULLBACK (rsi_w ≥ 70 — full verdict becomes WAIT-PULLBACK)
      daily_rsi_regime: BULLISH | NEUTRAL | BEARISH
      macd_histogram: CONFIRMING | NEUTRAL | WARNING
      volume_behavior: CONFIRMING | MIXED | WARNING
      obv_alignment: CONFIRMING | NEUTRAL | DIVERGING_BEARISH | DIVERGING_BULLISH
      confirmation_count: N/5
      overall: CONFIRMS_ENTRY | PARTIAL_CONFIRM | WAIT | CAUTION
    ```
    Pass the `overall` field to the synthesis skill. Never pass a raw `CONFIRMS_ENTRY` verdict without also passing `weekly_rsi_gate = PASS`.

12. **Do not buy a weekly-overbought tape** — third and final repetition. Weekly RSI > 70 (equities) / > 80 (crypto) overrides any number of favorable daily readings. This is the single most common source of chasing-extended-prices mistakes. Hard stop.

---

## Caveats

- **TA has a weak/mixed evidence base.** Academic literature finds limited edge for most indicators when tested out-of-sample with realistic costs. These tools are confirmation lenses for structure already identified by stage/pattern analysis — they are not alpha generators on their own.
- **MACD lags.** All MACD signals (histogram, cross, zero-line) describe what has already happened. They confirm momentum present-tense; they do not predict future moves. Late entries are a real cost.
- **RSI "overbought" in Stage 2 can persist far longer than expected.** Stocks in genuine institutional uptrends can hold RSI >70 for months. Exiting or refusing to hold because RSI is "too high" on the daily is a common and costly error — reserve that caution for the weekly timeframe.
- **Volume context is era- and instrument-dependent.** Option-driven hedging activity, index rebalancing, ETF flows, and earnings announcements can create volume spikes unrelated to organic accumulation or distribution. Always note if a high-volume bar coincides with a known event before drawing a distribution conclusion.
- **Divergences can last a long time before resolving.** Bullish or bearish RSI/OBV divergence can persist for weeks or months. Treat them as early alerts that raise or lower the probability of a turn — never as triggers.
- **OBV is sensitive to gap behavior.** Large gap-up or gap-down opens can swing OBV dramatically and create false divergence signals. Interpret OBV divergence with caution around earnings or macro events.
- **These rules are not a complete system.** They are ONE confirmation layer in a multi-file analytical stack. The full picture requires stage analysis (file 01), key levels and patterns (file 02), this momentum/volume confirmation (file 03), and macro/regime context (`regime-detection`). Missing any layer degrades the signal.
- **Crypto thresholds (80/20) are approximate.** Crypto assets regularly trend into extended momentum for longer than equities. The 80/20 bounds are a practical tightening vs the 70/30 equity default; they are not derived from empirical backtesting on crypto-specific data and should be validated via `analyst-systematic-trading` for any specific asset.
- **Confirmation is not prediction.** All five indicators are backward-looking to some degree. A full green checklist tells you that recent momentum and volume behavior is consistent with the structural setup being valid — it does not guarantee the trade works. Position sizing and stop placement (from `risk-management`) are the actual risk controls.
- **Indicators are correlated.** RSI, MACD, and OBV all respond to the same underlying price and volume data. A bullish reading on all three is not "three independent votes." It is one vote seen through three lenses. Weight structural evidence from files 01/02 heavily; treat all five confirmation items as one confirming layer, not five independent signals.
- **Regime shifts can make these thresholds temporarily useless.** In a fast-moving bear market or crash event, RSI can stay below 30 for an extended period and MACD can stay negative for months. During confirmed bear regimes (from `regime-detection`), tighten risk and do not interpret oversold readings as accumulation opportunities until the weekly trend evidence shifts.
- **The 20-period volume average is a reference, not a law.** Thinly-traded names, recently-listed stocks, and assets with structural low-float characteristics can show misleading volume ratios. Always sanity-check absolute volume levels alongside the ratio.
- **Momentum and volume CONFIRM the trend/structure read from files 01 and 02.** This is the core thesis, restated as a caveat: if you find yourself using a momentum signal to override a Stage-3 or Stage-4 structural read, stop. The structural read from file 01 takes precedence. No amount of bullish RSI divergence makes a downtrending stock with broken structure an appropriate long entry.

---

## Quick-reference: `ta.py` output fields used in this file

| Field | Source | Used in rule |
|---|---|---|
| `rsi_d` | RSI(14) on daily bars | Rules 2, 6, 10 |
| `rsi_w` | RSI(14) on weekly bars | Rule 1 (hard gate), 6 |
| `macd_hist_trend` | MACD(12,26,9) histogram slope ('rising'/'falling') | Rules 3, 6 |
| `macd_hist_last` | MACD histogram last value (≥ 0 = above zero) | Rule 3 (regime color) |
| `vol_ratio` | Last-bar volume ÷ 20-bar average | Rules 4, 6 |
| `obv_trend` | OBV trend direction (rising/falling/flat) | Rules 5, 6 |
| `divergence` | RSI(14) vs price divergence (bullish/bearish/none) | Rules 5, 10 |

Always run the script before encoding a verdict. Never substitute visual inspection for computed values in an automated context.
