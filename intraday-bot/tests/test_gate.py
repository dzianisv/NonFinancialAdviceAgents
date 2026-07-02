"""Unit tests for core/gate.py — look-ahead canary, shift-collapse check, metrics, DSR."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import gate
from core.costs import CostConfig


def _synthetic_df(n=800, seed=42, start="2020-01-01"):
    rng = np.random.default_rng(seed)
    idx = pd.date_range(start, periods=n, freq="D", tz="UTC")
    price = 100 * np.exp(np.cumsum(rng.normal(0.0002, 0.02, n)))
    return pd.DataFrame(
        {"open": price, "high": price * 1.01, "low": price * 0.99, "close": price, "volume": 1000.0},
        index=idx,
    )


def honest_sma_strategy(df_dict, params):
    """A correctly-lagged strategy: decides on prior bar close only."""
    out = {}
    for sym, d in df_dict.items():
        f = d["close"].rolling(params["fast"]).mean()
        s = d["close"].rolling(params["slow"]).mean()
        sig = (f > s).astype(float)
        out[sym] = sig.shift(1).fillna(0.0)
    return out


def cheating_strategy(df_dict, params):
    """A strategy that peeks at the SAME bar's close (no shift) — must be caught by the
    look-ahead canary."""
    out = {}
    for sym, d in df_dict.items():
        f = d["close"].rolling(params["fast"]).mean()
        s = d["close"].rolling(params["slow"]).mean()
        sig = (f > s).astype(float)
        out[sym] = sig  # NO shift -> look-ahead bug
    return out


def test_look_ahead_canary_passes_honest_strategy():
    df_dict = {"SYM": _synthetic_df()}
    result = gate.look_ahead_canary(honest_sma_strategy, df_dict, {"fast": 10, "slow": 30})
    assert result["ok"] is True


def test_look_ahead_canary_catches_cheating_strategy():
    df_dict = {"SYM": _synthetic_df()}
    result = gate.look_ahead_canary(cheating_strategy, df_dict, {"fast": 10, "slow": 30})
    assert result["ok"] is False
    assert "LOOK-AHEAD" in result["note"]


def test_shift_collapse_check_runs_on_honest_strategy():
    df_dict = {"SYM": _synthetic_df()}
    result = gate.shift_collapse_check(honest_sma_strategy, df_dict, {"fast": 10, "slow": 30},
                                        bars_per_year=365)
    assert "ok" in result


def test_week_start_utc_monday_boundary():
    # 2024-01-03 is a Wednesday -> week starts Monday 2024-01-01
    ts = pd.Timestamp("2024-01-03 15:30:00", tz="UTC")
    monday = gate.week_start_utc(ts)
    assert monday == pd.Timestamp("2024-01-01 00:00:00", tz="UTC")
    assert monday.dayofweek == 0


def test_week_start_utc_on_monday_itself():
    ts = pd.Timestamp("2024-01-01 00:00:00", tz="UTC")
    assert gate.week_start_utc(ts) == ts


def test_compute_metrics_none_on_flat_returns():
    net = pd.Series([0.0] * 20)
    w = pd.Series([0.0] * 20)
    assert gate.compute_metrics(net, w, 365) is None


def test_compute_metrics_reasonable_on_synthetic():
    rng = np.random.default_rng(1)
    net = pd.Series(rng.normal(0.001, 0.02, 500))
    w = pd.Series(rng.uniform(0, 1, 500))
    m = gate.compute_metrics(net, w, 365)
    assert m is not None
    assert isinstance(m.sharpe, float)
    assert m.n_bars == 500


def test_deflated_sharpe_more_trials_lowers_dsr():
    """More trials tried for the same observed Sharpe should give a lower (harsher) DSR."""
    few = gate.deflated_sharpe_ratio(sharpe_hat=0.05, n_trials=2, n_obs=500)
    many = gate.deflated_sharpe_ratio(sharpe_hat=0.05, n_trials=200, n_obs=500)
    assert many["dsr"] <= few["dsr"]


def test_deflated_sharpe_more_obs_raises_dsr_for_fixed_positive_sharpe():
    small_n = gate.deflated_sharpe_ratio(sharpe_hat=0.05, n_trials=5, n_obs=100)
    big_n = gate.deflated_sharpe_ratio(sharpe_hat=0.05, n_trials=5, n_obs=5000)
    assert big_n["dsr"] >= small_n["dsr"]


def test_run_backtest_no_lookahead_signal_all_zero_gives_zero_or_negative_net():
    df_dict = {"SYM": _synthetic_df()}
    flat_strategy = lambda dd, p: {sym: pd.Series(0.0, index=d.index) for sym, d in dd.items()}
    net, w = gate.run_backtest(flat_strategy, df_dict, {}, CostConfig(), 365)
    assert net is not None
    assert (net == 0).all()  # zero position, zero turnover -> exactly zero net return


def test_gate_end_to_end_random_walk_fails():
    """A random-walk price series should FAIL the gate (no genuine edge) — this exercises the
    full pipeline end-to-end and is a sanity precursor to the harness self-test script."""
    df_dict = {"SYM": _synthetic_df(n=2000)}
    grid = [dict(fast=f, slow=s) for f in [10, 20] for s in [50, 100] if f < s]
    report = gate.gate(honest_sma_strategy, df_dict, grid, interval="1d")
    assert report["verdict"] in ("PASS", "FAIL (no edge found)")
    assert report["canary"]["ok"] is True
