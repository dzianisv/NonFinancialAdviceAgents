# Rental Underwriting Data Sources (Tahoe-focused, reusable)

Use this as the grounding checklist before any LTR/STR recommendation.

## 1) Property-level facts

| Data | Acceptable source | Notes |
|---|---|---|
| Price/status/DOM/sqft/HOA/listing remarks | Redfin/Zillow/Realtor MLS page | Keep "listing claims" separate from verified legal docs. |
| Public-record inconsistencies | County assessor / listing public-record panel | Flag conflicts (e.g., type, year built, sqft). |
| Condo/townhome risk items | HOA package, reserve study, master policy, special assessment history | Mandatory before underwriting leverage risk. |

## 2) STR legality and compliance (hard gate for STR mode)

| Jurisdiction | Required checks | Primary source |
|---|---|---|
| Douglas County (Tahoe Township) | VHR framework exists, but parcel tier/cap/waitlist and address eligibility must be verified for the specific parcel. | https://www.douglascountynv.gov/government/departments/community-development/vacation-home-rentals |
| Douglas County lodging tax | Include transient lodging tax assumptions (currently 14% + $5 per room/night per county page). | https://www.douglascountynv.gov/cms/One.aspx?portalId=12493103&pageId=13612059 |
| Washoe County | Permit required, local responsible party, liability coverage requirement, permit nontransferability, HOA supremacy over county allowance. | https://www.washoecounty.gov/csd/planning_and_development/short_term_rentals/FAQ.php |
| Washoe ordinance history/current | Recheck latest ordinance posture and implementation notes before relying on stale summaries. | https://www.washoecounty.gov/csd/planning_and_development/short_term_rentals/archive-strhistory.php |
| North Lake Tahoe Fire Protection District | STR and defensible-space/fire compliance obligations may affect permit viability and operating cost. | https://nltfpd.org/short-term-rentals and https://nltfpd.org/defensible-space |

### HOA/CC&R rule

County permission does **not** override HOA/CC&R restrictions. STR mode stays `BLOCKED` until the governing HOA docs confirm compatibility.

## 3) Revenue assumptions

| Use case | Minimum evidence | Notes |
|---|---|---|
| LTR rent assumption | 3+ comparable long-term leases or broker/property-manager rent opinion for VERIFIED BUY-quality input. | Listing-site rent estimate can be used only as a HYPOTHETICAL scenario prior, not VERIFIED BUY evidence. |
| STR ADR/occupancy | AirDNA or PriceLabs preferred; otherwise >=3 dated cited comps with fit notes. | If missing, STR revenue is `[UNAVAILABLE]` and mode is blocked. |
| Seasonality | Monthly profile or shoulder-season discount assumptions | Document assumption source and confidence. |

## 4) Expense assumptions

Must source at least:
- property tax estimate (county/escrow estimate),
- insurance quote (dwelling + landlord + liability for STR where applicable),
- HOA dues and fee escalation language,
- utilities and snow/removal assumptions,
- management, maintenance, capex reserve assumptions,
- STR-specific cleaning/platform/tax burden.

## 5) Financing assumptions

Document:
- rate lock quote date and terms,
- amortization and points,
- down payment and reserves,
- closing-cost estimate source.

## 6) Minimum underwriting packet before any BUY verdict

1. Address-level STR permit path and status.
2. HOA/CC&R rental rule extract.
3. Revenue evidence packet (LTR: 3+ comps or broker/property-manager opinion; STR: AirDNA/PriceLabs or 3+ comps).
4. Insurance quote.
5. Full operating-cost budget.
6. Tax profile assumptions reviewed with CPA (especially §469, §280A, CA split).

Without this packet, return `PASS` or `BLOCKED`, not a buy recommendation.

Evidence strings/URLs are reviewed by the analyst + skeptic; the deterministic calculator only enforces the declared status/source-type/comps-count shape.
