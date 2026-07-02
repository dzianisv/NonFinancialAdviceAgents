"""Unit tests for core/data.py — timestamp unit assertion is the critical safety check
(Binance switched ms -> microseconds in 2025 files; a misparse must raise, never silently
shift the index)."""
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import data


def test_detect_ms_unit():
    # 2024-01-01 00:00:00 UTC in milliseconds (13 digits)
    assert data.detect_timestamp_unit(1704067200000) == "ms"


def test_detect_us_unit():
    # 2025-01-01 00:00:00 UTC in microseconds (16 digits) — post-2025-switch format
    assert data.detect_timestamp_unit(1735689600000000) == "us"


def test_detect_garbage_raises():
    with pytest.raises(ValueError):
        data.detect_timestamp_unit(12345)  # way too small, neither ms nor us epoch


def test_detect_seconds_raises():
    # seconds-since-epoch (10 digits) is NOT a valid Binance unit -> must raise, not guess
    with pytest.raises(ValueError):
        data.detect_timestamp_unit(1704067200)


def test_normalize_open_time_ms_and_us_agree_on_same_instant():
    """The ms-encoded and us-encoded representations of the SAME instant must normalize
    to the identical UTC timestamp — this is the core misparse-prevention check."""
    ms_series = pd.Series([1704067200000, 1704153600000])
    us_series = pd.Series([1704067200000000, 1704153600000000])
    idx_ms = data._normalize_open_time(ms_series)
    idx_us = data._normalize_open_time(us_series)
    assert idx_ms.iloc[0] == idx_us.iloc[0]
    assert idx_ms.iloc[1] == idx_us.iloc[1]
    assert str(idx_ms.dt.tz) == "UTC"


def test_normalize_mixed_units_within_file_raises():
    """A file where first/last rows disagree on unit magnitude is corrupt — must raise,
    never silently pick one and shift half the data."""
    mixed = pd.Series([1704067200000, 1735689600000000])  # ms then us
    with pytest.raises(ValueError):
        data._normalize_open_time(mixed)


def test_load_raises_if_not_downloaded(tmp_path, monkeypatch):
    monkeypatch.setattr(data, "DATA_DIR", str(tmp_path))
    with pytest.raises(FileNotFoundError):
        data.load("NOPE_NOT_A_REAL_SYMBOL", "1d")


def test_months_between_inclusive():
    months = data._months_between("2024-01", "2024-03")
    assert months == ["2024-01", "2024-02", "2024-03"]


def test_normalize_one_file_handles_ms_file_and_us_file_independently():
    """Regression test: each raw FILE is normalized independently at ingestion (before
    cross-month concat). A ms-unit file and a us-unit file, normalized separately, must
    each succeed and produce indices that concatenate cleanly (no false 'mixed units'
    error from comparing across different months/files, which legitimately differ in
    raw unit around the 2025 Binance switch)."""
    ms_file = pd.DataFrame({
        "open_time": [1704067200000, 1704153600000],  # 2024-01-01, 2024-01-02 (ms)
        "open": [100.0, 101.0], "high": [102.0, 103.0], "low": [99.0, 100.0],
        "close": [101.0, 102.0], "volume": [10.0, 11.0], "close_time": [0, 0],
        "quote_vol": [1.0, 1.0], "count": [1, 1], "taker_buy_base": [1.0, 1.0],
        "taker_buy_quote": [1.0, 1.0], "ignore": [0, 0],
    })
    us_file = pd.DataFrame({
        "open_time": [1735689600000000, 1735776000000000],  # 2025-01-01, 2025-01-02 (us)
        "open": [200.0, 201.0], "high": [202.0, 203.0], "low": [199.0, 200.0],
        "close": [201.0, 202.0], "volume": [20.0, 21.0], "close_time": [0, 0],
        "quote_vol": [1.0, 1.0], "count": [1, 1], "taker_buy_base": [1.0, 1.0],
        "taker_buy_quote": [1.0, 1.0], "ignore": [0, 0],
    })
    norm_ms = data._normalize_one_file(ms_file)
    norm_us = data._normalize_one_file(us_file)
    combined = pd.concat([norm_ms, norm_us])
    combined = combined[~combined.index.duplicated(keep="first")].sort_index()
    assert list(combined.index.date.astype(str)) == [
        "2024-01-01", "2024-01-02", "2025-01-01", "2025-01-02",
    ]
    assert combined.index.is_monotonic_increasing
    assert str(combined.index.tz) == "UTC"


