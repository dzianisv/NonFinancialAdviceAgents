---
name: stocks-advisor
description: "Portfolio-agnostic equity advisor. Analyzes a user-supplied ticker list, a Google Sheet of holdings, OR discovers stocks via current market themes (AI supply chain, robotics, energy transition, defense) found LIVE via read-news (scripts/read_news.ts, never a raw web_fetch of a publisher page). Runs a 6-seat analyst panel per stock (fundamental / technical / narrative-macro / sentiment-positioning / smart-money-institutional-flows / sell-side-analyst-consensus) in parallel subagents. When holdings are provided (Google Sheet URL), outputs HOLD/ADD/TRIM/EXIT per position with tax harvest table and cash deployment plan. When discovering or analyzing a watchlist, outputs entry zone, bar-close trigger, market-based stop, conviction, theme tag. Triggers: \"run the stock panel\", \"analyze these stocks: [list]\", \"review my portfolio\", \"find stocks in the AI supply chain theme\", \"find entry points for my watchlist\". Individual stocks only. Educational, not advice."
license: MIT
compatibility: opencode
metadata:
  audience: equity-allocators
  domain: equity-portfolio-management
  role: portfolio-manager
  source: "Architecture mirrors crypto-advisor (2026); seats grounded in analyse-fundamental + analyse-technical (Bernstein 2009)"
---

# Stocks Portfolio Manager

Analyze individual stocks **one at a time** → run a 6-seat analyst panel per stock → output a concrete
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
Reads positions (ticker, qty, cost basis) from the sheet, runs the 6-seat panel per position. Verdicts
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
3. **Sequential data pull, parallel analysis.** The six seats per stock share nothing — spawn them **in
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
7. **The panel is an investor panel, not a generic "research" step — this holds even when compressed.** If a
   run compresses the panel (one bundled agent per ticker instead of 6 parallel subagents), the bundled agent
   MUST still load and apply each named investor lens from `references/seat-prompts.md`
   (Fundamental=Buffett, Technical=Druckenmiller, Narrative=Alden, Cycle/Regime=Dalio, Smart-Money=flows,
   Sell-side=Street consensus) and label each seat line with its lens (§Output format per stock). A run whose
   output shows generic seat labels without lens names — or that skips loading the lens skills to save time —
   is non-compliant, not merely abbreviated.
8. **SELL ORIGINATION RULE — technicals may not originate or decide a sell.** See the full rule below. This
   is a hard constraint, not a preference. A TRIM or EXIT that cannot name a fundamentals / narrative /
   smart-money seat finding the thesis impaired, with stated evidence, is a defect — delete it and print
   WATCH instead.
9. **No script may emit a verdict.** `scripts/triage.py` ranks ATTENTION only (REVIEW_NOW / REVIEW /
   NO_ACTION). Verdicts come from the seats. The removed `scripts/scorecard.py` violated this and is now a
   hard-fail shim; if you see it invoked anywhere, that call site is stale.

---

## SELL ORIGINATION RULE (hard constraint — read before any TRIM/EXIT)

**Only a thesis seat may originate a sell.** A TRIM or EXIT is valid only if at least one of

| Seat | What counts as thesis impairment |
|---|---|
| **Fundamentals** (Buffett lens) | deteriorating unit economics, margin compression, EPS/FCF decline, balance-sheet stress, ROIC below cost of capital, accounting red flags |
| **Narrative / business** (Alden lens) | the reason you own it stopped being true — end-market gone, competitive moat breached, regulatory kill-shot, product/roadmap failure, management credibility loss |
| **Smart-money / flows** | insiders selling on Form 4 (open-market S, not 10b5-1 auto), a 13D/G exit, sustained short-interest build with a stated reason, sponsor/anchor distribution |

finds the thesis **impaired** AND states the evidence (a number, a filing, a URL, a dated event).

**Technicals may NOT originate or decide a sell.** Price is demoted to exactly two roles:

1. **Execution timing** — *after* a thesis seat has called impairment, the technical seat says when and how
   to exit (levels, liquidity, scale-out path). It answers "how", never "whether".
2. **A stated hard stop** — a pre-declared, pure risk-control level, printed as a number in advance. A stop
   firing is a risk action, not a thesis conclusion; it must be labeled as such.

**A technical break with no thesis impairment produces `WATCH` + an armed alert. Never a sell.** This is
what the old rule 3 got wrong: MRVL received a TRIM for being "expensive + in an uptrend" — a multiple and a
moving average, no seat, no evidence. That output was removed, not re-tuned.

**How this is enforced mechanically.** Every `triage.py` finding carries a `class` and a
`may_originate_sell` boolean:

```
class THESIS  → may_originate_sell: true  when FIRED  (fundamentals deterioration)
class PRICE   → may_originate_sell: false ALWAYS      (trend break, drawdown, RSI, valuation multiple)
class RISK    → may_originate_sell: false             (concentration → a SIZING action, not a thesis sell)
class DATA    → may_originate_sell: false             (integrity/missingness → escalates attention only)
```

`record["sell_origination_eligible"]` lists the codes that *could* support a sell. **If that list is empty,
no TRIM/EXIT may be printed for that name under any hierarchy, by any seat, for any reason** — the correct
output is WATCH plus an armed alert. And even when it is non-empty, triage has only established that a
thesis question exists; the seat must still do the work and state the evidence.

**Concentration is the one non-thesis reason to reduce**, and it must be labeled `TRIM (SIZING)` with the
weight number, never dressed up as a thesis call.

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

From the `analyse-fundamental` skill, on full-history backtests of the investable stock-selection methods
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
   Then widen breadth via [[read-news]]'s Bloomberg firehose feed and its discovery-only Google News adapter
   (Bloomberg/Reuters/Business Insider/CNBC/IBD) instead of a raw listing-page `web_fetch` — `read-news` is
   the sole fetch front door, so never `web_fetch` `bloomberg.com` or `finance.yahoo.com` listing pages directly:
   ```bash
   bun .agents/skills/read-news/scripts/read_news.ts --source bloomberg,googlenews --query "<theme>" --days 5
   ```
   A `googlenews` record is a discovery pointer only (`body` is always `null`) — it names a candidate theme/
   ticker to investigate further, it is never itself the citable T2 quote.
2. **Map names to themes.** Tag each candidate ticker with one bucket:
   `AI_SUPPLY_CHAIN | ROBOTICS | ENERGY | DEFENSE | FINTECH | HEALTHCARE | OTHER`. Buckets are a
   classification convention, not a fixed universe — add one if the evidence supports it.
3. **Anti-hallucination rule (same as the narrative seat):** name a theme or constituent only if you found it
   this run in feed-script/`read_news.ts` output you actually ran (`feeds/wsj.ts`/`feeds/ft.ts` print real
   URLs + verbatim teasers; `read_news.ts --source bloomberg,googlenews` prints real/discovery URLs — those
   count as fetched). No feed record = not a theme. Never list a "current narrative" from memory.

If the user supplies an explicit ticker list, skip discovery and analyze that list (still tag each name with
a theme in the output).

---

## Step 0 — Classify the request, then route (do this first)

Route BEFORE running any per-name panel. Do not run a full 6-seat panel on a question that is really an
allocation/deployment question.

| Intent (detect from the ask) | Route |
|---|---|
| "analyze these tickers / find entries / is now a good time to buy X" | This skill — per-name 6-seat panel (rest of this doc) |
| "review my portfolio" + holdings sheet | This skill per-name on the triaged subset → then hand to `stock-chair` for sizing/concentration |
| "deploy $X / what ETFs should I buy / which big-caps to avoid / sleeve allocation" | ALLOCATION question. Route to `tradfi-portfolio-manager` for the ETF/sleeve plan FIRST; use this skill only for the single-name satellite slice. Do NOT front-load a per-name panel. |

