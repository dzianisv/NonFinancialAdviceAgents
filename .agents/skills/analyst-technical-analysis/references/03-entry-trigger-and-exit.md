# Entry Trigger, Stops & Exit — Bernstein

> Source: Jacob Bernstein, *The Ultimate Day Trader* (2009, F+W Media) — Ch. 6–13 (per-method triggers, the bar-close rule, the A–B–C–D–E divergence trigger, market-based stops, profit targets, the danger-zone / free-trade exit, time-of-day, trade/fade the news). Distilled 2026-06-07. **Parameters preserved verbatim.**

## Core thesis
The set-up tells you *what could happen*; the **trigger** tells you *it is happening now*. The **CARDINAL RULE**: a trigger is valid **only at the END of a price bar** — an intrabar penetration that does not hold to the close does **not** count, and you must never "jump the gun." Entries are mechanical; exits (Follow-Through) are managed. **Stops must be market-based**, derived from range/volatility/structure, *never* an arbitrary dollar figure: "the market has no respect for such stops." The exit logic is built around getting out of the **danger zone** fast (move to break-even = a **free trade**) and then riding the rare big winner with a trailing stop.

## Key frameworks / mental models
- **Bar-close trigger rule.** "A trigger can only occur at the end of a price bar." No exceptions; no anticipation.
- **Danger-zone / free-trade exit.** Hit the first profit target (P1) → take a partial → move the stop to **break-even** (now a *free trade*) → ride the remainder → trail.
- **Market-based stops.** Stops live where the *market structure / range / volatility* says, not where a fixed dollar loss says.
- **Time-of-day structure.** The first **15–30 minutes** are volatile and serve as the **setup window**; day trades **close by session end**. FOREX trades **23–24 hours** — all fair game.

## Specific claims, mechanisms & data (PRESERVE EXACT PARAMETERS)
- **GAP trigger.** Gap **up** → **sell short when price falls back below the prior day's high**. Gap **down** → **buy when price rises back above the prior day's low**. **Stop** = the opposite side. **Exit** = end of day / **First Profitable Opening (FPO)** / split.
- **VOLUME-SPIKE trigger.** Isolate the spike on the **10-minute** chart; mark the **spike bar's high and low**. **Buy on a bar CLOSE above the spike high; sell on a bar CLOSE below the spike low.** **Stop** = opposite side. **Exit** by session end or trail.
- **DIVERGENCE A-B-C-D-E trigger.** Label: **A** = the lowest price low; **B** = the Momentum value at that low; **C** = the previous Momentum low; **D** = the price at C; **E** = the **highest Momentum reading between B and C** = the **"Momentum Breakout Point."** The **buy triggers when Momentum rises back up to E** (mirror for sells). Spot divergence on **daily charts in a ~3-month / ~60-bar window** (experienced traders up to 5–6 months); the divergence **must last ≥ 6 bars (6 trading days)**.
- **STOCHASTIC POP trigger.** **%K crosses above 70 → buy on the close**; **%K crosses below 30 → sell on the close**. **Exit when %K crosses back.**
- **TREND-BREAKOUT orders.** **Buy stop one tick above the highest high of the last 16 bars**; **sell stop below the lowest low of the last 16 bars.**
- **NEWS — "Trade/Fade the news" (stocks).** Set-up = a stock **opens ≥ 50% of the prior daily range beyond the prior high/low** on news. **WAIT 15 minutes (no action).** Then, after a sharply *lower* open, **buy if any 15-minute bar ENDS above the high of the first 15-minute bar** (mirror for a higher open). **Risk** = a new high/low for the day. The trigger **may take hours or never come.**
- **STOPS.** Must be **market-based** (indicator / volatility / range), **never arbitrary dollar**: "the market has no respect for such stops."
- **First profit target (divergence)** = **one-half the range** of the highest-high to the lowest-low across the **A–D window**.
- **DANGER-ZONE / FREE-TRADE.** Hit P1 → take partial → move stop to **break-even** → ride remainder → trailing stop.

## How to APPLY (decision rules for an agent using this lens)
1. **Never act intrabar.** Wait for the **bar to close** beyond the level (or for %K/Momentum to confirm on close). "No trigger, no trade."
2. **Pre-place the stop** on the opposite side / market-structure level *before* entry; reject any dollar-based stop.
3. For divergence, **compute E (the Momentum Breakout Point)** and trigger only when Momentum reaches it; require **≥6 bars** of divergence.
4. **Set the first target** (½ the A–D range for divergence) and run the **danger-zone → free-trade → trail** sequence.
5. For news, **enforce the 15-minute wait** and accept that the trigger may never arrive — that is a feature, not a failure.
6. **Close day trades by session end** unless the method explicitly trails (and never carry a loser overnight — see `04`).

## Caveats / where he hedges
- The exit is **intentionally discretionary** — Bernstein "offers apologies in advance" that it is "not entirely mechanical," which is also why it cannot be cleanly backtested.
- The news trigger "may take hours or never come," so the set-up frequently produces **no trade** at all.
- Targets and trailing logic are rules of thumb, not optimized/validated quantities.

## Memorable quotes
- "No trigger, no trade."
- "A trigger can only occur at the end of a price bar."
- "The sooner we can get out of the danger zone… the sooner we can enjoy the benefits of riding a free trade."
- "The market has no respect for such stops." (on arbitrary dollar stops)
