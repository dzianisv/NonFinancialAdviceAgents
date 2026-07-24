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
                      or {"ticker": "XYZ", "in_top_100": "UNKNOWN", ...}  (see below)
  --list           -> {"as_of": "<iso timestamp>", "list": [{"rank":1,"ticker":"NVDA"}, ...],
                       "resolved": 100, "requested": 100, "unresolved": []}

A MISSING INPUT IS NEVER A `false` (fixed 2026-07-24):
  Each of the ~100 instrument UUIDs is a separate HTTP GET, and any one of them
  can time out. The previous version returned None for a failed resolve, dropped
  it, and then RE-NUMBERED the ranks — so one timeout silently (a) shifted every
  rank below it up by one and (b) turned "we could not determine this" into a
  confident `"in_top_100": false`. That fabricated negative is the exact bug
  class this skill bans: a default must never mask a missing input.
  Now: `rank` is the TRUE 1-indexed position in Robinhood's list and never
  renumbers; unresolved instruments are named in `unresolved`; and a ticker that
  is absent from an INCOMPLETE list reports `"in_top_100": "UNKNOWN"` with the
  count, not `false`. Absent from a COMPLETE list is still a real `false`.

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
    except Exception as e:
        # A cache miss falls back to a REAL fetch, so no fabricated value can
        # escape here — but the reason still gets named on stderr rather than
        # swallowed, so a permanently-corrupt cache is visible instead of
        # showing up only as unexplained slowness.
        print("warn: unreadable cache %s (%s: %s) -> refetching"
              % (CACHE_FILE, type(e).__name__, str(e)[:80]), file=sys.stderr)
    return None


def _write_cache(data):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        # Caching is best-effort and cannot affect the value returned this run,
        # so a write failure must not fail the run — but it is still named.
        print("warn: cache write failed %s (%s: %s)"
              % (CACHE_FILE, type(e).__name__, str(e)[:80]), file=sys.stderr)


def _resolve_symbol(session, instrument_url):
    """One instrument UUID URL -> (ticker, None) or (None, "<named reason>").

    The reason travels back with the failure. A caller that only sees `None`
    cannot tell a dead instrument from a timed-out one, and cannot report how
    much of the list it is actually holding.
    """
    try:
        r = session.get(instrument_url, headers=HEADERS, timeout=INSTRUMENT_TIMEOUT_S)
        if r.status_code != 200:
            return None, "HTTP %d" % r.status_code
        symbol = (r.json() or {}).get("symbol")
        if not symbol:
            return None, "200 but no 'symbol' field"
        return symbol.upper().strip(), None
    except Exception as e:
        return None, "%s: %s" % (type(e).__name__, str(e)[:80])


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
            resolved = list(pool.map(lambda u: _resolve_symbol(session, u), instrument_urls))

    # Rank = TRUE 1-indexed position in Robinhood's ranked list. It is taken from
    # the source index and never renumbered, so a failed resolve leaves a gap in
    # the rank sequence instead of silently promoting everything below it.
    ranked = [{"rank": i + 1, "ticker": sym}
              for i, (sym, _err) in enumerate(resolved) if sym]
    unresolved = [{"rank": i + 1, "reason": err}
                  for i, (sym, err) in enumerate(resolved) if not sym]
    if not ranked:
        raise ValueError("resolved 0/%d instruments to tickers" % len(instrument_urls))

    return {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "list": ranked,
        "requested": len(instrument_urls),
        "resolved": len(ranked),
        # Named, never silent. Downstream turns a non-empty list into UNKNOWN
        # rather than a fabricated "not in the top 100".
        "unresolved": unresolved,
    }


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
    refresh = False
    i = 0
    while i < len(args):
        if args[i] == "--ticker" and i + 1 < len(args):
            ticker = args[i + 1].upper().strip()
            i += 2
        elif args[i] == "--list":
            do_list = True
            i += 1
        elif args[i] == "--refresh":
            refresh = True
            i += 1
        else:
            i += 1

    if not ticker and not do_list:
        sys.exit("usage: robinhood_top100.py --ticker TICKER | --list [--refresh]")

    try:
        data = get_list(force_refresh=refresh)
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

    # Absent from the list. That is only a real `false` if the list is COMPLETE.
    # If any instrument failed to resolve, this ticker might be one of them, so
    # the honest answer is UNKNOWN with the gap named — not a fabricated false.
    unresolved = data.get("unresolved")
    if unresolved is None:
        # Cache written before this field existed: completeness is unknown, and
        # claiming `false` on an unverifiable list is the bug being fixed.
        print(json.dumps({
            "ticker": ticker, "in_top_100": "UNKNOWN",
            "reason": "cached list predates resolution tracking — completeness unverifiable; "
                      "re-run with --refresh",
        }))
        return
    if unresolved:
        print(json.dumps({
            "ticker": ticker, "in_top_100": "UNKNOWN",
            "reason": "%d of %d instruments failed to resolve; ticker may be among them"
                      % (len(unresolved), data.get("requested", len(unresolved))),
            "unresolved_ranks": [u["rank"] for u in unresolved],
        }))
        return
    print(json.dumps({"ticker": ticker, "in_top_100": False,
                      "resolved": data.get("resolved")}))


if __name__ == "__main__":
    main()
