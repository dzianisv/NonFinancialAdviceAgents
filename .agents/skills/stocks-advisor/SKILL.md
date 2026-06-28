---
name: stocks-advisor
description: "Portfolio-agnostic equity advisor. Analyzes a user-supplied ticker list, a Google Sheet of holdings, OR discovers stocks via current market themes (AI supply chain, robotics, energy transition, defense, fintech) discovered LIVE via web_fetch. Runs a 5-seat analyst panel per stock (fundamental / technical / narrative-macro / sentiment-positioning / smart-money-institutional-flows) in parallel subagents. When holdings are provided (Google Sheet URL), outputs HOLD/ADD/TRIM/EXIT per position with tax harvest table and cash deployment plan. When discovering or analyzing a watchlist, outputs entry zone, bar-close trigger, market-based stop, conviction, theme tag. Triggers: \"run the stock panel\", \"analyze these stocks: [list]\", \"review my portfolio: [sheet URL]\", \"find stocks in the AI supply chain theme\", \"what stocks should I look at this week\", \"find entry points for my watchlist\". Individual stocks only. Educational, not advice."
license: MIT
compatibility: opencode
metadata:
  audience: equity-allocators
  domain: equity-portfolio-management
  role: portfolio-manager
  source: "Architecture mirrors crypto-advisor (2026); seats grounded in fundamental-analysis + analyst-technical-analysis (Bernstein 2009)"
---

# Stocks Portfolio Manager

Analyze individual stocks **one at a time** → run a 5-seat analyst panel per stock → output a concrete
**entry plan** (zone + trigger + stop) and a BUY / WATCH / SKIP decision. The stock list is user-supplied
or **discovered live** from the market themes currently driving institutional flows. Hardcode nothing — no
positions, no themes.

> Educational analysis, not financial advice. Single stocks are satellites; the index is the bar.

## The job is the ENTRY, not the company

The question is **not** "is this a good company" — it is **"is NOW a good time to enter, and where
exactly?"** A great company at the wrong entry is a wrong trade. Every output ends with a price zone, a
bar-close trigger, and a market-based stop, or it is incomplete.

## Quickstart

### Review your existing portfolio (Google Sheet)
```
Invoke the stocks-advisor skill.
Holdings: https://docs.google.com/spreadsheets/d/1aunLbpNGo85WqrMHiIsy6nFUija4Lnjot-rIhE-pGU8/edit?gid=1914937017
Tab: IBKR
Cash to deploy: $26,320
```
Reads positions (ticker, qty, cost basis) from the sheet, runs the 5-seat panel per position. Verdicts
become **HOLD / ADD / TRIM / EXIT** (not BUY/WATCH/SKIP) since cost basis and P&L are known. Output adds a
tax-harvest table and cash-deployment plan.

### Analyze a supplied watchlist
```
Run stocks-advisor on: AVGO, MRVL, VRT, CEG
```

### Discover stocks within a theme, then analyze
```
Find stocks in the AI supply chain theme and run the stock panel
```
Discovers the theme's constituents live (web_fetch — §Theme discovery), then runs the per-stock panel on
the discovered names.

**Full per-run loop:** see Step 1.5 (Sequential per-stock loop).

---

## Hard constraints — read before running (these dictate the whole design)

1. **TradingView MCP + yfinance live ONLY in the orchestrator (you).** Subagents spawned via the task tool
   get a fresh toolset with **no** `tradingview-*` tools and **no** yfinance. So YOU pull every chart datum,
   run `fundamentals.py`, assemble one data package per stock, and **inject** it into each seat. Never tell
   a subagent to "pull TradingView data" or "run yfinance" — it cannot. Seats only *receive* the package and
   reason; the narrative seat may still `web_fetch` news.
2. **The chart is a single shared symbol slot.** `chart_set_symbol` mutates the one global chart — two
   tickers cannot be pulled at once. **Pull data strictly sequentially, one ticker at a time.** Track
   progress in the `todos` table so an interrupted run resumes cleanly.
3. **Sequential data pull, parallel analysis.** The five seats per stock share nothing — spawn them **in
   parallel** once the package is assembled.
4. **TradingView symbol mapping:** use `NASDAQ:{TICKER}` or `NYSE:{TICKER}` for US stocks. On exchange-lookup
   failure, fall back to bare `{TICKER}`. When unsure of the exchange, call `tradingview-symbol_search` to
   resolve it before `chart_set_symbol`.
5. **Indicators from TradingView; fundamentals + MA levels from yfinance.** `data_get_study_values` returns
   RSI(14), Bollinger(20,2), MACD(12,26,9), Volume at standard lengths — use them verbatim, do not recompute.
   Price levels (`ma50`, `ma200`, `52w_high/low`, `dd_from_52wh`, `vs_200d_ma`) and all fundamentals come
   from `scripts/fundamentals.py` (yfinance). This sidesteps the TradingView MA-length bug entirely (its
   `chart_manage_indicator` ignores the MA `length` input).
6. **Individual stocks only.** ETF / sleeve allocation belongs in `tradfi-portfolio-manager`. Portfolio-level
   synthesis across the analyzed names is the `stock-chair` skill's job (§Step 4).

---

## CONFIG — optional Notion publish target

Notion publishing is **opt-in**. The target lives in `.cache/stocks-advisor/notion.yaml`:

```yaml
page_url: "https://app.notion.com/p/..."
page_id: "<32-char hex id>"
```

Read `page_id` at publish time (§Step 5) — never hardcode it here. If the file is missing OR `page_id` is
empty, **skip publishing silently** and finish the run; absence is not an error.

---

## The honest base rate (state this every run)

From the `fundamental-analysis` skill, on full-history backtests of the investable stock-selection methods
vs SPY: **only 1 of 10 methods beat SPY on return (momentum); 0 of 10 beat it on Sharpe — including the ETF
that implements Morningstar's own stock-picking.** Single-stock selection is a low-base-rate bet. So:
- Single names are **satellites**, the index is the **core and the bar**.

> Source: Carver, *Systematic Trading*, Ch.2 — single-equity Sharpe ratio ≈ 0.15; a diversified equity index SR ≈ 0.20; each additional uncorrelated instrument raises the portfolio Sharpe; individual stock selection is structurally at a disadvantage to indexing on a risk-adjusted basis.

- A passing panel is a **hypothesis**, not validated alpha. TA setups are **hypothesis generation** —
  validate any mechanical rule with `strategy-discovery-backtest` (full costs, walk-forward) before risking
  real capital.