A portfolio review asking "what to buy/sell" is BOTH: triage the book here, but route the cash-deployment /
ETF-allocation answer to `tradfi-portfolio-manager` — do not improvise sleeve allocation here.

---

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

**Hard rule:** all fundamentals inputs/outputs and triage files live under `.cache/stocks-advisor/` —
never write into the skill's own `scripts/` directory. `fundamentals.py` input JSONs go under
`$RUN_DIR/{TICKER}/` (or any path under `.cache/stocks-advisor/`); its `--out-dir` flag must be passed (or
left at its default, `.cache/stocks-advisor/fundamentals/`) so `*.out.json` never lands next to the input
or inside `scripts/`.

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
│   ├── seat_sellside.json
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

   Write the input JSON under `$RUN_DIR`, never inside `scripts/`, and pass `--out-dir` so the output lands
   in `.cache/` too:
   ```bash
   mkdir -p "$RUN_DIR/$TICKER"
   echo "{\"symbol\":\"$TICKER\",\"period\":\"1y\"}" > "$RUN_DIR/$TICKER/fundamentals_input.json"
   python3 .agents/skills/stocks-advisor/scripts/fundamentals.py \
     "$RUN_DIR/$TICKER/fundamentals_input.json" \
     --out-dir ".cache/stocks-advisor/fundamentals/"
   # -> writes .cache/stocks-advisor/fundamentals/$TICKER.out.json (never scripts/$TICKER.json*)
   ```
2. **Rank by decision-relevance** from that screen: concentration weight (% of book), |unrealized P&L %|,
   cash-deploy candidate, proximity to a key level (near 50d/200d or a 52w extreme), or a fundamental/thesis
   break.
3. **Select the deep-dive subset** — the names that warrant a chart: the top decision-relevant names (default
   K ≈ 10) PLUS any name the screen flags (sitting on a trigger level, a TRIM/EXIT candidate, a deploy
   target). Everything else stays fundamentals-only.
4. **Run TradingView (Step 1.5, sequential single slot) + the full 6-seat panel ONLY on the deep-dive
   subset.** Every other name gets its verdict from the fundamentals screen alone (HOLD/TRIM/EXIT, or WATCH
   for a watchlist) — no TradingView, no 6 seats.
5. If TradingView is down (DEGRADED_TECH, Step 0.7), the deep-dive subset also falls back to
   fundamentals-only — the whole book is screen-level, nothing blocks.
6. State explicitly which names got the TradingView deep dive vs the fundamentals-only screen, and the K
   used. Never silently drop a name.

---

## Step 0.82 — Triage: rank ATTENTION over the whole book (MANDATORY — this step emits NO verdicts)

**What changed and why (2026-07-24).** This step used to run `scripts/scorecard.py`, a static rule tree that
printed an ACTION (HOLD/TRIM/EXIT/ADD/WAIT). That design failed twice on the same ticker and both failures
were structural, not tuning problems:

- **NEM — an unreachable state.** NEM was a +119% winner trading below BOTH its 50d and 200d. Rule 0.5
  (exhaustion HOLD) required `RSI < 40`; NEM's RSI was **47.9**. Rule 0.7 (early trend-break TRIM) required
  `dd > −25%`; NEM's drawdown was **−29.6%**. It matched neither, fell through to rule 4, and the script
  confidently printed **WAIT — "do nothing."** The entire quadrant `{dd ≤ −25% AND RSI ≥ 40}` had *no*
  trend-break coverage at all. A rule tree with windowed guards is partial by construction; widening a
  threshold would have moved the hole, not closed it.
- **MRVL — a technical sell.** Rule 3 printed **TRIM** for "expensive + uptrend" — a multiple and a moving
  average. No seat asked for it, no thesis was impaired, no evidence was stated.

Both are the same root cause: **a script was making investment decisions.** The fix is not a better tree.
The fix is that the script stops deciding.

**The script's ONLY job now** is to guarantee that *every* position gets screened, and to rank which ones
deserve a full analyst panel. Its output vocabulary is exactly three tokens:

| Level | Meaning | What you do |
|---|---|---|
| **REVIEW_NOW** | material position with an open question | run the full seat panel this run — non-negotiable |
| **REVIEW** | an open item exists but not at a size that demands a panel today | note it; panel if capacity allows |
| **NO_ACTION** | every check evaluated and CLEAR (or fired but informational at this position size, and *named* in the basis) | nothing owed |

**There is no HOLD, TRIM, EXIT, ADD, BUY, SELL or WAIT in this step's output.** If you see one, the run is
non-compliant. Verdicts come from the seats (§Step 2), bounded by the §SELL ORIGINATION RULE.

```bash
# positions.csv columns: Position,MarketValue,Unrealized_PnL  (ticker + MV used; MV gives concentration weights)
# Target defaults to .cache/stocks-advisor/fundamentals/ (where fundamentals.py wrote its *.out.json files
# in Step 0.8); --out-dir defaults to .cache/stocks-advisor/ for _triage.json. Both stay out of scripts/.
python3 .agents/skills/stocks-advisor/scripts/triage.py .cache/stocks-advisor/fundamentals/ --positions <positions.csv>
```

### Totality — the anti-unreachable-state design

There is **no decision tree and no first-match-wins ordering.** Every check in `CHECKS` runs on every name,
independently, and each returns **exactly one** finding with status `FIRED | CLEAR | MISSING`. Therefore:

- `len(record["findings"]) == len(CHECKS)` for every possible input. `scripts/test_triage.py` proves this by
  enumerating the (drawdown × RSI × vs200 × vs50 × quote_type × position-context) grid — **97,020 inputs,
  0 silent defaults.**
- `NO_ACTION` is **not a fall-through.** It is emitted only when every check explicitly cleared, and the
  basis string states how many checks were evaluated to get there.
- The specific NEM hole is a named regression test: `test_old_scorecard_gap_is_now_covered` re-implements the
  old rule 0.5 / 0.7 predicates, collects every grid input matching **neither** (79 of them), and asserts each
  now surfaces as **REVIEW_NOW** with `TREND_BREAK_200D` FIRED. `check_trend_break_200d` fires on **any**
  `vs_200d_ma < 0` — there is no drawdown window and no RSI window on it, so the hole cannot reopen.

### The checks (all 12 run on every name, always)

| Code | Class | Fires when | May originate a sell? |
|---|---|---|---|
| `PRICE_INTEGRITY` | DATA | price absent/zero — the name was **not** screened | no |
| `UPSTREAM_DATA_ERROR` | DATA | `fundamentals.py` recorded a fetch exception for this name — the null is a *broken fetch*, not a real absence of the value | no |
| `NO_FUNDAMENTAL_BASIS` | DATA | `quote_type` is ETF/MUTUALFUND/INDEX/… — no company fundamentals exist, so route the own/trim call to `tradfi-portfolio-manager` / `analyse-macro`, never to a chart read | no |
| `CONCENTRATION` | RISK | weight ≥ 15% of book | no — a **SIZING** action, label it `TRIM (SIZING)` |
| `TREND_BREAK_200D` | PRICE | below the 200d, **at any drawdown, at any RSI** | **no** |
| `TREND_BREAK_50D` | PRICE | below the 50d | **no** |
| `DRAWDOWN` | PRICE | drawdown from 52w high past the band thresholds | **no** |
| `MOMENTUM_STATE` | PRICE | RSI washed out or extended | **no** |
| `THESIS_DETERIORATION` | **THESIS** | declining EPS / shrinking revenue / margin compression | **YES — routes to the fundamentals seat to adjudicate** |
| `VALUATION_STRETCH` | PRICE | multiple/FCF-yield stretched | **no** (this is the removed rule 3) |
| `SHORT_INTEREST` | DATA | short % of float elevated | no — routes to smart-money |
| `EVENT_SOON` | DATA | earnings inside the window | no |

