# Tahoe rental underwriting note — 2026-07-13

Educational analysis only, not tax/legal/investment advice.

## Direct answer to your question

### 1) Listing-fact status after independent corroboration

- **11 Manzanita Ct (Stateline): verified.** Independent sources align on **$625,000**, for-sale/active framing, **2 bd / 1 ba / 1,072 sf**, **$609 HOA**, and townhouse type (Zillow + Movoto), and the Douglas assessor independently matches townhouse classification + 1,072 sf (not price).
  Zillow: https://www.zillow.com/homedetails/11-Manzanita-Ct-Stateline-NV-89449/450496345_zpid/
  Movoto: https://www.movoto.com/stateline-nv/11-manzanita-ct-stateline-nv-89449/pid_78wehd9aih/
  Douglas assessor: https://douglasnv-search.gsacorp.io/parcel/131823310054
  Captures: `/Users/engineer/Documents/Tahoe_Rental_Underwriting_Research_20260713/captures/11-manzanita-ct__zillow__20260713T215429Z.txt`, `/Users/engineer/Documents/Tahoe_Rental_Underwriting_Research_20260713/captures/11-manzanita-ct__movoto__20260713T215457Z.txt`, `/Users/engineer/Documents/Tahoe_Rental_Underwriting_Research_20260713/captures/11-manzanita-ct__douglas-assessor__20260713T215715Z.txt`.

- **1367 Carinthia Ln (Incline Village): core facts corroborated.** Redfin + Zillow align on **$950,000**, **3 bd / 2 ba / 1,152 sf**; both carry STR/Airbnb marketing language. **$429 HOA** appears in the Redfin capture and is kept as a listing observation (not Zillow-corrobated this pass).
  Redfin: https://www.redfin.com/NV/Incline-Village/1367-Carinthia-Ln-89451/home/68067114
  Zillow: https://www.zillow.com/homedetails/1367-Carinthia-Ln-Incline-Village-NV-89451/7325516_zpid/
  Captures: `/Users/engineer/Documents/Tahoe_Rental_Underwriting_Research_20260713/captures/1367-carinthia-ln__redfin-curl__20260713T215101Z.txt`, `/Users/engineer/Documents/Tahoe_Rental_Underwriting_Research_20260713/captures/1367-carinthia-ln__zillow__20260713T215200Z.txt`.

- **109 Lake Village Dr Unit A: not independently confirmed as a current active listing.** A live Redfin observation shows **$650,000 / Active / MLS 260004514 / HOA $626**, but the independent Zillow record for the same unit shows `homeStatus:"OTHER"` and no current for-sale fact card in fetched content; no second current source was captured. Treat current price/status/HOA as a diligence item to confirm with listing agent + MLS before relying; your earlier $625k figure may be stale, but it is also unconfirmed without MLS/agent confirmation.
  Redfin: https://www.redfin.com/NV/Stateline/109-Lake-Village-Dr-89449/unit-A/home/69082956
  Zillow: https://www.zillow.com/homedetails/109-Lake-Village-Dr-A-Stateline-NV-89449/2084466325_zpid/
  Captures: `/Users/engineer/Documents/Tahoe_Rental_Underwriting_Research_20260713/captures/109-lake-village-dr-unit-a__redfin__20260713T214915Z.txt`, `/Users/engineer/Documents/Tahoe_Rental_Underwriting_Research_20260713/captures/109-lake-village-dr-unit-a__zillow__20260713T215012Z.txt`.

### 2) Is the ~$300k Carinthia premium likely "hidden damage"?

From grounded listing evidence, the premium is more plausibly explained by **product + STR-marketing profile + positioning differences** than by proven hidden damage:

- Carinthia is marketed as a 3-bed, 2-bath, 1,152-sf property with freestanding/Airbnb language (marketing claim) and Redfin-listed HOA $429.
  Sources: https://www.redfin.com/NV/Incline-Village/1367-Carinthia-Ln-89451/home/68067114, https://www.zillow.com/homedetails/1367-Carinthia-Ln-Incline-Village-NV-89451/7325516_zpid/, capture refs above.
- Manzanita and Lake Village Unit A are attached 2-bedroom Lake Village product with materially higher listed HOA burden ($609 Manzanita; $626 Unit A from Redfin observation).
  Sources: https://www.zillow.com/homedetails/11-Manzanita-Ct-Stateline-NV-89449/450496345_zpid/, https://www.movoto.com/stateline-nv/11-manzanita-ct-stateline-nv-89449/pid_78wehd9aih/, https://www.redfin.com/NV/Stateline/109-Lake-Village-Dr-89449/unit-A/home/69082956, capture refs above.
- Carinthia also has a **property-type diligence conflict**: Redfin classifies single-family/house, while Zillow metadata describes multi-family/multiple-occupancy and listing text says freestanding home.
  Sources: https://www.redfin.com/NV/Incline-Village/1367-Carinthia-Ln-89451/home/68067114, https://www.zillow.com/homedetails/1367-Carinthia-Ln-Incline-Village-NV-89451/7325516_zpid/, capture refs above.

