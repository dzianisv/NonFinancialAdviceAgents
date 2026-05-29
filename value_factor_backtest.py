"""
Morningstar-proxy undervalued stock picking backtest.
Uses price-based valuation proxies on S&P 500 large-caps, 2020-2026.
"""

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime

# Universe
TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "BRK-B", "UNH", "JNJ",
    "V", "MA", "PG", "HD", "KO", "PEP", "COST", "MRK", "ABBV", "LLY",
    "AVGO", "TMO", "ACN", "ADBE", "CRM", "NFLX", "AMD", "QCOM", "TXN", "HON",
    "LOW", "UNP", "CAT", "DE", "GE", "RTX", "LMT", "BA", "IBM", "INTC",
    "CSCO", "WMT", "DIS", "CMCSA", "VZ", "T", "PFE", "BMY", "GILD", "AMGN",
    "MDT", "CVX", "XOM", "COP", "SLB", "NEE", "SO", "DUK", "GS", "JPM",
]

START = "2019-01-01"  # extra year for lookback
END = "2026-05-27"
BACKTEST_START = "2020-01-01"
CAPITAL = 1_000_000
TOP_N = 15
RF_RATE = 0.04


def download_data():
    """Download price data for universe + SPY."""
    tickers = TICKERS + ["SPY"]
    print(f"Downloading {len(tickers)} tickers...")
    data = yf.download(tickers, start=START, end=END, auto_adjust=True, progress=False)
    prices = data["Close"].copy()
    # Drop tickers with too much missing data
    prices = prices.dropna(axis=1, thresh=int(len(prices) * 0.8))
    prices = prices.ffill().bfill()
    print(f"Got data for {prices.shape[1]} tickers, {prices.shape[0]} days")
    return prices


def compute_signals(prices, date, spy_col="SPY"):
    """Compute valuation signals for all stocks on a given date using only past data."""
    loc = prices.index.get_loc(date)
    if loc < 252:
        return None

    stock_cols = [c for c in prices.columns if c != spy_col]
    signals = {}

    for ticker in stock_cols:
        p = prices[ticker].iloc[:loc + 1]
        spy = prices[spy_col].iloc[:loc + 1]

        if len(p) < 252 or p.iloc[-1] != p.iloc[-1]:
            continue

        current = p.iloc[-1]
        high_252 = p.iloc[-252:].max()
        low_252 = p.iloc[-252:].min()

        # Distance from 52-week high (0=at high, -1=at low)
        if high_252 == low_252:
            dist_from_high = 0.0
        else:
            dist_from_high = (current - high_252) / high_252  # negative = cheaper

        # 12-month relative performance vs SPY
        if len(p) >= 252 and len(spy) >= 252:
            ret_12m = current / p.iloc[-252] - 1
            spy_ret_12m = spy.iloc[-1] / spy.iloc[-252] - 1
            rel_perf_12m = ret_12m - spy_ret_12m
        else:
            rel_perf_12m = 0.0

        # 1-month momentum (approx 21 trading days)
        if len(p) >= 21:
            mom_1m = current / p.iloc[-21] - 1
        else:
            mom_1m = 0.0

        # 60-day realized volatility
        if len(p) >= 60:
            rets = p.iloc[-60:].pct_change().dropna()
            vol_60d = rets.std() * np.sqrt(252)
        else:
            vol_60d = 1.0

        signals[ticker] = {
            "dist_from_high": dist_from_high,
            "rel_perf_12m": rel_perf_12m,
            "mom_1m": mom_1m,
            "vol_60d": vol_60d,
        }

    return pd.DataFrame(signals).T


def select_variant_a(signals_df):
    """Pure Contrarian Value: lowest dist_from_high + worst relative perf."""
    df = signals_df.copy()
    # Rank: lower dist_from_high = more beaten down (rank ascending, lower rank = more beaten)
    df["rank_dist"] = df["dist_from_high"].rank(ascending=True)
    # Rank: more negative rel_perf = more undervalued
    df["rank_rel"] = df["rel_perf_12m"].rank(ascending=True)
    # Quality filter: prefer lower vol
    df["rank_vol"] = df["vol_60d"].rank(ascending=True)
    # Composite (lower = more undervalued)
    df["composite"] = df["rank_dist"] * 0.4 + df["rank_rel"] * 0.4 + df["rank_vol"] * 0.2
    return df.nsmallest(TOP_N, "composite").index.tolist()


def select_variant_b(signals_df):
    """Value + Momentum confirmation: lower half of 52-week range + positive 1-month mom."""
    df = signals_df.copy()
    # Filter: in lower half of range (dist_from_high < median)
    median_dist = df["dist_from_high"].median()
    cheap = df[df["dist_from_high"] <= median_dist].copy()
    # Filter: positive 1-month momentum (catching the turn)
    turning = cheap[cheap["mom_1m"] > 0].copy()
    if len(turning) < TOP_N:
        # Relax: take those with least negative momentum
        turning = cheap.nlargest(TOP_N, "mom_1m")
    # Rank by momentum strength + low vol
    turning["rank_mom"] = turning["mom_1m"].rank(ascending=False)
    turning["rank_vol"] = turning["vol_60d"].rank(ascending=True)
    turning["composite"] = turning["rank_mom"] * 0.6 + turning["rank_vol"] * 0.4
    return turning.nsmallest(TOP_N, "composite").index.tolist()


