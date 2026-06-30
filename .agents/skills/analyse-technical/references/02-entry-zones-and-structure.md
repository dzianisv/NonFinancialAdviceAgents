# Entry Zones & Chart Structure

> Source: Public technical-analysis frameworks (support/resistance, stage analysis, multi-timeframe
> confluence, base breakouts) summarized for agent use — NOT verbatim-distilled from any single book
> or author. Standard numeric conventions (50d MA, 200d MA, >10% extension) are widely published
> and not proprietary.

## Core thesis

Long-term entry timing is not about predicting direction; it is about locating price within structure
and buying at defined zones where risk is quantifiably contained. Every entry decision reduces to
three questions: (1) Where is price relative to the dominant structure — base, breakout, extension,
or downtrend? (2) Is the higher-timeframe (weekly) trend consistent with opening a long today?
(3) Is there a clear structural level just below entry that invalidates the thesis if broken —
close enough to keep risk-per-share tight? When all three resolve favorably, enter. When any one
conflicts, wait or stand aside. TA on daily/weekly charts cannot reliably predict direction; its
value is asymmetric positioning — you take the trade at a defined structural level where you know
immediately if you are wrong, and you exit there.

## Framework

- **Horizontal support & resistance zones**
  - Formed by: prior swing highs, prior swing lows, multi-week consolidation edges, prior ATHs,
    and round numbers (psychological levels).
  - These are ZONES (±1–3% around the reference price), not exact prices.
  - Significance scales with:
    - Number of distinct price touches (more = stronger)
    - Volume traded at the level (high volume = more market participants anchored there)
    - Time spent consolidating at the level (longer = more significance)
    - Whether the level is a prior ATH (ATH overhead supply can persist for years)
  - A zone with 3+ touches and above-average volume is a high-conviction structural level.

- **Polarity / role reversal**
  - Prior resistance, once broken and held on a retest, becomes support (and vice versa).
  - This is a high-quality entry setup: buy the *throwback/retest* to a broken resistance level
    that is now being defended as support.
  - Confirmation: price tests the old resistance zone on a pullback but does NOT re-enter it
    on a closing basis; a doji/hammer at the zone on declining selling volume is ideal.
  - Invalidation: a clean close back *inside* the old resistance zone = polarity failed → exit.
  - The throwback must arrive on declining volume (orderly, not panic); if volume accelerates
    into the throwback, the breakout was likely a fakeout.

- **Stage model (widely published framework)**
  - **Stage 1** — Basing / accumulation. Price moves sideways under a flat 200d MA. Volume quiet.
    No trend. Appropriate action: watch, not buy (except small starter near Stage 1 late).
  - **Stage 2** — Uptrend. Rising 200d MA, price above MA. This is the only stage for full-size
    long entries. Characterized by higher highs and higher lows on the weekly chart.
  - **Stage 3** — Topping / distribution. Price churning near highs, volume erratic, MA flattening.
    Reduce longs, no new positions.
  - **Stage 4** — Downtrend. Declining 200d MA, price below MA. No longs. Avoid entirely.
  - **Stage 1-late → Stage 2 transition** is the base-breakout entry. **Stage 2 pullbacks** to
    a rising 50d or 200d MA are the continuation entry. Everything else = wait or avoid.

- **Pullback-to-rising-MA entries**
  - In a confirmed Stage 2 uptrend, a pullback to a *rising* 50d MA is a structurally defined,
    low-risk long entry zone.
  - Conditions that MUST all be true:
    - The 50d MA is rising (positive slope) — not flat, not declining.
    - Price approaches from above (orderly pullback in an uptrend, not a breakdown through).
    - The broader weekly trend is also Stage 2 (weekly gate — see below).
  - The **first** retest of a newly rising 50d MA is the cleanest entry; later retests carry more
    risk of eventual MA failure.
  - A pullback to a FALLING MA is NOT a buy — it is a potential relief rally in a downtrend.
  - The 200d MA is the same concept at a slower cadence: Stage 2 stocks that correct deeply can
    find support at the rising 200d MA — this is a legitimate entry only if 200d MA is still rising.

- **Base / consolidation breakouts (volume confirmation mandatory)**
  - A multi-week or multi-month sideways base (flat base, range, coil) resolving higher on
    EXPANDING volume marks a Stage 1→2 transition or a Stage 2 continuation breakout.
  - **Volume expansion on breakout is mandatory** — breakout day/week volume should be
    meaningfully above the recent average (commonly cited: 1.5–2× the 50-day average volume).
  - A breakout on declining or below-average volume is suspect: likely a fakeout / failed breakout.
  - The breakout level becomes new structural support.
  - Entry options:
    - Aggressive: buy at the breakout level as it clears resistance on strong volume.
    - Conservative: wait for the first pullback (throwback) to the breakout level and buy there —
      better risk/reward, confirmation that the level holds as support.
  - Failed breakout: if price re-enters the base on a close within 1–2 sessions → exit.

