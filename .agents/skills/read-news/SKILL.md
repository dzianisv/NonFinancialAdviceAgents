---
name: read-news
description: The ONE front door for the financial-news pipeline — fetch + normalize + dedup + store + query, in a single Bun/TypeScript stack. Pulls every wired RSS feed (CoinDesk, Decrypt, CoinTelegraph, The Block, Bitcoin Magazine, Coinbase, FT, WSJ, Bloomberg) via `read_news.ts`, collapses multi-outlet coverage of the same story into ONE event (SQLite + FTS5 BM25 + near-dup Jaccard clustering), keeps cross-run state so the panel never re-reads news it already saw, and answers ranked hybrid queries. Use when gathering the crypto/macro news feed, when narrative-news / analyse-narrative needs deduped events, when an advisor needs FT/WSJ headlines on demand, or when asked to "get the news", "what's new since last run", "dedup crypto news", "cluster multi-outlet coverage", "query the news store", "FT headlines", "WSJ markets news", or "what is the news saying about X". Keyless, no API key, no embedding model required. NEVER fabricates a headline or body.
license: MIT
compatibility: opencode
metadata:
  audience: crypto-research-pipeline
  domain: news-fetch-dedup-store-query
  role: unified-news-pipeline
---

# Read News (fetch → dedup → store → query — events, not articles, and never twice)

The single news pipeline the [[narrative-news]] and [[analyse-narrative]] gather seats read. It
**fetches** every wired feed, **normalizes** each article into the common record, **collapses
multi-outlet coverage of the same event into ONE event** carrying a `source_count` (crowdedness), and
**keeps state across runs** so the panel never re-reads news it already saw — the same "no re-alert"
discipline as [[analyse-smartmoney-13f]] / [[dip-scanner]].

This skill replaces the old `feed-*` per-source adapters and the `crypto-news-store` Python store: one
Bun/TypeScript stack, one SQLite file, one front door.

## Hard rule

Never fabricate. The store only ever holds what the feeds actually fetched. Paywalled sources with no
teaser surface `[UNAVAILABLE - paywall]`; a feed that fails to fetch surfaces loudly in `unavailable` —
never silently dropped, never invented.

## One command (preferred — fetch + ingest + ranked events in one shot)

```bash
bun .agents/skills/read-news/scripts/read_news.ts \
  --db .cache/read-news/news.db --days 5 \
  --query "bitcoin BTC ETF regulation treasury strategy"
# → {fetched, feeds_ok, unavailable:[...], events:[ {title, source_count, ...} ranked by relevance ]}
```

`--query` returns the hybrid (BM25 + near-dup) **relevant** events and cuts the new-since noise; omit it
to get everything new-since. Build `--query` from the asset(s)/entities in the workflow question. Per-feed
failures come back in `unavailable` (loud) — never silently dropped.

| Flag | Default | Meaning |
|---|---|---|
| `--db` | `.cache/read-news/news.db` (env `CRYPTO_NEWS_DB`) | SQLite file |
| `--days` | `3` | recency window for new-since / query / discovery |
| `--k` | `15` | max events returned by `--query` / per-asset queries |
| `--query` | `""` | if set → ranked relevant events (also the Google News search topic); else → all new-since |
| `--source` | all | CSV to restrict feeds, e.g. `--source ft,wsj` or `--source yahoo,googlenews` |
| `--asset` | — | single ticker/symbol; also fetches the 5 keyless per-asset sources and queries by asset |
| `--assets` | — | CSV batch form of `--asset`, e.g. `--assets AAPL,MSFT,NVDA`; coexists with `--asset` (merged) |
| `--equities-only` | off | opt-in filter for an `--asset`/`--assets` run: drops CoinMarketCap (crypto-only per-asset source) and the 6 crypto-only RSS firehose feeds, unless `--source` was explicitly given (explicit `--source` always wins) |

After the brief is written, mark events surfaced so they don't repeat next run:

```bash
bun .agents/skills/read-news/scripts/news_store.ts --db .cache/read-news/news.db mark-surfaced --ids 1 4 --on 2026-06-15
```

