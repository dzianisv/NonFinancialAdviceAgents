#!/usr/bin/env python3
"""
Discovery engine — VALIDATION GATE (Stage 0 equivalent). NO product built until this passes.

Hypothesis: companies whose SEC filings contain a demand-shift signal (e.g. "capacity
constrained") go on to OUTPERFORM the market over the next 6-12 months. If true, reading
filings at scale is a real discovery edge. If false, we do NOT build the pipeline.

Point-in-time + low survivorship: we take whoever FILED the phrase at date T (including names
that later cratered or delisted), using only info available at T, and measure forward return
vs SPY. EDGAR full-text search is timestamped, so this is honest in a way the momentum baskets
never were.

Sources (free): EDGAR FTS (efts.sec.gov), CIK->ticker map (sec.gov), prices (yfinance).
Caveat: yfinance can't price delisted tickers -> they drop out = residual survivorship skew
(flagged in output). FTS covers 2001+.

Usage: python3 edgar_signal_test.py --signal "capacity constrained" --forms 10-Q,10-K
Educational, not advice.
"""
import sys, time, json, argparse, warnings
from datetime import datetime, timedelta
warnings.filterwarnings("ignore")
import os
import urllib.request, urllib.parse
import numpy as np, pandas as pd, yfinance as yf

# EDGAR requires a User-Agent with contact info. Set EDGAR_UA to your own
# "name email" per https://www.sec.gov/os/webmaster-faq#developers
UA = os.getenv("EDGAR_UA", "backtest-research research@example.com")


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return json.load(urllib.request.urlopen(req, timeout=30))


def cik_ticker_map():
    d = _get("https://www.sec.gov/files/company_tickers.json")
    return {int(v["cik_str"]): v["ticker"] for v in d.values()}


def fts(signal, forms, startdt, enddt, max_pages=4):
    """Return list of (cik, filing_date) hits for the phrase in the window."""
    out = []
    q = urllib.parse.quote(f'"{signal}"')
    for page in range(max_pages):
        url = (f"https://efts.sec.gov/LATEST/search-index?q={q}&forms={forms}"
               f"&startdt={startdt}&enddt={enddt}&from={page*10}")
        try:
            d = _get(url)
        except Exception:
            break
        hits = d.get("hits", {}).get("hits", [])
        if not hits:
            break
        for h in hits:
            src = h.get("_source", {})
            ciks = src.get("ciks", [])
            fdate = src.get("file_date")
            if ciks and fdate:
                out.append((int(ciks[0]), fdate))
        time.sleep(0.15)  # SEC fair-access
    return out


def fwd_excess(ticker, fdate, months):
    """Forward total return of ticker minus SPY, from fdate over `months`. None if unpriced."""
    try:
        start = pd.to_datetime(fdate)
        end = start + pd.Timedelta(days=int(months * 30.5) + 5)
        px = yf.download([ticker, "SPY"], start=start - pd.Timedelta(days=5),
                         end=end + pd.Timedelta(days=5), progress=False, auto_adjust=True)["Close"]
        if isinstance(px, pd.Series) or ticker not in px or "SPY" not in px:
            return None
        px = px.dropna()
        if len(px) < 10:
            return None
        t0 = px.index[px.index >= start][0]
        tN = px.index[px.index <= end][-1]
        if tN <= t0:
            return None
        r = px[ticker].loc[tN] / px[ticker].loc[t0] - 1
        m = px["SPY"].loc[tN] / px["SPY"].loc[t0] - 1
        return float(r - m)
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--signal", default="capacity constrained")
    ap.add_argument("--forms", default="10-Q,10-K")
    ap.add_argument("--quarters", type=int, default=6, help="how many past quarters to scan")
    ap.add_argument("--cap", type=int, default=25, help="max unique companies per quarter")
    ap.add_argument("--asof", default="2024-09-30", help="end of newest quarter (need 12m fwd after)")
    args = ap.parse_args()

    print(f"EDGAR signal gate | '{args.signal}' | forms {args.forms} | "
          f"{args.quarters}q ending {args.asof} | point-in-time")
    print("=" * 74)
    tmap = cik_ticker_map()

    asof = pd.to_datetime(args.asof)
    rows = []
    seen_global = set()
    for qi in range(args.quarters):
        qend = asof - pd.Timedelta(days=91 * qi)
        qstart = qend - pd.Timedelta(days=91)
        hits = fts(args.signal, args.forms, qstart.strftime("%Y-%m-%d"), qend.strftime("%Y-%m-%d"))
        # unique CIKs this quarter, mapped to tickers
        ciks, picks = set(), []
        for cik, fdate in hits:
            if cik in ciks or cik not in tmap:
                continue
            ciks.add(cik)
            picks.append((tmap[cik], fdate))
            if len(picks) >= args.cap:
                break
        n_unpriced = 0
        for tk, fdate in picks:
            key = (tk, fdate[:7])
            if key in seen_global:
                continue
            seen_global.add(key)
            ex6 = fwd_excess(tk, fdate, 6)
            ex12 = fwd_excess(tk, fdate, 12)
            if ex6 is None and ex12 is None:
                n_unpriced += 1
                continue
            rows.append({"q": qstart.strftime("%Y-%m"), "ticker": tk, "fdate": fdate,
                         "ex6": ex6, "ex12": ex12})
        print(f"  {qstart.strftime('%Y-%m')}..{qend.strftime('%Y-%m')}: "
              f"{len(picks)} flagged, {n_unpriced} unpriced(delisted)")

    R = pd.DataFrame(rows)
    if R.empty:
        print("\nNo priceable flagged companies — widen window or check signal."); return
    print("\n" + "=" * 74)
    print(f"FLAGGED companies priced: {len(R)}  (delisted/unpriced excluded = survivorship skew UP)")
    for h, col in (("6-month", "ex6"), ("12-month", "ex12")):
        s = R[col].dropna()
        if len(s) < 5:
            continue
        win = (s > 0).mean()
        t = s.mean() / (s.std() / np.sqrt(len(s))) if s.std() > 0 else float("nan")
        print(f"  {h} forward excess vs SPY: mean {s.mean()*100:+.1f}%  median {s.median()*100:+.1f}%  "
              f"hit-rate {win*100:.0f}%  n={len(s)}  t={t:.2f}")
    print("\nGATE: signal has discovery value only if forward excess is clearly >0 with decent")
    print("hit-rate AND t-stat, knowing delisting skews this OPTIMISTIC. Weak/zero => do NOT build.")
    print("Educational, not advice. One signal, small sample — directional gate, not proof.")


if __name__ == "__main__":
    main()
