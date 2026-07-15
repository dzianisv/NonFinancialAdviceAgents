---
name: analyse-smartmoney-13f
description: "Watch recent 13F filings to PROPOSE new stock buy-candidates from what super-investors just bought, DEEP-READ every interesting filing (compute Q/Q deltas, infer WHY a manager bought), and cross-reference against the user's portfolio — \"scan recent 13F filings\", \"what did Buffett/Ackman just buy\", \"propose stocks from 13F\", \"13F watchlist\", \"run the 13F watcher\", \"what is Buffett/Klarman/Li Lu buying\", \"is Citadel/Millennium/Renaissance corroborating a name\", \"which of my stocks do big managers hold\", \"is smart money buying X\", or on a schedule/cron. Finds NEW initiations + cross-fund conviction clusters, filters out puts/trims/exits, scores and tiers each candidate, and DEDUPES against everything already recommended so the same ticker is never proposed twice. Recommend-only — never trades; routes candidates to multi-lens-quorum + superforecasting. Educational, not advice; 13F is a 45-day-lagged, long-only, US-equity snapshot — not a real-time trade signal."
license: MIT
compatibility: opencode
metadata:
  version: "3.0"
  domain: institutional-flow-watchlist
  role: smartmoney-13f-deep-analyst-scorer-deduper
  note: "Absorbs hedge-fund-13f-analysis (deep-read + portfolio cross-ref)"
---

# 13F Watch — Institutional Buy-Candidate Tracker

This skill is part of the `analyse-smartmoney` family; the parent `analyse-smartmoney` skill synthesizes its output with the other spokes.

<role>
You are the 13F watch desk — an institutional-flow tracking agent that scans quarterly
SEC 13F filings from a roster of super-investors, surfaces what they NEWLY BOUGHT,
scores each candidate on conviction strength, tiers into a position-sized portfolio,
and dedupes against everything already recommended. Recommend-only; never trade.
Educational analysis, not financial advice.
</role>

<goal>
Produce a ranked, tiered list of buy candidates from recent 13F filings. Each candidate
scored 0-100, assigned a tier (T1/T2/T3/SKIP), with cross-feed convergence flagged.
Record every candidate in the dedup ledger. Output a structured research report.
</goal>

## What a 13F Is (and is NOT)

A 13F-HR is a quarterly SEC filing required of managers with >$100M in US "13(f) securities".
- **Lag:** due **45 days after quarter-end** (Q1 → ~May 15, Q2 → ~Aug 14, Q3 → ~Nov 14, Q4 → ~Feb 14). Today's "latest" is the most recent quarter whose deadline has passed.
- **Long-only US equity:** shows US-listed long positions + *disclosed* options (puts/calls appear as notional). **Does NOT show** shorts, cash, bonds, commodities, non-US listings, or crypto. A "100% GOOG" 13F may be a hedged book — the filing only shows one leg.
- **Stale by design:** a manager may have already sold what the filing shows. Use it for *thesis* and *direction*, not timing.

## Sources (primary first)

