"""Chart for the regime_sma_maker fill-sim report. Reads results/regime_sma_maker_fillsim.json
and plots OOS Sharpe by fill-sim tier, both symbols (BTC, ETH) — the chart referenced by
reports/regime_sma_maker.md as report/img/regime_sma_maker_fillsim_stress.png.

Added post-P0-fix (2026-07-02): previously this chart had no committed regeneration script
(README-flagged reproducibility gap); adding it now so the fixed fill-sim numbers (P&L now
computed from actual simulated fill prices, not close-to-close only) can be regenerated with
one command going forward, matching the pattern of chart_xs_momentum.py / chart_meanrev_maker.py.

Run: /Users/engineer/.venv/bin/python3 scripts/chart_regime_sma_maker.py
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

IMG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "report", "img")
os.makedirs(IMG_DIR, exist_ok=True)

RESULTS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "results", "regime_sma_maker_fillsim.json")

TIERS = ["base", "offset_5bp", "stress_2x_fees", "stress_delay_1bar",
          "stress_reduced_fill_prob", "stress_worst_vol_slippage"]


def main():
    with open(RESULTS_PATH) as f:
        results = json.load(f)

    tier_labels = [t.replace("stress_", "").replace("_", "\n") for t in TIERS]

    fig, ax = plt.subplots(figsize=(11, 5))
    width = 0.35
    x = range(len(TIERS))

    btc_sharpes = [results["BTCUSDT"][t]["metrics"]["sharpe"] if results["BTCUSDT"][t]["metrics"] else None for t in TIERS]
    eth_sharpes = [results["ETHUSDT"][t]["metrics"]["sharpe"] if results["ETHUSDT"][t]["metrics"] else None for t in TIERS]

    ax.bar([i - width / 2 for i in x], [s if s is not None else 0 for s in btc_sharpes],
           width=width, label="BTC (sma_window=50)", color="steelblue")
    ax.bar([i + width / 2 for i in x], [s if s is not None else 0 for s in eth_sharpes],
           width=width, label="ETH (sma_window=200)", color="darkorange")
    ax.axhline(0, color="black", linewidth=1)
    ax.set_xticks(list(x))
    ax.set_xticklabels(tier_labels, fontsize=8)
    ax.set_ylabel("OOS Sharpe (bar-by-bar maker-fill sim, P&L from actual fill price)")
    ax.set_title("regime_sma_maker: OOS Sharpe by fill-sim tier (2024-01-01 -> 2026-07-01)")
    for i, s in enumerate(btc_sharpes):
        if s is not None:
            ax.text(i - width / 2, s + (0.02 if s >= 0 else -0.05), f"{s:.2f}", ha="center", fontsize=7)
    for i, s in enumerate(eth_sharpes):
        if s is not None:
            ax.text(i + width / 2, s + (0.02 if s >= 0 else -0.05), f"{s:.2f}", ha="center", fontsize=7)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "regime_sma_maker_fillsim_stress.png"), dpi=120)
    plt.close(fig)
    print("Wrote regime_sma_maker_fillsim_stress.png")


if __name__ == "__main__":
    main()
