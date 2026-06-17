/**
 * Feed: Wall Street Journal (WSJ)
 * PAYWALLED — headline + teaser only.
 * Source: Google News RSS filtered to site:wsj.com (official DJ feeds dead since Jan 2025).
 * Google News URLs are opaque redirects (CBM-encoded protobuf); we store them as-is.
 * Dedup key: <guid> (stable per article). Wayback enrichment uses the <source url> when available.
 * Usage: bun .agents/scripts/feeds/feed_wsj.ts [--db path] [--days n] [--no-enrich]
 */

import { Database } from "bun:sqlite";
import type { Article, FeedResult, RSSItem } from "./types";
import {
  parseRSS,
  stripHtml,
  toISO,
  isWithinDays,
  parseArgs,
} from "./types";
import { openDb, upsertArticle, hasArticle } from "./news_db";

// Google News RSS: fresh WSJ articles (last 7d). Official feeds.a.dj.com frozen Jan 2025.
const FEED_URLS = [
  "https://news.google.com/rss/search?q=site%3Awsj.com+when%3A7d&hl=en-US&gl=US&ceid=US%3Aen",
];

/** Strip common suffixes Google News appends to titles */
function cleanTitle(raw: string): string {
  return raw.replace(/\s*[-–—]\s*(The Wall Street Journal|WSJ)\s*$/i, "").trim();
}

/**
 * Google News <source url="..."> is the PUBLISHER homepage (e.g. "https://www.wsj.com"),
 * NOT the article URL. Use item.link (Google News redirect) as the canonical URL.
 * For Wayback enrichment, we can't resolve the real wsj.com article path from here.
 */
function articleUrl(item: RSSItem): string {
  return item.link;
}

export async function fetchWSJ(
  db: Database,
  days: number,
  noEnrich = false,
): Promise<FeedResult> {
  const result: FeedResult = { source: "wsj", fetched: 0, inserted: 0, enriched: 0, withinWindow: 0, errors: [] };

  for (const feedUrl of FEED_URLS) {
    try {
      const resp = await fetch(feedUrl, {
        headers: { "User-Agent": "Mozilla/5.0 (compatible; FeedBot/1.0; +https://example.invalid)" },
      });
      if (!resp.ok) {
        result.errors.push(`HTTP ${resp.status} from ${feedUrl}`);
        continue;
      }

      const xml = await resp.text();
      const items = parseRSS(xml);
      result.fetched += items.length;

      for (const item of items) {
        if (!item.link) continue;
        const publishedAt = toISO(item.pubDate);
        if (!isWithinDays(publishedAt, days)) continue;
        result.withinWindow++;

        const url = articleUrl(item);

        // Dedup on URL (Google News link or resolved wsj.com link)
        if (hasArticle(db, url)) continue;

        let body: string | null = null;
        // Wayback enrichment disabled — Google News URLs are opaque redirects,
        // not resolvable to real wsj.com paths without a headless browser.
        // TODO: If needed, resolve via puppeteer/playwright in a separate pass.

        const article: Article = {
          source: "wsj",
          url,
          title: cleanTitle(item.title),
          summary: stripHtml(item.description),
          body,
          published_at: publishedAt,
          lang: "en",
          tags: item.categories,
        };

        if (upsertArticle(db, article)) {
          result.inserted++;
          if (body) result.enriched++;
        }
      }
    } catch (e: unknown) {
      result.errors.push(e instanceof Error ? e.message : String(e));
    }
  }

  return result;
}

// ── Standalone entry point ──────────────────────────────────────────────────

if (import.meta.main) {
  const { dbPath, days, noEnrich } = parseArgs();
  const db = openDb(dbPath);
  const r = await fetchWSJ(db, days, noEnrich);
  db.close();
  console.log(`wsj: fetched=${r.fetched} window=${r.withinWindow} inserted=${r.inserted} enriched=${r.enriched} errors=${r.errors.length}`);
  if (r.fetched > 0 && r.withinWindow === 0) {
    console.warn("⚠ STALE: Google News returned articles but none within date window.");
  }
  if (r.errors.length) console.error("Errors:", r.errors);
  process.exit(r.errors.length ? 1 : 0);
}
