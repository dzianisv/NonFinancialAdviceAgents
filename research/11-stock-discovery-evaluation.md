# 11 — Stock Discovery Pipeline Evaluation (2026-06-17)

*Which of our discovery approaches actually finds pre-move stocks? Run on live data, scored honestly.
Educational analysis, not advice.*

## The question

The repo has **3 independent discovery pipelines** + a **convergence layer** + a **13F institutional
overlay**. Each claims to find the next NVDA/SanDisk before the move. We ran them all on live data
(2026-06-17, regime RISK_ON 0.75) to see what they actually produce and whether they'd have caught
historical winners.

---

## Pipeline-by-pipeline results

### 1. Theme Radar + Emerging Scan (`trend-stock-research`)

**What it does:** Scores 9 pre-defined tech themes by 6-month relative strength and breadth; ranks
stocks within strong themes by momentum.

**What it found (2026-06-17):**

| Theme | Heat | Stage | Leader | 6m RS |
|-------|:----:|-------|--------|:-----:|
| ai-memory-storage | 100 | LATE | SNDK | +866% |
| optical-networking | 89 | LATE | AAOI | +433% |
| ai-compute | 78 | LATE | MU | +324% |
| space-satellite | 67 | LATE | IRDM | +136% |
| datacenter-power | 56 | MID | POWL | +161% |
| quantum-computing | 44 | MID | LSCC | +90% |
| robotics-automation | 33 | MID | TER | +112% |
| nuclear-smr | 22 | WEAK | GEV | +47% |
| defense-tech | 11 | WEAK | MRCY | +51% |

Emerging scan found 73/182 names beating SPY. "Early movers": OKTA, MS, GS, GE, FCX, NET, TGT.

**Verdict: LATE detector.** The top themes are all +100-866% — the move already happened. The
"early movers" are just lower-momentum names in the universe, not fundamental-catalyst-driven
discoveries. The SKILL.md is honest: "Weak edge; hypothesis only."

**Would it have caught NVDA before the move?** Only after NVDA was already the leader of a LATE
theme. Not before.

**Strength:** Gives a structured market map. Useful for understanding *what's happening* and
filtering extended names (don't chase SNDK at +866%).

**Gap:** No demand-inflection signal. The themes are hardcoded (9 themes, curated). A new theme
(e.g., behind-the-meter power for data centers) would need manual addition.

---

### 2. Dip Screener (`dip-screener`)

**What it does:** Screens S&P 100 for quality names ≥20% below 52-week high. Fires alerts when
a HIGH-conviction dip (≥−30%) aligns with RISK_ON regime.

**What it found (2026-06-17):**

| Tier | Names | Notable |
|------|:-----:|---------|
| HIGH (≥−30%) | 16 | NOW −52%, ZTS −52%, ADBE −48%, ACN −48%, ORCL −45%, CRM −42% |
| MED (−25 to −30%) | 5 | MSFT −29%, TMO, DHR, SPGI, REGN |
| WATCH (−20 to −25%) | 3 | META −25%, AVGO −24%, HD −21% |

**Verdict: Quality-on-sale detector.** Finds beaten-down blue chips, not pre-move growth stocks.
This is value-investing reversion, not trend discovery. Useful for the v3 portfolio's equity
sleeve but won't find the next NVDA — NVDA would never appear here (it doesn't dip from highs
during its secular move).

**Would it have caught NVDA before the move?** No. NVDA was not in the S&P 100 before its move.
And momentum stocks don't show up in dip screens by definition.

**Strength:** Reliable, deterministic, runs in <10s, emits pool files for convergence.
The regime cross-check (only alert HIGH dips in RISK_ON) prevents buying into a crash.

**Gap:** S&P 100 only (misses mid/small caps). No thesis — just price mechanics.

---

### 3. Narrative/Journalism Pool (`narrative-news` → `narrative.jsonl`)

**What it found (2026-06-17):**

| Ticker | Narrative |
|--------|-----------|
| INIO | Behind-the-meter gas-engine datacenter power; VoltaGrid 2.3GW order; Jun-2026 IPO |
| CAT | Reciprocating engine capacity 3x 2024; multi-GW genset orders; record $63B backlog |
| LLY | Oral GLP-1 Foundayo FDA-approved Apr-2026 beating Novo; $6.5B Texas API plant |

