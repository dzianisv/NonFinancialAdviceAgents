#!/usr/bin/env python3
"""
Quality Factor + Low Volatility Stock Picking Strategy Backtest
Period: 2020-01-01 to 2026-05-27
Universe: ~100 S&P 500 large caps
Strategy: Combined 6-month momentum (40%) + 12-month momentum (30%) + low vol rank (30%)
"""

import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from datetime import datetime, timedelta
import time

# ── Config ──────────────────────────────────────────────────────────────────
START_DATE = "2019-07-01"   # extra history for momentum calc
BACKTEST_START = "2020-01-01"
END_DATE = "2026-05-27"
INITIAL_CAPITAL = 1_000_000
RISK_FREE_RATE = 0.04
TOP_N_VARIANTS = [10, 15, 20]

UNIVERSE = [
    "AAPL","MSFT","GOOGL","AMZN","META","NVDA","JPM","V","MA","UNH",
    "JNJ","PG","KO","PEP","COST","HD","LOW","NKE","MCD","SBUX",
    "DIS","NFLX","ADBE","CRM","NOW","INTU","QCOM","AVGO","TXN","AMD",
    "ORCL","IBM","CSCO","INTC","MU","LRCX","AMAT","KLAC","WMT","TGT",
    "AMGN","GILD","BIIB","REGN","LLY","TMO","ABT","MDT","SYK","DHR",
    "BAC","WFC","GS","MS","BLK","SCHW","AXP","MMC","ICE","CME",
    "CVX","XOM","COP","SLB","HAL","NEE","DUK","SO","AEP","D",
    "LIN","APD","ECL","SHW","NEM","FCX","CAT","DE","HON","MMM",
    "GE","RTX","LMT","NOC","BA","UPS","FDX","CSX","UNP","NSC",
]

# ── Download price data ──────────────────────────────────────────────────────
print("Downloading price data...")
all_tickers = UNIVERSE + ["VOO"]

try:
    raw = yf.download(all_tickers, start=START_DATE, end=END_DATE,
                      auto_adjust=True, progress=False)
    prices = raw["Close"].copy()
except Exception as e:
    print(f"Batch download failed ({e}), trying individual tickers...")
    frames = {}
    for tk in all_tickers:
        try:
            d = yf.download(tk, start=START_DATE, end=END_DATE,
                            auto_adjust=True, progress=False)
            if not d.empty:
                frames[tk] = d["Close"]
        except:
            pass
        time.sleep(0.1)
    prices = pd.DataFrame(frames)

# Clean up column names (yfinance sometimes returns MultiIndex)
if isinstance(prices.columns, pd.MultiIndex):
    prices.columns = prices.columns.get_level_values(0)

prices = prices.dropna(axis=1, how="all")
print(f"Got data for {len(prices.columns)} tickers, {len(prices)} days")

# Separate VOO
voo_prices = prices["VOO"].dropna() if "VOO" in prices.columns else None
stock_prices = prices[[c for c in prices.columns if c != "VOO"]]

# ── Helper: compute metrics ──────────────────────────────────────────────────
def compute_metrics(portfolio_values: pd.Series, rf: float = RISK_FREE_RATE):
    rets = portfolio_values.pct_change().dropna()
    n_years = (portfolio_values.index[-1] - portfolio_values.index[0]).days / 365.25
    cagr = (portfolio_values.iloc[-1] / portfolio_values.iloc[0]) ** (1 / n_years) - 1

    ann_ret = rets.mean() * 252
    ann_vol = rets.std() * np.sqrt(252)
    sharpe = (ann_ret - rf) / ann_vol if ann_vol > 0 else 0

    roll_max = portfolio_values.cummax()
    dd = (portfolio_values - roll_max) / roll_max
    max_dd = dd.min()

    return {"CAGR": cagr, "Sharpe": sharpe, "MaxDD": max_dd, "AnnVol": ann_vol}

# ── Build scoring signals on monthly frequency ──────────────────────────────
# Resample to month-end
monthly = stock_prices.resample("M").last()

def score_universe(date_idx: int, monthly_df: pd.DataFrame) -> pd.Series:
    """Score all stocks at a given month-end index."""
    if date_idx < 12:
        return pd.Series(dtype=float)

    current = monthly_df.iloc[date_idx]

    # 6-month momentum
    past6 = monthly_df.iloc[date_idx - 6]
    mom6 = (current / past6 - 1)

    # 12-month momentum
    past12 = monthly_df.iloc[date_idx - 12]
    mom12 = (current / past12 - 1)

    # 252-day realized volatility (use daily prices up to this date)
    date = monthly_df.index[date_idx]
    # find daily prices window
    daily_window = stock_prices.loc[:date].tail(252)
    if len(daily_window) < 60:
        return pd.Series(dtype=float)
    vol252 = daily_window.pct_change().std() * np.sqrt(252)

    # Only score tickers with all three signals available
    common = mom6.index.intersection(mom12.index).intersection(vol252.index)
    mom6 = mom6[common].dropna()
    mom12 = mom12[common].dropna()
    vol252 = vol252[common].dropna()
    common = mom6.index.intersection(mom12.index).intersection(vol252.index)

    if len(common) < 20:
        return pd.Series(dtype=float)

    # Rank (percentile, higher is better)
    r_mom6 = mom6[common].rank(pct=True)
    r_mom12 = mom12[common].rank(pct=True)
    r_lowvol = (1 - vol252[common].rank(pct=True))  # invert: lower vol = higher rank

    score = 0.40 * r_mom6 + 0.30 * r_mom12 + 0.30 * r_lowvol
    return score.sort_values(ascending=False)

