# Stateful Daily Research Agent — Architecture Design

> **Scheduling**: NOT built into the skill. Run externally via `claude /loop schedule` or
> openclaw cron task. The skill reads/writes the DB — the scheduler calls it.

## Problem

A single-shot skill (no matter how good) cannot replicate the "read daily for weeks, accumulate
patterns, then act" workflow that found TSMC/NVDA/SanDisk. The edge isn't one article — it's
multiple independent sources confirming the same thesis over 2-4 weeks.

## Design (from HN/Reddit research + user input)

### The Core Insight

From HN community (goosmurf, 2010): "I find most of my investments through general news as an
indicator of future growth prospects, and through industry stalking... who's hot, who's not."

From strike.market founder (jakubroz, 2022): "I used data like website traffic, mobile app ranks,
Google Trends, share of search... manually. But it is very time consuming to check these data every
month for every company."

From TradingAgents (TauricResearch): "The decision log is always on. Each completed run appends
its decision to memory. On the next run for the same ticker, it fetches the realized return,
generates a reflection, and injects recent same-ticker decisions plus cross-ticker lessons."

**Translation**: the system needs MEMORY that accumulates across runs and a WEEKLY synthesis
that queries accumulated evidence.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DAILY READER (cron, 6am ET)                    │
│                                                                   │
│  1. Run emerging_scan.py → sectors/themes                        │
│  2. Browser → read FT/WSJ/SA headlines (via chrome-use / CDP)    │
│  3. For each interesting headline:                                │
│     - Read article (bypass paywall via extension)                 │
│     - Extract: {company, theme, demand_signal, source, date}      │
│  4. Check SEC EDGAR for recent 8-K/Form-4 on tracked companies   │
│  5. Upsert extracts into vector DB                               │
│                                                                   │
│  Output: append-only daily log + vector embeddings                │
└─────────────────────────────────────────────────┬───────────────┘
                                                  │
                                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    VECTOR DB (ChromaDB / local)                   │
│                                                                   │
│  Collections:                                                     │
│  - articles: {text, source, date, theme, companies[], sentiment} │
│  - signals: {type: demand_inflection|insider_buy|capacity_ramp,  │
│              company, date, source, confidence}                    │
│  - thesis_log: {ticker, thesis_text, created_date, evidence[],    │
│                 status: building|active|killed|realized}           │
│                                                                   │
│  Persistence: ~/.local/share/trend-research/chroma/              │
└─────────────────────────────────────────────────┬───────────────┘
                                                  │
                                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                  WEEKLY SYNTHESIZER (cron, Saturday)              │
