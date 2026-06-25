/**
 * Feed: CoinDesk
 * Unpaywalled — description + optional <content:encoded>.
 * Usage: bun .agents/scripts/feeds/feed_coindesk.ts [--db path] [--days n]
 */

import { Database } from "bun:sqlite";
import type { Article, FeedResult } from "./types";
import { parseRSS, stripHtml, toISO, isWithinDays, parseArgs } from "./types";
import { openDb, upsertArticle } from "./news_db";

const FEED_URL = "https://www.coindesk.com/arc/outboundfeeds/rss/";

export async function fetchCoindesk(db: Database, days: number): Promise<FeedResult> {
  const result: FeedResult = { source: "coindesk", fetched: 0, inserted: 0, enriched: 0, withinWindow: 0, errors: [] };

  try {
    const resp = await fetch(FEED_URL, {
      headers: { "User-Agent": "FeedBot/1.0 (news aggregator)" },
    });
    if (!resp.ok) {
      result.errors.push(`HTTP ${resp.status} from ${FEED_URL}`);
      return result;
    }

    const xml = await resp.text();
    const items = parseRSS(xml);
    result.fetched = items.length;

    for (const item of items) {
      if (!item.link) continue;
      const publishedAt = toISO(item.pubDate);
      if (!isWithinDays(publishedAt, days)) continue;
      result.withinWindow++;

      const body = item.contentEncoded ? stripHtml(item.contentEncoded) : null;
      const article: Article = {
        source: "coindesk",
        url: item.link,
        title: item.title,
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

  return result;
}

// ── Standalone entry point ──────────────────────────────────────────────────

if (import.meta.main) {
  const { dbPath, days } = parseArgs();
  const db = openDb(dbPath);
  const r = await fetchCoindesk(db, days);
  db.close();
  console.log(`coindesk: fetched=${r.fetched} inserted=${r.inserted} enriched=${r.enriched} errors=${r.errors.length}`);
  if (r.errors.length) console.error("Errors:", r.errors);
  process.exit(r.errors.length ? 1 : 0);
}
