#!/usr/bin/env python3
"""
Price layer for the backtest — so directional assets (ETH/BTC/SOL) earn price return, not just yield.

Without this, the simulator counts only lending/staking APY and the directional sleeve looks like pure
drag (its upside is invisible) — the mirror of how a yield-only model hides tail risk. Fetches daily
USD prices via yfinance and writes per-kind month-start prices to data/prices.json keyed by the
simulator's grid (first-of-month).

Run: /Users/engineer/.venv/bin/python3 crypto/backtest/fetch_prices.py
"""
import json
import os

import yfinance as yf

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
START, END = "2024-06-01", "2026-06-15"
KIND_TICKER = {"eth": "ETH-USD", "btc": "BTC-USD", "sol": "SOL-USD"}


def month_starts(start, end):
    y, m = int(start[:4]), int(start[5:7])
    out = []
    while f"{y:04d}-{m:02d}-01" <= end:
        out.append(f"{y:04d}-{m:02d}-01")
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return out


def main():
    os.makedirs(DATA, exist_ok=True)
    grid = month_starts("2024-07-01", "2026-05-01")
    out = {}
    for kind, ticker in KIND_TICKER.items():
        df = yf.download(ticker, start=START, end=END, interval="1d",
                         auto_adjust=True, progress=False)
        if df.empty:
            print(f"  ! {ticker}: no data"); continue
        close = df["Close"]
        # yfinance may return a single-col DataFrame; squeeze to Series
        if hasattr(close, "columns"):
            close = close.iloc[:, 0]
        # date -> price, ISO strings
        series = {d.strftime("%Y-%m-%d"): float(v) for d, v in close.items()}
        dates = sorted(series)
        prices = {}
        for g in grid:
            # nearest available trading day on/before g (else first after)
            le = [d for d in dates if d <= g]
            key = le[-1] if le else dates[0]
            prices[g] = series[key]
        out[kind] = prices
        lo, hi = prices[grid[0]], prices[grid[-1]]
        print(f"  {kind:4} {ticker:8} {grid[0]} ${lo:,.0f} → {grid[-1]} ${hi:,.0f}  ({(hi/lo-1)*100:+.0f}%)")
    with open(os.path.join(DATA, "prices.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(f"wrote {DATA}/prices.json")


if __name__ == "__main__":
    main()
