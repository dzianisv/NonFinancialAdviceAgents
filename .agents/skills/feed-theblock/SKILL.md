---
name: feed-theblock
description: Source adapter for The Block crypto news feed (theblock.co) — fetch + normalize RSS into the common article record consumed by narrative-news + crypto-news-store. Use when gathering the crypto news feed, when narrative-news needs The Block coverage, or when asked for "The Block headlines" / "The Block crypto news". Fetch + normalize ONLY — no dedup/store/judge. Degrades to [UNAVAILABLE]; never fabricates.
license: MIT
compatibility: opencode
metadata:
  audience: crypto-research-pipeline
  domain: news-feed-adapter
  role: source-adapter
  tier: crypto-native
---

# feed-theblock (The Block source adapter)

Pure **fetch + normalize** adapter for one outlet. Emits the common record (or `[UNAVAILABLE]`). Dedup/
store/judge live downstream in [[crypto-news-store]] + [[narrative-news]].

## Hard rule

Never fabricate. On failure → `[UNAVAILABLE]`. Return **≥1 record or a clean `[UNAVAILABLE]`** (PRD AC5/AC6).

## Retrieval recipe

- **Endpoint (verified resolving, RSS 2.0):** `https://www.theblock.co/rss.xml`
- Parse RSS `channel > item`: `title`→title, `link`→url (canonicalize, strip `utm_*`), `pubDate`(RFC-822)→`published_at` (ISO-8601 UTC), `description`/`content:encoded`→`summary` (strip HTML), `category`→`tags`, `dc:creator` optional, `media:thumbnail` is an image (ignore for record). `lang: en`, `source: theblock`.

## Politeness (required)

Conditional GET (ETag/If-Modified-Since; `304` → nothing-new). Exponential backoff on `429`/`5xx`, ~2 retries, then `[UNAVAILABLE]`. Sequential fetch.

## Normalized output record

```json
{"source":"theblock","url":"https://www.theblock.co/post/<id>/<slug>","title":"...","published_at":"2026-06-15T...Z","summary":"...","lang":"en","tags":["HYPE","ETF"]}
```

## Failure mode

```json
{"source":"theblock","status":"[UNAVAILABLE]","reason":"<http code / parse error>"}
```

> Educational, not advice. Fetch + normalize only.
