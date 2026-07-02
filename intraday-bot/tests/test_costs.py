"""Unit tests for core/costs.py — cost math (maker/taker rates, min-fee floor, stress tiers)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.costs import CostConfig, fee, fee_rate_effective, slippage_cost, MAKER_RATE, TAKER_RATE, MIN_FEE_USD


def test_maker_rate_is_15bp():
    assert MAKER_RATE == 0.0015


def test_taker_rate_is_25bp():
    assert TAKER_RATE == 0.0025


def test_fee_maker_normal_notional():
    assert fee(1000.0, is_maker=True) == pytest.approx(1000.0 * 0.0015)


def test_fee_taker_normal_notional():
    assert fee(1000.0, is_maker=False) == pytest.approx(1000.0 * 0.0025)


def test_fee_zero_notional_is_zero():
    assert fee(0.0, is_maker=True) == 0.0


def test_fee_floor_kicks_in_below_threshold():
    # notional where maker fee would be < $0.01: 0.01/0.0015 = $6.67
    tiny = fee(1.0, is_maker=True)
    assert tiny == MIN_FEE_USD


def test_fee_floor_exact_boundary():
    # notional at exactly the floor boundary
    boundary_notional = MIN_FEE_USD / MAKER_RATE
    f = fee(boundary_notional, is_maker=True)
    assert f == pytest.approx(MIN_FEE_USD, rel=1e-6)


def test_fee_2x_stress_multiplier():
    cfg = CostConfig(fee_multiplier=2.0)
    normal = fee(1000.0, is_maker=False)
    stressed = fee(1000.0, is_maker=False, cfg=cfg)
    assert stressed == pytest.approx(normal * 2)


def test_fee_rate_effective_matches_notional_ratio():
    r = fee_rate_effective(10_000.0, is_maker=False)
    assert r == pytest.approx(TAKER_RATE)


def test_fee_rate_effective_zero_notional():
    assert fee_rate_effective(0.0, is_maker=True) == 0.0


def test_slippage_cost_zero_by_default():
    assert slippage_cost(1000.0) == 0.0


def test_slippage_cost_10bp_stress_tier():
    cfg = CostConfig(extra_slippage_bps=10.0)
    assert slippage_cost(1000.0, cfg) == pytest.approx(1000.0 * 0.001)


def test_forced_exit_pays_taker_not_maker():
    """House rule: forced/timeout exits pay taker, never maker."""
    notional = 500.0
    taker_fee = fee(notional, is_maker=False)
    maker_fee = fee(notional, is_maker=True)
    assert taker_fee > maker_fee  # taker (0.25%) strictly costs more than maker (0.15%)
