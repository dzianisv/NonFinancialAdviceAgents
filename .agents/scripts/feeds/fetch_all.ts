/**
 * Orchestrator — runs all 4 feeds sequentially, reports summary table.
 * Usage: bun .agents/scripts/feeds/fetch_all.ts [--db path] [--days n] [--no-enrich]
 */

import { parseArgs } from "./types";
import type { FeedResult } from "./types";
import { openDb, articleCount } from "./news_db";
import { fetchDecrypt } from "./feed_decrypt";
import { fetchCoindesk } from "./feed_coindesk";
import { fetchFT } from "./feed_ft";
import { fetchWSJ } from "./feed_wsj";

const { dbPath, days, noEnrich } = parseArgs();

console.log(`DB: ${dbPath}`);
console.log(`Filter: articles within ${days} days | Wayback enrich: ${!noEnrich}\n`);

const db = openDb(dbPath);
const beforeCount = articleCount(db);

const feeds: Array<{ name: string; fn: () => Promise<FeedResult> }> = [
  { name: "decrypt",  fn: () => fetchDecrypt(db, days) },
  { name: "coindesk", fn: () => fetchCoindesk(db, days) },
  { name: "ft",       fn: () => fetchFT(db, days, noEnrich) },
  { name: "wsj",      fn: () => fetchWSJ(db, days, noEnrich) },
];

const results: FeedResult[] = [];

for (const { name, fn } of feeds) {
  try {
    console.log(`  Fetching ${name}...`);
    const r = await fn();
    results.push(r);
    let warn = "";
    if (r.fetched > 0 && r.withinWindow === 0) {
      warn = " ⚠ STALE — RSS returned articles but none within date window";
    }
    console.log(`  ${name}: ${r.inserted} new / ${r.fetched} total${r.enriched ? ` (${r.enriched} enriched)` : ""}${r.errors.length ? ` [${r.errors.length} errors]` : ""}${warn}`);
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    results.push({ source: name, fetched: 0, inserted: 0, enriched: 0, withinWindow: 0, errors: [msg] });
    console.error(`  ${name}: FAILED — ${msg}`);
  }
}

const afterCount = articleCount(db);
db.close();

// ── Summary table ───────────────────────────────────────────────────────────

console.log("");
const sep  = "------------|---------|----------|----------|-------";
const head = "Feed        | Fetched | Inserted | Enriched | Errors";

console.log(head);
console.log(sep);

const totals = { fetched: 0, inserted: 0, enriched: 0, errors: 0 };

for (const r of results) {
  console.log(
    `${r.source.padEnd(12)}| ${String(r.fetched).padStart(7)} | ${String(r.inserted).padStart(8)} | ${String(r.enriched).padStart(8)} | ${r.errors.length}`,
  );
  totals.fetched += r.fetched;
  totals.inserted += r.inserted;
  totals.enriched += r.enriched;
  totals.errors += r.errors.length;
}

console.log(sep);
console.log(
  `${"TOTAL".padEnd(12)}| ${String(totals.fetched).padStart(7)} | ${String(totals.inserted).padStart(8)} | ${String(totals.enriched).padStart(8)} | ${totals.errors}`,
);

console.log(`\nDB: ${beforeCount} → ${afterCount} articles (+${afterCount - beforeCount})`);

// ── Error detail ────────────────────────────────────────────────────────────

const allErrors = results.flatMap((r) => r.errors.map((e) => `[${r.source}] ${e}`));
if (allErrors.length) {
  console.error("\nErrors:");
  for (const e of allErrors) console.error(`  ${e}`);
}

process.exit(totals.errors > 0 ? 1 : 0);
