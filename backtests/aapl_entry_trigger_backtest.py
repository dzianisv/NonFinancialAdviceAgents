#!/usr/bin/env python3
"""
AAPL Entry-Trigger Gate Backtest — Does Waiting for a Technical Dip Beat Immediate Activation?
================================================================================================
strategy-discovery-backtest gate for a NEW hypothesis, distinct from (and downstream of) the
already-PASSed `aapl_weekly_dca_backtest.py` gate. That prior gate validated WHICH capped policy
to run once the AAPL satellite is active (10% target / 15% ceiling, "Standard capped satellite").
THIS gate asks a different, narrower question: **for that same approved policy, does adding a
price-only ENTRY TRIGGER (wait for a technical pullback before starting to buy AAPL) beat simply
activating immediately?** This operationalizes the `analyse-technical` lens's "pullback to a
rising MA" / "RSI confirmation" entry heuristic as a mechanical, backtested rule instead of a
narrative judgment call, per that skill's own instruction to "validate via
analyse-systematic-trading [i.e. this gate] before sizing."

>>> SURVIVORSHIP / SELECTION CAVEAT (carried over from the prior gate, holds regardless of
    outcome) <<<
AAPL was picked by the user WITH HINDSIGHT knowledge of its historical outperformance. Nothing
below validates a forward, repeatable edge for AAPL itself — it describes what already happened
to one stock. This gate can ONLY validate (or refute) an ENTRY-TIMING OVERLAY on a position the
user has already decided to build (via the prior gate) — it is NEVER proof that AAPL has forward
alpha, and it is NEVER proof that technical timing generalizes to other assets.

--------------------------------------------------------------------------------------------------
SPEC (predeclared before any data pull — every number below has a named CONFIG constant)
--------------------------------------------------------------------------------------------------
THE ONE ECONOMIC REASON AN EDGE MIGHT EXIST (Stage 0 of the gate, stated before touching data):
  Trend-following / "buy the pullback within an uptrend" is the ONE technical-analysis family
  with a robust (if modest) empirical base (per `analyse-technical`'s own honesty rules): buying
  after price has already given back some gains (closed at/below a trailing moving average, or
  short-term momentum has cooled per RSI) could plausibly reduce average cost basis vs. buying
  every week regardless of price level, IF pullbacks are followed by mean-reversion more often
  than by further, larger declines. This is a real, falsifiable hypothesis — not guaranteed to
  hold, which is exactly what this gate tests, net of costs and lag.

Universe / instruments: identical to the prior gate — AAPL (satellite candidate) + RSP (proxy for
the user's existing ~$710,445 diversified stock sleeve — NOT literal RSP holdings).

Initial state (identical at the start of EVERY window simulated — OOS headline, every rolling
cohort, every crisis window — each is a FRESH account starting from this state at ITS OWN start
date, matching the prior gate's already-approved initial state, never the live-date $289/$272
AAPL/RSP quotes on the day this script happens to run):
  - RSP-proxy stock sleeve  : $710,445
  - Direct AAPL position    : $26        (negligible but tracked, never zeroed)
  - New weekly contribution : $250       (decided at each complete Friday weekly close)

APPROVED STANDARD POLICY (post-activation, reused verbatim from the PASSed prior gate — this
gate does NOT re-litigate the policy itself, only WHEN it starts):
  target 10% / hard ceiling 15% direct AAPL (of AAPL+RSP, pending cash excluded). Each week,
  BEFORE deciding that week's $250, mark AAPL/RSP value from actual held shares (post any
  settlement/trim). If weight < target, route enough of the $250 toward (never past) target:
  solve x in (AAPL+x)/(AAPL+RSP+250) = target, x clipped to [0,250]; remainder -> RSP. If
  weight >= target, 100% -> RSP. At every CALENDAR QUARTER-END (last complete weekly bar
  on/before Mar/Jun/Sep/Dec), if AAPL weight > 15% ceiling, SELL AAPL down to EXACTLY the 10%
  target (not the ceiling) and route (cost-adjusted) proceeds to RSP. This is the ONLY
  rebalancing mechanism in this script, and it fires ONLY once a trial's policy is ACTIVE
  (pre-activation, the trim mechanic does not exist — see below).

Four trials — the ONLY thing that differs between them is WHEN the standard policy above
switches on ("activates"). Before activation, 100% of every week's $250 goes to RSP (no AAPL
buys at all — the tiny legacy $26 position just drifts in price, untouched); no quarter-end trim
check happens pre-activation. ACTIVATION IS A ONE-TIME, STICKY REGIME SWITCH: once triggered, the
standard policy runs for the remainder of that window, forever — even if the price signal later
flips back to "false". This models an ENTRY-TIMING decision (when to START the satellite,
matching `analyse-technical`'s framing of timing an entry into a position already justified on
other grounds), NOT a continuous on/off rebalancing signal.
  1. Immediate activation (benchmark) : standard policy active from week 0 of every window, no
     waiting at all. This is the prior gate's already-PASSed "Standard capped satellite (10%/15%)"
     variant, run unchanged, as the baseline every delayed trial must beat.
  2. Wait for weekly close <= 20-week EMA (AAPL, point-in-time): activates at week t+1 where week
     t is the first week whose COMPLETED Friday weekly close is <= AAPL's 20-week EMA as of that
     same week's close (the EMA is a point-in-time trailing indicator using only data through
     week t; see DATA/no-lookahead below).
  3. Wait for daily close <= 50-day SMA (AAPL) AND daily Wilder RSI(14) < 50, both evaluated at
     the completed Friday: activates at week t+1 where week t is the first week whose completed
     Friday daily close is <= the 50-day SMA (point-in-time, trailing 50 daily bars through that
     Friday) AND the daily Wilder RSI(14) (point-in-time, trailing) is < 50 on that same Friday.
  4. Wait for weekly close <= 20-week EMA AND daily Wilder RSI(14) < 50 (trial 2's weekly
     condition combined with trial 3's RSI sub-condition; does NOT require the 50-day SMA
     condition).
No-earlier-than-t+1 rule (structural, not a judgment call): a signal computed from week t's
COMPLETED close can only switch the policy on starting week t+1's decision. It is IMPOSSIBLE,
by construction (activation_start_index = signal_true_index + 1, asserted at runtime), for the
same week's close that produced the signal to ALSO be the first week the standard policy buys
AAPL under that signal — see self-checks.

Delayed-fill / cash queue (identical mechanic to the prior gate, always on, for ALL FOUR
trials): a contribution (or trim's proceeds) decided at week t's close becomes "pending cash",
invested at week t+1's close (one full week settlement lag), modeled as an explicit
per-instrument pending-cash queue. No shares may be created before their settlement week. Any
still-pending cash at a window's final week remains uninvested CASH in terminal value.

DATA / no-lookahead: yfinance AAPL & RSP, auto_adjust=True Close, longest common history,
resampled to weekly Friday (W-FRI, last available close each week). A trailing weekly bucket is
DROPPED if the raw daily data does not yet extend through that bucket's Friday (in-progress week
— asserted programmatically). ALL THREE signal inputs (20-week EMA, 50-day SMA, Wilder RSI14)
are computed as TRAILING indicators over AAPL's own FULL available daily/weekly price history
(from the earliest AAPL daily bar, well before RSP's own history begins in ~2003) — deliberately
NOT reset to zero warm-up at each window's own start date, because a real trailing indicator's
value at any given calendar date reflects genuine, already-public market history as of that
date, regardless of when a particular account happened to start; resetting it per-window would
be a MORE artificial construction, not a more honest one. Each signal value at row t depends
ONLY on price data at or before t (rolling/ewm windows, Wilder's recursive smoothing, and
`Series.asof`, none of which look forward) — proven structurally by construction and verified
empirically in self-checks (b) and (c) below.
  IS  : 2003-01-01 (or first common date if later) -> 2015-12-31    (context only)
  OOS : 2016-01-01 -> latest COMPLETE weekly close                   <- HEADLINE (verdict)
  Rolling 5y cohorts : start 2005, 2010, 2015, 2020 (fresh state each, truncated at the earlier
    of start+5y or the latest available data)
  Rolling 10y cohorts: start first-common-year, 2005, 2010, 2013 (same truncation rule)
  Crisis windows     : 2008 GFC (2007-10-01 -> 2009-03-31), 2020 COVID (2020-01-01 ->
    2020-12-31), 2022 rate-hike bear (2022-01-01 -> 2022-12-31) — fresh state each.

Costs (applied to EVERY buy/sell trade): base 2bps | stress 5bps | doubled-base stress 4bps |
PLUS an extra 25bps stacked ONLY on top of the doubled 4bps base, applied only to trades
EXECUTED in each trial's own worst-5%-return weeks (2-pass: identify worst-5% weeks from the
doubled-cost run, then re-run with the extra cost stacked on those specific execution dates).
The 1-week delayed fill is ALWAYS ON (structural, not a togglable stress). Predeclared threshold:
stress terminal wealth for EACH delayed trial must not be more than
MAX_STRESS_WEALTH_DEGRADATION_PCT worse than that SAME trial's own base-case terminal wealth,
OOS headline window (a trial is compared against ITSELF across cost scenarios here, not against
the immediate benchmark — the immediate-vs-delayed comparison is a separate PASS criterion below).

Metrics contract (all net of costs unless noted):
  - XIRR (money-weighted): weekly cashflow schedule of -$250 at every decision date, plus
    +terminal_account_value folded into the final cashflow. DOCUMENTED SPEC DEVIATION (identical
    to, and for the identical reason as, the prior gate): the initial $710,471 base IS included
    as an additional t0 outflow, NOT omitted — omitting it produces a mathematically
    ill-posed/meaningless IRR here (verified by hand: the $710k base dominates the $250/wk
    stream, forcing the solver to misattribute nearly all terminal growth to the tiny weekly
    stream, inflating IRR to >50%/yr for what is actually an ~11-14%/yr RSP-dominated period).
    Solved via scipy.optimize.brentq with a widening-bracket fallback.
  - Time-weighted weekly return series, annualized vol and Sharpe (blended risk-free rate per
    AGENTS.md convention: 5% 1999-2005, 3% 2005-2020, 4% 2020-2026, blended by calendar-day
    overlap).
  - Contribution-adjusted max drawdown + time-in-drawdown (wealth-multiple series =
    account_value / cumulative(initial + contributions to date)).
  - ACTIVATION DELAY (new metric this gate introduces): number of weeks from a window's own
    start until the standard policy switches on (0 for the immediate benchmark; "NEVER" if the
    signal never fires within that window — tracked as its own rate, see below).
  - NEVER-ACTIVATED RATE (new metric): across the 8 rolling cohorts (4x 5y + 4x 10y), the % of
    cohorts in which a delayed trial's signal never fires at all before the cohort's own window
    ends (100% - this = the ACTIVATION RATE used in the PASS threshold below).
  - Max AND ending direct-AAPL weight, quarter-end trim count/$ and turnover (trim
    dollar volume / average sleeve value).
  - OOS-vs-IS decay: OOS XIRR minus IS XIRR per trial (context, not a PASS criterion by itself).

Predeclared PASS thresholds for a delayed trigger (CONFIG constants, referenced by name in
verdict logic; a delayed trial (2, 3, or 4) is judged against the immediate benchmark ONLY on
the OOS headline window unless stated otherwise):
  MAX_XIRR_SHORTFALL_PP        = 0.50  (delayed trial's OOS XIRR must not be more than this many
                                         percentage points WORSE than the immediate benchmark's)
  MIN_RISK_IMPROVEMENT_PCT     = 5.0   (delayed trial's OOS max-DD OR annualized vol must be
                                         AT LEAST this % relatively BETTER (lower) than the
                                         immediate benchmark's — only one of the two needs to
                                         clear the bar)
  MAX_STRESS_WEALTH_DEGRADATION_PCT = 1.0  (that trial's own stress-case OOS terminal wealth
                                         must not be worse than its own base-case OOS terminal
                                         wealth by more than this %)
  MIN_COHORT_ACTIVATION_RATE_PCT = 80.0 (the trial's signal must actually fire — "effectively
                                         activate" with at least 1 week to act before the
                                         window's own end — in at least this % of the 8 rolling
                                         5y+10y cohorts; below this, "waiting" too often means
                                         "never buying AAPL at all", which is not a validated
                                         entry-timing edge, it is an accidental all-RSP outcome)
A delayed trial PASSES only if ALL FOUR conditions hold. Otherwise FAIL — "price-only waiting
has no validated edge [here]", which per the strategy-discovery-backtest gate's own honesty
rules is a valid, valuable result, not a failure to fix by loosening thresholds.

DEFLATED SHARPE RATIO (DSR) — WHY IT IS A POOR STATISTICAL FIT HERE (per gate Stage 4, "deflate
for the number of trials tried", trials = 4): a numeric DSR/PSR estimate under a naive N=4 iid
Sharpe-under-luck model IS computed below for procedural completeness, but it is a POOR fit for
this specific test, for three structural reasons stated up front (not discovered post-hoc): (1)
the extreme-value asymptotics the DSR/PSR formulas rely on need a reasonably large N of trials
to be statistically stable; N=4 is far too small for that approximation to mean much either way;
(2) the 4 trials are NOT independent draws from a "strategy space" — trial 4 is LITERALLY the
logical AND of trial 2's condition with trial 3's RSI sub-condition, and trial 3 and trial 4
share that identical RSI14<50 sub-condition, so the "independent trials" assumption central to
DSR is violated by construction, not by accident; (3) all 4 trials share the identical
underlying asset (AAPL), identical post-activation account mechanics, and largely overlapping
historical return streams once each activates — this is a nested ABLATION of ONE entry-timing
idea (wait for a technical pullback, operationalized 3 ways) plus a no-wait control, not 4
independently data-mined strategies pulled from a large search space, which is the actual
overfitting scenario DSR was built to correct for. The real defense against overfitting in THIS
gate is the OOS-headline + rolling-cohort walk-forward + stress-test discipline above, not the
DSR number, which is reported only so "trials tried" is disclosed per the gate's honesty rules.

Implementation self-checks (`--selfcheck`, and always run first inside a full run too):
  (a) Wilder RSI(14)-style formula hand-verified against a fully hand-computed small synthetic
      series (period=5 for tractable arithmetic) — Wilder's SMMA seeded with a SIMPLE average of
      the first `period` gains/losses (per Wilder 1978 / the standard derivation), not pandas'
      default `ewm` single-observation seeding, which is a measurably different (if
      asymptotically converging) initialization — this script uses the textbook seeding.
  (b) NO-SAME-BAR-ACTIVATION: a synthetic AAPL/RSP weekly series engineered so the signal first
      turns true at a known week t proves activation_start_index == t+1 (never t or earlier), and
      that the account's ACTUAL contribution routing at week t itself, and every week before it,
      is 100% RSP / 0% AAPL — i.e. the week whose close TRIGGERS the signal is never itself the
      week the account acts on it.
  (c) NO-LOOKAHEAD / SHIFT-THE-FUTURE TEST: two synthetic price paths, IDENTICAL through week t,
      that diverge only in weeks AFTER t+1 (one continues crashing, the other V-shape recovers),
      prove the signal value at every week <= t is BYTE-IDENTICAL between the two paths — i.e.
      changing the future cannot change a past/contemporaneous activation decision. This is a
      strictly stronger, more direct proof of no-lookahead than the generic "shift signals +1
      bar" heuristic from the gate's own SKILL.md (which is built for continuous vectorized
      alpha signals); the substitution is deliberate and is exactly what an explicit
      trailing-indicator + discrete-activation engine like this one needs.
  (d) Delayed-fill settlement lag and calendar-quarter-end trim mechanics (reused, adapted from
      the prior gate's already-verified engine) re-verified against a hand-constructed
      engineered-rally synthetic series through this script's OWN simulate_entry_trigger_window().
Determinism: two consecutive full runs must produce byte-identical
backtests/results/aapl_entry_trigger_summary.txt (no wall-clock timestamps are written to that
file). A raw-data cache at RAW_DATA_CACHE_PATH (outside this repo, under the user's home cache
dir — not one of this script's owned repo deliverables) pins the exact downloaded yfinance bytes
across separate CLI invocations for CACHE_MAX_AGE_HOURS hours, for the same reason documented in
the prior gate (yfinance's auto_adjust=True close is recomputed server-side on every call and
carries sub-cent jitter between live downloads). Delete the cache file to force a fresh download.
"""

