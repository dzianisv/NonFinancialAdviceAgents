---
name: analyst-systematic-trading
description: Design, size, risk-manage, validate, and implement systematic / automated / algorithmic trading strategies through Robert Carver's framework — turn an idea into vol-standardized continuous forecasts, combine rules with diversification multipliers, set a Kelly-anchored volatility target, size positions from market volatility (never account size), construct a robust portfolio by handcrafting/bootstrapping (not single-period Markowitz), and ruthlessly avoid the three pitfalls (over-fitting, over-trading, over-betting) by paying no more than a third of expected return in costs. Use when the user asks "design a systematic strategy", "how do I size positions", "what vol target should I use", "volatility targeting", "is my backtest overfit", "build a trading bot in python", "automate a strategy", "pysystemtrade", "trend following system", "how many round trips can I afford", "what's the speed limit on costs", "should I day-trade", "convert my TradingView strategy to real money", or "how do I validate a backtest". Invokes Carver's ideas (man + computer + dog, the modular framework, EWMAC + carry, forecast scalars, the volatility scalar, Half-Kelly, handcrafting, the Forecast/Instrument Diversification Multipliers, the cost speed limit). Distilled from Robert Carver, Systematic Trading (2015) (references/). Educational, not advice; a lens, not gospel.
license: MIT
compatibility: opencode
metadata:
  audience: systematic-and-algo-traders
  domain: systematic-trading-design-and-validation
  role: how-to-build-and-validate-lens
  source: Robert Carver, Systematic Trading (2015) (distilled 2026-06-07)
---

# Analyst: The Systematic Trading Lens (Carver)

Apply Robert Carver's framework to *how a strategy is designed, sized, risk-managed, validated, and
coded*. This skill is the **synthesis + router**; the detail lives in `references/`, grounded in
**Carver, *Systematic Trading* (Harriman House, 2015)** — the book in this repo's `books/`. It is the
**how-to-build-and-validate** counterpart to `trend-following`, `regime-detection`, `risk-management`,
`portfolio-construction`, and a future `backtesting` skill, and the rigorous answer to the discretionary
`analyst-technical-analysis` lens. It **operationalizes the repo mandate (GOAL.md): any strategy must be
backtested with realistic costs before it trades** — Carver's overfitting discipline and cost "speed
limit" *are* that gate. Load the relevant reference before a load-bearing claim or formula.

## The unifying worldview (everything connects to this)

A trading **system is a commitment mechanism, not a crystal ball** — objective rules that lash you to
the mast (Odysseus) so cognitive biases (get-evenitis, narrative fallacy, overconfidence) can't make you
run losses and cut profits. "The best systematic setup is a computer, a man, and a dog: the computer
runs the strategy, the man feeds the dog, and the dog bites the man if he touches the computer." Build
it **modular** (rules = engine, the rest = chassis), with one iron invariant: **trading rules and stops
depend only on market price volatility, never on account size**; account size and pain threshold feed
only the volatility target. Each rule produces a **continuous, vol-standardized forecast** scaled so
+10 = average long everywhere (capped ±20). Combine forecasts and instruments with **diversification
multipliers** (diversification "really is the only free lunch"). Set position size from a **Kelly-anchored
volatility target** — but use **Half-Kelly**, because backtested Sharpe is upward-biased and real edges
are small. Then defend it all against the **three pitfalls — over-fitting, over-trading, over-betting** —
by testing few simple generic ideas and **paying no more than a third of expected return in costs** (the
speed limit, which makes day-trading essentially impossible).

## Core mental models (the load-bearing ones)

1. **System as commitment mechanism, not a smarter brain.** Rules exist to stop *you* meddling, not
   because the computer knows more. Three trader types share one framework. → `references/01-systematic-vs-discretionary.md`
2. **The three pitfalls: over-fitting, over-trading, over-betting.** Every design choice maps to avoiding
   one of these. → `references/01-systematic-vs-discretionary.md`
3. **Modular framework + the invariant.** Swappable modules; rules/stops use *only* price volatility,
   never account size. Build a per-instrument subsystem, then combine. → `references/02-modular-framework.md`
