# Crypto Research & Decision — TDD (1-min read)

> How it's built. Implements [crypto.prd.md](crypto.prd.md). Skills live in `.agents/skills/` (discoverable by
> Claude Code via the `.claude/skills` symlink — see [[claude-code-skill-discovery]]).

## Architecture: a dynamic workflow (`crypto-panel-review`)

```
Phase 1 GATHER (parallel, data-only)   → Phase 2 CONSOLIDATE (1 agent → sourced brief)
   ↓                                       ↓
Phase 3 PANEL (lenses debate brief)    → Phase 4 DECIDE (chair) → Phase 5 WRITE → Phase 6 LEDGER
```
**Parameterized, not frozen:** the workflow takes `date`/`anchor` via args (no hard-coded `2026-06-15`); `run_id` + `git_sha` stamped per run (NFR7).

### Phase 1 — Gather seats (one agent each, structured-output schema, no opinions)
| Seat | Skill / source |
|---|---|
| odds | [[prediction-market-odds]] → Polymarket Gamma, Kalshi |
| price + on-chain | yfinance + checkonchain/lookintobitcoin/newhedge |
| derivatives | [[analyst-derivatives-positioning]] → Deribit, Coinglass |
| macro | [[fomc-monitor]] → federalreserve.gov, BLS |
| liquidity | Howell, Fed B/S, DXY, M2 |
| **etf-flows** | **TODO: build.** Farside / SoSoValue spot BTC/ETH ETF **net daily flow + trend** — hard data, not opinion. Feeds NFR4 hard-event tier. |
| sentiment/regime | [[regime-detection]] → alternative.me F&G |
| **narrative-news** | **TODO: build.** Consumes `feed-*` → news store (below) → emits deduped **EVENTS** + priced-in tags. Designed below. |
| **feed-\*** (input layer) | **TODO: build (none exist yet).** Per-source adapters feeding `narrative-news` — see "News feed skills" below. |

### `narrative-news` + `etf-flows` seat design
**`narrative-news`** (one Gather agent):
1. Calls the `feed-*` adapters (raw normalized articles).
2. Runs them through the **news store** (dedup + state, see "Hybrid news store" below).
3. Returns **only NEW or materially-updated EVENTS** (not articles), each:
   ```
   {event, sources[]+source_count, first_seen, materiality, priced_in}
   ```
   - **`source_count`** = crowdedness (NFR2).
   - **Priced-in heuristic** (concrete): compare the catalyst's timing to signals already in the brief — if the **price already moved** in the catalyst's direction **OR** the relevant **odds already shifted** (from the odds seat) → tag `PRICED_IN`; if the event is **fresh and unreacted** (within NFR3 window, no matching price/odds move) → tag `ACTIONABLE_CONTEXT`. (Guardrail per PRD FR1.8: context/disconfirmation, never a trigger.)
   - **Velocity:** reuse `mention_velocity.py` **for velocity only**. Note: it is a **stock tool** (`.agents/skills/trend-stock-research/`) — it needs a **crypto-universe adaptation** (BTC/ETH/MSTR/ETF tickers, crypto outlets); it does **not** work on the crypto universe as-is. *(TODO: adapt.)*

**`etf-flows`** (one Gather agent): pull Farside / SoSoValue spot BTC/ETH ETF net daily flow + multi-day trend; structured hard-data record, no narrative. *(TODO: build.)*

### Hybrid news store (the ingestion/store layer `feed-*` points at)
**Goal:** the panel receives **EVENTS, not articles**; never re-read/re-surface the same news; **keep state across runs** (mirrors the dedup-ledger pattern in [[13f-watch]] / [[congressman-stock-watch]] / [[crypto-dip-scanner]] — "never re-propose / no re-alert same week").
- **Two-layer dedup:**
  1. **Exact** — canonical URL + SHA hash of normalized `title+body`.
  2. **Semantic** — embed the article, cluster by **cosine ≥ ~0.85** within a time window → collapse multi-outlet coverage into one event + `source_count` (NFR2).
- **State store** keyed by `event_cluster_id`:
  ```
  {first_seen, last_updated, sources[], materiality, priced_in, surfaced_to_panel_on}
  ```
  Each run: **ingest → dedup vs store → only NEW or materially-updated clusters reach the panel** (older/unchanged clusters suppressed — the "no re-alert" rule).
- **Hybrid retrieval:** **BM25** for named entities/tickers (`MSTR`, `$11B`, `ETF`) + **dense vectors** for semantic dup/relevance, fused via **RRF** (reciprocal-rank fusion).
- **Tech (file-based, no server; pod is sometimes no-python):** **SQLite + FTS5** (BM25 built-in) **+ `sqlite-vec`** (vectors) — a single file beside the existing `.jsonl` ledgers. Embeddings from a **small local model or an API**; **BM25-only fallback** when embeddings are unavailable (skip the vector layer, retrieve on FTS5 alone). **LanceDB** is the embedded fallback if `sqlite-vec` is unworkable. *(TODO: build.)*

### News feed skills (`feed-*`) — pure source adapters *(all TODO: build — none exist yet)*
**They fetch + normalize only.** They do NOT dedup, store, embed, or judge relevance — that is the downstream
ingestion/store layer (owned by `narrative-news` + a separate design task).
The dedup/store/embed boundary lives in **"Hybrid news store"** (above), not here.

