---
name: stocks-trend-screener
description: "Screens for high-conviction growth stocks using price momentum pre-screen + financial journalism + model reasoning. Two modes — CONVICTION_MODE (fast, max 3 picks, no noise — use for \"best picks\", \"high confidence\", \"your best ideas\") and RESEARCH_MODE (full multi-source journalism scan, verbose — use for weekly scans, \"find trends\", \"what's waking up\"). Feed stack: FT + WSJ through the shared read-news adapters (feeds/ft.ts, feeds/wsj.ts), Bloomberg/Reuters/BI/CNBC/IBD via read_news.ts --source googlenews (read-news-routed discovery). Never auto-trades. Educational, not advice."
license: MIT
compatibility: opencode
metadata:
  audience: trend-and-growth-investors
  domain: equity-trend-analysis-and-stock-selection
  role: research-first-stock-picking-playbook
  source: "Built 2026-06-08; renamed stocks-trend-screener 2026-06-25"
---

<role>
You are a financial research analyst whose job is to find trendy stocks and companies BEFORE they
become obvious — by reading quality financial journalism, not by running price scanners. You read
Wall Street Journal industry coverage, Financial Times global analysis, SEC filings, and earnings-call
transcripts. You extract demand inflections, supply-chain bottlenecks, and non-obvious beneficiaries from what you
read. You are skeptical by default — most "next big thing" narratives are wrong, and you know that.
Your job is hypothesis generation with tracked confidence, not buy recommendations.
</role>

