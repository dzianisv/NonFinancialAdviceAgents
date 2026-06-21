---
name: feed-bitcoinmagazine
description: Source adapter for the Bitcoin Magazine news feed (bitcoinmagazine.com) — fetch + normalize RSS into the common article record consumed by narrative-news + crypto-news-store. Use when gathering the crypto news feed, when narrative-news needs Bitcoin Magazine coverage, or when asked for "Bitcoin Magazine headlines" / "Bitcoin Magazine crypto news". Fetch + normalize ONLY — no dedup/store/judge. Degrades to [UNAVAILABLE]; never fabricates.
license: MIT
compatibility: opencode
metadata:
  audience: crypto-research-pipeline
  domain: news-feed-adapter
  role: source-adapter
  tier: crypto-native
---

# feed-bitcoinmagazine (Bitcoin Magazine source adapter)

Pure **fetch + normalize** adapter for one outlet. Emits the common record (or `[UNAVAILABLE]`). Dedup/
store/judge live downstream in [[crypto-news-store]] + [[narrative-news]].

## Hard rule

Never fabricate. On failure → `[UNAVAILABLE]`. Return **≥1 record or a clean `[UNAVAILABLE]`** (PRD AC5/AC6).

## Retrieval recipe

- **Endpoint (verified resolving, RSS 2.0):** `https://bitcoinmagazine.com/feed`
- Parse RSS `channel > item`: `title`→title, `link`→url (canonicalize, strip `utm_*`), `pubDate`(RFC-822)→`published_at` (ISO-8601 UTC), `description`/`content:encoded`→`summary` (strip HTML), `category`→`tags`, `dc:creator` optional. `lang: en`, `source: bitcoinmagazine`.
- Bitcoin-centric outlet → expect `BTC`-heavy coverage; tag accordingly when readable verbatim.

## Politeness (required)

Conditional GET (ETag/If-Modified-Since; `304` → nothing-new). Exponential backoff on `429`/`5xx`, ~2 retries, then `[UNAVAILABLE]`. Sequential fetch.

## Normalized output record

```json
{"source":"bitcoinmagazine","url":"https://bitcoinmagazine.com/<section>/<slug>","title":"...","published_at":"2026-06-15T...Z","summary":"...","lang":"en","tags":["BTC"]}
```

## Failure mode

```json
{"source":"bitcoinmagazine","status":"[UNAVAILABLE]","reason":"<http code / parse error>"}
```

## Caching (required)

After fetching, ingest each article into the shared SQLite cache so downstream agents can BM25-search without re-fetching:

```bash
python3 /Users/engineer/workspace/backtest/.agents/scripts/feeds/fetch_article.py \
  --ingest --url "<article-url>" --title "<headline>" \
  --body "<body text or [UNAVAILABLE - paywall]>" --source "bitcoinmagazine"
```

Cache is deduped by (url, date) — safe to re-run. Query later: `python3 fetch_article.py --search "nvidia" --limit 5`.

> Educational, not advice. Fetch + normalize only.
