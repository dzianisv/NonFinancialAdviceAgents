# Pre-registration: fresh-symbol confirmation test for `regime_sma_maker`

**Date:** 2026-07-06
**Author:** Claude (delegated research task), on behalf of the intraday-bot research process
**Status at time of writing: NO RESULTS EXIST YET.** This document is committed to git
BEFORE any fresh-symbol backtest is run. The commit hash of this file is the pre-registration
timestamp, per `ROADMAP.md` Section 5 ("Pre-registered fresh-symbol confirmation for the
trend family (explicitly NOT a retune)").

## Why this run exists

`regime_sma_maker` (BTC/ETH "price above N-day SMA" trend family) is a **dead, firewalled
family** per `TRIAL_LEDGER.md`: it fails the DSR >= 0.95 significance gate even at its honest
cumulative trial count N=5 (corrected DSR 0.39 BTC / 0.30 ETH — both < 0.95). No further
retunes are sanctioned inside this family. `ROADMAP.md` Section 5 sanctions exactly ONE more
type of evidence here: a **pre-registered, zero-parameter-change confirmation run on fresh
(never-tuned-on) symbols**. This document is that pre-registration.

**This is a falsification test, not significance-hunting.** Because crypto majors correlate
0.6-0.85 with BTC/ETH, even a full pass across all 5 fresh symbols would add almost no real
statistical evidence — the effective number of independent observations (N_eff) for the added
symbols caps near 1.2-1.4, per `ROADMAP.md` Section 3 and Section 5. Therefore:

- A **PASS must never be written up as moving the family's DSR needle or reopening
  deployment.** It only means the frozen rule's real-looking edge on BTC/ETH generalizes to a
  handful of other correlated large-cap coins — a much weaker claim than statistical
  significance.
- A **FAIL is strong evidence against the family**, precisely because nothing was tuned to
  produce it — the rule and its parameter were frozen using only BTC/ETH data, before any
  fresh symbol's numbers were seen.

This honest framing must be preserved in every downstream document (results section below,
`TRIAL_LEDGER.md` entry, commit message) — no hype in either direction.

## The frozen rule (zero code modifications)

Reused unchanged from `strategies/regime_sma_maker.py`'s `signals()` function. Docstring
lines 10-18, quoted verbatim:

> Rule: long (weight=1.0) when PRIOR bar's close > PRIOR SMA(N) of close, else flat (0.0).
> `sma_window` (N) is the only tunable parameter: 200 (headline, matches "REGIME-SMA
> (BTC>200d)" naming) and 50 (the June-tested N=50 variant), per symbol (BTC primary,
> ETH secondary).
>
> Prior-bar-close-only: the signal at bar t uses close[t-1] and SMA computed over
> close[..t-1] (rolling window ending at t-1), then the WHOLE resulting series is shifted
> by one more bar so the position is only ever known as of the START of bar t (the
> contractual "decided on prior bar close" timing the harness's canary checks for).

**Parameter: `{"sma_window": 50}`** — the BTC-winning config. Source:
`results/regime_sma_maker_gate.json`'s `BTCUSDT.best_params == {"sma_window": 50}` (also
mirrored in `results/regime_sma_maker.json`'s `flat_cost_gate.BTCUSDT.best_params`).

No grid. No per-symbol tuning. No second config. `sma_window=200` (the ETH-winning config)
is explicitly NOT used here — this run tests whether the BTC-winning parameter, frozen as-is,
generalizes, not whether some parameter can be found that works per fresh symbol.

## Execution / cost model

Identical to `scripts/run_regime_sma_maker_gate.py`:
`core.gate.gate(signals, {sym: df}, param_grid=[{"sma_window": 50}], interval="1d")` with
default `CostConfig()`.

Per `core/gate.py`'s `run_backtest()` (lines 349-392): when `is_maker` is not passed, it
defaults to `False`, so turnover is costed at `TAKER_RATE` (0.25%/side) —
`fee_rate = (cost_cfg.maker_rate if is_maker else cost_cfg.taker_rate) * cost_cfg.fee_multiplier`.
This is the same "flat-cost gate" methodology that produced the ledger's headline BTC OOS
Sharpe 0.576 / ETH OOS Sharpe 0.410 numbers. **This is a conservative (taker-rate) flat cost,
not a cheap-maker-assumed one** — stated explicitly so nobody later mistakes the strategy
family's name ("regime_sma_maker") as meaning maker fees were assumed in this flat-cost path.

**Also run:** the honest maker-fill simulator, mirroring `scripts/run_regime_sma_maker_fillsim.py`'s
`run_symbol()` with `sma_window=50`, restricted to 3 of its 6 tiers: `base`, `stress_2x_fees`,
`stress_delay_1bar` (the other 3 — `offset_5bp`, `stress_reduced_fill_prob`,
`stress_worst_vol_slippage` — are out of scope for this run).

Both the flat-cost gate's own analytic stress tiers (`stress_suite()`'s `2x_fees` and
`delayed_fill_1bar`) AND the honest fillsim's stress tiers (`stress_2x_fees`,
`stress_delay_1bar`) will be reported side by side. **These two methodologies can legitimately
disagree** — they did for BTC in the existing ledger: the flat-gate's delayed-fill tier stayed
Sharpe-positive (~0.52) while the honest bar-by-bar fillsim's delayed-fill tier went negative
(per `ROADMAP.md` Section 1). If this recurs for any fresh symbol, it will be stated explicitly
in the results, not averaged or smoothed over.

