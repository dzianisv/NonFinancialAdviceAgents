I supplied ~$10k USDC into the **Extrafi XLend USDC** vault on Base (a MetaMorpho V1.1 / ERC-4626 vault on Morpho). I treated it as boring USDC lending. Here's what I pieced together on-chain, and where I'm stuck.

**What happened**

- The vault's curator allocated supplier USDC into a Morpho Blue market with **USR (Resolv) as collateral**, USDC as the loan asset, 91.5% LLTV.
- In March 2026, USR depegged (after the exploit) from ~$1 to ~$0.17. Borrowers who had posted USR walked away.
- That market booked **$2.377M of bad debt**. The vault's share — ~$433k — was written off as `lostAssets`.
- The vault still *shows* a balance (share price ~$1.06), but `realTotalAssets` is ~$0. `totalAssets = realTotalAssets + lostAssets`, so the displayed number is accounting, not recoverable money. Withdrawals are frozen; the market is deprecated, 0 liquidity, removed from the withdraw queue.

**The recovery gap**

I went to Resolv's `/recover` portal. It says: *"You have no tokens eligible for recovery payment."* That makes sense mechanically — I never held USR. The USR was the **borrowers'** collateral, sitting in the Morpho market escrow. Resolv's snapshot seems to credit direct USR / wstUSR / RLP holders, not the USDC suppliers sitting behind a lending market that took the USR collateral.

So the people who *lost* the money (USDC suppliers) aren't the people Resolv is compensating (USR holders). The remaining USR collateral is claimable by whoever held the USR on-chain — the lending market / borrowers, not me.

**Questions for anyone who's dealt with this**

1. If you were a supplier behind a USR-collateral market (Morpho, Euler, etc.), did you recover anything, and how?
2. Is there any mechanism to make the remaining USR collateral in the market redeem 1:1 via Resolv and flow back to suppliers — or does that require the curator/borrowers to act?
3. Did ExtraFi (or any curator) backstop suppliers, or publish a plan?
4. Is there a coordinated effort — governance proposal, Discord, legal — for the affected USR lending vaults?

**To verify on-chain (Base):**

- Vault: `0x23479229e52Ab6aaD312D0B03DF9F33B46753B5e`
- USR/USDC market: `0xff0f2bd52ca786a4f8149f96622885e880222d8bed12bbbf5950296be8d03f89`
- USR token: `0x35E5dB674D8e93a03d814FA0ADa70731efe8a4b9`

Not looking for "DeFi bad" takes — looking for an actual recovery channel for lenders downstream of the depeg. Thanks.
