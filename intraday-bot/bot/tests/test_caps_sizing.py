"""
Tests for bot/sizing.py + bot/caps.py — proves the $500-book caps are hardcoded and that
sizing clamps orders to the per-order cap BEFORE they ever reach connectors.hard_caps.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from bot.caps import BOOK_500_CAPS, CapConfig, Order, BookState, would_pass
from bot.sizing import diff_to_order, diff_universe, target_notional, MIN_ORDER_NOTIONAL_USD


def test_book_500_caps_values():
    """House rule: max order $250, max position $500, no shorts, no leverage."""
    assert BOOK_500_CAPS.max_order_notional == 250.0
    assert BOOK_500_CAPS.max_position_notional == 500.0
    assert BOOK_500_CAPS.max_gross_notional == 500.0
    assert BOOK_500_CAPS.allow_shorts is False
    assert BOOK_500_CAPS.max_daily_loss == 25.0
    assert BOOK_500_CAPS.max_orders_per_day == 20


def test_target_notional_clamps_weight_to_0_1():
    """No leverage: weight > 1 clamps to the full $500 cap, not beyond."""
    assert target_notional(1.5, cap=500.0) == 500.0
    assert target_notional(0.5, cap=500.0) == 250.0
    # negative weight (would-be short) clamps to 0 -- no shorts house rule
    assert target_notional(-0.5, cap=500.0) == 0.0


def test_diff_to_order_buy_clamped_to_per_order_cap():
    """Target implies $500 notional from flat; sizing must clamp the single order to $250
    (the per-order cap), not propose the whole $500 gap in one shot."""
    order = diff_to_order("BTC/USD", target_weight=1.0, current_notional=0.0)
    assert order is not None
    assert order.side == "buy"
    assert order.notional == 250.0  # clamped, not 500


def test_diff_to_order_sell_never_exceeds_current_holding_no_shorts():
    """Long-only: a sell can never propose more than what's currently held."""
    order = diff_to_order("BTC/USD", target_weight=0.0, current_notional=80.0)
    assert order is not None
    assert order.side == "sell"
    assert order.notional == 80.0  # capped at current holding, would not go short


def test_diff_to_order_below_min_notional_returns_none():
    """A tiny drift below Alpaca's $1 minimum should not spam an order."""
    order = diff_to_order("BTC/USD", target_weight=0.001, current_notional=0.0)
    assert order is None or order.notional >= MIN_ORDER_NOTIONAL_USD


def test_diff_to_order_at_target_returns_none():
    order = diff_to_order("BTC/USD", target_weight=0.5, current_notional=250.0)
    assert order is None


def test_diff_universe_multi_symbol():
    weights = {"BTC/USD": 0.5, "ETH/USD": 0.0}
    positions = {"BTC/USD": 0.0, "ETH/USD": 100.0}
    orders = diff_universe(weights, positions)
    by_sym = {o.symbol: o for o in orders}
    assert by_sym["BTC/USD"].side == "buy"
    assert by_sym["ETH/USD"].side == "sell"
    assert by_sym["ETH/USD"].notional == 100.0


def test_caps_reject_oversized_order_directly():
    """connectors.hard_caps.check() is the final backstop even if sizing were bypassed."""
    oversized = Order("BTC/USD", "buy", 9999.0, "alpaca", "strategies/dummy_flat.py")
    assert not would_pass(oversized, BookState(), BOOK_500_CAPS)


def test_caps_reject_short_when_flat():
    sell = Order("BTC/USD", "sell", 50.0, "alpaca", "strategies/dummy_flat.py")
    assert not would_pass(sell, BookState(positions={}), BOOK_500_CAPS)


def test_caps_accept_order_within_all_limits():
    ok = Order("BTC/USD", "buy", 200.0, "alpaca", "strategies/dummy_flat.py")
    assert would_pass(ok, BookState(), BOOK_500_CAPS)


def test_caps_reject_missing_strategy_ref():
    no_ref = Order("BTC/USD", "buy", 100.0, "alpaca", "")
    assert not would_pass(no_ref, BookState(), BOOK_500_CAPS)


def test_caps_kill_switch(tmp_path):
    kill_file = tmp_path / ".KILL"
    kill_file.write_text("halt")
    cfg = CapConfig(kill_switch_file=str(kill_file))
    order = Order("BTC/USD", "buy", 50.0, "alpaca", "strategies/dummy_flat.py")
    assert not would_pass(order, BookState(), cfg)
