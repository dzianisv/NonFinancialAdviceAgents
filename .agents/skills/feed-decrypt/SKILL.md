---
name: feed-decrypt
description: Source adapter for Decrypt crypto news feed (decrypt.co) — fetch + normalize RSS into the common article record consumed by narrative-news + crypto-news-store. Use when gathering the crypto news feed, when narrative-news needs Decrypt coverage, or when asked for "Decrypt headlines" / "Decrypt crypto news". Fetch + normalize ONLY — does not dedup, store, or judge. Degrades to [UNAVAILABLE] on failure; never fabricates.
license: MIT
compatibility: opencode
metadata:
  audience: crypto-research-pipeline
  domain: news-feed-adapter
  role: source-adapter
  tier: crypto-native
---

# feed-decrypt (Decrypt source adapter)

A pure **fetch + normalize** adapter for one outlet. Emits the common article record (or `[UNAVAILABLE]`).
It does **not** dedup, store, embed, or judge relevance — that is [[crypto-news-store]] + [[narrative-news]].

## Hard rule

Never fabricate a title, body, date, or URL. On paywall/failure → `[UNAVAILABLE]`. Return **≥1 normalized record or a clean `[UNAVAILABLE]`** — never a half-record, never a silent empty (PRD AC5/AC6).

## Retrieval recipe

- **Endpoint (verified resolving, RSS 2.0):** `https://decrypt.co/feed`
- Fetch with `web_fetch` (pod) or curl/python (local). Parse RSS `channel > item`:
  - `title` → `title`
  - `link` → `url` (canonicalize: strip `#…` and `utm_*`/`ref`/`fbclid` params)
  - `pubDate` (RFC-822, e.g. `Mon, 15 Jun 2026 21:05:00 +0000`) → `published_at` (keep ISO-8601 UTC)
  - `description` (and/or `content:encoded`) → `summary` (strip HTML tags; do not invent prose)
  - `category` tags → `tags` (append tickers you can read verbatim, e.g. `BTC`, `MSTR`)
- `lang`: `en`. `source`: `decrypt`.

## Politeness (required)

- **Conditional GET** — send `If-None-Match` (ETag) / `If-Modified-Since` from the prior fetch; `304` → emit nothing-new, do not re-ingest.
- **Backoff** — on `429`/`5xx`: exponential backoff (e.g. 1s, 2s, 4s), retry ~2×, then `[UNAVAILABLE]`.
- One sequential fetch; do not hammer in parallel.

## Normalized output record

```json
{"source":"decrypt","url":"https://decrypt.co/<slug>","title":"...","published_at":"2026-06-15T21:05:00Z","summary":"...","lang":"en","tags":["BTC"]}
```
Emit a JSON list of these (most-recent first). Hand the list to `crypto-news-store ingest`.

## Failure mode

Feed 404/timeout/non-XML, or all retries exhausted → emit exactly:
```json
{"source":"decrypt","status":"[UNAVAILABLE]","reason":"<http code / parse error>"}
```

> Educational, not advice. Fetch + normalize only.
