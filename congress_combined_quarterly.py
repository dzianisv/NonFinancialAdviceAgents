"""
Congress Combined Portfolio: Pelosi + McCaul + Green
Tests across 20 quarterly start dates (Q1-2020 through Q4-2024)
"""

import warnings
warnings.filterwarnings("ignore")

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import timedelta

# ── Trade data ────────────────────────────────────────────────────────────────
ALL_TRADES = [
    ("Pelosi", "AAPL",  "2020-02-28", 500000),
    ("Pelosi", "MSFT",  "2020-02-28", 250000),
    ("Pelosi", "GOOGL", "2020-07-02", 500000),
    ("Pelosi", "TSLA",  "2020-12-18", 500000),
    ("Pelosi", "AAPL",  "2021-01-29", 750000),
    ("Pelosi", "TSLA",  "2021-03-19", 250000),
    ("Pelosi", "NVDA",  "2021-06-18", 500000),
    ("Pelosi", "MSFT",  "2021-10-22", 500000),
    ("Pelosi", "AAPL",  "2022-07-26", 750000),
    ("Pelosi", "NVDA",  "2022-07-26", 1000000),
    ("Pelosi", "AMZN",  "2022-11-17", 250000),
    ("Pelosi", "GOOGL", "2023-03-17", 500000),
    ("Pelosi", "NVDA",  "2023-11-10", 1000000),
    ("Pelosi", "AAPL",  "2024-01-12", 500000),
    ("Pelosi", "MSFT",  "2024-06-14", 250000),
    ("Green",  "XOM",   "2020-03-20", 100000),
    ("Green",  "CVX",   "2020-03-20", 100000),
    ("Green",  "JNJ",   "2020-04-15", 100000),
    ("Green",  "PFE",   "2020-11-09", 200000),
    ("Green",  "MRNA",  "2020-11-09", 200000),
    ("Green",  "SLB",   "2021-06-18", 100000),
    ("Green",  "PFE",   "2021-11-26", 150000),
    ("Green",  "ABBV",  "2022-03-04", 100000),
    ("Green",  "XOM",   "2022-06-10", 200000),
    ("Green",  "CVX",   "2022-06-10", 100000),
    ("Green",  "LLY",   "2023-02-14", 200000),
    ("Green",  "PFE",   "2023-06-21", 100000),
    ("Green",  "XOM",   "2024-01-19", 150000),
    ("McCaul", "GOOGL", "2020-03-18", 500000),
    ("McCaul", "AMZN",  "2020-03-18", 500000),
    ("McCaul", "MSFT",  "2020-03-18", 500000),
    ("McCaul", "META",  "2020-09-03", 250000),
    ("McCaul", "AAPL",  "2021-02-12", 500000),
    ("McCaul", "NVDA",  "2021-06-30", 250000),
    ("McCaul", "META",  "2022-02-04", 500000),
    ("McCaul", "GOOGL", "2022-05-20", 500000),
    ("McCaul", "MSFT",  "2022-10-28", 250000),
    ("McCaul", "AMZN",  "2023-04-28", 500000),
    ("McCaul", "NVDA",  "2023-05-25", 500000),
    ("McCaul", "META",  "2023-10-27", 250000),
    ("McCaul", "AAPL",  "2024-02-16", 500000),
]

# ── Parameters ────────────────────────────────────────────────────────────────
STARTING_CASH   = 1_000_000
CASH_RATE_WEEKLY = 0.04 / 52   # 4% annual cash yield
END_DATE        = "2026-05-27"

TICKERS = ["AAPL","MSFT","GOOGL","TSLA","NVDA","AMZN","META",
           "XOM","CVX","JNJ","PFE","MRNA","SLB","ABBV","LLY","VOO"]

# ── Download prices ───────────────────────────────────────────────────────────
print("Downloading price data...")
raw = yf.download(TICKERS, start="2019-01-01", end="2026-05-28",
                  interval="1wk", auto_adjust=True)["Close"]

# Normalise column names (yfinance sometimes returns tuples)
if isinstance(raw.columns[0], tuple):
    raw.columns = [c[0] for c in raw.columns]

prices = raw.copy()
prices.index = pd.to_datetime(prices.index).tz_localize(None)
prices = prices.sort_index()

print(f"Price data: {prices.index[0].date()} → {prices.index[-1].date()}, "
      f"{len(prices)} weeks, {prices.shape[1]} tickers")


def next_weekly_close(date, price_index):
    """Return the first weekly-close date >= date."""
    candidates = price_index[price_index >= date]
    if len(candidates) == 0:
        return None
    return candidates[0]