Only `THESIS_DETERIORATION` is THESIS-class, so it is the only finding that can put a name on the
sell-origination path — and even then triage has established only that *a question exists*. The seat must do
the work and state the evidence. See §SELL ORIGINATION RULE.

### Missing inputs may never be absorbed into a default

The old file's `if fy is None: return 0, "valuation: no FCF data (neutral)"` is **banned**. A missing input
now produces `status=MISSING`, **names the absent field**, and **raises** attention. Concretely:

- A name whose `.out.json` is unreadable or contains an error → `REVIEW_NOW`, not skipped. (The old script
  did `continue` on these; on 2026-07-24 that silently dropped **38 of 83** cached names, including SNDK.)
- A held position with **no screen output at all** → a synthetic `REVIEW_NOW` record reading *"HELD POSITION
  WITH NO SCREEN OUTPUT — it was NOT screened this run; this is not 'nothing to do'."* The old script simply
  never mentioned those names. On 2026-07-24 there were **6** of them.
- A position whose MarketValue/PnL will not parse → relevance `UNKNOWN`, which **escalates**. It is a data
  failure, not a small position, and must never be graded down as one.
- `positions.csv` parse errors are collected and printed, never swallowed by a bare `except`.

Check the run's `data MISSING` count. If it is non-trivial, **re-run `fundamentals.py` before running the
panel** — a panel over a book that was two-thirds unscreened is theatre.

### Relevance grades urgency; it can never grade a finding out of existence

Position size and locked-in gain decide *how loud* a finding is, never *whether it is reported*. The worst
grading can do is move `REVIEW_NOW → REVIEW` on a small position, and a floor protects the checks that must
never be quiet: `TREND_BREAK_200D`, `THESIS_DETERIORATION`, `CONCENTRATION`, `PRICE_INTEGRITY`. A FIRED
finding graded to informational is still listed in `record["fired"]`, in `record["informational"]`, and by
name in the basis string. Nothing vanishes.

### What Step 0.82 hands to the seats

For every name: `attention`, `basis`, the full `findings` array, `sell_origination_eligible`, and
`route_to_seats`. Run the panel on the REVIEW_NOW set. Print the ATTENTION level and BASIS verbatim in each
output block **alongside** the seat verdict — they are different things and must never be conflated.

`risk-desk` (`.agents/skills/risk-desk/`) still runs the standing risk layer over HELD positions; it is a
sizing/stop authority and its breaches are RISK-class actions, subject to the same labeling rule.

---

## Smart-money data path (MANDATORY — this seat may originate a sell, so its plumbing must work)

**The 2026-07-24 failure.** The smart-money seat returned `INSUFFICIENT_DATA` on every name — not because
the flows were ambiguous, but because **nothing was fetched.** The seat pointed at finviz (301s) and
openinsider (403 since 2026-07-05), found neither, and quietly abstained. The panel silently lost a vote and
nothing in the output revealed it. That is not survivable now that this is one of only three seats that may
originate a sell.

**Always run the fetcher first** — before any web_fetch, for every name going to the panel:

```bash
python3 .agents/skills/stocks-advisor/scripts/smartmoney.py {TICKER} --days 120 --json
```

It resolves the CIK from SEC `company_tickers.json`, pulls every Form 4 in the window from the EDGAR
submissions API, parses the **raw** XML for open-market P/S transactions, runs an EDGAR full-text search for
SC 13D/13G, and computes today's exact 13F staleness. Every source returns `OK | NO_DATA | MISSING(reason)`.

> Note for anyone extending it: EDGAR's `primaryDocument` for a Form 4 is the **XSL-rendered HTML** view
> (`xslF345X06/form4.xml`). Fetching that path returns HTML with zero `<nonDerivativeTransaction>` elements,
> which parses to "no insider activity" — a false negative on a sell-originating seat. The script strips the
> `xsl*/` prefix and asserts the body actually looks like Form 4 XML before parsing.

### Source priority — LOW LAG FIRST. State the lag out loud.

| Rank | Source | Lag | Role |
|---|---|---|---|
| 1 | **Form 4** insider transactions | **T+2 business days** | PRIMARY — deciding |
| 2 | **13D / 13G** activist & 5% stakes | 13D T+5d; 13G varies | deciding |
| 3 | **Short-interest CHANGE** | twice monthly, ~T+8d | supporting |
| 4 | **Options flow / dark-pool** prints | near real-time | supporting — name the venue |
| 5 | **13F** institutional holdings | **45 DAYS MINIMUM** | corroboration only |

### The 13F rule (hard)

**13F is due 45 calendar days after quarter end.** As of 2026-07-24 the newest FILED quarter is Q1'26
(period ended 2026-03-31). **Q2'26 is NOT filed — it is due ~2026-08-14.** A 13F read today therefore
describes positions **at least ~115 days old** that may have been fully unwound.

- 13F may **CORROBORATE** a low-lag signal. It may **NEVER substitute** for one.
- Never describe 13F holdings as "current", "recent" or "latest" positioning.
- **Never originate a sell from 13F.** A 45-day-stale, long-only snapshot cannot establish that a thesis is
  impaired today.
- Print the staleness number the script computed, verbatim, whenever 13F is cited.

### 10b5-1 vs open-market — the distinction that decides a sell

A pre-scheduled **10b5-1** sale carries almost no thesis information: it was set months earlier, usually for
diversification or taxes. A discretionary **open-market** sale by a named officer is real evidence. The
script tags each transaction. **Never cite a 10b5-1 sale as evidence of thesis impairment.**

Worked example, 2026-07-24: NEM showed 7 insider sells — **all 10b5-1, zero open-market** → weak, does not
support a sell. MRVL showed 1 officer open-market sale of **$632,272** plus 6 scheduled → that single
open-market line is the only one that could support a TRIM, and only alongside a stated thesis.

### Missing is named, never silent

If a source is unreachable, the seat reports it **by name with the reason**. It may not abstain, and it may
not fold the failure into a generic `INSUFFICIENT_DATA`. Known-dead sources — report MISSING and move on,
do not stall: `finviz.com` (301/blocked), `openinsider.com` (403 since 2026-07-05).

SEC fair-access requires a User-Agent of the literal form `<name> <email>`; a browser UA and a parenthetical
`tool/1.0 (contact ...)` form are **both** rejected with HTTP 403. Override via the `SEC_UA` env var.

### A partial read is not a clean read

Same rule one level down: an *incomplete* source must not present as a *complete* one. `smartmoney.py`
reports `complete`, `filings_seen`, `filings_examined`, `filings_failed`, and prints `[OK/PARTIAL]` when
they disagree; `dollar_totals_complete` is false whenever some transaction had unparseable share/price
fields, which makes every dollar figure a **floor**, not a total. The seat must state PARTIAL in its verdict
line and drop CONVICTION one step.

Why: on 2026-07-24 the fetcher capped at the newest 25 Form 4s. MRVL had filed **43** in the window, so the
seat saw **1** open-market officer sale (**$632,272**) and reported a confident `OK`. The full read is **5**
sales totalling **$4,639,734** — a materially different evidence picture on a seat that is allowed to
originate a sell. The cap is now `MAX_FORM4_FETCH = 100` and any truncation that still bites is named in
`reason` and flips `complete` to false.

