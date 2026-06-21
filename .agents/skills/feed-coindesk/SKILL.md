---
name: feed-coindesk
description: Source adapter for the CoinDesk crypto news feed (coindesk.com) — fetch + normalize RSS into the common article record consumed by narrative-news + crypto-news-store. Use when gathering the crypto news feed, when narrative-news needs CoinDesk coverage, or when asked for "CoinDesk headlines" / "CoinDesk crypto news". Fetch + normalize ONLY — no dedup/store/judge. Degrades to [UNAVAILABLE]; never fabricates.
license: MIT
compatibility: opencode
metadata:
  audience: crypto-research-pipeline
  domain: news-feed-adapter
  role: source-adapter
  tier: crypto-native
---

# feed-coindesk (CoinDesk source adapter)

Pure **fetch + normalize** adapter for one outlet. Emits the common record (or `[UNAVAILABLE]`). Dedup/
store/judge live downstream in [[crypto-news-store]] + [[narrative-news]].

## Hard rule

Never fabricate. On failure → `[UNAVAILABLE]`. Return **≥1 record or a clean `[UNAVAILABLE]`** (PRD AC5/AC6).

## Retrieval recipe

- **Endpoint (verified resolving, RSS 2.0):** `https://www.coindesk.com/arc/outboundfeeds/rss/`
  (CoinDesk runs the Arc Publishing "outboundfeeds" RSS; this is the canonical site-wide feed.)
- Parse RSS `channel > item`: `title`→title, `link`→url (canonicalize, strip `utm_*`), `pubDate`(RFC-822)→`published_at` (ISO-8601 UTC), `description`→`summary` (strip HTML), `category`→`tags`, `dc:creator` optional, `media:content` is an image URL (ignore for the record). `lang: en`, `source: coindesk`.

## Politeness (required)

Conditional GET (ETag/If-Modified-Since; `304` → nothing-new). Exponential backoff on `429`/`5xx`, ~2 retries, then `[UNAVAILABLE]`. Sequential fetch.

## Normalized output record

```json
{"source":"coindesk","url":"https://www.coindesk.com/<section>/<slug>","title":"...","published_at":"2026-06-15T...Z","summary":"...","lang":"en","tags":["ETF"]}
```

## Failure mode

```json
{"source":"coindesk","status":"[UNAVAILABLE]","reason":"<http code / parse error>"}
```

## Caching (required)

After fetching, ingest each article into the shared SQLite cache so downstream agents can BM25-search without re-fetching:

```bash
python3 /Users/engineer/workspace/backtest/.agents/scripts/feeds/fetch_article.py \
  --ingest --url "<article-url>" --title "<headline>" \
  --body "<body text or [UNAVAILABLE - paywall]>" --source "coindesk"
```

Cache is deduped by (url, date) — safe to re-run. Query later: `python3 fetch_article.py --search "nvidia" --limit 5`.

> Educational, not advice. Fetch + normalize only.
