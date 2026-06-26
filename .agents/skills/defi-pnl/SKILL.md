---
name: defi-pnl
description: >
  Compute a wallet's REALIZED stablecoin/LP yield over a chosen trailing timespan (1Y, 2Y, or
  custom) across ALL DeFi protocols by tracing on-chain ERC-20 receipt-token cash flows — the
  historical/realized counterpart to defi-portfolio-manager (which reads current state and forward
  APY, not realized history). Use when asked "what yield did I get last year", "1Y or 2Y realized
  PnL", "how much did my stablecoins actually earn", "realized DeFi yield over a timespan",
  "PnL trace across protocols", "how much did Beefy/Aero/Curve actually return", or "compare my
  DeFi yield to T-bills". Recommend-only; the investor reviews and acts. Educational, not financial
  advice. Scope: stablecoin/LP positions only — directional ETH/BTC FX exposure is out of scope.
compatibility: opencode
metadata:
  author: engineer
  version: "1.0"
---

# DeFi Realized PnL Tracer

You are a **DeFi realized-PnL tracer** that computes a wallet's realized stablecoin/LP yield over
a chosen timespan across ALL protocols by tracing on-chain ERC-20 receipt-token cash flows.

---

## When to use

Load this skill when the user asks any of:

- "What yield did I get last year / 2Y?"
- "1Y or 2Y realized PnL on my DeFi positions"
- "How much did my stablecoins actually earn?"
- "Realized DeFi yield over a timespan / PnL trace across protocols"
- "How much did Beefy / Aero / Curve actually return?"
- "Compare my DeFi yield to T-bills"
- "What is my actual DeFi return, not just APY?"

---

## Data-source split — READ THIS FIRST

`PnL = Withdrawn + CurrentValue − Deposited` has two legs served by different sources.

### Leg 1 — Current open-position value (ALL protocols)
Use **DeBank web UI** via the `chrome-use` skill: `https://debank.com/profile/<wallet>`.  
DeBank natively aggregates and prices Beefy, Aerodrome/Velodrome, Uniswap V3, Curve, Pendle,
Morpho, and ERC-4626 vaults in one view — you do NOT need per-protocol RPC calls for the current
leg. Use the per-protocol RPC/API in the reference table below only as a ground-truth **fallback**
for impaired or phantom vaults (e.g. a deprecated Beefy vault DeBank still prices at face value
even though the vault is frozen).

**Never call `api.debank.com`** — it is key-gated and forbidden.

### Leg 2 — Historical deposit/withdraw cash-flow basis over the window
Use the **on-chain ERC-20 receipt scan** (`yield_trace.ts` helper). WHY DeBank can't do this:
its web-UI History tab paginates only recent months and cannot reach 2023–2024. This is exactly
what hid a wallet's Aave/Beefy history in a prior session and forced the on-chain scan. The only
place DeBank exposes realized PnL is `api.debank.com`, which is forbidden. (Verified 2026-06-25 on a
live book: the web UI's "Earnings" header read **$0** and the only PnL shown was *unrealized* perp
PnL — there is no realized profit-since-deposit field in the UI, so do not trust "Earnings".)
Conclusion:

> **DeBank = current value. On-chain Blockscout scan = historical cash-flow basis.**

---

## The 6-step method

### Step 1 — Enumerate ALL protocols
Query DeBank current view (via `chrome-use`) AND run the on-chain receipt scan. Never rely on a
single-protocol view — the original mistake was a Morpho-only trace that missed Beefy, Aerodrome,
and Aave positions entirely.

### Step 2 — Per-position dated cash-flow trace
For each receipt token (mooToken, LP token, ERC-4626 share), match each mint/burn to the
stablecoin transfer in the **same tx hash** to build dated entries (cost) and exits (proceeds).
`classifyTransfers()` in `yield_trace.ts` does this.

### Step 3 — Price emission rewards and INCLUDE them
Emission tokens received from gauges, voters, and Merkl distributors (AERO, VELO, CRV, OP,
MORPHO, ARB, CVX, …) ARE the yield for Aerodrome/Velodrome/Curve LPs. Value each at historical
USD via `coins.llama.fi/prices/historical/{ts}/{chain}:{addr}` on its receipt date and add to
realized yield.

**WHY this matters:** dropping emissions silently under-counts LP yield. In a prior session a book
showed only **+$4,819 over 2Y** — implausibly low, because a ~$120k stablecoin book at T-bill rates
(~4.5%) should clear on the order of **~$10k over two years**. That gap between the reported figure
and the risk-free benchmark is the *tell* that emissions were dropped, not proof the book
under-performed. Treat the benchmark as a sanity floor (Step 6), price emissions, then re-judge —
never report LP yield with emissions at $0 unless you have confirmed the vault auto-compounds.
`yield_trace.ts` adds `totalEmissionUsd` (from `priceEmissions()`) to every position's lifetime and
windowed PnL; the Python reference dropped it.

