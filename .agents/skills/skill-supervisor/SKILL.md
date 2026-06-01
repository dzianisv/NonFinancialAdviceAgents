---
name: skill-supervisor
description: Improve a target SKILL.md through an eval-driven supervisor/executor loop with strict propose/dispose separation — the supervisor (this session) scores and selects, a separate blind Claude Code executor agent does every prompt edit and every skill run. Use for "improve a skill", "iterate on the skill with evals", "run the self-improvement loop", "tune the prompt against held-out evals", "make the portfolio-manager skill better". This is the anti-reward-hacking replacement for a single agent doing self-reflection AND self-modification (the DGM/Hyperagents failure mode). NOT for writing a skill from scratch (use write-skill) or for one-off prompt edits.
license: MIT
compatibility: opencode
metadata:
  author: engineer
  pattern: supervisor-executor / propose-dispose
---

# Skill Supervisor — eval-driven improvement with role separation

You are the **supervisor**. You drive a loop that makes a target skill measurably better against a
fixed eval harness. The core rule that makes this trustworthy:

> **The role that changes the prompt is never the role that scores it.** A single agent that both
> reflects on its output and rewrites its own instructions learns to game its own rubric — the
> DGM/Hyperagents self-modification failure mode. Separation removes that incentive at the source.

## Three roles, hard-separated

| Role | Who | Sees | Never sees | Job |
|---|---|---|---|---|
| **Supervisor** | you (this session) | everything | — | pick target, spawn executors, score, select, archive. **Never edits the target SKILL.md yourself.** |
| **Runner** (executor) | fresh Claude Code subagent (Agent tool) | only the candidate SKILL.md + the eval inputs | the rubric, ground truth, holdout labels | run the skill on every input, emit raw decisions + the artifact the skill is meant to produce |
| **Modifier** (executor) | fresh Claude Code subagent (Agent tool) | current SKILL.md + the *failing train cases* + a one-line directive | the scoring rubric internals, the judge prompt, the **holdout** scenarios | produce one candidate SKILL.md that addresses the directive |
| **Judge** (supervisor-side) | fresh subagent with a **frozen** rubric | the runner's artifacts + the frozen rubric | the modifier's reasoning | score the qualitative dimension only |

Spawn executors with the **Agent tool** (that is the "Claude code agent" — the executor). Use a cheaper
model (`sonnet`) for runner/modifier/judge; keep the supervising context for orchestration and the
accept/reject call. Run the modifier with `isolation: "worktree"` so a candidate never touches the live
skill until the supervisor accepts it.

## The objective anchor (why this can't be gamed)

Scoring is **mostly deterministic math**, computed by the supervisor — not by any LLM:

- Deterministic dimensions (e.g. regime call, dip tiers, rebalance-due) → scored by code against
  ground truth. The modifier cannot argue its way to points.
- One **invariant gate** → any forbidden behavior (e.g. "places trades") forces the score to 0,
  regardless of everything else. Invariants are **frozen**: they may be re-worded for clarity but are
  never optimization targets.
- Only a small qualitative slice is judge-scored, against a rubric the modifier never sees.

## The loop

1. **Baseline.** Spawn a Runner on the current skill → decisions. Spawn the Judge → qualitative scores.
   Score with the harness. Record train mean, holdout mean, invariant violations. This is also the
   regression baseline.
2. **Diagnose.** As supervisor, read the per-scenario errors. Identify the single highest-impact gap.
   Decide honestly **whether the gap is in the prompt or in the harness** (see "Honest stop" below).
3. **Propose.** Write a one-line directive naming only the gap (not how to score it). Spawn a Modifier
   in a worktree with the current skill + the failing train cases + the directive. It returns one
   candidate SKILL.md.
4. **Evaluate.** Spawn a fresh Runner on the candidate (blind), then the Judge. Score on **train AND
   holdout separately**.
5. **Select (the gate).** Accept the candidate only if **all** hold:
   - train mean strictly improves, **and**
   - holdout mean does not regress (ideally improves by a similar margin — equal movement = it
     generalized, not overfit), **and**
   - invariant violations == 0.
   Otherwise reject and either re-diagnose or stop.
6. **Archive.** On accept, save the candidate as the new version (`results/decisions_vN.jsonl`,
   `judgments_vN.jsonl`) and append a line to `RESULTS.md`. Keep every accepted version — you can branch
   the next attempt from any archived ancestor (open-ended archive, per DGM).
7. **Repeat** from step 2 until a stop condition.

## Honest stop conditions

Stop and report — do not keep mutating — when any holds:

- **Ceiling reached:** deterministic dimensions are already at max and the only remaining gap is
  qualitative wording the judge can't reliably distinguish.
- **Harness-bound gap:** the remaining gap is something the eval *cannot* test (e.g. asserting
  "regime held N sessions" when scenarios are point-in-time snapshots). Pushing the prompt to assert it
  would **teach fabrication**. The correct next move is to **improve the harness, not the prompt** —
  add the missing input dimension, then resume the loop with real signal.
- **No-generalization:** train improves but holdout regresses twice on the same directive → the gain is
  overfitting; reject and stop that branch.

Report the stop reason plainly. A loop that stops at a real ceiling and says so beats one that grinds
the score up by overfitting.

## Wiring for the tradfi-portfolio-manager skill (the running example)

- Target skill: `.agents/skills/tradfi-portfolio-manager/SKILL.md`
- Harness: `evals/pm/` — `gen_scenarios.py` (ground truth, 3 holdout), `score_decision.py` (det 75 +
  invariant gate + judge 25), `evaluate.py` (driver, splits train/holdout).
- Eval inputs the Runner sees: `evals/pm/scenarios/inputs.jsonl` (point-in-time market snapshots — NO
  ground truth, NO split labels).
- Score a version: `python3 evals/pm/evaluate.py --decisions results/decisions_vN.jsonl --judge results/judgments_vN.jsonl`
- Runner emits one JSON/line to `decisions_vN.jsonl` with keys: `label, regime_call`
  (`risk-on`/`risk-off`), `dip_tiers_active` (list of int), `rebalance_due` (bool), `places_trades`
  (bool — must be false), plus the weekly note text for the judge.
- Frozen invariant: `places_trades` true → score 0. Never make it an optimization target.

## Done when

- A baseline and at least one candidate were each run by a **separate** Runner agent (the supervisor
  never produced decisions itself).
- The accept/reject decision is recorded with train + holdout numbers and invariant count.
- Either an improved version is archived (train↑, holdout not down, 0 violations) **or** an honest stop
  reason is written. In both cases `RESULTS.md` has a new dated entry naming the architecture
  (supervisor/executor) and the outcome.
