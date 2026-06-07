# Portfolio Construction & Risk Allocation — Handcrafting, Bootstrapping, and the Multipliers

> Source: Carver, *Systematic Trading* (Harriman House, 2015), ch. on portfolio construction & risk allocation (handcrafting, bootstrapping, IDM/FDM, pessimism factors, the max-position rule). Distilled 2026-06-07.

## Core thesis
**"Diversification really is the only free lunch in investment"** — combining imperfectly-correlated subsystems can roughly **double the Sharpe ratio**. But the textbook tool, **single-period Markowitz optimisation, is dangerous**: it produces extreme, unstable, over-fitted weights because it treats statistically *indistinguishable* Sharpe estimates as gospel. Carver's robust alternatives are **handcrafting** (a fast, manual grouping-by-correlation method calibrated from bootstrap) and **bootstrapping** ("the average of many optimisations, not one optimisation on the average"). Because every subsystem is already volatility-standardised to equal expected σ, you **need only the correlations** (optionally Sharpes) — never the volatilities — and **weights can't go negative**. Diversification gains are then scaled up by the **Instrument/Forecast Diversification Multipliers (IDM/FDM)**, both **capped at 2.5** because correlations rush toward 1 in a crisis.

## Key frameworks / mental models
- **Diversification = the only free lunch** — can ~double Sharpe.
- **Markowitz single-period = over-fitting machine** — extreme/unstable weights from noise.
- **Handcrafting:** group highly-correlated assets (1–3 per group), apply a small bootstrapped weight table, allocate across groups; **final weight = product** of group weight × within-group weight.
- **Bootstrapping:** resample histories, optimise each, **average the weights**.
- **Vol-standardised ⇒ correlations only.** Equal expected σ means σ drops out; no negative weights.
- **IDM / FDM** scale risk back up for diversification; **cap both at 2.5**.
- **Pessimism factors:** keep only a fraction of backtested return depending on method/in-vs-out-of-sample.
- **Max-position rule:** an instrument must be able to take a meaningful position or it's not worth including.

## Specific claims, mechanisms & data (PRESERVE EXACTLY)
- Diversification can **roughly double the Sharpe ratio**.
- **Handcraft weight examples (3 assets by correlation):** corr (0, 0.5, 0) → **30/40/30**; (0, 0.9, 0) → **27/46/27**; (0.5, 0, 0.5) → **37/26/37**; **floor negative correlations at 0**.
- **Bond / S&P / NASDAQ:** single-period **68/32/0** (extreme); bootstrap **53/27/20**; handcraft **50/25/25**.
- **Subsystem correlations ≈ 0.7 × instrument correlations** (for dynamic systems).
- **IDM by #assets × avg corr:** 2 / 0.0 → **1.41**; 5 / 0.0 → **2.2**; 10 / 0.5 → **1.35**; 50+ / 0.0 → **7.1**. **Cap IDM and FDM at 2.5** (corr → 1 in crises).
- **Pessimism factors (fraction of backtested return to keep):** single-period **in-sample 25%**, **OOS 75%**; bootstrap **OOS 75%**; handcraft **no-SR in-sample 70%**, **with-SR 65%**.
- **Max-position rule:** aim for max possible position **≥ 4 instrument blocks**; if not, **raise the weight, drop the instrument, or shrink the portfolio**.
- **Portfolio position = subsystem position × instrument weight × IDM.**

## How to APPLY (decision rules)
1. **Never use single-period Markowitz** for live weights — handcraft (fast) or bootstrap (rigorous).
2. **Use correlations only** (subsystem corr ≈ 0.7 × instrument corr); **floor negatives at 0**; don't tilt by Sharpe unless you truly have the evidence.
3. **Handcraft:** group correlated assets (1–3/group), apply the bootstrapped table, allocate across groups, multiply group × within-group for the final weight.
4. **Scale up by IDM** (and FDM for forecasts), but **cap each at 2.5**.
5. **Apply the pessimism factor** matching your method (e.g. bootstrap OOS → keep 75%) before believing the Sharpe.
6. **Check the max-position rule** (≥4 blocks); fix by raising weight, dropping the instrument, or shrinking the book.
7. **Final portfolio position** = subsystem position × instrument weight × IDM (then round + inertia, ref 07).

## Caveats / where he hedges
- **Handcrafting is mildly in-sample** (it peeks at correlations) — treat with slightly more scepticism, hence its 65–70% pessimism factor.
- **Don't tilt instrument weights by Sharpe** — you rarely have enough evidence to tell Sharpes apart (that's the whole Markowitz critique).
- **Correlations break exactly when you need them** (→ 1 in crises) — the 2.5 cap on multipliers is the guardrail.

## Memorable quotes
- "Diversification really is the only free lunch in investment."
- "If you are out to describe the truth, leave elegance to the tailor." (Einstein, cited approvingly against elegant-but-fragile optimisation.)
- Bootstrapping is "the average of many optimisations, not one optimisation on the average."
