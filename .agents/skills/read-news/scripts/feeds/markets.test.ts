import { test, expect } from "bun:test";
import {
  flattenTvAst,
  tvSymbolToAsset,
  mapCmcItem,
} from "./markets";
import type { Article } from "../types";

// ── flattenTvAst ─────────────────────────────────────────────────────────────

test("flattenTvAst: string leaf returns itself", () => {
  expect(flattenTvAst("hello")).toBe("hello");
});

test("flattenTvAst: nested AST produces joined text", () => {
  const ast = {
    type: "root",
    children: [
      { type: "paragraph", children: ["AAVE surged 10%"] },
      { type: "paragraph", children: ["DeFi markets reacted strongly"] },
    ],
  };
  const result = flattenTvAst(ast);
  expect(result).toContain("AAVE surged 10%");
  expect(result).toContain("DeFi markets reacted strongly");
});

test("flattenTvAst: list items joined with semicolons", () => {
  const ast = {
    type: "root",
    children: [
      {
        type: "list",
        children: [
          { type: "*", children: ["Key fact one"] },
          { type: "*", children: ["Key fact two"] },
        ],
      },
    ],
  };
  const result = flattenTvAst(ast);
  expect(result).toContain("Key fact one");
  expect(result).toContain("Key fact two");
  expect(result).toContain(";");
});

test("flattenTvAst: story-ref nodes are ignored", () => {
  const ast = {
    type: "root",
    children: [
      { type: "story-ref", params: { id: "abc123" } },
      { type: "paragraph", children: ["Visible text"] },
    ],
  };
  const result = flattenTvAst(ast);
  expect(result).not.toContain("abc123");
  expect(result).toContain("Visible text");
});

test("flattenTvAst: null/undefined returns empty string", () => {
  expect(flattenTvAst(null)).toBe("");
  expect(flattenTvAst(undefined)).toBe("");
});

// ── tvSymbolToAsset ──────────────────────────────────────────────────────────

test("tvSymbolToAsset: COINBASE:AAVEUSD → AAVE", () => {
  expect(tvSymbolToAsset("COINBASE:AAVEUSD")).toBe("AAVE");
});

test("tvSymbolToAsset: NASDAQ:AAPL → AAPL", () => {
  expect(tvSymbolToAsset("NASDAQ:AAPL")).toBe("AAPL");
});

test("tvSymbolToAsset: BINANCE:BTCUSDT → BTC", () => {
  expect(tvSymbolToAsset("BINANCE:BTCUSDT")).toBe("BTC");
});

test("tvSymbolToAsset: COINBASE:ETHUSD → ETH", () => {
  expect(tvSymbolToAsset("COINBASE:ETHUSD")).toBe("ETH");
});

test("tvSymbolToAsset: no exchange prefix", () => {
  expect(tvSymbolToAsset("AAPL")).toBe("AAPL");
});

// ── mapCmcItem ───────────────────────────────────────────────────────────────

const CMC_FIXTURE = {
  slug: "aave",
  cover: "https://example.com/cover.jpg",
  assets: [{ name: "AAVE", coinId: 7278, type: "main" }],
  createdAt: "2026-06-25T10:00:00.000Z",
  meta: {
    title: "AAVE Launches New Governance Proposal",
    subtitle: "The proposal aims to improve liquidity incentives.",
    sourceName: "CoinDesk",
    sourceUrl: "https://coindesk.com/aave-governance-2026",
    type: "article",
    id: "abc-123",
  },
};

test("mapCmcItem: maps title, summary, url, published_at, source", () => {
  const article = mapCmcItem(CMC_FIXTURE, "AAVE");
  expect(article.source).toBe("coinmarketcap");
  expect(article.title).toBe("AAVE Launches New Governance Proposal");
  expect(article.summary).toBe("The proposal aims to improve liquidity incentives.");
  expect(article.url).toBe("https://coindesk.com/aave-governance-2026");
  expect(article.published_at).toBe("2026-06-25T10:00:00.000Z");
});

test("mapCmcItem: assets is [queriedAsset] not CMC noisy assets", () => {
  const article = mapCmcItem(CMC_FIXTURE, "AAVE");
  expect(article.assets).toEqual(["AAVE"]);
});

test("mapCmcItem: assets array present on result", () => {
  const article = mapCmcItem(CMC_FIXTURE, "BTC");
  expect(Array.isArray(article.assets)).toBe(true);
  expect(article.assets).toEqual(["BTC"]);
});

test("mapCmcItem: falls back to CMC community URL when no sourceUrl", () => {
  const item = { ...CMC_FIXTURE, meta: { ...CMC_FIXTURE.meta, sourceUrl: undefined, id: "xyz-789" } };
  const article = mapCmcItem(item, "AAVE");
  expect(article.url).toContain("coinmarketcap.com");
  expect(article.url).toContain("xyz-789");
});
