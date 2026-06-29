# Trend & Stage Analysis — Weinstein Stages and the MA Trend Filter

> Source: These are PUBLIC technical-analysis frameworks summarized from Stan Weinstein's widely-taught stage methodology and standard MA conventions — NOT verbatim-distilled from any book. No quotes, page numbers, or statistics are attributed beyond common public knowledge.

## Core thesis

Technical analysis is **the measurement of crowd behavior over time** — not fundamental value, not macro causality. The single most durable insight from decades of market study is that **trending assets continue to trend more than random-walk theory predicts**, and that the *stage* of that trend — not a single candle or indicator — determines whether an entry has a positive expected value. Stan Weinstein's stage framework operationalizes this: every tradeable asset cycles through four recognizable phases of accumulation, advance, distribution, and decline. The job of this lens is to answer one question before anything else: **what stage is this asset in right now?** If the answer is Stage 4, nothing else matters — stop reading and move on. If the answer is Stage 2, you have structural tailwind and must only decide where, when, and how much. Everything else — momentum, RSI, volume, pattern — is subordinate detail that either confirms or refines a stage verdict, never overrides it.

---

## Framework

- **Stan Weinstein's Stage 1 — Basing / Accumulation**
  - Price has stopped declining and is moving *sideways*, oscillating around a **flattening 30-week MA**.
  - Smart money accumulates quietly; volume is low and unremarkable.
  - The MA itself is flat or gently rounding up — it is no longer falling.
  - **No high-confidence long entries yet.** Watch only. Enter LATE in Stage 1 as the base tightens, volume starts to pick up, and the MA begins curling upward. A premature entry here means dead money for months.

- **Stan Weinstein's Stage 2 — Advancing / Markup** ← **the ONLY high-confidence buy zone**
  - Price **breaks out of the Stage 1 base** on **expanding volume** — this is the trigger.
  - The 30-week MA has turned UP and price holds consistently *above* it.
  - Each pullback to the rising MA is a secondary entry opportunity; a break *below* the MA on volume is a warning.
  - Risk/reward is most favorable here. This is where the bulk of gains occur.
  - Sub-phases: early Stage 2 (fresh breakout, highest edge), mid Stage 2 (trending cleanly), late Stage 2 (extended, wider stops required).

- **Stan Weinstein's Stage 3 — Topping / Distribution**
  - Momentum stalls. Price churns sideways or chops above and below a **flattening MA** again.
  - Breadth weakens; smart money distributes into retail buying.
  - Volume on down days begins to exceed volume on up days.
  - **No new long entries.** If already long: tighten stops, reduce size on rallies, do not add.
  - Looks deceptively like Stage 1 — the difference is context (comes after an advance, not a decline) and volume character.

- **Stan Weinstein's Stage 4 — Declining / Markdown** ← **AVOID; do not catch falling knives**
  - Price breaks below the Stage 3 base on volume; the 30-week MA **rolls over and points DOWN**.
  - Price consistently *below* a falling MA — the defining visual.
  - Most portfolio damage happens here. Value buyers get destroyed repeatedly.
  - Only valid plays are shorts (if book permits) or standing aside entirely.

- **The 30-week Moving Average** (≈ 150-day MA) — Weinstein's primary stage diagnostic
  - Its **SLOPE** defines the stage: rising → Stage 2 bias; flat → Stage 1 or Stage 3; falling → Stage 4.
  - Price *location* relative to the MA is secondary; slope is primary.
  - A price above a falling MA is a bear-market bounce, not a new Stage 2.

- **The 200-day Moving Average — the long-term regime filter** (standard public convention)
  - Price **above a rising 200d MA** = broadly bullish regime; below a falling 200d MA = broadly bearish.
  - Use both **slope** and **price location**. A flat 200d with price just above it carries much less conviction than a steeply rising 200d with price comfortably above.
  - Align your position sizing to regime: full size only when 200d is rising and price is above it.

- **The 50-day Moving Average — the intermediate trend gauge**
  - Faster cycle; useful for identifying pullback quality and momentum health.
  - **50d above 200d** = uptrend structure intact (bullish alignment).
  - In Stage 2, pullbacks to the 50d on low volume are healthy; breaks below on heavy volume are warning signs.

