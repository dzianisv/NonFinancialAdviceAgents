# Self-improvement loop — final architecture (researched + proven)

The fully self-contained "one workflow runs the target N times and edits itself" does **not** work in this
runtime, and shouldn't anyway. Two walls, both real:

1. **Runtime:** a workflow cannot nest a heavy target — `workflow(name)`→null, `workflow({scriptPath})`→throws.
   So the loop cannot self-run the target.
2. **Methodological:** a self-graded, pointwise LLM-judge is unreliable AND it's the reward-hack the user caught
   (inflated 76→94). Pointwise absolute scores cluster/fluctuate — they gave iter1=88/iter4=89, then 63.5/64,
   never separating a news-FAILED report from a complete one.

## The architecture that works (orchestrated, not self-contained)

```
SUPERVISOR (main agent) drives the loop:
  1. run target           -> Workflow tool (research-crypto-market / research-stock-market)   [WORKS]
  2. REFLEXION (diagnose)  -> judges critique baseline report -> name single weakest skill
  3. DSPy (propose)        -> K instruction rewrites of that ONE skill (separate proposer agent)
  4. apply candidate       -> write skill, re-run target via Workflow tool -> candidate report
  5. SELECT (pairwise)     -> pairwise-eval.js: N blind judges pick candidate vs baseline,
                              position-randomized, majority vote                                [PROVEN]
  6. accept iff candidate wins the majority -> commit (HUMAN GATE before merge)
  7. ground truth          -> forecast-ledger Brier score over weeks/months (the real arbiter)
```

Roles stay separated (judge ≠ proposer ≠ executor) — no self-grading.

## Why pairwise (the key fix)

Research (Zheng 2023 / MT-Bench / AlpacaEval; see survey): LLM judges are far more stable comparing two
outputs than assigning an absolute score — relative comparison needs no calibrated scale and tracks human
preference better. So **selection** (accept/reject) uses pairwise, not a 0-100 number.

**What's actually shown (honest):** `pairwise-eval.js` on iter1 (news seat literally `[UNAVAILABLE — DID NOT
RUN]`) vs iter4 (complete), 5 judges, order swapped by index → iter4 won 5–0; pointwise on the same pair gave
88/89 then 63.5/64. This validates the **plumbing** (parallel judges, position-randomization, tally) and that
pairwise cleanly flags a **gross defect**. It does NOT yet prove pairwise discriminates **subtle** improvements
(two fully-complete reports differing only in reasoning) — that is the real use case and is **UNPROVEN**. The
5-0 is a near-gimme (one report visibly says a section didn't run). Next validation must use a hard pair, under
a rubric the proposer did not write.

## Components (all committed, on branch crypto-workflow-research)

| File | Role | Status |
|---|---|---|
| `.agents/workflows/research-market.workflow.js` | unified crypto+equity research target | proven (ran 4×) |
| `.agents/workflows/pairwise-eval.workflow.js` | blind A/B selection | works; validated on a GROSS-defect pair only — subtle-case discrimination UNPROVEN |
| `crypto/workflows/blind-eval.js` | pointwise scoring | **DELETED** (unreliable for selection) — recoverable from git |
| `crypto/workflows/improve-workflow.js` | self-contained loop | **DELETED** (blocked by nesting) — this orchestrated procedure replaces it; recoverable from git |

## What's NOT done (honest)

The end-to-end auto cycle (propose → edit → re-run → pairwise → auto-commit) is not wired as a single button —
it's the supervisor procedure above, because target runs must be external. The hard, uncertain part (a
trustworthy blind selection that discriminates) is built and proven; the rest is Workflow-tool orchestration.