### Batch equities and targeted discovery — CLI examples

```bash
# Existing single-asset form — TradingView, CoinMarketCap, Google Finance, Morningstar, Yahoo + firehose
bun .agents/skills/read-news/scripts/read_news.ts --asset AAVE --days 7

# New batch form — multiple equity tickers, skip irrelevant crypto/firehose sources
bun .agents/skills/read-news/scripts/read_news.ts --assets AAPL,MSFT,NVDA --equities-only --days 5
# → adds a `by_asset: {AAPL:[...], MSFT:[...], NVDA:[...]}` breakdown alongside the flat `events` union

# Targeted publisher discovery via Google News (Bloomberg/Reuters/Business Insider/CNBC/IBD only)
bun .agents/skills/read-news/scripts/read_news.ts --source googlenews --query "AI capex slowdown" --days 3

# Yahoo Finance ticker-scoped headlines only
bun .agents/skills/read-news/scripts/read_news.ts --source yahoo --asset AAPL --days 5
```

## Targeted single-source pulls (FT / WSJ on demand)

When an advisor wants only FT or only WSJ headlines (no DB, prints to stdout):

```bash
bun .agents/skills/read-news/scripts/feeds/ft.ts  --section markets,global-economy --query bitcoin --days 5 --text
bun .agents/skills/read-news/scripts/feeds/wsj.ts --feed markets --days 5 --limit 20 --text
```

## What it is

`scripts/` — **Bun + `bun:sqlite` only** (no network at store layer, no embedding model, zero npm deps).

- `read_news.ts` — the orchestrator: fetch all feeds → ingest (dedup + state) → query / new-since → JSON.
- `news_store.ts` — the SQLite store (single file, default `.cache/read-news/news.db`):
  - **`articles`** — one row per ingested article (+ `canonical_url`, `content_hash`, `simhash`).
  - **`articles_fts`** (FTS5) — BM25 over `title + summary` for named entities/tickers (`MSTR`, `$11B`, `ETF`).
  - **`events`** — one row per event cluster carrying cross-run state: `{first_seen, last_updated,
    sources(json), source_count, surfaced_to_panel_on}`.
- `feeds/` — fetch + normalize adapters: `ft.ts`, `wsj.ts`, `crypto.ts` (7 generic-RSS feeds), `markets.ts`
  (TradingView, CoinMarketCap), `googlefinance.ts`, `morningstar.ts`, `yahoo.ts` (per-asset), `googlenews.ts`
  (discovery-only) — unified by `feeds/index.ts` → `fetchAllNews({sources?, assets?, query?, days?}) →
  {records, unavailable}`.

### Two-layer dedup
1. **Exact** — canonical URL (utm/tracking stripped) **OR** `sha256(normalized(title+summary))` already
   present → skip re-ingest.
2. **Near-dup** — token-shingle (word + bigram) **Jaccard** over normalized text; `>= 0.15`
   (env `CRYPTO_NEWS_JACCARD`) attaches the article to the existing event and bumps its `source_count`.
   **Jaccard, not SimHash Hamming, is the deciding metric** — on short news text (headline + summary)
   same-event Jaccard ≈ 0.27 vs different-event ≈ 0.03–0.05 (clean separation); SimHash Hamming on the
   same text was 21 vs 30 (too close). A 64-bit SimHash is still computed and stored as a coarse signature.

### OPTIONAL dense-vector upgrade (graceful, never crashes)
Set env `CRYPTO_NEWS_EMBED_CMD` to a shell command that reads text on stdin and prints a JSON float array
on stdout. If set **and** it works, near-dup uses cosine `>= CRYPTO_NEWS_EMBED_COS` (default 0.85) and the
vector is stored on the event. If absent **or** the command errors, it silently falls back to Jaccard.

### Hybrid retrieval (query)
BM25 (FTS5) **fused with** near-dup-cluster Jaccard rank via **RRF** (reciprocal-rank fusion, k=60).
Returns **events, not raw rows**.

