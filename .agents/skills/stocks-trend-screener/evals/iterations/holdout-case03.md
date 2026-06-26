# Holdout Validation — Case 03 (Robotics Deep-Dive)

## Scores

| Dimension | Score | Notes |
|---|---|---|
| source_grounding | 4 | Korea JoongAng, Reuters ×2 with dates + specific numbers. Honest about paywall blocks. |
| non_obvious_discovery | 4 | Schaeffler (auto/bearing → humanoid actuator). Correct "hides in different sector" pattern. |
| skeptic_discipline | 5 | Killed 4/5 candidates with explicit numeric thresholds. LOW confidence on survivor. |
| actionability | 4 | Full table, Dec 2026-Jun 2027 timeline. Correctly LOW/watch-only for speculative theme. |
| quorum_routing | 5 | Explicit LOW flag, "watch-only." Does not oversell speculative thesis. |

**Holdout mean: 4.4** ✅

## Stop condition (final check)

| Metric | Value | Threshold | Status |
|---|---|---|---|
| Train mean | 4.65 | ≥ 4.2 | ✅ |
| Holdout mean | 4.4 | ≥ 4.0 | ✅ |
| Min dimension (all cases) | 4.0 | ≥ 3.0 | ✅ |

**VERDICT: SHIP. Skill converged.**

## Notable behaviors

1. Scanner ran first — confirmed robotics is NOT crowded in price (good for idea-gen)
2. Actor found Schaeffler via sourced reading (Korea JoongAng, Reuters) — not from the skill examples
3. Correctly rated LOW confidence — humanoid robot volumes are speculative/years away
4. Honest about kill: "no medium-confidence survivor"
5. Killed Korean pure-plays (SPG +255%, Robotis +362%) that retail would chase

## Comparison to old pick-trend-stocks eval

The old `pick-trend-stocks` TrendPickingEval.csv scored 7/7 PASS at commit 763389c (iter 2).
That eval used binary PASS/PARTIAL/FAIL — less granular than our 0-5 rubric.

The new `trend-stock-research` skill with the 6-dim rubric:
- Explicitly tests prescreen usage (the old eval didn't measure this)
- Requires extractable evidence per citation (the old eval didn't grade citation quality)
- Tests on a trap case (case 04) — the old eval had no adversarial case
- Mean 4.65/5 with holdout 4.4/5 is a stronger validated result
