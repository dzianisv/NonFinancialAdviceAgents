import { test, expect } from "bun:test";
import { resolveExchange, buildHeadlineUrl, fetchMorningstar } from "./morningstar";
import { connect, ingest } from "../news_store";

// ── resolveExchange ──────────────────────────────────────────────────────────

test("resolveExchange: known stock returns xnas", () => {
  expect(resolveExchange("AAPL")).toBe("xnas");
});

test("resolveExchange: case-insensitive lookup", () => {
  expect(resolveExchange("aapl")).toBe("xnas");
  expect(resolveExchange("Msft")).toBe("xnas");
});

test("resolveExchange: unknown stock returns null, never silently defaults to xnas", () => {
  const result = resolveExchange("ZZZQ");
  expect(result).toBeNull();
  expect(result).not.toBe("xnas");
});

// ── buildHeadlineUrl ─────────────────────────────────────────────────────────

const PAGE_URL = "https://www.morningstar.com/stocks/xnas/aapl/quote";

test("buildHeadlineUrl: same pageUrl + same title -> identical URL (idempotent)", () => {
  const title = "Apple Reports Record Q3 Revenue Amid iPhone Demand Surge";
  const url1 = buildHeadlineUrl(PAGE_URL, title);
  const url2 = buildHeadlineUrl(PAGE_URL, title);
  expect(url1).toBe(url2);
});

test("buildHeadlineUrl: same pageUrl + different title -> different URL", () => {
  const titleA = "Apple Reports Record Q3 Revenue Amid iPhone Demand Surge";
  const titleB = "Apple Announces New Buyback Program Worth $90 Billion";
  const urlA = buildHeadlineUrl(PAGE_URL, titleA);
  const urlB = buildHeadlineUrl(PAGE_URL, titleB);
  expect(urlA).not.toBe(urlB);
});

test("buildHeadlineUrl: preserves pageUrl prefix (provenance)", () => {
  const url = buildHeadlineUrl(PAGE_URL, "Some headline text here");
  expect(url.startsWith(PAGE_URL)).toBe(true);
});

// ── Integration: distinct same-page headlines must not silently dedupe ──────

test("ingest: two distinct headlines scraped off the same Morningstar page both land as new", () => {
  const db = connect(":memory:");

  const titleA = "Apple Reports Record Q3 Revenue Amid iPhone Demand Surge";
  const titleB = "Apple Announces New Buyback Program Worth $90 Billion";

  const articleA = {
    source: "morningstar",
    url: buildHeadlineUrl(PAGE_URL, titleA),
    title: titleA,
    summary: "[headline only — no teaser available]",
    body: null,
    published_at: new Date().toISOString(),
    lang: "en",
    tags: ["morningstar"],
    assets: ["AAPL"],
  };
  const articleB = {
    source: "morningstar",
    url: buildHeadlineUrl(PAGE_URL, titleB),
    title: titleB,
    summary: "[headline only — no teaser available]",
    body: null,
    published_at: new Date().toISOString(),
    lang: "en",
    tags: ["morningstar"],
    assets: ["AAPL"],
  };

  const result = ingest(db, [articleA, articleB]);
  expect(result.new).toBe(2);
  expect(result.duplicate).toBe(0);
});

// ── Regression: crypto rejection must still work ────────────────────────────

test("fetchMorningstar: crypto asset still returns 'not available for crypto asset' error", async () => {
  const { articles, errors } = await fetchMorningstar("BTC");
  expect(articles).toEqual([]);
  expect(errors.some((e) => e.includes("not available for crypto asset"))).toBe(true);
});
