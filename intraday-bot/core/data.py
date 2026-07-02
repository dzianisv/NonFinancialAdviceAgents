"""
Binance Vision kline downloader + loader.

Source: https://data.binance.vision/data/spot/monthly/klines/<SYMBOL>/<interval>/<SYMBOL>-<interval>-<YYYY-MM>.zip
Daily endpoint fills in the current (incomplete) month:
https://data.binance.vision/data/spot/daily/klines/<SYMBOL>/<interval>/<SYMBOL>-<interval>-<YYYY-MM-DD>.zip

Cache: intraday-bot/data/<SYMBOL>/<interval>/  (raw zips + a merged parquet/csv per symbol+interval)

HARD ASSERTION: Binance kline timestamps are milliseconds since epoch for files up to some point
in 2025, then Binance switched some endpoints to MICROSECONDS. We must never silently misparse
this — a magnitude check on open_time asserts the unit and normalizes to UTC pandas
DatetimeIndex. A misparse raises, it never silently shifts data.

Columns (Binance spot kline schema, 12 columns):
  open_time, open, high, low, close, volume, close_time,
  quote_vol, count, taker_buy_base, taker_buy_quote, ignore

No look-ahead: these are raw exchange bars; it is the STRATEGY layer's job to only use
prior-bar-close information (see core/gate.py). This module just loads honest OHLCV.
"""
from __future__ import annotations

import io
import os
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone, date
from typing import Optional

import numpy as np
import pandas as pd
import requests

BASE_URL = "https://data.binance.vision/data/spot"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

KLINE_COLUMNS = [
    "open_time", "open", "high", "low", "close", "volume", "close_time",
    "quote_vol", "count", "taker_buy_base", "taker_buy_quote", "ignore",
]

# Binance kline timestamp units: legacy = milliseconds (13-digit epoch), 2025+ some
# symbols/files switched to microseconds (16-digit epoch). We assert the magnitude of
# open_time explicitly rather than trust a fixed unit — a misparse must raise.
_MS_MIN, _MS_MAX = 1_000_000_000_000, 9_999_999_999_999          # 13-digit ms range
_US_MIN, _US_MAX = 1_000_000_000_000_000, 9_999_999_999_999_999  # 16-digit us range


def detect_timestamp_unit(sample_open_time: int) -> str:
    """Return 'ms' or 'us' based on magnitude of a raw open_time int. Raises on anything else
    (e.g. seconds, or garbage) — never silently guess/shift."""
    v = int(sample_open_time)
    if _MS_MIN <= v <= _MS_MAX:
        return "ms"
    if _US_MIN <= v <= _US_MAX:
        return "us"
    raise ValueError(
        f"open_time {v} does not match known Binance ms (13-digit) or us (16-digit) "
        f"epoch ranges — refusing to silently guess a unit. Inspect the source file."
    )


def _normalize_open_time(raw: pd.Series) -> pd.DatetimeIndex:
    """Assert timestamp unit on the FIRST value, normalize the whole column to UTC.
    All rows in one file share the schema, but we defensively check first+last agree."""
    raw = raw.astype(np.int64)
    unit_first = detect_timestamp_unit(int(raw.iloc[0]))
    unit_last = detect_timestamp_unit(int(raw.iloc[-1]))
    if unit_first != unit_last:
        raise ValueError(
            f"mixed timestamp units within one file: first={unit_first} last={unit_last} "
            f"— this file is corrupt or straddles Binance's ms->us switch mid-file."
        )
    pd_unit = "ms" if unit_first == "ms" else "us"
    return pd.to_datetime(raw, unit=pd_unit, utc=True)


def _cache_dir(symbol: str, interval: str) -> str:
    d = os.path.join(DATA_DIR, symbol, interval)
    os.makedirs(d, exist_ok=True)
    return d


def _monthly_url(symbol: str, interval: str, yyyy_mm: str) -> str:
    return f"{BASE_URL}/monthly/klines/{symbol}/{interval}/{symbol}-{interval}-{yyyy_mm}.zip"


def _daily_url(symbol: str, interval: str, yyyy_mm_dd: str) -> str:
    return f"{BASE_URL}/daily/klines/{symbol}/{interval}/{symbol}-{interval}-{yyyy_mm_dd}.zip"


