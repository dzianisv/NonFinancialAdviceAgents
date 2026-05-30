import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# ── Data ──────────────────────────────────────────────────────────────────────
tickers = ["VOO", "TLT", "GLD", "IEF", "GBTC"]
prices = yf.download(tickers, start="2019-01-01", end="2026-05-28",
                     interval="1wk", auto_adjust=True)["Close"]
prices = prices.ffill().dropna()

starts     = pd.date_range("2020-01-01", "2024-10-01", freq="QS")
end_date   = pd.Timestamp("2026-05-27")
INITIAL    = 100_000
RF_WEEKLY  = 0.04 / 52

# ── Strategy definitions ──────────────────────────────────────────────────────
strategies = {
    "VOO DCA":         {"VOO": 1.00},
    "60/40 DCA":       {"VOO": 0.60, "TLT": 0.40},
    "All-weather DCA": {"VOO": 0.30, "TLT": 0.40, "GLD": 0.15, "IEF": 0.15},
    "Degen DCA":       {"VOO": 0.70, "GLD": 0.20, "GBTC": 0.10},
    "Gold hedge DCA":  {"VOO": 0.80, "GLD": 0.20},
}

def run_strategy(alloc: dict, start: pd.Timestamp, end: pd.Timestamp,
                 prices: pd.DataFrame, initial: float = 100_000,
                 rf_weekly: float = 4/52/100) -> dict:
    """Simulate quarterly DCA for a given allocation dict."""
    # Quarterly installment schedule
    quarters = pd.date_range(start, end, freq="QS")
    n_q      = len(quarters)
    install  = initial / n_q          # equal installment each quarter

    # Price slice for this window
    px = prices.loc[start:end, list(alloc.keys())].copy()
    if px.empty:
        return None

    weeks      = px.index
    cash       = initial              # starts fully in cash
    shares     = {t: 0.0 for t in alloc}
    port_vals  = []
    next_q_idx = 0                    # pointer into quarters[]

    for week in weeks:
        # Deploy quarterly installment if it's time
        while next_q_idx < n_q and week >= quarters[next_q_idx]:
            for t, w in alloc.items():
                if t in px.columns and not pd.isna(px.loc[week, t]):
                    p = px.loc[week, t]
                    if p > 0:
                        shares[t] += (install * w) / p
            cash -= install
            cash  = max(cash, 0)      # guard against float drift
            next_q_idx += 1

        # Cash earns 4%/52 per week
        cash *= (1 + rf_weekly)

        # Portfolio value = cash + market value of shares
        equity = sum(shares[t] * px.loc[week, t]
                     for t in alloc
                     if t in px.columns and not pd.isna(px.loc[week, t]))
        port_vals.append(cash + equity)

    series = pd.Series(port_vals, index=weeks)

    # ── Metrics ───────────────────────────────────────────────────────────────
    total_invested = initial                  # all cash deployed eventually
    final_val      = series.iloc[-1]
    total_ret      = (final_val - total_invested) / total_invested

    n_years = (end - start).days / 365.25
    cagr    = (final_val / total_invested) ** (1 / n_years) - 1

    # Max drawdown (on weekly portfolio value)
    roll_max = series.cummax()
    dd       = (series - roll_max) / roll_max
    max_dd   = dd.min()

    # Weekly returns & Sharpe
    wr      = series.pct_change().dropna()
    excess  = wr - rf_weekly
    sharpe  = (excess.mean() / excess.std()) * np.sqrt(52) if excess.std() > 0 else np.nan

    return {
        "series":     series,
        "cagr":       cagr,
        "max_dd":     max_dd,
        "sharpe":     sharpe,
        "total_ret":  total_ret,
        "final_val":  final_val,
    }

# ── Run all combos ────────────────────────────────────────────────────────────
results = {}          # results[strategy][start] = metrics dict
for strat, alloc in strategies.items():
    results[strat] = {}
    for s in starts:
        r = run_strategy(alloc, s, end_date, prices, INITIAL, RF_WEEKLY)
        results[strat][s] = r

# ── Build summary table ───────────────────────────────────────────────────────
rows = []
for strat in strategies:
    for s in starts:
        r    = results[strat][s]
        r_voo = results["VOO DCA"][s]
        if r is None or r_voo is None:
            continue
        vs_voo = r["cagr"] - r_voo["cagr"]
        rows.append({
            "Strategy":   strat,
            "Start":      s.strftime("%Y-%m-%d"),
            "CAGR":       r["cagr"],
            "Max DD":     r["max_dd"],
            "Sharpe":     r["sharpe"],
            "Total Ret":  r["total_ret"],
            "vs VOO DCA": vs_voo,
        })

df = pd.DataFrame(rows)

