/**
 * bofainstitute.ts — Bank of America Institute public macro/consumer-research fetcher.
 *
 * Bank of America Institute (institute.bankofamerica.com) is BofA's PUBLIC-facing research arm —
 * "Consumer Checkpoint", "Small Business Checkpoint", monthly employment reads, and economic/
 * consumer-behavior insights, published free with no login. robots.txt allows crawling (only
 * `/cgi-bin/` and `/tmp/` are disallowed) and a real, current sitemap is served at
 * `content/institute/bank-of-america-institute.sitemap.xml`.
 *
 * This is emphatically NOT "BofA Global Research" (the entitlement-gated sell-side analyst/equity-
 * research product) — see SKILL.md "Source classes and access limits". BofA Global Research remains
 * `[UNAVAILABLE - license required]`; nothing here changes that. `source: "bofainstitute"` /
 * tag `"bofa-institute"` must never be presented as, or conflated with, BofA analyst coverage.
 *
 * Fetch strategy: the sitemap lists every page URL with an `<lastmod>` — an UPDATE timestamp (last
 * time the page's content changed), not necessarily the date the page was first published — so this
 * fetcher (1) downloads the sitemap once, (2) keeps only individual insight pages (under
 * `/economic-insights/`, `/transformation/`, `/sustainability/` — excludes hub/index pages like
 * `/economic-insights.html`) whose `<lastmod>` falls within the lookback window (a freshness hint
 * used ONLY to pick which candidate pages are worth fetching — never stored on the resulting
 * `Article`), then (3) fetches each candidate page and reads its own `<title>` + `<meta
 * name="description">` — the site's own headline and teaser, never fabricated. Full body text is NOT
 * extracted (the page body is client-rendered); `body` is always `null`, same honesty ceiling as the
 * Google Finance/Morningstar scrapers.
 *
 * `published_at`: live inspection of institute.bankofamerica.com pages (wedding-spending.html,
 * consumer-checkpoint-february-2025.html, monthly-employment-report-june-2026.html — checked 2026-07)
 * found exactly one JSON-LD block per page, `{"@type":"WebPage", ...}` with no `datePublished`/
 * `dateModified`, and no `<meta property="article:published_time">`, `<meta name="date"/"DC.date">`,
 * or `<time datetime>` element anywhere in the document. There is no source-authored publication
 * date on these pages today. `extractPublishedDate()` below still actively looks for JSON-LD
 * `datePublished` and the common publish-date meta tags (in case BofA adds them, or a page type
 * this fetcher hasn't sampled has them) and uses that verbatim — via `toVerifiedISO()`, which
 * returns `null` on anything that doesn't parse rather than silently defaulting to "now" — when
 * found.
 *
 * When no verifiable date exists — the observed case, today, for every sampled page —
 * `published_at` is `null` and `date_provenance` is `"unavailable"`. Fetch/ingest time is NEVER
 * substituted as a stand-in publication date: presenting the moment we happened to scrape a page
 * as if it were the moment BofA Institute published it would misrepresent our own crawl schedule
 * as authorship time, and would silently corrupt any recency-based ranking or "how old is this"
 * judgment downstream. The sitemap `<lastmod>` is, for the same reason, never substituted in
 * either — it is an update timestamp, not a publication date (see fetch strategy above). The
 * article is still kept (BofA Institute is real, valuable primary-source research and dropping
 * every page for lacking a date field would make the feed useless). This gap is visible per-
 * article, in-band, via `published_at: null` + `date_provenance: "unavailable"` on the returned
 * `Article` — and is deliberately NEVER pushed into this fetcher's `errors` array (and therefore
 * never into `read_news.ts`'s top-level `unavailable` array / `feeds_ok` count). An unverifiable
 * publisher date is not a fetch failure: the sitemap fetch succeeded, the page fetch succeeded,
 * and a real, honestly-dated (or honestly null-dated) article was returned. Treating that as a
 * feed-level failure would misrepresent a successful fetch as broken. See `news_store.ts`
 * `ingest()` for how the store honors `date_provenance` end-to-end
 * (never fabricating `articles.published_at`, while still using ingestion time for its own,
 * separate, honest "when did we first see this" event bookkeeping).
 */

