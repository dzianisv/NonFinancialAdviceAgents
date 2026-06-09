# Trend-Stock-Research Evaluation Rubric

Score each dimension 0–5. A dimension marked N/A for a case is excluded from that case's mean.

## Dimensions

### 1. source_grounding
Did the actor actually read and cite real journalism (SA/WSJ/FT/filings), or hallucinate/speculate?

- **5**: Every claim tied to a named source with extractable detail (author, date, or quote). No unsourced assertions.
- **4**: Most claims sourced; 1-2 minor assertions lack explicit citation but are verifiable.
- **3**: Some sources cited but significant claims are unsourced or vaguely attributed ("reports suggest...").
- **2**: Mostly narrative with token citations. Sources named but no specific content extracted from them.
- **1**: Sources mentioned in passing but content is clearly fabricated/hallucinated (wrong facts, non-existent articles).
- **0**: No sources consulted; pure speculation presented as research.

**Failure mode**: "Citation theater" — naming a publication without extracting specific factual content from it.

### 2. non_obvious_discovery
Did the actor map past the obvious leader to find a hidden beneficiary in a different sector?

- **5**: Identified a non-obvious beneficiary that hides in a different sector, with a clear supply-chain logic chain (demand → bottleneck → who controls the bottleneck → why it's hidden).
- **4**: Found a less-obvious name with supply-chain reasoning, but it's in the same sector or partially known.
- **3**: Named a "less covered" company but without rigorous supply-chain mapping. Or identified the bottleneck but not who controls it.
- **2**: Only surfaced obvious leaders that any screen would find (NVDA for AI, TSLA for EVs).
- **1**: Listed trending tickers with no supply-chain reasoning.
- **0**: Did not attempt non-obvious mapping; just listed whatever came up first.

**Failure mode**: "Same-sector obvious" — naming the #2 in the same sector instead of finding the hidden supplier.

### 3. skeptic_discipline
Did the actor apply hard skeptic filters and kill candidates that fail (already priced, no catalyst, no named risk)?

- **5**: Every candidate passed through all 3 skeptic questions explicitly. Majority of initial candidates were killed with stated reasons. Survivors have concrete timelines.
- **4**: Skeptic filter applied to all; most kills are justified. One candidate might have a soft catalyst ("eventually...").
- **3**: Filter applied but too lenient — didn't kill names that are obviously already priced (>150% in 12mo) or lacks concrete timelines for catalysts.
- **2**: Perfunctory skeptic section but no candidates actually killed; everything "survived."
- **1**: Skeptic filter mentioned but not applied meaningfully.
- **0**: No skeptic discipline; all candidates presented as equally valid.

**Failure mode**: "Everything passes" — listing 8+ survivors with no kills, or keeping >150% runners.

### 4. actionability
Are finalists concrete enough for the multi-lens-quorum to make a buy/wait/pass judgment?

- **5**: Each finalist has: ticker, demand inflection (specific), catalyst + timeline (quarter), entry thesis, kill condition, confidence level. Quorum has everything it needs.
- **4**: Mostly complete; one finalist might lack a specific timeline or kill condition.
- **3**: Finalists named with thesis but missing either timeline, kill condition, or confidence level.
- **2**: Tickers listed with vague thesis ("should benefit from AI"). Not enough for the quorum to judge.
- **1**: Just a ticker list with no supporting thesis.
- **0**: No finalists produced; skill stopped at research without synthesizing to actionable output.

**Failure mode**: "Thesis without timeline" — a good story but no specific catalyst date the quorum can anchor on.

### 5. quorum_routing
Does the actor explicitly hand off to multi-lens-quorum and NOT self-decide buy/sell?

- **5**: Explicit routing statement. No buy/sell recommendations made. Confidence flags attached. Clear that this is nomination, quorum decides.
- **4**: Routes to quorum but includes slightly prescriptive language ("strong buy candidate" rather than "routing with HIGH confidence").
- **3**: Mentions quorum but also makes its own recommendation ("I think you should buy X, and the quorum will confirm").
- **2**: No mention of quorum; makes its own buy/sell call.
- **1**: Explicitly recommends "buy now" or "sell" without any routing.
- **0**: Auto-trades or presents itself as the final decision-maker.

**Failure mode**: "Self-deciding" — making the buy call instead of routing to the quorum.

### 6. prescreen_usage
Did the actor use the quantitative scanner as Step 1 to identify hot neighborhoods before reading?

- **5**: Ran or referenced the scanner output, identified which sectors/themes are hot, then focused reading on those areas. Scanner clearly framed as pre-screen (not the answer).
- **4**: Used scanner and directed reading, but didn't explicitly state that scanner is pre-screen only.
- **3**: Mentioned the scanner but didn't clearly use its output to direct the reading effort.
- **2**: Skipped the scanner entirely; jumped straight to reading without directional input.
- **1**: Used only the scanner and declared its output as the answer (no journalism reading).
- **0**: Neither scanner nor reading — produced output from memory/speculation alone.

**Failure mode**: "Scanner-as-answer" — treating the quantitative pre-screen as the stock pick itself.

## Scoring rules

- Mean across applicable dimensions is the round score.
- A case declares which dimensions apply in its `applies:` frontmatter.
- Judge scores the *output quality* — not whether the skill instructions are well-written.
- Score what the actor DID, not what it promised to do.

## Stop condition

- Train mean ≥ 4.2 AND holdout mean ≥ 4.0 AND no dimension below 3.0 → SHIP.
- Or: mean stops rising for 2 consecutive rounds AND holdout has plateaued → CONVERGED (ship best holdout variant).
