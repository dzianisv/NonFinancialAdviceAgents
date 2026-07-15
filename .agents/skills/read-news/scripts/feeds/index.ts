/**
 * index.ts — unified registry for all news feeds.
 *
 * fetchAllNews({ sources, assets, query, days }) fetches every requested feed sequentially
 * (polite ~300ms gap) and returns normalized Article records plus per-feed failures.
 *
 * The 5 market sources (tradingview, coinmarketcap, googlefinance, morningstar, yahoo) are
 * per-asset and are NOT in the default NEWS_FEEDS firehose — they are fetched only when
 * explicitly requested via opts.sources.
 *
 * googlenews is a 6th, fundamentally different, source class: a free-text SEARCH endpoint, not
 * a firehose and not purely ticker-driven. It requires either an explicit opts.query or explicit
 * opts.assets (never the internal DEFAULT_MARKET_ASSETS fallback) — see QUERY_SOURCES below.
 */

import type { Article } from "../types";
import { sleep } from "../types";
import { fetchAllSections } from "./ft";
import type { FtArticle } from "./ft";
import { fetchAllFeeds } from "./wsj";
import type { WsjArticle } from "./wsj";
import { fetchBofaInstitute } from "./bofainstitute";
import { fetchCryptoFeed, CRYPTO_FEED_URLS } from "./crypto";
import {
  fetchTradingViewNews,
  fetchCmcNews,
  DEFAULT_MARKET_ASSETS,
} from "./markets";
import { fetchGoogleFinance } from "./googlefinance";
import { fetchMorningstar } from "./morningstar";
import { fetchYahooNews } from "./yahoo";
import { fetchGoogleNews, PUBLISHER_DOMAINS } from "./googlenews";

export const CRYPTO_SOURCES = Object.keys(CRYPTO_FEED_URLS);

// The default firehose — does NOT include market sources (per-asset, N×asset fetches).
// "bofainstitute" = Bank of America Institute's public macro/consumer research (keyless, sitemap-
// driven) — NOT BofA Global Research (sell-side/analyst research), which remains entitlement-gated
// and unintegrated. See SKILL.md "Source classes and access limits".
export const NEWS_FEEDS: string[] = ["ft", "wsj", "bofainstitute", ...CRYPTO_SOURCES];

// Known per-asset market sources
const MARKET_SOURCES = new Set(["tradingview", "coinmarketcap", "googlefinance", "morningstar", "yahoo"]);

// Free-text discovery sources — query/topic driven, never a ticker firehose (see fetchAllNews).
const QUERY_SOURCES = new Set(["googlenews"]);

// "bi" is just an alias for businessinsider.com — drop it so we don't emit a duplicate
// site:businessinsider.com clause alongside the one from "businessinsider".
export const GOOGLENEWS_DEFAULT_PUBLISHERS = Object.keys(PUBLISHER_DOMAINS).filter((k) => k !== "bi");

function ftToArticle(a: FtArticle): Article {
  return {
    source: a.source,
    url: a.url,
    title: a.title,
    summary: a.summary,
    body: null,
    published_at: a.published_at,
    lang: "en",
    tags: a.tags,
    assets: [],
  };
}

function wsjToArticle(a: WsjArticle): Article {
  return {
    source: a.source,
    url: a.url,
    title: a.title,
    summary: a.summary,
    body: null,
    published_at: a.published_at,
    lang: "en",
    tags: a.tags,
    assets: [],
  };
}

