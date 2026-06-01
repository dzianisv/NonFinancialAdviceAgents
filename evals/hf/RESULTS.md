# Hedge-fund-manager capability eval — results

Capability eval for `.agents/skills/hedge-fund-manager/SKILL.md` — "does it do all the job a hedge fund
does, end to end, by managing and delegating to a team?" Built on the supervisor/executor pattern
(`.agents/skills/skill-supervisor`): **executor subagents run the skill; the main session (supervisor)
scores how the job was done.** Educational analysis, not financial advice.

## Harness

- `scenarios/inputs.jsonl` — 6 fund-state + market snapshots the runner sees (NO answer key): a quarter-end
  with sleeve drift + an underwater lot, a Tier-2 dip event, a calm weekly, a risk-breach drawdown, a
  new-idea-with-no-backtest gate test, and a month-start DCA. 4 train / 2 holdout.
- `scenarios/scenarios.jsonl` — ground truth: expected cadences, required report sections, rebalance
  breach, dip tiers, risk verdict, backtest-gate requirement.
- `score_capability.py` — deterministic score (100): **coverage 40** (parsed from the report's own section
  tags, so it can't be self-graded) + **cadence routing 15** + **decision calls 25** (rebalance/dip/risk) +
  **backtest gate 5** + **judge quality 15**. Invariant gate: claims-to-place-trades or fabricated
  holdings/cost-basis → 0.
- `JUDGE_RUBRIC.md` — frozen qualitative rubric (delegation 5 / decision-ownership+risk-gate 4 / orders
  concrete 3 / bull-lag 3).
- `evaluate_hf.py` — aggregates, split train/holdout.

## Scores

| Skill version | Train | Holdout | Delegation (judge dim) | Invariant viol. |
|---|--:|--:|--:|--:|
| v0 — solo pipeline (manager does it all) | 89.8 | 95.0 | **0 / 5** | 0 |
| **v1 — manager delegates to a team** | **99.2** | **99.0** | **14–15 / 15** | 0 |

## What happened

v0 produced correct numbers but **ran no team** — a single-voice pipeline with no `<desk>` trace and no
delegation to named analysts. The judge scored delegation 0/5 across all 6 scenarios. That matched the
user's critique: a hedge-fund *manager* manages a team and delegates research / portfolio assessment / risk
assessment — it doesn't do the analysis itself.

v1 rewrote the skill **delegation-first**: a roster of specialist analysts (Regime, Research, Signals,
Construction, Risk, Cash, Rebalance, Tax), explicit delegation mechanics (convene only the cadence's team,
parallelize independent analysts, sequence the dependent chain, Risk Manager veto is the binding choke
point), and a required `<desk>` delegation trace in the report. Capability rose **91.5 → 99.2**, holdout
moved with train (generalized, not overfit), 0 invariant violations.

**Eval bug the supervisor caught (not a skill failure):** two scenarios initially lost cadence points
because the ground truth omitted "weekly"/"event" — but both dates are Mondays and one proposes a new idea,
so the skill's routing was correct. Ground truth was corrected; both versions re-scored fairly.

**Remaining v1 gap (honest):** the Signal/Research analysts do substantive work but aren't always listed in
the `<desk>` roll-call (−1 on delegation in 5/6). Next tweak: require the `<desk>` block to name every
analyst convened. Left for the next supervisor cycle rather than overfitting now.

## Reproduce

```
# executor subagent runs the skill on scenarios/inputs.jsonl -> results/decisions_v1.jsonl + reports_v1.md
# judge subagent scores reports -> results/judgments_v1.jsonl
python3 evals/hf/evaluate_hf.py --decisions results/decisions_v1.jsonl --judge results/judgments_v1.jsonl
```

Re-run before shipping any edit to `hedge-fund-manager/SKILL.md`; reject anything that lowers the score or
trips the invariant gate.
