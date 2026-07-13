import { test, expect } from "bun:test";
import { buildYahooRssUrl, parseYahooRssItems } from "./yahoo";

// ── RSS fixtures (inline, no network) — modeled closely on real Yahoo headline RSS ──────────

const YAHOO_RSS = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <copyright>Copyright (c) 2026 Yahoo Inc. All rights reserved.</copyright>
  <description>Latest Financial News for AAPL</description>
  <item>
    <description>Fidelity runs a tech ETF that shadows VGT tick for tick at a lower fee, yet financial advisors quietly steer clients away from making the switch.</description>
    <guid isPermaLink="false">550b1514-9497-390b-8649-a7e9af2befff</guid>
    <link>https://247wallst.com/investing/etf/2026/07/13/why-smart-money-is-quietly-swapping-vgt-for-its-nearly-identical-cheaper-twin/?.tsrc=rss</link>
    <pubDate>Mon, 13 Jul 2026 20:15:43 +0000</pubDate>
    <title>Why Smart Money Is Quietly Swapping VGT for Its Nearly Identical, Cheaper Twin</title>
  </item>
  <item>
    <description>Apple would not comment on the "security breach," which allegedly allowed a former employee to download sensitive files from Apple's network long after he departed the company for rival OpenAI.</description>
    <guid isPermaLink="false">cb529cd1-dc04-3275-988f-ff156e0cba54</guid>
    <link>https://finance.yahoo.com/technology/ai/articles/apple-says-former-employee-exploited-200017484.html?.tsrc=rss</link>
    <pubDate>Mon, 13 Jul 2026 20:00:17 +0000</pubDate>
    <title>Apple says former employee exploited 'rare' bug to download confidential files after leaving for OpenAI</title>
  </item>
  <item>
    <guid isPermaLink="false">aaaa1111-bbbb-2222-cccc-333344445555</guid>
    <link>https://finance.yahoo.com/news/some-headline-without-a-teaser-100000000.html?.tsrc=rss</link>
    <pubDate>Mon, 13 Jul 2026 19:00:00 +0000</pubDate>
    <title>Some headline without a teaser</title>
  </item>
</channel>
</rss>`;

// Modeled on real "unknown ticker" response — valid RSS, empty channel, zero items.
const YAHOO_RSS_EMPTY = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <copyright>Copyright (c) 2026 Yahoo Inc. All rights reserved.</copyright>
  <description>Latest Financial News for ZZZZNOTATICKER</description>
</channel>
</rss>`;

// ── parseYahooRssItems ────────────────────────────────────────────────────────

test("parseYahooRssItems maps title/link/summary/pubDate correctly for normal items", () => {
  const articles = parseYahooRssItems(YAHOO_RSS, ["AAPL"]);
  expect(articles.length).toBe(3);
  expect(articles[0].title).toBe("Why Smart Money Is Quietly Swapping VGT for Its Nearly Identical, Cheaper Twin");
  expect(articles[0].url).toBe(
    "https://247wallst.com/investing/etf/2026/07/13/why-smart-money-is-quietly-swapping-vgt-for-its-nearly-identical-cheaper-twin/?.tsrc=rss",
  );
  expect(articles[0].summary).toBe(
    "Fidelity runs a tech ETF that shadows VGT tick for tick at a lower fee, yet financial advisors quietly steer clients away from making the switch.",
  );
  expect(articles[0].published_at).toBe("2026-07-13T20:15:43.000Z");
});

test("third-party link and finance.yahoo.com-hosted link both pass through as real URLs", () => {
  const articles = parseYahooRssItems(YAHOO_RSS, ["AAPL"]);
  expect(articles[0].url.startsWith("https://247wallst.com/")).toBe(true);
  expect(articles[1].url.startsWith("https://finance.yahoo.com/")).toBe(true);
});

test("missing <description> -> [UNAVAILABLE - no teaser in feed], never fabricated", () => {
  const articles = parseYahooRssItems(YAHOO_RSS, ["AAPL"]);
  expect(articles[2].summary).toBe("[UNAVAILABLE - no teaser in feed]");
});

test("body is always null", () => {
  const articles = parseYahooRssItems(YAHOO_RSS, ["AAPL"]);
  for (const a of articles) expect(a.body).toBeNull();
});

test("source is always 'yahoo'", () => {
  const articles = parseYahooRssItems(YAHOO_RSS, ["AAPL"]);
  for (const a of articles) expect(a.source).toBe("yahoo");
});

test("empty-channel fixture returns [] without throwing or fabricating a placeholder", () => {
  const articles = parseYahooRssItems(YAHOO_RSS_EMPTY, ["ZZZZNOTATICKER"]);
  expect(articles).toEqual([]);
});

test("garbage/invalid XML string returns [] without throwing", () => {
  expect(parseYahooRssItems("not xml at all", ["AAPL"])).toEqual([]);
  expect(parseYahooRssItems("", ["AAPL"])).toEqual([]);
});

// ── asset tagging ─────────────────────────────────────────────────────────────

test("single-symbol request tags every article with that one symbol", () => {
  const articles = parseYahooRssItems(YAHOO_RSS, ["AAPL"]);
  for (const a of articles) expect(a.assets).toEqual(["AAPL"]);
});

test("multi-symbol request tags every article with the full requested symbol list", () => {
  const articles = parseYahooRssItems(YAHOO_RSS, ["AAPL", "MSFT"]);
  for (const a of articles) {
    expect(a.assets).toContain("AAPL");
    expect(a.assets).toContain("MSFT");
    expect(a.assets.length).toBe(2);
  }
});

// ── buildYahooRssUrl ───────────────────────────────────────────────────────────

test("buildYahooRssUrl single symbol -> s=AAPL", () => {
  const url = new URL(buildYahooRssUrl(["AAPL"]));
  expect(url.searchParams.get("s")).toBe("AAPL");
});

test("buildYahooRssUrl multiple symbols -> comma-joined and uppercased", () => {
  const url = new URL(buildYahooRssUrl(["aapl", "msft"]));
  expect(url.searchParams.get("s")).toBe("AAPL,MSFT");
});

test("buildYahooRssUrl applies default region/lang when omitted", () => {
  const url = new URL(buildYahooRssUrl(["AAPL"]));
  expect(url.searchParams.get("region")).toBe("US");
  expect(url.searchParams.get("lang")).toBe("en-US");
});

test("buildYahooRssUrl honors custom region/lang when provided", () => {
  const url = new URL(buildYahooRssUrl(["AAPL"], { region: "GB", lang: "en-GB" }));
  expect(url.searchParams.get("region")).toBe("GB");
  expect(url.searchParams.get("lang")).toBe("en-GB");
});

test("buildYahooRssUrl points at the correct Yahoo headline RSS host/path", () => {
  const url = new URL(buildYahooRssUrl(["AAPL"]));
  expect(url.origin + url.pathname).toBe("https://feeds.finance.yahoo.com/rss/2.0/headline");
});