export async function fetchAllNews(opts?: {
  sources?: string[];
  assets?: string[];
  query?: string;
  days?: number;
}): Promise<{ records: Article[]; unavailable: string[] }> {
  const requested = opts?.sources ?? NEWS_FEEDS;
  const assets = opts?.assets ?? DEFAULT_MARKET_ASSETS;
  const records: Article[] = [];
  const unavailable: string[] = [];

  // Separate market sources, query (discovery) sources, and standard firehose feeds
  const marketSourcesRequested = requested.filter(s => MARKET_SOURCES.has(s));
  const querySourcesRequested = requested.filter(s => QUERY_SOURCES.has(s));
  const standardRequested = requested.filter(s => !MARKET_SOURCES.has(s) && !QUERY_SOURCES.has(s));

  for (const name of standardRequested) {
    if (name === "ft") {
      const { articles, errors } = await fetchAllSections();
      records.push(...articles.map(ftToArticle));
      if (errors.length) unavailable.push(`ft:${errors.join("; ")}`);
    } else if (name === "wsj") {
      const { articles, errors } = await fetchAllFeeds();
      records.push(...articles.map(wsjToArticle));
      if (errors.length) unavailable.push(`wsj:${errors.join("; ")}`);
    } else if (name === "bofainstitute") {
      const { articles, errors } = await fetchBofaInstitute();
      records.push(...articles);
      if (errors.length) unavailable.push(`bofainstitute:${errors.join("; ")}`);
    } else if (CRYPTO_FEED_URLS[name] !== undefined) {
      const { articles, errors } = await fetchCryptoFeed(name);
      records.push(...articles);
      if (errors.length) unavailable.push(`${name}:${errors.join("; ")}`);
    } else {
      unavailable.push(`${name}:unknown feed`);
    }
    await sleep(300);
  }

  // Handle per-asset market sources
  for (const sourceName of marketSourcesRequested) {
    for (const asset of assets) {
      const upper = asset.toUpperCase();
      try {
        if (sourceName === "tradingview") {
          // crypto → COINBASE:<SYM>USD, else NASDAQ:<SYM>
          const isCrypto = ["BTC","ETH","SOL","TON","HYPE","AAVE","JUP","UNI","AERO","PUMP","LINK"].includes(upper);
          const tvSym = isCrypto ? `COINBASE:${upper}USD` : `NASDAQ:${upper}`;
          const { articles, errors } = await fetchTradingViewNews(tvSym);
          records.push(...articles);
          for (const e of errors) unavailable.push(`tradingview:${e}`);
        } else if (sourceName === "coinmarketcap") {
          const { articles, errors } = await fetchCmcNews(upper);
          records.push(...articles);
          for (const e of errors) unavailable.push(`coinmarketcap:${e}`);
        } else if (sourceName === "googlefinance") {
          const { articles, errors } = await fetchGoogleFinance(upper);
          records.push(...articles);
          for (const e of errors) unavailable.push(`googlefinance:${e}`);
        } else if (sourceName === "morningstar") {
          const { articles, errors } = await fetchMorningstar(upper);
          records.push(...articles);
          for (const e of errors) unavailable.push(`morningstar:${e}`);
        } else if (sourceName === "yahoo") {
          const { articles, errors } = await fetchYahooNews([upper]);
          records.push(...articles);
          for (const e of errors) unavailable.push(`yahoo:${e}`);
        }
      } catch (e) {
        unavailable.push(`${sourceName}:${e instanceof Error ? e.message : String(e)}`);
      }
      await sleep(300);
    }
  }

  // Handle query (discovery) sources — free-text search, never a bare per-asset firehose.
  for (const sourceName of querySourcesRequested) {
    if (sourceName === "googlenews") {
      const days = opts?.days ?? 7;
      if (opts?.query) {
        try {
          const { articles, errors } = await fetchGoogleNews(opts.query, { publishers: GOOGLENEWS_DEFAULT_PUBLISHERS, days });
          records.push(...articles);
          for (const e of errors) unavailable.push(`googlenews:${e}`);
        } catch (e) {
          unavailable.push(`googlenews:${e instanceof Error ? e.message : String(e)}`);
        }
      } else if (opts?.assets && opts.assets.length) {
        // Asset-mode fallback: use each EXPLICITLY requested asset symbol itself as the search
        // topic (only when the caller passed --asset/--assets — opts?.assets is the raw field,
        // checked before the `?? DEFAULT_MARKET_ASSETS` fallback above is applied — so googlenews
        // never silently searches the 11 default crypto tickers as bare-text queries when the
        // caller gave no asset context at all).
        for (const asset of opts.assets) {
          try {
            const { articles, errors } = await fetchGoogleNews(asset.toUpperCase(), { publishers: GOOGLENEWS_DEFAULT_PUBLISHERS, days });
            records.push(...articles);
            for (const e of errors) unavailable.push(`googlenews:${e}`);
          } catch (e) {
            unavailable.push(`googlenews:${e instanceof Error ? e.message : String(e)}`);
          }
          await sleep(300);
        }
      } else {
        unavailable.push("googlenews: [UNAVAILABLE - no --query or --asset provided; refusing to fetch an unscoped Google News firehose]");
      }
    }
    await sleep(300);
  }

  return { records, unavailable };
}
