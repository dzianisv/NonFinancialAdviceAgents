import { test, expect } from "bun:test";
import { fetchAllNews } from "./index";

// ── googlenews unscoped-request refusal (no network) ────────────────────────
//
// When "googlenews" is requested with neither --query nor --asset/--assets, fetchAllNews
// must refuse instantly rather than silently fanning out a bare-text search over the internal
// DEFAULT_MARKET_ASSETS crypto ticker list. This resolves synchronously (no fetch() call is
// ever made), so it's safe to run in the unit test suite without hitting the network.

test("fetchAllNews({sources:['googlenews']}) with no query/assets refuses without network calls", async () => {
  const { records, unavailable } = await fetchAllNews({ sources: ["googlenews"] });
  expect(records).toHaveLength(0);
  const refusal = unavailable.find((u) => u.includes("googlenews") && u.includes("UNAVAILABLE"));
  expect(refusal).toBeDefined();
});
