"""
meanrev_maker — intraday limit-order mean-reversion, designed to EARN the spread.

Thesis: on 5m bars, price occasionally dips k standard deviations below a short rolling
mean/VWAP. We rest a BUY LIMIT at that dip level (a maker order, so we are the counterparty
providing liquidity to impatient taker flow paying for immediacy) rather than chasing with a
market order. If filled, we rest a SELL LIMIT back at the rolling mean (again maker) with a
timeout; if the mean-reversion doesn't happen in time we exit at market (taker). A hard stop
(taker) caps the loss if price keeps falling instead of reverting.

SIGNAL LOGIC ONLY. This module outputs a TARGET POSITION series per bar, decided using ONLY
prior-bar-close information (rolling mean/std computed on `close`, then shifted +1). It does
NOT simulate fills or costs — core/gate.py's run_backtest() owns that for the IS/OOS/walk-
forward/DSR pipeline, and core/fills.py's bar-by-bar simulator is driven separately (see
scripts/run_meanrev_maker_gate.py) for the mandated fill-model report (fill rate, skipped
signals, adverse drift, timeout-to-taker rate).

Because run_backtest() computes turnover-based costs at a single rate controlled by its
`is_maker` flag, and this strategy's entire thesis is paying maker (not taker) fees on both
legs when fills succeed, the gate driver script calls run_backtest(..., is_maker=True) for
this strategy family. That is not cost-loosening: it is correctly using the harness's
existing maker/taker toggle for a maker strategy, at the SAME maker rate (0.15%/side) defined
once in core/costs.py. The separate fill-model report (below) is what tells us whether that
maker assumption is actually earned in practice or is a fantasy once no-fill skips and
timeout-taker exits are honestly counted.

Signal representation for the gate's simplified return-space scoring:
    position in {0, 1} (long-only, no shorts per $500-book house rule) per bar, meaning
    "we intend to be long, entered via a maker dip-buy, held until mean reversion or stop."
    This is necessarily an APPROXIMATION for the gate()'s turnover-cost scoring path (which
    has no concept of no-fill skips) -- the fill-model report is the source of truth for
    whether the approximation is optimistic or conservative, and the report states this
    explicitly (see reports/meanrev_maker.md).

Entry trigger (decided on PRIOR bar close only):
    mean_t   = close.rolling(lookback).mean()      # shifted +1 before use
    std_t    = close.rolling(lookback).std()        # shifted +1 before use
    z_t      = (close - mean_t) / std_t              # shifted +1 before use
    enter when z_{t-1} <= -k  (prior bar closed k std devs below its own rolling mean)

Exit trigger (approximated in the return-space signal as a fixed holding period equal to
    the timeout, since the gate's simplified scorer has no bar-level limit-order state):
    hold until either `timeout_bars` have elapsed OR the position's return has retraced back
    through 0 relative to entry (proxy for "reverted to the mean and exited"), whichever is
    first, then flatten. This is intentionally simple and documented as a proxy: the fill
    simulator (core/fills.py path) is what actually enforces the real limit/timeout/stop
    mechanics bar-by-bar and is the source of truth reported alongside this.

Universe: BTCUSDT, ETHUSDT, SOLUSDT, 5m bars, 2022-01-01 -> now.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Declared config grid (IS-tuning only; every config below counts in n_trials)
# ---------------------------------------------------------------------------
# k: entry deviation, in rolling std devs, below the rolling mean.
# lookback: rolling window (in 5m bars) for the mean/std.
# timeout_bars: bars held before forcing exit (also used by the fill-sim exit timeout).
# stop_k: hard-stop distance, in multiples of the ENTRY deviation (k), i.e. stop at
#         2*k std devs below the rolling mean at entry time (house spec: "hard stop at 2x
#         the entry deviation").
PARAM_GRID = [
    {"lookback": lb, "k": k, "timeout_bars": tb, "stop_k": 2.0}
    for lb in (12, 24, 48)          # 1h, 2h, 4h lookback on 5m bars
    for k in (1.0, 1.5, 2.0)
    for tb in (6, 12, 24)           # 30min, 1h, 2h timeout
]
# 3 * 3 * 3 = 27 configs. This is the FULL declared grid; every one of these 27 is scored
# on IS only, and n_trials=27 is what feeds the deflated Sharpe ratio.


def _zscore(close: pd.Series, lookback: int) -> tuple[pd.Series, pd.Series, pd.Series]:
    mean = close.rolling(lookback, min_periods=lookback).mean()
    std = close.rolling(lookback, min_periods=lookback).std()
    z = (close - mean) / std.replace(0.0, np.nan)
    return mean, std, z


def _single_asset_signal(df: pd.DataFrame, params: dict) -> pd.Series:
    """Target position (0/1, long-only) for one asset, decided on PRIOR bar close only.

    Entry: prior bar's z-score <= -k (a maker dip-buy trigger would have rested there).
    Exit (return-space proxy): hold for `timeout_bars` bars after entry, or until the
    z-score has recovered to >= 0 (proxy for 'reverted to mean'), whichever first, then
    flatten for at least one bar before a new entry can trigger (no pyramiding).
    """
    lookback = params["lookback"]
    k = params["k"]
    timeout_bars = params["timeout_bars"]

    close = df["close"]
    _, _, z = _zscore(close, lookback)
    z_prior = z.shift(1)  # PRIOR bar close only, house rule
    z_vals = z_prior.to_numpy(dtype=float)  # NaN where undefined (pandas NA -> float NaN)

    n = len(df)
    pos = np.zeros(n, dtype=float)

    # Vectorization-friendly state machine: a plain Python loop over a numpy array (not
    # pandas .iloc, which is what was slow) is fast enough for ~500k bars. This is still a
    # sequential state machine (entry/exit depend on prior state), which is inherently
    # non-vectorizable with rolling numpy ops -- but numpy-array indexing instead of
    # pandas .iloc/.notna per-element removes the pandas overhead that dominated runtime.
    in_position = False
    entry_i = -1
    entry_trigger = -float(k)
    for i in range(n):
        zi = z_vals[i]
        has_z = zi == zi  # NaN-safe check (NaN != NaN), faster than pd.notna in a hot loop
        if not in_position:
            if has_z and zi <= entry_trigger:
                in_position = True
                entry_i = i
                pos[i] = 1.0
        else:
            bars_held = i - entry_i
            reverted = has_z and zi >= 0.0
            timed_out = bars_held >= timeout_bars
            if reverted or timed_out:
                in_position = False
            else:
                pos[i] = 1.0
    return pd.Series(pos, index=df.index)


def signals(df_dict: dict, params: dict) -> dict:
    """Strategy interface required by core/gate.py: signals(df_dict, params) -> dict[str, pd.Series]
    of target positions indexed by bar, decided on PRIOR bar close only. Long-only, no shorts
    (house $500-book rule)."""
    out = {}
    for sym, df in df_dict.items():
        out[sym] = _single_asset_signal(df, params)
    return out
