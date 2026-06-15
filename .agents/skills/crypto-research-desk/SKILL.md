---
name: crypto-research-desk
description: Consolidate raw gather-seat data into ONE clean, sourced crypto market brief (the evidence file a panel reasons over). Use in the Consolidate phase of the crypto research workflow. Triggers — "consolidate the brief", "merge the data seats", crypto-panel Consolidate phase. Produces evidence only, no recommendations.
license: MIT
compatibility: opencode
metadata:
  role: synthesis
  domain: crypto-research
---

# Crypto research desk — consolidate the brief

Merge the raw data seats into ONE dense, factual brief on the asset/portfolio in question, as of the given date. **No recommendations** — this is the evidence the panel debates.

## Sections (in order)
1. **QUESTION & PORTFOLIO** — restate the user's question + current holdings/exposure verbatim so every downstream seat sees it.
2. **PRICE & TREND** · 3. **ON-CHAIN VALUATION** · 4. **DERIVATIVES / POSITIONING** · 5. **MACRO (CPI/FOMC/rates)** · 6. **LIQUIDITY FLOWS** · 7. **SENTIMENT / REGIME** · 8. **NEWS / NARRATIVE** (events + source-count + priced-in tag; `[UNAVAILABLE]` if no news seat ran) · 9. **PREDICTION-MARKET ODDS** · 10. **CROSS-SOURCE CONFLICTS** · 11. **DATA GAPS**.

## Rules
- Every number keeps its `as-of` + `source`. Quote, don't paraphrase, priced probabilities.
- **Completeness contract:** if a required category is `[UNAVAILABLE]`, write `[UNAVAILABLE — <category> seat failed to return]` in its section AND list it in §11 DATA GAPS at the top. Never paper over a gap.
- Surface conflicts (e.g. liquidity expanding vs contracting) in §10; do not average them away.
- Be dense and neutral. No verdicts, no sizing, no "should."

## Done when
All 11 sections present; every figure sourced + dated; gaps and conflicts explicit.
