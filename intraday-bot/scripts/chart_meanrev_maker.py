"""Charts for the meanrev_maker report. Reads results/meanrev_maker.json plus re-derives the
OOS equity curve (is_maker=True) and the benchmark hold-BTC equity curve for a side-by-side
plot, and a bar chart of fill-model stats (fill rate / timeout-exit rate by stress tier).

Run: /Users/engineer/.venv/bin/python3 scripts/chart_meanrev_maker.py
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
from strategies.meanrev_maker import signals

IMG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "report", "img")
os.makedirs(IMG_DIR, exist_ok=True)

BEST_PARAMS = {"lookback": 48, "k": 2.0, "timeout_bars": 24, "stop_k": 2.0}


def main():
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "results", "meanrev_maker.json")) as f:
        results = json.load(f)

    df_dict = {sym: data.load(sym, "5m") for sym in ["BTCUSDT", "ETHUSDT", "SOLUSDT"]}
    bpy = gate.BARS_PER_YEAR["5m"]

    # --- Chart 1: OOS equity curve, strategy (is_maker=True) vs hold-BTC benchmark ---
    net, w = gate.run_backtest(signals, df_dict, BEST_PARAMS, CostConfig(), bpy,
                                start=gate.OOS_START, is_maker=True)
    eq_strat = (1 + net).cumprod()

    btc_close = df_dict["BTCUSDT"]["close"]
    oos_close = btc_close[btc_close.index >= pd.Timestamp(gate.OOS_START, tz="UTC")]
    ret_hold = oos_close.pct_change().fillna(0.0)
    ret_hold.iloc[0] = ret_hold.iloc[0] - TAKER_RATE
    eq_hold = (1 + ret_hold).cumprod()

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(eq_strat.index, eq_strat.values, label="meanrev_maker (OOS, net of maker costs)", color="firebrick")
    ax.plot(eq_hold.index, eq_hold.values, label="Buy-and-hold BTC (OOS, net of 1 entry taker fee)", color="steelblue")
    ax.set_yscale("log")
    ax.set_title("meanrev_maker OOS equity vs hold-BTC benchmark (2024-01-01 -> 2026-07-01, log scale)")
    ax.set_ylabel("Equity (log scale, start=1.0)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "meanrev_maker_equity_oos.png"), dpi=120)
    plt.close(fig)

    # --- Chart 2: fill-model report by stress tier ---
    fm = results["fill_model_report"]
    tiers = list(fm.keys())
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    x = range(len(tiers))
    width = 0.25
    for i, sym in enumerate(symbols):
        fill_rates = [fm[t][sym]["fill_rate"] for t in tiers]
        axes[0].bar([xi + i * width for xi in x], fill_rates, width, label=sym)
    axes[0].set_xticks([xi + width for xi in x])
    axes[0].set_xticklabels([t.replace("stress_", "").replace("_", "\n") for t in tiers], fontsize=8)
    axes[0].set_ylabel("Entry fill rate")
    axes[0].set_title("Maker entry fill rate by stress tier")
    axes[0].legend(fontsize=8)
    axes[0].grid(alpha=0.3, axis="y")

    for i, sym in enumerate(symbols):
        timeout_pct = [fm[t][sym]["n_timeout_exits_pct_of_exits"] for t in tiers]
        axes[1].bar([xi + i * width for xi in x], timeout_pct, width, label=sym)
    axes[1].set_xticks([xi + width for xi in x])
    axes[1].set_xticklabels([t.replace("stress_", "").replace("_", "\n") for t in tiers], fontsize=8)
    axes[1].set_ylabel("% of exits forced to taker (timeout)")
    axes[1].set_title("Timeout-to-taker exit rate by stress tier")
    axes[1].legend(fontsize=8)
    axes[1].grid(alpha=0.3, axis="y")

    fig.suptitle("meanrev_maker fill-model report (OOS window, best-IS config)")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "meanrev_maker_fillmodel_stress.png"), dpi=120)
    plt.close(fig)

    # --- Chart 3: gross vs net return per round trip, base tier ---
    fig, ax = plt.subplots(figsize=(9, 5))
    base = fm["base"]
    gross = [base[s]["mean_gross_return_per_round_trip"] * 10000 for s in symbols]
    net_rt = [base[s]["mean_net_return_per_round_trip"] * 10000 for s in symbols]
    x = range(len(symbols))
    ax.bar([xi - 0.2 for xi in x], gross, width=0.4, label="Mean gross return/round-trip (bps)", color="steelblue")
    ax.bar([xi + 0.2 for xi in x], net_rt, width=0.4, label="Mean net return/round-trip (bps)", color="firebrick")
    ax.axhline(-30, color="black", linestyle="--", linewidth=1, label="Required breakeven: -30bp maker round-trip cost")
    ax.set_xticks(list(x))
    ax.set_xticklabels(symbols)
    ax.set_ylabel("bps per round trip")
    ax.set_title("meanrev_maker: gross vs net edge per round trip (base tier, OOS)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "meanrev_maker_edge_per_roundtrip.png"), dpi=120)
    plt.close(fig)

    print("Wrote 3 charts to", IMG_DIR)


if __name__ == "__main__":
    main()
