/**
 * yahoo.ts — Yahoo Finance headline RSS adapter (self-contained).
 *
 * Ticker/topic-scoped "latest news" via a legacy, unofficial-but-currently-functional Yahoo
 * Finance route: `feeds.finance.yahoo.com/rss/2.0/headline?s=<TICKERS>&region=US&lang=en-US`.
 * Yahoo deprecated much of its old developer RSS network years ago; this specific route still
 * responded with valid RSS 2.0 as of 2026-07-13, but could stop working without notice — same
 * honesty caveat this codebase already documents for the Bloomberg podcast feed ("often 403").
 *
 * Unlike Google News, `<link>` here IS a genuinely navigable citation URL — either a direct
 * third-party publisher URL or a Yahoo-hosted article page. Still, `source: "yahoo"` should be
 * read as "Yahoo Finance's aggregation of this story," not "the original outlet," since Yahoo
 * sometimes hosts syndicated copies rather than the true original publisher.
 *
 * Imports parseRSS/stripHtml/toISO from ../types (no npm deps).
 */

import type { Article } from "../types";
import { parseRSS, stripHtml, toISO } from "../types";

const UA = "FeedBot/1.0 (news aggregator; +https://example.invalid)";

/** Build the Yahoo Finance headline RSS URL for one or more tickers. Pure — no network. */
export function buildYahooRssUrl(
  symbols: string[],
  opts?: { region?: string; lang?: string },
): string {
  const region = opts?.region ?? "US";
  const lang = opts?.lang ?? "en-US";
  const s = symbols.map((sym) => sym.toUpperCase()).join(",");
  const params = new URLSearchParams({ s, region, lang });
  return `https://feeds.finance.yahoo.com/rss/2.0/headline?${params.toString()}`;
}

/**
 * Parse Yahoo Finance headline RSS into normalized Articles. Pure — no network.
 *
 * `symbols` is the list of tickers that were REQUESTED (not per-item info the feed provides —
 * Yahoo's combined multi-ticker feed doesn't indicate which specific ticker triggered each item).
 */
export function parseYahooRssItems(xml: string, symbols: string[]): Article[] {
  const items = parseRSS(xml);
  const articles: Article[] = [];

  // Single requested symbol -> precise attribution is safe. Multiple requested symbols -> tag
  // every article with the full requested list; this is an imprecise best-effort tag (mirrors
  // the existing documented CoinMarketCap caveat in this codebase: "queried asset, CMC NER is
  // noisy" — same honesty pattern, different mechanism).
  const assets = symbols.map((s) => s.toUpperCase());

  for (const item of items) {
    if (!item.link) continue;
    articles.push({
      source: "yahoo",
      url: item.link,
      title: item.title,
      summary: item.description ? stripHtml(item.description) : "[UNAVAILABLE - no teaser in feed]",
      body: null, // always — this feed never carries full body
      published_at: toISO(item.pubDate),
      lang: "en",
      tags: item.categories,
      assets,
    });
  }

  return articles;
}

export async function fetchYahooNews(
  symbols: string[],
): Promise<{ source: string; articles: Article[]; errors: string[] }> {
  const errors: string[] = [];
  const url = buildYahooRssUrl(symbols);

  let xml: string;
  try {
    const ac = new AbortController();
    const timer = setTimeout(() => ac.abort(), 15_000);
    const res = await fetch(url, {
      headers: { "User-Agent": UA, Accept: "application/rss+xml, application/xml, text/xml, */*" },
      signal: ac.signal,
    });
    clearTimeout(timer);
    if (!res.ok) {
      errors.push(`yahoo: HTTP ${res.status} for symbols ${symbols.join(",")}`);
      return { source: "yahoo", articles: [], errors };
    }
    xml = await res.text();
  } catch (e) {
    errors.push(e instanceof Error ? e.message : String(e));
    return { source: "yahoo", articles: [], errors };
  }

  // Zero parsed items (e.g. an unknown/junk ticker returns HTTP 200 with an empty <channel>) is
  // a legitimate "no news" result, not a failure — do not push a fake error.
  const articles = parseYahooRssItems(xml, symbols);
  return { source: "yahoo", articles, errors };
}
