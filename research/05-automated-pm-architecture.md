# 05 — Building the Agentic Systematic Fund

*Engineering + quant building blocks for a small, automated, agent-driven fund.
Each section maps onto an opencode SKILL.md (see `skills/`). Sources at the end.*

## Agentic architecture (the team)

Mirror a real trading desk. The canonical reference design is TauricResearch's
**TradingAgents** (arXiv 2412.20138).

| Agent | Owns | Outputs |
|-------|------|---------|
| **Regime Analyst** | risk-on/off detection; sets gross exposure | regime score, exposure multiplier |
| **Research/Signal analysts** (technical, macro, fundamental) | candidate signals & ranks | structured signal reports |
| **Bull vs Bear debate** | adversarial check before sizing | argued risk cases |
| **Portfolio Manager** | target weights, vol target, sizing, rebalance | target portfolio |
| **Risk Manager** | **veto + de-risk authority**; drawdown/exposure caps | approve / scale / block |
| **Execution** | turn weights into orders, no-trade bands, cost checks | orders to Alpaca/IBKR |

**Engineering pattern that works:** structured (JSON) outputs for facts/state; natural-language
debate only where reasoning adds value; a **shared global state object** agents query instead of
re-asking through long dialogue (cuts tokens and drift). ReAct-style prompting per agent.

**Guardrails (non-negotiable):**
- **Deterministic risk layer in code, outside the LLM** — vol target + drawdown de-risking + hard
  caps + kill switch. Agents cannot override it.
- **Human-in-the-loop** approval for any new live strategy, trades above a notional threshold, leverage.
- **Paper-trade everything** for weeks; require live-paper Sharpe/DD to match backtest within tolerance.
- **Full audit log** — every signal, decision, prompt, and order timestamped and append-only.

## 1. Regime detection (sets gross exposure)

Treat as a **weighted ensemble**, never a single trigger. Require **persistence** (signal holds N days)
before acting.

| Signal | Robustness | Use |
|--------|-----------|-----|
| **Price vs 200-day MA** | core, very robust | trend filter; add ±1-2% band to cut whipsaw |
| **VIX term structure** (VIX/VIX3M) | robust stress detector | de-risk when in backwardation; poor for bottom-ticking |
| **Credit spreads** (HYG/LQD, FRED HY OAS) | robust, *leads* equities | risk-off confirmation |
| Yield-curve inversion (10y-2y, 10y-3m) | slow (6-18 mo lead) | strategic tilt only |
| Breadth (% > 200dma) | confirmatory | weak standalone; good divergence flag |
| 50/200 crossover (golden/death) | laggy | one ensemble vote |
| Hindenburg Omen | noisy (~20-25% hit) | only when *clustered*; raises vigilance, never a direct sell |

Score each −1/0/+1, weight the robust core higher, map the aggregate to a target gross-exposure
multiplier (e.g., 0.3×–1.0×).

## 2. Signal construction

- **Time-series momentum (TSMOM):** own-trailing-12m return predicts next month across asset classes
  (Moskowitz-Ooi-Pedersen 2012). The documented alpha is **largely from volatility scaling** — TSMOM is
  really "vol-targeted trend." The workhorse signal.
- **Cross-sectional momentum:** rank assets by relative trailing return; long top / underweight bottom.
- **Mean-reversion:** short-horizon z-score/Bollinger; fragile in trends — gate behind the regime detector.
- **Volatility targeting:** size positions inversely to recent realized vol; scale the book to a target
  vol (e.g., 10%). Improves Sharpe and tames drawdowns more than almost any signal tweak.
- **Risk-parity weighting:** equal *risk* contribution. "Naive risk parity" (weight ∝ 1/vol) captures
  most of the benefit without a full covariance optimizer.
- **Kelly / fractional Kelly:** full Kelly → 50-80% drawdowns and assumes you know true probabilities.
  Use **¼-½ Kelly as a cap** on vol-targeted sizing, not the primary sizer. Need 50-100+ trades before
  win-rate estimates are stable.

## 3. Rebalancing

- **Calendar** (monthly/quarterly): simple, auditable — default for a strategic book.
- **Threshold/band** (rebalance when a weight drifts > tolerance, e.g. ±20% relative): lower turnover,
  better risk control. **Best practice: "check on calendar, act only on threshold breach."**
- **Transaction-cost awareness:** model commission + spread + impact; suppress trades whose expected
  alpha < cost (no-trade zone). **Turnover control:** cap or penalize; always report net-of-cost.
- **Tax-aware:** harvest losses (see the tax-loss-harvesting skill), prefer long-term holds, rebalance
  with new cashflows before selling.

## 4. Risk management (the agent with veto power)

Layered defenses:
1. **Vol target** — first line; pre-empts most blowups.
2. **Drawdown-based de-risking** — scale gross exposure down as drawdown deepens (e.g., linearly from
   −5% DD to zero at −20%). Mechanical, emotionless.
3. **CPPI** — hold a floor; invest multiplier × (NAV − floor) in risky assets; exposure → 0 as NAV nears
   floor. A hard drawdown cap. Risk-parity-then-CPPI is strong for tail control.
4. **Trend exits over fixed stops** for trend strategies (fixed % stops get whipsawed).
5. **Position/concentration limits** — per name, sector, asset class; gross & net caps.
6. **Conditional correlation monitoring** — correlations spike toward 1 in crises; alert when
   diversification collapses.

## 5. Metrics (the reporting contract every agent emits)

Always **net of costs**, in-sample *and* out-of-sample: **CAGR, Sharpe, Sortino, Calmar, max drawdown**,
win rate + payoff ratio (feeds Kelly), **turnover**, plus rolling Sharpe/vol, time-in-drawdown,
exposure-over-time, per-sleeve attribution.

## 6. Pitfalls to design against
**Overfitting** (limit params, walk-forward, deflate Sharpe for # of trials), **look-ahead bias**
(point-in-time data, lag fundamentals, decide on prior close), **survivorship bias** (yfinance lacks
delisted names), **transaction costs** (#1 killer of paper-profitable strategies), **regime change**
(test across 2008/2020/2022), **LLM overconfidence** (bound with the deterministic risk layer).

## Recommended starter stack
yfinance + FRED for research → **vectorbt** (fast signal research) + **`bt`** (portfolio/rebalance logic)
→ **Alpaca paper trading** for forward-testing → human-approved go-live with hard caps in code.

## Sources
- TradingAgents: tauricresearch.github.io/TradingAgents, github.com/TauricResearch/TradingAgents, arXiv 2412.20138
- TSMOM: aqr.com (Time Series Momentum), SSRN 2089463
- VIX term structure: macrosynergy.com, cboe.com, quantpedia.com
- Kelly/CPPI: en.wikipedia.org/wiki/Kelly_criterion, quantpedia.com (CPPI), quantifiedstrategies.com
- Hindenburg: en.wikipedia.org/wiki/Hindenburg_Omen, realinvestmentadvice.com
- Frameworks/APIs: autotradelab.com (backtester comparison), alpaca.markets, nb-data.com (data APIs 2026)