## Source ownership — read-news is the sole fetch front door

`read_news.ts` is the ONE place any skill/workflow fetches financial news from. Consumers
([[narrative-news]], [[analyse-narrative]], `crypto-advisor`, `stocks-trend-screener`, etc.) must call
`read_news.ts` and read its `{events}` / `{unavailable}` output — they must never scrape any of the sources
below directly (no ad-hoc `curl`/`fetch` against FT, WSJ, TradingView, CoinMarketCap, Google Finance,
Morningstar, Yahoo, or Google News from consumer code). Centralizing fetch here is what makes dedup,
cross-run state, and the `[UNAVAILABLE]` honesty contract actually hold.

## Source classes and access limits

| Class | Sources | Access pattern |
|---|---|---|
| **Keyless firehose** (default `NEWS_FEEDS`, 10 sources) | FT, WSJ, **Bank of America Institute (new, higher-authority)**, 6 crypto-only RSS (CoinDesk, Decrypt, CoinTelegraph, The Block, Bitcoin Magazine, Coinbase blog), Bloomberg markets RSS | Global feed, fetched every run unless `--source` restricts it |
| **Keyless per-asset** (5 sources, ticker-scoped) | TradingView, CoinMarketCap (crypto-only), Google Finance, Morningstar, **Yahoo Finance (new)** | Opt-in via `--asset`/`--assets` + `--source`; one fetch per source per requested ticker |
| **Keyless discovery-only** (1 source, query/topic-scoped) | **Google News (new)** | Targeted `site:` search restricted to Bloomberg/Reuters/Business Insider/CNBC/IBD; requires `--query` or an explicit `--asset`/`--assets` symbol as the search topic — refuses (`[UNAVAILABLE]`, no network call) rather than silently fanning out an unscoped firehose search over default tickers |
| **Entitlement-gated / not integrated** | **JPMorgan and BofA Global Research** (sell-side/analyst research) | `[UNAVAILABLE - license required]`. No endpoint, no scraping, no paywall bypass, no unofficial reseller, no placeholder vendor claim exists or will be added until a licensed official feed is explicitly configured. This is a **permanent documented limitation**, not a TODO. **Not the same product** as the public Bank of America Institute feed above — see note below. |
| **Explicitly excluded** | Seeking Alpha | Is not, and will not be, added as a source. |

Google News is fundamentally a free-text SEARCH endpoint, not a firehose — there is no "fetch everything"
mode, so it is kept out of the per-asset `MARKET_SOURCES` loop and out of `NEWS_FEEDS`. Calling
`fetchAllNews({ sources: ["googlenews"] })` with neither `--query` nor `--asset`/`--assets` returns
immediately with an `[UNAVAILABLE - no --query or --asset provided]` entry and makes zero network calls —
it will never silently search the internal default crypto ticker list as bare text.

**Bank of America Institute vs. BofA Global Research — do not conflate these.** `source: "bofainstitute"`
is Bank of America **Institute** — BofA's public-facing macro/consumer research arm, published free at
`institute.bankofamerica.com` (household spending, small-business, wealth transformation, sustainability
studies from aggregated BofA transaction/deposit data). It is a different desk, a different product, and a
different licensing status from BofA **Global Research** (BofA's sell-side equity/credit analyst research),
which remains entitlement-gated per the row above and is **not** integrated. Never relabel one as the other
in code, comments, docs, or downstream reports.

**Higher-authority sources.** `news_store.ts` defines `AUTHORITATIVE_SOURCES` (currently just
`"bofainstitute"`) — official primary-source institutional research that publishes its own proprietary
data, as opposed to secondary reporting. Any event citing an authoritative source gets `authoritative: true`
in its `EventRecord`, and `query()`'s RRF fusion score gets a small additive `AUTHORITY_BONUS` (`0.005`,
≈30% of one RRF rank term). This is a bounded tie-breaker among results that already cleared the normal
BM25/Jaccard relevance bar — it can reorder near-ties, it cannot promote an irrelevant authoritative-source
match over a clearly more relevant one. It does not affect dedup/clustering or `source_count`, which are
computed identically regardless of source.

