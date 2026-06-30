# Asset-Class Specifics — Stocks and Crypto

> Source: PUBLIC technical-analysis frameworks (O'Neil-style base analysis, Weinstein stage
> analysis, perpetual-swap market-microstructure) — summarized from widely-published conventions,
> NOT verbatim-distilled from any single book; no fabricated quotes or statistics.

---

## Core thesis

Technical entry-timing for **long-term and swing positions** (daily/weekly charts) requires reading
**price/volume structure** differently for equities vs crypto. Stocks are session-bound instruments
trading within RTH (09:30–16:00 ET); breakout volume must be measured against RTH bars, earnings
gaps must never be confused with base breakouts, and a stock's **relative-strength line versus the
S&P 500** is the single best filter for separating leadership from laggard traps. Crypto is a
**continuous 24/7 market** anchored to UTC daily boundaries; it carries derivatives-specific signals
(funding rate, open interest) that have no equity equivalent, and its long-run rhythm is dominated
by the **four-year halving cycle**, which provides a coarse stage-analysis framework on the weekly
chart. Both asset classes share the same foundation — Stage 2 markup is the only stage worth owning
on the long side; price > rising MA, volume-confirmed breakouts, and clear base structure — but the
instrument-specific overlays below are non-negotiable for disciplined entry-timing.

**Scope boundary (critical):**
On-chain valuation (MVRV, NUPL, realized price, Puell multiple) is **out of scope here** — route
all valuation questions to `analyse-onchain-lens`. Intraday execution is **not this skill** — route to
`investor-bernstein-intraday`. Validate any rule statistically with `analyse-systematic-trading`
before trading it live.

---

## Framework

**STOCKS**

- **Relative strength vs SPX / sector**
  Plot the stock-to-SPY ratio alongside the stock's price. A **rising RS line** while price builds
  a base confirms institutional accumulation relative to the index — the most reliable leadership
  filter available. A rising RS line making a NEW HIGH at or before the price breakout = highest
  conviction. A **falling RS line** during a breakout attempt signals distribution trap; avoid
  regardless of how clean the pattern looks. Also compare to the sector ETF: a stock leading both
  the index and its sector is the top tier; lagging both is the bottom tier.

- **Stage 2 prerequisite (Weinstein-style)**
  Price must be above a **rising 150-day EMA** (proxy for the 30-week MA). The MA itself must be
  sloping upward. If price is below a flat or declining 150d EMA, classify as Stage 1 (base), 3
  (top), or 4 (decline) — **do not attempt a long breakout entry in those stages**.

