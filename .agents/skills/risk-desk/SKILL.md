---
name: risk-desk
description: "Always-on risk layer for HELD equity/crypto-beta positions, modeled on Citadel/Millennium central-risk-desk mechanics. Runs deterministic price/concentration/cluster rules over the live positions book, independent of any alpha view, and fires TRIM/REVIEW breaches that OVERRIDE stocks-advisor's scorecard WAIT/HOLD. Delivers via the watchlist-alerts sheet pipeline. Triggers: \"run risk desk\", \"check for trend breaks\", \"any positions breaching risk limits\", \"is anything oversized / rolling over\"."
license: MIT
compatibility: opencode
metadata:
  audience: equity-allocators
  domain: portfolio-risk-management
  role: risk-manager
  source: "Built after the NEM incident (2026-06/07): scorecard.py scored NEM WAIT while it sat 8%+ of book, +100%+ gain, and broken below its 200d MA for weeks — nothing in the picker layer is designed to ask 'is this still sized right', only 'is this worth buying more of'."
---

# risk-desk

## risk-desk is NOT a picker

`stocks-advisor`'s `scorecard.py` `decide()` answers one question: **is this a good time to add?**
Its WAIT verdict ("cheap but downtrending — do not add") is the *correct* answer to that question and a
*useless* answer to a completely different one that nothing else in the stack was asking: **is this
position still sized right, given what it's already done?**

`risk-desk` asks only the second question, continuously, over the positions actually held — not the
universe of names being screened for entry. It has no opinion on valuation, growth, or thesis. It runs
independently of the alpha view and, on held positions, **risk overrides alpha**: a scorecard WAIT or HOLD
does not block a risk-desk TRIM/REVIEW from firing or being delivered. This mirrors how central risk desks
at multi-strat funds (Citadel, Millennium) work — PMs pick names, but a separate, mechanical risk function
polices size, drawdown, and correlation across the whole book regardless of what any PM's view is.

See `docs/architecture.excalidraw.json` for the full system diagram (Data → Alpha/Picker (on-demand) +
Risk Desk (always-on) → Delivery).

## The NEM case study (why this exists)

Through late June 2026, NEM sat at **8.3–8.9% of book** with an unrealized gain the project's own memory
logs recorded as **+112% to +120%**, and had rolled over below its 200-day moving average. `scorecard.py`
correctly scored it **WAIT** — cheap valuation, downtrend, don't catch the knife — which is right for "should
I buy more" and silent on "should I still hold this much." Nothing ever trimmed it.

Checked against live Yahoo data for this build: NEM's daily close **crossed below its 200d MA on
2026-06-22** (with a brief false reclaim on 2026-06-15 after an earlier 2026-06-05 break), and was still
below on 2026-07-16, roughly **3–4 weeks** of an unaddressed trend break on a position that was, at various
points in that window, both oversized (5%+) and a large locked-in winner. Had `risk-desk` been running on a
cron cadence alongside `watchlist-alerts`, **R1 (TREND_BREAK)**, **R3 (CONCENTRATION_REVIEW)**, and **R4
(WINNER_ROLLOVER)** would all have fired within days of the 2026-06-22 break — independent of, and
overriding, the scorecard's WAIT.

Caveat for the live verification run in this build (2026-07-16 positions snapshot): the `Unrealized_PnL`
field for NEM in `positions_live_2026-07-16.csv` is `0`, which this script treats as **unknown, not a real
0% gain** (see Rules below) — so on *that specific snapshot*, R2/R4 (which require a known gain ≥50%)
correctly did not fire; only R1 and R3 (REVIEW tier) fired. This is not a bug in risk-desk, it's a gap in
that day's PnL data for a subset of rows — the rule guards against a worse failure mode (silently reporting
a real winner as flat).

## Rules

