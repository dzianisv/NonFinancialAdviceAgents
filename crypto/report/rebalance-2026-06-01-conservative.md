# Real-book rebalance — 2026-06-01 · CONSERVATIVE variant

Sibling to the MODERATE plan (`rebalance-2026-06-01.md`). Same book (~$177,145), same exits — but
**no crypto-direction bet**: 100% clean stable yield + a small gold ballast. **Read-only: you execute.**
Confirm live balances, re-pull APYs, verify addresses before signing.

## Why this may be the better call
The repo backtest (`crypto/backtest/RESULTS.md`) showed that over 2024–26 the all-clean-stable book
returned **~5.0% with ~0 drawdown**, while the moderate directional sleeve returned **2.44% with −18.5%
drawdown** — because ETH fell 33%. Unless you hold a bullish crypto view, conservative is the
better-evidenced risk-adjusted choice in the current risk-off regime (Resolv/Gauntlet curator losses,
TON bridge closing). Moderate only wins if crypto rises.

## Target — 100% clean stable + gold, all caps compliant (sums to 100%)

| Venue | Chain | Collateral / yield source | Live APY [source · re-pull] | $ | % |
|---|---|---|---|---|---|
| Maple syrupUSDC (native pool `43641cf5…`) | Ethereum | o/c institutional loans | 4.62% [DL] | $25,000 | 14.1% |
| Morpho steakUSDC (Steakhouse) | Base | o/c cbBTC/ETH | 4.61% [DL] | $25,000 | 14.1% |
| Morpho gtUSDCp / Steakhouse Prime | Base | o/c cbBTC | 4.61% [DL] | $20,000 | 11.3% |
| Aave v3 USDC (instant anchor) | Ethereum | blue-chip cross-coll | 3.20% [DL] | $25,000 | 14.1% |
| Sky sUSDS | Ethereum | Sky T-bills + PSM | 3.60% [DL] | $25,000 | 14.1% |
| Ondo USDY | Ethereum | US T-bills (RWA) | 3.55% [DL] | $20,000 | 11.3% |
| Fluid USDC (rewarded $129M pool) | Ethereum | o/c lending | 6.38% all-in [DL] | $14,000 | 7.9% |
| save.finance USDC | Solana | o/c lending | 2.20% [DL] | $13,000 | 7.3% |
| jup.ag USDC-lend | Solana | o/c lending | ~5% [DL] | $5,000 | 2.8% |
| PAXG (gold ballast) | Ethereum | LBMA gold | 0% | $4,360 | 2.5% |
| instant USDC reserve | Base | — | 0% | $1,785 | 1.0% |
| **Total** | | | **~4.2% blended** | **$178,145** | **100%** |

**Caps:** ≤20%/position ✓ (max 14.1%) · ≤30%/protocol ✓ (Morpho steakUSDC+gtUSDCp = $45k = 25.4%) ·
≤25%/issuer ✓ (T-bill issuers Sky vs Ondo separate) · off-main ≤13% ✓ (Solana = $18k = 10.2%) ·
instant-liquidity reserve held · synthetic/perp-LP/directional = **0**.

## Crash test
−60% crypto ≈ **−1% to +0%** (stables flat, gold +5%). Near-zero drawdown — the point of conservative.
Residual: USDC-heavy (sUSDS/USDY/USDT legs diversify issuer; a hard USDC depeg still hits the sleeve);
Maple notice window (14%, the one non-instant leg); curator tail (blue-chip curators + 25% protocol cap).

## Tickets
Same **TON-first** exit sequence and idle-reactivation as the moderate plan (tickets 1–15 there), EXCEPT
the directional build (C) is replaced by rotating ALL crypto positions to stables:
- stETH $3,141 + cbETH $233 + fragSOL $3,935 + SOL $1,490 + HYPE $5,175 + ASTER $3,547 + alts/dust →
  **sell to USDC → stable core** (Aave/sUSDS/USDY to target). Keep only **PAXG $4,360** as gold ballast.
- All idle + exited junk → the stable table above.
- Net: blended yield 1.68% → **~4.2%**, with near-zero crash drawdown and zero crypto beta.

**I do not execute — you sign every ticket. Re-pull APYs + verify addresses first.**