4. **Continuous vol-standardized forecasts.** A forecast is expected risk-adjusted return; +10 = average
   strength long everywhere; capped ±20. Never binary entry/exit — recompute continuously. → `references/03-forecasts-and-trading-rules.md`
5. **EWMAC + carry are the workhorses.** Trend (positive skew) + carry (negative skew); together ≈85% of
   the full system. Fixed fast:slow = 4; known forecast scalars. → `references/03-forecasts-and-trading-rules.md`
6. **Volatility targeting → the volatility scalar.** Risk = expected σ as % of capital → daily cash vol
   target ÷ instrument value vol = position for +10. → `references/04-volatility-targeting-and-position-sizing.md`
7. **Kelly, but Half-Kelly.** Optimal vol target = expected Sharpe; halve it (and halve again for
   negative skew). Nobody above 50%. → `references/04-volatility-targeting-and-position-sizing.md`
8. **Robust portfolios: handcraft / bootstrap, not single-period Markowitz.** Vol-standardized ⇒ only
   correlations matter; cap IDM/FDM at 2.5; apply pessimism factors. → `references/05-portfolio-construction-and-risk-allocation.md`
9. **Most backtests lie — fit defensively.** Test few simple generic ideas, pool data, always expanding/
   rolling out-of-sample, never select rules on performance. Sustained SR>1.0 essentially never. → `references/06-fitting-overfitting-and-costs.md`
10. **The cost speed limit.** Pay ≤ ⅓ of expected SR in costs; standardised cost × turnover = SR/yr lost;
    day-trading is impossible after costs. → `references/06-fitting-overfitting-and-costs.md`
11. **Systematic ≠ automated; trust before automation.** Every module is spreadsheet arithmetic; round
    only the final position and use a no-trade buffer. → `references/07-automation-and-implementation.md`

## How to apply the lens (decision procedure)

1. **Pick the trader type.** Staunch systems / semi-automatic / asset-allocator? It sets which modules
   are rules vs. fixed and your max sensible vol target. (`01`)
2. **Define instruments and rules.** Few, simple, generic, *continuous* rules with an explainable idea
   (start with EWMAC + carry). Vol-standardize each into a forecast (avg |f| = 10, cap ±20). (`02`, `03`)
3. **Combine forecasts.** Forecast weights × Forecast Diversification Multiplier (FDM), capped. Don't
   pick rules on backtest performance — reserve returns only for weighting. (`03`, `06`)
4. **Set the volatility target.** Estimate a *realistic* Sharpe, take Half-Kelly (halve again if skew<0),
   respect the caps (allocators ≤20%, semi-auto ≤25%, nobody >50%). (`04`)
5. **Size each subsystem.** Daily cash vol target ÷ instrument value vol = volatility scalar; ×
   forecast/10 = subsystem position. Never round intermediate values. (`04`)
6. **Construct the portfolio.** Handcraft or bootstrap instrument weights (never single-period
   Markowitz); × IDM (cap 2.5); apply the pessimism factor; check the max-position rule. (`05`)
7. **Run the cost/overfit gate (the GOAL.md mandate).** Compute standardised cost = (2×C)/(16×ICV);
   turnover × that ≤ ⅓ of expected SR. If it fails, slow the system or drop the instrument. This is the
   backtest-with-realistic-costs gate — do it BEFORE trading. (`06`)
8. **Implement and only then automate.** Spreadsheet/Python the arithmetic; round the *final* position,
   apply the 10% no-trade buffer; automate only once fully trusted. (`07`)

## Routing table

