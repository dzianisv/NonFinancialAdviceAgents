---
name: pick-trend-stocks
description: Research-first method to pick trendy stocks by reading quality financial journalism (Seeking Alpha, WSJ, Financial Times) — the only approach that has worked to find the next NVDA/SanDisk BEFORE the move. Static scanners can only pre-screen; the real insights come from reading analysts who understand the demand inflection, supply-chain bottleneck, and catalyst. Use when asked "find trendy stocks", "what companies are trending", "analyze the market for opportunities", "what should I buy", "find the next NVDA/SanDisk", "what's the next big trend", "research a sector for winners", or to build a weekly trend-stock watchlist. Hypothesis generation, not a buy signal; never auto-trades. Educational, not advice.
license: MIT
compatibility: opencode
metadata:
  audience: trend-and-growth-investors
  domain: equity-trend-analysis-and-stock-selection
  role: research-first-stock-picking-playbook
  source: "Built 2026-06-08; research-reading method proven by experience (NVDA 2021, SanDisk 2025)"
---

# Pick Trend Stocks — a research-first playbook

The core truth: **reading quality financial journalism is the only method that has worked to find
winners early** (NVDA in 2021, SanDisk in 2025). Static price scanners find trends AFTER they've
already moved. They can pre-screen — but the edge is in reading and reasoning over what good
analysts are writing about demand shifts, supply constraints, and catalysts.

## The method (5 steps)

### Step 1 — Pre-screen: what sectors/themes are hot (optional, fast)

Run the static scanner to see what's already moving — this is AWARENESS ONLY, not where ideas come from:
```
/Users/engineer/.venv/bin/python3 .agents/skills/trend-scout/scripts/emerging_scan.py --top 25
```
Also glance at sector ETFs (XLK, SMH, XLE, XLV, ITA, XLF, XLU, ARKK, ICLN) vs SPY.

This tells you which neighborhoods are hot. **It does NOT tell you what to buy or what's forming
before the move.** Most of the real finds (NVDA 2021, Ajinomoto, CLF) wouldn't have shown up here
until it was too late.

### Step 2 — READ: the real research (this is where the edge is)

Read the following sources systematically. This is the step that actually finds winners early.

**Primary sources (highest signal):**
- **Seeking Alpha** — deep-dive articles on individual companies. Search for thesis-driven
  pieces on sectors/themes from Step 1. Look for articles that explain WHY demand is inflecting
  (not just "stock went up"). The best SA articles identify supply-chain bottlenecks and non-obvious
  beneficiaries before the market catches on.
  - Search: `site:seekingalpha.com "<sector/theme>" "supply constrained" OR "capacity" OR "bottleneck"`
  - Look for: multi-part deep dives, supply-chain analysis, "hidden gem" thesis articles
  - Pay attention to: author track record, whether claims are backed by filings/data

- **Wall Street Journal** — sector/industry coverage, earnings analysis, M&A, regulatory shifts.
  WSJ catches structural shifts (policy changes, trade restrictions, capex cycles) that create
  demand inflections. Read the business section daily; scan for:
  - New industrial policy / subsidies / tariffs that redirect capital
  - Capacity expansion announcements and who supplies the expansion
  - M&A activity (signals what insiders think is undervalued)
  - Search: `site:wsj.com "<industry>" "shortage" OR "backlog" OR "capacity" OR "supply chain"`

- **Financial Times** — global/macro view, European/Asian companies US coverage misses. FT is
  especially good for finding non-US beneficiaries invisible to US-centric screens.
  - Companies like Ajinomoto (Japan), Schaeffler (Germany), Thales (France) — FT covers them;
    US sources barely mention them.
  - Search: `site:ft.com "<theme>" "monopoly" OR "market share" OR "sole supplier"`

**Supporting sources:**
- **Earnings call transcripts** — search for: "capacity constrained", "record backlog",
  "supply agreement", "multi-year contract", "lead times extended", capex step-ups.
  Pattern: `"<company> earnings call transcript Q[1-4] 2026"`
- **SEC EDGAR full-text search** — free, authoritative:
  `https://efts.sec.gov/LATEST/search-index?q=%22<phrase>%22&forms=10-Q,10-K&startdt=<YYYY-MM-DD>&enddt=<YYYY-MM-DD>`
