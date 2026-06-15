#!/usr/bin/env python3
"""
regime_monitor.py — Daily market-regime monitor.

Computes a weighted-ensemble regime score from robust signals:
  - S&P 500 vs 200-day MA (weight 3)
  - VIX term structure VIX/VIX3M (weight 2)
  - HY credit spreads — FRED BAMLH0A0HYM2 OAS, else HYG/LQD proxy (weight 2)
  - Yield-curve slope 10y-3m (^TNX - ^IRX) (weight 1)

Requires: pip install yfinance
  yfinance handles Yahoo Finance session cookies automatically.

Data-source notes (validated 2026-06):
  - FRED fredgraph.csv is unreliable from sandboxes (connection drops / timeouts)
    and the FRED JSON API requires a free api_key. We try the CSV with retries +
    a browser User-Agent; if it stays blocked we fall back to the HYG/LQD credit
    proxy and LABEL the credit score "[proxy: HYG/LQD]" vs "[OAS]".
  - Yield curve uses Yahoo ^TNX (10y) and ^IRX (13-week/3m) since Yahoo has no 2y
    series; 10y-3m is an equally valid recession-curve signal.
  - Breadth (% S&P > 200dma) and Hindenburg Omen need a full-constituent or
    advance/decline + 52w-high/low feed that has no reliable free structured
    source here, so they are reported as [UNAVAILABLE] rather than silently dropped.

Usage:
    python3 regime_monitor.py
    python3 regime_monitor.py --json
    python3 regime_monitor.py --ticker SPY

Educational only — not investment advice.
"""
from __future__ import annotations
import argparse, json, sys, time
from urllib.request import Request, urlopen

try:
    import yfinance as yf
except ImportError:
    sys.exit("pip install yfinance")

_BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def _fetch_fred_last(series_id: str, retries: int = 2) -> tuple[float, str] | None:
    """Fetch the most recent (value, date) from a FRED series CSV.

    Tries the documented fredgraph.csv endpoint with a real browser User-Agent
    and a few retries (most 403s/drops are UA/throttle related). Returns None if
    the endpoint stays blocked so the caller can fall back to a labeled proxy.
    """
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    headers = {
        "User-Agent": _BROWSER_UA,
        "Accept": "text/csv,text/plain,*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "close",
    }
    for i in range(retries):
        try:
            with urlopen(Request(url, headers=headers), timeout=12) as r:
                lines = r.read().decode().strip().split("\n")
            # Walk backwards to the last row with a numeric value (FRED pads "." ).
            for row in reversed(lines[1:]):
                parts = row.split(",")
                if len(parts) < 2:
                    continue
                date_s, val_s = parts[0].strip(), parts[1].strip()
                if val_s not in (".", "", "NA"):
                    return float(val_s), date_s
            return None
        except Exception:
            if i < retries - 1:
                time.sleep(2)
    return None