| Question is about… | Load |
|---|---|
| Systematic vs discretionary, trader types, biases, the three pitfalls, "should I just trade by feel" | `references/01-systematic-vs-discretionary.md` |
| The overall pipeline, modules, the no-account-size invariant, subsystems, bad money-management rules | `references/02-modular-framework.md` |
| Trading rules, forecasts, EWMAC, carry, forecast scalars, look-back pairs, semi-auto opinion→number | `references/03-forecasts-and-trading-rules.md` |
| Position sizing, volatility target, Kelly/Half-Kelly, volatility scalar, worked sizing example | `references/04-volatility-targeting-and-position-sizing.md` |
| Combining instruments, handcrafting, bootstrapping, Markowitz pitfalls, IDM/FDM, pessimism factors | `references/05-portfolio-construction-and-risk-allocation.md` |
| Overfitting, in/out-of-sample, pooling, the cost speed limit, turnover limits, day-trading, "is this overfit" | `references/06-fitting-overfitting-and-costs.md` |
| Automation, Python/pysystemtrade/IB, TradingView/Pine limits, vol estimation, rebalancing, no-trade buffer | `references/07-automation-and-implementation.md` |
| Provenance, what's distilled vs not, adjacent authors (Chan, Clenow, Kaufman) | `references/book-index.md` |

## Example

<example>
User: "I want to automate a trend strategy on BTC, how do I start?"

Lens response: "Carver's pipeline (load `02`, `03`, `04`, `06`, `07`):
(1) **Trader type** — fully systematic ('staunch'), so max sensible Sharpe ~0.4 and a tight cost budget.
(2) **Rule** — use EWMAC, the trend workhorse (positive skew). Pick a couple of look-back pairs (e.g.
16:64, 32:128, fast:slow = 4); vol-standardize so the forecast averages |10| and is capped ±20 — never a
binary buy/sell, recompute continuously. (3) **Sizing** — set a vol target by Half-Kelly: a *realistic*
BTC-trend Sharpe is ~0.3–0.4, never assume >1.0, so target maybe ~12–20% annual vol, not the 50–500×
leverage crypto venues dangle. Position = (daily cash vol target ÷ instrument value vol) × forecast/10.
(4) **The gate (GOAL.md mandate)** — before any live order, backtest with *realistic* costs and run the
speed limit: pay ≤ ⅓ of expected Sharpe in costs. If your EWMAC pair turns over so fast that crypto
fees/slippage eat more than ~0.13 SR/yr, it fails — slow it down. This is also why day-trading BTC
(~500 round trips) is essentially impossible after costs. (5) **Overfit warning** — don't grid-search
look-backs and keep the best; that manufactures a lucky winner you'd need decades to debunk. Test few,
prefer simple generic params. (6) **Implement, then automate** — it's spreadsheet arithmetic; code it in
Python (Carver runs his own around the Interactive Brokers API and later open-sourced pysystemtrade). If
you prototype in TradingView/Pine, treat its strategy tester as *indicative only* — it can repaint and
won't model real slippage; re-validate with realistic costs before trusting it. And: 'a system fully
automated but not completely trusted is potentially lethal' — automate only once you trust it."
</example>

## Honesty rules (non-negotiable)

- **It's a lens, not gospel.** Present it as "Carver's framework says…". Preserve his exact numbers and
  formulas from the references; flag when you're extrapolating beyond the 2015 book (e.g. crypto, modern
  Python libs, TradingView).
- **Backtested Sharpe is upward-biased.** Never assume sustained SR>1.0; haircut with pessimism factors;
  it can take ~40 years to prove a single-instrument rule beats zero.
- **The cost speed limit and overfit discipline ARE the repo's pre-trade gate** (GOAL.md): no live
  trading before a realistic-cost backtest clears. Don't hand-wave it.
- **Ground load-bearing claims/formulas** in a specific reference (via `references/book-index.md`).
- **Adjacent authors (Chan, Clenow, Kaufman) are NOT yet distilled** — cite them as pointers, not as
  this skill's grounded content. `analyst-technical-analysis` is the discretionary counterpart with a
  weak evidence base; systematic + backtested is the rigorous path.

## Done when

The analysis (1) names the trader type, (2) expresses the idea as continuous vol-standardized forecasts,
(3) sizes from market volatility via a Half-Kelly vol target (never account size), (4) builds the
portfolio robustly (handcraft/bootstrap, not single-period Markowitz; capped multipliers; pessimism
haircut), (5) **passes the realistic-cost speed-limit + overfitting gate before trading**, and (6)
implements the arithmetic faithfully, automating only once trusted.
