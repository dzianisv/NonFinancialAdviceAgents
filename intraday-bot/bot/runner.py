#!/usr/bin/env python3
"""
bot/runner.py — the live/paper trading daemon loop.

Cycle:
    1. fetch latest bars for every configured symbol (bot/market_data.py: alpaca-py public
       market data, ccxt public fallback)
    2. compute target position by calling the SAME strategy module used in backtests
       (strategies/<key>.py, key from config.yaml) — no reimplementation of signal logic
    3. diff target vs current position (bot/sizing.py) -> proposed orders
    4. propose orders -> connectors.hard_caps.check() (via bot/executor.py) -> execute per
       mode (notify/paper/live)
    5. journal every order/cycle to bot/state/*.jsonl (idempotent restart)

Usage:
    python3 bot/runner.py [--config path/to/config.yaml] [--once]

All timestamps UTC (house rule). Signals are computed on PRIOR bar close only — this
runner does not touch signal logic itself; it trusts the strategy module's own contract,
which core/gate.py's look_ahead_canary()/shift_collapse_check() verify at backtest time.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # intraday-bot/

from bot.caps import BOOK_500_CAPS, CapConfig  # noqa: E402
from bot.config import BotConfig, load_config, DEFAULT_CONFIG_PATH  # noqa: E402
from bot.executor import execute_order  # noqa: E402
from bot.market_data import fetch_universe, MarketDataError  # noqa: E402
from bot.sizing import diff_universe  # noqa: E402
from bot.state_store import StateStore  # noqa: E402
from bot.strategy_loader import load_strategy, StrategyLoadError  # noqa: E402

KILL_SWITCH_MESSAGE = "kill switch active — cycle skipped, no orders proposed"


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _cycle_ts() -> str:
    """Coarse per-cycle timestamp used in client_order_id (minute resolution is enough to
    dedupe within-cycle retries without colliding across distinct cycles)."""
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M")


def run_cycle(cfg: BotConfig, store: StateStore, cap_cfg: CapConfig = BOOK_500_CAPS) -> dict:
    """Run exactly one fetch -> signal -> diff -> caps -> execute cycle. Returns a summary
    dict (also journaled to cycles.jsonl). Never raises for expected failure modes (missing
    data, no signal) — those are logged and the cycle ends cleanly; only programming errors
    propagate."""
    cycle_ts = _cycle_ts()
    started = _now_iso()

    if os.path.exists(cap_cfg.kill_switch_file):
        summary = {"cycle_ts": cycle_ts, "started": started, "status": "KILLED",
                   "note": KILL_SWITCH_MESSAGE}
        store.log_cycle(summary)
        print(f"[{cycle_ts}] {KILL_SWITCH_MESSAGE}")
        return summary

    # 1. fetch latest bars
    df_dict, skipped_symbols = fetch_universe(cfg.symbols, cfg.interval, cfg.lookback_bars)
    if skipped_symbols:
        for sym, err in skipped_symbols.items():
            print(f"[{cycle_ts}] [WARN] market data unavailable for {sym}: {err}")
    if not df_dict:
        summary = {"cycle_ts": cycle_ts, "started": started, "status": "NO_DATA",
                   "skipped_symbols": skipped_symbols}
        store.log_cycle(summary)
        print(f"[{cycle_ts}] no market data for any configured symbol — cycle skipped")
        return summary

    # 2. strategy signal (SAME module used in backtests)
    try:
        signal_fn = load_strategy(cfg.strategy_key)
    except StrategyLoadError as e:
        summary = {"cycle_ts": cycle_ts, "started": started, "status": "STRATEGY_LOAD_ERROR",
                   "error": str(e)}
        store.log_cycle(summary)
        print(f"[{cycle_ts}] [ERROR] {e}")
        return summary

    raw = signal_fn(df_dict, cfg.strategy_params)
    target_weights = {}
    for sym, series in (raw.items() if isinstance(raw, dict) else {next(iter(df_dict)): raw}.items()):
        if sym not in df_dict or series is None or len(series) == 0:
            continue
        target_weights[sym] = float(series.iloc[-1])  # most recent (prior-bar-decided) weight

    # 3. diff vs current position
    current_positions = store.reconstruct_positions()
    proposed = diff_universe(target_weights, current_positions, cap_cfg)

    # 4. execute each proposed order through caps -> mode routing
    results = []
    for po in proposed:
        last_price = float(df_dict[po.symbol]["close"].iloc[-1]) if po.symbol in df_dict else None
        res = execute_order(
            po, store, cap_cfg, cfg.mode, cfg.strategy_key, cycle_ts,
            last_price=last_price, maker_offset_bps=cfg.maker_offset_bps,
        )
        results.append(res)
        print(f"[{cycle_ts}] {res.result:20s} {po.side.upper():4s} ${po.notional:>7.2f} {po.symbol}"
              f"  (target_w={po.target_weight:.2f})")
        # reflect PROPOSED/SUBMITTED buys/sells into the position journal so the NEXT cycle's
        # diff sees the updated holding (idempotent: one snapshot per fill event)
        if res.result in ("PROPOSED", "SUBMITTED", "FILLED"):
            delta = po.notional if po.side == "buy" else -po.notional
            new_notional = current_positions.get(po.symbol, 0.0) + delta
            current_positions[po.symbol] = new_notional
            store.log_position_snapshot({
                "symbol": po.symbol, "notional": new_notional, "cycle_ts": cycle_ts,
                "reason": res.result,
            })

    summary = {
        "cycle_ts": cycle_ts, "started": started, "status": "OK",
        "symbols_fetched": list(df_dict.keys()), "symbols_skipped": skipped_symbols,
        "target_weights": target_weights, "n_proposed": len(proposed),
        "results": [{"client_order_id": r.client_order_id, "result": r.result} for r in results],
    }
    store.log_cycle(summary)
    if not proposed:
        print(f"[{cycle_ts}] no order needed — all symbols within target band")
    return summary


def run_daemon(cfg: BotConfig, cap_cfg: CapConfig = BOOK_500_CAPS) -> None:
    state_dir = cfg.state_dir if os.path.isabs(cfg.state_dir) else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bot", cfg.state_dir)
    store = StateStore(state_dir)

    print(f"intraday-bot runner starting — mode={cfg.mode} strategy={cfg.strategy_key} "
          f"symbols={cfg.symbols} interval={cfg.interval} poll={cfg.poll_seconds}s")
    print(f"caps: order<=${cap_cfg.max_order_notional:.0f} position<=${cap_cfg.max_position_notional:.0f} "
          f"gross<=${cap_cfg.max_gross_notional:.0f} daily_loss_kill=${cap_cfg.max_daily_loss:.0f} "
          f"orders/day<={cap_cfg.max_orders_per_day} shorts={'allowed' if cap_cfg.allow_shorts else 'DISABLED'}")

    n = 0
    while True:
        try:
            run_cycle(cfg, store, cap_cfg)
        except Exception as e:  # noqa: BLE001 - daemon must survive an unexpected cycle error
            print(f"[ERROR] cycle raised unexpectedly: {e}")
            store.log_cycle({"cycle_ts": _cycle_ts(), "status": "ERROR", "error": str(e)})

        n += 1
        if cfg.dry_run_once or (cfg.max_loop_iterations is not None and n >= cfg.max_loop_iterations):
            print(f"stopping after {n} iteration(s) (dry_run_once={cfg.dry_run_once}, "
                  f"max_loop_iterations={cfg.max_loop_iterations})")
            break
        time.sleep(cfg.poll_seconds)


def main() -> None:
    ap = argparse.ArgumentParser(description="intraday-bot live/paper runner")
    ap.add_argument("--config", default=DEFAULT_CONFIG_PATH)
    ap.add_argument("--once", action="store_true", help="run exactly one cycle then exit")
    args = ap.parse_args()

    cfg = load_config(args.config)
    if args.once:
        cfg.dry_run_once = True
    run_daemon(cfg)


if __name__ == "__main__":
    main()
