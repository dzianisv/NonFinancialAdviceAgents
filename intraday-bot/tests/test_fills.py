"""Unit tests for core/fills.py — the maker-fill simulator. Deterministic, no RNG."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import fills
from core.costs import CostConfig, MAKER_RATE, TAKER_RATE, MIN_FEE_USD


def make_bar(open_, high, low, close):
    return pd.DataFrame([{"open": open_, "high": high, "low": low, "close": close}])


# ---------- Rule 1: trade-through, not touch ----------

def test_buy_limit_touch_only_does_not_fill():
    """low == limit exactly (touch, no trade-through) must NOT fill."""
    df = make_bar(100, 105, 100.0, 102)
    res = fills.try_limit_fill(df, 0, "buy", limit_price=100.0)
    assert res.filled is False


def test_buy_limit_trade_through_1bp_fills():
    """low trades through limit by >= 1bp -> fills."""
    limit = 100.0
    df = make_bar(101, 105, limit * (1 - 0.0001) - 1e-9, 102)  # just past 1bp through
    res = fills.try_limit_fill(df, 0, "buy", limit_price=limit)
    assert res.filled is True
    assert res.is_maker is True
    assert res.fill_price == limit


def test_buy_limit_trade_through_less_than_1bp_does_not_fill():
    """low dips below limit but NOT by the full 1bp -> no fill (touch-adjacent, not enough)."""
    limit = 100.0
    df = make_bar(101, 105, 99.999, 102)  # only 0.001% through, < 1bp
    res = fills.try_limit_fill(df, 0, "buy", limit_price=limit)
    assert res.filled is False


def test_sell_limit_mirrors_buy():
    limit = 100.0
    df_fill = make_bar(99, limit * (1 + 0.0001) + 1e-9, 95, 98)
    res = fills.try_limit_fill(df_fill, 0, "sell", limit_price=limit)
    assert res.filled is True

    df_touch = make_bar(99, limit, 95, 98)  # exact touch only
    res2 = fills.try_limit_fill(df_touch, 0, "sell", limit_price=limit)
    assert res2.filled is False


# ---------- Rule 2: queue-position haircut / stress fill-prob tier ----------

def test_stress_fill_prob_requires_deeper_trade_through():
    """Under stress_fill_prob=True, a bar that clears the base 1bp threshold but not the
    0.25*range threshold must NOT fill, while base tier fills it."""
    limit = 100.0
    # range = high-low = 10; 0.25*range = 2.5 -> need low <= 97.5 to fill under stress
    df = make_bar(100, 105, 99.5, 102)  # trades through base 1bp (low<limit) but not stress depth
    base = fills.try_limit_fill(df, 0, "buy", limit_price=limit)
    stress = fills.try_limit_fill(df, 0, "buy", limit_price=limit, stress_fill_prob=True)
    assert base.filled is True
    assert stress.filled is False


def test_stress_fill_prob_fills_when_deep_enough():
    limit = 100.0
    df = make_bar(100, 105, 97.0, 102)  # low=97 <= 100-2.5=97.5 -> fills even under stress
    stress = fills.try_limit_fill(df, 0, "buy", limit_price=limit, stress_fill_prob=True)
    assert stress.filled is True


def test_stress_fill_prob_is_deterministic_reproducible():
    """Same inputs -> same output, run twice, no RNG involved."""
    limit = 100.0
    df = make_bar(100, 105, 97.0, 102)
    r1 = fills.try_limit_fill(df, 0, "buy", limit_price=limit, stress_fill_prob=True)
    r2 = fills.try_limit_fill(df, 0, "buy", limit_price=limit, stress_fill_prob=True)
    assert r1.filled == r2.filled
    assert r1.fill_price == r2.fill_price


# ---------- Rule 4: no-fill fallback (entry skip, exit timeout->market) ----------

def test_entry_never_fills_is_skipped_not_carried_forward():
    limit = 100.0
    df = make_bar(101, 103, 100.5, 102)  # never trades through
    res = fills.simulate_entry(df, 0, "buy", limit_price=limit)
    assert res.filled is False
    assert res.skipped_entry is True


def test_exit_timeout_forces_market_taker():
    limit = 100.0
    # 3 bars, none trade through a sell limit far above the range
    df = pd.DataFrame([
        {"open": 90, "high": 91, "low": 89, "close": 90},
        {"open": 90, "high": 91, "low": 89, "close": 90.5},
        {"open": 90, "high": 91, "low": 89, "close": 91},
    ])
    res = fills.simulate_exit_with_timeout(df, 0, "sell", limit_price=limit, timeout_bars=3)
    assert res.filled is True
    assert res.timeout_exit is True
    assert res.is_maker is False  # forced market = taker
    assert res.fill_price == 91  # close of last bar in window


def test_exit_fills_maker_before_timeout_when_it_trades_through():
    limit = 100.0
    df = pd.DataFrame([
        {"open": 90, "high": 91, "low": 89, "close": 90},
        {"open": 99, "high": limit * 1.0002, "low": 98, "close": 100.5},  # trades through
        {"open": 90, "high": 91, "low": 89, "close": 91},
    ])
    res = fills.simulate_exit_with_timeout(df, 0, "sell", limit_price=limit, timeout_bars=3)
    assert res.filled is True
    assert res.timeout_exit is False
    assert res.is_maker is True
    assert res.bar_index == 1


def test_forced_exit_always_pays_taker_rate():
    df = pd.DataFrame([{"open": 90, "high": 91, "low": 89, "close": 90}])
    res = fills.market_fill(df, 0, "sell", notional=1000.0)
    expected_fee = max(1000.0 * TAKER_RATE, MIN_FEE_USD)
    assert res.fee_usd == pytest.approx(expected_fee)
    assert res.is_maker is False


# ---------- Rule 3: adverse selection ----------

def test_adverse_drift_buy_positive_when_price_drops_next_bar():
    df = pd.DataFrame([
        {"open": 100, "high": 101, "low": 99, "close": 100},
        {"open": 100, "high": 100, "low": 95, "close": 96},  # drops 4%
    ])
    adv = fills.adverse_drift(df, fill_pos=0, side="buy")
    assert adv == pytest.approx(0.04)  # positive = adverse cost


def test_adverse_drift_sell_positive_when_price_rises_next_bar():
    df = pd.DataFrame([
        {"open": 100, "high": 101, "low": 99, "close": 100},
        {"open": 100, "high": 105, "low": 100, "close": 104},  # rises 4%
    ])
    adv = fills.adverse_drift(df, fill_pos=0, side="sell")
    assert adv == pytest.approx(0.04)


def test_adverse_drift_none_at_end_of_data():
    df = pd.DataFrame([{"open": 100, "high": 101, "low": 99, "close": 100}])
    assert fills.adverse_drift(df, fill_pos=0, side="buy") is None


# ---------- Fee floor (rule 6) ----------

def test_min_fee_floor_applies_on_tiny_notional():
    from core.costs import fee
    tiny_fee = fee(0.01, is_maker=True)
    assert tiny_fee == MIN_FEE_USD


def test_fee_no_floor_on_large_notional():
    from core.costs import fee
    notional = 10_000.0
    f = fee(notional, is_maker=False)
    assert f == pytest.approx(notional * TAKER_RATE)
    assert f > MIN_FEE_USD


# ---------- Stress tier (b): delayed fills ----------

def test_delay_bars_shifts_evaluation_to_later_bar():
    limit = 100.0
    df = pd.DataFrame([
        {"open": 101, "high": 103, "low": 100.5, "close": 102},  # bar 0: no trade-through
        {"open": 100, "high": 101, "low": 99.0, "close": 100},   # bar 1: trades through
    ])
    no_delay = fills.try_limit_fill(df, 0, "buy", limit_price=limit)
    delayed = fills.try_limit_fill(df, 0, "buy", limit_price=limit, delay_bars=1)
    assert no_delay.filled is False
    assert delayed.filled is True
    assert delayed.bar_index == 1


# ---------- Stress tier (d): worst-vol slippage ----------

def test_extra_slippage_applied_on_high_vol_bar():
    limit = 100.0
    df = make_bar(101, 105, 90.0, 102)  # wide range -> triggers vol threshold
    res = fills.try_limit_fill(
        df, 0, "buy", limit_price=limit, notional=1000.0,
        extra_slip_worst_vol=True, vol_p95_threshold=0.01,  # low threshold, this bar qualifies
    )
    assert res.filled is True
    assert res.slippage_usd > 0


def test_no_extra_slippage_below_vol_threshold():
    limit = 100.0
    df = make_bar(101, 102, 99.9, 100.5)  # tight range
    res = fills.try_limit_fill(
        df, 0, "buy", limit_price=limit, notional=1000.0,
        extra_slip_worst_vol=True, vol_p95_threshold=0.5,  # high bar, this bar won't qualify
    )
    assert res.slippage_usd == 0.0


# ---------- Integration: stress tier (c) monotonically reduces fill rate vs base ----------

def test_stress_fill_prob_is_subset_of_base_fills_over_many_bars():
    """Over a realistic bar sequence, the stress (harder trade-through) tier's fill count
    must never exceed the base tier's fill count — every stress fill is also a base fill."""
    rng = np.random.default_rng(7)
    n = 300
    price = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    df = pd.DataFrame({
        "open": price,
        "high": price * (1 + np.abs(rng.normal(0, 0.005, n))),
        "low": price * (1 - np.abs(rng.normal(0, 0.005, n))),
        "close": price,
    })
    base_fills = stress_fills = 0
    for i in range(n):
        limit = df["close"].iloc[i] * 0.999
        r_base = fills.try_limit_fill(df, i, "buy", limit)
        r_stress = fills.try_limit_fill(df, i, "buy", limit, stress_fill_prob=True)
        base_fills += int(r_base.filled)
        stress_fills += int(r_stress.filled)
        if r_stress.filled:
            assert r_base.filled, "a stress-tier fill occurred without a base-tier fill (not a subset)"
    assert stress_fills <= base_fills
    assert stress_fills < base_fills  # must be strictly harder on a realistic (non-degenerate) sequence
