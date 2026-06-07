# Fitting, Overfitting & Costs — the Speed Limit

> Source: Carver, *Systematic Trading* (Harriman House, 2015), ch. on fitting/over-fitting and the chapter on trading costs (the standardised cost, the one-third speed limit, day-trading impossibility). Distilled 2026-06-07.

## Core thesis
**Most backtests lie.** If you test many rules, lucky winners are *guaranteed* — and you'd need **decades** of data to tell a genuinely good rule from a lucky one. So the discipline is: **test few ideas, prefer simple/robust/generic parameters, pool data across instruments, always test expanding/rolling out-of-sample (never a time machine), and DON'T select rules on their performance** — reserve return data only for setting forecast *weights* (and even then down-weight, rarely exclude). The second killer is **costs**. Carver makes them comparable with a **standardised cost** (Sharpe units lost per round trip), and imposes a hard **speed limit: never pay more than one-third of your expected Sharpe in costs.** This single rule makes **day-trading essentially impossible** after costs, and is the repo's pre-trade gate (GOAL.md): backtest with *realistic* costs and clear the speed limit before trading.

## Key frameworks / mental models
- **Over-fitting is the default outcome** of searching many rules — "if you test enough rules, some bad ones will always slip through."
- **In/out-of-sample hierarchy:** in-sample **BANNED**; **expanding-window (anchored / walk-forward) PREFERRED**; rolling-window OK with enough data.
- **Don't pick rules on performance** — pool, equal-weight by default, use returns only to *weight* (down-weight) not to select.
- **Pooling data** across instruments multiplies effective history and makes good rules detectable far sooner.
- **Standardised cost** = a common currency for cost (SR lost per round trip).
- **The speed limit:** costs ≤ ⅓ of expected SR → a **turnover limit**.

## Specific claims, mechanisms & data (PRESERVE EXACTLY)
- **Realistic Sharpe ranges:** single-instrument rule ≈ **0.30–0.40**; multi-asset roughly **doubles** (~0.40–0.50 dynamic; static ~0.40; semi-auto ~0.25). **Sustained SR > 1.0 essentially never.**
- **Gold fitting demo:** pick the best variation annually → SR **0.07**; pick randomly → **0.20**; equal-weight all 90 variations → **0.33** (equal-weighting beats clever selection).
- **Years to prove SR > 0:** SR 0.3 → **37 yr**; 0.5 → **20**; 1.0 → **6**; 2.0 → **1.4** (the average single-instrument rule needs **~40 yr**).
- **Years to prove rule A > B:** 0.5 advantage, corr 0 → **37 yr**; 0.25 advantage, corr 0.95 → **10 yr**.
- **Pooling:** 0.05 vs 0.30 on one instrument → **45 yr** to distinguish; pooled (→ 0.13 vs 1.13) → **11 yr**.
- **Standardised cost = (2 × C) ÷ (16 × ICV)** = SR units lost per round trip (C = cost to trade one block; ICV from ref 04).
- **Cost benchmarks (SR per round trip):** liquid futures ~**0.001–0.002**; expensive ~**0.03**; index spread bets ~**0.01**; ETFs ~**0.08**.
- **Cost in SR/yr = standardised cost × turnover.**
- **SPEED LIMIT: pay ≤ ⅓ of expected SR in costs.** Staunch (max SR ~0.4) → **≤ 0.13 SR/yr**; asset allocators & semi-auto (max ~0.25) → **≤ 0.08 SR/yr**.
- **Turnover limit = limit ÷ standardised cost** (e.g. Euro Stoxx: 0.13 ÷ 0.002 = **65 round trips/yr** ≈ ~1-week holding).
- **Day trading (~500 round trips/yr) is essentially impossible after costs.** Carver's own ch.15 rule set turns over **12.5 round trips/yr**.

## How to APPLY (decision rules)
1. **Test few, simple, generic ideas.** Resist grid-searching parameters and keeping the winner.
2. **Always out-of-sample** — expanding/anchored window preferred; in-sample results are inadmissible.
3. **Never select rules on returns**; use them only to weight (and rarely exclude). Equal-weight beats clever selection (the gold demo).
4. **Pool data across instruments** to shorten the decades-long detection problem.
5. **Compute the standardised cost** = (2×C)/(16×ICV); multiply by turnover to get SR/yr lost.
6. **Apply the speed limit:** costs ≤ ⅓ of expected SR (≤0.13 staunch, ≤0.08 allocator/semi-auto). If it fails, **slow the system or drop the instrument.**
7. **Treat this as the GOAL.md pre-trade gate** — no live order before a realistic-cost backtest clears the speed limit. Day-trading fails this gate by construction.

## Caveats / where he hedges
- **Backtest Sharpe is upward-biased** even done correctly — haircut it (and combine with the pessimism factors in ref 05).
- **You may never get enough data** to prove a rule works — which is *why* the priors (simple, generic, pooled, few) matter more than the fit.
- **Cost estimates are approximate**; for small traders assume cost ≈ half the bid-offer spread (ref 07) and err pessimistic.

## Memorable quotes
- "If you test enough rules, some bad ones will always slip through."
- "I personally think it's foolhardy to pay more than a third of your expected profits in trading costs."
- Equal-weighting all 90 gold variations (SR 0.33) beat annually picking the 'best' (SR 0.07) — selection destroys value.
