# Hierarchy eval protocol — blind pairwise (used 2026-07-08, rounds 1 & 2)

Reproducible procedure for comparing two+ decision hierarchies. Never self-grade: rubric author,
chain producers, and judges are all separate agents; judges are blind to hierarchy identity.

## Pipeline

```
1 rubric author (firewalled: must NOT read hierarchies/ or prior evals)
        │ writes rubric: 8 weighted dims + pairwise protocol + anti-gaming rules
        ▼
N chains × M tickers on IDENTICAL frozen inputs (briefing + binding scorecard ACTION)
        │ hierarchy mechanism = the ONLY variable
        ▼
anonymize: scrub hierarchy names → X/Y labels; leak-check with grep; key.txt records mapping
        ▼
1+ blind judge per pair (alternate block order across pairs to cancel position bias)
        ▼
unblind → tally: head-to-head count + average weighted margin (margin breaks a coin-flip count)
```

## Judge prompt (verbatim template)

> You are a blind pairwise judge for investment-decision quality. Read: (1) the rubric
> `<rubric path>` IN FULL, (2) Block ONE: `<blind/TICKER-A.md>`, (3) Block TWO: `<blind/TICKER-B.md>`.
> Both are decisions for the SAME stock from the SAME frozen briefing; only the decision pipeline
> differs — you don't know which pipelines, and you must not reward or punish a block for its
> structural style (single-analyst vs multi-vote) per se, only for rubric-measured quality.
> Follow the rubric's pairwise protocol exactly: winner per dimension (or tie) with one-line
> justification each, then weighted overall winner. Apply the anti-gaming rules (no credit for
> length/jargon/confidence). Return compact: per-dimension table (dimension | winner | why) +
> OVERALL: ONE|TWO|TIE + two-sentence rationale.

## Rubric dimensions (2026-07-08 independent rubric — reuse or re-author, never let a
hierarchy designer author it)

Actionability 20% · Evidence Grounding 18% · Risk Honesty 18% · Internal Consistency 14% ·
Calibration 12% · Dissent Preservation 10% · Trigger Specificity 8% · Portfolio Context 8%

## Known limits + upgrades (apply when the decision matters)

| Weakness | Upgrade |
|---|---|
| n=1 judge per pair | 3 judges, majority; measure inter-judge agreement |
| position bias | re-judge with block order swapped; same winner both ways |
| judge never calibrated | planted-defect pair (one block carries a known fabricated number) — a judge that misses it is disqualified |
| same model family everywhere | cross-family judge (different vendor/model) |
| report quality ≠ being right | forecast ledger: Brier-score each verdict's falsifiable prediction over months — the only true ground truth |

## History

- 2026-07-08 round 1 (bsc/bridgewater/millennium, FIS+ESTC): bsc 4–0. `.cache/stocks-advisor/eval/RESULTS-2026-07-08-hierarchy-pairwise.md`
- 2026-07-08 round 2 (bsc vs panel, 5 diverse tickers): panel 3–2 count, bsc 55.8–44.2 margin → bsc default. `.cache/stocks-advisor/eval/round2/RESULTS-round2-bsc-vs-panel.md`
