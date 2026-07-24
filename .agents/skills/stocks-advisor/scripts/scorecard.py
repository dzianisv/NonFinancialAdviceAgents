#!/usr/bin/env python3
"""REMOVED — scorecard.py no longer exists as a verdict engine.

This file is a hard-fail shim, on purpose. It does NOT forward to triage.py and
it does NOT emit a verdict, because a silent forward would let a stale caller
keep printing an ACTION that nothing computes any more.

WHY IT WAS REMOVED (2026-07-24)
-------------------------------
scorecard.py was a static rule tree that emitted HOLD/TRIM/EXIT/ADD/WAIT. It
failed twice on the same ticker:

  NEM, a +119% winner trading below both its 50d and 200d MA, matched NO rule:
    rule 0.5 (exhaustion)        needed RSI < 40   -> NEM RSI = 47.9   MISS
    rule 0.7 (early trend break) needed dd > -25%  -> NEM dd  = -29.6% MISS
  ...so it fell through to rule 4 and printed WAIT. The entire quadrant
  {dd <= -25% AND RSI >= 40} had no trend-break coverage at all.

  MRVL got a TRIM out of rule 3 ("expensive + uptrend") — a sell originated by
  price and multiple alone, with no thesis seat involved.

Both are the same root cause: a script was making investment decisions from a
partial rule tree. Widening a threshold would not fix the class of bug.

WHAT TO USE INSTEAD
-------------------
  scripts/triage.py   — ranks ATTENTION (REVIEW_NOW / REVIEW / NO_ACTION) so
                        every position gets screened. It emits no verdicts.
  The panel seats     — the verdict layer (SKILL.md Step 2). A TRIM or EXIT may
                        only be ORIGINATED by the fundamentals, narrative or
                        smart-money seat finding the thesis impaired, with
                        stated evidence. Technicals are timing and stops only.

See SKILL.md §SELL ORIGINATION RULE and §Step 0.82.
"""
import sys

MESSAGE = __doc__.strip()

if __name__ == "__main__":
    sys.stderr.write(MESSAGE + "\n\n")
    sys.stderr.write(
        "REFUSING TO RUN. Re-run as:\n"
        "  python3 .agents/skills/stocks-advisor/scripts/triage.py "
        ".cache/stocks-advisor/fundamentals/ --positions <positions.csv>\n")
    sys.exit(2)
