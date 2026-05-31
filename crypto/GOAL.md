# Crypto Portfolio — GOAL

> **Educational analysis only — not financial advice.** APYs/balances pulled live from DefiLlama and
> protocol APIs (last: **2026-05-30**) and move hourly. Verify against your own wallet before acting.
> Read-only research mandate: **never** custody keys or sign transactions — the investor executes.

## The mission

Build and run a **risk-aware yield strategy** — a standing policy, not a one-time trade — that manages the
live **~$177k multi-chain crypto book *and all available cash*** (idle balances, new deposits, harvested
yield, proceeds from exits) to earn the **best sustainable net yield the mandate allows, without ever
compromising capital preservation.** Conservative, capital-preservation-first — managed against crypto's
own failure modes (smart-contract, depeg, bridge, custody, liquidity, yield-traps), not any macro cycle.

The strategy's **output at any moment is an optimal target allocation**: a specific, defended weight for every
dollar, derived from the full eligible opportunity set under explicit constraints, such that you **cannot raise
expected risk-adjusted return without breaking a constraint or lowering collateral quality.** But the goal is
not a single snapshot — it is the **strategy that keeps producing and holding that allocation as rates, cash,
and market regime change**: deploy idle cash fast, rotate out when a venue's yield decays or its collateral
degrades, rebalance on drift, and de-risk in a crash. No dollar sits idle; no dollar takes unpriced risk.

## The strategy (the actual deliverable)

A written, automatable policy — a control loop, not a spreadsheet — with five standing jobs:

| Job | Trigger | Default action |
|-----|---------|----------------|
| **Deploy** | Any cash (new deposit, harvested yield, exit proceeds, idle balance) sits > **D_cash days** | Move to the current best **C1-passing** venue with capacity, respecting the caps below |
| **Monitor** | Continuous (via `portfolio.py`) | Track live blended yield, idle $, concentration, collateral grade per position |
| **Rotate** | A held venue's net yield falls below the clean frontier, or its collateral degrades / fails C1 | Exit to a better eligible venue; record why |
| **Rebalance** | A sleeve or position drifts outside its band (C2–C8) | Trim/add back to target |
| **Defend** | Crypto risk-off (BTC/ETH trend break, funding/vol spike, a major depeg or exploit) | Raise stable/gold weight, cut satellite, per the policy bands |

"Better yield, risk-aware" = **maximize sustainable net yield subject to the hard constraints below** — never
the other way around. The optimization problem below is how each cycle of this loop is *solved*; the loop is
the strategy.

## The optimization problem (well-defined)

**Decision variables.** A weight `wᵢ ≥ 0` for each eligible venue/asset `i`, with `Σ wᵢ = 1` (of investable capital).

**Two layers** (solve top-down):

1. **Strategic sleeves** — the split across `{clean-stable-yield, ETH, SOL, BTC, gold, satellite}`. Driven by
   the **investor's risk tolerance / horizon / liquidity needs and crypto's volatility**, not by yield.
   This layer is a *policy choice*, not a free optimization — it needs the investor inputs below.
2. **Within the stable sleeve** — a true constrained yield-maximization (a linear program):
   **maximize** `Σ wᵢ · r_netᵢ` **subject to** the constraints below, where `r_netᵢ` = live APY net of expected
   loss, gas, and protocol fees.

**Objective.** Maximize expected **net** blended yield on the cash sleeve and risk-adjusted total return overall,
where the directional sleeve is sized for *survival in a crash*, not for yield.

**Hard constraints (a position is ineligible or capped if it violates any):**

| # | Constraint | Current setting (tunable) |
|---|---|---|
| C1 | **Collateral whitelist.** Every yield position backed only by T-bills, BTC, ETH, SOL-staking, or overcollateralized loans against those. No reflexive/synthetic dollars (sUSDe, stcUSD, reUSD…), no PT/looped/long-tail, no perp-LP in the core. | per [`10-crypto-lp-yield-state.md`](../research/10-crypto-lp-yield-state.md) checklist |
| C2 | **Position concentration** ≤ X% of book in any one vault/pool | 15% |
| C3 | **Protocol concentration** ≤ Y% across all pools of one protocol | 25% |
| C4 | **Chain concentration** ≤ Z% per chain outside Ethereum/Base | 10% |
| C5 | **Capacity** — deposit ≤ 10% of a pool's TVL (avoid rate impact) | 10% of TVL |
| C6 | **Liquidity** — ≥ L% of the book redeemable within D days (respect Maple/notice windows) | *needs investor input* |
| C7 | **Satellite cap** — high-risk/perp-LP/points positions ≤ S% total, sized so a total loss is survivable | 5% |
| C8 | **Sleeve bands** — stable / ETH / SOL / BTC / gold / satellite within target ranges | *needs investor input* |
| C9 | **No idle cash** — no stablecoin/cash balance sits below the clean frontier longer than `D_cash` days; default destination = current best C1 venue with capacity | D_cash = 3 days |

**Definition of optimal (the stop condition).** The allocation is optimal when it sits **on the efficient
frontier for this mandate**: no feasible reallocation raises expected net yield (stable sleeve) or improves the
risk/return of the whole book without violating C1–C8. Equivalently — every stable dollar earns ≥ the clean
frontier (~4.5–4.7%) or has a documented reason it can't, and no constraint is breached.

## Required investor inputs (without these, "optimal" is undefined)

These are policy choices only the investor can make — they set C6, C8, and the satellite appetite:

