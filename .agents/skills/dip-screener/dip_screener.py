#!/usr/bin/env python3
"""
dip_screener.py — Daily quality-stock dip scanner.
Screens S&P 100 for stocks >= threshold% below 52-week ATH.
Educational only — not investment advice.

Usage:
    python3 dip_screener.py
    python3 dip_screener.py --threshold 25
    python3 dip_screener.py --json
"""
from __future__ import annotations
import argparse, json, sys, time

try:
    import yfinance as yf
except ImportError:
    sys.exit("pip install yfinance")

SP100 = [
    "AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "BRK-B", "LLY", "JPM", "V",
    "UNH", "TSLA", "XOM", "MA", "JNJ", "PG", "AVGO", "HD", "COST", "ABBV",
    "MRK", "CVX", "KO", "PEP", "ADBE", "WMT", "BAC", "CRM", "ACN", "TMO",
    "MCD", "CSCO", "ABT", "DHR", "NFLX", "ORCL", "AMD", "QCOM", "TXN", "PM",
    "NEE", "AMGN", "IBM", "INTC", "HON", "CAT", "GE", "SPGI", "MS", "GS",
    "RTX", "BLK", "T", "UNP", "AXP", "ELV", "MDT", "PFE", "BMY", "GILD",
    "USB", "C", "LOW", "DE", "SBUX", "SCHW", "MO", "BA", "MMC", "CVS",
    "SO", "DUK", "CL", "ZTS", "CB", "NOW", "ISRG", "ADI", "REGN", "SYK",
    "PLD", "AMT", "EQIX", "VRTX", "PANW", "ANET", "MU", "KLAC", "LRCX", "SNPS",
    "AON", "TGT", "FDX", "ETN", "ADP", "ITW", "NSC", "WM", "APH", "CARR",
]


def scan(threshold_pct: float = 20.0) -> list[dict]:
    results = []
    batch_size = 10
    for i in range(0, len(SP100), batch_size):
        batch = SP100[i:i + batch_size]
        try:
            raw = yf.download(batch, period="1y", auto_adjust=True, progress=False)
            data = raw["Close"].ffill() if "Close" in raw else raw.ffill()
        except Exception:
            time.sleep(2)
            continue
        for ticker in batch:
            try:
                col = ticker if ticker in data.columns else None
                if col is None:
                    continue
                s = data[col].dropna()
                if len(s) < 20:
                    continue
                current = float(s.iloc[-1])
                ath_52w = float(s.max())
                sma200 = float(s.rolling(min(200, len(s))).mean().iloc[-1])
                pct_from_ath = (current - ath_52w) / ath_52w * 100
                pct_vs_200d = (current - sma200) / sma200 * 100
                if pct_from_ath <= -threshold_pct:
                    results.append({
                        "ticker": ticker,
                        "current": round(current, 2),
                        "ath_52w": round(ath_52w, 2),
                        "pct_from_ath": round(pct_from_ath, 1),
                        "sma200": round(sma200, 2),
                        "pct_vs_200d": round(pct_vs_200d, 1),
                        "conviction": (
                            "HIGH" if pct_from_ath <= -30
                            else "MEDIUM" if pct_from_ath <= -25
                            else "WATCH"
                        ),
                    })
            except Exception:
                continue
        time.sleep(1)
    results.sort(key=lambda x: x["pct_from_ath"])
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=20.0)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    hits = scan(a.threshold)

    if a.json:
        print(json.dumps(hits, indent=2))
        return

    if not hits:
        print(f"No S&P 100 stocks >= {a.threshold:.0f}% below 52w ATH today.")
        return

    print(f"\n=== DIP SCREENER — S&P 100 stocks >= {a.threshold:.0f}% below 52-week ATH ===\n")
    for r in hits:
        label = {"HIGH": "[HIGH]", "MEDIUM": "[MED]", "WATCH": "[WATCH]"}[r["conviction"]]
        trend = "above" if r["pct_vs_200d"] >= 0 else "below"
        print(
            f"  {label} {r['ticker']:6s}  {r['pct_from_ath']:+.1f}% from ATH (${r['ath_52w']:.2f})  "
            f"now ${r['current']:.2f}  200dMA ${r['sma200']:.2f} ({r['pct_vs_200d']:+.1f}% {trend})"
        )
    print(f"\n  {len(hits)} candidate(s). Educational only — not advice.\n")


if __name__ == "__main__":
    main()
