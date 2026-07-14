# Sources — Verified Citation Cards (Nevada, California & Federal)

> Seeded from the W-2 Real-Estate Tax Research run. Every URL below was fetched over HTTP on the
> `verified_on` date. **verified_on: 2026-07-13 — RE-VERIFY BEFORE USE.** Tax law, rates, and
> permitting change; a card older than ~90 days must be re-fetched, and any figure whose source now
> `NOT_FOUND` / `FETCH_FAILED` is downgraded to `[UNVERIFIED]`. Do **not** invent new exact rates —
> use only the figures the cited primary source actually states.
>
> **Tiers:** T1 = controlling primary law (statute / Treasury reg / state code / agency). T2 =
> regulator or market reference (express as ranges). T3 = volatile listing (market color only, never a
> model input).

## Federal — statute & regulation (T1)

### F1 — Qualified residence interest (acquisition-debt cap)
- Claim: mortgage interest deductible only on acquisition indebtedness ≤ $750,000 (post-2017-12-15).
- 26 U.S.C. §163 — https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title26-section163&num=0&edition=prelim
- Support (IRS Topic 505): https://www.irs.gov/taxtopics/tc505
- verified_on: 2026-07-13 · tier: T1

### F2 — SALT applicable limitation amount
- Claim: 2026 aggregate SALT cap = §164(b)(7) "applicable limitation amount" ($40,400; phased down for
  high earners; reverts to $10,000 after 2029). The phase-down computation is modeling, not statute.
- 26 U.S.C. §164 — https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title26-section164&num=0&edition=prelim
- verified_on: 2026-07-13 · tier: T1

### F3 — Depreciation recovery period (transient-use 39-year)
- Claim: a dwelling used on a transient basis is nonresidential real property → **39-year** recovery
  (not the 27.5-year residential-rental period).
- 26 U.S.C. §168 — https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title26-section168&num=0&edition=prelim
- verified_on: 2026-07-13 · tier: T1

### F4 — Passive activity losses limited
- Claim: a rental activity is per se passive; losses disallowed against W-2 by default.
- 26 U.S.C. §469 — https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title26-section469&num=0&edition=prelim
- verified_on: 2026-07-13 · tier: T1

### F5 — ≤7-day average-stay exception
- Claim: activity with average customer use ≤ 7 days is not a "rental activity" under §469.
- Treas. Reg. §1.469-1T — https://www.law.cornell.edu/cfr/text/26/1.469-1T
- verified_on: 2026-07-13 · tier: T1

### F6 — Material participation tests + proof standard
- Claim: the §1.469-5T(a) tests (e.g. >500 hours) that make an STR loss non-passive; and
  §1.469-5T(f)(4) — participation "may be established by **any reasonable means**" (calendars,
  appointment books, narrative summaries), so **contemporaneous logs are NOT legally required** (though
  recommended as audit defense). A management company does **not** defeat the >500-hour test (owner's
  own hours only); it mainly burdens the substantially-all, >100-and-no-one-more, and
  facts-and-circumstances tests.
- Treas. Reg. §1.469-5T — https://www.law.cornell.edu/cfr/text/26/1.469-5T
- verified_on: 2026-07-13 · tier: T1

### F7 — Tangible personal property vs structural components (cost seg)
- Claim: cost-seg reclassifies building components into short-life tangible personal property distinct
  from structural components.
- Treas. Reg. §1.48-1 — https://www.law.cornell.edu/cfr/text/26/1.48-1
- verified_on: 2026-07-13 · tier: T1
- Note: §465 at-risk, §461(l) EBL cap, and §1245/§1250 recapture are the four backstops; the §461(l)
  cap amount is inflation-indexed and the bonus rule is keyed to **acquisition date** (see F9) —
  confirm both for the actual property and year.

### F8 — §280A personal-use / vacation-home limit
- Claim: a dwelling used for personal purposes for more than the greater of **14 days or 10% of the
  days rented at fair rental** is treated as a **residence** and rental deductions are **limited to
  rental income** [§280A(d)]; if used as a residence and **rented < 15 days**, rental income is
  **excluded** and no rental deductions are allowed [§280A(g)]. This gate runs **before** §469.
- 26 U.S.C. §280A — https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title26-section280A&num=0&edition=prelim
- verified_on: 2026-07-13 · tier: T1

### F9 — Bonus depreciation: 100% made permanent (OBBBA §70301), keyed to acquisition date
- Claim: as of 2026-07-13, **100% bonus depreciation is permanent** for qualified property **acquired
  after 2025-01-19** and placed in service thereafter; property acquired on or before 2025-01-19 stays
  on the older transition/phase-down schedule. Re-verify the acquisition date and current §168(k)
  because future law can change it; conventions and property-eligibility rules still apply.
