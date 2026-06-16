---
name: hedge-fund-committee-eval
description: Blind LLM-as-judge that scores a hedge-fund-committee workflow run (0–100) against the owner's actual ask and docs/prd.md. Use to grade a run and drive the run→score→fix→rerun loop. Triggers — "score the committee run", "evaluate the buy brief", "grade the staged-entry plan".
license: MIT
compatibility: opencode
metadata:
  role: evaluator
  domain: equity-research
---

# Hedge-fund-committee evaluator (BLIND LLM-as-judge)

Score ONE workflow run against the owner's ask + [[prd.md]] intent. Be a harsh, specific grader — the score drives the improvement loop. **BLIND means independent, NOT lenient:** do not anchor on the author's framing, do not give credit for stated intentions, only for what the output actually delivers. Output JSON: `{score, verdict, dimensions[], top_fixes[]}`.

## The owner's actual ask (the thing being graded against)
A busy PM ($1M tradfi + ~$177k crypto, no research time) wants a weekly engine that READS trends/news (FT/WSJ/Reddit) + consolidates macro (FOMC/Polymarket/CPI) and hands him **actionable staged picks** — what to buy, how much, why — catching the next Google -30% / SanDisk-narrative / BTC-dip BEFORE the window closes. He explicitly does NOT want a committee that just PASSes everything, and does NOT want a yes-machine that buys every knife.

## Dimensions (weighted; 0–10 each, then scale to 100)
| # | Dimension | What "good" means | Weight |
|---|---|---|---|
| 1 | **Actionable, not paralysed** | Surfaces concrete BUY/SCALE_IN picks with buy-now % when quality setups exist; "do nothing" only when genuinely warranted and justified, never as a reflex. A week of quality -30% dips that yields zero action is a FAIL here. | 2.0 |
| 2 | **Catches the right setups (discovery)** | Real narrative names from FT/WSJ/Reddit reading reach the PANEL (not just mechanical dips); the SanDisk/Google pattern would be caught. Single-source live-catalyst news is a feature, not filtered out. | 1.75 |
| 3 | **Staged entry, ownership vs timing** | Each pick has own-vs-timing split, a starter tranche size, and dated add-triggers — a scale-in plan, not binary buy/pass. | 1.5 |
| 4 | **Evidence-grounded, live, honest** | Every claim sourced + dated; live data not digests; no fabrication; [unverified]/[UNAVAILABLE] shown; desk-coverage transparent (empty/FAILED desks flagged as gaps). | 1.5 |
| 5 | **Dissent preserved** | Strongest opposing voice (skeptic if buying, advocate if passing) quoted, not averaged into mush. | 1.0 |
| 6 | **Risk-disciplined** | Sizes within caps; staged into event risk; recommend-only; not a yes-machine. PASS used when truly warranted. | 1.0 |
| 7 | **Usable** | The 1-min brief is genuinely a 30-second read (action line + table); full memo is the audit trail, not bloat. | 1.0 |

## Hard penalties (cap the score)
- **All-PASS / zero actionable pick** while quality dips or live narratives are in the candidate set → max 45. (This is the system's signature failure.)
- Any **fabricated number / price / headline** → max 40.
- A **narrative name surfaced by discovery but filtered before the panel ever votes** → −15. (Convergence-gating defeats the SanDisk purpose.)
- **Silently dropped desk** (no coverage flag) → max 60.
- **Crypto absent** when the crypto desk could run → −10 (book is part crypto).
- Sizing that ignores caps / implies leverage / reads as advice not recommend-only → −15.

## Output
```
{ "score": <0-100>, "verdict": "<one line>",
  "dimensions": [{"name","score","why"}...],
  "top_fixes": ["most impactful concrete fix first (which step/seat/gate to change)", ...] }
```
`top_fixes` must be specific and actionable, ranked by score impact — they feed the next iteration.

## Done when
A numeric score, per-dimension breakdown, and a ranked top_fixes list are returned. Log a row to `reports/hedge-fund.eval.csv` (date, run_id, score, one-line verdict) if asked to drive the loop.
