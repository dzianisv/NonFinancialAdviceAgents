"""
Flat-cost gate driver for the regime_sma_maker strategy candidate — the previously
missing half of the pair (scripts/run_regime_sma_maker_fillsim.py is the fill-sim half).

Closes the verifier-flagged P1 reproducibility gap (see README "Known reproducibility
gap"): results/regime_sma_maker_gate.json used to have no committed driver — the verifier
reproduced it by calling core.gate.gate() directly. This script IS that call, committed,
mirroring the run_<strategy>_gate.py pattern of the other two strategies.

Runs core/gate.py's gate() PER SYMBOL (BTC primary, ETH secondary — this strategy is a
single-asset regime timer, not cross-sectional) over the declared PARAM_GRID
(strategies/regime_sma_maker.PARAM_GRID), then adds a buy-and-hold benchmark per symbol
over the same OOS window, net of one entry taker fee (the same convention as
run_xs_momentum_gate.py's benchmarks() and harness_self_test.py).

Writes intraday-bot/results/regime_sma_maker_gate.json.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import data, gate
from core.costs import TAKER_RATE
from strategies.regime_sma_maker import signals, PARAM_GRID

INTERVAL = "1d"
BARS_PER_YEAR = gate.BARS_PER_YEAR[INTERVAL]
OOS_START = gate.OOS_START
SYMBOLS = ["BTCUSDT", "ETHUSDT"]


def _clean(obj):
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, (np.floating,)):
        return None if obj != obj else float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, float) and obj != obj:  # NaN
        return None
    if isinstance(obj, pd.Timestamp):
        return str(obj)
    return obj


def hold_benchmark(df: pd.DataFrame) -> dict | None:
    """Buy-and-hold over the OOS window, net of one entry taker fee (same convention as
    run_xs_momentum_gate.py's benchmarks())."""
    close = df["close"]
    close = close[close.index >= pd.Timestamp(OOS_START, tz="UTC")]
    if len(close) < 5:
        return None
    ret = close.pct_change().fillna(0.0)
    net = ret.copy()
    net.iloc[0] = net.iloc[0] - TAKER_RATE
    w = pd.Series(1.0, index=close.index)
    m = gate.compute_metrics(net, w, BARS_PER_YEAR)
    return m.to_dict() if m else None


def main():
    report = {}
    benchmarks = {}
    for sym in SYMBOLS:
        df = data.load(sym, INTERVAL)
        print(f"=== {sym}: gate() over PARAM_GRID={PARAM_GRID} ===")
        r = gate.gate(signals, {sym: df}, PARAM_GRID, interval=INTERVAL)
        report[sym] = r
        oos = r.get("out_of_sample")
        print(f"  verdict={r['verdict']} best_params={r['best_params']} "
              f"oos_sharpe={oos['sharpe'] if oos else None} "
              f"dsr={r['deflated_sharpe']}")
        benchmarks[f"hold_{sym}"] = hold_benchmark(df)
    report["benchmarks"] = benchmarks

    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "regime_sma_maker_gate.json")
    with open(out_path, "w") as f:
        json.dump(_clean(report), f, indent=2, default=str)
    print(f"\nWrote {out_path}")
    return report


if __name__ == "__main__":
    main()
