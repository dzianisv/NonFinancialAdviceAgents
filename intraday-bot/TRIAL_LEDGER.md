# intraday-bot — Trial Ledger

**This file is append-only.** One row per configuration ever scored against out-of-sample
(OOS) data, grouped by family. Created 2026-07-02 per
`reports/research-roadmap-2026-07-02.md` Section 5 ("Process changes").

## Rules (binding)

1. **N never resets.** `cumulative_family_n_trials` is a running total per family. Renaming
   a strategy, "starting a new investigation," or re-launching the same idea under a new
   script name does not reset it. The deflated Sharpe ratio (DSR) gate in `core/gate.py`
   must always be graded at the family's current cumulative N, not the count from a single
   run.
2. **Pre-registered grid size = N increment.** The multiple-comparisons event is *choosing
   the IS winner from a grid*, not the single OOS look that follows. Committing a frozen
   param grid before touching 2024–2026H1 data, then picking the winner from IS-only
   (2020–2023) data, adds `len(grid)` to family N — even though only one config per
   symbol/universe is ultimately scored on OOS.
3. **OOS is single-use per config.** One observation per config, ever. A retune after
   seeing OOS performance is a new trial (N += 1) and must be evaluated on fresh forward
   bars, not re-scored against the window it just lost on.
4. **Every future gate run reads this ledger first.** "New investigation" framing does not
   reset N; the ledger is the source of truth for what N to grade at.
5. **Append only.** Never edit or delete a past row. Corrections get a new row with a note,
   not a silent rewrite.

Columns: **Date** = when the config was scored against OOS (best available; June entries
predate this ledger and are reconstructed from `results/regime_sma_maker.json`'s
`n_trials` note, not from original run logs — exact IS/OOS numbers for those 3 are marked
unknown rather than fabricated). **Git commit** = repo commit the run was produced under,
where known. **Family N (after)** = cumulative family count including this row.

---

## Family: `regime_sma_maker` (BTC/ETH "price above N-day SMA" trend-following)

**Status: standing dead family (firewalled 2026-07-02) — real, reproducible, stress-surviving
edge, but fails DSR ≥ 0.95 even after the units-bug fix (0.66 BTC / 0.55 ETH at N=2, 0.39 /
0.30 at the honest N=5). No further retunes inside this family; the only sanctioned next
evidence is (a) forward calendar time via the notify-mode shadow deployment, scored at the
same N=5, or (b) a pre-registered, zero-parameter-change confirmation run on a fresh symbol
set (logged as confirmation evidence, not a new config — see roadmap Section 5).**

