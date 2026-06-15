---
name: feed-wsj
description: Source adapter for The Wall Street Journal (WSJ) Markets — PAYWALLED, so HEADLINES ONLY. Fetch + normalize the WSJ Markets RSS into the common article record (headline + url + published_at) with body marked [UNAVAILABLE - paywall]. Use when gathering the crypto/macro news feed, when narrative-news needs WSJ markets coverage, or when asked for "WSJ headlines" / "Wall Street Journal markets news". Fetch + normalize ONLY — no dedup/store/judge. NEVER fabricates a body.
license: MIT
compatibility: opencode
metadata:
  audience: crypto-research-pipeline
  domain: news-feed-adapter
  role: source-adapter
  tier: macro-paywalled
---

# feed-wsj (WSJ Markets source adapter — headlines only)

Pure **fetch + normalize** adapter for a **paywalled** outlet. WSJ bodies are behind a paywall, so this
adapter emits **headline + url + published_at only** and marks the body `[UNAVAILABLE - paywall]`. Dedup/
store/judge live downstream in [[crypto-news-store]] + [[narrative-news]].

## Hard rule (paywall)

**NEVER fabricate body text.** Headline-only is acceptable; invented prose is a defect (PRD AC6). On any
failure → `[UNAVAILABLE]`. Return **≥1 headline record or a clean `[UNAVAILABLE]`** (AC5).

## Retrieval recipe

- **Endpoint (verified resolving, RSS 2.0 — WSJ Markets Main):** `https://feeds.a.dj.com/rss/RSSMarketsMain.xml`
  Other WSJ feeds (same publisher, same paywall rule): `https://feeds.a.dj.com/rss/RSSWorldNews.xml`,
  `https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml`.
- Parse `channel > item`: `title`→title, `link`→url (canonicalize, strip `utm_*`), `pubDate`(RFC-822)→`published_at` (ISO-8601 UTC). The RSS `description` is WSJ's own teaser — keep verbatim as `summary` if present (publisher-provided, not fabricated), else `"[UNAVAILABLE - paywall]"`. **Do NOT scrape the full body.** `category`→`tags`, `lang: en`, `source: wsj`.

## Politeness (required)

Conditional GET (ETag/If-Modified-Since; `304` → nothing-new). Exponential backoff on `429`/`5xx`, ~2 retries, then `[UNAVAILABLE]`. Sequential fetch.

## Normalized output record

```json
{"source":"wsj","url":"https://www.wsj.com/articles/<slug>","title":"...","published_at":"2026-06-15T...Z","summary":"<publisher teaser or [UNAVAILABLE - paywall]>","lang":"en","tags":["markets"]}
```

## Failure mode

```json
{"source":"wsj","status":"[UNAVAILABLE]","reason":"paywall / fetch failed"}
```

> Educational, not advice. Headlines only; never fabricate a paywalled body.
