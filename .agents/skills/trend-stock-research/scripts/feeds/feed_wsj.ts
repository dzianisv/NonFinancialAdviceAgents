/**
 * Feed: Wall Street Journal (WSJ) — trend-stock-research ingest ADAPTER.
 *
 * Single source of truth for WSJ endpoints + RSS parsing is the feed-wsj skill's on-demand fetcher
 * (../../../feed-wsj/scripts/fetch_wsj.ts), backed by Dow Jones' official public RSS on
 * feeds.content.dowjones.io. This adapter calls its `fetchAllFeeds()` — which returns normalized
 * www.wsj.com URLs, decoded teasers (WSJ emits hexadecimal HTML entities like &#x2019;), titles with
 * the " - The Wall Street Journal" suffix stripped, and ISO dates — then adds only the pipeline glue:
 * date-window filter, DB dedup and SQLite upsert. WSJ bodies are paywalled, so body stays null;
 * absent teaser already arrives as "[UNAVAILABLE - paywall]" (never fabricated).
 *
 * Usage: bun .agents/skills/trend-stock-research/scripts/feeds/feed_wsj.ts [--db path] [--days n] [--no-enrich]
 */

import { Database } from "bun:sqlite";
import type { Article, FeedResult } from "./types";
import { isWithinDays, parseArgs } from "./types";
import { openDb, upsertArticle, hasArticle } from "./news_db";
import { fetchAllFeeds } from "../../../feed-wsj/scripts/fetch_wsj";

export async function fetchWSJ(
  db: Database,
  days: number,
  _noEnrich = false,
): Promise<FeedResult> {
  const result: FeedResult = { source: "wsj", fetched: 0, inserted: 0, enriched: 0, withinWindow: 0, errors: [] };

  const { articles, errors } = await fetchAllFeeds();
  result.errors.push(...errors);
  result.fetched = articles.length;

  for (const a of articles) {
    if (!isWithinDays(a.published_at, days)) continue;
    result.withinWindow++;

    // Canonical fetcher already normalized the URL; dedup against DB (also dedups across the 4 feeds
    // within this run, since the first upsert makes hasArticle() true for the rest).
    if (hasArticle(db, a.url)) continue;

    // Body stays null — WSJ articles are paywalled. summary = publisher's own RSS teaser.
    const article: Article = {
      source: "wsj",
      url: a.url,
      title: a.title,
      summary: a.summary,
      body: null,
      published_at: a.published_at,
      lang: "en",
      tags: a.tags,
    };

    if (upsertArticle(db, article)) result.inserted++;
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
    console.warn("⚠ STALE: Dow Jones RSS returned articles but none within date window.");
  }
  if (r.errors.length) console.error("Errors:", r.errors);
  process.exit(r.errors.length ? 1 : 0);
}
