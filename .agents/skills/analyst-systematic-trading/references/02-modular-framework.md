# The Modular Framework — and the No-Account-Size Invariant

> Source: Carver, *Systematic Trading* (Harriman House, 2015), Part Two ("Toolbox") — the framework overview, the modular pipeline, and the chapter demolishing fixed-% money management. Distilled 2026-06-07.

## Core thesis
A good trading system is **modular**: swappable components like car parts (the trading rules are the *engine*; everything else — sizing, portfolio, execution — is the *chassis*). Each module is **basic arithmetic you can do in a spreadsheet**. The architecture enforces one **iron invariant: trading rules and stop losses depend ONLY on expected market price volatility, NEVER on your account size.** Account size and your pain threshold feed *only* the volatility target; position size is where the two finally meet. You build a self-contained **subsystem per instrument** — sized as if 100% of capital were on it — and then combine subsystems into a portfolio. This separation is what kills the most common amateur error: capital-based "money management" rules.

## Key frameworks / mental models
- **Car analogy:** rules = engine (swappable, where the "edge" lives); the rest = chassis (carries any engine safely).
- **The invariant (most load-bearing rule in the book):** price-volatility → rules & stops; account-size & pain-threshold → volatility target only; the two combine *only* at position sizing.
- **Subsystem-first:** design each instrument as a standalone system at full capital, then scale down by its portfolio weight.
- **Forecast as a universal currency:** a forecast of **+10 always means the same thing** — average-strength long — across every instrument; **±20 is the cap**.
- **The six-stage pipeline** (each stage = arithmetic).

## Specific claims, mechanisms & data
The pipeline:
1. **Instruments** — choose the markets.
2. **Forecasts** — each rule variation → a forecast = expected risk-adjusted return (+ = buy, − = sell), scaled so average |forecast| = 10.
3. **Combined forecast** — forecast weights, rescaled by the **Forecast Diversification Multiplier (FDM)**, then capped (±20).
4. **Volatility target** — capital × % volatility target → cash risk per year (and ÷16 → daily).
5. **Position sizing** — combine forecast + instrument volatility + capital → **subsystem position**.
6. **Portfolio** — instrument weights × **Instrument Diversification Multiplier (IDM)** → round → trade with **position inertia** (no-trade buffer).

The bad example he **demolishes — fixed-% money management** ("never risk more than 3% per trade", capital-based stops): it (a) ignores instrument volatility, (b) confuses per-trade risk with account-relative risk, and (c) ignores how fast the rule trades. It violates the invariant by tying stops to account size.

## How to APPLY (decision rules)
1. **Never let a stop or rule see your account balance.** If a rule's output changes when your capital changes, it's wrong — refactor so only the vol target uses capital.
2. **Build per-instrument subsystems** at notional 100% capital first; combine afterward via instrument weights × IDM.
3. **Standardise everything to the +10 forecast** so a signal is comparable across markets; cap at ±20.
4. **Keep each module to spreadsheet arithmetic** — if a step needs an optimizer or magic, suspect over-fitting.
5. **Reject capital-based "X% per trade" stop rules**; set stops from price volatility instead.
6. **Round only at the very end** (stage 6), then apply position inertia.

## Caveats / where he hedges
- Modularity is a *design* virtue; you still need a real edge in the engine (rules) — a great chassis around a bad engine still loses.
- The arithmetic is simple, but the *parameters* (vol estimate, scalars, weights) carry the over-fitting risk handled in references 03–06.

## Memorable quotes
- "Trading rules and stop losses should be based only on expected market price volatility, and should never take your account size into consideration."
- The rules are the engine; everything else is the chassis.
- A forecast of +10 "always means the same thing" — average-strength long — and is capped at ±20.
