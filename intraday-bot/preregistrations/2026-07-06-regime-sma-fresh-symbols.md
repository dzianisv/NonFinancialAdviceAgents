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

## Results

Run executed 2026-07-06 via `scripts/run_regime_sma_maker_fresh_symbols.py`, all 5
pre-registered symbols, zero errors, zero substitutions. Full report:
`results/regime_sma_fresh_symbols.json`. Confirmed data ranges before running (Step 3):
SOLUSDT 2151 daily bars (2020-08-11 -> 2026-07-01, its actual Binance listing date), XRPUSDT
/ DOGEUSDT / ADAUSDT / LINKUSDT each 2374 daily bars (2020-01-01 -> 2026-07-01).

Primary OOS window for all 5 symbols: 2024-01-01 -> 2026-07-01 (913 bars each — the actual
last cached bar, matching the expectation).

### Per-symbol table (primary OOS window, 2024-01-01 -> 2026-07-01)

| Symbol | OOS Sharpe | CAGR | MaxDD | Hold Sharpe | Beats hold (Sharpe)? | 2x-fee stress: gate | 2x-fee stress: fillsim | Delayed-fill stress: gate | Delayed-fill stress: fillsim | DSR@N=5 (informational) | Counts toward majority? |
|---|---:|---:|---:|---:|:---:|---:|---:|---:|---:|---:|:---:|
| SOLUSDT  | -0.136 | -16.2% | -58.8% |  0.180 | No  | -0.240 | -0.157 | -0.211 | **-1.257** | 0.080 | **No** |
| XRPUSDT  |  0.534 |  20.6% | -60.7% |  0.595 | No  |  0.413 |  0.510 |  0.292 | **-0.308** | 0.373 | **No** |
| DOGEUSDT |  0.413 |   9.8% | -76.3% |  0.309 | Yes |  0.332 |  0.385 |  0.548 | **-0.078** | 0.298 | **No** |
| ADAUSDT  | -0.470 | -30.1% | -73.9% | -0.192 | No  | -0.602 | -0.539 | -0.361 | -1.600 | 0.027 | **No** |
| LINKUSDT |  0.081 |  -7.1% | -47.9% |  0.033 | Yes | -0.037 |  0.037 |  0.039 | **-1.005** | 0.144 | **No** |

Bold marks the sign that decides a fail against the majority test. Gate's own internal
verdict (its full pass/fail logic, including the DSR>=0.95 clause, not just the
pre-registered majority rule above) is **FAIL** for all 5 symbols independently — see
`gate_primary.reasons` per symbol in the JSON.

**0 of 5 symbols count toward the majority** (need >=3 of 5): none simultaneously (a) beat
their own buy-and-hold on OOS Sharpe AND (b) stayed Sharpe-positive under both the 2x-fee and
delayed-fill stress tiers on BOTH methodologies.

- SOLUSDT, ADAUSDT: fail immediately on (a) — the frozen rule underperforms buy-and-hold on
  a risk-adjusted basis (and both have negative absolute OOS Sharpe).
- XRPUSDT: fails on (a) — hold Sharpe (0.595) edges out the frozen rule (0.534); also fails
  the delayed-fill fillsim tier (-0.308) regardless.
- DOGEUSDT: the one symbol that beats its own hold benchmark on Sharpe (0.413 vs 0.309) and
  clears every gate-side stress tier — but the honest fillsim's delayed-fill tier goes
  negative (-0.078), so it does not clear the "both methodologies" bar.
- LINKUSDT: beats hold on Sharpe (0.081 vs 0.033) but fails the gate's own 2x-fee stress tier
  (-0.037) and the fillsim's delayed-fill tier (-1.005).

