"""
Target-position -> proposed-order sizing.

Strategy output is a weight in [-1, 1] (fraction of the PER-SYMBOL cap notional, not book
NAV — this is a $500 book with a hardcoded $500 max_position_notional, so 'weight' here
means fraction of that fixed $500 ceiling, matching how core/gate.py backtests treat
weight as a target exposure fraction). This module diffs target notional vs current held
notional and proposes a single order to close the gap, pre-clamped to the $250 per-order
cap so the SAME order that would violate caps is visibly shrunk here (caps.check() is the
final deterministic backstop, not the only line of defense).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from bot.caps import BOOK_500_CAPS

MIN_ORDER_NOTIONAL_USD = 1.0  # Alpaca crypto minimum notional (verified docs.alpaca.markets)


@dataclass
class ProposedOrder:
    symbol: str
    side: str            # "buy" | "sell"
    notional: float       # absolute $ amount, already clamped to per-order cap
    target_weight: float
    current_notional: float
    target_notional: float


def target_notional(weight: float, cap: float = BOOK_500_CAPS.max_position_notional) -> float:
    """weight in [-1, 1] (long-only house rule clamps negative to 0) -> $ notional against
    the fixed per-symbol cap."""
    w = max(0.0, min(1.0, float(weight)))  # no shorts, no leverage (house rule)
    return w * cap


def diff_to_order(symbol: str, target_weight: float, current_notional: float,
                   cap_cfg=BOOK_500_CAPS) -> Optional[ProposedOrder]:
    """Compute the single order needed to move current_notional toward the target implied
    by target_weight, clamped to the per-order notional cap. Returns None if the gap is
    below the exchange minimum (nothing worth proposing) or already at target."""
    tgt = target_notional(target_weight, cap_cfg.max_position_notional)
    gap = tgt - current_notional

    if abs(gap) < MIN_ORDER_NOTIONAL_USD:
        return None

    side = "buy" if gap > 0 else "sell"
    notional = min(abs(gap), cap_cfg.max_order_notional)

    if not cap_cfg.allow_shorts and side == "sell":
        # never sell past flat (no shorts) — clamp sell size to current holding
        notional = min(notional, max(0.0, current_notional))
        if notional < MIN_ORDER_NOTIONAL_USD:
            return None

    return ProposedOrder(
        symbol=symbol, side=side, notional=round(notional, 2),
        target_weight=target_weight, current_notional=current_notional, target_notional=tgt,
    )


def diff_universe(target_weights: dict, current_positions: dict,
                   cap_cfg=BOOK_500_CAPS) -> list:
    """target_weights: {symbol: weight}. current_positions: {symbol: notional held}.
    Returns a list of ProposedOrder, skipping symbols already at target."""
    orders = []
    for sym, w in target_weights.items():
        cur = current_positions.get(sym, 0.0)
        order = diff_to_order(sym, w, cur, cap_cfg)
        if order is not None:
            orders.append(order)
    return orders
