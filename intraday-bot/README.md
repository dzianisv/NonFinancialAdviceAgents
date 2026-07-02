# intraday-bot

Foundation layer for crypto intraday/swing strategy discovery. Plain Python package, no
framework. Everything downstream (strategies, live/paper execution) plugs into `core/`.

> Educational analysis, not financial advice. Backtests do not guarantee future results.
> "No edge found" is a valid, valuable result of this pipeline — never loosen costs, fills,
> or date windows to manufacture a PASS.

## Layout

```
intraday-bot/
  core/
    data.py       Binance Vision monthly/daily kline downloader + loader. Parallel
                   download, parquet cache under data/. Hard timestamp-unit assertion
                   (Binance ms -> microseconds switch, 2025).
    fills.py       Maker-fill simulator: trade-through (not touch) rule, queue-position
                   haircut, adverse-selection tracking, no-fill fallback, stress tiers.
    costs.py       Cost model: Alpaca Crypto maker 0.15%/taker 0.25% per side, stress
                   multipliers, $0.01 min-fee floor.
    gate.py        The strategy-discovery-backtest gate: IS/OOS split, rolling walk-
                   forward, deflated Sharpe, regime windows, stress suite, metrics
                   contract, look-ahead canary.
    universe.py    Point-in-time top-N USDT universe builder (90d listing gate, honest
                   delisted-coin coverage report). A verifier-found bug (rolling
                   30d-volume window let a delisted coin linger in "top-N" membership
                   for ~15 days on stale data) was FIXED 2026-07-02: membership is now
                   additionally gated on each symbol's last observed data date — see
                   RESULTS.md xs_momentum verifier notes. Gated results were re-run with
                   the fix; verdicts unchanged.
  strategies/      Gated strategy candidates: regime_sma_maker.py, xs_momentum.py,
                   meanrev_maker.py (all FAIL, see RESULTS.md), dummy_flat.py (smoke-test
                   only, never a live strategy_ref).
  bot/             Notify/paper/live execution daemon — see "Running the bot" below.
  deploy/          GCP e2-micro deploy artifacts (nothing provisioned by this repo) — see
                   deploy/README-DEPLOY.md.
  data/            Downloaded parquet cache (gitignored — '*' — never commit market data).
  tests/           pytest unit tests for every core module.
  scripts/         download_all.py, basis_check.py, harness_self_test.py, and one
                   run_<strategy>_gate.py / chart_<strategy>.py pair per gated strategy —
                   the reproducible entry points described below.
  results/         Gate-run JSON artifacts (committed, one per strategy) — the source of
                   truth every number in RESULTS.md is cross-checked against.
  reports/         Per-strategy narrative write-ups (implementer's report; RESULTS.md is
                   the final, verifier-reconciled version).
  report/          Output charts / run artifacts (gitignored data, code tracked).
  RESULTS.md       Final, verified results across all gated strategies — read this first.
```

## Conventions (binding, hardcoded once, reused everywhere)

- **All timestamps UTC.** Every DataFrame loaded via `core.data.load()` has a UTC-aware
  `pd.DatetimeIndex`; loading a naive-tz cache file raises.
- **Weekly boundary = Monday 00:00 UTC.** Single shared constant/function:
  `core.gate.week_start_utc()` / `WEEK_START_DOW = 0`. Never redefine this elsewhere.
- **Signals decide on PRIOR bar close only — no look-ahead.** A strategy is a function
  `signals(df_dict, params) -> position(s) indexed by bar`. The harness independently
  verifies this with two checks on every gate run:
  - `core.gate.look_ahead_canary()` — corrupts one bar's OHLC and asserts the strategy's
    signal at/before that bar is unchanged.
  - `core.gate.shift_collapse_check()` — re-runs with one extra bar of lag and checks
    Sharpe doesn't collapse (a collapse is the tell for a strategy that was secretly
    peeking at same-bar/future data).
