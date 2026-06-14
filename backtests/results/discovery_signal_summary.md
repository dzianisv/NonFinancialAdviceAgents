# Conclusion — what works for an investing agent team (evidence-backed, 2026-06-08)

One session, four hypotheses, all killed by testing. The conclusion is the deliverable.

## What was tested and refuted (bias-free / out-of-sample)
1. **Laggard rotation** ("buy the cheap supply-chain name in a hot theme") — negative net at
   every horizon (Ken French 49, OOS). Refuted.
2. **Buy-the-single-strongest (argmax)** — surfaces parabolic blow-offs (SNDK +702%); not what
   cohort-momentum validated. Flawed (user caught it).
3. **Momentum itself** — real but WEAK and decaying (Q5-Q1 t=1.70 OOS). Barely an edge.
4. **Filing-text discovery** (EDGAR "capacity constrained / record backlog / capacity
   expansion / record bookings") — no forward edge; positive means are skew over negative
   medians + sub-50% hit-rate; the one significant result was NEGATIVE. Markets price filings.

## The honest law
**Anything an agent can cheaply, scalably compute, the market has already priced.** There is
no free scalable mechanical alpha for "catch the next NVDA." If it were easy, it wouldn't last.
Stop building predictive screeners and trusting them.

## What an agent team IS good for (the real edge)
NOT prediction. Judgment, breadth, discipline, validation:
- **Multi-lens quorum = the crown jewel.** Independent analyst lenses judging the same facts;
  preserves dissent. Proven value: vetoed chasing SNDK at +702% (the euphoric top). That is
  money saved through DISCIPLINE, not forecasting.
- **Breadth + synthesis** — read widely, surface candidates as HYPOTHESES for a human to judge.
  Never as buy signals.
- **Adversarial validation** — test before believing. This single discipline killed all four
  bad ideas above before they cost anything. It is the most valuable capability in the stack.
- **Risk / anti-blowup** — sizing, not buying euphoria, surviving drawdowns (Carver/Housel/Graham seats).

## Operating model going forward
- **Ideas/discovery**: human + reading + the quorum as judge. Outputs are hypotheses, not signals.
- **Decisions**: route every real money question through `multi-lens-quorum` (already auto-triggers).
- **Always validate before believing** — a hand-picked-winner backtest proves nothing; demand
  bias-free / out-of-sample / point-in-time.
- **trend-scout (PR #24)**: keep ONLY as a humble theme-monitoring / "am I chasing?" timing
  view. Honestly labeled weak-edge. Optional to merge; the value is the quorum, not the screen.
- **Do NOT**: ship mechanical alpha screeners as if they predict; chase momentum/euphoria;
  believe a backtest of names you chose with hindsight.

## Status of artifacts
- discovery-engine: gate FAILED -> pipeline NOT built (correct call). Scripts kept as the
  validation harness (edgar_signal_test.py is reusable to kill future signal ideas fast).
- trend-scout: built, honest, demoted to timing. PR #24 open, Den's merge call.
- multi-lens-quorum + analyst lenses: the keepers.
