"""
Latest-bars fetcher for the live/paper runner.

Primary: alpaca-py CryptoHistoricalDataClient — Alpaca's crypto market data is PUBLIC (no
API keys required) per docs.alpaca.markets/docs/crypto-pricing-data, so this works even in
mode=notify with zero credentials.

Fallback: ccxt public REST (no keys) against Coinbase, used if alpaca-py isn't importable
or its request fails (network blip, rate limit, endpoint change) — keeps the notify-mode
smoke path independent of any single vendor.

Returns bars in the SAME schema core/data.py uses (open, high, low, close, volume,
UTC DatetimeIndex) so the SAME strategy signal functions used in backtests can run
unmodified against live data.
"""
from __future__ import annotations

import datetime as _dt
from typing import Optional

import pandas as pd

# interval string -> (alpaca TimeFrame kwargs, ccxt timeframe string, pandas freq for bar math)
_INTERVAL_MAP = {
    "1m": {"alpaca_amount": 1, "alpaca_unit": "Minute", "ccxt": "1m", "minutes": 1},
    "5m": {"alpaca_amount": 5, "alpaca_unit": "Minute", "ccxt": "5m", "minutes": 5},
    "15m": {"alpaca_amount": 15, "alpaca_unit": "Minute", "ccxt": "15m", "minutes": 15},
    "1h": {"alpaca_amount": 1, "alpaca_unit": "Hour", "ccxt": "1h", "minutes": 60},
    "1d": {"alpaca_amount": 1, "alpaca_unit": "Day", "ccxt": "1d", "minutes": 60 * 24},
}


class MarketDataError(Exception):
    pass


def _alpaca_symbol(symbol: str) -> str:
    """Alpaca crypto symbols use 'BTC/USD' form already — pass through, but normalize
    common 'BTCUSD'/'BTC-USD' spellings defensively."""
    if "/" in symbol:
        return symbol
    if "-" in symbol:
        return symbol.replace("-", "/")
    # bare 'BTCUSD' -> 'BTC/USD' (assume 3-4 char quote currency at the end, USD/USDT/USDC)
    for quote in ("USDT", "USDC", "USD"):
        if symbol.endswith(quote) and len(symbol) > len(quote):
            return f"{symbol[:-len(quote)]}/{quote}"
    return symbol


def _ccxt_symbol(symbol: str) -> str:
    return _alpaca_symbol(symbol)  # ccxt also uses 'BTC/USD' form


def fetch_bars_alpaca(symbol: str, interval: str, lookback_bars: int) -> pd.DataFrame:
    from alpaca.data.historical.crypto import CryptoHistoricalDataClient
    from alpaca.data.requests import CryptoBarsRequest
    from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

    spec = _INTERVAL_MAP[interval]
    tf = TimeFrame(spec["alpaca_amount"], TimeFrameUnit[spec["alpaca_unit"]])
    # crypto market data is public — no keys needed for historical bars
    client = CryptoHistoricalDataClient()
    end = _dt.datetime.now(_dt.timezone.utc)
    start = end - _dt.timedelta(minutes=spec["minutes"] * (lookback_bars + 5))
    sym = _alpaca_symbol(symbol)
    req = CryptoBarsRequest(symbol_or_symbols=[sym], timeframe=tf, start=start, end=end)
    bars = client.get_crypto_bars(req)
    df = bars.df
    if df.empty:
        raise MarketDataError(f"alpaca returned no bars for {sym} {interval}")
    if isinstance(df.index, pd.MultiIndex):
        df = df.xs(sym, level=0)
    df = df.rename(columns={"trade_count": "count"})
    df.index = pd.to_datetime(df.index, utc=True)
    df.index.name = "open_time_utc"
    return df[["open", "high", "low", "close", "volume"]].sort_index().tail(lookback_bars)


def fetch_bars_ccxt(symbol: str, interval: str, lookback_bars: int) -> pd.DataFrame:
    import ccxt

    spec = _INTERVAL_MAP[interval]
    ex = ccxt.coinbase({"enableRateLimit": True})
    sym = _ccxt_symbol(symbol)
    ohlcv = ex.fetch_ohlcv(sym, timeframe=spec["ccxt"], limit=lookback_bars)
    if not ohlcv:
        raise MarketDataError(f"ccxt returned no bars for {sym} {interval}")
    df = pd.DataFrame(ohlcv, columns=["ts_ms", "open", "high", "low", "close", "volume"])
    df.index = pd.to_datetime(df["ts_ms"], unit="ms", utc=True)
    df.index.name = "open_time_utc"
    return df[["open", "high", "low", "close", "volume"]].sort_index()


def fetch_bars(symbol: str, interval: str, lookback_bars: int = 300) -> pd.DataFrame:
    """Fetch the latest `lookback_bars` OHLCV bars for `symbol`. Tries alpaca-py market
    data first (public, no keys); falls back to ccxt public REST on any failure. Raises
    MarketDataError only if BOTH sources fail — the runner should treat that as
    'skip this cycle', never as 'assume flat/zero data'."""
    if interval not in _INTERVAL_MAP:
        raise MarketDataError(f"unsupported interval {interval!r}; supported: {list(_INTERVAL_MAP)}")

    errors = []
    try:
        return fetch_bars_alpaca(symbol, interval, lookback_bars)
    except Exception as e:  # noqa: BLE001 - any alpaca failure falls through to ccxt
        errors.append(f"alpaca: {e}")

    try:
        return fetch_bars_ccxt(symbol, interval, lookback_bars)
    except Exception as e:  # noqa: BLE001
        errors.append(f"ccxt: {e}")

    raise MarketDataError(f"both data sources failed for {symbol} {interval}: " + " | ".join(errors))


def fetch_universe(symbols: list, interval: str, lookback_bars: int = 300) -> dict:
    """Fetch bars for every symbol; a per-symbol failure is logged and that symbol is
    dropped from the returned dict (never silently zero-filled) so the strategy only ever
    sees honest data."""
    out = {}
    skipped = {}
    for sym in symbols:
        try:
            out[sym] = fetch_bars(sym, interval, lookback_bars)
        except MarketDataError as e:
            skipped[sym] = str(e)
    return out, skipped