def run_portfolio(trades, start_date, end_date, price_df,
                  starting_cash=STARTING_CASH, n_politicians=3):
    """
    Simulate a buy-and-hold portfolio.

    trades        : list of (politician, ticker, trade_date_str, notional)
    start_date    : pd.Timestamp — portfolio inception
    end_date      : pd.Timestamp — last valuation date
    n_politicians : divisor for notional (budget is shared)
    """
    price_idx = price_df.index

    # Build execution schedule
    scheduled = []
    for pol, ticker, td_str, notional in trades:
        trade_date = pd.Timestamp(td_str)
        exec_date  = next_weekly_close(trade_date + timedelta(days=30), price_idx)
        if exec_date is None:
            continue
        if exec_date < start_date:
            continue
        if exec_date > pd.Timestamp(end_date):
            continue
        scheduled.append({
            "politician": pol,
            "ticker": ticker,
            "exec_date": exec_date,
            "notional": notional,
        })

    scheduled.sort(key=lambda x: x["exec_date"])

    # Weekly simulation
    week_dates = price_idx[(price_idx >= start_date) & (price_idx <= pd.Timestamp(end_date))]
    if len(week_dates) == 0:
        return None

    cash      = float(starting_cash)
    holdings  = {}   # ticker -> shares
    portfolio_values = []
    exec_set  = {d["exec_date"]: [] for d in scheduled}
    for d in scheduled:
        exec_set[d["exec_date"]].append(d)

    n_trades = 0
    for wdate in week_dates:
        # Execute any trades due today
        if wdate in exec_set:
            for t in exec_set[wdate]:
                ticker = t["ticker"]
                if ticker not in price_df.columns:
                    continue
                px = price_df.loc[wdate, ticker]
                if pd.isna(px) or px <= 0:
                    continue
                # Position size
                size = min(t["notional"] / n_politicians, cash * 0.10)
                if size <= 0:
                    continue
                shares = size / px
                holdings[ticker] = holdings.get(ticker, 0.0) + shares
                cash -= size
                n_trades += 1

        # Cash earns weekly interest
        cash *= (1 + CASH_RATE_WEEKLY)

        # Mark-to-market
        equity = sum(
            holdings[tk] * price_df.loc[wdate, tk]
            for tk in holdings
            if tk in price_df.columns and not pd.isna(price_df.loc[wdate, tk])
        )
        portfolio_values.append({"date": wdate, "value": cash + equity})

    if not portfolio_values:
        return None

    pv = pd.DataFrame(portfolio_values).set_index("date")["value"]
    return pv, n_trades


def cagr(start_val, end_val, years):
    if years <= 0 or start_val <= 0:
        return np.nan
    return (end_val / start_val) ** (1 / years) - 1


def sharpe(series, rf_weekly=CASH_RATE_WEEKLY):
    """Weekly Sharpe annualised."""
    if len(series) < 4:
        return np.nan
    rets = series.pct_change().dropna()
    excess = rets - rf_weekly
    if excess.std() == 0:
        return np.nan
    return excess.mean() / excess.std() * np.sqrt(52)


# ── VOO benchmark ─────────────────────────────────────────────────────────────
def voo_portfolio(start_date, end_date, price_df, starting_cash=STARTING_CASH):
    """Buy VOO at the first available date and hold."""
    price_idx = price_df.index
    week_dates = price_idx[(price_idx >= start_date) & (price_idx <= pd.Timestamp(end_date))]
    if len(week_dates) == 0:
        return None
    px0 = price_df.loc[week_dates[0], "VOO"]
    if pd.isna(px0) or px0 <= 0:
        return None
    shares = starting_cash / px0
    vals = []
    cash = 0.0
    for wd in week_dates:
        px = price_df.loc[wd, "VOO"]
        if pd.isna(px):
            continue
        vals.append({"date": wd, "value": shares * px + cash})
        cash *= (1 + CASH_RATE_WEEKLY)
    if not vals:
        return None
    return pd.DataFrame(vals).set_index("date")["value"]


# ── McCaul-only portfolio (for comparison) ────────────────────────────────────
MCCAUL_TRADES = [t for t in ALL_TRADES if t[0] == "McCaul"]


# ── Main loop ─────────────────────────────────────────────────────────────────
starts = pd.date_range("2020-01-01", "2024-10-01", freq="QS")  # 20 dates
end_dt = pd.Timestamp(END_DATE)

results = []
pv_q1   = {}   # store Q1-2020 time series for right panel

print("\nRunning 20 quarterly backtests...\n")