- **Net of costs ALWAYS.** `core/costs.py` is the only place fee rates are hardcoded:
  Alpaca Crypto maker 0.15%/side, taker 0.25%/side; forced/timeout exits ALWAYS pay taker.
  A `$0.01` minimum notional-fee floor applies per order.
- **Honest reporting.** OOS numbers are the headline. IS is context only. "FAIL / no edge"
  is a valid outcome — never relax costs/fills/dates to force a PASS. That is reward-hacking
  the gate and is treated as a firing offense in this repo.
- **$500 book constraints** (once this reaches execution, not enforced in this backtest
  layer): max order $250, max position $500, no shorts, no leverage — see
  `connectors/hard_caps.py` at the repo root for the deterministic risk layer.

## Maker-fill model (core/fills.py) — exactly what is implemented

1. **Trade-through, not touch.** A resting BUY limit fills only if `low <= limit*(1-0.0001)`
   (>= 1bp through). SELL mirrors: `high >= limit*(1+0.0001)`. Touching the limit exactly is
   NOT a fill.
2. **Queue-position haircut (deterministic, no RNG).** Base tier = rule 1's flat 1bp
   trade-through (the assumed p_fill≈0.8 average outcome is baked into that criterion, not
   drawn from a random number). The stress "reduced fill probability" tier (`stress_fill_prob=True`,
   proxy for p_fill≈0.4) requires trade-through by **>= 0.25 × the bar's high-low range** —
   a strictly harder bar to clear, which mechanically produces a lower realized fill rate.
   Deterministic and reproducible: identical OHLC in -> identical fill/no-fill out, always.
3. **Adverse selection.** After every fill, `core.fills.adverse_drift()` records the next
   bar's close-to-close return against the position just taken. Reported as a metric — if
   mean maker savings (vs. taker) is smaller than mean adverse drift, the maker "win" is
   fake and the report says so explicitly.
4. **No-fill fallback.** Entry limit that doesn't fill on its bar -> signal is SKIPPED
   (not carried forward), tracked as opportunity cost (count + would-be gross return
   logged, never counted as realized P&L). Exit limit unfilled within `timeout_bars` ->
   forced MARKET exit, paying taker (0.25%) + slippage.
5. **Stress tiers (each a separate full run):**
   - (a) 2x fees — `core.costs.STRESS_2X_FEES`
   - (b) all fills delayed one bar — `delay_bars=1`
   - (c) reduced fill probability — `stress_fill_prob=True` (see rule 2)
   - (d) worst-5%-vol bars get +10bp slippage — `extra_slip_worst_vol=True` with a
     precomputed `vol_p95_threshold` (see `core.fills.vol_p95_threshold()`)
6. **Fee floor.** `core.costs.fee()` applies a `$0.01` minimum notional fee per order.

## Data (core/data.py)

Source: `https://data.binance.vision/data/spot/{monthly,daily}/klines/<SYMBOL>/<interval>/...zip`.
Monthly zips cover completed months; the `daily` endpoint fills the current, still-open month.
Cached as merged parquet per `data/<SYMBOL>/<interval>/<SYMBOL>-<interval>-merged.parquet`.
Parallel download via `ThreadPoolExecutor` (default 8 workers, matching the house
`xargs -P8` convention).

**Timestamp-unit safety (critical):** Binance kline `open_time` was milliseconds
(13-digit epoch) through 2024; some 2025+ files switched to **microseconds** (16-digit
epoch). `core.data.detect_timestamp_unit()` asserts the magnitude explicitly and
`_normalize_open_time()` cross-checks the first and last row of every file agree — a
misparse (wrong unit, corrupt file, seconds-epoch, garbage) **raises**, it never silently
shifts the index. Verified against real Binance Vision files spanning the ms->us boundary
(see coverage below).

