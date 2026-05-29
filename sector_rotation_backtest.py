"""
Sector Rotation / ETF Momentum Rotation Backtest
=================================================
Period: 2020-01-01 to 2026-05-27
Starting capital: $1,000,000
Benchmark: VOO lump sum

Variants:
1. Top 1 sector by 3-month momentum, hold monthly
2. Top 3 sectors by 3-month momentum, equal weight
3. Top 3 sectors by 12-1 month momentum + absolute momentum filter (cash if all negative)
4. Weighted by momentum strength (proportional to return rank)

Risk overlay: If SPY < 200-day SMA, move 50% to cash (BIL)
"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ── Config ──────────────────────────────────────────────────────────────────
START        = "2019-07-01"   # extra history for momentum lookback
TRADE_START  = "2020-01-01"
TRADE_END    = "2026-05-27"
CAPITAL      = 1_000_000
RISK_FREE    = 0.04
REBAL_FREQ = "M"           # month-end

SECTOR_ETFS  = ["XLK","XLF","XLE","XLV","XLC","XLI","XLY","XLP","XLB","XLRE","XLU",
                 "QQQ","SMH","XBI","ARKK","SOXX"]
CASH_ETF     = "BIL"
BENCH_ETF    = "VOO"
SPY_ETF      = "SPY"

ALL_TICKERS  = list(set(SECTOR_ETFS + [CASH_ETF, BENCH_ETF, SPY_ETF]))

# ── Download data ────────────────────────────────────────────────────────────
print("Downloading price data …")
raw = yf.download(ALL_TICKERS, start=START, end=TRADE_END, auto_adjust=True, progress=False)
prices = raw["Close"].ffill()

print(f"  Tickers downloaded: {list(prices.columns)}")
print(f"  Date range: {prices.index[0].date()} → {prices.index[-1].date()}")

# ── Helper: performance metrics ──────────────────────────────────────────────
def metrics(equity: pd.Series, rf: float = RISK_FREE) -> dict:
    eq = equity.dropna()
    if len(eq) < 2:
        return {"CAGR": np.nan, "Sharpe": np.nan, "MaxDD": np.nan}
    n_years = (eq.index[-1] - eq.index[0]).days / 365.25
    cagr    = (eq.iloc[-1] / eq.iloc[0]) ** (1 / n_years) - 1
    daily_r = eq.pct_change().dropna()
    excess  = daily_r - rf / 252
    sharpe  = excess.mean() / excess.std() * np.sqrt(252) if excess.std() > 0 else np.nan
    rolling_max = eq.cummax()
    dd      = (eq / rolling_max - 1)
    max_dd  = dd.min()
    return {"CAGR": cagr, "Sharpe": sharpe, "MaxDD": max_dd}

# ── Monthly rebalancing dates ────────────────────────────────────────────────
trade_prices = prices.loc[TRADE_START:TRADE_END]
rebal_dates  = trade_prices.resample(REBAL_FREQ).last().index

# ── SPY 200-day SMA (computed on full history) ───────────────────────────────
spy_sma200 = prices[SPY_ETF].rolling(200).mean()

# ── Momentum calculators ─────────────────────────────────────────────────────
def momentum_3m(prices_df: pd.DataFrame, date: pd.Timestamp) -> pd.Series:
    """3-month total return ending on `date`."""
    past = date - pd.DateOffset(months=3)
    try:
        p0 = prices_df.loc[:past].iloc[-1]
        p1 = prices_df.loc[date]
        return (p1 / p0 - 1)
    except Exception:
        return pd.Series(np.nan, index=prices_df.columns)

def momentum_12_1(prices_df: pd.DataFrame, date: pd.Timestamp) -> pd.Series:
    """12-1 month momentum (12-month return minus the most recent month)."""
    past12 = date - pd.DateOffset(months=12)
    past1  = date - pd.DateOffset(months=1)
    try:
        p0  = prices_df.loc[:past12].iloc[-1]
        p1  = prices_df.loc[:past1].iloc[-1]
        return (p1 / p0 - 1)
    except Exception:
        return pd.Series(np.nan, index=prices_df.columns)

# ── Generic backtest engine ───────────────────────────────────────────────────
def run_backtest(variant_fn, label: str) -> pd.Series:
    """
    variant_fn(date, sector_prices, spy_sma200) → dict {ticker: weight}
    Returns daily equity series.
    """
    portfolio = pd.Series(dtype=float)
    cash      = CAPITAL
    holdings  = {}   # {ticker: shares}
    equity    = {}

    # daily loop — but only rebalance on rebal_dates
    all_days = trade_prices.index
    rebal_set = set(rebal_dates)

    for i, day in enumerate(all_days):
        # ── Rebalance ──────────────────────────────────────────────────
        if day in rebal_set or i == 0:
            # current portfolio value
            port_val = sum(holdings.get(t, 0) * trade_prices.loc[day, t]
                           for t in holdings if t in trade_prices.columns)
            port_val += cash

            # compute target weights
            weights = variant_fn(day, prices[SECTOR_ETFS], spy_sma200)

            # rebalance
            holdings = {}
            cash = 0.0
            for ticker, w in weights.items():
                if ticker == "CASH":
                    cash += w * port_val
                elif ticker in trade_prices.columns:
                    alloc  = w * port_val
                    price_ = trade_prices.loc[day, ticker]
                    if price_ > 0 and not np.isnan(price_):
                        holdings[ticker] = alloc / price_
                    else:
                        cash += alloc

        # ── Daily mark-to-market ───────────────────────────────────────
        port_val = sum(holdings.get(t, 0) * trade_prices.loc[day, t]
                       for t in holdings if t in trade_prices.columns)
        port_val += cash
        equity[day] = port_val

    return pd.Series(equity, name=label)


# ── Risk overlay helper ───────────────────────────────────────────────────────
def spy_above_200(date: pd.Timestamp) -> bool:
    try:
        spy_price = prices.loc[date, SPY_ETF]
        sma       = spy_sma200.loc[date]
        return spy_price > sma
    except Exception:
        return True   # default: no defensive shift


def apply_risk_overlay(weights: dict, date: pd.Timestamp) -> dict:
    """If SPY < 200-day SMA, move 50% to cash."""
    if not spy_above_200(date):
        adj = {}
        for k, v in weights.items():
            adj[k] = v * 0.5
        adj["CASH"] = adj.get("CASH", 0) + 0.5
        return adj
    return weights


# ══════════════════════════════════════════════════════════════════════════════
# Variant 1 — Top 1 by 3-month momentum
# ══════════════════════════════════════════════════════════════════════════════
def variant1(date, sector_prices, sma200):
    mom = momentum_3m(sector_prices, date)[SECTOR_ETFS].dropna()
    if mom.empty:
        return {"CASH": 1.0}
    winner = mom.idxmax()
    return apply_risk_overlay({winner: 1.0}, date)


# ══════════════════════════════════════════════════════════════════════════════
# Variant 2 — Top 3 by 3-month momentum, equal weight
# ══════════════════════════════════════════════════════════════════════════════
def variant2(date, sector_prices, sma200):
    mom = momentum_3m(sector_prices, date)[SECTOR_ETFS].dropna()
    if mom.empty:
        return {"CASH": 1.0}
    top3 = mom.nlargest(3).index.tolist()
    w    = {t: 1/3 for t in top3}
    return apply_risk_overlay(w, date)


# ══════════════════════════════════════════════════════════════════════════════
# Variant 3 — Top 3 by 12-1 momentum + absolute momentum filter
# ══════════════════════════════════════════════════════════════════════════════
def variant3(date, sector_prices, sma200):
    mom = momentum_12_1(sector_prices, date)[SECTOR_ETFS].dropna()
    if mom.empty:
        return {"CASH": 1.0}
    # absolute momentum: if ALL top-3 are negative, hold cash
    top3 = mom.nlargest(3)
    if (top3 <= 0).all():
        return {"CASH": 1.0}
    positive = top3[top3 > 0]
    if positive.empty:
        return {"CASH": 1.0}
    w = {t: 1/len(positive) for t in positive.index}
    return apply_risk_overlay(w, date)


# ══════════════════════════════════════════════════════════════════════════════
# Variant 4 — Weighted by momentum rank (rank-proportional)
# ══════════════════════════════════════════════════════════════════════════════
def variant4(date, sector_prices, sma200):
    mom = momentum_3m(sector_prices, date)[SECTOR_ETFS].dropna()
    if mom.empty:
        return {"CASH": 1.0}
    top5  = mom.nlargest(5)
    ranks = top5.rank()                      # 1 = lowest, 5 = highest
    total = ranks.sum()
    w     = {t: ranks[t] / total for t in top5.index}
    return apply_risk_overlay(w, date)


# ── Run all variants ──────────────────────────────────────────────────────────
print("\nRunning backtests …")
equities = {}
equities["V1: Top1 3M"    ] = run_backtest(variant1, "V1: Top1 3M")
equities["V2: Top3 3M EW" ] = run_backtest(variant2, "V2: Top3 3M EW")
equities["V3: Top3 12-1+ABS"] = run_backtest(variant3, "V3: Top3 12-1+ABS")
equities["V4: Rank-Weighted"] = run_backtest(variant4, "V4: Rank-Weighted")

# ── VOO benchmark ─────────────────────────────────────────────────────────────
voo = trade_prices[BENCH_ETF].dropna()
voo_equity = CAPITAL * voo / voo.iloc[0]
equities["VOO (lump sum)"] = voo_equity

# ── Results table ─────────────────────────────────────────────────────────────
print("\n" + "="*70)
print(f"{'Strategy':<25} {'CAGR':>8} {'Sharpe':>8} {'MaxDD':>8} {'Final $':>14}")
print("="*70)

results = {}
for name, eq in equities.items():
    m = metrics(eq)
    final = eq.iloc[-1]
    results[name] = m
    results[name]["Final"] = final
    cagr_s   = f"{m['CAGR']*100:>7.1f}%" if not np.isnan(m['CAGR'])   else "   N/A"
    sharpe_s = f"{m['Sharpe']:>7.2f}"    if not np.isnan(m['Sharpe']) else "   N/A"
    mdd_s    = f"{m['MaxDD']*100:>7.1f}%" if not np.isnan(m['MaxDD'])  else "   N/A"
    final_s  = f"${final:>13,.0f}"
    print(f"{name:<25} {cagr_s} {sharpe_s} {mdd_s} {final_s}")

print("="*70)
print(f"  Pelosi baseline: 20.0% CAGR, Sharpe 0.68")
print(f"  McCaul baseline: 28.3% CAGR, Sharpe 0.91")

# ── Beat Pelosi? ──────────────────────────────────────────────────────────────
print("\nBeats Pelosi (20% CAGR)?")
for name, m in results.items():
    if name == "VOO (lump sum)":
        continue
    beats = "YES ✓" if m['CAGR'] > 0.20 else "no"
    print(f"  {name:<25}: CAGR={m['CAGR']*100:.1f}%  → {beats}")

# ── Chart ─────────────────────────────────────────────────────────────────────
print("\nGenerating chart …")
fig = plt.figure(figsize=(16, 10))
gs  = gridspec.GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.3)

colors = {
    "V1: Top1 3M"      : "#e74c3c",
    "V2: Top3 3M EW"   : "#3498db",
    "V3: Top3 12-1+ABS": "#2ecc71",
    "V4: Rank-Weighted": "#f39c12",
    "VOO (lump sum)"   : "#95a5a6",
}

# ── Panel 1: equity curves ────────────────────────────────────────────────────
ax1 = fig.add_subplot(gs[0, :])
for name, eq in equities.items():
    ax1.plot(eq.index, eq / 1e6, label=name, color=colors[name],
             linewidth=2 if "VOO" not in name else 1.5,
             linestyle="--" if "VOO" in name else "-",
             alpha=0.9)
ax1.axhline(1.0, color="gray", linewidth=0.5, linestyle=":")
ax1.set_title("Sector Rotation Strategy — Equity Curves (2020–2026)", fontsize=14, fontweight="bold")
ax1.set_ylabel("Portfolio Value ($M)")
ax1.legend(loc="upper left", fontsize=9)
ax1.grid(True, alpha=0.3)
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:.1f}M"))

# ── Panel 2: bar — CAGR ───────────────────────────────────────────────────────
ax2 = fig.add_subplot(gs[1, 0])
names_  = list(equities.keys())
cagrs   = [results[n]["CAGR"] * 100 for n in names_]
bars    = ax2.bar(range(len(names_)), cagrs,
                  color=[colors[n] for n in names_], alpha=0.85, edgecolor="white")
ax2.axhline(20.0, color="purple",  linewidth=1.5, linestyle="--", label="Pelosi 20%")
ax2.axhline(28.3, color="darkred", linewidth=1.5, linestyle=":",  label="McCaul 28.3%")
ax2.set_xticks(range(len(names_)))
ax2.set_xticklabels([n.replace(" ", "\n") for n in names_], fontsize=7.5)
ax2.set_ylabel("CAGR (%)")
ax2.set_title("CAGR Comparison", fontweight="bold")
ax2.legend(fontsize=8)
ax2.grid(True, alpha=0.3, axis="y")
for bar, v in zip(bars, cagrs):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
             f"{v:.1f}%", ha="center", fontsize=8)

# ── Panel 3: bar — Sharpe ─────────────────────────────────────────────────────
ax3 = fig.add_subplot(gs[1, 1])
sharpes = [results[n]["Sharpe"] for n in names_]
bars3   = ax3.bar(range(len(names_)), sharpes,
                  color=[colors[n] for n in names_], alpha=0.85, edgecolor="white")
ax3.axhline(0.68, color="purple",  linewidth=1.5, linestyle="--", label="Pelosi 0.68")
ax3.axhline(0.91, color="darkred", linewidth=1.5, linestyle=":",  label="McCaul 0.91")
ax3.set_xticks(range(len(names_)))
ax3.set_xticklabels([n.replace(" ", "\n") for n in names_], fontsize=7.5)
ax3.set_ylabel("Sharpe Ratio")
ax3.set_title("Sharpe Ratio Comparison", fontweight="bold")
ax3.legend(fontsize=8)
ax3.grid(True, alpha=0.3, axis="y")
for bar, v in zip(bars3, sharpes):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
             f"{v:.2f}", ha="center", fontsize=8)

fig.suptitle("Sector ETF Momentum Rotation Backtest  |  $1M  |  2020–2026",
             fontsize=15, fontweight="bold", y=1.01)

out_path = "report/img/sector_rotation_backtest.png"
plt.savefig(out_path, dpi=150, bbox_inches="tight")
print(f"Chart saved → {out_path}")
print("\nDone.")
