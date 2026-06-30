# TDD — Trend Stock Research Workflow

Covers the equity research track: open-universe candidate discovery → multi-lens verdict → backtest gate → quorum file. Feeds into the SLOW tier of the AI Agent Investment Advisor (`docs/prd.md`, `docs/tdd.md §8`).

RECOMMEND-ONLY. Never trades. Honest-or-`[UNAVAILABLE]`. Backtest gate is Invariant #1 — no order exists until PASS.

---

## 1. Purpose

Find the next NVDA or SanDisk **before** the move — by reading quality financial journalism to understand the demand inflection, supply-chain bottleneck, or re-rating catalyst, then routing high-conviction candidates through independent lenses and a cost-aware backtest.

Static scanners only pre-screen. The real edge is reading analysts who understand *why* a name is waking up.

---

## 2. Pipeline

```
  STEP 1: SCOUT                 STEP 2: JUDGE                   STEP 3: GATE
  ─────────────                 ─────────────                   ────────────
  trend-stock-research          multi-lens-quorum               strategy-discovery-backtest
  (journalism + scan)    ──▶    (4-7 independent lenses)  ──▶   (IS backtest + OOS + costs)
         │                             │                                │
         │                             ▼                                ▼
         │                    research/quorum-{tickers}-      PASS → staged entry plan
         │                    {date}.md                        FAIL → dead-idea log
         ▼
  candidate list
  (no buy signal yet —
   hypothesis only)
```

Three distinct jobs — keep them separate:

| Step | Skill | Job | Output |
|---|---|---|---|
| SCOUT | `trend-stock-research` | *Find WHICH names* | watchlist of hypotheses |
| JUDGE | `multi-lens-quorum` | *Judge WHETHER / how much* | quorum file with verdict per ticker |
| GATE | `strategy-discovery-backtest` | *Validate the ENTRY rule* | PASS/FAIL + cost-adjusted stats |

They **chain**: scout picks → quorum judges → backtest times. Never skip or reorder.

---

## 3. Step 1 — SCOUT: `trend-stock-research`

**Skill:** `.agents/skills/trend-stock-research/`

**What it does:**

1. Runs `emerging_scan.py` — quantitative pre-screen over a ~180-name universe (price momentum, volume, RS). Produces a short candidate list.
2. Reads quality financial journalism (Seeking Alpha, WSJ, FT) for each candidate. Looks for: demand inflection, supply-chain bottleneck, analyst re-rating, margin expansion, category-defining product.
3. Rates each name on *why now* — what is the narrative catalyst that most people haven't priced yet?
4. Outputs a ranked watchlist with one-line thesis per name and a confidence tier (HIGH / MEDIUM / SPECULATIVE).

**Output file:** `stocks/watchlist-{date}.md` (or inline in the quorum input)

**What it is NOT:** a buy signal. It is hypothesis generation. Every name exits this step as a *candidate*, not a recommendation.

**Trigger phrases:** "find trendy stocks", "what's waking up", "find the next NVDA/SanDisk", "scan for emerging stocks", "weekly trend watchlist"

---

## 4. Step 2 — JUDGE: `multi-lens-quorum`

**Skill:** `.agents/skills/multi-lens-quorum/`

**What it does:**

Spawns 4-7 subagents in parallel. Each reads **one** lens/skill and judges the **same** candidate on **identical facts**. Lenses are independent — they do not see each other's verdicts until synthesis.

For equity research, typical lens set:

| Seat | Skill | Focus |
|---|---|---|
| Fundamental | `analyse-fundamental` | valuation, FCF, moat, quality screen |
| Macro | `investor-lyn-alden` or `macro-panel` | regime fit, sector tailwind |
| Positioning | `analyst-derivatives-positioning` | how market is currently positioned |
| Systematic | `analyse-systematic-trading` | whether the entry rule is systematic and testable |
| Behavioral | `research-morgan-housel` | is this chasing, or is this a real opportunity? |
| Sentiment | `analyse-technical` | chart setup, set-up→trigger→follow-through |
| Prediction | `superforecasting` (optional) | calibrated probability of the thesis playing out |

**Synthesis rules:**

- Tabulate each lens: verdict (BUY / HOLD OFF / SELL), conviction (HIGH/MED/LOW), what-would-change-my-mind.
- Surface **agreement** AND **disagreement** — never average away dissent.
- One lens dissenting at HIGH conviction is a flag, not noise.
- Final verdict requires ≥ 3 lenses at BUY and NO lens at HIGH-conviction SELL.

**Output file:** `research/quorum-{tickers}-{date}.md`

Required sections:
```
## Executive Summary
Verdict per ticker: BUY / HOLD OFF / SELL

## Quorum Table
| Lens | Ticker | Verdict | Conviction | Thesis | What changes my mind |
|...

## Dissent Log
Lenses that broke from consensus + their exact reasoning

## Entry Plan (BUY verdicts only)
Tier 1 / Tier 2 / Tier 3 entry levels with sizing rationale

## Invalidation Triggers
Specific, observable events that kill the thesis
```

---

## 5. Step 3 — GATE: `strategy-discovery-backtest`

**Skill:** `.agents/skills/strategy-discovery-backtest/`

**Applies to:** BUY verdicts only. HOLD OFF / SELL do not proceed.

**This step is Invariant #1.** No entry plan reaches a live order without a PASS here.

**What it validates:**

