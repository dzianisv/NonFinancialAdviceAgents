# Volatility Targeting & Position Sizing — the Volatility Scalar and Half-Kelly

> Source: Carver, *Systematic Trading* (Harriman House, 2015), ch. on volatility targeting and position sizing (the volatility scalar, Kelly/Half-Kelly, the worked WTI sizing example). Distilled 2026-06-07.

## Core thesis
You don't choose how many shares/contracts to buy — you choose **how much risk** to run, expressed as a **volatility target**: the expected annual σ of the *whole account* as a percentage of trading capital. Convert that to cash, then size every position so that an **average forecast (+10) delivers exactly that risk**, scaling **linearly** with the forecast. The bridge is the **volatility scalar** = daily cash vol target ÷ instrument value volatility — the number of blocks to hold at +10. How big should the vol target be? **Kelly** says the optimal % vol target equals your **expected Sharpe** (SR 0.5 → 50%). But because backtested Sharpe is upward-biased and edges are fragile, **use Half-Kelly — and halve again for negative skew.** Nobody should run above 50%.

## Key frameworks / mental models
- **Risk-first sizing.** Pick a vol target; positions fall out of it. Account size enters *only here* (the invariant from ref 02).
- **Linear in the forecast.** +10 → target risk; +20 → double; −6 → 0.6× short.
- **The volatility scalar** = position for a +10 forecast (don't round it).
- **Kelly anchor, Half-Kelly mandate.** Optimal vol target ≈ expected Sharpe; halve for safety, halve again if skew < 0.
- **Avoid ultra-low-vol instruments** that need insane leverage to hit the target (tail-risk trap).

## Specific claims, mechanisms & data (PRESERVE EXACTLY)
- **Daily cash vol target** = annual cash vol target **÷ 16**.
- **Block value** = cash per **1% price move** of one block (contract/lot).
- **Price volatility** = expected daily σ of % returns; default estimate **25-day simple MA** OR **36-day EWMA** (= RiskMetrics half-life).
- **Instrument currency volatility (ICV)** = block value × price volatility.
- **Instrument value volatility** = ICV × FX rate.
- **Volatility scalar** = daily cash vol target ÷ instrument value volatility (= position at +10; **don't round**).
- **Subsystem position** = volatility scalar × forecast ÷ 10.
- **Kelly:** optimal % vol target = expected Sharpe (SR 0.5 → 50%). **Mandate: Half-Kelly, then half again for negative skew.**
- **Recommended % vol targets (skew > 0):** SR 0.25 → **12%**; 0.40 → **20%**; 0.50 → **25%**; 0.75 → **37%**; ≥1.0 → **50%**. **Negative skew: halve these.**
- **Caps by trader type:** asset allocators ≤ **20%**; semi-auto ≤ **25%**; **NOBODY > 50%**.
- **Carver's own ~45-instrument futures system:** 35-yr bootstrapped SR ~1.0 × 0.75 realism → 0.75 → Half-Kelly → 37% max; **he runs 25%.**
- **Loss intuition ($100k, SR 0.5, zero skew):** 50% target → ~10% chance of losing half over 10 yr; **200% target → 93% chance.**
- **Worked example:** £1M, annual vol target → **£62,500 daily**; WTI at $75, 1000 bbl/contract → **block value $750**; price vol 1.33% → **ICV $997.50**; × FX 0.67 → **£668.33** value vol; **volatility scalar = 62,500 ÷ 668.33 = 93.52 contracts**; forecast −6 → **short 56.11 contracts** (93.52 × −6/10).

## How to APPLY (decision rules)
1. **Estimate a realistic Sharpe** (haircut the backtest — never assume >1.0) and read off the recommended vol target; **halve again if skew < 0**.
2. **Respect the caps:** allocator ≤20%, semi-auto ≤25%, never >50%.
3. **Compute the volatility scalar** = daily cash vol target ÷ instrument value vol; **never round it**.
4. **Subsystem position** = volatility scalar × forecast/10 — linear in conviction.
5. **Use the 25-day MA / 36-day EWMA** for price vol (slower for expensive instruments — see ref 07).
6. **Reject instruments needing absurd leverage** to reach the target (low-vol tail-risk trap).

## Caveats / where he hedges
- **Full Kelly is too aggressive** — drawdowns are brutal and the optimum is estimated with error; Half-Kelly sacrifices little growth for much smaller drawdowns.
- **Backtested Sharpe is upward-biased**; the 0.75 realism haircut on his own system is deliberate.
- **Low-vol instruments are a trap:** EUR/CHF's Jan-2015 ~16% move means realistic max leverage ~7× → only ~7% achievable vol target — a single de-peg can blow up a "low-risk" book.

## Memorable quotes
- "Set your volatility target at the same level as your expected SR… [but] it is far better to use Half-Kelly."
- A 200% vol target gives a **93%** chance of losing half your money over a decade — over-betting is ruin.
- The volatility scalar is "the position you'd hold for an average forecast of 10."
