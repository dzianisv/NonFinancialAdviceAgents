# Real-book rebalance — 2026-06-01 (MODERATE) · red-teamed v2

Produced by the `defi-portfolio-manager` hedge-fund team on the investor's actual ~$177,145 book,
then **adversarially red-teamed and corrected** (5 must-fix errors found & fixed — see end).
**Read-only: the investor executes every transaction.** Confirm current balances and re-pull every
APY + verify every on-chain address before signing.

## Verdict
A 1.68%-yield book where **$103.9k (59%) sits idle <3%**, the largest position ($37.8k Seamless USDC)
earns **0.00% live**, and ~$48k is in synthetics + perp-LP "you're-the-house" junk. Fix: free
idle-reactivation (+~$4.5–5k/yr, zero new risk) → exit synthetics/perp-LP → build directional to the
moderate band with staked BTC/ETH/SOL. Target blended → ~5.3%. **This is a crypto-direction bet
(29–33% directional); the repo backtest shows it lost vs all-stable in the 2024–26 bear — say the word
for a conservative all-stable (~5%, near-zero-drawdown) re-cut.**

## Moderate target — reconciles to 100%, all caps compliant

| Sleeve | $ | % | Venues |
|---|---|---|---|
| **Stable core** | $114.9k | **65%** | gtUSDCp Base $25k · steakUSDC Base $20k · **Maple syrupUSDC (native pool `43641cf5…`, NOT a Morpho "SYRUPUSDC" market)** $17.3k · **Fluid USDC (rewarded $129M pool, 6.38% all-in)** $14k · Sky sUSDS $13k · Ondo USDY $12k · save.finance Solana $6k · jup.ag USDC-lend Solana $1.2k · instant reserve $6.4k |
| **Directional** | $57.7k | **33%** | jitoSOL Solana **$13.5k** · wstETH $14.5k · **cbBTC held SPOT (self-custody, NOT lent on Morpho)** $21k · HYPE $5.2k · SOL $1.5k · ASTER $2k |
| **Gold** | $4.36k | **2.5%** | PAXG |
| **Total** | **$177.0k** | **100%** | |

**Caps (compliant by construction):** ≤20%/position ✓ (max gtUSDCp 14.1%) · ≤30%/protocol ✓ (Morpho = gtUSDCp+steakUSDC $45k = 25.4%; cbBTC is **spot, not Morpho**, so it doesn't add) · off-main ≤13% ✓ (Solana = jitoSOL 13.5 + save 6 + jup 1.2 = $20.7k = **11.7%**) · satellite 0 · synthetic/perp-LP **fully exited this cycle (was $17.4k Storm + others; →0 after legs 9–16)** · instant reserve $6.4k held.

## Crash test
−60% crypto ≈ **−21%** book — inside the moderate −30% budget. Tails named: Morpho curator risk (risk-off regime post Resolv/USR 2026-03-22; blue-chip curators + 25% protocol cap mitigate), Solana smart-contract (Drift $286M Apr-2026 was admin-key, not jitoSOL — confirm save/jup admin posture), Maple credit (single-issuer ≤10%).

## Tickets — sequence **TON-first** (bridge degrading this month), then idle-reactivation, then directional

**Each ticket: verify on-chain address & re-pull APY before signing.**

**TON EXIT — DO FIRST (oracles withdraw June 2026, bridge shuts Sept 1; fees currently waived):**
1. EXIT $8,877 + $8,520 — Storm USDT-SLPT + TON-SLP (TON) → unwind → bridge USDT→USDC (confirm you receive native USDC, not a j-token needing a 2nd hop) → Sky sUSDS / Ondo USDY (Eth). *Perp-LP veto + TON exit.*
2. EXIT $6,383 — DeDust TON-USDT LP (TON) → unwind (mind IL) → bridge → stable core. *AMM-LP/IL + TON.*

**FREE IDLE-REACTIVATION (zero new risk):**
3. $25,000 — Seamless USDC (Base, vault `0x616a4E1db48e22028f6bbf20444Cd3b8e3273738` — the legit Gauntlet-curated vault, safe to withdraw, just 0% for you) → Morpho gtUSDCp (Base).
4. $12,770 — Seamless USDC remainder → Morpho steakUSDC (Base, top to $20k) + $3.77k → reserve. (Clears the 21.3% position-cap breach.)
5. $10,000 — Extrafi XLend (Base, 0%) → **Fluid USDC rewarded $129M pool** (Eth, ~6.38% all-in).
6. $10,000 — Universal USDC L3 (Base, 0%) → Sky sUSDS (Eth).
7. $10,000 — Universal $4,094 + Hyperliquid idle $5,676 → Ondo USDY (Eth).
8. $5,964 — idle Solana/DeFi.app/Asterdex USDC → save.finance (Solana, top to $6k) / overflow gtUSDCp.
9. $2,054 — Woo.Fi vault (Avax) → Morpho gtUSDCp (Base).

**EXIT JUNK (reject-list):**
10. EXIT $6,149 R7 USDe @ Morpho → steakUSDC (synthetic).
11. EXIT $2,887 sUSDe @ Ethena → **Maple native syrupUSDC** (synthetic).
12. EXIT $2,806 Re7 eUSD @ Morpho → Fluid (USR-exposed curator + synthetic).
13. EXIT $5,000 HLP @ Hyperliquid → gtUSDCp (perp-LP).
14. EXIT $1,000 Avantis LP → reserve (perp-LP).
15. EXIT $609 lighter.xyz SOL farm → jitoSOL (emissions).

**DIRECTIONAL BUILD (last):**
16. CONVERT $3,935 fragSOL + $1,490 SOL → jitoSOL (target $13.5k staked — keeps Solana ≤13%).
17. CONSOLIDATE $233 cbETH + $3,141 stETH → wstETH (kill 0% cbETH).
18. BUY ~$21,000 → **cbBTC held SPOT / self-custody (do NOT lend on Morpho — would breach the 30% protocol cap)**.
19. TRIM ASTER $3,547 → $2,000; let TRUMP/micro-dust bleed into stable core.

## Red-team review (applied)
Adversarial review (live data, 2026-06-01) found and this v2 fixes:
- **H1** Solana cap breach → jitoSOL cut to $13.5k, Solana now 11.7% (≤13%).
- **H2** false "perp-LP = 0" → reworded "fully exited this cycle."
- **H3** syrupUSDC routing trap → pinned to Maple native pool `43641cf5-a92e-416b-bce9-27113d3c0db6`, not a Morpho "SYRUPUSDC" 0% collateral market.
- **M1** ~$28k unaccounted → target reconciled to 100% (stable to 65% band, directional to 33%, cbBTC to $21k spot).
- **M2** TON bridge closing June/Sept 2026 → TON exits re-sequenced FIRST.
- **M4** cbBTC venue → specified SPOT/self-custody so Morpho stays ≤30%.
- **L1** Fluid → deposit the rewarded $129M pool (6.38%), not the $8.5M clone.
- **L2** Seamless is the legit Gauntlet vault, not a malicious clone — safe to withdraw.

## Caveats
- Balances are the session snapshot; **confirm live balances first.**
- Re-pull APYs + verify each address (deprecated Morpho clones earn ~0%); use Circle CCTP for USDC bridging.
- MODERATE = a crypto-direction bet (backtest `crypto/backtest/RESULTS.md` shows it lost in the 2024–26 bear). Conservative all-stable re-cut available on request.