# ── Print per-strategy tables ─────────────────────────────────────────────────
for strat in strategies:
    sub = df[df["Strategy"] == strat].copy()
    print(f"\n{'═'*80}")
    print(f"  {strat}")
    print(f"{'═'*80}")
    print(f"{'Start':<12} {'CAGR':>8} {'Max DD':>9} {'Sharpe':>8} {'Total Ret':>11} {'vs VOO DCA':>11}")
    print(f"{'-'*12} {'-'*8} {'-'*9} {'-'*8} {'-'*11} {'-'*11}")
    for _, row in sub.iterrows():
        vs_str = f"{row['vs VOO DCA']:+.2%}"
        print(f"{row['Start']:<12} {row['CAGR']:>8.2%} {row['Max DD']:>9.2%} "
              f"{row['Sharpe']:>8.2f} {row['Total Ret']:>11.2%} {vs_str:>11}")

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"\n{'═'*80}")
print("  SUMMARY — How often does each strategy beat VOO DCA?")
print(f"{'═'*80}")
print(f"{'Strategy':<22} {'Beats VOO':>10} {'Avg CAGR':>10} {'Avg CAGR gap':>14} "
      f"{'Avg Max DD':>11} {'Avg Sharpe':>11}")
print(f"{'-'*22} {'-'*10} {'-'*10} {'-'*14} {'-'*11} {'-'*11}")

summary_data = {}
for strat in strategies:
    sub      = df[df["Strategy"] == strat]
    beats    = (sub["vs VOO DCA"] > 0).sum()
    avg_cagr = sub["CAGR"].mean()
    avg_gap  = sub["vs VOO DCA"].mean()
    avg_dd   = sub["Max DD"].mean()
    avg_sh   = sub["Sharpe"].mean()
    summary_data[strat] = {"beats": beats, "avg_cagr": avg_cagr,
                            "avg_gap": avg_gap, "avg_dd": avg_dd, "avg_sh": avg_sh}
    print(f"{strat:<22} {beats:>10}/20 {avg_cagr:>10.2%} {avg_gap:>+14.2%} "
          f"{avg_dd:>11.2%} {avg_sh:>11.2f}")

# ── Key findings ──────────────────────────────────────────────────────────────
print(f"\n{'═'*80}")
print("  KEY FINDINGS")
print(f"{'═'*80}")

# Best strategy by avg CAGR gap
best   = max((s for s in strategies if s != "VOO DCA"),
             key=lambda s: summary_data[s]["avg_gap"])
worst  = min((s for s in strategies if s != "VOO DCA"),
             key=lambda s: summary_data[s]["avg_gap"])

print(f"\n1. Best alternative: {best}  (avg CAGR gap vs VOO: {summary_data[best]['avg_gap']:+.2%})")
print(f"   Worst alternative: {worst}  (avg CAGR gap vs VOO: {summary_data[worst]['avg_gap']:+.2%})")

# Gold hedge drawdown
voo_dd  = summary_data["VOO DCA"]["avg_dd"]
gold_dd = summary_data["Gold hedge DCA"]["avg_dd"]
print(f"\n2. Gold hedge vs pure VOO — avg Max DD:  VOO={voo_dd:.2%}  Gold hedge={gold_dd:.2%}")
dd_delta = gold_dd - voo_dd
print(f"   Drawdown difference: {dd_delta:+.2%}  "
      f"({'reduced' if dd_delta < 0 else 'worsened'} drawdown)")

# 60/40 analysis
sixty_gap = summary_data["60/40 DCA"]["avg_gap"]
sixty_beats = summary_data["60/40 DCA"]["beats"]
print(f"\n3. 60/40 DCA: beat VOO in {sixty_beats}/20 starts, avg CAGR gap {sixty_gap:+.2%}")
print(f"   → Bonds were crushed 2021-2022; 60/40 dragged by TLT in rising-rate env.")

# GBTC analysis
degen_gap    = summary_data["Degen DCA"]["avg_gap"]
degen_beats  = summary_data["Degen DCA"]["beats"]
degen_dd     = summary_data["Degen DCA"]["avg_dd"]
print(f"\n4. Degen DCA (GBTC 10%): beat VOO in {degen_beats}/20 starts, avg CAGR gap {degen_gap:+.2%}")
print(f"   Avg Max DD: {degen_dd:.2%}  (vs VOO {voo_dd:.2%})")
print(f"   → GBTC is highly path-dependent; entry-timing matters enormously.")

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(2, 1, figsize=(16, 12))

# Top: CAGR advantage bars per strategy (all 20 quarters stacked side-by-side)
ax1 = axes[0]
alt_strats = [s for s in strategies if s != "VOO DCA"]
n_alts     = len(alt_strats)
n_starts   = len(starts)
x          = np.arange(n_starts)
width      = 0.18
colors     = ["#2196F3", "#FF9800", "#4CAF50", "#E91E63"]

for i, strat in enumerate(alt_strats):
    sub   = df[df["Strategy"] == strat].sort_values("Start")
    gaps  = sub["vs VOO DCA"].values
    bars  = ax1.bar(x + i * width - 1.5 * width, gaps * 100, width,
                    label=strat, color=colors[i], alpha=0.85, edgecolor="white")

ax1.axhline(0, color="black", linewidth=1.2, linestyle="--")
ax1.set_xticks(x)
ax1.set_xticklabels([s.strftime("%Y-Q%q") if hasattr(s, 'strftime') else str(s)
                     for s in starts], rotation=45, ha="right", fontsize=8)
