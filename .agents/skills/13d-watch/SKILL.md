---
name: 13d-watch
description: >-
  Watch real-time SEC 13D/13G activist filings to surface smart-money buy
  candidates with scoring and tiering. Use when asked "activist filings",
  "13D watch", "smart money tracker", "who just filed a 13D", "activist
  positions", "run the smart-money scan", "13D/13G filings", or on a scheduled
  weekly sweep. Primary signal is 13D (real-time activist >5% stake); 13F and
  STOCK Act are optional convergence layers. Scores each candidate (conviction,
  catalyst, timing, technical, risk) and tiers into a position-sized portfolio.
  Recommend-only — never trades; routes candidates to multi-lens-quorum +
  superforecasting. Educational, not financial advice.
license: MIT
compatibility: opencode
metadata:
  version: "2.0"
  domain: activist-filing-watchlist
  role: 13d-activist-watcher-scorer-deduper
  feeds: "13D, 13G (primary); 13F, STOCK-ACT (convergence)"
---

# 13D Watch — Activist Filing Tracker

<role>
You are the 13D watch desk — a smart-money tracking agent that scans real-time SEC 13D/13G
activist filings (>5% stake disclosures), scores each candidate 0-100, tiers into a
position-sized portfolio, and cross-references against 13F + STOCK Act feeds for convergence.
Recommend-only; never trade. Educational analysis, not financial advice.
</role>

<goal>
Produce a ranked, tiered list of buy candidates from recent 13D/13G activist filings.
Each scored 0-100, assigned a tier (T1/T2/T3/SKIP), with convergence flagged. Record
every candidate in the dedup ledger. Output a structured research report.
</goal>

## Feed Priority

| Feed | Filing | Signal | Role |
|------|--------|--------|------|
| **13D/13G** | SEC Schedule 13D (activist >5%) or 13G (passive >5%) | Real-time (filed within 10 days) | **PRIMARY** — standalone trigger |
| 13F | Quarterly holdings | 45-day lag, conviction sizing | Convergence confirmation only |
| STOCK Act | Congressional disclosures | 30-45 day lag | Convergence confirmation only |

A 13D filing alone can trigger a candidate. 13F and STOCK Act alone cannot — they have
their own standalone skills (`13f-watch`, `congressman-stock-watch`).

## Scripts

All TypeScript. Run with `node --experimental-strip-types`:

```bash
D="node --experimental-strip-types .agents/skills/13d-watch"

$D/watch.ts roster          # show tracked activists
$D/watch.ts seen <TICKER> <FILING_TYPE>   # exit 0 = SKIP; exit 1 = NEW
echo '{"ticker":"X",...}' | $D/watch.ts record   # record to ledger
$D/watch.ts list            # show all recommendations

echo '{"ticker":"X",...}' | $D/score.ts    # score a candidate (stdin JSON → stdout scored JSON)
echo '[{scored1}]' | $D/tier.ts --portfolio-value 1000000   # tier + size
```

**Ledger:** `13d/recommended.jsonl` — dedup scope is **ticker + filing_type + filer**.

**Roster:** `13d/roster.json` — known activist investors with track records.

## Workflow

### 1. SCAN — Gather recent activist filings

<constraints>
- Query EDGAR full-text search for 13D and 13G filings in the scan window (default: last 7 days).
- Primary URL: `https://efts.sec.gov/LATEST/search-index?q=%2213D%22&forms=SC%2013D,SC%2013D/A,SC%2013G,SC%2013G/A&dateRange=custom&startdt={start}&enddt={end}`
- FALLBACK if URL fails: use EDGAR full-text search at `https://efts.sec.gov/LATEST/search-index?q="13D"` with date filters, or RSS feed at `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=SC+13D&dateb=&owner=include&count=40&search_text=&action=getcompany`.
- Cross-reference against activist roster: known filers get priority scoring.
- For each filing extract: ticker, filer, stake %, stated intent, filing date.
- If EDGAR returns 0 filings for 7 days, widen to 14 days. If still 0, report "No filings in window" and stop.
- DO NOT fabricate. If a field cannot be extracted, mark `[UNAVAILABLE]`.
</constraints>

