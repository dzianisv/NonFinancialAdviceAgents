#!/usr/bin/env bun
/**
 * read_news.ts — unified news-fetch orchestrator.
 *
 * Flow: fetchAllNews → ingest (in-process) → query or newSince → print JSON.
 * Output keys: {fetched, feeds_ok, unavailable, events}.
 *
 * --asset <SYM>    also fetches per-asset market sources for that asset and queries by asset.
 * --assets <CSV>   batch form of --asset; coexists with --asset (merged, deduped).
 * --equities-only  opt-in filter: drops CoinMarketCap (crypto-only) from the per-asset sources
 *                  and drops the crypto-only RSS firehose feeds, unless --source was explicitly
 *                  given (an explicit --source always wins).
 */

import { connect, ingest, query, newSince, queryByAsset } from "./news_store";
import { fetchAllNews, NEWS_FEEDS, CRYPTO_SOURCES } from "./feeds/index";
import type { Article } from "./types";

// ── Arg parsing ──────────────────────────────────────────────────────────────

interface ReadNewsOpts {
  db?: string;
  days?: number;
  k?: number;
  query?: string;
  sources?: string[];
  asset?: string;
  assets?: string[];
  equitiesOnly?: boolean;
}

interface ReadNewsResult {
  fetched: number;
  feeds_ok: number;
  unavailable: string[];
  events: unknown[];
  by_asset?: Record<string, unknown[]>;
  note?: string;
}

export function parseCliArgsFromTokens(args: string[]): ReadNewsOpts {
  const opts: ReadNewsOpts = {};

  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--db" && args[i + 1]) {
      opts.db = args[++i];
    } else if (args[i] === "--days" && args[i + 1]) {
      opts.days = parseInt(args[++i], 10);
    } else if (args[i] === "--k" && args[i + 1]) {
      opts.k = parseInt(args[++i], 10);
    } else if (args[i] === "--query" && args[i + 1]) {
      opts.query = args[++i];
    } else if (args[i] === "--source" && args[i + 1]) {
      opts.sources = args[++i].split(",").map((s) => s.trim()).filter(Boolean);
    } else if (args[i] === "--asset" && args[i + 1]) {
      opts.asset = args[++i];
    } else if (args[i] === "--assets" && args[i + 1]) {
      opts.assets = args[++i].split(",").map((s) => s.trim()).filter(Boolean);
    } else if (args[i] === "--equities-only") {
      opts.equitiesOnly = true;
    }
  }

  return opts;
}

function parseCliArgs(): ReadNewsOpts {
  return parseCliArgsFromTokens(process.argv.slice(2));
}

// ── Core logic (exported for tests) ─────────────────────────────────────────

// Crypto-only firehose feeds (excludes "bloomberg", which is general markets/macro, not crypto-specific)
const CRYPTO_ONLY_SOURCES = new Set(CRYPTO_SOURCES.filter((s) => s !== "bloomberg"));

// The 5 keyless per-asset sources fetched whenever --asset/--assets is used (see README.md/SKILL.md,
// which document Yahoo Finance as one of the 5). Exported so tests can assert on it directly without
// making network calls via runReadNews/fetchAllNews.
export const DEFAULT_ASSET_SOURCES = ["tradingview", "coinmarketcap", "googlefinance", "morningstar", "yahoo"];

export async function runReadNews(opts: ReadNewsOpts = {}): Promise<ReadNewsResult> {
  const dbPath = opts.db ?? process.env.CRYPTO_NEWS_DB ?? ".cache/read-news/news.db";
  const days = opts.days ?? 3;
  const k = opts.k ?? 15;
  const queryStr = opts.query ?? "";
  const sources = opts.sources;

  // Merge --asset and --assets into one deduped, uppercased list. Using BOTH flags together is
  // supported (merged), but the common case is either/or.
  const assetList = Array.from(new Set([
    ...(opts.assets ?? []),
    ...(opts.asset ? [opts.asset] : []),
  ].map((a) => a.toUpperCase())));

  let fetchSources = sources;
  let fetchAssets: string[] | undefined;

  // When --asset/--assets is set, also pull per-asset market sources for those assets
  if (assetList.length > 0) {
    fetchAssets = assetList;
    let assetSources = DEFAULT_ASSET_SOURCES;
    if (opts.equitiesOnly) {
      // Opt-in: CoinMarketCap is crypto-only and always irrelevant noise for an equities-only query.
      assetSources = assetSources.filter((s) => s !== "coinmarketcap");
    }
    const baseFirehose = sources ?? NEWS_FEEDS;
    // Opt-in, and ONLY when the caller did not explicitly pass --source (an explicit --source
    // always wins — we never silently override a user's explicit source list). Skips the
    // crypto-only RSS firehose (decrypt/coindesk/cointelegraph/theblock/bitcoinmagazine/coinbase)
    // for an equities-only asset query. This is a deliberate, documented, OPT-IN behavior change —
    // by default (no --equities-only), the exact prior inclusive behavior is preserved unchanged.
    const effectiveFirehose = (opts.equitiesOnly && !sources)
      ? baseFirehose.filter((s) => !CRYPTO_ONLY_SOURCES.has(s))
      : baseFirehose;
    fetchSources = [...effectiveFirehose, ...assetSources];
  }

  const { records, unavailable } = await fetchAllNews({
    sources: fetchSources,
    assets: fetchAssets,
    query: queryStr || undefined,
    days,
  });

  if (records.length === 0) {
    return {
      fetched: 0,
      feeds_ok: 0,
      unavailable,
      events: [],
      note: "all feeds [UNAVAILABLE]",
    };
  }

  const db = connect(dbPath);
  ingest(db, records as unknown as Record<string, unknown>[]);

  let events: unknown[];
  let byAsset: Record<string, unknown[]> | undefined;

  if (assetList.length > 1) {
    // Batch mode: query each requested asset, then union the resulting events (deduped by
    // event_cluster_id) into the flat `events` array for simple consumers, PLUS an additive
    // `by_asset` breakdown for asset-aware consumers. Purely additive — the singular --asset
    // path below is untouched.
    byAsset = {};
    const seen = new Map<number, { event_cluster_id: number }>();
    for (const a of assetList) {
      const evs = queryByAsset(db, a, { days, k });
      byAsset[a] = evs;
      for (const e of evs) {
        if (!seen.has(e.event_cluster_id)) seen.set(e.event_cluster_id, e);
      }
    }
    events = Array.from(seen.values());
  } else if (assetList.length === 1) {
    events = queryByAsset(db, assetList[0], { days, k }); // identical call shape to the old opts.asset path
  } else if (queryStr) {
    events = query(db, queryStr, { days, k, sources });
  } else {
    events = newSince(db, days);
  }

  db.close();

  const allSources = fetchSources ?? NEWS_FEEDS;
  const requestedCount = allSources.length;
  const feedsOk = requestedCount - unavailable.length;

  const result: ReadNewsResult = {
    fetched: records.length,
    feeds_ok: Math.max(0, feedsOk),
    unavailable,
    events,
  };
  if (byAsset) result.by_asset = byAsset;
  if (queryStr && assetList.length === 0 && events.length === 0) {
    result.note = "INSUFFICIENT_DATA — no article cleared the relevance floor for this query"
      + (sources?.length ? ` within source(s) ${sources.join(",")}` : "") + "; do not guess.";
  }
  return result;
}

// ── CLI entry point ──────────────────────────────────────────────────────────

if (import.meta.main) {
  const opts = parseCliArgs();
  const result = await runReadNews(opts);
  console.log(JSON.stringify(result, null, 1));
}
