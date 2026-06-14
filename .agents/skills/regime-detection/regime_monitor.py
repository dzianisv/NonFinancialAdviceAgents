#!/usr/bin/env python3
"""
regime_monitor.py — Daily market-regime monitor.

Computes a weighted-ensemble regime score from robust signals:
  - S&P 500 vs 200-day MA (weight 3)
  - VIX term structure VIX/VIX3M (weight 2)
  - HY credit spreads via FRED BAMLH0A0HYM2 (weight 2)

Requires: pip install yfinance
  yfinance handles Yahoo Finance session cookies automatically.

Usage:
    python3 regime_monitor.py
    python3 regime_monitor.py --json
    python3 regime_monitor.py --ticker SPY

Educational only — not investment advice.
"""
from __future__ import annotations
import argparse, json, sys
from urllib.request import Request, urlopen

try:
    import yfinance as yf
except ImportError:
    sys.exit("pip install yfinance")


def _fetch_fred_last(series_id: str) -> float | None:
    """Fetch the most recent value from a FRED series CSV."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(req, timeout=15) as r:
            lines = r.read().decode().strip().split("\n")
        last = lines[-1].split(",")
        val = last[1].strip() if len(last) > 1 else "."
        return float(val) if val not in (".", "", "NA") else None
    except Exception:
        return None


def compute_regime(equity_ticker: str = "SPY") -> dict:
    signals: dict[str, int] = {}
    weights: dict[str, int] = {}
    data: dict = {}

    # Download price data via yfinance (handles cookies/crumb automatically)
    tickers = [equity_ticker, "^VIX", "^VIX3M"]
    px = yf.download(tickers, period="1y", auto_adjust=True, progress=False)["Close"].ffill()

    def _last(col):
        s = px[col].dropna()
        return float(s.iloc[-1]) if len(s) else float("nan")

    # 1) Price vs 200-day MA (weight 3)
    p = px[equity_ticker].dropna()
    price = float(p.iloc[-1])
    sma200 = float(p.rolling(200).mean().iloc[-1])
    data["equity_ticker"] = equity_ticker
    data["price"] = round(price, 2)
    data["sma200"] = round(sma200, 2)
    if price > sma200 * 1.01:
        signals["sma200"] = 1
    elif price < sma200 * 0.99:
        signals["sma200"] = -1
    else:
        signals["sma200"] = 0
    weights["sma200"] = 3

    # 2) VIX term structure VIX/VIX3M (weight 2)
    vix = _last("^VIX")
    vix3m = _last("^VIX3M")
    data["vix"] = round(vix, 2) if vix == vix else None
    data["vix3m"] = round(vix3m, 2) if vix3m == vix3m else None
    if vix == vix and vix3m == vix3m and vix3m != 0:
        ratio = vix / vix3m
        data["vix_vix3m_ratio"] = round(ratio, 3)
        signals["vix_ts"] = 1 if ratio < 0.95 else (-1 if ratio > 1.0 else 0)
    else:
        data["vix_vix3m_ratio"] = None
        signals["vix_ts"] = 0
    weights["vix_ts"] = 2

    # 3) HY credit spreads via FRED BAMLH0A0HYM2 OAS in % (weight 2)
    hy_oas = _fetch_fred_last("BAMLH0A0HYM2")
    data["hy_oas_pct"] = round(hy_oas, 2) if hy_oas is not None else None
    if hy_oas is not None:
        # OAS in %; < 3.5% = tight (risk-on); > 5.0% = wide (risk-off)
        signals["credit"] = 1 if hy_oas < 3.5 else (-1 if hy_oas > 5.0 else 0)
    else:
        signals["credit"] = 0
    weights["credit"] = 2

    wsum = sum(weights.values())
    score = sum(signals[k] * weights[k] for k in signals) / wsum

    if score >= 0.5:
        mult, regime = 1.0, "RISK_ON"
    elif score >= 0.0:
        mult, regime = 0.7, "NEUTRAL"
    elif score >= -0.5:
        mult, regime = 0.5, "RISK_OFF (mild)"
    else:
        mult, regime = 0.3, "RISK_OFF"

    return {
        "regime": regime,
        "exposure_multiplier": mult,
        "score": round(score, 3),
        "signals": signals,
        "weights": weights,
        **data,
        "note": (
            "Persistence rule: require regime to hold 3-5 sessions before acting. "
            "Educational, not advice."
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Regime monitor")
    ap.add_argument("--ticker", default="SPY", help="equity ticker (default SPY)")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    a = ap.parse_args()

    try:
        r = compute_regime(a.ticker)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    if a.json:
        print(json.dumps(r, indent=2))
        return

    print(f"\n=== Market Regime ===")
    print(f"  {r['equity_ticker']}: {r['price']}   200d MA: {r['sma200']}")
    print(f"  VIX: {r.get('vix', 'n/a')}  "
          f"VIX3M: {r.get('vix3m', 'n/a')}  "
          f"ratio: {r.get('vix_vix3m_ratio', 'n/a')}")
    print(f"  HY OAS: {r.get('hy_oas_pct', 'n/a')}%")
    print(f"  signals: {r['signals']}  (weights {r['weights']})")
    print(f"\n  REGIME: {r['regime']}   score {r['score']:+.3f}")
    print(f"  -> target gross-exposure multiplier: {r['exposure_multiplier']}x")
    print(f"\n  {r['note']}\n")


if __name__ == "__main__":
    main()