def test_load_raises_on_naive_index(tmp_path, monkeypatch):
    """A cached parquet whose index lost its UTC tz-awareness must be rejected on load."""
    monkeypatch.setattr(data, "DATA_DIR", str(tmp_path))
    cache_dir = data._cache_dir("FAKEUSDT", "1d")
    bad_df = pd.DataFrame(
        {"open": [1.0], "high": [1.0], "low": [1.0], "close": [1.0]},
        index=pd.to_datetime(["2024-01-01"]),  # naive, no tz
    )
    bad_df.to_parquet(os.path.join(cache_dir, "FAKEUSDT-1d-merged.parquet"))
    with pytest.raises(ValueError):
        data.load("FAKEUSDT", "1d")


def _fake_kline_row(day_ts_ms: int) -> dict:
    return {
        "open_time": day_ts_ms, "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5,
        "volume": 10.0, "close_time": day_ts_ms, "quote_vol": 1000.0, "count": 5,
        "taker_buy_base": 1.0, "taker_buy_quote": 1.0, "ignore": 0,
    }


def test_month_gap_falls_back_to_daily_endpoint_when_monthly_zip_missing(tmp_path, monkeypatch):
    """Regression test for the June-2026 data-gap bug: a completed month whose `monthly`
    zip 404s (not yet published by Binance -- the normal state right after month-end) must
    NOT be silently dropped. It must fall back to the `daily` endpoint, day by day, exactly
    like the current/incomplete month already does. Confirmed on real data: BTCUSDT (and all
    45 other daily symbols, plus 1h/5m for BTC/ETH/SOL) had a hole from 2026-05-31 to
    2026-07-01 because the June monthly zip 404'd and the old code had no fallback for a
    non-current month.

    Fully network-free: monkeypatches `_download_zip_csv` to 404 (return None) for the
    `monthly` URL and to succeed for the `daily` URL, then asserts every day of the gap
    month appears in the merged output with no hole."""
    monkeypatch.setattr(data, "DATA_DIR", str(tmp_path))

    # freeze "today" to a fixed date so this test doesn't depend on when it's run, and pick
    # a "gap month" that is NOT the current month (mirrors June being a prior, completed
    # month relative to the July run that discovered the bug).
    import datetime as _dt

    fixed_now = _dt.datetime(2026, 7, 2, tzinfo=_dt.timezone.utc)

    class _FixedDateTime(_dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now if tz else fixed_now.replace(tzinfo=None)

    monkeypatch.setattr(data, "datetime", _FixedDateTime)

    def fake_download_zip_csv(url, timeout=30):
        if "/monthly/klines/" in url and "-2026-06.zip" in url:
            return None  # simulate the un-published-yet monthly zip 404
        if "/daily/klines/" in url:
            # url ends "...FAKEUSDT-1d-2026-06-05.zip" -- pull the trailing YYYY-MM-DD
            stem = url.rsplit("/", 1)[-1].replace(".zip", "")  # "FAKEUSDT-1d-2026-06-05"
            day_str = "-".join(stem.split("-")[-3:])  # "2026-06-05"
            ts = int(pd.Timestamp(day_str, tz="UTC").timestamp() * 1000)
            return pd.DataFrame([_fake_kline_row(ts)])
        if "/monthly/klines/" in url:
            # any other month's monthly zip: succeed trivially (not under test here)
            return pd.DataFrame([])
        return None

    monkeypatch.setattr(data, "_download_zip_csv", fake_download_zip_csv)

    path = data._download_one_symbol_interval("FAKEUSDT", "1d", "2026-06", "2026-06")
    assert os.path.exists(path)
    df = pd.read_parquet(path)

    expected_days = pd.date_range("2026-06-01", "2026-06-30", freq="D", tz="UTC")
    missing = expected_days.difference(df.index)
    assert list(missing) == [], f"June gap regressed -- missing days: {list(missing)}"
    assert len(df) == 30
    assert not df.index.duplicated().any()
