import type { Article } from "../types";
import { toISO, stripHtml, sleep } from "../types";

export const DEFAULT_MARKET_ASSETS = ["BTC","ETH","SOL","TON","HYPE","AAVE","JUP","UNI","AERO","PUMP","LINK"];

const MARKET_SOURCES = new Set(["tradingview", "coinmarketcap", "googlefinance"]);

// CMC symbol → slug map
const CMC_SLUG: Record<string, string> = {
  BTC: "bitcoin", ETH: "ethereum", SOL: "solana", TON: "toncoin",
  AAVE: "aave", UNI: "uniswap", LINK: "chainlink", JUP: "jupiter-ag",
  AERO: "aerodrome-finance", PUMP: "pump-fun", HYPE: "hyperliquid",
};

// News domains used to filter Google Finance anchor hrefs
const GF_NEWS_DOMAIN_RE = /(?:reuters|bloomberg|fool|finance\.yahoo|cnbc|marketwatch|barrons|seekingalpha|investing|businessinsider|wsj|ft)\.com/;

export function flattenTvAst(node: unknown): string {
  if (typeof node === "string") return node;
  if (!node || typeof node !== "object") return "";
  const n = node as { type?: string; children?: unknown[]; params?: unknown };
  if (n.type === "story-ref") return "";
  if (Array.isArray(n.children)) {
    const parts: string[] = [];
    for (const child of n.children) {
      const text = flattenTvAst(child);
      if (text) parts.push(text);
    }
    // list items joined with "; "
    if (n.type === "list") return parts.join("; ");
    return parts.join(" ");
  }
  return "";
}

export function tvSymbolToAsset(sym: string): string {
  // "COINBASE:AAVEUSD" → "AAVE", "NASDAQ:AAPL" → "AAPL", "BINANCE:BTCUSDT" → "BTC"
  const part = sym.includes(":") ? sym.split(":")[1] : sym;
  // Strip trailing fiat/stable suffixes for crypto pairs
  const stripped = part.replace(/(?:USDT|USDC|USD|EUR|BTC|ETH)$/, "");
  return (stripped || part).toUpperCase();
}

export function mapCmcItem(item: any, queriedAsset: string): Article {
  const meta = item.meta ?? {};
  const url = meta.sourceUrl || `https://coinmarketcap.com/community/articles/${meta.id ?? ""}`;
  return {
    source: "coinmarketcap",
    url,
    title: meta.title ?? "",
    summary: meta.subtitle ?? "",
    body: null,
    published_at: toISO(item.createdAt ?? ""),
    lang: "en",
    tags: [],
    assets: [queriedAsset.toUpperCase()],
  };
}

export function parseGoogleFinanceHtml(html: string, ticker: string): Article[] {
  const asset = ticker.split(":")[0].toUpperCase();
  const articles: Article[] = [];

  // Real Google Finance structure:
  //   <a href="https://www.reuters.com/..." target="_blank"><div class="TQWIEd">TITLE</div></a>
  // Class names are obfuscated and rotate — match on STRUCTURE, not class names.
  // published_at = current ISO time (no absolute timestamp in HTML).
  const cardRe = /<a\s+href="(https?:\/\/[^"]+)"[^>]*target="_blank"[^>]*>\s*<div[^>]*>([^<]{8,250})<\/div>\s*<\/a>/g;
  let m: RegExpExecArray | null;
  while ((m = cardRe.exec(html)) !== null) {
    const url = m[1];
    if (!GF_NEWS_DOMAIN_RE.test(url)) continue;
    const title = stripHtml(m[2]).trim();
    if (!title || title.length < 8) continue;
    articles.push({
      source: "googlefinance",
      url,
      title,
      summary: "",
      body: null,
      published_at: new Date().toISOString(), // no absolute timestamp in GF HTML
      lang: "en",
      tags: [],
      assets: [asset],
    });
  }

  // deduplicate by url
  const seen = new Set<string>();
  return articles.filter(a => {
    if (seen.has(a.url)) return false;
    seen.add(a.url);
    return true;
  });
}

export async function fetchTradingViewNews(
  symbol: string,
  opts?: { withStory?: boolean; storyLimit?: number }
): Promise<{ articles: Article[]; errors: string[] }> {
  const withStory = opts?.withStory ?? true;
  const storyLimit = opts?.storyLimit ?? 5;
  const errors: string[] = [];
  const articles: Article[] = [];

  try {
    const ac = new AbortController();
    const timer = setTimeout(() => ac.abort(), 15_000);
    const url = `https://news-headlines.tradingview.com/v2/headlines?client=web&lang=en&symbol=${encodeURIComponent(symbol)}`;
    const res = await fetch(url, { signal: ac.signal });
    clearTimeout(timer);
    if (!res.ok) {
      errors.push(`HTTP ${res.status} from TradingView headlines`);
      return { articles, errors };
    }
    const data = await res.json() as { items?: any[] };
    const items = data.items ?? [];

    for (const item of items) {
      const articleUrl = item.link ?? (item.storyPath ? `https://www.tradingview.com${item.storyPath}` : "");
      if (!articleUrl) continue;
      const relatedAssets = Array.isArray(item.relatedSymbols)
        ? item.relatedSymbols.map((s: any) => tvSymbolToAsset(s.symbol ?? "")).filter(Boolean)
        : [];
      articles.push({
        source: "tradingview",
        url: articleUrl,
        title: item.title ?? "",
        summary: "",
        body: null,
        published_at: toISO(String((item.published ?? 0) * 1000)),
        lang: "en",
        tags: [],
        assets: relatedAssets,
      });
    }

    // Fetch story summaries for top N
    if (withStory && storyLimit > 0) {
      const toEnrich = articles.slice(0, storyLimit);
      for (let i = 0; i < toEnrich.length; i++) {
        const originalItem = items[i];
        if (!originalItem?.id) continue;
        try {
          const ac2 = new AbortController();
          const t2 = setTimeout(() => ac2.abort(), 10_000);
          const storyUrl = `https://news-headlines.tradingview.com/v3/story?id=${encodeURIComponent(originalItem.id)}&lang=en`;
          const sr = await fetch(storyUrl, { signal: ac2.signal });
          clearTimeout(t2);
          if (sr.ok) {
            const sd = await sr.json() as { astDescription?: unknown };
            if (sd.astDescription) {
              toEnrich[i].summary = flattenTvAst(sd.astDescription).trim();
            }
          }
        } catch {
          // one story failure doesn't abort the rest
        }
        if (i < toEnrich.length - 1) await sleep(200);
      }
    }
  } catch (e) {
    errors.push(e instanceof Error ? e.message : String(e));
  }

  return { articles, errors };
}