**Verdict: The only pipeline that finds demand inflections.** INIO (IPO in a hot theme) and CAT
(secular datacenter-power demand) are exactly the kind of catalyst-driven stories that could be
the next NVDA — identified via journalism, not price screens. LLY's oral GLP-1 is a category
catalyst.

**Would it have caught NVDA before the move?** Potentially yes — if it had been reading Jensen
Huang's GTC keynotes and datacenter GPU order announcements in 2022-2023, before the price moved.
The journalism-first approach is the only one that *could* catch a pre-move inflection.

**Gap:** Only 3 entries. The pool is nearly empty because:
- No automated feed pipeline populates it on cron
- `auto_research.py` / the `feed-*` adapters haven't been wired to append to `narrative.jsonl`
- Manual research sessions (e.g., `research.stock.2026-06-15.md`) produce reports but don't
  feed the convergence pool

---

### 4. Signal Convergence (`signal-convergence-alert`)

**Initial run (2026-06-17 AM):** Zero convergences. No ticker appeared in ≥2 sources.

**Root cause (3 bugs):**
1. **Empty 13F pool** — no SEC filings had been pulled.
2. **Date field mismatch** — `convergence.py` checked for `date`/`recorded`/`ts`, but the feeder
   scripts (`watch.py`, `congressman-stock-watch`) write `recommended_on`/`transaction_date`.
   Every entry was silently dropped by the freshness filter. Fixed: added `recommended_on` and
   `transaction_date` to the lookup chain in `convergence.py:55`.
3. **13F pool path mismatch** — `watch.py` writes 13F data to the repo's skill directory
   (`.agents/skills/13f-watch/13f/recommended.jsonl`) but `convergence.py` reads from the
   openclaw workspace (`~/.openclaw/workspace/investor/13f/recommended.jsonl`). Fixed: copied
   data to expected path; long-term fix is to unify pool output paths across all feeders.

**After fixes (2026-06-17, all 4 pools live):** 4 convergences found across 2 signal-pair types:

| Ticker | Sources | Signal |
|--------|---------|--------|
| **SNPS** | Dip + Congress | −31% from 52w high + Rep. Ro Khanna (D-CA) purchased |
| **ISRG** | Dip + Congress | −31% from 52w high + Rep. Ro Khanna (D-CA) purchased |
| **GOOGL** | 13F + Congress | Buffett $15.6B + Rep. David Taylor (R-OH) purchased |
| **KHC** | 13F + Congress | Buffett $7.3B + Sen. Gary Peters (D-MI) purchased |

Two signal-pair types surfaced:
- **Dip × Congress** (SNPS, ISRG): Quality S&P 100 names beaten down ≥30% that a congressman is
  simultaneously buying. This is the "quality-on-sale + institutional interest" convergence.
- **13F × Congress** (GOOGL, KHC): Buffett's large positions that congress-members also purchased.
  This is the "smart-money + insider-access" convergence (note: 13F lags 45 days; congress
  disclosures lag 30-45 days — both are backward-looking).

**Verdict: The plumbing works once wired.** The algorithm is sound; the system was starved
of inputs and had 3 silent wiring bugs (empty pools, date field mismatch, path mismatch).

| Pool | Status | Entries |
|------|--------|:------:|
| `dip_candidates.jsonl` | **LIVE** (wired with `--emit-pool`) | 16 |
| `narrative.jsonl` | Functional, sparse | 3 |
| `13f/recommended.jsonl` | **LIVE** (4 managers Q1 2026, 29 unique tickers) | 35 |
| `congress/recommended.jsonl` | **LIVE** (10 recent purchases) | 10 |

**Remaining gaps:**
- ALLY, COF, LEN (Ro Khanna buys that overlap with Buffett) were identified manually but are not
  in `congress/recommended.jsonl` — the congressional scraper didn't capture them. Adding those
  would raise convergence to potentially 7 tickers.
- No Narrative × Dip or Narrative × 13F convergences yet — the narrative pool (3 entries: INIO,
  CAT, LLY) doesn't overlap with the other pools. This is expected: narrative finds pre-move
  catalysts that by definition haven't dipped or attracted institutional filings yet.

---

### 5. 13F Watch (`13f-watch`) — Expanded to 4 Managers

**What it found:** Q1 2026 (period 2026-03-31) holdings from 4 managers pulled directly from
SEC EDGAR 13F-HR XML filings:

| Manager | CIK | Positions | Filed | Notable holdings |
|---------|-----|-----------|-------|-----------------|
| **Buffett** (Berkshire) | 0001067983 | 8 tickers | 2026-05-15 | OXY $17.2B, GOOGL $15.6B, KHC $7.3B |
| **Ackman** (Pershing Sq) | 0001336528 | 8 tickers | 2026-05-15 | BN $2.4B, AMZN $2.4B, UBER $2.2B, MSFT $2.1B |
| **Klarman** (Baupost) | 0001061768 | 10 tickers | 2026-05-14 | AMZN $650M, QSR $597M, WCC $393M, UNP $374M |
| **Li Lu** (Himalaya) | 0001709323 | 9 tickers | 2026-05-15 | GOOGL $1.4B (52%), PDD $471M, BRK.B $430M |

**Total:** 35 entries in `13f/recommended.jsonl`, covering 29 unique tickers.

**Cross-fund conviction clusters (same ticker, ≥2 managers):**

| Ticker | Managers | Combined $ | Signal strength |
|--------|----------|-----------|----------------|
| **GOOGL** | All 4 (Buffett, Ackman, Klarman, Li Lu) | ~$17.4B | **Highest conviction** — also in Congress pool |
| **AMZN** | Ackman + Klarman | ~$3.1B | Shared growth-at-scale thesis |
| **QSR** | Ackman + Klarman | ~$2.3B | Shared franchise/compounder thesis |
| **OXY** | Buffett + Li Lu | ~$17.3B | Shared energy/hard-asset thesis |

**Convergence with other pools (cross-source overlaps from `convergence.py`):**

| Ticker | Sources | Notes |
|--------|---------|-------|
| **GOOGL** | 13f × congress | 4 managers + Rep. David Taylor — 5-source convergence |
| **MSFT** | dip × 13f | -29.1% from 52w high + Ackman $2.1B |
| **SPGI** | dip × 13f | -25.2% from 52w high + Li Lu $52M |
| **KHC** | 13f × congress | Buffett $7.3B + Sen. Gary Peters |
| **KR** | 13f × congress | Buffett $3.6B + Rep. David Taylor |
| **META** | 13f × congress | Ackman $1.5B + Rep. John McGuire |

**Verdict: Working and expanded.** Multi-manager coverage surfaces cross-fund conviction that
single-manager couldn't: GOOGL is the standout (4 managers + 1 congressman = 5 independent
sources). The Ackman/Klarman overlap (AMZN, QSR) suggests shared value-compounder thesis
filtering. Li Lu's extreme concentration (52% GOOGL) adds signal weight beyond dollar size.

**Key observations:**
- Li Lu's portfolio is a concentrated Buffett meta-bet: GOOGL (52%) + BRK.B (16%) + BAC + OXY
- Klarman is most diversified (22 total positions in filing; 10 recommended) — value/industrial tilt
- Ackman runs ~equal-weight top 3 (~$2.2-2.4B each) — high-conviction concentrated
- MSFT convergence (dip × 13f) is actionable: -29.1% drawdown + Ackman conviction

**Remaining gap:** No automated quarterly pull yet. Each new quarter's filings must be manually
fetched. The `watch.py` dedup logic works correctly (prevents re-recommending known positions).

---

## Comparative scorecard

| Pipeline | Finds pre-move? | Finds quality-on-sale? | Automated? | Pool-wired? | Data richness |
|----------|:---:|:---:|:---:|:---:|:---:|
| Theme Radar | No (LATE) | No | Yes | No | 182 names, 9 themes |
| Dip Screener | No (by design) | **Yes** | **Yes** | **Yes** | S&P 100, 16 entries |
| Narrative/Journalism | **Potentially** | No | **No** (manual) | Partial (3 entries) | 3 entries |
| Convergence | N/A (meta-layer) | N/A | **Yes** | **Yes** (4/4 pools) | **8 convergences** |
| 13F Watch | Lagging (45d) | No | **No** (manual) | **Yes** | 35 entries, 29 tickers (4 managers) |

---

## The core finding

**No pipeline currently catches pre-move stocks.** The theme radar and emerging scan find what
already moved (+100-866%). The dip screener finds beaten-down quality (the opposite signal). The
narrative pool — the only approach that identifies demand inflections — has 3 entries because
nothing feeds it automatically.