---

## Step 2 — Decision Hierarchy (pluggable)

The decision chain (how per-stock panel verdicts get turned into a final call) is **pluggable** — load the appropriate module based on the user's `--hierarchy` flag:

```bash
HIERARCHY="${HIERARCHY_FLAG:-panel}"   # default: panel (flipped from bsc round 4, 2026-07-09 — see hierarchy table below)
HIERARCHY_FILE=".agents/skills/stocks-advisor/references/hierarchies/${HIERARCHY}.md"
if [[ ! -f "$HIERARCHY_FILE" ]]; then
  echo "Unknown hierarchy: $HIERARCHY. Available: bsc, bridgewater, berkshire, citadel, millennium, point72, soros, panel"
  exit 1
fi
# Load and follow the steps in $HIERARCHY_FILE — they replace Steps 2–2.7 entirely
cat "$HIERARCHY_FILE"
```

Available hierarchies (see `references/hierarchies/`). Scores from blind eval on 85-position IBKR portfolio ($578k equity, COIN 21.5%):

| Name | Key mechanism | Eval score | Best for |
|---|---|---|---|
| `panel` (default, since round 4 — 2026-07-09) | Research desk briefing → 6 independent investor votes → conviction-weighted quorum; the quorum ORIGINATES the verdict, bounded by the SELL ORIGINATION RULE | **Pairwise winner, rounds 3+4** — not a /25 pointwise score; see caveat below. R3 patched-panel: 3–2 count AND panel margin 52.6–47.4 (modest, one win prompt-confounded). R4 (same 5 tickers, confound closed, 3-judge-majority upgrade, 15 judge votes): panel again 3–2 count, margin 53.05–46.95, 86.7% inter-judge agreement. Two consecutive rounds replicate within ~1pt of each other under different judge conditions — real, reproducible edge, not noise. Known open issue: mechanical conviction-boost rule miscalibrates HOLD confidence direction (patch-next, did not cost the round). | Full portfolio reviews and standard equity analysis — new default; named-investor-lens transparency, auditable per-seat OWN/TODAY votes, best-in-class dissent preservation |
| `bsc` (prior default, demoted round 4) | Edge Gate + Skeptic [MEM audit] + P0/P1/P2/P3 | **25/25** (original pointwise eval); lost pairwise rounds 3 and 4 to `panel` on both count and margin | Still fully available via `--hierarchy bsc` — broad coverage, strong Edge Gate/Skeptic audit trail |
| `bridgewater` | Skeptic → CIO → Risk Manager | 23/25 | Standard equity analysis — strong adversarialism without edge gate overhead |
| `soros` | Macro thesis → Reflexivity → P0/P1/P2/P3 | 21/25 | Macro-driven positions where regime is the primary driver |
| `berkshire` | Circle of Competence → Moat → Munger → Margin of Safety | 20/25 | Long-term concentrated conviction positions only |
| `millennium` | PM thesis → Auto Hard Stop (Kelly-based, no override) | 20/25 | Risk-first portfolio triage — automated de-risking on breach |
| `citadel` | Pod PM → Central Risk (bidirectional, no PM recourse) → Griffin | 19/25 | Multi-strategy books with strict factor concentration limits |
| `point72` | Edge Gate → Conviction → Cohen Seat | 19/25 | Idea-generation / new positions with strong edge hypothesis |
| `tiger` (reference-only — file not shipped; scored worst, use discouraged) | Variant perception → Adversarial pitch → Robertson sole authority | 15/25 | Concentrated 15–20 name long/short books only — not suitable for diversified portfolios |

Eval-score caveat: the original /25 pointwise rubric's authorship was never verified as independent — treat
those numbers as indicative only. **Re-eval done 2026-07-08** (independently-authored rubric, frozen identical
inputs, blind pairwise, 6 judges): **bsc 4–0 · millennium 2–2 · bridgewater 0–4** — confirmed `bsc` as default
at the time; note millennium beat bridgewater head-to-head twice, flipping the old #2. Caveats: n=2 WAIT-type
tickers, same-model-family judges. Full results:
`.cache/stocks-advisor/eval/RESULTS-2026-07-08-hierarchy-pairwise.md`.

**Default flipped bsc → panel after round 4 (2026-07-09).** `panel`'s score above is a pairwise win-rate
result (head-to-head count + average weighted margin across two independent rounds), not a /25 pointwise
score — it is not directly comparable to the other rows' numbers, only to `bsc`'s round 3/4 pairwise results.
See `.cache/stocks-advisor/eval/round4/RESULTS-round4-bsc-vs-panel.md` and
`.cache/stocks-advisor/eval/round3/RESULTS-round3-bsc-vs-panel.md` for full reasoning, and
`ai-evaluate/SKILL.md`'s History section for the round-by-round summary.

**Invoking with a specific hierarchy:**
```
Run stocks-advisor with --hierarchy berkshire on: AAPL, KO, AXP
```
or for portfolio review:
```
Review my portfolio [sheet URL] using --hierarchy bsc
```

**Eval protocol** (how hierarchies are compared — blind pairwise, judge prompt, anti-self-grading): `../ai-evaluate/SKILL.md`.

**Invoking the comparison mode** (runs all hierarchies on the same input, blind-scored):
```
Compare hierarchies on: AAPL, KO — use all
```
→ Routes to the `hierarchy-compare-workflow` (see `.claude/workflows/hierarchy-compare-workflow.js`).

After loading $HIERARCHY_FILE, follow its steps exactly. The file contains the full decision chain (subagent prompts, output shapes, hard constraints). Do not improvise or mix steps from different hierarchies.

---

## Output format per stock

> **TOP RECAP rule (MANDATORY — chat output AND Notion page).** Every run's report OPENS with a 2–3 sentence
> prose RECAP, before any per-stock block or the signal table, stating in plain English: (a) the
> highest-confidence BUY/SELL actions to take now, each with one-line reasoning; (b) the current market
> narrative in one sentence. This is a prose TL;DR — **distinct** from the Step 3.6 RECAP *table* at the end.

> **Recap style rules (mandatory — every seat line, chat output AND Notion page):**
> - **No provenance-as-content.** When a run doesn't re-verify every seat for every ticker (e.g. a same-day
>   rerun, or a caller-supplied `prior_context` carrying forward an earlier panel) and a seat's verdict is
>   reused rather than freshly analyzed, print that seat's **actual finding** (the metric/fact) in the SEAT
>   VERDICTS line below — never `"carried from MM-DD"` or `"no data this run"` as the line itself. Append a
>   compact `(as of MM-DD)` staleness tag at the end of the line instead; the tag is metadata, not content.
>   If a seat returned `INSUFFICIENT_DATA` with no prior verdict to fall back on, omit that seat's line from
>   the SEAT VERDICTS block below (it still belongs, explicitly, in the Step 3.5 SOURCES appendix — that's
>   the audit-trail surface, a different purpose) and fold it into one line at the end of the stock's block:
>   `⚠️ dark: {Seat, Seat — reason}`.
> - **Action-first, grouped by urgency — not a ticker-ordered stream.** The TOP RECAP prose above and the
>   Step 3.6 RECAP + SETUP ALERTS + EXECUTION TABLE (P0→P3) already satisfy this; keep leading every report
>   with them and do not bury BUY/SELL actions inside the per-stock blocks below.

