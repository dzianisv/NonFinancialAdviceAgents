import type { Article } from "../types";
import { shortHash } from "../types";

// Morningstar exchange code mapping (NASDAQ → xnas, NYSE → xnys)
const STOCK_EXCHANGE: Record<string, string> = {
  AAPL: "xnas",
  GOOGL: "xnas",
  MSFT: "xnas",
  NVDA: "xnas",
  AMZN: "xnas",
  META: "xnas",
  TSLA: "xnas",
  PYPL: "xnas",
  AMD: "xnas",
};

const KNOWN_CRYPTO = new Set([
  "BTC","ETH","SOL","TON","HYPE","AAVE","JUP","UNI","AERO","PUMP","LINK",
]);

// Nav/UI fragments that appear in <h3> but are not news headlines
const UI_TEXT_RE =
  /^(Home|Markets|Portfolio|News|Insights|Video|Research|Education|Sign In|Sign Up|Premium|Membership|Watch|Listen|Read More|See All|More|Back|Next|Previous|Loading|Subscribe|Log In|Register|Menu|Search|Close|Skip|Morningstar|Contact|About|Learn More|Get Started|Try Free|Unlock|Upgrade|Continue|View All|Show More|Related Articles|Top Stories|Recent News|Latest News|Market News|Company News|Analyst Reports)$/i;

/**
 * Resolve a stock symbol to its Morningstar exchange code. STOCK_EXCHANGE is the
 * single source of truth for "known" listings — returns null for anything not
 * explicitly mapped rather than silently defaulting to NASDAQ (xnas).
 */
export function resolveExchange(asset: string): string | null {
  return STOCK_EXCHANGE[asset.toUpperCase()] ?? null;
}

/**
 * Build a per-headline article URL that keeps the base page URL intact for
 * citation/provenance (a human clicking it still lands on the exact same real
 * Morningstar page) while adding a content-derived, non-tracking discriminator
 * query param. Without this, every headline scraped off one page shares the same
 * canonical_url and every headline after the first is silently dropped as a
 * "duplicate" by news_store's exact-dedup check, even though the title differs.
 */
export function buildHeadlineUrl(pageUrl: string, title: string): string {
  return `${pageUrl}?h=${shortHash(title)}`;
}

export async function fetchMorningstar(
  asset: string,
): Promise<{ source: string; articles: Article[]; errors: string[] }> {
  const errors: string[] = [];
  const articles: Article[] = [];
  const upper = asset.toUpperCase();

  // Morningstar has no crypto pages
  if (KNOWN_CRYPTO.has(upper)) {
    errors.push(`morningstar: not available for crypto asset ${upper}`);
    return { source: "morningstar", articles, errors };
  }

  // Resolve exchange code — refuse to default to NASDAQ for unmapped stocks.
  const exchange = resolveExchange(upper);
  if (!exchange) {
    errors.push(`morningstar: [UNAVAILABLE - unknown exchange for ${upper}; not in STOCK_EXCHANGE map, refusing to default to NASDAQ]`);
    return { source: "morningstar", articles, errors };
  }
  const pageUrl = `https://www.morningstar.com/stocks/${exchange}/${upper.toLowerCase()}/quote`;

  let rawHtml: string;
  try {
    const ac = new AbortController();
    const t = setTimeout(() => ac.abort(), 15_000);
    const res = await fetch(pageUrl, {
      headers: {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        Referer: "https://www.morningstar.com/",
      },
      signal: ac.signal,
    });
    clearTimeout(t);
    if (!res.ok) {
      errors.push(`morningstar: HTTP ${res.status} for ${upper}`);
      return { source: "morningstar", articles, errors };
    }
    rawHtml = await res.text();
  } catch (e) {
    errors.push(`morningstar: fetch failed — ${e instanceof Error ? e.message : String(e)}`);
    return { source: "morningstar", articles, errors };
  }

  // Extract H3 headlines — no timestamps or teasers available in SSR HTML
  const h3Re = /<h3[^>]*>([^<]+)<\/h3>/g;
  const seen = new Set<string>();
  let m: RegExpExecArray | null;
  while ((m = h3Re.exec(rawHtml)) !== null) {
    const text = m[1].replace(/\s+/g, " ").trim();
    if (text.length < 20) continue;       // too short to be a news headline
    if (UI_TEXT_RE.test(text)) continue;  // navigation / UI label
    if (seen.has(text)) continue;         // deduplicate
    seen.add(text);
    articles.push({
      source: "morningstar",
      url: buildHeadlineUrl(pageUrl, text),
      title: text,
      summary: "[headline only — no teaser available]",
      body: null,
      published_at: new Date().toISOString(),
      lang: "en",
      tags: ["morningstar"],
      assets: [upper],
    });
  }

  if (articles.length === 0) {
    errors.push(
      `morningstar: no H3 headlines found for ${upper} (possible paywall or bot-block on ${pageUrl})`,
    );
  }

  return { source: "morningstar", articles, errors };
}