- **Industry/trade press** — `"<industry> shortage / bottleneck 2026"`

**What to extract from reading:**
For each promising idea, note:
1. The **demand inflection** — what new use case creates demand supply can't meet?
2. The **supply-chain bottleneck** — what scarce input gates the trend?
3. The **non-obvious beneficiary** — who controls that input but screens as something else?
4. The **catalyst** — what specific event (next 1-4 quarters) unlocks value?
5. The **source quality** — is this from a filing/earnings call, or a blog post?

### Step 3 — Map to the non-obvious beneficiary (the SanDisk/Ajinomoto pattern)

The biggest winners are usually one layer DOWN from the obvious leader — the picks-and-shovels
that supply the bottleneck.

For each inflection found in Step 2, ask:
1. **Who is the obvious leader?** (usually already priced — note it, move on).
2. **What is the scarce INPUT that gates the whole trend?** (material, component, process, fuel,
   equipment).
3. **Who controls that input?** Find the company with **oligopoly/monopoly share**.
4. **Does it hide in a different sector?** The best finds screen as something else (Ajinomoto =
   "food"; Cleveland-Cliffs GOES = "steel") so no thematic screen sees them. Invisibility = edge.

### Step 4 — Skeptic filter (MANDATORY — most candidates die here)

For every candidate, answer all three. Drop or downgrade any that fail:
- **Already priced?** Up >100% in 6-12mo? At highs with everyone covering it? → LATE; watchlist
  only. (Cheap/ignored + real catalyst is often the better entry.)
- **Concrete catalyst + timeline?** A specific event in the next 1-4 quarters (price hike,
  capacity online, contract, spinoff, product, regulatory deadline). No catalyst → drop.
- **What kills it?** State the single biggest disconfirming risk. If you can't name it, you
  don't understand it yet — research more or drop.

### Step 5 — Judge, rank, and route

Rank survivors by: strength of demand inflection × non-obviousness × concrete catalyst, minus
how-already-priced. Then hand top finalists to **`multi-lens-quorum`** for the buy / wait /
late-chase call and sizing. Research only NOMINATES; the quorum DECIDES. Never auto-trade.

## Output format

| Ticker | Inflection (demand driver) | Catalyst + when | Non-obvious why | Already priced? | Kills it | Confidence | Sources (SA/WSJ/FT/filing) |

## Honest rules (non-negotiable)

- **Reading > scanning.** The scanner is a pre-screen. The edge is in reading Seeking Alpha, WSJ,
  FT — understanding WHY something is forming, not seeing that a price moved.
- **Hypothesis generation, not alpha.** Low hit-rate — most ideas are wrong. That's expected.
- **Source quality matters.** Claims from blogs/promotions must be confirmed against primary
  sources (filings, earnings calls, company releases) before they count. SA articles backed by
  filing data >> SA articles with just narrative.
- **Track every call's outcome** over time — the only way to learn if the method works.
- **Never auto-trade.** Educational, not advice.

## Example — how CLF (Cleveland-Cliffs) was found

<example>
1. Pre-screen: the scanner flags "AI power/infrastructure" as hot. Awareness only.
2. READ (the real work): FT + WSJ articles on the transformer-shortage crisis. SA deep-dive titled
   "The Hidden Monopoly In Electrical Steel" explains that grain-oriented electrical steel (GOES)
   is the bottleneck for power transformer manufacturing. Earnings calls from transformer OEMs
   repeat "lead times 3-5 years", "capacity constrained".
3. Non-obvious beneficiary: obvious = GE Vernova (already +200%). Bottleneck = GOES.
   Cleveland-Cliffs (CLF) is the SOLE US producer of GOES — but screens as "commodity steel",
   invisible to any AI/power screen. That's the find.
4. Skeptic: priced? No — ~$14, near lows, money-losing commodity division masks it. Catalyst?
   Weirton GOES plant ramp + potential segment spin. Kills it? Flat-rolled losses swamp GOES upside;
   no spin signaled yet.
5. Route CLF to multi-lens-quorum for the buy/size call.
</example>

## Done when

The analysis (1) read SA/WSJ/FT for demand inflections and supply-chain insights, (2) mapped each
to the non-obvious beneficiary, (3) passed candidates through the skeptic filter, (4) routed
finalists to multi-lens-quorum, and produced the output table with sources cited.