1. **Hypothesis → signal** — translate the quorum thesis into a mechanical entry rule (e.g., "buy CCJ when price pulls back ≥10% from 52w high while above 200dMA and uranium ETF URA is in uptrend").
2. **In-sample backtest (IS)** — 2010–2020, no look-ahead. Signal on prior bar's close.
3. **Walk-forward out-of-sample (OOS)** — 2021–2026. Check for degradation.
4. **Cost adjustment** — minimum 10bps round-trip (commission + spread/slippage). Never show gross returns.
5. **Deflation / multiple-comparison penalty** — if the signal required tuning, apply Bonferroni or a 30% Sharpe haircut.
6. **Stress test** — 2020 crash, 2022 bear, 2008 if available.

**PASS criteria:**

| Metric | Minimum threshold |
|---|---|
| OOS Sharpe (net of costs) | ≥ 0.5 |
| Max drawdown | ≤ benchmark + 10% |
| OOS vs IS Sharpe ratio | ≥ 0.6 (degradation check) |
| Profitable in ≥ 3 of 4 market regimes | required |

**FAIL output:** name goes to `backtests/results/dead-ideas.md` with the thesis that was tested, so it is never re-tested blindly.

**PASS output:** `backtests/results/{ticker}_summary.txt` + chart in `report/img/`. Proceed to staged entry plan.

---

## 6. Staged Entry Plan (post-PASS)

Produced by `multi-lens-quorum` entry section, confirmed against backtest stats.

```
Ticker: CCJ
Thesis: Uranium re-rating, nuclear power policy tailwind, strong balance sheet
Quorum: BUY (5/5 lenses), Conviction: HIGH

Tier 1: $44–46 (current range)     — 0.5% of book
Tier 2: $40–42 (–8% from current)  — 0.75% of book
Tier 3: $36–38 (–16%)              — 1.0% of book

Full position: ~2.25% of book (risk-management cap: ≤3% single name)

Stop: close below $34 (invalidates thesis — below 2024 base)
Target: $58–62 (analyst consensus, 18–24 month horizon)

Backtest edge (OOS 2021-2026): Sharpe 0.71, max DD -22%, win rate 61%
```

---

## 7. Artefact Map

| Step | Artefact | Location |
|---|---|---|
| SCOUT | watchlist with one-line theses | `stocks/watchlist-{date}.md` |
| SCOUT | mention-velocity pool | `stocks/mention_velocity_pool.json` (via `mention_velocity.py`) |
| JUDGE | quorum verdicts file | `research/quorum-{tickers}-{date}.md` |
| GATE (PASS) | backtest summary + chart | `backtests/results/{ticker}_summary.txt`, `report/img/` |
| GATE (FAIL) | dead-idea entry | `backtests/results/dead-ideas.md` |
| ENTRY | staged limit order tickets | appended to quorum file under `## Entry Plan` |

---

## 8. Constraints & Hard Rules

1. **SCOUT output = hypothesis, not recommendation.** Never skip to GATE from a journalism read alone.
2. **Quorum before backtest.** Don't backtest names that fail quorum — it wastes compute and risks data-mining.
3. **BUY verdict only enters GATE.** HOLD OFF and SELL stop at the quorum file.
4. **No look-ahead in backtest.** Signal always uses prior bar's close; splits/dividends adjusted via `yfinance auto_adjust=True`.
5. **Net of costs always.** Gross returns are forbidden in PASS/FAIL verdicts.
6. **Dead ideas are logged, not deleted.** `dead-ideas.md` prevents re-testing the same broken idea.
7. **Dissent preserved.** A single HIGH-conviction dissent in the quorum table is never averaged away — it appears in the dissent log and is considered in position sizing.
8. **Regime gate.** RISK_OFF regime (per `regime-detection`) → no new BUY entries regardless of backtest result. Positions in-flight are not added to.
9. **Max single-name exposure:** 3% of book (risk-management hard cap, enforced in code).

---

## 9. Integration with the Advisor Tiers

This workflow is the **SLOW tier's primary research engine** — it is run weekly (Monday) as part of `hedge-fund-committee.workflow.js`.

The **FAST tier** feeds it: `dip-screener`, `crypto-dip-scanner`, and `signal-convergence-alert` can surface names that then get routed into `trend-stock-research` for journalism verification before entering the quorum.

```
FAST tier alert (dip-screener / convergence)
            │
            ▼  (if alert fires on an equity name)
SLOW tier: trend-stock-research  →  multi-lens-quorum  →  strategy-discovery-backtest
```

A FAST alert does **not** bypass the quorum or backtest gate. It only accelerates the SCOUT step by providing a pre-qualified candidate.

---

## 10. Example Run — 2026-06-17 (FCX / CCJ / ETN)

| Step | Output |
|---|---|
| SCOUT | `trend-stock-research` surfaced FCX (copper/China), CCJ (uranium), ETN (grid infrastructure) from journalism + emerging scan |
| JUDGE | `multi-lens-quorum` ran 4 lenses; verdicts: FCX=HOLD OFF (China demand uncertain), CCJ=BUY (nuclear policy + balance sheet + backtest-ready signal), ETN=HOLD (expensive, wait for pullback) |
| Artefact | `research/quorum-fcx-ccj-etn-2026-06-17.md` written |
| GATE | CCJ only → `backtests/ccj_pullback_backtest.py` (IS 2010-2020, OOS 2021-2026, pullback-in-uptrend signal, 10bps RT) — pending |
| Alerts | FCX limit at $60, ETN limit at $370 — pending (set when HOLD OFF reversal conditions approach) |