import sys
import time
import warnings
from dataclasses import dataclass
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

try:
    import yfinance as yf
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance", "-q"])
    import yfinance as yf

from scipy.optimize import brentq
from scipy.stats import norm


# ═════════════════════════════  CONFIG  ══════════════════════════════════════
@dataclass(frozen=True)
class Config:
    tickers: tuple = ("AAPL", "RSP")

    # Initial state (identical for every window simulated -- matches the already-PASSed prior
    # gate's approved initial state, never the static live-date quote on the day this runs).
    initial_rsp_value: float = 710445.0
    initial_aapl_value: float = 26.0
    initial_total_value: float = 710445.0 + 26.0   # = 710471.0
    weekly_contribution: float = 250.0

    # Costs (fractions, i.e. 0.0002 = 2bps)
    base_cost_bps: float = 0.0002
    stress_cost_bps: float = 0.0005
    doubled_cost_bps: float = 0.0004
    extra_stress_bps: float = 0.0025   # stacked ONLY on doubled-base worst-5%-week trades

    # Periods
    is_start_floor: str = "2003-01-01"
    is_end: str = "2015-12-31"
    oos_start: str = "2016-01-01"

    rolling_5y_starts: tuple = (2005, 2010, 2015, 2020)
    rolling_10y_starts_fixed: tuple = (2005, 2010, 2013)   # first-common-year added at runtime

    crisis_windows: tuple = (
        ("2008 GFC", "2007-10-01", "2009-03-31"),
        ("2020 COVID", "2020-01-01", "2020-12-31"),
        ("2022 rate-hike bear", "2022-01-01", "2022-12-31"),
    )

    # Blended risk-free rate buckets per AGENTS.md convention: (start, end_excl, annual rate)
    rf_buckets: tuple = (
        ("1999-01-01", "2005-01-01", 0.05),
        ("2005-01-01", "2020-01-01", 0.03),
        ("2020-01-01", "2030-01-01", 0.04),
    )

    # APPROVED STANDARD POLICY (post-activation), reused verbatim from the PASSed prior gate.
    target_pct: float = 10.0
    ceiling_pct: float = 15.0

    # Signal parameters
    ema_span_weeks: int = 20
    sma_days: int = 50
    rsi_period: int = 14
    rsi_threshold: float = 50.0

    # Predeclared PASS thresholds for a delayed trigger vs the immediate benchmark
    max_xirr_shortfall_pp: float = 0.50
    min_risk_improvement_pct: float = 5.0
    max_stress_wealth_degradation_pct: float = 1.0
    min_cohort_activation_rate_pct: float = 80.0


CFG = Config()

TRIAL_DEFS = (
    {"key": "immediate", "label": "1. Immediate activation (benchmark, no wait)", "signal": "none"},
    {"key": "weekly_ema", "label": "2. Wait: weekly close <= 20wk EMA", "signal": "ema"},
    {"key": "daily_sma_rsi", "label": "3. Wait: daily close <= 50d SMA AND RSI14<50", "signal": "sma_rsi"},
    {"key": "weekly_ema_rsi", "label": "4. Wait: weekly <=20wk EMA AND RSI14<50", "signal": "ema_rsi"},
)
TRIAL_BY_KEY = {t["key"]: t for t in TRIAL_DEFS}
BASELINE_KEY = "immediate"
DELAYED_TRIAL_KEYS = ("weekly_ema", "daily_sma_rsi", "weekly_ema_rsi")
SIGNAL_COL_BY_TRIAL = {"weekly_ema": "sig_ema", "daily_sma_rsi": "sig_sma_rsi",
                       "weekly_ema_rsi": "sig_ema_rsi"}

REPORT_DIR = Path(__file__).resolve().parent.parent / "report" / "img"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
CHART_PATH = REPORT_DIR / "aapl_entry_trigger_backtest.png"
SUMMARY_PATH = RESULTS_DIR / "aapl_entry_trigger_summary.txt"
# Raw-download cache, kept OUTSIDE this git repo (own cache dir, separate from the prior gate's
# cache, so the two scripts never step on each other) -- see docstring for why this cache exists.
RAW_DATA_CACHE_PATH = Path.home() / ".cache" / "aapl-entry-trigger-backtest" / "raw_daily_close.csv"
CACHE_MAX_AGE_HOURS = 20

LOG_LINES = []


def log(msg=""):
    print(msg)
    LOG_LINES.append(str(msg))


def log_console_only(msg=""):
    """Print-only diagnostic (cache-hit/cold wording is inherently run-dependent) -- must NOT be
    appended to LOG_LINES/the persisted .txt summary, or it would break the byte-identical-
    summary determinism guarantee for no numerical reason."""
    print(msg)


def fmt_money(x):
    return f"${x:,.0f}" if pd.notna(x) else "n/a"


def fmt_pct(x):
    return f"{x*100:.2f}%" if pd.notna(x) else "n/a"


# ═════════════════════════════  DATA  ════════════════════════════════════════
def robust_download(tickers, start, end, retries=4):
    last_err = None
    for attempt in range(retries + 1):
        try:
            df = yf.download(list(tickers), start=start, end=end, auto_adjust=True,
                              progress=False, threads=True)
            if df is None or df.empty:
                raise ValueError("empty frame")
            return df
        except Exception as e:  # noqa: BLE001
            last_err = e
            wait = 1.5 * (2 ** attempt)
            log(f"  download attempt {attempt+1}/{retries+1} failed: {e} -- retrying in {wait:.1f}s")
            time.sleep(wait)
    raise RuntimeError(f"yfinance download failed after {retries+1} attempts: {last_err}")


