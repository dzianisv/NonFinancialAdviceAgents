---
name: feed-wsj
description: Source adapter for The Wall Street Journal (WSJ) Markets — PAYWALLED, RSS descriptions/teasers available as summary. Fetch + normalize the WSJ Markets RSS into the common article record (headline + url + published_at + publisher's RSS teaser). Use when gathering the crypto/macro news feed, when narrative-news needs WSJ markets coverage, or when asked for "WSJ headlines" / "Wall Street Journal markets news". Fetch + normalize ONLY — no dedup/store/judge. NEVER fabricates a body.
license: MIT
compatibility: opencode
metadata:
  audience: crypto-research-pipeline
  domain: news-feed-adapter
  role: source-adapter
  tier: macro-paywalled
---

# feed-wsj (WSJ Markets source adapter — RSS teasers available)

Pure **fetch + normalize** adapter for a **paywalled** outlet. WSJ bodies are behind a paywall, so this
adapter emits **headline + url + published_at + RSS teaser** (the publisher's own `description`) and marks
the body `[UNAVAILABLE - paywall]` only when the RSS teaser is absent. Dedup/store/judge live downstream in
[[crypto-news-store]] + [[narrative-news]].

## Hard rule (paywall)

**NEVER fabricate body text.** Headline-only is acceptable; invented prose is a defect (PRD AC6). On any
failure → `[UNAVAILABLE]`. Return **≥1 headline record or a clean `[UNAVAILABLE]`** (AC5).

## Retrieval recipe

- **Primary endpoint (verified working 2026-06-16):** Google News RSS filtered to WSJ:
  `https://news.google.com/rss/search?q=site%3Awsj.com+when%3A7d&hl=en-US&gl=US&ceid=US%3Aen`
  Returns ~100 articles/7 days. URLs are opaque Google News redirects (work in browsers, not directly resolvable).
- **DEPRECATED (dead since Jan 2025):** `https://feeds.a.dj.com/rss/RSSMarketsMain.xml` and other DJ feeds — frozen, return stale data.
- Parse `channel > item`: `title`→title (strip `" - The Wall Street Journal"` suffix), `link`→url (Google News redirect), `pubDate`(RFC-822)→`published_at` (ISO-8601 UTC). The RSS `description` is Google News's snippet — keep verbatim as `summary` if present, else `"[UNAVAILABLE - paywall]"`. **Do NOT scrape the full body.** `category`→`tags`, `lang: en`, `source: wsj`.

## Reading the BODY (verified method, June 2026)

For the full article body, use the script — **no extension required**:

```bash
/Users/engineer/workspace/backtest/.agents/scripts/feeds/read_article.sh "<wsj-url>"
```

**Method:** `curl -sL "https://web.archive.org/web/2/<url>"` (Wayback Machine). Unlike FT, WSJ does NOT
serve a paywall page to the Wayback crawler — full article bodies are available headlessly. Verified 2026-06-20.

If no Wayback snapshot exists, the script falls back to archive.ph via Chrome.

**Direct fetch / Googlebot-UA spoof**: HTTP 401 from agent IPs. Do NOT use these.

**Legal/ToS:** web.archive.org is a public archive; for owner's personal research only, never redistribution.

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

## Full-body fallback

See [[bypass-paywalls]] skill for CAPTCHA instructions and manual usage. Call `read_article.sh`
directly from agent bash for ad-hoc reads; this skill handles automated daily RSS ingestion only.

> Educational, not advice. Headlines only; never fabricate a paywalled body.