| # | Date | Config | Symbol | Git commit | IS Sharpe | OOS Sharpe | Family N (after) | Notes |
|---|---|---|---|---|---:|---:|---:|---|
| 1 | June 2026 | TSMOM N=30 | unknown | unknown | unknown | unknown | 1 | Pre-ledger trial; name only, per `results/regime_sma_maker.json`'s `n_trials.june_trial_names`. Exact IS/OOS not reconstructed — not fabricated here. |
| 2 | June 2026 | SMA N=50 | unknown | unknown | unknown | unknown | 2 | Pre-ledger trial; name only, same source as above. |
| 3 | June 2026 | REGIME-SMA(BTC>200d) N=50 | unknown | unknown | unknown | unknown | 3 | Pre-ledger trial; name only, same source as above. |
| 4 | 2026-07-01/02 | Grid `{sma_window: 50, 200}`, IS-selected 2020–2023, scored once OOS 2024-01-01→2026-07-01. Winner: BTC→N=50, ETH→N=200. | BTC | 08b692d | 1.275 | 0.576 | 4 | This grid is 1 config-count of 2 shared across both symbols (`this_run_per_symbol: 2` in the JSON means "grid size 2," not "2 per symbol" — confirmed by `n_trials=2` used identically in both symbols' DSR call). Counted once here at row 4; ETH's OOS look (row 5) shares this same grid and does not add a second +2. |
| 5 | 2026-07-01/02 | Same grid as row 4 (shared, not a new grid) | ETH | 08b692d | 1.334 | 0.410 | 5 | See row 4 note — this row completes the family N=5 total (3 June + 2 this grid), it does not add its own +2. |

**Corrected DSR at family N=5** (moment-adjusted, per-bar, `core/gate.py` fix 2026-07-02):
BTC dsr=0.39 (z=-0.27), ETH dsr=0.30 (z=-0.54) — both < 0.95. **FAIL** at the honest
cumulative count, same verdict as at N=2.

---

## Family: `xs_momentum` (cross-sectional momentum, top-N by trailing K-day return, weekly rebalance)

**Status: standing dead family (firewalled 2026-07-02) — textbook overfit (IS Sharpe 1.77
→ OOS Sharpe -0.57, a sign flip), loses to naive equal-weight hold of its own candidate
universe. No further retunes; a different ranking signal or rebalance cadence would be a
new family, not a trial in this one.**

| # | Date | Config | Universe | Git commit | IS Sharpe | OOS Sharpe | Family N (after) | Notes |
|---|---|---|---|---|---:|---:|---:|---|
| 1–6 | 2026-07-01/02 | Pre-registered grid `{lookback_days: 7,14,28} × {top_n: 3,5}` (6 configs), IS-selected 2020–2023, one winner scored once OOS. Winner: lookback=28, top_n=5. | 46 USDT-major coins, point-in-time top-30-by-volume | 08b692d | 1.770 | -0.574 | 6 | Only the winning config's IS/OOS metrics are persisted in `results/xs_momentum.json`; the other 5 grid candidates' IS-only numbers were not retained by the harness and are not reconstructed here. No prior (pre-ledger) trials found for this family in `reports/research-roadmap-2026-07-02.md`. |

**Corrected DSR at N=6:** dsr=0.01 (z=-2.21) — irrelevant to the verdict: OOS Sharpe is
already negative, so the family fails on raw edge regardless of any significance
correction.

---

## Family: `meanrev_maker` (5-minute rolling z-score mean-reversion, resting maker limits)

**Status: standing dead family (firewalled 2026-07-02) — gross (pre-fee) edge is negative
across all 27 grid configs on IS data (best IS Sharpe -9.33); this is not an overfitting
story, the entire family is broken. Execution layer (fill mechanics) was independently
validated as sound — the signal itself is dead. No further retunes; this specific
z-score/rolling-mean entry trigger is closed to further trials at any lookback/k/timeout
combination already covered by the grid.**

| # | Date | Config | Universe | Git commit | IS Sharpe | OOS Sharpe | Family N (after) | Notes |
|---|---|---|---|---|---:|---:|---:|---|
| 1–27 | 2026-07-01/02 | Pre-registered grid `{lookback} × {k} × {timeout_bars}` = 3×3×3 = 27 configs, IS-selected 2020–2023, one winner scored once OOS. Winner: lookback=48, k=2.0, timeout_bars=24, stop_k=2.0. | BTC/ETH/SOL, 5-minute bars | 08b692d | -9.333 | -10.302 | 27 | Only the winning config's IS/OOS metrics are persisted in `results/meanrev_maker.json`; the other 26 grid candidates' IS-only numbers were not retained by the harness and are not reconstructed here. Every one of the 27 configs failed on IS (best IS Sharpe -9.33), so the winner shown here is the *least bad* of 27 losers, not a promising candidate. |

**Corrected DSR at N=27:** dsr=0.00 (z=-18.53) — irrelevant to the verdict: OOS Sharpe is
catastrophically negative, so the family fails on raw edge regardless of any significance
correction.

---

## Cumulative summary (as of 2026-07-02)

| Family | Cumulative N | Current DSR (at cumulative N) | Verdict | Firewall status |
|---|---:|---|---|---|
| `regime_sma_maker` | 5 | BTC 0.39 / ETH 0.30 | FAIL (DSR < 0.95) | Dead, firewalled — forward shadow-run data or fresh-symbol confirmation only |
| `xs_momentum` | 6 | 0.01 (moot — OOS Sharpe already negative) | FAIL (negative OOS edge) | Dead, firewalled |
| `meanrev_maker` | 27 | 0.00 (moot — OOS Sharpe already negative) | FAIL (negative OOS edge) | Dead, firewalled |

No candidate has ever cleared the gate's N=1 significance hurdle (annualized Sharpe ~1.04
on the 2.5y OOS window), let alone the higher hurdle its actual cumulative N demands. See
`reports/research-roadmap-2026-07-02.md` Sections 3–4 for the full arithmetic and the
"standing dead families" firewall list.
