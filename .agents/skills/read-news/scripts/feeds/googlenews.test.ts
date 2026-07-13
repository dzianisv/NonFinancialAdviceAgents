import { test, expect } from "bun:test";
import {
  PUBLISHER_DOMAINS,
  buildGoogleNewsUrl,
  parseGoogleNewsItems,
} from "./googlenews";

// ── RSS fixture (inline, no network) — modeled closely on a real captured Google News item ──

const GOOGLENEWS_RSS = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>"bitcoin ETF" - Google News</title>
  <item>
    <title>Weekly market commentary - BlackRock</title>
    <link>https://news.google.com/rss/articles/CBMingFBVV95cUxQMOCK1?oc=5</link>
    <guid isPermaLink="false">CBMingFBVV95cUxQMOCK1</guid>
    <pubDate>Mon, 13 Jul 2026 17:34:29 GMT</pubDate>
    <description>&lt;a href="https://news.google.com/rss/articles/CBMingFBVV95cUxQMOCK1?oc=5" target="_blank"&gt;Weekly market commentary&lt;/a&gt;&amp;nbsp;&amp;nbsp;&lt;font color="#6f6f6f"&gt;BlackRock&lt;/font&gt;</description>
    <source url="https://www.blackrock.com">BlackRock</source>
  </item>
  <item>
    <title>Fed holds rates steady - Reuters</title>
    <link>https://news.google.com/rss/articles/CBMingFBVV95cUxQMOCK2?oc=5</link>
    <guid isPermaLink="false">CBMingFBVV95cUxQMOCK2</guid>
    <pubDate>Mon, 13 Jul 2026 16:00:00 GMT</pubDate>
    <description>&lt;a href="https://news.google.com/rss/articles/CBMingFBVV95cUxQMOCK2?oc=5" target="_blank"&gt;Fed holds rates steady&lt;/a&gt;&amp;nbsp;&amp;nbsp;&lt;font color="#6f6f6f"&gt;Reuters&lt;/font&gt;</description>
  </item>
  <item>
    <title>Markets update roundup</title>
    <link>https://news.google.com/rss/articles/CBMingFBVV95cUxQMOCK3?oc=5</link>
    <guid isPermaLink="false">CBMingFBVV95cUxQMOCK3</guid>
    <pubDate>Mon, 13 Jul 2026 15:00:00 GMT</pubDate>
    <description>&lt;a href="https://news.google.com/rss/articles/CBMingFBVV95cUxQMOCK3?oc=5" target="_blank"&gt;Markets update roundup&lt;/a&gt;</description>
  </item>