```
═══════════════════════════════════════════════════════
 {TICKER} — {COMPANY} — {DATE}
 Theme: {AI_SUPPLY_CHAIN | ROBOTICS | ENERGY | DEFENSE | FINTECH | HEALTHCARE | OTHER}
 Theme phase: {EARLY_CYCLE | MID_CYCLE | LATE_CYCLE | FADING}
═══════════════════════════════════════════════════════
 SEAT VERDICTS (each line names the investor lens applied — see references/seat-prompts.md)
 Fundamental — Buffett lens     : {STRONG/GOOD/FAIR/POOR} — {one line: key metric}
 Technical — Druckenmiller lens : {SETUP_NAMED/NO_SETUP/BROKEN} — {setup name or "no trigger"}
 Narrative — Alden lens         : {EARLY/MID/LATE/FADING} — {one line: why}
 Cycle/Regime — Dalio lens      : {QUIET_ACCUM/NEUTRAL/CROWDED/EXTREME} — {one line}
 Smart-Money — flows            : {ACCUMULATING/DISTRIBUTING/NEUTRAL} — {CONVICTION: HIGH/MED/LOW | one line: key signal}
 Sell-side — Street consensus   : {BULLISH/NEUTRAL/BEARISH} — {consensus_rating, N analysts, PT $mean (upside %), dispersion, momentum}
 Skeptic — Hunt lens            : {SKIP/WATCH/BUY} — {one line: strongest objection}

 CIO DECISION: {BUY / WATCH / SKIP / PASS}   (or ADD / HOLD / TRIM / EXIT on holdings path)
 Timing      : {EVENT_SOON — earnings in {days}d ({date}); stage {ACTION} after print | N/A}
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
2. **Smart-money / filing sources** — the `scripts/smartmoney.py` JSON plus every URL the seat additionally
   web_fetched. Print each source with its STATUS and its LAG (see §Smart-money data path). A source that
   was unreachable is listed **by name with the reason** (`Form 4: MISSING (EDGAR HTTP 503)`) — never
   omitted and never collapsed into a bare `INSUFFICIENT_DATA`. The 13F staleness line is mandatory whenever
   13F is cited at all. Retail crowd positioning (explicitly a WEAK signal — retail crowding, not
   institutional flow): call `python3 scripts/robinhood_top100.py --ticker TICKER` to check whether the name
   is in Robinhood's current Top-100-Most-Popular list; treat an `INSUFFICIENT_DATA` result as *absent* (not
   "no" and not an error to surface loudly), and never invent/fabricate a rank the script didn't return. One
   per line.
3. **Sell-side / analyst-consensus sources** — every analyst-page URL the sell-side seat actually
   web_fetched (Yahoo Finance analysis tab, StockAnalysis.com forecast, TipRanks, MarketBeat, Zacks,
   Morningstar, Nasdaq analyst-research, Finviz, WSJ research-ratings). One per line. If the seat returned
   `INSUFFICIENT_DATA`, list it here explicitly rather than omitting it.
4. **Market-data provenance** — state the origin of prices/indicators/fundamentals: `fundamentals.py
   (yfinance) per ticker: {tickers run}` and `Technicals: TradingView studies RSI/BB/MACD/Volume` (or, in
   DEGRADED_TECH mode: `Technicals: DEGRADED — MA levels from fundamentals.py only, no TradingView`).
5. If any seat returned `INSUFFICIENT DATA`, list it here explicitly rather than omitting it.

Format:
```
SOURCES & DATA — {DATE}
News ({n}):
  [T1] https://... (date) — "verbatim teaser"
  ...
Filings/flows ({n}):
  https://...
Sell-side / analyst pages ({n}):
  https://... (date) — "verbatim figure or quote"
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

**SETUP ALERTS — buy/sell only when a condition fires. These are AUTO-REGISTERED, not offered.** Every
WATCH/WAIT name with a *defined, falsifiable* trigger (a price reclaim, a level, an indicator like RSI, or a
dated earnings catalyst) goes here — not as a buy-now. State the exact condition and the action it unlocks.
The watch **is the deliverable**: after the per-name verdicts, the skill immediately wires each one so the
user gets pinged when the trigger fires — no manual "want me to set this up?" step. Do NOT stop at printing
the table; the table is a *receipt* of what was armed.

**Precision over recall (mandatory guard).** Only auto-register a WATCH/WAIT that has a CONCRETE, falsifiable
trigger. A WATCH with no defined trigger ("looks interesting, keep an eye on it") is **NOT armed** — list it
in the report as "no trigger, not armed" rather than spamming a meaningless alert. Alert fatigue is the
failure mode; precision beats recall. Every armed alert carries the **conviction grade** and the **thesis
text** in its `--reason`.

**Trigger-TYPE routing (the important nuance — a price alert cannot judge a semantic condition):**
- **Mechanical trigger** — a price reclaim, a level break, an RSI/MA/MACD condition → register a
  `mkt-alert.ts` price/indicator alert (`above`/`below`/`sma_cross_above`/`sma_cross_below`/`rsi_below` etc.,
  with `--data-source` for any `above`/`below` price level as mkt requires). Example: NBIS "reclaims 50d MA"
  → `--condition sma_cross_above --value 50 --period 50`. See *Set a buy-alert*.
- **Event / semantic trigger** — a WAIT-for-earnings condition that a number cannot decide ("beats AND holds",
  "organic reaccelerates", "guide raised") → a price alert CANNOT evaluate this. Register it as a **scheduled
  re-evaluation** dated to the day after the print: schedule (or emit a ready-to-run spec for) a re-run of
  `stocks-advisor` on that ticker. This routes to a Claude Code **scheduled routine / the mkt-daemon**, NOT a
  price threshold — because judging "did it beat and hold" needs re-running the panel, not comparing one
  number. Never encode a semantic condition as a dumb price level. See *Schedule an event re-eval*.

```
SETUP ALERTS ({DATE})
Asset   Trigger (exact)                 Type        Then do        Armed via                    Thesis (one line)
-----   ---------------                 ----        -------        ---------                    -----------------
{TICK}  close > ${level} (reclaim)      mechanical  BUY {zone}     mkt-alert.ts sma_cross_above {≤12-word reason}
{TICK}  RSI(14) < 30 / pullback ${lvl}  mechanical  ADD            mkt-alert.ts rsi_below       {≤12-word reason}
{TICK}  beats & holds after {earn date} event       RE-EVAL        scheduled re-eval {date+1}   {≤12-word reason}
{TICK}  (no defined trigger)            —           —              NOT ARMED                    watch only, no ping
...
```

A name is in RECAP **or** SETUP ALERTS, never both — high-confidence-now and buy-on-condition are mutually
exclusive. Auto-registration runs in BOTH normal and DEGRADED_TECH mode; in DEGRADED mode the mechanical
conditions are MA/price levels (no live bar-close trigger). After wiring, print the **ALERTS ARMED** summary
(below) reporting what was registered — do not ask permission first.

**ALERTS ARMED — report what was wired (print immediately after SETUP ALERTS).** This is the confirmation the
watches exist, so the user never has to run a manual step:

```
ALERTS ARMED ({DATE})
Ticker  Mechanism                       Trigger                       Channel                  Conviction  Status
------  ---------                       -------                       -------                  ----------  ------
{TICK}  mkt-alert.ts (price/indicator)  sma_cross_above 50d           telegram:@...            4/5         ARMED
{TICK}  scheduled re-eval (mkt-daemon)  re-run panel {date+1}         claude-code routine      3/5         SCHEDULED
{TICK}  —                               no defined trigger            —                        2/5         NOT ARMED (why)
```

**EXECUTION TABLE — P0/P1/P2/P3 (Soros format — cross-portfolio priority, runs after SETUP ALERTS)**