def compute_regime(equity_ticker: str = "SPY") -> dict:
    signals: dict[str, int] = {}
    weights: dict[str, int] = {}
    data: dict = {}

    # Download price data via yfinance (handles cookies/crumb automatically).
    # ^TNX = 10y yield, ^IRX = 13-week (3m) yield, HYG/LQD = credit proxy.
    tickers = [equity_ticker, "^VIX", "^VIX3M", "^TNX", "^IRX", "HYG", "LQD"]
    px = yf.download(tickers, period="1y", auto_adjust=True, progress=False)["Close"].ffill()

    def _last(col):
        """Return (value, ISO-date) for the last valid observation of a column.

        The as-of date is taken from the DataFrame's own DatetimeIndex at the
        last non-NaN row for THIS column, so each quote's date label is always
        the true date of that value (fixes the mismatched-year bug from raw
        chart-JSON timestamp parsing)."""
        if col not in px:
            return float("nan"), None
        s = px[col].dropna()
        if not len(s):
            return float("nan"), None
        return float(s.iloc[-1]), s.index[-1].date().isoformat()

    data["dates"] = {}

    # 1) Price vs 200-day MA (weight 3)
    p = px[equity_ticker].dropna()
    price = float(p.iloc[-1])
    sma200 = float(p.rolling(200).mean().iloc[-1])
    data["equity_ticker"] = equity_ticker
    data["price"] = round(price, 2)
    data["sma200"] = round(sma200, 2)
    data["dates"]["price"] = p.index[-1].date().isoformat()
    if price > sma200 * 1.01:
        signals["sma200"] = 1
    elif price < sma200 * 0.99:
        signals["sma200"] = -1
    else:
        signals["sma200"] = 0
    weights["sma200"] = 3

    # 2) VIX term structure VIX/VIX3M (weight 2)
    vix, vix_d = _last("^VIX")
    vix3m, vix3m_d = _last("^VIX3M")
    data["vix"] = round(vix, 2) if vix == vix else None
    data["vix3m"] = round(vix3m, 2) if vix3m == vix3m else None
    data["dates"]["vix"] = vix_d
    data["dates"]["vix3m"] = vix3m_d
    if vix == vix and vix3m == vix3m and vix3m != 0:
        ratio = vix / vix3m
        data["vix_vix3m_ratio"] = round(ratio, 3)
        signals["vix_ts"] = 1 if ratio < 0.95 else (-1 if ratio > 1.0 else 0)
    else:
        data["vix_vix3m_ratio"] = None
        signals["vix_ts"] = 0
    weights["vix_ts"] = 2

    # 3) HY credit spreads (weight 2): prefer FRED BAMLH0A0HYM2 OAS (%); if the
    #    fredgraph endpoint stays blocked, fall back to the HYG/LQD price ratio
    #    and LABEL which source actually fired so the memo can tell them apart.
    fred = _fetch_fred_last("BAMLH0A0HYM2")
    if fred is not None:
        hy_oas, oas_date = fred
        data["credit_source"] = "[OAS]"
        data["hy_oas_pct"] = round(hy_oas, 2)
        data["dates"]["credit"] = oas_date
        # OAS in %; < 3.5% = tight (risk-on); > 5.0% = wide (risk-off)
        signals["credit"] = 1 if hy_oas < 3.5 else (-1 if hy_oas > 5.0 else 0)
    else:
        hyg, hyg_d = _last("HYG")
        lqd, lqd_d = _last("LQD")
        data["hy_oas_pct"] = None
        if hyg == hyg and lqd == lqd and lqd != 0:
            # HYG/LQD rising = HY outperforming IG = spreads tightening = risk-on.
            # Score vs the 50-day average of the ratio (trend, not absolute level).
            ratio = (px["HYG"] / px["LQD"]).dropna()
            cur = float(ratio.iloc[-1])
            avg50 = float(ratio.rolling(50).mean().iloc[-1])
            data["credit_source"] = "[proxy: HYG/LQD]"
            data["hyg_lqd_ratio"] = round(cur, 4)
            data["hyg_lqd_50d_avg"] = round(avg50, 4)
            data["dates"]["credit"] = hyg_d
            signals["credit"] = 1 if cur > avg50 * 1.005 else (-1 if cur < avg50 * 0.995 else 0)
        else:
            data["credit_source"] = "[UNAVAILABLE]"
            signals["credit"] = 0
    weights["credit"] = 2

    # 4) Yield-curve slope 10y-3m (weight 1) — ^TNX minus ^IRX, both in %.
    #    Yahoo has no 2y series, so 10y-3m stands in for 10y-2y (equally valid
    #    recession curve). Positive = risk-on; inverted = risk-off (strategic).
    tnx, tnx_d = _last("^TNX")
    irx, irx_d = _last("^IRX")
    if tnx == tnx and irx == irx:
        slope = tnx - irx
        data["curve_10y_3m"] = round(slope, 2)
        data["dates"]["curve"] = tnx_d
        signals["curve"] = 1 if slope > 0 else -1
        weights["curve"] = 1
    else:
        data["curve_10y_3m"] = "[UNAVAILABLE]"
        signals["curve"] = 0
        weights["curve"] = 0

    # 5) Breadth (% S&P > 200dma) and Hindenburg Omen: no reliable free
    #    structured source (need full constituents / advance-decline + 52w
    #    highs-lows feed). Reported honestly rather than silently omitted.
    data["breadth_pct_above_200dma"] = "[UNAVAILABLE]"
    data["hindenburg"] = "[UNAVAILABLE]"

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

    d = r.get("dates", {})
    print(f"\n=== Market Regime ===")
    print(f"  {r['equity_ticker']}: {r['price']}   200d MA: {r['sma200']}"
          f"   (as of {d.get('price', 'n/a')})")
    print(f"  VIX: {r.get('vix', 'n/a')} (as of {d.get('vix', 'n/a')})  "
          f"VIX3M: {r.get('vix3m', 'n/a')} (as of {d.get('vix3m', 'n/a')})  "
          f"ratio: {r.get('vix_vix3m_ratio', 'n/a')}")
    src = r.get("credit_source", "")
    if r.get("hy_oas_pct") is not None:
        print(f"  Credit {src}: HY OAS {r['hy_oas_pct']}%  (as of {d.get('credit', 'n/a')})")
    elif "hyg_lqd_ratio" in r:
        print(f"  Credit {src}: ratio {r['hyg_lqd_ratio']} vs 50d {r['hyg_lqd_50d_avg']}"
              f"  (as of {d.get('credit', 'n/a')})")
    else:
        print(f"  Credit {src}")
    print(f"  Yield curve (10y-3m): {r.get('curve_10y_3m', 'n/a')}"
          f"  (as of {d.get('curve', 'n/a')})")
    print(f"  Breadth (%>200dma): {r.get('breadth_pct_above_200dma')}   "
          f"Hindenburg: {r.get('hindenburg')}")
    print(f"  signals: {r['signals']}  (weights {r['weights']})")
    print(f"\n  REGIME: {r['regime']}   score {r['score']:+.3f}")
    print(f"  -> target gross-exposure multiplier: {r['exposure_multiplier']}x")
    print(f"\n  {r['note']}\n")


if __name__ == "__main__":
    main()