import type { Article } from "../types";
import { stripHtml, sleep } from "../types";

// Exported so the live integration test can fetch the exact same real sitemap independently
// (no fixture/captured copy) and re-derive candidates for cross-checking.
export const SITEMAP_URL =
  "https://institute.bankofamerica.com/content/institute/bank-of-america-institute.sitemap.xml";
const UA =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36";

// How far back (by sitemap <lastmod>) to consider a page "recent" enough to fetch, and how many
// individual pages to fetch per run. BofA Institute publishes on a weekly/monthly cadence (not an
// intraday firehose like FT/WSJ), so 45 days comfortably covers a missed-run gap without turning
// every read_news.ts invocation into a 100+-page crawl of the whole publication archive.
export const DEFAULT_LOOKBACK_DAYS = 45;
export const MAX_ARTICLES = 25;

// Individual insight pages live under these three sections. Hub/index pages (`/economic-insights.html`,
// `/transformation.html`, `/sustainability.html`, `/about.html`, `/subscribe.html`, the homepage, etc.)
// are deliberately excluded — they are navigation, not publications, and re-ingesting them on every
// run would just create a permanently "new" non-event.
const INSIGHT_PATH_RE = /^\/(economic-insights|transformation|sustainability)\/[a-z0-9-]+\.html$/i;

export interface SitemapEntry {
  url: string;
  lastmod: string;
}

function xmlTag(block: string, name: string): string | null {
  const m = block.match(new RegExp(`<${name}(?:\\s[^>]*)?>([\\s\\S]*?)</${name}>`, "i"));
  return m ? m[1].trim() : null;
}

/** Parse a sitemap.xml document into {url, lastmod} entries. Pure — no network. */
export function parseSitemap(xml: string): SitemapEntry[] {
  const out: SitemapEntry[] = [];
  const blocks = xml.match(/<url[\s>][\s\S]*?<\/url>/gi) || [];
  for (const b of blocks) {
    const loc = xmlTag(b, "loc");
    if (!loc) continue;
    out.push({ url: loc.trim(), lastmod: xmlTag(b, "lastmod") || "" });
  }
  return out;
}

/**
 * True only for an individual institute.bankofamerica.com insight page (economic-insights/
 * transformation/sustainability sub-pages) — false for hub pages, the homepage, or any other host.
 */
export function isEligibleInsightUrl(url: string): boolean {
  try {
    const u = new URL(url);
    if (u.hostname.toLowerCase() !== "institute.bankofamerica.com") return false;
    return INSIGHT_PATH_RE.test(u.pathname);
  } catch {
    return false;
  }
}