- **Multi-timeframe confluence — weekly GATES daily (the most critical rule)**
  - The weekly chart is the higher timeframe. It GATES whether a daily setup is tradeable.
  - **WEEKLY AGREES** (Stage 2 on weekly, rising 30-week MA, price above MA):
    Daily pullback setups and daily breakouts are valid long entries at full size.
  - **WEEKLY MIXED** (Stage 1 late or Stage 2 early, MA just turning up, price near MA):
    Daily setups are valid but reduce size; require stronger confirmation (volume breakout,
    not just a pullback). Watch for early Stage 2 failure.
  - **WEEKLY CONFLICTS** (Stage 3 or Stage 4 on weekly):
    Daily bullish setups are bear-market bounces. DO NOT take them. Output AVOID-DOWNTREND.
  - This rule applies first, before any daily-chart analysis. If weekly conflicts, stop.
  - Repeat: if the WEEKLY and DAILY conflict → defer to the WEEKLY → stand aside or wait.

- **Entry-zone taxonomy (five verdicts)**
  - **ACCUMULATE {support}** — Stage 2, price near support, `rsi_w` < 70, confirmation present (`obv_trend` = 'rising' OR `divergence` = 'bullish'). Highest-conviction add. Level = support.
  - **BUY-ZONE {support}** — Stage 2, price near support, `rsi_w` < 70, confirmation mixed or absent. Proceed at normal sizing. Level = support.
  - **WAIT-PULLBACK {level}** — Fires in three cases: (1) Stage 3 topping [level = support]; (2) Stage 2 but extended (`dist_50d_pct` > 15 — price >15% above rising 50d MA) [level = the 50d MA]; (3) Stage 2 but weekly overbought (`rsi_w` ≥ 70) [level = the 50d MA]. Wait to buy the pullback to that level.
  - **WAIT-BREAKOUT {resistance}** — Stage 1 (basing). Price range-bound below unbroken resistance. Wait for a daily close above resistance = level.
  - **AVOID-DOWNTREND** — Stage 4 (declining). Level = resistance. No long positions.

- **Extension check**
  - If price is >15% above its rising 50d MA (`dist_50d_pct` > 15), it is *extended*.
  - Chasing extended price means: wide stop (invalidation is far), poor risk/reward, high
    probability of mean reversion back to the MA before any further advance.
  - Correct action: classify WAIT-PULLBACK {50d MA} and wait.
  - The script `python .agents/skills/analyse-technical/scripts/ta.py {SYMBOL}` computes
    `dist_50d_pct` and `dist_200d_pct` (percentage distance of price from the 50d MA and
    200d MA respectively), along with structural distances to support/resistance zones.
    Derive base/breakout/extended from `stage`, `dist_50d_pct` (>15 = extended), and price
    vs `resistance` (price ≥ resistance·0.99 = breakout). Do not eyeball.

- **Structural invalidation levels**
  - Invalidation is ALWAYS structure-based — never an arbitrary dollar amount or fixed percentage.
  - Place invalidation just below the structural anchor defining the thesis:
    - Base low (for ACCUMULATE or WAIT-BREAKOUT entries)
    - Swing low at the pullback (for BUY-ZONE pullback-to-MA entries)
    - Breakout level / polarity zone (for polarity-retest entries)
    - The key MA being tested (50d or 200d)
  - Trigger condition: a *sustained* close below the structural level — defined as either:
    - A single close >3% below the level, or
    - Two consecutive closes below the level on any volume.
  - An intraday wick below the level that closes back above = noise, not an invalidation.
  - Distinguish wick from sustained break explicitly in output.

## How to APPLY (decision rules for an agent)

1. **Run the structural script first.**
   Execute `python .agents/skills/analyse-technical/scripts/ta.py {SYMBOL}`.
   Capture: `dist_50d_pct`, `dist_200d_pct`, `support`, `resistance`, `vol_ratio`.
   Derive base/breakout/extended from `stage`, `dist_50d_pct` (>15 = extended), and
   price vs `resistance` (price ≥ resistance·0.99 = breakout).
   All numeric thresholds in rules 2–10 reference these outputs.

2. **Apply the weekly gate — this is the FIRST and MANDATORY filter.**
   Determine the weekly stage from the 30-week MA direction and price position:
   - Weekly Stage 4 (MA declining, price below MA) → **AVOID-DOWNTREND**. STOP. Output this.
   - Weekly Stage 3 (MA flattening, price churning near highs) → **AVOID-DOWNTREND**. STOP.
   - Weekly Stage 2 (MA rising, price above MA) → proceed to step 3 with `WEEKLY_AGREES`.
   - Weekly Stage 1 late (MA flat/turning up, price near MA) → proceed with `WEEKLY_MIXED`
     (reduced conviction; require stronger daily confirmation).

3. **Check for extension (step 2 of daily classification).**
   If `dist_50d_pct > 15` → classify **WAIT-PULLBACK {50d MA}**. Stop daily analysis.
   Log: "Price is [X]% above rising 50d MA — extended. Wait for pullback to MA support."