def _load_or_download_raw_close(cfg: Config) -> pd.DataFrame:
    """Raw (un-rounded) daily Close frame, from the local cross-run cache if fresh enough, else
    a live yfinance download (which then populates the cache)."""
    cache_path = RAW_DATA_CACHE_PATH
    if cache_path.exists():
        age_hours = (time.time() - cache_path.stat().st_mtime) / 3600.0
        if age_hours <= CACHE_MAX_AGE_HOURS:
            log_console_only(
                f"Using cached raw daily close data ({cache_path}, age {age_hours:.1f}h) "
                f"for run-to-run determinism -- delete this file to force a fresh download.")
            log(f"Loaded {', '.join(cfg.tickers)} daily close data "
                f"(auto_adjust=True, adjusted-close proxy).")
            cached = pd.read_csv(cache_path, index_col=0, parse_dates=True)
            cached.columns.name = None
            return cached
        log_console_only(f"Cache at {cache_path} is {age_hours:.1f}h old "
                          f"(> {CACHE_MAX_AGE_HOURS}h) -- refreshing from yfinance.")

    log_console_only(f"Downloading {', '.join(cfg.tickers)} fresh from yfinance "
                      f"(auto_adjust=True, adjusted-close proxy)...")
    log(f"Loaded {', '.join(cfg.tickers)} daily close data "
        f"(auto_adjust=True, adjusted-close proxy).")
    end = pd.Timestamp.today().normalize() + pd.Timedelta(days=1)
    raw = robust_download(cfg.tickers, start="1999-01-01", end=end.strftime("%Y-%m-%d"))
    close = raw["Close"].copy()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    close.to_csv(cache_path)
    log_console_only(f"  cached raw daily close data to {cache_path} for subsequent-run "
                      f"determinism.")
    return close


def load_prices(cfg: Config = CFG) -> tuple:
    """Returns (weekly_common, aapl_daily_full):
      - weekly_common: AAPL+RSP weekly (W-FRI) close, sliced to the LONGEST COMMON history,
        complete-weeks-only -- used for the account simulation (identical methodology to the
        prior gate).
      - aapl_daily_full: AAPL's OWN full daily close series (its own history, NOT restricted to
        the AAPL/RSP common start) -- used ONLY for signal computation (EMA/SMA/RSI warm-up),
        since a real trailing indicator's value reflects genuine market history regargless of
        when RSP (or this account) happened to start.
    """
    close = _load_or_download_raw_close(cfg)
    # DETERMINISM FIX: yfinance's auto_adjust=True close is recomputed server-side on every call
    # and carries sub-cent floating-point jitter between successive live downloads; quantizing to
    # cents (the economically meaningful unit for equity prices) removes this without altering
    # any economically meaningful price info.
    close = close.round(2)

    last_raw_date = close.dropna(how="all").index.max()

    available = [t for t in cfg.tickers if t in close.columns and close[t].dropna().shape[0] > 0]
    missing = [t for t in cfg.tickers if t not in available]
    if missing:
        raise RuntimeError(f"BLOCKING FAILURE: no data returned for required tickers: {missing}")
    close = close[available].dropna(how="all")

    for t in available:
        first, last = close[t].dropna().index[0], close[t].dropna().index[-1]
        log(f"  {t}: {first.date()} -> {last.date()}  ({close[t].dropna().shape[0]} daily bars)")
    log(f"  Last raw daily bar across all tickers: {last_raw_date.date()}")

    aapl_daily_full = close["AAPL"].dropna().copy()

    weekly = close.resample("W-FRI").last()
    weekly = weekly.dropna(how="all")

    if len(weekly.index) > 0 and last_raw_date < weekly.index[-1]:
        log(f"  Dropping incomplete trailing week: last raw bar {last_raw_date.date()} < "
            f"weekly bucket label {weekly.index[-1].date()} (current calendar week not yet "
            f"closed -- bucket built from partial data, discarded).")
        weekly = weekly.iloc[:-1]
    assert weekly.index[-1] <= last_raw_date, (
        "COMPLETE-WEEKS-ONLY SELF-CHECK FAILED: final weekly bucket label "
        f"{weekly.index[-1].date()} exceeds last raw daily bar {last_raw_date.date()}."
    )
    log(f"  Complete-weeks-only self-check PASSED: last weekly bucket label "
        f"{weekly.index[-1].date()} <= last raw daily bar {last_raw_date.date()}.")

    common_start = weekly.dropna(how="any").index[0]
    weekly_common = weekly.loc[weekly.index >= common_start].dropna(how="any")
    log(f"  Common weekly history: {weekly_common.index[0].date()} -> "
        f"{weekly_common.index[-1].date()}  ({len(weekly_common)} weekly bars)")

    # Also drop any trailing incomplete week from the AAPL-only daily-derived signal base (same
    # completeness rule, applied independently since AAPL's own history runs longer than RSP's).
    aapl_daily_full = aapl_daily_full.loc[aapl_daily_full.index <= last_raw_date]

    return weekly_common[list(cfg.tickers)], aapl_daily_full


# ═══════════════════════════  RISK-FREE RATE  ════════════════════════════════
def blended_rf(start: pd.Timestamp, end: pd.Timestamp, cfg: Config = CFG) -> float:
    total_days = (end - start).days
    if total_days <= 0:
        return 0.03
    weighted = 0.0
    for b_start, b_end, rate in cfg.rf_buckets:
        b_start_ts, b_end_ts = pd.Timestamp(b_start), pd.Timestamp(b_end)
        overlap_start = max(start, b_start_ts)
        overlap_end = min(end, b_end_ts)
        overlap_days = (overlap_end - overlap_start).days
        if overlap_days > 0:
            weighted += overlap_days * rate
    return weighted / total_days


# ═══════════════════════════════  XIRR  ═══════════════════════════════════════
def xirr(dates, cashflows) -> float:
    t0 = dates[0]
    years = np.array([(d - t0).days / 365.25 for d in dates])
    cfs = np.array(cashflows, dtype=float)

    def npv(r):
        return np.sum(cfs / (1.0 + r) ** years)

    for hi in (10.0, 100.0, 1000.0, 1e6):
        try:
            lo_val, hi_val = npv(-0.9999), npv(hi)
            if np.isfinite(lo_val) and np.isfinite(hi_val) and lo_val * hi_val < 0:
                return brentq(npv, -0.9999, hi, maxiter=500)
        except Exception:  # noqa: BLE001
            continue
    try:
        from scipy.optimize import newton
        return newton(npv, x0=0.1, maxiter=200)
    except Exception:  # noqa: BLE001
        return float("nan")


# ══════════════════════════  QUARTER-END BAR DATES  ══════════════════════════
def quarter_end_bar_dates(index: pd.DatetimeIndex):
    """(set_of_enforcement_bar_dates, list_of_(calendar_quarter_end, weekly_bar_used) pairs),
    derived from real calendar quarter boundaries -- never an 'every 13 weeks' approximation.
    A quarter-end target only enforced if the window's data actually extends on/past it."""
    if len(index) == 0:
        return set(), []
    start, end = index.min(), index.max()
    targets = pd.date_range(start=start - pd.offsets.QuarterEnd(1),
                             end=end + pd.offsets.QuarterEnd(1), freq="QE-DEC")
    bar_dates = set()
    pairs = []
    for qt in targets:
        assert qt.month in (3, 6, 9, 12), f"quarter-end target {qt} not on a real quarter boundary"
        if qt > end:
            continue
        pos = index.searchsorted(qt, side="right") - 1
        if pos < 0:
            continue
        bar = index[pos]
        if bar < start or bar > end:
            continue
        bar_dates.add(bar)
        pairs.append((qt, bar))
    return bar_dates, pairs


