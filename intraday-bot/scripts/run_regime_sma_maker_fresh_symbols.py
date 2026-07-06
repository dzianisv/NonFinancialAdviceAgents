"""
Pre-registered fresh-symbol confirmation run for the regime_sma_maker strategy family.

See intraday-bot/preregistrations/2026-07-06-regime-sma-fresh-symbols.md for the full
pre-registration (frozen rule, symbol list, cost model, scoring windows, and the mechanical
pass/fail interpretation rule) — committed BEFORE this script was run against any result.

This is a FALSIFICATION test, not significance-hunting: regime_sma_maker is dead-firewalled
per TRIAL_LEDGER.md (DSR 0.39 BTC / 0.30 ETH at honest N=5). ROADMAP.md Section 5 sanctions
exactly one more evidence type here — a zero-parameter-change confirmation on fresh symbols.
This run does NOT increment cumulative_family_n_trials (stays 5); it is confirmation
evidence, not a new trial.

Frozen rule: strategies/regime_sma_maker.signals() unchanged, sma_window=50 (the BTC-winning
config per results/regime_sma_maker_gate.json's BTCUSDT.best_params), no grid, no per-symbol
tuning. Mirrors scripts/run_regime_sma_maker_gate.py (flat-cost gate + hold benchmark) and
scripts/run_regime_sma_maker_fillsim.py (honest bar-by-bar fill sim), restricted to tiers
base / stress_2x_fees / stress_delay_1bar.

Symbols: SOLUSDT, XRPUSDT, DOGEUSDT, ADAUSDT, LINKUSDT (pre-registered; never substituted).

Writes intraday-bot/results/regime_sma_fresh_symbols.json.
"""
from __future__ import annotations

import json
import os
import sys
import traceback

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import data, gate
from core.costs import TAKER_RATE, CostConfig, STRESS_2X_FEES
from strategies.regime_sma_maker import signals

