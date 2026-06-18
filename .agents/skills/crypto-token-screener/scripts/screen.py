#!/usr/bin/env python3
"""Pull the raw numbers for the crypto infra-token screen.

For each token in a watchlist, fetch the data the 6-point filter needs:
  - DefiLlama holder revenue (the fees that actually reach the token)  -> filter 1 & 2
  - DefiLlama 30d run-rate (is revenue growing or fading?)            -> filter 1
  - CoinGecko market cap, FDV, mcap/FDV (dilution)                    -> filter 5
  - CoinGecko price trend vs BTC over `--days`                        -> filter 4 (the hurdle)
Then compute P/E (mcap / holder-rev-1y) and holder yield.

This script fetches ONLY. It does not score, rank, or recommend — the agent applies the
filter and judgement (wash-trading exclusion, accrual enforced-vs-discretionary, durability).
Every unavailable field prints as "n/a" so a bad slug shows a gap, never a fake number.

Usage:
    python3 screen.py                         # default watchlist (references/watchlist.json)
    python3 screen.py --watchlist my.json     # custom list
    python3 screen.py --days 180              # BTC-relative window (default 90)
    python3 screen.py --token hyperliquid:hyperliquid   # one ad-hoc token  llama_slug:cg_id
"""
from __future__ import annotations
import argparse, json, os, sys, time, urllib.request, urllib.error

LLAMA = "https://api.llama.fi/summary/fees/{slug}?dataType=dailyHoldersRevenue"
CG_COIN = "https://api.coingecko.com/api/v3/coins/{id}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false"
CG_CHART = "https://api.coingecko.com/api/v3/coins/{id}/market_chart?vs_currency=btc&days={days}"


def _get(url: str, tries: int = 3):
    """GET JSON with retry/backoff. Returns dict/list or None (never raises)."""
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "infra-token-screen/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429:           # rate limited -> back off and retry
                time.sleep(2 * (i + 1))
                continue
            return None
        except Exception:
            time.sleep(1 + i)
    return None


def holder_revenue(slug: str):
    """Return (annual_holder_rev, run_rate_annualized_from_30d) in USD, or (None, None)."""
    d = _get(LLAMA.format(slug=slug))
    if not d:
        return None, None
    yr = d.get("total1y")
    m30 = d.get("total30d")
    run = m30 * 365 / 30 if isinstance(m30, (int, float)) else None
    return yr, run


def market(cg_id: str, days: int):
    """Return dict with mcap, fdv, mcap_fdv, vs_btc_pct (over `days`), or Nones."""
    out = {"mcap": None, "fdv": None, "mcap_fdv": None, "vs_btc_pct": None}
    c = _get(CG_COIN.format(id=cg_id))
    if c:
        md = c.get("market_data", {}) or {}
        out["mcap"] = (md.get("market_cap") or {}).get("usd")
        out["fdv"] = (md.get("fully_diluted_valuation") or {}).get("usd")
        if out["mcap"] and out["fdv"]:
            out["mcap_fdv"] = round(out["mcap"] / out["fdv"], 3)
    time.sleep(1)  # be gentle with CoinGecko's free tier
    ch = _get(CG_CHART.format(id=cg_id, days=days))
    if ch and ch.get("prices"):
        p = [x[1] for x in ch["prices"] if x and x[1]]
        if len(p) >= 2 and p[0]:
            out["vs_btc_pct"] = round(100 * (p[-1] - p[0]) / p[0], 1)
    return out


def fmt_usd(v):
    if not isinstance(v, (int, float)):
        return "n/a"
    for unit, div in (("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(v) >= div:
            return f"${v/div:.1f}{unit}"
    return f"${v:.0f}"


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--watchlist", default=os.path.join(here, "..", "references", "watchlist.json"))
    ap.add_argument("--days", type=int, default=90, help="BTC-relative trend window")
    ap.add_argument("--token", action="append", default=[], help="ad-hoc llama_slug:cg_id")
    a = ap.parse_args()

    tokens = []
    for t in a.token:
        slug, _, cid = t.partition(":")
        tokens.append({"name": cid or slug, "llama": slug, "cg": cid or slug})
    if not a.token:
        with open(a.watchlist) as f:
            tokens = json.load(f)

    print(f"# Infra-token screen — vs-BTC window = {a.days}d — fetched live\n")
    hdr = ["TOKEN", "holder_rev_1y", "run_rate_30d", "mcap", "P/E", "yield%", "mcap/FDV", f"vs_BTC_{a.days}d"]
    print("| " + " | ".join(hdr) + " |")
    print("|" + "|".join(["---"] * len(hdr)) + "|")

    for t in tokens:
        yr, run = holder_revenue(t["llama"])
        mk = market(t["cg"], a.days)
        pe = f"{mk['mcap']/yr:.1f}x" if (mk["mcap"] and yr) else "n/a"
        yld = f"{100*yr/mk['mcap']:.1f}%" if (mk["mcap"] and yr) else "n/a"
        vsb = f"{mk['vs_btc_pct']:+.1f}%" if mk["vs_btc_pct"] is not None else "n/a"
        row = [t["name"], fmt_usd(yr), fmt_usd(run), fmt_usd(mk["mcap"]), pe, yld,
               str(mk["mcap_fdv"]) if mk["mcap_fdv"] is not None else "n/a", vsb]
        print("| " + " | ".join(row) + " |")
        sys.stdout.flush()

    print("\nNotes: holder_rev_1y=0 or n/a => DefiLlama lacks a holdersRevenue series for that slug "
          "(coverage gap, NOT proof of zero accrual) — verify the slug and the buyback mechanism by hand. "
          "Numbers are point-in-time; re-run before acting.")


if __name__ == "__main__":
    main()
