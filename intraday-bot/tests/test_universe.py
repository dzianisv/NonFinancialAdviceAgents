"""Unit tests for core/universe.py — point-in-time universe builder."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import universe


def _make_symbol_df(start, n, base_vol):
    idx = pd.date_range(start, periods=n, freq="D", tz="UTC")
    price = np.full(n, 100.0)
    vol = np.full(n, base_vol)
    return pd.DataFrame(
        {"open": price, "high": price, "low": price, "close": price, "volume": vol,
         "quote_vol": price * vol},
        index=idx,
    )


def test_coin_excluded_before_90d_listed():
    df_dict = {
        "A": _make_symbol_df("2020-01-01", 200, 1_000_000),
        "B": _make_symbol_df("2020-01-01", 200, 500_000),
    }
    u = universe.point_in_time_universe(df_dict, top_n=5, trailing_days=10, min_listed_days=90)
    early_day = pd.Timestamp("2020-01-10", tz="UTC")
    assert u.loc[early_day, "members"] == []  # both coins < 90d listed


def test_coin_included_after_90d_listed():
    df_dict = {
        "A": _make_symbol_df("2020-01-01", 200, 1_000_000),
    }
    u = universe.point_in_time_universe(df_dict, top_n=5, trailing_days=10, min_listed_days=90)
    late_day = pd.Timestamp("2020-01-01", tz="UTC") + pd.Timedelta(days=95)
    assert "A" in u.loc[late_day, "members"]


def test_top_n_ranks_by_trailing_volume_not_raw_listing_order():
    df_dict = {
        "OLD_LOW_VOL": _make_symbol_df("2020-01-01", 300, 100_000),
        "NEW_HIGH_VOL": _make_symbol_df("2020-01-01", 300, 10_000_000),
    }
    u = universe.point_in_time_universe(df_dict, top_n=1, trailing_days=10, min_listed_days=90)
    day = pd.Timestamp("2020-01-01", tz="UTC") + pd.Timedelta(days=150)
    assert u.loc[day, "members"] == ["NEW_HIGH_VOL"]


def test_point_in_time_no_lookahead_volume_spike_after_date_does_not_affect_earlier_membership():
    """A volume spike planted LATE in a symbol's history must not change universe membership
    on dates BEFORE that spike (point-in-time property)."""
    df_dict = {
        "A": _make_symbol_df("2020-01-01", 300, 1_000_000),
        "B": _make_symbol_df("2020-01-01", 300, 900_000),
    }
    baseline = universe.point_in_time_universe(df_dict, top_n=1, trailing_days=10, min_listed_days=90)

    df_dict2 = {k: v.copy() for k, v in df_dict.items()}
    df_dict2["B"].iloc[-1, df_dict2["B"].columns.get_loc("quote_vol")] = 1e12  # huge late spike

    mutated = universe.point_in_time_universe(df_dict2, top_n=1, trailing_days=10, min_listed_days=90)

    early_day = pd.Timestamp("2020-01-01", tz="UTC") + pd.Timedelta(days=150)
    assert baseline.loc[early_day, "members"] == mutated.loc[early_day, "members"]


def test_coverage_report_distinguishes_fetched_vs_unavailable():
    df_dict = {"OLDCOIN": _make_symbol_df("2020-01-01", 50, 1000)}
    report = universe.coverage_report(df_dict, ["OLDCOIN", "GHOSTCOIN"])
    assert report["successfully_fetched"] == ["OLDCOIN"]
    assert report["unavailable"] == ["GHOSTCOIN"]


def test_listing_date_returns_first_index():
    df_dict = {"A": _make_symbol_df("2021-06-01", 10, 1000)}
    dates = universe.listing_date(df_dict)
    assert dates["A"] == pd.Timestamp("2021-06-01", tz="UTC")


def test_last_listed_date_returns_last_index():
    df_dict = {"A": _make_symbol_df("2021-06-01", 10, 1000)}
    dates = universe.last_listed_date(df_dict)
    assert dates["A"] == pd.Timestamp("2021-06-10", tz="UTC")


def test_delisted_symbol_does_not_linger_in_universe_past_its_last_bar():
    """Regression test for the rolling-volume staleness bug (found by the xs_momentum
    verifier, confirmed on real SRMUSDT/COCOSUSDT data): panel.rolling(30,
    min_periods=15).mean() kept producing a non-NaN trailing volume for a DELISTED coin
    for up to ~15 days after its last real bar, because the window still had >= 15 real
    (pre-delisting) observations even though the coin's OWN current-day volume was NaN
    the whole time. That let a dead symbol linger in top-N membership on stale data.

    Setup mirrors the real-world shape: DEAD trades for 200 days then stops (delisting);
    ALIVE keeps trading for 300 days total (panel's date index extends well past DEAD's
    last bar, exactly like BTCUSDT's index extending past SRMUSDT's 2022-11-28 cutoff).
    DEAD has much higher volume than ALIVE, so before delisting DEAD dominates top-1;
    the bug would keep DEAD in the top-1 slot for ~15 days after it stops trading."""
    start = "2020-01-01"
    dead_len = 200      # DEAD delists after 200 days
    alive_len = 300      # ALIVE's data (and the panel's date index) extends past that
    trailing_days = 30
    min_periods = trailing_days // 2  # 15, matching point_in_time_universe's own default ratio

    dead_df = _make_symbol_df(start, dead_len, base_vol=10_000_000)  # high volume, dominates top-1
    alive_df = _make_symbol_df(start, alive_len, base_vol=1_000_000)  # lower volume, but never stops

    df_dict = {"DEAD": dead_df, "ALIVE": alive_df}
    u = universe.point_in_time_universe(
        df_dict, top_n=1, trailing_days=trailing_days, min_listed_days=90,
    )

    last_dead_date = dead_df.index[-1]

    # Sanity: while DEAD is actually trading (and past the 90d listing gate), it dominates
    # top-1 membership (it has 10x ALIVE's volume).
    day_before_delisting = last_dead_date
    assert u.loc[day_before_delisting, "members"] == ["DEAD"], (
        "sanity check failed -- DEAD should hold the top-1 slot right up to its last bar"
    )

    # The bug: for ~15 days after DEAD's last bar, the OLD rolling-mean-only logic would
    # still report a non-NaN (stale, pre-delisting) trailing volume for DEAD, high enough
    # to keep it in the top-1 slot, crowding out ALIVE on point-in-time-stale data.
    for days_after in [1, 5, 10, 14]:
        dt = last_dead_date + pd.Timedelta(days=days_after)
        if dt not in u.index:
            continue
        members = u.loc[dt, "members"]
        assert "DEAD" not in members, (
            f"DEAD lingered in universe {days_after}d after its last bar ({last_dead_date.date()}) "
            f"-- staleness bug regressed. members={members}"
        )
        assert members == ["ALIVE"], f"expected ALIVE to hold top-1 once DEAD is gone, got {members}"

    # Well past the old ~15-day leak window too -- must stay excluded permanently.
    far_after = last_dead_date + pd.Timedelta(days=40)
    if far_after in u.index:
        assert "DEAD" not in u.loc[far_after, "members"]