All rules are deterministic and evaluated independently — a position can breach several at once, and every
breach is reported (no first-match-wins short-circuit across rules, except within R3's own tiers).

| # | Rule | Condition | Directive |
|---|---|---|---|
| R1 | `TREND_BREAK` | weight ≥ 3% AND price < MA200 | `TRIM-REVIEW: trend broken on a meaningful position` |
| R2 | `GIVE_BACK` | gain ≥ 50% AND price ≤ 52wk-high × 0.70 (given back ≥30% off the high) | `TRIM: winner giving back gains` |
| R3 | `CONCENTRATION` (tiered, first match wins within R3) | weight ≥ 15% → **HARD CAP**; else weight ≥ 10% AND price < MA200 → **TRIM**; else weight ≥ 5% AND price < MA200 → **REVIEW** | `HARD CAP: trim to 15%` / `TRIM: oversized + trend broken` / `REVIEW: sizeable position below trend` |
| R4 | `WINNER_ROLLOVER` (the NEM rule) | weight ≥ 5% AND gain ≥ 50% AND price < MA200 | `TRIM: large locked-in winner rolling over — protect the gain` |
| R5 | `CLUSTER` | static sleeve weight > 12% (`gold`: NEM/GDX/PHYS/GLD/PSLV; `crypto_beta`: COIN/TONX/CRCL/HOOD/BTC; `ai_semis`: MRVL/AVGO/QCOM/TSM/MU/SNDK/INTC/AMD/ASML/NVDA) | `CLUSTER REVIEW: <sleeve> sleeve at X%` |

R1/R2/R4 are per-position and price-conditional — these are the ones `--arm` can turn into standing
Watchlist tripwires. R3/R5 are portfolio-level (concentration/cluster), reported every run but never armed
as a standalone alert (they need a whole-book re-run to re-evaluate, not a price crossing).

**Gain% and the PnL=0 guard.** `gain% = PnL / (MV − PnL) × 100`. A `PnL` of exactly `0` is treated as
**unknown/not tracked for that lot**, not a genuine 0% gain — several rows in the live positions snapshot
carry a hard 0 because that lot's cost basis hasn't been reconciled, and reporting those as "flat" would
silently suppress R2/R4 on real winners. Divide-by-zero and a degenerate (≤0) cost basis are guarded the
same way.

## Mandate clamp

`COIN` and `TONX` are held under a standing crypto-beta mandate (per user instruction, not a portfolio
default) — risk-desk never suppresses a breach on them, but it never issues a trim instruction either. Any
R1–R4 breach on a mandate-clamped symbol is still reported in the table and still armable, but its
directive is replaced with:

```
[MANDATE-CLAMPED — surfaced, not auto-trimmed; tripwire]
```

When armed, mandate-clamped rows are written with `Status = ACTIVE_REVIEW_ONLY` (the same status
`watchlist-alerts.ts` already treats as "no auto-action" — its Telegram message gets a `⚠️ REVIEW ONLY`
banner automatically), instead of `ACTIVE`.

## CLI usage

```bash
bun .agents/skills/risk-desk/scripts/risk-desk.ts [--positions <csv>] [--arm] [--json]
```

- `--positions <csv>` — defaults to the newest `.cache/stocks-daily/positions_live_*.csv` by filename date,
  falling back to `.cache/stocks-daily/positions.csv`. Columns matched by header name: `Position`,
  `MarketValue`, `Unrealized_PnL` (extra columns ignored). Non-equity rows (Cash, T-Bills, money-market
  sweeps) are counted toward total book weight but skipped for market-data evaluation.
- `--arm` — for every R1/R2/R4 breach, **upserts** an `ACTIVE` (or `ACTIVE_REVIEW_ONLY` if mandate-clamped)
  row into the Watchlist sheet (spreadsheet `1aunLbpNGo85WqrMHiIsy6nFUija4Lnjot-rIhE-pGU8`, tab
  `Watchlist`), Alert ID `risk-<symbol>-below-<MA200 rounded>`, Desk `risk`. Idempotent — skips if that
  exact Alert ID already exists anywhere in the sheet. **Default is off** (report-only); without `--arm` the
  script prints exactly what it *would* arm.
- `--json` — also prints a machine-readable JSON summary (positions, breaches, cluster breaches, arm
  candidates) after the human-readable report.

Market data: Yahoo v8 chart (`range=1y&interval=1d`), one fetch per unique symbol per run (cached), same
`User-Agent` convention as `watchlist-alerts.ts`. Computes latest close (price), SMA200 (null if fewer than
200 closes), 52-week high (max daily high), and Wilder RSI14. Symbol remapping: `BRK.B` → `BRK-B`,
`BTC` → `BTC-USD`. A fetch failure skips only that symbol's position, with a warning — it never aborts the
run.

## Cadence

Run alongside `watchlist-alerts` on the same cron cadence (see that skill's README for the Hermes/cron
pointer) — report-only (`--arm` off) is safe to run as often as desired; arming is idempotent so repeated
`--arm` runs are also safe, but the sheet write path should be exercised deliberately, not blindly
cron'd, until it's been run live at least once and reviewed.

```bash
bun /Users/engineer/workspace/backtest/.agents/skills/risk-desk/scripts/risk-desk.ts
# add --arm once the report-only output has been reviewed for a given day
```

## Files

- `scripts/risk-desk.ts` — the whole thing, one file, Bun built-ins only (`fetch`, `Bun.spawnSync`) plus the
  `gws` CLI on `PATH` (only invoked under `--arm`).
- `docs/architecture.excalidraw.json` — system diagram: Data → {Alpha/Picker (on-demand), Risk Desk
  (always-on)} → Delivery, with the NEM lesson annotated directly on the diagram.