│                                                                   │
│  1. Query vector DB: "themes mentioned by 3+ sources in 3+ wks" │
│  2. For each building-theme:                                     │
│     - Count independent sources (SA, WSJ, FT, EDGAR = diff)     │
│     - Check if evidence is ACCELERATING (more mentions/week)     │
│     - Check if still non-obvious (not in ETF flows / Reddit)    │
│  3. Apply skeptic filter (same as skill Step 4)                  │
│  4. Produce WATCHLIST with confidence:                            │
│     - 1 week of mentions: "monitoring"                           │
│     - 2 weeks, 3+ sources: "building"                            │
│     - 3+ weeks, 5+ sources, catalyst identified: "ACTIONABLE"   │
│  5. Route ACTIONABLE to multi-lens-quorum                        │
│  6. Append to thesis_log with evidence trail                     │
│                                                                   │
│  Output: weekly-picks.md + quorum routing                        │
└─────────────────────────────────────────────────────────────────┘
```

### Signal Accumulation Model

The key innovation vs a one-shot skill: **CONVERGENCE scoring**.

```
Signal strength = (# independent sources) × (time_span_weeks) × (evidence_quality_weight)

where evidence_quality_weight:
  - SEC filing / earnings call:  1.0
  - WSJ/FT reporting:            0.8
  - Google News discovery (Bloomberg/Reuters/BI/CNBC/IBD, lead only): 0.5
  - Blog/social:                 0.2
  - Insider Form 4 cluster:     1.2 (multiplier, not additive)

Threshold for ACTIONABLE: signal_strength ≥ 5.0
```

Example: "Power transformer shortage" mentioned by:
- WSJ article week 1 (0.8)
- FT article week 2 (0.8)
- GE Vernova earnings call week 3 (1.0)
- CLF insider buy Form 4 week 4 (×1.2 multiplier)
→ Total: (0.8 + 0.8 + 1.0) × 1.2 × (4 weeks span factor) = 2.6 × 1.2 = strong signal

### Components to Build

1. **Daily reader script** (`scripts/daily_reader.py`)
   - Uses the shared `read-news` adapters (`feeds/ft.ts`, `feeds/wsj.ts`, `read_news.ts --source googlenews`)
     to fetch FT/WSJ/Bloomberg/Reuters/BI/CNBC/IBD — never a raw `chrome-use`/`web_fetch` scrape of a
     publisher page, and never Seeking Alpha (not automatable, permanently excluded — no adapter exists
     or will be added)
   - Reads top headlines, decides which to read in full
   - Extracts structured data from each article
   - Stores in ChromaDB

2. **Vector DB setup** (`scripts/setup_db.py`)
   - ChromaDB local persistence
   - Collection schemas for articles, signals, thesis_log
   - Embedding model: sentence-transformers (local, fast)

3. **Weekly synthesizer script** (`scripts/weekly_synthesizer.py`)
   - Queries ChromaDB for convergence patterns
   - Applies skeptic filter
   - Produces weekly-picks.md
   - Updates thesis_log

4. **Thesis tracker** (`scripts/thesis_tracker.py`)
   - Tracks price movement of active theses
   - When thesis moves ±20%, triggers reflection
   - Builds accuracy track record over time

5. **Cron / scheduler integration**
   - Daily: `0 6 * * * daily_reader.py`
   - Weekly: `0 8 * * 6 weekly_synthesizer.py`

### Data Sources (from HN research — what actually works)

| Source | Signal Type | Access Method |
|--------|------------|---------------|
| FT | Global view, non-US companies | `read-news` `feeds/ft.ts` (no chrome-use scrape needed for headlines/teasers) |
| WSJ | Sector shifts, M&A, policy | `read-news` `feeds/wsj.ts` (no chrome-use scrape needed for headlines/teasers) |
| Bloomberg/Reuters/BI/CNBC/IBD | Broad discovery leads (never a body quote) | `read-news` `read_news.ts --source googlenews` |
| Seeking Alpha | Thesis deep-dives | **Excluded — not automatable, no adapter exists or will be added** |
| SEC EDGAR | Filings, Form 4, 13F | web_fetch (free) |
| SEC EDGAR full-text | Supply constraint language | web_fetch (free API) |
| Strike.market signals | Alt data (web traffic, app ranks) | web_fetch (free tier) |
| Google Trends | Consumer interest proxy | web_fetch |
| Industry RSS feeds | Real-time sector news | web_fetch |

### Key Principles (from research)

1. **Speed hierarchy** (Galanwe on HN): SEC posts → analysts trade → earnings call → transcripts
   → NLP hedge funds → Bloomberg article → retail FOMO. Be at Day 0-1, not Day 2+.

2. **Cross-validation** (kavout): CEO buys + 3 executives buy + analysts upgrade + Congress trades
   = highest confidence. Single signal = noise.

3. **Theme tracking > ticker tracking**: Watch "AI power infrastructure" as a theme. Companies
   within the theme come and go — the structural demand is what persists.

4. **Inverse signal**: When Reddit/fintwit is saturated with a theme, it's PRICED. Track social
   saturation as a NEGATIVE signal (contrarian indicator).

### Dependencies

- `chromadb` — vector DB (pip install)
- `sentence-transformers` — embeddings (pip install, ~400MB model)
- `chrome-use` CLI — browser access (already installed)
- `yfinance` — price checks for skeptic filter
- `schedule` or cron — daily/weekly runs

### What This Replaces

The one-shot `trend-stock-research` skill remains useful for AD-HOC queries ("find me something
in robotics right now"). The daily agent is the ACCUMULATOR that builds conviction over time.

They work together:
- Daily agent accumulates → produces weekly ACTIONABLE picks
- One-shot skill handles on-demand requests → can query the vector DB for prior evidence
- Both route to multi-lens-quorum for the decision

### Risk / Honest Assessment

- **Cold start**: first 2-4 weeks produce nothing — need evidence to accumulate
- **False positives**: theme that looks convergent but is just media echo chamber
- **Maintenance**: browser tools break, paywalls evolve, sources change
- **Track record**: need 6+ months to know if this actually produces alpha

This is an EXPERIMENT, not a proven system. The hypothesis: daily reading with memory > weekly
one-shot without memory. The proof requires time.
