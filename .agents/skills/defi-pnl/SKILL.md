---
name: defi-pnl
description: >
  Compute realized stablecoin/LP yield for a wallet via two-stage wallet-boundary pipeline.
  Use when asked: "what yield did I get last year", "1Y realized PnL", "how much did my
  stablecoins actually earn", "realized DeFi yield over a timespan", "PnL trace across
  protocols", "how much did Beefy/Aero/Curve actually return". Recommend-only; investor
  reviews and acts. Scope: stablecoin/LP positions only.
compatibility: opencode
metadata:
  author: engineer
  version: "2.0"
---

# DeFi Realized PnL — Wallet-Boundary Method

Computes realized stablecoin/LP yield via a two-stage wallet-boundary pipeline. Stage 1
builds a flat transfer ledger; Stage 2 computes boundary PnL from that ledger.
Rotation bug fix: intra-wallet stable rotations (vault A → stable → vault B) net to zero
because they stay inside the wallet boundary and never cross external counterparties.

---

## Two-Stage Pipeline

### Stage 1 — Build transfer ledger

```bash
bun yield_trace.ts <wallet> --ledger [--chains base,ethereum,arbitrum,optimism] --out <ledger.json>
```

Outputs a flat JSON fact table (`rows[]`). Each row is one ERC-20 transfer:
- `direction` ("in"/"out" relative to wallet), `counterparty`, `amountFloat`, `usd`
- `isStable` (true if token in built-in stables map), `symbol`, `tokenAddr`, `chain`
- `counterpartyIsContract` (bool, resolved via Blockscout v2 `/api/v2/addresses/{addr}`)

Spam tokens appear in ledger with `usd` ≈ null/zero (SPAM_REGEX match). No filtering at
this stage — the judgment layer in Stage 2 decides relevance.

### Stage 2 — Compute boundary PnL

**Single-wallet (original) mode:**
```bash
bun boundary_pnl.ts <ledger.json> --window 1y [--out <report.json>]
```

**Cluster mode — canonical for a connected multi-wallet book:**
```bash
bun boundary_pnl.ts --cluster <ledgerA.json> <ledgerB.json> ... [--window 1y] [--out file]
```

Cluster mode treats all listed wallets as ONE entity. Inter-wallet transfers net to zero
(symmetric pairs cancel in `computeClusterCapitalFlows`); only flows crossing the whole-cluster
boundary count. Correct for a book where 5 wallets forward stablecoins between each other —
per-wallet mode would show capital leaving one wallet as a fake loss. Use `--cluster` with all
owned wallets for any connected book.

Single-wallet mode is only correct for a wallet with zero inter-wallet or external-EOA outflow
activity.

Outputs per-protocol table + JSON. Two headline numbers are always reported:

**(A) Total book stablecoin P&L** (`anchor` / `trailing_1y.pnl_1y_anchor`) — conserves
(Δ≈$0 after Unattributed row); includes all yield, principal changes, and residuals.

**(B) DeFi LP/stablecoin yield only** (`trailing_1y.pnl_1y`, apportioned) — excludes:
- `Perps` row: on-chain perps/derivatives DEX P&L (ZkLighter)
- `Bridge` row: cross-chain bridge legs (capital movements, not yield)
- `Unidentified` row: inflows that cannot be positively tied to a stablecoin/LP yield source
  (conservative lower bound; shown as flagged line, never counted on faith)
- Principal losses (depegs) booked in protocol row `lifePnL`, not netted into yield headline

Other JSON fields:
- `delta_vs_anchor` — gap between per-protocol sum and anchor (target: ≈$0 after residual)
- `protocols[]` — per-protocol rows: `lifePnL`, `pnl1y`, `pnl1y_facebasis`, `curVal`, `flags`
- `trailing_1y.pnl_1y_anchor` — independent 1Y anchor
- `idle_rpc` / `idle_flow` — idle stable cross-check (RPC vs ledger-net)

---

## Wallet-Boundary Model

### Lifetime anchor formula

```
anchorComputed = currentValueTotal + capitalOut − capitalIn

where:
  currentValueTotal = idleRpc + Σ vault curVal + directionalCurVal
  capitalIn         = cexIn + ownedIn        (stables IN from external EOAs + owned wallets)
  capitalOut        = ownedOut + bridgeOut   (stables OUT to owned wallets + bridges)
```

Per-protocol: `lifePnL = proceedsOut + curVal − costIn`

Per-protocol rows must sum to `anchorComputed`. Residual is exposed as explicit
"Unattributed" row — never a silent bucket.

### Why rotations net to zero

