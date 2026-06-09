# Iteration 3 — Full coverage (v1, all 4 train cases)

## Scores

| Dimension | Case 01 | Case 02 | Case 03 | Case 04 | Mean |
|---|---|---|---|---|---|
| source_grounding | 4 | 4 | 5 | 4 | 4.25 |
| non_obvious_discovery | 5 | — | 5 | — | 5.0 |
| skeptic_discipline | **3** | **3** | 4 | 5 | **3.75** |
| actionability | 4 | 5 | 5 | 5 | 4.75 |
| quorum_routing | 5 | 5 | 4 | 5 | 4.75 |
| prescreen_usage | 5 | 5 | — | 5 | 5.0 |

**Case means: 01=4.33, 02=4.4, 03=4.6, 04=4.8**
**Overall train mean: 4.53**

## Judge verbatim findings

### Case 01 — skeptic_discipline: 3
"Kills are listed with reasons but mostly rely on price-extension heuristics rather than
explicitly testing all three skeptic questions; 'ETN: non-obvious fails' is too vague, and the
filter is applied leniently to survivors."

### Case 02 — skeptic_discipline: 3
"Kills are present and cover most named tickers, but reasons are single-liners ('headline
quantum name,' 'known names,' '+142% 12m') rather than explicit passage through all three
skeptic questions; PANW/CRWD/OKTA grouped and dismissed with 'known names' alone — too
perfunctory for systematic filtering."

### Case 03 — quorum_routing: 4
"The actor self-applies and delivers the quorum verdict rather than purely nominating, making
it slightly prescriptive."

## Insight (round 3)

- **Dragging dim:** `skeptic_discipline` at 3.0 on cases 01 and 02 (the cases with survivors).
  On case 04 (pure kills) it scores 5 — so the problem is specific to cases where candidates
  SURVIVE: the actor applies the filter but doesn't show the 3-question format explicitly.
- **Root cause:** Step 4 says "answer ALL THREE questions" but doesn't require a per-candidate
  structured output (Q1/Q2/Q3 format). Actors compress kills into one-liners and batch them.
  The skill says "record your skeptic assessment" but this is too vague.
- **Secondary weakness:** `quorum_routing` on case 03 dropped to 4 because the actor RAN the
  quorum itself (gave lenses' verdicts) instead of just nominating. The skill says "route to
  multi-lens-quorum" but doesn't say "do NOT execute the quorum yourself."
- **Edit this round:**
  1. Add explicit per-candidate 3-question template to Step 4 (force structured output).
  2. Add "NEVER execute the quorum yourself — only NOMINATE" to Step 5.
- **Comparison to iter-2:** iter-2 scored 4.65 on 2 cases (01+04 only). Adding cases 02+03
  revealed the skeptic weakness that 2 cases couldn't detect. This is expected — more cases
  = more realistic score. The skill didn't get WORSE; the measurement got BETTER.
- **Watch next round:** Does forcing 3-question format per candidate bloat the output and cause
  actors to skip some candidates entirely? Over-correction check needed.
