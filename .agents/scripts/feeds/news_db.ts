/**
 * SQLite database module for feed article storage.
 * Uses bun:sqlite — zero npm deps.
 * Compatible with the existing Python news_store.py schema.
 */

import { Database } from "bun:sqlite";
import { dirname } from "node:path";
import { mkdirSync, existsSync } from "node:fs";
import type { Article } from "./types";
import { normalizeUrl, contentHash } from "./types";

// ── Schema ──────────────────────────────────────────────────────────────────

const CREATE_TABLE = `
CREATE TABLE IF NOT EXISTS articles (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id      INTEGER,
    source        TEXT,
    url           TEXT,
    title         TEXT,
    summary       TEXT,
    published_at  TEXT,
    lang          TEXT DEFAULT 'en',
    tags          TEXT DEFAULT '[]',
    canonical_url TEXT UNIQUE,
    content_hash  TEXT,
    simhash       TEXT,
    ingested_at   TEXT DEFAULT (datetime('now'))
);`;

const CREATE_INDEXES = [
  "CREATE INDEX IF NOT EXISTS idx_art_canon ON articles(canonical_url);",
  "CREATE INDEX IF NOT EXISTS idx_art_hash  ON articles(content_hash);",
];

// ── Public API ──────────────────────────────────────────────────────────────

export function openDb(path: string): Database {
  const dir = dirname(path);
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });

  const db = new Database(path, { create: true });
  db.exec("PRAGMA journal_mode=WAL;");
  db.exec(CREATE_TABLE);
  for (const idx of CREATE_INDEXES) db.exec(idx);
  return db;
}

/**
 * INSERT OR IGNORE by canonical_url.
 * Stores article.body in the DB summary column when available (best text).
 * Returns true if inserted (new), false if duplicate.
 */
export function upsertArticle(db: Database, article: Article): boolean {
  const canonical = normalizeUrl(article.url);
  const hash = contentHash(article.title, article.summary);

  const existing = db.prepare("SELECT 1 FROM articles WHERE canonical_url = ?").get(canonical);
  if (existing) return false;

  const textToStore = article.body || article.summary;

  db.prepare(
    `INSERT INTO articles
       (source, url, title, summary, published_at, lang, tags, canonical_url, content_hash)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
  ).run(
    article.source,
    article.url,
    article.title,
    textToStore,
    article.published_at,
    article.lang,
    JSON.stringify(article.tags),
    canonical,
    hash,
  );

  return true;
}

/** Check if an article URL already exists (avoids expensive enrichment). */
export function hasArticle(db: Database, url: string): boolean {
  const canonical = normalizeUrl(url);
  return !!db.prepare("SELECT 1 FROM articles WHERE canonical_url = ?").get(canonical);
}

/** Query recent articles from a source. */
export function recentArticles(db: Database, source: string, days = 7): Article[] {
  const cutoff = new Date(Date.now() - days * 86_400_000).toISOString();
  const rows = db
    .prepare(
      "SELECT source, url, title, summary, published_at, lang, tags FROM articles WHERE source = ? AND published_at >= ? ORDER BY published_at DESC",
    )
    .all(source, cutoff) as Array<{
    source: string;
    url: string;
    title: string;
    summary: string;
    published_at: string;
    lang: string;
    tags: string;
  }>;

  return rows.map((r) => ({
    source: r.source,
    url: r.url,
    title: r.title,
    summary: r.summary,
    body: null,
    published_at: r.published_at,
    lang: r.lang || "en",
    tags: JSON.parse(r.tags || "[]") as string[],
  }));
}

/** Count total articles, optionally filtered by source. */
export function articleCount(db: Database, source?: string): number {
  if (source) {
    const row = db.prepare("SELECT COUNT(*) as cnt FROM articles WHERE source = ?").get(source) as {
      cnt: number;
    } | null;
    return row?.cnt ?? 0;
  }
  const row = db.prepare("SELECT COUNT(*) as cnt FROM articles").get() as { cnt: number } | null;
  return row?.cnt ?? 0;
}
