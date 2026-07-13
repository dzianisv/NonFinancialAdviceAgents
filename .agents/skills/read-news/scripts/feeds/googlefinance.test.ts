import { test, expect } from "bun:test";
import { resolveGfSymbol, buildConsensusUrl } from "./googlefinance";
import { connect, ingest } from "../news_store";

// ── resolveGfSymbol ──────────────────────────────────────────────────────────

test("resolveGfSymbol: known stock returns exact mapped string", () => {
  expect(resolveGfSymbol("AAPL")).toBe("AAPL:NASDAQ");
});

test("resolveGfSymbol: known crypto returns exact mapped string", () => {
  expect(resolveGfSymbol("BTC")).toBe("BTC-USD:CURRENCY");
});

test("resolveGfSymbol: case-insensitive lookup", () => {
  expect(resolveGfSymbol("aapl")).toBe("AAPL:NASDAQ");
  expect(resolveGfSymbol("btc")).toBe("BTC-USD:CURRENCY");
});

test("resolveGfSymbol: unknown symbol returns null, never a crypto-style guess", () => {
  const result = resolveGfSymbol("ZZZQ");
  expect(result).toBeNull();
  expect(result).not.toBe("ZZZQ-USD:CURRENCY");
});

test("resolveGfSymbol: unmapped real equity ticker returns null (not silently treated as crypto)", () => {
  // XOM/IBM are real stocks but not in GF_SYMBOL — must not become "XOM-USD:CURRENCY".
  expect(resolveGfSymbol("XOM")).toBeNull();
  expect(resolveGfSymbol("IBM")).toBeNull();
});

// ── buildConsensusUrl ────────────────────────────────────────────────────────

const PAGE_URL = "https://www.google.com/finance/quote/AAPL%3ANASDAQ";

test("buildConsensusUrl: same pageUrl + same summaryText -> identical URL (idempotent)", () => {
  const summary = "Apple (AAPL): 40 analysts — 30 Buy, 8 Hold, 2 Sell. Avg 12-month price target: USD 250.00.";
  const url1 = buildConsensusUrl(PAGE_URL, summary);
  const url2 = buildConsensusUrl(PAGE_URL, summary);
  expect(url1).toBe(url2);
});

test("buildConsensusUrl: same pageUrl + different summaryText -> different URL", () => {
  const summaryDay1 = "Apple (AAPL): 40 analysts — 30 Buy, 8 Hold, 2 Sell. Avg 12-month price target: USD 250.00.";
  const summaryDay2 = "Apple (AAPL): 41 analysts — 31 Buy, 8 Hold, 2 Sell. Avg 12-month price target: USD 255.00.";
  const url1 = buildConsensusUrl(PAGE_URL, summaryDay1);
  const url2 = buildConsensusUrl(PAGE_URL, summaryDay2);
  expect(url1).not.toBe(url2);
});

test("buildConsensusUrl: preserves pageUrl prefix and view=analyst-consensus marker", () => {
  const url = buildConsensusUrl(PAGE_URL, "some summary text");
  expect(url.startsWith(PAGE_URL)).toBe(true);
  expect(url).toContain("view=analyst-consensus");
});

// ── Integration: distinct consensus snapshots must not silently dedupe ──────

test("ingest: two distinct consensus snapshots for the same ticker both land as new", () => {
  const db = connect(":memory:");

  const summaryDay1 = "Apple (AAPL): 40 analysts — 30 Buy, 8 Hold, 2 Sell. Avg 12-month price target: USD 250.00.";
  const summaryDay2 = "Apple (AAPL): 41 analysts — 31 Buy, 8 Hold, 2 Sell. Avg 12-month price target: USD 255.00.";

  const articleDay1 = {
    source: "googlefinance",
    url: buildConsensusUrl(PAGE_URL, summaryDay1),
    title: "Google Finance Analyst Consensus — AAPL: Buy (30B/8H/2S, avg target 250.00)",
    summary: summaryDay1,
    body: null,
    published_at: new Date().toISOString(),
    lang: "en",
    tags: ["analyst-consensus", "google-finance"],
    assets: ["AAPL"],
  };
  const articleDay2 = {
    source: "googlefinance",
    url: buildConsensusUrl(PAGE_URL, summaryDay2),
    title: "Google Finance Analyst Consensus — AAPL: Buy (31B/8H/2S, avg target 255.00)",
    summary: summaryDay2,
    body: null,
    published_at: new Date().toISOString(),
    lang: "en",
    tags: ["analyst-consensus", "google-finance"],
    assets: ["AAPL"],
  };

  const result = ingest(db, [articleDay1, articleDay2]);
  expect(result.new).toBe(2);
  expect(result.duplicate).toBe(0);

  // Re-ingesting the identical day-2 snapshot again must now correctly dedupe.
  const rerun = ingest(db, [articleDay2]);
  expect(rerun.new).toBe(0);
  expect(rerun.duplicate).toBe(1);
});
