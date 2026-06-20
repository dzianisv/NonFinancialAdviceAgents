---
name: overview-crypto-portfolio
description: >
  Scan all DeFi yielding positions across configured wallet addresses using
  chrome-use + DeBank (no API key required). Extracts protocol positions
  (Morpho, Maple Syrup, Aave, Ethena, LIDO, Hyperliquid, Uniswap LP, etc.)
  with asset, balance, and USD value per wallet. Produces a cross-wallet
  summary sorted by size and a decision matrix comparing each position's APY
  against a BTC rotation opportunity. Use when asked to "review my DeFi
  positions", "scan my wallets", "check my yield", "what should I rotate to
  BTC", or "overview my crypto portfolio".
---

<role>
DeFi portfolio analyst. Scan all configured wallets via DeBank in Chrome.
Extract every yield-bearing position. Produce a rotation decision matrix.
No fabrication — mark [UNAVAILABLE] for anything you cannot read.
</role>

<goal>
For each wallet in WALLETS below: open the DeBank profile in Chrome, extract
total USD value and all protocol positions (protocol, type, asset, balance,
USD), then build a cross-wallet decision matrix comparing each position's APY
to the active BTC entry signal to identify rotation candidates.
</goal>

## Wallets (defaults — override via ARGUMENTS)

```
L1: 0x5c1b7a3ab7797e237cc9ec1e30a18048c364174a
L3: 0x5d039ece117073323ade5057a516864f4c40e653
B1: 0x9945Ba0a781200B90b4c28528cced309aBB90871
B3: 0xd6b5587944a2bf537ef9cf04695ed093f4805e75
B5: 0xaefdc2b58f5a15b6e5e3d6d7ac707c76967ab4ae
```

If ARGUMENTS contains wallet addresses (e.g. `wallet=0x...`), use those instead.

## Fetch procedure

<constraints>
- Use chrome-use ONLY. DeBank's v1 API returns 404. Etherscan/Ankr require paid keys. publicnode.com free RPC returns raw token balances only — it misses ALL protocol positions. Chrome + DeBank is the only reliable no-key path.
- Never fabricate balances or APYs. Mark [UNAVAILABLE] if a page fails to load.
- Parallel subagents CANNOT share chrome-use — all subagents share one proxy → one active-tab pointer → race conditions. Must be sequential reads but can pre-load tabs in parallel.
</constraints>

```bash
CHROME=/Users/engineer/.claude/skills/chrome-use/scripts/chrome-use
```

### Tab-preload strategy (~15s total vs ~40s sequential)

Open all wallet tabs first (fast, no wait), then read each — tabs finish loading in parallel while you open the next one.

**Step 1 — open all tabs (no sleep between opens):**

```bash
$CHROME open "https://debank.com/profile/0x5c1b7a3ab7797e237cc9ec1e30a18048c364174a"  # L1 → tab t_L1
$CHROME tab new "https://debank.com/profile/0x5d039ece117073323ade5057a516864f4c40e653"  # L3 → tab t_L3
$CHROME tab new "https://debank.com/profile/0x9945Ba0a781200B90b4c28528cced309aBB90871"  # B1 → tab t_B1
$CHROME tab new "https://debank.com/profile/0xd6b5587944a2bf537ef9cf04695ed093f4805e75"  # B3 → tab t_B3
$CHROME tab new "https://debank.com/profile/0xaefdc2b58f5a15b6e5e3d6d7ac707c76967ab4ae"  # B5 → tab t_B5

# Single wait after all tabs opened — React app + protocol data loads in parallel
sleep 8
```

**Step 2 — read each tab sequentially (note the tab ID from `$CHROME tab` output):**

```bash
$CHROME tab <t_L1>
$CHROME eval "document.body.innerText" 2>&1   # L1 data

$CHROME tab <t_L3>
$CHROME eval "document.body.innerText" 2>&1   # L3 data

$CHROME tab <t_B1>
$CHROME eval "document.body.innerText" 2>&1   # B1 data

$CHROME tab <t_B3>
$CHROME eval "document.body.innerText" 2>&1   # B3 data

$CHROME tab <t_B5>
$CHROME eval "document.body.innerText" 2>&1   # B5 data
```

**If a tab's innerText is empty or only shows tokens (popup fully blocking):** switch to that tab, reload, sleep 4, re-eval. The Rabby popup renders slower than page content — a reload usually clears it.

**Popup workaround:** DeBank shows a Rabby Wallet promo popup that blocks the protocol section in screenshots and `get text body`. The `eval "document.body.innerText"` call reads the full DOM including content below the popup — use eval, never `get text body`.

**Parse the text output:** DeBank renders protocol positions in this pattern:
```
<Protocol Name>
$<USD total>
<Type: Yield | Staked | Deposit | Liquidity Pool | Rewards | Perpetuals>
Pool       Balance          USD Value
<Pool name>
<Asset>    <amount> <asset>  $<value>
```

Extract: protocol name, position type, pool name, asset(s), balance, USD value.
Chain breakdown (e.g. "Base $56,177 79%") appears above the wallet token list.

## Output format

<output_format>

### Per-wallet table (one per wallet)

