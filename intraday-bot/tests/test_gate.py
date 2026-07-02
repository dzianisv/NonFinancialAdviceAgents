"""Unit tests for core/gate.py — look-ahead canary, shift-collapse check, metrics, DSR."""
import math
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


# ---------------------------------------------------------------------------
# P0 #2 (2026-07-02): DSR units-bug regression tests — locks the corrected math.
# See RESULTS.md / reports/research-roadmap-2026-07-02.md Section 2 for the root cause:
# the old code defaulted var_sr to 1.0 (an annualized-equivalent noise-Sharpe unit) while
# sharpe_hat is per-bar, manufacturing |z| ~ sqrt(n_obs) garbage. The fix defaults var_sr to
# the moment-adjusted null per-bar SR-estimator variance
# (1 - skew*sharpe_hat + (kurt-1)/4*sharpe_hat**2) / n_obs.
# ---------------------------------------------------------------------------

def test_deflated_sharpe_corrected_units_regime_sma_maker_fingerprint():
    """Locks the exact corrected numbers from the roadmap's root-cause fingerprint: annualized
    OOS Sharpe 0.576, T=913 daily bars (365 bars/yr), N=2 trials, Gaussian moments (skew=0,
    kurt=3). Expected per-bar E[maxSR] ~= 0.5197553/sqrt(913) = 0.0172014 exactly (the
    fingerprint confirming the units-bug root cause), z ~= +0.391, DSR prob ~= 0.652."""
    annualized_sr = 0.576
    bars_per_year = 365
    n_obs = 913
    period_sharpe = annualized_sr / math.sqrt(bars_per_year)

    result = gate.deflated_sharpe_ratio(period_sharpe, n_trials=2, n_obs=n_obs, skew=0.0, kurt=3.0)

    expected_e_max_sr = 0.5197553 / math.sqrt(913)
    assert result["expected_max_sharpe_noise"] == pytest.approx(expected_e_max_sr, abs=1e-3)
    assert result["expected_max_sharpe_noise"] == pytest.approx(0.01720, abs=1e-3)
    assert result["z"] == pytest.approx(0.391, abs=1e-3)
    assert result["dsr"] == pytest.approx(0.652, abs=1e-3)


def test_deflated_sharpe_units_consistency_across_bar_frequency():
    """DSR of the SAME strategy (same annualized Sharpe, same calendar span) must be
    approximately invariant to bar granularity -- daily bars and 5-minute bars of the same
    2.5y OOS window should produce near-identical DSR, because the corrected per-bar noise
    threshold scales as sqrt(1/n_obs) and per-bar sharpe_hat scales as 1/sqrt(bars_per_year),
    so the two effects cancel (to leading order) at fixed calendar span. This is exactly the
    invariance the old var_sr=1.0 default violated: it made the fine-bar hurdle come out
    ~sqrt(bars_per_year) times harsher than the daily-bar hurdle for identical evidence."""
    annualized_sr = 0.576
    years = 913 / 365  # same 2.5y calendar span as the daily fingerprint case

    configs = {"1d": 365, "1h": 24 * 365, "5m": 12 * 24 * 365}
    thresholds = {}
    dsrs = {}
    for label, bars_per_year in configs.items():
        n_obs = round(bars_per_year * years)
        period_sharpe = annualized_sr / math.sqrt(bars_per_year)
        result = gate.deflated_sharpe_ratio(period_sharpe, n_trials=2, n_obs=n_obs, skew=0.0, kurt=3.0)
        thresholds[label] = result["expected_max_sharpe_noise"]
        dsrs[label] = result["dsr"]

    # The per-bar threshold itself scales with 1/sqrt(n_obs) -- assert the ratio between the
    # 1d and 5m thresholds matches the ratio of sqrt(1/n_obs) between those two frequencies.
    n_obs_1d = round(configs["1d"] * years)
    n_obs_5m = round(configs["5m"] * years)
    predicted_ratio = math.sqrt(n_obs_5m / n_obs_1d)
    actual_ratio = thresholds["1d"] / thresholds["5m"]
    assert actual_ratio == pytest.approx(predicted_ratio, rel=1e-3)

    # And the resulting DSR probability -- the thing the 0.95 gate bar is compared against --
    # should be approximately the same regardless of bar granularity for the same underlying
    # evidence (small deviations are fine; they come from the second-order skew/kurt terms).
    assert dsrs["1d"] == pytest.approx(dsrs["5m"], abs=0.01)
    assert dsrs["1d"] == pytest.approx(dsrs["1h"], abs=0.01)


def test_deflated_sharpe_n_trials_1_reduces_to_plain_psr():
    """N=1 trial means no multiple-testing haircut: E[maxSR] must be exactly 0, so the DSR
    collapses to the plain (non-deflated) probabilistic Sharpe ratio test."""
    result = gate.deflated_sharpe_ratio(sharpe_hat=0.03, n_trials=1, n_obs=913, skew=0.0, kurt=3.0)
    assert result["expected_max_sharpe_noise"] == 0.0

    # With e_max_sr=0, z reduces to sharpe_hat * sqrt(n_obs-1) / denom -- the plain PSR z-stat.
    denom = math.sqrt(1 - 0.0 * 0.03 + (3.0 - 1) / 4 * 0.03 ** 2)
    expected_z = 0.03 * math.sqrt(913 - 1) / denom
    assert result["z"] == pytest.approx(expected_z, rel=1e-9)


def test_deflated_sharpe_var_sr_override_still_respected():
    """The explicit sharpe_var_trials override parameter must still take priority over the
    moment-adjusted default -- callers that legitimately have an empirical cross-trial
    variance estimate must be able to supply it directly."""
    default_result = gate.deflated_sharpe_ratio(sharpe_hat=0.03, n_trials=2, n_obs=913)
    override_result = gate.deflated_sharpe_ratio(sharpe_hat=0.03, n_trials=2, n_obs=913,
                                                  sharpe_var_trials=0.5)
    assert override_result["expected_max_sharpe_noise"] != pytest.approx(
        default_result["expected_max_sharpe_noise"])
    assert override_result["expected_max_sharpe_noise"] == pytest.approx(
        math.sqrt(0.5) * 0.5197553, rel=1e-3)


def test_return_moments_matches_gaussian_defaults_for_normal_series():
    rng = np.random.default_rng(7)
    net = pd.Series(rng.normal(0.0005, 0.01, 5000))
    skew, kurt = gate._return_moments(net)
    assert skew == pytest.approx(0.0, abs=0.15)
    assert kurt == pytest.approx(3.0, abs=0.3)


def test_return_moments_falls_back_to_gaussian_on_degenerate_series():
    flat = pd.Series([0.0] * 10)
    skew, kurt = gate._return_moments(flat)
    assert (skew, kurt) == (0.0, 3.0)