- 26 U.S.C. §168(k) — https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title26-section168&num=0&edition=prelim
- OBBBA (One Big Beautiful Bill Act), Pub. L. 119-21, §70301 (enacted 2025-07-04) — https://www.govinfo.gov/app/details/PLAW-119publ21
- Corroboration (IRS FS-2025-03, OBBBA overview) — https://www.irs.gov/newsroom/one-big-beautiful-bill-act-tax-deductions-for-working-americans-and-seniors
- verified_on: 2026-07-13 · tier: T1

### F10 — §280A(e) mixed-use expense allocation
- Claim: when a dwelling has **both** personal and rental use, expenses must be **allocated** between
  rental and personal days under **§280A(e)** (then further limited by the §280A(d) residence cap). A
  single property *can* have mixed use — it is a **separate allocation regime**, not an impossibility,
  and is **outside** the simplified full-STR model (route day-count/allocation to a specialist).
- 26 U.S.C. §280A(e) — https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title26-section280A&num=0&edition=prelim
- verified_on: 2026-07-13 · tier: T1

### F11 — §469(i) active-participation $25,000 allowance (phaseout)
- Claim: a taxpayer who **actively participates** in a rental real-estate activity may offset up to
  **$25,000** of loss against non-passive income; the allowance **phases out $0.50 per $1 of modified
  AGI over $100,000 and is $0 at $150,000 MAGI** — generally unavailable to a high-income persona.
- 26 U.S.C. §469(i) — https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title26-section469&num=0&edition=prelim
- verified_on: 2026-07-13 · tier: T1

### F12 — §469(c)(7) real-estate-professional (REP) exception
- Claim: a rental escapes the per-se-passive rule if **one spouse individually** (a) performs **> 750
  hours** in real-property trades/businesses **and** (b) spends **more than half (> 50%)** of that
  spouse's personal-service hours in real-property trades/businesses; **employee hours count only if the
  spouse is a ≥ 5% owner** [§469(c)(7)(D)(ii)]. Spouses do **not** pool hours to meet these tests, and
  REP status alone is insufficient — the taxpayer must also materially participate (see F6 / F13).
- 26 U.S.C. §469(c)(7) — https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title26-section469&num=0&edition=prelim
- verified_on: 2026-07-13 · tier: T1

### F13 — Reg. §1.469-9 rental real-estate grouping/aggregation election (for REPs)
- Claim: a qualifying real estate professional may **elect to treat all interests in rental real estate
  as a single activity** (aggregation) under **Reg. §1.469-9** so that **material participation** is
  measured across the combined portfolio. Spousal participation may count toward material participation,
  but this does not merge the individual REP > 750 / > 50% tests.
- Treas. Reg. §1.469-9 — https://www.law.cornell.edu/cfr/text/26/1.469-9
- verified_on: 2026-07-13 · tier: T1

## Nevada (T1 / T2)

### NV1 — Property tax mechanics
- Claim: assessed at 35% of taxable value; owner-occupied primary-residence annual increase capped at
  3% (abatement class differs for non-owner-occupied / STR — confirm parcel class).
- Nevada Revised Statutes Ch. 361 — https://www.leg.state.nv.us/nrs/nrs-361.html
- verified_on: 2026-07-13 · tier: T1

### NV2 — Washoe County / Incline STR permit
- Claim: permit required before advertising or renting < 28 days; HOA/CC&Rs may independently ban STRs.
- Washoe County STR FAQ — https://www.washoecounty.gov/csd/planning_and_development/short_term_rentals/FAQ.php
- verified_on: 2026-07-13 · tier: T1

### NV3 — No individual wage income tax
- Claim: Nevada levies no individual income tax on wages (CA top rate 13.3% for contrast).
- Tax Foundation, state individual income-tax rates — https://taxfoundation.org/data/all/state/state-income-tax-rates/
- verified_on: 2026-07-13 · tier: T2

## California (T1 / T2)

### CA1 — Tax imposed on residents' entire income
- Claim: CA taxes "the entire taxable income of every resident of this state."
- RTC §17041 — https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=17041.&lawCode=RTC
- verified_on: 2026-07-13 · tier: T1

### CA2 — Definition of resident (domicile / temporary-transitory)
- Claim: resident = present for other than temporary/transitory purpose OR domiciled-but-temporarily-
  absent → a NV deed alone does not change CA residency.
- RTC §17014 — https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=17014.&lawCode=RTC
- verified_on: 2026-07-13 · tier: T1

### CA3 — Proposition 13 property tax
- Claim: 1% of assessed value + voter-approved debt; purchase triggers reassessment to market.
- CA Legislative Analyst's Office, "Understanding California's Property Taxes" — https://lao.ca.gov/Publications/Report/3497
- verified_on: 2026-07-13 · tier: T1