Columns: `open_time, open, high, low, close, volume, close_time, quote_vol, count,
taker_buy_base, taker_buy_quote` (Binance's `ignore` column is dropped after normalization).

## core/gate.py — the pipeline

```
canary            look_ahead_canary() + shift_collapse_check() — must pass before any
                   metric is trusted.
IS select         grid search over param_grid, best Sharpe on IS_START..IS_END
                   (2020-01-01 .. 2023-12-31).
OOS headline       best IS params, scored fresh on OOS_START.. (2024-01-01 -> latest).
walk-forward       rolling: fit N months -> score next M months -> roll by M; OOS windows
                   concatenated into one continuous OOS series (default fit=12mo, score=3mo).
deflated Sharpe     Bailey & Lopez de Prado (2014) formula, implemented from scratch (no
                   scipy dependency — Acklam's inverse-normal-CDF approximation), takes
                   n_trials (= len(param_grid)) and haircuts for multiple-testing.
regimes            2021 bull, 2022 LUNA/FTX, 2023-24 recovery, 2025 drawdown, 2026 YTD.
stress suite        2x fees, 1-bar delayed fills (cost-model-level; the bar-level fill-sim
                   stress tiers live in core/fills.py and are exercised directly by
                   scripts/harness_self_test.py + tests).
verdict            PASS only if: OOS Sharpe > 0, deflated-Sharpe probability >= 0.95,
                   AND the edge survives both stress runs. Else FAIL (no edge found).
```

Strategy interface: `signals(df_dict: dict[str, DataFrame], params: dict) -> pd.Series |
dict[str, pd.Series]` of target positions indexed by bar, decided on **prior bar close
only**. The harness (not the strategy) owns fill simulation via `core/fills.py`, so a
strategy cannot hand-pick favorable fills.

## core/universe.py

Point-in-time top-N USDT pairs by **trailing 30d quote volume**, computed only from data
available as of each date (no look-ahead in membership). A coin enters the universe only
after **90 days** of listed history. `coverage_report()` documents exactly which
delisted/faded Binance pairs we attempted and which were actually fetchable from
`data.binance.vision` — see the coverage note below; Binance does not publish an official
delisted-symbol registry, so this coverage is honest-best-effort, not exhaustive.

## Running tests

```bash
cd intraday-bot
/Users/engineer/.venv/bin/python3 -m pytest tests/ -v
```

## Running the gate on a strategy

```python
from core import data, gate
btc = data.load("BTCUSDT", "1d")
report = gate.gate(my_strategy_fn, {"BTCUSDT": btc}, param_grid=[...], interval="1d")
print(report["verdict"], report["reasons"])
```

## Reproducible entry-point scripts

```bash
# Download the full spec'd universe (1d ~40 pairs, 1h/5m BTC-ETH-SOL)
/Users/engineer/.venv/bin/python3 scripts/download_all.py

# Coinbase vs Binance BTC/ETH basis check (last 12 months)
/Users/engineer/.venv/bin/python3 scripts/basis_check.py

# Harness self-test: deterministic pseudo-random strategy (net ≈ -cost drag) +
# buy-and-hold BTC benchmark (OOS Sharpe net of one entry fee) — single command,
# fully reproducible (fixed seed=1337).
/Users/engineer/.venv/bin/python3 scripts/harness_self_test.py
```

## Data coverage

See the run log for exact symbol/interval/first-date/last-date/row-count coverage
(printed by `scripts/download_all.py` and captured in `data/download_log.txt`). Any
delisted/faded pair that failed to download is listed explicitly, not silently dropped.

## Gated strategy results

**Read [`RESULTS.md`](RESULTS.md) first.** Three strategies have been run end-to-end
through the gate (flat-cost + bar-by-bar maker-fill simulation) and independently
verified: `regime_sma_maker`, `xs_momentum`, `meanrev_maker`. **All three FAIL — 0 PASS,
nothing trades, nothing is even paper-trading yet.** `regime_sma_maker` has a real,
stress-surviving positive Sharpe that fails purely on statistical-significance grounds
(deflated Sharpe); the other two have genuinely negative gross edge. See `RESULTS.md` for
the full per-strategy spec/metrics/stress/verifier verdict, and
`backtests/results/intraday_bot_summary.txt` for the dead-idea-log entry (do not
re-test these exact idea/timeframe/universe combinations without new evidence).

To re-run a strategy's gate from scratch:

```bash
cd intraday-bot
/Users/engineer/.venv/bin/python3 scripts/run_regime_sma_maker_gate.py      # flat-cost gate half -> results/regime_sma_maker_gate.json
/Users/engineer/.venv/bin/python3 scripts/run_regime_sma_maker_fillsim.py   # fill-sim half -> results/regime_sma_maker_fillsim.json
/Users/engineer/.venv/bin/python3 scripts/run_xs_momentum_gate.py
/Users/engineer/.venv/bin/python3 scripts/run_meanrev_maker_gate.py
```

Each writes its `results/<strategy>.json` (diff against the committed version — should be
byte-identical apart from wall-clock fields). `scripts/chart_<strategy>.py` (where
present) regenerates the `report/img/*.png` charts.

**Reproducibility gap (P1, flagged by the verifier) — CLOSED 2026-07-02:** the flat-cost
IS/OOS/DSR/walk-forward numbers (`results/regime_sma_maker_gate.json`) originally had no
committed driver script; the verifier reproduced them by calling `core.gate.gate()`
directly against `strategies/regime_sma_maker.py`. `scripts/run_regime_sma_maker_gate.py`
(mirroring the pattern of the other two strategies) now exists and regenerates that
artifact with one command. The consolidated `results/regime_sma_maker.json` combines that
gate output with the fill-sim artifact plus curated n_trials-accounting/narrative fields;
its numeric sections are synced from the two script-generated artifacts.

## Running the bot (`bot/`)

Three modes, set in `bot/config.yaml` (`mode: notify|paper|live`). **Default is
`notify`, which touches zero broker credentials, ever.**

```bash
cd intraday-bot
/Users/engineer/.venv/bin/python3 bot/runner.py --config bot/config.yaml --once   # one cycle
/Users/engineer/.venv/bin/python3 bot/runner.py --config bot/config.yaml          # daemon loop
```

- **`notify` (default):** fetches public Alpaca/Coinbase market data, computes signals via
  `strategies/<strategy_key>.py`, sizes against the hardcoded $500-book caps
  (`bot/caps.py`), and writes an audit-logged, human-approvable ticket. Never contacts a
  broker.
- **`paper`:** same caps + audit path, then places a real post-only limit order on
  Alpaca's **paper** account (`ALPACA_PAPER_KEY`/`ALPACA_PAPER_SECRET` env). No real
  funds. **This is where a PASS strategy goes first** — never straight to live.
- **`live`:** deliberately gated stub. Refuses unless `CONFIRM_LIVE=<today's UTC date>`
  env, `ALPACA_LIVE_KEY` present, a named `strategy_ref`, and hard caps pass — and even
  then stays a stub (does not place real orders) until a human wires the final call. See
  `deploy/README-DEPLOY.md` for the full gate explanation and env-var table.

There is currently **no PASS strategy to point `strategy_key` at** — `bot/config.yaml`
ships pointed at `strategies/dummy_flat.py`, explicitly a smoke-test-only strategy, never
to be used as a live `strategy_ref`. Caps are hardcoded in `bot/caps.py` and **not**
overridable from `config.yaml` (`load_config()` raises `ConfigError` on any attempt to set
a risk-cap key there). **Alpaca note:** SOL is not tradable on Alpaca (confirmed via 3
independent sources) — only BTC/USD and ETH/USD from the "top 3" candidate set are
deployable; `bot/config.yaml`'s default `symbols` reflects this.

## Deploying (artifacts only — nothing provisioned)

`deploy/setup_gcp.sh` provisions a GCP e2-micro Debian 12 box (python venv, dedicated
non-root service user, systemd unit defaulting to `mode: notify`) when run **by a human,
on the target VM**. Nothing in this repo touches a real GCP instance or real credentials.
Full env-var table, Bitwarden `dev`-collection convention, and the live-mode gate
explanation: [`deploy/README-DEPLOY.md`](deploy/README-DEPLOY.md).
