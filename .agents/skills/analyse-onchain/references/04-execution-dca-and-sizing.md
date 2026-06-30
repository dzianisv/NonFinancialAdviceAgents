# Execution — Valuation-Tilted DCA + Vol-Target Sizing (the discipline)
> Source: DCA-vs-lump-sum evidence (Vanguard-style studies adapted to crypto); vol-target sizing from `analyse-systematic-trading` (Carver, *Systematic Trading* 2015); 200d-MA trend-cap from trend-following practice. Distilled 2026-06.

## Core thesis
Reading the market is half the job; **how you deploy capital is the other half, and it's where most edge is won or lost.** The honest, defensible execution policy is **valuation-and-sentiment-tilted dollar-cost-averaging across tranches, governed by the liquidity cycle, sized by volatility** — *not* lump-sum-on-conviction and *not* TA day-timing. Lump-sum only wins when you nail the bottom, which nobody does repeatably; DCA wins on a **risk-adjusted** basis and removes the single biggest behavioral failure (deploying everything at the local top).

## Key frameworks / mental models
- **DCA beats lump-sum risk-adjusted.** Spreading entries lowers variance of outcomes and the regret/timing risk that drives capitulation. Lump-sum has higher *expected* return only under perfect timing (and in steadily rising markets) — neither holds for crypto's drawdowns.
- **Valuation-band-tilted DCA.** Keep a base schedule, then **scale tranche size by the on-chain zone and sentiment**: buy *more* when MVRV-Z is low / F&G in extreme fear, *less* when MVRV-Z is high / F&G in extreme greed. This is the link from `02`+`03` into capital.
- **Liquidity governor over the pace.** When the GLI is rolling over (Speculation→Turbulence, `01`), **throttle** to measured/defensive tranches and hold dry powder; when it's rising (Rebound/Calm), release the pace. The governor caps the *rate*, the valuation band sets the *tilt*.
- **Vol-target sizing.** Size positions from **market volatility, never account size** — borrow `analyse-systematic-trading` directly: daily cash vol target ÷ instrument value vol = the volatility scalar; use a **Half-Kelly** vol target (crypto's fat tails / negative-skew episodes argue halving again). This converts a tilt into a concrete tranche size.
- **Optional 200d-MA trend risk-cap.** Cap or reduce exposure when price is below its 200-day MA. This is **drawdown control, not alpha** — it trims the worst bear legs at the cost of some upside; use it for capital preservation, not as a timing signal.

## Specific claims, mechanisms & data
- **Lump-sum-only-wins-with-perfect-timing**: the expected-return edge of lump-sum evaporates once you account for the realistic distribution of entry points and the behavioral reality that conviction lumps cluster near euphoria (the worst entries).
- **Tilted-DCA > flat-DCA > lump (risk-adjusted)** is the ordering this skill defends; the sentiment-tilt Sharpe uplift (`03`, ~1.38 vs ~0.88) is *directionally* consistent but the magnitude is unverified.
- **Vol-target math** is identical to the systematic-trading engine — do not reinvent it; route there for the scalar, IDM/FDM, and the Half-Kelly cap (allocators ≤20%, nobody >50%).

## How to APPLY (decision rules for the discipline)
1. **Set a base DCA schedule** (e.g. fixed cadence over N tranches) — the spine that removes timing-paralysis.
2. **Apply the valuation+sentiment tilt** from `02`+`03`: multiply each tranche by a tilt factor (larger in cheap/extreme-fear zones, smaller in rich/extreme-greed).
3. **Apply the liquidity governor** from `01`: cap the *pace* when the tide is ebbing; release it when rising. Hold explicit dry powder for the throttled case.
4. **Size each tranche by vol target** via `analyse-systematic-trading` (Half-Kelly; size from σ, never from account size).
5. **Optionally gate with the 200d MA** for drawdown control — and label it as risk-management, not alpha.
6. **Resolve pillar tension toward tilted-DCA, not lump.** On-chain-cheap + liquidity-rolling-over = deploy a measured tilted base now, keep powder, let the governor cap pace. (This is the `<example>` in SKILL.md.)

## Caveats / where it hedges
- **DCA gives up upside in straight-up markets** — its win is risk-adjusted and behavioral, not maximal raw return.
- **Tilting adds parameters** (band thresholds, tilt multipliers) → overfitting risk; keep the tilt simple and pre-committed, not curve-fit.
- **The 200d cap whipsaws** in choppy ranges (buy-high/sell-low churn) and costs upside — it's insurance with a premium.
- **All of this is sizing/scheduling, not prediction** — it does not claim to know the bottom; it claims to deploy *well* without knowing it.

## Memorable quotes
- "Lump-sum only wins if you time the bottom — and you won't, repeatably."
- "Tilt the DCA by valuation and fear; govern its pace by liquidity; size it by volatility — never by account size."
- "The 200-day cap is insurance, not alpha."
- "When the pillars conflict, the answer is a bigger tilt on a steady schedule — not a bigger bet."