def backtest(prices, select_fn):
    """Run monthly rebalance backtest."""
    bt_prices = prices.loc[BACKTEST_START:]
    # Get month-end dates
    monthly_dates = bt_prices.resample("M").last().index
    # Map to actual trading days
    rebal_dates = []
    for d in monthly_dates:
        mask = bt_prices.index <= d
        if mask.any():
            rebal_dates.append(bt_prices.index[mask][-1])

    portfolio_value = [CAPITAL]
    dates = [rebal_dates[0]]
    holdings = []
    turnover_list = []

    for i in range(len(rebal_dates) - 1):
        rebal_date = rebal_dates[i]
        next_date = rebal_dates[i + 1]

        # Compute signals
        signals_df = compute_signals(prices, rebal_date)
        if signals_df is None or len(signals_df) < TOP_N:
            # Hold cash
            portfolio_value.append(portfolio_value[-1])
            dates.append(next_date)
            continue

        # Select stocks
        picks = select_fn(signals_df)
        if len(picks) == 0:
            portfolio_value.append(portfolio_value[-1])
            dates.append(next_date)
            continue

        # Compute turnover
        if holdings:
            new_set = set(picks)
            old_set = set(holdings)
            turnover = len(new_set - old_set) / TOP_N
        else:
            turnover = 1.0
        turnover_list.append(turnover)
        holdings = picks

        # Compute equal-weight return over the month
        period_prices = bt_prices.loc[rebal_date:next_date]
        if len(period_prices) < 2:
            portfolio_value.append(portfolio_value[-1])
            dates.append(next_date)
            continue

        valid_picks = [p for p in picks if p in period_prices.columns]
        if not valid_picks:
            portfolio_value.append(portfolio_value[-1])
            dates.append(next_date)
            continue

        start_prices = period_prices[valid_picks].iloc[0]
        end_prices = period_prices[valid_picks].iloc[-1]
        returns = (end_prices / start_prices - 1).mean()
        new_val = portfolio_value[-1] * (1 + returns)
        portfolio_value.append(new_val)
        dates.append(next_date)

    equity = pd.Series(portfolio_value, index=dates)
    avg_turnover = np.mean(turnover_list) if turnover_list else 0
    return equity, avg_turnover


def compute_metrics(equity, rf=RF_RATE):
    """Compute CAGR, Sharpe, Max Drawdown."""
    total_days = (equity.index[-1] - equity.index[0]).days
    years = total_days / 365.25
    cagr = (equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1

    monthly_rets = equity.pct_change().dropna()
    excess = monthly_rets - rf / 12
    sharpe = excess.mean() / monthly_rets.std() * np.sqrt(12) if monthly_rets.std() > 0 else 0

    cummax = equity.cummax()
    drawdown = (equity - cummax) / cummax
    max_dd = drawdown.min()

    return cagr, sharpe, max_dd


def main():
    prices = download_data()

    print("\nRunning Variant A (Pure Contrarian Value)...")
    eq_a, turn_a = backtest(prices, select_variant_a)

    print("Running Variant B (Value + Momentum Confirmation)...")
    eq_b, turn_b = backtest(prices, select_variant_b)

    # SPY benchmark
    spy_prices = prices["SPY"].loc[BACKTEST_START:]
    spy_monthly = spy_prices.resample("M").last()
    spy_equity = CAPITAL * spy_monthly / spy_monthly.iloc[0]

    # Metrics
    cagr_a, sharpe_a, dd_a = compute_metrics(eq_a)
    cagr_b, sharpe_b, dd_b = compute_metrics(eq_b)
    cagr_spy, sharpe_spy, dd_spy = compute_metrics(spy_equity)

    print("\n" + "=" * 70)
    print("MORNINGSTAR-PROXY VALUE FACTOR BACKTEST RESULTS")
    print("=" * 70)
    print(f"Period: {BACKTEST_START} to {END} | Capital: ${CAPITAL:,.0f} | Top {TOP_N} stocks | Monthly rebalance")
    print("-" * 70)
    print(f"{'Metric':<20} {'Variant A (Contrarian)':<25} {'Variant B (Val+Mom)':<25} {'SPY Benchmark':<20}")
    print("-" * 70)
    print(f"{'CAGR':<20} {cagr_a:>20.2%}      {cagr_b:>20.2%}      {cagr_spy:>15.2%}")
    print(f"{'Sharpe Ratio':<20} {sharpe_a:>20.2f}      {sharpe_b:>20.2f}      {sharpe_spy:>15.2f}")
    print(f"{'Max Drawdown':<20} {dd_a:>20.2%}      {dd_b:>20.2%}      {dd_spy:>15.2%}")
    print(f"{'Final Value':<20} ${eq_a.iloc[-1]:>18,.0f}      ${eq_b.iloc[-1]:>18,.0f}      ${spy_equity.iloc[-1]:>13,.0f}")
    print(f"{'Avg Turnover/Mo':<20} {turn_a:>20.1%}      {turn_b:>20.1%}      {'0.0%':>15}")
    print("=" * 70)

    # Plot
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(eq_a.index, eq_a.values, label="Variant A (Pure Contrarian)", linewidth=1.5)
    ax.plot(eq_b.index, eq_b.values, label="Variant B (Value + Momentum)", linewidth=1.5)
    ax.plot(spy_equity.index, spy_equity.values, label="SPY Benchmark", linewidth=1.5, linestyle="--", color="gray")
    ax.set_title("Morningstar-Proxy Value Factor Backtest (2020-2026)")
    ax.set_ylabel("Portfolio Value ($)")
    ax.set_xlabel("Date")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))
    plt.tight_layout()
    plt.savefig("report/img/value_factor_backtest.png", dpi=150)
    print("\nChart saved to value_factor_backtest.png")


if __name__ == "__main__":
    main()
