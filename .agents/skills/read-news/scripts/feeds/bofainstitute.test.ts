import { test, expect, describe } from "bun:test";
import {
  fetchBofaInstitute,
  parseSitemap,
  isEligibleInsightUrl,
  extractPublishedDate,
  toVerifiedISO,
  SITEMAP_URL,
} from "./bofainstitute";
import { fetchAllNews } from "./index";
import { connect, ingest, query } from "../news_store";

// ── Live network integration test only — no mocks, no fixtures, no captured payloads ────────
//
// Per repo/user testing policy, unit tests against fabricated or captured fixture bytes are not
// used here. Every assertion below is against the REAL institute.bankofamerica.com sitemap and
// REAL live pages, fetched fresh at test-run time. Assertions are the deterministic invariants
// that must hold for whatever content the site currently serves — not against a fixed dataset.
//
// The central regression guard this test exists to enforce: `published_at` on a returned Article
// must never be a fetch/ingest-time value, or the sitemap `<lastmod>` (an update timestamp),
// mislabeled as a publication date. It must be either (a) a real date pulled from the page's own
// structured `datePublished`/meta fields, with `date_provenance: "source"`, or (b) `null` with
// `date_provenance: "unavailable"` when no such field exists on the page — the case observed live
// as of 2026-07. A regression back to `toISO(lastmod)` or `new Date().toISOString()` is caught
// deterministically below: sitemap `<lastmod>` values for eligible pages are, in practice, always
// at least days old relative to "now" (BofA Institute publishes weekly/monthly, not within the
// last few minutes), and "now" is trivially distinguishable from `null`, so either fabrication
// fails the assertions below.

describe("bofainstitute sitemap (live)", () => {
  test("real sitemap.xml parses into well-formed entries with at least one eligible insight URL", async () => {
    const ac = new AbortController();
    const t = setTimeout(() => ac.abort(), 15_000);
    const res = await fetch(SITEMAP_URL, {
      headers: { Accept: "application/xml, text/xml" },
      signal: ac.signal,
    });
    clearTimeout(t);
    expect(res.ok).toBe(true);
    const xml = await res.text();

    const entries = parseSitemap(xml);
    // A hard parse failure (empty result) means the live sitemap format changed or the fetch
    // returned something unexpected — the only legitimate way this is empty.
    expect(entries.length).toBeGreaterThan(0);

    for (const e of entries) {
      expect(() => new URL(e.url)).not.toThrow();
      expect(new URL(e.url).hostname).toBe("institute.bankofamerica.com");
    }

    const eligible = entries.filter((e) => isEligibleInsightUrl(e.url));
    expect(eligible.length).toBeGreaterThan(0);
    // Hub/index pages must never be classified as eligible individual insight pages.
    const hubPage = entries.find((e) => /\/economic-insights\.html$/.test(e.url));
    if (hubPage) expect(isEligibleInsightUrl(hubPage.url)).toBe(false);
  }, 30_000);
});

describe("fetchBofaInstitute (live)", () => {
  test("returns real articles honestly dated — null+unavailable when unverifiable, never fetch time or <lastmod>", async () => {
    const { source, articles, errors } = await fetchBofaInstitute({ days: 400, limit: 5 });

    expect(source).toBe("bofainstitute");
    expect(Array.isArray(articles)).toBe(true);
    // A hard network/parsing failure would show up here — the live site or its sitemap format
    // changing is the only way this legitimately returns nothing.
    expect(articles.length).toBeGreaterThan(0);

    let datelessCount = 0;

    for (const a of articles) {
      expect(a.source).toBe("bofainstitute");
      expect(a.url.startsWith("https://institute.bankofamerica.com/")).toBe(true);
      expect(a.title.length).toBeGreaterThan(0);
      expect(a.body).toBeNull();
      expect(a.assets).toEqual([]);
      expect(a.tags).toContain("bofa-institute");
      // Never conflated with the entitlement-gated sell-side product.
      expect(a.source).not.toBe("bofaglobalresearch");
      expect(a.tags.join(" ").toLowerCase()).not.toContain("global research");

      // date_provenance and published_at must always agree with each other.
      expect(["source", "unavailable"]).toContain(a.date_provenance);
      if (a.date_provenance === "unavailable") {
        expect(a.published_at).toBeNull();
        datelessCount++;
      } else {
        expect(typeof a.published_at).toBe("string");
        expect(isNaN(Date.parse(a.published_at as string))).toBe(false);
      }

      // Independently re-fetch the same live page and re-derive whether it carries its own
      // structured publication date, to deterministically cross-check published_at's source.
      const pageRes = await fetch(a.url, { headers: { Accept: "text/html" } });
      expect(pageRes.ok).toBe(true);
      const html = await pageRes.text();
      const explicitDate = extractPublishedDate(html);
      const verifiedDate = explicitDate ? toVerifiedISO(explicitDate) : null;

      if (verifiedDate !== null) {
        // Page carries its own datePublished/meta date — published_at must match it exactly
        // and provenance must be "source", not the sitemap lastmod and not "unavailable".
        expect(a.date_provenance).toBe("source");
        expect(a.published_at).toBe(verifiedDate);
      } else {
        // No source-authored date exists on the page (the case observed live as of 2026-07) —
        // published_at must be null and provenance "unavailable". It must NEVER be fetch-time
        // (which would make this assertion fail, since fetch time is never `null`) and never
        // the sitemap <lastmod> (which would make it a valid, non-null date here too).
        expect(a.date_provenance).toBe("unavailable");
        expect(a.published_at).toBeNull();
      }
    }

    expect(Array.isArray(errors)).toBe(true);
    // An unverifiable publisher date is NOT a fetch failure — the honest "date unknown" signal
    // already lives in-band on each Article (`published_at`/`date_provenance`, asserted above per
    // article). `errors` must therefore never contain a "publisher date absent" advisory,
    // regardless of `datelessCount`, because pushing one there would propagate into
    // read_news.ts's top-level `unavailable` array and wrongly make a successful fetch look like
    // a broken feed.
    expect(errors.some((e) => e.includes("publisher date absent"))).toBe(false);
  }, 90_000);
});

describe("fetchAllNews -> ingest -> query (live, end-to-end)", () => {
  test("a successful bofainstitute fetch never appears in the top-level `unavailable` array, and its articles are queryable + marked authoritative", async () => {
    const { records, unavailable } = await fetchAllNews({ sources: ["bofainstitute"] });

    // Regression guard for the exact bug: a successful fetch (real articles returned) must never
    // be reported as an unavailable/broken feed.
    expect(records.length).toBeGreaterThan(0);
    expect(unavailable.some((u) => u.startsWith("bofainstitute:"))).toBe(false);

    const db = connect(":memory:");
    // ingest() takes Row[] (Record<string, unknown>[]); cast the same way read_news.ts does
    // when passing typed Article[] records through — the object shapes are fully compatible,
    // only the strict Article interface lacks an index signature.
    ingest(db, records as unknown as Record<string, unknown>[]);

    // Derive a search string from a real fetched article's own title — never a fabricated string.
    const sample = records.find((r) => r.source === "bofainstitute")!;
    expect(sample).toBeDefined();
    const words = sample.title
      .split(/\s+/)
      .filter((w) => w.length > 3)
      .slice(0, 3);
    const searchString = words.join(" ") || sample.title;

    const results = query(db, searchString, { k: 20, days: 400 });
    const bofaEvent = results.find((e) => e.sources.includes("bofainstitute"));
    expect(bofaEvent).toBeDefined();
    expect(bofaEvent!.authoritative).toBe(true);
  }, 60_000);
});
