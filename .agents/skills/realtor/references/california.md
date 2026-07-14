# California Rules — Residency (RTC §17041/§17014), Prop 13, SF STR, Insurance

> Source: California Revenue & Taxation Code §17041, §17014 (leginfo.legislature.ca.gov); CA
> Legislative Analyst's Office on Prop 13 (lao.ca.gov); San Francisco Administrative Code Chapter 41A
> and the sf.gov STR host guide; California Earthquake Authority (earthquakeauthority.com) and
> ValuePenguin CA earthquake cost. Distilled from the W-2 Real-Estate Tax Research run.
> **verified_on: 2026-07-13 — re-verify before use** (residency rules, wage-sourcing regs, SF night
> caps, insurer availability and rates all change; the controlling SF Admin Code Ch. 41A §41A.5
> un-hosted-night count must be confirmed against the live code).

## Residency & the NV≠CA-escape correction [RTC §17041, §17014]

**This is the correction to issue whenever a user implies a Nevada purchase avoids California tax.**

- California **taxes "the entire taxable income of every resident of this state"** [RTC §17041], with
  a top marginal individual rate of **13.3%**.
- A **"resident"** [RTC §17014] includes **every individual in the state for other than a temporary or
  transitory purpose**, *and* **every individual domiciled in the state who is temporarily absent**.
- **Consequence:** buying a home in Nevada (or anywhere), **by itself, changes California wage-tax
  liability by exactly $0**. A California resident with California-source employment who buys a Nevada
  house and keeps California residency/work still owes California tax in full.
- **What actually changes it:** an **actual change of domicile AND work-sourcing** — a
  facts-and-circumstances test weighing physical days in each state, where the family home is, driver's
  license, voter registration, vehicle registration, and professional/social ties.
- **Wage sourcing rule [RTC §17951 / 18 CCR §17951-5]:** W-2 wages are sourced to **where the services
  are physically performed, not where the employer is headquartered**. After a genuine NV domicile move,
  **Nevada workdays and remote work physically performed in Nevada are generally not California-source**;
  but **in-California workdays remain CA-source, and certain deferred/equity compensation attributable
  to a period of California service stays CA-taxable** — this equity/deferred treatment is nuanced and
  should be routed to a specialist. Even after a genuine move, **CA-source wages remain
  California-taxable**. A domicile change is an **attorney** question, not a purchase.
- **Model residency SEPARATELY** from the property (PRIMARY_HOME) and from any STR (STR_INVESTMENT).
  It is a person/work attribute, never a deed attribute.

## Property tax: Proposition 13

- **Rate:** capped at **1% of assessed value plus voter-approved debt** [CA LAO on Prop 13]
  (illustratively ~$11.7k–$11.8k on a $1M home in San Francisco — a modeled estimate).
- **Purchase reset:** a purchase triggers **reassessment to market value**, resetting the assessed
  basis to the new price. No owner-occupied income-tax offset changes this.

## Short-term rentals: San Francisco

- **Controlling law:** **San Francisco Administrative Code Chapter 41A** (Residential Unit Conversion
  and Short-Term Residential Rentals), §41A.5 — cite the ordinance, not just the how-to guide.
- **Primary-residence requirement:** SF requires the host to **certify the unit is their primary
  residence** (the sf.gov host guide, which is **live**, requires two proofs of primary residence — CA
  driver's license, voter registration, utility bill, etc.). This is **fundamentally incompatible with
  a pure investment STR** — an investor who does not live in the unit generally **cannot** operate a
  legal STR there. Classify SF as **GENERALLY NOT FEASIBLE** for a pure investment STR.
- **90-night un-hosted cap:** Chapter 41A also caps **un-hosted** nights (commonly cited as **90
  nights/year**). The primary-residence conclusion is verified via the live sf.gov guide; the **exact
  90-night count is `[UNVERIFIED]`** here only because the controlling §41A.5 subsection text could not
  be fetched this run — confirm the number against SF Admin Code Ch. 41A §41A.5 live. The sf.gov guide
  page **is live** (it loads and states the primary-residence proof requirement), so do not describe it
  as a dead/404 link without rechecking.
- **Other CA localities:** verify the **specific** municipal code live each run; do not generalize SF
  rules to the rest of California.

## Insurance: earthquake + wildfire, as ranges

- **Earthquake is excluded** from standard homeowners policies and must be bought separately —
  California Earthquake Authority (CEA) averages roughly **$3.54 per $1,000 of coverage** (about
  $1,770/yr on $500k of coverage) with a **very wide** quote dispersion ($50–$7,500 cited). Express as
  a **range**, not a point.
- **Wildfire (CA WUI):** high-risk areas can lose admitted coverage and fall to **FAIR plans or E&S**
  lines that are "significantly pricier" — the same swing variable as Nevada's Tahoe exposure.
- **Flood is excluded** from standard homeowners and comes via a separate NFIP policy where
  applicable. Full peril detail and the "ranges never points" rule in `insurance-and-feasibility.md`.

## What to tell the user

- **Lead with the NV≠CA-escape correction** whenever the user frames a Nevada purchase as a way to
  dodge California tax — before modeling anything.
- Prop 13 property tax and the CA wage tax are **different questions**; do not blend them.
- SF is generally not feasible for a pure investment STR; treat the exact night cap as `[UNVERIFIED]`
  until re-verified live.
- Quote earthquake and wildfire insurance as **ranges**.
- Close with the educational-not-advice + CPA/tax-attorney line.
