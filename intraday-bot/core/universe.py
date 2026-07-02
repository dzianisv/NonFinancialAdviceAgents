"""
Point-in-time universe builder for cross-sectional work.

Universe rule: top-N USDT pairs by TRAILING 30d quote volume, computed point-in-time from
downloaded daily klines (no look-ahead — on any given day, only volume observed UP TO that
day is used to decide membership). A coin enters the universe only after 90d of listed
history (avoids day-1 illiquidity/listing-pump artifacts).

Survivorship honesty: Binance Vision's monthly-klines archive is indexed by CURRENTLY
listed/known symbols; it does not publish an official "delisted symbols" list. We attempt
to include a handful of historically faded/delisted-from-major-listing USDT pairs that are
still fetchable from the archive (their historical klines remain in Binance Vision even if
the pair is no longer actively traded/listed on binance.com today), but we CANNOT claim full
delisting coverage — Binance does not expose a delisted-symbol registry, and any pair that
was fully removed from data.binance.vision (as opposed to just spot.binance.com) is simply
unavailable to us. This is documented honestly in the coverage report, not hidden.
"""
from __future__ import annotations

from typing import Optional

import pandas as pd

from core.data import load_universe

MIN_LISTED_DAYS = 90


def build_daily_volume_panel(df_dict: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """quote_vol per symbol per day, aligned on a common daily UTC index (outer join;
    missing days for a not-yet-listed symbol are NaN, not zero — a coin with NaN volume
    has not started trading yet and must not be treated as a zero-volume, in-universe coin)."""
    cols = {}
    for sym, df in df_dict.items():
        if "quote_vol" in df.columns:
            cols[sym] = df["quote_vol"]
        else:
            cols[sym] = df["close"] * df["volume"]
    panel = pd.concat(cols, axis=1)
    return panel.sort_index()


def listing_date(df_dict: dict[str, pd.DataFrame]) -> dict[str, pd.Timestamp]:
    return {sym: df.index[0] for sym, df in df_dict.items() if len(df) > 0}


def last_listed_date(df_dict: dict[str, pd.DataFrame]) -> dict[str, pd.Timestamp]:
    """Last date each symbol actually has data for (its de-facto delisting/staleness
    cutoff). Used to hard-exclude a symbol from universe membership once we're past its
    last observed bar, independent of what a rolling-mean window over NaN-padded volume
    might otherwise still report as a non-NaN average (see point_in_time_universe's
    trailing_days-staleness fix)."""
    return {sym: df.index[-1] for sym, df in df_dict.items() if len(df) > 0}


def point_in_time_universe(df_dict: dict[str, pd.DataFrame], top_n: int = 20,
                            trailing_days: int = 30,
                            min_listed_days: int = MIN_LISTED_DAYS) -> pd.DataFrame:
    """Return a DataFrame indexed by date, columns = ['members'] (list of symbols in the
    top-N by trailing `trailing_days` quote volume, restricted to symbols with >= 90d of
    prior listed history as of that date). Entirely point-in-time: on date t, only data
    with timestamp <= t is used.

    STALENESS FIX (2026-07-02): a symbol's raw daily quote_vol is NaN (not zero) for every
    date after it stops trading (delisting, or simply no more data past the cache's last
    row) -- see build_daily_volume_panel's outer-join note. `panel.rolling(...).mean()`
    with min_periods < trailing_days will keep returning a non-NaN mean for up to
    (trailing_days - min_periods) days after the symbol's last real observation, because
    the window still contains enough real (pre-delisting) observations to clear
    min_periods even though the CURRENT day's own volume is NaN. That let a delisted coin
    linger in top-N membership on stale data (confirmed ~15 days for SRMUSDT/COCOSUSDT at
    trailing_days=30, min_periods=15). Fixed by tracking each symbol's last-observed date
    explicitly and hard-excluding it from eligibility on any date past that cutoff --
    independent of whatever the rolling mean still computes."""
    panel = build_daily_volume_panel(df_dict)
    list_dates = listing_date(df_dict)
    last_dates = last_listed_date(df_dict)

    trailing_vol = panel.rolling(trailing_days, min_periods=max(1, trailing_days // 2)).mean()

    rows = []
    for dt in panel.index:
        eligible_syms = [
            sym for sym in panel.columns
            if sym in list_dates and (dt - list_dates[sym]).days >= min_listed_days
            and sym in last_dates and dt <= last_dates[sym]
        ]
        if not eligible_syms:
            rows.append({"date": dt, "members": []})
            continue
        day_vol = trailing_vol.loc[dt, eligible_syms].dropna()
        top = day_vol.sort_values(ascending=False).head(top_n).index.tolist()
        rows.append({"date": dt, "members": top})

    out = pd.DataFrame(rows).set_index("date")
    return out


def coverage_report(df_dict: dict[str, pd.DataFrame], attempted_delisted: list[str]) -> dict:
    """Honest documentation of what delisted/faded names we could and could not fetch."""
    got = [s for s in attempted_delisted if s in df_dict and len(df_dict[s]) > 0]
    missing = [s for s in attempted_delisted if s not in got]
    return {
        "attempted_delisted_or_faded": attempted_delisted,
        "successfully_fetched": got,
        "unavailable": missing,
        "note": (
            "Binance Vision (data.binance.vision) does not publish an official delisted-symbol "
            "registry. We can only fetch symbols whose historical archive still exists there; "
            "pairs fully purged from the archive are not recoverable via this pipeline. "
            "'unavailable' entries above returned zero downloadable months and are excluded "
            "from the universe — this means the universe still has a partial (not zero, but "
            "not complete) survivorship bias that we can quantify but not eliminate."
        ),
    }