Rank all BUY/ADD/EXIT/TRIM verdicts by portfolio urgency, with exact share counts and triggers. This is the
actionable to-do list — one row per decision, ordered from most-urgent to watchlist:

```
EXECUTION TABLE ({DATE})
Priority  Ticker  Action    Shares  Entry zone    Trigger                  Port %   Falsification
--------  ------  ------    ------  ----------    -------                  ------   -------------
P0        {TICK}  EXIT      all     market open   immediately — thesis broken (state the break)
P1        {TICK}  ADD       N shr   $X–$Y         close > $Z on D ({date})   +X%    {specific condition that kills the add}
P2        {TICK}  ADD       N shr   $X–$Y         pullback to $W + RSI<40    +X%    {specific condition}
P3        {TICK}  WATCH     —       —             RSI<30 / close > $Z        —      {alert registered via mkt}
```

Priority tiers:
- **P0** — act at open, no conditions. Triggered by a thesis break already confirmed (disclosed earnings miss, management departure, position limit breach). No P0 without a named trigger already fired.
- **P1** — act this week if trigger fires. Conviction ≥ 4/5, setup named, Risk Manager APPROVED.
- **P2** — act this quarter if condition met. Conviction 3/5, waiting for a cleaner entry level.
- **P3** — watchlist, alert registered via `mkt` skill. Conviction ≤ 2/5 or condition is multi-week away.

**Share count rule:** use Risk Manager's APPROVED size ($amount) ÷ entry_high. Round to nearest 5 shares. State the dollar amount alongside the share count.

> Source: Soros/Druckenmiller Quantum Fund operating model — explicit P0/P1/P2/P3 execution table forces ranking of actions by urgency; prevents the common failure mode where all BUY signals are treated as equally urgent and nothing gets executed. Adding to winners (P1 = market confirms thesis) is systematic, not discretionary. Bridgewater All Weather allocation principle: cash deployment priority is determined by portfolio-level fit (fills a gap, reduces concentration) rather than ticker-level conviction alone.

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

## Step 5.5 — Reasoning diagram (MANDATORY when a report was produced; DELEGATE to one subagent)

After the report exists (and the Notion page, if configured, is created), attach a **mermaid diagram of how
the run reached its conclusions** — the decision flow the reader can audit: data inputs → triage ATTENTION
level → per-seat evidence → skeptic/dissent → originating seat → final verdict + flip-trigger, per ticker.

**Delegate the WHOLE step to ONE subagent** (`/model sonnet`) — never build the diagram in the main
orchestrator context (it re-reads the full report and would bloat the main context). The subagent:

1. Reads `$RUN_DIR/report.md` (or the saved `.cache/stocks-advisor/research/<title>.md`) and
   `$RUN_DIR/_triage.json`.
2. Writes `$RUN_DIR/reasoning_diagram.mmd` — a mermaid `flowchart TD` with:
   - one subgraph per ticker containing **the full panel as desks**: one node per seat that ran, named
     by its investor lens per `references/seat-prompts.md` — e.g. `Buffett desk (Fundamental)`,
     `Druckenmiller desk (Technical)`, `Alden desk (Narrative)`, `Dalio desk (Cycle/Regime)`,
     `Smart-Money desk (flows)`, `Sell-side desk (Street consensus)` — each carrying its seat
     verdict + the key number it contributed ("Smart-$: CEO bought $1M — ACCUMULATING"), flowing into the
     **Hunt desk / Skeptic** (strongest objection) → **CIO decision node** (the quorum verdict + which seat
     ORIGINATED it — for any TRIM/EXIT the diagram MUST name the fundamentals / narrative / smart-money seat
     that found the thesis impaired, and the evidence; a sell node with no originating thesis seat is a
     defect in the run, not a drawing choice) → DISSENT node when a seat disagreed (name the seat, show it
     was overruled) → final verdict node with the flip-to-ADD/BUY trigger. The panel structure must be visible
     as a panel — seats are desks in a deliberation, not a flat evidence list;
   - a shared top node for the run inputs (fundamentals.py / TradingView / triage ATTENTION) and a shared bottom
     node for the report outputs;
   - seat nodes carry the load-bearing evidence ("div 6.65%, 127y streak", "insiders sold @62"), so the
     diagram answers *"why this verdict and who argued what"*, not just *"what ran"*;
   - if the run compressed seats (bundled panel agent), still draw the seats individually — they each
     produced a verdict line — and note the compression in a caption node.
3. Renders it: `npx --yes @mermaid-js/mermaid-cli -i reasoning_diagram.mmd -o reasoning_diagram.png -b transparent -w 1600`
   (mermaid-cli is available via npx; on render failure keep the .mmd and continue — the code block still
   publishes).
