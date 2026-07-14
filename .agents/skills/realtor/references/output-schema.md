# Output Schema — Markdown Contract, Evidence Gates, and Optional JSON Companion

> Source: Skill design for the `realtor` W-2 real-estate/STR tax advisor; gates adapted from AGENTS.md
> Invariant #6 (skeptic) and the repo `reference-validator` convention.
> **verified_on: 2026-07-13 — re-verify before use.**

Every `realtor` response returns the **Markdown schema** below. A **JSON companion** is optional and
included when the caller asks for machine-readable output. Context (portfolio, brief, raw figures)
goes at the top of the working notes; the schema is the final rendered answer.

## Evidence gates (all must pass before presenting)

1. **Current-date gate** — anchor every claim to today's date; tax law changes yearly.
2. **Freshness gate** — every statutory/rate figure carries a `verified_on` date + primary-source URL.
   If > 90 days stale, uncited, or the fetch failed → mark `[UNVERIFIED — confirm for placed-in-service
   year]`; do not state as fact.
3. **Primary-source gate** — legal claims cite controlling primary law (Title 26 / Treas. Reg. / RTC /
   NRS / municipal code); cost claims cite a regulator/market source and are expressed as **ranges**.
4. **Citation-verification gate** — spawn `reference-validator` over the citation list; any
   `NOT_FOUND` / `FETCH_FAILED` source is downgraded to `[UNVERIFIED]`.
5. **Listing gate** — Zillow/Redfin prices are **market color only**, never model inputs; label them
   volatile and captured-on-date.
6. **Skeptic gate** — spawn the `skeptic` subagent over every price level, tax-mechanic claim, and
   macro/regulatory statement; present only after PASS or all challenges resolved with fetched data.
7. **Blocklist gate** — the output must carry the disclaimer block and must **NOT** contain the words
   `guaranteed`, `will save`, or `risk-free`. Reword to "modeled," "estimated," or "may, if
   [conditions] hold."
8. **NV≠CA-escape gate** — if the plan implies a Nevada purchase avoids CA tax without a real domicile
   change, the output opens with the correction.

## Markdown schema (always rendered)

```markdown
## Realtor — Tax Reasoning (Nevada & California)

**Question type:** PRIMARY_HOME | STR_INVESTMENT | RESIDENCY | MIXED (auto-split)
*MIXED = one property with both personal and rental use → a separate §280A allocation regime (§280A(d)/(e)/(g)); route day-count/allocation to a specialist, do not stack the full itemized + full depreciation benefits.*
**Jurisdiction(s):** NV | CA | both | OTHER — *federal chain still applies; state/local sections UNKNOWN until the jurisdiction is named and its primary sources are verified*
**NV≠CA-escape correction:** N/A | ISSUED — <one-line reason>

### A. Primary-home carry (if applicable)
| Item | Value |
|---|---|
| Itemized benefit (yr1, modeled) | $<range> @ <marginal rate> — *modeled, not a promise* |
| Property tax (normalized est.) | $<range> + statute cite (NRS 361 / Prop 13) |
| Insurance | **low / base / high RANGE** + perils (wildfire / earthquake / flood) |

### B. STR investment (if applicable — SEPARATE property, never stacked on A; render in THIS order)
| Item | Value |
|---|---|
| Feasibility (gate — runs first) | FEASIBLE | FEASIBLE_SUBJECT_TO_PERMIT_HOA | NOT_FEASIBLE | LIMITED | UNKNOWN + permit/HOA/zoning basis |
| §280A personal-use status | personal use ≤ greater(14 days, 10% of fair-rental days)? yes/no/unknown · rented ≥15 days? · residence-limited: yes/no |
| §469 door status (STR) | ≤7-DAY: yes/no/unknown · MATERIAL PARTICIPATION: met/unmet/unverified (logs recommended, not required — §1.469-5T(f)(4)) |
| §469 LTR fallback (only if long-term rental) | §469(c)(2) passive per se · §469(i) active-participation $25k allowance: available/phased-out/$0 (MAGI $100k→$150k phaseout) · §469(c)(7) REP: qualified/not/unverified (one spouse >750 hrs AND >50% personal services; employee hrs only if ≥5% owner; hours not pooled) · activity-level material participation (§1.469-5T; group/elect Reg. §1.469-9): met/unmet/unverified |
| Depreciation (illustrative; match rental mode) | STR transient-use: 39-year shell · conventional residential LTR: generally 27.5-year shell · 100% bonus applies only to qualified short-life components under OBBBA §70301 for property acquired after 2025-01-19 — confirm acquisition date and classification |
| Loss backstops | §465 at-risk · basis · §461(l) EBL · recapture — each: applies/limits |

### C. Residency / domicile (if applicable — person/work, never the deed)
<domicile facts-and-circumstances note; CA-source-wage exposure; route to attorney if a move is intended>

### Evidence
| Claim | Source | URL | verified_on | tier |
|---|---|---|---|---|
| ... | ... | ... | 2026-07-13 | T1/T2/T3 |

**Confidence:** High (primary law) | Medium (market range) | Low (unverified)

> Educational only — not tax, legal, or financial advice. No figure here is a promise or a certainty.
> Confirm every number with a licensed CA/NV CPA or tax attorney for your actual facts and
> placed-in-service year.
```

