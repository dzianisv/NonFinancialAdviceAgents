---
name: ai-evaluate
description: "Blind pairwise evaluation of K generator variants (decision hierarchies, workflows, prompt versions) on identical frozen inputs — firewalled rubric author, name-scrubbed blinding, blind pairwise judges, count+margin tally. Never self-grade. Triggers: \"compare hierarchies\", \"A/B these prompts\", \"run a blind eval\"."
license: MIT
compatibility: opencode
metadata:
  audience: skill-and-workflow-authors
  domain: evaluation-methodology
  role: evaluator/orchestration
  source: "Promoted from stocks-advisor/references/eval-protocol.md, proven 2026-07-08 rounds 1 & 2 (hierarchy comparison)"
---

# Blind pairwise eval — the method

Reproducible procedure for comparing **K generator variants** — decision hierarchies, workflows, prompt
versions, anything that produces an output from an input — on **identical frozen inputs**. Never
self-grade: the rubric author, the variant producers, and the judges are all separate agents, and judges
are blind to variant identity. The unit under test can be anything with a name and an output; only the
mechanism producing the output is allowed to vary.

## Pipeline

```
0 orchestrator freezes inputs (owned by the orchestrator, not a subagent — see Step 0)
        ▼
1 rubric author (firewalled: must NOT read the variants/ or prior evals)
        │ writes rubric: weighted dims + pairwise protocol + anti-gaming rules
        ▼
K variants × M inputs on IDENTICAL frozen inputs (variant mechanism = the ONLY thing that differs)
        │ (large fan-outs → delegate to the pairwise-eval-workflow, see Step 2)
        ▼
anonymize: scrub variant names → X/Y labels; leak-check with grep; key.txt records the mapping
        ▼
1+ blind judge per pair (alternate block order across pairs to cancel position bias)
        ▼
unblind → tally: head-to-head count + average weighted margin (margin breaks a coin-flip count)
```

## Step 0 — freeze the inputs (orchestrator-owned)

The orchestrator (main agent), not a subagent, freezes the input set before any variant runs. This
matters for two reasons: (1) every variant must see byte-identical inputs or the comparison is
confounded, and (2) some inputs require live data pulls — e.g. an MCP call (TradingView, a market-data
API) or anything needing the orchestrator's tool access — that a firewalled subagent cannot make on its
own. Pull/snapshot the inputs once, write them to a fixed path (e.g. `briefing.md`, `in.json`), and hand
every variant and judge the same path. Never let a variant or judge re-fetch live data mid-eval — a
market price or news feed that moves between runs silently breaks the "identical inputs" invariant.

## Step 1 — firewalled rubric author

Spawn a subagent whose **only** job is to author the rubric. It **must not** read the variants directory,
any prior eval results, or anything that would let it infer which variant is expected to win. Give it:
the domain, the frozen input(s) (so it knows what "good" looks like for this kind of input), and the
pairwise-judge protocol shape below to fill in. It returns: N weighted dimensions + a pairwise-judgment
protocol + anti-gaming rules (no credit for length, jargon, or confident tone). Reuse a rubric across
rounds when the domain is unchanged — re-author only when the domain changes or you suspect rubric drift;
never let a variant's designer author or edit it.

## Step 2 — run K variants × M inputs

Each variant processes every frozen input, producing one output artifact per (variant, input) pair. This
is the only step where the variant mechanism is allowed to differ; everything else — input, format
expectations, output location convention — must be identical across variants.

