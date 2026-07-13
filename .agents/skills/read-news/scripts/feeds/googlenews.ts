/**
 * googlenews.ts — Google News RSS discovery adapter (self-contained).
 *
 * DISCOVERY-ONLY: targets a whitelist of publishers (Bloomberg, Reuters, Business Insider,
 * CNBC, Investor's Business Daily) via Google News' `site:` search operator, since those
 * publishers don't offer reliable public direct feeds/APIs of their own. This surfaces
 * headlines + which outlet ran them so a human/agent can decide whether to read further.
 *
 * IMPORTANT: `item.link` is an opaque Google-internal redirect (`news.google.com/rss/articles/...`),
 * NOT a resolved/direct publisher URL — `curl -I` on these links returns a 302 back into a
 * self-referential JS-consent-flow redirect chain on news.google.com itself, not a one-hop
 * redirect to the real publisher. There is no reliable way to resolve the true destination via
 * plain HTTP fetch (it requires client-side JS execution). This adapter NEVER claims the link is
 * a resolved/verified publisher citation, and NEVER fabricates a summary from the RSS
 * `<description>` (which is just repeated HTML anchor markup, not real teaser content).
 *
 * Imports parseRSS/toISO from ../types (no npm deps).
 */

import type { Article } from "../types";
import { parseRSS, toISO } from "../types";

const UA = "FeedBot/1.0 (news aggregator; +https://example.invalid)";

// Recognized publisher aliases -> real domain, used to build `site:` search clauses.
export const PUBLISHER_DOMAINS: Record<string, string> = {
  bloomberg: "bloomberg.com",
  reuters: "reuters.com",
  businessinsider: "businessinsider.com",
  bi: "businessinsider.com", // alias
  cnbc: "cnbc.com",
  ibd: "investors.com", // Investor's Business Daily
};

/**
 * Build a Google News RSS search URL restricted (optionally) to a whitelist of publishers via
 * `site:` clauses, plus a recency window via `when:Nd`. Pure — no network.
 */
export function buildGoogleNewsUrl(
  query: string,
  opts?: { publishers?: string[]; days?: number },
): string {
  const days = opts?.days ?? 7;
  const publishers = opts?.publishers ?? [];

  const siteClauses = publishers
    .map((p) => {
      const key = p.toLowerCase().trim();
      const domain = PUBLISHER_DOMAINS[key] ?? key;
      return domain ? `site:${domain}` : "";
    })
    .filter(Boolean);

  const parts = [query.trim()];
  if (siteClauses.length) parts.push(`(${siteClauses.join(" OR ")})`);
  parts.push(`when:${days}d`);

  const q = parts.filter(Boolean).join(" ");
  const params = new URLSearchParams({ q, hl: "en-US", gl: "US", ceid: "US:en" });
  return `https://news.google.com/rss/search?${params.toString()}`;
}

/**
 * Parse Google News search RSS into normalized, honestly-labeled discovery-only Articles.
 * Pure — no network.
 */
export function parseGoogleNewsItems(xml: string): Article[] {
  const items = parseRSS(xml);
  const articles: Article[] = [];

  for (const item of items) {
    if (!item.link) continue;

    // <source url="https://www.blackrock.com">BlackRock</source> -> genuine publisher domain.
    let publisherDomain: string | null = null;
    if (item.sourceUrl) {
      try {
        const host = new URL(item.sourceUrl).hostname.toLowerCase();
        publisherDomain = host.replace(/^www\./, "") || null;
      } catch {
        publisherDomain = null;
      }
    }

    // Google's <title> is "Real Headline - PublisherName" — split on the LAST " - " as a
    // best-effort heuristic only. If it doesn't cleanly split, leave the name null rather than
    // fabricating one.
    let publisherName: string | null = null;
    const lastSep = item.title.lastIndexOf(" - ");
    if (lastSep !== -1) {
      const tail = item.title.slice(lastSep + 3).trim();
      if (tail) publisherName = tail;
    }

    const tags = ["google-news", "discovery-only"];
    if (publisherName) tags.push(`publisher:${publisherName}`);
    tags.push(...item.categories);

    articles.push({
      source: "googlenews",
      url: item.link, // raw Google redirect link, passed through unchanged — never "resolved"
      title: item.title, // raw, unmodified (never strip the " - Publisher" suffix here)
      summary: `[DISCOVERY-ONLY — Google News aggregation link; no article body fetched; publisher: ${publisherName ?? "unknown"} (${publisherDomain ?? "unresolved"})]`,
      body: null, // always — this source is discovery-only by construction
      published_at: toISO(item.pubDate),
      lang: "en",
      tags,
      assets: [],
    });
  }

  return articles;
}

export async function fetchGoogleNews(
  query: string,
  opts?: { publishers?: string[]; days?: number },
): Promise<{ source: string; articles: Article[]; errors: string[] }> {
  const errors: string[] = [];
  const url = buildGoogleNewsUrl(query, opts);

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
      errors.push(`googlenews: HTTP ${res.status} for query "${query}"`);
      return { source: "googlenews", articles: [], errors };
    }
    xml = await res.text();
  } catch (e) {
    errors.push(e instanceof Error ? e.message : String(e));
    return { source: "googlenews", articles: [], errors };
  }

  // Zero parsed items is a legitimate empty result, not an error.
  const articles = parseGoogleNewsItems(xml);
  return { source: "googlenews", articles, errors };
}
