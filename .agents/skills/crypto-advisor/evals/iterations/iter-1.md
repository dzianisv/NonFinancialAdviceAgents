# Round 1 — Iteration Log

Date: 2026-06-26
SKILL.md version: v0

---

## Raw Judge Outputs

### case-01-btc-deep-value
Dims tested: signal_correctness, zone_discipline, data_sufficiency, no_fabrication

JUDGE SCORES — case-01-btc-deep-value
signal_correctness: 5 — PASS
zone_discipline: 5 — PASS
data_sufficiency: 5 — PASS
no_fabrication: 5 — PASS
MEAN: 5.0
FIX TARGETS: none

Actor summary: correctly counted seats_bull=2, seats_bear=1 → SPLIT; weekly_closes=312≥200 gate passes; zone=DEEP_VALUE; BUY(small). Full stepwise reasoning shown.

---

### case-02-hype-elevated
Dims tested: signal_correctness, zone_discipline, data_sufficiency, no_fabrication

JUDGE SCORES — case-02-hype-elevated
signal_correctness: 5 — PASS
zone_discipline: 5 — PASS
data_sufficiency: 5 — PASS
no_fabrication: 5 — PASS
MEAN: 5.0
FIX TARGETS: none

Actor summary: correctly counted seats_bull=3, seats_bear=0 → BULLISH; gate triggered (87<200) → UNKNOWN zone → HOLD. Cited verbatim rule from SKILL.md. Excellent.

---

### case-03-governor-extreme-fear
Dims tested: signal_correctness, portfolio_governor

JUDGE SCORES — case-03-governor-extreme-fear
signal_correctness: 5 — PASS (correctly flagged BTC pre-governor signal as UNCERTAIN per truth table)
portfolio_governor: 4 — Downgrade priority order not explicitly confirmed even though no downgrades fired; governor format not printed (correctly, since no downgrades) but ranking step skipped
MEAN: 4.5
FIX TARGETS:
- Governor section: require always ranking BUY signals by conviction before checking cap, even when total ≤ cap

Actor summary: correctly identified 4 BUY(small) signals, F&G=13→Extreme Fear→cap=4, 4≤4 so no downgrades. Correctly noted no governor output needed. Bonus: correctly flagged BTC pre-governor signal as UNCERTAIN (seats_bull=1, seats_bear=2) which should have been HOLD — genuine catch.

---

### case-04-listing-page-citation
Dims tested: source_discipline, no_fabrication

JUDGE SCORES — case-04-listing-page-citation
source_discipline: 5 — PASS
no_fabrication: 5 — PASS
MEAN: 5.0
FIX TARGETS: none

Actor summary: correctly excluded listing page from ranked citations, correctly placed it as [NOT CITED — discovery only], cited article URL as T2 with verbatim quote, DeFiLlama as T1 with verbatim data. Two-step rule applied perfectly.

---

## Per-Dimension Averages (Round 1)

| Dimension | Cases Tested | Scores | Avg |
|-----------|-------------|--------|-----|
| signal_correctness | 01, 02, 03 | 5, 5, 5 | 5.0 |
| zone_discipline | 01, 02 | 5, 5 | 5.0 |
| data_sufficiency | 01, 02 | 5, 5 | 5.0 |
| source_discipline | 04 | 5 | 5.0 |
| critic_coverage | — | not tested | N/A |
| portfolio_governor | 03 | 4 | 4.0 |
| no_fabrication | 01, 02, 04 | 5, 5, 5 | 5.0 |

**Train mean (Round 1): 4.83** (6 tested dims, critic_coverage excluded)
**Lowest dimension: portfolio_governor (4.0)**

---

## Diagnosis

**Structural gap:** The governor section in SKILL.md only instructs the actor what to do *when downgrades are needed* (total > cap). It does not require the actor to always rank the BUY signals by conviction before checking the cap. When no downgrades fire, a model following the instructions exactly will skip the ranking step — because the instruction is conditional ("if total BUYs exceed the cap..."). 

**General-principle fix (not case-specific):** Require the actor to always build and print the conviction-ranked BUY list as a mandatory intermediate step, before applying the cap check. This makes the step explicit regardless of whether downgrades are triggered, and makes the downgrade logic auditable.

---

## Synthesized Insight

The skill is very strong on signal mechanics (truth table, zone gate, data sufficiency). The only structural gap is in the Governor block — the instruction structure is conditional-only, leaving the ranking step implicit when the cap is not exceeded. A one-sentence addition requiring "always print the ranked BUY list before the cap check" would close this.
