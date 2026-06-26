#!/usr/bin/env bun
/**
 * Tests for merkl_rewards.ts — pure reward classification + amount math (no network).
 * Fixtures are the REAL Merkl rows for 0x5D03…e653 that exposed the symbol-spoof trap.
 *   bun test ./.agents/skills/defi-portfolio-manager/scripts/merkl_rewards.test.ts
 */
import { expect, test } from "bun:test";
import { classifyReward, rewardAmounts, CANONICAL_STABLES, STABLE_SYMBOLS } from "./merkl_rewards.ts";

test("canonical Base USDC reward is VERIFIED", () => {
  const v = classifyReward({ symbol: "USDC", address: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", chainId: 8453, price: 0.9996 });
  expect(v.verified).toBe(true);
});

test("the spoof: 'USDC' at non-canonical 0xBE1e… on Base is UNVERIFIED (the $5,110 phantom)", () => {
  const v = classifyReward({ symbol: "USDC", address: "0xBE1e24249ac123D127aE01229A1b9E2421994efc", chainId: 8453, price: 1 });
  expect(v.verified).toBe(false);
  expect(v.reason).toContain("non-canonical");
});

test("canonical stable at an exact $1 print is VERIFIED (address is the real guard, not price)", () => {
  const v = classifyReward({ symbol: "USDT", address: "0xdac17f958d2ee523a2206206994597c13d831ec7", chainId: 1, price: 1 });
  expect(v.verified).toBe(true);
});

test("canonical Ethereum USDT at oracle price is VERIFIED", () => {
  const v = classifyReward({ symbol: "USDT", address: "0xdac17f958d2ee523a2206206994597c13d831ec7", chainId: 1, price: 0.9999 });
  expect(v.verified).toBe(true);
});

test("non-stable governance rewards trust Merkl's oracle price (MORPHO, SEAM, EXTRA, OP)", () => {
  for (const [sym, addr, cid, px] of [
    ["MORPHO", "0xBAa5CC21fd487B8Fcc2F632f3F4E8D37262a0842", 8453, 1.7516],
    ["SEAM", "0x1C7a460413dD4e964f96D8dFC56E7223cE88CD85", 8453, 0.006437],
    ["EXTRA", "0x2dAD3a13ef0C6366220f989157009e501e7938F8", 8453, 0.004091],
    ["OP", "0x4200000000000000000000000000000000000042", 10, 0.108],
  ] as const) {
    expect(classifyReward({ symbol: sym, address: addr, chainId: cid, price: px }).verified).toBe(true);
  }
});

test("rewardAmounts handles 6- and 18-decimal tokens and big ints exactly", () => {
  // canonical USDC 6dp: 5_906_623 -> 5.906623
  expect(rewardAmounts("5906623", "0", 6).claimable).toBeCloseTo(5.906623, 6);
  // MORPHO 18dp: earned 85.8139, claimed 74.4229 -> claimable ~11.391
  const m = rewardAmounts("85813878445900067112", "74422862043778634072", 18);
  expect(m.claimable).toBeCloseTo(11.391, 2);
  // the spoof: 5_110_463_734 at 6dp = 5110.4637 (proves the value is real-looking, hence must be flagged by SYMBOL/address, not size)
  expect(rewardAmounts("5110463734", "0", 6).earned).toBeCloseTo(5110.4637, 3);
});

test("config: canonical maps + stable symbol set are populated", () => {
  expect(CANONICAL_STABLES[8453].has("0x833589fcd6edb6e08f4c7c32d4f71b54bda02913")).toBe(true);
  expect(STABLE_SYMBOLS.has("USDC")).toBe(true);
  expect(STABLE_SYMBOLS.has("MORPHO")).toBe(false);
});
