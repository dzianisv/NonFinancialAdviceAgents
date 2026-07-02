"""
REGIME-SMA — the June `backtests/daytrade/README.md` "still-open hypothesis": does the
drawdown-control value of BTC>200d-SMA regime timing survive an HONEST maker-fill
simulation (trade-through fills, adverse selection, no-fill skips, delayed-fill stress),
not just a cheaper flat taker/maker rate?

Signal only — no execution logic here. The harness (core/gate.py for the flat-cost gate
path, core/fills.py for the maker-fill-sim report) owns all fills/costs.

Rule: long (weight=1.0) when PRIOR bar's close > PRIOR SMA(N) of close, else flat (0.0).
`sma_window` (N) is the only tunable parameter: 200 (headline, matches "REGIME-SMA
(BTC>200d)" naming) and 50 (the June-tested N=50 variant), per symbol (BTC primary,
ETH secondary).

Prior-bar-close-only: the signal at bar t uses close[t-1] and SMA computed over
close[..t-1] (rolling window ending at t-1), then the WHOLE resulting series is shifted
by one more bar so the position is only ever known as of the START of bar t (the
contractual "decided on prior bar close" timing the harness's canary checks for).
"""
from __future__ import annotations

import pandas as pd


def signals(df_dict: dict, params: dict) -> dict:
    """params: {"sma_window": int}. Returns {symbol: pd.Series} of target position
    (1.0 = long, 0.0 = flat), indexed to each df's bars, decided using only data
    strictly before the bar it applies to (prior-bar-close contract)."""
    window = int(params.get("sma_window", 200))
    out = {}
    for sym, df in df_dict.items():
        close = df["close"]
        sma = close.rolling(window=window, min_periods=window).mean()
        # raw regime flag computed AS OF each bar's own close (uses bar t's own close/sma[t])
        raw_long = (close > sma).astype(float)
        # shift by 1: position entering bar t is decided using info available at the CLOSE
        # of bar t-1 only (close[t-1] vs sma[t-1]) -- never bar t's own close.
        pos = raw_long.shift(1).fillna(0.0)
        out[sym] = pos
    return out


PARAM_GRID = [
    {"sma_window": 200},  # headline REGIME-SMA (BTC>200d), matches June naming
    {"sma_window": 50},   # June-tested N=50 variant
]
