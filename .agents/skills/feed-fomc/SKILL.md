---
name: feed-fomc
description: "Source adapter for Federal Reserve FOMC data — fetches official federalreserve.gov calendar, most recent statement/minutes, and computes rate-path probabilities from ZQ Fed Funds futures. Emits a normalized data record consumed by analysis-macro and macro-panel. Pure fetch + normalize only — no market-impact judgment. Use when gathering Fed policy data, when analysis-macro needs FOMC inputs, or when asked for the latest FOMC statement, meeting date, or rate-path odds. Degrades gracefully; never fabricates."
license: MIT
compatibility: opencode
metadata:
  audience: macro-research-pipeline
  domain: fed-policy-data
  role: source-adapter
  tier: macro-data
---

# feed-fomc (Federal Reserve data adapter)

Pure **fetch + normalize** adapter for Fed policy data. Emits a structured record consumed downstream by
`analysis-macro`, `macro-panel`, and `superforecasting`. No market-impact judgment — interpretation lives
in those downstream skills.

## Citation rule — no URL = not a source

Every external claim MUST include ALL THREE:
1. **Full URL** fetched: `https://exact-page-url`
2. **Date** (ISO): `YYYY-MM-DD`
3. **Verbatim quote**: exact words from the page

Format: `[source] https://exact-url (YYYY-MM-DD) — "verbatim quote"`

Never write source name alone. If fetch failed: `[FETCH FAILED: https://...]`.

## Primary sources (official gov only)

```
Calendar:    https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
Statements:  https://www.federalreserve.gov/newsevents/pressreleases.htm
Minutes:     https://www.federalreserve.gov/monetarypolicy/fomcminutes.htm
Chair press: https://www.federalreserve.gov/newsevents/speech.htm
Rate-path:   compute from ZQ Fed Funds futures via fedwatch_zq.py (do NOT quote CME FedWatch page or WebSearch summaries — they have inverted numbers)
```

## Rate-path probability — fetch first-hand, never second-hand

CME FedWatch page is JS-rendered and unreachable from a sandbox. ZQ quotes are fetchable. Compute directly:

```bash
python3.12 fedwatch_zq.py                       # nearest two meetings
python3.12 fedwatch_zq.py "Sep 2026,2026,9,17"  # override meeting date
```

Pulls current target range + EFFR from NY Fed markets API and ZQ futures from Yahoo chart API (both keyless, both live).

## Fetch procedure

1. **GET calendar** — WebFetch `https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm` → extract next scheduled meeting date(s)
2. **GET latest statement** (3-hop):
   - HOP 1: WebFetch `https://www.federalreserve.gov/newsevents/pressreleases.htm` → find href for current-year FOMC press releases
   - HOP 2: WebFetch that href → find href matching `monetary{YYYY}*.htm`
   - HOP 3: WebFetch that statement URL → extract full statement text
3. **GET rate-path probabilities** — run `fedwatch_zq.py`
4. **On any fetch failure** — set the affected field to `[FETCH FAILED: <url>]`; never fabricate

## Output schema

```json
{
  "category": "fomc",
  "next_meeting": "YYYY-MM-DD",
  "statement_url": "https://www.federalreserve.gov/newsevents/pressreleases/monetary20260429a.htm",
  "statement_date": "YYYY-MM-DD",
  "statement_text": "<full text or [FETCH FAILED: url]>",
  "rate_current_range": "5.25–5.50%",
  "rate_path_probs": {
    "next_meeting": { "hold": 0.72, "cut_25": 0.25, "hike_25": 0.03 }
  },
  "sources_fetched": [
    "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm (YYYY-MM-DD)",
    "https://www.federalreserve.gov/newsevents/pressreleases/monetary20260429a.htm (YYYY-MM-DD)"
  ],
  "feeds_unavailable": []
}
```

## Hard rules

- **Never fabricate.** On fetch failure → `[FETCH FAILED: url]` in the affected field.
- **Never quote CME FedWatch page or WebSearch summaries** for rate probabilities — use `fedwatch_zq.py` only.
- **Data only.** No "this is hawkish", no "this implies rate cuts". Interpretation lives in `analysis-macro`.

## Done when

Output record contains: `next_meeting`, `statement_url`, `statement_date`, `rate_path_probs`, and `sources_fetched` with real URLs + dates. Failed fetches listed in `feeds_unavailable`. No market-impact language in the record.