**Gate-vs-fillsim disagreement, stated explicitly (not smoothed over), exactly as
pre-registered as a possibility:** the flat-cost gate's analytic delayed-fill tier and the
honest bar-by-bar fillsim's delayed-fill tier **disagree in sign for 3 of 5 symbols**
(XRPUSDT: gate +0.292 vs fillsim -0.308; DOGEUSDT: gate +0.548 vs fillsim -0.078; LINKUSDT:
gate +0.039 vs fillsim -1.005). In every one of these cases the gate's simplified one-bar
weight-shift approximation reads Sharpe-positive while the honest fill simulator — which
actually walks the maker-limit-order mechanics bar by bar — reads meaningfully
Sharpe-negative. This is the same pattern the pre-registration flagged as having occurred for
BTC in the existing ledger (ROADMAP.md Section 1), and it recurred here on a majority of the
fresh symbols. This disagreement is reported as-is; the mechanical verdict above already
requires a symbol to clear BOTH methodologies, so it does not get averaged or waived.

### Secondary (full available history per symbol; NOT used for the verdict)

| Symbol | Full-history Sharpe | Full-history CAGR | Full-history MaxDD | Full-history hold Sharpe |
|---|---:|---:|---:|---:|
| SOLUSDT  | 1.278 | 112.7% | -69.7% | 1.001 |
| XRPUSDT  | 0.441 |  11.7% | -83.5% | 0.706 |
| DOGEUSDT | 0.796 |  98.2% | -86.5% | 0.789 |
| ADAUSDT  | 0.851 |  48.8% | -73.9% | 0.683 |
| LINKUSDT | 0.250 |  -6.3% | -88.0% | 0.696 |

Reported for context only, per the pre-registration: these symbols contributed zero
information to the original IS tuning (sma_window=50 was chosen using only BTC/ETH), so there
is no real IS/OOS split here — full-history numbers are descriptive, not confirmatory. Note
the full-history picture is NOT uniformly better than the OOS picture (XRPUSDT and LINKUSDT
underperform hold on full history too); this is not evidence being cherry-picked toward a
pass.

### Overall verdict (applying the pre-registered interpretation rule mechanically)

**FAILED CONFIRMATION.** 0 of 5 pre-registered symbols clear the majority bar (>=3 of 5
required). Per the pre-registered rule, this is treated as **evidence AGAINST the
`regime_sma_maker` family**, precisely because zero parameters were changed to produce this
result — the frozen BTC-winning rule (sma_window=50, identical cost/execution model) was
applied unmodified to 5 fresh, never-tuned-on symbols and it does not reliably beat
buy-and-hold on a risk-adjusted, stress-surviving basis on any of them under both cost
methodologies simultaneously.

**What this does and does not mean, stated plainly:** this FAIL does not by itself prove the
family has zero edge anywhere — DOGEUSDT and LINKUSDT both individually beat their own hold
benchmark on OOS Sharpe, and the family's underlying BTC/ETH edge was never in question here
(that question is already settled, separately, by the DSR<0.95 firewall). What this result
adds is a modestly-informative, N_eff ~1.2-1.4 falsification check, and it came back negative:
the frozen rule's apparent edge does not generalize cleanly to this basket of correlated
large-cap alts once the same honest cost/fill stress bar is applied. Combined with the
family's pre-existing DSR firewall (0.39 BTC / 0.30 ETH at N=5), there is now no open evidence
stream pointing toward `regime_sma_maker` other than the forward-calendar-time shadow run
already in progress (ROADMAP.md Section 5's second sanctioned path). This result does **not**
change the family's cumulative trial count (stays N=5) and does **not** reopen deployment —
per the pre-registered rule, even a PASS here would not have done that.

## Scope of this run (files touched)

This run only writes to: `intraday-bot/preregistrations/` (this file, plus its Results
section appended after the run), `intraday-bot/results/` (new JSON), an append to
`intraday-bot/TRIAL_LEDGER.md`, a new script
`intraday-bot/scripts/run_regime_sma_maker_fresh_symbols.py`, and any newly-downloaded data
files under `intraday-bot/data/` if fetching proves necessary. `ROADMAP.md`, `RESULTS.md`, and
`TDD.md` are supervisor-owned and are NOT touched by this run.
