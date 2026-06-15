#!/usr/bin/env python3
"""
crypto_dip_scanner.py — Daily crypto dip scanner.
Checks major crypto for % below 52-week INTRADAY high, Fear & Greed, BTC funding rate.
Educational only — not investment advice.

Usage:
    python3 crypto_dip_scanner.py
    python3 crypto_dip_scanner.py --threshold 25
    python3 crypto_dip_scanner.py --json

Data sources (all free, no API key):
  - Prices:      yfinance  (BTC-USD, ETH-USD, etc.) — High/Close, auto_adjust=False
  - Fear & Greed: api.alternative.me/fng/
  - Funding rate: OKX (primary) -> dYdX (fallback). Binance (fapi.binance.com) is
                  geo-blocked (HTTP 451) and Bybit returns 403 from many sandboxes,
                  so they are intentionally NOT used. Funding is a BONUS confirmation
                  signal only — never a hard requirement.
  - Regime x-ref: lightweight SPY vs 200d-MA check (yfinance) to surface whether
                  TradFi is RISK_OFF alongside the crypto dip. Self-contained; does
                  not depend on the regime-detection skill running.

Honesty notes:
  - "52w high" = max trailing-1y INTRADAY HIGH, not a closing max, not all-time.
  - sma200 is null when <200 days of history exist.
  - Funding conventions differ by venue: OKX returns the current 8h funding rate;
    dYdX's nextFundingRate is a 1h rate, normalized to 8h (x8) for comparability.
"""
from __future__ import annotations
import argparse, json, sys
from datetime import datetime, timezone
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
    try:
        if d and d.get("data"):
            v = d["data"][0]
            return {"value": int(v["value"]), "label": v["value_classification"]}
    except (KeyError, ValueError, TypeError):
        return None
    return None


def _ms_to_iso(ms) -> str | None:
    try:
        return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, TypeError, OSError):
        return None


def btc_funding_rate() -> dict | None:
    """Live BTC perp funding rate from a non-geo-blocked venue.

    Returns {"rate_pct", "venue", "timestamp", "interval_h"} or None if all blocked.
    Rate is reported as the venue's native funding rate in percent. OKX = 8h rate;
    dYdX is a 1h rate normalized to an 8h-equivalent (x8) so the sign/scale is
    comparable to the Binance convention this skill historically used.
    Binance (451) and Bybit (403) are deliberately skipped.
    """
    # 1) OKX — current 8h funding rate for BTC-USD perpetual swap.
    d = _get("https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USD-SWAP")
    try:
        if isinstance(d, dict) and d.get("code") == "0" and d.get("data"):
            row = d["data"][0]
            return {
                "rate_pct": round(float(row["fundingRate"]) * 100, 5),
                "venue": "OKX",
                "timestamp": _ms_to_iso(row.get("fundingTime")),
                "interval_h": 8,
            }
    except (KeyError, ValueError, TypeError, IndexError):
        pass

    # 2) dYdX v4 — nextFundingRate is a 1h rate; normalize to 8h-equivalent.
    d = _get("https://indexer.dydx.trade/v4/perpetualMarkets?ticker=BTC-USD")
    try:
        if isinstance(d, dict) and d.get("markets", {}).get("BTC-USD"):
            m = d["markets"]["BTC-USD"]
            rate_1h = float(m["nextFundingRate"])
            return {
                "rate_pct": round(rate_1h * 8 * 100, 5),
                "venue": "dYdX (1h x8)",
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "interval_h": 8,
            }
    except (KeyError, ValueError, TypeError):
        pass

    return None


def spy_regime() -> dict | None:
    """Lightweight TradFi regime cross-reference: SPY vs its 200d moving average.

    Self-contained (no dependency on the regime-detection skill). Returns
    {"ticker", "price", "sma200", "pct_vs_200d", "regime"} or None if data is
    unavailable. regime is "RISK_OFF" when price < 200d-MA, else "RISK_ON".
    """
    try:
        raw = yf.download("SPY", period="1y", auto_adjust=False, progress=False, group_by="column")
        cs = raw["Close"]
        if hasattr(cs, "columns"):  # multiindex/group_by guard
            cs = cs["SPY"]
        cs = cs.dropna()
        if len(cs) < 200:
            return None
        price = float(cs.iloc[-1])
        sma200 = float(cs.rolling(200).mean().iloc[-1])
        pct = (price - sma200) / sma200 * 100
        return {
            "ticker": "SPY",
            "price": round(price, 2),
            "sma200": round(sma200, 2),
            "pct_vs_200d": round(pct, 1),
            "regime": "RISK_OFF" if price < sma200 else "RISK_ON",
        }
    except Exception:
        return None