### CA4 — San Francisco STR: controlling ordinance + primary-residence requirement
- Claim: **SF Administrative Code Chapter 41A §41A.5** governs STRs; host must certify the unit is
  their primary residence → pure investment STR generally not feasible in SF; un-hosted-night cap
  commonly cited as 90/yr. The sf.gov host guide is **live** and confirms the primary-residence proof
  requirement (two proofs). The exact 90-night count is `[UNVERIFIED]` here because the controlling
  §41A.5 subsection text could not be fetched this run — confirm against the live SF Admin Code.
- SF Administrative Code Chapter 41A (American Legal Publishing) — https://codelibrary.amlegal.com/codes/san_francisco/latest/overview
- SF host guide (live) — https://www.sf.gov/guide-opening-short-term-residential-rental
- verified_on: 2026-07-13 · tier: T1 · status: 90-night count `[UNVERIFIED]` — confirm §41A.5 text live

### CA7 — Wage sourcing: physically-performed, not employer HQ
- Claim: a nonresident's CA gross income includes only income from **sources within California**
  [RTC §17951]; W-2 wages are sourced to **where the services are physically performed, not where the
  employer is headquartered** [18 CCR §17951-5 / FTB Pub. 1031]. After a genuine NV domicile move, NV
  workdays are generally not CA-source, but in-CA workdays and certain deferred/equity compensation for
  CA service stay CA-taxable (equity/deferred treatment is nuanced → specialist review).
- RTC §17951 — https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=17951.&lawCode=RTC
- 18 CCR §17951-5 (implementing reg) / FTB Pub. 1031, Guidelines for Determining Resident Status
- verified_on: 2026-07-13 · tier: T1 · note: equity/deferred comp `[SPECIALIST REVIEW]`

### CA5 — Earthquake insurance excluded; CEA policy
- Claim: earthquake damage excluded from standard homeowners; covered via separate CEA policy.
- California Earthquake Authority — https://www.earthquakeauthority.com/california-earthquake-insurance-policies/homeowners
- verified_on: 2026-07-13 · tier: T1

### CA6 — California earthquake insurance cost (range)
- Claim: CEA averages ~$3.54 per $1,000 of coverage; quotes range $50–$7,500 (wide dispersion).
- ValuePenguin, CA earthquake insurance cost — https://www.valuepenguin.com/california-earthquake-insurance-cost
- verified_on: 2026-07-13 · tier: T2 (express as range)

## Insurance perils — both states (T1 / T2)

### INS1 — Wildfire: FAIR plans (CA only) & excess/surplus lines
- Claim: in high-risk areas admitted coverage is often unavailable → the fallback is a **FAIR Plan (in
  California) or excess & surplus (E&S) lines**, "significantly pricier"; the ranking-reversing swing.
  **Nevada has no FAIR Plan**, so an Incline/NV home falls to **E&S / surplus lines only** — never cite
  a FAIR plan for a Nevada property.
- Policygenius, wildfire insurance — https://www.policygenius.com/homeowners-insurance/wildfire-insurance/
- verified_on: 2026-07-13 · tier: T2 (express as range)

### INS2 — FAIR plan mechanics (state-specific; CA has one, NV does not)
- Claim: how to insure a high-risk home when admitted carriers decline; FAIR Plans are state-run and
  exist in California but **not** Nevada — reserve the FAIR Plan reference for California.
- ValuePenguin, FAIR plans — https://www.valuepenguin.com/homeowners-insurance/fair-plans-and-how-do-you-insure-high-risk-home
- verified_on: 2026-07-13 · tier: T2

### INS3 — Flood excluded from homeowners; NFIP
- Claim: standard homeowners does not cover flood; coverage via separate NFIP policy.
- FEMA, Flood Insurance & NFIP — https://www.fema.gov/flood-insurance
- Terminology (Special Flood Hazard Area) — https://www.fema.gov/flood-insurance/terminology-index
- verified_on: 2026-07-13 · tier: T1

## Market color — LISTINGS ONLY (T3, never a model input)

### MKT1 — San Francisco listing (illustrative)
- Volatile; captured 2026-07-13; NOT a model input; no reproducible HTTP 200 claimed.
- https://www.zillow.com/homedetails/667-London-St-San-Francisco-CA-94112/15176411_zpid/
- verified_on: 2026-07-13 · tier: T3

### MKT2 — Incline Village listing (illustrative)
- Volatile; captured 2026-07-13; NOT a model input; no reproducible HTTP 200 claimed.
- https://www.zillow.com/homedetails/696-Bidwell-Ct-Incline-Village-NV-89451/7324367_zpid/
- verified_on: 2026-07-13 · tier: T3

---

**Re-verification protocol:** before citing any card, re-fetch the URL; update `verified_on`; if the
figure changed, use the new figure; if the fetch failed or the quote is no longer present, mark the
claim `[UNVERIFIED — confirm for placed-in-service year]`. Run the `reference-validator` subagent over
the full list, and the `skeptic` subagent over any claim-heavy conclusion, before presenting.
