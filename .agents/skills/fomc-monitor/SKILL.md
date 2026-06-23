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
Rate-path odds (market-implied): compute from ZQ Fed Funds futures — `python3.12 fedwatch_zq.py`
                                 (durable; do NOT quote the JS FedWatch page or a WebSearch summary)
```

## Rate-path probability — fetch it FIRST-HAND, never second-hand

The CME FedWatch *page* (cmegroup.com) is JS-rendered and routinely unreachable from a sandbox.
Quoting its % from a WebSearch *summary* is a real, repeated failure (news digests paraphrase and have
**inverted** the number). The durable fix: FedWatch is just arithmetic on CME 30-Day Fed Funds futures
(ZQ), and ZQ quotes ARE fetchable. Compute the implied path yourself:

```bash
python3.12 fedwatch_zq.py                       # nearest two meetings (June + July 2026 defaults)
python3.12 fedwatch_zq.py "Sep 2026,2026,9,17"  # override meeting dates as label,YYYY,MM,effective-day
```

This pulls the current target range + EFFR from the **NY Fed markets API** and ZQ futures from the
**Yahoo chart API** (both no-key, both fetched live), then solves the post-meeting EFFR implied by each
contract's month-average price and maps the implied move to P(hold)/P(cut)/P(hike). If a source is
unreachable it prints `[UNAVAILABLE]` for that leg — never a fabricated number. Always print the
as-of date the script reports. Cross-check against `prediction-market-odds` (Polymarket/Kalshi); if the
ZQ-implied and crowd numbers disagree by >5pts, report the spread rather than picking one.

## Citation rule — no URL = not a source

Every external claim (news event, data point, quote, analysis) MUST include ALL THREE:
1. **Full URL** fetched: `https://exact-page-url` (specific article, not homepage or search page)
2. **Date** (ISO): `YYYY-MM-DD` (publication or as-of date)
3. **Verbatim quote**: exact words from the page, copied not paraphrased

Format in output: `[TIER] https://exact-url (YYYY-MM-DD) — "verbatim quote"`

**Never write:**
- Source name alone (`CoinDesk`, `Bloomberg`) — without URL it is hallucination bait
- A quote without its URL
- A URL without a date
- Anything paraphrased from memory without a prior web_fetch call

**If fetch failed:** `[FETCH FAILED: https://...] — not counted toward minimum`
**If < 2 real sources:** output `INSUFFICIENT_DATA — do not guess`

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
Sources fetched:  HOP1: https://www.federalreserve.gov/newsevents/pressreleases.htm (<fetch-date>)
                  HOP2: https://www.federalreserve.gov/newsevents/pressreleases/<year>-press-fomc.htm (<fetch-date>)
                  HOP3: https://www.federalreserve.gov/newsevents/pressreleases/monetary<YYYYMMDD>a.htm (<fetch-date>)
─────────────────────────────────────────────
Summary (2-3 sentences): what the Fed said, what changed, and what it means for equities/rates.
```

## Procedure

1. **Fetch calendar** — get the next scheduled FOMC meeting date(s). Flag if we are within 10 days of a meeting (heightened sensitivity).

2. **Fetch latest statement** — exact 3-hop procedure:
   ```
   HOP 1: WebFetch https://www.federalreserve.gov/newsevents/pressreleases.htm
           Find href: /newsevents/pressreleases/2026-press-fomc.htm  (or current year)

   HOP 2: WebFetch https://www.federalreserve.gov/newsevents/pressreleases/2026-press-fomc.htm
           Find the FIRST href matching pattern: /newsevents/pressreleases/monetary2026*.htm
           (e.g. /newsevents/pressreleases/monetary20260429a.htm = April 29, 2026 meeting)

   HOP 3: WebFetch https://www.federalreserve.gov/newsevents/pressreleases/monetary20260429a.htm
           THIS is the actual FOMC statement. Read it fully.
           Extract: rate decision, key policy paragraphs, vote tally, any guidance language.
   ```
   Do NOT stop at hop 1 or hop 2. You MUST fetch hop 3 to read the actual policy language.

3. **Fetch prior statement** — the SECOND monetary*.htm link from hop 2's page. Same 3-hop procedure but take link #2.

4. **Parse tone delta** — compare key policy language:
   - Count hawkish phrases: "remains committed to returning inflation", "still elevated", "further increases may be appropriate", "restrictive", "ongoing increases"
   - Count dovish phrases: "data-dependent", "appropriate to slow", "pause", "balanced", "well-anchored expectations", "easing", "rate cuts"
   - Note any changes in the description of the labor market, inflation trajectory, and balance-sheet policy.

5. **Pull market-implied path** — run `python3.12 fedwatch_zq.py` for the ZQ-futures-implied hold/cut/hike probability for BOTH the nearest AND the following meeting (not just the nearest). Corroborate with `prediction-market-odds` (Polymarket + Kalshi). Report each meeting's P(hold) with its source and as-of date; if venues diverge >5pts, report the spread.

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