**The honest answer to "find the next NVDA":** The journalism-first approach (`trend-stock-research`
SKILL.md's §2 methodology) is the only one with a credible claim, but it's the least automated
and least populated. The scanners are reliable infrastructure that find the *wrong thing* for this
question (momentum after the move, or mean-reversion).

---

## The fix: 3 concrete improvements

### Fix 1: Wire all 4 sources into convergence pools [DONE]

**Status quo (before):** Only `dip_candidates.jsonl` was live. `narrative.jsonl` had 3 manual
entries. `13f/recommended.jsonl` was empty. `congress/recommended.jsonl` didn't exist. The
convergence layer was starved of inputs and had 3 silent bugs.

**Bugs found and fixed:**
- [x] **Date field mismatch** (`convergence.py:55`): added `recommended_on` and `transaction_date`
  to the lookup chain. Without this, every 13F and congress entry was silently dropped.
- [x] **13F pool path mismatch**: `watch.py` writes to `.agents/skills/13f-watch/13f/` but
  `convergence.py` reads from `~/.openclaw/workspace/investor/13f/`. Copied data to expected path.
- [x] **Empty pools**: Ran initial 13F pull (Buffett Q1 2026, 8 tickers) and Congress scrape
  (10 recent purchases). Dip screener `--emit-pool` flag already works.

**Result (initial, Buffett-only):** 4 convergences detected (SNPS, ISRG, GOOGL, KHC) across 2
signal-pair types (Dip×Congress, 13F×Congress). All 4 pools now read by convergence.py.

**Expanded (4-manager 13F, see Section 5):** 8 convergences across 3 signal-pair types
(Dip×Congress, Dip×13F, 13F×Congress). The 4 new hits — MSFT, SPGI, KR, META — emerged only
after adding Ackman, Klarman, and Li Lu holdings.

**Remaining pool gap:** `narrative.jsonl` has only 3 entries and produces no convergences.
Congress scraper is missing some Ro Khanna purchases (ALLY, COF, LEN) that would overlap with
Buffett's 13F.

### Fix 2: Build the "pre-move screen" (the missing pipeline)

None of the 3 existing pipelines catches a stock *before* it moves. The gap is a screen that
combines:
- **Narrative catalyst** (from journalism pool — a demand inflection, not just a headline)
- **Early momentum** (from emerging scan — outperforming SPY but <+50% 6m RS, i.e., not LATE)
- **Institutional flow** (from 13F — a notable manager just initiated a position)

When 2+ of these align on the same ticker, that's the pre-move signal the system is missing.
This is effectively a *specialized convergence* tuned for early-stage names, not the general
"any 2 sources" convergence.

**Action:** Create `pre-move-screen` skill that:
1. Reads `narrative.jsonl` for catalyst-driven names
2. Cross-references against `emerging_scan.py --top 50` for early momentum (RS_6m < +100%)
3. Cross-references against `13f/recommended.jsonl` for institutional initiation
4. Surfaces names with ≥2 of the 3 signals

### Fix 3: Automate the journalism pipeline

The narrative pool is sparse because journalism reading is manual. To make it automated:
- Wire `feed-wsj`, `feed-ft`, `feed-bloomberg` (macro/equity) into a daily scan
- Extract ticker mentions + catalyst summaries → append to `narrative.jsonl`
- Use `crypto-news-store`'s dedup/clustering logic (already built) to prevent duplicates

This is the highest-leverage fix: the journalism pipeline is the only one that finds pre-move
catalysts, and it's currently hand-cranked.

---

## What this means for the fund

1. **The existing pipelines serve different purposes.** Dip screener = defensive equity sleeve
   (buy quality on sale). Theme radar = market map (know what's extended). Convergence = meta-layer
   (still needs inputs). None of them is the "find the next NVDA" tool.

2. **Journalism-first discovery is the real edge** — consistent with note 09's finding that
   mechanical screens don't beat the index. The insight that finds NVDA before the move comes from
   *reading about datacenter GPU demand inflection*, not from screening PE ratios or 52-week highs.

3. **The system's strength is defense, not offense.** The regime/trend/risk/dip machinery is
   excellent at *not losing money* (note 03: max DD −16% vs −55%). Finding the next 10-bagger is a
   different problem with a different answer (journalism + early conviction + institutional flow).

4. **The hedge-fund-committee workflow is the right evaluation stage** — once candidates are found
   by any pipeline, the committee (panel vote → risk veto → scale-in plan) is the quality gate.
   But the committee is only as good as its candidates.

---

*Run date: 2026-06-17. Regime: RISK_ON (0.75). Data: yfinance, live. All results are past/current
observations; no guarantee of future results. Educational, not advice.*
