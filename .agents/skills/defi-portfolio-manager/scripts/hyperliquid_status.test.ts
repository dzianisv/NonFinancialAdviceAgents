#!/usr/bin/env bun
/**
 * Tests for hyperliquid_status.ts — pure valuation/flagging logic (no network).
 * Fixtures are the REAL HL-API rows for 0x5D03…e653 that exposed the spot-mid mispricing trap.
 *   bun test ./.agents/skills/defi-portfolio-manager/scripts/hyperliquid_status.test.ts
 */
import { expect, test } from "bun:test";
import { valueSpotToken, isHlpVault, STABLES, PERP_ALIAS } from "./hyperliquid_status.ts";

// canonical perp marks at read time
const MARKS = { HYPE: 64.189, SOL: 69.205, BTC: 61630, ETH: 1647.6 };

test("HYPE priced off its perp mark, not the broken spot mid ($0.092)", () => {
  const v = valueSpotToken("HYPE", 131.707296, MARKS);
  expect(v.flagged).toBe(false);
  expect(v.basis).toBe("perp-mark:HYPE");
  expect(v.usd).toBeCloseTo(131.707296 * 64.189, 1); // ≈ $8,455, matches DeBank $8,365
});

test("USOL (Unit-bridged SOL) priced off SOL perp mark via alias", () => {
  const v = valueSpotToken("USOL", 16.3274664, MARKS);
  expect(v.basis).toBe("perp-mark:SOL");
  expect(v.usd).toBeCloseTo(16.3274664 * 69.205, 1); // ≈ $1,130, matches DeBank $1,126
  expect(v.flagged).toBe(false);
});

test("MAX dust is FLAGGED and valued $0 — NOT the $8.65M the spot mid implies (the trap)", () => {
  const v = valueSpotToken("MAX", 1317072.96, MARKS);
  expect(v.flagged).toBe(true);
  expect(v.usd).toBe(0);
  expect(v.basis).toBe("illiquid/no-perp-oracle");
});

test("USDC stable priced at $1", () => {
  const v = valueSpotToken("USDC", 0.11, MARKS);
  expect(v.usd).toBeCloseTo(0.11, 4);
  expect(v.basis).toBe("stable=$1");
  expect(v.flagged).toBe(false);
});

test("a token that IS itself a perp coin (no alias needed) uses its mark", () => {
  const v = valueSpotToken("BTC", 0.5, MARKS);
  expect(v.usd).toBeCloseTo(0.5 * 61630, 1);
  expect(v.flagged).toBe(false);
});

test("HLP vault address is recognized (perp-LP reject), case-insensitive", () => {
  expect(isHlpVault("0xdfc24b077bc1425ad1dea75bcb6f8158e10df303")).toBe(true);
  expect(isHlpVault("0xDFC24B077BC1425AD1DEA75BCB6F8158E10DF303")).toBe(true);
  expect(isHlpVault("0x0000000000000000000000000000000000000000")).toBe(false);
  expect(isHlpVault(null)).toBe(false);
});

test("config sanity: stables tight, HYPE/USOL aliases present", () => {
  expect(STABLES.has("USDC")).toBe(true);
  expect(STABLES.has("MAX")).toBe(false);
  expect(PERP_ALIAS["USOL"]).toBe("SOL");
  expect(PERP_ALIAS["HYPE"]).toBe("HYPE");
});