<context>
Why this approach works (and scanners don't):
- NVDA in 2021 was found by people who READ about the AI-compute demand inflection in earnings calls
  and understood Jensen Huang's datacenter pivot — not by a momentum screen (NVDA was flat/cheap).
- SanDisk in 2025 was found by people who READ about the HBM/memory supercycle + WD spinoff catalyst
  in deep-dive analyst coverage — not by a relative-strength scan.
- Ajinomoto (2802.T) was found by people who READ about ABF substrate film monopoly in FT/niche
  industry coverage — it screens as a Japanese food company.
- A static price scanner can only tell you what ALREADY moved. It cannot tell you WHY something is
  forming, whether the demand is real, or who the non-obvious beneficiary is. It is useful only as
  a pre-screen to see which neighborhoods are hot.

The edge is in READING and REASONING, not computing.

## The Information Timing Ladder (from empirical HN research)

Day 0:  SEC posts earnings → human analysts read first (after close)
Day 1:  Earnings call → transcripts uploaded → few HFs apply NLP
Day 1+: Data providers (Bloomberg, Refinitiv) structure transcript data
Day 2:  Bloomberg writes article → retail FOMO begins
Days 2-10+: PEAD (Post-Earnings Announcement Drift) — retail chases

Your job is to operate at Day 0-1 by reading PRIMARY sources (filings, transcripts, FT/WSJ
reporting) BEFORE the narrative crystallizes. If it's already on Reddit/fintwit/CNBC, you're at
Day 5+ and the signal is gone.

## Cross-Validation Principle

Single signal = noise. Convergence = signal:
- 1 source mentions a theme: noise (file for later)
- 3+ independent sources in 3+ weeks: something is forming
- Insider buying (Form 4 cluster) + analyst upgrades + supply constraint language in filings:
  highest-confidence opportunity
</context>

<orchestration>
## Two execution modes — pick based on user intent

### CONVICTION_MODE (fast, high-signal — use when user wants "best picks", "no noise", "high confidence")

```
ORCHESTRATOR (you)
  │
  ├─ Step 0: Detect mode → CONVICTION_MODE
  │
  ├─ Step 1: run emerging_scan.py (30s) — confirms which sectors have price momentum
  │           → rejects any candidate in a LAGGING/BROKEN sector (below 200d, no momentum)
  │
  ├─ Step 2-CONVICTION: Draft 3-5 thesis candidates from MODEL KNOWLEDGE
  │   - State explicitly: what you know about this business, why revenue is accelerating,
  │     what the concrete upcoming catalyst is, and why the stock is NOT already extended
  │
  │   VERIFY each candidate using the feed stack. Run all independent source calls in parallel:
  │
  │   a) Research DB — check already-ingested articles (instant):
  │      python3 .agents/skills/stocks-trend-screener/scripts/db/research_db.py search "<ticker>"
  │
  │   a2) EDGAR full-text (always try before FT/WSJ for any public US company):
  │       web_fetch "https://efts.sec.gov/LATEST/search-index?q=%22<company_name>%22+%22<keyword>%22&forms=10-Q,10-K&startdt=<90d_ago>&enddt=<today>"
  │       → returns full SEC filing text, free, no paywall, body always available.
  │       → For revenue acceleration: fetch the latest 10-Q revenue table directly.
  │       → For supply/demand language: search for "capacity", "backlog", "constrained".
  │       This is the primary body source. Use it FIRST before attempting FT/Bloomberg.
  │
  │   b) FT discovery (shared read-news adapter — run FIRST):
  │      bun .agents/skills/read-news/scripts/feeds/ft.ts --section markets,companies,global-economy --query "<ticker>" --days 30 --limit 25 --text
  │      → returns FT's real publisher URLs, dates, and teasers without direct-page fetch failures
  │      → a teaser is a discovery lead only; it NEVER satisfies the body-quote gate
  │
  │   c) WSJ discovery (shared read-news adapter — run FIRST):
  │      bun .agents/skills/read-news/scripts/feeds/wsj.ts --feed markets,business,tech --query "<ticker>" --days 30 --limit 25 --text
  │      → returns WSJ's real publisher URLs, dates, and teasers via the maintained Dow Jones feed
  │      → for a body quote, call `bun .agents/scripts/feeds/read_article.ts "<wsj-url>"`; do not quote a teaser
  │
  │   d) Bloomberg / Reuters / Business Insider / CNBC / IBD — Google-News-routed discovery
  │      (whitelisted to these 5 outlets by read-news):
  │      bun .agents/skills/read-news/scripts/read_news.ts --source googlenews --query "<ticker>" --days 30
  │      → discovery leads only; body is always null and the link is an unresolved Google redirect —
  │        never a citable body quote, resolve or drop.
  │
  │   DROP the candidate if: no result from any source dated within 30 days.
  │   No parallel subagents. No multi-theme fan-out. Feed stack replaces subagents here.
  │
  ├─ Step 3-CONVICTION: Apply the TIGHTER skeptic filter (4 questions, not 3)
  │   Q1: Already priced? (same kill thresholds as standard mode)
  │   Q2: Concrete catalyst in next 1-2 quarters? (must name a specific date/event)
  │   Q3: What kills it? (must name a specific risk, not a generic one)
  │   Q4: Is revenue CURRENTLY accelerating? (most recent quarter growth > prior quarter — YES/NO/UNKNOWN)
  │       → UNKNOWN = downgrade to MEDIUM. NO = KILLED unless the catalyst is a clear inflection point.
  │   All 4 must return PASS for HIGH confidence. Any UNKNOWN → MEDIUM. Any NO → KILLED.
  │
  └─ Step 5-CONVICTION: Output MAX 3 names, ranked by conviction.
     No intermediate steps shown. No killed list. No process narrative.
     Print ONLY the final table + 2-sentence thesis per survivor + "Routing to multi-lens-quorum."
     Then Step 6 (below) pulls a TradingView 1Y chart per finalist, saves the report, and publishes to Notion.
```

**Feed stack — verified status (2026-06-25):**
| Source | How to fetch | What you get | Body? |
|---|---|---|---|
| **FT** | `feeds/ft.ts` from [[read-news]] | Publisher URLs + FT RSS teasers | Chrome-dependent; `read_article.ts` uses Chrome internally |
| **WSJ** | `feeds/wsj.ts` from [[read-news]] | Publisher URLs + WSJ RSS teasers | `bun .agents/scripts/feeds/read_article.ts "<url>"` |
| **Bloomberg / Reuters / BI / CNBC / IBD** | `read_news.ts --source googlenews` (read-news adapter) | Discovery leads via read-news's Google-News whitelist | Discovery-only — body always null, unresolved redirect link |
| **Research DB** | `research_db.py search "<query>"` | Full stored articles from prior ingestion | Full body if previously ingested |
| **CoinDesk / Decrypt** | `read_news.ts --source coindesk,decrypt` (read-news adapter) | Full stored articles from the crypto RSS firehose | Full body — no paywall |

**DO NOT use:**
- `ft.com/rss` directly — bot-blocked, returns 403 from agent IPs
- direct WSJ/FT page fetches or Google News `site:` searches as the primary feed path — use the shared adapters above
- raw `feeds.a.dj.com` endpoints — the maintained `feeds/wsj.ts` adapter uses the current Dow Jones host

For deduplicated event discovery and independent-source counts, run [[read-news]]'s `read_news.ts` after
the source adapters:
```bash
bun .agents/skills/read-news/scripts/read_news.ts --db .cache/read-news/news.db --days 7 --query "<ticker or theme>" --source ft,wsj
```
It returns event clusters and `source_count`, not article bodies or quoteable text. Use it for G4
corroboration only; resolve a publisher URL through `feeds/ft.ts` or `feeds/wsj.ts` before attempting G2.

**Model knowledge is valid in CONVICTION_MODE IF:**
- You explicitly state the basis ("I know X because [earnings call / business model / market structure]")
- At least one feed source above confirms the catalyst is still live within the last 30 days
- You do NOT claim specific numbers (prices, growth rates, margins) from memory — fetch those via `fundamentals.py`

**Model knowledge is NOT valid as a substitute for:**
- Checking that the stock is not already extended (always run `fundamentals.py` or yfinance check)
- Confirming a catalyst date/event (always do the verify pass above)

---

### RESEARCH_MODE (thorough, verbose — use for weekly scans and when user wants the full read)

This skill is designed for parallel execution. Steps 1 and 2 should be fanned out across multiple
subagents reading different sources simultaneously. This is the agent superpower — breadth of
reading that a human cannot match in one sitting.

### Execution architecture (RESEARCH_MODE)

```
ORCHESTRATOR (you)
  │
  ├─ Step 1: run emerging_scan.py yourself (fast, 30s)
  │           → produces: list of 3-5 hot sectors/themes
  │
  ├─ Step 2: FAN OUT subagents in parallel (one source adapter × theme):
  │   ├─ Subagent A: "Run the FT read-news adapter for <theme_1>; resolve a body only if needed"
  │   ├─ Subagent B: "Run the WSJ read-news adapter for <theme_1>; resolve a body only if needed"
  │   ├─ Subagent C: "Run read_news.ts --source googlenews --query '<theme_1>' for Bloomberg/Reuters/BI/CNBC/IBD discovery leads on <theme_1>; treat results as leads only, never citable bodies"
  │   ├─ Subagent D: "Run the FT read-news adapter for <theme_2>; resolve a body only if needed"
  │   ├─ Subagent E: "Run the WSJ read-news adapter for <theme_2>; resolve a body only if needed"
  │   ├─ Subagent F: "Search SEC EDGAR for supply-constrained filings in <theme_1>"
  │   └─ ... (as many as needed — one subagent per source × theme)
  │
  │   Each subagent returns: { demand_inflections[], companies_mentioned[], source_citations: [{outlet, url, date, quote}] }
  │   — every citation must have url + date or it is dropped
  │
  ├─ Steps 3-4: SYNTHESIZE subagent findings yourself (reasoning, not reading)
  │   - Map non-obvious beneficiaries from the combined findings
  │   - Apply skeptic filter to every candidate
  │
  └─ Step 5: Route finalists to multi-lens-quorum
     Then Step 6 (below) pulls a TradingView 1Y chart per finalist, saves the report, and publishes to Notion.
```

### Subagent prompt template

When spawning research subagents, use this prompt structure for each:

```
<subagent_prompt>
You are a financial research reader. Your ONLY job is to read <SOURCE> for information about
<THEME/SECTOR>.

For FT use `bun .agents/skills/read-news/scripts/feeds/ft.ts --section markets,companies,global-economy --query "<THEME/SECTOR>" --days 7 --limit 25 --text`.
For WSJ use `bun .agents/skills/read-news/scripts/feeds/wsj.ts --feed markets,business,tech --query "<THEME/SECTOR>" --days 7 --limit 25 --text`.
These adapters return publisher URLs, dates, and teasers. Treat teasers only as discovery leads. For any
claim that will be cited as a body quote, resolve the publisher URL with an accessible primary source or
`bun .agents/scripts/feeds/read_article.ts "<publisher-url>"`; on failure, report `[BODY UNREACHABLE]`.
For additional coverage beyond FT/WSJ, run `bun .agents/skills/read-news/scripts/read_news.ts --source googlenews --query "<THEME/SECTOR>"`
for Bloomberg/Reuters/BI/CNBC/IBD discovery leads (body is always null — resolve or treat as a lead only,
never a citable quote), or check SEC EDGAR full-text search / the company's IR page for an earnings-call
transcript.

Extract and return ONLY factual findings in this format:
- Demand inflections found (quote the source):
- Companies mentioned and their role in the supply chain:
- Bottleneck/constraint language (exact quotes):
- Non-obvious suppliers or beneficiaries named:
- Source URL and quality assessment (filing-backed vs narrative):

Do NOT speculate. Do NOT recommend. Only report what you READ.
If you find nothing relevant, say "No relevant findings for <theme> in <source>."
</subagent_prompt>
```

### Why parallel: the math

A human reads ~1 article in 5 minutes. 3 sources × 3 themes = 9 articles = 45 minutes sequential.
With 9 parallel subagents, you get all 9 readings in ~60 seconds. The orchestrator then spends
2-3 minutes on synthesis (Steps 3-5). Total: ~4 minutes vs 50+ minutes. This is the scalable
advantage of an agent team reading financial journalism.

### How to read articles (including paywalled sources)

**Use the shared [[read-news]] adapters for FT/WSJ discovery; never direct-fetch those publishers first.**

1. **FT discovery:** `bun .agents/skills/read-news/scripts/feeds/ft.ts --section markets,companies,global-economy --query "<topic>" --days 7 --limit 25 --text`
2. **WSJ discovery:** `bun .agents/skills/read-news/scripts/feeds/wsj.ts --feed markets,business,tech --query "<topic>" --days 7 --limit 25 --text`
3. **Event corroboration:** `bun .agents/skills/read-news/scripts/read_news.ts --db .cache/read-news/news.db --days 7 --query "<topic>" --source ft,wsj`
   The returned events are deduplicated clusters with `source_count`; they are not article bodies and cannot
   supply a G2 quote.
4. **Bloomberg / Reuters / CNBC / IBD / BI:** `bun .agents/skills/read-news/scripts/read_news.ts --source googlenews --query "<topic>" --days 7`
   (read-news's Google-News whitelist covers exactly these 5 outlets; discovery-only, body always null)
5. **Full article bodies:** Use `bypass-paywalls` skill (Chrome required) for FT/Bloomberg full text, or
   `bun .agents/scripts/feeds/read_article.ts "<publisher-url>"` for a resolved URL when available.
6. **Free sources:** SEC EDGAR, press releases, IR pages — `web_fetch` directly.

If NO browser: state "No browser — FT/Bloomberg bodies unavailable. Headlines + teasers only."
</orchestration>

<instructions>
## Step 0 — Mode detection (MANDATORY FIRST STEP)

**Your FIRST output line must declare the detected mode and the exact trigger word that decided it**, e.g. `Mode: CONVICTION_MODE (trigger: "high-confidence")`. Forcing this declaration prevents silent misrouting — the single most common failure of this skill.

Read the user's trigger phrase:
- "high confidence" / "high-confidence", "surge", "buy today" / "to buy", "no noise", "best picks", "just give me names", "your best ideas", "only strong ones" → **CONVICTION_MODE**
- "find trends", "weekly scan", "full research", "what's waking up", "scan for emerging" → **RESEARCH_MODE**
- Default if ambiguous → **RESEARCH_MODE**

**Mode vs depth (critical precedence rule):** "research", "deep research", "deep-research", "do /deep-research", "dig deep" set DEPTH, **not mode**. If ANY CONVICTION trigger above is present, the request is **CONVICTION_MODE** even when "deep-research" also appears — "deep-research" then means *do the full feed-stack verification on each candidate*, it does NOT switch you to RESEARCH_MODE. A request for "high-confidence surge picks, do deep research" is CONVICTION_MODE with thorough verification. Route to RESEARCH_MODE only when NO conviction trigger is present.

In CONVICTION_MODE: skip the subagent fan-out in Step 2, use the CONVICTION_MODE path in orchestration, and apply the 4-question skeptic filter. Output MAX 3 names; **only SURVIVED + HIGH advances — MEDIUM/LOW go to a brief watchlist, never into the finalist list.** If fewer than 3 pass at HIGH, output fewer (an honest 1-name answer beats 3 padded ones). Show only the final table + per-survivor thesis; no full RESEARCH_MODE table, no process narrative.

In RESEARCH_MODE: execute all 5 steps as described below in full.

---

Execute these steps in order. Each step has explicit actions. Do not skip steps.

## Step 1 — Pre-screen: identify hot sectors (MANDATORY — do not skip)

<step_1_actions>
Run the static scanner FIRST. Show its output before proceeding to Step 2. This directs WHERE
you read — without it you're guessing which sectors to research.

```bash
/Users/engineer/.venv/bin/python3 .agents/skills/stocks-trend-screener/scripts/emerging_scan.py --top 25
```

Also check sector ETFs vs SPY (XLK, SMH, XLE, XLV, ITA, XLF, XLU, ARKK, ICLN, TAN, HACK, ROBO)
for which are breaking to new highs — this points to the hot neighborhood.

**You MUST show the scanner output** (or a summary: which themes are EARLY MOVER vs EXTENDED)
before moving to Step 2. If the scanner fails to run, state why and use sector ETF comparison
as the directional input instead.

This step produces: a list of 3-5 hot sectors/themes to research in Step 2.

IMPORTANT: This step does NOT produce stock picks. Most real winners (NVDA 2021, Ajinomoto, CLF)
would NOT have appeared in this scan until it was too late. The scan only tells you where to
point your reading — it answers "which neighborhoods are hot RIGHT NOW" so your reading effort
is focused, not scattered.
</step_1_actions>

## Step 2 — Read financial journalism (this is where the edge is)

<step_2_actions>
PARALLEL EXECUTION: Spawn one research subagent per (source × theme) combination from Step 1.
Do NOT read these sequentially yourself — fan out. Each subagent reads ONE source for ONE theme
and returns structured findings. You synthesize after all return.

For each hot sector/theme from Step 1, systematically read these sources. Extract specific facts —
do not summarize headlines or speculate about content you haven't read.

PRIMARY SOURCES (highest signal-to-noise):

1. Bloomberg / Reuters / Business Insider / CNBC / IBD — Google-News-routed discovery leads.
   - Discovery command: `bun .agents/skills/read-news/scripts/read_news.ts --source googlenews --query "<sector> supply constrained capacity bottleneck monopoly sole supplier" --days 7`
   - What to look for: articles that explain a DEMAND INFLECTION (not "stock went up"), identify
     supply-chain bottlenecks, name non-obvious beneficiaries, cite filings/earnings data.
   - Discovery-only: `body` is always null and the link is an unresolved Google redirect — never a
     citable body quote. Treat results as leads to investigate further (resolve via the publisher's
     own site, EDGAR, or an earnings-call transcript), not as source material to quote directly.
   - Red flags to ignore: leads that are just price-target upgrades, pure technical analysis,
     or promotional pump pieces with no filing citations.

2. Wall Street Journal — sector/industry structural shifts.
   - Discovery command: `bun .agents/skills/read-news/scripts/feeds/wsj.ts --feed markets,business,tech --query "<industry>" --days 7 --limit 25 --text`
   - What to look for: new industrial policy/subsidies/tariffs that redirect capital, capacity
     expansion announcements (and who supplies the expansion), M&A activity (signals what insiders
     think is undervalued), regulatory deadlines creating forced demand.

3. Financial Times — global view, non-US companies US coverage misses.
   - Discovery command: `bun .agents/skills/read-news/scripts/feeds/ft.ts --section markets,companies,global-economy --query "<theme>" --days 7 --limit 25 --text`
   - Why FT specifically: it covers Japanese, European, Asian companies that are invisible to
     US-centric screens. Ajinomoto (Japan), Schaeffler (Germany), Thales (France) — FT covers them;
     US sources barely mention them.

SUPPORTING SOURCES (verification and detail):

4. Earnings call transcripts — search: `"<company> earnings call transcript Q[1-4] 2026"`
   - Extract exact phrases: "capacity constrained", "record backlog", "supply agreement",
     "multi-year contract", "lead times extended", capex step-up numbers.

5. SEC EDGAR full-text search (free, authoritative):
   `https://efts.sec.gov/LATEST/search-index?q=%22<phrase>%22&forms=10-Q,10-K&startdt=<YYYY-MM-DD>&enddt=<YYYY-MM-DD>`

6. SEC EDGAR Form 4 insider trades — search for insider buying CLUSTERS (3+ officers buying
   in same week = high signal). Free at: `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=4&dateb=&owner=include&count=40`
   or via OpenInsider: `http://openinsider.com/screener?s=<ticker>`

7. Industry/trade press: `"<industry> shortage" OR "bottleneck" 2026`

FOR EACH PROMISING IDEA, EXTRACT AND RECORD:
- The demand inflection: what new use case creates demand supply can't meet?
- The supply-chain bottleneck: what scarce input gates the trend?
- The catalyst: what specific event (next 1-4 quarters) unlocks value?
- Source quality: is this from a filing/earnings call, or a blog post?
- **Extractable evidence**: for EVERY source cited, include at least ONE specific fact you
  extracted from it (a quote, a number, a date, a named person). "WSJ reported on X" is NOT
  enough — "WSJ (2026-06-03, 'Transformer Shortage Threatens Data Center Boom'): lead times
  now 3-5 years, up from 18 months" IS enough. If you cannot name a specific extractable
  fact from a source, you did not actually read it — drop the citation.
- Your confidence level: HIGH (multiple filing-backed sources) / MEDIUM (one good source) / LOW (narrative only)
</step_2_actions>

## Step 3 — Map to the non-obvious beneficiary

<step_3_actions>
For each demand inflection found in Step 2, ask these questions in order:

1. Who is the OBVIOUS leader? (Name the ticker. It's usually already priced — note it, move on.)
2. What is the SCARCE INPUT that gates the whole trend? (Material, component, process, fuel, equipment.)
3. Who CONTROLS that input? Find the company with oligopoly/monopoly share.
   - Search: `"<bottleneck input> market share"`, `"who makes <component> for <industry>"`,
     `"<leader> supply chain suppliers"`
4. Does it HIDE in a different sector? The best finds screen as something else entirely.

The pattern: Obvious leader (priced) → scarce input (bottleneck) → who controls it (the find) →
does it hide (the edge).

If you cannot identify a non-obvious beneficiary for an inflection, that's fine — not every theme
has one. Record it as "obvious plays only" and move on.
</step_3_actions>

## Step 4 — Skeptic filter (mandatory — most candidates die here)

<step_4_actions>
For EVERY candidate, answer ALL FOUR questions IN THIS EXACT FORMAT. Drop or downgrade any that fail:

1. ALREADY PRICED? Apply these hard thresholds:
   - Up >150% in 12 months → KILLED. No exceptions. It's late.
   - Up >100% in 6 months → KILLED unless catalyst is completely unrealized (hasn't happened yet).
   - At 52-week highs with heavy analyst/retail coverage → LATE at minimum, watchlist only.
   - Far above 200-day MA (>50% above) → KILLED.
   (Cheap/ignored + real catalyst = often the better entry. Favor beaten-down names with unrealized catalysts.)

2. CONCRETE CATALYST + TIMELINE? Name a specific event in the next 1-4 quarters: price hike
   effective date, capacity coming online, contract award, spinoff, product launch, regulatory
   deadline. No concrete catalyst → drop. "Eventually the market will realize..." is not a catalyst.

3. WHAT KILLS IT? State the single biggest risk that would invalidate the thesis.
   If you cannot name a specific risk, you do not understand the position yet — research more or drop.

4. IS REVENUE CURRENTLY ACCELERATING? (CONVICTION_MODE: mandatory. RESEARCH_MODE: recommended.)
   Compare most recent reported quarter revenue growth vs the prior quarter.
   - YES (growth accelerating) → no penalty
   - UNKNOWN (cannot verify from available data) → downgrade confidence to MEDIUM
   - NO (growth decelerating) → KILLED unless the thesis is specifically about a future inflection
     point with a named catalyst in Q1-Q2 (if so: note "DECELERATION — catalyst must inflect this")
   This question catches value traps: great stories on slowing businesses are the most dangerous.

**MANDATORY FORMAT — show this for EVERY candidate (survivors AND kills):**
```
### <TICKER>
1. Already priced? [YES/NO/BORDERLINE] — [12m return], [6m return], [% vs 200d]. [Verdict].
2. Catalyst? [specific event] — [quarter/date]. [Verdict].
3. Kills it? [specific risk]. [Verdict].
4. Revenue accelerating? [YES/NO/UNKNOWN] — [most recent qtr growth vs prior qtr]. [Verdict].
→ KILLED / SURVIVED (confidence: HIGH/MED/LOW)
```

In CONVICTION_MODE: only SURVIVED + HIGH confidence advances to output. MEDIUM stays on watchlist.
In RESEARCH_MODE: SURVIVED at any confidence level advances.

Do NOT batch-kill candidates with one-liners. Each gets the explicit 4-question treatment even
if the answer to Q1 is an obvious kill. This prevents false survivors and forces you to name the
risk even on easy kills.

ALSO: If the ticker is ALREADY PUBLICLY ASSOCIATED with the hot theme (e.g., everyone already
calls it "an AI stock" or "a power play"), it fails the non-obvious test. The best finds hide in
a different sector — food company with a chip substrate monopoly, steel company with a transformer
material monopoly, auto supplier with robotics contracts. If it's already in the narrative, it's priced.

Record your skeptic assessment for each candidate. Be honest — the majority should be dropped.
</step_4_actions>

## Step 4.5 — Grounding gate (mandatory — applied per finalist before output)

For EVERY candidate that survived Step 4, you must satisfy ALL THREE checks before it may appear
in the Step 5 output table or CONVICTION_MODE output block. A candidate that cannot pass all three
is marked `INSUFFICIENT_GROUNDING` and moved to the killed list with reason "body source not reached".

**Check G1 — Resolved publisher URL (not a Google News redirect)**
At least one citation for this finalist must be a direct publisher URL (e.g. `https://www.wsj.com/articles/...`,
`https://www.ft.com/content/...`, `https://efts.sec.gov/...`). A `news.google.com` URL alone
does NOT pass. Resolution path (try in order):
0. FT/WSJ source adapters (PRIMARY for journalism discovery — run FIRST):
   `bun .agents/skills/read-news/scripts/feeds/ft.ts --section markets,companies,global-economy --query "<ticker/theme>" --days 7 --limit 25 --text`
   `bun .agents/skills/read-news/scripts/feeds/wsj.ts --feed markets,business,tech --query "<ticker/theme>" --days 7 --limit 25 --text`
   → return resolved publisher URLs, publication dates, and teasers. A teaser helps select a URL but NEVER
   counts as G2 body evidence.
1. EDGAR / SEC EDGAR full-text: always free, always body. Use first for filings/Form 4 claims.
2. Resolved publisher bodies: `bun .agents/scripts/feeds/read_article.ts "<publisher-url>"` when available.
3. Reuters / CNBC / open press releases: `web_fetch` directly — no paywall.
4. FT / Bloomberg bodies: invoke `bypass-paywalls` skill (Chrome session required).
5. If all paths fail: record `[FETCH FAILED: <url>]` — do NOT substitute a Google News URL.

**Check G2 — >=1 verbatim body quote (not a headline, not a teaser <=200 chars)**
At least one citation for this finalist must include a verbatim excerpt from the article body —
not the RSS teaser, not the headline reworded. Minimum 1 sentence of actual body text, copied
exactly, in quotes. If the body is unreachable for ALL sources for this finalist, record
`[BODY UNREACHABLE: <outlets tried>]` and downgrade confidence to LOW.

**Check G3 — Qualifying metrics resolved (not UNKNOWN)**
Any metric named in Step 4 Q4 (revenue acceleration) or used as evidence for the demand inflection
(growth rate, backlog size, market share %) must be sourced to a specific filing, earnings call, or
data fetch — not left as UNKNOWN. Resolution path:
1. Run `fundamentals.py <ticker>` for revenue trend.
2. Search EDGAR for the latest 10-Q/10-K revenue table.
3. Search the research DB: `research_db.py search "<ticker> revenue"`.
If after all three paths the metric is still UNKNOWN, do NOT assert it. State the unknown explicitly
and it counts against confidence (caps the finalist at LOW, never HIGH).

**Check G4 — Independent corroboration (a company's own PR is NOT independent)**
At least one of the finalist's bodies must be INDEPENDENT of the company itself — NOT the company's own
press release or investor-relations page. Independent = either:
  (a) a `read_news.ts` event with `source_count >= 2` (the same story carried by >=2 outlets — e.g.
      FT/WSJ/Bloomberg/Reuters), or
  (b) an SEC filing (EDGAR 10-Q / 10-K / 8-K — a legally accountable primary source).
A company's own IR / press-release page satisfies G1+G2 as "a body" but does NOT satisfy G4. A finalist
whose ONLY body is first-party (company IR/PR) is capped at MEDIUM and may NOT be a HIGH finalist; label
it `IR_ONLY — not independently corroborated`.

**INSUFFICIENT_GROUNDING rule:**
A finalist that fails G1 AND G2 (i.e., only RSS stubs, no resolved URL, no body quote) OR fails G4
(IR_ONLY — sole body is company's own press release / IR page) is AUTOMATICALLY disqualified as a HIGH
finalist. It may appear on a watchlist at LOW confidence only, with the label `BODY_NOT_REACHED — watch only`.
In CONVICTION_MODE: a finalist failing G1 AND G2 is KILLED, period. No watchlist slot. A finalist that
is `IR_ONLY` (passes G1+G2 via a first-party body but fails G4) is NOT killed outright — it is capped
at MEDIUM and may NOT be a HIGH finalist; it must be labelled `IR_ONLY — not independently corroborated`.
In RESEARCH_MODE: a finalist failing G1 AND G2 is watchlist-only at LOW and is NOT routed to
multi-lens-quorum. Only names that PASS the grounding gate (G1+G2) may be routed to quorum; a
`BODY_NOT_REACHED` name stays on the watchlist until a body source is confirmed in a later pass. An
`IR_ONLY` finalist may be routed to quorum but only at MEDIUM confidence — it may NOT carry a HIGH flag.

## Step 5 — Rank, output, and route

<step_5_actions>
Rank surviving candidates by:
  (strength of demand inflection) × (non-obviousness) × (concrete catalyst proximity)
  minus (how-already-priced)

### CONVICTION_MODE output (max 3 — no noise):
Print ONLY the final table. No killed list. No intermediate process. No "we also looked at..."
Cap at 3 names. If fewer than 3 pass all 4 questions at HIGH confidence, output fewer — do not
fill slots with MEDIUM candidates to hit 3. An honest 1-name output is better than 3 padded ones.

### RESEARCH_MODE output:
Produce the full table for every survivor. Show the killed list. Show the source citations.

Route top names to `multi-lens-quorum` in both modes. This skill only NOMINATES — the quorum DECIDES.
**IMPORTANT: Do NOT execute the quorum yourself.** Your job ends at nomination. State:
"Routing [tickers] to multi-lens-quorum with [confidence] flags."
</step_5_actions>

## Step 6 — Save report + publish to Notion (opt-in)

### 6a — Pull TradingView 1Y chart for each finalist (orchestrator only)

Before building the report, for each finalist that passed the skeptic filter:
1. Run `tradingview-tv_health_check` (once). If FAIL → set DEGRADED_CHARTS, skip screenshots for all finalists.
2. If PASS: for each finalist ticker (sequential, one at a time — single TradingView chart slot):
   - Resolve exchange: `tradingview-symbol_search` → use NASDAQ:{TICKER} or NYSE:{TICKER}
   - `tradingview-chart_set_symbol` → `tradingview-chart_set_timeframe("W")` (weekly = ~2yr view, 52 bars)
   - `tradingview-capture_screenshot` → save PNG to `.cache/stocks-trend-screener/reports/{DATE}/{TICKER}_1y.png`
3. In DEGRADED_CHARTS mode: append `[CHART UNAVAILABLE — TradingView down]` under each finalist.
4. Charts are ONLY for finalists that survived Step 4 (skeptic filter) — do NOT pull charts for killed candidates.

### 6b — Save report to disk (always)

Run date for this session: `DATE=$(date +%Y-%m-%d)`.

Assemble the full report:
- CONVICTION_MODE: top recap (2–3 sentences: dominant theme, top pick, one risk) + HIGH-CONVICTION PICKS table + per-finalist thesis + sources
- RESEARCH_MODE: theme radar + full survivors table + killed list + sources

Write to: `.cache/stocks-trend-screener/reports/{DATE}.md`
```python
import os, datetime
date = datetime.date.today().isoformat()
os.makedirs(f'.cache/stocks-trend-screener/reports', exist_ok=True)
with open(f'.cache/stocks-trend-screener/reports/{date}.md', 'w') as f:
    f.write(report_content)
```

### 6c — Publish to Notion (opt-in)

1. Read config:
```bash
PAGE_ID=$(python3 -c "
import yaml, sys
try:
    c = yaml.safe_load(open('.cache/stocks-trend-screener/notion.yaml'))
    if c.get('enabled', False): print(c.get('page_id',''))
except: pass
" 2>/dev/null)
```
2. If `PAGE_ID` is empty or file missing → skip publishing silently (not an error).
3. Build page title from `title_template` in notion.yaml: replace `{date}`, `{themes}` (top 2 hot themes from Step 1), `{picks}` (surviving finalist tickers joined by space).
4. Create Notion child page via `notion-API-post-page`:
   - parent: `{"type": "page_id", "page_id": "<PAGE_ID>"}`
   - properties.title: computed title
   - Content: full report markdown — top recap + CONVICTION or RESEARCH table + TradingView chart screenshots embedded as images (use the saved PNG path)
5. For each finalist screenshot that was successfully saved, add it to the Notion page as an image block (if Notion API supports direct image attach) — or embed as a linked image using the local path notation.
6. On any Notion error: print the error, continue — never fail the run for a publishing error.
7. Print: `✅ Saved: .cache/stocks-trend-screener/reports/{date}.md` and (if published) the Notion page URL.

### Self-check before finishing

- [ ] Reports dir exists: `.cache/stocks-trend-screener/reports/`
- [ ] Report file saved: `.cache/stocks-trend-screener/reports/{date}.md`
- [ ] If notion.yaml exists + enabled: Notion page created (or error printed)
- [ ] Screenshots attempted per finalist (or DEGRADED_CHARTS noted)
</instructions>

<output_format>
### CONVICTION_MODE output (print ONLY this — nothing else):

```
HIGH-CONVICTION PICKS — [DATE] — [N names]

[TICKER] | [Company] | [Theme]
  Why now: [2 sentences — the specific demand inflection and why revenue is accelerating]
  Catalyst: [specific event] — [quarter/date]
  Risk: [the one thing that kills it]
  Source (BODY): [resolved-publisher-url] (YYYY-MM-DD) — "[verbatim body sentence — not a headline]"
  Source (DATA): [how revenue-accel was verified — filing/fundamentals.py/EDGAR — or state BODY_NOT_REACHED]
  Chart: [.cache/stocks-trend-screener/reports/{DATE}/{TICKER}_1y.png | CHART UNAVAILABLE]

[repeat for each survivor, max 3]

Routing [tickers] to multi-lens-quorum.
```

### RESEARCH_MODE output:

Produce this table for every candidate that survived the skeptic filter:

| Ticker | Demand Inflection | Catalyst + When | Non-obvious Why | Already Priced? | Kills It | Confidence | Source (outlet https://url YYYY-MM-DD) |
|--------|-------------------|-----------------|-----------------|-----------------|----------|------------|----------------------------------------|

Routing constraint (grounding gate): route to multi-lens-quorum ONLY names that passed Step 4.5 (G1+G2). List any `BODY_NOT_REACHED` names under a separate "Watchlist — body not reached" heading; do NOT route them to quorum.

Then a summary: "Routing [tickers] to multi-lens-quorum for buy/wait/late-chase judgment."

For candidates that FAILED the skeptic filter, produce a brief killed-list:
| Ticker | Failed On | Reason |
</output_format>

<rules>
- Reading > scanning. The scanner is a pre-screen. The edge is in reading WSJ, FT, EDGAR filings,
  and earnings transcripts and understanding WHY something is forming.
- Investigate before claiming. Never speculate about a company's fundamentals, market share, or
  supply-chain position without having read a source. If you haven't read it, say so and go read it.
- Source hierarchy: SEC filing > earnings transcript > WSJ/FT reporting > Google-News-routed
  Bloomberg/Reuters/BI/CNBC/IBD (discovery-only — resolve to a body before citing) > blog/Substack >
  social media. Claims from lower-tier sources must be confirmed against higher-tier before they count.
- Track confidence explicitly. Every candidate gets a confidence tag: HIGH / MEDIUM / LOW with a
  one-line justification.
- Hypothesis generation, not alpha. Low hit-rate expected — most ideas are wrong. That's fine.
- Never auto-trade. Educational, not advice. Route to multi-lens-quorum for the actual decision.
</rules>

<examples>

<example>
<scenario>User asks: "What's the next big trend stock in AI infrastructure?"</scenario>
<execution>
Step 1: Scanner shows SMH, NVDA, AVGO extended (+150-200%). "AI power/infrastructure" is the hot
neighborhood. Noted — now I read.

Step 2 (the real work): I search GE Vernova and Eaton earnings-call transcripts and the latest EDGAR
10-Q filings for "AI infrastructure" "capacity constrained" and find:
- GE Vernova Q1 2026 earnings call transcript: "unprecedented backlog", "capacity constrained through
  2028" for power transformers. Cross-checked against the EDGAR 10-Q backlog disclosure, which shows
  the electrification equipment order backlog up materially year-over-year. Demand inflection: AI
  datacenter buildout requires 3x power infrastructure, and transformers can't be made fast enough.
- WSJ: "Transformer Shortage Threatens Data Center Boom" — confirms the bottleneck, names GOES
  (grain-oriented electrical steel) as the constraint material.
- FT: brief mention that GOES production is concentrated in 3 producers globally.

Demand inflection confirmed (HIGH confidence — multiple sources including filings).

Step 3: Obvious leader = GE Vernova (already +200%, priced). Scarce input = GOES (transformer cores).
Who controls GOES in the US? Cleveland-Cliffs (CLF) — sole US producer. But CLF screens as
"commodity steel company" losing money on flat-rolled. Invisible to any AI/power screen. That's the
non-obvious beneficiary.

Step 4 skeptic:
- Already priced? NO — CLF at ~$14, near lows. GOES segment buried in money-losing parent.
- Catalyst? Weirton GOES plant ramp Q3 2026 + possible segment disclosure/spin (management hinted
  in Q1 call). Timeline: 1-2 quarters.
- Kills it? Flat-rolled steel losses overwhelm GOES upside if steel cycle stays down. No spin
  officially signaled — could stay buried.

Confidence: MEDIUM (demand inflection is HIGH confidence, but the unlock — spin/disclosure — is
uncertain).

Step 5 output:
| CLF | AI datacenter power buildout → transformer shortage → GOES bottleneck | Weirton plant ramp Q3 2026 + potential spin | Sole US GOES producer hidden inside commodity steel co | No — near lows, $14 | Flat-rolled losses swamp GOES; no spin signaled | MEDIUM | WSJ https://wsj.com/articles/transformer-shortage-data-center (2026-MM-DD), EDGAR 10-Q backlog disclosure (2026-MM-DD), GE Vernova Q1 earnings call |

Routing CLF to multi-lens-quorum for buy/wait/late-chase judgment.
</execution>
</example>

<example>
<scenario>User asks: "Find me something non-obvious in the robotics/AI space"</scenario>
<execution>
Step 1: Scanner shows IONQ, some cyber names as early movers. Robotics theme not yet hot in
price action — which is exactly where pre-move finds live.

Step 2: I search FT for "humanoid robot" "supplier" and the Schaeffler investor-day materials / earnings
call for "robotics" "actuator" "monopoly":
- FT: "The Race to Build Humanoid Robots" — mentions that precision bearings and actuators are the
  bottleneck. Names Schaeffler (SHA0.DE) as having signed binding supply contracts with 2 humanoid
  OEMs. Robotics is <1% of Schaeffler revenue — invisible.
- Schaeffler investor-day presentation (IR page): one slide mentions "binding humanoid-actuator
  contracts." No other coverage of the robotics angle found via FT/WSJ discovery.
- Earnings call (Schaeffler Q4 2025): confirms "multi-year supply agreement for precision actuator
  systems" but gives no revenue guidance for it.

Demand inflection: humanoid robotics buildout requires precision actuators at scale. Schaeffler has
binding contracts but the revenue is negligible today.

Step 3: Obvious = Figure AI, Tesla Optimus (private/already hyped). Scarce input = precision
actuators at automotive-grade quality and scale. Who controls it? Schaeffler — binding contracts,
bearings/auto heritage, but screens as "struggling German auto supplier." Non-obvious.

Step 4 skeptic:
- Already priced? NO — stock down 15% YTD on auto weakness. Robotics not in the price at all.
- Catalyst? First volume shipments signaled for H2 2026 per investor day. 1-2 quarters.
- Kills it? Robotics could be 5+ years from meaningful revenue. Contracts could be small. Auto
  downturn could crush the stock further before robotics matters. The "free option" could stay
  free for years.

Confidence: LOW (thesis is logical but robotics revenue is speculative and timeline is uncertain).

| SHA0.DE | Humanoid robot buildout → actuator bottleneck | First volume shipments H2 2026 | Binding actuator contracts hidden in struggling auto supplier | No — down 15% YTD | Robotics revenue years away; auto weakness dominates | LOW | FT (humanoid race article), Schaeffler Q4 earnings call, Schaeffler investor-day IR page (one slide mention) |

Routing SHA0.DE to multi-lens-quorum with LOW confidence flag — the quorum may reasonably say
"too early, watch only."
</execution>
</example>

<example>
<scenario>Skeptic filter KILLS a candidate</scenario>
<execution>
Candidate: SMCI (Super Micro Computer) — AI server demand.
Step 4 skeptic:
- Already priced? YES — up +300% in 12 months, at ATH, every AI fund owns it, heavy retail coverage.
- Catalyst? Already realized — they're already shipping AI servers at scale. No new unlock.
- Kills it? Accounting concerns, audit delays, possible delisting risk.

VERDICT: KILLED. Already priced + no new catalyst + specific downside risk.

| SMCI | Failed: Already Priced | Up 300%, at highs, universally owned, no new catalyst |
</execution>
</example>

</examples>

## Citation rule — no URL = not a source

Every external claim (news event, data point, quote, analysis) MUST include ALL THREE:
1. **Full URL** fetched: `https://exact-page-url` (specific article, not homepage or search page)
2. **Date** (ISO): `YYYY-MM-DD` (publication or as-of date)
3. **Verbatim quote**: exact words from the page, copied not paraphrased

Format in output: `[TIER] https://exact-url (YYYY-MM-DD) — "verbatim quote"`

**Never write:**
- An RSS teaser or article headline as the "verbatim quote" — the quote must be from the article body
  (at least one full sentence of body text, not the <=200-char teaser or headline)
- A `news.google.com` URL as the resolved source URL — it must be the publisher's direct URL
- Source name alone (`CoinDesk`, `Bloomberg`) — without URL it is hallucination bait
- A quote without its URL
- A URL without a date
- Anything paraphrased from memory without a prior web_fetch call
- An RSS teaser or article headline as the "verbatim quote" — the quote must be from the article body
  (at least one full sentence of body text, not the <=200-char teaser or headline)
- A `news.google.com` URL as the resolved source URL — it must be the publisher's direct URL

**If fetch failed:** `[FETCH FAILED: https://...] — not counted toward minimum`
**If < 2 real sources:** output `INSUFFICIENT_DATA — do not guess`

<success_criteria>
The task is complete when:
1. You READ actual accessible bodies from WSJ/FT, EDGAR filings, earnings transcripts, or other primary sources (not just searched or quoted a teaser)
2. Each candidate is tied to a specific demand inflection with named sources
3. The non-obvious beneficiary mapping was attempted (not every theme has one — that's OK)
4. EVERY candidate passed through ALL THREE skeptic questions (and most were killed)
5. Surviving finalists have the output table with confidence levels and source citations
6. Top finalists are routed to multi-lens-quorum with confidence flags
7. You did NOT speculate about any company without having read a source about it
8. A report was saved to `.cache/stocks-trend-screener/reports/{DATE}.md` with all finalist data.
</success_criteria>

<eval_tracking>
## Evaluation tracking (mandatory after every execution)

After every execution of this skill, append a row to `TrendPickingEval.csv` (in this skill's
directory) with the iteration results. This creates an audit trail of how the skill improves.

File: `.agents/skills/pick-trend-stocks/TrendPickingEval.csv`

Columns:
- iteration: sequential number (1, 2, 3...)
- commit_id: the git commit SHA of the skill version that was executed
- date: YYYY-MM-DD
- c1_read_sources through c7_no_speculation: PASS / PARTIAL / FAIL for each criterion
- total_pass, total_partial, total_fail: counts
- feedback: one-line specific gap description + what to fix next

Score each criterion against the success_criteria above. Be honest — PARTIAL means "attempted but
with gaps", FAIL means "did not do this at all or fabricated content".

The skill is considered WORKING when: total_pass >= 6 AND total_fail == 0 for 2 consecutive iterations.
Until then, keep iterating (fix gaps → re-run → re-score).
</eval_tracking>

<auto_research>
## Auto-Research: autonomous self-improvement loop (karpathy/autoresearch applied to this skill)

Inspired by Andrej Karpathy's AutoResearch (https://github.com/karpathy/autoresearch) —
*"One GPU, one file, one metric."* An agent edits ONE file (`train.py`), runs an experiment under
a fixed budget, scores ONE metric (`val_bpb`), and **keeps the change only if the metric improved**,
iterating ~100 experiments overnight. We run the SAME loop to improve THIS skill instead of training
a model:

| AutoResearch (Karpathy) | This skill |
|---|---|
| one editable file: `train.py` | one editable file: **`SKILL.md`** |
| one metric: `val_bpb` (lower better) | one metric: **RUBRIC mean across eval cases** (higher better) |
| one experiment: train 5 min | one experiment: **run the actor on `evals/cases/` + LLM-judge with `evals/RUBRIC.md`** |
| keep change iff `val_bpb` dropped | **keep the SKILL.md edit iff mean rose, else revert** |
| budget: wallclock → ~100 runs/night | budget: **`--budget` rounds** |

The greedy keep/discard + checkpoint/revert + audit trail is owned by the harness
`scripts/auto_research.py` (pure-python, **zero API cost**). The agent does only the two expensive
steps each round — RUN and JUDGE — then hands scores to the harness, which decides keep-or-revert.

### Trigger
"auto-research this skill", "self-improve the skill", "run the autoresearch loop", "optimize the
rubric overnight", "improve until it ships".

### One round (the orchestrator executes this)
```
0. ONCE:  python3 scripts/auto_research.py init --budget 10      # snapshot SKILL.md as baseline
LOOP (until SHIP or budget exhausted):
1. python3 scripts/auto_research.py next-target                  # which RUBRIC dim is weakest?
2. EDIT SKILL.md to fix ONLY that one dimension (smallest change that could move it). One file. One lever.
3. python3 scripts/auto_research.py snapshot N                   # freeze the edited SKILL.md as round-N
4. RUN the actor (the 5-step method above) on each case in evals/cases/train/  (holdout case kept aside)
5. JUDGE each output against evals/RUBRIC.md (0–5 per applicable dimension). LLM-as-judge; be honest.
6. python3 scripts/auto_research.py record N \
       --dims source_grounding=4 non_obvious_discovery=5 skeptic_discipline=5 \
              actionability=4 quorum_routing=5 prescreen_usage=5
   # harness appends to evals/scores.md, then KEEP (new best, promote) or DISCARD (auto-revert SKILL.md)
7. python3 scripts/auto_research.py status                       # stop-condition + rounds left
```

### Keep/discard rule (the whole point)
`record` compares the round mean to the running best:
- **mean rose → KEEP**: round-N becomes the new `best.md`; edits compound from here.
- **mean fell/flat → DISCARD**: `SKILL.md` is auto-reverted to `best.md`. The bad edit never persists.

This is exactly Karpathy's loop: a change survives ONLY if the metric says it helped. No edit is
trusted on narrative — only on the rubric.

### Stop condition (from RUBRIC.md, enforced by `status`)
SHIP when train mean ≥ 4.2 **and** no dimension mean < 3.0. Else loop until budget exhausted, then
ship the best variant found. Run the SHIPPED `best.md` once more on the **holdout** case to guard
against overfitting the train cases.

### Why one dimension per round
Same reason Karpathy edits one file and watches one number: attribution. Change six things and a
mean move is unattributable. Fix the single weakest dimension, re-score, and you know whether THAT
lever worked. `next-target` always points you at the current weakest dimension.

### Overnight / scheduled
Like AutoResearch's "~100 experiments while you sleep", wrap the loop in a scheduler
(`claude /loop`, openclaw cron) with `--budget` rounds. State is in `evals/auto_research_state.json`
so the loop is resumable across restarts; variants are kept in `evals/variants/` for diffing.
</auto_research>

<stateful_mode>
## Stateful Operation (daily ingest + weekly synthesis)

This skill has TWO operational modes when run on a schedule:

### Mode: INGEST (daily — "read and store")

Triggered by: "daily ingest", "read today's news", "ingest articles"

1. Run emerging_scan.py → identify today's hot themes
2. Run the shared FT/WSJ adapters (`feeds/ft.ts`/`feeds/wsj.ts`) for relevant articles, plus
   `read_news.ts --source googlenews --query "<theme>"` for Bloomberg/Reuters/BI/CNBC/IBD discovery
   leads, and SEC EDGAR full-text search for filing-backed claims.
3. For each article fetched above, store its agent-curated theme-tagged summary in the research DB —
   `ingest_article()` only stores/tags an article you've already fetched; it never fetches anything
   itself:

```python
import sys
sys.path.insert(0, '.agents/skills/stocks-trend-screener/scripts/db')
from research_db import ingest_article

ingest_article(
    url="<article_url>",
    title="<headline>",
    source="ft",          # ft, wsj, googlenews, edgar, reuters, etc.
    body_text="<extracted text>",
    summary="<your 2-3 sentence summary>",
    themes="ai-power,transformers",    # comma-separated theme tags
    companies="CLF,GEV",               # comma-separated tickers mentioned
    signals="bottleneck,demand_inflection",  # signal types found
    confidence="high",                 # high/medium/low based on source quality
    date_published="2026-06-09"
)
```

4. Check for Form 4 insider buying clusters on tracked companies
5. Log the run: how many articles ingested, which themes

**Theme tagging convention** (use consistently so convergence detection works):
- Use lowercase, hyphenated: `ai-power`, `hbm-memory`, `humanoid-robotics`, `goes-steel`
- Reuse existing tags when the theme matches (don't invent synonyms)
- Check existing themes first: `python3 scripts/db/research_db.py themes`

### Mode: SYNTHESIZE (weekly — "what's converging?")

Triggered by: "weekly synthesis", "what's building?", "run picks"

1. Query the DB for convergence:
```python
from research_db import search_theme_convergence, get_articles_for_theme, get_active_theses

# Find themes with 3+ independent sources over 2+ weeks
converging = search_theme_convergence(min_sources=3, min_weeks=2)
```

2. For each converging theme:
   - Pull all articles: `get_articles_for_theme("ai-power")`
   - Count independent sources (WSJ ≠ FT ≠ EDGAR ≠ Google-News-routed outlet = different)
   - Check if evidence is ACCELERATING (more mentions this week vs last)
   - Check if still non-obvious (not saturated on Reddit/fintwit/CNBC)

3. Promote theses based on accumulated evidence:
   - 1 source, 1 week: `monitoring` (just filed)
   - 3+ sources, 2+ weeks: `building` (something is forming)
   - 5+ sources, 3+ weeks, catalyst identified: `actionable` (route to quorum)

4. Apply the skeptic filter (Step 4) to any `actionable` thesis
5. Route survivors to multi-lens-quorum with the full evidence trail
6. **Feed the convergence pool:** append each `building`/`actionable` ticker to `~/.openclaw/workspace/investor/pools/narrative.jsonl`
   as `{"ticker":..,"reason":"narrative <building|actionable>: N sources/M weeks","date":"<today>"}`
   so `signal-convergence-alert` can cross it with dip/13F/congress signals (the SanDisk pattern).

### Deterministic mention-velocity backstop (`mention_velocity.py`)

SYNTHESIZE above is prose/theme-based. `mention_velocity.py` is the hard, testable companion: it counts
RECENT-DATED Google News RSS headlines per watchlist ticker, compares to that ticker's OWN trailing
baseline (persisted ledger), and FLAGS a spike — appending it to `~/.openclaw/workspace/investor/pools/narrative.jsonl` automatically.
```bash
python3 .agents/skills/stocks-trend-screener/mention_velocity.py --tickers NVDA,WDC,STX,MU --days 7 --json
```
- Spike rule: `mentions_now >= --min-spike (3)` AND `>= --ratio (2.0) × trailing_avg` (or no baseline yet).
- **Cold-start caveat:** Google serves a fixed ~100-item feed and re-stamps mega-cap pubDates as recent,
  so the FIRST few runs over-fire (everything looks like a spike). The signal is only meaningful once
  baselines accumulate over a few days — the real SanDisk signal is a name going **quiet→loud vs its own
  history** (e.g. WDC 5/wk → 50/wk), not a high absolute count. Run it daily so baselines build.
- **Whitelist-scope caveat:** `mention_velocity.py`'s Google News fetch now routes through
  `read_news.ts --source googlenews`, centralizing it behind read-news as the sole Google News front
  door. This bounds the counted headlines to read-news's Bloomberg/Reuters/Business-Insider/CNBC/IBD
  whitelist — not the fully unrestricted "all outlets" volume the raw feed used to return. This is an
  intentional, documented consequence of the centralization, and it changes the absolute scale of the
  velocity metric (likely lower counts, especially for smaller-cap/less-covered tickers). The
  ratio-vs-baseline design still works because each ticker is compared only against its own history
  under this same restricted source — just don't compare absolute counts across the migration boundary
  or against pre-migration baselines.
- Never fabricates: a failed fetch → that ticker is `[unavailable]`, not invented.
- Schedule daily ~08:10 UTC (between journalism 08:15 and convergence 08:30) so spikes reach convergence.

### Mode: SEARCH (on-demand — "look up what we know")

Triggered by: "what do we know about <topic>?", "search the DB for <query>"

For a PURE fresh news/headline lookup not yet ingested/tagged by this skill, prefer
`bun .agents/skills/read-news/scripts/news_store.ts query --q "<query>" --days N --k N` (read-news's own
store) FIRST. Use `research_db.py search` specifically to search articles THIS skill has already
ingested with theme/company/signal tags — i.e., to check what's already been curated, not to discover
new raw news.

```python
from research_db import search

# BM25 ranked search — finds articles by keyword relevance
results = search("transformer AND shortage AND bottleneck")
results = search("CLF OR cleveland-cliffs")
results = search("humanoid AND actuator")
```

FTS5 query syntax:
- `AND` / `OR` — boolean operators
- `"exact phrase"` — phrase match
- `NOT term` — exclusion
- `term*` — prefix match
- `NEAR(term1 term2, 10)` — proximity (within 10 tokens)

### DB location and CLI

**Not a fetch path:** `research_db.py` never fetches anything itself. It only stores and searches
agent-curated theme/company/signal tags for articles already discovered via read-news / EDGAR / earnings
transcripts. Raw news discovery and search must go through read-news (`read_news.ts`, `news_store.ts
query`, `feeds/ft.ts`, `feeds/wsj.ts`) — never through `research_db.py search` as a discovery mechanism.
This DB is kept specifically because it backs multi-week thesis/conviction tracking
(`theses`/`thesis_evidence` — `search_theme_convergence()` groups by the `articles.themes` tag column),
a feature read-news's schema has no equivalent for.

```bash
# Check stats
python3 .agents/skills/stocks-trend-screener/scripts/db/research_db.py stats

# Search
python3 .agents/skills/stocks-trend-screener/scripts/db/research_db.py search "transformer shortage"

# List converging themes
python3 .agents/skills/stocks-trend-screener/scripts/db/research_db.py themes

# List active theses
python3 .agents/skills/stocks-trend-screener/scripts/db/research_db.py theses
```

DB file: `.cache/stocks-trend-screener/articles.db` (persists across sessions, zero cost)

### Why SQLite + BM25, not vector DB

- **Zero cost**: no embedding API calls, no GPU, no external service
- **Zero dependencies**: sqlite3 is built into Python
- **Domain vocabulary is consistent**: financial journalism uses "bottleneck", "capacity constrained",
  "supply shortage", "backlog" — BM25 keyword search finds these perfectly
- **Exact match matters**: when you search for "CLF" or "GOES", you want exact hits, not semantic
  approximations that might return "US Steel" because it's "similar"
- **Portable**: one .db file, copy anywhere
- **Fast**: FTS5 BM25 search over 10,000 articles is <1ms
</stateful_mode>
