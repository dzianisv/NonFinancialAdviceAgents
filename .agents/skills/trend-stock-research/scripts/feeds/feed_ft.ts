/**
 * Feed: Financial Times (FT) — trend-stock-research ingest ADAPTER.
 *
 * Single source of truth for FT endpoints + RSS parsing is the feed-ft skill's on-demand fetcher
 * (../../../feed-ft/scripts/fetch_ft.ts). This adapter calls its `fetchAllSections()` — which returns
 * normalized ft.com/content URLs, decoded 1-sentence teasers (incl. WSJ/FT hex HTML entities), cleaned
 * titles and ISO dates — then adds only the pipeline glue: date-window filter, DB dedup, optional
 * Wayback body enrichment (best-effort; usually blocked by FT's subscribe-wall) and SQLite upsert.
 * Bodies stay paywalled; absent teaser already arrives as "[UNAVAILABLE - paywall]" (never fabricated).
 *
 * Usage: bun .agents/skills/trend-stock-research/scripts/feeds/feed_ft.ts [--db path] [--days n] [--no-enrich]
 */

import { Database } from "bun:sqlite";
import type { Article, FeedResult } from "./types";
import { isWithinDays, parseArgs, sleep, fetchWaybackBody } from "./types";
import { openDb, upsertArticle, hasArticle } from "./news_db";
import { fetchAllSections } from "../../../feed-ft/scripts/fetch_ft";

export async function fetchFT(
  db: Database,
  days: number,
  noEnrich = false,
): Promise<FeedResult> {
  const result: FeedResult = { source: "ft", fetched: 0, inserted: 0, enriched: 0, withinWindow: 0, errors: [] };

  const { articles, errors } = await fetchAllSections();
  result.errors.push(...errors);
  result.fetched = articles.length;

  for (const a of articles) {
    if (!isWithinDays(a.published_at, days)) continue;
    result.withinWindow++;

    // Canonical fetcher already normalized the URL; dedup against DB (also dedups across sections
    // within this run, since the first upsert makes hasArticle() true for the rest).
    if (hasArticle(db, a.url)) continue;

    let body: string | null = null;
    if (!noEnrich) {
      body = await fetchWaybackBody(a.url);
      await sleep(1000); // polite delay between Wayback requests
    }

    const article: Article = {
      source: "ft",
      url: a.url,
      title: a.title,
      summary: a.summary,
      body,
      published_at: a.published_at,
      lang: "en",
      tags: a.tags,
    };

    if (upsertArticle(db, article)) {
      result.inserted++;
      if (body) result.enriched++;
    }
  }

  return result;
}

// ── Standalone entry point ──────────────────────────────────────────────────

if (import.meta.main) {
  const { dbPath, days, noEnrich } = parseArgs();
  const db = openDb(dbPath);
  const r = await fetchFT(db, days, noEnrich);
  db.close();
  console.log(`ft: fetched=${r.fetched} inserted=${r.inserted} enriched=${r.enriched} errors=${r.errors.length}`);
  if (r.fetched > 0 && r.withinWindow === 0) {
    console.warn("⚠ STALE: RSS returned articles but none within date window.");
  }
  if (r.errors.length) console.error("Errors:", r.errors);
  process.exit(r.errors.length ? 1 : 0);
}