A rotation (stable → vault A entry → vault A redemption → stable → vault B entry) records
costIn for vault A and costIn for vault B, but also proceedsOut for vault A's redemption.
Since the stable never crosses the wallet boundary to an external counterparty, it never
appears in `capitalIn`/`capitalOut`. Attribution handles it correctly: the vault A
proceedsOut cancels its costIn inside the boundary.

### Counterparty classification (`classifyCounterparty` — first-match wins)

1. addr in `OWNED_WALLETS` set → `"owned"`
2. addr in `KNOWN_BRIDGES` set → `"bridge"`
3. Blockscout name cache matches `BRIDGE_NAME_REGEX` (`bridge|stargate|hop|across|synapse|…`) → `"bridge"`
4. stable goes OUT to addr AND no non-stable receipt token returns in same tx → `"bridge"`
5. `counterpartyIsContract === true` → `"internal"` (protocol contract)
6. `counterpartyIsContract === false` → `"external_eoa"` (CEX or personal EOA)
7. default → `"internal"`

Classification is data-driven from the ledger's `counterpartyIsContract` field. No CEX
address is hardcoded — any EOA (personal wallet, exchange) that sends stables in falls into
`external_eoa`, which flows into `cexIn` / `capitalIn`.

---

## RPC Sanity Guard

Every `balanceOf` / valuation call retries with exponential backoff (3 attempts: 500ms/1s/2s).

After computing idle stable value, the skill cross-checks live RPC total (`idle_rpc`) against
ledger-derived estimate (`idle_flow`). If they diverge beyond `max($500, 3% of idle_flow)` after
one retry pass, the skill **throws and exits non-zero** rather than emitting a wrong number:

```
RPC current-value read failed: idle_rpc=$X vs idle_flow=$Y (diff $Z exceeds tolerance $T)
— refusing to emit a PnL number
```

Reliability guarantee: the skill prints a correct number or errors loudly — it never silently
emits a fictional figure when RPC reads fail. (Implemented in `assertIdleRpcSanity`, called in
`computeBoundaryPnL` and in cluster mode main().)

---

## Conservative Current-Value Rule

This is load-bearing. Fabricating values for unidentified tokens inflates PnL with fictional
numbers (e.g., a governance token priced via market API can "inflate Other by tens of millions").

| Asset type | Valuation method |
|---|---|
| Idle stablecoins | Face value ($1/token) via on-chain `balanceOf` ÷ decimals |
| ERC-4626 vault shares | `convertToAssets(balanceOf)` via live RPC |
| ERC-4626 fallback (no `convertToAssets`) | `totalAssets / totalSupply × balanceOf` via RPC |
| Unidentified non-stable tokens | **$0** — flagged `"unvalued:N(SYM1,SYM2…)"` in `flags` |

LlamaFi historical price fallback is **intentionally removed** from `receiptValueUsd()`:

```typescript
// NOTE: LlamaFi price fallback intentionally removed.
// Pricing non-stable receipt tokens via external price feeds produces fictional values
// (e.g., governance tokens priced at market rate inflate "Other" by tens of millions).
// Tokens that do not expose ERC-4626 on-chain redemption value contribute $0.
// They are tracked in the protocol row's flags as "unvalued:N(SYM1,SYM2…)".
return { value: 0, method: "unpriced" };
```

Flagged tokens appear in the row's `flags` as `unvalued:2(TOKEN1,TOKEN2)`. These are real
holdings excluded from PnL — not fabricated as zero yield. The output must say so explicitly.

---

## Self-Validation / Proof

### Conservation anchor check

```
1. anchorComputed = currentValueTotal + capitalOut − capitalIn  (independent path)
2. sumPnL_preResidual = Σ protocolRows.lifePnL
3. lifeResidual = anchorComputed − sumPnL_preResidual
4. if |lifeResidual| > $0.01 → push explicit "Unattributed" row with lifePnL = lifeResidual
5. After residual: Σ lifePnL ≈ anchorComputed within $1
```

Same check for 1Y: `delta_1y = Σ pnl1y_facebasis (excl. Directional) − pnl_1y_anchor`.
Must be ≈$0 after residual row. The table total always equals the anchor — no hidden buckets.

### 30-test eval harness — deterministic and offline

```bash
bun test ./.agents/skills/defi-pnl/scripts/boundary_pnl.test.ts
```