# ---- frozen, pre-registered (do NOT edit after seeing any result) ----
SMA_WINDOW = 50
PARAM_GRID = [{"sma_window": SMA_WINDOW}]
SYMBOLS = ["SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "LINKUSDT"]
INTERVAL = "1d"
BARS_PER_YEAR = gate.BARS_PER_YEAR[INTERVAL]
OOS_START = gate.OOS_START
FAMILY_N_TRIALS_INFORMATIONAL = 5  # honest cumulative family N per TRIAL_LEDGER.md; this
                                    # run does NOT add to it (confirmation, not a new trial)


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


def hold_benchmark(df: pd.DataFrame, start: str | None, end: str | None = None) -> dict | None:
    """Buy-and-hold, net of one entry taker fee — identical convention to
    run_regime_sma_maker_gate.py's hold_benchmark(), generalized to an optional start/end
    (used for both the primary OOS window and the secondary full-history window)."""
    close = df["close"]
    if start:
        close = close[close.index >= pd.Timestamp(start, tz="UTC")]
    if end:
        close = close[close.index <= pd.Timestamp(end, tz="UTC")]
    if len(close) < 5:
        return None
    ret = close.pct_change().fillna(0.0)
    net = ret.copy()
    net.iloc[0] = net.iloc[0] - TAKER_RATE
    w = pd.Series(1.0, index=close.index)
    m = gate.compute_metrics(net, w, BARS_PER_YEAR)
    return m.to_dict() if m else None


def informational_dsr_at_n5(oos_metrics_dict: dict | None, oos_net: pd.Series | None) -> dict | None:
    """Informational-only DSR at n_trials=5 (family's current cumulative N per
    TRIAL_LEDGER.md), mirroring core/gate.py's gate() lines ~552-557 but hardcoding
    n_trials=5 instead of len(param_grid). NOT part of the pass/fail verdict — see
    pre-registration's N_eff ~1.2-1.4 correlation caveat."""
    if oos_metrics_dict is None or oos_net is None:
        return None
    import math
    sharpe = oos_metrics_dict["sharpe"]
    n_bars = oos_metrics_dict["n_bars"]
    period_sharpe = sharpe / math.sqrt(BARS_PER_YEAR)
    skew, kurt = gate._return_moments(oos_net)
    return gate.deflated_sharpe_ratio(period_sharpe, n_trials=FAMILY_N_TRIALS_INFORMATIONAL,
                                       n_obs=n_bars, skew=skew, kurt=kurt)


def fillsim_tiers(df_full: pd.DataFrame, symbol: str, sma_window: int) -> dict:
    """Honest bar-by-bar maker-fill simulation, mirroring
    scripts/run_regime_sma_maker_fillsim.py's run_symbol(), restricted to the 3
    pre-registered tiers: base, stress_2x_fees, stress_delay_1bar."""
    # Local import to reuse the exact simulate()/metrics_from_net() + tier-kwargs dicts
    # unchanged, per the pre-registration ("reuse ... unchanged from the script").
    import importlib
    fillsim_mod = importlib.import_module("scripts.run_regime_sma_maker_fillsim")

    pos_full = signals({symbol: df_full}, {"sma_window": sma_window})[symbol]
    df_oos = df_full[df_full.index >= pd.Timestamp(OOS_START, tz="UTC")]
    pos_oos = pos_full.reindex(df_oos.index).fillna(0.0)

    all_tiers = {
        "base": dict(offset_bps=0.0, stress_fill_prob=False, delay_bars=0,
                     extra_slip_worst_vol=False, base_cost_cfg=CostConfig()),
        "stress_2x_fees": dict(offset_bps=0.0, stress_fill_prob=False, delay_bars=0,
                                extra_slip_worst_vol=False, base_cost_cfg=STRESS_2X_FEES),
        "stress_delay_1bar": dict(offset_bps=0.0, stress_fill_prob=False, delay_bars=1,
                                   extra_slip_worst_vol=False, base_cost_cfg=CostConfig()),
    }

    out = {}
    for name, kwargs in all_tiers.items():
        sim = fillsim_mod.simulate(df_oos, pos_oos, notional=100.0, **kwargs)
        m = fillsim_mod.metrics_from_net(sim["net_returns"], bars_per_year=BARS_PER_YEAR)
        out[name] = {
            "sim": {k: v for k, v in sim.items() if k != "net_returns"},
            "metrics": m.to_dict() if m else None,
        }
    return out


def run_symbol(symbol: str) -> dict:
    df = data.load(symbol, INTERVAL)
    out = {
        "symbol": symbol,
        "sma_window": SMA_WINDOW,
        "n_bars_total": len(df),
        "first_bar": str(df.index[0]),
        "last_bar": str(df.index[-1]),
    }

    # --- primary: flat-cost gate() over the OOS window ---
    print(f"=== {symbol}: gate() over frozen param_grid={PARAM_GRID} (primary OOS) ===")
    g = gate.gate(signals, {symbol: df}, PARAM_GRID, interval=INTERVAL)
    out["gate_primary"] = g

    oos = g.get("out_of_sample")
    print(f"  verdict={g['verdict']} oos_sharpe={oos['sharpe'] if oos else None} "
          f"dsr(gate,n_trials=1)={g['deflated_sharpe']}")

    out["hold_benchmark_oos"] = hold_benchmark(df, start=OOS_START)

    # --- secondary: full-history metrics, same frozen rule, informational only ---
    net_full, w_full = gate.run_backtest(signals, {symbol: df}, {"sma_window": SMA_WINDOW},
                                          CostConfig(), BARS_PER_YEAR, start=None, end=None)
    m_full = gate.compute_metrics(net_full, w_full, BARS_PER_YEAR) if net_full is not None else None
    out["secondary_full_history"] = m_full.to_dict() if m_full else None
    out["hold_benchmark_full_history"] = hold_benchmark(df, start=None, end=None)

    # --- informational DSR at n_trials=5 (family's honest cumulative N) ---
    # gate.gate() doesn't return the raw OOS net-return series, so recompute it directly
    # (same call gate() makes internally) purely to get skew/kurt for the DSR calc.
    oos_net_direct, oos_w_direct = gate.run_backtest(signals, {symbol: df}, {"sma_window": SMA_WINDOW},
                                                      CostConfig(), BARS_PER_YEAR, start=OOS_START)
    out["informational_dsr_at_n5"] = informational_dsr_at_n5(oos, oos_net_direct)

    # --- honest fillsim tiers: base, stress_2x_fees, stress_delay_1bar ---
    print(f"  running fillsim tiers (base, stress_2x_fees, stress_delay_1bar)...")
    out["fillsim"] = fillsim_tiers(df, symbol, SMA_WINDOW)

    return out


def main():
    report = {
        "pre_registration": "intraday-bot/preregistrations/2026-07-06-regime-sma-fresh-symbols.md",
        "pre_registration_commit": "a00a18fdbc508f1a19a1ca3a2be61db1729b339e",
        "frozen_rule": {"strategy": "regime_sma_maker", "sma_window": SMA_WINDOW},
        "symbols_pre_registered": SYMBOLS,
        "note": "This run does NOT increment cumulative_family_n_trials (stays 5 per "
                "TRIAL_LEDGER.md) -- it is confirmation evidence per ROADMAP.md Section 5, "
                "not a new config/trial.",
        "symbols": {},
        "errors": {},
    }
    for sym in SYMBOLS:
        try:
            report["symbols"][sym] = run_symbol(sym)
        except Exception as e:
            print(f"!!! {sym} ERRORED: {type(e).__name__}: {e}")
            traceback.print_exc()
            report["errors"][sym] = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc(),
            }

    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "regime_sma_fresh_symbols.json")
    with open(out_path, "w") as f:
        json.dump(_clean(report), f, indent=2, default=str)
    print(f"\nWrote {out_path}")
    return report


if __name__ == "__main__":
    main()