```
WALLET L3 — $87,299  (0x5d03...e653)
Protocol        Type      Pool                    Asset      Balance       USD
Morpho          Yield     Seamless USDC Vault     USDC       29,342        $29,366
Morpho          Yield     Extrafi XLend USDC      USDC       10,224        $10,232
Morpho          Yield     Universal USDC          USDC       10,178        $10,186
Morpho          Yield     eUSD                    eUSD        6,206         $6,204
Maple           Yield     Syrup USDC              USDC        9,200         $9,207
Ethena          Staked    sUSDe                   USDe        2,938         $2,938
LIDO            Staked    stETH                   ETH         1.41          $2,442
Hyperliquid     Deposit   Spot                    HYPE+USOL  —            $10,421
Hyperliquid     Yield     Vaults                  USDC        5,340         $5,340
Merkl           Rewards   —                       SEAM+misc  —               $189
Wallet tokens   —         —                       cbETH/ETH  —               $243
```

### Cross-wallet summary (all positions, sorted by USD desc)

```
TOTAL PORTFOLIO: $XXX,XXX across N wallets

Rank  Wallet  Protocol         Asset   USD        APY (est)
1     L3      Morpho Seamless  USDC    $29,366    ~7-9%
2     B3      Idle USDT        USDT    $15,616    0%
...
```

### Decision matrix

For each stablecoin/yield position compare APY to BTC opportunity:

```
Position                Wallet  USD       APY     BTC 12m opp-cost*   Verdict
Idle USDT               B3      $15,616   0%      ~$17,646            ROTATE → BTC
Maple Syrup USDC        B3      $8,456    4.7%    ~$9,555             ROTATE → BTC
Maple Syrup USDC        L3      $9,207    4.7%    ~$10,404            ROTATE → BTC
Morpho Universal USDC   L3      $10,186   ~8%     ~$11,510            ROTATE → BTC
...
LIDO stETH              L3      $2,442    3.5%    ETH yield           HOLD (diff asset class)
```

*BTC opp-cost = position_size × 113% (historical median 12-month return from 200-week MA entries).
Include this note: "BTC opp-cost is the median, not a guarantee. Actual returns depend on entry/exit."

### Rotation summary

```
TOTAL ROTATABLE CAPITAL (ROTATE verdicts): $XX,XXX
First move (idle stables):                 $XX,XXX
Second move (lowest APY):                  $XX,XXX
Gas note: [wallet] has [X] ETH — [sufficient/needs top-up] for mainnet txns.
```

</output_format>

## Live APY fetch (run BEFORE building decision matrix)

**Do not use the static table below as APYs — they drift. Always fetch live first.**

```bash
python3 /Users/engineer/workspace/backtest/.agents/skills/overview-crypto-portfolio/fetch_apys.py
```

This script queries:
- **Morpho Blue** (`blue-api.morpho.org/graphql`) — Seamless / Universal / Extrafi / eUSD vaults
- **DeFiLlama** (`yields.llama.fi/pools`) — Maple Syrup USDC/USDT, LIDO stETH
- **Ethena** (`ethena.fi/api/yields/...`) — sUSDe staking yield

If a vault returns `[UNAVAILABLE]` from the API (Morpho returning 0%, or blocked endpoints), mark its APY as `[VERIFY LIVE]` in the decision matrix rather than guessing.

**Live APY snapshot (2026-06-20 — re-run script for current):**

| Protocol / Pool | Live APY | Source |
|---|---|---|
| Morpho Seamless USDC (Base) | 4.48% | blue-api.morpho.org |
| Morpho eUSD (Base) | 2.59% | blue-api.morpho.org |
| Morpho Universal USDC (Base) | **0% ⚠️ IDLE** | blue-api.morpho.org (confirmed) |
| ExtraFi XLend USDC (Base) | **1.29%** | yields.llama.fi (extra-finance-xlend) |
| Maple Syrup USDC | 4.82% | yields.llama.fi |
| Maple Syrup USDT | 4.15% | yields.llama.fi |
| Ethena sUSDe | 3.50% | ethena.fi/api |
| LIDO stETH | 2.39% | yields.llama.fi |
| Avantis Junior USDC | **10.25%** | yields.llama.fi |
| Hyperliquid HLP Vault | **0.13%** | api.hyperliquid.xyz |

**Critical: Universal USDC (Base) confirmed 0% APY.** L3 has $10,186 and L1 has $4,295 earning nothing. These are the highest-priority moves after idle USDT.

## BTC entry signal context

Apply the rotation logic when BTC is at or below the 200-week MA:
- **200-week MA** ~$62,237 (June 2026 canonical)
- **MVRV-Z** < 1.0 (accumulation zone)
- **F&G** < 25 (Extreme Fear)
- **Historical median 12-month return** from 200-week MA: ~113%

When the signal is NOT active (BTC well above 200w MA, MVRV-Z > 3, F&G > 60):
change opp-cost column to "N/A — BTC not at entry zone" and skip ROTATE verdicts.

## Done when

- All N wallets scanned (or [UNAVAILABLE] with reason for any failures)
- Per-wallet table complete for each wallet
- Cross-wallet summary table sorted by USD
- Decision matrix with explicit ROTATE/HOLD verdict per position
- Total rotatable capital figure stated
- Gas check: flag any wallet with < 0.003 ETH on mainnet as needing top-up before executing
