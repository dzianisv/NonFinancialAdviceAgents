# USR Incident Retro — DeFi Vault Alerting Design
*2026-06-25 — thinking doc for next agent*

## What Happened (30s)

ExtraFi XLend USDC vault on Base used Morpho with USR as collateral.
USR oracle was **hardcoded at $1.00** on-chain. After a March 2026 exploit, USR depegged to $0.60-0.70 on DEXes.
Morpho kept accepting USR as $1.00 collateral → vault drained by liquidators → `lostAssets = totalAssets`.
Result: $10k in → $5.1k recovered → **$4,900 permanent loss**.

The vault's own on-chain signals (Health Factor, lostAssets, liquidation events) were **all blind** during the exploit because the oracle never moved. The only reliable early signal was **external DEX price vs. oracle price**.

Estimated exit window: **~2-6 hours** between USR first breaking $0.90 on Uniswap and vault utilization hitting 100%.

---

## Alert Scenarios to Cover

### 1. Collateral Depeg (highest priority — this is what caused the loss)
- For each Morpho vault in the portfolio, identify collateral asset(s)
- Poll collateral DEX price every 5 min via **DeFiLlama** `coins.llama.fi/prices/current/base:0x...`
- Get oracle price: on-chain call `IOracle(vault.oracle()).price()` (returns 1e36 scaled)
- Alert if `|dex_price - oracle_price| / oracle_price > 3%`
- This would have fired ~2-6 hours early on USR

### 2. Pool APY Below T-Bill Rate
- Daily check: fetch `supplyApy` / `netApy` from `api.morpho.org/graphql` per vault
- For Maple: on-chain `totalAssets / totalSupply` delta over 7d → annualize
- For Beefy: `pricePerFullShare` delta
- Compare against T-bill proxy: FRED `DGS3MO` (free API) or hardcode ~5.25%
- Alert if pool APY < t_bill - 0.5% for 3 consecutive days (avoid noise)

### 3. Utilization Spike (liquidity risk)
- Morpho vault: `totalBorrowAssets / totalSupplyAssets`
- Alert if utilization > 90% (can't withdraw when 100%)
- This is a lagging signal vs. depeg but still useful — 90% threshold gives ~hours of notice

### 4. lostAssets Trigger (post-mortem signal)
- Morpho MetaMorpho: call `lostAssets()` on vault contract
- Alert immediately if > 0 (means curator already socialized a loss)
- Lagging — by definition fires after the loss — but catches any future incidents instantly
- Also catches partial losses (not just 100% drain)

### 5. Vault Deprecation
- Morpho `api.morpho.org/graphql` → `vault.whitelisted` or `state.isDeprecated`
- Alert if `whitelisted = false` OR `deposit_disabled = true`
- This was already built in `morpho_vault_status.ts` — wire it into the daily cron

---

## Data Sources

| Signal | Source | Reliability |
|---|---|---|
| DEX price | `coins.llama.fi/prices/current/chain:addr` | ✅ Free, no key, fast |
| Oracle price | On-chain RPC `IOracle.price()` | ✅ Canonical |
| Vault APY | `api.morpho.org/graphql` → `supplyApy` | ✅ Works |
| T-bill rate | FRED `https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS3MO` | ✅ Free, daily |
| Vault utilization | On-chain `totalBorrowAssets / totalSupplyAssets` | ✅ Canonical |
| lostAssets | On-chain `lostAssets()` on MetaMorpho | ✅ Canonical |
| Vault deprecated | `api.morpho.org/graphql` `whitelisted` field | ✅ Works |
| Maple default | Maple `api.maple.finance` or on-chain pool events | ⚠️ Undocumented API |

---

## Implementation Sketch (for next agent)

**Script:** `defi_alert_check.py` — daily cron, Telegram DM on trigger

```
1. Load active positions from defi-pnl-per-pool-2026-06-25.md or on-chain scan
2. For each Morpho vault:
   a. GET coins.llama.fi for each collateral asset DEX price
   b. RPC call oracle.price() → convert to USD
   c. If divergence > 3% → ALERT immediately
   d. GET api.morpho.org/graphql → supplyApy, utilization, lostAssets, whitelisted
   e. If utilization > 90% → ALERT
   f. If lostAssets > 0 → ALERT CRITICAL
   g. If whitelisted = false → ALERT
3. For Maple: compute 7d pricePerShare delta → annualized APY
4. Compare all APYs to T-bill (FRED DGS3MO)
5. If APY < T-bill - 0.5% for 3d → ALERT
6. Send Telegram message with table: pool | apy | t-bill | status | action
```

**Cron:** daily at 09:00 local. Run `defi_alert_check.py`. Silence on all-green.

**Alert channels:** Telegram bot (already used in this repo for crypto signals).

---

## Hardest Part

**Identifying collateral assets for each vault** — requires:
1. Read vault's `IRM` + market IDs from MetaMorpho contract
2. For each market, call `market.collateralToken()`
3. Map collateral token → oracle contract (`market.oracle()`)
4. Call oracle for price

This is 3-4 on-chain calls per vault per position. The `morpho_vault_status.ts` helper already does
some of this — extend it to also return `collateralToken` + `oracle` per market.

Alternatively: scrape `api.morpho.org/graphql` → `vault.markets[].market.collateralAsset.address`
and `vault.markets[].market.oracleAddress` — saves RPC calls.

---

## Current Positions Needing Coverage

| Pool | Chain | Collateral at risk | Oracle type |
|---|---|---|---|
| ExtraFi XLend USDC | Base | CLOSED | n/a |
| Morpho sUSDe vaults | Base/ETH | sUSDe, PT_sUSDe | Likely Chainlink/Redstone |
| Maple syrupUSDC | ETH | BTC/ETH/SOL/PT_sUSDe | Internal |
| HLP | Hyperliquid | perp-backed | Internal |

Immediate priority: any vault holding **PT_sUSDe** as collateral → check oracle type before next deposit.

---

## Key Lesson

Don't trust vault APY dashboards to surface risk. Vaults display face-value accounting.
The signal is always **collateral price vs. oracle price divergence** — nothing inside the vault can see this when the oracle is hardcoded. Build external monitoring first.
