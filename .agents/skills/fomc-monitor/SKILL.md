---
name: fomc-monitor
description: Monitor the Federal Reserve FOMC calendar, statements, and meeting minutes. Use when asked "what did the Fed say", "next FOMC meeting", "is the Fed hawkish or dovish", "rate hike probability", "parse Fed statement", "Fed tone shift", "FOMC schedule", or as a scheduled daily check. Fetches official sources (federalreserve.gov), parses hawkish/dovish language delta vs the prior statement, and outputs a structured signal consumed by macro-panel, superforecasting, and regime-detection. Not financial advice.
license: MIT
compatibility: opencode
metadata:
  audience: macro-aware-investors
  domain: central-bank-policy-monitoring
  role: fed-primary-source-monitor
---

# FOMC Monitor

Fetch the official FOMC calendar, most recent statement/minutes, and parse the hawkish/dovish tone shift vs the prior statement. Output a structured signal for the rest of the pipeline.

## Primary sources (always use official gov sources first)

```
Calendar:    https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
Statements:  https://www.federalreserve.gov/newsevents/pressreleases.htm   (filter: monetary policy)
Minutes:     https://www.federalreserve.gov/monetarypolicy/fomcminutes.htm
Chair press: https://www.federalreserve.gov/newsevents/speech.htm           (Powell speeches)
CME FedWatch (market-implied): via prediction-market-odds skill
```

## Output contract

Every run MUST produce a structured block:

```
FOMC SIGNAL — <date>
─────────────────────────────────────────────
Next meeting:     <date(s)>
Current rate:     <Fed Funds target range>
Priced next move: <from prediction-market-odds / CME FedWatch>
Tone:             HAWKISH / NEUTRAL / DOVISH  (vs prior statement)
Tone delta:       +2 / 0 / -1  (directional shift, += more hawkish)
Key language:     "<exact quote from statement that moved the needle>"
Changed from:     "<prior statement equivalent phrase>"
Risk-asset signal: RISK_ON / NEUTRAL / RISK_OFF
─────────────────────────────────────────────
Summary (2-3 sentences): what the Fed said, what changed, and what it means for equities/rates.
```

## Procedure

1. **Fetch calendar** — get the next scheduled FOMC meeting date(s). Flag if we are within 10 days of a meeting (heightened sensitivity).

2. **Fetch latest statement** — exact steps:
   ```
   a. WebFetch: https://www.federalreserve.gov/newsevents/pressreleases.htm
   b. Scan the HTML for href links matching the pattern: /newsevents/pressreleases/monetary20*.htm
      (e.g. /newsevents/pressreleases/monetary20260507a.htm)
   c. The FIRST such link is the most recent FOMC statement.
   d. WebFetch: https://www.federalreserve.gov<that href>
   e. Extract: rate decision, key language paragraphs, vote tally.
   ```
   Do NOT stop at step (a) — the index page is NOT the statement. You MUST follow the link in step (d).

3. **Fetch prior statement** — the SECOND monetary*.htm link from the same index page. Same fetch procedure.

4. **Parse tone delta** — compare key policy language:
   - Count hawkish phrases: "remains committed to returning inflation", "still elevated", "further increases may be appropriate", "restrictive", "ongoing increases"
   - Count dovish phrases: "data-dependent", "appropriate to slow", "pause", "balanced", "well-anchored expectations", "easing", "rate cuts"
   - Note any changes in the description of the labor market, inflation trajectory, and balance-sheet policy.

5. **Pull market-implied path** — invoke `prediction-market-odds` skill for CME FedWatch probabilities for the next 2 meetings.

6. **Emit the structured signal** above. Route to `macro-panel` as the "Fed" input.

## Hawkish / Dovish keyword reference

**Hawkish signals:** "elevated inflation", "remains committed", "further firming", "restrictive for longer", "above target", "labor market remains tight", "wage growth elevated", "ongoing increases"

**Dovish signals:** "inflation has eased", "below 2%", "appropriate to hold", "well-anchored", "moderating", "labor market cooling", "rate cuts", "balance sheet reduction pace to slow"

**Neutral:** "data-dependent", "meeting-by-meeting", "monitoring developments"

## Schedule recommendation

- **Run daily at 08:00 UTC** — on non-meeting days, a 60-second fetch confirms nothing changed. On meeting days (typically 2pm ET), re-run at 19:00 UTC after the statement drops.
- Flag meeting days on the calendar check so the agent knows to re-run.

## Minutes vs Statement

The **Statement** is released the day of the meeting — the primary signal. The **Minutes** are released ~3 weeks later and contain deliberation details (useful for superforecasting the *next* move). Read both; weight the statement more heavily for near-term signals.

## Integration

- Feed output to `macro-panel` as the "Fed" chair position
- Feed rate-path probability to `superforecasting` as the market-implied anchor
- If Tone = HAWKISH and Tone delta ≥ +2: set regime input toward RISK_OFF (tighter financial conditions)
- If Tone = DOVISH and Tone delta ≤ -2: set regime input toward RISK_ON (easing supports equities)
