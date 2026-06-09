---
name: portfolio-monitor
description: Living DISCIPLINE monitor over an already-reviewed equity book (CSV with theses + written triggers). Pulls live prices via yfinance, computes extension vs 200d MA (euphoria gauge) and % from 52-week high, detects which written triggers in Price_Flag/Next_Step have FIRED or are NEAR (best-effort regex, requires literal $; handles macro proxies BTC/Brent/oil/TON), flags EUPHORIA (>30% above 200dMA + HIGH AI_Bubble_Fragility), UNACTIONED SELL, and CONCENTRATION (>10% of book). Emits stocks/monitor-report-<date>.md: what needs action now, sorted by $. Materially-changed positions are then handed to multi-lens-quorum (separate agent step) for the buy/sell/hold call. Run: python3 scripts/portfolio_monitor.py --csv <file> --out <dir>. Triggers: monitor my portfolio, what changed in my book, did any triggers fire, check my holdings for euphoria or concentration, portfolio discipline check. Discipline not alpha; notification-only; never trades.
license: MIT
compatibility: opencode
metadata:
  author: engineer
  role: discipline-monitor
  scope: equity-book-only
---

# Portfolio Monitor — living discipline check over the reviewed book

You enforce **written discipline** on a book that has already been reviewed and annotated. You do NOT
screen for new ideas, predict returns, or place trades. Your job is: run the script, parse the delta
report, and surface what needs a human decision today.

## Honesty rails (non-negotiable)

- **Discipline, not alpha.** This skill surfaces risk and fired triggers; it does not predict returns.
  The project proved no scalable mechanical alpha — the validated edge is judgment + discipline at scale.
- **Trigger parse is best-effort.** The regex requires a literal `$` before price levels to avoid
  false-fires on percentages, years, and share counts. The report quotes the matched text verbatim —
  always verify the quoted text before acting on a FIRED/NEAR status.
- **PRIVACY.** The real holdings CSV (`stocks/portfolio-review.csv`) and all generated reports
  (`stocks/monitor-report-*.md`) are gitignored. Never commit real positions to the repo.
- **Notification-only; never trades.** This skill produces a report. Route all decisions to
  `multi-lens-quorum` for the buy/sell/hold call.
- Educational, not financial advice.

## Inputs

| Column | Purpose |
|---|---|
| `Ticker` | equity symbol (first token used) |
| `Shares` + `Sheet_Value_USD` | position sizing / concentration check |
| `Action` | SELL triggers UNACTIONED SELL flag if shares > 0 |
| `Conviction` | reported in delta summary |
| `AI_Bubble_Fragility` | HIGH + >30% ext → EUPHORIA flag |
| `Price_Flag` / `Next_Step` | free-text trigger sources (regex parsed) |
| `Thesis`, `Key_Risk`, `Reasoning` | passed through for context |

Macro proxies handled: `BTC`/`BITCOIN` → BTC-USD, `BRENT` → BZ=F, `OIL` → CL=F, `TON` → TON-USD.

## Flags emitted

- **EUPHORIA** — price >30% above 200d MA AND `AI_Bubble_Fragility` = HIGH.
- **UNACTIONED SELL** — `Action` contains SELL but `Shares` > 0.
- **CONCENTRATION** — position > 10% of total book value.
- **TRIGGER FIRED / NEAR** — a written price level from `Price_Flag` or `Next_Step` has been crossed
  or is within 5% of current price.

## Run

```bash
# default: reads stocks/portfolio-review.csv, writes to stocks/
/Users/engineer/.venv/bin/python3 scripts/portfolio_monitor.py

# explicit paths
/Users/engineer/.venv/bin/python3 scripts/portfolio_monitor.py \
  --csv stocks/portfolio-review.csv \
  --out stocks/
```

Requires `yfinance` (available in `/Users/engineer/.venv`). Fetches 1 year of daily closes in one
batch call; dead or merged tickers show `no-data` and are skipped gracefully.

## Output: `stocks/monitor-report-<date>.md`

```
# portfolio-monitor — 2026-06-08

## ⚑ WHAT NEEDS ACTION NOW (2 positions)

- **BBB** ($8,000, MEDIUM): EUPHORIA: +38%>200dMA & HIGH bubble-fragility · TRIGGER NEAR: 'above $200' (BBB=194.50)
- **CCC** ($3,000, LOW): UNACTIONED SELL: flagged SELL, still held

## Full live status

TICKER     PRICE        EXT      FROM HIGH  ACTION
AAA       $450.00     +12%>MA     -5% from hi  HOLD
BBB       $194.50     +38%>MA    -12% from hi  HOLD   ⚑ EUPHORIA | TRIGGER NEAR
CCC        $15.00      +3%>MA    -45% from hi  SELL (tax-loss)   ⚑ UNACTIONED SELL
```

EXT = % above 200d MA (euphoria gauge). The report quotes trigger text verbatim — verify before acting.

## What you do as the agent

1. Confirm the CSV path with the user (default `stocks/portfolio-review.csv`).
2. Run the script using the repo venv. Show stdout (path written, action-now list).
3. Read the generated report and summarize the delta: fired triggers, euphoria flags, unactioned sells,
   concentration breaches — in descending $ order.
4. For each flagged position, quote the exact trigger text from the report.
5. Recommend routing flagged positions to `multi-lens-quorum` for the buy/sell/hold call. Do NOT make
   that call yourself.
6. Do not commit the CSV or report to git.

## Example

**User:** did any triggers fire in my book?

**You:**
1. Run `portfolio_monitor.py --csv stocks/portfolio-review.csv --out stocks/`.
2. Read `stocks/monitor-report-2026-06-08.md`.
3. Report: "2 positions need attention — BBB ($8k): EUPHORIA (+38% above 200dMA, HIGH fragility) and
   trigger NEAR 'above $200' (current $194.50); CCC ($3k): UNACTIONED SELL still held. Trigger text
   quoted verbatim — please verify before acting. Recommend passing BBB and CCC to multi-lens-quorum."

## Done when

- [ ] Script ran without errors (or errors explained).
- [ ] Delta section read and summarized in $ descending order.
- [ ] Every FIRED/NEAR trigger quoted verbatim from the report.
- [ ] Flagged positions named for multi-lens-quorum handoff.
- [ ] No real CSV or report committed to git.
