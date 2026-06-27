# stocks-daily

**One-liner:** Weekly portfolio review. Reads cached positions, runs the stocks-advisor 5-seat panel, which publishes a dated report to Notion when configured. Despite the `daily` name, the cadence is WEEKLY (user chose the command name). Educational, not investment advice.

**Triggers:** `/stocks-daily`, "run weekly stocks report", "publish stocks weekly report"

---

> **Disclaimer:** Output is educational analysis for a backtesting research environment. Nothing here is financial advice. All verdicts must be validated against your own risk tolerance and a licensed advisor before acting.

---

## CONFIG

```
POSITIONS_CSV = /Users/engineer/workspace/backtest/.cache/stocks-daily/positions.csv
```

- `POSITIONS_CSV` — the user maintains this file; the skill NEVER invents or edits it.

---

## Step 1 — Load positions

1. Read `POSITIONS_CSV`. Schema: `Position,Quantity,Type,Unrealized_PnL`.
2. If the file is missing or empty, stop immediately. Tell the user:
   > "Create `{POSITIONS_CSV}` with columns: Position,Quantity,Type,Unrealized_PnL. One row per holding."
3. Parse into a holdings list: ticker, qty, type, pnl.
4. Tag crypto-adjacent names as HOLD-ONLY. The user is crypto-bullish; never recommend selling these:
   `COIN, TONX, CRCL, HOOD, SOFI, IBKR, BTC` (and any ticker the user has flagged crypto-related in the CSV `Type` column as `crypto-beta`).
   Pass these through to analysis but mark them exempt from EXIT/TRIM recommendations.

---

## Step 2 — Run the analysis (delegate to stocks-advisor; do NOT reimplement)

1. Read the project daily log (`.agents/memory/YYYY-MM-DD.md`) to extract any prior weekly context for these tickers — pass it as `prior_context` to bias the run toward changed names.
2. Invoke the `stocks-advisor` skill in **holdings-review mode** on the parsed positions list.
   stocks-advisor handles: Step -1 memory recall, Step 0.7 TradingView health check (DEGRADED fallback = MA-only, WATCH-only verdicts), Step 0.8 triage (N>12 → full-panel top K≈10, one-line screen the rest), 5-seat panel analysis, Step 3.5 SOURCES & DATA appendix, Step 3.6 high-confidence RECAP + SETUP ALERTS.
3. Do NOT pull TradingView data, yfinance, or fundamentals yourself — stocks-advisor's orchestrator does that.
4. Collect stocks-advisor's full output for assembly in Step 3.

---

## Step 3 — Assemble the weekly report

Compose a single Markdown document in this order:

### (a) Date + Book Snapshot
- Report date
- Total equity (sum of positions × approximate price or use PnL + cost basis from CSV if available)
- Top-10 concentration % (top 10 positions as % of total book)
- Crypto-beta % (HOLD-ONLY names as % of total book)

### (b) Financial Narrative
- Sourced narrative from stocks-advisor's narrative seat.
- Every factual claim MUST include a URL citation. Reuse stocks-advisor's narrative output verbatim where possible.

### (c) High-Confidence RECAP Table
- Source: stocks-advisor Step 3.6 output.
- Only verdicts with conviction ≥ 4.
- Columns: Asset | Action (ADD/TRIM/EXIT) | One-line reason.
- HOLD-ONLY names: show as HOLD regardless of analysis output.

### (d) SETUP ALERTS Table
- Source: stocks-advisor Step 3.6 setup alerts.
- Columns: Asset | Exact condition | Then-do | Thesis.
- After the table, add: "Register these alerts via the `mkt` skill."

### (e) DROP List
- Non-crypto-beta EXIT and TRIM candidates with one-line reasoning.
- Never include HOLD-ONLY names here.

### (f) ETF Section
- Which ETFs in the portfolio are fair/undervalued vs extended, per stocks-advisor ETF analysis.
- Note if only trend/MA data was available (no fundamental data for ETFs).

### (g) SOURCES & DATA Appendix
- All web-fetched URLs used in analysis.
- Fundamentals.py provenance (which tickers used live data vs cached).
- Reuse stocks-advisor Step 3.5 output verbatim.

---

## Step 4 — Publishing (delegated to stocks-advisor)

Notion publishing is owned by `stocks-advisor`. When `.cache/stocks-advisor/notion.yaml` is configured, the Step 2 delegation to stocks-advisor publishes the research as a dated Notion page (title `YYYY-MM-DD <narrative>`) and returns its URL. stocks-daily does NOT publish separately — this avoids duplicated publish logic. Capture the URL stocks-advisor returns for the memory step. If stocks-advisor's Notion config is absent, no page is published (publishing is opt-in there); surface that to the user rather than re-implementing publishing here.

---

## Step 5 — Persist memory (mandatory; do BEFORE replying to user)

Append to `.agents/memory/$(date +%F).md` using the standard workflow_memory_format:

```markdown
## stocks-daily — YYYY-MM-DD
**Query:** Weekly portfolio review
**Assets found:** [comma-separated tickers reviewed]
**Verdicts:**
- TICKER: [T1/T2/T3/AVOID] [ACCUMULATE/WAIT/AVOID/HOLD] | entry: [price zone or condition] | catalyst: [trigger] | invalidation: [kill condition]
**Key delta:** [what changed vs prior week — one sentence]
**Report:** [Notion page URL returned by stocks-advisor, or "inline" if unpublished]
```

stocks-advisor writes per-ticker detail memory; this step adds the weekly roll-up. Do not skip.

---

## Scheduling (document only; do not auto-create)

To automate: use the `schedule` skill or configure a cron that fires `/stocks-daily` once a week (e.g., Sunday evening).

The skill is **idempotent per week** — re-running creates another dated Notion page; no harm done.

---

## Done when

- [ ] `positions.csv` read and parsed without inventing data
- [ ] stocks-advisor analysis completed (holdings-review mode)
- [ ] Weekly report assembled: narrative + RECAP table + SETUP ALERTS + DROP list + ETF section + SOURCES appendix
- [ ] Notion publishing left to stocks-advisor (no duplicate publish here); captured the returned page URL if one was produced
- [ ] Memory entry appended to daily log
- [ ] Response to user flags output as educational, not advice