**Source priority for narrative analysis:**
1. `read_news.ts` — primary; run first, covers the 10-feed firehose plus any per-asset/discovery sources requested
2. `--source googlenews --query "..."` — targeted Bloomberg/Reuters/BI/CNBC/IBD entity search when the firehose misses a name
3. SEC EDGAR (`analyse-fundamental` / direct `web_fetch`, not this pipeline) — hard, timestamped primary-source regulatory/treasury events
4. CoinGecko trending (direct `web_fetch`, not this pipeline) — retail attention signal
5. farside.co.uk — ETF flows; WebFetch/CDP path only (JS-rendered, not curl-able, not wired into this pipeline)

## Store commands

```bash
S="bun .agents/skills/read-news/scripts/news_store.ts"   # add --db <path> for a throwaway store

$S --db .cache/read-news/news.db ingest --json records.json   # idempotent → {new, duplicate, events_touched}
$S query --q "strategy bitcoin" --days 2 --k 10           # HYBRID BM25+near-dup, fused via RRF → events
$S new-since --days 2                                     # events in window AND not yet surfaced (panel feed)
$S mark-surfaced --ids 1 4 --on 2026-06-15                # stamp surfaced; excludes from future new-since
```

`records.json` is a JSON list of normalized records `{source, url, title, summary, published_at, lang,
tags}` (optional `body`). `ingest` accepts a bare list or `{"records": [...]}`. `published_at` is an
ISO datetime of a **verified publisher date**, or `null` when the source has none (optional
`date_provenance: "unavailable"` makes that explicit) — never a fetch/ingest-time substitute. See
`read-news/README.md` "Date semantics" for the full contract and the `bofainstitute` feed as the
canonical example of a source with no publisher-supplied dates.

## Self-test (run to verify the install)

```bash
bun test ./.agents/skills/read-news/scripts/
# news_store.test.ts includes a GOLDEN PARITY gate: a frozen snapshot of the retired Python store's
# exact ingest counts, new-since set, and query ranking (captured before retirement). The TS store must
# reproduce them — the regression guard that lets the Python pipeline stay retired.
```

## Citation and body rules — never fabricate

The hard rule at the top of this doc ("never fabricate; `[UNAVAILABLE - paywall]` when no teaser exists")
extends explicitly to every new source:
- **Google News** links (`news.google.com/rss/articles/...`) are opaque Google-internal redirects. They are
  **discovery pointers, never resolved/verified citations** — this adapter never claims otherwise, and never
  fabricates a summary from the RSS `<description>` (which is just repeated anchor markup). `body` is always
  `null` by construction.
- **Yahoo Finance** `<link>` values ARE genuinely navigable citation URLs, but treat `source: "yahoo"` as
  "Yahoo's aggregation of this story," not "the original outlet" — Yahoo sometimes hosts syndicated copies
  rather than the true original publisher.
- **Morningstar / Google Finance consensus** records now carry content-derived URL discriminators (a
  `?h=<shortHash(...)>` query param appended to the same page URL) so that multiple distinct headlines
  scraped off one shared page get distinct dedup keys instead of collapsing into one record — see the
  same-page-dedup fix in `morningstar.ts`/`googlefinance.ts`. The discriminator changes the URL string for
  storage/dedup purposes only; it still points at the same real page, so citation provenance for a human
  reader is unchanged.
- **Bank of America Institute (`bofainstitute`)** pages carry no publisher-authored publication date
  (no `datePublished`/`article:published_time`/similar metadata as of 2026-07 inspection). The rule
  extends to dates, not just body/summary text: `published_at` is `null` (`date_provenance:
  "unavailable"`) rather than a fabricated fetch-time or the sitemap's `<lastmod>` (an UPDATE
  timestamp, never a publication date) relabeled as one. The article is still kept and ingested —
  dropping every dateless page would make a real, valuable primary-source feed useless. The gap is
  surfaced per-article, in-band, via `published_at: null` + `date_provenance: "unavailable"` on the
  `Article` itself — and is deliberately never pushed into `errors`/the top-level `unavailable`
  array, since an unverifiable publisher date is not a fetch failure and must not make a
  successfully-fetched feed look broken. See `read-news/README.md` "Date semantics" and
  `feeds/bofainstitute.ts`.

