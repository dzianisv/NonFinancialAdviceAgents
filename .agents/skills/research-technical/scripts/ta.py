#!/usr/bin/env python3
"""ta.py — Long-term / swing entry-timing technical analysis engine."""
import argparse, json, sys, warnings
import numpy as np
import pandas as pd
warnings.filterwarnings('ignore')

CRYPTO_TICKERS = {'BTC','ETH','SOL','ADA','DOT','AVAX','LINK','UNI','AAVE','MATIC','BNB','XRP','DOGE','LTC','BCH','ETC','ATOM','ALGO','FTM','NEAR','HBAR','VET','ICP','THETA','EOS','TRX','XLM','HYPE','TON'}

# Ordered exchange fallback chain for crypto OHLCV. Binance is first (best
# liquidity/history) but is geo-blocked in some environments, so the loop falls
# through to the next venue until one returns enough bars.
EXCHANGE_CHAIN = ['binance', 'coinbase', 'kraken', 'kucoin', 'okx']

QUOTE_MAP = {
    'coinbase': 'USD',
    'kraken': 'USD',
    'bitstamp': 'USD',
    'binance': 'USDT',
    'kucoin': 'USDT',
    'okx': 'USDT',
}

# ── Pure functions ────────────────────────────────────────────────────────────

def resolve_symbol(base, exchange_id):
    """Return the ccxt market symbol for a given base asset and exchange.

    Pure (no network) so tests can assert the mapping directly. USD-quoted
    venues (coinbase/kraken/bitstamp) differ from USDT-quoted ones.
    """
    quote = QUOTE_MAP.get(exchange_id, 'USDT')
    return f"{base}/{quote}"

def sma(x, n):
    return pd.Series(x).rolling(n).mean()

def ema(x, n):
    return pd.Series(x).ewm(span=n, adjust=False, min_periods=n).mean()

def rsi(close, period=14):
    """True Wilder RSI: alpha = 1/period. Matches TradingView and the standard reference."""
    close = pd.Series(close)
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    alpha = 1 / period
    avg_gain = gain.ewm(alpha=alpha, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=alpha, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)

def macd(close, fast=12, slow=26, signal=9):
    close = pd.Series(close)
    macd_line = close.ewm(span=fast, adjust=False).mean() - close.ewm(span=slow, adjust=False).mean()
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def obv(close, volume):
    c = pd.Series(close).reset_index(drop=True)
    v = pd.Series(volume).reset_index(drop=True)
    obv_val = [0.0]
    for i in range(1, len(c)):
        if c.iloc[i] > c.iloc[i-1]:
            obv_val.append(obv_val[-1] + v.iloc[i])
        elif c.iloc[i] < c.iloc[i-1]:
            obv_val.append(obv_val[-1] - v.iloc[i])
        else:
            obv_val.append(obv_val[-1])
    return pd.Series(obv_val, index=pd.Series(close).index)

def volume_ratio(volume, n=20):
    v = pd.Series(volume)
    avg = float(v.iloc[-n:].mean())
    if avg == 0:
        return 1.0
    return float(v.iloc[-1] / avg)

def ma_slope(ma_series, n=10):
    ma = pd.Series(ma_series).dropna()
    if len(ma) < 2:
        return 'flat'
    actual_n = min(n, len(ma) - 1)
    if actual_n < 1:
        return 'flat'
    prev = ma.iloc[-1 - actual_n]
    curr = ma.iloc[-1]
    if prev == 0 or np.isnan(prev) or np.isnan(curr):
        return 'flat'
    val = (curr - prev) / prev * 100
    if val > 0.5:
        return 'rising'
    elif val < -0.5:
        return 'falling'
    return 'flat'

def weinstein_stage(price_series, weekly_ma_series):
    price = pd.Series(price_series)
    ma = pd.Series(weekly_ma_series)
    n = min(10, max(2, len(ma) - 1))
    slope = ma_slope(ma, n=n)
    last_price = price.iloc[-1]
    last_ma = ma.iloc[-1]
    # Priority order
    if last_price >= last_ma and slope == 'rising':
        return 2
    if last_price < last_ma and slope == 'falling':
        return 4
    lb = min(26, len(price) - 1)
    # prev_price = price.iloc[-1 - lb]  # not used in stage determination
    if last_price >= last_ma:
        return 3
    else:
        return 1

