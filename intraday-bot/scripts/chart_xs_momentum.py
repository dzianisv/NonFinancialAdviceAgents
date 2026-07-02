"""Charts for the xs_momentum report. Reads results/xs_momentum.json plus re-derives the
OOS equity curve for the chosen config (harness cost-model path, not the bar-by-bar fill
sim) against hold-BTC and equal-weight-hold-universe benchmarks, and bar charts for the
fill-model stress tiers and the N-sensitivity / drop-top-1 ablation.

Run: /Users/engineer/.venv/bin/python3 scripts/chart_xs_momentum.py
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import data, gate
from core.costs import CostConfig, TAKER_RATE
from strategies import xs_momentum as xm
from scripts.run_xs_momentum_gate import CANDIDATE_SYMBOLS, load_universe

IMG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "report", "img")
os.makedirs(IMG_DIR, exist_ok=True)

RESULTS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "results", "xs_momentum.json")


def main():
    with open(RESULTS_PATH) as f:
        results = json.load(f)

    best_params = results["gate"]["best_params"]
    bpy = gate.BARS_PER_YEAR["1d"]

    print("Loading candidate universe...")
    df_dict, missing = load_universe()
    print(f"  loaded {len(df_dict)} symbols, missing {missing}")

    # --- Chart 1: OOS equity curve, chosen xs_momentum config vs hold-BTC vs
    #     equal-weight-hold-universe (harness cost-model path, net of costs) ---
    net, w = gate.run_backtest(xm.signals, df_dict, best_params, CostConfig(), bpy, start=gate.OOS_START)
    eq_strat = (1 + net).cumprod()

    btc_close = df_dict["BTCUSDT"]["close"]
    oos_close = btc_close[btc_close.index >= pd.Timestamp(gate.OOS_START, tz="UTC")]
    ret_hold = oos_close.pct_change().fillna(0.0)
    ret_hold.iloc[0] = ret_hold.iloc[0] - TAKER_RATE
    eq_hold = (1 + ret_hold).cumprod()

    rets = {}
    for sym, df in df_dict.items():
        c = df["close"]
        c = c[c.index >= pd.Timestamp(gate.OOS_START, tz="UTC")]
        if len(c) < 5:
            continue
        r = c.pct_change().fillna(0.0)
        r.iloc[0] -= TAKER_RATE
        rets[sym] = r
    M = pd.concat(rets, axis=1).fillna(0.0)
    port_ew = M.mean(axis=1)
    eq_ew = (1 + port_ew).cumprod()

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(eq_strat.index, eq_strat.values,
            label=f"xs_momentum (OOS, net of costs, lookback={best_params['lookback_days']}d top_n={best_params['top_n']})",
            color="firebrick")
    ax.plot(eq_hold.index, eq_hold.values, label="Buy-and-hold BTC (OOS, net of 1 entry taker fee)", color="steelblue")
    ax.plot(eq_ew.index, eq_ew.values, label="Equal-weight hold full candidate universe (OOS, net of 1 entry fee/name)",
            color="darkorange", alpha=0.8)
    ax.set_yscale("log")
    ax.set_title("xs_momentum OOS equity vs benchmarks (2024-01-01 -> 2026-07-01, log scale)")
    ax.set_ylabel("Equity (log scale, start=1.0)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "xs_momentum_equity_oos.png"), dpi=120)
    plt.close(fig)
    print("Wrote xs_momentum_equity_oos.png")

    # --- Chart 2: fill-model report by stress tier (fill rate, skipped entries, Sharpe) ---
    fm = results["fill_model_report"]
    tiers = list(fm.keys())
    tier_labels = [t.replace("stress_", "").replace("_", "\n") for t in tiers]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    fill_rates = [fm[t]["fill_rate"] for t in tiers]
    axes[0].bar(tier_labels, fill_rates, color="steelblue")
    axes[0].set_ylabel("Entry+exit fill rate")
    axes[0].set_title("Fill rate by stress tier")
    axes[0].set_ylim(0, 1.05)
    axes[0].grid(alpha=0.3, axis="y")

    skipped = [fm[t]["n_skipped_entries"] for t in tiers]
    axes[1].bar(tier_labels, skipped, color="darkorange")
    axes[1].set_ylabel("# skipped entries (opportunity cost, not realized P&L)")
    axes[1].set_title("Skipped rebalance entries by stress tier")
    axes[1].grid(alpha=0.3, axis="y")

    sharpes = [fm[t]["metrics"]["sharpe"] if fm[t]["metrics"] else None for t in tiers]
    colors = ["firebrick" if (s is not None and s < 0) else "seagreen" for s in sharpes]
    axes[2].bar(tier_labels, [s if s is not None else 0 for s in sharpes], color=colors)
    axes[2].axhline(0, color="black", linewidth=1)
    axes[2].set_ylabel("OOS Sharpe (bar-by-bar fill sim)")
    axes[2].set_title("Sharpe by stress tier (fill-sim path)")
    axes[2].grid(alpha=0.3, axis="y")

    fig.suptitle("xs_momentum fill-model report (OOS window, chosen config)")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "xs_momentum_fillmodel_stress.png"), dpi=120)
    plt.close(fig)
    print("Wrote xs_momentum_fillmodel_stress.png")

    # --- Chart 3: N-sensitivity + drop-top-1 ablation, OOS Sharpe bar chart ---
    sens = results["sensitivity"]
    labels = list(sens.keys())
    sharpes = [sens[k]["oos_metrics"]["sharpe"] if sens[k]["oos_metrics"] else None for k in labels]
    colors = ["firebrick" if (s is not None and s < 0) else "seagreen" for s in sharpes]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar(labels, [s if s is not None else 0 for s in sharpes], color=colors)
    ax.axhline(0, color="black", linewidth=1)
    ax.set_ylabel("OOS Sharpe (harness cost-model path)")
    ax.set_title("xs_momentum: N-sensitivity + drop-top-1 ablation (OOS, same lookback)")
    for i, s in enumerate(sharpes):
        if s is not None:
            ax.text(i, s + (0.02 if s >= 0 else -0.05), f"{s:.2f}", ha="center", fontsize=9)
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "xs_momentum_sensitivity.png"), dpi=120)
    plt.close(fig)
    print("Wrote xs_momentum_sensitivity.png")

    print("Wrote 3 charts to", IMG_DIR)


if __name__ == "__main__":
    main()
