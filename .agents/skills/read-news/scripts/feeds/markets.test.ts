import { test, expect } from "bun:test";
import {
  flattenTvAst,
  tvSymbolToAsset,
  mapCmcItem,
  parseGoogleFinanceHtml,
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

// ── parseGoogleFinanceHtml ───────────────────────────────────────────────────

// Real Google Finance news card structure (obfuscated classes omitted — matched by structure):
//   <div class="WrUjhf">Reuters</div>...<div class="JQ8Czd">5 hours ago</div>
//   <a href="URL" target="_blank"><div class="TQWIEd">TITLE</div></a>
const GF_FIXTURE_HTML = `
<!DOCTYPE html>
<html>
<body>
<div class="Yfwt5">
  <div class="WrUjhf">Reuters</div>
  <div class="JQ8Czd">5 hours ago</div>
</div>
<a href="https://www.reuters.com/markets/us/aapl-beats-earnings-q3-2026-06-25/" target="_blank"><div class="TQWIEd">Apple Beats Q3 Earnings Expectations</div></a>
<div class="Yfwt5">
  <div class="WrUjhf">CNBC</div>
  <div class="JQ8Czd">3 hours ago</div>
</div>
<a href="https://www.cnbc.com/2026/06/25/apple-stock-surges-after-earnings.html" target="_blank"><div class="TQWIEd">Apple Stock Surges After Earnings Beat</div></a>
</body>
</html>
`;

test("parseGoogleFinanceHtml: extracts reuters.com article", () => {
  const articles = parseGoogleFinanceHtml(GF_FIXTURE_HTML, "AAPL:NASDAQ");
  const reuters = articles.find(a => a.url.includes("reuters.com"));
  expect(reuters).toBeDefined();
  expect(reuters!.url).toBe("https://www.reuters.com/markets/us/aapl-beats-earnings-q3-2026-06-25/");
  expect(reuters!.title).toBe("Apple Beats Q3 Earnings Expectations");
});

test("parseGoogleFinanceHtml: extracts cnbc.com article", () => {
  const articles = parseGoogleFinanceHtml(GF_FIXTURE_HTML, "AAPL:NASDAQ");
  const cnbc = articles.find(a => a.url.includes("cnbc.com"));
  expect(cnbc).toBeDefined();
  expect(cnbc!.title).toBe("Apple Stock Surges After Earnings Beat");
});

test("parseGoogleFinanceHtml: assets set to ticker", () => {
  const articles = parseGoogleFinanceHtml(GF_FIXTURE_HTML, "AAPL:NASDAQ");
  for (const a of articles) {
    expect(a.assets).toEqual(["AAPL"]);
  }
});

test("parseGoogleFinanceHtml: every article has assets array", () => {
  const articles = parseGoogleFinanceHtml(GF_FIXTURE_HTML, "AAPL:NASDAQ");
  for (const a of articles) {
    expect(Array.isArray(a.assets)).toBe(true);
  }
});

test("parseGoogleFinanceHtml: junk HTML returns empty array", () => {
  const articles = parseGoogleFinanceHtml("<html><body><p>No news here</p></body></html>", "AAPL");
  expect(articles).toEqual([]);
});

test("parseGoogleFinanceHtml: nav links without target=_blank are ignored", () => {
  // Plain <a href> without target="_blank" must not be picked up
  const html = `<a href="https://www.reuters.com/nav-link/"><div class="TQWIEd">Home</div></a>`;
  const articles = parseGoogleFinanceHtml(html, "AAPL");
  expect(articles).toEqual([]);
});

test("parseGoogleFinanceHtml: non-news-domain target=_blank links are ignored", () => {
  const html = `<a href="https://www.google.com/some-page" target="_blank"><div class="TQWIEd">Not a news headline</div></a>`;
  const articles = parseGoogleFinanceHtml(html, "AAPL");
  expect(articles).toEqual([]);
});

test("parseGoogleFinanceHtml: no fabricated titles — bare anchor text skipped", () => {
  // target=_blank with no inner <div> text → must be skipped (title too short / empty)
  const html = `<a href="https://www.reuters.com/bare/" target="_blank"><div class="X"></div></a>`;
  const articles = parseGoogleFinanceHtml(html, "AAPL");
  for (const a of articles) {
    expect(a.title.length).toBeGreaterThan(0);
  }
});