4. Appends a `## Reasoning diagram` section to the report .md containing the fenced ```mermaid code block.
5. If a Notion page was created this run: appends the same fenced mermaid block to that page
   (`notion-update-page`; Notion renders mermaid natively). Loads the tool itself via ToolSearch.
6. Returns ONLY: the .mmd/.png paths and "Notion updated: yes/no" — never the diagram source (context bloat).

The orchestrator then sends `reasoning_diagram.png` to the user alongside the report link. On any failure in
this step, report it and continue — the diagram never fails the run.

---

## Worked example (one stock)

<example>
User: "Run stocks-advisor on MRVL."

Orchestrator (sequential): resolves `NASDAQ:MRVL`; pulls D/W OHLCV + RSI/BB/MACD/Volume + screenshot;
runs `fundamentals.py` → `{price: 264.71, ma200: 116.31, vs_200d_ma: +127.6%, fwd_pe: 42.9, peg: 1.58,
fcf_yield: 0.98, rev_growth: 27.6%, earnings_growth: -80.4%, short: 4.7%, inst: 85.5%, rec_mean: 1.45,
analysts: 41, dd_from_52wh: -19.8%}`. Assembles the package, spawns 6 seats in parallel.

Seat verdicts:
- Fundamental — Buffett lens: **FAIR** — fwd P/E 42.9, PEG 1.58, FCF yield 0.98% (rich); but rev +27.6% AI-driven. Thin
  margin of safety at this price.
- Technical — Druckenmiller lens: **SETUP_NAMED** — pullback off 52w high, holding well above rising 200d ($116). Trigger:
  daily close > $280 on above-avg volume. Stop: $245 (range low / 50d). Target $320, R:R ~2.4:1.
- Narrative — Alden lens: **MID_CYCLE** — custom-silicon / AI accelerator theme, broad participation, earnings
  confirming [source: https://www.ft.com/...]. Real beneficiary, not noise.
- Cycle/Regime — Dalio lens: **CROWDED** — rec_mean 1.45 across 41 analysts, inst 85.5% — little marginal buyer left.
- Sell-side — Street consensus: **NEUTRAL** — consensus Buy, 41 analysts, PT mean $290 (+9.6% upside), dispersion WIDE, momentum
  STABLE; independent view (Morningstar) not confirming — 2-of-3 rule not met, crowded-consensus trap.

Decision: Fundamental only FAIR (not ≥ GOOD) → fails the BUY gate → **WATCH**. Output a WATCH block: enter
$255–270 only if a daily close > $280 confirms; conviction 3/5 (CROWDED −1; MID_CYCLE neutral).
Invalidation: loss of the 200d trend or AI-capex guidance cut. Honest note: "this is a hypothesis — the
$280 trigger rule must clear strategy-discovery-backtest before risking capital."
</example>

---

## Self-check before printing the signal table

**Gate 0 — the sell-origination audit. Do this FIRST and treat a failure as blocking, not cosmetic.**

- [ ] **Every TRIM/EXIT names its originating seat and evidence.** For each sell in the table, point to the
      `THESIS_IMPAIRED: YES` from the **fundamentals**, **narrative** or **smart-money** seat plus the stated
      evidence (metric + delta, or filing + date + amount). A sell that cannot produce one is a **defect** —
      delete it and print `WATCH` + an armed alert instead. This is the MRVL failure; do not re-ship it.
- [ ] **No sell rests on price.** Grep your own output: if the justification is a moving average, a
      drawdown, an RSI level, or a stretched multiple, it is not a sell. Technicals supply `TIMING` and a
      stated `HARD STOP` only.
- [ ] **Sizing and stop reductions are labeled as such** — `TRIM (SIZING) — {weight}% of book` and
      `TRIM (RISK) — hard stop ${X} hit`. Neither may be presented as a thesis conclusion.
- [ ] **No script verdict anywhere.** Step 0.82 prints `REVIEW_NOW | REVIEW | NO_ACTION` and nothing else.
      If any output block shows a scorecard ACTION, a CHAIN-READ/ACTION split, or an "informational only"
      reconcile note, the run used a stale template — fix it before printing.
- [ ] **Triage covered the whole book.** `{n} names screened` matches the position count, and the
      `data MISSING` count is stated. Any held position that produced no screen output is listed as
      `REVIEW_NOW / NO_SCREEN_OUTPUT`, never silently absent.
- [ ] **Smart-money actually ran.** `smartmoney.py` output exists for every panel name, each source carries
      `OK | NO_DATA | MISSING(reason)` with its lag, and any 13F citation carries its staleness in days.

- [ ] The report **OPENS with the 2–3 sentence prose RECAP** (highest-confidence buy/sell to take now +
      one-line reasoning + the market narrative in one sentence) before any per-stock block or the signal table.
- [ ] **No seat line reads "carried from MM-DD" or "no data this run".** Reused verdicts print the actual
      finding with an `(as of MM-DD)` tag; seats with nothing (and no prior verdict) are dropped from the
      block and rolled into one `⚠️ dark: {Seat, Seat — reason}` line.
- [ ] Every FULL-PANEL ticker has `status='done'` in `stock_analysis`; one-line-screened names (N>12 triage)
      carry a one-line note and are listed, not dropped.
- [ ] Each stock block ends with a concrete **entry zone + bar-close trigger + market-based stop** — never a
      vague "looks good". WATCH/SKIP names what would change it.
- [ ] The **Timing line is present** whenever `days_to_earnings` (from `fundamentals.py`) is ≤10 trading
      days out — `EVENT_SOON — earnings in {days}d ({date}); stage {ACTION} after print` — else `N/A`. This
      is a non-gating annotation only; it never decides anything (Step 0.82 emits attention, not actions).
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
- [ ] The smart-money seat **ran `scripts/smartmoney.py`** and reported each source's status + lag. A bare
      `INSUFFICIENT DATA` with no named source is NOT acceptable any more — that was the 2026-07-24 failure
      (nothing was fetched and nobody could tell). Every unreachable source is named with its reason; no
      filing is fabricated; any 13F citation carries its computed staleness in days and is labeled
      corroboration, never the basis for a sell.
- [ ] **The Sell-side seat ran on every deep-dive ticker** (or returned `INSUFFICIENT_DATA`), cited every
      analyst page it actually `web_fetch`ed (Yahoo/StockAnalysis.com/TipRanks/MarketBeat/Zacks/Morningstar),
      and did **NOT** assign BULLISH on the raw consensus rating level alone — the ≥2-of-3 rule (independent
      view, dispersion, momentum) was applied. Cached at `$RUN_DIR/{TICKER}/seat_sellside.json`.
- [ ] Portfolio sizing/concentration was deferred to `stock-chair`; ETF allocation to
      `tradfi-portfolio-manager`. This skill stayed on individual-stock entries only.
- [ ] **No ETF / thematic-basket / commodity name received a technical-only verdict** (Step 0.82 rule 0.4):
      any name with no company fundamentals (`quote_type` = ETF/MUTUALFUND/INDEX, or all VALUE/QUALITY/GROWTH
      inputs null — e.g. URNM) returned **REVIEW_THESIS**, not a HOLD/TRIM off RSI/MA, and was routed to
      `tradfi-portfolio-manager` / `analyse-macro`. Concentration TRIM (rule 0, ≥15%) may still fire for such
      names — that is risk management, not a fundamental verdict.
- [ ] Prior research reports in `.cache/stocks-advisor/research/` checked for context if relevant (human-readable history, not verdict inputs)
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
- [ ] **Edge Articulation Gate ran** (Step 0.85) — every deep-dive ticker has a named edge (INFORMATION/ANALYTICAL/TIMING/STRUCTURAL) in its output block header. Tickers with NO_EDGE stayed fundamentals-only and are listed as WATCH in the signal table with the NO_EDGE note.
- [ ] **Citation audit tags present** — Skeptic's TAIL RISK and HISTORICAL ANALOG carry [LIVE]/[FILED]/[MEM] tags. Any [MEM]-only claim is flagged ⚠️[MEM-only] and the CIO addressed it in DISSENT LOGGED.
- [ ] **Portfolio tail stress numbers present** — Skeptic output includes explicit -30% and -50% dollar impact at current weight for every BUY/ADD ticker (Step 2 Skeptic prompt).
- [ ] **P0/P1/P2/P3 Execution Table present** — printed after SETUP ALERTS (Step 3.6); all BUY/ADD/EXIT/TRIM verdicts appear in the table with share counts, entry zones, triggers, and falsification conditions. No P0 without a named trigger already fired.
- [ ] **Exit-watches registered for every held position** — a standing 200d-break (and, for large/overweight winners, a trailing) sell-alert per holding via `mkt-alert.ts`, so a Rule 0.7 trend break pings the user in real time between panel runs (the NEM/MRVL "keep watching" fix). See *Set an exit-watch*.
- [ ] **Every WATCH/WAIT with a defined trigger was auto-registered** — mechanical triggers (price reclaim / level / RSI / MA / MACD) armed via `mkt-alert.ts`; event/earnings/semantic triggers ("beats and holds", "reaccelerates") scheduled as a dated re-eval routine (mkt-daemon / Claude Code routine), NEVER encoded as a price threshold. WATCH names with **no** defined trigger are listed as "not armed" (not spammed). Every armed alert carries a conviction grade + thesis text. See *Set a buy-alert* / *Schedule an event re-eval*.
- [ ] **ALERTS ARMED summary printed** (Step 3.6) — reports each registered alert (mechanism, trigger, channel, conviction) plus which WATCH names were left un-armed and why. Registration was automatic, not offered.

## Set a buy-alert (notify-me-when) — AUTO-REGISTERED for every WATCH/WAIT with a mechanical trigger

A WATCH/WAIT verdict ("good company, wrong price — buy near $X / when RSI < V / on a 50d reclaim") **auto-arms**
a durable alert that pings the user **with your entry thesis** on trigger. This is not offered afterward — the
skill registers it as soon as the verdict is set. Use the **`mkt`** skill — it carries the reasoning into the
notification (mkt's native message cannot). Register the entry plan as a job:

```bash
cd .agents/skills/mkt/scripts
bun mkt-alert.ts add --desk stocks --symbol NVDA \
  --condition below --value 142 \
  --data-source "50d MA = $142 from 60d TV/yfinance daily closes (as of <date>)" \
  --reason "CONVICTION 4/5. Buy-zone = prior breakout retest + 50d reclaim; add to core, not a new satellite." \
  --channel telegram:@CryptoAiInvestor --expiry 2026-09-30