# ══════════════════════════  WILDER RSI (textbook seeding)  ══════════════════
def wilder_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder's smoothed RSI (SMMA, alpha=1/period), seeded with a SIMPLE average of the first
    `period` gains/losses (per Wilder 1978 / the standard textbook derivation -- see docstring
    self-check (a)), NOT pandas' default `ewm` single-observation seeding (which is measurably
    different, if asymptotically converging, for the early history). Every value at row i
    depends ONLY on close[<=i] -- purely trailing/point-in-time by construction; no future data
    is read anywhere in this function (no negative shifts, no centered windows)."""
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    n = len(close)
    avg_gain = pd.Series(np.nan, index=close.index, dtype=float)
    avg_loss = pd.Series(np.nan, index=close.index, dtype=float)
    if n <= period:
        return pd.Series(np.nan, index=close.index)

    seed_pos = period  # delta[1..period] -> avg placed at close.index[period]
    avg_gain.iloc[seed_pos] = gain.iloc[1:seed_pos + 1].mean()
    avg_loss.iloc[seed_pos] = loss.iloc[1:seed_pos + 1].mean()
    ag = avg_gain.iloc[seed_pos]
    al = avg_loss.iloc[seed_pos]
    ag_vals = avg_gain.values
    al_vals = avg_loss.values
    gain_vals = gain.values
    loss_vals = loss.values
    for i in range(seed_pos + 1, n):
        ag = (ag * (period - 1) + gain_vals[i]) / period
        al = (al * (period - 1) + loss_vals[i]) / period
        ag_vals[i] = ag
        al_vals[i] = al
    avg_gain = pd.Series(ag_vals, index=close.index)
    avg_loss = pd.Series(al_vals, index=close.index)

    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    rsi = rsi.where(avg_loss != 0, 100.0)
    rsi = rsi.mask((avg_gain == 0) & (avg_loss == 0), 50.0)
    return rsi


# ══════════════════════════  SIGNAL COMPUTATION  ═════════════════════════════
def compute_signals(aapl_daily_full: pd.Series, weekly_index: pd.DatetimeIndex,
                     cfg: Config = CFG) -> pd.DataFrame:
    """Point-in-time trigger signals for AAPL, aligned to the weekly (Friday-labeled) grid used
    by the account simulation. Every column at row t uses ONLY AAPL daily/weekly data at or
    before date t (trailing indicators over AAPL's OWN full history, not reset per window) --
    no lookahead by construction (rolling/ewm/asof are all backward-looking)."""
    aapl_daily_full = aapl_daily_full.dropna().sort_index()
    weekly_full = aapl_daily_full.resample("W-FRI").last().dropna()
    ema20_full = weekly_full.ewm(span=cfg.ema_span_weeks, adjust=False).mean()
    sma50_full = aapl_daily_full.rolling(cfg.sma_days).mean()
    rsi14_full = wilder_rsi(aapl_daily_full, cfg.rsi_period)

    weekly_close = weekly_full.reindex(weekly_index)
    ema20 = ema20_full.reindex(weekly_index)
    # asof: last available AAPL daily observation AT OR BEFORE each Friday label -- the same
    # "last available close within the week" logic used to build weekly_full/weekly_close
    # itself, so daily_close_aligned should equal weekly_close row-for-row (checked below).
    daily_close_aligned = aapl_daily_full.asof(weekly_index)
    sma50_aligned = sma50_full.asof(weekly_index)
    rsi14_aligned = rsi14_full.asof(weekly_index)
    daily_close_aligned.index = weekly_index
    sma50_aligned.index = weekly_index
    rsi14_aligned.index = weekly_index

    mismatch = (weekly_close - daily_close_aligned).abs()
    max_mismatch = mismatch.max()
    if pd.notna(max_mismatch) and max_mismatch > 1e-9:
        raise AssertionError(
            f"SIGNAL ALIGNMENT SELF-CHECK FAILED: asof-reconstructed daily-Friday-close diverges "
            f"from the weekly-resampled close by up to {max_mismatch} -- alignment bug."
        )

    sig_rsi = rsi14_aligned < cfg.rsi_threshold
    sig_ema = weekly_close <= ema20
    sig_sma = daily_close_aligned <= sma50_aligned

    return pd.DataFrame({
        "weekly_close": weekly_close, "ema20": ema20, "daily_close": daily_close_aligned,
        "sma50": sma50_aligned, "rsi14": rsi14_aligned,
        "sig_ema": sig_ema, "sig_sma_rsi": (sig_sma & sig_rsi), "sig_ema_rsi": (sig_ema & sig_rsi),
    }, index=weekly_index)


def activation_index_for_trial(trial_key: str, signals_window: pd.DataFrame, n: int) -> tuple:
    """(activation_start_index, signal_true_index_or_None). activation_start_index is guaranteed
    STRICTLY GREATER than signal_true_index (never same-bar) -- computed as
    signal_true_index + 1: the account can only start the standard policy the week AFTER the
    week whose COMPLETED close satisfied the condition, never the same week."""
    if trial_key == "immediate":
        return 0, None
    col = SIGNAL_COL_BY_TRIAL[trial_key]
    bools = signals_window[col].fillna(False).to_numpy()
    true_positions = np.where(bools)[0]
    if len(true_positions) == 0:
        return n + 1, None  # sentinel: never triggers within this window
    t = int(true_positions[0])
    start_index = t + 1
    assert start_index > t, "NO-SAME-BAR-ACTIVATION SELF-CHECK FAILED"
    return start_index, t


# ══════════════════════════════  ENGINE  ═════════════════════════════════════
def simulate_entry_trigger_window(prices: pd.DataFrame, activation_start_index: int,
                                   cost_bps: float, extra_cost_dates: set = None,
                                   extra_cost_bps: float = 0.0, cfg: Config = CFG) -> pd.DataFrame:
    """
    Simulate one trial's account over `prices` (already sliced to the desired window), starting
    FRESH from cfg.initial_aapl_value / cfg.initial_rsp_value at prices.index[0].

    Mechanics per week i (decision date dt):
      A) SETTLE -- any cash decided at week i-1 executes at THIS week's close (always-on
         one-week delayed fill). Runtime assertion: decision_week + 1 == settlement_week for
         every executed event, and no week-i event exists in the queue before week i's own
         decisions run (no-lookahead self-check).
      B) MARK -- AAPL/RSP value from shares alone (pending cash excluded).
      C) QUARTER-END TRIM -- ONLY once `is_active` (i >= activation_start_index): if AAPL
         weight > 15% ceiling, sell AAPL down to EXACTLY the 10% target; sell-side cost on the
         trim, proceeds queued as pending RSP cash (buy-side cost at settlement). Pre-activation,
         this mechanic simply does not run (matches "before activation, all $250 -> RSP, no
         trims" -- there is no capped policy yet to enforce).
      D) ROUTE this week's new $250: if `is_active`, standard 10%/15% capped-satellite routing
         (identical formula to the prior gate's approved policy); else 100% -> RSP.
    """
    dates = prices.index
    n = len(dates)
    if n == 0:
        return pd.DataFrame()
    extra_cost_dates = extra_cost_dates or set()
    aapl_px = prices["AAPL"]
    rsp_px = prices["RSP"]

    qe_bar_dates, _ = quarter_end_bar_dates(dates)

    aapl_shares = cfg.initial_aapl_value / aapl_px.iloc[0]
    rsp_shares = cfg.initial_rsp_value / rsp_px.iloc[0]

    target = cfg.target_pct / 100.0
    ceiling = cfg.ceiling_pct / 100.0

    queue = []
    rows = []
    new_contrib_cum = 0.0
    trims_log = []
    first_active_index = None

    for i, dt in enumerate(dates):
        cost_today = cost_bps + (extra_cost_bps if dt in extra_cost_dates else 0.0)
        is_active = i >= activation_start_index

        # ---- A) settle pending cash decided at week i-1 ----
        still_pending = []
        for ev in queue:
            if ev["decision_week"] == i - 1:
                assert ev["decision_week"] + 1 == i, (
                    "NO-LEAKAGE SELF-CHECK FAILED: settlement week must equal "
                    "decision_week + 1 for every cash event."
                )
                price = aapl_px.iloc[i] if ev["ticker"] == "AAPL" else rsp_px.iloc[i]
                if pd.notna(price) and price > 0 and ev["amount"] > 0:
                    dollars = ev["amount"] * (1.0 - cost_today)
                    if ev["ticker"] == "AAPL":
                        aapl_shares += dollars / price
                    else:
                        rsp_shares += dollars / price
            else:
                still_pending.append(ev)
        queue = still_pending
        assert all(ev["decision_week"] != i for ev in queue), (
            "NO-LEAKAGE SELF-CHECK FAILED: a week-i cash event exists before week i's own "
            "decision step ran."
        )

        # ---- B) mark ----
        aapl_val = aapl_shares * aapl_px.iloc[i]
        rsp_val = rsp_shares * rsp_px.iloc[i]

        # ---- C) quarter-end trim -- ONLY once the standard policy is ACTIVE ----
        trim_gross = 0.0
        trim_net = 0.0
        is_qe = dt in qe_bar_dates
        if is_active and is_qe:
            total_ex_pending = aapl_val + rsp_val
            weight = aapl_val / total_ex_pending if total_ex_pending > 0 else 0.0
            if weight > ceiling and total_ex_pending > 0:
                sell_gross = (aapl_val - target * total_ex_pending) / (1.0 - target)
                sell_gross = min(max(sell_gross, 0.0), aapl_val)
                if sell_gross > 0:
                    aapl_shares -= sell_gross / aapl_px.iloc[i]
                    net_proceeds = sell_gross * (1.0 - cost_today)
                    queue.append({"decision_week": i, "ticker": "RSP", "amount": net_proceeds})
                    trim_gross = sell_gross
                    trim_net = net_proceeds
                    trims_log.append((dt, sell_gross, net_proceeds))
                    aapl_val = aapl_shares * aapl_px.iloc[i]

        # ---- D) route this week's new $250 contribution ----
        contribution = cfg.weekly_contribution
        if is_active:
            total = aapl_val + rsp_val
            weight = aapl_val / total if total > 0 else 0.0
            if weight < target:
                x = target * (total + contribution) - aapl_val
                x = min(max(x, 0.0), contribution)
            else:
                x = 0.0
            aapl_contrib = x
            rsp_contrib = contribution - x
            if first_active_index is None:
                first_active_index = i
        else:
            aapl_contrib = 0.0
            rsp_contrib = contribution

        if aapl_contrib > 0:
            queue.append({"decision_week": i, "ticker": "AAPL", "amount": aapl_contrib})
        if rsp_contrib > 0:
            queue.append({"decision_week": i, "ticker": "RSP", "amount": rsp_contrib})
        new_contrib_cum += contribution

        pending_cash = sum(ev["amount"] for ev in queue)
        account_value = aapl_val + rsp_val + pending_cash
        contrib_cum = cfg.initial_total_value + new_contrib_cum
        denom = aapl_val + rsp_val
        aapl_weight_pct = (aapl_val / denom * 100.0) if denom > 0 else float("nan")

        rows.append({
            "date": dt, "aapl_shares": aapl_shares, "rsp_shares": rsp_shares,
            "aapl_value": aapl_val, "rsp_value": rsp_val, "pending_cash": pending_cash,
            "account_value": account_value, "new_contrib_cum": new_contrib_cum,
            "contrib_cum": contrib_cum, "wealth_multiple": account_value / contrib_cum,
            "aapl_weight_pct": aapl_weight_pct, "is_qe": is_qe, "is_active": is_active,
            "trim_gross": trim_gross, "trim_net": trim_net,
            "aapl_contrib_decided": aapl_contrib, "rsp_contrib_decided": rsp_contrib,
        })

    out = pd.DataFrame(rows).set_index("date")
    out.attrs["trims"] = trims_log
    out.attrs["first_active_index"] = first_active_index
    return out


# ═════════════════════════════  METRICS  ═════════════════════════════════════
def time_weighted_returns(sim: pd.DataFrame, cfg: Config = CFG) -> pd.Series:
    if sim.empty or len(sim) < 2:
        return pd.Series(dtype=float)
    v = sim["account_value"]
    r = (v - cfg.weekly_contribution) / v.shift(1) - 1.0
    return r.iloc[1:]


def wealth_multiple_drawdown(wm: pd.Series) -> tuple:
    peak = wm.cummax()
    dd = (peak - wm) / peak
    return dd.max(), (wm < peak).mean()


def sharpe_of_returns(weekly_ret: pd.Series, annual_rf: float) -> float:
    weekly_rf = annual_rf / 52.0
    excess = weekly_ret - weekly_rf
    mean_w, std_w = excess.mean(), excess.std()
    if std_w == 0 or np.isnan(std_w):
        return float("nan")
    return (mean_w * 52.0) / (std_w * np.sqrt(52.0))


def money_weighted_metrics(sim: pd.DataFrame, cfg: Config = CFG) -> dict:
    if sim.empty:
        keys = ["terminal_value", "new_contrib", "total_contrib", "xirr", "max_dd",
                "time_in_dd", "pending_cash_terminal"]
        return {k: float("nan") for k in keys}
    terminal_value = sim["account_value"].iloc[-1]
    new_contrib = sim["new_contrib_cum"].iloc[-1]
    total_contrib = sim["contrib_cum"].iloc[-1]
    pending_terminal = sim["pending_cash"].iloc[-1]
    dates = list(sim.index)
    # DOCUMENTED SPEC DEVIATION (identical to, and for the identical reason as, the prior gate):
    # the initial $710,471 base IS included as a t0 outflow, not omitted -- see module docstring.
    cashflows = [-cfg.weekly_contribution] * len(dates)
    cashflows[0] += -cfg.initial_total_value
    cashflows[-1] += terminal_value
    irr = xirr(dates, cashflows)
    max_dd, time_in_dd = wealth_multiple_drawdown(sim["wealth_multiple"])
    return {
        "terminal_value": terminal_value, "new_contrib": new_contrib,
        "total_contrib": total_contrib, "xirr": irr, "max_dd": max_dd,
        "time_in_dd": time_in_dd, "pending_cash_terminal": pending_terminal,
    }


def weight_stats(sim: pd.DataFrame) -> tuple:
    if sim.empty:
        return float("nan"), float("nan")
    w = sim["aapl_weight_pct"].dropna()
    if w.empty:
        return float("nan"), float("nan")
    return w.max(), w.iloc[-1]


def trim_stats(sim: pd.DataFrame) -> dict:
    if sim.empty:
        return {"count": 0, "gross": 0.0, "net": 0.0, "turnover": float("nan")}
    n_trims = int((sim["trim_gross"] > 0).sum())
    gross = float(sim["trim_gross"].sum())
    net = float(sim["trim_net"].sum())
    avg_sleeve = float((sim["aapl_value"] + sim["rsp_value"]).mean())
    turnover = gross / avg_sleeve if avg_sleeve > 0 else float("nan")
    return {"count": n_trims, "gross": gross, "net": net, "turnover": turnover}


def worst_week_dates(sim: pd.DataFrame, cfg: Config = CFG) -> set:
    ret = time_weighted_returns(sim, cfg).dropna()
    if ret.empty:
        return set()
    threshold = np.percentile(ret.values, 5)
    return set(ret.index[ret <= threshold])


# ══════════════════════════  TRIAL RUNNER  ═══════════════════════════════════
def run_trials(prices_window: pd.DataFrame, signals_window: pd.DataFrame, cost_bps: float,
               extra_cost_dates_by_trial: dict = None, extra_cost_bps: float = 0.0,
               cfg: Config = CFG) -> tuple:
    extra_cost_dates_by_trial = extra_cost_dates_by_trial or {}
    n = len(prices_window)
    sims = {}
    activation_info = {}
    for t in TRIAL_DEFS:
        key = t["key"]
        start_idx, signal_true_idx = activation_index_for_trial(key, signals_window, n)
        extra_dates = extra_cost_dates_by_trial.get(key, set())
        sim = simulate_entry_trigger_window(prices_window, start_idx, cost_bps,
                                             extra_cost_dates=extra_dates,
                                             extra_cost_bps=extra_cost_bps, cfg=cfg)
        sims[key] = sim
        activation_info[key] = {
            "signal_true_index": signal_true_idx,
            "activation_start_index": start_idx,
            "n": n,
            "effectively_activated": start_idx < n,
        }
    return sims, activation_info


def run_worst5_stress(prices_window: pd.DataFrame, signals_window: pd.DataFrame,
                       cfg: Config = CFG) -> tuple:
    sims_pass1, _act1 = run_trials(prices_window, signals_window, cfg.doubled_cost_bps, cfg=cfg)
    extra_dates_by_trial = {k: worst_week_dates(sims_pass1[k], cfg) for k in sims_pass1}
    sims_pass2, act2 = run_trials(prices_window, signals_window, cfg.doubled_cost_bps,
                                   extra_cost_dates_by_trial=extra_dates_by_trial,
                                   extra_cost_bps=cfg.extra_stress_bps, cfg=cfg)
    return sims_pass1, sims_pass2, act2


def full_report(sims: dict, activation_info: dict, cfg: Config = CFG) -> dict:
    out = {}
    for t in TRIAL_DEFS:
        key = t["key"]
        sim = sims[key]
        mw = money_weighted_metrics(sim, cfg)
        max_w, end_w = weight_stats(sim)
        trims = trim_stats(sim)
        ret = time_weighted_returns(sim, cfg)
        vol_ann = ret.std() * np.sqrt(52) * 100 if len(ret) > 1 else float("nan")
        out[key] = {**mw, "max_weight_pct": max_w, "ending_weight_pct": end_w,
                    "trims": trims, "vol_ann_pct": vol_ann, "ret_series": ret, "sim": sim,
                    "activation": activation_info[key]}
    return out


def slice_window(prices: pd.DataFrame, signals: pd.DataFrame, start, end) -> tuple:
    mask_p = (prices.index >= pd.Timestamp(start)) & (prices.index <= pd.Timestamp(end))
    mask_s = (signals.index >= pd.Timestamp(start)) & (signals.index <= pd.Timestamp(end))
    return prices.loc[mask_p], signals.loc[mask_s]


def activation_label(activation: dict) -> str:
    if activation["signal_true_index"] is None and activation["activation_start_index"] == 0:
        return "0 (immediate)"
    if activation["effectively_activated"]:
        return str(activation["activation_start_index"])
    return "NEVER"


def trial_row(key, m) -> dict:
    row = {
        "Trial": TRIAL_BY_KEY[key]["label"],
        "Activation delay (wk)": activation_label(m["activation"]),
        "XIRR": fmt_pct(m["xirr"]),
        "Terminal $": fmt_money(m["terminal_value"]),
        "New contrib $": fmt_money(m["new_contrib"]),
        "Ann.vol": f"{m['vol_ann_pct']:.1f}%" if pd.notna(m["vol_ann_pct"]) else "n/a",
        "MaxDD": fmt_pct(m["max_dd"]),
        "Time-in-DD": fmt_pct(m["time_in_dd"]),
        "Max AAPL wt": f"{m['max_weight_pct']:.2f}%" if pd.notna(m["max_weight_pct"]) else "n/a",
        "End AAPL wt": f"{m['ending_weight_pct']:.2f}%" if pd.notna(m["ending_weight_pct"]) else "n/a",
    }
    t = m["trims"]
    row["Trims (n/$)"] = f"{t['count']}/{fmt_money(t['gross'])}"
    row["Turnover"] = f"{t['turnover']*100:.1f}%" if pd.notna(t["turnover"]) else "n/a"
    return row


def metrics_table(report: dict) -> pd.DataFrame:
    rows = [trial_row(t["key"], report[t["key"]]) for t in TRIAL_DEFS]
    return pd.DataFrame(rows)


def expected_max_sharpe_under_trials(n_trials: int, sharpe_std: float) -> float:
    """Bailey & Lopez de Prado (2014) E[max SR] approximation under N iid-normal trials with the
    given cross-trial Sharpe standard deviation. See module docstring for why this is reported
    for procedural completeness only and is a POOR statistical fit for this specific 4-trial,
    nested/correlated ablation."""
    if n_trials <= 1 or not np.isfinite(sharpe_std) or sharpe_std <= 0:
        return float("nan")
    euler_gamma = 0.5772156649015329
    term1 = (1 - euler_gamma) * norm.ppf(1 - 1.0 / n_trials)
    term2 = euler_gamma * norm.ppf(1 - 1.0 / (n_trials * np.e))
    return sharpe_std * (term1 + term2)


# ═════════════════════════════  MAIN PIPELINE  ═══════════════════════════════
def cohort_window(common_start, latest, start_year, horizon_years):
    start_dt = pd.Timestamp(f"{start_year}-01-01")
    if start_dt < common_start:
        start_dt = common_start
    if start_dt > latest:
        return None
    end_dt = min(start_dt + pd.DateOffset(years=horizon_years), latest)
    truncated = (start_dt + pd.DateOffset(years=horizon_years)) > latest
    return start_dt, end_dt, truncated


# ══════════════════════════════  SELF-CHECKS  ═════════════════════════════════
def _build_synthetic_scenario(post_crash_prices):
    """45 synthetic weekly Fridays (2018-01-05 onward): AAPL rises linearly from 100.0
    (weeks 0-29, +1.0/week) so the 20-week EMA has a full 20+ weeks to converge and lag
    STRICTLY below a clearly rising price well before the crash (avoiding the trivial
    ewm-seed-equality artifact at week 0 of any freshly-started series). At week 30 AAPL
    crashes hard to 60.0 in a single week; `post_crash_prices` (len 15) supplies weeks
    30..44's closes -- varying ONLY this tail (while holding week 30 itself fixed) is what
    self-check (c)'s shift-the-future test exploits. RSP is held perfectly flat at 100.0
    throughout (irrelevant to the AAPL-only signals; included only so the shared account
    engine has both tickers).
    Also returns a matching synthetic DAILY AAPL series (5 business days/week, each day
    within a week taking that week's AAPL close -- a deliberately simple step function,
    sufficient to exercise the daily SMA50/RSI14 alignment + no-lookahead mechanics without
    needing a "realistic" daily path)."""
    assert len(post_crash_prices) == 15
    n_weeks = 45
    dates = pd.date_range("2018-01-05", periods=n_weeks, freq="W-FRI")
    aapl_vals = [100.0 + i * 1.0 for i in range(30)] + list(post_crash_prices)
    rsp_vals = [100.0] * n_weeks
    weekly = pd.DataFrame({"AAPL": aapl_vals, "RSP": rsp_vals}, index=dates)

    daily_dates = pd.bdate_range(dates[0] - pd.Timedelta(days=4), dates[-1])
    daily = pd.Series(index=daily_dates, dtype=float)
    for wk_date, price in zip(dates, aapl_vals):
        wk_start = wk_date - pd.Timedelta(days=4)
        mask = (daily_dates >= wk_start) & (daily_dates <= wk_date)
        daily.loc[daily_dates[mask]] = price
    daily = daily.ffill().dropna()
    return weekly, daily


def run_selfchecks(cfg: Config = CFG) -> bool:
    """
    Four independent self-checks, all exercised through this script's OWN production
    functions (wilder_rsi, compute_signals, activation_index_for_trial,
    simulate_entry_trigger_window) -- never a separately-hand-rolled shadow implementation.
    """
    ok = True

    # ---- (a) Wilder RSI hand-verification (period=5, exactly-precomputed expected values) ----
    log("-" * 100)
    log("[selfcheck a] Wilder RSI(14)-style formula vs a fully hand-computed synthetic series "
        "(period=5 for tractable by-hand arithmetic)")
    log("-" * 100)
    synth_close = pd.Series([100, 102, 101, 103, 106, 105, 107, 104, 108, 110], dtype=float)
    expected_rsi = {
        5: 77.7777777778, 6: 82.6086956522, 7: 58.6872586873, 8: 72.1354166667, 9: 76.8460914255,
    }
    rsi_out = wilder_rsi(synth_close, period=5)
    for idx, exp_val in expected_rsi.items():
        got = rsi_out.iloc[idx]
        if abs(got - exp_val) > 1e-6:
            ok = False
            log(f"  [selfcheck a] FAIL: RSI at index {idx}: expected {exp_val:.10f}, got {got:.10f}")
        else:
            log(f"  [selfcheck a] PASS: RSI at index {idx} = {got:.10f} (expected {exp_val:.10f})")
    if rsi_out.iloc[:5].notna().any():
        ok = False
        log("  [selfcheck a] FAIL: RSI produced a value before the seed position (period=5) -- "
            "would imply a lookahead/warm-up bug")
    else:
        log("  [selfcheck a] PASS: RSI is NaN for all indices before the seed position (no "
            "premature/invalid early value)")

    # ---- (b)+(c): synthetic crash scenario, exercised through compute_signals() ----
    log("-" * 100)
    log("[selfcheck b+c] NO-SAME-BAR-ACTIVATION and SHIFT-THE-FUTURE (no-lookahead) tests, via "
        "compute_signals() + activation_index_for_trial() on a synthetic AAPL/RSP series")
    log("-" * 100)
    weekly_a, daily_a = _build_synthetic_scenario([60.0] * 15)          # flat post-crash tail
    weekly_b, daily_b = _build_synthetic_scenario([60.0] + [150.0] * 14)  # diverges from week 31

    signals_full_a = compute_signals(daily_a, weekly_a.index, cfg)
    signals_full_b = compute_signals(daily_b, weekly_b.index, cfg)

    # Test window = a slice of the FULL synthetic history (weeks 15..44), matching the
    # production pattern of "compute signals once over full history, then slice per window".
    test_prices = weekly_a.iloc[15:]
    test_signals = signals_full_a.loc[test_prices.index]
    n_test = len(test_prices)
    crash_week_local = 30 - 15  # = 15, the local index of the week-30 crash within the slice

    for trial_key in DELAYED_TRIAL_KEYS:
        start_idx, sig_true_idx = activation_index_for_trial(trial_key, test_signals, n_test)
        label = TRIAL_BY_KEY[trial_key]["label"]
        if sig_true_idx is None:
            ok = False
            log(f"  [selfcheck b] FAIL ({label}): signal never fired in the synthetic crash "
                f"scenario -- expected a trigger at/after the crash week")
            continue
        if sig_true_idx < crash_week_local:
            ok = False
            log(f"  [selfcheck b] FAIL ({label}): signal fired EARLY at local week "
                f"{sig_true_idx} (before the crash week {crash_week_local}) -- false positive "
                f"during the clean uptrend")
        else:
            log(f"  [selfcheck b] PASS ({label}): signal first true at local week "
                f"{sig_true_idx} (>= crash week {crash_week_local}, no early false trigger "
                f"during the uptrend)")
        if start_idx != sig_true_idx + 1:
            ok = False
            log(f"  [selfcheck b] FAIL ({label}): activation_start_index={start_idx} != "
                f"signal_true_index+1={sig_true_idx + 1}")
        else:
            log(f"  [selfcheck b] PASS ({label}): activation_start_index={start_idx} == "
                f"signal_true_index+1 exactly (no same-bar activation)")

        # Run the real engine and confirm ZERO AAPL contribution routing at/before the
        # signal week itself, and STRICTLY POSITIVE AAPL contribution routing decided the
        # week activation starts (there is budget under target from the tiny $26 seed).
        sim = simulate_entry_trigger_window(test_prices, start_idx, cfg.base_cost_bps, cfg=cfg)
        pre_activation_contrib = sim["aapl_contrib_decided"].iloc[:sig_true_idx + 1]
        if (pre_activation_contrib.abs() > 1e-9).any():
            ok = False
            log(f"  [selfcheck b] FAIL ({label}): nonzero AAPL contribution decided at/before "
                f"the signal week {sig_true_idx} (weeks 0..{sig_true_idx})")
        else:
            log(f"  [selfcheck b] PASS ({label}): AAPL contribution decided is EXACTLY zero for "
                f"every week 0..{sig_true_idx} (through and including the signal week itself)")
        first_active_contrib = sim["aapl_contrib_decided"].iloc[start_idx]
        if not (first_active_contrib > 0):
            ok = False
            log(f"  [selfcheck b] FAIL ({label}): expected STRICTLY POSITIVE AAPL contribution "
                f"decided at week {start_idx} (first active week), got {first_active_contrib}")
        else:
            log(f"  [selfcheck b] PASS ({label}): AAPL contribution decided at week {start_idx} "
                f"(first active week) = ${first_active_contrib:.4f} > 0 (activation actually "
                f"takes effect the week immediately AFTER the triggering close)")

    # Shift-the-future: scenarios A and B are IDENTICAL through and including week 30 (the
    # crash week itself), diverging only from week 31 onward. Every signal column, for every
    # week <= 30 (local index <= crash_week_local), must be BYTE-IDENTICAL between A and B.
    cols = ["weekly_close", "ema20", "daily_close", "sma50", "rsi14",
            "sig_ema", "sig_sma_rsi", "sig_ema_rsi"]
    through_crash = test_prices.index[:crash_week_local + 1]
    sig_a = signals_full_a.loc[through_crash, cols]
    sig_b = signals_full_b.loc[through_crash, cols]
    mismatches = []
    for col in cols:
        s_a, s_b = sig_a[col], sig_b[col]
        if s_a.dtype == bool or s_b.dtype == bool:
            diff = (s_a.astype(bool) != s_b.astype(bool))
        else:
            diff = (s_a - s_b).abs() > 1e-9
        if diff.any():
            mismatches.append((col, list(through_crash[diff])))
    if mismatches:
        ok = False
        log(f"  [selfcheck c] FAIL: signal values through the crash week (identical inputs) "
            f"diverged between the two future-differing scenarios: {mismatches}")
    else:
        log(f"  [selfcheck c] PASS: ALL signal columns ({', '.join(cols)}) for every week "
            f"<= the crash week ({through_crash[-1].date()}) are BYTE-IDENTICAL between "
            f"scenario A (flat post-crash) and scenario B (diverges to +150 from week 31 "
            f"onward) -- changing the future cannot change a past/contemporaneous signal.")

    # ---- (d) Delayed-fill + calendar-quarter-end trim mechanics, via THIS script's engine ----
    log("-" * 100)
    log("[selfcheck d] Delayed-fill settlement lag + calendar-quarter-end trim mechanics, via "
        "simulate_entry_trigger_window() (activation_start_index=0, i.e. the 'immediate' "
        "trial's exact code path)")
    log("-" * 100)
    n_weeks_d = 26
    dates_d = pd.date_range("2021-01-08", periods=n_weeks_d, freq="W-FRI")
    assert dates_d.min() < pd.Timestamp("2021-03-31") < dates_d.max()
    rsp_prices_d = pd.Series(100.0, index=dates_d)
    aapl_prices_d = pd.Series(10.0, index=dates_d)
    for i in range(4, n_weeks_d):
        aapl_prices_d.iloc[i] = 30.0  # tripled from week 4 onward -> forces a ceiling breach
    synth_prices_d = pd.DataFrame({"AAPL": aapl_prices_d, "RSP": rsp_prices_d})
    synth_cfg_d = Config(initial_rsp_value=9000.0, initial_aapl_value=1000.0,
                          initial_total_value=10000.0, weekly_contribution=250.0)
    sim_d = simulate_entry_trigger_window(synth_prices_d, activation_start_index=0,
                                           cost_bps=0.0002, cfg=synth_cfg_d)

    qe_bar_dates_d, qe_pairs_d = quarter_end_bar_dates(synth_prices_d.index)
    log(f"  [selfcheck d] synthetic quarter-end enforcement bars: "
        f"{[(str(t.date()), str(b.date())) for t, b in qe_pairs_d]}")
    for qt, _bar in qe_pairs_d:
        if qt.month not in (3, 6, 9, 12):
            ok = False
            log(f"  [selfcheck d] FAIL: quarter-end target {qt} not on a real quarter boundary")

    initial_weight_d = sim_d["aapl_weight_pct"].iloc[0]
    if abs(initial_weight_d - 10.0) > 0.05:
        ok = False
        log(f"  [selfcheck d] FAIL: expected initial AAPL weight ~10.0%, got {initial_weight_d:.4f}%")
    else:
        log(f"  [selfcheck d] PASS: initial AAPL weight = {initial_weight_d:.4f}% (target 10%)")

    first_qe_bar_d = sorted(qe_bar_dates_d)[0]
    pre_trim_idx_d = sim_d.index.get_loc(first_qe_bar_d) - 1
    pre_trim_weight_d = sim_d["aapl_weight_pct"].iloc[pre_trim_idx_d]
    trim_row_d = sim_d.loc[first_qe_bar_d]
    if pre_trim_weight_d <= 15.0:
        ok = False
        log(f"  [selfcheck d] FAIL: expected pre-trim weight > 15% ceiling the week before "
            f"{first_qe_bar_d.date()}, got {pre_trim_weight_d:.2f}%")
    else:
        log(f"  [selfcheck d] PASS: pre-trim weight {pre_trim_weight_d:.2f}% > 15% ceiling the "
            f"week before {first_qe_bar_d.date()} (breach confirmed)")
    if trim_row_d["trim_gross"] <= 0:
        ok = False
        log(f"  [selfcheck d] FAIL: expected a trim to fire at quarter-end bar {first_qe_bar_d.date()}")
    else:
        log(f"  [selfcheck d] PASS: trim fired at {first_qe_bar_d.date()} "
            f"(gross ${trim_row_d['trim_gross']:.2f})")
    post_trim_weight_d = trim_row_d["aapl_weight_pct"]
    if abs(post_trim_weight_d - 10.0) > 0.05:
        ok = False
        log(f"  [selfcheck d] FAIL: expected post-trim weight ~= target 10%, got "
            f"{post_trim_weight_d:.4f}%")
    else:
        log(f"  [selfcheck d] PASS: post-trim weight {post_trim_weight_d:.4f}% == target 10% "
            f"(returned to TARGET, not ceiling)")

    trace_i = 2
    decided_aapl_d = sim_d["aapl_contrib_decided"].iloc[trace_i]
    decided_rsp_d = sim_d["rsp_contrib_decided"].iloc[trace_i]
    for ticker, decided in (("AAPL", decided_aapl_d), ("RSP", decided_rsp_d)):
        shares_col = "aapl_shares" if ticker == "AAPL" else "rsp_shares"
        price_series = synth_prices_d[ticker]
        shares_at_i = sim_d[shares_col].iloc[trace_i]
        shares_at_i_plus_1 = sim_d[shares_col].iloc[trace_i + 1]
        actual_new_shares = shares_at_i_plus_1 - shares_at_i
        if decided <= 0:
            if abs(actual_new_shares) > 1e-9:
                ok = False
                log(f"  [selfcheck d] FAIL: week {trace_i} decided $0 for {ticker}, but "
                    f"{actual_new_shares:.6f} shares appeared at week {trace_i + 1}")
            else:
                log(f"  [selfcheck d] PASS: week {trace_i} decided $0 for {ticker} -> zero new "
                    f"shares at week {trace_i + 1}")
            continue
        expected_new_shares = (decided * (1.0 - 0.0002)) / price_series.iloc[trace_i + 1]
        if abs(actual_new_shares - expected_new_shares) > 1e-6:
            ok = False
            log(f"  [selfcheck d] FAIL: week {trace_i}->{trace_i + 1} delayed-fill {ticker} "
                f"share math mismatch: expected +{expected_new_shares:.6f}, got "
                f"+{actual_new_shares:.6f}")
        else:
            log(f"  [selfcheck d] PASS: cash decided for {ticker} at week {trace_i} "
                f"(${decided:.4f}) produces exactly +{actual_new_shares:.6f} shares at week "
                f"{trace_i + 1}'s close (one-week lag confirmed)")

    return ok


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    log("=" * 100)
    log("AAPL ENTRY-TRIGGER GATE -- DOES WAITING FOR A TECHNICAL DIP BEAT IMMEDIATE ACTIVATION? "
        "(strategy-discovery-backtest)")
    log("=" * 100)
    log(__doc__)

    log("=" * 100)
    log("SELF-CHECKS (RSI hand-verify, no-same-bar-activation, shift-the-future no-lookahead, "
        "delayed-fill/trim mechanics -- all via this script's OWN production functions)")
    log("=" * 100)
    selfcheck_ok = run_selfchecks(CFG)
    if not selfcheck_ok:
        log("\nSELF-CHECKS FAILED -- aborting before running the real backtest.")
        SUMMARY_PATH.write_text("\n".join(LOG_LINES) + "\n")
        sys.exit(1)
    log("\nAll self-checks PASSED.\n")

    log("=" * 100)
    log("DOCUMENTED ASSUMPTIONS / SPEC DEVIATIONS (stated explicitly, per task instructions)")
    log("=" * 100)
    log("1. XIRR cashflow schedule DEVIATES from the literal spec text: the initial "
        f"{fmt_money(CFG.initial_total_value)} base IS included as an additional t0 outflow "
        "(alongside week 0's -$250), not omitted -- identical treatment, and for the identical "
        "reason, as the prior (already-PASSed) aapl_weekly_dca_backtest.py gate: omitting it "
        "produces a mathematically ill-posed/meaningless IRR, since the pre-existing lump sum "
        "dominates the $250/wk stream.")
    log("2. Signals (20wk EMA / 50d SMA / RSI14) are computed over AAPL's OWN FULL available "
        "daily/weekly history from its earliest downloaded bar (NOT reset to a fresh warm-up at "
        "each window's own start date) -- see module docstring 'DATA / no-lookahead' section for "
        "the rationale. This is deliberate and is re-verified structurally in self-checks (b)/(c).")
    log("3. The illustrative chart uses the full common-history window (fresh initial state at "
        "first common date, base 2bps cost) purely for visualization; it is NOT the verdict "
        "window. All PASS/FAIL verdicts are based on the OOS-headline window "
        f"({CFG.oos_start} -> latest complete week) as specified.")
    log("4. DSR (Deflated Sharpe Ratio) is reported below for procedural completeness only and "
        "is a POOR statistical fit here (trials=4, non-independent by construction) -- see module "
        "docstring and the dedicated DSR section below for the full explanation.")
    log("")

    weekly_common, aapl_daily_full = load_prices(CFG)
    signals_full = compute_signals(aapl_daily_full, weekly_common.index, CFG)

    common_start = weekly_common.index[0]
    latest = weekly_common.index[-1]
    is_start = max(common_start, pd.Timestamp(CFG.is_start_floor))
    is_end_ts = pd.Timestamp(CFG.is_end)
    oos_start_ts = pd.Timestamp(CFG.oos_start)

    log("=" * 100)
    log("ENGINE-LEVEL DETERMINISM PROOF (same downloaded data, same process, simulation run TWICE)")
    log("=" * 100)
    log("Isolates CODE-level determinism (dict/set ordering, floating-point op order, no unseeded "
        "randomness) from DATA-SOURCE determinism (yfinance's auto_adjust=True close is "
        "recomputed server-side per call, hence the RAW_DATA_CACHE_PATH cache across separate CLI "
        "invocations -- see module docstring). This in-process check proves that GIVEN IDENTICAL "
        "input data, the engine is 100% deterministic.")
    _p1, _s1 = slice_window(weekly_common, signals_full, oos_start_ts, latest)
    _sims_a, _act_a = run_trials(_p1, _s1, CFG.base_cost_bps, cfg=CFG)
    _report_a = full_report(_sims_a, _act_a, CFG)
    _sims_b, _act_b = run_trials(_p1, _s1, CFG.base_cost_bps, cfg=CFG)
    _report_b = full_report(_sims_b, _act_b, CFG)
    _mismatches = []
    for t in TRIAL_DEFS:
        k = t["key"]
        for field in ("terminal_value", "xirr", "max_dd", "time_in_dd", "max_weight_pct",
                      "ending_weight_pct", "vol_ann_pct"):
            a, b = _report_a[k][field], _report_b[k][field]
            if a != b and not (pd.isna(a) and pd.isna(b)):
                _mismatches.append((k, field, a, b))
        if _report_a[k]["activation"] != _report_b[k]["activation"]:
            _mismatches.append((k, "activation", _report_a[k]["activation"], _report_b[k]["activation"]))
    if _mismatches:
        log(f"  ENGINE DETERMINISM CHECK FAILED: {_mismatches}")
    else:
        log("  ENGINE DETERMINISM CHECK PASSED: identical input data -> byte-identical numeric "
            "results across two in-process simulation runs (all trials, all fields, including "
            "activation indices).")
    log("")

    log(f"IS window (context only, not the verdict criterion): {is_start.date()} -> {CFG.is_end}")
    log(f"OOS window: {CFG.oos_start} -> {latest.date()}   <-- HEADLINE (verdict window, fresh "
        f"initial state at {CFG.oos_start})")
    log("")
    log(f"Initial state (identical at the start of EVERY window below): RSP-proxy sleeve "
        f"{fmt_money(CFG.initial_rsp_value)} + direct AAPL {fmt_money(CFG.initial_aapl_value)} "
        f"= {fmt_money(CFG.initial_total_value)} total, plus {fmt_money(CFG.weekly_contribution)}"
        f"/week new money. Before activation: 100% of the $250 -> RSP.")
    log("")

    oos_prices, oos_signals = slice_window(weekly_common, signals_full, oos_start_ts, latest)
    qe_bars, qe_pairs = quarter_end_bar_dates(oos_prices.index)
    log("-" * 100)
    log("QUARTER-END ENFORCEMENT DATES (OOS window, once a trial is ACTIVE) -- derived from real "
        "calendar quarter boundaries, NOT 'every 13 weeks':")
    log("-" * 100)
    for qt, bar in qe_pairs:
        assert qt.month in (3, 6, 9, 12)
        log(f"  calendar quarter-end {qt.date()} -> last complete weekly bar used: {bar.date()}")

    # ── IS context (base cost, not a verdict input) ─────────────────────────
    log("")
    log("-" * 100)
    log("IN-SAMPLE (IS) -- base cost 2bps -- context only, NOT the gate criterion")
    log("-" * 100)
    is_prices, is_signals = slice_window(weekly_common, signals_full, is_start, is_end_ts)
    sims_is, act_is = run_trials(is_prices, is_signals, CFG.base_cost_bps, cfg=CFG)
    report_is = full_report(sims_is, act_is, CFG)
    log(metrics_table(report_is).to_string(index=False))

    # ── OOS headline: base cost ──────────────────────────────────────────────
    log("")
    log("=" * 100)
    log("OUT-OF-SAMPLE (OOS) -- HEADLINE RESULT -- base cost 2bps, always-on 1-week delayed fill")
    log("=" * 100)
    sims_oos_base, act_oos_base = run_trials(oos_prices, oos_signals, CFG.base_cost_bps, cfg=CFG)
    report_oos_base = full_report(sims_oos_base, act_oos_base, CFG)
    oos_rf = blended_rf(oos_start_ts, latest)
    log(f"Blended OOS risk-free rate (AGENTS.md convention): {oos_rf*100:.2f}%")
    log(metrics_table(report_oos_base).to_string(index=False))

    oos_sharpe = {t["key"]: sharpe_of_returns(report_oos_base[t["key"]]["ret_series"], oos_rf)
                  for t in TRIAL_DEFS}
    log("")
    log("Sharpe (annualized, on the ACTUAL time-weighted return series, drift-aware, blended RF):")
    for t in TRIAL_DEFS:
        log(f"  {t['label']:50s}  Sharpe={oos_sharpe[t['key']]:.3f}")

    # ── OOS cost scenarios (2bps / 5bps / 4bps) + worst-5%-week stress ──────
    log("")
    log("=" * 100)
    log("OOS COST SCENARIOS (base 2bps / stress 5bps / doubled-base 4bps) + worst-5%-week stress "
        "(doubled 4bps + extra 25bps stacked ONLY on each trial's own worst-5%-return weeks)")
    log("=" * 100)
    cost_scenarios = {}
    for label, cost in [("Base (2bps)", CFG.base_cost_bps), ("Stress (5bps)", CFG.stress_cost_bps),
                         ("Doubled-base (4bps)", CFG.doubled_cost_bps)]:
        sims, act = run_trials(oos_prices, oos_signals, cost, cfg=CFG)
        cost_scenarios[label] = full_report(sims, act, CFG)
        log(f"\n--- {label} ---")
        log(metrics_table(cost_scenarios[label]).to_string(index=False))

    sims_w5_pass1, sims_w5_pass2, act_w5 = run_worst5_stress(oos_prices, oos_signals, CFG)
    report_worst5 = full_report(sims_w5_pass2, act_w5, CFG)
    worst5_label = (f"Doubled+Worst5%wk ({CFG.doubled_cost_bps*10000:.0f}bps+"
                     f"{CFG.extra_stress_bps*10000:.0f}bps)")
    cost_scenarios[worst5_label] = report_worst5
    log(f"\n--- {worst5_label} ---")
    log(metrics_table(report_worst5).to_string(index=False))

    # ── Stress wealth-degradation check (each trial vs its OWN base case) ───
    log("")
    log("-" * 100)
    log(f"STRESS WEALTH-DEGRADATION CHECK (OOS headline) -- threshold: "
        f"MAX_STRESS_WEALTH_DEGRADATION_PCT = {CFG.max_stress_wealth_degradation_pct:.1f}% "
        f"(each trial's own stress terminal wealth must not be more than this % worse than "
        f"that SAME trial's own base-case terminal wealth)")
    log("-" * 100)
    stress_degradation = {}
    stress_ok = {}
    for t in TRIAL_DEFS:
        key = t["key"]
        base_term = cost_scenarios["Base (2bps)"][key]["terminal_value"]
        stress_term = cost_scenarios[worst5_label][key]["terminal_value"]
        degradation_pct = (base_term - stress_term) / base_term * 100.0
        stress_degradation[key] = degradation_pct
        passfail = degradation_pct <= CFG.max_stress_wealth_degradation_pct
        stress_ok[key] = passfail
        log(f"  {t['label']:50s}  base={fmt_money(base_term)}  stress={fmt_money(stress_term)}  "
            f"degradation={degradation_pct:.3f}%  -> {'PASS' if passfail else 'FAIL'}")

    # ── Rolling cohorts ──────────────────────────────────────────────────────
    log("")
    log("=" * 100)
    log("ROLLING START-DATE COHORTS -- each a FRESH account from the same initial state, base "
        "cost 2bps")
    log("=" * 100)
    first_common_year = common_start.year
    cohort_5y_starts = list(CFG.rolling_5y_starts)
    cohort_10y_starts = sorted(set([first_common_year, *CFG.rolling_10y_starts_fixed]))

    cohort_activation = {t["key"]: [] for t in TRIAL_DEFS}  # list of bool "effectively_activated"

    def cohort_report(start_year, horizon_years):
        win = cohort_window(common_start, latest, start_year, horizon_years)
        if win is None:
            return None
        start_dt, end_dt, truncated = win
        c_prices, c_signals = slice_window(weekly_common, signals_full, start_dt, end_dt)
        sims, act = run_trials(c_prices, c_signals, CFG.base_cost_bps, cfg=CFG)
        rep = full_report(sims, act, CFG)
        for t in TRIAL_DEFS:
            cohort_activation[t["key"]].append(rep[t["key"]]["activation"]["effectively_activated"])
        row = {"Cohort start": start_dt.date(), "Cohort end": end_dt.date(),
               "Truncated": "yes" if truncated else "no"}
        for t in TRIAL_DEFS:
            m = rep[t["key"]]
            row[f"{t['key']} delay(wk)"] = activation_label(m["activation"])
            row[f"{t['key']} XIRR"] = fmt_pct(m["xirr"])
        return row

    log("\n--- 5-year cohorts ---")
    rows5 = [r for r in (cohort_report(y, 5) for y in cohort_5y_starts) if r]
    log(pd.DataFrame(rows5).to_string(index=False) if rows5 else "  (no cohorts in range)")

    log("\n--- 10-year cohorts ---")
    rows10 = [r for r in (cohort_report(y, 10) for y in cohort_10y_starts) if r]
    log(pd.DataFrame(rows10).to_string(index=False) if rows10 else "  (no cohorts in range)")

    n_cohorts = len(rows5) + len(rows10)
    cohort_activation_rate = {}
    log("")
    log(f"COHORT ACTIVATION RATE (n={n_cohorts} cohorts: {len(rows5)}x 5y + {len(rows10)}x 10y) "
        f"-- threshold MIN_COHORT_ACTIVATION_RATE_PCT = {CFG.min_cohort_activation_rate_pct:.1f}%")
    for t in TRIAL_DEFS:
        key = t["key"]
        flags = cohort_activation[key]
        rate = 100.0 * sum(flags) / len(flags) if flags else float("nan")
        cohort_activation_rate[key] = rate
        never_rate = 100.0 - rate
        log(f"  {t['label']:50s}  activated in {sum(flags)}/{len(flags)} cohorts "
            f"({rate:.1f}%)  never-activated rate={never_rate:.1f}%")

    # ── Crisis windows ──────────────────────────────────────────────────────
    log("")
    log("=" * 100)
    log("CRISIS WINDOWS -- each a FRESH account from the same initial state, base cost 2bps")
    log("=" * 100)
    for name, c_start, c_end in CFG.crisis_windows:
        c_start_ts, c_end_ts = pd.Timestamp(c_start), pd.Timestamp(c_end)
        if c_start_ts < common_start:
            log(f"\n--- {name} ({c_start} -> {c_end}) --- SKIPPED: before common data start")
            continue
        c_end_ts = min(c_end_ts, latest)
        c_prices, c_signals = slice_window(weekly_common, signals_full, c_start_ts, c_end_ts)
        sims, act = run_trials(c_prices, c_signals, CFG.base_cost_bps, cfg=CFG)
        rep = full_report(sims, act, CFG)
        log(f"\n--- {name} ({c_start_ts.date()} -> {c_end_ts.date()}) ---")
        log(metrics_table(rep).to_string(index=False))

    # ── OOS-vs-IS decay ──────────────────────────────────────────────────────
    log("")
    log("=" * 100)
    log("OOS-vs-IS DECAY (context, not a standalone PASS criterion) -- OOS XIRR minus IS XIRR")
    log("=" * 100)
    decay_rows = []
    for t in TRIAL_DEFS:
        key = t["key"]
        is_xirr = report_is[key]["xirr"]
        oos_xirr = report_oos_base[key]["xirr"]
        decay_rows.append({
            "Trial": t["label"], "IS XIRR": fmt_pct(is_xirr), "OOS XIRR": fmt_pct(oos_xirr),
            "OOS-IS (pp)": f"{(oos_xirr - is_xirr) * 100:.2f}pp" if pd.notna(is_xirr) and pd.notna(oos_xirr) else "n/a",
        })
    log(pd.DataFrame(decay_rows).to_string(index=False))

    # ── DSR (Deflated Sharpe Ratio) -- procedural completeness only ─────────
    log("")
    log("=" * 100)
    log("DEFLATED SHARPE RATIO (DSR) -- procedural completeness only, POOR STATISTICAL FIT here "
        "(see module docstring for the full 3-reason explanation: N=4 too small for the "
        "extreme-value asymptotics; trials are NOT independent -- trial 4 = trial 2 AND trial "
        "3's RSI sub-condition; all 4 trials share the same asset/mechanics/overlapping history)")
    log("=" * 100)
    sharpe_vals = np.array([oos_sharpe[t["key"]] for t in TRIAL_DEFS if pd.notna(oos_sharpe[t["key"]])])
    sharpe_std = float(np.std(sharpe_vals, ddof=1)) if len(sharpe_vals) > 1 else float("nan")
    expected_max_sharpe = expected_max_sharpe_under_trials(len(TRIAL_DEFS), sharpe_std)
    log(f"  Observed OOS Sharpe values across the 4 trials: "
        f"{[round(float(x), 3) for x in sharpe_vals]}")
    log(f"  Cross-trial Sharpe std dev: {sharpe_std:.4f}")
    log(f"  E[max Sharpe | N=4 iid-normal trials] (Bailey & Lopez de Prado 2014 approximation): "
        f"{expected_max_sharpe:.4f}")
    max_observed_sharpe = float(np.max(sharpe_vals)) if len(sharpe_vals) else float("nan")
    log(f"  Max OBSERVED trial Sharpe: {max_observed_sharpe:.4f}  "
        f"(vs E[max SR under luck alone] {expected_max_sharpe:.4f} -- "
        f"{'exceeds' if max_observed_sharpe > expected_max_sharpe else 'does NOT clearly exceed'} "
        f"the naive luck-only benchmark, but see caveats above: this comparison is NOT treated "
        f"as a PASS/FAIL criterion in this gate precisely because DSR is a poor fit for 4 "
        f"non-independent, nested trials on one asset.")

    # ── Verdict ──────────────────────────────────────────────────────────────
    log("")
    log("=" * 100)
    log("VERDICT -- PASS can ONLY validate a PRICE-ONLY ENTRY-TIMING OVERLAY on the ALREADY-"
        "APPROVED capped satellite policy, NEVER forward AAPL alpha and NEVER that technical "
        "timing generalizes beyond AAPL. AAPL was picked WITH HINDSIGHT knowledge of its "
        "historical outperformance. Excludes tax consequences entirely.")
    log("=" * 100)

    baseline_xirr = report_oos_base[BASELINE_KEY]["xirr"]
    baseline_dd = report_oos_base[BASELINE_KEY]["max_dd"]
    baseline_vol = report_oos_base[BASELINE_KEY]["vol_ann_pct"]

    verdicts = {}
    verdicts[BASELINE_KEY] = ("BENCHMARK (not gated) -- the 3 delayed trials are judged against "
                               "this immediate-activation baseline.")
    log(f"\n  {TRIAL_BY_KEY[BASELINE_KEY]['label']}: {verdicts[BASELINE_KEY]}")

    trial_pass = {}
    for key in DELAYED_TRIAL_KEYS:
        t = TRIAL_BY_KEY[key]
        trial_xirr = report_oos_base[key]["xirr"]
        trial_dd = report_oos_base[key]["max_dd"]
        trial_vol = report_oos_base[key]["vol_ann_pct"]

        xirr_shortfall_pp = (baseline_xirr - trial_xirr) * 100.0
        xirr_ok = xirr_shortfall_pp <= CFG.max_xirr_shortfall_pp

        dd_improvement_pct = (baseline_dd - trial_dd) / baseline_dd * 100.0 if baseline_dd else float("nan")
        vol_improvement_pct = (baseline_vol - trial_vol) / baseline_vol * 100.0 if baseline_vol else float("nan")
        risk_ok = (pd.notna(dd_improvement_pct) and dd_improvement_pct >= CFG.min_risk_improvement_pct) or \
                  (pd.notna(vol_improvement_pct) and vol_improvement_pct >= CFG.min_risk_improvement_pct)

        this_stress_ok = stress_ok[key]
        this_cohort_rate = cohort_activation_rate[key]
        cohort_ok = pd.notna(this_cohort_rate) and this_cohort_rate >= CFG.min_cohort_activation_rate_pct

        passed = xirr_ok and risk_ok and this_stress_ok and cohort_ok
        trial_pass[key] = passed

        log(f"\n  {t['label']}:")
        log(f"    (1) XIRR shortfall vs immediate: {xirr_shortfall_pp:.3f}pp "
            f"(threshold <= {CFG.max_xirr_shortfall_pp:.2f}pp) -> {'PASS' if xirr_ok else 'FAIL'}")
        log(f"    (2) Risk improvement: maxDD {dd_improvement_pct:.2f}% better, vol "
            f"{vol_improvement_pct:.2f}% better (threshold >= "
            f"{CFG.min_risk_improvement_pct:.1f}% on EITHER) -> {'PASS' if risk_ok else 'FAIL'}")
        log(f"    (3) Stress survival: own degradation {stress_degradation[key]:.3f}% "
            f"(threshold <= {CFG.max_stress_wealth_degradation_pct:.1f}%) -> "
            f"{'PASS' if this_stress_ok else 'FAIL'}")
        log(f"    (4) Cohort activation rate: {this_cohort_rate:.1f}% "
            f"(threshold >= {CFG.min_cohort_activation_rate_pct:.1f}%) -> "
            f"{'PASS' if cohort_ok else 'FAIL'}")
        log(f"    => OVERALL: {'PASS' if passed else 'FAIL'} -- "
            f"{'all four conditions hold.' if passed else 'at least one condition failed above.'}")

    log("")
    passing = [k for k in DELAYED_TRIAL_KEYS if trial_pass[k]]
    if passing:
        names = " and ".join(TRIAL_BY_KEY[k]["label"] for k in passing)
        log(f"  OVERALL: {names} PASS as a validated price-only entry-timing overlay -- hand off "
            f"to hedge-fund-manager / tradfi-portfolio-manager for notification-first paper "
            f"tracking, behind human sign-off, NOT as proof of forward AAPL alpha or of technical "
            f"timing generalizing beyond AAPL.")
    else:
        log("  OVERALL: NONE of the 3 delayed-activation trials pass the predeclared bands -- "
            "price-only waiting has no validated edge here. This is a valid, valuable 'no edge "
            "found' result per the strategy-discovery-backtest gate's own honesty rules, not a "
            "failure to fix by loosening thresholds. Immediate activation (the already-approved "
            "policy from the prior gate) remains the recommendation.")

    # ── Chart (illustrative full-history run, NOT used for verdict metrics) ─
    log("")
    log(f"Saving chart to {CHART_PATH} ... (illustrative full-history run, fresh state at "
        f"{common_start.date()}, base cost 2bps -- NOT the verdict window; verdict metrics use "
        f"the OOS-headline fresh-start window reported above)")
    sims_full_hist, act_full_hist = run_trials(weekly_common, signals_full, CFG.base_cost_bps, cfg=CFG)
    fig, ax = plt.subplots(figsize=(13, 7))
    colors = {"immediate": "#4f81bd", "weekly_ema": "#c0504d",
              "daily_sma_rsi": "#9bbb59", "weekly_ema_rsi": "#f0ad4e"}
    for t in TRIAL_DEFS:
        sim = sims_full_hist[t["key"]]
        ax.plot(sim.index, sim["wealth_multiple"], label=t["label"], color=colors.get(t["key"]),
                linewidth=1.6)
    ax.axvline(oos_start_ts, color="black", linestyle=":", linewidth=1.2,
               label=f"OOS headline start ({CFG.oos_start})")
    ax.axhline(1.0, color="black", linewidth=0.5)
    ax.set_title("AAPL entry-trigger overlay -- wealth multiple (account value / cumulative\n"
                 "initial+contributions), illustrative full-history run (fresh state at "
                 f"{common_start.date()})")
    ax.set_ylabel("Wealth multiple (x initial+contributions)")
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(CHART_PATH, dpi=130)
    plt.close(fig)
    log("  Chart saved.")

    SUMMARY_PATH.write_text("\n".join(LOG_LINES) + "\n")
    log(f"\nSummary written to {SUMMARY_PATH}")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        result_ok = run_selfchecks(CFG)
        print("\nSELF-CHECK RESULT:", "PASS" if result_ok else "FAIL")
        sys.exit(0 if result_ok else 1)
    main()
