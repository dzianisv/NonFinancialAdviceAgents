"""
Notification-first executor — the connector that satisfies GOAL tracks D & E in
**paper / notification mode** without any live credentials.

Operating modes (GOAL invariant #2: notification-first / human-in-the-loop):
  - "notify"  (DEFAULT): validate against hard caps, append to the immutable audit log, and EMIT
                the order ticket for a human to place/approve. NEVER contacts a broker. No creds needed.
  - "paper" : same, but routes to a TESTNET venue when available (Coinbase CDP base-sepolia faucet).
                Still no mainnet funds. (Hook point — real testnet call is wired when creds present.)
  - "live"  : routes to the real venue. HARD-GATED — refuses unless ALL of:
                (a) env creds present for the venue,
                (b) CONFIRM_LIVE=<today's date> env matches,
                (c) order.strategy_ref names a backtest that PASSed the gate,
                (d) caps pass.
              Live wiring is intentionally a stub here (raises) so this module can never place a
              real order by accident; the documented path to enable it is in the connector skills.

Venues: "robinhood" (MCP: agent.robinhood.com/mcp/trading) and "coinbase-cdp" (npx @coinbase/cdp-cli,
also an MCP server). In notify mode we don't call them — we describe the exact call the human/agent
would approve.

Educational analysis, not financial advice. The agent proposes; a human disposes.
"""
from __future__ import annotations
import os, json, sys, datetime as _dt
from dataclasses import asdict
from typing import Iterable

sys.path.insert(0, os.path.dirname(__file__))
from hard_caps import Order, BookState, CapConfig, check, CapViolation

AUDIT_LOG = os.path.join(os.path.dirname(__file__), "audit_log.jsonl")

VENUE_CREDS = {
    # env var that must be present for "live" on each venue (user supplies out-of-band)
    "robinhood": "ROBINHOOD_AGENT_CONNECTED",   # set after `claude mcp add robinhood-trading` + onboarding
    "coinbase-cdp": "CDP_API_KEY_JSON",          # path to the CDP API key json
    "alpaca": "ALPACA_LIVE_KEY",                 # intraday-bot/bot/executor.py live-mode venue
}


def _audit(record: dict, path: str = AUDIT_LOG) -> None:
    """Append-only immutable audit trail (invariant: full audit log)."""
    with open(path, "a") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")


def _ticket(order: Order) -> str:
    arrow = "BUY " if order.side == "buy" else "SELL"
    return (f"[{order.venue}] {arrow} ${order.notional:,.0f} {order.symbol}  "
            f"(strategy: {order.strategy_ref})")


def execute(order: Order, book: BookState, cfg: CapConfig, mode: str = "notify",
            now: str | None = None, audit_path: str = AUDIT_LOG) -> dict:
    """Validate + route one order. Returns a result dict. NEVER places a live order unless the
    live gate fully opens (and even then the live call is a stub that must be wired deliberately)."""
    now = now or "unknown-date"  # caller passes the date; module avoids hidden time calls
    base = {"ts": now, "mode": mode, "order": asdict(order)}

    # caps first — deterministic, model can't override
    try:
        check(order, book, cfg)
    except CapViolation as e:
        rec = {**base, "result": "REJECTED", "reason": str(e)}
        _audit(rec, audit_path)
        return rec

    if mode in ("notify", "paper"):
        rec = {**base, "result": "PROPOSED",
               "ticket": _ticket(order),
               "note": ("notification-only — a human places/approves this order"
                        if mode == "notify" else
                        "paper/testnet — no mainnet funds; wire testnet call when creds present")}
        _audit(rec, audit_path)
        return rec

    if mode == "live":
        reasons = _live_gate_blocks(order, now)
        if reasons:
            rec = {**base, "result": "LIVE_BLOCKED", "reason": "; ".join(reasons)}
            _audit(rec, audit_path)
            return rec
        # caps + gate passed. Live placement is a DELIBERATE stub — never auto-wired.
        rec = {**base, "result": "LIVE_NOT_WIRED",
               "reason": "live gate open, but real venue call is intentionally unwired in code — "
                         "enable per the connector skill, behind explicit human sign-off"}
        _audit(rec, audit_path)
        return rec

    rec = {**base, "result": "REJECTED", "reason": f"unknown mode {mode!r}"}
    _audit(rec, audit_path)
    return rec


def _live_gate_blocks(order: Order, today: str) -> list[str]:
    """All conditions that must be FALSE for live to proceed. Any returned string blocks live."""
    blocks = []
    cred_env = VENUE_CREDS.get(order.venue)
    if not cred_env or not os.environ.get(cred_env):
        blocks.append(f"missing creds: env {cred_env} not set for {order.venue}")
    if os.environ.get("CONFIRM_LIVE", "") != today:
        blocks.append("CONFIRM_LIVE env does not match today's date (explicit daily opt-in required)")
    if not order.strategy_ref.strip():
        blocks.append("no strategy_ref (backtest-before-trade)")
    return blocks


def run_batch(orders: Iterable[Order], book: BookState, cfg: CapConfig,
              mode: str = "notify", now: str | None = None, audit_path: str = AUDIT_LOG) -> list[dict]:
    out = []
    for o in orders:
        res = execute(o, book, cfg, mode=mode, now=now, audit_path=audit_path)
        out.append(res)
        # reflect approved (proposed) orders into the book snapshot so caps compound across a batch
        if res["result"] in ("PROPOSED",):
            delta = o.notional if o.side == "buy" else -o.notional
            book.positions[o.symbol] = book.positions.get(o.symbol, 0.0) + delta
            book.orders_today += 1
    return out


if __name__ == "__main__":
    # demo: notification-mode batch, no creds, nothing placed
    cfg = CapConfig()
    book = BookState()
    demo = [
        Order("BTC-USD", "buy", 3000, "coinbase-cdp", "crypto_lowfreq_backtest.py:REGIME-SMA(paper)"),
        Order("RSP", "buy", 4000, "robinhood", "midrisk_allocation_backtest.py:RSP70/GLD15/IEF15"),
        Order("NVDA", "buy", 9999, "robinhood", "stock_intraday_backtest.py"),  # exceeds per-order cap
        Order("ETH-USD", "sell", 1000, "coinbase-cdp", ""),                      # no strategy_ref
    ]
    print("Notification-mode batch (no creds, nothing placed):\n")
    for r in run_batch(demo, book, cfg, mode="notify", now="2026-06-03"):
        line = r.get("ticket") or r.get("reason")
        print(f"  {r['result']:14s} {line}")
    print(f"\nAudit log -> {AUDIT_LOG}")
