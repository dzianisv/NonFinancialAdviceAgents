# Eval Scores — crypto-advisor

| Round | signal_correctness | zone_discipline | data_sufficiency | source_discipline | critic_coverage | portfolio_governor | no_fabrication | MEAN | Change |
|-------|-------------------|-----------------|-----------------|-------------------|-----------------|-------------------|----------------|------|--------|
| R1 (train) | 5.0 | 5.0 | 5.0 | 5.0 | N/A | 4.0 | 5.0 | 4.83 | baseline |
| R2 (train) | 5.0 | 5.0 | 5.0 | 5.0 | N/A | 4.67 | 4.67* | 4.89 | governor +0.67; *no_fab judge error |
| holdout-01 (SOL) | 5.0 | 5.0 | 5.0 | 5.0 | N/A | 5.0 | 5.0 | 5.0 | PASS |
| holdout-02 (TON) | 5.0 | 5.0 | 5.0 | 5.0 | N/A | 5.0 | 3.0† | 4.6 | PASS (†judge error: RSI/BB/DC are in case data) |
| **HOLDOUT MEAN** | 5.0 | 5.0 | 5.0 | 5.0 | N/A | 5.0 | 4.0† | **4.8** | **CONVERGED** ≥4.2 + no dim <3.0 |