- **Flat base** (O'Neil-style base analysis, public framework)
  A tight, shallow sideways consolidation (typically ≤10–15% depth) after a prior advance of ≥20%.
  Duration: typically ≥5 weeks. Price compresses in a narrow range just below prior resistance.
  Breakout trigger: **daily close above the resistance ceiling on volume expansion** (≥130% of the
  50-day average RTH volume). **Invalidation: daily close below the base low.**

- **Cup-with-handle** (O'Neil-style base analysis, public framework)
  A rounded U-shaped correction (the cup) followed by a minor drift pullback of ≤15% from the cup
  rim (the handle). Handle should form in the upper half of the cup on declining volume. Buy the
  breakout above the handle's descending trendline / cup rim on **volume expansion**. The handle
  is the final shakeout of weak holders. **Invalidation: daily close below the handle low.**

- **Ascending base**
  A series of pullbacks each holding a higher low, compressing price against a resistance ceiling.
  Each trough shallower than the prior one. Breakout above the ceiling on volume = continuation.
  **Invalidation: close below the most recent higher trough.**

- **Volume rule (all base patterns)**
  Breakout bar must show **RTH volume ≥ 130% of the 50-day average volume**. Pre-market and
  after-hours volume do NOT count — judge RTH only. Below-average breakouts are suspect; either
  wait for a follow-through bar with volume, or stand aside. Volume expansion is the single
  strongest confirmation signal available; a technically clean pattern without it is low conviction.

- **Earnings-gap caution**
  A post-earnings gap is driven by a **fundamental surprise**, not by orderly accumulation. It is
  **not** a base breakout. Earnings gaps are prone to reversal (gap-fill) and whipsaw. Protocol:
  if the recent advance includes an earnings gap within the past 10 sessions, flag
  **EARNINGS GAP RISK**. Wait ≥3–5 sessions for price to stabilize. Only enter when either (a)
  the stock forms a tight mini-base above the gap and holds for ≥5 sessions, or (b) the gap is
  well-absorbed with price trading quietly at the highs. Do not chase the initial gap print.
  Note: a gap that bases cleanly for 3–6 weeks and then breaks out with volume IS a valid entry
  — the caution is about timing, not a permanent pass.

- **RTH vs extended-hours volume**
  All volume-based rules — breakout confirmation, distribution-day counts, climax-run detection —
  use **regular-trading-hours bars only**. Extended-hours prints are thin, unrepresentative, and
  misleading for any volume-confirmation signal. This is non-negotiable for stock analysis.

---

**CRYPTO**

- **4-year halving-cycle stage on the WEEKLY** (Weinstein-stage heuristic)
  Map the cycle to four stages using the **weekly chart**:
  - **Stage 1** — post-bear accumulation: BTC near multi-year lows, 30-week MA flat or curling up,
    volume quiet, sentiment near maximum fear.
  - **Stage 2** — halving-driven markup bull: price above rising 30-week MA, altcoins follow BTC
    with a lag, OI building, funding turns positive. The only stage with strong long bias.
  - **Stage 3** — cycle-top distribution: price churning at highs on declining volume on new highs,
    funding persistently elevated, divergences mounting.
  - **Stage 4** — bear markdown: price below declining 30-week MA, OI collapses, funding negative,
    capitulation wicks.
  **This is a heuristic, not a law.** Prior cycles (2013, 2017, 2021) are a sample of three. Macro
  liquidity shocks, ETF inflows, regulatory events, and stablecoin supply dynamics can truncate or
  extend any stage materially. Do not treat the halving calendar as a deterministic timer.

- **Funding rate as froth gauge** (perpetual swaps)
  Funding rate reflects the cost of holding a perpetual long vs short relative to spot.
  - **Persistently HIGH POSITIVE funding** (e.g., >+0.05–0.10% per 8h sustained over multiple days)
    = crowded longs paying a premium to stay long = **ENTRY CAUTION** — late, overheated, prone to
    long-flush liquidation cascade. Do not add to longs into elevated funding.
  - **NEGATIVE or near-zero funding** = shorts paying / market neutral = contrarian accumulation
    interest, potential capitulation bottom.
  Funding is a **confirmation signal, not a standalone trigger**. Do not short solely because
  funding is high; do not buy solely because it is negative. It confirms froth or exhaustion at
  the margin only. Funding data is pulled via `ccxt.fetch_funding_rate()` inside
  `python .agents/skills/analyse-technical/scripts/ta.py {SYMBOL} --asset crypto`.

- **Open-interest (OI) trend matrix**
  Read OI in combination with price direction. Four regimes:

  | OI     | Price  | Interpretation                              | Agent action         |
  |--------|--------|---------------------------------------------|----------------------|
  | OI ↑   | Price ↑| New capital entering, longs building         | Healthy; trend-confirm |
  | OI ↑   | Price ↓| New shorts building, bearish pressure        | Avoid longs           |
  | OI ↓   | Price ↑| Short-covering, NOT new demand               | **Weak/fade-prone**   |
  | OI ↓   | Price ↓| Long liquidation / capitulation              | Watch for bottom      |

  OI data is pulled via `ccxt.fetch_open_interest()` inside `ta.py` — **not from TradingView**.

- **24/7 = no session gaps, no opening-range**
  Crypto trades continuously. Session-bound concepts — opening gaps, overnight gap fades,
  opening-range breakouts, daily open/close as significant anchors — do **NOT apply**. Anchor all
  "daily" candles to the **UTC midnight boundary**. Trendlines are cleaner (no overnight gaps), but
  there is no "volume-at-the-open" spike signal; volume expansion on a breakout is assessed over
  the full 24h candle relative to the 30-day average daily volume.

- **Spot vs perpetual symbol mapping**
  Price structure, trend analysis, and base patterns are read on the **SPOT instrument**
  (e.g., `BINANCE:BTCUSDT`). Funding rate and open interest are **derivatives signals** from the
  perpetual swap — a separate instrument with its own price series. The `ta.py` script handles
  this: OHLCV from spot via ccxt; funding/OI from the perp endpoint where available. Do not
  conflate spot price action with perp signals; validate each on its own instrument.
  When only a perpetual symbol is available, note the discrepancy but still apply base/MA rules
  to the price series.

---

## How to APPLY (decision rules for an agent)

**STOCKS — ordered execution checklist**

1. **Stage gate (mandatory first).** Compute whether price > 150-day EMA AND the 150d EMA slope
   is positive (current value > value 20 days ago). If EITHER fails: classify Stage 1/3/4 and
   return **AVOID-DOWNTREND**. Do not proceed to pattern analysis.

2. **RS line gate.** Compute stock-to-SPY 3-month return ratio slope. If RS line is trending DOWN
   (negative slope over 60 days): tag **LAGGARD** and **reduce conviction by one tier**. If RS
   line is at or near a new high concurrent with the base: tag **LEADER** and upgrade conviction.

3. **Base identification.** Scan for flat base, cup-with-handle, or ascending base. Record:
   base type, depth (%), duration (weeks), pivot/resistance price. If no recognizable base and
   price is >20% extended above any prior base: tag **EXTENDED — wait for next base; no entry**.

4. **RTH volume confirmation.** On the breakout bar, check RTH volume vs 50-day average.
   If volume ≥ 130%: tag **CONFIRMED**. If volume 100–129%: tag **BORDERLINE — watch follow-through**.
   If volume < 100%: tag **UNCONFIRMED — do not enter; wait for follow-through or retrace**.

5. **Earnings-gap filter.** Check if any bar in the base or the breakout bar itself was an
   earnings-reaction gap. If yes and it occurred within the past 10 sessions: tag
   **EARNINGS GAP RISK** and defer entry. Re-evaluate once the stock has traded ≥5 sessions above
   the gap without reversal and forms a recognizable consolidation.

6. **Set entry and invalidation.** Entry = breakout above pivot on confirmed volume. Hard stop =
   daily close below base low (flat/ascending) or handle low (cup-with-handle). Log both levels.
   Route stop distance and position size to `risk-management`.

**CRYPTO — ordered execution checklist**

7. **Halving-cycle stage (weekly chart).** Classify the current weekly stage (1/2/3/4) using the
   30-week MA slope and price relationship. In Stage 3 or 4: **require materially stronger evidence
   before entering a long** — demand OI capitulation, negative funding, and a tested weekly support
   level. In Stage 2: standard breakout rules apply at normal conviction thresholds.

8. **Funding rate check.** Pull via `ta.py`. If average 8h funding > +0.05% over the past 3 days:
   append **FROTH WARNING** to output. Require a pullback to recognized daily support before entry.
   Do not size a full position into elevated funding.

9. **OI regime classification.** Compute prior-session OI direction vs price direction. Classify
   into one of the four OI regimes above. If regime is OI↓ + price↑ (short-covering):
   tag **WEAK RALLY — fade-prone** and reduce position size or stand aside.

10. **Spot-based base/MA analysis.** Run all pattern and MA checks on the SPOT symbol via ccxt OHLCV.
    If short-covering OI regime and weak funding: downgrade; if OI↑ + price↑ + low funding: upgrade.

11. **UTC daily anchor.** When computing ATR, volume averages, or breakout volume ratios, use
    UTC-midnight-bounded daily candles. Never mix exchange-local daily boundaries.

12. **Three-factor convergence trigger.** Full-size entry is only warranted when ALL THREE align:
    - OI↑ + price↑ (new capital, not short-covering)
    - Funding neutral-to-low (<+0.02% per 8h)
    - Price breaks above a recognized base or weekly resistance on above-average daily volume
    Any one factor missing: reduce conviction one tier. Two missing: do not enter — hold for a
    cleaner setup (the engine resolves this to **WAIT-PULLBACK** or **WAIT-BREAKOUT** by stage).

---

## Caveats

- **TA has weak and mixed empirical support.** Base patterns and RS signals work best in trending
  bull markets and degrade badly in choppy or mean-reverting regimes. Always check `regime-detection`
  output; in a risk-off regime, lower conviction on all pattern signals.

- **Volume thresholds are conventions, not constants.** The 130%/40%-above-average guidelines are
  industry conventions (O'Neil-style public frameworks). Validate specific thresholds for specific
  universes with `analyse-systematic-trading` before relying on them mechanically.

- **Halving-cycle timing is a sample-of-three heuristic.** Do not extrapolate three data points
  into a mechanical calendar. Macro liquidity, ETF structural demand, and regulatory shocks can
  and do override cycle positioning.

- **Funding spikes are noisy short-term.** Single-session funding spikes mean-revert frequently.
  Require multi-day (≥3 days) persistence of elevated funding before flagging FROTH.

- **OI data quality varies.** Aggregated OI via ccxt may lag or be incomplete for low-liquidity
  altcoins. For coins outside the top 20 by open interest, treat OI signals as indicative only.

- **Earnings gaps can be the START of a new Stage 2.** The caution is about entry timing
  specifically, not a permanent disqualification. A clean post-earnings base that then breaks out
  on volume is a valid, often high-quality, setup.

- **Relative strength is momentum, not fundamentals.** It underperforms in sector rotations where
  prior laggards re-rate. Use alongside fundamental context and `regime-detection`, not in isolation.

- **On-chain valuation is explicitly out of scope.** MVRV, NUPL, realized price, and Puell multiple
  belong to `analyse-onchain-lens`. This lens is price/volume structure only. Never attempt to infer
  cycle valuation position from chart patterns alone.

- **All sizing and risk decisions route through `risk-management`.** This skill provides entry
  zones, base types, and invalidation levels only. It does not size positions.

- **Cross-skill chain (required for full picture):**
  Entry timing (this skill) → Valuation context (`analyse-onchain-lens`) → Backtest any rule
  (`analyse-systematic-trading`) → Size and veto (`risk-management`) → Regime filter
  (`regime-detection`) → Intraday execution (`investor-bernstein-intraday`).
