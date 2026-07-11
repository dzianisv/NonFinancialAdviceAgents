#!/usr/bin/env python3
"""
Retail crowd positioning: Robinhood's "100 Most Popular" list, resolved to
tickers. This is a WEAK signal (retail crowding), never institutional flow —
consumed by the Smart-Money seat as one additional, explicitly-labeled input
alongside Form 4 / 13F / 13D / PTR (see SKILL.md §Step 3.5).

Source: Robinhood's public, unauthenticated internal API (no key, no login):
  GET https://api.robinhood.com/midlands/tags/tag/100-most-popular/
    -> {"instruments": ["https://api.robinhood.com/instruments/{uuid}/", ...]}
  each instrument URL resolves (unauthenticated GET) to {"symbol": "NVDA", ...}

This is an undocumented Robinhood-internal endpoint (gray-area, could change or
disappear without notice) — not an official/documented API. It is currently
alive and is the same endpoint the actively-maintained `robin_stocks` library
wraps as `get_top_100()`. Handle every failure gracefully; never crash the
calling pipeline.

CACHING: the resolved ranked list is cached under
  .cache/stocks-advisor/robinhood/top100.json
for ~30 minutes (matches the endpoint's own cache-control freshness window) so
repeated per-ticker lookups in one run do not each re-fetch + re-resolve ~100
instruments.

OUTPUT CONTRACT:
  --ticker TICKER  -> {"ticker": "NVDA", "in_top_100": true, "rank": 3}
                      or {"ticker": "XYZ", "in_top_100": false}
  --list           -> {"as_of": "<iso timestamp>", "list": [{"rank":1,"ticker":"NVDA"}, ...]}

On ANY failure (network error, non-200, unexpected shape, timeout, etc.):
  print {"status": "INSUFFICIENT_DATA", "reason": "<short reason>"} and exit 0.
  Never a crash, never a non-zero exit, never an unhandled traceback — mirrors
  this skill's existing graceful-degradation convention (openinsider 403 /
  finviz fallback in the Smart-Money seat, see references/seat-prompts.md).

USAGE:
  python3 robinhood_top100.py --ticker NVDA
  python3 robinhood_top100.py --list
"""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

TAG_URL = "https://api.robinhood.com/midlands/tags/tag/100-most-popular/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/json",
}
TAG_TIMEOUT_S = 10
INSTRUMENT_TIMEOUT_S = 8
MAX_WORKERS = 10
CACHE_DIR = os.path.join(".cache", "stocks-advisor", "robinhood")
CACHE_FILE = os.path.join(CACHE_DIR, "top100.json")
CACHE_FRESH_MINUTES = 30


def _insufficient(reason):
    print(json.dumps({"status": "INSUFFICIENT_DATA", "reason": str(reason)[:200]}))
    sys.exit(0)


def _load_fresh_cache():
    """Return the cached {as_of, list} dict if it exists and is < 30min old, else None."""
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE) as f:
            data = json.load(f)
        as_of = datetime.fromisoformat(data["as_of"])
        if datetime.now(timezone.utc) - as_of < timedelta(minutes=CACHE_FRESH_MINUTES):
            return data
    except Exception:
        pass  # corrupt/missing cache -> treat as a miss, refetch
    return None


def _write_cache(data):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass  # caching is best-effort; a write failure must not fail the run


def _resolve_symbol(session, instrument_url):
    """One instrument UUID URL -> ticker symbol, or None on any failure."""
    try:
        r = session.get(instrument_url, headers=HEADERS, timeout=INSTRUMENT_TIMEOUT_S)
        if r.status_code != 200:
            return None
        symbol = (r.json() or {}).get("symbol")
        return symbol.upper().strip() if symbol else None
    except Exception:
        return None


def fetch_ranked_list():
    """Fetch + resolve the current Top-100 list from Robinhood. Raises on failure."""
    import requests

    resp = requests.get(TAG_URL, headers=HEADERS, timeout=TAG_TIMEOUT_S)
    resp.raise_for_status()
    payload = resp.json()
    instrument_urls = payload.get("instruments")
    if not isinstance(instrument_urls, list) or not instrument_urls:
        raise ValueError("unexpected response shape: no 'instruments' list")

    with requests.Session() as session:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            symbols = list(pool.map(lambda u: _resolve_symbol(session, u), instrument_urls))

    # Rank = 1-indexed position in Robinhood's ranked list, among tickers that
    # actually resolved (order preserved; unresolved instruments are dropped,
    # not left as gaps).
    ranked = [{"rank": i + 1, "ticker": sym} for i, sym in enumerate(s for s in symbols if s)]
    if not ranked:
        raise ValueError("resolved 0/%d instruments to tickers" % len(instrument_urls))

    return {"as_of": datetime.now(timezone.utc).isoformat(), "list": ranked}


def get_list(force_refresh=False):
    """Cached-or-fetched ranked list. Raises on failure (caller catches)."""
    if not force_refresh:
        cached = _load_fresh_cache()
        if cached is not None:
            return cached
    data = fetch_ranked_list()
    _write_cache(data)
    return data


def main():
    args = sys.argv[1:]
    ticker = None
    do_list = False
    i = 0
    while i < len(args):
        if args[i] == "--ticker" and i + 1 < len(args):
            ticker = args[i + 1].upper().strip()
            i += 2
        elif args[i] == "--list":
            do_list = True
            i += 1
        else:
            i += 1

    if not ticker and not do_list:
        sys.exit("usage: robinhood_top100.py --ticker TICKER | --list")

    try:
        data = get_list()
    except Exception as e:
        _insufficient(f"{type(e).__name__}: {e}")
        return  # unreachable, _insufficient exits

    if do_list:
        print(json.dumps(data, indent=2))
        return

    for row in data["list"]:
        if row["ticker"] == ticker:
            print(json.dumps({"ticker": ticker, "in_top_100": True, "rank": row["rank"]}))
            return
    print(json.dumps({"ticker": ticker, "in_top_100": False}))


if __name__ == "__main__":
    main()
