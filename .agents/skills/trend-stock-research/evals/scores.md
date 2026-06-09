# Scores — trend-stock-research eval loop

| Round | Variant | source_grounding | non_obvious | skeptic | actionability | quorum_routing | prescreen | Mean | Change |
|---|---|---|---|---|---|---|---|---|---|
| 1 | v0-baseline | 3.5 | 5.0 | 4.0 | 4.5 | 4.5 | 2.0 | 3.78 | — |
| 2 | v1-prescreen-mandatory | 4.0 | 4.0 | 5.0 | 5.0 | 4.5 | 5.0 | **4.65** | +0.87 |
| holdout | v1 (case 03 robotics) | 4.0 | 4.0 | 5.0 | 4.0 | 5.0 | — | **4.4** | — |

## Stop condition check
- Train mean ≥ 4.2: ✅ (4.65)
- Holdout mean ≥ 4.0: ✅ (4.4)
- No dimension below 3.0: ✅ (min = 4.0)
- **STATUS: CONVERGED — SHIPPED as v1**
