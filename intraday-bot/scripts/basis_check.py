"""
Basis check: Coinbase BTC/USD + ETH/USD daily closes (via ccxt) vs Binance BTCUSDT/ETHUSDT
daily closes (already downloaded to intraday-bot/data/), over the last 12 months.

We backtest on Binance data but would execute on Alpaca/US venues — this quantifies how
much the Binance price series diverges from what a US venue would actually fill at.
Report: mean absolute % basis per symbol over the last 12 months.

Run: /Users/engineer/.venv/bin/python3 scripts/basis_check.py
"""
import os
import sys
from datetime import datetime, timedelta, timezone

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import data


def fetch_coinbase_daily(symbol: str, since_days: int = 400) -> pd.DataFrame:
    import ccxt
    ex = ccxt.coinbase()
    ex.load_markets()
    if symbol not in ex.markets:
        raise ValueError(f"{symbol} not listed on coinbase")
    since_ms = ex.milliseconds() - since_days * 24 * 3600 * 1000
    rows = []
    ms = since_ms
    tf_ms = 24 * 3600 * 1000
    while True:
        batch = ex.fetch_ohlcv(symbol, "1d", since=ms, limit=300)
        if not batch:
            break
        rows += batch
        new_last = batch[-1][0]
        if new_last <= ms or len(batch) < 300:
            break
        ms = new_last + tf_ms
    df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])
    df = df.drop_duplicates("ts")
    df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    return df.set_index("ts").sort_index()


def basis_for_pair(binance_symbol: str, coinbase_symbol: str, months: int = 12) -> dict:
    cutoff = pd.Timestamp.now(tz="UTC") - pd.DateOffset(months=months)

    b = data.load(binance_symbol, "1d")
    b_close = b["close"]
    b_close.index = b_close.index.normalize()
    b_close = b_close[b_close.index >= cutoff]

    c = fetch_coinbase_daily(coinbase_symbol, since_days=months * 31 + 5)
    c_close = c["close"]
    c_close.index = c_close.index.normalize()
    c_close = c_close[c_close.index >= cutoff]

    merged = pd.concat([b_close.rename("binance"), c_close.rename("coinbase")], axis=1).dropna()
    if merged.empty:
        return {"symbol": binance_symbol, "n_days": 0, "mean_abs_pct_basis": None,
                "note": "no overlapping dates"}

    basis_pct = (merged["coinbase"] - merged["binance"]).abs() / merged["binance"] * 100
    return {
        "symbol": binance_symbol,
        "coinbase_symbol": coinbase_symbol,
        "n_days": len(merged),
        "start": str(merged.index[0].date()),
        "end": str(merged.index[-1].date()),
        "mean_abs_pct_basis": float(basis_pct.mean()),
        "max_abs_pct_basis": float(basis_pct.max()),
        "median_abs_pct_basis": float(basis_pct.median()),
    }


def main():
    results = []
    for b_sym, c_sym in [("BTCUSDT", "BTC/USD"), ("ETHUSDT", "ETH/USD")]:
        try:
            r = basis_for_pair(b_sym, c_sym, months=12)
            results.append(r)
            print(f"{b_sym} vs {c_sym}: mean abs basis = {r['mean_abs_pct_basis']:.4f}%  "
                  f"(median {r['median_abs_pct_basis']:.4f}%, max {r['max_abs_pct_basis']:.4f}%, "
                  f"n={r['n_days']} days, {r['start']}..{r['end']})")
        except Exception as e:
            print(f"{b_sym} vs {c_sym}: FAILED — {e}")
            results.append({"symbol": b_sym, "error": str(e)})
    return results


if __name__ == "__main__":
    main()