4. **Classify the daily entry zone using the taxonomy.**
   Apply checks in this order (first match wins):
   a. Stage 2, near support, `rsi_w` < 70, `obv_trend == 'rising'` OR `divergence == 'bullish'` → **ACCUMULATE {support}**.
   b. Stage 2, near support, `rsi_w` < 70, confirmation mixed or absent → **BUY-ZONE {support}**.
   c. Stage 1 (price range-bound, 30-week MA flat/curling) → **WAIT-BREAKOUT {resistance}**.
   d. Default if none of the above resolve cleanly → **WAIT-PULLBACK {50d MA}** (ambiguous; stay cautious).

5. **Confirm weekly-daily alignment and log it explicitly.**
   Output exactly one of:
   - `"Weekly Stage 2 AGREES with daily [classification] → entry valid."`
   - `"Weekly Stage 1-late MIXED — reduce size, require volume confirmation."`
   - `"Weekly Stage 3/4 CONFLICTS with daily bullish setup → AVOID-DOWNTREND regardless."`
   Never omit this statement from the output.

6. **Set and log the structural invalidation before sizing.**
   Identify the structural anchor just below the entry:
   base low, nearest swing low, breakout level, or the MA being tested.
   Write: "Invalidation: sustained close below $[level] ([structure name])."
   Example: "Invalidation: sustained close below $142.50, the March swing low / base."
   Do NOT use a fixed-percentage stop from entry — use the structural level.

7. **Classify invalidation distance and gate sizing.**
   - Invalidation within 4–6% of entry → tight risk → full-size entry consistent with
     `risk-management` caps.
   - Invalidation 6–10% away → medium risk → reduce size by ~30–50%.
   - Invalidation >10% away → wide risk → do NOT enter yet; reclassify as WAIT-PULLBACK
     or WAIT-BREAKOUT (wait for a closer structural anchor). Route sizing to `risk-management`.

8. **Check regime before finalizing.**
   Query `regime-detection`. In a risk-OFF regime (broad market Stage 3/4):
   - BUY-ZONE setups → reclassify as WAIT-BREAKOUT (require breakout volume confirmation).
   - ACCUMULATE → reduce size by 50%.
   - WAIT-BREAKOUT → hold; require volume ratio ≥ 1.75× average on breakout.
   Log the regime state in the output.

9. **For intraday execution within the zone, route to `investor-bernstein-intraday`.**
   This skill defines the structural zone for a position intended to hold weeks-to-months.
   It does NOT manage intraday timing, limit order placement, or scaling within the day.

10. **Before applying any new entry rule at scale, route to `analyse-systematic-trading`.**
    Example: "Does buying the first 50d MA retest in Stage 2 outperform buy-and-hold in this
    universe?" → backtest via `analyse-systematic-trading` before sizing up the rule.

11. **Output the structured verdict in this format every time:**
    ```
    entry_zone:        ACCUMULATE | BUY-ZONE | WAIT-PULLBACK | WAIT-BREAKOUT | AVOID-DOWNTREND
    weekly_gate:       WEEKLY_AGREES | WEEKLY_MIXED | WEEKLY_CONFLICTS
    regime:            RISK_ON | RISK_OFF | NEUTRAL (from regime-detection)
    key_level_below:   $[price] — [structure name]
    invalidation:      Sustained close below $[price]; threshold >3% or 2 consecutive closes
    dist_50d_pct: [X]% (from ta.py)
    dist_200d_pct:[X]% (from ta.py)
    structural_notes:  [1 paragraph plain-English interpretation]
    ```

## Caveats

- **TA has weak and mixed predictive evidence.** Support/resistance levels are self-fulfilling
  to a degree (widely watched → reinforced) but that effect is noisy and unreliable on any single
  trade. This skill is a *risk-reduction* framework, not a win-rate booster.

- **Volume data is noisier than it was.** Dark pools, ETF arbitrage, and HFT mean daily breakout
  volume is a weaker confirmation signal than in earlier eras. Require both volume expansion AND
  a clean closing price above resistance — not just an intraday volume spike.

- **MAs are lagging.** A rising 50d MA reflects 50 days of past price. In sharp mean-reverting
  environments, price can slice through a rising MA and recover without invalidating the trend.
  Use MA direction (rising/falling) as the primary filter, not a single close relative to the MA.

- **Polarity is not guaranteed.** Former resistance becomes support probabilistically, not
  certainly. Failed polarity retests are common. If price closes back inside the old resistance
  zone on a retest → exit immediately; polarity failed.

- **Stage transitions are only obvious in hindsight.** A stock appearing to be Stage 1 late may
  be entering a prolonged base failure (Stage 4 in disguise). The structural invalidation (below
  the base low) is the primary protection against misclassification.

- **Multi-timeframe analysis can be gamed by selective framing.** If you only consult the daily
  chart and ignore a bearish weekly, you will find clean daily setups that fail because the
  higher-timeframe distribution is already underway. The weekly gate is mandatory, not optional.

- **No entry rule is regime-invariant.** Pullback-to-rising-MA entries perform well in trending
  bull markets and fail badly in choppy, mean-reverting, or distribution regimes. Always check
  `regime-detection` before applying any entry rule. Low regime confidence → reduce exposure.

- **Script outputs are mechanical.** `ta.py` computes geometric distances and simple flags.
  It does not score level quality (number of touches, volume at level). Level quality judgment
  remains qualitative — a known gap in the automation.