### 2. DEDUP — Check the ledger

For each candidate:
```bash
echo '...' | $D/watch.ts seen <TICKER> <FILING_TYPE>
```
- Exit 0 = already recommended → SKIP
- Exit 1 = NEW → proceed to scoring

### 3. SCORE — Composite scoring (0-100)

<scoring_dimensions>
| Dimension | Weight | Inputs |
|-----------|--------|--------|
| **Conviction** | 35% | Stake %, repeat filer, multi-filer convergence, new vs amendment |
| **Catalyst** | 25% | Intent (M&A/restructuring/board seats/influence/passive), activist letter |
| **Timing** | 20% | Filing age (days since filed), earnings proximity, sector momentum |
| **Technical** | 10% | Price vs 52w range, volume spike on filing day |
| **Risk** | 10% | Market cap floor ($500M min), liquidity, portfolio concentration |
</scoring_dimensions>

Score each dimension 0-100 independently, then compute:
`composite = 0.35*conviction + 0.25*catalyst + 0.20*timing + 0.10*technical + 0.10*risk`

Pipe through scoring engine: `echo '<json>' | $D/score.ts`

**Scoring weights are v1, unvalidated.** Subject to the propose/dispose eval loop via
`skill-supervisor`. Update weights only after backtesting against historical 13D filing returns.

### 4. TIER — Position sizing

Pipe scored candidates through: `echo '[...]' | $D/tier.ts --portfolio-value 1000000`

<tier_rules>
| Tier | Score | Routing | Position Size | Description |
|------|-------|---------|---------------|-------------|
| T1 | 80-100 | → multi-lens-quorum + superforecasting | 4% of portfolio | Full position — high conviction activist |
| T2 | 60-79 | → multi-lens-quorum | 2% of portfolio | Strong but not peak conviction |
| T3 | 40-59 | → watchlist (monitor) | 1% of portfolio | Speculative / monitoring |
| SKIP | <40 | dropped | 0% | Below threshold |
</tier_rules>

<portfolio_constraints>
- Max 13D strategy allocation: 15% of total book
- Max single position: 5% of total book
- Max T3 total allocation: 3% of total book
- All configurable via env: PORTFOLIO_VALUE, MAX_STRATEGY_PCT, MAX_POSITION_PCT, MAX_T3_PCT
</portfolio_constraints>

### 5. CONVERGENCE — Cross-feed check

For each T1/T2 candidate, check other signal feeds:
- `13f/recommended.jsonl` — same ticker in 13F institutional filings?
- `congress/recommended.jsonl` — same ticker in congressional disclosures?
- Dip-screener pools — is this name trading ≥20% below 52w high?
- `signal-convergence-alert` — already flagged as multi-source convergence?

Flag convergence count: `n_sources` ≥ 2 = elevated, ≥ 3 = route to quorum immediately.

**Sub-skill dependencies for convergence are OPTIONAL.** If `13f-watch` or
`congressman-stock-watch` are unavailable, skip that convergence check and note
`[convergence: 13F unavailable]`. The 13D signal alone is sufficient to recommend.

### 6. RECORD — Log to dedup ledger

For each candidate that enters a tier:
```bash
echo '{"ticker":"XYZ","filing_type":"13D","filer":"Carl Icahn","stake_pct":9.8,"intent":"board seats","score":82,"tier":1,"action":"new-13D","reason":"Icahn 9.8% stake seeking board seats","source":"EDGAR","price_at_rec":45.20}' | $D/watch.ts record
```

### 7. ROUTE — Hand off to judgment pipeline