# ── Run backtest for a given top-N ──────────────────────────────────────────
def run_backtest(top_n: int):
    capital = INITIAL_CAPITAL
    portfolio_val = {}
    holdings = {}  # ticker -> shares

    backtest_months = [i for i, d in enumerate(monthly.index)
                       if d >= pd.Timestamp(BACKTEST_START)]

    prev_date = pd.Timestamp(BACKTEST_START) - pd.offsets.BDay(1)
    portfolio_val[prev_date] = capital

    for i in backtest_months:
        rebal_date = monthly.index[i]

        # Mark-to-market current holdings at rebal date
        if holdings:
            mtm = 0
            for tk, shares in holdings.items():
                if tk in stock_prices.columns:
                    price_series = stock_prices[tk]
                    # get closest price on or before rebal_date
                    avail = price_series.loc[:rebal_date].dropna()
                    if not avail.empty:
                        mtm += shares * avail.iloc[-1]
            capital = mtm

        portfolio_val[rebal_date] = capital

        # Score and select
        scores = score_universe(i, monthly)
        if scores.empty:
            continue

        selected = scores.head(top_n).index.tolist()
        if not selected:
            continue

        # Get prices on rebal date
        prices_on_date = {}
        for tk in selected:
            if tk in stock_prices.columns:
                avail = stock_prices[tk].loc[:rebal_date].dropna()
                if not avail.empty:
                    prices_on_date[tk] = avail.iloc[-1]

        selected = [tk for tk in selected if tk in prices_on_date]
        if not selected:
            continue

        alloc_per = capital / len(selected)
        holdings = {}
        for tk in selected:
            holdings[tk] = alloc_per / prices_on_date[tk]

    # Final mark-to-market
    final_date = pd.Timestamp(END_DATE)
    if holdings:
        mtm = 0
        for tk, shares in holdings.items():
            if tk in stock_prices.columns:
                avail = stock_prices[tk].loc[:final_date].dropna()
                if not avail.empty:
                    mtm += shares * avail.iloc[-1]
        capital = mtm
    portfolio_val[final_date] = capital

    pv = pd.Series(portfolio_val).sort_index()
    # Daily interpolation for smoother metrics
    pv_daily = pv.reindex(
        pd.date_range(pv.index[0], pv.index[-1], freq="B")
    ).ffill()

    return pv_daily

# ── VOO baseline ────────────────────────────────────────────────────────────
def voo_baseline():
    if voo_prices is None:
        return None
    v = voo_prices.loc[BACKTEST_START:END_DATE].dropna()
    nav = INITIAL_CAPITAL * (v / v.iloc[0])
    return nav

# ── Run all variants ─────────────────────────────────────────────────────────
print("\nRunning backtests...")
results = {}
portfolios = {}

for n in TOP_N_VARIANTS:
    print(f"  Top-{n}...", end=" ", flush=True)
    pv = run_backtest(n)
    # Trim to backtest period
    pv = pv.loc[BACKTEST_START:END_DATE]
    metrics = compute_metrics(pv)
    results[f"Top-{n}"] = metrics
    portfolios[f"Top-{n}"] = pv
    print(f"CAGR={metrics['CAGR']:.1%}  Sharpe={metrics['Sharpe']:.2f}  MaxDD={metrics['MaxDD']:.1%}")

voo_pv = voo_baseline()
if voo_pv is not None:
    voo_metrics = compute_metrics(voo_pv)
    results["VOO"] = voo_metrics
    portfolios["VOO"] = voo_pv
    print(f"  VOO:    CAGR={voo_metrics['CAGR']:.1%}  Sharpe={voo_metrics['Sharpe']:.2f}  MaxDD={voo_metrics['MaxDD']:.1%}")

# ── Print summary table ──────────────────────────────────────────────────────
print("\n" + "="*70)
print(f"{'Strategy':<12} {'CAGR':>8} {'Sharpe':>8} {'Max DD':>8} {'Ann Vol':>8} {'Beats Pelosi?':>14}")
print("-"*70)

PELOSI_CAGR = 0.200
PELOSI_SHARPE = 0.68

for name, m in results.items():
    beats = "YES ✓" if m["CAGR"] > PELOSI_CAGR and m["Sharpe"] > PELOSI_SHARPE else (
            "CAGR only" if m["CAGR"] > PELOSI_CAGR else "No")
    print(f"{name:<12} {m['CAGR']:>7.1%}  {m['Sharpe']:>7.2f}  {m['MaxDD']:>7.1%}  {m['AnnVol']:>7.1%}  {beats:>14}")

