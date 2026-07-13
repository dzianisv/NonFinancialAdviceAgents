# Rental Underwriting Tax Rules (US + California)

Educational reference only. Tax treatment is fact-specific and must be confirmed with a CPA.

## Federal baseline rules (primary sources)

| Topic | Practical underwriting implication | Primary source |
|---|---|---|
| Bonus depreciation under §168(k) | Qualified <=20-year property can be eligible for current-year bonus treatment (input-driven, not a hardcoded forever constant). Used property can qualify only if statutory acquisition rules are met. | https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title26-section168&num=0&edition=prelim |
| Effective date language | Current statutory text references property acquired after 2025-01-19 for 100% rate in operative text. Re-verify each filing year and acquisition-date eligibility. | https://www.law.cornell.edu/uscode/text/26/168 |
| Passive activity rules | Rental losses are generally passive unless an exception applies. | https://www.law.cornell.edu/uscode/text/26/469 |
| <=7-day average stay rule | If average customer use <=7 days, activity can be treated as non-rental for §469 grouping tests. This is separate from §168 life classification. | https://www.law.cornell.edu/cfr/text/26/1.469-1T |
| Material participation tests | Nonpassive STR treatment requires material participation tests to be met. | https://www.law.cornell.edu/cfr/text/26/1.469-5T |
| Personal-use limitation (§280A) | Personal use >14 days or >10% of rental days can limit current loss use. | https://www.irs.gov/taxtopics/tc415 and https://www.law.cornell.edu/uscode/text/26/280A |
| At-risk limits | Losses can be limited by basis/at-risk constraints. | https://www.law.cornell.edu/uscode/text/26/465 |
| Sale recapture layers | Cost-seg personalty can face §1245 ordinary recapture; building depreciation can create unrecaptured §1250 layer. | https://www.law.cornell.edu/uscode/text/26/1245 and https://www.law.cornell.edu/uscode/text/26/1250 |
| Like-kind exchange reference | §1031 can defer gain in qualifying real-property exchanges, but assumptions must be explicit and are not automatic. | https://www.law.cornell.edu/uscode/text/26/1031 |

## LTR active participation allowance (model approximation)

Use as an underwriting approximation only:

- max allowance: `$25,000`
- phaseout starts: `MAGI = $100,000`
- phaseout reaches zero: `MAGI = $150,000`
- reduction factor: `$0.50 per $1` over $100,000

Formula:

```text
allowance = 25,000                          (MAGI <= 100,000)
allowance = 25,000 - 0.5*(MAGI - 100,000)  (100,000 < MAGI < 150,000)
allowance = 0                               (MAGI >= 150,000)
```

## Depreciation-life caution for transient STR

- The <=7-day test is a **§469 passive-activity** concept.
- Building recovery life for transient use is a **§168 classification** question.
- For single-house transient STR facts, 27.5 vs 39 years can be case-specific in practice.
- When unresolved, underwrite both sensitivities and require CPA confirmation.

## California layer

| Topic | Underwriting implication | Source |
|---|---|---|
| CA resident taxation | California residents are taxed on worldwide income; model CA tax impact even for out-of-state activity. | https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=17041.&lawCode=RTC |
| Bonus depreciation conformity | CA does not conform to federal bonus depreciation; federal/state schedules should be modeled separately. | https://www.ftb.ca.gov/forms/2024/2024-3885a-instructions.html |
| STR passive/nonpassive classification | Do not assume CA automatically follows federal <=7-day logic in every fact pattern; require explicit state treatment confirmation before modeling nonpassive losses. | https://www.ftb.ca.gov/forms/2024/2024-3801-instructions.html |

## Modeling convention warnings

- This calculator intentionally uses straight-line approximations with remaining-basis caps and does **not** implement MACRS mid-month/mid-quarter/half-year conventions.
- Treat modeled recapture/gain outputs as underwriting estimates only; filing computations require CPA software/workpapers.

## IRS plain-language references

- IRS Pub 527 (Residential Rental Property): https://www.irs.gov/publications/p527
- IRS Pub 925 (Passive Activity / At-Risk): https://www.irs.gov/publications/p925