Neighborhood/Incline premium remains an **inference**, not proof; inspection, HOA docs, permit records, title, and insurance can overturn this conclusion.
References: https://www.washoecounty.gov/csd/planning_and_development/short_term_rentals/FAQ.php, https://nltfpd.org/short-term-rentals, https://nltfpd.org/defensible-space.

### 3) Are the cheaper Lake Village/Stateline units automatically better investments?

No.

- There is no independently archived LTR lease-comp set or STR ADR/occupancy packet in this evidence package, so a defensible NOI comparison is not available yet (package artifacts: `/Users/engineer/Documents/Tahoe_Rental_Underwriting_Research_20260713/report.md`, `/Users/engineer/Documents/Tahoe_Rental_Underwriting_Research_20260713/claims.jsonl`).
- HOA burden alone is material for the attached Lake Village product ($609 Manzanita; Redfin-observed $626 Unit A; Redfin-observed $429 Carinthia).
  Sources: https://www.zillow.com/homedetails/11-Manzanita-Ct-Stateline-NV-89449/450496345_zpid/, https://www.movoto.com/stateline-nv/11-manzanita-ct-stateline-nv-89449/pid_78wehd9aih/, https://www.redfin.com/NV/Stateline/109-Lake-Village-Dr-89449/unit-A/home/69082956, https://www.redfin.com/NV/Incline-Village/1367-Carinthia-Ln-89451/home/68067114, capture refs above.
- Unit A status/price is unresolved across sources, so even entry price assumptions are not yet underwriting-grade.
  Sources: https://www.redfin.com/NV/Stateline/109-Lake-Village-Dr-89449/unit-A/home/69082956, https://www.zillow.com/homedetails/109-Lake-Village-Dr-A-Stateline-NV-89449/2084466325_zpid/, capture refs above.

