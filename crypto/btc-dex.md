# Buying Native BTC on a DEX — Venue & Routing Notes

> Research notes (2026-06-05) for the crypto book. **Educational analysis, not financial advice.**
> Goal answered: *cheapest, lowest-risk way to buy spot BTC for USDT/USDC on a DEX and actually
> withdraw native Bitcoin to self-custody.* Two books stay separate — this is the crypto track
> (`crypto/GOAL.md`), not the $1M tradfi book.

## TL;DR

- **"Spot BTC" on a perps-DEX is a wrapped IOU, not Bitcoin.** Hyperliquid = UBTC, AsterDex = BEP-20 BTC on BNB Chain.
- For a **clean, on-chain, USDT/USDC → native BTC** swap, the right category is a **native cross-chain DEX**: **Chainflip**, THORChain, Maya.
- **THORChain is benched** right now: ~$10–11M vault exploit (May 2026) + US Treasury sanctions on linked addresses.
- **Chainflip is the cleanest native option today** — no wrapper at any step, no fund-draining hack on record, and USDT/BTC is its deepest pair. Caveats: thinner liquidity (slip on size) and a censorable front-end.
- **Cheapest overall is still a low-fee CEX** (MEXC/Kraken) → withdraw native BTC, *if* you accept the exchange touching funds briefly. Pure-DEX = pay slip + gas to avoid any custodian/wrapper.
- **Total cost = fee + spread/slip + withdrawal/bridge + gas.** Headline maker fee is the small part. Always quote the exact amount before sending.

## The venues compared

| Venue | Wrapper? | Native BTC out | Hack history | Depth | Best for |
|---|---|---|---|---|---|
| **Chainflip** | none | yes, direct | clean (no drain) | thin | small–mid USDT→BTC, max trust-minimization |
| **Hyperliquid / Unit (UBTC)** | UBTC, then redeem | yes | clean | deep | larger size, deepest book |
| **THORChain / Maya** | none | yes | ⚠️ May-2026 $10M + sanctions | deepest | AVOID this month |
| **AsterDex** | wrapped BEP-20 on BNB | no (need a bridge) | — | low | cheap fee, but wrong tool for real BTC |
| **CEX (Kraken / MEXC)** | n/a (custodial) | yes | n/a | deepest | cheapest, simplest, brief custody |

### Fees (spot, base tier)
- **AsterDex spot:** 0.005% maker / 0.04% taker (USDT & USDC). Cheapest headline — but "BTC" is a BNB-chain wrapper.
- **Hyperliquid spot:** 0.04% maker / 0.07% taker, quoted natively in USDC.
- **Chainflip:** 0.1% protocol fee + JIT-AMM spread + source-chain gas + BTC outbound miner fee. (0.1% buys & burns FLIP.)
- **THORChain / Maya:** slip-based — ~0.25–0.3% LP fee + variable slip + gas + outbound. Slip dominates on size.
- **CEX:** MEXC ~0% maker / 0.05% taker; Kraken Pro tiered 0–0.25% maker; + a native-BTC withdrawal fee.

## Custody / withdrawal mechanics (the actual risk)

- **AsterDex** — "BTC" is a **BEP-20 wrapped token on BNB Chain**. Self-custody of the *wrapper*, but the withdraw button gives you the BNB-chain token, **not** native BTC. Reaching mainchain BTC needs a *separate bridge* (extra fee + depeg/bridge risk). Wrong tool if the plan is hold real BTC.
- **Hyperliquid (UBTC via Unit protocol)** — trade UBTC; real BTC held 1:1 in **Unit's custody** under a **2-of-3 MPC threshold guardian network** (key never exists whole, ≥2 guardians to move). **Redeem = native BTC** broadcast to your BTC address. You *can* get real Bitcoin out. Trust point = the Unit guardian set; your USDC has to bridge onto Hyperliquid (Arbitrum→HL) first.
- **Chainflip** — fully native, **no wrapper at any step**. See below.
- **THORChain / Maya** — native, threshold-signed vaults, output is native BTC directly. But see the May-2026 exploit + sanctions.

## Chainflip deep dive

**What:** native cross-chain swap protocol. USDT/USDC → native BTC to your own Bitcoin address, no wrapped token, no bridge IOU. Internal settlement asset is **USDC** (every swap routes `asset → USDC → asset`).

