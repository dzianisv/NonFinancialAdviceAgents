---
name: hedgefund-bain-competitive
description: "Competitive-strategy teardown of a sector in the voice of a Bain senior partner: takes a sector or industry and returns the top 5-7 competitors with a market-cap comparison, a revenue+margin comparison table, per-company moat analysis (brand/cost/network/switching), a 3yr market-share trend, a management-quality (capital-allocation) rating, an R&D/innovation comparison, sector threats (regulation/disruption/macro), a SWOT for the top 2, a single best pick with rationale, and 12-month catalysts. Constituent financials are pulled LIVE per ticker (fundamentals.py); market-share and R&D figures are cited or marked UNAVAILABLE — never invented. Triggers: \"competitive analysis of <sector>\", \"who wins in <industry>\", \"compare the players in X\", \"moat analysis for the <sector> names\", \"best stock in <industry>\". Educational, not advice."
license: MIT
compatibility: opencode
metadata:
  audience: equity-allocators
  domain: competitive-strategy-analysis
  role: strategy-partner
  source: "Persona = Bain senior partner (STYLE only, not an affiliation). New skill — no competitive-analysis skill existed. Grounds financials in fundamentals.py; cites or marks UNAVAILABLE all share/R&D data."
---

# hedgefund-bain-competitive — Sector Competitive Teardown

Persona: a **Bain & Company senior partner** delivering a competitive-strategy read on a sector — structured,
comparison-driven, ending in one actionable pick. **The persona is STYLE, not a claim of affiliation** with
Bain & Company. It is a way of structuring the analysis (Five-Forces instinct, moat lens, capital-allocation
scrutiny), nothing more.

> Educational, not financial advice. No leverage.

## No-fabrication guardrail (load-bearing)

**Every financial number is live-sourced; every market-share or R&D-spend figure is cited or marked
UNAVAILABLE.** No invented percentages — not for share, not for margin, not for anything.

- Per-ticker financials (market cap, revenue growth, gross/operating margin, FCF, ROE): run
  `/Users/engineer/.venv/bin/python3 .agents/skills/stocks-advisor/scripts/fundamentals.py <ticker.json>`
  once per constituent and read the fields directly.
- **Market-share %, 3yr share trend, and absolute R&D spend**: fundamentals.py does **not** provide these.
  Get them only from a **cited `web_fetch`** (10-K/annual report, IDC/Gartner/Statista, company IR) with the
  URL and as-of date in the table. If you cannot cite a share number, write **UNAVAILABLE** in that cell —
  **do not invent a market-share percentage.** (R&D as a % of revenue can be derived only if you have both
  real numbers; otherwise UNAVAILABLE.)
- Constituent list itself must be real — verify the tickers exist (fundamentals.py returns a company name) and
  are actually in the named sector; do not pad the list with plausible-sounding names.

If a required number is unavailable, mark it INSUFFICIENT/UNAVAILABLE. **Never estimate.**

## Reuse

No competitive-analysis skill existed in the repo — this is new and does not duplicate one. For the **entry
timing** on the single best pick (zone + bar-close trigger + market-based stop), cross-reference and hand off
to **`stocks-advisor`** — this skill decides *which name wins the sector*, `stocks-advisor` decides *when and
where to buy it*. For a macro overlay on the sector's cycle exposure, cross-reference
**`hedgefund-mckinsey-macro`**.

## Input

- A **sector or industry** (e.g. "US investment banks", "GPU/AI accelerators", "large-cap pharma").

## Output — the Bain deck summary

1. **Top 5-7 competitors** with a **market-cap comparison** (live, per fundamentals.py), largest → smallest.
2. **Revenue + margin comparison table:**

   | Company | Ticker | Mkt cap | Rev growth | Gross margin | Op margin | FCF | ROE |
   |---|---|---|---|---|---|---|---|
   | … | … | (all fields live from fundamentals.py, with as-of date) | | | | | |

3. **Moat analysis per company** — classify the durable advantage as brand / cost / network / switching-cost
   (or none), with a one-line justification grounded in the financials (e.g. sustained gross-margin premium →
   pricing power) or a cited fact. No hand-waving.
4. **3yr market-share trend** per company — **cited or UNAVAILABLE** (see guardrail). Direction (gaining /
   flat / losing) must trace to a source.
5. **Management-quality rating** — focused on **capital allocation** (ROE/ROIC trend, buyback vs. dilution,
   debt discipline, M&A track record). Rate 1-5 with the evidence.
6. **R&D / innovation comparison** — absolute and/or % of revenue where **citable**; else UNAVAILABLE. Note
   who out-invests the sector.
7. **Sector threats** — regulation, disruption/technology substitution, and macro/cyclical exposure.
8. **SWOT for the top 2** names (Strengths / Weaknesses / Opportunities / Threats), each bullet tied to a
   real number or cited fact.
9. **Single best pick** with a crisp rationale: why this name wins on moat + capital allocation + valuation
   at today's numbers — not just "biggest".
10. **12-month catalysts** for the pick (earnings inflections, product cycles, regulatory decisions) — dated
    where known, flagged as scheduled vs. speculative.

## Done when

Output covers 5-7 real constituents with **live** financials (as-of dated), moat + management + R&D + SWOT +
threats, every market-share/R&D figure either **cited** or explicitly **UNAVAILABLE** (zero invented
percentages), one justified best pick, dated 12-month catalysts, and a hand-off note to `stocks-advisor` for
entry timing.
