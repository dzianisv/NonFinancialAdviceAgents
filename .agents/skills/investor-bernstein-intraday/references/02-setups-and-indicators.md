# Set-Ups & Indicators — the Named Methods with Exact Parameters — Bernstein

> Source: Jacob Bernstein, *The Ultimate Day Trader* (2009, F+W Media) — Ch. 5–12 (the gap, 30-minute breakout, Moving Average Channel, day-of-week, volume spikes, Momentum/MACD divergence, stochastic POP, trend breakout), with indicator definitions and settings. Distilled 2026-06-07. **Parameters preserved verbatim.**

## Core thesis
Bernstein offers roughly **seven named, historically verifiable set-up methods** and urges the trader to **diversify across them** rather than be a "one trick pony." Each method pairs a recognizable pattern (the set-up) with a specific indicator and **exact settings**. The unifying idea: indicators *measure* crowd energy and exhaustion; they do not predict by themselves. "Momentum indicates the amount of energy, not the direction." A set-up never authorizes a trade on its own.

## Key frameworks / mental models
- **Diversify methods** — avoid being a "one trick pony"; run an uncorrelated basket of set-ups.
- **Indicators measure energy/behavior**, not direction or value.
- **Leading set-ups** (divergence) anticipate; **lagging set-ups** (MA channel, stochastics) confirm.

## Specific claims, mechanisms & data (PRESERVE EXACT PARAMETERS)
1. **GAP day trading.** A *gap* = the open is beyond the **prior day's high or low**. A **gap UP → SELL set-up**; a **gap DOWN → BUY set-up** (Larry Williams' "**Oops**" pattern). **Larger gap = higher probability.** Gaps tend to fade because market makers trade *into* the gap.
2. **THIRTY-MINUTE BREAKOUT (S&P).** Use the **first 30 minutes** of the **full S&P 500** to define the range, then **trade the E-Mini**.
3. **MOVING AVERAGE CHANNEL (MAC).** **Two SIMPLE moving averages** — a **10-period MA of the HIGHS** (upper channel) and an **8-period MA of the LOWS** (lower channel). *Not* closes, *not* exponential. Trigger indicator = **28-period Momentum** with its **28-period simple MA** on intraday charts. For **daily** charts, prefer a **57-period MA of Momentum**, *or* **Williams Accumulation/Distribution with a 57-period MA**. **SPY** serves as the stock proxy for the S&P.
4. **DAY-OF-WEEK pattern.** S&P **open-vs-close** tendencies by day, with **Monday** and **Friday** the notable ones.
5. **VOLUME SPIKES (VS).** A volume spike = a **4× or greater** volume increase over **up to ~4 bars**. Preferred timeframe is the **10-minute chart** (15-minute also usable).
6. **MOMENTUM / MACD DIVERGENCE.** **28-period Momentum** plus **MACD set to 9 and 18** — and Bernstein uses the **single-line MACD** = the *difference* of the two EMAs, **NOT** the signal-line crossover. **Momentum = price minus the price N periods ago** (i.e., Rate of Change). **Bullish divergence** = price makes a *new low* while Momentum makes a *higher low*; **bearish divergence** = price makes a *new high* while Momentum makes a *lower high*. Divergence appears at "**about 60 to 70 percent of meaningful tops and bottoms**" — not all. **Either Momentum OR MACD** triggering is enough: "We do not need both."
7. **STOCHASTIC "POP."** Deliberately counter-intuitive — **buy when "overbought," sell when "oversold."** Use a **9-period SLOW stochastic, %K only, 3-bar smoothing**, with boundaries at **30% and 70%**. (Note: the standard stochastic period N is often **14**, but "there is no standardized formula… which creates havoc when one tries to back-test.")
8. **TREND BREAKOUT (Keltner-derived).** **Buy on a new 16-period high; sell on a new 16-period low.** Trend filter = **14-period Momentum vs its 14-period MA**: take **buys only when the 14-period Momentum is above its MA** (mirror for sells).

## How to APPLY (decision rules for an agent using this lens)
1. **Match the chart to one named method** and use its **exact** settings; do not improvise parameters.
2. For divergence, **map it but do not trade it yet** — divergence is a set-up, never a signal (see `03`).
3. Remember **either Momentum OR MACD** suffices for divergence — don't demand both.
4. Use the **MAC** (10-high / 8-low simple MAs) to frame trend channels; use **28-Momentum** (intraday) or **57-period Momentum/Williams A-D MA** (daily) as the channel trigger.
5. Treat **gaps** with the fade bias (gap up → sell set-up; gap down → buy set-up), bigger gap = higher probability.
6. Run **several uncorrelated methods**, not one.
7. Flag that the non-standardized stochastic period is a documented **backtest hazard**.

## Caveats / where he hedges
- "There is **no standardized formula** [for the stochastic]… which creates havoc when one tries to back-test." (His own admission of parameter fragility.)
- Divergence works only "about 60 to 70 percent" of the time — it **misses 30–40%** of real turns.
- "**Bullish Momentum divergence in itself is not a buy signal!**" — the pattern must wait for the trigger.
- The specific numbers (10/8, 28, 9/18, 9-period 30/70, 16-bar, 14/14) are presented **without curve-fitting controls** — see `05-psychology-and-honest-assessment.md`.

## Memorable quotes
- "No trigger, no trade. Do not anticipate a trigger."
- "Bullish Momentum divergence in itself is not a buy signal!"
- "Momentum indicates the amount of energy, not the direction."
- "We do not need both." (on Momentum vs MACD divergence triggers)
- "there is no standardized formula… which creates havoc when one tries to back-test."