**Architecture**
- **State Chain** — own Substrate proof-of-stake chain; does accounting/consensus; coins never live here.
- **Vaults** — real BTC/ETH/etc. in addresses controlled by the validator set via **threshold signatures (TSS)**, re-keyed as validators churn.
- **150 validators**, each **stakes FLIP**; permissionless entry; **slashing** for signing conflicting txs, going offline mid-ceremony, or dishonest key-gen. Security = cost-to-corrupt-a-threshold > extractable value.
- **JIT AMM** — Uniswap-v3-style in Rust; LPs quote *just in time* at swap moment and front-run *each other* to give the user a tighter price (flips MEV in the user's favor).
- **Timing:** ETH/SOL/Arbitrum legs ~2–5 min; **BTC needs 3 confirmations → ~10–30 min**.

**Security record**
- **No vault hack / no drained-funds exploit** — the key contrast with THORChain (same TSS-vault *category*, but Chainflip not exploited).
- **Bybit-hack response (Feb 2026):** pushed an emergency upgrade to block the $1.4B stolen funds and cut its main front-end. Shows responsiveness **and** that the official UI can censor/filter (a centralization touchpoint — the protocol stays permissionless; run alternate interfaces/SDKs if needed).
- Has been used as a laundering hop (Flow $3.9M, Bybit attempts) → same regulatory-attention risk that got THORChain sanctioned. **Not sanctioned itself** as of 2026-06.

**Liquidity — the real weakness**
- Much smaller than THORChain or a CEX. Fees annualize ~$10M; TVL modest; volume choppy. **Thin depth → slip grows fast on size.** Fine for a few-$k buy; for tens of $k you move the pool. **Quote the exact amount in the UI first** and compare all-in vs a CEX.

## USDT/BTC on Chainflip

- **USDT↔BTC is Chainflip's busiest market:** BTC→USDT ~$52M (15.5% of volume, #1), USDT→BTC ~$48M (#2). Deepest-liquidity path on the protocol.
- **v2.1 added native USDT on Solana & Arbitrum** (was Polkadot-only). USDC live on Ethereum/Solana/Arbitrum/Polkadot; BNB Chain coming.
- Mechanical note: internally USDT→USDC→BTC, so you cross **two pool spreads + 0.1%**, not one.

## Best chain to hold USDT for Chainflip

The chain you hold on = the **deposit-tx gas** you pay to start every swap. Slip/depth is identical across chains (shared BTC pool), so chain choice only moves the **gas + speed** lever.

| Chain | Deposit gas | Speed | Verdict |
|---|---|---|---|
| **Solana** | ~cents | fastest | 🥇 cheapest to initiate (best if funding fresh) |
| **Arbitrum** | a few cents | fast | 🥈 great, EVM, nearly as cheap |
| **Ethereum** | $1–10+ | fine | ❌ L1 gas eats small swaps |
| Polkadot Assethub | low | fine | thinner, skip |

**Recommendation:** hold **Arbitrum USDT** (already cheap; if you have it there, don't move it — an Arbitrum→Solana bridge wipes out the tiny Solana edge). Use **Solana USDT** only when funding fresh and chasing the gas floor. **Don't initiate from Ethereum mainnet** for small/mid size — deposit gas can dwarf the 0.1% fee.

## Decision guide

- **Fully on-chain, self-custody, USDT(Arbitrum)→native BTC, small–mid size** → **Chainflip** (quote slip first).
- **Larger size, want deepest book, OK trusting Unit guardians** → **Hyperliquid (UBTC)**, then redeem to native BTC.
- **Cheapest + simplest, tolerate a brief CEX touch** → **Kraken / MEXC** → withdraw native BTC.
- **THORChain / Maya** → revisit after the May-2026 exploit recovery + sanctions situation settles.
- **AsterDex** → only for cheap *wrapped* exposure / leverage, not for holding real Bitcoin.

## Sources
- Aster spot fees — https://docs.asterdex.com/product/aster-spot/spot-fee-structure
- Aster deposit/withdraw (wrapped BEP-20) — https://docs.asterdex.com/product/aster-spot/deposit-and-withdrawal-guide
- Hyperliquid fees — https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees
- Unit withdraw (native BTC redeem) — https://docs.hyperunit.xyz/how-to/withdraw
- THORChain swap / fees — https://thorchain.org/swap , https://docs.thorchain.org/technical-documentation/technical-deep-dive/fees
- THORChain May-2026 exploit — https://www.cryptotimes.io/2026/05/17/10-8-million-drained-inside-the-thorchain-exploit-that-froze-cross-chain-defi-for-13-hours/
- THORChain exploit across 9 chains (TRM) — https://www.trmlabs.com/resources/blog/thorchain-exploit-drains-usd-11m-across-at-least-nine-chains-what-trm-knows-now
- Chainflip protocol overview — https://docs.chainflip.io/protocol/protocol-overview
- Chainflip JIT AMM — https://docs.chainflip.io/concepts/swaps-amm/just-in-time-amm-protocol
- Chainflip security architecture — https://blog.chainflip.io/chainflip-security-architecture-trustless-swap-protocol/
- Chainflip blocks Bybit hack funds — https://cointelegraph.com/news/chainflip-blocks-bybit-hacker-funds-security-upgrade
- Chainflip v2.1 (USDT on Solana & Arbitrum) — https://blog.chainflip.io/chainflip-v2-1-expanding-bitcoin-and-stablecoin-liquidity/
- Chainflip stablecoin pairs — https://blog.chainflip.io/chainflip-stablecoins-cross-chain-usdc-usdt-swaps/
- Chainflip TVL/fees (DefiLlama) — https://defillama.com/protocol/chainflip

*Educational analysis, not advice; you place the orders.*
