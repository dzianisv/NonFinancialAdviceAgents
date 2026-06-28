# Stablecoin / LP vault cost-basis reconstruction
Source: Blockscout (base + eth) keyless API + DefiLlama prices. Date: 2026-06-25.
Current USD = user-provided (portfolio snapshot, authoritative). Deposited USD = on-chain underlying traced.

| Position | Wallet | Chain | Share token (addr) | Deposited USD | Current USD | PnL USD | First deposit | Proof (blockscout) |
|---|---|---|---|---:|---:|---:|---|---|
| Maple syrupUSDC | L3 | eth | 0x80ac24aA929eaF5013f6436cdA2a7ba190f5Cc0b | 9,005.84 | 9,217.39 | +211.55 | 2026-01-03 | https://eth.blockscout.com/tx/0xab203f86f92622b70c060d46283f3597f3a73a05d7c31e86548fcd247c63f03e |
| Maple syrupUSDC | B3 | eth | 0x80ac24aA929eaF5013f6436cdA2a7ba190f5Cc0b | 8,223.10 | 8,465.33 | +242.23 | 2025-11-01 | https://eth.blockscout.com/tx/0xc40443e3b9c3e645346cd9360b7ee452055c217e3670168814e4722e3e6a4830 |
| Fluid fUSDT | B3 | eth | 0x5C20B550819128074FD538Edf79791733ccEdd18 | 15,633.00 | 15,608.28 | -24.72 | 2026-06-25 | https://eth.blockscout.com/tx/0x8596df192ffa0fe0a2bdb5995d4d32d9aaeda94f346a99172dc3b81d4c2fd3c2 |
| Avantis Jr Tranche USDC | B3 | base | 0x944766f715b51967E56aFdE5f0Aa76cEaCc9E7f9 | 1,000.00 | 1,042.20 | +42.20 | 2025-10-24 | https://base.blockscout.com/tx/0x7bc7374fde32faf0cb136e2a995bee1296db304f7ffe345d83f684a71852d196 |
| sUSDe (Ethena) | L3 | eth | 0x9D39A5DE30e57443BfF2A8307A4256c8797A3497 | 2,886.63 | 2,938.41 | +51.78 | 2026-01-04 | https://eth.blockscout.com/tx/0xb1b0e72cc3d617be4fb4202fd24761ff6996a879a92f9869dcfc0f38c79eff53 |
| eUSD idle (ex-Morpho meUSD) | L3 | base | eUSD 0xCfa3Ef…99FB4 (was meUSD 0xbb819D…f313) | 6,070.76 | 6,356.35 | +285.59 | 2025-02-14 | dep https://base.blockscout.com/tx/0x7e8053f9b704b32baf64de1944a4133f239baf1df1be3b5dc4001f2bcea6c40d · redeem https://base.blockscout.com/tx/0xd8c114842d5749408b188e439bc9dc89a51d3cfd824b6463696ce02e7d916a20 |
| eUSD idle (ex-Morpho meUSD) | L1 | base | eUSD 0xCfa3Ef…99FB4 (was meUSD 0xbb819D…f313) | 2,805.97 | 2,841.90 | +35.93 | 2025-09-12 | dep https://base.blockscout.com/tx/0x727a057a0c6b6869273cd3be533bb85c4744ceaa0e92a5daf995da16ef9e7209 · redeem https://base.blockscout.com/tx/0x5eb2a33ca6c7fd6491e320fa7311d56f7ddd8dbb74d47eef2fe3143127c20397 |
| **TOTAL** | | | | **45,625.30** | **46,469.86** | **+844.56** | | |

## Caveats
1. **All cost bases are in stablecoin face value ≈ USD** (DefiLlama spot: USDC=$1.00, USDT=$0.999, USDe=$0.998, eUSD=$1.0003). sUSDe basis is the 2,886.63 USDe paid; eUSD bases are the eUSD supplied to the vault. True original USD (e.g. USDC used to mint USDe/eUSD) is not traced further back since these are $1 pegs.
2. **eUSD idle = redeemed Morpho eUSD (meUSD) vault, exited TODAY 2026-06-25.** L3 redeemed 6,208.99 eUSD (tx 0xd8c11484…), L1 redeemed 2,842.02 eUSD (tx 0x5eb2a33c…). "Deposited USD" shown is the original eUSD supplied to the MetaMorpho vault (true capital); the wallet's idle eUSD now = face value received via redemption. Blockscout `/tokens` still shows stale meUSD balances (cache lag) — token-transfers confirm the redeem succeeded.
3. **L3 eUSD discrepancy:** on-chain redeemed value ≈ $6,211 vs user snapshot $6,356.35 (~$145 gap, source-price/timing). Using on-chain redeemed amount, realized vault yield = 6,208.99 − 6,070.76 = **+138.23 eUSD**. L1 reconciles exactly (2,842.02 redeemed vs $2,841.90).
4. fUSDT deposited 15,633 USDT TODAY — PnL ≈ flat (−$24.72 is entry slippage/peg, not loss). No partial withdrawals on any vault position (share_out=0 for syrupUSDC/fUSDT/avUSDC/sUSDe).
