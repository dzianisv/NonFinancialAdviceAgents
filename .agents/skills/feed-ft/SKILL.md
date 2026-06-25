---
name: feed-ft
description: Source adapter for the Financial Times (FT) — PAYWALLED, RSS descriptions/teasers available as summary. Fetch + normalize the FT RSS into the common article record (headline + url + published_at) with body from RSS teaser (or [UNAVAILABLE - paywall] if empty). When an agent needs FT news on demand, run `scripts/fetch_ft.ts` to print live FT headlines + real URLs + teasers to stdout (no DB, no deps). Use when gathering the crypto/macro news feed, when narrative-news needs FT coverage, or when asked for "FT headlines" / "Financial Times news" / "what is the FT saying about X". Fetch + normalize ONLY — no dedup/store/judge. NEVER fabricates a body.
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

## On-demand fetch (agent) — START HERE

When you (an agent) need FT news **right now**, run the self-contained fetcher. It pulls FT's native
section RSS, normalizes + dedups, and prints to **stdout** — no database, no npm deps (Bun built-ins):

```bash
bun /Users/engineer/workspace/backtest/.agents/skills/feed-ft/scripts/fetch_ft.ts [flags]
```

| Flag | Default | Meaning |
|---|---|---|
| `--section a,b,c` | `markets,companies,global-economy,world` | FT sections; any `ft.com/<section>` works (technology, lex, unhedged, alphaville, …) |
| `--query "terms"` | — | Case-insensitive filter over title+teaser; multiple words = AND |
| `--days N` | `7` | Keep only items published within N days |
| `--limit N` | `50` | Cap the number of records |
| `--text` | off | Human-readable lines instead of JSON |

```bash
# Latest markets + companies headlines as JSON
bun .../scripts/fetch_ft.ts --section markets,companies --limit 20

# What is the FT saying about AI chips this week, human-readable?
bun .../scripts/fetch_ft.ts --query "AI chips" --days 7 --text
```

**Output:** JSON array of `{source,url,title,published_at,summary,tags}` (newest first). Each `summary` is
FT's own teaser, or `"[UNAVAILABLE - paywall]"` if FT shipped none — **never a fabricated body**. If every
section fails the script prints a single `{"status":"[UNAVAILABLE]","reason":...}` record and exits non-zero.
For full article text use the logged-in-Chrome reader in **Reading the BODY** below.

Tests (deterministic, no network): `bun test ./.agents/skills/feed-ft/scripts/fetch_ft.test.ts`.

## Hard rule (paywall)

**NEVER fabricate body text.** Headline-only is acceptable; invented prose is a defect (PRD AC6). On any
failure → `[UNAVAILABLE]`. Return **≥1 headline record or a clean `[UNAVAILABLE]`** (AC5).

## Retrieval recipe

- **Primary endpoint (verified working 2026-06-25):** FT native section RSS — `https://www.ft.com/<section>?format=rss`.
  Returns real `ft.com/content/<uuid>` article URLs **plus a short publisher teaser** (~25 items/section).
  Use these sections for macro/markets coverage:
  `markets` · `companies` · `global-economy` · `world` · `technology` · `lex` · `unhedged`
  Example: `https://www.ft.com/markets?format=rss`
- **DEPRECATED (dead):** `https://www.ft.com/rss/home` and `…/rss/markets` — the `/rss/*` paths 301-redirect to
  a stale stub (`/rss/home/international`) and return ~0 usable items. Do NOT use.
- **Optional topical fallback (opaque URLs):** Google News RSS filtered to FT —
  `https://news.google.com/rss/search?q=site%3Aft.com+<terms>+when%3A7d&hl=en-US&gl=US&ceid=US%3Aen`.
  Use ONLY for targeted topic search; its links are opaque Google redirects (not real ft.com paths).
- Parse: `title`→title, `link`→url (real ft.com/content URL; canonicalize, strip `utm_*`/tracking),
  `pubDate`(RFC-822)→`published_at` (ISO-8601 UTC), `description`→`summary` (FT's own teaser — keep
  **verbatim**, never scrape or fabricate the body). If a teaser is absent → `summary = "[UNAVAILABLE - paywall]"`.
  `lang: en`, `source: ft`.
- **Pipeline:** the automated ingest is `crypto-news-store/news_fetch.py` (Python, drives narrative-news)
  and `trend-stock-research/scripts/feeds/feed_ft.ts` (TS) — both already point at these endpoints.

## Reading the BODY

For the full article body, use the script:

```bash
bun /Users/engineer/workspace/backtest/.agents/scripts/feeds/read_article.ts "<ft-url>"
```

**Method:** Chrome live — navigates to the actual FT URL using your logged-in Chrome session.
Content IS in DOM when subscribed. **One-time setup required:** open `https://www.ft.com` in
Chrome and sign in with your FT subscription. After that the script works automatically.

**Error `Chrome: paywall in DOM — SETUP REQUIRED`:** sign in to ft.com in Chrome, then retry.

**What does NOT work for FT:**
- Wayback Machine — FT serves "Subscribe to read" wall to Wayback; BLOCKED
- Bing cache (`cc.bingj.com`) — DNS does not resolve
- Google cache — deprecated, returns error page
- archive.ph — Cloudflare CAPTCHA every session; abandoned
- Direct fetch — 403 bot-block from agent IPs; hard paywall in browser
- 12ft.io — broken SSL (`ERR_CERT_AUTHORITY_INVALID`)
- archive.ph via curl — Cloudflare CAPTCHA blocks datacenter IPs

**Legal/ToS:** archive.today is a public archive; for owner's personal research only, never redistribution.

## Politeness (required)

Conditional GET (ETag/If-Modified-Since; `304` → nothing-new). Exponential backoff on `429`/`5xx`, ~2 retries, then `[UNAVAILABLE]`. Sequential fetch. Respect the bot-block — do not retry aggressively.

## Normalized output record

```json
{"source":"ft","url":"https://www.ft.com/content/<id>","title":"EasyJet in talks with Castlelake after rejecting £4.9bn takeover offer","published_at":"2026-06-24T...Z","summary":"Budget airline turned down offer that US private credit firm valued the carrier at...","lang":"en","tags":["companies"]}
```

The `summary` is FT's own RSS teaser (1 sentence). Body text is NOT in the feed — for full body use the
logged-in-Chrome `read_article.ts` above. If a teaser is missing → `summary:"[UNAVAILABLE - paywall]"`.

## Failure mode

```json
{"source":"ft","status":"[UNAVAILABLE]","reason":"paywall / 403 bot-block / fetch failed"}
```

## Full-body fallback

See [[bypass-paywalls]] skill for CAPTCHA instructions and manual usage. Call `read_article.ts`
directly from agent bash for ad-hoc reads; this skill handles automated daily RSS ingestion only.

> Educational, not advice. Headlines only; never fabricate a paywalled body.