/** First path segment ("economic-insights" | "transformation" | "sustainability"), or null. */
export function sectionFromUrl(url: string): string | null {
  try {
    const seg = new URL(url).pathname.match(/^\/([a-z0-9-]+)\//i);
    return seg ? seg[1].toLowerCase() : null;
  } catch {
    return null;
  }
}

/** Is this sitemap <lastmod> date within `days` of `nowMs`? Missing/unparseable -> false. */
export function withinLookback(lastmod: string, days: number, nowMs: number = Date.now()): boolean {
  if (!lastmod) return false;
  const t = Date.parse(lastmod);
  if (isNaN(t)) return false;
  return t >= nowMs - days * 86_400_000;
}

/**
 * Extract the page's own <title> and <meta name="description"> — real site-authored copy, never a
 * fabricated summary. Both null if not present (caller decides fallback behavior).
 */
export function extractHeadMeta(html: string): { title: string | null; description: string | null } {
  const titleRaw = xmlTag(html, "title");
  const title = titleRaw ? stripHtml(titleRaw) : null;

  const descMatch = html.match(/<meta\s+name=["']description["']\s+content=["']([\s\S]*?)["']\s*\/?>/i);
  const description = descMatch ? stripHtml(descMatch[1]) : null;

  return { title, description };
}

/**
 * Extract a genuine, source-authored publication date from the page itself — never the sitemap
 * `<lastmod>`. Checks, in order:
 *   1. JSON-LD `datePublished` (any `<script type="application/ld+json">` block — the site's own
 *      structured-data field for "this is when we published this", distinct from `dateModified`,
 *      which is deliberately NOT read here for the same reason `<lastmod>` isn't: a modification
 *      timestamp is not a publication timestamp).
 *   2. `<meta property="article:published_time" content="...">` (Open Graph article convention).
 *   3. `<meta name="date"|"DC.date"|"dcterms.created" content="...">` (common CMS date meta).
 * Live inspection of institute.bankofamerica.com pages (2026-07) found none of these present — the
 * site's JSON-LD is `{"@type":"WebPage"}` with no date fields at all — so this returns `null` on
 * every currently-observed page and the caller records `date_provenance: "unavailable"` (never a
 * fetch-time fallback). Kept as real extraction logic (not a stub) in case BofA adds this metadata
 * later, or a page type outside the three sampled here already has it.
 */
export function extractPublishedDate(html: string): string | null {
  const ldBlocks = html.match(/<script[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi) || [];
  for (const block of ldBlocks) {
    const inner = block.replace(/^<script[^>]*>/i, "").replace(/<\/script>$/i, "");
    try {
      const data = JSON.parse(inner);
      const candidates = Array.isArray(data) ? data : [data];
      for (const d of candidates) {
        if (d && typeof d.datePublished === "string" && d.datePublished.trim()) {
          return d.datePublished.trim();
        }
      }
    } catch {
      // Not valid JSON — ignore this block, don't throw.
    }
  }

  const metaPatterns = [
    /<meta\s+property=["']article:published_time["']\s+content=["']([^"']+)["']/i,
    /<meta\s+name=["']date["']\s+content=["']([^"']+)["']/i,
    /<meta\s+name=["']DC\.date["']\s+content=["']([^"']+)["']/i,
    /<meta\s+name=["']dcterms\.created["']\s+content=["']([^"']+)["']/i,
  ];
  for (const re of metaPatterns) {
    const m = html.match(re);
    if (m && m[1].trim()) return m[1].trim();
  }

  return null;
}

/**
 * Validate + normalize a candidate publication date string extracted from the page itself into a
 * real ISO-8601 datetime, or `null` if it doesn't parse. Deliberately does NOT use `types.ts`'s
 * `toISO()` here — that helper silently falls back to `new Date()` (fetch time) on a parse
 * failure, which is exactly the fabrication this fetcher must avoid. `extractPublishedDate()`
 * pulls from untrusted page content (JSON-LD/meta tags a CMS could populate with anything), so a
 * malformed value must be treated the same as "no date found" (`date_provenance: "unavailable"`),
 * never quietly relabeled as a real, validated date.
 */
export function toVerifiedISO(dateStr: string): string | null {
  const d = new Date(dateStr);
  return isNaN(d.getTime()) ? null : d.toISOString();
}

/**
 * Fetch Bank of America Institute's public sitemap, keep individual insight pages whose sitemap
 * <lastmod> falls within the lookback window (a freshness hint for candidate selection only), and
 * fetch each one's real <title>/<meta description> plus, if present, its own structured publication
 * date. Sequential + polite (300ms gap) like every other fetcher in this pipeline.
 */
export async function fetchBofaInstitute(
  opts: { days?: number; limit?: number; nowMs?: number } = {},
): Promise<{ source: string; articles: Article[]; errors: string[] }> {
  const days = opts.days ?? DEFAULT_LOOKBACK_DAYS;
  const limit = opts.limit ?? MAX_ARTICLES;
  const nowMs = opts.nowMs ?? Date.now();
  const errors: string[] = [];
  const articles: Article[] = [];

  let xml: string;
  try {
    const ac = new AbortController();
    const t = setTimeout(() => ac.abort(), 15_000);
    const res = await fetch(SITEMAP_URL, {
      headers: { "User-Agent": UA, Accept: "application/xml, text/xml" },
      signal: ac.signal,
    });
    clearTimeout(t);
    if (!res.ok) {
      errors.push(`bofainstitute: HTTP ${res.status} fetching sitemap`);
      return { source: "bofainstitute", articles, errors };
    }
    xml = await res.text();
  } catch (e) {
    errors.push(`bofainstitute: sitemap fetch failed — ${e instanceof Error ? e.message : String(e)}`);
    return { source: "bofainstitute", articles, errors };
  }

  const entries = parseSitemap(xml);
  if (!entries.length) {
    errors.push("bofainstitute: [UNAVAILABLE - 0 <url> entries parsed from sitemap; schema may have changed]");
    return { source: "bofainstitute", articles, errors };
  }

  const candidates = entries
    .filter((e) => isEligibleInsightUrl(e.url) && withinLookback(e.lastmod, days, nowMs))
    .sort((a, b) => b.lastmod.localeCompare(a.lastmod))
    .slice(0, limit);

  // Zero candidates within the window is a legitimate quiet period (BofA Institute publishes
  // weekly/monthly, not daily) — NOT an error, so it must never surface as [UNAVAILABLE].
  for (const { url } of candidates) {
    try {
      const ac = new AbortController();
      const t = setTimeout(() => ac.abort(), 15_000);
      const res = await fetch(url, {
        headers: { "User-Agent": UA, Accept: "text/html,application/xhtml+xml" },
        signal: ac.signal,
      });
      clearTimeout(t);
      if (!res.ok) {
        errors.push(`bofainstitute: HTTP ${res.status} for ${url}`);
        continue;
      }
      const html = await res.text();
      const { title, description } = extractHeadMeta(html);
      if (!title) {
        errors.push(`bofainstitute: no <title> found for ${url}`);
        continue;
      }
      const section = sectionFromUrl(url) ?? "institute";
      // Never store the sitemap <lastmod> as published_at — it is an update timestamp, not a
      // publication date (see file header + extractPublishedDate doc). Use the page's own
      // structured publication date when present and it actually parses; otherwise the date is
      // genuinely unknown — `published_at: null` + `date_provenance: "unavailable"` — never a
      // fetch-time fabrication. The article is still kept (see file header rationale); the gap is
      // surfaced per-article via `date_provenance`, never pushed into `errors` (see file header).
      const explicitDate = extractPublishedDate(html);
      const verifiedDate = explicitDate ? toVerifiedISO(explicitDate) : null;
      const published_at: string | null = verifiedDate;
      const date_provenance: "source" | "unavailable" = verifiedDate ? "source" : "unavailable";
      articles.push({
        source: "bofainstitute",
        url,
        title,
        summary: description || "[UNAVAILABLE - no teaser found]",
        body: null,
        published_at,
        date_provenance,
        lang: "en",
        tags: ["bofa-institute", section],
        assets: [],
      });
    } catch (e) {
      errors.push(`bofainstitute: fetch failed for ${url} — ${e instanceof Error ? e.message : String(e)}`);
    }
    await sleep(300);
  }

  // NOTE: an unverifiable publisher date (published_at: null, date_provenance: "unavailable" on
  // individual articles above) is intentionally NEVER pushed into `errors` here. `errors` is
  // reserved for actual fetch failures (bad HTTP status, sitemap fetch/parse failure, a per-page
  // fetch failure, or a missing <title>) that propagate into read_news.ts's top-level
  // `unavailable` array and reduce `feeds_ok`. A dateless-but-successfully-fetched article is not
  // a failure — the honest "date unknown" signal already lives in-band on the Article record
  // itself. Do not reintroduce a `datelessCount`/aggregated-errors-push here: doing so previously
  // made every successful bofainstitute run look broken, since these pages currently carry no
  // publisher-authored date at all (see file header).
  return { source: "bofainstitute", articles, errors };
}