</channel>
</rss>`;

// ── parseGoogleNewsItems ──────────────────────────────────────────────────────

test("parseGoogleNewsItems extracts publisher domain + name when <source> present", () => {
  const articles = parseGoogleNewsItems(GOOGLENEWS_RSS);
  expect(articles.length).toBe(3);
  expect(articles[0].tags).toContain("publisher:BlackRock");
  expect(articles[0].summary).toContain("publisher: BlackRock (blackrock.com)");
});

test("publisher domain is null (not fabricated) when <source> tag absent, name still derived from title", () => {
  const articles = parseGoogleNewsItems(GOOGLENEWS_RSS);
  const reuters = articles[1];
  expect(reuters.tags).toContain("publisher:Reuters");
  expect(reuters.summary).toContain("publisher: Reuters (unresolved)");
});

test("both publisher name and domain are null when title has no ' - ' separator and no <source>", () => {
  const articles = parseGoogleNewsItems(GOOGLENEWS_RSS);
  const noSep = articles[2];
  expect(noSep.tags.some((t) => t.startsWith("publisher:"))).toBe(false);
  expect(noSep.summary).toContain("publisher: unknown (unresolved)");
});

test("body is always null", () => {
  const articles = parseGoogleNewsItems(GOOGLENEWS_RSS);
  for (const a of articles) expect(a.body).toBeNull();
});

test("summary always starts with the discovery-only marker", () => {
  const articles = parseGoogleNewsItems(GOOGLENEWS_RSS);
  for (const a of articles) expect(a.summary.startsWith("[DISCOVERY-ONLY")).toBe(true);
});

test("url equals the raw <link> value verbatim — never altered or 'resolved'", () => {
  const articles = parseGoogleNewsItems(GOOGLENEWS_RSS);
  expect(articles[0].url).toBe("https://news.google.com/rss/articles/CBMingFBVV95cUxQMOCK1?oc=5");
  expect(articles[1].url).toBe("https://news.google.com/rss/articles/CBMingFBVV95cUxQMOCK2?oc=5");
});

test("title is passed through raw and unmodified (suffix not stripped from title field)", () => {
  const articles = parseGoogleNewsItems(GOOGLENEWS_RSS);
  expect(articles[0].title).toBe("Weekly market commentary - BlackRock");
  expect(articles[1].title).toBe("Fed holds rates steady - Reuters");
});

test("source is always 'googlenews', assets always empty, body always null", () => {
  const articles = parseGoogleNewsItems(GOOGLENEWS_RSS);
  for (const a of articles) {
    expect(a.source).toBe("googlenews");
    expect(a.assets).toEqual([]);
    expect(a.body).toBeNull();
  }
});

test("tags always include google-news and discovery-only", () => {
  const articles = parseGoogleNewsItems(GOOGLENEWS_RSS);
  for (const a of articles) {
    expect(a.tags).toContain("google-news");
    expect(a.tags).toContain("discovery-only");
  }
});

test("summary never implies the link is a verified/resolved direct publisher URL", () => {
  const articles = parseGoogleNewsItems(GOOGLENEWS_RSS);
  for (const a of articles) {
    expect(a.summary.toLowerCase()).not.toContain("verified publisher");
    expect(a.summary.toLowerCase()).not.toContain("resolved publisher url");
    expect(a.summary.toLowerCase()).not.toContain("direct publisher url");
  }
});

test("parseGoogleNewsItems returns [] on garbage or empty XML, no throw", () => {
  expect(parseGoogleNewsItems("not xml at all")).toEqual([]);
  expect(parseGoogleNewsItems("")).toEqual([]);
});

// ── buildGoogleNewsUrl ────────────────────────────────────────────────────────

test("buildGoogleNewsUrl includes site: clauses for known publisher aliases", () => {
  const url = buildGoogleNewsUrl("earnings", { publishers: ["bloomberg", "reuters"] });
  const q = new URL(url).searchParams.get("q") ?? "";
  expect(q).toContain("site:bloomberg.com");
  expect(q).toContain("site:reuters.com");
  expect(q).toContain(" OR ");
});

test("buildGoogleNewsUrl resolves 'ibd' alias to investors.com", () => {
  const url = buildGoogleNewsUrl("earnings", { publishers: ["ibd"] });
  const q = new URL(url).searchParams.get("q") ?? "";
  expect(q).toContain("site:investors.com");
});

test("buildGoogleNewsUrl has no site: clause when publishers omitted", () => {
  const url = buildGoogleNewsUrl("earnings");
  const q = new URL(url).searchParams.get("q") ?? "";
  expect(q).not.toContain("site:");
});

test("buildGoogleNewsUrl days option changes when:Nd value; default is 7", () => {
  const defaultUrl = buildGoogleNewsUrl("earnings");
  const defaultQ = new URL(defaultUrl).searchParams.get("q") ?? "";
  expect(defaultQ).toContain("when:7d");

  const customUrl = buildGoogleNewsUrl("earnings", { days: 2 });
  const customQ = new URL(customUrl).searchParams.get("q") ?? "";
  expect(customQ).toContain("when:2d");
});

test("buildGoogleNewsUrl sets hl/gl/ceid params", () => {
  const url = new URL(buildGoogleNewsUrl("earnings"));
  expect(url.searchParams.get("hl")).toBe("en-US");
  expect(url.searchParams.get("gl")).toBe("US");
  expect(url.searchParams.get("ceid")).toBe("US:en");
});

test("PUBLISHER_DOMAINS maps all five required publishers", () => {
  expect(PUBLISHER_DOMAINS.bloomberg).toBe("bloomberg.com");
  expect(PUBLISHER_DOMAINS.reuters).toBe("reuters.com");
  expect(PUBLISHER_DOMAINS.businessinsider).toBe("businessinsider.com");
  expect(PUBLISHER_DOMAINS.cnbc).toBe("cnbc.com");
  expect(PUBLISHER_DOMAINS.ibd).toBe("investors.com");
});
