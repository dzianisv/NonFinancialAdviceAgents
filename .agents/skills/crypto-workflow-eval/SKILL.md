---
name: crypto-workflow-eval
description: LLM-as-judge that scores the crypto research workflow's output (0–100) against the input question and the product spec. Use to evaluate a workflow run, drive the run→score→fix→rerun loop, and log to crypto.eval.csv. Triggers — "evaluate the workflow output", "score this crypto decision", "grade the panel run".
license: MIT
compatibility: opencode
metadata:
  role: evaluator
  domain: crypto-research
---

# Crypto workflow evaluator (LLM-as-judge)

Score ONE workflow run against the input question + [[crypto.prd.md]] intent. Be a harsh, specific grader — the score drives the improvement loop. Output JSON: `{score, verdict, dimensions[], top_fixes[]}`.

## Inputs
The original question + portfolio, and the workflow output (chair decision + brief + verdicts).

## Dimensions (weighted; 0–10 each, then scale to 100)
| # | Dimension | What "good" means | Weight |
|---|---|---|---|
| 1 | **Answers the actual question** | Direct yes/no/partial to what was asked (e.g. "buy BTC today?"), up front | 2.0 |
| 2 | **Portfolio-aware, buy AND sell** | Maps holdings to exposure (COIN = levered BTC-beta proxy), flags concentration, recommends both add and trim/sell | 2.0 |
| 3 | **Evidence-grounded, live data** | Every claim sourced + dated; priced odds pulled live not from digests; no fabrication | 1.5 |
| 4 | **Completeness** | All categories present incl. **news/catalysts**; gaps shown as `[UNAVAILABLE]`, not hidden | 1.5 |
| 5 | **Disagreement preserved** | Bear dissent visible, not averaged into mush | 1.0 |
| 6 | **Actionable + disciplined** | Concrete tranche plan + invalidation; sizing inside risk-capital boundary, survivable −50%, no leverage | 1.0 |
| 7 | **Calibration / honesty** | Confidence matches evidence; FOMO/anchoring trap addressed; no overclaiming | 1.0 |

## Hard penalties (cap the score)
- Any **fabricated number / odds from a news digest** → max 40.
- **Ignores the portfolio** (treats it as generic BTC-buy) → max 50.
- **Silently drops a data category** (no `[UNAVAILABLE]`) → max 60.
- **No sell/trim side** when holdings are given → −15.
- **Missing a material catalyst** that was public on the date (e.g. a large treasury BTC buy) → −15.

## Output
```
{ "score": <0-100>, "verdict": "<one line>",
  "dimensions": [{"name","score","why"}...],
  "top_fixes": ["most impactful concrete fix first", ...] }
```
`top_fixes` must be specific and actionable (which skill/seat to change), ranked by score impact — these feed the next iteration.

## Done when
A numeric score, per-dimension breakdown, and a ranked top_fixes list are returned.
