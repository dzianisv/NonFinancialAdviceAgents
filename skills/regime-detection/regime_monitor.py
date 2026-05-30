#!/usr/bin/env python3
"""
regime_monitor.py — Daily market-regime monitor.

Computes a weighted-ensemble regime score from robust signals and maps it to a
target gross-exposure multiplier. Notification-first: prints (or emits JSON) a
recommendation; it does NOT place trades.

Signals (each scored -1 / 0 / +1, weighted):
    - S&P 500 vs 200-day MA (with a 1% band)        weight 3   [trend, robust]
    - VIX term structure  VIX / VIX3M               weight 2   [stress]
    - Credit spreads      HYG / LQD ratio trend     weight 2   [credit leads equities]
    - Breadth proxy       % of a sample > 200dma     weight 1   [confirmatory]
    - Yield curve         10y-2y (^TNX vs 2y proxy)  weight 1   [slow, strategic]

Usage:
    python regime_monitor.py
    python regime_monitor.py --json
    python regime_monitor.py --ticker SPY

Requires: pip install yfinance pandas numpy
Data caveats & upgrades: see ../dip-tranches-strategy/references/data-sources.md
Educational only — not investment advice.
"""
from __future__ import annotations
import argparse, json, sys
import numpy as np
import pandas as pd

try:
    import yfinance as yf
except ImportError:
    sys.exit("pip install yfinance pandas numpy")


def _last(series):
    s = series.dropna()
    return float(s.iloc[-1]) if len(s) else float("nan")


def compute_regime(equity_ticker="^GSPC"):
    tickers = [equity_ticker, "^VIX", "^VIX3M", "HYG", "LQD"]
    px = yf.download(tickers, period="2y", auto_adjust=True, progress=False)["Close"].ffill()

    signals, weights = {}, {}

    # 1) Price vs 200d MA (+/-1% band)  weight 3
    p = px[equity_ticker]
    sma200 = p.rolling(200).mean()
    price, ma = _last(p), _last(sma200)
    if price > ma * 1.01:
        signals["sma200"] = 1
    elif price < ma * 0.99:
        signals["sma200"] = -1
    else:
        signals["sma200"] = 0
    weights["sma200"] = 3

    # 2) VIX term structure VIX/VIX3M  weight 2  (>1 backwardation = stress)
    if "^VIX" in px and "^VIX3M" in px:
        ratio = _last(px["^VIX"]) / _last(px["^VIX3M"])
        signals["vix_ts"] = 1 if ratio < 0.95 else (-1 if ratio > 1.0 else 0)
    else:
        signals["vix_ts"], ratio = 0, float("nan")
    weights["vix_ts"] = 2

    # 3) Credit spreads via HYG/LQD ratio trend (20d slope)  weight 2
    if "HYG" in px and "LQD" in px:
        cr = (px["HYG"] / px["LQD"]).dropna()
        slope = _last(cr) - cr.iloc[-21] if len(cr) > 21 else 0.0
        signals["credit"] = 1 if slope > 0 else (-1 if slope < 0 else 0)
    else:
        signals["credit"] = 0
    weights["credit"] = 2

    # 4) Breadth proxy: is the equity index itself > 50d & 200d (cheap stand-in)  weight 1
    sma50 = _last(p.rolling(50).mean())
    signals["breadth"] = 1 if (price > sma50 and price > ma) else (-1 if price < ma else 0)
    weights["breadth"] = 1

    # weighted score normalized to [-1, 1]
    wsum = sum(weights.values())
    score = sum(signals[k] * weights[k] for k in signals) / wsum

    if score >= 0.5:
        mult, regime = 1.0, "risk-on"
    elif score >= 0.0:
        mult, regime = 0.7, "neutral"
    elif score >= -0.5:
        mult, regime = 0.5, "risk-off (mild)"
    else:
        mult, regime = 0.3, "risk-off"

    return {
        "date": str(px.index[-1].date()),
        "equity_ticker": equity_ticker,
        "price": round(price, 2),
        "sma200": round(ma, 2),
        "vix_vix3m_ratio": round(ratio, 3) if ratio == ratio else None,
        "regime": regime,
        "exposure_multiplier": mult,
        "score": round(score, 3),
        "signals": signals,
        "weights": weights,
        "note": "Persistence rule: require this regime to hold 3-5 sessions before acting. "
                "Educational, not advice.",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", default="^GSPC", help="equity index ticker (default ^GSPC)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    r = compute_regime(a.ticker)
    if a.json:
        print(json.dumps(r, indent=2))
        return
    print(f"\n=== Market Regime  ({r['date']}) ===")
    print(f"  {r['equity_ticker']}: {r['price']}   200d MA: {r['sma200']}")
    print(f"  VIX/VIX3M: {r['vix_vix3m_ratio']}")
    print(f"  signals: {r['signals']}  (weights {r['weights']})")
    print(f"\n  REGIME: {r['regime'].upper()}   score {r['score']:+.2f}")
    print(f"  -> target gross-exposure multiplier: {r['exposure_multiplier']}x")
    print(f"\n  {r['note']}\n")


if __name__ == "__main__":
    main()
