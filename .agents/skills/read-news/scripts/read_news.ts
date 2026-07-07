#!/usr/bin/env bun
/**
 * read_news.ts — unified news-fetch orchestrator.
 *
 * Flow: fetchAllNews → ingest (in-process) → query or newSince → print JSON.
 * Output keys: {fetched, feeds_ok, unavailable, events}.
 *
 * --asset <SYM>  also fetches TradingView + CMC for that asset and queries by asset.
 */

import { connect, ingest, query, newSince, queryByAsset } from "./news_store";
import { fetchAllNews, NEWS_FEEDS } from "./feeds/index";
import type { Article } from "./types";

// ── Arg parsing ──────────────────────────────────────────────────────────────

interface ReadNewsOpts {
  db?: string;
  days?: number;
  k?: number;
  query?: string;
  sources?: string[];
  asset?: string;
}

interface ReadNewsResult {
  fetched: number;
  feeds_ok: number;
  unavailable: string[];
  events: unknown[];
  note?: string;
}

function parseCliArgs(): ReadNewsOpts {
  const args = process.argv.slice(2);
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
    }
  }

  return opts;
}

// ── Core logic (exported for tests) ─────────────────────────────────────────

export async function runReadNews(opts: ReadNewsOpts = {}): Promise<ReadNewsResult> {
  const dbPath = opts.db ?? process.env.CRYPTO_NEWS_DB ?? ".cache/read-news/news.db";
  const days = opts.days ?? 3;
  const k = opts.k ?? 15;
  const queryStr = opts.query ?? "";
  const sources = opts.sources;

  let fetchSources = sources;
  let fetchAssets: string[] | undefined;

  // When --asset is set, also pull market sources for that specific asset
  if (opts.asset) {
    fetchAssets = [opts.asset];
    fetchSources = [...(sources ?? NEWS_FEEDS), "tradingview", "coinmarketcap", "googlefinance", "morningstar"];
  }

  const { records, unavailable } = await fetchAllNews({ sources: fetchSources, assets: fetchAssets });

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
  if (opts.asset) {
    events = queryByAsset(db, opts.asset, { days, k });
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
  if (queryStr && !opts.asset && events.length === 0) {
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
