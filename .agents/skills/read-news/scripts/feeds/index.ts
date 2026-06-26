/**
 * index.ts — unified registry for all news feeds.
 *
 * fetchAllNews({ sources, assets }) fetches every requested feed sequentially
 * (polite ~300ms gap) and returns normalized Article records plus per-feed failures.
 *
 * The 3 market sources (tradingview, coinmarketcap, googlefinance) are per-asset
 * and are NOT in the default NEWS_FEEDS firehose — they are fetched only when
 * explicitly requested via opts.sources.
 */

import type { Article } from "../types";
import { sleep } from "../types";
import { fetchAllSections } from "./ft";
import type { FtArticle } from "./ft";
import { fetchAllFeeds } from "./wsj";
import type { WsjArticle } from "./wsj";
import { fetchCryptoFeed, CRYPTO_FEED_URLS } from "./crypto";
import {
  fetchTradingViewNews,
  fetchCmcNews,
  fetchGoogleFinanceNews,
  fetchMarketNews,
  DEFAULT_MARKET_ASSETS,
} from "./markets";

const CRYPTO_SOURCES = Object.keys(CRYPTO_FEED_URLS);

// The default firehose — does NOT include market sources (per-asset, N×asset fetches)
export const NEWS_FEEDS: string[] = ["ft", "wsj", ...CRYPTO_SOURCES];

// Known per-asset market sources
const MARKET_SOURCES = new Set(["tradingview", "coinmarketcap", "googlefinance"]);

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
}): Promise<{ records: Article[]; unavailable: string[] }> {
  const requested = opts?.sources ?? NEWS_FEEDS;
  const assets = opts?.assets ?? DEFAULT_MARKET_ASSETS;
  const records: Article[] = [];
  const unavailable: string[] = [];

  // Separate market sources from standard feeds
  const marketSourcesRequested = requested.filter(s => MARKET_SOURCES.has(s));
  const standardRequested = requested.filter(s => !MARKET_SOURCES.has(s));

  for (const name of standardRequested) {
    if (name === "ft") {
      const { articles, errors } = await fetchAllSections();
      records.push(...articles.map(ftToArticle));
      if (errors.length) unavailable.push(`ft:${errors.join("; ")}`);
    } else if (name === "wsj") {
      const { articles, errors } = await fetchAllFeeds();
      records.push(...articles.map(wsjToArticle));
      if (errors.length) unavailable.push(`wsj:${errors.join("; ")}`);
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
          const isCrypto = ["BTC","ETH","SOL","TON","HYPE","AAVE","JUP","UNI","AERO","PUMP","LINK"].includes(upper);
          const gfSym = isCrypto ? `${upper}USD:CRYPTO` : `${upper}:NASDAQ`;
          const { articles, errors } = await fetchGoogleFinanceNews(gfSym);
          records.push(...articles);
          for (const e of errors) unavailable.push(`googlefinance:${e}`);
        }
      } catch (e) {
        unavailable.push(`${sourceName}:${e instanceof Error ? e.message : String(e)}`);
      }
      await sleep(300);
    }
  }

  return { records, unavailable };
}
