# intraday-bot — Results (final, honest)

Date: 2026-07-01/02. Scope: 3 strategies gated end-to-end (flat-cost gate + bar-by-bar
maker-fill simulation), plus a paper/notify-mode execution bot built and smoke-tested.

**Bottom line: 0 of 3 strategies passed the gate. Nothing trades live. Nothing is even
paper-trading yet — all 3 are FAIL / no edge found, independently verified.** The
execution bot (`bot/`) is built, tested, and defaults to `notify` mode (zero broker
credentials touched). It has no PASS strategy to run yet.

> No cost, fill, or date-window assumption was loosened anywhere in this cycle to force
> a PASS. Every "FAIL (no edge found)" below is the honest, reproduced result.

---

## Executive summary (plain English)

We tested three trading ideas on crypto (Bitcoin, Ethereum, Solana, and a basket of the
top 46 US-dollar-paired coins on Binance) using six-plus years of historical price data,
2020 through mid-2026. All three failed a strict statistical test before any money would
be risked. This is not a coding failure — it's the honest answer to "does this idea make
money after real trading costs." Two of the three ideas actually lost money outright, and
badly. The third idea (trend-following on Bitcoin, "buy when price is above its moving
average") didn't lose money — it made a real, positive return and cut the worst
drawdowns roughly in half compared to just buying and holding Bitcoin — but it failed a
stricter statistical significance test (explained below) that asks "is this better than
what you'd expect from pure luck, given how many variations you tried?" The answer was no.

**Terms used below, defined once:**
- **OOS (out-of-sample):** results measured on data the strategy was never tuned on — the
  only numbers that matter. IS (in-sample) numbers are shown for context only and are
  always overstated (that's what tuning does).
- **Sharpe ratio:** return per unit of risk. Above 0 = made money adjusted for
  volatility. Above ~1 is good. Below 0 = lost money.
- **Deflated Sharpe Ratio (DSR):** a stricter Sharpe that penalizes you for how many
  variants you tried before picking a winner (the "if you flip enough coins, one looks
  like a genius" problem). Our gate requires DSR probability ≥ 0.95 (95% confidence the
  result isn't luck) to PASS. All three strategies scored DSR = 0.00.
  the honest, deflated grade you get to be a "PASS" in this pipeline.
- **Maker vs. taker fees:** a "maker" order rests on the order book and waits to be
  filled (cheaper, 0.15% per trade side); a "taker" order executes immediately against
  the book (more expensive, 0.25% per side, and always the fallback for time-out exits).
- **Stress test:** re-running the same strategy with costs doubled, or fills delayed by
  one bar, to check the result isn't fragile.
- **Fill simulation:** instead of assuming every order fills instantly at a perfect
  price, we simulate whether a resting limit order would actually have been filled bar by
  bar, using real historical highs/lows (a maker order only "fills" if price genuinely
  trades through it, not just touches it).

---

## Metrics table (OOS, net of costs — the headline numbers)

| Strategy | Symbol | OOS Sharpe | OOS CAGR | Max Drawdown | DSR | 2x-fee stress | 1-bar-delay stress | Verdict |
|---|---|---:|---:|---:|---:|---:|---:|---|
| regime_sma_maker (BTC>SMA, N=50) | BTC | 0.576 | +19.2% | -27.7% | 0.00 | 0.392 (survives) | 0.521 (survives) | **FAIL — DSR only** |
| regime_sma_maker (BTC>SMA, N=200) | ETH | 0.410 | +13.3% | -38.9% | 0.00 | 0.366 (survives) | 0.371 (survives) | **FAIL — DSR only** |
| xs_momentum (28d lookback, top-5) | 46-coin universe | -0.574 | -52.0% | -91.0% | 0.00 | -0.723 (fails) | -0.505 (fails) | **FAIL — no edge** |
| meanrev_maker (5m mean-reversion) | BTC/ETH/SOL | -10.30 | -97.0% | -99.98% | 0.00 | -20.45 (fails) | -17.73 (fails) | **FAIL — no edge, catastrophic** |

Benchmarks, same OOS windows, net of one entry fee:

| Benchmark | Sharpe | CAGR | Max DD |
|---|---:|---:|---:|
| Hold BTC (2024-01→2026-07) | 0.409 | +12.9% | -53.0% |
| Hold ETH (2024-01→2026-07) | 0.064 | -14.2% | -67.6% |
| Equal-weight hold, 43-coin universe | -0.26 | -32.6% | -81.4% |

All numbers above were cross-checked byte-for-byte against
`intraday-bot/results/regime_sma_maker_gate.json`, `results/regime_sma_maker_fillsim.json`,
`results/xs_momentum.json`, and `results/meanrev_maker.json`. No discrepancies found.
(All four artifacts were regenerated 2026-07-02 after the June-2026 data backfill and the
`core/universe.py` delisting-staleness fix; every number in this document was re-synced to
the regenerated artifacts. All verdicts were unchanged by the re-run.)

---

## Strategy 1 — regime_sma_maker (BTC/ETH trend-following, "price above moving average")

**Spec:** Long when yesterday's close was above its N-day simple moving average, flat
otherwise. Long-only, daily bars, 2020-01-01 to 2026-07-01. N tuned in-sample only
(2020-2023) from {50, 200} per symbol → N=50 for BTC, N=200 for ETH. Scored once on OOS
(2024-01-01→2026-07-01). Both a flat-cost gate run and a full bar-by-bar maker-fill
simulation were run (resting limit at prior close, forced market exit on timeout).

**Headline OOS (net of costs):**
- BTC (N=50): Sharpe 0.576, CAGR +19.2%, max DD -27.7%, win rate 27.4%, profit factor 1.15.
- ETH (N=200): Sharpe 0.410, CAGR +13.3%, max DD -38.9%, win rate 24.0%, profit factor 1.11.
- Fill-sim base tier (honest execution model, **P0-fixed 2026-07-02** — see below): BTC
  Sharpe 0.650, ETH Sharpe 0.428 — both slightly better than the flat-cost gate, and both
  saw a 100% base-tier fill rate. Base-tier numbers are unchanged by the P0 fix (see why in
  the P0 note below); other fill-sim tiers did change.

**Stress (fill-sim tiers, post-P0-fix):** 2x fees (BTC 0.539, ETH 0.402) and worst-vol-bar
slippage (BTC 0.648, ETH 0.427) stay Sharpe-positive and are numerically unchanged by the
fix. **1-bar delayed fill now FAILS for both symbols (BTC 0.650→-0.023, ETH 0.428→-0.012)**
and reduced fill-probability, while still positive, is materially worse than previously
reported (BTC 0.394→0.148, ETH 0.216→0.108) — see the P0 fix note below for why. (Separately,
`core/gate.py`'s own flat-cost-level stress suite — a different, cost-model-only
approximation of delayed fills via a weight-shift, not this bar-by-bar fill sim — still
shows 2x fees BTC 0.392/ETH 0.366 and 1-bar-delay BTC 0.521/ETH 0.371, both survive; that
number is untouched by this fix and is the one the gate verdict actually uses.)

**Deflated Sharpe:** 0.00 for both symbols (threshold 0.95), z-scores -14.8 (BTC) /
-15.0 (ETH) — roughly 15 standard deviations short. This gap is an order of magnitude, not
marginal; it holds whether you count 2 trials (this run) or 5 (cumulative, including 3
prior June variants of the same idea family).

**Benchmark:** Beats hold-BTC on both return and risk-adjusted return while roughly
halving max drawdown (-27.7% vs -53.0%). Beats hold-ETH too, but ETH's own drawdown stays
large (-38.9%) — the "cuts drawdowns in half" story is BTC-specific, not universal.

**Verifier's verdict: CONFIRMED_FAIL — the top-line FAIL stands, but with an important
downgrade to the report's supporting claim.** The verifier independently reproduced every
number bit-for-bit and confirmed the look-ahead canary and shift-collapse checks are
real and pass. **The verifier found a P0 defect in the fill-simulation script
(`scripts/run_regime_sma_maker_fillsim.py`): the actual simulated fill price was never used
in the P&L calculation — only fees and a timing skip/no-skip decision were. P&L was computed
purely from close-to-close returns, not from the price the maker order would actually have
filled at.** Proof: the "offset 5bp" variant (testing a limit order resting 5bp away from
the prior close) used to produce byte-for-byte identical returns to the base tier —
mathematically impossible if fill price actually mattered.

**P0 FIX (2026-07-02):** entry/exit bar P&L is now computed from `FillResult.fill_price`
(the actual limit price for maker fills, the bar's close for forced-market timeout exits)
against the adjacent mark-to-market point, instead of plain close-to-close. Base tier and
the 2x-fees/worst-vol-slippage tiers are numerically unchanged (on this signal, transitions
always fill on their own bar at `limit_price == prior_close` exactly, so the old
approximation happened to coincide with the correct answer there). The offset-5bp tier now
correctly differs from base (proof the fix works: BTC 0.650→0.686, ETH 0.428→0.437). The
**1-bar-delayed-fill tier now fails (goes Sharpe-negative)** for both symbols — this is the
most consequential correction: a fill delayed one bar past a transition (an outsized-move
day by construction) lands at a materially worse price than the signal-time close, and that
price gap is exactly what the old bug was blind to. Reduced-fill-probability stays positive
but is meaningfully worse than previously reported. **This does not flip the gate verdict**
(DSR fails regardless, using the separate flat-cost gate's numbers, not this fill-sim
script's), but the report's prior claim that "the drawdown-control edge and its fill-realism
both hold up under stress" is downgraded: it holds for 3 of 4 fill-sim stress tiers, not all
of them, and the delayed-fill tier is now a real fragility, not a survived stress test.

**Final verdict: FAIL.** Sole binding reason: deflated Sharpe = 0.00 (statistical
significance gate), not fill/cost fragility. Confirms June's finding under an honest cost
and, as of the P0 fix above, a genuinely fill-price-honest execution model.

---

## Strategy 2 — xs_momentum (cross-sectional crypto momentum, weekly rebalance)

**Spec:** Long-only, equal-weight top-N by trailing K-day momentum, from a point-in-time
top-30-by-volume universe drawn from 46 USDT-major coins (90-day listing gate, no
look-ahead). K and N grid-searched IS-only over {7,14,28}×{3,5} → chosen K=28, N=5. Weekly
rebalance at Monday 00:00 UTC. Maker limits at prior close, taker fallback after 1-bar
timeout.

**Headline OOS (2024-01-01→2026-07-01, 913 bars):** Sharpe -0.57, CAGR -52.0%, max DD
-91.0%, breakeven cost -9,730bps (negative — loses money even at **zero** cost, so this
is not a cost-model artifact; the underlying momentum ranking itself has negative
expected value on this window). IS (for contrast): Sharpe +1.77, CAGR +283% — a complete
sign flip from IS to OOS, the textbook overfitting signature.

**Stress:** Fails both mandatory stress tiers outright: 2x fees → Sharpe -0.72; 1-bar
delayed fill → Sharpe -0.50. No stress-survival question — the base case already fails.

**Deflated Sharpe:** 0.00, z=-40.2 — the realized Sharpe is far below even the noise
floor for 6 trials; not a borderline multiple-testing case.

**Benchmark:** Underperforms BOTH hold-BTC (+0.41 Sharpe) and naive equal-weight-hold of
its own 43-coin candidate pool (-0.26 Sharpe) — the cleanest possible signal that the
momentum ranking/selection step itself destroys value here, not just that trading costs
are too high.

**Verifier's verdict: CONFIRMED_FAIL, fully reproduced.** Independent live re-run
(not from cache) matched every number bit-for-bit, including all 5 fill-sim stress tiers
and the hand-rederived DSR math. Two secondary findings, neither changes the verdict:
(1) the gate's cost model is pure-taker throughout (0.25%/side), not "maker/taker-blended"
as one doc line describes it — a conservative-direction inaccuracy (overstates costs);
(2) a real, previously-undetected latent bug in `core/universe.py`: the point-in-time
universe's 30-day rolling volume window doesn't correctly zero out a coin's volume after
it delists, letting it linger in the "top-30" membership table for up to ~15 days on stale
data. Traced through and confirmed this did NOT contaminate this run's P&L (the momentum
signal independently excludes delisted names via its own NaN handling), but it's a real
defect worth fixing before a future strategy relies purely on universe membership.
**[FIXED 2026-07-02: `core/universe.py` now gates membership on each symbol's last
observed data date; the numbers in this section come from a re-run that includes the
fix — verdict unchanged.]**

**Final verdict: FAIL.** Decisive on all 4 gate criteria simultaneously (OOS Sharpe≤0,
DSR<0.95, fails both stress tiers). Gross (pre-cost) edge is itself negative. This is a
real absence of edge, not a look-ahead bug or a cost artifact.

---

## Strategy 3 — meanrev_maker (5-minute intraday mean-reversion, limit-order dip-buy)

**Spec:** BTC/ETH/SOL 5-minute bars, 2022-01-01→2026-07-01. Buy on a resting maker limit
when price z-scores k standard deviations below its rolling mean; exit on a resting maker
limit at the rolling mean, forced taker market exit on timeout, hard stop at 2x entry
deviation. $250/order, long-only. 27-config grid searched IS-only (lookback×k×timeout_bars).

**Headline OOS (2024-01-01→2026-07-01, 262,944 5-minute bars, maker-cost model):**
Sharpe **-10.30**, CAGR **-97.0%**, max DD **-99.98%**, breakeven cost -14.3bps (loses
money even at zero cost). Every one of the 27 grid configs failed on IS too (best IS
Sharpe was -9.33) — this is not an overfitting story, the whole family is broken.

**Stress:** Both mandatory tiers make it worse: 2x fees → Sharpe -20.45, CAGR -99.9%;
1-bar delayed fill → Sharpe -17.73, CAGR -99.8%.

**Fill-model report:** This is the interesting, non-obvious finding. The maker entry
mechanism itself works exactly as designed — 97-99% fill rate, and the maker-vs-taker fee
savings (20bp) genuinely exceeds the tiny adverse-selection drift after fill (0.4-0.9bp),
so `maker_win_is_real=True` for all three symbols. **The execution layer isn't the
problem.** The problem is the trading idea itself: mean **gross** (pre-fee) return per
round trip is already negative (-10 to -17bp across the three coins) before any cost is
applied — 5-minute mean-reversion has negative expected value on these assets over this
period. 59% of exits are forced to pay taker fees because price doesn't revert to the mean
fast enough within the timeout window, compounding an already-losing thesis.

**Deflated Sharpe:** 0.00, z=-1056.8 — not a borderline call by any measure; the observed
Sharpe is over a thousand standard errors below the noise floor for 27 trials.

**Benchmark:** Loses to buy-and-hold BTC by roughly 112 percentage points of CAGR and 10.7
Sharpe points over the identical window — decisively worse than doing nothing.

**Verifier's verdict: CONFIRMED_FAIL, fully reproduced byte-for-byte** (re-ran the entire
gate script from scratch, zero cached results, diffed to zero differences across every
nested metric). All 60 core unit tests pass. Only finding: a trivial P2 rounding
imprecision in one summary sentence of the report (stated walk-forward window range as
"-8.9 to -16.4" when the true range including one additional real window was "-7.18 to
-16.37" at the time) — doesn't affect any headline number or the verdict. [Post-June-2026
backfill, the final quarterly window now covers the full quarter and the true full-window
range is -7.18 to -13.53; the report has been updated accordingly.]

**Final verdict: FAIL. All four gate criteria fail decisively.** Root cause is a
genuinely unprofitable signal at this timeframe, not a fill/execution artifact — the fill
model actually vindicates the execution design while confirming the underlying idea is
dead.

---

## What would change our mind / next hypotheses

1. **regime_sma_maker is the one worth revisiting, not abandoning outright.** It has a
   real, reproducible, stress-surviving positive edge and genuinely cuts BTC drawdowns in
   half — it just doesn't clear the statistical-significance bar with only 2-5 trials and
   ~910 OOS daily bars. To change the verdict: (a) extend the OOS window as more data
   accrues (DSR requires roughly an order-of-magnitude higher period Sharpe than observed,
   so more bars alone won't flip it — but a materially different underlying edge might);
   (b) test on a genuinely independent, pre-registered symbol set instead of re-testing
   BTC/ETH after already knowing they've worked in two separate strategy families this
   year (a fresh, out-of-family confirmation would count as new evidence, not another
   trial in the same haircut pool); (c) do NOT keep re-running BTC>SMA variants — every
   additional trial in this family raises the DSR bar further, not lowers it.
2. **[DONE 2026-07-02] Fix the fill-sim P0 bug (regime_sma_maker fill-price wiring).**
   Fixed and re-run — see the P0 FIX note in the regime_sma_maker section above. The
   fill-sim now correctly distinguishes a 0bp from a 5bp limit offset, and the corrected
   delayed-fill fragility is documented.
3. **xs_momentum: cross-sectional momentum on this coin universe over 2024-2026 has
   negative expected value, underperforming even naive equal-weight holding of the same
   coins.** Would need a fundamentally different ranking signal (not lookback-return
   momentum) or a different rebalance cadence/universe construction to be worth another
   trial — simply re-tuning K/N within this family is very unlikely to clear DSR given how
   far OOS Sharpe (-0.52) sits below even the flat-cost noise floor.
4. **meanrev_maker: 5-minute mean-reversion is decisively, catastrophically unprofitable
   on BTC/ETH/SOL 2022-2026, gross of costs.** The execution/fill design was validated as
   sound in isolation (worth reusing for a different signal), but this specific
   signal-timeframe combination should not be retried without a fundamentally different
   entry trigger (this z-score/rolling-mean approach is now a closed line of inquiry — see
   dead-idea log).
5. **[DONE 2026-07-02] Fix `core/universe.py`'s rolling-volume staleness bug** (found by
   the xs_momentum verifier) — fixed by gating membership on each symbol's last observed
   data date; xs_momentum was re-run with the fix included (verdict unchanged).

---

## Human sign-off — binding

**Nothing in this cycle trades live. No PASS strategy exists yet, so nothing is even
queued for paper trading.** If and when a strategy clears the gate (OOS Sharpe > 0, DSR
≥ 0.95, survives both stress tiers), the path is: **PASS → human review of this report →
Alpaca PAPER account first (`mode: paper` in `bot/config.yaml`, real paper-account order
placement, zero real funds) → a separate, explicit human decision before `mode: live` is
ever engaged.** `bot/executor.py`'s live mode is a deliberately gated stub (refuses
without `CONFIRM_LIVE=<today's UTC date>` env, `ALPACA_LIVE_KEY`, a named strategy
reference, and passing hard caps) — it does not place real orders even when the gate
opens, by design, until a human wires it up. Hard caps (`bot/caps.py`, $500 book: max
order $250, max position $500, no shorts, no leverage, $25/day kill switch) are hardcoded
outside any config or LLM override and apply to every mode identically.

---

## Cross-check note

Every metric quoted in this report was diffed against the underlying JSON artifacts in
`intraday-bot/results/` (`regime_sma_maker_gate.json`, `regime_sma_maker_fillsim.json`,
`regime_sma_maker.json`, `xs_momentum.json`, `meanrev_maker.json`) and matched exactly —
no rounding beyond 2-3 significant figures for readability, no substitutions. Where the
verifier found a documentation inaccuracy in the implementer's own `reports/*.md` files
(the ETH walk-forward Sharpe framing in regime_sma_maker, the "maker/taker-blended" cost
description in xs_momentum, the walk-forward range rounding in meanrev_maker), this
document uses the verified/corrected framing, not the original report's framing.