for start in starts:
    years = (end_dt - start).days / 365.25

    # Combined portfolio (all three politicians)
    res_combined = run_portfolio(ALL_TRADES, start, end_dt, prices,
                                  n_politicians=3)
    # McCaul-only portfolio
    res_mccaul   = run_portfolio(MCCAUL_TRADES, start, end_dt, prices,
                                  n_politicians=1)
    # VOO benchmark
    pv_voo = voo_portfolio(start, end_dt, prices)

    if res_combined is None or pv_voo is None:
        continue

    pv_comb, n_trades_comb = res_combined
    pv_mc,   n_trades_mc   = res_mccaul if res_mccaul else (None, 0)

    cagr_combined = cagr(STARTING_CASH, pv_comb.iloc[-1], years)
    cagr_mccaul   = cagr(STARTING_CASH, pv_mc.iloc[-1],   years) if pv_mc is not None else np.nan
    cagr_voo      = cagr(STARTING_CASH, pv_voo.iloc[-1],  years)

    beats_voo     = "YES" if cagr_combined > cagr_voo else "no"

    sharpe_combined = sharpe(pv_comb)
    sharpe_mccaul   = sharpe(pv_mc)   if pv_mc is not None else np.nan
    sharpe_voo      = sharpe(pv_voo)

    results.append({
        "start":          start,
        "cagr_combined":  cagr_combined,
        "cagr_mccaul":    cagr_mccaul,
        "cagr_voo":       cagr_voo,
        "beats_voo":      beats_voo,
        "n_trades":       n_trades_comb,
        "sharpe_combined":sharpe_combined,
        "sharpe_mccaul":  sharpe_mccaul,
        "sharpe_voo":     sharpe_voo,
        "pv_combined":    pv_comb,
        "pv_mccaul":      pv_mc,
        "pv_voo":         pv_voo,
    })

    if start == pd.Timestamp("2020-01-01"):
        pv_q1["combined"] = pv_comb
        pv_q1["mccaul"]   = pv_mc
        pv_q1["voo"]      = pv_voo

df = pd.DataFrame(results)

# ── Print table ───────────────────────────────────────────────────────────────
header = (f"{'Start':<12} {'Combined':>10} {'McCaul':>10} {'VOO':>8} "
          f"{'Beats VOO':>10} {'N trades':>8}")
sep = "-" * len(header)

print(sep)
print(header)
print(sep)

for _, row in df.iterrows():
    print(f"{row['start'].strftime('%Y-%m-%d'):<12} "
          f"{row['cagr_combined']:>9.1%} "
          f"{row['cagr_mccaul']:>9.1%} "
          f"{row['cagr_voo']:>7.1%} "
          f"{row['beats_voo']:>10} "
          f"{int(row['n_trades']):>8}")

print(sep)

# ── Summary averages ──────────────────────────────────────────────────────────
avg_combined = df["cagr_combined"].mean()
avg_mccaul   = df["cagr_mccaul"].mean()
avg_voo      = df["cagr_voo"].mean()
n_beats      = (df["beats_voo"] == "YES").sum()
n_mc_beats   = (df["cagr_mccaul"] > df["cagr_voo"]).sum()

avg_sharpe_combined = df["sharpe_combined"].mean()
avg_sharpe_mccaul   = df["sharpe_mccaul"].mean()
avg_sharpe_voo      = df["sharpe_voo"].mean()

print(f"\n{'SUMMARY AVERAGES':}")
print(f"  Avg Combined CAGR : {avg_combined:.1%}")
print(f"  Avg McCaul   CAGR : {avg_mccaul:.1%}")
print(f"  Avg VOO      CAGR : {avg_voo:.1%}")
print(f"\n  Combined beats VOO: {n_beats}/20 quarters")
print(f"  McCaul   beats VOO: {n_mc_beats}/20 quarters")
print(f"\n  Avg Sharpe — Combined : {avg_sharpe_combined:.2f}")
print(f"  Avg Sharpe — McCaul   : {avg_sharpe_mccaul:.2f}")
print(f"  Avg Sharpe — VOO      : {avg_sharpe_voo:.2f}")

# ── Answering the key questions ───────────────────────────────────────────────
print("\n" + "=" * 60)
print("KEY FINDINGS")
print("=" * 60)

if n_beats > 14:
    beat_str = f"IMPROVES: {n_beats}/20 vs McCaul-alone 14/20"
elif n_beats == 14:
    beat_str = f"SAME: {n_beats}/20 — combining neither improves nor hurts vs-VOO win rate"
else:
    beat_str = f"HURTS: {n_beats}/20 vs McCaul-alone 14/20"
print(f"Combined vs McCaul alone (beats VOO): {beat_str}")

if avg_sharpe_combined > avg_sharpe_mccaul:
    sharpe_str = f"IMPROVES Sharpe ({avg_sharpe_combined:.2f} vs McCaul {avg_sharpe_mccaul:.2f})"
else:
    sharpe_str = f"HURTS Sharpe ({avg_sharpe_combined:.2f} vs McCaul {avg_sharpe_mccaul:.2f})"
print(f"Sharpe effect of combining: {sharpe_str}")

if avg_combined < avg_mccaul:
    drag_str = (f"YES — Green's energy/pharma trades drag combined CAGR "
                f"({avg_combined:.1%}) below McCaul alone ({avg_mccaul:.1%})")
