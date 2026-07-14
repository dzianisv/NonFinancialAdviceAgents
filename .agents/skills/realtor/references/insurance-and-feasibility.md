# Insurance & Feasibility — The Swing Variables

> Source: Policygenius / ValuePenguin wildfire & FAIR-plan references; California Earthquake Authority
> and ValuePenguin CA earthquake cost; FEMA National Flood Insurance Program; Washoe County STR FAQ;
> San Francisco Administrative Code Chapter 41A §41A.5 and the sf.gov host guide. Distilled from the
> W-2 Real-Estate Tax Research run.
> **verified_on: 2026-07-13 — re-verify before use** (carrier availability, admitted-vs-surplus
> status, deductibles, and municipal permitting all change frequently and by parcel).

Insurance and local feasibility — not the tax math — are what most often decide these deals. Model
both explicitly. **Insurance is always a low/base/high RANGE. Feasibility is a gate that runs before
any depreciation math.**

## Part 1 — Insurance: express as ranges, never a point

Standard homeowners policies **exclude** the perils that dominate NV/CA markets. The range *is* the
finding; a single number hides the decision's largest uncertainty.

| Peril | Standard policy? | How it is covered | Illustrative range (modeled, re-verify) |
|---|---|---|---|
| **Wildfire — California WUI** | Often **unavailable** on admitted market | **CA FAIR Plan** or **excess & surplus (E&S)** lines | **~$4,500 admitted → ~$25,000 E&S** — the ranking-reversing swing |
| **Wildfire — Nevada / Incline (Tahoe)** | Often **unavailable** on admitted market | **E&S / surplus lines only — Nevada has NO FAIR Plan** | **~$4,500 admitted → ~$25,000 E&S** — the ranking-reversing swing |
| **Earthquake** | **Excluded** | Separate policy (e.g. CA Earthquake Authority) | **~$3.54 / $1,000 coverage**; quotes $50–$7,500 (wide dispersion) |
| **Flood** | **Excluded** ("most homeowners insurance does not cover flood damage") | Separate **NFIP** policy | Parcel-specific; depends on flood zone |

Rules:

- **Never collapse insurance to one number.** Present low / base / high with the peril noted.
- **Wildfire E&S is the single line that can reverse a jurisdiction ranking** — a Nevada home that is
  cheapest on property tax can become the most expensive to carry once admitted wildfire coverage is
  unavailable and the owner falls to E&S.
- **FAIR Plans are state-specific: California has one; Nevada does not.** For a **Nevada** (Incline /
  Tahoe) home, the only fallback when admitted coverage is declined is the **E&S / surplus-lines**
  market — never quote a "FAIR plan" for a Nevada property. Reserve the FAIR Plan for California.
- **Get quotes in writing before committing**, especially in wildfire-exposed Tahoe/Incline.
  Admitted-vs-surplus status and deductibles can move the number by five figures.
- Mark any rate whose fetch failed or is > 90 days stale as `[UNVERIFIED]`.

## Part 2 — Feasibility gates (run BEFORE the depreciation math)

For an STR, **feasibility is the binding constraint** — a perfect §469 plan is worthless if the
property cannot legally be rented short-term. Check all three gates and stop at the first hard block.

### Gate A — Municipal / county permit

| Jurisdiction | Rule | STR feasibility |
|---|---|---|
| **Washoe County / Incline Village, NV** | Permit required **before advertising or renting < 28 days** [Washoe STR FAQ] | FEASIBLE *subject to permit + HOA* |
| **San Francisco, CA** | **SF Admin Code Ch. 41A §41A.5**: host must **certify the unit is their primary residence** (live sf.gov guide requires two primary-residence proofs); un-hosted-night cap commonly cited **90/yr** — confirm exact count against Ch. 41A §41A.5 (`[UNVERIFIED]` until fetched) | GENERALLY NOT FEASIBLE as a pure investment STR |
| **Reno / other NV & CA localities** | Verify the **specific** municipal code live each run | UNKNOWN until verified |

### Gate B — HOA / CC&Rs (can override a valid county permit)

An HOA or the recorded CC&Rs can **independently prohibit** short-term rentals **even where the county
permits them** (e.g. IVGID-area associations in Incline). This is a **private** restriction the public
permit does not cure. If the HOA/CC&Rs ban STRs, the plan is **moot** — say so before modeling.

### Gate C — Zoning / land-use

Some land-use categories restrict or bar transient rental. Confirm the parcel's zoning permits
short-term rental use.

## Feasibility verdict enum

Report one of: **FEASIBLE** | **FEASIBLE_SUBJECT_TO_PERMIT_HOA** | **NOT_FEASIBLE** | **LIMITED** |
**UNKNOWN**, each with the permit/HOA/zoning basis cited.

## What to tell the user

- Present insurance as a **range** with the peril; call out wildfire E&S as the ranking-reversing swing.
- Run **permit → HOA/CC&Rs → zoning** feasibility **before** any STR depreciation number; if any gate
  is a hard block, the §469 plan is moot.
- Mark unverifiable rates or caps as `[UNVERIFIED]`.
- Close with the educational-not-advice + CPA/tax-attorney line.
