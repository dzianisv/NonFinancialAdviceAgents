#!/usr/bin/env bun
/**
 * merkl_rewards.ts — ground-truth a wallet's Merkl incentive rewards from Merkl's OWN public API (no key).
 *
 * WHY: Merkl is the canonical source for incentive-campaign rewards and is the only place that cleanly
 * shows EARNED / CLAIMED / CLAIMABLE (unclaimed) per token — unclaimed rewards are idle money the
 * investor has already earned but not collected, an efficiency an aggregator (DeBank) under-shows. BUT
 * Merkl carries the same mispricing trap we guard against everywhere else: its `token.price` is a
 * placeholder for symbol-spoofed campaign tokens. A real wallet had a reward token at
 * 0xBE1e…efc symbol "USDC" priced exactly $1 (name on-chain: "USD Coin (wrapped)") implying $5,110
 * claimable — but canonical Base USDC is 0x8335…2913. So this helper prices rewards but FLAGS any token
 * whose symbol is a major stable while its on-chain address is NOT that chain's canonical stable address
 * (the spoof guard), excluding it from the "collect now" total until a human confirms redeemability.
 *
 * Endpoint: GET https://api.merkl.xyz/v4/users/<address>/rewards?chainId=<id>  (public, no key).
 *
 * Usage:
 *   bun merkl_rewards.ts <walletAddress> [--chains 1,8453,42161,10] [--json]
 *
 * Exit: 2 if any reward is flagged unverified (so a caller can gate), 1 on API error, else 0.
 */

// Canonical stablecoin token addresses (lowercased) per chainId — the ONLY addresses a stable-symbol
// reward may legitimately carry. A stable symbol at any other address is a spoof.
export const CANONICAL_STABLES: Record<number, Set<string>> = {
  1: new Set([
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", // USDC
    "0xdac17f958d2ee523a2206206994597c13d831ec7", // USDT
    "0x6b175474e89094c44da98b954eedeac495271d0f", // DAI
  ]),
  10: new Set(["0x0b2c639c533813f4aa9d7837caf62653d097ff85"]), // Optimism USDC
  8453: new Set(["0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"]), // Base USDC
  42161: new Set(["0xaf88d065e77c8cc2239327c5edb3a432268e5831"]), // Arbitrum USDC
};
// Symbols that MUST resolve to a canonical address — otherwise the reward token is symbol-spoofed.
export const STABLE_SYMBOLS = new Set(["USDC", "USDT", "DAI", "USDC.E", "USDS", "USDE", "USDBC"]);

export type RewardInput = { symbol: string; address: string; chainId: number; price: number | null };
export type RewardVerdict = { verified: boolean; reason: string };

/**
 * A reward is UNVERIFIED if its symbol claims to be a major stable but its address is not that chain's
 * canonical stable address (symbol-spoof). Canonical stables (even at an exact $1 print) are fine.
 * Non-stable governance/reward tokens (MORPHO, SEAM, OP, ARB…) trust Merkl's oracle price.
 */
export function classifyReward(r: RewardInput): RewardVerdict {
  const sym = (r.symbol || "").toUpperCase();
  if (STABLE_SYMBOLS.has(sym)) {
    const canon = CANONICAL_STABLES[r.chainId];
    const addr = (r.address || "").toLowerCase();
    if (!canon || !canon.has(addr)) {
      return { verified: false, reason: `stable symbol ${sym} at non-canonical address ${addr.slice(0, 10)}…` };
    }
  }
  return { verified: true, reason: "oracle-priced / canonical" };
}

export function rewardAmounts(rawAmount: string, rawClaimed: string, decimals: number) {
  const d = 10 ** decimals;
  const earned = Number(BigInt(rawAmount || "0")) / d;
  const claimed = Number(BigInt(rawClaimed || "0")) / d;
  return { earned, claimed, claimable: earned - claimed };
}

