# Forecasts & Trading Rules — EWMAC, Carry, and Scalars

> Source: Carver, *Systematic Trading* (Harriman House, 2015), ch. on trading rules & forecasts (the EWMAC trend rule, the carry rule, forecast scaling/capping, vol standardisation), plus the semi-automatic "opinion → number" guidance. Distilled 2026-06-07.

## Core thesis
A **trading rule** turns price (and other) data into a **forecast** — a number proportional to the *expected risk-adjusted return* (expected Sharpe) of holding the instrument now. A good rule is: explainable (a real economic idea), **generic** (works across many instruments, not tuned to one), **simple**, **objective**, and crucially **continuous** — not a binary buy/sell but a graded conviction. Forecasts are **volatility-standardised** so they are comparable across instruments and so the *size* of the forecast is meaningful: avg |forecast| = **10**, capped at **±20**. The two workhorse rules are **EWMAC** (trend, positive skew) and **carry** (positive carry, negative skew); together they capture roughly **85%** of a fuller system's performance.

## Key frameworks / mental models
- **Forecast ∝ expected Sharpe.** A bigger forecast means a bigger expected risk-adjusted return, so position scales linearly with it.
- **Continuous, not binary.** Don't build separate entry/exit rules — **recompute the forecast continuously**; the position naturally grows/shrinks/flips.
- **Vol standardisation:** divide the raw signal by recent return σ so the rule means the same thing in a calm vs. wild market.
- **EWMAC** (exponentially-weighted moving-average crossover) = trend follower, **positive skew**.
- **Carry** = earn the roll/yield differential, **negative skew**.
- **Diversify across rule variations** (different speeds), then combine with forecast weights × FDM.

## Specific claims, mechanisms & data (PRESERVE EXACTLY)
- **Scaling:** create forecasts with an **expected absolute value of 10**, **capped at ±20** (≈ only **5%** of a Gaussian exceeds 20).
- **Vol standardisation:** `raw_signal ÷ recent return σ`.
- **Forecast scalar** = `10 ÷ (natural average |forecast|)` (a single constant per rule, estimated once, generically).
- **EWMA:** `A = 2/(L+1)`; `E_t = A·P_t + (1−A)·E_{t−1}` (matches pandas EWMA `span`).
- **Fixed fast:slow ratio = 4.**
- **Look-back pairs:** 2:8, 4:16, 8:32, 16:64, 32:128, 64:256 — **adjacent pairs ≈ 0.90 correlated**.
- **EWMAC forecast scalars:** 2,8 → **10.6**; 4,16 → **7.5**; 8,32 → **5.3**; 16,64 → **3.75**; 32,128 → **2.65**; 64,256 → **1.87**.
- **Carry forecast scalar** (example) = **30**.
- **EWMAC + carry alone ≈ 85%** of the fuller system's performance.
- **Semi-automatic opinion → number table:** map your conviction onto the forecast scale, **−20 = very strong sell … 0 = neutral … +20 = very strong buy** (then feed it into the same sizing framework as a systematic forecast).

## How to APPLY (decision rules)
1. **Express the idea as a continuous forecast**, vol-standardised, with avg |f| = 10 and cap ±20. Never binary.
2. **Start with EWMAC + carry** — they're generic, explainable, and capture ~85% of the value.
3. **Pick a few look-back pairs** (fast:slow = 4); remember adjacent pairs are ~0.90 correlated, so 2–3 distinct speeds add most of the diversification.
4. **Apply the published forecast scalars** above rather than re-fitting them per instrument (re-fitting invites over-fitting).
5. **Combine variations** with forecast weights, multiply by the FDM, then **cap the combined forecast at ±20**.
6. **Semi-auto:** translate your view into a −20…+20 number and run it through the identical sizing pipeline.

## Caveats / where he hedges
- **Very large forecasts are unreliable** — that's *why* they're capped at ±20.
- **Don't fit scalars or look-backs to a single instrument** — use generic, pooled values.
- **Separate entry/exit rules don't fit this framework** — the continuous forecast already handles getting in, scaling, and out.
- The forecast is *expected* risk-adjusted return; it's a tilt, not a guarantee.

## Memorable quotes
- "Create forecasts which have an expected absolute value of 10… capped at a maximum absolute value… I recommend a limit of 20."
- EWMAC + carry alone deliver roughly **85%** of the full system — simplicity is most of the prize.
- A forecast is the expected risk-adjusted return; "+10 means an average-strength long."
