"""
Deterministic hard caps + kill switch — the risk layer that lives OUTSIDE the LLM.

GOAL invariant #3: "Hard caps + kill switch in deterministic code, outside the LLM."
The agent PROPOSES orders; this module DISPOSES. No prompt can override these checks — they are
plain Python, evaluated before any order (paper or live) is allowed through the executor.

Educational analysis, not financial advice.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import os


@dataclass(frozen=True)
class CapConfig:
    max_order_notional: float = 5_000.0      # per-order $ cap
    max_position_notional: float = 25_000.0  # per-symbol $ cap (post-trade)
    max_gross_notional: float = 100_000.0    # whole-book gross $ cap (post-trade)
    max_daily_loss: float = 2_000.0          # realized+unrealized daily loss kill threshold ($)
    max_orders_per_day: int = 20             # fee/PDT budget
    allow_shorts: bool = False               # long-only by default (no borrow/locate)
    kill_switch_file: str = ".KILL"          # if this file exists, ALL orders are blocked


@dataclass
class BookState:
    """Minimal book snapshot the caps reason about. Supplied by the caller, not the LLM."""
    positions: dict = field(default_factory=dict)  # symbol -> signed notional held
    realized_pnl_today: float = 0.0
    unrealized_pnl_today: float = 0.0
    orders_today: int = 0


@dataclass(frozen=True)
class Order:
    symbol: str
    side: str          # "buy" | "sell"
    notional: float    # absolute $ amount
    venue: str         # "robinhood" | "coinbase-cdp"
    strategy_ref: str  # MUST reference a backtest that PASSed the gate (invariant #1)


class CapViolation(Exception):
    pass


def check(order: Order, book: BookState, cfg: CapConfig) -> None:
    """Raise CapViolation if the order breaks any hard cap. Silent return = approved.
    This is the deterministic gate; it never consults the model."""
    # 0. kill switch — a file on disk halts everything (ops can `touch .KILL`)
    if os.path.exists(cfg.kill_switch_file):
        raise CapViolation(f"KILL SWITCH active ({cfg.kill_switch_file} present) — all orders blocked")

    # 1. backtest-before-trade linkage (invariant #1): an order with no PASSed-strategy ref is rejected
    if not order.strategy_ref or not str(order.strategy_ref).strip():
        raise CapViolation("order has no strategy_ref — backtest-before-trade not satisfied")

    if order.notional <= 0:
        raise CapViolation("order notional must be positive")
    if order.side not in ("buy", "sell"):
        raise CapViolation(f"bad side {order.side!r}")

    # 2. daily loss kill
    daily = book.realized_pnl_today + book.unrealized_pnl_today
    if daily <= -abs(cfg.max_daily_loss):
        raise CapViolation(f"daily loss {daily:.0f} <= -{cfg.max_daily_loss:.0f} — kill switch")

    # 3. order-count budget
    if book.orders_today >= cfg.max_orders_per_day:
        raise CapViolation(f"order budget exhausted ({book.orders_today}/{cfg.max_orders_per_day})")

    # 4. per-order notional
    if order.notional > cfg.max_order_notional:
        raise CapViolation(f"order ${order.notional:.0f} > per-order cap ${cfg.max_order_notional:.0f}")

    # 5. post-trade per-position notional
    cur = book.positions.get(order.symbol, 0.0)
    delta = order.notional if order.side == "buy" else -order.notional
    new_pos = cur + delta
    if not cfg.allow_shorts and new_pos < -1e-6:
        raise CapViolation(f"shorting disabled — {order.symbol} would go to {new_pos:.0f}")
    if abs(new_pos) > cfg.max_position_notional:
        raise CapViolation(
            f"{order.symbol} post-trade ${abs(new_pos):.0f} > position cap ${cfg.max_position_notional:.0f}")

    # 6. post-trade gross
    gross = sum(abs(v) for k, v in book.positions.items() if k != order.symbol) + abs(new_pos)
    if gross > cfg.max_gross_notional:
        raise CapViolation(f"book gross ${gross:.0f} > gross cap ${cfg.max_gross_notional:.0f}")


def would_pass(order: Order, book: BookState, cfg: CapConfig) -> bool:
    try:
        check(order, book, cfg)
        return True
    except CapViolation:
        return False