**Delegate large fan-outs to the workflow, not ad-hoc subagents.** Per the workflow rule in
`~/.agents/AGENTS.md` (#Skills — "if a skill needs many parallel subagents, build it as a dynamic
workflow"), when K×M exceeds a handful of runs, use
`/Users/engineer/workspace/backtest/.claude/workflows/pairwise-eval-workflow.js` (or a workflow shaped
like it) rather than manually spawning and tracking dozens of subagents from the main thread. That
workflow already implements: parallel judge fan-out, deterministic position-swap by index (no
`Math.random` in that runtime), and vote tally — reuse it for the judging step (Step 4) too rather than
re-deriving position-bias handling by hand.

## Step 3 — anonymize + leak-check

Copy each (variant, input) output into a `blind/` directory renamed to a scrubbed label — `X`/`Y`/`Z` per
variant, keyed to the input (e.g. `blind/TICKER-X.md`). Record the real mapping in `blind/key.txt`, which
the judges never see. Then **grep the blind files for every real variant name** before showing them to a
judge — a leaked name in a header, footer, or self-referential sentence ("as bridgewater's approach
would...") silently un-blinds the judge and invalidates the round.

```python
import re, pathlib, sys

VARIANT_NAMES = ["bridgewater", "millennium", "bsc"]  # real names, from key.txt — never expose to judges
BLIND_DIR = pathlib.Path("blind")

leaks = []
for f in BLIND_DIR.glob("*.md"):
    text = f.read_text()
    for name in VARIANT_NAMES:
        if re.search(re.escape(name), text, re.IGNORECASE):
            leaks.append((f, name))

if leaks:
    for f, name in leaks:
        print(f"LEAK: {f} contains variant name '{name}'", file=sys.stderr)
    sys.exit(1)
print(f"clean: {len(list(BLIND_DIR.glob('*.md')))} files, no leaks")
```

Do not proceed to judging until this script (or equivalent) reports clean.

## Step 4 — blind judges (verbatim prompt)

Spawn one judge per pair (or per pair per judge, for the 3-judge upgrade in Step 6). **Alternate block
order across pairs** — pair 1 shows variant X first, pair 2 shows Y first, etc. — so position bias cancels
across the round rather than compounding in one direction. Each judge sees only the rubric and the two
blind blocks; it never sees `key.txt` or the variants directory.

> You are a blind pairwise judge for [DOMAIN] decision quality. Read: (1) the rubric `<rubric path>` IN
> FULL, (2) Block ONE: `<blind/INPUT-A.md>`, (3) Block TWO: `<blind/INPUT-B.md>`. Both are outputs for the
> SAME input from the SAME frozen briefing; only the generator mechanism differs — you don't know which
> mechanisms, and you must not reward or punish a block for its structural style (e.g. single-pass vs
> multi-step) per se, only for rubric-measured quality. Follow the rubric's pairwise protocol exactly:
> winner per dimension (or tie) with one-line justification each, then weighted overall winner. Apply the
> anti-gaming rules (no credit for length/jargon/confidence). Return compact: per-dimension table
> (dimension | winner | why) + OVERALL: ONE|TWO|TIE + two-sentence rationale.

Swap `[DOMAIN]` for the actual domain (investment-decision quality, code-review quality, workflow-output
quality, prompt-response quality, ...) but otherwise reuse this prompt verbatim — the "you must not reward
or punish... for its structural style" clause is the anti-gaming core and should not be diluted per round.

## Step 5 — unblind + tally

Only after every judge has returned a verdict, open `key.txt` and translate `X`/`Y`/`Z` labels back to real
variant names. Tally two numbers, not one:

- **Head-to-head count**: wins per variant across all pairs judged.
- **Average weighted margin**: the rubric's weighted score gap per pair, averaged across pairs.

Report both. **The margin is what breaks a coin-flip count** — a 3–2 count with a 55.8–44.2 average margin
is a real (if modest) edge; a 3–2 count with margins clustered near zero is noise dressed as a decision.
Never report the count alone when the margin is available.

## Step 6 — upgrades when it matters

Apply these when the decision is expensive enough to warrant the extra cost — not by default.

| Weakness | Upgrade |
|---|---|
| n=1 judge per pair | 3 judges, majority; measure inter-judge agreement |
| position bias | re-judge with block order swapped; same winner both ways |
| judge never calibrated | planted-defect pair (one block carries a known fabricated number) — a judge that misses it is disqualified |
| same model family everywhere | cross-family judge (different vendor/model) |
| eval quality ≠ being right | forecast ledger: Brier-score each verdict's falsifiable prediction over months — the only true ground truth |

## Done when

- [ ] Inputs frozen by the orchestrator (Step 0) — including any MCP/live-data pulls a subagent could not
      make itself — and every variant/judge sees the identical, byte-frozen input.
- [ ] Rubric authored by a subagent that never read the variants or prior evals (Step 1).
- [ ] Every variant ran on every frozen input, with only the mechanism differing (Step 2); large fan-outs
      went through the pairwise-eval-workflow rather than ad-hoc subagent tracking.
- [ ] `blind/` directory built, `key.txt` written, and the leak-check script reports clean before any
      judge sees a block (Step 3).
- [ ] Judges ran blind on the verbatim prompt, with block order alternated across pairs (Step 4).
- [ ] Tally reports **both** head-to-head count and average weighted margin, not count alone (Step 5).
- [ ] For a high-stakes call: at least one Step 6 upgrade applied (3-judge majority is the cheapest,
      highest-value first upgrade).

## History (worked examples — hierarchy comparison, 2026-07-08)

- **Round 1** (bsc / bridgewater / millennium hierarchies, tickers FIS + ESTC): bsc won 4–0.
  `.cache/stocks-advisor/eval/RESULTS-2026-07-08-hierarchy-pairwise.md`
- **Round 2** (bsc vs a multi-lens panel hierarchy, 5 diverse tickers): panel won 3–2 on count, but bsc led
  55.8–44.2 on average weighted margin → bsc kept as the default (the margin overturned what the raw count
  suggested).
  `.cache/stocks-advisor/eval/round2/RESULTS-round2-bsc-vs-panel.md`
- **Round 3** (bsc vs PATCHED panel, 5 FRESH tickers — patches not taught to the round-2 bug names): panel
  won 3–2 count AND flipped the margin to 52.6–47.4 (round-2 patches moved it ~8.4 pts). A reversal — but
  modest (~5 pts), n=5, and one panel win (AMD) was **prompt-confounded** (the orchestrator's per-ticker
  stress instruction nudged the bsc runner into a TRIM/new-position contradiction the judge then penalized).
  Lesson logged: **keep the orchestrator's per-variant prompts byte-identical except for the variant file** —
  a stray per-ticker instruction difference confounds the comparison exactly like an input difference would.
  Verdict: not clean enough to auto-flip a twice-validated default; recommend a clean round 4 (identical
  prompts) + the Step-6 3-judge-majority upgrade before deciding.
  `.cache/stocks-advisor/eval/round3/RESULTS-round3-bsc-vs-panel.md`
