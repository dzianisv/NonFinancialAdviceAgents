"""
The gate harness — implements the strategy-discovery-backtest pipeline programmatically.

Strategy interface:
    a strategy is a callable  signals(df_dict, params) -> pd.Series (or dict[str, pd.Series])
    of target positions (-1/0/1 or continuous weight) indexed by bar, using ONLY prior-close
    information. The signal function itself must already be shift(+1)'d (decided on prior bar
    close) — the harness ALSO runs an independent shift-collapse canary test (see
    look_ahead_canary()) so a strategy that cheats gets caught even if it "forgot" its own shift.

The harness OWNS execution simulation via core/fills.py — strategies output TARGET POSITIONS,
never fills or P&L directly, so a strategy cannot hand-pick favorable fills.

Weekly boundary convention: Monday 00:00 UTC (hardcoded WEEK_START_DOW=0 constant below —
single source of truth per house rule).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np
import pandas as pd

from core.costs import CostConfig

# ---- house-rule constants (single source of truth) ----
WEEK_START_DOW = 0  # Monday=0 for pandas .dt.dayofweek; weekly boundary = Monday 00:00 UTC

IS_START = "2020-01-01"
IS_END = "2023-12-31"
OOS_START = "2024-01-01"
# OOS_END left open (None = through latest available data)

BARS_PER_YEAR = {
    "1d": 365,
    "1h": 24 * 365,
    "5m": 12 * 24 * 365,
}

RF = 0.04  # annual risk-free rate used in Sharpe/Sortino

# Regime windows for crypto (documented, used by regime_report())
REGIME_WINDOWS = {
    "2021_bull": ("2021-01-01", "2021-12-31"),
    "2022_luna_ftx": ("2022-01-01", "2022-12-31"),
    "2023_2024_recovery": ("2023-01-01", "2024-12-31"),
    "2025_drawdown": ("2025-01-01", "2025-12-31"),
    "2026_ytd": ("2026-01-01", None),
}


StrategyFn = Callable[[dict, dict], pd.Series]


def week_start_utc(ts: pd.Timestamp) -> pd.Timestamp:
    """Return the Monday 00:00 UTC that begins the week containing ts. Single shared
    definition of the weekly boundary per house rule."""
    ts = pd.Timestamp(ts)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    days_since_monday = ts.dayofweek  # Monday=0
    monday = (ts - pd.Timedelta(days=days_since_monday)).normalize()
    return monday


# ---------------------------------------------------------------------------
# Look-ahead canary
# ---------------------------------------------------------------------------

def look_ahead_canary(strategy_fn: StrategyFn, df_dict: dict, params: dict) -> dict:
    """Look-ahead detector: corrupt ONE middle bar's OHLC to a wild 100x spike, re-run the
    strategy, and assert the signal AT and BEFORE the corrupted bar is unchanged. A strategy
    that only ever uses PRIOR-bar-close information (the required contract) decides bar t's
    signal from bars < t only, so it cannot see a spike planted AT bar t (let alone after it);
    its signal for every bar <= t must be byte-identical pre/post corruption. If it changes,
    the strategy is using same-bar (or future) information -> look-ahead detected, FAIL.
    """
    sym = next(iter(df_dict))
    df = df_dict[sym]
    if len(df) < 20:
        return {"ok": True, "note": "insufficient bars for canary, skipped"}

    baseline = strategy_fn(df_dict, params)
    baseline = baseline[sym] if isinstance(baseline, dict) else baseline

    # Corrupt a MIDDLE bar's close/high/low to a wild spike; a non-leaking (prior-bar-only)
    # strategy's signal AT and BEFORE the corrupted bar must be unaffected — bar t's decision
    # can only ever see bars < t, so it never observes bar t's own (corrupted) close.
    mid = len(df) // 2
    corrupted = {}
    for k, v in df_dict.items():
        cv = v.copy()
        if k == sym:
            spike = cv["close"].iloc[mid] * 100  # absurd 100x spike
            cv.iloc[mid, cv.columns.get_loc("close")] = spike
            cv.iloc[mid, cv.columns.get_loc("high")] = spike
            cv.iloc[mid, cv.columns.get_loc("low")] = spike
        corrupted[k] = cv

    mutated = strategy_fn(corrupted, params)
    mutated = mutated[sym] if isinstance(mutated, dict) else mutated

    before = baseline.iloc[:mid + 1]  # inclusive of the corrupted bar itself
    after = mutated.iloc[:mid + 1]
    aligned = before.index.intersection(after.index)
    match = np.allclose(before.loc[aligned].fillna(0), after.loc[aligned].fillna(0), atol=1e-9)

    return {
        "ok": bool(match),
        "note": "signal at/before the corrupted bar must be unchanged by a same-bar spike"
                if match else
                "LOOK-AHEAD DETECTED: signal at/before the corrupted bar CHANGED when that "
                "bar was spiked — strategy is using same-bar (non-prior-bar) information",
    }


def shift_collapse_check(strategy_fn: StrategyFn, df_dict: dict, params: dict,
                          cost_cfg: CostConfig = CostConfig(), bars_per_year: int = 365) -> dict:
    """House-rule mandated check: re-run the backtest with the strategy's own signal shifted
    ONE EXTRA bar (double-lag, strictly more conservative/later than the contractual
    prior-bar-close decision) and confirm Sharpe does not collapse in a way that reveals
    look-ahead. A strategy with genuine prior-bar-only signal should be roughly insensitive
    to (or slightly worse off from) one extra bar of lag; a strategy that was secretly
    peeking at same-bar/future data sees its edge collapse once forced to lag an additional
    bar. We flag if the extra-shift Sharpe collapses > 50% relative to the base (contractual)
    Sharpe while the base Sharpe is positive -- that pattern is the tell for look-ahead."""
    sym0 = next(iter(df_dict))
    net0, w0 = run_backtest(strategy_fn, df_dict, params, cost_cfg, bars_per_year)
    m0 = compute_metrics(net0, w0, bars_per_year) if net0 is not None else None

    raw_signal = strategy_fn(df_dict, params)
    sig_map = raw_signal if isinstance(raw_signal, dict) else {sym0: raw_signal}
    shifted_results = {}
    for sym, sig in sig_map.items():
        if sym not in df_dict:
            continue
        close = df_dict[sym]["close"]
        w = sig.reindex(close.index).fillna(0.0).shift(1).fillna(0.0)  # ONE EXTRA bar of lag
        ret = close.pct_change().fillna(0.0)
        turnover = w.diff().abs().fillna(w.abs())
        cost = turnover * cost_cfg.taker_rate
        shifted_results[sym] = w * ret - cost
    if not shifted_results:
        return {"ok": True, "note": "no data to check"}
    M = pd.concat(shifted_results, axis=1).fillna(0.0)
    port_shifted = M.mean(axis=1)
    m1 = compute_metrics(port_shifted, port_shifted.abs(), bars_per_year)

    if m0 is None or m1 is None:
        return {"ok": True, "note": "insufficient data for shift-collapse comparison"}

    sharpe0, sharpe1 = m0.sharpe, m1.sharpe
    collapsed = sharpe0 > 0 and (sharpe1 < 0.5 * sharpe0)
    return {
        "ok": not collapsed,
        "sharpe_base": sharpe0,
        "sharpe_extra_shift": sharpe1,
        "note": ("PASS: Sharpe stable under an extra bar of lag (no look-ahead signature)"
                 if not collapsed else
                 "WARN: Sharpe collapses >50% under one extra bar of lag - possible look-ahead"),
    }


# ---------------------------------------------------------------------------
# Metrics contract
# ---------------------------------------------------------------------------

@dataclass
class Metrics:
    cagr: float
    sharpe: float
    sortino: float
    calmar: float
    max_dd: float
    turnover: float
    round_trips_per_day: float
    win_rate: float
    profit_factor: float
    breakeven_cost_bps: float
    exposure: float
    n_bars: int
    equity_curve: pd.Series = field(repr=False)

    def to_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items() if k != "equity_curve"}
        return d


def compute_metrics(net_returns: pd.Series, weights: pd.Series, bars_per_year: int) -> Optional[Metrics]:
    net = net_returns.dropna()
    if len(net) < 10 or net.std() == 0:
        return None
    eq = (1 + net).cumprod()
    yrs = len(net) / bars_per_year
    cagr = eq.iloc[-1] ** (1 / yrs) - 1 if eq.iloc[-1] > 0 and yrs > 0 else -1.0
    vol = net.std() * math.sqrt(bars_per_year)
    sharpe = (net.mean() * bars_per_year - RF) / vol if vol > 0 else 0.0

    downside = net[net < 0]
    dvol = downside.std() * math.sqrt(bars_per_year) if len(downside) > 1 else 0.0
    sortino = (net.mean() * bars_per_year - RF) / dvol if dvol > 0 else 0.0

    dd = (eq / eq.cummax() - 1).min()
    calmar = cagr / abs(dd) if dd < 0 else 0.0

    turnover = weights.diff().abs().fillna(weights.abs()).sum()
    round_trips_per_day = (weights.diff().abs().fillna(0) > 0.01).sum() / max(yrs * 365, 1e-9)

    wins = net[net > 0]
    losses = net[net < 0]
    win_rate = len(wins) / len(net) if len(net) else 0.0
    profit_factor = wins.sum() / abs(losses.sum()) if losses.sum() != 0 else float("inf")

    gross_edge = net.mean() * bars_per_year
    avg_turnover_per_year = turnover / max(yrs, 1e-9)
    breakeven_cost_bps = (gross_edge / avg_turnover_per_year * 10_000) if avg_turnover_per_year > 0 else float("nan")

    exposure = weights.abs().mean()

    return Metrics(
        cagr=cagr, sharpe=sharpe, sortino=sortino, calmar=calmar, max_dd=dd,
        turnover=turnover, round_trips_per_day=round_trips_per_day, win_rate=win_rate,
        profit_factor=profit_factor, breakeven_cost_bps=breakeven_cost_bps,
        exposure=exposure, n_bars=len(net), equity_curve=eq,
    )


# ---------------------------------------------------------------------------
# Deflated Sharpe Ratio (Bailey & Lopez de Prado, 2014)
# ---------------------------------------------------------------------------

def _norm_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _norm_ppf(p: float) -> float:
    # Acklam's inverse normal CDF approximation (no scipy dependency).
    if p <= 0 or p >= 1:
        raise ValueError("p must be in (0,1)")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00]
    p_low, p_high = 0.02425, 1 - 0.02425
    if p < p_low:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p <= p_high:
        q = p - 0.5
        r = q*q
        return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
               (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
    q = math.sqrt(-2 * math.log(1 - p))
    return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
            ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)


def deflated_sharpe_ratio(sharpe_hat: float, n_trials: int, n_obs: int,
                           skew: float = 0.0, kurt: float = 3.0,
                           sharpe_var_trials: Optional[float] = None) -> dict:
    """Bailey & Lopez de Prado (2014) deflated Sharpe ratio: probability the observed Sharpe
    is genuinely > 0 after accounting for selection bias from `n_trials` configurations tried.

    sharpe_hat: the (non-deflated, per-period) Sharpe of the selected strategy.
    n_trials: number of independent configurations tried during selection.
    n_obs: number of return observations used to estimate sharpe_hat.
    skew/kurt: skewness/kurtosis of the strategy's per-period returns (default = normal).
    sharpe_var_trials: variance of Sharpe ratios across trials; if None, assumed 1.0 (a
        conservative default per the paper's guidance when trial-level distribution is unknown).
    """
    if n_trials < 1:
        n_trials = 1
    var_sr = sharpe_var_trials if sharpe_var_trials is not None else 1.0
    euler_gamma = 0.5772156649015329
    if n_trials > 1:
        e_max_sr = math.sqrt(var_sr) * (
            (1 - euler_gamma) * _norm_ppf(1 - 1.0 / n_trials) +
            euler_gamma * _norm_ppf(1 - 1.0 / (n_trials * math.e))
        )
    else:
        e_max_sr = 0.0

    denom = math.sqrt(max(1e-12, 1 - skew * sharpe_hat + (kurt - 1) / 4 * sharpe_hat ** 2))
    if n_obs <= 1:
        return {"dsr": float("nan"), "expected_max_sharpe_noise": e_max_sr, "note": "insufficient obs"}
    z = (sharpe_hat - e_max_sr) * math.sqrt(n_obs - 1) / denom
    dsr = _norm_cdf(z)
    return {"dsr": dsr, "expected_max_sharpe_noise": e_max_sr, "z": z, "n_trials": n_trials, "n_obs": n_obs}


# ---------------------------------------------------------------------------
# IS/OOS split + rolling walk-forward
# ---------------------------------------------------------------------------

def slice_period(s: pd.Series, start: Optional[str] = None, end: Optional[str] = None) -> pd.Series:
    if start:
        s = s[s.index >= pd.Timestamp(start, tz="UTC")]
    if end:
        s = s[s.index <= pd.Timestamp(end, tz="UTC")]
    return s


def run_backtest(strategy_fn: StrategyFn, df_dict: dict, params: dict, cost_cfg: CostConfig,
                  bars_per_year: int, start: Optional[str] = None, end: Optional[str] = None,
                  is_maker: bool = False) -> tuple[Optional[pd.Series], Optional[pd.Series]]:
    """Run a strategy over df_dict (possibly multi-asset), sliced to [start,end], applying
    the cost model to weight changes (turnover * fee_rate). This is the SIMPLE (non-fill-sim)
    execution path used for the walk-forward/gate scoring loop — the full maker-fill simulator
    (core/fills.py) is used separately for the fill-model stress tiers on a chosen strategy,
    since running the bar-by-bar limit-order simulator inside a large parameter sweep would be
    prohibitively slow and isn't necessary to score signal quality net of realistic costs.
    Returns (net_returns, weights) both sliced to the requested window, or (None, None)."""
    raw_signal = strategy_fn(df_dict, params)
    # Return-space cost math uses the plain per-side rate (maker/taker * stress multiplier).
    # The $0.01 min-fee floor is a per-order DOLLAR amount, not a rate, and only binds at
    # tiny notionals — it is exercised directly in core/costs.py tests and in the fill-sim
    # path (core/fills.py), not in this return-space walk-forward scoring loop.
    fee_rate = (cost_cfg.maker_rate if is_maker else cost_cfg.taker_rate) * cost_cfg.fee_multiplier

    results = {}
    weight_map = {}
    symbols = df_dict.keys() if isinstance(raw_signal, dict) else [next(iter(df_dict))]
    sig_map = raw_signal if isinstance(raw_signal, dict) else {next(iter(df_dict)): raw_signal}

    for sym in symbols:
        if sym not in df_dict or sym not in sig_map:
            continue
        close = df_dict[sym]["close"]
        w = sig_map[sym].reindex(close.index).fillna(0.0)
        w = slice_period(w, start, end)
        c = slice_period(close, start, end)
        if len(c) < 5:
            continue
        ret = c.pct_change().fillna(0.0)
        turnover = w.diff().abs().fillna(w.abs())
        cost = turnover * fee_rate
        net = (w.shift(0) * ret) - cost  # w already prior-bar-decided by the strategy contract
        results[sym] = net
        weight_map[sym] = w

    if not results:
        return None, None
    M = pd.concat(results, axis=1).fillna(0.0)
    port = M.mean(axis=1)
    W = pd.concat(weight_map, axis=1).fillna(0.0).mean(axis=1)
    return port, W


def walk_forward(strategy_fn: StrategyFn, df_dict: dict, param_grid: list[dict], cost_cfg: CostConfig,
                  bars_per_year: int, fit_months: int = 12, score_months: int = 3,
                  start: Optional[str] = None, end: Optional[str] = None) -> dict:
    """Rolling walk-forward: fit (select best params by Sharpe) on a `fit_months` window,
    score on the NEXT `score_months` window (pure OOS for that window), roll forward by
    `score_months`, concatenate all OOS windows into one continuous OOS return series.
    Reports OOS-by-window and the concatenated OOS score."""
    sym0 = next(iter(df_dict))
    idx = df_dict[sym0].index
    if start:
        idx = idx[idx >= pd.Timestamp(start, tz="UTC")]
    if end:
        idx = idx[idx <= pd.Timestamp(end, tz="UTC")]
    if len(idx) == 0:
        return {"windows": [], "oos_concat": None, "oos_weights_concat": None}

    windows = []
    cursor = idx[0]
    last = idx[-1]
    while True:
        fit_start = cursor
        fit_end = fit_start + pd.DateOffset(months=fit_months)
        score_start = fit_end
        score_end = score_start + pd.DateOffset(months=score_months)
        if score_start > last:
            break
        windows.append((fit_start, fit_end, score_start, min(score_end, last + pd.Timedelta(days=1))))
        cursor = cursor + pd.DateOffset(months=score_months)

    oos_segments = []
    oos_weight_segments = []
    window_reports = []
    for fit_start, fit_end, score_start, score_end in windows:
        best = None
        for params in param_grid:
            net, w = run_backtest(strategy_fn, df_dict, params, cost_cfg, bars_per_year,
                                   start=str(fit_start.date()), end=str(fit_end.date()))
            m = compute_metrics(net, w, bars_per_year) if net is not None else None
            if m and (best is None or m.sharpe > best[1].sharpe):
                best = (params, m)
        if best is None:
            continue
        params, _ = best
        oos_net, oos_w = run_backtest(strategy_fn, df_dict, params, cost_cfg, bars_per_year,
                                       start=str(score_start.date()), end=str(score_end.date()))
        oos_m = compute_metrics(oos_net, oos_w, bars_per_year) if oos_net is not None else None
        window_reports.append({
            "fit": (str(fit_start.date()), str(fit_end.date())),
            "score": (str(score_start.date()), str(score_end.date())),
            "params": params,
            "oos_metrics": oos_m.to_dict() if oos_m else None,
        })
        if oos_net is not None:
            oos_segments.append(oos_net)
            oos_weight_segments.append(oos_w)

    oos_concat = pd.concat(oos_segments).sort_index() if oos_segments else None
    oos_w_concat = pd.concat(oos_weight_segments).sort_index() if oos_weight_segments else None
    if oos_concat is not None:
        oos_concat = oos_concat[~oos_concat.index.duplicated(keep="first")]
        oos_w_concat = oos_w_concat[~oos_w_concat.index.duplicated(keep="first")]

    return {"windows": window_reports, "oos_concat": oos_concat, "oos_weights_concat": oos_w_concat}


# ---------------------------------------------------------------------------
# Regime report
# ---------------------------------------------------------------------------

def regime_report(strategy_fn: StrategyFn, df_dict: dict, params: dict, cost_cfg: CostConfig,
                   bars_per_year: int) -> dict:
    out = {}
    for name, (start, end) in REGIME_WINDOWS.items():
        net, w = run_backtest(strategy_fn, df_dict, params, cost_cfg, bars_per_year, start=start, end=end)
        m = compute_metrics(net, w, bars_per_year) if net is not None else None
        out[name] = m.to_dict() if m else None
    return out


# ---------------------------------------------------------------------------
# Stress suite driver (cost/turnover-level; the bar-level fill-sim stress tiers live
# in core/fills.py and are exercised directly in tests + the harness self-test).
# ---------------------------------------------------------------------------

def stress_suite(strategy_fn: StrategyFn, df_dict: dict, params: dict, base_cost_cfg: CostConfig,
                  bars_per_year: int, start: Optional[str] = None, end: Optional[str] = None) -> dict:
    from core.costs import STRESS_2X_FEES
    out = {}
    net, w = run_backtest(strategy_fn, df_dict, params, STRESS_2X_FEES, bars_per_year, start, end)
    out["2x_fees"] = compute_metrics(net, w, bars_per_year).to_dict() if net is not None and compute_metrics(net, w, bars_per_year) else None

    # delayed-fill stress: shift weights one extra bar (approximates fills always one bar late)
    raw_signal = strategy_fn(df_dict, params)
    sym0 = next(iter(df_dict))
    sig_map = raw_signal if isinstance(raw_signal, dict) else {sym0: raw_signal}
    delayed_results = {}
    for sym, sig in sig_map.items():
        if sym not in df_dict:
            continue
        close = df_dict[sym]["close"]
        w_delayed = sig.reindex(close.index).fillna(0.0).shift(1).fillna(0.0)
        w_delayed = slice_period(w_delayed, start, end)
        c = slice_period(close, start, end)
        if len(c) < 5:
            continue
        ret = c.pct_change().fillna(0.0)
        turnover = w_delayed.diff().abs().fillna(w_delayed.abs())
        cost = turnover * base_cost_cfg.taker_rate
        delayed_results[sym] = w_delayed * ret - cost
    if delayed_results:
        M = pd.concat(delayed_results, axis=1).fillna(0.0)
        port = M.mean(axis=1)
        m = compute_metrics(port, port.abs(), bars_per_year)
        out["delayed_fill_1bar"] = m.to_dict() if m else None
    else:
        out["delayed_fill_1bar"] = None

    return out


# ---------------------------------------------------------------------------
# Top-level gate() entry point
# ---------------------------------------------------------------------------

def gate(strategy_fn: StrategyFn, df_dict: dict, param_grid: list[dict], interval: str,
         cost_cfg: CostConfig = CostConfig(), fit_months: int = 12, score_months: int = 3) -> dict:
    """Run the full pipeline: canary -> IS select -> OOS walk-forward -> deflated Sharpe ->
    regimes -> stress -> verdict. Returns a report dict (JSON-serializable-ish, equity curves
    excluded from to_dict())."""
    bars_per_year = BARS_PER_YEAR.get(interval)
    if bars_per_year is None:
        raise ValueError(f"unknown interval {interval!r}, add to BARS_PER_YEAR")

    canary = look_ahead_canary(strategy_fn, df_dict, param_grid[0])
    shift_check = shift_collapse_check(strategy_fn, df_dict, param_grid[0])

    is_rows = []
    for params in param_grid:
        net, w = run_backtest(strategy_fn, df_dict, params, cost_cfg, bars_per_year, end=IS_END)
        m = compute_metrics(net, w, bars_per_year) if net is not None else None
        if m:
            is_rows.append((params, m))
    if not is_rows:
        return {"verdict": "FAIL (no edge found)", "reason": "no IS configuration produced valid metrics",
                "canary": canary, "shift_check": shift_check}

    best_params, best_is_metrics = max(is_rows, key=lambda r: r[1].sharpe)
    n_trials = len(param_grid)

    oos_net, oos_w = run_backtest(strategy_fn, df_dict, best_params, cost_cfg, bars_per_year, start=OOS_START)
    oos_metrics = compute_metrics(oos_net, oos_w, bars_per_year) if oos_net is not None else None

    wf = walk_forward(strategy_fn, df_dict, param_grid, cost_cfg, bars_per_year,
                       fit_months=fit_months, score_months=score_months, start=IS_START)
    wf_oos_metrics = compute_metrics(wf["oos_concat"], wf["oos_weights_concat"], bars_per_year) \
        if wf["oos_concat"] is not None else None

    dsr = None
    if oos_metrics:
        period_sharpe = oos_metrics.sharpe / math.sqrt(bars_per_year)  # per-period, not annualized
        dsr = deflated_sharpe_ratio(period_sharpe, n_trials=n_trials, n_obs=oos_metrics.n_bars)

    regimes = regime_report(strategy_fn, df_dict, best_params, cost_cfg, bars_per_year)
    stress = stress_suite(strategy_fn, df_dict, best_params, cost_cfg, bars_per_year, start=OOS_START)

    # ---- verdict ----
    reasons = []
    passed = True
    if oos_metrics is None or oos_metrics.sharpe <= 0:
        passed = False
        reasons.append("OOS Sharpe <= 0 net of costs")
    if dsr and not math.isnan(dsr.get("dsr", float("nan"))) and dsr["dsr"] < 0.95:
        passed = False
        reasons.append(f"deflated Sharpe probability {dsr['dsr']:.2f} < 0.95 threshold")
    stress_2x = stress.get("2x_fees")
    if stress_2x is None or stress_2x["sharpe"] <= 0:
        passed = False
        reasons.append("edge dies under 2x fee stress")
    stress_delay = stress.get("delayed_fill_1bar")
    if stress_delay is None or stress_delay["sharpe"] <= 0:
        passed = False
        reasons.append("edge dies under 1-bar delayed-fill stress")

    verdict = "PASS" if passed else "FAIL (no edge found)"

    return {
        "verdict": verdict,
        "reasons": reasons,
        "canary": canary,
        "shift_check": shift_check,
        "best_params": best_params,
        "n_trials": n_trials,
        "in_sample": best_is_metrics.to_dict(),
        "out_of_sample": oos_metrics.to_dict() if oos_metrics else None,
        "walk_forward_oos": wf_oos_metrics.to_dict() if wf_oos_metrics else None,
        "walk_forward_windows": wf["windows"],
        "deflated_sharpe": dsr,
        "regimes": regimes,
        "stress": stress,
    }