## Optional JSON companion

```json
{
  "question_type": "STR_INVESTMENT",
  "jurisdiction": ["NV"],
  "nv_ca_escape_correction": "N/A",
  "primary_home": null,
  "str": {
    "feasibility": "FEASIBLE_SUBJECT_TO_PERMIT_HOA",
    "feasibility_basis": "Washoe permit before advertising <28d; HOA/CC&Rs may ban",
    "sec280a_personal_use_ok": "unknown",
    "sec280a_rented_15_days_or_more": "unknown",
    "sec280a_residence_limited": "unknown",
    "avg_stay_le_7_days": "unknown",
    "material_participation": "unverified",
    "material_participation_proof_note": "contemporaneous logs recommended, not legally required (§1.469-5T(f)(4))",
    "ltr_fallback": {
      "applies": false,
      "rental_passive_per_se_469c2": true,
      "active_participation_allowance_469i": "phased_out_high_MAGI ($100k->$150k, $0 for this persona)",
      "rep_469c7_qualified": "unverified",
      "rep_test_note": "one spouse >750 hrs AND >50% personal services in real-property trades/businesses; employee hrs only if >=5% owner; spouses do NOT pool hours for REP",
      "activity_material_participation": "unverified",
      "grouping_election_1469_9": "not_elected"
    },
    "depreciation_shell_illustrative_usd": 215385,
    "recovery_period_years": 39,
    "bonus_note": "100% bonus permanent (OBBBA §70301) for property acquired after 2025-01-19; confirm acquisition date",
    "backstops": {
      "basis": "applies",
      "at_risk_465": "applies",
      "ebl_461l": "applies",
      "recapture": "timing-only benefit (§1245/§1250)"
    }
  },
  "insurance_usd": {"low": 4500, "base": 7500, "high": 25000, "perils": ["wildfire_E&S", "earthquake"]},
  "confidence": "Medium",
  "evidence": [
    {"claim": "39-yr transient-use recovery", "source": "26 USC §168",
     "url": "https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title26-section168&num=0&edition=prelim",
     "verified_on": "2026-07-13", "tier": "T1"},
    {"claim": "personal use > greater(14 days, 10% of fair-rental days) => residence; deductions limited; <15 rental days => income excluded, no deductions",
     "source": "26 USC §280A(d),(g)",
     "url": "https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title26-section280A&num=0&edition=prelim",
     "verified_on": "2026-07-13", "tier": "T1"}
  ],
  "disclaimer_present": true,
  "blocklist_terms_present": false
}
```

## Self-check on the output

- [ ] A/B/C kept separate; the **full** (A) itemized stack and **full** (B) depreciation stack not combined on one property; any mixed personal/rental use flagged as a **separate §280A allocation regime** (§280A(d)/(e)/(g)) routed to a specialist (not stated as "impossible").
- [ ] STR block rendered **feasibility → §280A → §469 → depreciation → backstops** (this order).
- [ ] For a **long-term rental**, §469(c)(2) passive default, §469(i) $25k phaseout, §469(c)(7) REP >750/>50% one-spouse test (hours not pooled; employee hrs only if ≥5% owner), and activity-level material participation (§1.469-5T; Reg. §1.469-9) tracked.
- [ ] §280A personal-use test (greater of 14 days / 10% of fair-rental days) and <15-day rule applied.
- [ ] NV≠CA-escape correction issued if the premise appeared; wages sourced to where work is physically performed.
- [ ] Insurance is a range; Nevada fallback is **E&S**, not FAIR; STR shell is 39-year; bonus verified by **acquisition date** (100% permanent post-2025-01-19, OBBBA §70301).
- [ ] Backstops (§465 / basis / §461(l) / recapture) listed.
- [ ] Evidence table has URL + `verified_on`; stale/failed marked `[UNVERIFIED]`.
- [ ] Disclaimer block present; blocklist terms absent.
