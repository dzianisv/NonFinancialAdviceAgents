# Crypto Portfolio — STRATEGY

> **Educational analysis, not financial advice.** Live data 2026-05-30 (DefiLlama + Morpho + protocol
> sources). Read-only mandate: the investor signs every transaction; this file never custodies keys.
> Implements the goal in [`GOAL.md`](GOAL.md). APYs move — re-run [`portfolio.py`](portfolio.py) before acting.

This is the standing policy that turns the goal into action: **maximize sustainable net yield on the book
*and all incoming cash*, subject to hard capital-preservation constraints.** It is a control loop, not a
one-time trade list.

## 0. Policy assumptions (acting as the investor — override any of these)

The optimization is undefined without a risk policy. I've set conservative defaults that match the current
book (already 69% stables) and crypto's actual risk profile. **Tell me to change any line.**

| Policy | Default | Rationale |
|---|---|---|
| Max whole-book drawdown in a −60% crypto move | **~ −20%** | Conservative; crypto draws down 60–80% routinely (2018, 2022), so the book must absorb that without breaking |
| Time horizon | **3–5+ yr**, no near-term liquidity event | Lets us use notice-window products (Maple) for part of the sleeve |
| Instant-liquidity reserve | **≥ $25k (~15%)** withdrawable same-day | Survives a DeFi run / utilization spike without unwinding the whole book |
| Stable vs directional posture | **Keep stables high; do NOT add crypto beta** | Directional vol (60–80% drawdowns) dwarfs any yield; the durable win is real yield on principal |
| KYC for tokenized T-bills | **No (default permissionless)** | Keep it click-to-deposit; revisit if you want the ~4.65% USDY tier |
| Self-custody | **Yes** — blue-chip spot off perp venues to a hardware wallet | Removes exchange/venue custody risk on the directional sleeve |
| Stablecoin mix | **Diversify USDC-heavy → add USDT + USDS** | A single-stable depeg is the sleeve's main correlated risk |

## 1. Target allocation

Two layers: **strategic sleeves** (policy-driven), then **the venue menu inside the stable sleeve** (yield-maximized
under the caps). Sized on the current ~$177k. **Net effect: yield ~1.7% → ~3.8–4.5%, while risk drops** (exit perp-LP,
cut TON concentration, drop speculative alts, diversify the stable base).

### Strategic sleeves

| Sleeve | Target | $ | vs now | Why |
|---|---|---|---|---|
| **Clean stable yield** | **68%** | ~$120k | 69% → 68% (but reactivated) | The engine. Most of the book, now actually earning ~4.6% instead of ~1.7% |
| **Gold (PAXG)** | **6%** | ~$11k | 2.5% → 6% | Non-correlated, non-custodial-counterparty ballast; funded by exiting speculative alts, not by selling stables |
| **SOL (jitoSOL)** | **4%** | ~$7k | consolidate | Staking is near-mandatory (~5.6% MEV-real); consolidate fragSOL + idle SOL |
| **ETH (wstETH)** | **3%** | ~$5k | hold | Keep existing exposure, convert to the safest LST; don't add beta |
| **Satellite** | **≤5%** | ~$9k | 12% → 5% | Cap the "you-are-the-house" / high-risk sleeve; survivable if it zeros |
| **Cash/gas buffer** | ~2% | ~$4k | — | Operating float for rotations |

Note the deliberate trade: adding defensive gold (0% yield) costs ~0.2% of blended yield versus an
all-into-stables max. That is the risk-aware choice — bought downside protection, not chased basis points.

### The stable sleeve menu (yield-max under the caps: ≤15%/position, ≤25%/protocol, ≥$25k instant)