All 30 tests run offline (injectable `balanceProvider` stub) and complete in < 1 second — no
network. The stub makes async tests deterministic: they validate accounting logic given correct
current-values; the runtime RPC guard (#2 above) protects the live-RPC integration path.

Tests assert:

| # | Group | What it checks |
|---|---|---|
| 1–7 | `classifyCounterparty` (7 tests) | owned→owned; CEX EOA (data-driven, `counterpartyIsContract=false`) →external_eoa; known bridge→bridge; unknown+isContract=true→internal; unknown+isContract=false→external_eoa; Blockscout name→bridge; default→internal |
| 8 | idle USDC cross-check | ledger net USDC on Base ≈ $44,637 ± $5; matches `CURRENT_VALUES.idle_usdc_base` |
| 9 | spam → $0 | all rows matching `SPAM_REGEX` sum to < $1 USD total |
| 10–11 | bridge classification (2 tests) | all `KNOWN_BRIDGES` addresses → "bridge"; bridge stable outflows ≈ $30,305 ± $50 |
| 12 | lifetime conservation (offline stub) | `|delta_vs_anchor| < $250` |
| 13 | 1Y conservation (offline stub) | `|delta_1y| < $250`; `|pnl_1y| < $30,000` |
| 14–15 | `isStableRow` (2 tests) | EUSD (`isStable=false`) counts as stable via `STABLE_OVERRIDE_ADDRS`; genuine USDC counts as stable |
| 16 | `detectProtocol` | MEUSD → Morpho |
| 17–20 | `computeApportionFraction` (4 tests) | fully pre-window → 0; fully post-window → 1; 50/50 straddle → ≈0.5; `NOW` constant = 1782432000 |
| 21 | apportionment bounds (offline stub) | per-protocol `pnl1y ≤ lifePnL + $1`; total 1Y apportioned in $9k–$13k band |
| 22 | attribution reconciliation (offline stub) | `|Σ lifePnL − anchor| < $1`; `|Σ pnl1y_facebasis − 1Y anchor| < $1` |
| 23–25 | cluster capital flows (3 tests) | inter-wallet transfer → capitalIn=0, capitalOut=0; external-EOA outflow counted as capital-out; external-EOA inflow counted as capital-in |
| 26 | attribution reconciliation offline | Σ protocol rows === anchor ±$1 |
| 27–30 | RPC sanity guard (4 tests) | `assertIdleRpcSanity` throws `"refusing to emit a PnL number"` on divergent idle_rpc; passes within 3%; passes when both small and diff < $500; throws when diff > 3% for large values |

---

## Honest Limitations

- **Large "Unvalued" flags**: wallets with significant unvalued non-stable holdings cannot
  produce a trustworthy full PnL without per-protocol RPC valuation. State explicitly per
  wallet: "Unvalued holdings: N tokens (SYM1,SYM2…) excluded; true value unknown. Figure
  is a lower bound on PnL."
- **Trailing 1Y is a linear-accrual model**: `pnl_1y = lifePnL × fraction_of_hold_in_window`.
  This is an estimate, not hard-measured. `pnl_1y_anchor` is the independent bound;
  `pnl_1y_facebasis` is the upper bound (pre-window yield can leak in). Use `pnl_1y` as
  headline with this caveat stated.
- **Directional ETH excluded**: stETH/cbETH/wstETH appear in a "Directional" protocol row
  with `curVal=$0`. Computing requires an ETH price feed + per-wallet RPC balance — omitted
  to prevent cross-wallet value leakage. Report separately if needed.
- **Hyperliquid excluded** from stablecoin-yield scope.
- **Bridges-out = par withdrawals**: bridge outflows are valued at ledger USD (face value for
  stables). If cross-chain principal was lost after bridging, the loss is invisible here.

---

## Protocol Valuation Reference

Use Stage 2 RPC for current value. Use this table as fallback/ground-truth for impaired
vaults or when Stage 2 returns $0 for a provably-open position.

**Never call `api.debank.com`** — it is key-gated and forbidden.

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

## Done When

- [ ] Ledger built and untruncated (all chains, all transfers)
- [ ] Connected book: used `--cluster` with all owned wallets (single-wallet mode only for isolated wallets)
- [ ] `delta_vs_anchor ≈ $0` — run conserves (Δ≈$0 after Unattributed row)
- [ ] Per-protocol `lifePnL` sums to anchor within $1 (after Unattributed row)
- [ ] `delta_1y ≈ $0` (face-basis 1Y attribution ≈ independent 1Y anchor)
- [ ] RPC guard active — no silent fiction: if idle_rpc/idle_flow diverge beyond tolerance, run threw and was fixed before reporting
- [ ] Yield/non-yield split reported: Perps, Bridge, Unidentified rows present and excluded from yield headline
- [ ] Unidentified inflows excluded (conservative lower bound), not fabricated or counted on faith
- [ ] Unvalued positions flagged in `flags`, not fabricated into PnL
- [ ] Per-wallet trustworthiness statement in output: unvalued holdings named, or "all
      positions valued — figure is trustworthy"
- [ ] Eval green: `bun test ./.agents/skills/defi-pnl/scripts/boundary_pnl.test.ts` passes all 30 (deterministic, offline, < 1s)
