# Iteration 2 — Round 2 (v1: prescreen-mandatory + extractable citations)

## Scores

| Dimension | Case 01 (AI infra) | Case 04 (trap) | Mean |
|---|---|---|---|
| source_grounding | 4 | 4 | 4.0 |
| non_obvious_discovery | 4 | N/A | 4.0 |
| skeptic_discipline | 5 | 5 | 5.0 |
| actionability | 5 | 5 | 5.0 |
| quorum_routing | 4 | 5 | 4.5 |
| prescreen_usage | 5 | 5 | 5.0 |

**Case 01 mean: 4.5 (vs iter-1: 4.17) → +0.33**
**Case 04 mean: 4.8 (vs iter-1: 3.4) → +1.4**
**Overall mean: 4.65 (vs iter-1: 3.78) → +0.87**

## Fix applied (v0 → v1)

1. Removed "optional" from Step 1 → prescreen now MANDATORY ("do not skip")
2. Added "You MUST show the scanner output before moving to Step 2"
3. Added extractable evidence requirement: every citation must include a specific fact (quote/number/date)
4. Added Form 4 insider cluster as supporting source
5. Added Information Timing Ladder + Cross-Validation Principle to context section

## Judge notes

### Case 01 (AI infrastructure hidden beneficiaries)
- **prescreen_usage jumped 2→5**: Scanner ran first, output was SHOWN, and explicitly directed the reading focus ("not obvious semis"). This was the primary drag in iter-1 — completely fixed.
- **source_grounding held at 4**: Good extractable facts (WSJ date, 8-K dates, dollar amounts). Honest about SA/FT paywall blocks. Could reach 5 with article titles in every citation.
- **non_obvious_discovery held at 4**: ECL (hygiene→cooling) and AAON (HVAC→datacenter) are solid non-obvious. But both are industrial→datacenter (same sector-shift type). v0 had the more exotic Ajinomoto (food→semiconductor) which is harder to find.
- **skeptic_discipline rose 4→5**: Killed 6/8 candidates rigorously. CLF correctly killed with a REAL factual update (Weirton plant cancelled!) that v0 didn't catch.
- **Notable**: Actor KILLED CLF (which v0 passed) because it actually found the Weirton cancellation news — this is the skill WORKING. Better research = different conclusions.

### Case 04 (already-priced trap)
- **prescreen_usage jumped 2→5**: Scanner confirmed "ALREADY EXTENDED" status — used as primary kill evidence.
- **source_grounding rose 3→4**: Specific dates, numbers, publication names. Honest about 401 paywall blocks.
- **skeptic_discipline rose 4→5**: Explicit kills with scanner data as evidence. SNDK killed with specific factual differentiation (HBF ≠ HBM, experimental timeline).
- **Correct outcome**: Zero finalists, firm "you're late" verdict. No caving to user enthusiasm.

## Convergence assessment

| Metric | Iter-1 (v0) | Iter-2 (v1) | Threshold | Status |
|---|---|---|---|---|
| Train mean | 3.78 | 4.65 | ≥ 4.2 | ✅ PASS |
| Min dimension | 2.0 (prescreen) | 4.0 (source, non-obvious) | ≥ 3.0 | ✅ PASS |
| Improvement | — | +0.87 | — | Strong |

**VERDICT: v1 PASSES the stop condition.** Train mean 4.65 > 4.2, no dim below 3.0.

## Remaining weaknesses (won't fix this iteration — diminishing returns)

- `source_grounding` at 4 (not 5): Paywalled sources couldn't be read in test env. In real execution with chrome-use active, this would likely be 5.
- `non_obvious_discovery` at 4 (not 5): Both finds are in the same sector-shift pattern (industrial→datacenter). A 5 would require finding something truly exotic like Ajinomoto. This is partially luck-dependent — not a skill-prompt issue.

## Decision

**SHIP v1.** Run holdout cases (02, 03) as final validation before removing old skills.