### Step 4 — Window clipping for pre-window positions
For positions opened before the window start, the windowed formula is:

```
windowed_PnL = (proceeds_after + priced_rewards_after + priced_emissions_after + current_value)
             − cost_incurred_after_window_start
             − value_at_window_start
```

`value_at_window_start` = `convertToAssets(balanceOf @ window-start block)` for ERC-4626,
`getPricePerFullShare() × shares` for Beefy, or a DeBank snapshot. If the archive RPC returns $0
for a provably-open position, set `archiveSuspect: true` and flag — never silently zero the basis
(that inflates windowed PnL). `positionPnL()` in `yield_trace.ts` implements this.

### Step 5 — Separate principal losses from yield
Book impairments (depegs, hacks, frozen oracles) **separately**; never net a loss into yield.

<example>
Wallet lost $4,884 in USR/ExtraFi depeg. The DeFi yield trace books:
  Realized yield: +$6,200 (Beefy auto-compound + Aero emissions priced + Curve CRV)
  Principal losses: −$4,884 (USR depeg, booked separately)
  Net: +$1,316
Reporting only net would make the yield strategy look worse than it is.
Also flag any deprecated vault whose convertToAssets still reads face value — mark it
[PHANTOM VALUE — verify vault status].
</example>

### Step 6 — Reconcile top-down
Compute time-weighted average deployed stablecoin balance × benchmark APY (4.5% T-bill floor)
and compare to the bottom-up trace. If `bottom-up < ~80% of benchmark`, treat it as a probable
under-count and investigate: missed emissions, archive-RPC basis failures, missed positions.
`reconcile()` in `yield_trace.ts` does this and sets `underCountFlag: true` when `ratio < 0.8`.

<example>
reconcile() result:
  bottomUp:   $5,100   (realized — sum of all positionPnL.windowed)
  benchmark:  $6,200   (TWAB $92k × 4.5% × 1.5y)
  ratio:      0.82     → passes (≥ 0.8)
  underCountFlag: false
If ratio were 0.48 → investigate: likely AERO/VELO emissions not priced, or a position missed.
</example>

---

## Run the helper

```bash
# Full trace (all chains)
bun .agents/skills/defi-pnl/scripts/yield_trace.ts <0x-wallet> [--chains base,ethereum,arbitrum,optimism] [--window 1y|2y]

# Output: per-position lifetime PnL + 1Y/2Y windowed PnL, emissionUsd, archiveSuspect flags,
#         reconcile() verdict (ratio, underCountFlag, TWAB, benchmark).

# Run tests (pure functions only — no network)
bun test .agents/skills/defi-pnl/scripts/yield_trace.test.ts
```

The helper's exported pure functions (safe to unit-test without network):
- `classifyTransfers(transfers, wallet, receiptToken, stablesMap)` — entry/exit/stableReward/emission classification
- `positionPnL({entries, exits, stableRewards, pricedEmissions, currentValue, windowTs, basisAtWindow})` — lifetime + windowed PnL
- `clipWindow(items, windowTs)` — filter to window
- `reconcile(positions[], benchmarkApy?)` — TWAB × benchmark sanity check
- `stableUsd(addrLower, rawValue, decimals, stablesMap)` — stable amount → USD

<example>
Pricing an AERO emission (Step 3 in code):
  // Emission: 1,240 AERO received 2024-09-15, addr=0x940181a94A35A4569E4529A3CDfB74e38FD98631
  const ts = 1726358400; // 2024-09-15 unix
  const priceResp = await fetch(
    `https://coins.llama.fi/prices/historical/${ts}/base:0x940181a94A35A4569E4529A3CDfB74e38FD98631`
  );
  const aeroPrice = priceResp.coins["base:0x940..."].price; // e.g. $1.42
  const emissionUsd = 1240 * 1.42; // $1,760.80 → add to realized yield
</example>

---

## Protocol valuation reference

Use DeBank for current value; use this table as fallback/ground-truth for impaired vaults.

**Working keyless archive RPCs (drpc.org returned 400/500 for archive `eth_call` — do not use):**

| Chain | RPC | Blockscout |
|---|---|---|
| Base | `https://mainnet.base.org` | `https://base.blockscout.com/api` |
| Ethereum | `https://eth.llamarpc.com` | `https://eth.blockscout.com/api` |
| Arbitrum | `https://arb1.arbitrum.io/rpc` | `https://arbitrum.blockscout.com/api` |
| Optimism | `https://mainnet.optimism.io` | `https://optimism.blockscout.com/api` |