- yfinance fundamentals are **point-in-time UNSAFE** (today's numbers) — fine for *current* entry analysis,
  never for backtesting a screen.

> Source: Housel, *Psychology of Money*, Ch.1 — "doing well with money has a little to do with how smart you are and a lot to do with how you behave"; systematic checklists and fixed decision rules enforce the behavioral discipline that discretionary portfolios consistently lack.

---

## Theme discovery — discovered live, never hardcoded

Market narratives rotate. **Do not hardcode a theme list.** When the user asks "find stocks in theme X" /
"what should I look at this week", discover live themes and constituents by fetching and reading real pages:

1. **Identify the live themes.** Pull WSJ + FT first via the **paywall-free feed scripts** (the
   `wsj.com`/`ft.com` listing pages are bot-blocked from agent IPs — the feed scripts return real article
   URLs + a verbatim publisher teaser + date, no login):
   ```bash
   bun .agents/skills/read-news/scripts/feeds/wsj.ts --feed markets,business --days 5 --limit 25 --text
   bun .agents/skills/read-news/scripts/feeds/ft.ts  --section markets,companies,global-economy --days 5 --limit 25 --text
   ```
   Then `web_fetch` 1–2 of the **non-paywalled** listings for breadth:
   - `https://www.bloomberg.com/markets`
   - `https://finance.yahoo.com/topic/latest-news/` (sector/thematic trend listings)
2. **Map names to themes.** Tag each candidate ticker with one bucket:
   `AI_SUPPLY_CHAIN | ROBOTICS | ENERGY | DEFENSE | FINTECH | HEALTHCARE | OTHER`. Buckets are a
   classification convention, not a fixed universe — add one if the evidence supports it.
3. **Anti-hallucination rule (same as the narrative seat):** name a theme or constituent only if you found it
   this run in a page you actually `web_fetch`ed **or** in feed-script output you actually ran
   (`feeds/wsj.ts`/`feeds/ft.ts` print real URLs + verbatim teasers — those count as fetched). No fetched
   URL / no feed record = not a theme. Never list a "current narrative" from memory.

If the user supplies an explicit ticker list, skip discovery and analyze that list (still tag each name with
a theme in the output).

---

## Step 0 — Classify the request, then route (do this first)

Route BEFORE running any per-name panel. Do not run a full 5-seat panel on a question that is really an
allocation/deployment question.

| Intent (detect from the ask) | Route |
|---|---|
| "analyze these tickers / find entries / is now a good time to buy X" | This skill — per-name 5-seat panel (rest of this doc) |
| "review my portfolio" + holdings sheet | This skill per-name on the triaged subset → then hand to `stock-chair` for sizing/concentration |
| "deploy $X / what ETFs should I buy / which big-caps to avoid / sleeve allocation" | ALLOCATION question. Route to `tradfi-portfolio-manager` for the ETF/sleeve plan FIRST; use this skill only for the single-name satellite slice. Do NOT front-load a per-name panel. |

A portfolio review asking "what to buy/sell" is BOTH: triage the book here, but route the cash-deployment /
ETF-allocation answer to `tradfi-portfolio-manager` — do not improvise sleeve allocation here.

---

## Step 0.3 — Load prior memory

Before seeding the todo list, pull prior verdicts and user preferences for this run's tickers:

```bash
bun .agents/skills/portfolio-memory/recall.ts --desk stocks \
  --tickers "AVGO MRVL COIN PYPL"
```

Inject the printed `<prior_context>` block into EVERY seat's data package. It has two parts: the
**canonical** current stance per ticker (the latest verdict, which physically overwrote any older one — you
cannot follow a stale call) and **episodic** dated history newest-first. If there is no prior memory the
script prints `[no prior memory for this run]` — continue normally. See `portfolio-memory` for the model.

Inspect the printed `source=` attribute. If `source="grep-fallback"` (the structured store was missed and it
fell back to grepping daily logs), set **MEMORY_DEGRADED** and print: "Memory: DEGRADED (grep-fallback) — no
canonical per-ticker stance; treat any recalled verdict as low-confidence, not an authoritative supersede."
Continue the run, but do not present a grep-fallback stance as the canonical current call.

---

## Step 0.5 — Load holdings from Google Sheet (if provided)

If the user passed a Google Sheet URL, read holdings before seeding the todo list. Use the `gws-sheets-read`
skill (https://www.skills.sh/googleworkspace/cli/gws-sheets-read):

```bash
gws sheets +read \
  --spreadsheet <ID extracted from URL> \
  --range "<Tab>!A:E"
```

Extract the spreadsheet ID from the URL (the long alphanumeric string between `/d/` and `/edit`). Parse the
response into `[{ticker, qty, cost_basis, market_value, pnl_pct, cash}]`:
- Rows where Type = "Cash" → set as `cash_to_deploy`
- Rows where Type = "Stock" → build the ticker universe for this run

When holdings are loaded:
- Add `cost_basis`, `qty`, `pnl_pct`, `dd_from_cost` to each ticker's data package
- Seat verdicts shift to **HOLD / ADD / TRIM / EXIT** (not BUY/WATCH/SKIP)
- After the signal table, output a **tax-harvest section** (positions with largest unrealized losses) and a
  **cash deployment section** (where to put `cash_to_deploy`)

If no sheet URL was provided, skip this step and use the user-supplied ticker list or theme discovery.

---

## Step 0.6 — Create the run artifact directory

Run once before the per-ticker loop. All per-ticker data packages, seat results, and the final report land
here.

```bash
RUN_DIR=".cache/stocks-advisor/research/$(date +%Y-%m-%d_%H-%M)"
mkdir -p "$RUN_DIR"
echo "Artifacts: $RUN_DIR"
```

Every ticker gets its own subdirectory `$RUN_DIR/{TICKER}/`. Layout after a complete run:
```
.cache/stocks-advisor/research/2026-06-27_14-30/
├── report.md
├── AVGO/
│   ├── data_package.json          # merged TV + fundamentals.py output
│   ├── seat_fundamental.json
│   ├── seat_technical.json
│   ├── seat_narrative_macro.json
│   ├── seat_sentiment.json
│   ├── seat_smart_money.json
│   └── verdict.json               # decision, entry_low/high, trigger, stop, target, conviction
├── MRVL/
│   └── ...
└── ...
```

---

## Step 0.7 — Preflight: is TradingView alive? (run before the per-ticker loop)

Call `tradingview-tv_health_check` ONCE before the loop.
- PASS → normal mode (pull live charts per Step 1).
- FAIL (CDP down, or `tv_launch` returns "not found") → enter **DEGRADED_TECH** for the whole run:
  - Technical read comes from `fundamentals.py` ONLY: `ma50`, `ma200`, `vs_200d_ma`, `vs_50d_ma`,
    `52w_high/low`, `dd_from_52wh`.
  - RSI / Bollinger / MACD = **UNAVAILABLE** — do not guess them. Technical STATE collapses to
    `{ABOVE_TREND, BELOW_TREND, UNKNOWN}` (above/below the 200d).

> Source: Carver, *Systematic Trading*, Ch.7 (Forecasts / EWMAC) — exponentially weighted moving average crossovers are the primary evidence-based trend-following rule class; above/below a long-period MA is the simplest valid trend-state signal, grounded in the same prospect-theory behavioral rationale as all trend following.

  - No live bar-close trigger is computable → every name is **WATCH-only, never BUY**; entry zones come from
    MA levels.
  - Skip `capture_screenshot`; the screenshot self-check item does NOT apply in this mode.
  - Tag every output block: `DEGRADED: TradingView down — trend-only read, no live trigger.`

---

## Step 0.8 — Screen every name with fundamentals.py; reserve TradingView for deep dives

`fundamentals.py` (yfinance) is the DEFAULT source for the WHOLE book — cheap, no chart slot, runs for every
name. TradingView (live RSI/BB/MACD + screenshot) is the single-chart-slot bottleneck — running it for every
name does not scale (a 50-80 name book = thousands of MCP calls). So TradingView is SELECTIVE, not default.

1. **Screen ALL names with `fundamentals.py` first** — the baseline for every holding/candidate. Run it for
   the entire list (parallelizable; it is a plain script, not an MCP call). Produce a one-line read per name:
   trend (above/below 200d & 50d), valuation, growth, drawdown.
2. **Rank by decision-relevance** from that screen: concentration weight (% of book), |unrealized P&L %|,
   cash-deploy candidate, proximity to a key level (near 50d/200d or a 52w extreme), or a fundamental/thesis
   break.
3. **Select the deep-dive subset** — the names that warrant a chart: the top decision-relevant names (default
   K ≈ 10) PLUS any name the screen flags (sitting on a trigger level, a TRIM/EXIT candidate, a deploy
   target). Everything else stays fundamentals-only.
4. **Run TradingView (Step 1.5, sequential single slot) + the full 5-seat panel ONLY on the deep-dive
   subset.** Every other name gets its verdict from the fundamentals screen alone (HOLD/TRIM/EXIT, or WATCH
   for a watchlist) — no TradingView, no 5 seats.
5. If TradingView is down (DEGRADED_TECH, Step 0.7), the deep-dive subset also falls back to
   fundamentals-only — the whole book is screen-level, nothing blocks.
6. State explicitly which names got the TradingView deep dive vs the fundamentals-only screen, and the K
   used. Never silently drop a name.

---

## Step 0.9 — Macro-regime synthesis (run ONCE before the per-stock loop)

Produce a single shared macro-regime paragraph that all seats receive in their data package — the market
context every per-stock decision is made inside.

**Run the news feeds:**
```bash
bun .agents/skills/read-news/scripts/feeds/wsj.ts --feed markets,economy --days 3 --limit 15 --text
bun .agents/skills/read-news/scripts/feeds/ft.ts  --section markets,global-economy --days 3 --limit 15 --text
```
Also fetch `https://finance.yahoo.com/topic/latest-news/` for breadth.

**Produce a 5-sentence macro-regime paragraph** covering exactly these five dimensions, each grounded in a
specific named fact from the feeds:

```
MACRO REGIME — {DATE}
1. Fed/rates: [Fed stance + next meeting expectation + one named data point, e.g. "CME FedWatch: 62% for Sep cut"]
2. Growth/earnings: [current earnings season signal or GDP read, specific number]
3. Inflation: [latest CPI/PCE print with date, one sentence]
4. Geopolitics/exogenous: [the single most market-relevant geopolitical fact this week, named]
5. Liquidity/risk appetite: [equity market trend + vol signal, e.g. "VIX at 18, Nasdaq -3% week"]
```

> Source: Howell, *Capital Wars*, Preface — "economic cycles are driven by financial flows, namely quantities of savings and credits, and not by high street inflation or the level of interest rates"; Global Liquidity ($130 trillion pool of footloose capital) is the dominant driver of asset-price booms and busts; Fed/rates matter primarily through their effect on liquidity supply, not through the cost-of-capital channel alone.

**Anti-hallucination rule:** every sentence names a source and a specific, dateable fact — none from memory.
If a dimension has no data from the feeds this run, write "No live signal for [dimension] this run."

**Inject into every seat's data package** as `macro_regime: "..."` — shared context, identical for all seats,
not per-seat research.

**Save to run dir:**
```bash
echo "$MACRO_REGIME" > "$RUN_DIR/macro_regime.txt"
```

---

## Step 1 — Seed the todo list (one row per ticker)

```sql
INSERT INTO todos (id, title, description) VALUES
 ('stk-AVGO', 'Analyzing AVGO', 'Pull TradingView D/W + studies, run fundamentals.py, 5-seat panel, decide'),
 ('stk-MRVL', 'Analyzing MRVL', 'idem'),
 ('stk-VRT',  'Analyzing VRT',  'idem');
-- one row per ticker in this run's list
```

Create the verdict tracker once:

```sql
CREATE TABLE IF NOT EXISTS stock_analysis (
  symbol TEXT PRIMARY KEY, company TEXT, theme TEXT, theme_phase TEXT,
  fundamental TEXT, technical TEXT, narrative TEXT, sentiment TEXT, smartmoney TEXT,
  decision TEXT, entry_low REAL, entry_high REAL, trigger TEXT,
  stop REAL, target REAL, conviction INTEGER, status TEXT DEFAULT 'pending');
```

```bash
# Back-compat: pre-existing 4-seat tables lack the smartmoney column; idempotent — error suppressed if column already exists
sqlite3 "$DB" 'ALTER TABLE stock_analysis ADD COLUMN smartmoney TEXT;' 2>/dev/null || true
```

---

## Step 1.5 — Sequential per-stock loop (orchestrator only; do NOT parallelize the data pull)

Runs ONLY for the deep-dive subset selected in Step 0.8 — names that stayed fundamentals-only never enter
this loop. Pick the next `pending` todo, `UPDATE todos SET status='in_progress'`, then for that ticker:

**1a. Pull TradingView data (MCP, in this session).** First call `tradingview-chart_get_state` and inspect
the `studies` list. **Add a study only if its name is NOT already present** — a duplicate pushes a second
identical series, inflates context, and produces duplicate rows. Required studies (add only if absent):
**Relative Strength Index**, **Bollinger Bands**, **MACD**. Volume is always present. Do NOT add MA studies
(length input is ignored — use yfinance MAs).

```
tradingview-symbol_search    query="{TICKER}"          → resolve NASDAQ:/NYSE: prefix if unknown
tradingview-chart_get_state                            → inspect studies; dedup before proceeding
tradingview-chart_set_symbol   symbol="NASDAQ:{TICKER}" (or NYSE:, or bare {TICKER} on failure)
tradingview-chart_set_timeframe timeframe="D"
tradingview-data_get_ohlcv     count=365 summary=true  → 52w structure + avg volume
tradingview-data_get_ohlcv     count=250 summary=false → daily closes for the technical seat
tradingview-data_get_study_values                       → RSI(14), BB(20,2), MACD, Volume (one each)
tradingview-chart_set_timeframe timeframe="W"
tradingview-data_get_ohlcv     count=210 summary=false → weekly closes (long-term structure)
tradingview-chart_set_timeframe timeframe="D"          → reset to daily
tradingview-capture_screenshot                          → save; then `view` the file_path to embed inline
```

**1b. Pull fundamentals (yfinance helper, in this session):**
```bash
echo '{"symbol":"{TICKER}","period":"1y"}' > .agents/skills/stocks-advisor/scripts/{TICKER}.json
/Users/engineer/.venv/bin/python3 .agents/skills/stocks-advisor/scripts/fundamentals.py \
  .agents/skills/stocks-advisor/scripts/{TICKER}.json
```
The helper writes `{TICKER}.json.out.json` with: price, 52w_high/low, ma50, ma200, forward_pe, trailing_pe,
peg_ratio, revenue_growth, earnings_growth, gross_margin, operating_margin, fcf, market_cap, fcf_yield, roe,
short_percent, institutional_pct, recommendation_mean, analyst_count, dd_from_52wh, vs_200d_ma, vs_50d_ma.
Any field yfinance lacks is `null` — never fill a null with a guess.

> Source: Graham, *The Intelligent Investor*, Ch.14 — defensive investor screen: fwdPE ≤ 15 and price-to-book ≤ 1.5; margin of safety is the gap between price and intrinsic value. Lynch, *One Up on Wall Street* — PEG < 1.0 = undervalued growth; FCF yield threshold: Portfolio heuristic — positive FCF is the prerequisite for compounding without dilution. Institutional ownership (`institutional_pct`): Portfolio heuristic derived from 13F flow literature; high institutional concentration signals crowding risk (see conviction rules).

**1c. Assemble the data package** by merging the TradingView study values (RSI, BB, MACD, Volume, 52w hi/lo
from `summary=true`, the daily/weekly close arrays) with the full `fundamentals.py` JSON. This single package
is what every seat receives — seats add nothing to it except the narrative seat's fetched news.

> Source: Wilder, *New Concepts in Technical Trading Systems* (1978) — RSI(14) is the original specification; readings < 30 = oversold, > 70 = overbought as sentiment extremes, not automatic reversal signals. Appel (MACD inventor, 1979) — MACD(12,26,9) crossover signals momentum regime change. Bernstein, *Ultimate Day Trader*, Ch.9 — MACD and Momentum are listed as key Trigger tools within the STF framework; use in conjunction with a Setup, never in isolation.

**Cache the data package:**
```bash
mkdir -p "$RUN_DIR/{TICKER}"
python3 -c "
import json, sys
pkg = sys.argv[1]
open('$RUN_DIR/{TICKER}/data_package.json', 'w').write(pkg)
" "$DATA_PACKAGE_JSON"
```

**1d. Spawn the 5 seats IN PARALLEL** (task subagents), each with the **same** package injected. Each seat
reads ONE lens and returns the fixed shape below. Seats share nothing, so they run concurrently.

---

## The 5-seat panel (subagent prompts — reuse verbatim, fill the blanks)

> The data package is injected into every seat. Subagents are a **context firewall**: they reason over the
> package only and never pull MCP/yfinance data. External calls allowed: the **narrative seat** may web_fetch
> news + run paywall-free feed scripts (`feeds/wsj.ts`/`feeds/ft.ts`); the **smart-money seat** may web_fetch
> disclosed-flow sources (openinsider.com, 13f.info, EDGAR, capitoltrades.com). All other seats: injected
> data only.

> Source: Surowiecki, *The Wisdom of Crowds* (2004) — independent assessments from multiple expert perspectives, aggregated without anchoring to each other's views, consistently outperform single-expert forecasts; the 5-seat structure enforces independence by design (seats share data but never see each other's verdicts before returning their own).

| Seat | Lens file (read ONLY this) | Output shape |
|---|---|---|
| 1 Fundamental | `.agents/skills/fundamental-analysis/SKILL.md` | RATING / KEY METRIC / MOAT / MARGIN OF SAFETY / BLIND SPOT |
| 2 Technical | `.agents/skills/analyst-technical-analysis/SKILL.md` | STATE / SETUP / TRIGGER / STOP / TARGET / BLIND SPOT |
| 3 Narrative-Macro | web_fetch + feed scripts (read_news.ts, feeds/wsj.ts, feeds/ft.ts) | PHASE / THEME / SOURCES(≥2 real) / WHY / BLIND SPOT |
| 4 Sentiment | injected package only | READ / KEY / CONTRARIAN TILT / BLIND SPOT |
| 5 Smart-Money | web_fetch openinsider/13f.info/EDGAR/capitoltrades | VERDICT / CONVICTION / Form4·13F·13D·PTR / SOURCES |

**Full subagent prompts — copy verbatim from `references/seat-prompts.md`.** Each seat receives the same
injected data package; only Seats 3 and 5 may make external calls.

**Cache seat results** — write each seat's output immediately after it returns:
```bash
echo '{fundamental_json}'     > "$RUN_DIR/{TICKER}/seat_fundamental.json"
echo '{technical_json}'       > "$RUN_DIR/{TICKER}/seat_technical.json"
echo '{narrative_macro_json}' > "$RUN_DIR/{TICKER}/seat_narrative_macro.json"
echo '{sentiment_json}'       > "$RUN_DIR/{TICKER}/seat_sentiment.json"
echo '{smart_money_json}'     > "$RUN_DIR/{TICKER}/seat_smart_money.json"
```
Each seat JSON must include at minimum `{verdict, conviction, key_metric, blind_spot, sources:[]}`.

**After all 5 seats return:** proceed to Step 2 (SKEPTIC) → Step 2.5 (CIO SYNTHESIS) → Step 2.7 (RISK
MANAGER, BUY/ADD only). The per-seat data feeds the Skeptic; Skeptic output feeds the CIO; CIO verdict feeds
the Risk Manager. The hierarchy is sequential by design — do not skip ahead.

**1e. Persist the seat verdicts and decision:**

After Step 2.7 completes (or Step 2.5 for non-BUY/ADD tickers), the final verdict is available.

```sql
-- Add new columns if not present (idempotent)
ALTER TABLE stock_analysis ADD COLUMN skeptic TEXT;    -- 2>/dev/null || true
ALTER TABLE stock_analysis ADD COLUMN cio_memo TEXT;   -- 2>/dev/null || true
ALTER TABLE stock_analysis ADD COLUMN dissent TEXT;    -- 2>/dev/null || true
ALTER TABLE stock_analysis ADD COLUMN risk_status TEXT;-- 2>/dev/null || true

UPDATE stock_analysis SET company=?, theme=?, theme_phase=?, fundamental=?, technical=?,
  narrative=?, sentiment=?, smartmoney=?, skeptic=?, cio_memo=?, dissent=?, risk_status=?,
  decision=?, entry_low=?, entry_high=?, trigger=?, stop=?, target=?,
  conviction=?, status='done' WHERE symbol=?;
UPDATE todos SET status='done' WHERE id='stk-{TICKER}';
```

**Cache the verdict:**
```bash
echo '{verdict_json}' > "$RUN_DIR/{TICKER}/verdict.json"
# verdict_json = {decision, entry_low, entry_high, trigger, stop, target, conviction, theme,
#                invalidation[3], dissent, cio_memo, risk_status, risk_position_size}
```

**1f. Repeat** for the next `pending` todo until none remain.

**1g. Write verdict to memory.** After each ticker completes, persist the verdict. This upserts the canonical
one-line stance (the new verdict overwrites any prior one for this ticker — supersede is enforced here, not
left to the agent) and appends to the dated episodic log:

```bash
bun .agents/skills/portfolio-memory/remember.ts \
  --desk stocks --ticker {TICKER} --verdict {BUY|ADD|WATCH|HOLD|TRIM|EXIT|SKIP} \
  --date {YYYY-MM-DD} --conviction {N} \
  --body "{cause-first thesis ≤200 chars}: fundamental {RATING} {KEY_METRIC}; technical {STATE}; narrative {PHASE}; entry {entry_low}-{entry_high}, stop {stop}. Theme {theme}."
```

---

## Step 2 — SKEPTIC (subagent — spawn after all 5 seat verdicts for this ticker return)

The analyst panel is the proposal. The Skeptic is the mandatory institutional adversary — assigned, not
volunteer. It runs on every ticker regardless of how bullish the panel looks. Never skip this step. Spawn
as a subagent (`/model sonnet /effort high`).

**Skeptic subagent prompt — inject verbatim, fill `{placeholders}`:**

```
You are the Skeptic for {TICKER}. Your role is mandatory: find the strongest case AGAINST the consensus, even if you privately agree with the analysts.

GAP ANALYSIS: Name the single biggest blind spot across all 5 analyst verdicts — data they had but underweighted, or a dimension none of them checked.
TAIL RISK: Name one specific, non-generic downside scenario. Assign a probability (1–15%) and the expected loss magnitude if it fires. No generics like "macro deterioration."
HISTORICAL ANALOG: One real failed trade with a structurally identical setup — same thesis type, same narrative phase, same sentiment read. Exact company, year, outcome. No fabricated cases.

INVALIDATION CONDITIONS (all three required before any BUY advances):
  (a) {falsifiable condition — a specific price level, ratio, or filing event that proves the thesis wrong}
  (b) {falsifiable condition 2}
  (c) {falsifiable condition 3}

SKEPTIC VERDICT: {SKIP | WATCH | BUY} — {one sentence explaining the controlling factor}
Inputs: {ALL_5_SEAT_VERDICTS_JSON} | {MACRO_REGIME}
```

Cache output: `echo '{skeptic_json}' > "$RUN_DIR/{TICKER}/seat_skeptic.json"`

---

## Step 2.5 — CIO SYNTHESIS (subagent — spawn after Skeptic returns)

The CIO reads all 5 analyst verdicts plus the Skeptic's challenge and makes the final call. Cannot abstain.
Spawn as a subagent (`/model sonnet /effort high`). The CIO's verdict replaces the old deterministic table —
the rules below are the CIO's decision criteria, applied with judgment, not mechanically.

**CIO subagent prompt — inject verbatim, fill `{placeholders}`:**

```
You are the CIO for {TICKER}. Read all 5 analyst verdicts and the Skeptic challenge. You cannot abstain.

CIRCLE OF COMPETENCE: State in 2 sentences how {TICKER} earns money and why competitors cannot replicate it. If you cannot → FINAL VERDICT: PASS. Stop here.
SKEPTIC RESPONSE: Address the Skeptic's single strongest argument — rebut with evidence, or accept it and explain why you invest despite it.
VERDICT (believability-weighted: fundamental/narrative 2×, technical 2×):
  BUY requires: Fundamental ≥ GOOD, named setup + live bar-close trigger, narrative not LATE/FADING, Sentiment ≠ EXTREME.
  Holdings path: ADD/HOLD/TRIM/EXIT when cost basis is known (EXIT: POOR/FADING/BROKEN; TRIM: weight>15%/EXTREME/LATE; ADD: BUY gate + room; HOLD: else).
  Conviction (start 3): +1 ≥3 seats; +1 EARLY+QUIET; −1 CROWDED; −1 PEG>2/neg FCF; −1 LATE; +1 SM-accum (≥2 seats); −1 SM-distrib (caps BUY at 3). Clamp 1–5.

Output exactly:
FINAL VERDICT: {BUY|WATCH|SKIP}  or {ADD|HOLD|TRIM|EXIT}
CONVICTION: {1–5}/5
DISSENT LOGGED: {Skeptic's best objection in one sentence — printed even when overruled}
CIO MEMO: {1 paragraph: controlling factor, Skeptic right/wrong and why, one fact that would change this call}
Inputs: {ALL_5_VERDICTS_JSON} | {SKEPTIC_JSON} | {MACRO_REGIME}
```

> Source: Surowiecki, *Wisdom of Crowds* (2004) — domain-weighted aggregation (believability by demonstrated track record in a specific area) consistently outperforms equal-vote averaging; the CIO weights fundamental/narrative for thesis quality and technical for timing rather than treating all 5 seats as peers. Bridgewater ILC design principle: every open position has a standing institutional adversary; the Skeptic role encodes this structurally so the challenge function cannot collapse when the same voice both proposes and critiques.

**A WATCH verdict is an alert trigger.** Register via the `mkt` skill (see *Set a buy-alert*) with the CIO Memo as the thesis string.

Cache output: `echo '{cio_json}' > "$RUN_DIR/{TICKER}/seat_cio.json"`

---

## Step 2.7 — RISK MANAGER CHECK (orchestrator inline — run only when CIO verdict is BUY or ADD)

Skip entirely when CIO verdict is WATCH, SKIP, HOLD, TRIM, EXIT, or PASS. The Risk Manager checks
portfolio-level constraints only — thesis quality is the CIO's job. Hard rules cannot be overridden by a
strong thesis. Run this inline (not a subagent) using the portfolio data already loaded.

**Risk Manager check prompt — run inline, fill `{placeholders}`:**

```
You are the Risk Manager for {TICKER} (CIO: {BUY|ADD}, conviction: {N}/5). Check constraints only — not thesis quality. First breach blocks, no override.
Rule 1: Position ≥ 10% of book → BLOCKED: "concentration cap — no ADD until trimmed below 8%."
Rule 2: Primary factor group ≥ 25% of book → BLOCKED: "factor concentration limit."
Rule 3: Cash < $2,000 → BLOCKED: "insufficient cash for minimum position."
Rule 4: Conviction ≤ 2/5 → BLOCKED: "below minimum conviction threshold."
If no rule fires → APPROVED.
Position size (APPROVED): conviction × 2% × total_book, capped at (10% − current_weight).
  5/5 → 10% target; 4/5 → 6%; 3/5 → 4%. Subtract current weight for the add size.

Output:
STATUS: {APPROVED | BLOCKED}
POSITION SIZE: {$amount, % of book} or "n/a"
REASON: {rule fired, or "all constraints clear — factor headroom: {pct}%"}
Portfolio inputs: current_weight={W}%, factor_group={F}, factor_group_weight={FW}%, cash=${CASH}, total_book=${BOOK}
```

**Verdict flow after Risk Manager:** if APPROVED → CIO verdict stands; if BLOCKED → downgrade to WATCH
(thesis intact, constraint violated — fix the constraint, then re-run). Log the block reason in the final
output block so the user knows what to clear.

Cache output: `echo '{risk_json}' > "$RUN_DIR/{TICKER}/seat_risk.json"`

> Source: Citadel operating model (from comparative research) — risk team has operational authority to force position reduction without PM consent; the hard-gate design here encodes this: portfolio-level constraints are enforced by a separate role with veto power, independent of how compelling the thesis is. Carver, *Systematic Trading*, Ch.4 — concentration limits (≤10% single name, ≤25% factor group) are the primary structural protection against idiosyncratic drawdown; stops alone are insufficient.

**Step 2 exit conditions:** after Step 2.7 (or Step 2.5 for non-BUY/ADD verdicts), the final verdict is set.
Proceed to Step 3. The output format block includes DISSENT LOGGED and RISK STATUS fields (see below).

---

## Output format per stock

> **TOP RECAP rule (MANDATORY — chat output AND Notion page).** Every run's report OPENS with a 2–3 sentence
> prose RECAP, before any per-stock block or the signal table, stating in plain English: (a) the
> highest-confidence BUY/SELL actions to take now, each with one-line reasoning; (b) the current market
> narrative in one sentence. This is a prose TL;DR — **distinct** from the Step 3.6 RECAP *table* at the end.

```
═══════════════════════════════════════════════════════
 {TICKER} — {COMPANY} — {DATE}
 Theme: {AI_SUPPLY_CHAIN | ROBOTICS | ENERGY | DEFENSE | FINTECH | HEALTHCARE | OTHER}
 Theme phase: {EARLY_CYCLE | MID_CYCLE | LATE_CYCLE | FADING}
═══════════════════════════════════════════════════════
 SEAT VERDICTS
 Fundamental : {STRONG/GOOD/FAIR/POOR} — {one line: key metric}
 Technical   : {SETUP_NAMED/NO_SETUP/BROKEN} — {setup name or "no trigger"}
 Narrative   : {EARLY/MID/LATE/FADING} — {one line: why}
 Sentiment   : {QUIET_ACCUM/NEUTRAL/CROWDED/EXTREME} — {one line}
 Smart-money : {ACCUMULATING/DISTRIBUTING/NEUTRAL} — {CONVICTION: HIGH/MED/LOW | one line: key signal}
 Skeptic     : {SKIP/WATCH/BUY} — {one line: strongest objection}

 CIO DECISION: {BUY / WATCH / SKIP / PASS}   (or ADD / HOLD / TRIM / EXIT on holdings path)
 Entry zone  : ${low}–${high}
 Trigger     : {bar-close above/below X on timeframe Y}
 Stop        : ${level} ({basis: support/MA/range})
 Target      : ${level} (risk:reward {X}:1)
 Conviction  : {1-5}/5
 Dissent     : {Skeptic's best objection — printed even when overruled}
 CIO memo    : {one sentence — controlling factor and what would change this call}
 Risk status : {APPROVED $X (N% book) | BLOCKED: reason | N/A (not BUY/ADD)}
 Invalidation: {3 falsifiable conditions from Skeptic — thesis-break, not just the price stop}
═══════════════════════════════════════════════════════
```

**Citation rule (per stock):** any narrative/news claim in the block carries an inline
`[source: https://exact-article-url]`. Technical indicators (RSI, MACD, MAs) computed from price data need no
source; news facts, theme claims, and fund-flow figures DO. No URL = remove the claim.

---

## Step 3 — Final signal table

```
STOCKS PANEL — {DATE} — {N} stocks analyzed
Theme map: [AI_SUPPLY_CHAIN: X] [ROBOTICS: Y] [ENERGY: Z] [DEFENSE: W] ...

Ticker  Company         Decision  Conv  Entry zone     Trigger            Theme
------  -------         --------  ----  ----------     -------            -----
AVGO    Broadcom        WATCH     4/5   $350-380       Reclaim $390       AI_SUPPLY_CHAIN
MRVL    Marvell Tech    BUY       4/5   $255-270       Bar close >$280    AI_SUPPLY_CHAIN
CEG     Constellation   SKIP      2/5   —              none (LATE_CYCLE)  ENERGY
...
```

---

## Step 3.5 — Sources & data provenance appendix (MANDATORY — always print)

After the signal table, ALWAYS print a consolidated **SOURCES & DATA** block so every news claim and
market-data point is traceable. Aggregate from every seat that fetched:

1. **News / narrative sources** — every URL the narrative seat web_fetched OR got from the feed scripts
   (`feeds/wsj.ts`, `feeds/ft.ts`, `read_news.ts`). One per line: `[Tn] https://url (date) — "verbatim teaser/quote"`.
2. **Smart-money / filing sources** — every URL the smart-money seat actually web_fetched (openinsider,
   13f.info, EDGAR, capitoltrades, finviz/marketbeat fallbacks). One per line.
3. **Market-data provenance** — state the origin of prices/indicators/fundamentals: `fundamentals.py
   (yfinance) per ticker: {tickers run}` and `Technicals: TradingView studies RSI/BB/MACD/Volume` (or, in
   DEGRADED_TECH mode: `Technicals: DEGRADED — MA levels from fundamentals.py only, no TradingView`).
4. If any seat returned `INSUFFICIENT DATA`, list it here explicitly rather than omitting it.

Format:
```
SOURCES & DATA — {DATE}
News ({n}):
  [T1] https://... (date) — "verbatim teaser"
  ...
Filings/flows ({n}):
  https://...
Market data:
  fundamentals.py (yfinance): {tickers}
  Technicals: {TradingView studies | DEGRADED MA-only}
```

Never print a verdict that depends on a source you cannot list here. No source listed = remove the claim.
Required in BOTH normal and DEGRADED_TECH mode.

---

## Step 3.6 — High-confidence recap + setup-alerts table (MANDATORY — final output, print LAST)

End EVERY run with these two tables so the user sees the actionable subset at a glance.

**RECAP — high-confidence only.** Include ONLY decisions with conviction ≥ 4/5 (or, for a holdings review,
the unambiguous ADD / EXIT calls). Drop everything WATCH-without-a-trigger, NEUTRAL, or conviction ≤ 3 —
those live in the full table above. If nothing clears the bar, print "No high-confidence actions today — all
names are WATCH (see table above)" rather than padding the list.

```
RECAP — high-confidence ({DATE})
Asset   Action            Why (one line, plain English)
-----   ------            -----------------------------
{TICK}  BUY/ADD/EXIT/TRIM {≤12-word plain-English reason}
...
```

**SETUP ALERTS — buy/sell only when a condition fires.** Every WATCH name with a *defined* trigger (a price
reclaim, a level, an indicator like RSI) goes here — not as a buy-now. State the exact condition and the
action it unlocks. Register these with the `mkt` skill so the user is pinged with the thesis when the
condition hits (see *Set a buy-alert*).

```
SETUP ALERTS ({DATE})
Asset   Condition (exact)               Then do        Thesis (one line)
-----   -----------------               -------        -----------------
{TICK}  close > ${level} (reclaim)      BUY {zone}     {≤12-word reason}
{TICK}  RSI(14) < 30 / pullback ${lvl}  ADD            {≤12-word reason}
...
```

A name is in RECAP **or** SETUP ALERTS, never both — high-confidence-now and buy-on-condition are mutually
exclusive. After printing SETUP ALERTS, offer to register them via the `mkt` skill. Required in BOTH normal
and DEGRADED_TECH mode; in DEGRADED mode the alert conditions are MA/price levels (no live bar-close trigger).

---

## Step 4 — Portfolio-synthesis seat (run inline AFTER per-stock loop completes)

After all per-stock panels finish, run a dedicated **portfolio-synthesis seat** — a single subagent that
receives ALL per-stock verdicts + the full holdings list and reasons across positions holistically. This is
the step the per-stock loop structurally cannot do.

**Input to the synthesis seat:**
- Full holdings list (ticker, qty, cost_basis, market_value, weight_pct)
- All per-stock verdicts from `$RUN_DIR/*/verdict.json`
- The macro_regime paragraph from `$RUN_DIR/macro_regime.txt`
- Theme map (how many names per theme bucket)

**Synthesis seat prompt (spawn as a subagent `/model opus /effort xhigh`):**

```
Produce a portfolio synthesis with EXACTLY these five sections, in order:

1. FACTOR CORRELATION MAP
   Group all holdings by primary risk factor (Fed/rates, USD, oil, AI-capex, China exposure, etc.). Per
   group: list holdings, total weight %, and the tail scenario ("if [factor] moves -20%, these all fall
   together"). Flag any factor whose combined weight > 25% of book as a CONCENTRATION RISK.

2. OVER-DIVERSIFICATION CRITIQUE
   Count positions. If > 40, state: "N positions means individual-stock selection creates noise, not signal
   — each name must earn its place or become index." List positions that are index-like (correlation > 0.85
   to SPY, market cap > $500B) and could be replaced with VOO for lower cost and less monitoring overhead.

> Source: Carver, *Systematic Trading*, Ch.2 & Ch.6 — "the law of active management shows diversification is the best source of additional risk-adjusted returns"; beyond ~20 uncorrelated instruments, marginal diversification benefit falls sharply; very large equity-only books approximate the index, making passive ETFs a cheaper substitute for index-like names.

3. CROSS-POSITION CONFLICTS
   Identify pairs where one seat says ADD and another says TRIM on names sharing the same factor exposure —
   these conflict at the portfolio level even if individually correct.

4. PORTFOLIO STRUCTURE VERDICT
   One paragraph: the biggest structural risk in this book right now, and the single action that reduces it
   most. Name the risk, name the action.

5. CASH DEPLOYMENT PRIORITY
   Given the per-stock ADD verdicts and cash available ($CASH), rank ADD candidates by portfolio-level fit
   (fills a gap, reduces concentration, best risk:reward). Maximum 3 names.

> Source: Carver, *Systematic Trading*, Ch.9 (Volatility Targeting) — "positions should be sized based on how volatile markets are, how confident your price forecasts are, and the amount of capital you wish to gamble"; staged entry (tranching cash into ranked ADD candidates) is the practical implementation of volatility-scaled position building. George (2004), *52-Week High and Momentum* — proximity to the 52-week high is a positive momentum predictor; used here as a tie-breaker when ranking ADD candidates by technical strength.

Do NOT re-analyze individual stocks — the per-stock panels already did that. Reason ACROSS positions and
surface what the per-stock loop structurally cannot see.

Holdings: {HOLDINGS_JSON}
Per-stock verdicts: {ALL_VERDICTS_JSON}
Macro regime: {MACRO_REGIME}
Theme map: {THEME_MAP}
```

This seat's output goes into the final report between the signal table and the SOURCES appendix.

**After this step, if the user asked a portfolio-aware question, invoke `stock-chair`** with the synthesis
seat's output for position sizing.

---

## Step 5 — Publish to Notion (if configured)

This skill is the **single owner** of Notion publishing for stock research (`stocks-daily` delegates here).
Publishing is opt-in and silent-skip — never fail the run because of it.

1. **Read the publish target:**
   ```sh
   PAGE_ID=$(grep '^page_id:' .cache/stocks-advisor/notion.yaml 2>/dev/null | sed -E 's/.*"([a-f0-9]+)".*/\1/')
   ```
   If `.cache/stocks-advisor/notion.yaml` is missing OR `PAGE_ID` is empty → **skip silently** and finish
   the run (do NOT stop, do NOT warn).
2. **Load Notion tools via ToolSearch:**
   `select:mcp__claude_ai_Notion__notion-create-pages,mcp__claude_ai_Notion__notion-fetch`
3. **Save to local file** (always — even if `PAGE_ID` is empty):
   - Filename: `YYYY-MM-DD <narrative>.md` — same title that would be used for Notion.
   - Path: `.cache/stocks-advisor/research/<title>.md`
   ```bash
   mkdir -p .cache/stocks-advisor/research
   # TITLE = computed title string, e.g. "2026-06-26 AI-bubble derisking — rotate to healthcare"
   # CONTENT = full report markdown (top recap + per-stock + sources + setup-alerts)
   python3 -c "
   import sys
   title, content = sys.argv[1], sys.argv[2]
   open(f'.cache/stocks-advisor/research/{title}.md', 'w').write(content)
   " "$TITLE" "$CONTENT"
   ```
4. **Create a NEW child page under `PAGE_ID`** (only if `PAGE_ID` non-empty):
   - **Title format `YYYY-MM-DD <narrative>`** — run date + a short narrative descriptor of the dominant
     theme (e.g. `2026-06-26 AI-bubble derisking — rotate to healthcare/defense`). Not a generic title.
   - Content: the full run output as Notion-flavored Markdown — the 2–3 sentence TOP RECAP first (§Output
     format per stock), then the narrative, the per-name decision tables, the SOURCES & DATA appendix
     (§Step 3.5), and the high-confidence RECAP + SETUP ALERTS (§Step 3.6). Use real Notion table blocks, not
     code-fenced text.
5. On any Notion error, report it and **continue** — never fail the run because publishing failed.
6. Print: `✅ Saved: .cache/stocks-advisor/research/<title>.md` and (if published) the Notion page URL.

---

## Worked example (one stock)

<example>
User: "Run stocks-advisor on MRVL."

Orchestrator (sequential): resolves `NASDAQ:MRVL`; pulls D/W OHLCV + RSI/BB/MACD/Volume + screenshot;
runs `fundamentals.py` → `{price: 264.71, ma200: 116.31, vs_200d_ma: +127.6%, fwd_pe: 42.9, peg: 1.58,
fcf_yield: 0.98, rev_growth: 27.6%, earnings_growth: -80.4%, short: 4.7%, inst: 85.5%, rec_mean: 1.45,
analysts: 41, dd_from_52wh: -19.8%}`. Assembles the package, spawns 5 seats in parallel.

Seat verdicts:
- Fundamental: **FAIR** — fwd P/E 42.9, PEG 1.58, FCF yield 0.98% (rich); but rev +27.6% AI-driven. Thin
  margin of safety at this price.
- Technical: **SETUP_NAMED** — pullback off 52w high, holding well above rising 200d ($116). Trigger:
  daily close > $280 on above-avg volume. Stop: $245 (range low / 50d). Target $320, R:R ~2.4:1.
- Narrative: **MID_CYCLE** — custom-silicon / AI accelerator theme, broad participation, earnings
  confirming [source: https://www.ft.com/...]. Real beneficiary, not noise.
- Sentiment: **CROWDED** — rec_mean 1.45 across 41 analysts, inst 85.5% — little marginal buyer left.

Decision: Fundamental only FAIR (not ≥ GOOD) → fails the BUY gate → **WATCH**. Output a WATCH block: enter
$255–270 only if a daily close > $280 confirms; conviction 3/5 (CROWDED −1; MID_CYCLE neutral).
Invalidation: loss of the 200d trend or AI-capex guidance cut. Honest note: "this is a hypothesis — the
$280 trigger rule must clear strategy-discovery-backtest before risking capital."
</example>

---

## Self-check before printing the signal table

- [ ] The report **OPENS with the 2–3 sentence prose RECAP** (highest-confidence buy/sell to take now +
      one-line reasoning + the market narrative in one sentence) before any per-stock block or the signal table.
- [ ] Every FULL-PANEL ticker has `status='done'` in `stock_analysis`; one-line-screened names (N>12 triage)
      carry a one-line note and are listed, not dropped.
- [ ] Each stock block ends with a concrete **entry zone + bar-close trigger + market-based stop** — never a
      vague "looks good". WATCH/SKIP names what would change it.
- [ ] The technical seat **named a setup or said there is none**; no BUY without a live trigger.
- [ ] The narrative seat cited ≥2 real article URLs it **actually web_fetched or got from the feed scripts**
      (`feeds/wsj.ts`/`feeds/ft.ts`).
- [ ] **Inline citations:** every material news/market claim in the report body carries `[source: https://url
      (date)]` immediately after the claim — not appendix-only (the SOURCES appendix is in addition, not
      instead). Any claim without an inline source was removed or marked "(unverified)".
- [ ] **Macro regime paragraph** is present at the top of the report (Step 0.9) — 5 sentences, each with a
      named source and dateable fact; not from memory.
- [ ] **Portfolio-synthesis seat output** is present (Step 4) — factor correlation map, over-diversification
      critique, cross-position conflicts, portfolio structure verdict, cash deployment priority.
- [ ] Themes and constituents were **discovered live this run** (or the user supplied the list) — none
      asserted from memory.
- [ ] The honest base-rate note is present: single names are satellites, index is the bar; passing panels are
      hypotheses to be backtested in `strategy-discovery-backtest`.
- [ ] A TradingView screenshot is embedded inline per stock — UNLESS DEGRADED_TECH mode, where screenshots
      are skipped and each block is tagged DEGRADED.
- [ ] The smart-money seat cited ≥1 real filing/trade URL it actually web_fetched (openinsider, 13f.info,
      EDGAR, capitoltrades), or returned `NEUTRAL — INSUFFICIENT DATA`; no filing is fabricated.
- [ ] Portfolio sizing/concentration was deferred to `stock-chair`; ETF allocation to
      `tradfi-portfolio-manager`. This skill stayed on individual-stock entries only.
- [ ] recall.ts `source` was checked; if `grep-fallback`, the run is tagged MEMORY_DEGRADED and recalled
      stances flagged low-confidence.
- [ ] A consolidated **SOURCES & DATA** appendix is printed (Step 3.5) listing every web_fetched news/filing
      URL, every feed-script record, and the market-data provenance — required in normal AND DEGRADED mode.
- [ ] A final **RECAP (high-confidence only)** + **SETUP ALERTS** table is printed (Step 3.6); high-conviction-
      now and buy-on-condition names are split, never duplicated; if nothing clears the bar, that is stated.
- [ ] **Skeptic ran on every ticker** (Step 2) — no ticker skipped the adversarial challenge, even when all 5
      analysts agreed. Skeptic JSON cached at `$RUN_DIR/{TICKER}/seat_skeptic.json`.
- [ ] **CIO Synthesis ran after Skeptic** (Step 2.5) — final verdict came from the CIO prompt, not the old
      deterministic table. DISSENT LOGGED field is present in every output block (even when Skeptic was
      overruled). CIO JSON cached at `$RUN_DIR/{TICKER}/seat_cio.json`.
- [ ] **Risk Manager Check ran for every BUY/ADD verdict** (Step 2.7) — APPROVED or BLOCKED with reason in the
      output block. BUY/ADD verdicts without a Risk Manager result are invalid. Risk JSON at `seat_risk.json`.
- [ ] **Circle of Competence check passed** — the CIO stated the revenue model in 2 sentences before proceeding;
      PASS verdicts list "circle of competence: unclear" as the block reason, not a score.

## Set a buy-alert (notify-me-when) — for WATCH verdicts

A WATCH verdict ("good company, wrong price — buy near $X / when RSI < V") is when to register a durable
alert that pings the user **with your entry thesis** on trigger. Use the **`mkt`** skill — it carries the
reasoning into the notification (mkt's native message cannot). Register the entry plan as a job:

```bash
cd .agents/skills/mkt/scripts
bun mkt-alert.ts add --desk stocks --symbol NVDA \
  --condition below --value 142 \
  --reason "Buy-zone = prior breakout retest + 50d reclaim; add to core, not a new satellite." \
  --channel telegram:@CryptoAiInvestor --expiry 2026-09-30
# oversold add: --condition rsi_below --value 30 --period 14 --cooldown 21600
```

A scheduled `bun check.ts` (runtime cron) fires the notification with the reasoning when the zone/indicator
hits. See `.agents/skills/mkt/SKILL.md` for trigger patterns and the per-runtime scheduler cookbook.
Recommend-only and backtest-gated — an alert is a reminder to re-evaluate, not an order.

## Done when

- Each analyzed stock has a 5-seat panel → Skeptic challenge → CIO verdict → Risk Manager gate (if BUY/ADD),
  and a concrete entry plan (zone + trigger + stop + conviction + invalidation).
- The output block shows DISSENT LOGGED for every ticker (Skeptic's best objection, even when overruled).
- The signal table with the theme map is printed; every news claim is sourced inline.
- The SOURCES & DATA appendix (Step 3.5) lists all web_fetched URLs, feed-script records, and market-data
  provenance.
- The output is flagged as an educational, backtest-gated hypothesis — not advice.
- The high-confidence RECAP + SETUP ALERTS table (Step 3.6) is printed last, splitting immediate
  high-conviction actions from buy-on-condition names.
- If `.cache/stocks-advisor/notion.yaml` is configured, a dated Notion page (title `YYYY-MM-DD <narrative>`,
  Step 5) was created and its URL returned; if not configured, publishing was skipped silently (not an error).
</content>
</invoke>