print("-"*70)
print(f"{'Pelosi*':<12} {'20.0%':>8} {'0.68':>8} {'-42.7%':>8} {'N/A':>8}  {'baseline':>14}")
print(f"{'VOO*':<12} {'15.6%':>8} {'0.69':>8} {'-27.4%':>8} {'N/A':>8}  {'benchmark':>14}")
print("* Historical reference values")
print("="*70)

# Best variant
strategy_results = {k: v for k, v in results.items() if k != "VOO"}
best_name = max(strategy_results, key=lambda k: strategy_results[k]["CAGR"])
best = strategy_results[best_name]
print(f"\nBest variant: {best_name}")
print(f"  CAGR:    {best['CAGR']:.2%}")
print(f"  Sharpe:  {best['Sharpe']:.3f}")
print(f"  Max DD:  {best['MaxDD']:.2%}")
beats_pelosi = best["CAGR"] > PELOSI_CAGR
beats_sharpe = best["Sharpe"] > PELOSI_SHARPE
print(f"  Beats Pelosi CAGR (20%): {'YES' if beats_pelosi else 'NO'}")
print(f"  Beats Pelosi Sharpe (0.68): {'YES' if beats_sharpe else 'NO'}")

# ── Plot ─────────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(16, 12))
gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.4, wspace=0.35)

colors = {"Top-10": "#2196F3", "Top-15": "#4CAF50", "Top-20": "#FF9800", "VOO": "#9E9E9E"}

# 1. Portfolio value
ax1 = fig.add_subplot(gs[0, :])
for name, pv in portfolios.items():
    pv.plot(ax=ax1, label=name, color=colors.get(name, "black"),
            linewidth=2 if name != "VOO" else 1.5,
            linestyle="--" if name == "VOO" else "-")
ax1.set_title("Portfolio Value (Quality + Momentum + Low Vol Strategy)", fontsize=13, fontweight="bold")
ax1.set_ylabel("Portfolio Value ($)")
ax1.legend(loc="upper left")
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x/1e6:.2f}M"))
ax1.grid(True, alpha=0.3)

# 2. Drawdowns
ax2 = fig.add_subplot(gs[1, :])
for name, pv in portfolios.items():
    dd = (pv - pv.cummax()) / pv.cummax() * 100
    dd.plot(ax=ax2, label=name, color=colors.get(name, "black"),
            linewidth=1.5, linestyle="--" if name == "VOO" else "-")
ax2.fill_between([], [], alpha=0)
ax2.set_title("Drawdown (%)", fontsize=12)
ax2.set_ylabel("Drawdown (%)")
ax2.legend(loc="lower left")
ax2.grid(True, alpha=0.3)

# 3. Bar: CAGR comparison
ax3 = fig.add_subplot(gs[2, 0])
all_names = list(results.keys()) + ["Pelosi*"]
all_cagrs = [results[k]["CAGR"] * 100 for k in results.keys()] + [20.0]
bar_colors = [colors.get(n, "#E91E63") for n in results.keys()] + ["#E91E63"]
bars = ax3.bar(all_names, all_cagrs, color=bar_colors, alpha=0.85, edgecolor="white")
ax3.axhline(20.0, color="red", linestyle="--", linewidth=1.5, label="Pelosi (20%)")
ax3.axhline(15.6, color="gray", linestyle=":", linewidth=1.5, label="VOO (15.6%)")
ax3.set_title("CAGR Comparison (%)", fontsize=12)
ax3.set_ylabel("CAGR (%)")
ax3.legend(fontsize=8)
ax3.grid(True, alpha=0.3, axis="y")
for bar, val in zip(bars, all_cagrs):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
             f"{val:.1f}%", ha="center", va="bottom", fontsize=9)

# 4. Bar: Sharpe comparison
ax4 = fig.add_subplot(gs[2, 1])
all_sharpes = [results[k]["Sharpe"] for k in results.keys()] + [0.68]
bars2 = ax4.bar(all_names, all_sharpes, color=bar_colors, alpha=0.85, edgecolor="white")
ax4.axhline(0.68, color="red", linestyle="--", linewidth=1.5, label="Pelosi (0.68)")
ax4.axhline(0.69, color="gray", linestyle=":", linewidth=1.5, label="VOO (0.69)")
ax4.set_title("Sharpe Ratio Comparison", fontsize=12)
ax4.set_ylabel("Sharpe Ratio")
ax4.legend(fontsize=8)
ax4.grid(True, alpha=0.3, axis="y")
for bar, val in zip(bars2, all_sharpes):
    ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
             f"{val:.2f}", ha="center", va="bottom", fontsize=9)

plt.suptitle("Quality + Momentum + Low Volatility Strategy Backtest (2020–2026)",
             fontsize=15, fontweight="bold", y=1.01)

out_path = "report/img/quality_factor_backtest.png"
plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
print(f"\nChart saved to: {out_path}")
print("Script complete.")