# Simpler date labels
ax1.set_xticklabels([s.strftime("%b %Y") for s in starts],
                    rotation=45, ha="right", fontsize=8)
ax1.set_ylabel("CAGR Advantage vs VOO DCA (pp)", fontsize=11)
ax1.set_title("CAGR Advantage of Each Alternative Strategy Over Pure VOO DCA\n"
              "(by quarterly start date, 2020–2024)", fontsize=13, fontweight="bold")
ax1.legend(loc="upper right", fontsize=9)
ax1.grid(axis="y", alpha=0.3)
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:+.1f}pp"))

# Bottom: Average CAGR bar chart with ±1 std-dev error bars
ax2 = axes[1]
strat_names   = list(strategies.keys())
avg_cagrs     = [summary_data[s]["avg_cagr"] * 100 for s in strat_names]
std_cagrs     = [df[df["Strategy"] == s]["CAGR"].std() * 100 for s in strat_names]
bar_colors    = ["#9E9E9E", "#2196F3", "#FF9800", "#E91E63", "#4CAF50"]

bars2 = ax2.bar(strat_names, avg_cagrs, color=bar_colors, alpha=0.85,
                edgecolor="white", zorder=3)
ax2.errorbar(strat_names, avg_cagrs, yerr=std_cagrs,
             fmt="none", color="black", capsize=6, linewidth=2, zorder=4)

for bar, avg, std in zip(bars2, avg_cagrs, std_cagrs):
    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + std + 0.3,
             f"{avg:.1f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")

ax2.set_ylabel("Average CAGR (%) across 20 starts", fontsize=11)
ax2.set_title("Average CAGR by Strategy (±1 std dev across 20 quarterly starts)",
              fontsize=13, fontweight="bold")
ax2.set_xticklabels(strat_names, rotation=15, ha="right", fontsize=9)
ax2.grid(axis="y", alpha=0.3, zorder=0)
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))

plt.tight_layout(pad=2.5)
png_path = "report/img/alternatives_quarterly.png"
plt.savefig(png_path, dpi=150, bbox_inches="tight")
print(f"\nChart saved → {png_path}")

# ── Save summary text ─────────────────────────────────────────────────────────
txt_path = "/home/ubuntu/projects/investor/alternatives_summary.txt"
with open(txt_path, "w") as f:
    f.write("ALTERNATIVES QUARTERLY DCA ANALYSIS\n")
    f.write(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d')}\n")
    f.write(f"Period: 20 quarterly starts 2020-Q1 → 2024-Q4, end {end_date.date()}\n\n")

    f.write("=" * 80 + "\n")
    f.write("STRATEGY SUMMARY\n")
    f.write("=" * 80 + "\n")
    f.write(f"{'Strategy':<22} {'Beats VOO':>10} {'Avg CAGR':>10} "
            f"{'Avg CAGR gap':>14} {'Avg Max DD':>11} {'Avg Sharpe':>11}\n")
    f.write("-" * 80 + "\n")
    for strat in strategies:
        d = summary_data[strat]
        f.write(f"{strat:<22} {d['beats']:>10}/20 {d['avg_cagr']:>10.2%} "
                f"{d['avg_gap']:>+14.2%} {d['avg_dd']:>11.2%} {d['avg_sh']:>11.2f}\n")

    f.write("\n" + "=" * 80 + "\n")
    f.write("FULL DETAIL TABLE\n")
    f.write("=" * 80 + "\n")
    for strat in strategies:
        sub = df[df["Strategy"] == strat]
        f.write(f"\n--- {strat} ---\n")
        f.write(f"{'Start':<12} {'CAGR':>8} {'Max DD':>9} {'Sharpe':>8} "
                f"{'Total Ret':>11} {'vs VOO DCA':>11}\n")
        for _, row in sub.iterrows():
            f.write(f"{row['Start']:<12} {row['CAGR']:>8.2%} {row['Max DD']:>9.2%} "
                    f"{row['Sharpe']:>8.2f} {row['Total Ret']:>11.2%} "
                    f"{row['vs VOO DCA']:>+11.2%}\n")

    f.write("\n" + "=" * 80 + "\n")
    f.write("KEY FINDINGS\n")
    f.write("=" * 80 + "\n")
    f.write(f"Best alternative:  {best}  (avg CAGR gap {summary_data[best]['avg_gap']:+.2%})\n")
    f.write(f"Worst alternative: {worst}  (avg CAGR gap {summary_data[worst]['avg_gap']:+.2%})\n")
    f.write(f"Gold hedge drawdown improvement: {dd_delta:+.2%}\n")
    f.write(f"60/40 DCA beat VOO: {sixty_beats}/20 starts, avg gap {sixty_gap:+.2%}\n")
    f.write(f"Degen DCA beat VOO: {degen_beats}/20 starts, avg gap {degen_gap:+.2%}\n")

print(f"Summary saved  → {txt_path}")