def _months_between(start: str, end: str) -> list[str]:
    """Inclusive list of 'YYYY-MM' strings from start to end (both 'YYYY-MM' or 'YYYY-MM-DD')."""
    s = pd.Period(start[:7], freq="M")
    e = pd.Period(end[:7], freq="M")
    out = []
    p = s
    while p <= e:
        out.append(str(p))
        p += 1
    return out


def _days_in_month(yyyy_mm: str, today: Optional[date] = None) -> list[str]:
    """Days of the given month up to (and including) today if it's the current month,
    else the full month. Used to fill the incomplete current month via the daily endpoint."""
    today = today or datetime.now(timezone.utc).date()
    period = pd.Period(yyyy_mm, freq="M")
    start = period.start_time.date()
    end = period.end_time.date()
    if period == pd.Period(today.strftime("%Y-%m"), freq="M"):
        end = today
    days = pd.date_range(start, end, freq="D")
    return [d.strftime("%Y-%m-%d") for d in days]


def _download_zip_csv(url: str, timeout: int = 30) -> Optional[pd.DataFrame]:
    """Download one Binance Vision zip, return the raw kline DataFrame (unparsed dtypes),
    or None if the URL 404s (month/day doesn't exist yet, or symbol wasn't listed then)."""
    try:
        resp = requests.get(url, timeout=timeout)
    except requests.RequestException as e:
        print(f"    [WARN] network error {url}: {e}")
        return None
    if resp.status_code == 404:
        return None
    if resp.status_code != 200:
        print(f"    [WARN] HTTP {resp.status_code} for {url}")
        return None
    try:
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            names = zf.namelist()
            if not names:
                return None
            with zf.open(names[0]) as f:
                # Binance monthly/daily CSVs may or may not have a header row depending on
                # vintage; detect by checking if the first field parses as an int epoch.
                first_bytes = f.read(64)
                f.seek(0)
                has_header = not first_bytes.split(b",")[0].strip().isdigit()
                df = pd.read_csv(
                    f, header=0 if has_header else None, names=KLINE_COLUMNS if not has_header else None,
                )
                if has_header:
                    # normalize header names defensively (Binance sometimes ships them named)
                    df.columns = KLINE_COLUMNS[: len(df.columns)]
    except zipfile.BadZipFile:
        print(f"    [WARN] bad zip: {url}")
        return None
    return df


