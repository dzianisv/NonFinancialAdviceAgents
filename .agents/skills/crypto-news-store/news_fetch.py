#!/usr/bin/env python3
"""Deterministic unified news fetcher for the narrative-news gather seat.

Fetches ALL RSS feeds (crypto-native + macro paywalled), normalizes to the common
article record, pipes them into news_store.py (dedup + cross-run state), and
prints the NEW/updated EVENTS as JSON.

One reliable command instead of N fragile WebFetch calls:
    python3 news_fetch.py --days 3 --db .db/news.db

Stdlib only. Per-feed failures degrade to a logged [UNAVAILABLE], never crash.
Macro feeds (FT/WSJ/Bloomberg) return RSS descriptions/teasers — full-body extraction
is gated behind the article-paywall-bypass mechanism in trend-stock-research.
"""
import argparse, json, os, re, ssl, sys, subprocess, urllib.request
from email.utils import parsedate_to_datetime
from html import unescape
from urllib.parse import urljoin
from xml.etree import ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(HERE, "news_store.py")

# Verified-resolving RSS feeds (2026-06-15).
# Crypto-native (full content):
CRYPTO_FEEDS = {
    "decrypt": "https://decrypt.co/feed",
    "cointelegraph": "https://cointelegraph.com/rss",
    "coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "theblock": "https://www.theblock.co/rss.xml",
    "bitcoinmagazine": "https://bitcoinmagazine.com/feed",
    # Coinbase blog + institutional research ("Coinbase Bytes" newsletter content is published on the blog).
    # Direct coinbase.com/blog RSS is Cloudflare-gated (403); fetched via Google News proxy like wsj above.
    "coinbase": "https://news.google.com/rss/search?q=(site%3Acoinbase.com%2Fblog+OR+site%3Acoinbase.com%2Finstitutional)+when%3A14d&hl=en-US&gl=US&ceid=US%3Aen",
}
# Macro paywalled — bodies stay behind the paywall; we ingest headline + real article URL (+ teaser
# where the publisher provides one). Endpoints verified 2026-06-25:
#  - FT: native section RSS `ft.com/<section>?format=rss` returns real ft.com/content/<uuid> URLs
#    plus a 1-sentence <description> teaser (CDATA-wrapped). The old ft.com/rss/home is dead (301 →
#    stale ~1-item stub). Bodies stay paywalled — for full text use read_article.ts (logged-in Chrome).
#  - WSJ: Dow Jones migrated public RSS to feeds.content.dowjones.io (the old feeds.a.dj.com froze
#    2025-01-27). The new feeds carry real www.wsj.com URLs + a 1-sentence publisher teaser — far better
#    than the previous Google News proxy, whose links were opaque redirects with no body.
MACRO_FEEDS = {
    # FT/WSJ endpoint source of truth is the TS fetchers (feed-ft/scripts/fetch_ft.ts,
    # feed-wsj/scripts/fetch_wsj.ts). This stdlib-only Python ingest keeps its own copy of the same
    # URLs on purpose (no bun runtime dependency); html.unescape() below decodes hex entities correctly.
    # If an endpoint changes, update it in those TS files AND here.
    "ft-markets": "https://www.ft.com/markets?format=rss",
    "ft-companies": "https://www.ft.com/companies?format=rss",
    "ft-global-economy": "https://www.ft.com/global-economy?format=rss",
    "ft-world": "https://www.ft.com/world?format=rss",
    "wsj-markets": "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain",
    "wsj-world": "https://feeds.content.dowjones.io/public/rss/RSSWorldNews",
    "wsj-business": "https://feeds.content.dowjones.io/public/rss/WSJcomUSBusiness",
    "wsj-tech": "https://feeds.content.dowjones.io/public/rss/RSSWSJD",
    "bloomberg": "https://www.bloomberg.com/feed/podcast/etf-report.xml",  # podcast feed, not news — often 403
}

FEEDS = {**CRYPTO_FEEDS, **MACRO_FEEDS}
# Sources whose bodies are paywalled — an empty RSS teaser is marked [UNAVAILABLE - paywall],
# never fabricated, per the feed-ft / feed-wsj skill contract.
PAYWALLED = set(MACRO_FEEDS)
UA = "Mozilla/5.0 (news-research; +https://example.invalid)"
TAG = re.compile(r"<[^>]+>")


def _fetch(url, depth=0):
    """GET with UA; follow 308 (urllib doesn't) up to 3 hops."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        return urllib.request.urlopen(req, timeout=20,
                                      context=ssl.create_default_context()).read()
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 307, 308) and depth < 3:
            loc = e.headers.get("Location")
            if loc:
                return _fetch(urljoin(url, loc), depth + 1)  # Location may be relative
        raise


def _clean(s):
    return unescape(TAG.sub("", s or "")).strip()


def _parse(source, xml_bytes):
    out = []
    root = ET.fromstring(xml_bytes)
    for item in root.iter("item"):
        def g(tag):
            el = item.find(tag)
            return el.text if el is not None else ""
        title = _clean(g("title"))
        if not title:
            continue
        pub = g("pubDate") or ""
        iso = ""
        try:
            iso = parsedate_to_datetime(pub).astimezone().isoformat() if pub else ""
        except Exception:
            iso = ""
        summary = _clean(g("description"))[:600]
        if not summary and source in PAYWALLED:
            summary = "[UNAVAILABLE - paywall]"
        out.append({
            "source": source,
            "url": (g("link") or "").strip(),
            "title": title,
            "published_at": iso or pub,
            "summary": summary,
            "lang": "en",
            "tags": [],
        })
    return out


def main():
    ap = argparse.ArgumentParser(description="fetch crypto RSS -> news_store -> new events")
    ap.add_argument("--db", default=".db/news.db")
    ap.add_argument("--days", type=int, default=3)
    ap.add_argument("--k", type=int, default=15)
    ap.add_argument("--query", default="", help="if set, return ranked question-relevant events (hybrid BM25+near-dup) instead of all new-since; cuts noise")
    args = ap.parse_args()

    records, unavailable = [], []
    for name, url in sorted(FEEDS.items()):
        try:
            records += _parse(name, _fetch(url))
        except Exception as e:
            unavailable.append(f"{name}:{type(e).__name__}")
            print(f"[UNAVAILABLE] feed {name}: {e}", file=sys.stderr)

    if not records:
        print(json.dumps({"events": [], "unavailable": unavailable,
                          "note": "all feeds [UNAVAILABLE]"}))
        return

    # ingest (idempotent) then ask the store for new/updated events
    tmp = os.path.join(HERE, ".fetch_tmp.json")
    with open(tmp, "w") as f:
        json.dump(records, f)
    try:
        subprocess.run([sys.executable, STORE, "--db", args.db, "ingest", "--json", tmp],
                       check=True, capture_output=True, text=True)
        if args.query:  # focused, ranked, relevant — cuts the new-since noise
            ns = subprocess.run([sys.executable, STORE, "--db", args.db, "query",
                                 "--q", args.query, "--days", str(args.days), "--k", str(args.k)],
                                check=True, capture_output=True, text=True)
        else:
            ns = subprocess.run([sys.executable, STORE, "--db", args.db, "new-since",
                                 "--days", str(args.days)], check=True, capture_output=True, text=True)
    finally:
        os.path.exists(tmp) and os.remove(tmp)

    try:
        events = json.loads(ns.stdout)
    except Exception:
        events = ns.stdout
    print(json.dumps({"fetched": len(records), "feeds_ok": len(FEEDS) - len(unavailable),
                      "unavailable": unavailable, "events": events}, indent=1))


if __name__ == "__main__":
    main()