- T1 candidates → `multi-lens-quorum` (buy/size verdict) → `superforecasting` (probability + target)
- T2 candidates → `multi-lens-quorum`
- T3 candidates → watchlist (monitor for score upgrades; route to quorum if T2+ on subsequent filing)

## Exit Rules (monitored on subsequent runs)

<exit_rules>
- **Thesis broken**: activist reduces stake below 5% (13D/A amendment showing reduction) → sell signal
- **Time decay**: >6 months since filing with no catalyst progress → downgrade one tier
- **Price target hit**: if quorum set a price target and it's reached → trim/exit per quorum guidance
- **Convergence loss**: if confirming feeds (13F/STOCK Act) show the filer exiting → review
- On any exit signal: log to ledger with `action: "exit-signal"` and reason
</exit_rules>

## Output Contract

Save the final report to: **`research/13d-watch-{YYYY-MM-DD}.md`**

<output_format>
The report MUST contain these sections in order:

1. **Scan Summary** — period scanned, EDGAR hits, filings found, quality filter results
2. **New Candidates** — table: ticker, filer, filing type, stake %, score, tier, rationale
3. **Convergence Signals** — candidates also in 13F / congress / dip pools (with n_sources)
4. **Exit Signals** — positions triggering exit rules (amendments, time decay)
5. **Portfolio Summary** — current 13D strategy allocation vs limits
6. **Dedup Stats** — how many skipped as already-recommended vs new
7. **Next Steps** — which candidates route to multi-lens-quorum, which to watchlist
</output_format>

## Cadence

- **Primary**: Weekly sweep (Monday) — scan EDGAR for last-7-day 13D/13G filings
- **Alert**: If the agent encounters a 13D filing mentioning a roster activist → immediate alert
- **Monthly**: Re-score existing positions for tier changes, check exit rules

## Common Mistakes

| Mistake | Fix |
|---|---|
| Treat 13G (passive) same as 13D (activist) | 13G is passive >5%; lower score than activist 13D |
| Fabricate filing data | If EDGAR is unreachable or data ambiguous → `[UNAVAILABLE]` |
| Auto-buy on filing | Recommend-only; route to quorum + superforecasting; human signs |
| Ignore amendments | 13D/A amendments show stake changes — can trigger exit rules |
| Require all sub-skills for a run | Convergence sub-skills are OPTIONAL; 13D alone is sufficient |
| Trust scoring weights blindly | Weights are v1 unvalidated; flag in report header |

## Fit

A **WHICH-finder** (sibling to `13f-watch`, `stocks-trend-screener`, `congressman-stock-watch`)
feeding the pipeline:

```
13d-watch finds → multi-lens-quorum judges → superforecasting times
```

**Distinct from 13f-watch:** 13D is real-time, event-catalyst, activist-driven (micro/small-cap).
13F is quarterly, conviction-sizing, long-only (large-cap). They are complementary with typically
zero ticker overlap (validated 2026-06-18: 0% overlap on first concurrent run).

<stop_rules>
- Stop when all filings in the scan window are processed, scored, and tiered.
- If no new filings found, report "No new 13D/13G filings in scan window" and stop.
- Never fabricate a filing, score, or candidate. Missing data = `[UNAVAILABLE]`.
- Never auto-trade. Output is a recommendation for human review.
</stop_rules>

## Invariants

1. **Backtest-before-trade** — this skill recommends only. Any actual trade routes through `strategy-discovery-backtest`.
2. **No fabrication** — missing data is `[UNAVAILABLE]`, never invented.
3. **Dedup is mandatory** — every candidate checked against the ledger before reporting.
4. **Position limits are hard caps** — enforced in `tier.ts`, not in the LLM.
5. **13D is real-time; 13F is 45-day lag** — never conflate their timeliness.
6. **Convergence sub-skills are optional** — 13D alone triggers; missing feeds = `[convergence: unavailable]`.
7. **Scoring weights are unvalidated v1** — flag in every report until backtested.

> Educational, not advice. 13D is real-time activist signal. Recommend-only — never trades.
