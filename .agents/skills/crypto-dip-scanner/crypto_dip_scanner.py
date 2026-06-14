#!/usr/bin/env python3
"""
crypto_dip_scanner.py — Daily crypto dip scanner.
Checks major crypto for % below 52-week ATH, Fear & Greed, BTC funding rate.
Educational only — not investment advice.

Usage:
    python3 crypto_dip_scanner.py
    python3 crypto_dip_scanner.py --threshold 25
    python3 crypto_dip_scanner.py --json

Data sources (all free, no API key):
  - Prices:      yfinance  (BTC-USD, ETH-USD, etc.)
  - Fear & Greed: api.alternative.me/fng/
  - Funding rate: fapi.binance.com (Binance perp futures, public)
"""
from __future__ import annotations
import argparse, json, sys
from urllib.request import Request, urlopen

try:
    import yfinance as yf
except ImportError:
    sys.exit("pip install yfinance")

CRYPTO = {
    "BTC":  "BTC-USD",
    "ETH":  "ETH-USD",
    "SOL":  "SOL-USD",
    "BNB":  "BNB-USD",
    "AVAX": "AVAX-USD",
    "LINK": "LINK-USD",
}


def _get(url: str) -> dict | list | None:
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception:
        return None


def fear_greed() -> dict | None:
    d = _get("https://api.alternative.me/fng/?limit=1")
    if d and d.get("data"):
        v = d["data"][0]
        return {"value": int(v["value"]), "label": v["value_classification"]}
    return None


def btc_funding_rate() -> float | None:
    d = _get("https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=1")
    if isinstance(d, list) and d:
        return round(float(d[0]["fundingRate"]) * 100, 5)
    return None


def scan(threshold_pct: float = 20.0) -> tuple[list[dict], dict | None, float | None]:
    tickers = list(CRYPTO.values())
    try:
        raw = yf.download(tickers, period="1y", auto_adjust=True, progress=False)
        data = raw["Close"].ffill() if "Close" in raw else raw.ffill()
    except Exception:
        return [], None, None

    hits = []
    for name, yf_sym in CRYPTO.items():
        try:
            s = data[yf_sym].dropna() if yf_sym in data.columns else None
            if s is None or len(s) < 10:
                continue
            current = float(s.iloc[-1])
            ath_52w = float(s.max())
            sma200 = float(s.rolling(min(200, len(s))).mean().iloc[-1])
            pct_from_ath = (current - ath_52w) / ath_52w * 100
            pct_vs_200d = (current - sma200) / sma200 * 100
            if pct_from_ath <= -threshold_pct:
                hits.append({
                    "ticker": name,
                    "current_usd": round(current, 2),
                    "ath_52w_usd": round(ath_52w, 2),
                    "pct_from_ath": round(pct_from_ath, 1),
                    "sma200_usd": round(sma200, 2),
                    "pct_vs_200d": round(pct_vs_200d, 1),
                    "conviction": (
                        "HIGH" if pct_from_ath <= -40
                        else "MEDIUM" if pct_from_ath <= -30
                        else "WATCH"
                    ),
                })
        except Exception:
            continue

    hits.sort(key=lambda x: x["pct_from_ath"])
    return hits, fear_greed(), btc_funding_rate()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=20.0)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    hits, fg, fr = scan(a.threshold)

    if a.json:
        print(json.dumps({"dips": hits, "fear_greed": fg, "btc_funding_rate_pct": fr}, indent=2))
        return

    print("\n=== CRYPTO DIP SCANNER ===\n")
    if fg:
        zone = "BUY ZONE" if fg["value"] <= 25 else "GREED ZONE" if fg["value"] >= 75 else "NEUTRAL"
        print(f"  Fear & Greed: {fg['value']}/100 ({fg['label']})  [{zone}]")
    if fr is not None:
        fr_note = "shorts dominant" if fr < -0.01 else "overleveraged longs" if fr > 0.05 else "neutral"
        print(f"  BTC Funding:  {fr:+.4f}%  [{fr_note}]")
    print()

    if not hits:
        print(f"  No crypto >= {a.threshold:.0f}% below 52w ATH today.")
    else:
        for r in hits:
            label = {"HIGH": "[HIGH]", "MEDIUM": "[MED]", "WATCH": "[WATCH]"}[r["conviction"]]
            trend = "above" if r["pct_vs_200d"] >= 0 else "below"
            print(
                f"  {label} {r['ticker']:5s}  {r['pct_from_ath']:+.1f}% from ATH (${r['ath_52w_usd']:,.0f})  "
                f"now ${r['current_usd']:,.2f}  200dMA ${r['sma200_usd']:,.0f} ({r['pct_vs_200d']:+.1f}% {trend})"
            )
    print("\n  Educational only — not advice.\n")


if __name__ == "__main__":
    main()