So the cheaper units are **not automatically superior** under current evidence; legal gate + data gaps dominate (see Unit A source conflict and county-rule sources above: https://www.redfin.com/NV/Stateline/109-Lake-Village-Dr-89449/unit-A/home/69082956, https://www.zillow.com/homedetails/109-Lake-Village-Dr-A-Stateline-NV-89449/2084466325_zpid/, https://www.washoecounty.gov/csd/planning_and_development/short_term_rentals/FAQ.php, https://www.douglascountynv.gov/government/departments/community-development/vacation-home-rentals).

### 4) Can you "depreciate the house cost in 5 years" to offset W-2?

That framing is incorrect.

- **Land never depreciates.** (IRS Pub. 527: https://www.irs.gov/publications/p527)
- Building shell is generally long-life depreciation (LTR commonly 27.5 years; confirm classification with CPA). (IRC §168 baseline: https://www.law.cornell.edu/uscode/text/26/168)
- Cost segregation may move eligible components to shorter lives. Current §168(k)(1)(A) says qualifying property receives an allowance equal to **100 percent of adjusted basis**, while §168(k)(2)(A)(i)(I) limits qualified property here to recovery periods of 20 years or less; acquisition-date and other eligibility rules still require CPA confirmation. (https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title26-section168&num=0&edition=prelim, https://www.law.cornell.edu/uscode/text/26/168)
- W-2 offset depends on activity characterization: <=7-day average-stay exception + material participation can alter passive treatment. (https://www.law.cornell.edu/cfr/text/26/1.469-1T, https://www.law.cornell.edu/cfr/text/26/1.469-5T)
- §280A personal-use limits and CA nonconformity can materially change realized tax benefit. (https://www.irs.gov/taxtopics/tc415, https://www.ftb.ca.gov/forms/2024/2024-3885a-instructions.html, https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=17041.&lawCode=RTC)

### 5) Five-year-sale reality: tax benefit is often timing/deferral, not free money

A five-year hold should model, at minimum:

1. selling costs,
2. loan payoff,
3. §1245 recapture on cost-seg personalty (https://www.law.cornell.edu/uscode/text/26/1245),
4. §1250 / unrecaptured-gain layer on building depreciation (https://www.law.cornell.edu/uscode/text/26/1250),
5. residual gain tax,
6. suspended passive-loss release where applicable.

So accelerated depreciation can help early cash taxes but does not by itself make a weak property good (https://www.law.cornell.edu/uscode/text/26/168, https://www.law.cornell.edu/uscode/text/26/1245, https://www.law.cornell.edu/uscode/text/26/1250).

## Tahoe legality blockers that prevent a BUY call today

1. **Lake Village HOA/CC&R rental restrictions are still unverified.** (County permission baseline does not provide HOA text: https://www.douglascountynv.gov/government/departments/community-development/vacation-home-rentals; listing pages: https://www.zillow.com/homedetails/11-Manzanita-Ct-Stateline-NV-89449/450496345_zpid/, https://www.redfin.com/NV/Stateline/109-Lake-Village-Dr-89449/unit-A/home/69082956)
2. **Douglas parcel-tier/cap/waitlist eligibility is unverified at address level.** (https://www.douglascountynv.gov/government/departments/community-development/vacation-home-rentals, https://www.douglascountynv.gov/news/recent-news/applications_for_v_h_r_advisory_board)
3. **Carinthia permit transferability/current permit status unverified** (marketing language is not legal proof). (https://www.washoecounty.gov/csd/planning_and_development/short_term_rentals/FAQ.php, https://www.redfin.com/NV/Incline-Village/1367-Carinthia-Ln-89451/home/68067114, https://www.zillow.com/homedetails/1367-Carinthia-Ln-Incline-Village-NV-89451/7325516_zpid/)
4. **IVGID renter recreation-access assumptions unverified.** (https://teamblairtahoe.com/blog/ivgid-explained-beaches-passes-and-perks, https://nltfpd.org/short-term-rentals)
5. **Condo warrantability/master insurance/special-assessment risk not underwritten.** (Package diligence state: `/Users/engineer/Documents/Tahoe_Rental_Underwriting_Research_20260713/report.md`)

Legal-source anchors:
Douglas VHR: https://www.douglascountynv.gov/government/departments/community-development/vacation-home-rentals
Douglas lodging tax: https://www.douglascountynv.gov/cms/One.aspx?portalId=12493103&pageId=13612059
Washoe STR FAQ: https://www.washoecounty.gov/csd/planning_and_development/short_term_rentals/FAQ.php
Washoe STR ordinance/history: https://www.washoecounty.gov/csd/planning_and_development/short_term_rentals/archive-strhistory.php
NLTFPD STR + defensible space: https://nltfpd.org/short-term-rentals and https://nltfpd.org/defensible-space

## Preliminary fit ranking (not a buy recommendation)

1. **Carinthia** — best apparent STR candidate from listing narrative + 3-bed layout, but still blocked by permit/type/insurance diligence. (https://www.redfin.com/NV/Incline-Village/1367-Carinthia-Ln-89451/home/68067114, https://www.zillow.com/homedetails/1367-Carinthia-Ln-Incline-Village-NV-89451/7325516_zpid/)
2. **Manzanita** — independently verified listing facts, but attached 2-bed format + HOA load still pressure LTR economics unless rent comps are proven. (https://www.zillow.com/homedetails/11-Manzanita-Ct-Stateline-NV-89449/450496345_zpid/, https://www.movoto.com/stateline-nv/11-manzanita-ct-stateline-nv-89449/pid_78wehd9aih/, https://douglasnv-search.gsacorp.io/parcel/131823310054)
3. **Lake Village Unit A** — current status/price conflict across sources keeps this as a diligence hold, not a priced conviction. (https://www.redfin.com/NV/Stateline/109-Lake-Village-Dr-89449/unit-A/home/69082956, https://www.zillow.com/homedetails/109-Lake-Village-Dr-A-Stateline-NV-89449/2084466325_zpid/)

## Bottom line

- The observed spread is more consistent with product mix + STR-marketed positioning than proven hidden damage; neighborhood premium is still an inference, not proof. (https://www.redfin.com/NV/Incline-Village/1367-Carinthia-Ln-89451/home/68067114, https://www.zillow.com/homedetails/1367-Carinthia-Ln-Incline-Village-NV-89451/7325516_zpid/, https://www.zillow.com/homedetails/11-Manzanita-Ct-Stateline-NV-89449/450496345_zpid/, https://www.redfin.com/NV/Stateline/109-Lake-Village-Dr-89449/unit-A/home/69082956)
- Cheaper entry price alone is not enough here: HOA burden + unresolved legal/status diligence dominate the underwriting risk today. (https://www.washoecounty.gov/csd/planning_and_development/short_term_rentals/FAQ.php, https://www.douglascountynv.gov/government/departments/community-development/vacation-home-rentals, https://www.zillow.com/homedetails/11-Manzanita-Ct-Stateline-NV-89449/450496345_zpid/, https://www.movoto.com/stateline-nv/11-manzanita-ct-stateline-nv-89449/pid_78wehd9aih/, https://www.redfin.com/NV/Stateline/109-Lake-Village-Dr-89449/unit-A/home/69082956, https://www.zillow.com/homedetails/109-Lake-Village-Dr-A-Stateline-NV-89449/2084466325_zpid/)
- “Depreciate in 5 years to offset W-2” remains incomplete without activity tests, §168/§469/§280A gating, and recapture modeling. (https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title26-section168&num=0&edition=prelim, https://www.law.cornell.edu/cfr/text/26/1.469-1T, https://www.law.cornell.edu/cfr/text/26/1.469-5T, https://www.irs.gov/taxtopics/tc415, https://www.law.cornell.edu/uscode/text/26/1245, https://www.law.cornell.edu/uscode/text/26/1250)
- With missing lease/ADR comp packets plus open permit/HOA/insurance/inspection diligence, current stance stays **no BUY recommendation yet**. (`/Users/engineer/Documents/Tahoe_Rental_Underwriting_Research_20260713/report.md`, https://www.washoecounty.gov/csd/planning_and_development/short_term_rentals/FAQ.php, https://www.douglascountynv.gov/government/departments/community-development/vacation-home-rentals, https://nltfpd.org/short-term-rentals)