def _normalize_one_file(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize ONE raw Binance Vision file's timestamp column to a UTC DatetimeIndex.
    Each individual file uses a single consistent unit (ms pre-2025, us for some 2025+
    files) — the ms->us switch happens BETWEEN files/months, not within one file. We assert
    that here, per-file, at ingestion time, before any cross-month concatenation. This is
    the correct place for the hard assertion: concatenating already-normalized (UTC,
    consistent-dtype) indices across months is always safe regardless of which raw unit
    each source file used."""
    idx = _normalize_open_time(df["open_time"])
    out = df.copy()
    for col in ["open", "high", "low", "close", "volume", "quote_vol",
                "taker_buy_base", "taker_buy_quote"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    if "count" in out.columns:
        out["count"] = pd.to_numeric(out["count"], errors="coerce").astype("Int64")
    out.index = idx
    out.index.name = "open_time_utc"
    out = out.drop(columns=["ignore"], errors="ignore")
    return out


def _fill_month_via_daily(symbol: str, interval: str, cache_dir: str, yyyy_mm: str,
                           frames: list) -> None:
    """Download+cache one month's worth of data via the per-day `daily` endpoint, appending
    normalized frames to `frames` in place. Used both for the current (incomplete) month and
    as a fallback for any completed month whose `monthly` zip 404s (not yet published)."""
    for d in _days_in_month(yyyy_mm):
        raw_day_path = os.path.join(cache_dir, f"{symbol}-{interval}-{d}.zip.csv.parquet")
        if os.path.exists(raw_day_path):
            raw_df = pd.read_parquet(raw_day_path)
        else:
            raw_df = _download_zip_csv(_daily_url(symbol, interval, d))
            if raw_df is None or raw_df.empty:
                continue
            raw_df.to_parquet(raw_day_path)
        try:
            frames.append(_normalize_one_file(raw_df))
        except ValueError as e:
            print(f"    [ERROR] {symbol} {interval} {d}: {e}")
            raise


def _download_one_symbol_interval(symbol: str, interval: str, start: str, end: str,
                                   fill_current_month_daily: bool = True) -> str:
    """Download+cache all monthly zips for symbol/interval in [start,end], plus daily fill
    for the current month AND for any completed month whose monthly zip isn't published yet
    (Binance's monthly archive for a just-finished month lags behind month-end by some days;
    a 404 there does NOT mean the month has no data -- the `daily` endpoint already has it,
    day by day, well before the monthly zip is rolled up). Returns path to the merged parquet
    cache file.

    GAP FIX (2026-07-02): previously, any non-current month whose monthly zip 404'd was
    silently `continue`-d with NO daily-endpoint fallback, dropping the whole month from the
    cache (confirmed: this is exactly how June 2026 went missing for every 1d/1h/5m symbol --
    the June monthly zip wasn't published yet when this ran in early July, so it 404'd, and
    the old code only ever daily-filled `today_month`, never a prior 404'd month)."""
    cache_dir = _cache_dir(symbol, interval)
    merged_path = os.path.join(cache_dir, f"{symbol}-{interval}-merged.parquet")

    months = _months_between(start, end)
    frames = []
    today_month = datetime.now(timezone.utc).strftime("%Y-%m")

    for ym in months:
        if ym == today_month:
            continue  # handled by daily fill below
        raw_zip_path = os.path.join(cache_dir, f"{symbol}-{interval}-{ym}.zip.csv.parquet")
        if os.path.exists(raw_zip_path):
            raw_df = pd.read_parquet(raw_zip_path)
        else:
            raw_df = _download_zip_csv(_monthly_url(symbol, interval, ym))
            if raw_df is None or raw_df.empty:
                # monthly zip not (yet) published for this month -- fall back to the daily
                # endpoint instead of silently dropping the month. This is the normal path
                # for the most-recently-completed month right after month-end.
                print(f"    [FALLBACK] {symbol} {interval} {ym}: monthly zip unavailable, "
                      f"filling via daily endpoint instead")
                _fill_month_via_daily(symbol, interval, cache_dir, ym, frames)
                continue
            raw_df.to_parquet(raw_zip_path)
        try:
            frames.append(_normalize_one_file(raw_df))
        except ValueError as e:
            print(f"    [ERROR] {symbol} {interval} {ym}: {e}")
            raise

    if fill_current_month_daily and today_month in months:
        _fill_month_via_daily(symbol, interval, cache_dir, today_month, frames)

    if not frames:
        print(f"    [SKIP] {symbol} {interval}: no data found in range {start}..{end}")
        return merged_path

    out = pd.concat(frames)
    out = out[~out.index.duplicated(keep="first")].sort_index()

    out.to_parquet(merged_path)
    print(f"    [OK] {symbol:10s} {interval:4s} {len(out):7d} rows  "
          f"{out.index[0].date()} -> {out.index[-1].date()}")
    return merged_path


def download(symbols: list[str], interval: str, start: str, end: str, workers: int = 8) -> dict[str, str]:
    """Parallel download (ThreadPoolExecutor, default 8 workers per house-rule 'xargs -P8').
    Returns dict symbol -> merged parquet path."""
    results = {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {
            ex.submit(_download_one_symbol_interval, sym, interval, start, end): sym
            for sym in symbols
        }
        for fut in as_completed(futs):
            sym = futs[fut]
            try:
                results[sym] = fut.result()
            except Exception as e:
                print(f"    [ERROR] {sym} {interval}: {e}")
    return results


def load(symbol: str, interval: str) -> pd.DataFrame:
    """Load a cached merged parquet for symbol/interval. Raises if not downloaded yet."""
    path = os.path.join(_cache_dir(symbol, interval), f"{symbol}-{interval}-merged.parquet")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"no cached data for {symbol} {interval} at {path} — run download() first"
        )
    df = pd.read_parquet(path)
    if not isinstance(df.index, pd.DatetimeIndex) or df.index.tz is None:
        raise ValueError(f"{symbol} {interval} cache index is not UTC-aware DatetimeIndex — corrupt cache")
    return df


def load_universe(symbols: list[str], interval: str) -> dict[str, pd.DataFrame]:
    out = {}
    for sym in symbols:
        try:
            out[sym] = load(sym, interval)
        except FileNotFoundError as e:
            print(f"  [SKIP] {sym}: {e}")
    return out


if __name__ == "__main__":
    import sys
    syms = sys.argv[1:] or ["BTCUSDT"]
    print(f"Downloading 1d klines for {syms} (2020-01 -> now)...")
    download(syms, "1d", "2020-01", datetime.now(timezone.utc).strftime("%Y-%m"))
