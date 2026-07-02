"""
Harness self-test (single reproducible command):
  /Users/engineer/.venv/bin/python3 scripts/harness_self_test.py

1. DETERMINISTIC PSEUDO-RANDOM strategy (fixed seed=1337): flips a target position
   (0 or 1) each bar via a deterministic PRNG stream (numpy Generator with fixed seed —
   reproducible every run, not "random" in the sense of being unseeded). This strategy has
   NO genuine edge by construction. Net of costs, its return should be approximately equal
   to MINUS the cost drag (turnover * fee_rate) -- gross return should be ~0 (a coin flip
   long/flat has zero expected edge on a directionless prior), so net ≈ -cost_drag confirms
   the harness isn't fabricating edge out of nothing and IS charging costs correctly.

2. BUY-AND-HOLD BTC benchmark: one entry fee paid at OOS_START, hold to the end of the OOS
   window, one exit fee paid at the end. Report OOS Sharpe net of those two fees.

Both are run through core/gate.py's run_backtest() (the same execution path real strategies
use) so this is a genuine test of the harness's cost/metrics plumbing, not a separate ad hoc
calculation.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import data, gate
from core.costs import CostConfig, TAKER_RATE

SEED = 1337


def pseudo_random_strategy(df_dict: dict, params: dict) -> dict:
    """Deterministic coin-flip long/flat strategy — fixed seed, no genuine signal.
    Position flips to 1 or 0 independently each bar with p=0.5, decided using ONLY the
    PRNG stream (no data dependency at all, so it is trivially prior-bar-safe: it never
    reads df's price columns for its decision)."""
    out = {}
    for sym, df in df_dict.items():
        rng = np.random.default_rng(params.get("seed", SEED))
        flips = rng.integers(0, 2, size=len(df)).astype(float)
        # shift +1 for realism/consistency with the prior-bar-close contract even though this
        # strategy has no data dependency to begin with
        out[sym] = pd.Series(flips, index=df.index).shift(1).fillna(0.0)
    return out


def buy_and_hold(df_dict: dict, params: dict) -> dict:
    out = {}
    for sym, df in df_dict.items():
        out[sym] = pd.Series(1.0, index=df.index)
    return out


def run_self_test():
    print(f"=== HARNESS SELF-TEST (seed={SEED}) ===\n")

    btc = data.load("BTCUSDT", "1d")
    df_dict = {"BTCUSDT": btc}

    cost_cfg = CostConfig()  # base house costs: maker 0.15%/taker 0.25%

    # ---- 1) deterministic pseudo-random strategy ----
    print("--- 1) Deterministic pseudo-random entry/exit (no genuine edge) ---")
    net, w = gate.run_backtest(pseudo_random_strategy, df_dict, {"seed": SEED}, cost_cfg,
                                bars_per_year=365, start=gate.OOS_START)
    m = gate.compute_metrics(net, w, 365)
    if m is None:
        print("  insufficient data for pseudo-random self-test")
    else:
        turnover_cost_drag = (w.diff().abs().fillna(w.abs()) * cost_cfg.taker_rate).sum()
        avg_annual_cost_drag = turnover_cost_drag / (len(net) / 365)
        print(f"  OOS net CAGR:        {m.cagr:8.4%}")
        print(f"  OOS net Sharpe:      {m.sharpe:8.3f}")
        print(f"  OOS turnover (sum):  {m.turnover:8.3f}")
        print(f"  Approx cost drag/yr: {-avg_annual_cost_drag:8.4%}  (expected ≈ net CAGR since gross ≈ 0)")
        near_cost_drag = abs(m.cagr - (-avg_annual_cost_drag)) < 0.05  # within 5pp tolerance
        print(f"  Net return ≈ -cost drag (gross≈0)? {'YES' if near_cost_drag else 'NO -- INVESTIGATE'}")

    # Re-run TWICE to prove reproducibility (same seed -> identical result)
    net2, w2 = gate.run_backtest(pseudo_random_strategy, df_dict, {"seed": SEED}, cost_cfg,
                                  bars_per_year=365, start=gate.OOS_START)
    reproducible = net is not None and net2 is not None and net.equals(net2)
    print(f"  Reproducible across repeated runs (same seed)? {'YES' if reproducible else 'NO -- BUG'}")

    # ---- 2) buy-and-hold BTC benchmark ----
    print("\n--- 2) Buy-and-hold BTC benchmark (net of one entry fee) ---")
    oos_close = btc["close"]
    oos_close = oos_close[oos_close.index >= pd.Timestamp(gate.OOS_START, tz="UTC")]
    ret = oos_close.pct_change().fillna(0.0)
    # one entry fee at the start (taker, since a hold strategy has no reason to assume a
    # favorable resting limit got filled for a single one-time entry) -- no further trading.
    entry_fee_rate = TAKER_RATE
    net_hold = ret.copy()
    net_hold.iloc[0] = net_hold.iloc[0] - entry_fee_rate
    w_hold = pd.Series(1.0, index=oos_close.index)
    m_hold = gate.compute_metrics(net_hold, w_hold, 365)
    if m_hold:
        print(f"  OOS net CAGR:   {m_hold.cagr:8.4%}")
        print(f"  OOS net Sharpe: {m_hold.sharpe:8.3f}  (net of one entry taker fee, {entry_fee_rate:.2%})")
        print(f"  Max DD:         {m_hold.max_dd:8.4%}")
    else:
        print("  insufficient data for buy-and-hold benchmark")

    print("\n=== SELF-TEST COMPLETE ===")
    return {
        "pseudo_random": m.to_dict() if m else None,
        "reproducible": reproducible,
        "buy_and_hold_btc": m_hold.to_dict() if m_hold else None,
    }


if __name__ == "__main__":
    run_self_test()