else:
    drag_str = (f"NO — combined actually edges out McCaul alone "
                f"({avg_combined:.1%} vs {avg_mccaul:.1%})")
print(f"Does Green's energy drag dilute results? {drag_str}")


# ── Plotting ──────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(16, 7))
fig.suptitle("Congress Combined Portfolio: Pelosi + McCaul + Green", fontsize=14, fontweight="bold")

# ── Left panel: grouped bar chart ─────────────────────────────────────────────
ax = axes[0]
x     = np.arange(len(df))
width = 0.26
labels = [r["start"].strftime("%Y-Q%q") if hasattr(r["start"], 'quarter')
          else r["start"].strftime("%y-Q") + str((r["start"].month - 1) // 3 + 1)
          for _, r in df.iterrows()]
labels = [f"Q{(s.month-1)//3+1}'{s.strftime('%y')}" for s in df["start"]]

bars1 = ax.bar(x - width, df["cagr_combined"] * 100, width, label="Combined", color="#2196F3", alpha=0.85)
bars2 = ax.bar(x,          df["cagr_mccaul"]  * 100, width, label="McCaul",   color="#FF9800", alpha=0.85)
bars3 = ax.bar(x + width,  df["cagr_voo"]     * 100, width, label="VOO",      color="#4CAF50", alpha=0.85)

ax.set_xlabel("Portfolio Start Quarter")
ax.set_ylabel("CAGR (%)")
ax.set_title("CAGR by Start Quarter (Combined vs McCaul vs VOO)")
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
ax.legend()
ax.axhline(0, color="black", linewidth=0.5)
ax.grid(axis="y", alpha=0.3)

# ── Right panel: Q1-2020 portfolio value over time ────────────────────────────
ax2 = axes[1]
if pv_q1:
    if "combined" in pv_q1 and pv_q1["combined"] is not None:
        ax2.plot(pv_q1["combined"].index, pv_q1["combined"] / 1e6,
                 label="Combined (all 3)", color="#2196F3", linewidth=2)
    if "mccaul" in pv_q1 and pv_q1["mccaul"] is not None:
        ax2.plot(pv_q1["mccaul"].index, pv_q1["mccaul"] / 1e6,
                 label="McCaul only",     color="#FF9800", linewidth=2, linestyle="--")
    if "voo" in pv_q1 and pv_q1["voo"] is not None:
        ax2.plot(pv_q1["voo"].index, pv_q1["voo"] / 1e6,
                 label="VOO",             color="#4CAF50", linewidth=2, linestyle=":")

ax2.set_xlabel("Date")
ax2.set_ylabel("Portfolio Value ($M)")
ax2.set_title("Portfolio Value — Q1-2020 Start")
ax2.legend()
ax2.grid(alpha=0.3)
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"${v:.1f}M"))

plt.tight_layout()
png_path = "report/img/congress_combined_quarterly.png"
plt.savefig(png_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nChart saved: {png_path}")

# ── Save summary text ─────────────────────────────────────────────────────────
txt_path = "/home/ubuntu/projects/investor/congress_combined_summary.txt"
lines = []
lines.append("Congress Combined Portfolio Analysis")
lines.append("Pelosi + McCaul + Green | $1M start | 20 quarterly starts")
lines.append("=" * 60)
lines.append(f"{'Start':<12} {'Combined':>10} {'McCaul':>10} {'VOO':>8} {'Beats?':>8} {'Trades':>7}")
lines.append("-" * 60)
for _, row in df.iterrows():
    lines.append(
        f"{row['start'].strftime('%Y-%m-%d'):<12} "
        f"{row['cagr_combined']:>9.1%} "
        f"{row['cagr_mccaul']:>9.1%} "
        f"{row['cagr_voo']:>7.1%} "
        f"{row['beats_voo']:>8} "
        f"{int(row['n_trades']):>7}"
    )
lines.append("-" * 60)
lines.append(f"{'AVERAGE':<12} {avg_combined:>9.1%} {avg_mccaul:>9.1%} {avg_voo:>7.1%}")
lines.append("")
lines.append(f"Combined beats VOO: {n_beats}/20 quarters")
lines.append(f"McCaul-only beats VOO: {n_mc_beats}/20 quarters")
lines.append(f"Avg Sharpe — Combined : {avg_sharpe_combined:.2f}")
lines.append(f"Avg Sharpe — McCaul   : {avg_sharpe_mccaul:.2f}")
lines.append(f"Avg Sharpe — VOO      : {avg_sharpe_voo:.2f}")
lines.append("")
lines.append("KEY FINDINGS")
lines.append(beat_str)
lines.append(sharpe_str)
lines.append(drag_str)

with open(txt_path, "w") as f:
    f.write("\n".join(lines))
print(f"Summary saved: {txt_path}")