# 50d-reclaim trigger:  --condition sma_cross_above --value 50 --period 50
# oversold add:         --condition rsi_below --value 30 --period 14 --cooldown 21600
```

**Precision guard (mandatory):** only auto-register when the trigger is CONCRETE and falsifiable (a price
level, a reclaim, an RSI/MA/MACD condition). A WATCH with **no defined trigger** is left un-armed and listed
as "no trigger, not armed" — never fire a meaningless alert (alert fatigue is the failure). Every armed alert
**must** carry the **conviction grade** (e.g. `CONVICTION 4/5`) and the **thesis text** in `--reason`.

**Mechanical only.** This path handles conditions a price/indicator engine can evaluate. A semantic condition
("beats and holds", "organic reaccelerates") CANNOT be a `--value` threshold — route it to *Schedule an event
re-eval* below instead. Never encode a semantic/earnings condition as a dumb price level.

A scheduled `bun check.ts` (runtime cron) fires the notification with the reasoning when the zone/indicator
hits. See `.agents/skills/mkt/SKILL.md` for trigger patterns and the per-runtime scheduler cookbook.
Recommend-only and backtest-gated — an alert is a reminder to re-evaluate, not an order.

## Schedule an event re-eval — AUTO-REGISTERED for every WAIT-on-catalyst (earnings/semantic) verdict

A WAIT whose trigger is a **judgement about an event** — "buy if it beats AND holds after the Jul 29 print",
"add if core organic reaccelerates at Q2" — cannot be armed as a price alert: no threshold can decide "did it
beat and hold" or "did the narrative reaccelerate". Comparing one number would fire on a headline beat that
the market sells, or miss a quiet beat with a raised guide. **The correct trigger is re-running the panel**,
so the semantic condition auto-arms as a **dated re-evaluation** on the day after the catalyst, routed to a
Claude Code **scheduled routine / the mkt-daemon** — NOT to `mkt-alert.ts`.

Register it by scheduling (or emitting a ready-to-run spec for) a re-run of this skill on that ticker:

```
RE-EVAL SPEC (auto-scheduled)
  ticker:   SOFI
  when:     2026-07-30            # day AFTER the Jul 29 earnings print
  route:    claude-code scheduled routine / mkt-daemon   (NOT a price alert)
  action:   re-run stocks-advisor on SOFI; judge "beat AND held" from the panel, not a number
  thesis:   CONVICTION 3/5. WAIT — only add if the print beats and the tape holds the gap; a
            headline beat that fades is a NO. Semantic condition → needs the panel, not a threshold.
  channel:  telegram:@CryptoAiInvestor
```

Emit this spec as the deliverable when the mkt-daemon/scheduler is not directly reachable — a paste-able,
dated re-run instruction the user (or the daemon) can drop into a cron. Why this path exists: a price alert is
structurally incapable of evaluating a semantic/earnings condition; forcing one into a `--value` would be a
silent false trigger. The skill must route event triggers here and never to a price threshold.

Recommend-only and backtest-gated — a scheduled re-eval is a reminder to re-run the panel, not an order.

## Set an exit-watch (sell/trim alert) — for HELD positions (MANDATORY per run)

"Keep watching" is the whole point of the NEM/MRVL lesson: the missed exits happened *between* full panel
runs. Triage flags a trend-break **when you run it** — but a position can roll over on a
Tuesday you didn't run it. So for **every held position** (not just WATCH names), register a **standing
exit-watch** so the trend break pings the user in real time, with the exit thesis, the moment it happens —
not weeks later when they next run a panel. This reuses the same `mkt-alert.ts` mechanism as buy-alerts; do
**not** build a new scheduler.

For each held position, register the exit level that would fire Rule 0.7 — its **200d MA** (the disciplined
trend break), and for a large/overweight winner a **trailing level** below the recent price too:

```bash
cd .agents/skills/mkt/scripts
# Trend-break exit-watch on a held winner (fires Rule 0.7 in real time):
bun mkt-alert.ts add --desk stocks --symbol NEM \
  --condition below --value 46.00 \
  --data-source "200d MA = $46.00 from 250d TV/yfinance daily closes (as of <date>)" \
  --reason "EXIT-WATCH: +100% winner, 8% of book. Close below 200d = Rule 0.7 early trend-break exit — TRIM to protect the gain, do NOT wait for the oversold print." \
  --channel telegram:@CryptoAiInvestor --expiry 2026-12-31
# Optional trailing-stop leg for a big winner (protect locked gains on a sharp reversal):
#   --condition pct_down --value 12   (12% off the recent high)
# 50d-break early warning (rolling over before the 200d):  --condition sma_cross_below --value 50 --period 50
```

Notes:
- `below`/`above` price conditions **require `--data-source`** citing the OHLCV the level came from (mkt hard-fails otherwise) — quote the 200d level and its source.
- Set the exit-watch even for **HOLD/WAIT-verdict** positions: the point is to catch the *transition* to a breakdown, which by definition hasn't happened yet at panel time.
- The **`risk-desk`** skill (`.agents/skills/risk-desk/`) is the *always-on* companion: run it on a cron over the live positions book and it fires the same trend-break/winner-rollover breaches (its R1/R4) independently of any panel. Exit-watches (this section) + risk-desk (standing sweep) are belt-and-suspenders — register the alerts here, and let risk-desk poll the whole book. Neither replaces the other; both exist because NEM was missed by having *only* the on-demand picker.
- Recommend-only and backtest-gated — an exit-watch is a reminder to re-evaluate size, not an order to sell.

## Done when

- Each analyzed stock has a 6-seat panel → Skeptic challenge → CIO verdict → Risk Manager gate (if BUY/ADD),
  and a concrete entry plan (zone + trigger + stop + conviction + invalidation).
- The output block shows DISSENT LOGGED for every ticker (Skeptic's best objection, even when overruled).
- The signal table with the theme map is printed; every news claim is sourced inline.
- The SOURCES & DATA appendix (Step 3.5) lists all web_fetched URLs, feed-script records, and market-data
  provenance.
- The output is flagged as an educational, backtest-gated hypothesis — not advice.
- The high-confidence RECAP + SETUP ALERTS table (Step 3.6) is printed last, splitting immediate
  high-conviction actions from buy-on-condition names.
- **Every WATCH/WAIT with a defined trigger was auto-registered** — via `mkt-alert.ts` when the trigger is
  mechanical (price reclaim / level / RSI / MA / MACD), or scheduled as a dated re-eval routine when the
  trigger is event/earnings/semantic ("beats and holds", "reaccelerates"). Semantic conditions are never
  encoded as a price threshold. WATCH names with no defined trigger are listed as not-armed (precision guard,
  no alert spam). An **ALERTS ARMED** summary reports what was wired, the trigger, the channel, the conviction
  grade, and which names were left un-armed and why. Registration is automatic — not offered afterward.
- For a holdings review, a **standing exit-watch** (200d-break / trailing sell-alert) was registered for
  every held position via `mkt-alert.ts` (or delegated to the always-on `risk-desk` sweep) — so a trend
  break fires in real time between runs, the NEM/MRVL "keep watching" requirement.
- If `.cache/stocks-advisor/notion.yaml` is configured, a dated Notion page (title `YYYY-MM-DD <narrative>`,
  Step 5) was created and its URL returned; if not configured, publishing was skipped silently (not an error).
- A **reasoning diagram** (Step 5.5) was produced by a delegated subagent — `$RUN_DIR/reasoning_diagram.mmd`
  (+ rendered .png where mermaid-cli works), the mermaid block appended to the report .md and the Notion page,
  and the .png sent to the user. Diagram failure was reported but did not fail the run.
</content>
</invoke>