**Common output contract** — every `feed-*` emits the same record (or `[UNAVAILABLE]`):
```
{source, url(canonical), title, published_at, summary/body, lang, tags}
```
**Access strategy per tier:**
| Tier | Skills | Access | Failure mode |
|---|---|---|---|
| crypto-native | [[feed-coindesk]], [[feed-cointelegraph]], [[feed-decrypt]], [[feed-theblock]], [[feed-bitcoinmagazine]] | RSS-first (API/scrape fallback) | `[UNAVAILABLE]` |
| macro | [[feed-ft]], [[feed-wsj]], [[feed-bloomberg]], [[feed-reuters]] | RSS / headlines only (paywall) | headline-only or `[UNAVAILABLE]`; never fabricate body |

**Politeness (every skill):** conditional GET / ETag (skip unchanged), rate-limit aware, exponential backoff on 429.
**Extensible:** adding an outlet = one new `feed-<name>` skill, same contract — no pipeline change (PRD AC7).

### Phase 3 — Panel (each lens reads the SAME brief; structured verdict)
Voting: analyst-crypto, derivatives, druckenmiller, alden, **lacy-hunt (dissent)**, napier.
Non-voting guardrail: morgan-housel (process + survivable sizing; can veto sizing, not the asset call).

### Phase 4 — Decide
Chair: agreement / disagreement (preserved) / tally / decision / tranche plan / key risks / invalidation.
Constraint baked in: ~$0.5M risk capital only; survivable to −50%; no leverage.

### Phase 5 — Write
Writer agent writes `research/research.crypto.{date}.md` (scripts have no fs access → an agent uses Write). Stamps `run_id` + `git_sha` + per-figure timestamps (NFR7).

### Phase 6 — Ledger
A ledger agent runs `ledger.py add` for the chair's dated call: `{asset, question, prob, horizon, lens=voting seats, source, flip/invalidation}`. **Note:** `ledger.py` currently has **no `--flip` field** — the code agent adds it. *(TODO: code agent.)*

### NFR mechanisms (how each NFR is enforced)
| NFR | Mechanism |
|---|---|
| NFR1 rate-limit | Shared fetch helper: bounded concurrency (semaphore) + exponential backoff on 429 + conditional-GET/ETag; reuses the `feed-*` politeness path. |
| NFR2 dedup | News store collapses cosine-clustered articles into one event carrying `source_count` (see Hybrid news store). |
| NFR3 recency | Consolidate filters catalysts to the rolling 36h (24–48h) window AND materiality bar; older → context only. |
| NFR4 reliability | Each record tagged with its tier; consolidate resolves conflicts by tier, tags loser `disputed` (no averaging). |
| NFR5 budget | Orchestrator counts agent calls (~15 cap); on overflow sheds lowest-tier `feed-*`, emits `[DEGRADED]`; required FR1 seats never shed. |
| NFR6 completeness | Consolidate asserts every FR1.1–FR1.8 seat present; a null seat → `[UNAVAILABLE: <seat>]` + run flagged `incomplete` (no `.filter(Boolean)` silent-drop). |
| NFR7 reproducibility | `run_id` + `git_sha` captured at run start, stamped into brief/report and every figure timestamp. |

## Automation (mechanisms)
| Job | Cadence | Mechanism | Guardrail |
|---|---|---|---|
| Dip tripwire + on-chain + **ETF flows** | daily 07:50 UTC | `crypto_dip_scanner.py` cron | silent unless trigger |
| Full panel memo | weekly | `/schedule` cron runs the workflow (de-hardcode date/anchor) | recommend-only DM |
| Forecast resolve/score | daily | `ledger.py resolve`/`score` cron | human-confirm fuzzy resolutions |
| Liveness | daily | [[liveness-monitor]] — register the new crons | DM only on stale job |

## Build backlog (ranked)
1. **`feed-*` family → `narrative-news` + `etf-flows` Gather seats** — the `feed-*` adapters are the input layer; `narrative-news` consumes them. Closes the completeness gap that missed the Strategy buy (PRD AC1, AC5–AC7). *(All feed-\* + narrative-news still TODO: build.)*
2. **Hybrid news store** (SQLite + FTS5 + `sqlite-vec`, BM25-only fallback) — the dedup/state layer `narrative-news` reads (NFR2/AC9). *(TODO: build.)*
3. **Wire forecast-ledger** to the chair call (+ add `--flip` to `ledger.py`) — the discipline edge.
4. **Parameterize + schedule** the workflow weekly (date/anchor via args, not frozen); read a shared daily data cache instead of re-pulling.
5. **Shared daily brief cache** (`pools/crypto_brief.{date}.json`) so scanner + workflow agree on the numbers.

## Test
Replay a day with a known catalyst (Strategy $11B raise / BTC buy); assert the brief's news section names it
and tags priced-in (PRD AC1). Assert no digest-sourced odds (AC2) and a ledger entry exists (AC4).
**NFR replays:** same event from 3 outlets → 1 catalyst `source_count=3` (AC9); a 50h-old item excluded, a 12h item included (AC10); a forced null required seat → `[UNAVAILABLE]` + run `incomplete` (AC13); every brief carries `run_id`/`git_sha`/timestamps (AC14).
