# PM skill self-improvement loop — results

Empirical prompt-improvement loop for `.agents/skills/tradfi-portfolio-manager/SKILL.md`, modeled on the
Darwin Gödel Machine / Hyperagents pattern (arXiv 2603.19461): mutate the prompt → evaluate against tasks
→ keep only what improves → archive. Educational analysis, not financial advice.

## Harness

- `gen_scenarios.py` — 10 historical market scenarios with **deterministic ground truth** (dip tier from
  S&P drawdown-from-52w-high, regime from price vs 200d MA, rebalance-due from quarter-end), 3 held out.
- `score_decision.py` — hard score (0-100): regime 25 + dip-tiers 35 + rebalance 15 (objective) +
  qualitative 25 (judge). **Invariant gate:** any note that claims to place trades → total 0.
- `evaluate.py` — scores a decisions file, split train/holdout.
- Each round: an agent runs the skill on the scenarios (sees market facts only, never the answer key) →
  an independent judge scores the qualitative dimension → `evaluate.py` aggregates.

## Scores

| Version | Train | Holdout | Qualitative | Invariant viol. |
|---|--:|--:|--:|--:|
| v0 (baseline) | 91.9 | 91.3 | 16.7/25 | 0 |
| v1 | ~91.8 | — | 16.8/25 | 0 |
| **v2 (shipped)** | **98.0** | **98.0** | **23.0/25** | **0** |

Deterministic score was at ceiling (75/75) from v0 — the decision *rules* were already correct. All gains
were qualitative, and **holdout improved as much as train → generalization, not overfitting.**

## What each iteration changed

- **v1** — bull-market-lag honesty was omitted in 9/10 notes despite being a skill requirement; made it a
  mandatory report element (1/10 → 10/10). Resolved 3 ambiguities agents hit (regime-score fallback,
  dip sub-tranche definition, systemic-override-when-data-absent). Added a worked `<example>`.
- **v2** — killed the "--ticket punt" (notes deferred dip orders to a command): defined "produce the
  orders" concretely as per-sleeve **dollar** deploy amounts (tier% × $220K reserve, split weight/0.78).
  Made the quarter-end rebalance action concrete instead of "pending verification." `orders_actionable`
  2/10 → 10/10.

## Guardrails enforced

- **Objective anchor** — dip/regime/rebalance graded by math, not the judge.
- **Held-out set** — 3 scenarios the optimizer never saw; used to detect overfitting.
- **Frozen invariants** — notification-first / never-places-trades, backtest gate, risk caps, crypto
  separation were never optimization targets (only re-worded). 0 violations across all versions.
- **Monotonic** — ship only if aggregate ↑ and no invariant regresses.

## Stopping point & next (meta-level)

Stopped at v2: the remaining judge gap (regime "held N sessions" confirmation) is an **eval limitation** —
scenarios are point-in-time snapshots with no session history, so pushing the skill to assert it would
teach fabrication. Next improvement is to the **harness, not the prompt**: add multi-session context and
current-holdings/drift data so the regime-persistence and rebalance-order dimensions become testable.

## Reproduce

```
python3 evals/pm/gen_scenarios.py                 # regenerate scenarios + ground truth
# (agent runs skill on evals/pm/scenarios/inputs.jsonl -> results/decisions_*.jsonl)
# (judge -> results/judgments_*.jsonl)
python3 evals/pm/evaluate.py --decisions results/decisions_v2.jsonl --judge results/judgments_v2.jsonl
```

The harness is a permanent **regression test**: re-run it before shipping any future SKILL.md edit; reject
anything that lowers the score or violates the invariant gate.