- **Golden Cross / Death Cross (50d crossing 200d)**
  - Golden Cross: 50d crosses *above* 200d → bullish signal. Death Cross: 50d crosses *below* 200d → bearish signal.
  - **Honest assessment:** Naive MA crossovers are **weak as standalone triggers**. They lag severely (the move is often 10–30% complete before the cross fires) and whipsaw painfully in range-bound markets. Use them as *context* — a Golden Cross on a Stage 2 breakout confirms structural alignment; a Death Cross during a Stage 4 decline confirms you should stay out. **Never use a cross alone as an entry trigger.** Route any rule using MA crosses to `analyst-systematic-trading` for backtesting before use.

- **MA Slope Measurement — how to quantify "rising" vs "flat"**
  - Slope = (MA_today − MA_N_periods_ago) / MA_N_periods_ago. Lookback: 10 bars for both (the 30-week MA and the 200-day MA), with a ±0.5% flat band.
  - **Rising:** slope > +0.5% over the lookback period. **Flat:** slope between −0.5% and +0.5%. **Falling:** slope < −0.5%.
  - These thresholds are adjustable; the script `ta.py` uses them as defaults. The key point is that "flat" is a *range*, not a point — small oscillations around zero are noise.
  - Do not call a MA "rising" on a single week's uptick after a long decline. Require *consecutive* rising readings (≥3 weeks) to confirm a slope change.

- **Relative Strength as a Stage 2 quality filter**
  - A true Stage 2 asset should be outperforming its broad market index (S&P 500 for equities, BTC for altcoins) on a 3–6 month basis.
  - If price is technically in Stage 2 but relative strength is flat or declining, the breakout is suspect — institutional money is not accumulating with conviction.
  - Use RS rank ≥ 70th percentile as a soft filter for high-conviction Stage 2 entries.

- **Crypto 4-year Halving Cycle mapped to Weinstein Stages** (heuristic, not a law)
  - **Stage 1 ≈ Post-bear accumulation** — BTC bottoming 12–18 months post-ATH collapse; price range-bound, on-chain metrics compressing. See `analysis-onchain` for valuation context here.
  - **Stage 2 ≈ Bull advance / markup** — breakout above prior cycle range, halving supply shock as a catalyst, price above rising MAs. This is the regime where aggressive crypto allocation is justified.
  - **Stage 3 ≈ Cycle top / distribution** — parabolic blow-off followed by chop; MAs flattening; on-chain distribution signals. Reduce and tighten stops.
  - **Stage 4 ≈ Bear market / markdown** — price below falling 30-week MA and 200d, cascading liquidations. Avoid new positions; wait for Stage 1 re-accumulation.
  - *Caveat:* The halving cycle is a narrative that fits past data; treat it as a rough prior, not a predictive law. On-chain signals from `analysis-onchain` carry more evidential weight than cycle-timing alone.

---

## How to APPLY (decision rules for an agent)

1. **Determine the Stage FIRST.** Run `python .agents/skills/research-technical/scripts/ta.py {SYMBOL}` to get the computed 200d MA, 30-week MA, 50d MA, their slopes, and the auto-labeled Weinstein Stage. Do not skip this step.

2. **Stage 4 → STOP. Do not proceed.** If the 30-week MA is falling AND price is below it, output `AVOID-DOWNTREND` and terminate analysis for this symbol. No fundamental case, no "it's cheap" argument overrides a Stage 4 verdict for a long entry.

3. **Stage 3 → No new entries; manage exits only.** If already long, tighten stop to just below the base of the Stage 3 range. Flag for `risk-management` to review position sizing.

4. **Stage 1 → Watch list only.** If the MA is flat or curling after a decline, add to the watch list. Set a conditional: re-run this lens when volume exceeds 1.5× the 50-period average on a breakout attempt. Do not allocate capital yet.

5. **Stage 2 → Proceed to full analysis.** This is the only stage where a long entry is structurally justified. Confirm all three of: (a) 30-week MA slope is UP; (b) price is above the 30-week MA; (c) 50d MA is above 200d MA. If all three pass, the structural filter is GREEN.

6. **Verify the 200-day MA regime.** Price above a *rising* 200d → full regime support. Price above a *flat or declining* 200d → reduce confidence, cut position size by 30–50%, flag for `regime-detection`.

7. **Classify entry quality within Stage 2:**
   - *Early Stage 2 (fresh breakout):* price just cleared the Stage 1 base on volume ≥1.5× average. Highest edge. Use a stop just below the breakout pivot.
   - *Mid Stage 2 (pullback to rising MA):* price retraced to the 30-week MA or 50d MA on low volume. Valid secondary entry. Stop below the MA.
   - *Late Stage 2 (extended):* price is far above both MAs (>20% extension from 30-week MA). Do NOT chase. Wait for the next pullback or reduce target size.

