---
name: crypto-news-store
description: Local HYBRID news store (SQLite + FTS5 BM25 + deterministic near-dup clustering) so the crypto panel sees deduped EVENTS, not raw articles, and never re-surfaces the same news across runs. Use when ingesting normalized articles from the feed-* skills, when the narrative-news gather seat needs the state-aware "what's new since last run" feed, or when asked to "dedup crypto news", "cluster multi-outlet coverage into one event", "query the news store", or "what crypto news is new". Keeps cross-run state keyed by event_cluster_id. Stdlib python3 only — no embedding model required.
license: MIT
compatibility: opencode
metadata:
  audience: crypto-research-pipeline
  domain: news-ingestion-dedup-state
  role: hybrid-event-store
---

# Crypto News Store (events, not articles — and never twice)

The dedup + state layer the [[narrative-news]] gather seat reads. The [[feed-*]] adapters fetch + normalize
articles; this store **collapses multi-outlet coverage of the same event into ONE event** carrying a
`source_count` (crowdedness, NFR2), and **keeps state across runs** so the panel never re-reads news it
already saw — the same "no re-alert" discipline as [[13f-watch]] / [[crypto-dip-scanner]].

## Hard rule

Never fabricate. The store only ever holds what `feed-*` actually fetched. It judges dedup/recency/state — it does not invent text.

## What it is

`news_store.py` — **stdlib python3 + sqlite3 only** (runs in agent bash with python3.12; no network, no
embedding model). Single SQLite file, default `crypto/news/news.db`.

- **`articles`** — one row per ingested article (+ `canonical_url`, `content_hash`, `simhash`).
- **`articles_fts`** (FTS5) — BM25 over `title + summary` for named entities/tickers (`MSTR`, `$11B`, `ETF`).
- **`events`** — one row per event cluster, keyed by `event_cluster_id`, carrying the cross-run state:
  `{first_seen, last_updated, sources(json), source_count, materiality, priced_in, surfaced_to_panel_on}`.

### Two-layer dedup
1. **Exact** — canonical URL (utm/tracking stripped) **OR** `sha256(normalized(title+summary))` already
   present → skip re-ingest.
2. **Near-dup (semantic fallback)** — token-shingle (word + bigram) **Jaccard** over normalized text;
   `>= 0.15` (env `CRYPTO_NEWS_JACCARD`) attaches the article to the existing event and bumps its
   `source_count`. **Jaccard, not SimHash Hamming, is the deciding metric** — on short news text
   (headline + summary) measured same-event Jaccard ≈ 0.27 vs different-event ≈ 0.03–0.05, clean
   separation; SimHash Hamming on the same text was 21 vs 30 (too close to threshold). A 64-bit SimHash
   is still computed and stored as a coarse signature. This is the documented **BM25 + lexical-semantic
   fallback** for the dense-vector design.

### OPTIONAL dense-vector upgrade (graceful, never crashes)
Set env `CRYPTO_NEWS_EMBED_CMD` to a shell command that reads text on stdin and prints a JSON float array
on stdout. If set **and** it works, near-dup uses cosine `>= CRYPTO_NEWS_EMBED_COS` (default 0.85) and the
vector is stored on the event. If the env is absent **or** the command errors/times out, it silently falls
back to Jaccard. (True `sqlite-vec` ANN storage is the documented next hook; this keeps it stdlib-only.)

### Hybrid retrieval (query)
BM25 (FTS5) **fused with** near-dup-cluster Jaccard rank via **RRF** (reciprocal-rank fusion, k=60).
Returns **events, not raw rows**.

## Commands

```bash
S="python3 .agents/skills/crypto-news-store/news_store.py"   # add --db <path> for a throwaway store

$S --db crypto/news/news.db ingest --json records.json   # idempotent → {new, duplicate, events_touched}
$S query --q "strategy bitcoin" --days 2 --k 10           # HYBRID BM25+near-dup, fused via RRF → events
$S new-since --days 2                                     # events first_seen/last_updated in window AND
                                                          #   NOT yet surfaced_to_panel_on (panel feed)
$S mark-surfaced --ids 1 4 --on 2026-06-15                # stamp surfaced; excludes from future new-since
```
`records.json` is a JSON list of normalized feed records `{source, url, title, summary, published_at,
lang, tags}` (optional `materiality`, `priced_in`). `ingest` accepts a bare list or `{"records": [...]}`.

## Worked example (this is the self-test — run it to verify)

```bash
P=.agents/skills/crypto-news-store/news_store.py ; DB=/tmp/news_test.db ; rm -f $DB
# records.json holds 6 articles: decrypt + coindesk both cover "Strategy raises reserves to $11B,
# buys more BTC" (SAME event); plus 4 unrelated (SEC ETH ETF, HYPE ETF volume, Iran ceasefire, quiet day).
python3 $P --db $DB ingest --json records.json      # → {"new": 6, "duplicate": 0, "events_touched": 1}
python3 $P --db $DB ingest --json records.json      # → {"new": 0, "duplicate": 6, ...}  (idempotent)
python3 $P --db $DB query --q "strategy bitcoin" --k 2
```
Observed output of the query (the two outlets collapsed into ONE event with `source_count: 2`):
```json
[
  {
    "event_cluster_id": 1,
    "title": "Strategy raises reserves to $11B, buys more Bitcoin",
    "sources": ["decrypt", "coindesk"],
    "source_count": 2,
    "surfaced_to_panel_on": null,
    "score": 0.03279
  },
  { "event_cluster_id": 4, "title": "Bitcoin surges as Iran ceasefire collides with Fed week",
    "sources": ["bitcoinmagazine"], "source_count": 1, "score": 0.01613 }
]
```
Asserted (all PASS):
- Strategy coverage collapses to **1 event, `source_count=2`, sources `[decrypt, coindesk]`** (PRD AC9).
- 6 articles, 2 collapsed → **5 distinct events**.
- `query --q "strategy bitcoin"` returns the Strategy event ranked #1.
- second `ingest` of the same json → **`new=0`** (idempotent).
- `mark-surfaced --ids 1` → next `new-since` returns **4** events (surfaced one excluded — the no-re-alert rule).

## Fit

`feed-*` (normalize) → **`news_store.py ingest`** → **`news_store.py new-since`** → [[narrative-news]] emits
the NEW/updated events to the panel. The store owns dedup + recency + cross-run state; `feed-*` owns fetch;
`narrative-news` owns the priced-in judgment.

> Educational, not advice. Events are context + disconfirmation, never a trigger.
