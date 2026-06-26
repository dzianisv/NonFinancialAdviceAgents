# Iteration 1 — Round 1 (v0 baseline)

## Scores

| Dimension | Case 01 (AI infra) | Case 04 (trap) | Mean |
|---|---|---|---|
| source_grounding | 4 | 3 | 3.5 |
| non_obvious_discovery | 5 | N/A | 5.0 |
| skeptic_discipline | 4 | 4 | 4.0 |
| actionability | 5 | 4 | 4.5 |
| quorum_routing | 5 | 4 | 4.5 |
| prescreen_usage | 2 | 2 | 2.0 |

**Overall mean: 3.78 (case 01: 4.17, case 04: 3.4)**

## Judge findings

### Case 01 (AI infrastructure hidden beneficiaries)
- source_grounding (4): Most claims sourced but some assertions (pricing, monopoly strength) lack explicit citations.
- non_obvious_discovery (5): Perfect — found Ajinomoto (food→ABF substrate) and CLF (steel→GOES).
- skeptic_discipline (4): Good kill list but 3-question format not shown explicitly per name.
- actionability (5): Full table with all fields populated.
- quorum_routing (5): Clean handoff, no self-deciding.
- prescreen_usage (2): **Skipped the scanner entirely.** Jumped to reading with no pre-screen evidence.

### Case 04 (already-priced trap)
- source_grounding (3): Cites FT/WSJ/SA vaguely — no article-level detail or extractable quotes.
- skeptic_discipline (4): Strong kills, compressed format (not explicit 3-question per name).
- actionability (4): Correct zero finalists, but missing re-entry triggers.
- quorum_routing (4): Routes nothing correctly, but "wait/don't chase" is slightly prescriptive.
- prescreen_usage (2): **No evidence scanner was run.**

## Insight (round 1)

- **Dragging dim:** `prescreen_usage` flat at 2.0 across both cases. Common cause: skill Step 1 says "(fast, optional)" — the word "optional" gives the actor permission to skip it.
- **Secondary weakness:** `source_grounding` at 3.5 — the actor cites sources but doesn't extract specific quotes/details. Skill lacks a "cite with extractable detail" requirement.
- **Edit this round:**
  1. Remove "optional" from Step 1. Make prescreen MANDATORY with explicit "show scanner output before proceeding."
  2. Add requirement: every source citation must include one specific extractable fact (quote, number, date) from that source.
- **Watch next round:** Does forcing the prescreen slow the actor down without improving discovery? Does citation requirement bloat the output?
