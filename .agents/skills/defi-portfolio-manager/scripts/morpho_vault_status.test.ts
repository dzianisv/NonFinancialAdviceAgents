#!/usr/bin/env bun
/**
 * Tests for morpho_vault_status.ts — the pure deprecation classifier (no network).
 * Fixtures are the REAL Morpho-API rows for 0x5D03…e653 that motivated this check.
 *   bun test ./.agents/skills/defi-portfolio-manager/scripts/morpho_vault_status.test.ts
 */
import { expect, test } from "bun:test";
import { classifyVault, DEPRECATION_WARNINGS, DEAD_APY } from "./morpho_vault_status.ts";

test("delisted + deposit_disabled + 0% APY = DEAD (Seamless USDC, the real trap)", () => {
  const v = classifyVault({
    name: "Seamless USDC Vault", listed: false, netApy: 0,
    warnings: [{ type: "deposit_disabled" }, { type: "not_whitelisted" }],
  });
  expect(v.dead).toBe(true);
  expect(v.reasons).toContain("delisted");
  expect(v.reasons).toContain("warn:deposit_disabled");
  expect(v.reasons.some((r) => r.startsWith("netApy≈0"))).toBe(true);
});

test("listed but deposit_disabled + 0% = DEAD (Morpho eUSD; invalid_name ignored)", () => {
  const v = classifyVault({
    name: "Morpho eUSD", listed: true, netApy: 0,
    warnings: [{ type: "invalid_name" }, { type: "deposit_disabled" }],
  });
  expect(v.dead).toBe(true);
  expect(v.reasons).toContain("warn:deposit_disabled");
  // invalid_name is a metadata nit, not a deprecation reason
  expect(v.reasons.some((r) => r === "warn:invalid_name")).toBe(false);
});

test("listed, no warnings, but 0% APY = DEAD on yield alone (Universal USDC)", () => {
  const v = classifyVault({ name: "Universal USDC", listed: true, netApy: 0, warnings: [{ type: "deposit_disabled" }] });
  expect(v.dead).toBe(true);
});

test("healthy active vault = ok (Yearn USDC, 3.82%, listed, no warnings)", () => {
  const v = classifyVault({ name: "Yearn USDC", listed: true, netApy: 0.0382, warnings: [] });
  expect(v.dead).toBe(false);
  expect(v.reasons).toHaveLength(0);
});

test("just below the dead-APY floor flags; just above does not", () => {
  expect(classifyVault({ listed: true, netApy: DEAD_APY, warnings: [] }).dead).toBe(true);
  expect(classifyVault({ listed: true, netApy: DEAD_APY + 0.0001, warnings: [] }).dead).toBe(false);
});

test("missing fields are tolerated (null listed, null apy => 0% dead)", () => {
  const v = classifyVault({ name: "?", listed: null, netApy: null, warnings: null });
  expect(v.dead).toBe(true); // null apy treated as 0 => dead on yield
  expect(v.reasons).not.toContain("delisted"); // listed===false only — null is NOT delisted
});

test("listed:null is not treated as delisted", () => {
  const v = classifyVault({ listed: null, netApy: 0.05, warnings: [] });
  expect(v.reasons).not.toContain("delisted");
  expect(v.dead).toBe(false);
});

test("DEPRECATION_WARNINGS covers the wind-down signals, excludes invalid_name", () => {
  expect(DEPRECATION_WARNINGS.has("deposit_disabled")).toBe(true);
  expect(DEPRECATION_WARNINGS.has("not_whitelisted")).toBe(true);
  expect(DEPRECATION_WARNINGS.has("invalid_name")).toBe(false);
});