def scan(threshold_pct: float = 20.0) -> tuple[list[dict], dict | None, dict | None]:
    tickers = list(CRYPTO.values())
    try:
        raw = yf.download(tickers, period="1y", auto_adjust=False, progress=False, group_by="column")
        close = raw["Close"]
        high = raw["High"]
    except Exception as e:
        print(f"[crypto-dip] fetch failed: {e}", file=sys.stderr)
        return [], fear_greed(), btc_funding_rate()

    hits = []
    for name, yf_sym in CRYPTO.items():
        try:
            if yf_sym not in close.columns:
                print(f"[crypto-dip] no data for {name} (skipped)", file=sys.stderr)
                continue
            cs = close[yf_sym].dropna()
            hs = high[yf_sym].dropna()
            if len(cs) < 20 or len(hs) < 20:
                continue
            current = float(cs.iloc[-1])
            high_52w = float(hs.max())
            pct_from_high = (current - high_52w) / high_52w * 100
            if len(cs) >= 200:
                sma200 = float(cs.rolling(200).mean().iloc[-1])
                pct_vs_200d = round((current - sma200) / sma200 * 100, 1)
            else:
                sma200 = None
                pct_vs_200d = None
            if pct_from_high <= -threshold_pct:
                hits.append({
                    "ticker": name,
                    "current_usd": round(current, 2),
                    "high_52w_usd": round(high_52w, 2),
                    "pct_from_high": round(pct_from_high, 1),
                    "sma200_usd": round(sma200, 2) if sma200 is not None else None,
                    "pct_vs_200d": pct_vs_200d,
                    "conviction": (
                        "HIGH" if pct_from_high <= -40
                        else "MEDIUM" if pct_from_high <= -30
                        else "WATCH"
                    ),
                })
        except Exception as e:
            print(f"[crypto-dip] {name} parse error: {e}", file=sys.stderr)
            continue

    hits.sort(key=lambda x: x["pct_from_high"])
    return hits, fear_greed(), btc_funding_rate()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=20.0)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    hits, fg, fr = scan(a.threshold)
    regime = spy_regime()

    if a.json:
        print(json.dumps({
            "dips": hits,
            "fear_greed": fg,
            "btc_funding": fr,
            # backward-compatible scalar: the funding rate in percent (or null)
            "btc_funding_rate_pct": fr["rate_pct"] if fr else None,
            "tradfi_regime": regime,
        }, indent=2))
        return

    print("\n=== CRYPTO DIP SCANNER ===\n")
    if fg:
        zone = "BUY ZONE" if fg["value"] <= 25 else "GREED ZONE" if fg["value"] >= 75 else "NEUTRAL"
        print(f"  Fear & Greed: {fg['value']}/100 ({fg['label']})  [{zone}]")
    else:
        print("  Fear & Greed: [UNAVAILABLE]")
    if fr is not None:
        rate = fr["rate_pct"]
        fr_note = "shorts dominant" if rate < -0.01 else "overleveraged longs" if rate > 0.05 else "neutral"
        print(f"  BTC Funding:  {rate:+.4f}%  [{fr_note}]  "
              f"({fr['venue']}, {fr['interval_h']}h, {fr['timestamp']})")
    else:
        print("  BTC Funding:  [UNAVAILABLE — OKX + dYdX both unreachable]")
    if regime is not None:
        tag = "RISK_OFF — confirms crypto stress" if regime["regime"] == "RISK_OFF" else "RISK_ON"
        print(f"  TradFi (SPY): {regime['pct_vs_200d']:+.1f}% vs 200d-MA  [{tag}]")
    else:
        print("  TradFi (SPY): [UNAVAILABLE]")
    print()

    if not hits:
        print(f"  No crypto >= {a.threshold:.0f}% below 52w high today.")
    else:
        for r in hits:
            label = {"HIGH": "[HIGH]", "MEDIUM": "[MED]", "WATCH": "[WATCH]"}[r["conviction"]]
            if r["sma200_usd"] is not None:
                trend = "above" if r["pct_vs_200d"] >= 0 else "below"
                ma = f"200dMA ${r['sma200_usd']:,.0f} ({r['pct_vs_200d']:+.1f}% {trend})"
            else:
                ma = "200dMA n/a (<200d history)"
            print(
                f"  {label} {r['ticker']:5s}  {r['pct_from_high']:+.1f}% from 52w high (${r['high_52w_usd']:,.0f})  "
                f"now ${r['current_usd']:,.2f}  {ma}"
            )
    print("\n  Educational only — not advice.\n")


if __name__ == "__main__":
    main()
