---
name: rebalancing
description: Decide when and how to rebalance a multi-asset portfolio back to target weights — calendar vs threshold (band) rebalancing, no-trade zones, transaction-cost and turnover awareness, tax-aware rebalancing with new cashflows, and drift monitoring. Use this whenever the user asks how often to rebalance, whether to rebalance on a schedule or on drift, how to keep turnover/taxes/costs low while staying near targets, how to compute trade deltas from current holdings to target weights, or wants a rebalancing agent for a systematic book. Trigger when the user describes drift ("my stocks grew to 60% of my portfolio, should I trim?"). Educational, not personalized advice.
license: MIT
compatibility: opencode
metadata:
  audience: systematic-investors
  domain: portfolio-management
  role: portfolio-manager
---

# Rebalancing

Brings the book back toward the **portfolio-construction** targets at minimum cost. Good rebalancing
is mostly about **not** trading: the cheapest, most tax-efficient trade is the one a no-trade band lets
you skip.

## Mandatory framing
- Educational, not personalized advice (taxes especially are situation-specific — see a CPA).
- Rebalancing is a **risk-control** tool (it trims winners, controls drift), not a return-maximizer.

## The default rule: calendar check, threshold act
- **Check on a calendar** (monthly or quarterly) — predictable and auditable.
- **Act only on a threshold breach** — a sleeve has drifted beyond tolerance:
  - **±20% relative** (e.g., a 10% target sleeve breaches at <8% or >12%), or
  - **±5% absolute**, whichever you standardize on.
- This combines low turnover with bounded risk and beats naive "rebalance every month regardless."

## No-trade zone (cost awareness)
Around each target weight, define a band where you **do not trade**. Only trade the portion that
exceeds the band, and only if expected benefit > expected cost:
```
cost ≈ commission + half-spread + market impact
skip the trade if |drift| within band OR expected_alpha_of_trade < cost
```
Report everything **net of costs**. High turnover silently eats returns.

## Tax-aware rebalancing (taxable accounts)
1. **Rebalance with new cashflows first** — direct dividends/contributions to underweight sleeves before
   selling anything.
2. **Prefer trimming in tax-advantaged accounts** (IRA/401k) where no gain is realized.
3. **Harvest losses** on the way (hand off to `tax-loss-harvesting`); avoid realizing short-term gains.
4. Favor **long-term holding periods**; let high-basis lots go first if you must sell.

## Computing trade deltas
```
target_value_i = NAV * target_weight_i * risk_scale      # risk_scale from risk-management
current_value_i = shares_i * price_i
delta_i = target_value_i - current_value_i
trade only the part of delta_i outside the no-trade band; round to lot/fractional; net buys vs sells
```

## Outputs (contract)
```json
{
  "as_of": "2026-05-29",
  "method": "quarterly-check / 20%-relative-band",
  "trades": [{"ticker": "GLD", "action": "sell", "usd": 8200, "reason": "drifted to 12.4% vs 10% target"},
             {"ticker": "VXUS", "action": "buy", "usd": 7600, "reason": "drifted to 10.3% vs 12% target"}],
  "turnover_pct": 1.6,
  "skipped_within_band": ["RSP", "AVUV", "USMV"]
}
```

## Hand-offs
- Targets in from **portfolio-construction**; `risk_scale` from **risk-management**.
- Tax-loss opportunities out to **tax-loss-harvesting**.
- Dip-reserve deployment is handled separately by **dip-tranches-strategy** (don't double-count that cash).
- Approved trades → execution agent (notification-first; see `data-sources`).
