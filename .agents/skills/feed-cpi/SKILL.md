---
name: feed-cpi
description: "Source adapter for US CPI data — fetches the latest BLS Consumer Price Index release and normalizes into a structured record: headline YoY, MoM, core YoY, release date, and source URL. Pure fetch + normalize only — no hot/cold judgment, no Fed implication. Interpretation lives in analyse-macro. Use when gathering macro data, when analyse-macro needs CPI inputs, or when asked for the latest CPI number. Degrades gracefully; never fabricates."
license: MIT
compatibility: opencode
metadata:
  audience: macro-research-pipeline
  domain: inflation-data
  role: source-adapter
  tier: macro-data
---

# feed-cpi (BLS CPI data adapter)

Pure **fetch + normalize** adapter for US CPI data. Emits a structured record consumed downstream by
`analyse-macro`. No judgment — "is this hot or cold vs expectations?" lives in `analyse-macro`.

## Citation rule — no URL = not a source

Every external claim MUST include ALL THREE:
1. **Full URL** fetched: `https://exact-page-url`
2. **Date** (ISO): `YYYY-MM-DD`  
3. **Verbatim quote**: exact words from the page

Never write source name alone. If fetch failed: `[FETCH FAILED: https://...]`.

## Primary source

```
BLS CPI summary: https://www.bls.gov/news.release/cpi.nr0.htm
BLS CPI table:   https://www.bls.gov/news.release/cpi.t01.htm
```

## Fetch procedure

1. WebFetch `https://www.bls.gov/news.release/cpi.nr0.htm` → extract:
   - Headline CPI YoY % (12-month change, all items)
   - Headline CPI MoM % (1-month change, all items, seasonally adjusted)
   - Core CPI YoY % (all items less food and energy)
   - Release date
2. On fetch failure → set field to `[FETCH FAILED: url]`; never fabricate

## Output schema

```json
{
  "category": "cpi",
  "release_date": "YYYY-MM-DD",
  "headline_yoy": 3.4,
  "headline_mom": 0.4,
  "core_yoy": 3.8,
  "source_url": "https://www.bls.gov/news.release/cpi.nr0.htm",
  "verbatim_quote": "The Consumer Price Index for All Urban Consumers (CPI-U) rose 3.4 percent over the last 12 months",
  "feeds_unavailable": []
}
```

## Hard rules

- **Never fabricate.** On fetch failure → `[FETCH FAILED: url]` in the affected field.
- **Data only.** No "this is hot", no "Fed will cut". Interpretation lives in `analyse-macro`.

## Done when

Output record contains `release_date`, `headline_yoy`, `headline_mom`, `core_yoy`, `source_url`, and `verbatim_quote` with a real URL + date. Failed fetches listed in `feeds_unavailable`.
