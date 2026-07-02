"""
Dummy strategy for smoke-testing the bot runner end-to-end — NOT a trading strategy.

Contract (see intraday-bot/README.md / core/gate.py):
    signals(df_dict, params) -> pd.Series | dict[str, pd.Series] of target position weights
    in [-1, 1] (or notional-fraction), indexed by bar, decided on PRIOR bar close only.

This strategy alternates a small long exposure using only `df["close"].shift(1)` so the
runner has something non-trivial to size into without needing a PASSed gate strategy wired
up yet. It exists purely to prove the runner's fetch -> signal -> diff -> caps -> execute
loop works; it must never be pointed at by a live-mode strategy_ref.
"""
from __future__ import annotations

import pandas as pd


def signals(df_dict: dict, params: dict) -> dict:
    """Target weight = `params['target_weight']` (default 0.5) whenever the PRIOR bar's
    close was above its own 5-bar rolling mean (computed using only data up to and
    including that prior bar), else 0. Uses .shift(1) explicitly so the decision at bar t
    only ever sees data through bar t-1 (prior-bar-close-only contract)."""
    target_weight = params.get("target_weight", 0.5)
    lookback = params.get("lookback", 5)

    out = {}
    for sym, df in df_dict.items():
        prior_close = df["close"].shift(1)
        prior_mean = df["close"].rolling(lookback).mean().shift(1)
        w = (prior_close > prior_mean).astype(float) * target_weight
        w.index = df.index
        out[sym] = w.fillna(0.0)
    return out