## Symbol list

Selection rule (stated verbatim): "the most liquid Binance USDT spot pairs as of 2024-01-01
excluding BTC and ETH, with full daily-bar history from 2020-01-01 (or listing date if later,
noted per symbol)."

**SOLUSDT, XRPUSDT, DOGEUSDT, ADAUSDT, LINKUSDT**

Actual cached date ranges/row counts will be verified via `core.data.load(sym, "1d")` before
any backtest is run (Step 3 of the task), not assumed. If any symbol's cache is missing,
stale, or corrupt, `core/data.py`'s `download()` will be used to fetch fresh data for that
symbol only. **No symbol will ever be substituted for another after this document is
committed** — if a symbol's data proves unusable, it will be noted as unavailable/excluded
and the run will proceed with the remaining symbols.

## Scoring windows

- **Primary (used for the pass/fail verdict):** `core/gate.py`'s `OOS_START = "2024-01-01"`,
  OOS end left open (through the latest cached bar, expected ~2026-07-01, but the actual last
  date used will be reported, not assumed).
- **Secondary (reported, NOT used for the verdict):** full available history per symbol
  (actual first cached bar through latest bar), same cost model, same frozen rule, plus a
  full-history buy-and-hold benchmark. This is explicitly secondary — these symbols
  contributed zero information to the original IS tuning (there is no real IS/OOS split for
  them; `sma_window=50` was chosen using only BTC/ETH data).

## DSR (informational only)

Computed per symbol at `n_trials=5` (the family's current cumulative N per `TRIAL_LEDGER.md`)
via `core.gate.deflated_sharpe_ratio()` directly, moment-adjusted, using each symbol's OOS
per-bar Sharpe/skew/kurt/n_obs. **Labeled INFORMATIONAL ONLY — not part of the pass/fail
verdict.** The N_eff ~1.2-1.4 correlation caveat (Section 3/5 of `ROADMAP.md`) applies: these
are not 5 independent draws, so treat any DSR number here as illustrative, not decisive.

## The pre-registered interpretation rule (verdict rule)

Written verbatim; to be applied mechanically after results are in, with no adjustment:

> The regime_sma_maker family survives this falsification test only if the frozen rule
> (sma_window=50, identical cost/execution model) beats its own symbol's buy-and-hold
> benchmark on a Sharpe (risk-adjusted) basis, on the primary OOS window (2024-01-01 through
> the latest cached bar), on a MAJORITY (>=3 of 5) of the pre-registered symbols, AND those
> same majority symbols remain Sharpe-positive under BOTH the 2x-fee stress tier and the
> 1-bar-delayed-fill stress tier (checked under BOTH the flat-cost-gate's own stress tiers and
> the honest bar-by-bar fillsim's stress tiers — a symbol only counts toward the majority if
> it clears all of these). Failing to clear this bar is a FAILED confirmation and is treated
> as evidence AGAINST the family, precisely because zero parameters were changed to make it
> work. A PASS is explicitly NOT to be read as materially raising the family's DSR or
> reopening deployment — it only means the frozen rule's real-looking edge on BTC/ETH
> generalizes to a few more correlated large-cap coins, which is a much weaker claim.

## Scope of this run (files touched)

This run only writes to: `intraday-bot/preregistrations/` (this file, plus its Results
section appended after the run), `intraday-bot/results/` (new JSON), an append to
`intraday-bot/TRIAL_LEDGER.md`, a new script
`intraday-bot/scripts/run_regime_sma_maker_fresh_symbols.py`, and any newly-downloaded data
files under `intraday-bot/data/` if fetching proves necessary. `ROADMAP.md`, `RESULTS.md`, and
`TDD.md` are supervisor-owned and are NOT touched by this run.
