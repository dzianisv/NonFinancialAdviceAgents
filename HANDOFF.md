# Handoff — AI Supply Chain Research + Paywall Bypass
**Date:** 2026-06-20  
**Branch merged:** `feature/per-asset-pipeline-research-market` → `main`

---

## What was done this session

### 1. research-market workflow — 6 runs, AI supply chain focus

Ran the full `research-market` workflow autonomously to screen the next AI supply chain surge candidates (NVDA/INTC/QCOM/MU/SNDK tier). Six runs completed:

| Run | Tier focused | Key findings |
|-----|-------------|--------------|
| 1–2 | Initial screen | AMKR, PLAB, ONTO, KLIC, VICR, RMBS, AEHR found |
| 3 | PCB/thermal | Zero buys; chair directed CRDO/ALAB/SVCO for run 4 |
| 4 | Networking/EDA/optical | PLAB/ASYS/CLFD WAIT; rest AVOID |
| 5 | CRDO validated | CRDO: WAIT, BUY_ON_TOUCH $178–192 |
| 6 | Final screen | PLAB BUY_ON_TOUCH $29–31; CAMT BUY_ON_TOUCH $165–170; rest AVOID |

**Live verdicts (as of 2026-06-20):**
- **PLAB** T2 WAIT | entry $29–31 | catalyst: Q3 FY2026 margin >34% + Allen TX/Korea revenue H2
- **CAMT** T2 WAIT | entry $165–170 | catalyst: HBM inspection ramp + CoWoS expansion
- **CRDO** T2 WAIT | entry $178–192 | catalyst: volume scaling from hyperscaler 800G orders
- All others (BELFB, NVTS, MOD, KULR, AEHR): AVOID

Reports at `research/research.equity.2026-06-20.md`

---

### 2. Per-asset reasoning added to workflow output

`research-market.workflow.js` now emits `selection_reason` and `rejection_reason` per asset in the report. Every run produces a `## Per-asset reasoning` section explaining why each name was chosen or cut.

**Files changed:**
- `.agents/workflows/research-market.workflow.js` — `DECISION_SCHEMA.per_asset` + chair prompt + report template

---

### 3. Paywall bypass — archive.ph abandoned → Chrome live

`archive.ph` proved unusable (Cloudflare CAPTCHA every session, no headless bypass). Replaced with Chrome live via CDP: the script navigates to FT/WSJ/Bloomberg using your existing Chrome session with subscription cookies.

**What works now:**
- `bun .agents/scripts/feeds/read_article.ts <url>` — cache → Chrome live → Wayback → direct
- Chrome live validated on open sites (Reuters). FT/WSJ requires user login (see below)
- Bloomberg: CDP bot-detected ("Are you a robot?") — Chrome live does NOT work for Bloomberg headlessly

**Dead services documented (do not retry):** archive.ph, 12ft.io, Google cache, Bing cache, outline.com, textise.net

**Files changed:**
- `.agents/scripts/feeds/read_article.ts` — full rewrite, Chrome live primary, Wayback fallback
- `.agents/skills/bypass-paywalls/SKILL.md` — updated to document Chrome live approach + dead services
- `.agents/skills/feed-ft/SKILL.md` — body reading section updated

---

### 4. Article cache

SQLite cache at `~/.agents/cache/articles.db` (FTS5). Seven feed skills updated to ingest bodies. `fetch_article.py --by-url` for exact lookup, `--search` for FTS, `--ingest` to store.

---

## What still needs to be done

### P0 — Validate Chrome live FT extraction (BLOCKED on user login)

Chrome live has never been observed succeeding on a real paywalled FT/WSJ article. The mechanism is proven correct (Reuters ✓, tab polling ✓, DOM extraction ✓) but the paywall bypass itself requires your FT session cookie.

**One-time step:**
1. Open Chrome → navigate to `https://www.ft.com` → sign in with FT subscription
2. Run:
   ```bash
   bun /Users/engineer/workspace/backtest/.agents/scripts/feeds/read_article.ts \
     "https://www.ft.com/content/1d37cc08-e0aa-45a4-a45d-4ad282529314" --no-cache
   ```
3. Verify: article body printed to stdout, exit 0, >500 chars, no "Subscribe to read"

If WSJ subscription is easier: same process at `wsj.com`.

### P1 — Bloomberg CDP bot detection

Bloomberg shows "Are you a robot?" in Chrome when driven via CDP. Need to either:
- Solve the CAPTCHA manually once and hope session persists
- Use a stealth CDP approach (e.g. puppeteer-extra-plugin-stealth injected headers)
- Accept Bloomberg as unavailable via this method and fall back to Google News RSS teasers only

### P2 — FT/WSJ news in research-market workflow

The `NewsFetch` phase currently gets FT/WSJ headlines from Google News RSS (teasers only, no body). Once Chrome login is set up (P0 above), the `read_article.ts` script will auto-fetch full bodies. No workflow change needed — the script is already in the ladder.

### P3 — Next research-market run targeting P2 watchlist

Three WAIT signals are live. Next triggers to watch:
- **PLAB**: Q3 FY2026 earnings (August 2026) — watch for margin >34%
- **CAMT**: HBM inspection revenue confirmation in Q2'26 report
- **CRDO**: Next hyperscaler 800G order announcement

Run `research-market` again when any of these fires or monthly (whichever first).

---

## Key file locations

| Asset | Path |
|-------|------|
| Research workflow | `.agents/workflows/research-market.workflow.js` |
| Article reader | `.agents/scripts/feeds/read_article.ts` |
| Article cache | `~/.agents/cache/articles.db` |
| Bypass skill | `.agents/skills/bypass-paywalls/SKILL.md` (global: `~/.agents/skills/bypass-paywalls/SKILL.md`) |
| FT feed skill | `.agents/skills/feed-ft/SKILL.md` |
| Latest equity report | `research/research.equity.2026-06-20.md` |
| Memory log | `.agents/memory/2026-06-20.md` |
