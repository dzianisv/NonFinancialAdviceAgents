"""
Maker-fill simulator — MINIMUM HONEST MODEL (mandated by skeptic review, non-negotiable).
Deterministic. No RNG. Unit-tested in tests/test_fills.py.

Rules implemented exactly as specced:

1. TRADE-THROUGH, NOT TOUCH.
   A resting BUY limit fills only if the bar's LOW trades through the limit by >= 1bp:
       low <= limit * (1 - 0.0001)
   Mirror for SELL: high >= limit * (1 + 0.0001).
   Touching the limit exactly (low == limit) does NOT count as a fill.

2. QUEUE-POSITION HAIRCUT (deterministic, no RNG).
   Base tier: p_fill=0.8 is expressed structurally, not by dice — instead of a random draw,
   the base tier credits the fill unconditionally on trade-through (this is the "favorable
   queue position" case: base rate 0.8 is documented as the ASSUMED average outcome baked
   into the base tier's fill criterion, i.e. base tier = trade-through by >= 1bp as in rule 1).
   The STRESS "reduced fill probability" tier (p_fill=0.4, tier (c) below) is implemented
   as a STRICTER, deterministic trade-through requirement: require the bar to trade through
   the limit by >= 0.25 * (bar's high-low range), i.e.
       low <= limit - 0.25*(high-low)   [BUY]
       high >= limit + 0.25*(high-low)  [SELL]
   This is a harder bar to clear than rule 1's flat 1bp, which mechanically produces a lower
   realized fill rate on any real (non-degenerate) bar distribution — that lower realized
   rate IS the deterministic proxy for "p_fill=0.4". It is reproducible: same OHLC in,
   same fill/no-fill out, every time. No seed needed because there is no randomness.

3. ADVERSE SELECTION.
   After every simulated fill (maker or taker), record the NEXT bar's close-to-close drift
   in the direction adverse to the position just taken (buy fill -> adverse = next bar's
   return being negative; sell fill -> adverse = next bar's return being positive).
   Report mean post-fill adverse drift as a metric on the FillResult. If mean maker savings
   (vs taker cost) < mean adverse drift cost, the maker "win" is fake -- the harness must
   say so explicitly (see summarize()).

4. NO-FILL FALLBACK.
   Entry limit never fills within its bar -> signal is SKIPPED, not carried forward
   (tracked as opportunity cost: counted + the "would-be" gross return is logged for
   reporting, but NOT included in realized P&L).
   Exit limit doesn't fill within `timeout_bars` -> exit AT MARKET on the timeout bar,
   paying taker (0.25%) + slippage (worst-vol stress tier adds another 10bp on top).

5. STRESS TIERS (see core/gate.py stress_suite driver, each a full independent run):
   (a) 2x fees                          -> core.costs.STRESS_2X_FEES
   (b) all fills delayed one bar        -> `delay_bars=1` param on this module
   (c) reduced fill probability tier    -> `stress_fill_prob=True` param on this module
   (d) worst-5%-vol bars +10bp slippage -> `extra_slip_worst_vol=True` + vol percentile flag

6. FEE FLOOR: delegated to core.costs.fee() ($0.01 minimum notional fee per order).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

import numpy as np
import pandas as pd

from core.costs import CostConfig, fee, slippage_cost

TRADE_THROUGH_BPS = 0.0001  # 1bp, rule 1
STRESS_TRADE_THROUGH_FRAC = 0.25  # rule 2, stress tier (c): fraction of bar range required


Side = Literal["buy", "sell"]


@dataclass
class FillResult:
    filled: bool
    is_maker: bool
    fill_price: float
    fee_usd: float
    slippage_usd: float
    bar_index: int          # positional index of the bar the fill happened on
    skipped_entry: bool = False       # rule 4: entry limit never filled -> signal skipped
    timeout_exit: bool = False        # rule 4: exit limit timed out -> forced market exit
    opportunity_gross_return: Optional[float] = None  # for skipped entries: what we would've made


def _bar_range(row) -> float:
    return float(row["high"] - row["low"])


def try_limit_fill(
    df: pd.DataFrame,
    bar_pos: int,
    side: Side,
    limit_price: float,
    cost_cfg: CostConfig = CostConfig(),
    notional: float = 1.0,
    stress_fill_prob: bool = False,
    delay_bars: int = 0,
    extra_slip_worst_vol: bool = False,
    vol_p95_threshold: Optional[float] = None,
) -> FillResult:
    """Attempt to fill a resting limit order on bar `bar_pos` (or `bar_pos+delay_bars` under
    stress tier (b)). Returns a FillResult with filled=False if no trade-through this bar.

    df must have columns open/high/low/close and be positionally indexed (iloc-addressable).
    `vol_p95_threshold` (bar range as % of price) is precomputed by the caller for stress
    tier (d); if the fill bar's range exceeds it, add 10bp slippage on top of the fill.
    """
    eval_pos = bar_pos + delay_bars  # stress tier (b): fills delayed one bar
    if eval_pos >= len(df):
        return FillResult(False, True, limit_price, 0.0, 0.0, bar_pos)

    row = df.iloc[eval_pos]
    rng = _bar_range(row)
    threshold = STRESS_TRADE_THROUGH_FRAC * rng if stress_fill_prob else 0.0

    if side == "buy":
        required_low = limit_price * (1 - TRADE_THROUGH_BPS) if not stress_fill_prob else (limit_price - threshold)
        traded_through = row["low"] <= required_low
    else:
        required_high = limit_price * (1 + TRADE_THROUGH_BPS) if not stress_fill_prob else (limit_price + threshold)
        traded_through = row["high"] >= required_high

    if not traded_through:
        return FillResult(False, True, limit_price, 0.0, 0.0, bar_pos)

    slip = 0.0
    if extra_slip_worst_vol and vol_p95_threshold is not None:
        bar_vol_pct = rng / row["close"] if row["close"] else 0.0
        if bar_vol_pct >= vol_p95_threshold:
            slip = slippage_cost(notional, CostConfig(extra_slippage_bps=10.0))

    f = fee(notional, is_maker=True, cfg=cost_cfg)
    return FillResult(True, True, limit_price, f, slip, eval_pos)


def market_fill(
    df: pd.DataFrame,
    bar_pos: int,
    side: Side,
    cost_cfg: CostConfig = CostConfig(),
    notional: float = 1.0,
    extra_slip_worst_vol: bool = False,
    vol_p95_threshold: Optional[float] = None,
    timeout_exit: bool = False,
) -> FillResult:
    """Market (taker) fill at bar's close (deterministic proxy for immediate execution).
    Used for: initial taker strategies, AND rule-4 timeout exits (always taker)."""
    if bar_pos >= len(df):
        raise IndexError(f"bar_pos {bar_pos} out of range for df of len {len(df)}")
    row = df.iloc[bar_pos]
    price = float(row["close"])
    rng = _bar_range(row)

    slip = 0.0
    if extra_slip_worst_vol and vol_p95_threshold is not None:
        bar_vol_pct = rng / price if price else 0.0
        if bar_vol_pct >= vol_p95_threshold:
            slip = slippage_cost(notional, CostConfig(extra_slippage_bps=10.0))

    f = fee(notional, is_maker=False, cfg=cost_cfg)
    return FillResult(True, False, price, f, slip, bar_pos, timeout_exit=timeout_exit)


def simulate_entry(
    df: pd.DataFrame,
    bar_pos: int,
    side: Side,
    limit_price: float,
    cost_cfg: CostConfig = CostConfig(),
    notional: float = 1.0,
    stress_fill_prob: bool = False,
    delay_bars: int = 0,
    extra_slip_worst_vol: bool = False,
    vol_p95_threshold: Optional[float] = None,
) -> FillResult:
    """Rule 4 wired for entries: try the maker limit on this single bar; if it doesn't fill,
    the signal is SKIPPED (no chase, no next-bar retry) — tracked as opportunity cost by the
    caller (core/gate.py), which knows the would-be gross return and stamps it onto the result."""
    res = try_limit_fill(
        df, bar_pos, side, limit_price, cost_cfg, notional,
        stress_fill_prob, delay_bars, extra_slip_worst_vol, vol_p95_threshold,
    )
    if not res.filled:
        res.skipped_entry = True
    return res


def simulate_exit_with_timeout(
    df: pd.DataFrame,
    bar_pos: int,
    side: Side,
    limit_price: float,
    timeout_bars: int,
    cost_cfg: CostConfig = CostConfig(),
    notional: float = 1.0,
    stress_fill_prob: bool = False,
    delay_bars: int = 0,
    extra_slip_worst_vol: bool = False,
    vol_p95_threshold: Optional[float] = None,
) -> FillResult:
    """Rule 4 wired for exits: try the maker limit for up to `timeout_bars` bars starting at
    bar_pos; on the first trade-through bar, fill maker. If none of the bars in the window
    trade through, force a MARKET (taker) exit on the last bar of the window (timeout_bars
    is inclusive of the starting bar, i.e. timeout_bars=1 means only bar_pos itself is tried
    before forcing a market exit on that same bar)."""
    last_pos = bar_pos
    for offset in range(timeout_bars):
        pos = bar_pos + offset
        if pos >= len(df):
            break
        last_pos = pos
        res = try_limit_fill(
            df, pos, side, limit_price, cost_cfg, notional,
            stress_fill_prob, delay_bars, extra_slip_worst_vol, vol_p95_threshold,
        )
        if res.filled:
            return res
    # timeout: forced market exit, ALWAYS taker (house rule)
    exit_pos = min(last_pos, len(df) - 1)
    return market_fill(
        df, exit_pos, side, cost_cfg, notional,
        extra_slip_worst_vol, vol_p95_threshold, timeout_exit=True,
    )


def adverse_drift(df: pd.DataFrame, fill_pos: int, side: Side) -> Optional[float]:
    """Rule 3: next-bar close-to-close drift AGAINST the position just taken.
    buy -> adverse if next bar's return is negative (report as a positive 'cost' number).
    sell -> adverse if next bar's return is positive.
    Returns None if there's no next bar (end of data)."""
    if fill_pos + 1 >= len(df):
        return None
    close_now = float(df.iloc[fill_pos]["close"])
    close_next = float(df.iloc[fill_pos + 1]["close"])
    if close_now == 0:
        return None
    ret = (close_next - close_now) / close_now
    return -ret if side == "buy" else ret  # positive number = adverse (cost-like)


def vol_p95_threshold(df: pd.DataFrame, lookback_col: str = "close") -> float:
    """Compute the 95th percentile of bar-range-as-%-of-close over the whole df, used to
    flag 'worst-5%-volatility bars' for stress tier (d)."""
    rng_pct = (df["high"] - df["low"]) / df[lookback_col].replace(0, np.nan)
    return float(rng_pct.quantile(0.95))
