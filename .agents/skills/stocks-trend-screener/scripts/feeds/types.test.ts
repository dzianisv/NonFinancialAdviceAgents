import { test, expect } from "bun:test";
import { stripHtml, normalizeUrl } from "./types.ts";

// Pipeline feeds (coindesk, decrypt) and the generic parseRSS share this stripHtml. WSJ/Dow Jones
// emit hexadecimal HTML entities, so the decoder must handle hex — not just decimal — or teasers arrive
// garbled. These tests lock that behavior so the bug fixed in the canonical fetchers cannot regress here.

test("stripHtml decodes HEXADECIMAL numeric entities to genuine Unicode (not ASCII)", () => {
  const raw = "JD Vance&#x2019;s plan to&#xa0;Arab states &#x2014; he says&#x201c;yes&#x201d;";
  // &#x2019; -> ' (U+2019), &#xa0; -> NBSP collapsed to space, &#x2014; -> em dash, &#x201c;/&#x201d; -> curly quotes
  expect(stripHtml(raw)).toBe("JD Vance\u2019s plan to Arab states \u2014 he says\u201cyes\u201d");
});

test("stripHtml still decodes DECIMAL numeric + named entities", () => {
  expect(stripHtml("Tom&#8217;s &quot;deal&quot; &amp; co &lt;b&gt;")).toBe(
    "Tom\u2019s \"deal\" & co <b>",
  );
});

test("stripHtml decodes &amp; LAST so &amp;lt; stays literal text, not a tag bracket", () => {
  expect(stripHtml("A&amp;lt;B")).toBe("A&lt;B");
});

test("stripHtml unwraps CDATA and strips tags", () => {
  expect(stripHtml("<![CDATA[<p>Hello <b>world</b></p>]]>")).toBe("Hello world");
});

test("stripHtml ignores out-of-range code points without throwing", () => {
  expect(stripHtml("bad&#xFFFFFFFF; tail")).toBe("bad tail");
});

test("normalizeUrl strips tracking params for stable dedup", () => {
  const a = normalizeUrl("https://www.ft.com/content/abc?utm_source=rss&ns=1");
  const b = normalizeUrl("https://www.ft.com/content/abc");
  expect(a).toBe(b);
});
