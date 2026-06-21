---
name: feed-bloomberg
description: Source adapter for Bloomberg — NO reliable public RSS and heavy bot-blocking, so headline-via-search or [UNAVAILABLE]. Fetch + normalize whatever headline + url + published_at can be obtained into the common article record with body marked [UNAVAILABLE - paywall]. Use when gathering the crypto/macro news feed, when narrative-news needs Bloomberg macro coverage, or when asked for "Bloomberg headlines" / "Bloomberg news". Fetch + normalize ONLY — no dedup/store/judge. NEVER fabricates a title or body.
license: MIT
compatibility: opencode
metadata:
  audience: crypto-research-pipeline
  domain: news-feed-adapter
  role: source-adapter
  tier: macro-paywalled
---

# feed-bloomberg (Bloomberg source adapter — best-effort headlines only)

Pure **fetch + normalize** adapter for a **paywalled, RSS-less, bot-blocked** outlet. Dedup/store/judge
live downstream in [[crypto-news-store]] + [[narrative-news]].

## Limitation (documented, by design)

Bloomberg **does not publish a reliable public RSS feed** and aggressively bot-blocks scrapers
(`403`/CAPTCHA). There is **no stable retrieval recipe**. This adapter is therefore **best-effort
headline-only** and will frequently return `[UNAVAILABLE]` — that is correct behavior, not a failure.

## Hard rule

**NEVER fabricate a title, body, date, or URL.** If a real Bloomberg headline + canonical URL cannot be
obtained, emit `[UNAVAILABLE]`. Headline-only with body `[UNAVAILABLE - paywall]` is acceptable; invented
prose or a guessed headline is a defect (PRD AC6). Return **≥1 real headline record or a clean
`[UNAVAILABLE]`** (AC5).

## Retrieval recipe (best-effort, in priority order)

1. **Web search for a real headline** (`web_search` "Bloomberg crypto <topic>"): if a result is genuinely a
   `bloomberg.com` article, take its **headline + canonical `bloomberg.com` URL + published date** from the
   search result metadata only. Body = `"[UNAVAILABLE - paywall]"`.
2. **Do NOT** attempt to fetch/scrape the article page (bot-block; and scraping the paywalled body would
   risk fabrication).
3. If neither yields a verifiable real headline+URL → `[UNAVAILABLE]`.

Often a Bloomberg story is also covered by a crypto-native outlet ([[feed-coindesk]] etc.) — that coverage
will enter the store anyway and the cross-outlet dedup gives it a `source_count`. Bloomberg here is a bonus,
not a required seat.

## Politeness

Single search; no aggressive retries against bloomberg.com. Backoff on any `429`.

## Normalized output record (only if a REAL headline+URL was found)

```json
{"source":"bloomberg","url":"https://www.bloomberg.com/news/articles/<id>","title":"<real headline>","published_at":"2026-06-15T...Z","summary":"[UNAVAILABLE - paywall]","lang":"en","tags":["macro"]}
```

## Failure mode (the common case)

```json
{"source":"bloomberg","status":"[UNAVAILABLE]","reason":"no public RSS / bot-block; no verifiable headline"}
```

## Caching (required)

After fetching, ingest each article into the shared SQLite cache so downstream agents can BM25-search without re-fetching:

```bash
python3 /Users/engineer/workspace/backtest/.agents/scripts/feeds/fetch_article.py \
  --ingest --url "<article-url>" --title "<headline>" \
  --body "<body text or [UNAVAILABLE - paywall]>" --source "bloomberg"
```

Cache is deduped by (url, date) — safe to re-run. Query later: `python3 fetch_article.py --search "nvidia" --limit 5`.

> Educational, not advice. Best-effort headline only; never fabricate Bloomberg content.