def find_swing_lows(price_series, window=10):
    p = pd.Series(price_series).reset_index(drop=True)
    w = max(1, window // 2)
    result = []
    for i in range(w, len(p) - w):
        segment = p[i-w : i+w+1]
        if p.iloc[i] == segment.min() and p.iloc[i] < p.iloc[i-w] and p.iloc[i] < p.iloc[i+w]:
            result.append(i)
    # Deduplicate adjacent equal values, keep first
    deduped = []
    for idx in result:
        if deduped and p.iloc[deduped[-1]] == p.iloc[idx]:
            pass  # keep first
        else:
            deduped.append(idx)
    return sorted(deduped)

def find_swing_highs(price_series, window=10):
    p = pd.Series(price_series).reset_index(drop=True)
    w = max(1, window // 2)
    result = []
    for i in range(w, len(p) - w):
        segment = p[i-w : i+w+1]
        if p.iloc[i] == segment.max() and p.iloc[i] > p.iloc[i-w] and p.iloc[i] > p.iloc[i+w]:
            result.append(i)
    deduped = []
    for idx in result:
        if deduped and p.iloc[deduped[-1]] == p.iloc[idx]:
            pass
        else:
            deduped.append(idx)
    return sorted(deduped)

def support_resistance(price_series, window=10):
    p = pd.Series(price_series).reset_index(drop=True)
    current = p.iloc[-1]
    lows = find_swing_lows(p, window=window)
    highs = find_swing_highs(p, window=window)
    sup_candidates = [p.iloc[i] for i in lows if p.iloc[i] < current]
    res_candidates = [p.iloc[i] for i in highs if p.iloc[i] > current]
    support = max(sup_candidates) if sup_candidates else current * 0.95
    resistance = min(res_candidates) if res_candidates else current * 1.05
    return float(support), float(resistance)

def divergence(price_series, indicator_series, lookback=60):
    price_w = pd.Series(price_series).iloc[-lookback:].reset_index(drop=True)
    ind_w = pd.Series(indicator_series).iloc[-lookback:].reset_index(drop=True)

    low_idxs = find_swing_lows(price_w, window=10)
    high_idxs = find_swing_highs(price_w, window=10)

    # Bullish: need last 2 swing lows
    if len(low_idxs) >= 2:
        idx1, idx2 = low_idxs[-2], low_idxs[-1]  # idx1=earlier, idx2=later
        price_low1 = float(price_w.iloc[idx1])
        price_low2 = float(price_w.iloc[idx2])
        ind_low1 = float(ind_w.iloc[idx1])
        ind_low2 = float(ind_w.iloc[idx2])
        # Bullish: price makes lower low, indicator makes higher low
        if price_low2 < price_low1 and ind_low2 > ind_low1:
            return 'bullish'

    # Bearish: need last 2 swing highs
    if len(high_idxs) >= 2:
        idx1, idx2 = high_idxs[-2], high_idxs[-1]  # idx1=earlier, idx2=later
        price_high1 = float(price_w.iloc[idx1])
        price_high2 = float(price_w.iloc[idx2])
        ind_high1 = float(ind_w.iloc[idx1])
        ind_high2 = float(ind_w.iloc[idx2])
        # Bearish: price makes higher high, indicator makes lower high
        if price_high2 > price_high1 and ind_high2 < ind_high1:
            return 'bearish'

    return 'none'

def verdict(features):
    f = features
    stage = f['stage']
    price = f['price']
    dist_50d = f['dist_50d']
    rsi_w = f['rsi_w']
    obv_trend = f['obv_trend']
    div = f['div']
    support = f['support']
    resistance = f['resistance']
    ma50 = f['ma50']
    ma200 = f['ma200']

    if stage == 4:
        return {'verdict': 'AVOID-DOWNTREND', 'entry_low': price, 'entry_high': price,
                'invalidation': resistance, 'level': resistance}

    if stage == 3:
        return {'verdict': 'WAIT-PULLBACK', 'entry_low': support * 0.99, 'entry_high': support * 1.01,
                'invalidation': price * 0.95, 'level': support}

    if stage == 2:
        if dist_50d > 15:
            return {'verdict': 'WAIT-PULLBACK', 'entry_low': ma50 * 0.98, 'entry_high': ma50 * 1.02,
                    'invalidation': ma200 * 0.98, 'level': ma50}
        if rsi_w < 70:
            if obv_trend == 'rising' or div == 'bullish':
                return {'verdict': 'ACCUMULATE', 'entry_low': support * 0.99, 'entry_high': price * 1.01,
                        'invalidation': support * 0.95, 'level': support}
            else:
                return {'verdict': 'BUY-ZONE', 'entry_low': support * 0.99, 'entry_high': price * 1.01,
                        'invalidation': support * 0.95, 'level': support}
        # stage 2 but weekly RSI overbought (>= 70) — wait for pullback to rising 50d
        return {'verdict': 'WAIT-PULLBACK', 'entry_low': ma50 * 0.98, 'entry_high': ma50 * 1.02,
                'invalidation': ma200 * 0.98, 'level': ma50}

    if stage == 1:
        return {'verdict': 'WAIT-BREAKOUT', 'entry_low': resistance * 0.99, 'entry_high': resistance * 1.02,
                'invalidation': support * 0.95, 'level': resistance}

    # Fallback
    return {'verdict': 'WAIT-PULLBACK', 'entry_low': ma50 * 0.98, 'entry_high': ma50 * 1.02,
            'invalidation': ma200 * 0.98, 'level': ma50}


# ── Fetch functions ───────────────────────────────────────────────────────────

def fetch_stock(symbol):
    try:
        import yfinance as yf
        raw = yf.download(symbol, period='3y', interval='1d', progress=False, auto_adjust=True)
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)
        # Ensure columns
        for col in ['Open','High','Low','Close','Volume']:
            if col not in raw.columns:
                raw[col] = np.nan
        # Drop today's partial bar
        today = pd.Timestamp.now().date()
        if len(raw) > 0 and raw.index[-1].date() == today:
            raw = raw.iloc[:-1]
        raw = raw[['Open','High','Low','Close','Volume']].copy()
        weekly = raw.resample('W').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna(subset=['Close'])
        # Drop the last weekly bar if its period-end label is in the future
        # (label='right' means the index is the Sunday at week-end; if that Sunday
        # hasn't arrived yet the bar covers a partial week of trading data).
        today_ts = pd.Timestamp.now().normalize()
        if len(weekly) > 0 and weekly.index[-1].normalize() > today_ts:
            weekly = weekly.iloc[:-1]
        # Fetch SPY
        try:
            spy_raw = yf.download('SPY', period='3y', interval='1d', progress=False, auto_adjust=True)
            if isinstance(spy_raw.columns, pd.MultiIndex):
                spy_raw.columns = spy_raw.columns.get_level_values(0)
            if len(spy_raw) > 0 and spy_raw.index[-1].date() == today:
                spy_raw = spy_raw.iloc[:-1]
            spy_daily = spy_raw[['Close']].copy()
        except Exception:
            spy_daily = pd.DataFrame({'Close': [np.nan]})
        meta = {'symbol': symbol, 'asset': 'stock'}
        return raw, weekly, meta, spy_daily
    except Exception as e:
        empty = pd.DataFrame({'Open':[np.nan],'High':[np.nan],'Low':[np.nan],'Close':[np.nan],'Volume':[np.nan]},
                              index=[pd.Timestamp.now()])
        empty_w = empty.copy()
        spy_daily = pd.DataFrame({'Close': [np.nan]}, index=[pd.Timestamp.now()])
        meta = {'symbol': symbol, 'asset': 'stock', 'error': str(e)}
        return empty, empty_w, meta, spy_daily

def fetch_crypto_with_fallback(base, forced_exchange=None):
    """Fetch daily + weekly OHLCV, trying exchanges in order until one works.

    Binance is geo-blocked in some environments, so the chain falls through to
    coinbase/kraken/kucoin/okx. Returns (daily_df, weekly_df, meta) where meta
    carries the exchange that actually served the data. If every venue fails,
    returns empty frames with meta['degraded'] = True.
    """
    import ccxt
    chain = [forced_exchange] if forced_exchange else EXCHANGE_CHAIN
    today = pd.Timestamp.now().date()

    for exchange_id in chain:
        try:
            symbol = resolve_symbol(base, exchange_id)
            exchange = getattr(ccxt, exchange_id)({'enableRateLimit': True})

            ohlcv_d = exchange.fetch_ohlcv(symbol, '1d', limit=500)
            if not ohlcv_d or len(ohlcv_d) < 100:
                continue

            df = pd.DataFrame(ohlcv_d, columns=['ts','Open','High','Low','Close','Volume'])
            df.index = pd.to_datetime(df['ts'], unit='ms')
            df.drop(columns=['ts'], inplace=True)
            if len(df) > 0 and df.index[-1].date() == today:
                df = df.iloc[:-1]

            # Weekly bars: try native '1w', else resample daily → weekly. Some
            # venues (coinbase/kraken) don't expose a weekly interval.
            dfw = None
            try:
                ohlcv_w = exchange.fetch_ohlcv(symbol, '1w', limit=200)
                if ohlcv_w and len(ohlcv_w) >= 20:
                    dfw = pd.DataFrame(ohlcv_w, columns=['ts','Open','High','Low','Close','Volume'])
                    dfw.index = pd.to_datetime(dfw['ts'], unit='ms')
                    dfw.drop(columns=['ts'], inplace=True)
                    # For ccxt '1w', the timestamp is the candle open (week start).
                    # Drop the last bar if it started less than 7 days ago (unclosed week).
                    if len(dfw) > 0 and (pd.Timestamp.now() - dfw.index[-1]).days < 7:
                        dfw = dfw.iloc[:-1]
            except Exception:
                dfw = None

            if dfw is None or len(dfw) < 20:
                dfw = df.resample('W', label='right', closed='right').agg(
                    {'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
                # Drop partial current week (period-end label is in the future)
                today_ts = pd.Timestamp.now().normalize()
                if len(dfw) > 0 and dfw.index[-1].normalize() > today_ts:
                    dfw = dfw.iloc[:-1]

            meta = {'symbol': symbol, 'asset': 'crypto', 'exchange': exchange_id}
            return df, dfw, meta
        except Exception:
            continue  # try next exchange

    empty = pd.DataFrame({'Open':[np.nan],'High':[np.nan],'Low':[np.nan],'Close':[np.nan],'Volume':[np.nan]},
                          index=[pd.Timestamp.now()])
    meta = {'symbol': '', 'asset': 'crypto', 'exchange': 'none', 'degraded': True}
    return empty, empty.copy(), meta


def fetch_funding_oi(base):
    """Fetch funding rate and OI from the OKX perp, independent of OHLCV.

    Fully optional — never raises. Returns (funding_rate_str, oi_trend) where
    funding_rate is a formatted percent string or '[UNAVAILABLE]'.
    """
    import ccxt
    perp_symbol = f"{base}/USDT:USDT"

    try:
        exchange = ccxt.okx({'enableRateLimit': True})
        fr_data = exchange.fetch_funding_rate(perp_symbol)
        funding_rate = fr_data.get('fundingRate', None)
        if funding_rate is not None:
            funding_rate = f"{funding_rate*100:.4f}%"
        else:
            funding_rate = '[UNAVAILABLE]'
    except Exception:
        funding_rate = '[UNAVAILABLE]'

    try:
        exchange = ccxt.okx({'enableRateLimit': True})
        oi_data = exchange.fetch_open_interest(perp_symbol)
        oi_val = oi_data.get('openInterest', None) or oi_data.get('openInterestValue', None)
        oi_trend = 'available' if oi_val else '[UNAVAILABLE]'
    except Exception:
        oi_trend = '[UNAVAILABLE]'

    return funding_rate, oi_trend


# ── compute_features ──────────────────────────────────────────────────────────

def _safe(val, fallback=np.nan):
    try:
        f = float(val)
        return fallback if np.isnan(f) else f
    except Exception:
        return fallback

def compute_features(daily, weekly, asset, exchange=None, symbol=None):
    degraded = []
    feats = {}

    def guard(key, fn, fallback=np.nan):
        try:
            v = fn()
            feats[key] = v
        except Exception:
            feats[key] = fallback
            degraded.append(key)

    # price
    guard('price', lambda: float(daily['Close'].dropna().iloc[-1]))

    # MA series
    daily_close = daily['Close'].dropna()
    guard('ma50', lambda: float(sma(daily_close, 50).iloc[-1]))
    guard('ma200', lambda: float(sma(daily_close, 200).iloc[-1]))

    weekly_close = weekly['Close'].dropna() if 'Close' in weekly.columns else pd.Series([np.nan])
    guard('ma30w', lambda: float(sma(weekly_close, 30).iloc[-1]))

    # Slopes
    guard('slope_50d', lambda: ma_slope(sma(daily_close, 50)))
    guard('slope_200d', lambda: ma_slope(sma(daily_close, 200)))
    guard('slope_30w', lambda: ma_slope(sma(weekly_close, 30)))

    # RSI
    guard('rsi_d', lambda: float(rsi(daily_close, 14).dropna().iloc[-1]))
    guard('rsi_w', lambda: float(rsi(weekly_close, 14).dropna().iloc[-1]))

    # MACD
    def _macd():
        line, sig, hist = macd(daily_close, 12, 26, 9)
        last_hist = float(hist.iloc[-1])
        trend = 'rising' if float(hist.iloc[-1]) > float(hist.iloc[-2]) else 'falling'
        return last_hist, trend
    try:
        feats['macd_hist_last'], feats['macd_hist_trend'] = _macd()
    except Exception:
        feats['macd_hist_last'] = np.nan
        feats['macd_hist_trend'] = 'unknown'
        degraded.extend(['macd_hist_last', 'macd_hist_trend'])

    # OBV
    def _obv():
        vol = daily['Volume'].dropna()
        cl = daily_close
        obv_s = obv(cl, vol)
        last_obv = float(obv_s.iloc[-1])
        ref_obv = float(obv_s.iloc[-20]) if len(obv_s) >= 20 else float(obv_s.iloc[0])
        if abs(ref_obv) < 1e-9:
            trend = 'flat'
        else:
            pct = (last_obv - ref_obv) / abs(ref_obv) * 100
            trend = 'rising' if pct > 1 else ('falling' if pct < -1 else 'flat')
        return last_obv, trend
    try:
        feats['obv_d'], feats['obv_trend'] = _obv()
    except Exception:
        feats['obv_d'] = np.nan
        feats['obv_trend'] = 'flat'
        degraded.extend(['obv_d', 'obv_trend'])

    # Volume ratio
    guard('vol_ratio', lambda: volume_ratio(daily['Volume'], 20))

    # Weinstein stage
    def _stage():
        weekly_30w = sma(weekly_close, 30)
        return weinstein_stage(weekly_close, weekly_30w)
    guard('stage', _stage, fallback=1)

    # Support/Resistance
    def _sr():
        sup, res = support_resistance(daily_close)
        return sup, res
    try:
        feats['support'], feats['resistance'] = _sr()
    except Exception:
        feats['support'] = feats.get('price', np.nan) * 0.95
        feats['resistance'] = feats.get('price', np.nan) * 1.05
        degraded.extend(['support', 'resistance'])

    # Distance %
    price = feats.get('price', np.nan)
    ma50 = feats.get('ma50', np.nan)
    ma200 = feats.get('ma200', np.nan)
    try:
        feats['dist_50d_pct'] = (price - ma50) / ma50 * 100 if ma50 and not np.isnan(ma50) else np.nan
    except Exception:
        feats['dist_50d_pct'] = np.nan
        degraded.append('dist_50d_pct')
    try:
        feats['dist_200d_pct'] = (price - ma200) / ma200 * 100 if ma200 and not np.isnan(ma200) else np.nan
    except Exception:
        feats['dist_200d_pct'] = np.nan
        degraded.append('dist_200d_pct')

    # Divergence
    def _div():
        daily_rsi = rsi(daily_close, 14)
        return divergence(daily_close, daily_rsi, lookback=60)
    guard('div', _div, fallback='none')

    # Verdict
    def _verdict():
        price_v = feats.get('price', np.nan)
        if price_v is None or (isinstance(price_v, float) and np.isnan(price_v)):
            # Never emit a confident verdict when price data is missing
            return {'verdict': '[UNAVAILABLE]', 'entry_low': np.nan, 'entry_high': np.nan,
                    'invalidation': np.nan, 'level': np.nan}
        vf = {
            'stage': feats.get('stage', 1),
            'price': feats.get('price', 0),
            'dist_50d': feats.get('dist_50d_pct', 0) or 0,
            'dist_200d': feats.get('dist_200d_pct', 0) or 0,
            'rsi_w': feats.get('rsi_w', 50) or 50,
            'obv_trend': feats.get('obv_trend', 'flat'),
            'div': feats.get('div', 'none'),
            'support': feats.get('support', 0),
            'resistance': feats.get('resistance', 0),
            'ma50': feats.get('ma50', 0) or 0,
            'ma200': feats.get('ma200', 0) or 0,
        }
        return verdict(vf)
    guard('verdict_dict', _verdict, fallback={'verdict':'WAIT-PULLBACK','entry_low':0,'entry_high':0,'invalidation':0,'level':0})

    # Crypto extras (funding/OI) are fetched independently in main() via
    # fetch_funding_oi — kept out of compute_features so price data and
    # derivatives data fail independently.

    # Stock extras
    if asset == 'stock':
        try:
            # rel strength vs SPY
            feats['rel_strength'] = 'neutral'  # will be overridden below
        except Exception:
            feats['rel_strength'] = 'neutral'

    feats['degraded_fields'] = degraded
    return feats


# ── Formatting helpers ────────────────────────────────────────────────────────

def _fmt(val, fmt='.2f', fallback='N/A'):
    try:
        f = float(val)
        if np.isnan(f):
            return fallback
        return format(f, fmt)
    except Exception:
        return fallback

def _sfmt(val, fallback='N/A'):
    try:
        return str(val)
    except Exception:
        return fallback

def _pct(val, fmt='.1f', fallback='N/A'):
    try:
        f = float(val)
        if np.isnan(f):
            return fallback
        return format(f, fmt) + '%'
    except Exception:
        return fallback


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='TA engine')
    parser.add_argument('symbol', type=str)
    parser.add_argument('--asset', type=str, default='auto')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--exchange', type=str, default=None)
    args = parser.parse_args()

    sym = args.symbol.upper()
    asset = args.asset
    if asset == 'auto':
        if '/' in sym or sym in CRYPTO_TICKERS:
            asset = 'crypto'
        else:
            asset = 'stock'

    # Fetch
    exchange_obj = None
    spy_daily = None
    crypto_meta = {}
    if asset == 'crypto':
        base = sym.split('/')[0] if '/' in sym else sym
        daily, weekly, crypto_meta = fetch_crypto_with_fallback(base, forced_exchange=args.exchange)
    else:
        daily, weekly, meta, spy_daily = fetch_stock(sym)

    # Compute
    feats = compute_features(daily, weekly, asset, exchange=exchange_obj, symbol=sym)

    # Funding/OI fetched independently from price data (OKX perp).
    if asset == 'crypto':
        base = sym.split('/')[0] if '/' in sym else sym
        funding_rate, oi_trend = fetch_funding_oi(base)
        feats['funding_rate'] = funding_rate
        feats['oi_trend'] = oi_trend

    # Rel strength for stocks (needs spy_daily)
    if asset == 'stock' and spy_daily is not None:
        try:
            daily_close = daily['Close'].dropna()
            spy_close = spy_daily['Close'].dropna()
            n = min(60, len(daily_close)-1, len(spy_close)-1)
            if n > 0:
                sym_ret = float(daily_close.iloc[-1] / daily_close.iloc[-1-n] - 1)
                spy_ret = float(spy_close.iloc[-1] / spy_close.iloc[-1-n] - 1)
                if sym_ret > spy_ret + 0.02:
                    feats['rel_strength'] = 'out'
                elif sym_ret < spy_ret - 0.02:
                    feats['rel_strength'] = 'under'
                else:
                    feats['rel_strength'] = 'neutral'
        except Exception:
            feats['rel_strength'] = 'neutral'
            feats['degraded_fields'].append('rel_strength')

    vd = feats.get('verdict_dict', {})

    # Shared metadata (used by both json and text paths)
    stage_names = {1: 'basing', 2: 'advancing', 3: 'topping', 4: 'declining'}
    stage_val = feats.get('stage', 1)
    stage_label = stage_names.get(stage_val, 'unknown')
    try:
        asof = daily.index[-1].strftime('%Y-%m-%d')
    except Exception:
        asof = 'unknown'
    today_str = pd.Timestamp.now().strftime('%Y-%m-%d')
    if asset == 'crypto':
        data_src = f"{crypto_meta.get('exchange', 'none')}/ccxt"
    else:
        data_src = 'yfinance'

    if args.json:
        def _jnum(v):
            try:
                f = float(v)
                return None if np.isnan(f) else f
            except (TypeError, ValueError):
                return v

        out = {
            'symbol': sym,
            'asset': asset,
            'date': today_str,
            'price': _jnum(feats.get('price')),
            'stage': stage_val,
            'stage_label': stage_label,
            'ma50': _jnum(feats.get('ma50')),
            'ma200': _jnum(feats.get('ma200')),
            'ma30w': _jnum(feats.get('ma30w')),
            'slope_50d': feats.get('slope_50d'),
            'slope_200d': feats.get('slope_200d'),
            'slope_30w': feats.get('slope_30w'),
            'rsi_d': _jnum(feats.get('rsi_d')),
            'rsi_w': _jnum(feats.get('rsi_w')),
            'macd_hist_last': _jnum(feats.get('macd_hist_last')),
            'macd_hist_trend': feats.get('macd_hist_trend'),
            'obv_trend': feats.get('obv_trend'),
            'vol_ratio': _jnum(feats.get('vol_ratio')),
            'divergence': feats.get('div', 'none'),
            'support': _jnum(feats.get('support')),
            'resistance': _jnum(feats.get('resistance')),
            'dist_50d_pct': _jnum(feats.get('dist_50d_pct')),
            'dist_200d_pct': _jnum(feats.get('dist_200d_pct')),
            'verdict': vd.get('verdict'),
            'entry_low': _jnum(vd.get('entry_low')),
            'entry_high': _jnum(vd.get('entry_high')),
            'invalidation': _jnum(vd.get('invalidation')),
            'level': _jnum(vd.get('level')),
            'data_source': data_src,
            'asof': asof,
            'degraded_fields': feats.get('degraded_fields', []),
        }
        if asset == 'crypto':
            fr = feats.get('funding_rate')
            out['funding_rate'] = fr if fr not in (None, '') else '[UNAVAILABLE]'
            oi = feats.get('oi_trend')
            out['oi_trend'] = oi if oi not in (None, '', 'unknown') else '[UNAVAILABLE]'
        else:
            out['rel_strength_vs_spy'] = feats.get('rel_strength', 'neutral')
        print(json.dumps(out, indent=2))
        return

    # Human-readable output
    stage = stage_val

    price = feats.get('price', 0)
    ma50 = feats.get('ma50', 0) or 0
    ma200 = feats.get('ma200', 0) or 0
    slope_200d = feats.get('slope_200d', 'flat')
    slope_30w = feats.get('slope_30w', 'flat')

    above_below_200 = 'above' if price >= (ma200 or 0) else 'below'
    ma_dir = slope_200d if slope_200d in ('rising','falling','flat') else 'flat'
    slope_30w_str = 'up' if slope_30w == 'rising' else ('down' if slope_30w == 'falling' else 'flat')

    support = feats.get('support', price * 0.95)
    resistance = feats.get('resistance', price * 1.05)
    dist_50 = feats.get('dist_50d_pct', np.nan)
    dist_200 = feats.get('dist_200d_pct', np.nan)

    if isinstance(dist_50, (int, float)) and not np.isnan(dist_50) and dist_50 > 15:
        struct_state = 'extended'
    elif price >= resistance * 0.99:
        struct_state = 'breakout'
    else:
        struct_state = 'in base'

    rsi_d = feats.get('rsi_d', np.nan)
    rsi_w_val = feats.get('rsi_w', np.nan)
    if isinstance(rsi_w_val, (int, float)) and not np.isnan(rsi_w_val) and rsi_w_val > 70:
        rsi_label = 'OB'
    elif isinstance(rsi_w_val, (int, float)) and not np.isnan(rsi_w_val) and rsi_w_val < 30:
        rsi_label = 'OS'
    else:
        rsi_label = 'neutral'

    macd_hist_last = feats.get('macd_hist_last', 0) or 0
    macd_hist_trend = feats.get('macd_hist_trend', 'flat')
    macd_zero = 'above' if macd_hist_last >= 0 else 'below'

    div_str = feats.get('div', 'none')

    obv_trend = feats.get('obv_trend', 'flat')
    vol_ratio_val = feats.get('vol_ratio', np.nan)
    vol_action = 'accumulation' if obv_trend == 'rising' else ('distribution' if obv_trend == 'falling' else 'neutral')

    # Confluence
    verd = vd.get('verdict', '')
    if verd == '[UNAVAILABLE]':
        confluence = '[UNAVAILABLE]'
    elif (stage == 2 and verd in {'ACCUMULATE','BUY-ZONE'}) or \
       (stage == 4 and verd == 'AVOID-DOWNTREND') or \
       (stage == 1 and verd == 'WAIT-BREAKOUT') or \
       (stage == 3 and verd == 'WAIT-PULLBACK'):
        confluence = 'AGREES'
    else:
        confluence = 'CONFLICTS'

    entry_low = vd.get('entry_low', 0) or 0
    entry_high = vd.get('entry_high', 0) or 0
    invalidation = vd.get('invalidation', 0) or 0
    level = vd.get('level', 0) or 0

    # Last bar date / source already computed above
    degraded = feats.get('degraded_fields', [])
    degraded_str = f' | DEGRADED: {",".join(degraded)}' if degraded else ''

    notes_parts = []
    if asset == 'crypto':
        fr = feats.get('funding_rate', None)
        oi = feats.get('oi_trend', None)
        fr_str = fr if fr not in (None, '') else '[UNAVAILABLE]'
        oi_str = oi if oi not in (None, '', 'unknown') else '[UNAVAILABLE]'
        notes_parts.append(f"funding {fr_str}, OI {oi_str}")
    else:
        rs = feats.get('rel_strength', 'neutral')
        notes_parts.append(f"rel-str vs SPY {rs}-performing")
    notes = ' | '.join(notes_parts)

    print(f"=== ENTRY READ — {sym} ({asset}) — {today_str} ===")
    print(f"Horizon:     position/swing — weekly trend gates the daily entry")
    print(f"Price:       {_fmt(price)}")
    print(f"TREND/STAGE: Weekly Stage {stage} ({stage_label}) | 200d {above_below_200}, MA {ma_dir} | 30wk-MA slope {slope_30w_str}")
    print(f"STRUCTURE:   support {_fmt(support)} / resistance {_fmt(resistance)} | dist 50d {_pct(dist_50)} / 200d {_pct(dist_200)} | {struct_state}")
    print(f"MOMENTUM:    RSI14 D={_fmt(rsi_d, '.1f')} W={_fmt(rsi_w_val, '.1f')} ({rsi_label}) | MACD(12,26,9) hist {macd_hist_trend}, {macd_zero} zero | div {div_str}")
    print(f"VOLUME:      OBV {obv_trend} | last vol {_fmt(vol_ratio_val, '.2f')}x20avg | {vol_action}")
    print(f"CONFLUENCE:  weekly trend {confluence} with the daily setup")
    if verd == '[UNAVAILABLE]':
        print(f"VERDICT:     [UNAVAILABLE]")
        print(f"ENTRY ZONE:  [UNAVAILABLE]")
        print(f"INVALIDATION:[UNAVAILABLE]")
    else:
        print(f"VERDICT:     {verd} {_fmt(level)}")
        print(f"ENTRY ZONE:  {_fmt(entry_low)}–{_fmt(entry_high)}")
        print(f"INVALIDATION:{_fmt(invalidation)} — sustained close beyond = thesis wrong")
    print(f"NOTES:       {notes}")
    print(f"HONESTY:     Lens, not gospel. TA evidence base is weak/mixed; validate via analyst-systematic-trading before sizing.")
    print(f"DATA:        {data_src} | asof {asof}{degraded_str}")


if __name__ == '__main__':
    main()
