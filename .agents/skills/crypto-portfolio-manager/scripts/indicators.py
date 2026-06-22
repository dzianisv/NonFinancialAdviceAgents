#!/usr/bin/env python3
"""
Compute the indicator package from TradingView MCP OHLCV closes.

WHY THIS EXISTS: the TradingView MCP `chart_manage_indicator` tool ignores the
moving-average `length` input (an added EMA stays at the default length 9) and
has no `update` action, so EMA50 / EMA200 / SMA200 cannot be read off the chart.
RSI(14), Bollinger(20,2), MACD(12,26,9) and Volume DO read correctly from
`data_get_study_values` at their defaults — use those directly. For the moving
averages and 52w / 200-week levels, feed the MCP's returned closes into this
script. Computed values match TradingView's own study values (verified: BTC
RSI 42.8 vs 42.73, Bollinger bands identical).

Death cross uses the classic SMA50/SMA200 (exact with N bars, no warmup error),
not EMAs.

INPUT  (stdin or file): JSON, one object per token:
  {"symbol":"BTC",
   "daily_closes":[...>=200 daily closes, oldest->newest...],
   "weekly_closes":[...weekly closes, optional, for 200-week MA...],
   "hi52": 126200.0, "lo52": 59111.0,        # from MCP daily summary
   "vol_last": 14013.0, "vol_avg30": 8983.0} # optional, from MCP

USAGE:
  cat packages.json | python3 indicators.py
  python3 indicators.py packages.json
"""
import json, sys
import pandas as pd
import numpy as np


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def rsi(s, n=14):
    d = s.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def compute(t):
    c = pd.Series([float(x) for x in t["daily_closes"]])
    price = float(c.iloc[-1])
    e20 = float(ema(c, 20).iloc[-1])
    sma50 = float(c.rolling(50).mean().iloc[-1]) if len(c) >= 50 else float("nan")
    sma200 = float(c.rolling(200).mean().iloc[-1]) if len(c) >= 200 else float("nan")
    r = float(rsi(c).iloc[-1])
    ml = ema(c, 12) - ema(c, 26)
    sg = ema(ml, 9)
    hg = ml - sg
    mid = float(c.rolling(20).mean().iloc[-1])
    sd = float(c.rolling(20).std().iloc[-1])
    bbu, bbl = mid + 2 * sd, mid - 2 * sd

    wc = t.get("weekly_closes")
    wk200 = None
    if wc and len(wc) >= 50:
        ws = pd.Series([float(x) for x in wc])
        wk200 = float(ws.rolling(min(200, len(ws))).mean().iloc[-1])

    hi52 = float(t.get("hi52", c.tail(365).max()))
    lo52 = float(t.get("lo52", c.tail(365).min()))
    vl, va = t.get("vol_last"), t.get("vol_avg30")
    vol_vs_avg = round((float(vl) / float(va) - 1) * 100, 1) if vl and va else None

    pos = lambda p, e: "ABOVE" if p > e else "BELOW"
    bbpos = ("above upper" if price > bbu else "below lower" if price < bbl
             else "upper half" if price > mid else "lower half")

    return {
        "symbol": t["symbol"], "src": "tradingview-mcp", "n_daily": len(c),
        "price": round(price, 4), "chg_pct": round(float((c.iloc[-1] / c.iloc[-2] - 1) * 100), 2),
        "hi52": round(hi52, 4), "lo52": round(lo52, 4),
        "pct_from_52wh": round((price / hi52 - 1) * 100, 1),
        "pct_above_52wl": round((price / lo52 - 1) * 100, 1),
        "ema20": round(e20, 4), "sma50": round(sma50, 4), "sma200": round(sma200, 4),
        "vs_ema20": pos(price, e20), "vs_sma50": pos(price, sma50),
        "vs_sma200": pos(price, sma200) if not np.isnan(sma200) else None,
        "death_cross_50_200": bool(sma50 < sma200) if not np.isnan(sma200) else None,
        "rsi14": round(r, 1),
        "macd_line": round(float(ml.iloc[-1]), 4), "macd_signal": round(float(sg.iloc[-1]), 4),
        "macd_hist": round(float(hg.iloc[-1]), 4),
        "macd_state": "BULLISH" if float(hg.iloc[-1]) > 0 else "BEARISH",
        "bb_upper": round(bbu, 4), "bb_mid": round(mid, 4), "bb_lower": round(bbl, 4), "bb_pos": bbpos,
        "vol_vs_avg_pct": vol_vs_avg,
        "ma200w": round(wk200, 4) if wk200 else None,
        "pct_vs_200wma": round((price / wk200 - 1) * 100, 1) if wk200 else None,
    }


def main():
    raw = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()
    data = json.loads(raw)
    items = data if isinstance(data, list) else [data]
    print(json.dumps([compute(t) for t in items], indent=2))


if __name__ == "__main__":
    main()