- [ ] **Risk tolerance** — max tolerable drawdown on the *whole* book in a −60% crypto move (e.g. −15%? −30%?).
- [ ] **Time horizon** — when, if ever, is this capital needed?
- [ ] **Liquidity need** — how much must be withdrawable within 1 / 7 / 30 days?
- [ ] **Stable vs directional split** — target % in yield-bearing stables vs blue-chip crypto upside.
- [ ] **KYC willingness** — open to RWA tokenized-T-bill products (BUIDL/USTB/USDY) that require onboarding? They're the genuinely-safest ~3.5% tier but gated.
- [ ] **Per-protocol trust caps** — any protocol you want hard-limited or excluded regardless of yield.
- [ ] **Self-custody preference** — willing to move blue-chip spot (SOL/ETH) off exchanges/perp venues to cold storage?

## Success criteria (how we know the goal is reached)

- [ ] **Strategy written & automatable** — a standing policy ([`STRATEGY.md`](STRATEGY.md)) implementing the five-job control loop above, with explicit numeric bands and cash rules, not a one-off trade list.
- [ ] **Opportunity set enumerated** — the full menu of C1-passing venues across all held chains *and* the obvious unheld ones (Aave, Spark/sUSDS, clean Morpho vaults per chain, Maple, RWA T-bills, ETH LSTs, SOL LSTs, BTC-collateralized lending), each with live APY, TVL/capacity, and liquidity terms.
- [ ] **Investor inputs captured** (the checklist above) so C6/C8 are numbers, not blanks.
- [ ] **Target weights computed** by the two-layer optimization, with each weight traceable to a constraint or a yield rank.
- [ ] **Crash-validated** — the target survives a scenario test (BTC/ETH −60%, a stablecoin depeg, a venue freeze) within the C-row drawdown/liquidity limits.
- [ ] **Transition plan** — exact from→to tickets with gas/fee/tax cost, and net uplift > transition cost.
- [ ] **Instrumented** — [`portfolio.py`](portfolio.py) reports current weights vs target and the drift, monthly.

## Current status — ⚠️ GOAL NOT YET REACHED

Done so far (necessary, not sufficient):
- ✅ **Audited** the live book (2 research subagents vs DefiLlama/Morpho). Findings below.
- ✅ **Built the tracker** ([`portfolio.py`](portfolio.py)) — live value, blended yield, idle capital, concentration.
- ✅ **Interim "stop-the-bleeding" target** — reactivate idle cash to the clean frontier (the model below).

Now done (2026-05-30):
- ✅ **Opportunity set enumerated** — clean stable lending, RWA T-bills, and ETH/SOL/BTC staking swept across chains (3 research agents). The graded menu is in [`STRATEGY.md`](STRATEGY.md).
- ✅ **Strategy written** — [`STRATEGY.md`](STRATEGY.md): policy defaults (acting as investor), target allocation + venue menu, the control loop, cash waterfall, transition plan, and crash validation (modeled ~−8 to −12% in a −60% crash, within the −20% policy).

Still open to fully *close* the goal:
- ⏳ **Investor sign-off** on the §0 policy defaults (max-drawdown, KYC, sleeve split) — set as defaults, not yet confirmed.
- ⏳ **Encode target weights in `portfolio.py`** (drift tracking) and **execute** the transition (investor signs).

### Audited state (2026-05-30)

| Metric | Value |
|---|---|
| Total | ~$177,145 |
| Stablecoins | $122k (69%) |
| **Blended yield (live)** | **~1.7% (~$2,989/yr)** |
| Stables earning <3% | **~$104k** |
| Biggest position | Seamless USDC @ Morpho — **$37,770 (21%)**, **0.00% live** |

Key findings: ~$62k of "0%" Morpho USDC is **genuinely idle** (deposits no one borrows; some in **deprecated
vault versions — verify addresses**); ~$17k in Storm perp-LP makes you counterparty to leveraged traders; TON
ecosystem is 14% (bridge closing 2026); two tracking errors hid real ~5% yields (jup.ag, fragSOL).

### Interim model (the floor, not the goal)

Reallocate ~$113k of idle/sub-frontier/exit-able stables → ~4.5% clean frontier (Maple Syrup USDC, Morpho
steakUSDC/gtUSDCp). No new risk — *less* risk (exits the perp-LP).

| | Income/yr | Yield |
|---|---|---|
| Now | $2,989 | 1.69% |
| Interim target | **$7,058** | **3.98%** |
| Uplift | **+$4,069** | +2.3 pts |

## Roadmap to the optimum

1. **Capture investor inputs** — the policy checklist above (one short session).
2. **Enumerate the opportunity set** — research agents sweep every chain for C1-passing venues; build a graded, live menu with capacity + liquidity terms.
3. **Solve** — run the two-layer optimization (strategic sleeves from policy, stable sleeve as a constrained LP) → target weights.
4. **Validate** — crash-scenario test against C6/C-drawdown limits.
5. **Transition** — cost/tax-aware from→to tickets; execute (investor signs).
6. **Maintain** — monthly drift check via `portfolio.py`; re-screen; rebalance to bands.

## References

- Tooling: [`portfolio.py`](portfolio.py) · report in [`report/`](report/) · run guide in [`README.md`](README.md)
- Screening & yield landscape: [`../research/10-crypto-lp-yield-state.md`](../research/10-crypto-lp-yield-state.md)
- Conservative-deposit thesis: [`../blog/2026-05-where-to-park-usdt-usdc.md`](../blog/2026-05-where-to-park-usdt-usdc.md)
- Separate tradfi book (not a driver of this strategy): [`../GOAL.md`](../GOAL.md)
