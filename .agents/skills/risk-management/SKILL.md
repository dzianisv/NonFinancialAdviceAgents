---
name: risk-management
description: The deterministic risk layer for a systematic portfolio — volatility targeting, drawdown-based de-risking, CPPI floors, position/sector/gross-exposure caps, trend-based exits, and conditional-correlation monitoring. This agent has VETO and de-risk authority over the portfolio manager and runs as code OUTSIDE the LLM. Use this whenever the user asks how to size positions to control risk, set a max-drawdown limit or stop-loss, target a portfolio volatility, build a drawdown circuit-breaker, apply the Kelly criterion safely, set position/concentration limits, or wants a risk-manager agent with override power. Trigger when the user describes a risk concern ("how do I make sure I never lose more than 20%?", "how big should each position be?"). Always emphasise the hard caps live in deterministic code, not the model.
license: MIT
compatibility: opencode
metadata:
  audience: systematic-investors
  domain: risk-management
  role: risk-manager
---

# Risk Management (Deterministic Veto Layer)

The agent with **veto power**. It can scale exposure DOWN or BLOCK a trade; it can never be
overridden by the portfolio manager or by an LLM. Implement the hard rules as plain code with a
**kill switch**, so a model hallucination cannot blow up the book.

## Mandatory framing
- Risk controls reduce blowups at the cost of upside; that trade-off is intentional.
- Hard caps (max drawdown, position limits, kill switch) live in **deterministic code outside the LLM**.
- Not personalized advice.

## Layered defenses (apply in order)

1. **Volatility target — first line.** Size each position inversely to its recent realized vol; scale the
   whole book to a target portfolio vol (e.g., 10% annualized). Pre-empts most blowups; improves Sharpe
   more than almost any signal tweak.
   `weight_i ∝ target_vol / realized_vol_i`, then renormalize and cap.

2. **Drawdown-based de-risking.** Scale gross exposure down as drawdown deepens — e.g., linearly from
   full exposure at −5% drawdown to **zero risky exposure at −20%**. Mechanical and emotionless.
   ```
   if dd > -5%:   risk_scale = 1.0
   elif dd > -20%: risk_scale = (dd - (-20%)) / ((-5%) - (-20%))   # 1.0 -> 0.0
   else:           risk_scale = 0.0
   ```

3. **CPPI floor (hard drawdown cap).** Define a floor (e.g., 85% of capital). Invest
   `multiplier × (NAV − floor)` in risky assets, rest in T-bills; as NAV approaches the floor, risky
   exposure → 0. A time-varying multiplier tied to estimated vol improves it. Risk-parity-then-CPPI is
   a strong tail-control stack.

4. **Trend exits over fixed stops** for trend strategies (fixed % stops get whipsawed; exit on close
   below SMA/channel). Use hard catastrophic stops only as a backstop.

5. **Position & concentration limits.** Caps per name, per sector, per asset class; gross and net
   exposure caps. Default examples: ≤25% per asset-class sleeve, ≤10% per single ETF, gross ≤100%
   (no leverage) unless explicitly approved.

6. **Conditional-correlation monitoring.** Track the rolling correlation matrix and the *effective
   number of bets*. Correlations spike toward 1 in crises — monitor **stressed** correlation, alert and
   de-risk when diversification collapses.

## Position sizing — Kelly, safely
- Full Kelly produces 50-80% drawdowns and assumes you know true probabilities. **Use ¼–½ Kelly as a
  CAP** on the vol-targeted size, never as the primary sizer.
- Need **50-100+ trades** before win-rate/payoff estimates are stable enough to trust.

## The risk report (contract every cycle)
Always **net of costs**, in-sample and out-of-sample:
`CAGR, Sharpe, Sortino, Calmar, max drawdown, current drawdown, realized vol vs target, gross/net
exposure, largest position, effective # of bets, time-in-drawdown, turnover.`

```json
{
  "verdict": "approve | scale | block",
  "risk_scale": 0.6,
  "current_drawdown": -0.08,
  "portfolio_vol": 0.11,
  "breaches": ["GLD weight 12% < cap 25% OK", "gross 0.78 OK"],
  "kill_switch": false
}
```

## Decision flow
1. Receive target weights from **portfolio-construction** (already scaled by `regime-detection`).
2. Apply vol target → drawdown de-risk → CPPI → caps. Compute final `risk_scale` and adjusted weights.
3. If any **hard cap** or kill-switch fires → `block` and route to T-bills + human alert.
4. Emit the risk report; hand approved weights to **rebalancing** / execution.

## Pitfalls
Overfitting risk limits to one history; assuming long-run correlations hold in crises; trusting
LLM-estimated probabilities. **Test across 2008, 2020, 2022.** Keep the deterministic layer simple
enough to audit.