| Venue | Chain | ~APY | Target $ | Liquidity | Collateral |
|---|---|---|---|---|---|
| **Maple Syrup USDC** | Ethereum | 4.85% | $24k | **Notice window** (the one locked sleeve, <15%) | Overcollateralized institutional loans |
| **Morpho Steakhouse Prime USDC** | Base | 4.5% | $24k | Instant | 95% cbBTC |
| **Morpho Gauntlet USDC Prime** | Base | 4.5% | $18k | Instant | ~93% cbBTC (different curator = diversification) |
| **Kamino Main USDC** | Solana | ~5.0% | $18k | Instant | Overcollateralized SOL/BTC/ETH |
| **Aave v3 USDC** | Ethereum | 3.6% | $15k | **Instant — liquidity anchor** | Blue-chip cross-collateral, deepest book |
| **Jupiter Lend USDC** | Solana | ~4.0%* | $8k | Instant | Overcollateralized (≈1% is reward — haircut) |
| **Spark Savings (sUSDS)** | multi | 3.6% | $8k | **Instant — no-KYC T-bill floor** | Sky savings (T-bills + PSM); the USDS leg of the stable mix |
| **Maple Syrup USDT / Aave USDT** | Ethereum | 4.1% / 2.4% | $5k | Maple notice / Aave instant | USDT leg (depeg diversification) |

Blended stable yield ≈ **4.5–4.7%**. Instant-liquidity (Aave + sUSDS + all Morpho Base + Kamino + Jupiter) ≈ **$91k**,
far above the $25k floor; Maple is the only locked sleeve at $24k (<15%). Diversified across **6 protocols, 4 chains,
2 Morpho curators** — no single failure exceeds the 15% cap.

\* Jupiter's headline includes a token reward; budget the conservative base.

## 2. The standing rules (the control loop)

| Job | Trigger | Action |
|---|---|---|
| **Deploy** | Any cash/stable balance below the clean frontier for **> 3 days** (new deposit, harvested yield, exit proceeds, idle) | Push to the cash waterfall (§3). No idle cash. |
| **Monitor** | Weekly `portfolio.py` run | Check blended yield, idle $, concentration, each position's live APY + collateral grade |
| **Rotate** | A held venue's **net APY drops below 3%** for >1 week, **or** its collateral fails the C1 screen, **or** TVL/utilization signals stress | Exit to the next-best eligible venue; log the reason |
| **Rebalance** | A sleeve drifts **±5%** off target, or any position breaches the **15%** cap | Trim the overweight, top up the underweight |
| **Defend** | Crypto risk-off: BTC/ETH trend break, funding/vol spike, a major depeg or protocol exploit | Raise stable+gold toward the top of band, cut satellite to ~0, move directional to the safest LSTs |

## 3. Cash-deployment waterfall (for *any* incoming cash)

When cash arrives or a position is exited, fill in this order until each sleeve is at target:

1. **Instant-liquidity reserve** short of $25k? → Aave USDC / sUSDS first.
2. **Stable sleeve** below 68%? → fill the menu venue that is furthest below its target weight and still under its 15% cap (rotates deposits across protocols/chains automatically).
3. **Gold/SOL/ETH** below band? → top up (jitoSOL for SOL, wstETH for ETH, PAXG for gold).
4. **Everything at target?** → park overflow in the highest instant-liquidity clean venue; never leave it in a raw wallet.

This is what makes "available cash" first-class: every dollar has a defined next home within 3 days.

## 4. Transition plan (current → target)

Order matters: stop the bleeding first (free + risk-reducing), then clean up, then optimize.

**Phase 1 — Reactivate idle (this week, ~+$2.9k/yr, gas-only).** Verify on-chain addresses first — audit found
the tracked Seamless/Re7 vaults may be deprecated/empty.
- Move idle Morpho USDC (~$62k: Seamless $37.8k, Extrafi $10k, Universal $14k) → split into Morpho Steakhouse Prime + Gauntlet Prime (Base) + Maple, respecting the 15% cap.
- Sweep raw idle (Hyperliquid $5.7k, Solana $4k, DeFi.app $1k, Asterdex $1k) → Aave/Kamino.
- Move save.finance $16.3k (2.2%) → Kamino Main USDC (~5%).

