---
name: feed-ft
description: Source adapter for the Financial Times (FT) — PAYWALLED, so HEADLINES ONLY. Fetch + normalize the FT RSS into the common article record (headline + url + published_at) with body marked [UNAVAILABLE - paywall]. Use when gathering the crypto/macro news feed, when narrative-news needs FT macro coverage, or when asked for "FT headlines" / "Financial Times news". Fetch + normalize ONLY — no dedup/store/judge. NEVER fabricates a body.
license: MIT
compatibility: opencode
metadata:
  audience: crypto-research-pipeline
  domain: news-feed-adapter
  role: source-adapter
  tier: macro-paywalled
---

# feed-ft (Financial Times source adapter — headlines only)

Pure **fetch + normalize** adapter for a **paywalled** outlet. FT bodies are behind a hard paywall, so this
adapter emits **headline + url + published_at only** and marks the body `[UNAVAILABLE - paywall]`. Dedup/
store/judge live downstream in [[crypto-news-store]] + [[narrative-news]].

## Hard rule (paywall)

**NEVER fabricate body text.** Headline-only is acceptable; invented prose is a defect (PRD AC6). On any
failure → `[UNAVAILABLE]`. Return **≥1 headline record or a clean `[UNAVAILABLE]`** (AC5).

## Retrieval recipe

- **Endpoint:** `https://www.ft.com/rss/home` (FT home RSS — headlines + links + pubDate; bodies paywalled).
  Also useful: `https://www.ft.com/rss/markets`.
- **Note (verify at runtime):** FT aggressively bot-blocks; the RSS may return `403`/be unfetchable from
  some hosts/agents (e.g. `web_fetch` returned "unable to fetch" at build time). That is the paywall path,
  not a bug — **degrade to `[UNAVAILABLE]`, never fabricate**. If the RSS resolves, parse `channel > item`.
- Parse: `title`→title, `link`→url (canonicalize, strip `utm_*`), `pubDate`(RFC-822)→`published_at` (ISO-8601 UTC). **`summary` = `"[UNAVAILABLE - paywall]"`** (do NOT scrape or guess the body). `lang: en`, `source: ft`.
- The RSS `description`, if present, is FT's own short teaser — you MAY keep it verbatim as `summary` (it is
  publisher-provided, not fabricated). If empty/absent → `[UNAVAILABLE - paywall]`.

## Politeness (required)

Conditional GET (ETag/If-Modified-Since; `304` → nothing-new). Exponential backoff on `429`/`5xx`, ~2 retries, then `[UNAVAILABLE]`. Sequential fetch. Respect the bot-block — do not retry aggressively.

## Normalized output record

```json
{"source":"ft","url":"https://www.ft.com/content/<id>","title":"...","published_at":"2026-06-15T...Z","summary":"[UNAVAILABLE - paywall]","lang":"en","tags":["macro"]}
```

## Failure mode

```json
{"source":"ft","status":"[UNAVAILABLE]","reason":"paywall / 403 bot-block / fetch failed"}
```

> Educational, not advice. Headlines only; never fabricate a paywalled body.
