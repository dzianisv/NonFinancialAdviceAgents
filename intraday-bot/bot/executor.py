"""
Order execution — post-only limit orders (maker), same offset/timeout logic as the backtest
maker-fill model (core/fills.py: trade-through fills, timeout escalates to market/taker).

Mode routing:
  notify (DEFAULT): connectors.notify_executor.execute(mode="notify") — caps-checked,
                     audit-logged, proposes a human-approvable ticket. NEVER touches a broker.
  paper           : same caps + audit path, then places a REAL post-only limit order on the
                     Alpaca PAPER account (alpaca-py TradingClient(paper=True)), keys from
                     env ALPACA_PAPER_KEY/ALPACA_PAPER_SECRET. No real funds.
  live            : deliberate stub — refuses unless CONFIRM_LIVE=<today> env AND live keys
                     present (mirrors connectors/notify_executor.py's `_live_gate_blocks`
                     pattern exactly; reuses that gate, does not reimplement it).

The maker offset/timeout mechanics mirror core/fills.py: rest a post-only limit
`maker_offset_bps` inside the current touch (buy below best ask / sell above best bid,
biased toward the resting side), and if unfilled after `fill_timeout_seconds`, either
cancel+re-quote next cycle (allow_timeout_escalation=False) or cancel+replace at market
(True) — a forced timeout exit/entry ALWAYS pays taker, exactly like core/fills.py rule 4.
"""
from __future__ import annotations

import datetime as _dt
import os
import sys
from dataclasses import dataclass
from typing import Optional

_CONNECTORS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "connectors"
)
if _CONNECTORS_DIR not in sys.path:
    sys.path.insert(0, _CONNECTORS_DIR)

from hard_caps import Order as CapOrder, BookState, CapConfig  # noqa: E402
from notify_executor import execute as notify_execute, _live_gate_blocks  # noqa: E402

from bot.state_store import StateStore, client_order_id  # noqa: E402
from bot.sizing import ProposedOrder  # noqa: E402

PAPER_KEY_ENV = "ALPACA_PAPER_KEY"
PAPER_SECRET_ENV = "ALPACA_PAPER_SECRET"
LIVE_KEY_ENV = "ALPACA_LIVE_KEY"
LIVE_SECRET_ENV = "ALPACA_LIVE_SECRET"

STRATEGY_REF_PREFIX = "intraday-bot/strategies"


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _today_utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")


@dataclass
class ExecutionResult:
    client_order_id: str
    result: str            # PROPOSED | REJECTED | SUBMITTED | FILLED | LIVE_BLOCKED | LIVE_NOT_WIRED | ERROR
    detail: dict


def _maker_limit_price(side: str, last_price: float, offset_bps: float) -> float:
    """Rest INSIDE the touch — buy below last, sell above last — mirroring the backtest's
    maker orientation (we provide liquidity, never cross the spread)."""
    offset = last_price * (offset_bps / 10_000.0)
    return round(last_price - offset, 8) if side == "buy" else round(last_price + offset, 8)


def _to_cap_order(po: ProposedOrder, strategy_key: str) -> CapOrder:
    return CapOrder(
        symbol=po.symbol,
        side=po.side,
        notional=po.notional,
        venue="alpaca",
        strategy_ref=f"{STRATEGY_REF_PREFIX}/{strategy_key}.py",
    )


def _book_state_from_store(store: StateStore, cfg: CapConfig) -> BookState:
    today = _today_utc()
    return BookState(
        positions=store.reconstruct_positions(),
        realized_pnl_today=store.realized_pnl_today(today),
        unrealized_pnl_today=0.0,  # runner does not mark-to-market intraday; conservative (no credit)
        orders_today=store.orders_today(today),
    )


