---
name: portfolio-construction
description: Build a diversified, crash-resistant target portfolio for deploying cash (e.g., $1M) when equities look expensive/concentrated — combining a de-concentrated equity core (equal-weight, international, value, min-vol) with uncorrelated diversifiers (gold, trend-following/managed futures, modest Treasuries, TIPS) and a dry-powder reserve. Use this whenever the user asks how to allocate a lump sum or portfolio, wants an all-weather / permanent-portfolio / golden-butterfly / risk-parity style mix, is worried about an AI bubble or market concentration and wants to diversify away from cap-weight S&P/QQQ, asks "what should my portfolio look like", or wants target weights for a multi-asset book. Trigger even when the user just describes the situation ("I have cash to invest but I'm scared of a crash, what mix?"). Always present allocations as an educational framework with risk tiers, not personalized advice, and remind them to consult a fiduciary at meaningful size.
license: MIT
compatibility: opencode
metadata:
  audience: long-horizon-investors
  domain: asset-allocation
  role: portfolio-manager
---

# Portfolio Construction (Bubble-Aware, All-Weather)

Builds a **target allocation** that participates in equity upside but survives a
concentration-bubble unwind, without requiring a market-timing call. The thesis:
at high valuations + extreme concentration, the fix is **de-concentrate the equity core +
add uncorrelated diversifiers + keep dry powder**, not "predict the crash" or "go to cash."

## Mandatory framing
- Educational framework, not personalized advice; consult a fee-only fiduciary at meaningful size.
- Assumes a **long-horizon** investor treating this as growth capital, with emergency fund and
  high-interest debt already handled.
- Defense **underperforms in bull markets** — that lag is the premium paid to cap the left tail.

## The four macro regimes (the design principle)
Never bet everything on one. Hold something that wins in each:
prosperity (stocks, small-cap value), recession/deflation (long Treasuries, cash),
inflation (gold, commodities, TIPS), tight money (T-bills).

## Target allocation — pick a risk tier

| Sleeve | ETF examples | Defensive | **Balanced** | Growth-tilt |
|--------|--------------|:---------:|:------------:|:-----------:|
| US large cap | VOO / RSP (equal-wt) | 12% | 18% | 26% |
| International | VXUS / VEA+VWO | 10% | 12% | 12% |
| US small/mid value | AVUV / VBR | 6% | 8% | 10% |
| Min-vol / quality | USMV / QUAL | 8% | 7% | 6% |
| Gold | GLD / IAU | 12% | 10% | 8% |
| Trend / managed futures | DBMF / KMLM | 12% | 10% | 8% |
| Long/intermediate Treasuries | TLT / IEF | 8% | 7% | 4% |
| TIPS / commodities | SCHP / PDBC | 5% | 3% | 2% |
| Dry powder (T-bills) | SGOV / BIL | 25% | 22% | 22% |
| Tail / anti-beta (optional) | TAIL / BTAL | 2% | 3% | 2% |
| **Equity beta** | | ~36% | ~45% | ~54% |

Choose by the **drawdown the user can actually live through**, not by the return they want.

## Why this shape (the evidence)
- Equity is **de-concentrated** (equal-weight/intl/value/min-vol) instead of ~40% AI mega-caps.
- **Gold + trend** are the diversifiers that worked in 2022 when bonds failed; trend is "crisis alpha."
- **Treasuries kept modest** (not classic All-Weather's 40%) given the 2022 duration lesson and low-yield start.
- **Dry powder** earns ~4-5% and is deployed *into* declines by rule (hand off to `dip-tranches-strategy`).
- Backtest (this repo's `backtests/crash_protection_backtest.py`): diversified mixes earned ~7-8%/yr 2000-2026 with
  −16% to −24% max drawdowns vs the S&P's −55% / QQQ's −83%, and roughly doubled through the 2000-2009 lost decade.

## Sizing mechanics
- Optionally scale the **risky sleeves** by the `exposure_multiplier` from `regime-detection`
  (reduce equity/trend, park the difference in T-bills) — keep gold/TIPS as structural diversifiers.
- Within sleeves, default to the listed weights; for the multi-name equity sleeve use the ETF
  (don't stock-pick) unless a separate factor skill is in play.
- Respect `risk-management` caps (per-asset, per-sleeve, gross) — it can scale you down, never up.

## Outputs (contract)
```json
{
  "as_of": "2026-05-29",
  "tier": "balanced",
  "targets": {"RSP": 0.18, "VXUS": 0.12, "AVUV": 0.08, "USMV": 0.07,
              "GLD": 0.10, "DBMF": 0.10, "TLT": 0.07, "SCHP": 0.03,
              "SGOV": 0.22, "BTAL": 0.03},
  "equity_beta": 0.45,
  "notes": "Dry powder (SGOV) routed to dip-tranches skill for drawdown deployment."
}
```

## Hand-offs
- Cash deployment schedule + dip reserve → **dip-tranches-strategy**.
- Drift/rebalance back to these targets → **rebalancing**.
- Exposure scaling → **regime-detection** (input) and **risk-management** (override).
- Loss harvesting on the taxable sleeves → **tax-loss-harvesting**.