export async function fetchCmcNews(asset: string): Promise<{ articles: Article[]; errors: string[] }> {
  const errors: string[] = [];
  const articles: Article[] = [];
  const upper = asset.toUpperCase();
  const slug = CMC_SLUG[upper] ?? upper.toLowerCase();

  // Step 1: resolve numeric id
  let coinId: number;
  try {
    const ac = new AbortController();
    const t = setTimeout(() => ac.abort(), 10_000);
    const res = await fetch(
      `https://api.coinmarketcap.com/data-api/v3/cryptocurrency/detail/lite?slug=${encodeURIComponent(slug)}`,
      { headers: { Accept: "application/json" }, signal: ac.signal }
    );
    clearTimeout(t);
    if (!res.ok) {
      errors.push(`CMC resolve HTTP ${res.status} for ${slug}`);
      return { articles, errors };
    }
    const d = await res.json() as { data?: { id?: number } };
    const id = d?.data?.id;
    if (!id) {
      errors.push(`CMC: no id found for ${slug}`);
      return { articles, errors };
    }
    coinId = id;
  } catch (e) {
    errors.push(e instanceof Error ? e.message : String(e));
    return { articles, errors };
  }

  // Step 2: fetch news
  try {
    const ac = new AbortController();
    const t = setTimeout(() => ac.abort(), 15_000);
    const res = await fetch(
      `https://api.coinmarketcap.com/content/v3/news?coins=${coinId}&page=1&size=20`,
      { headers: { Accept: "application/json" }, signal: ac.signal }
    );
    clearTimeout(t);
    if (!res.ok) {
      errors.push(`CMC news HTTP ${res.status} for id=${coinId}`);
      return { articles, errors };
    }
    const d = await res.json() as { data?: any[] };
    for (const item of d.data ?? []) {
      articles.push(mapCmcItem(item, upper));
    }
  } catch (e) {
    errors.push(e instanceof Error ? e.message : String(e));
  }

  return { articles, errors };
}

export async function fetchGoogleFinanceNews(symbol: string): Promise<{ articles: Article[]; errors: string[] }> {
  const errors: string[] = [];
  const articles: Article[] = [];
  try {
    const ac = new AbortController();
    const t = setTimeout(() => ac.abort(), 15_000);
    const res = await fetch(`https://www.google.com/finance/quote/${encodeURIComponent(symbol)}`, {
      headers: {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
      },
      signal: ac.signal,
    });
    clearTimeout(t);
    if (!res.ok) {
      errors.push(`Google Finance HTTP ${res.status} for ${symbol}`);
      return { articles, errors };
    }
    const html = await res.text();
    const parsed = parseGoogleFinanceHtml(html, symbol);
    articles.push(...parsed);
  } catch (e) {
    errors.push(e instanceof Error ? e.message : String(e));
  }
  return { articles, errors };
}

export async function fetchMarketNews(
  assets: string[],
  opts?: { tvSymbols?: Record<string, string> }
): Promise<{ records: Article[]; unavailable: string[] }> {
  const records: Article[] = [];
  const unavailable: string[] = [];

  for (const asset of assets) {
    const upper = asset.toUpperCase();
    const tvSymbols = opts?.tvSymbols ?? {};
    const isCrypto = CMC_SLUG[upper] !== undefined || ["BTC","ETH","SOL"].includes(upper);

    // CMC (crypto only)
    if (isCrypto) {
      try {
        const { articles, errors } = await fetchCmcNews(upper);
        records.push(...articles);
        for (const e of errors) unavailable.push(`coinmarketcap:${e}`);
      } catch (e) {
        unavailable.push(`coinmarketcap:${e instanceof Error ? e.message : String(e)}`);
      }
      await sleep(300);
    }

    // TradingView
    try {
      const tvSym = tvSymbols[upper] ?? (isCrypto ? `COINBASE:${upper}USD` : `NASDAQ:${upper}`);
      const { articles, errors } = await fetchTradingViewNews(tvSym);
      records.push(...articles);
      for (const e of errors) unavailable.push(`tradingview:${e}`);
    } catch (e) {
      unavailable.push(`tradingview:${e instanceof Error ? e.message : String(e)}`);
    }
    await sleep(300);
  }

  return { records, unavailable };
}