def _place_alpaca_paper_order(po: ProposedOrder, last_price: float, offset_bps: float,
                               client_id: str):
    """Real post-only limit order on the Alpaca PAPER account. Requires
    ALPACA_PAPER_KEY/ALPACA_PAPER_SECRET env vars (Bitwarden 'dev' collection convention —
    see deploy/README-DEPLOY.md)."""
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import LimitOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce

    key = os.environ.get(PAPER_KEY_ENV)
    secret = os.environ.get(PAPER_SECRET_ENV)
    if not key or not secret:
        raise RuntimeError(f"paper mode requires {PAPER_KEY_ENV}/{PAPER_SECRET_ENV} env vars")

    client = TradingClient(key, secret, paper=True)
    limit_price = _maker_limit_price(po.side, last_price, offset_bps)
    req = LimitOrderRequest(
        symbol=po.symbol.replace("/", ""),
        notional=po.notional,
        side=OrderSide.BUY if po.side == "buy" else OrderSide.SELL,
        time_in_force=TimeInForce.GTC,
        limit_price=limit_price,
        client_order_id=client_id,
    )
    return client.submit_order(req)


def execute_order(po: ProposedOrder, store: StateStore, cap_cfg: CapConfig, mode: str,
                   strategy_key: str, cycle_ts: str, last_price: Optional[float] = None,
                   maker_offset_bps: float = 5.0) -> ExecutionResult:
    """Route one proposed order through caps -> mode-specific placement. Idempotent: if
    this exact client_order_id was already logged, skip re-submission (restart safety)."""
    client_id = client_order_id(cycle_ts, po.symbol, po.side)
    if client_id in store.seen_client_order_ids():
        return ExecutionResult(client_id, "SKIPPED_DUPLICATE",
                                {"note": f"client_order_id {client_id} already logged this cycle"})

    cap_order = _to_cap_order(po, strategy_key)
    book = _book_state_from_store(store, cap_cfg)

    # notify mode: reuse connectors.notify_executor verbatim — caps check + audit log +
    # human-approvable ticket, NEVER contacts a broker.
    if mode == "notify":
        rec = notify_execute(cap_order, book, cap_cfg, mode="notify", now=_now_iso())
        rec["client_order_id"] = client_id
        store.log_order_event(rec)
        return ExecutionResult(client_id, rec["result"], rec)

    if mode == "paper":
        # caps check first (same deterministic gate as notify), THEN place on paper venue
        rec = notify_execute(cap_order, book, cap_cfg, mode="paper", now=_now_iso())
        rec["client_order_id"] = client_id
        if rec["result"] != "PROPOSED":
            store.log_order_event(rec)
            return ExecutionResult(client_id, rec["result"], rec)
        if last_price is None:
            rec2 = {**rec, "result": "ERROR", "reason": "no last_price available to place paper order"}
            store.log_order_event(rec2)
            return ExecutionResult(client_id, "ERROR", rec2)
        try:
            submitted = _place_alpaca_paper_order(po, last_price, maker_offset_bps, client_id)
            rec2 = {**rec, "result": "SUBMITTED", "alpaca_order_id": str(getattr(submitted, "id", ""))}
            store.log_order_event(rec2)
            return ExecutionResult(client_id, "SUBMITTED", rec2)
        except Exception as e:  # noqa: BLE001
            rec2 = {**rec, "result": "ERROR", "reason": str(e)}
            store.log_order_event(rec2)
            return ExecutionResult(client_id, "ERROR", rec2)

    if mode == "live":
        # same hard gate as connectors/notify_executor.py — reused, not reimplemented.
        today = _today_utc()
        blocks = _live_gate_blocks(cap_order, today)
        if blocks:
            rec = {"ts": _now_iso(), "mode": "live", "order": po.__dict__,
                   "result": "LIVE_BLOCKED", "reason": "; ".join(blocks), "client_order_id": client_id}
            store.log_order_event(rec)
            return ExecutionResult(client_id, "LIVE_BLOCKED", rec)
        rec = notify_execute(cap_order, book, cap_cfg, mode="live", now=_now_iso())
        rec["client_order_id"] = client_id
        store.log_order_event(rec)
        return ExecutionResult(client_id, rec["result"], rec)

    raise ValueError(f"unknown mode {mode!r}")
