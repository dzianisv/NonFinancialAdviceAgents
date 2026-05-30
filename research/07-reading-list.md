# 07 — Reading List (Distilled)

*The books and papers behind the strategies in this research, each in a sentence
or two. Educational.*

## Books

- **Ray Dalio — *Principles for Navigating Big Debt Crises*.** Debt cycles (credit boom → bubble →
  deleveraging) are predictable in *mechanism* if not timing; crises are deflationary or inflationary.
  Diversify across regimes ("the Holy Grail" ≈ 15 uncorrelated return streams) → the basis of All-Weather.
- **Mark Spitznagel — *Safe Haven: Investing for Financial Storms*.** Geometric (compounding) returns are
  what matter; avoiding the big loss beats capturing the last bit of upside. Distinguishes *good* safe
  havens (raise compound return cost-effectively) from *costly* ones (gold, bonds). Convex tail hedges,
  sized small and monetized into crashes, can be "risk mitigation that pays."
- **Gary Antonacci — *Dual Momentum Investing*.** Combine relative + absolute momentum; **absolute
  (trend) momentum is the protective element** — leave equities when they trail T-bills. Beat buy-and-hold
  historically with roughly half the drawdown.
- **Nassim Taleb — *Antifragile*.** Seek things that *gain* from disorder. The **barbell**: ~90% ultra-safe
  + ~10% highly convex, avoid the fragile middle → capped downside, open-ended upside. Via negativa
  (remove fragility rather than predict).
- **William Bernstein — *The Four Pillars of Investing*.** Theory (risk = return), History (manias rhyme —
  study them), Psychology (your biases are the enemy), Business (costs/incentives). Broad, cheap, rebalanced
  diversification + discipline over forecasting.
- **Meb Faber — *The Ivy Portfolio*** (+ paper *A Quantitative Approach to Tactical Asset Allocation*).
  Diversified multi-asset set + the **10-month / 200-day MA rule** per sleeve (cash when below trend):
  equity-like returns at bond-like drawdowns; sidestepped most of 2008.
- **Harry Browne — *Fail-Safe Investing*.** The Permanent Portfolio: 25% each stocks/long bonds/gold/cash,
  one for each economic season. Simplicity and survivability over optimization.

## Papers / research

- **Hurst, Ooi, Pedersen (AQR) — *A Century of Evidence on Trend-Following Investing* (1880-2016).**
  Time-series momentum was positive in **8 of the 10 largest 60/40 drawdowns** over 137 years; low
  correlation to stocks/bonds every decade. The empirical case for trend as "crisis alpha."
- **Moskowitz, Ooi, Pedersen — *Time Series Momentum* (2012).** A security's own trailing 12m return
  predicts its next-month return across asset classes; the alpha is largely from **volatility scaling**.
- **Faber — *A Quantitative Approach to Tactical Asset Allocation* (SSRN id962461).** The 200-day timing
  model formalized.
- **TauricResearch — *TradingAgents: Multi-Agents LLM Financial Trading Framework* (arXiv 2412.20138).**
  Reference design for an agentic desk: analyst → bull/bear debate → PM → risk → execution, with shared
  structured state.
- **MIT NANDA — *The GenAI Divide: State of AI in Business 2025*.** 95% of enterprise GenAI pilots showed
  no measurable P&L return — a key bear data point for AI-capex ROI (note 01).

## How they connect to this repo
- All-Weather / Permanent / Golden Butterfly → notes 02, 04; backtested in `backtests/crash_protection_backtest.py`.
- Trend / Dual Momentum / GTAA → notes 02, 05; backtested as "Trend-Following S&P (200d)" & "Dual Momentum (GEM)".
- Tail hedging / barbell → note 02 (tail sleeve), note 08 (allocation).
- Agentic desk → note 05; encoded as `skills/` SKILL.md files.