type Row = {
  chainId: number; chain: string; symbol: string; address: string;
  earned: number; claimed: number; claimable: number; price: number;
  usdClaimable: number; usdEarned: number; verified: boolean; reason: string;
};

async function fetchChain(address: string, chainId: number): Promise<Row[]> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 25_000);
  try {
    const res = await fetch(`https://api.merkl.xyz/v4/users/${address}/rewards?chainId=${chainId}`, {
      headers: { accept: "application/json" }, signal: ctrl.signal,
    });
    const data = await res.json();
    const rows: Row[] = [];
    for (const chain of Array.isArray(data) ? data : []) {
      const cname = chain?.chain?.name ?? String(chainId);
      for (const r of chain?.rewards ?? []) {
        const tok = r.token ?? {};
        const price = tok.price == null ? 0 : Number(tok.price);
        const { earned, claimed, claimable } = rewardAmounts(r.amount, r.claimed, Number(tok.decimals ?? 18));
        const vd = classifyReward({ symbol: tok.symbol, address: tok.address, chainId, price });
        rows.push({
          chainId, chain: cname, symbol: tok.symbol ?? "?", address: tok.address ?? "",
          earned, claimed, claimable, price,
          usdClaimable: claimable * price, usdEarned: earned * price, verified: vd.verified, reason: vd.reason,
        });
      }
    }
    return rows;
  } finally {
    clearTimeout(t);
  }
}

async function main() {
  const argv = process.argv.slice(2);
  const address = argv.find((a) => /^0x[0-9a-fA-F]{40}$/.test(a));
  const asJson = argv.includes("--json");
  const chainsArg = argv[argv.indexOf("--chains") + 1];
  const chains = argv.includes("--chains") && chainsArg
    ? chainsArg.split(",").map((s) => Number(s.trim())).filter(Boolean)
    : [1, 10, 8453, 42161];
  if (!address) {
    console.error("usage: bun merkl_rewards.ts <0x-wallet> [--chains 1,8453,42161,10] [--json]");
    process.exit(1);
  }

  let rows: Row[] = [];
  try {
    rows = (await Promise.all(chains.map((c) => fetchChain(address, c)))).flat()
      .filter((r) => r.earned > 0).sort((a, b) => b.usdClaimable - a.usdClaimable);
  } catch (e) {
    console.error(`Merkl API error: ${(e as Error).message}`);
    process.exit(1);
  }

  const verifiedClaimable = rows.filter((r) => r.verified).reduce((s, r) => s + r.usdClaimable, 0);
  const flagged = rows.filter((r) => !r.verified && r.usdClaimable > 0);
  const flaggedUsd = flagged.reduce((s, r) => s + r.usdClaimable, 0);

  if (asJson) {
    console.log(JSON.stringify({ address, rows, verifiedClaimableUsd: verifiedClaimable, flaggedClaimableUsd: flaggedUsd }, null, 2));
  } else {
    console.log(`Merkl rewards — ${address}`);
    for (const r of rows) {
      const tag = r.verified ? "" : `  ⚠ UNVERIFIED: ${r.reason}`;
      console.log(`  ${r.chain.padEnd(9)} ${r.symbol.padEnd(8)} claimable=${r.claimable.toLocaleString("en-US", { maximumFractionDigits: 4 }).padStart(14)} ` +
        `$${r.usdClaimable.toLocaleString("en-US", { maximumFractionDigits: 2 }).padStart(10)}${tag}`);
    }
    console.log(`\n  VERIFIED claimable (collect now) ≈ $${verifiedClaimable.toLocaleString("en-US", { maximumFractionDigits: 2 })}`);
    if (flagged.length) {
      console.log(`  UNVERIFIED (confirm redeemability before counting): $${flaggedUsd.toLocaleString("en-US", { maximumFractionDigits: 2 })} ` +
        `[${flagged.map((r) => `${r.symbol}@${r.chain}`).join(", ")}]`);
    }
  }
  process.exit(flagged.length ? 2 : 0);
}

if (import.meta.main) main();
