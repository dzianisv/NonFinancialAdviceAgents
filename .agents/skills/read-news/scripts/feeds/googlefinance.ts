import type { Article } from "../types";
import { toISO, shortHash } from "../types";

// Asset → Google Finance quote symbol
const GF_SYMBOL: Record<string, string> = {
  // Crypto
  BTC: "BTC-USD:CURRENCY",
  ETH: "ETH-USD:CURRENCY",
  SOL: "SOL-USD:CURRENCY",
  TON: "TON-USD:CURRENCY",
  HYPE: "HYPE-USD:CURRENCY",
  AAVE: "AAVE-USD:CURRENCY",
  JUP: "JUP-USD:CURRENCY",
  UNI: "UNI3-USD:CURRENCY", // UNI conflicts with Union Pacific ticker
  AERO: "AERO-USD:CURRENCY",
  PUMP: "PUMP-USD:CURRENCY",
  LINK: "LINK-USD:CURRENCY",
  // Stocks
  AAPL: "AAPL:NASDAQ",
  GOOGL: "GOOGL:NASDAQ",
  MSFT: "MSFT:NASDAQ",
  NVDA: "NVDA:NASDAQ",
  AMZN: "AMZN:NASDAQ",
  META: "META:NASDAQ",
  TSLA: "TSLA:NASDAQ",
  PYPL: "PYPL:NASDAQ",
  AMD: "AMD:NASDAQ",
};

/**
 * Resolve an asset symbol to its exact Google Finance quote-symbol string.
 * GF_SYMBOL is the single source of truth for "known" assets — it already fully
 * resolves both crypto and stock symbols, so there's no need to guess asset class
 * at lookup time. Returns null for anything not explicitly mapped.
 */
export function resolveGfSymbol(asset: string): string | null {
  return GF_SYMBOL[asset.toUpperCase()] ?? null;
}

/**
 * Extract and evaluate an AF_initDataCallback({key: '<key>', ...}) blob from raw HTML.
 *
 * Google Finance embeds data as JS object literals (single-quoted keys/values), not JSON,
 * so JSON.parse cannot parse them. We use new Function to evaluate safely within this
 * script context (no DOM/browser APIs; runs as a local Bun script).
 */
function parseAfCallback(html: string, key: string): unknown {
  const re = new RegExp(
    `AF_initDataCallback\\(({key:\\s*'${key}'[\\s\\S]*?})\\);\\s*<\\/script>`,
    "s",
  );
  const m = html.match(re);
  if (!m) return null;
  try {
    // eslint-disable-next-line no-new-func
    return new Function(`return (${m[1]})`)();
  } catch {
    return null;
  }
}

/**
 * Extract analyst consensus fields from the ds:5 data array.
 *
 * ds:5 data layout (confirmed from live HTML):
 *   data[0] = [companyName, currency, lowPT, highPT, avgPT, pctUpside,
 *               totalCount, consensusLabel, buyCount, holdCount, sellCount, ...]
 *   data[1] = [[per-analyst entries...], ...]
 *
 * Previous implementation walked the whole tree looking for any length-3
 * integer array as the buy/hold/sell triplet. That never matched because
 * the counts live at indices [8][9][10] of a 13-element summary array, not
 * in a standalone 3-element array — so counts were always 0/0/0.
 *
 * Fix: read indices directly from data[0].
 */
function extractAnalystData(data: unknown): {
  consensus: string;
  buyCount: number;
  holdCount: number;
  sellCount: number;
  avgTarget: string;
  companyName: string;
  currency: string;
  totalCount: number;
} | null {
  if (!Array.isArray(data)) return null;
  const summary = data[0];
  if (!Array.isArray(summary) || summary.length < 11) return null;

  const companyName = typeof summary[0] === "string" ? summary[0] : "";
  const currency    = typeof summary[1] === "string" ? summary[1] : "USD";
  // summary[2] = lowPT, summary[3] = highPT
  const avgTargetNum = typeof summary[4] === "number" ? (summary[4] as number) : null;
  // summary[5] = % upside
  const totalCount   = typeof summary[6] === "number" ? (summary[6] as number) : 0;
  const consensus    = typeof summary[7] === "string" ? (summary[7] as string) : "";
  const buyCount     = typeof summary[8] === "number" ? (summary[8] as number) : 0;
  const holdCount    = typeof summary[9] === "number" ? (summary[9] as number) : 0;
  const sellCount    = typeof summary[10] === "number" ? (summary[10] as number) : 0;

  if (!consensus && avgTargetNum === null) return null;

  return {
    consensus,
    buyCount,
    holdCount,
    sellCount,
    avgTarget: avgTargetNum !== null ? avgTargetNum.toFixed(2) : "",
    companyName,
    currency,
    totalCount,
  };
}

/**
 * Build the analyst-consensus synthetic article's URL.
 *
 * Uses ?view=analyst-consensus so canonicalUrl() produces a distinct key from
 * the bare page URL (canonicalUrl strips # fragments but keeps query params,
 * so this prevents the old-article exact-dedup collision). A content hash of
 * the summary text is appended so identical consensus data still dedupes
 * correctly across idempotent re-runs of the same day, but a genuinely
 * changed snapshot (different buy/hold/sell/avgTarget) produces a new,
 * distinct record instead of being silently dropped as a duplicate.
 */