## Boundary with `analyse-sellside`

`read-news`'s Morningstar and Google Finance fetchers return **news headlines only**, for event clustering.
Structured sell-side data — analyst consensus ratings, price targets, fair-value/moat scores — is owned by
the separate `analyse-sellside` skill, which fetches its own data directly via `web_fetch` (not through this
pipeline). `read-news` must never attempt to route or re-derive that structured data through its
news-event clustering pipeline; if a workflow needs consensus ratings/price targets, call `analyse-sellside`
directly instead of trying to mine it out of `read_news.ts` headlines.

## Fit

`read_news.ts` (fetch + normalize via `feeds/`) → **`ingest`** (dedup + cluster) → **`new-since` / `query`**
→ [[narrative-news]] / [[analyse-narrative]] emit the NEW/updated events to the panel and own the
priced-in judgment. This skill owns fetch + dedup + recency + cross-run state; it does not judge.

> Educational, not advice. Events are context + disconfirmation, never a trigger.

## Per-Asset Market News Sources (2026-07)

Five keyless, ticker-scoped market news fetchers live in `scripts/feeds/markets.ts`, `googlefinance.ts`,
`morningstar.ts`, and `yahoo.ts` — plus a 6th, discovery-only source (`googlenews.ts`) that is query/topic
driven rather than purely ticker-driven.

| Source | Method | Keyless? | Per-asset tag | AI summary |
|---|---|---|---|---|
| TradingView | JSON API (v2 headlines + v3 story AST) | ✅ Yes | `relatedSymbols` mapped via `tvSymbolToAsset` | v3 story AST flattened to text |
| CoinMarketCap | JSON API (resolve slug→id, then /content/v3/news) | ✅ Yes (crypto-only) | Set to queried asset (CMC NER is noisy) | `meta.subtitle` teaser only |
| Google Finance | HTML scrape (regex external news URLs) | ✅ Yes | Ticker from query symbol | ❌ Client-rendered, blank |
| Morningstar | HTML scrape | ✅ Yes | Ticker from query symbol | Headline only |
| **Yahoo Finance (new)** | RSS (`feeds.finance.yahoo.com/rss/2.0/headline`) | ✅ Yes | Full requested symbol list tagged (imprecise on multi-symbol requests, same caveat pattern as CMC) | RSS `<description>` teaser or `[UNAVAILABLE - no teaser in feed]` |
| **Google News (new, discovery-only)** | RSS search (`news.google.com/rss/search`) restricted to Bloomberg/Reuters/Business Insider/CNBC/IBD via `site:` | ✅ Yes | None — query/topic driven, not ticker-driven | Never — `body` always `null`, discovery pointer only |

**Findings:**
- TradingView and CoinMarketCap: keyless JSON, no browser required, full AI digest available (TradingView).
- Google Finance / Morningstar: keyless HTML scrape, headlines only, AI summary unavailable to curl.
- Yahoo Finance: keyless RSS, genuinely navigable links, but an unofficial legacy route that could stop
  working without notice.
- Google News: keyless RSS search, publisher-whitelisted, discovery-only by design — never a resolved
  citation, never a firehose.

**Usage:**
```bash
# Fetch news for a specific asset (5 per-asset sources + all RSS feeds), query by asset
bun .agents/skills/read-news/scripts/read_news.ts --asset AAVE --days 7

# Batch multiple assets, equities-focused (drops CoinMarketCap + crypto-only firehose)
bun .agents/skills/read-news/scripts/read_news.ts --assets AAPL,MSFT,NVDA --equities-only --days 5

# Query the store directly by asset after ingestion
bun .agents/skills/read-news/scripts/news_store.ts by-asset --asset AAVE
```