8. **Volume confirmation is mandatory on breakouts.** A Stage 2 breakout on below-average volume is a false signal until volume confirms. Flag it as unconfirmed and wait for volume to expand before entering.

9. **For crypto assets: layer on the halving-cycle prior.** If the halving-cycle clock suggests Stage 1–early Stage 2 (12–30 months post-ATH trough), raise confidence. If it suggests late Stage 3 (18+ months into a bull run, MAs already flattening), cut size and add on-chain distribution check via `analysis-onchain`.

10. **Golden/Death cross — treat as context only.** If a Golden Cross fired recently AND Stage 2 structural criteria pass → add as a confirming signal (not a standalone trigger). If a Death Cross fired AND Stage 4 criteria hold → adds confirmation to the **AVOID-DOWNTREND** read. Never use a cross as the *sole* trigger.

11. **The stage→verdict mapping (engine rules):**
    - Stage 4 (declining) → **AVOID-DOWNTREND**; level = resistance.
    - Stage 3 (topping) → **WAIT-PULLBACK {support}**; no new entries.
    - Stage 1 (basing) → **WAIT-BREAKOUT {resistance}**; wait for a daily close above resistance.
    - Stage 2 + `dist_50d_pct` > 15 (price >15% above rising 50d MA, extended) → **WAIT-PULLBACK {50d MA level}**.
    - Stage 2 + `rsi_w` ≥ 70 (weekly overbought) → **WAIT-PULLBACK {50d MA level}**.
    - Stage 2, near support, `rsi_w` < 70, confirmation present (`obv_trend == 'rising'` OR `divergence == 'bullish'`) → **ACCUMULATE {support}** — highest-conviction add.
    - Stage 2, near support, `rsi_w` < 70, confirmation mixed or absent → **BUY-ZONE {support}**.
    Run `ta.py` — it emits `verdict`, `level`, `entry_low`, `entry_high`, and `invalidation` directly.

12. **Route decisions downstream correctly:**
    - Sizing and drawdown limits → `risk-management`
    - Risk-on / risk-off macro overlay → `regime-detection`
    - Intraday execution timing (entry price, order type) → `investor-bernstein-intraday`
    - On-chain valuation (crypto only) → `analysis-onchain`
    - Any rule you want to use mechanically → validate with `analyst-systematic-trading` first

---

## Caveats

- **TA describes, it does not predict.** Stage analysis identifies the *current regime* with reasonable reliability; it does not guarantee the regime continues. A Stage 2 label can flip to Stage 3 within weeks if macro conditions change.
- **30-week MA is noisy on crypto.** Crypto's volatility means the MA oscillates more than in equities; a single-week spike below the MA is not a Stage 4 signal — look at consecutive closes and slope direction over multiple weeks.
- **The 200d MA gives false comfort in trending crashes.** In a fast bear market (e.g., COVID March 2020, crypto Nov 2022), price gaps below the 200d before most agents can act. Don't treat "price above 200d" as a safety guarantee.
- **Simple MA cross rules have failed out-of-sample repeatedly.** Trend-following as a *family* has a positive long-run expected value in academic literature. But specific single-crossover rules (50d/200d) are heavily data-mined and whipsaw badly in the 30–40% of time markets are range-bound. Always backtest via `analyst-systematic-trading` before automating any rule.
- **Stage analysis does not provide price targets.** It tells you *when* to be positioned; it does not tell you *where* to exit. Use separate target-setting logic or trailing stops.
- **Volume data is degraded in crypto.** Exchange-reported volumes include wash trading; use volume signals qualitatively and with skepticism unless sourced from CME or aggregated reliable sources.
- **Halving cycle mapping is hindsight-fitting.** Two complete Bitcoin cycles is insufficient statistical evidence. Treat cycle-stage priors as weak priors that can be overridden by current MA and on-chain evidence.
- **This lens covers entry timing, not valuation.** A stock can be Stage 2 and massively overvalued. Combine with `fundamental-analysis` and `analysis-onchain` (for crypto) — do not use technicals as a substitute for understanding what you are buying.
- **Timeframe stacking:** daily chart defines the trade; weekly chart defines the trend. A Stage 2 signal on the daily but Stage 3 on the weekly is a lower-quality setup. When in conflict, the weekly wins.
- **Individual stock risk in a Stage 4 market:** even a true Stage 2 breakout in a Stage 4 index environment has a much lower completion rate. Always check `regime-detection` for the broad market stage before sizing individual positions at full allocation.