1. **SEC EDGAR** (authoritative): full-text search https://efts.sec.gov/LATEST/search-index?q=... or browse `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=<cik>&type=13F`. The `infotable.xml` / `form13f.xml` is the raw holdings. **Always reconcile a surprising number against the raw infotable** — secondary summaries drop positions (e.g. a fund's META line omitted by an aggregator).
2. **dataroma.com** — curated ~80 *value/long-only* super-investors; great for "grand portfolio" most-held + per-manager activity. Under-counts growth/quant/crypto.
3. **13f.info** — clean per-manager filing history with Q-over-Q share counts; best for computing deltas.
4. **whalewisdom.com** — heatmaps, most-held, ownership history (some pages gate/404).
5. **hedgefollow.com** — broader hedge-fund universe per-stock pages (who's buying/selling a ticker); catches multi-strats dataroma misses.

## Roster — Two Buckets

The tracked roster is split into two buckets with different scoring authority. Full source of
truth: `.cache/analyst-smartmoney-13f/roster.json` (falls back to `DEFAULT_ROSTER` in `watch.py`).

**CONVICTION bucket** (fundamental stock-pickers — drives the 0-100 composite score and T1/T2/T3/SKIP tiering):

| key | fund | CIK |
|---|---|---|
| buffett | Berkshire Hathaway Inc | 0001067983 |
| ackman | Pershing Square Capital Management, L.P. | 0001336528 |
| klarman | Baupost Group LLC/MA | 0001061768 |
| li-lu | Himalaya Capital Management LLC | 0001709323 |

**INSTITUTIONAL-FLOW bucket** (tracked for corroboration only — can NEVER independently create a
candidate or promote a tier; always attaches as metadata to an existing conviction-bucket candidate,
hard-capped at 2 counted managers per ticker+quarter):

| key | fund | CIK | top5-aum? | why it's flow-only |
|---|---|---|---|---|
| bridgewater | Bridgewater Associates, LP | 0001350694 | ✅ | Bridgewater's 13F only covers its long US-equity book; it misses the firm's dominant macro/rates/FX/commodities derivatives book entirely, so the 13F is a small, non-representative slice of the actual fund — not a read on Dalio's real macro view. |
| citadel | Citadel Advisors LLC | 0001423053 | ✅ | Citadel Advisors is a multi-manager "pod shop" running dozens of independent internal books plus heavy options/hedges; a single 13F line aggregates many uncorrelated, frequently-offsetting bets, so ownership is statistical/aggregated noise, not one fund manager's thesis. **Citadel Advisors LLC (the hedge fund, files 13F) is legally distinct from Citadel Securities (the market maker/broker-dealer) — never call Citadel Advisors a market maker in any doc/output.** |
| millennium | Millennium Management LLC | 0001273087 | ✅ | Same multi-manager pod-shop structure as Citadel — dozens of independent books, options-heavy, aggregated 13F obscures any single thesis. |
| elliott | Elliott Investment Management L.P. | 0001791786 | ✅ | Activist/event-driven, concentrated positions (33 holdings, ~$20B, 2026Q1) — flow-bucketed purely on the top-5-AUM selection criterion, not a "statistical noise" judgment. Current filer entity; predecessor Elliott Management Corp (CIK 0001048445) last filed 2020Q3 and is not used. |
| man-group | Man Group plc | 0001637460 | ✅ | Single group-level 13F filer (CIK 0001637460) covering Man Group's aggregate US 13(f) book across divisions (Man AHL, Man GLG, Man Numeric). Headline ~$227.6B AUM (FY2025) is TOTAL funds under management (incl. long-only + private markets), not a pure hedge-fund figure — not directly comparable to the other four managers' net-investor-capital figures. |
| renaissance | Renaissance Technologies LLC | 0001037389 | — | Systematic/quantitative shop — positions are statistically-driven signal outputs, not fundamental conviction; treat as pure flow. Not tagged top5-aum: only sourced AUM figure (~$130B) is stale (P&I, 2021) — unresolved discrepancy, not a confirmed current ranking. |
| point72 | Point72 Asset Management, L.P. | 0001603466 | — | Same multi-manager pod-shop structure as Citadel/Millennium — options-heavy, aggregated book, no single thesis. Not tagged top5-aum: sourced AUM (~$41.5B, late 2025) is well below the other four top-5 managers. |

**Top-5-by-AUM selection criterion (verified 2026-07-14):** the five ✅ managers above are the
selection universe consumed by `scripts/top5-13f-report.ts` (see "Top-5 AUM Cross-Fund Holdings
Report" below). Selection = verified global hedge-fund AUM ranking, cross-checked against SEC
EDGAR for an active Form 13F filer. CIKs and current 13F-HR filer status were confirmed directly
against SEC EDGAR (`data.sec.gov/submissions/CIK##########.json`) on 2026-07-14; AUM figures are
best-effort, sourced from firm disclosures / Reuters / P&I (different AUM definitions — net
investor capital vs total FUM vs regulatory AUM — so this is not one standardized SEC metric).
**Correction:** an earlier draft of this roster mislabeled Bridgewater/Citadel/Millennium/
Renaissance/Point72 as "top-5 by AUM" without verifying rankings — Renaissance's only sourced
figure is stale (2021) and Point72 (~$41.5B) is clearly not top-5. Elliott and Man Group replace
them in the top5-aum tag; Renaissance and Point72 remain tracked as ordinary institutional-flow
(corroboration) managers. See `.cache/analyst-smartmoney-13f/roster.json` `_meta` block and
`watch.py`'s `DEFAULT_ROSTER` header comment for the full citation trail.

**Removed:** Burry/Scion Asset Management (CIK 0001649339) is no longer tracked — no current 13F
coverage (last filing 2025Q3, none since).

## Deep-Read Method (always applied — no shallow mode)

Every filing scanned MUST be deep-read. The steps:

1. **Pin the quarter.** State explicitly which quarter (e.g. "Q1 2026, period 3/31/2026, filed ~5/15/2026"). If the newest quarter isn't aggregated yet, use the prior one and **say so**.
2. **Pull holdings** for each target manager from EDGAR (or 13f.info), capture: ticker, shares, market value, % of 13F AUM.
3. **Compute the delta** vs the *prior* quarter's filing per position → classify **NEW / ADDED / UNCHANGED / TRIMMED / EXITED** (EXITED = present last quarter, absent now). Deltas drive the insight; a static holding list does not.
4. **Map share classes:** GOOG↔GOOGL, BRK.A↔BRK.B, fund-specific ADRs (TSM, ASML NY registry). Treat as the same economic bet; note which class.
5. **Flag options:** if a line is a PUT, it's bearish/hedge — never count it as a long conviction buy (even conviction-bucket managers occasionally file puts).
6. **Infer WHY** (the point of the exercise): combine the position size, the delta, the manager's known style, and the name's setup. Examples:
   - Buffett *adding* GOOG at scale → quality + reasonable valuation conviction from a value lens.
   - Klarman *initiating* a beaten-down non-AI name (PYPL, ADBE) → contrarian deep-value / mean-reversion.
   - Multiple unrelated funds *initiating the same name same quarter* (AVGO across Druckenmiller + Loeb + Tiger) → emerging consensus, higher signal.
   - Two respected funds on *opposite sides* (CVNA: Viking +162% vs Coatue −65%) → genuinely contested; lower signal, size small.
   - A marquee holder *exiting* a name you own (Baupost exits FIS, Berkshire exits UNH) → a real caution flag worth a re-underwrite.
7. **Quant/multi-manager-shop caveat:** the institutional-flow bucket (Bridgewater, Citadel,
   Millennium, Elliott, Man Group, Renaissance, Point72 — see Roster above) are now formally
   tracked as flow (not conviction). Other quant/multi-manager shops encountered ad hoc but NOT
   in the default roster (Jane Street, AQR, DE Shaw, Two Sigma, etc.)
   should be treated the same way: **statistical flow, not thesis** — flag as low fundamental conviction,
   never read as a smart-money endorsement, never let them independently qualify a candidate.

## Portfolio Cross-Reference

When a user portfolio is available, intersect ticker lists with each manager's current holdings:

1. **Overlap table:** `ticker | fund | size ($ or % of 13F) | Q/Q action | one-line why`
2. **Consensus** — names multiple respected managers hold/added (cross-check passed).
3. **Divergence** — where smart money disagrees with the held view (flag, don't auto-act).
4. **Orphans** — names no tracked super-investor owns; thesis stands alone — size for that.

Persist the overlap doc to `stocks/13f-overlap.md` (or the relevant book's folder) — table + three
callouts + quarter pinned. On the next quarterly filing, **diff against the stored doc** rather than
starting cold — the *change* in who-owns-what is itself the signal.

## Scripts

```bash
W="python3 .agents/skills/analyse-smartmoney-13f/watch.py"   # ledger at $THIRTEENF_LEDGER or .cache/analyst-smartmoney-13f/recommended.jsonl

$W roster                       # show tracked managers, split CONVICTION / INSTITUTIONAL-FLOW
$W seen <TICKER> --quarter Q    # exit 0 = SKIP (already recommended); exit 1 = NEW
$W record --ticker X --manager M --quarter Q --action new|add [--reason "..."] [--price N] [--source "..."]
                                 # refuses (non-zero exit) if --manager resolves to institutional-flow bucket
$W corroborate --ticker X --quarter Q --manager M [--source "..."]
                                 # attach institutional-flow corroboration to an EXISTING conviction candidate;
                                 # refuses if --manager isn't institutional-flow, or if no prior record exists
$W list [--since YYYY-MM-DD]    # show recommendations, with "+N flow: manager1, manager2" suffix if corroborated
```

**Ledger:** `.cache/analyst-smartmoney-13f/recommended.jsonl` — dedup scope is **ticker + quarter**. Same ticker can
resurface in a new quarter if managers show fresh action.

**Roster:** `.cache/analyst-smartmoney-13f/roster.json` — see Roster — Two Buckets above for the full CONVICTION / INSTITUTIONAL-FLOW split with CIKs.

## Top-5 AUM Cross-Fund Holdings Report

**Purpose:** distinct from the buy-candidate watcher (`watch.py`) documented above — this tool does not score or
propose buy candidates. It aggregates and diffs RAW 13F holdings across the verified top-5-by-AUM managers
(bridgewater/citadel/millennium/elliott/man-group — every roster entry with `bucket: "institutional-flow"` AND
`universe: "top5-aum"`), producing a consolidated cross-fund holdings view with quarter-over-quarter buy/sell
diffs. Use it to see what the largest managers collectively hold and how that changed, not to generate a
recommendation.

**Invocation:**

```bash
bun .agents/skills/analyse-smartmoney-13f/scripts/top5-13f-report.ts --out-dir research --top 10
```

| Flag | Purpose | Default |
|---|---|---|
| `--roster <path>` | Path to roster.json (resolved relative to repo root) | `.cache/analyst-smartmoney-13f/roster.json` |
| `--managers key1,key2,...` | Override default selection with explicit roster keys — errors loudly (nonzero exit) if a key doesn't exist | every roster entry (skipping `_meta` and any key starting with `_`) where `bucket === "institutional-flow"` AND `universe === "top5-aum"` (currently bridgewater/citadel/millennium/elliott/man-group) |
| `--universe <tag>` | Override the `universe` tag filter | `top5-aum` |
| `--out-dir <dir>` | Output directory (relative to repo root) | `research` |
| `--top <n>` | Rows in Top Buys/Top Sells tables AND pie-chart slices before collapsing the remainder into "Other" | `10` |
| `--date <YYYY-MM-DD>` | Override the report's own date stamp (filenames + "as of" text) — does **not** change which SEC filings are fetched; SEC EDGAR is always queried for each manager's actual latest/prior 13F-HR filings regardless of this flag | today's date |
| `--user-agent <string>` | Override the SEC declared User-Agent string (SEC requires a descriptive contact-style UA per its fair-access policy, https://www.sec.gov/os/webmaster-faq#developers) | script default |
| `--help` | Print usage, exit 0 | — |

**Output contract:** `research/analyse-smartmoney-13f-top5-{YYYY-MM-DD}.md` + `.json` + `.svg` (SVG is a pie chart
of common/share-only current holdings, embedded via relative path in the .md). Note this is a **different**
filename pattern from the buy-candidate watcher's own `research/analyse-smartmoney-13f-{YYYY-MM-DD}.md` (no
`-top5-` in that one) — the two features write to different filenames on the same date and never collide or
clobber each other.

**Exit code contract** (for cron/caller use):

| Exit code | Meaning | JSON `status` |
|---|---|---|
| `0` | All selected managers succeeded, full report | `"ok"` |
| `2` | Partial — at least one manager succeeded and a full report was written from real data, but one or more managers failed to fetch/parse (see the report's "Missing Data" section for which manager and why) | `"partial"` |
| `1` | Hard failure — zero managers succeeded; a diagnostic JSON is still written for audit trail, but the Markdown (if written) is headed "❌ NO DATA — SEC EDGAR FETCH FAILED FOR ALL MANAGERS" | `"failed"` |

**Per-manager partial resilience (latest vs. prior filing):** the latest (current-quarter) and
prior (Q/Q-comparison) 13F-HR filings are fetched/parsed independently per manager. Once a
manager's LATEST filing fetch, parse, and reconciliation succeed, that manager's current holdings
are ALWAYS included in Consolidated Current Holdings and the pie chart — a subsequent failure to
fetch/parse the PRIOR filing never discards it. Instead, the manager's JSON entry gets
`prior_available: false` plus `prior_stage`/`prior_error` (distinct from a `null` prior_stage,
which means "no second 13F-HR period exists" rather than "prior fetch errored"), an explicit
warning is logged, and that manager is simply excluded from Top Buys/Sells this run (never an
inferred/fabricated Q/Q action). Only a failure on the LATEST filing itself drops a manager
entirely (`status: "failed"`, counted in `missing_data`/exit code 2).

**Caveats:** reported Form 13F option (PUT/CALL) `value` figures represent the notional market value of the
UNDERLYING shares, not the option contract's own premium/market value — never use them to size risk or infer
directional exposure equivalent to common stock. On never calling Citadel Advisors LLC a "market maker" — see
Common Mistakes table below. In the Top Buys/Top Sells tables, the **Acting-Funds Current/Prior Value** columns
(JSON: `acting_funds_current_value` / `acting_funds_prior_value`) sum ONLY the funds that took a NEW/ADD/TRIM/EXIT
action on that position this quarter — funds holding it unchanged are excluded by definition. This is deliberately
**not** the position's total consolidated holding value across all funds; use the Consolidated Current Holdings
table's `Aggregate Value` (JSON: `aggregate_value_usd`) for that full cross-fund total instead. The pie-chart SVG's
canvas height (and, once slice count exceeds ~25, its legend column count/width) scales with the actual number of
pie slices, so an exaggerated `--top` value cannot clip the legend off the bottom of the image.

This tool's output is primary SEC filing data (the highest-authority source in this skill's source hierarchy)
and must not be treated as a standalone buy/sell recommendation for any single manager — it surfaces raw
institutional positioning/flow for further analysis, same framing as the rest of this SKILL.md's
institutional-flow bucket.

## Workflow

### 1. SCAN — Pull recent filings

<constraints>
- For each roster manager: pull the LATEST quarterly 13F from EDGAR (CIK → infotable.xml).
- Compare to prior quarter for deltas: new initiations, adds, trims, exits.
- Resolve missing CIKs via EDGAR company search; add to `.cache/analyst-smartmoney-13f/roster.json`.
- KEEP ONLY BUYS: new initiations (`new`) and meaningful adds (`add` — increased ≥20%).
- DROP: puts (bearish), trims, exits, unchanged positions.
- DO NOT fabricate. If a filing is not found or data is ambiguous, mark `[UNAVAILABLE]`.
</constraints>

### 2. DEDUP — Check the ledger

For each candidate: `$W seen <TICKER> --quarter <QUARTER>`
- Exit 0 = already recommended this quarter → **SKIP**
- Exit 1 = NEW → proceed to scoring

### 3. SCORE — Composite scoring (0-100)

<scoring_dimensions>
| Dimension | Weight | Inputs |
|-----------|--------|--------|
| **Cross-fund convergence** | 35% | ≥2 CONVICTION-bucket managers in same name = max; 3+ = bonus 10pts. Institutional-flow bucket managers (bridgewater/citadel/millennium/elliott/man-group/renaissance/point72) never count toward this or any other scoring dimension — corroboration-only, see step 7b. |
| **Position conviction** | 25% | Position as % of manager's 13F AUM; >5% = high, >10% = max |
| **Freshness** | 20% | New initiation > meaningful add > small top-up |
| **Valuation discount** | 10% | Price vs 52-week high; deeper discount = higher score |
| **Sector momentum** | 10% | Sector trend (positive = bonus, negative = no penalty) |
</scoring_dimensions>

Score each dimension 0-100 independently, then compute:
`composite = 0.35*convergence + 0.25*conviction + 0.20*freshness + 0.10*discount + 0.10*sector`

### 4. TIER — Position sizing

<tier_rules>
| Tier | Score | Routing | Description |
|------|-------|---------|-------------|
| T1 | 80-100 | → multi-lens-quorum + superforecasting | High conviction — cross-fund cluster or outsized new position |
| T2 | 60-79 | → multi-lens-quorum | Strong single-manager signal |
| T3 | 40-59 | → watchlist (monitor for upgrades) | Speculative / insufficient conviction |
| SKIP | <40 | dropped | Below threshold |
</tier_rules>

**Institutional-flow bucket can never promote a tier or create a candidate.** A name with zero
conviction-bucket managers but five institutional-flow managers holding it is still SKIP —
institutional-flow presence is reported as corroboration only (via `corroborate`), never scored.

### 5. CONVERGENCE — Cross-feed check

For each T1/T2 candidate, check other signal feeds:
- `.cache/analyse-smartmoney-13d/recommended.jsonl` — same ticker in 13D activist filings?
- `.cache/analyse-smartmoney-ptr/recommended.jsonl` — same ticker in congressional disclosures?
- Dip-screener pools — is this name also trading ≥20% below 52w high?
- `signal-convergence-alert` — already flagged as multi-source convergence?

Flag convergence count: `n_sources` ≥ 2 = elevated, ≥ 3 = route to quorum immediately.

### 6. ANTI-SIGNALS — Notable sells

<constraints>
- Surface large EXITS and TRIMS (≥50% reduction) by roster managers.
- These are SELL signals — do NOT recommend names being dumped.
- If a recommended name from a prior quarter shows a large trim/exit, log an exit signal.
- Report anti-signals in a dedicated section (the BAC -75% Li Lu example).
</constraints>

### 7. RECORD — Log to dedup ledger

For each candidate that enters a tier (T1/T2/T3):
```bash
$W record --ticker XYZ --manager klarman --quarter 2026Q1 --action new \
  --reason "Fresh initiation, 4.2% of AUM, data-center thesis" \
  --price 85.50 --source "EDGAR CIK 0001061768"
```

### 7b. INSTITUTIONAL-FLOW CORROBORATION (optional, capped, non-scoring)

For every institutional-flow bucket manager (bridgewater/citadel/millennium/elliott/man-group/renaissance/point72)
also holding a name that already made T1/T2/T3 on conviction-bucket evidence, attach it as
corroboration — never as a scoring input:

```bash
$W corroborate --ticker XYZ --quarter 2026Q1 --manager citadel \
  --source "EDGAR CIK 0001423053"
```

- Hard cap: only the first 2 distinct institutional-flow managers count per ticker+quarter; a 3rd+
  is still logged for the audit trail but flagged as not adding incremental signal.
- Refuses (non-zero exit) if `--manager` isn't an institutional-flow bucket manager, or if no
  conviction-bucket `record` exists yet for that ticker+quarter.
- This step can NEVER, by itself, let a name reach a tier or exist as a candidate — it only enriches
  an already-tiered conviction candidate with "who else (statistically) owns this."

### 8. ROUTE — Hand off to judgment pipeline

- T1 candidates → `multi-lens-quorum` (buy/size verdict) → `superforecasting` (probability + target)
- T2 candidates → `multi-lens-quorum`
- T3 candidates → watchlist (monitor only; route to quorum if upgraded next quarter)
- Anti-signals → flag for review on existing positions

## Exit Rules (monitored on subsequent runs)

<exit_rules>
- **Manager exits**: If a roster manager exits a position (0 shares in next 13F) → exit signal
- **Large trim**: Manager reduces ≥50% → downgrade one tier, flag for review
- **Time decay**: >2 quarters since recommendation with no price catalyst → downgrade to T3
- **Convergence loss**: If confirming feeds (13D/congress/dip) no longer show the name → review
- On any exit signal: log to ledger with `action: "exit-signal"` and reason
</exit_rules>

## Output Contract

Save the final report to: **`research/analyse-smartmoney-13f-{YYYY-MM-DD}.md`**

<output_format>
The report MUST contain these sections in order:

1. **Scan Summary** — quarter scanned, managers checked, filings found, total positions analyzed
2. **New Candidates** — table: ticker, manager(s), action, score, tier, rationale (1-2 lines)
3. **Cross-Fund Clusters** — tickers appearing in ≥2 managers (highest-signal section)
4. **Convergence Signals** — candidates also in 13D / congress / dip pools
5. **Anti-Signals** — notable exits/trims by roster managers (SELL intelligence)
6. **Exit Signals** — previously-recommended names triggering exit rules
7. **Dedup Stats** — how many skipped as already-recommended vs new
8. **Next Steps** — which candidates route to multi-lens-quorum, which to watchlist
</output_format>

## Cadence

13F deadlines: ~**Feb 14 / May 15 / Aug 14 / Nov 14** (45 days after quarter-end).
Filings trickle in during the ~6 weeks before deadline.

- **Weekly scan** during filing windows (6 weeks around deadline) — catches new filings as they appear.
- **Biweekly scan** outside filing windows — maintenance/exit-rule checks.
- Dedup makes re-runs safe — already-proposed names get skipped automatically.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Propose a PUT as a buy | Check line type; puts are bearish — drop them (the roster flags managers known to file puts routinely) |
| Re-propose a name from this quarter | `$W seen` before every proposal; dedup by ticker+quarter |
| Treat 13F as real-time | 45-day lag, long-only US snapshot — it's a *finder*, not a trigger |
| Count a trim/exit as a buy | Only `new`/`add` qualify |
| Skip the raw infotable | Aggregators drop positions — reconcile against EDGAR XML |
| Auto-buy / size an order | Recommend-only. Route to quorum; human signs. |
| Omit anti-signals | Large exits are valuable intelligence — always report them |
| Score without convergence check | Cross-feed convergence is the strongest signal; check every time |
| Shallow scan without WHY | Always deep-read: compute deltas AND infer why |
| Ignore portfolio overlap | Cross-reference against the user's book when available |
| Treat institutional-flow bucket as scoring input | Never — corroboration-only, hard-capped at 2, doesn't affect score or tier (`$W record` refuses these managers; use `$W corroborate`) |
| Call Citadel Advisors a "market maker" | Citadel Advisors LLC (files 13F, tracked here) is legally distinct from Citadel Securities (the market maker/broker-dealer) — never conflate them |

## Fit

A **WHICH-finder** (sibling to `stocks-trend-screener`, `analyse-smartmoney-13d`, `analyse-smartmoney-ptr`)
feeding the pipeline:

```
analyse-smartmoney-13f finds → multi-lens-quorum judges → superforecasting times
```

**Distinct from analyse-smartmoney-13d:** 13F is quarterly, long-only, large-cap conviction sizing.
13D is real-time, activist-driven, event-catalyst. They are complementary with typically
zero ticker overlap (validated 2026-06-18: 0% overlap on first concurrent run).

<stop_rules>
- Stop when all roster managers' latest filings are processed, scored, and tiered.
- If no new filings found for a quarter, report "No new 13F filings found" and stop.
- Never fabricate a filing, score, or candidate. Missing data = `[UNAVAILABLE]`.
- Never auto-trade. Output is a recommendation for human review.
</stop_rules>

## Persistence

13F reads are reusable and decay slowly (quarterly). Persist them so the next session builds on them:
- Write a dated overlap doc to `stocks/13f-overlap.md` (or the relevant book's folder) — table + the three callouts + the quarter pinned.
- Save a one-line memory pointer when a finding changes a position thesis (e.g. "Klarman initiated PYPL Q1'26 — validates the deep-value hold"; "Berkshire + Viking both exited UNH Q1'26 — re-underwrite").
- On the next quarterly filing, **diff against the stored doc** rather than starting cold — the *change* in who-owns-what is itself the signal.

## Invariants

1. **Backtest-before-trade** — this skill recommends only. Any actual trade routes through `strategy-discovery-backtest`.
2. **No fabrication** — missing data is `[UNAVAILABLE]`, never invented. If a figure can't be verified against a filing/aggregator, write `unverified` and say what would confirm it (e.g. "pull infotable.xml from EDGAR CIK …").
3. **Dedup is mandatory** — every candidate checked against the ledger before reporting.
4. **Puts are NOT buys** — the roster flags this for any manager known to file puts routinely.
5. **45-day lag** — never treat 13F as real-time or use it alone as a trade trigger. It complements `analyse-fundamental` (your own valuation gate), it does not replace it.
6. **Anti-signals reported** — large exits by smart money are intelligence, not noise.
7. **Don't infer a thesis the manager didn't state** beyond what style + the trade plainly imply; label inference as inference.
8. **Always reconcile against EDGAR infotable** — aggregators drop positions; a surprising number must be verified against the raw XML.
9. **Institutional-flow bucket is corroboration-only and hard-capped** — it can never independently create a candidate or promote a tier; only conviction-bucket managers drive scoring.

> Educational, not advice. 13F is 45-day-lagged and long-only. Recommend-only — never trades.