**Phase 2 — De-risk (this week, removes the biggest tail risks).**
- **Exit both Storm SLP legs (~$17.4k)** — you're underwriting leveraged traders → redeploy to the stable menu.
- **Exit DeDust TON-USDT ($6.4k)** — IL at ~0% + the TON bridge is closing 2026 → redeploy. Brings TON from 14% to ~0%.
- **Exit ASTER ($3.5k)** and sweep alt dust (STRK, LINEA, JUP, TRUMP, POL, OP) → gold + stables.
- **Trim HYPE** from $5.2k toward ~$2–3k (it's at ATH on a ~100x multiple) → gold/stables.

**Phase 3 — Consolidate directional (this month).**
- fragSOL + idle SOL ($5.4k) → **jitoSOL** (~5.6%, deepest liquidity).
- stETH + cbETH ($3.4k) → **wstETH** (rebase-free).
- Add ~$6.6k from alt proceeds to **PAXG** (2.5% → 6%).
- Keep satellite ≤5%: HLP $5k (best-governed) + Avantis $1k; everything else exits.

**Phase 4 — Instrument (ongoing).** Encode these target weights in `portfolio.py`, run weekly, act on drift.

## 5. Crash validation (does the target survive the thing we're defending against?)

Scenario: **BTC/ETH/SOL −60%, broad crypto risk-off.** Approximate book impact:

| Sleeve | Weight | Stress assumption | Contribution |
|---|---|---|---|
| Stable (overcollateralized + T-bills) | 68% | −1 to −2% (liquidation buffers hold; possible brief liquidity/notice delay) | ≈ −1.4% |
| Gold | 6% | +5% (typical crisis ballast) | +0.3% |
| ETH+SOL | 7% | −60% | −4.2% |
| Satellite | 5% | −50% | −2.5% |
| **Total book** | | | **≈ −8% to −12%** |

Inside the −20% tolerance, **by design** — the defense is structural (low directional beta + a large
overcollateralized stable base + gold), not a market call.

**Residual risks (named, not hidden):**
- **USDC depeg** — the sleeve is USDC-heavy. Mitigated partially by the USDT (Maple/Aave) and USDS (sUSDS) legs; a hard USDC depeg still hits most of the sleeve. Watch Circle/USDC peg; widen the USDT/USDS legs if concerned.
- **Maple notice window** — in a stress run, the $24k Maple sleeve may not be same-day. That's why $91k sits in instant venues and the reserve floor is $25k.
- **Smart-contract risk** — diversified across 6 protocols; the 15% cap bounds any single exploit to ≤$26k.

## 6. Expected outcome

| | Now | After strategy |
|---|---|---|
| Blended yield | ~1.7% (~$2,989/yr) | **~3.8–4.5% (~$6,700–7,000/yr)** |
| Idle stables (<3%) | ~$104k | ~$0 |
| Biggest single position | 21% (Seamless, 0%) | ≤15%, all earning |
| Perp-LP / "you're-the-house" | ~$22k | ≤$6k (capped satellite) |
| TON concentration | 14% | ~0% |
| Est. crash drawdown | not modeled | **~ −8 to −12%** (within −20% policy) |

**~$3,700–4,000/yr more income, less concentration, less platform risk, and a modeled crash floor** — the goal's
definition of better-yield-risk-aware.

## 7. What still needs you

- **Confirm or edit the §0 policy defaults** (especially max-drawdown and the no-KYC choice).
- **Verify the on-chain addresses** of the Seamless/Extrafi/Universal/Re7 holdings before Phase 1 (possible deprecated vaults).
- **Execute** — I'll produce exact per-transaction tickets (amount, from, to) on request; you sign from your wallet.

## References

Goal & constraints: [`GOAL.md`](GOAL.md) · Tracker: [`portfolio.py`](portfolio.py) · Screening: [`../research/10-crypto-lp-yield-state.md`](../research/10-crypto-lp-yield-state.md) · Separate tradfi book: [`../GOAL.md`](../GOAL.md)
