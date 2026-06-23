---
name: stock-research-desk
description: Consolidate raw equity gather-seat data into ONE clean, sourced stock/market brief (the evidence file a panel reasons over). Use in the Consolidate phase of the stock research workflow. Triggers — "consolidate the equity brief", "merge the stock data seats", stock-panel Consolidate phase. Produces evidence only, no recommendations.
license: MIT
compatibility: opencode
metadata:
  role: synthesis
  domain: equity-research
---

# Stock research desk — consolidate the brief

Merge the raw data seats into ONE dense, factual brief on the stock(s)/portfolio in question, as of the given date. **No recommendations** — this is the evidence the panel debates.

## Sections (in order)
1. **QUESTION & PORTFOLIO** — restate the user's question + current holdings/exposure verbatim so every downstream seat sees it.
2. **VALUATION & QUALITY** — P/E, EV/EBIT, FCF yield, ROIC/ROE, margins, moat read; price vs fair-value/intrinsic estimate (state the discount/premium).
3. **DRAWDOWN / PRICE LEVEL** — % below 52-week high, distance to support, relevant entry levels.
4. **TECHNICALS / TREND** — price vs 200-day, trend, momentum, breadth context.
5. **INSTITUTIONAL CONVICTION** — 13F initiations/adds/trims, cross-fund clusters (45-day lagged); flag puts/exits.
6. **CONGRESSIONAL BUYS** — recent STOCK Act purchases in the name/sector (30–45 day lag; long-only personal accounts).
7. **EQUITY REGIME** — risk-on vs risk-off, exposure dial.
8. **MACRO (CPI/FOMC/rates/liquidity)** — Fed tone delta, rate path, liquidity backdrop.
9. **NEWS / NARRATIVE** — catalysts + source-count + priced-in tag + url + published_at per event (`[UNAVAILABLE]` if no news seat ran).
10. **CROSS-SOURCE CONFLICTS** — surface disagreements (e.g. cheap on FCF but technically broken); do not average them away.
11. **DATA GAPS**.

## Rules
- Every number keeps its `as-of` + `source`. Quote, don't paraphrase, priced figures.
- **Completeness contract:** if a required category is `[UNAVAILABLE]`, write `[UNAVAILABLE — <category> seat failed to return]` in its section AND list it in §11 DATA GAPS at the top. Never paper over a gap.
- Surface conflicts in §10; do not average them away.
- Be dense and neutral. No verdicts, no sizing, no "should."

## Citation rule — no URL = not a source

Every external claim (news event, data point, quote, analysis) MUST include ALL THREE:
1. **Full URL** fetched: `https://exact-page-url` (specific article, not homepage or search page)
2. **Date** (ISO): `YYYY-MM-DD` (publication or as-of date)
3. **Verbatim quote**: exact words from the page, copied not paraphrased

Format in output: `[TIER] https://exact-url (YYYY-MM-DD) — "verbatim quote"`

**Never write:**
- Source name alone (`CoinDesk`, `Bloomberg`) — without URL it is hallucination bait
- A quote without its URL
- A URL without a date
- Anything paraphrased from memory without a prior web_fetch call

**If fetch failed:** `[FETCH FAILED: https://...] — not counted toward minimum`
**If < 2 real sources:** output `INSUFFICIENT_DATA — do not guess`

## Done when
All 11 sections present; every figure sourced + dated; gaps and conflicts explicit.