Block by timestamp: `https://coins.llama.fi/block/{chain}/{ts}`  
Blockscout token history: `?module=account&action=tokentx&address=X&sort=asc`

| Protocol | Position type | Current-value source (keyless) | Gotcha |
|---|---|---|---|
| **Beefy** | ERC-20 `mooToken` | `api.beefy.finance/vaults/{chain}` — `pricePerFullShare` (÷1e18) embedded; LP price from `/lps` | Auto-compounds — no separate reward token; PPFS growth IS the yield. `status: "eol"` = deprecated, PPFS may be frozen. |
| **Aerodrome / Velodrome** | ERC-20 LP + optional gauge | RPC only (`api.aerodrome.finance` DNS dead). `getReserves()` → share fraction × reserve prices | Check **both** `lpToken.balanceOf` and `gauge.balanceOf` — staked LP is held by gauge. AERO/VELO emissions are separate AND are the primary yield; they are NOT auto-compounded unless Beefy wraps the position. |
| **Uniswap V3** | NFT from `NonfungiblePositionManager` | RPC: `positions(tokenId)` + tick math + `slot0()` sqrtPriceX96 | Out-of-range earns zero fees (effectively a limit order). `tokensOwed0/1` = claimable fees now; accruing fees need `feeGrowthInside` delta. Negative ticks need sign extension. |
| **Curve** | ERC-20 LP + optional gauge | `api.curve.finance/api/getPools/{network}/{type}` → `virtualPrice` (÷1e18). **Not** `api.curve.fi` (301 dead) | Tricrypto pools: `virtualPrice` is NOT USD — multiply by cheapest token price. Convex staking: LP may be in Convex booster, not Curve gauge. CRV rewards tracked separately. |
| **Pendle** | PT / YT / LP (PLP) | `api-v2.pendle.finance/core/v1/{chainId}/markets` → PT/YT/LP price USD. No user-positions endpoint (404) — track via Blockscout `balanceOf` | PT discount is NOT a loss — redeems 1:1 at maturity. YT decays to $0 at expiry. PENDLE gauge rewards not in `lp_price_usd`. |
| **ERC-4626** (Morpho, Yearn, Maple…) | Vault shares | RPC: `totalAssets() / totalSupply()` = `pricePerShare`; `currentValue = balanceOf × pricePerShare` | Oracle freeze risk: deprecated vault's `convertToAssets` may still read face value while real value ≈ $0 (see USR/ExtraFi). Always check vault is not deprecated before trusting the number. |

Key selectors (for fallback RPC calls):

```
ERC-20:    balanceOf(address)         0x70a08231   totalSupply()       0x18160ddd   decimals() 0x313ce567
ERC-4626:  totalAssets()              0x01e1d114   convertToAssets()   0x07a2d13a
Beefy:     getPricePerFullShare()     0x77c7b8fc
Curve:     get_virtual_price()        0xbb7b8b80
UniV3 PM:  positions(tokenId)         0x99fbab88   tokenOfOwnerByIndex 0x2f745c59
UniV3 Pool: slot0()                   0x3850c7bd
Aerodrome: getReserves()              0x0902f1ac   earned(address)     0x008cc262
```

---

## Caveats

- **Emissions are the #1 leak.** For Aerodrome/Velodrome/Curve LPs, AERO/VELO/CRV rewards are the
  bulk of yield — if unpriced they can halve the reported return. `yield_trace.ts` prices them;
  never skip this.
- **Emission under-count is still possible** even with the helper if a reward was claimed and
  immediately swapped to a non-stable in a tx the scan cannot match to the original position.
  State this honestly; flag `unmatched: true` entries.
- **Never silently zero an open position's basis.** If archive RPC returns $0 for a position you
  can verify is open (from DeBank current view), set `archiveSuspect: true` and investigate.
- **Book principal losses separately.** Depeg losses, hacks, and frozen-oracle phantom values are
  NOT yield — netting them in makes the strategy look worse than it is and obscures the actual
  protocol performance.
- **Enumerate ALL protocols.** A single-protocol trace is almost always incomplete. Run DeBank
  current view AND the receipt-token scan in parallel before drawing conclusions.

---

## Done when

- [ ] All protocols enumerated from both DeBank (current view) and on-chain receipt scan
- [ ] Each position has dated entries + exits with stablecoin matching
- [ ] Emission tokens priced at historical USD and included in yield
- [ ] Principal losses booked separately from yield
- [ ] `archiveSuspect` flags resolved or documented
- [ ] `reconcile()` ratio ≥ 0.8, OR the gap is explained (missed emissions, archive failure, open
      position with no basis yet)
- [ ] Numbers net of gas/costs
- [ ] Output is recommend-only; investor reviews before acting
