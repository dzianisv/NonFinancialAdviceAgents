---
name: feed-coinbase
description: Source adapter for the Coinbase blog + institutional research feed (coinbase.com/blog, coinbase.com/institutional) — fetch + normalize into the common article record consumed by narrative-news + crypto-news-store. Covers Coinbase product/listing/regulatory posts AND the "Coinbase Bytes" newsletter / mailing-list content (published on the blog). Use when gathering the crypto news feed, when narrative-news needs Coinbase first-party coverage, or when asked for "Coinbase blog", "Coinbase Bytes", "Coinbase newsletter", "any new listings". Fetch + normalize ONLY — no dedup/store/judge. Degrades to [UNAVAILABLE]; never fabricates.
license: MIT
compatibility: opencode
metadata:
  audience: crypto-research-pipeline
  domain: news-feed-adapter
  role: source-adapter
  tier: crypto-native-firstparty
---

# feed-coinbase (Coinbase blog + institutional source adapter)

Pure **fetch + normalize** adapter for Coinbase's own publishing channels — the product blog, the
institutional research insights, and the **Coinbase Bytes** newsletter (the "mailing list"; its content is
published on the blog, so no email scraping is needed). Emits the common record (or `[UNAVAILABLE]`).
Dedup/store/judge live downstream in [[crypto-news-store]] + [[narrative-news]].

## Why first-party matters

Coinbase posts are **primary-source catalysts**, not commentary: new asset listings (the "Coinbase effect"),
roadmap/perp-futures launches, regulatory wins/losses, and institutional research notes often move price or
de-risk a thesis before secondary outlets cover them. Treat as `ACTIONABLE_CONTEXT` when it's a listing /
product / regulatory hard event; otherwise `PRICED_IN` marketing.

## Hard rule

Never fabricate. On failure → `[UNAVAILABLE]`. Return **≥1 record or a clean `[UNAVAILABLE]`**.

## Retrieval recipe

- **Direct RSS is Cloudflare-gated** — `https://www.coinbase.com/blog/rss.xml` and `blog.coinbase.com/feed`
  return `403 "Just a moment…"` to urllib. Do NOT rely on them.
- **Working endpoint (Google News RSS proxy, same workaround as [[feed-wsj]]):**
  `https://news.google.com/rss/search?q=(site%3Acoinbase.com%2Fblog+OR+site%3Acoinbase.com%2Finstitutional)+when%3A14d&hl=en-US&gl=US&ceid=US%3Aen`
  Returns standard RSS 2.0 `channel > item`. Wired into `crypto-news-store/news_fetch.py` as feed key `coinbase`.
- Parse RSS `item`: `title`→title (strip trailing ` - Coinbase`), `link`→url (Google redirect URL — accepted,
  same as wsj), `pubDate`(RFC-822)→`published_at` (ISO-8601 UTC), `description`→`summary` (strip HTML).
  `lang: en`, `source: coinbase`.

## Politeness (required)

Conditional GET (ETag/If-Modified-Since; `304` → nothing-new). Exponential backoff on `429`/`5xx`, ~2 retries,
then `[UNAVAILABLE]`. Sequential fetch.

## Normalized output record

```json
{"source":"coinbase","url":"https://news.google.com/rss/articles/...","title":"Coinbase launches in India with direct INR rails","published_at":"2026-06-..Z","summary":"...","lang":"en","tags":["listing"]}
```

## Failure mode

```json
{"source":"coinbase","status":"[UNAVAILABLE]","reason":"<http code / parse error>"}
```

## Caching (required)

After fetching, ingest each article into the shared SQLite cache so downstream agents can BM25-search without re-fetching:

```bash
python3 /Users/engineer/workspace/backtest/.agents/scripts/feeds/fetch_article.py \
  --ingest --url "<article-url>" --title "<headline>" \
  --body "<body text or [UNAVAILABLE - paywall]>" --source "coinbase"
```

Cache is deduped by (url, date) — safe to re-run. Query later: `python3 fetch_article.py --search "nvidia" --limit 5`.

> Educational, not advice. Fetch + normalize only.
