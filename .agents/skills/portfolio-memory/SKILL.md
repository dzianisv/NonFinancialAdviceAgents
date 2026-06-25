---
name: portfolio-memory
description: "Cross-run BM25 memory store for stocks-advisor and crypto-advisor. Stores per-ticker verdicts and durable user preferences in SQLite FTS5. On each run: (1) inject_context.py recalls relevant prior verdicts ranked by BM25 × exponential recency decay (half-life 45 days); (2) after analysis, memory.py remember appends the new verdict. Prevents agents forgetting prior calls (COIN=HOLD, PYPL=EXIT, crypto-bullish pref). SQLite FTS5 stdlib only — no embeddings, no numpy, no external APIs. Triggers: used internally by stocks/crypto-advisor Step -1 (load) and Step 1g (write)."
license: MIT
compatibility: opencode
metadata:
  domain: agent-memory
  role: cross-run-state
  source: "Architecture mirrors crypto-news-store/news_store.py; BM25×decay pattern from agent-memory research 2026-06-24"
---

# Portfolio Memory — BM25 × Recency Decay

Cross-run memory store for the portfolio manager agents. Stores every ticker verdict after each run and recalls them on the next run — so the agent never re-derives what COIN is a hold, what PYPL is a value trap, or what the user's preferences are.

**SQLite FTS5, stdlib only. No embeddings. No numpy. No external APIs.**

## How it works

```
WRITE (after each ticker verdict):
  python3 memory.py remember --desk stocks --ticker COIN --verdict HOLD --body "..."
  ↓ INSERT into memory table → AFTER INSERT trigger auto-populates FTS5 index

READ (before each run):
  python3 scripts/inject_context.py --desk stocks --tickers COIN PYPL AVGO
  ↓ SELECT ranked by: -bm25(fts, 10.0, 1.0) × decay(created_at)
                       ↑ relevance (ticker 10× body)  ↑ recency (half-life 45d)
  ↓ Print <prior_context> block → inject into every seat's data package
```

## The two tables

### `memory` — per-ticker-per-run verdicts (BM25-indexed)
| Field | Description |
|-------|-------------|
| `ticker` | e.g. `COIN` (weighted 10× in FTS5) |
| `verdict` | `HOLD\|BUY\|WATCH\|SKIP\|EXIT\|TRIM\|SELL` |
| `body` | Full text the BM25 engine ranks (ticker + reasoning + theme) |
| `meta` | JSON: entry, stop, conviction, theme, seats |
| `run_id` | `YYYY-MM-DD` of the run that produced it |
| `desk` | `stocks` or `crypto` |

### `preferences` — durable user preferences (always injected, never BM25-gated)
Examples: `"crypto bullish — do not sell COIN"`, `"RSP over VOO"`.
These are too important to miss — they are injected into EVERY run regardless of query.

## BM25 × recency decay formula

```python
final_score = -bm25(memory_fts, 10.0, 1.0) * 0.5 ** (age_days / 45.0)
```

- `bm25()` in SQLite FTS5 returns **negative** numbers (more negative = more relevant) → flip with `-bm25`
- Ticker column weighted `10.0×` body column → a COIN query surfaces COIN rows first
- `0.5 ** (age_days / 45)` = exponential half-life: a verdict loses half its recency weight every 45 days
- Combined: recent relevant memories rank highest; stale memories rank lower even if exact-match

## CLI

```bash
M="python3 .agents/skills/portfolio-memory/memory.py --db .db/portfolio_memory.db"

# Recall prior verdicts for a ticker or theme
$M recall --q "COIN" --desk stocks --k 5

# Write a new verdict after analysis
$M remember --desk stocks --ticker COIN --verdict HOLD \
  --body "COIN HOLD — crypto bullish, rev -30.8%, below 200d -36%, fwd PE 30. Conviction 3/5. Theme CRYPTO_INFRA." \
  --meta '{"conviction": 3, "theme": "CRYPTO_INFRA"}' \
  --run-id 2026-06-24

# Add a durable user preference
$M pref-add --text "crypto bullish — do not sell COIN, HOOD, CRCL" --desk stocks --scope "COIN,HOOD,CRCL"
$M pref-add --text "RSP over VOO for new US equity" --desk stocks

# List all preferences
$M pref-list --desk stocks

# Database stats
$M stats
```

## Integration with portfolio-manager skills

### Step -1 — Load prior memory (add before Step 0 in both PM skills)

```bash
# At the start of every run, before seeding the todo list:
python3 .agents/skills/portfolio-memory/scripts/inject_context.py \
  --db .db/portfolio_memory.db \
  --desk stocks \
  --tickers AVGO MRVL COIN PYPL ACN NEM URNM
```

Inject the printed `<prior_context>` block into EVERY seat's data package. This is how the agent knows: COIN=HOLD (crypto bullish), PYPL=EXIT (value trap), prior entry zones, prior theme classifications.

### Step 1g — Write verdict to memory (add after Step 1e in both PM skills)

After each ticker completes its 4-seat panel, write the verdict:

```bash
python3 .agents/skills/portfolio-memory/memory.py remember \
  --desk stocks \
  --ticker {TICKER} \
  --verdict {BUY|WATCH|SKIP|HOLD|EXIT|TRIM} \
  --body "{TICKER} {VERDICT} — fundamental {rating}: {key_metric}; technical {state}: {setup}; narrative {phase}: {why}; sentiment {read}: {key}. Entry {zone}, trigger {trigger}, stop {stop}, conviction {conv}/5. Theme {theme}." \
  --meta '{"entry_low": X, "entry_high": Y, "stop": Z, "conviction": N, "theme": "..."}' \
  --run-id {YYYY-MM-DD}
```

**body format contract** (what makes BM25 work well):
- Lead with the ticker symbol (gets 10× FTS5 weight)
- Include the verdict, theme, and key reasoning terms
- Keep under 300 chars so it injects cleanly into prompts
- Include conviction and theme — these are the most useful terms for cross-run recall

## Database location

Default: `.db/portfolio_memory.db` (gitignored — user data, never commit).

## Done when

- `recall --q "COIN"` returns prior COIN verdicts, most recent first
- `recall --q "AI supply chain"` returns AVGO/MRVL/NVDA verdicts ranked by relevance × recency
- `pref-list` always returns all preferences regardless of query
- `inject_context.py` prints a clean `<prior_context>` block for any ticker list
- Verdicts written today outrank identical verdicts from 3 months ago (recency decay working)
