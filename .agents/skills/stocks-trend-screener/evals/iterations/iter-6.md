# Iteration 6 — holdout generalization round (case 05: conviction dual-theme)

Extends a CONVERGED loop (v2/v3 shipped, train 4.62 / holdout 4.40) with a NEW frozen holdout
case harvested from a real 2026-06-26 session — a shape absent from train: CONVICTION_MODE +
dual-theme (robotics AND ai supply chain) + explicit "do /deep-research".

## Isolation
- Actor: sonnet, given ONLY the skill body (read SKILL.md) + the case request. No rubric.
- Judge: sonnet, given ONLY case + actor response + RUBRIC.md. Blind to skill body.

## Raw judge output (v3-shipped on case 05)
- source_grounding: **2** — citation theater; RSS-headline stubs, no resolved URLs / body extraction; revenue accel UNKNOWN for ECL/AAON/6324.T (the qualifying metric left unverified).
- non_obvious_discovery: **4** — legit cross-sector chains (GEV→GOES→CLF; VRT→liquid cooling→ECL/CoolIT); haircut: CLF "sole US producer" stated without share/capacity data.
- skeptic_discipline: **3** — 6 killed with reasons (good), but 4 of 6 survivors are LOW and advanced as finalists despite a HIGH-confidence ask; CLF catalyst had no named quarter.
- actionability: **3** — no entry price zones; UNKNOWN revenue blocks quorum judgment; final table described not delivered cleanly.
- quorum_routing: **4** — routing stated, flags attached, no buy call; haircut: 6 survivors but only 4 routed (inconsistency).
- prescreen_usage: **4** — scanner used as directional pre-screen, redirected reading to robotics; haircut: verification commands not shown.
- **MEAN: 3.33**
- Judge's top fix target: source_grounding (resolve URLs + extract body quotes).

## Insight (round 6) — read first next round
- **Biggest failure is unmeasured by the rubric.** The actor MISSED CONVICTION_MODE — it wrote
  "producing RESEARCH_MODE output" because "do /deep-research" lexically pulled it to RESEARCH_MODE.
  The rubric has no mode_detection dimension, so the judge could only penalize it indirectly
  (via skeptic_discipline 3 + actionability 3). The true error is structural mode misrouting.
- **Cause:** Step 0 listed "high confidence" as a trigger but (a) didn't cover surge/buy-today,
  (b) had no precedence rule for when a conviction trigger and "deep research" co-occur, (c) didn't
  force the model to declare the mode, so the misroute was silent.
- **Edit this round (v3→v4, general principle):** Step 0 now declares mode+trigger as line 1;
  adds surge/high-confidence/buy-today triggers; adds mode-vs-depth precedence ("deep-research" =
  DEPTH not MODE; conviction trigger wins on co-occurrence); restates max-3 / HIGH-only / no-pad.
- **Watch next round (over-correction check):** does v4 wrongly force CONVICTION on a pure
  RESEARCH_MODE request (e.g. train case 02 "weekly scan")? Re-run case 02 with v4 to confirm it
  still routes RESEARCH_MODE. Keep v4 only if holdout(case05) rises AND train(case02) holds.
- **Source_grounding (secondary):** RSS-stub citation theater is partly a live-feed limitation, but
  the skill could require resolving at least one publisher URL + one body quote per finalist before
  it counts. Defer until mode-detection is validated (don't fix two levers in one round).
- **Rubric residual:** add `mode_detection` dim for FUTURE rounds; do not retro-apply (would
  invalidate the train trend).

## Status
v4 archived (archive/v4-mode-detection-precedence.md), SKILL.md edited live. **NOT re-measured**
(context budget). Next round = validate v4 (re-run actor+judge on case 05 holdout + case 02 train),
then keep-or-revert.
