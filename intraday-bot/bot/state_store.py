"""
Append-only jsonl state journal for positions/orders. Idempotent restart: on boot, the
runner replays the journal to reconstruct current positions and today's order count/PnL
rather than trusting any in-memory state — a crash/restart never double-submits an order
because the last-known-good state is always re-derived from disk, and every order carries
a deterministic client_order_id so a resubmission of the same intent is detectable.

Files (under bot/state/):
    orders.jsonl     one line per order lifecycle event (PROPOSED/SUBMITTED/FILLED/REJECTED/...)
    positions.jsonl  one line per position snapshot after a fill/reconciliation
    cycles.jsonl      one line per runner loop iteration (heartbeat + summary)
"""
from __future__ import annotations

import json
import os
import datetime as _dt
from dataclasses import asdict, is_dataclass
from typing import Optional


class StateStore:
    def __init__(self, state_dir: str):
        self.state_dir = state_dir
        os.makedirs(state_dir, exist_ok=True)
        self.orders_path = os.path.join(state_dir, "orders.jsonl")
        self.positions_path = os.path.join(state_dir, "positions.jsonl")
        self.cycles_path = os.path.join(state_dir, "cycles.jsonl")

    @staticmethod
    def _to_jsonable(record: dict) -> dict:
        out = {}
        for k, v in record.items():
            if is_dataclass(v):
                out[k] = asdict(v)
            else:
                out[k] = v
        return out

    def _append(self, path: str, record: dict) -> None:
        record = dict(record)
        record.setdefault("logged_at", _dt.datetime.now(_dt.timezone.utc).isoformat())
        with open(path, "a") as f:
            f.write(json.dumps(self._to_jsonable(record), sort_keys=True, default=str) + "\n")

    def log_order_event(self, record: dict) -> None:
        self._append(self.orders_path, record)

    def log_position_snapshot(self, record: dict) -> None:
        self._append(self.positions_path, record)

    def log_cycle(self, record: dict) -> None:
        self._append(self.cycles_path, record)

    @staticmethod
    def _read_jsonl(path: str) -> list:
        if not os.path.exists(path):
            return []
        out = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue  # tolerate a torn last line from a crash mid-write
        return out

    def read_orders(self) -> list:
        return self._read_jsonl(self.orders_path)

    def read_positions(self) -> list:
        return self._read_jsonl(self.positions_path)

    def read_cycles(self) -> list:
        return self._read_jsonl(self.cycles_path)

    def seen_client_order_ids(self) -> set:
        """All client_order_ids we've ever logged an event for — used to dedupe on restart
        so the SAME intended order (same symbol/side/cycle) is never resubmitted."""
        return {r["client_order_id"] for r in self.read_orders() if r.get("client_order_id")}

    def reconstruct_positions(self) -> dict:
        """Replay position snapshots to the latest known state per symbol (signed notional).
        Returns {} if no snapshots exist yet (fresh book)."""
        latest: dict = {}
        for rec in self.read_positions():
            sym = rec.get("symbol")
            if sym is None:
                continue
            latest[sym] = rec  # jsonl is append-only in order, last write wins
        return {sym: rec.get("notional", 0.0) for sym, rec in latest.items()}

    def orders_today(self, today_utc: str) -> int:
        """Count of order-submission events logged today (UTC date string 'YYYY-MM-DD'),
        counting only PROPOSED-or-later terminal attempts that reached the executor
        (mirrors connectors.notify_executor's PROPOSED counting)."""
        n = 0
        for rec in self.read_orders():
            ts = rec.get("ts", rec.get("logged_at", ""))
            if isinstance(ts, str) and ts.startswith(today_utc) and rec.get("result") == "PROPOSED":
                n += 1
        return n

    def realized_pnl_today(self, today_utc: str) -> float:
        total = 0.0
        for rec in self.read_orders():
            ts = rec.get("ts", rec.get("logged_at", ""))
            if isinstance(ts, str) and ts.startswith(today_utc):
                total += float(rec.get("realized_pnl", 0.0) or 0.0)
        return total


def client_order_id(cycle_ts: str, symbol: str, side: str) -> str:
    """Deterministic id for idempotency: same cycle+symbol+side always maps to the same id,
    so a restart mid-cycle can detect 'did I already submit this' instead of resubmitting."""
    safe_sym = symbol.replace("/", "-")
    return f"{cycle_ts}_{safe_sym}_{side}"