export function buildConsensusUrl(pageUrl: string, summaryText: string): string {
  return `${pageUrl}?view=analyst-consensus&h=${shortHash(summaryText)}`;
}

export async function fetchGoogleFinance(
  asset: string,
): Promise<{ source: string; articles: Article[]; errors: string[] }> {
  const errors: string[] = [];
  const articles: Article[] = [];
  const upper = asset.toUpperCase();

  // Resolve symbol — GF_SYMBOL is the single source of truth; refuse to guess
  // asset class for unmapped symbols (previously fell back to a crypto pattern).
  const gfSymbol = resolveGfSymbol(upper);
  if (!gfSymbol) {
    errors.push(`googlefinance: [UNAVAILABLE - unknown symbol ${upper}; not in GF_SYMBOL map, refusing to guess whether it is a stock or crypto asset]`);
    return { source: "googlefinance", articles, errors };
  }

  const pageUrl = `https://www.google.com/finance/quote/${encodeURIComponent(gfSymbol)}`;

  let rawHtml: string;
  try {
    const ac = new AbortController();
    const t = setTimeout(() => ac.abort(), 15_000);
    const res = await fetch(pageUrl, {
      headers: {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
      },
      signal: ac.signal,
    });
    clearTimeout(t);
    if (!res.ok) {
      errors.push(`googlefinance: HTTP ${res.status} for ${gfSymbol}`);
      return { source: "googlefinance", articles, errors };
    }
    rawHtml = await res.text();
  } catch (e) {
    errors.push(`googlefinance: fetch failed — ${e instanceof Error ? e.message : String(e)}`);
    return { source: "googlefinance", articles, errors };
  }

  // ── ds:18 — per-asset news articles ─────────────────────────────────────────
  // Item shape: [url, title, source_name, thumb, unix_timestamp, is_video, is_premium,
  //              favicon, [tickers], article_id, null, w, h, timestamp, 1, teaser_text]
  try {
    const parsed18 = parseAfCallback(rawHtml, "ds:18");
    if (!parsed18 || typeof parsed18 !== "object") {
      errors.push(`googlefinance: ds:18 block not found for ${gfSymbol}`);
    } else {
      const data = (parsed18 as Record<string, unknown>).data;
      const newsItems = Array.isArray(data) ? data : [];
      for (const item of newsItems) {
        if (!Array.isArray(item)) continue;
        const url = typeof item[0] === "string" ? item[0] : "";
        const title = typeof item[1] === "string" ? item[1] : "";
        const unixTs = typeof item[4] === "number" ? item[4] : 0;
        const teaser = typeof item[15] === "string" ? item[15] : "";
        if (!url || !title) continue;
        articles.push({
          source: "googlefinance",
          url,
          title,
          summary: teaser,
          body: null,
          published_at: unixTs ? toISO(String(unixTs * 1000)) : new Date().toISOString(),
          lang: "en",
          tags: [],
          assets: [upper],
        });
      }
    }
  } catch (e) {
    errors.push(`googlefinance: ds:18 parse error — ${e instanceof Error ? e.message : String(e)}`);
  }

  // ── ds:5 — analyst consensus synthetic article (best-effort, non-fatal) ──────
  try {
    const parsed5 = parseAfCallback(rawHtml, "ds:5");
    if (parsed5 && typeof parsed5 === "object") {
      const data5 = (parsed5 as Record<string, unknown>).data;
      const analyst = extractAnalystData(data5);
      if (analyst && (analyst.consensus || analyst.buyCount + analyst.holdCount + analyst.sellCount > 0)) {
        const { consensus, buyCount, holdCount, sellCount, avgTarget, companyName, currency, totalCount } = analyst;
        const ratingStr = `${buyCount}B/${holdCount}H/${sellCount}S`;
        const ptStr = avgTarget ? `, avg target ${avgTarget}` : "";
        const summaryText =
          `${companyName || upper} (${upper}): ${totalCount} analysts — ` +
          `${buyCount} Buy, ${holdCount} Hold, ${sellCount} Sell. ` +
          (avgTarget ? `Avg 12-month price target: ${currency} ${avgTarget}.` : "");
        // See buildConsensusUrl() doc comment for why summaryText is hashed into the URL.
        const consensusUrl = buildConsensusUrl(pageUrl, summaryText);
        articles.push({
          source: "googlefinance",
          url: consensusUrl,
          title: `Google Finance Analyst Consensus — ${upper}: ${consensus || "N/A"} (${ratingStr}${ptStr})`,
          summary: summaryText,
          body: null,
          published_at: new Date().toISOString(),
          lang: "en",
          tags: ["analyst-consensus", "google-finance"],
          assets: [upper],
        });
      }
    }
  } catch {
    // ds:5 failure is non-fatal — synthetic article skipped silently
  }

  return { source: "googlefinance", articles, errors };
}
