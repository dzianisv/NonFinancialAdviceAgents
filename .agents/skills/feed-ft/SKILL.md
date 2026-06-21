---
name: feed-ft
description: Source adapter for the Financial Times (FT) — PAYWALLED, RSS descriptions/teasers available as summary. Fetch + normalize the FT RSS into the common article record (headline + url + published_at) with body from RSS teaser (or [UNAVAILABLE - paywall] if empty). Use when gathering the crypto/macro news feed, when narrative-news needs FT coverage, or when asked for "FT headlines" / "Financial Times news". Fetch + normalize ONLY — no dedup/store/judge. NEVER fabricates a body.
license: MIT
compatibility: opencode
metadata:
  audience: crypto-research-pipeline
  domain: news-feed-adapter
  role: source-adapter
  tier: macro-paywalled
---

# feed-ft (Financial Times source adapter — RSS teasers available)

Pure **fetch + normalize** adapter for a **paywalled** outlet. FT bodies are behind a hard paywall, so this
adapter emits **headline + url + published_at + RSS teaser** (the publisher's own `description`) and marks
the body `[UNAVAILABLE - paywall]` only when the RSS teaser is absent. Dedup/store/judge live downstream in
[[crypto-news-store]] + [[narrative-news]].

## Hard rule (paywall)

**NEVER fabricate body text.** Headline-only is acceptable; invented prose is a defect (PRD AC6). On any
failure → `[UNAVAILABLE]`. Return **≥1 headline record or a clean `[UNAVAILABLE]`** (AC5).

## Retrieval recipe

- **Primary endpoint (verified working 2026-06-20):** Google News RSS filtered to FT:
  `https://news.google.com/rss/search?q=site%3Aft.com+when%3A7d&hl=en-US&gl=US&ceid=US%3Aen`
  Returns ~100 articles/7 days. Use topic-specific variants for targeted research:
  `https://news.google.com/rss/search?q=site%3Aft.com+AI+semiconductors+when%3A7d&hl=en-US&gl=US&ceid=US%3Aen`
  URLs are opaque Google News redirects (work in browsers, not directly resolvable to FT bodies).
- **DEPRECATED:** `https://www.ft.com/rss/home` — FT aggressively bot-blocks from agent/datacenter IPs;
  returns `403` or a login-redirect stub (~7KB of HTML, not real articles). Do NOT use as primary.
- Parse: `title`→title, `link`→url (canonicalize, strip `utm_*`), `pubDate`(RFC-822)→`published_at` (ISO-8601 UTC). **`summary` = `"[UNAVAILABLE - paywall]"`** (do NOT scrape or guess the body). `lang: en`, `source: ft`.
- The RSS `description`, if present, is FT's own short teaser — you MAY keep it verbatim as `summary` (it is
  publisher-provided, not fabricated). If empty/absent → `[UNAVAILABLE - paywall]`.

## Reading the BODY (verified method, June 2026)

For the full article body, use the script — **no extension required**:

```bash
/Users/engineer/workspace/backtest/.agents/scripts/feeds/read_article.sh "<ft-url>"
```

**Method:** `archive.ph/newest/<url>` via Chrome (chrome-use). FT hard paywall means content is NOT in
DOM when paywalled — archive.ph captures it. Verified 2026-06-20 on a live FT article.

**CAPTCHA:** archive.ph needs a one-time Cloudflare CAPTCHA per browser session. If `[UNAVAILABLE - archive.ph CAPTCHA]` returned, open `https://archive.ph` in Chrome, solve it, retry.

**What does NOT work for FT:**
- Wayback Machine — FT serves "Subscribe to read" wall to Wayback crawler
- Direct fetch — 403 bot-block from agent IPs; hard paywall in browser
- 12ft.io — broken SSL (`ERR_CERT_AUTHORITY_INVALID`)
- bypass-paywalls-clean extension — NOT installed in this Chrome

**Legal/ToS:** archive.today is a public archive; for owner's personal research only, never redistribution.

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

## Full-body fallback

See [[bypass-paywalls]] skill for CAPTCHA instructions and manual usage. Call `read_article.sh`
directly from agent bash for ad-hoc reads; this skill handles automated daily RSS ingestion only.

> Educational, not advice. Headlines only; never fabricate a paywalled body.
