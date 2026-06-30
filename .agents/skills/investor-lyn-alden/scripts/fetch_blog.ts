#!/usr/bin/env bun
/**
 * fetch_blog.ts — Lyn Alden blog RSS fetcher.
 *
 * Pulls https://www.lynalden.com/feed/, parses RSS 2.0 with raw string
 * methods (zero npm deps), filters to a --days window, and optionally
 * (--full) downloads each article and extracts prose paragraphs.
 */

const FEED_URL = "https://www.lynalden.com/feed/";
const UA =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";
const TIMEOUT_MS = 15_000;
// The live origin sits behind a WAF that 202/503s datacenter IPs, so don't wait
// long on it — fail fast to the reliable Wayback path.
const LIVE_TIMEOUT_MS = 6_000;
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export interface BlogPost {
  title: string;
  url: string;
  date: string; // ISO
  pubDate: string; // raw
  categories: string[];
  teaser: string;
  fullText?: string;
}

async function timedFetch(url: string, timeoutMs: number = TIMEOUT_MS): Promise<string> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      headers: { "User-Agent": UA, Accept: "text/html,application/xml,*/*" },
      signal: ctrl.signal,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.text();
  } finally {
    clearTimeout(t);
  }
}

// Internet Archive endpoints are slower than live origins; give them more room.
const ARCHIVE_TIMEOUT_MS = 30_000;

/** True when the body is a real RSS document (not a WAF challenge / 403 page). */
function looksLikeRss(body: string): boolean {
  return /<rss[\s>]/i.test(body) && /<item[\s>]/i.test(body);
}

/**
 * Fetch the feed, transparently falling back to the Internet Archive when the
 * live site is blocked by its WAF (Sucuri/nginx 403 or JS captcha challenge).
 * Wayback returns the same RSS XML — possibly a little stale, but real and
 * dependency-free. Returns the raw XML plus which source served it.
 */
async function fetchFeedXml(): Promise<{ xml: string; source: "live" | "wayback" }> {
  try {
    const xml = await timedFetch(FEED_URL, LIVE_TIMEOUT_MS);
    if (looksLikeRss(xml)) return { xml, source: "live" };
  } catch {
    /* fall through to Wayback */
  }
  // Resolve the most recent successful Wayback capture, then fetch it raw (id_).
  // web.archive.org occasionally times out, so retry the whole resolution a few times.
  const cdx =
    "https://web.archive.org/cdx/search/cdx?url=lynalden.com/feed/&output=json&filter=statuscode:200&limit=-1";
  let lastErr = "no Wayback snapshot available";
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const meta = await timedFetch(cdx, ARCHIVE_TIMEOUT_MS);
      const ts = (meta.match(/\d{14}/) ?? [])[0];
      if (!ts) {
        lastErr = "no Wayback snapshot in CDX";
        continue;
      }
      const snap = `https://web.archive.org/web/${ts}id_/https://www.lynalden.com/feed/`;
      const xml = await timedFetch(snap, ARCHIVE_TIMEOUT_MS);
      if (looksLikeRss(xml)) return { xml, source: "wayback" };
      lastErr = "Wayback snapshot did not contain RSS";
    } catch (e: any) {
      lastErr = `Wayback fetch failed — ${e?.message ?? e}`;
    }
    await sleep(1_000 * (attempt + 1));
  }
  throw new Error(`live feed blocked and ${lastErr}`);
}

/**
 * Fetch an arbitrary article URL, falling back to its latest Wayback capture if
 * the live site WAF blocks us. Used for --full prose extraction. Returns "" on
 * total failure so the caller never crashes.
 */
async function fetchArticleHtml(url: string): Promise<string> {
  try {
    const html = await timedFetch(url);
    if (/403 - Forbidden|sgcaptcha/i.test(html) === false && html.length > 1000) return html;
  } catch {
    /* fall through to Wayback */
  }
  try {
    const cdx = `https://web.archive.org/cdx/search/cdx?url=${encodeURIComponent(
      url
    )}&output=json&filter=statuscode:200&limit=-1`;
    const meta = await timedFetch(cdx, ARCHIVE_TIMEOUT_MS);
    const ts = (meta.match(/\d{14}/) ?? [])[0];
    if (!ts) return "";
    return await timedFetch(`https://web.archive.org/web/${ts}id_/${url}`, ARCHIVE_TIMEOUT_MS);
  } catch {
    return "";
  }
}

function stripCDATA(s: string): string {
  return s.replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1");
}

function decodeEntities(s: string): string {
  return s
    .replace(/&#x([0-9a-fA-F]+);/g, (_, h) => String.fromCodePoint(parseInt(h, 16)))
    .replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(parseInt(d, 10)))
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;|&apos;/g, "'")
    .replace(/&nbsp;/g, " ")
    .replace(/&hellip;/g, "…")
    .replace(/&#8217;|&rsquo;/g, "'")
    .replace(/&#8216;|&lsquo;/g, "'")
    .replace(/&#8220;|&ldquo;/g, '"')
    .replace(/&#8221;|&rdquo;/g, '"')
    .replace(/&#8211;|&ndash;/g, "–")
    .replace(/&#8212;|&mdash;/g, "—");
}

function stripTags(s: string): string {
  return decodeEntities(
    s
      .replace(/<script[\s\S]*?<\/script>/gi, "")
      .replace(/<style[\s\S]*?<\/style>/gi, "")
      .replace(/<[^>]+>/g, " ")
  )
    .replace(/\s+/g, " ")
    .trim();
}

function extractFirst(block: string, tag: string): string | null {
  const re = new RegExp(`<${tag}\\b[^>]*>([\\s\\S]*?)<\\/${tag}>`, "i");
  const m = block.match(re);
  return m ? stripCDATA(m[1]).trim() : null;
}

function extractAll(block: string, tag: string): string[] {
  const re = new RegExp(`<${tag}\\b[^>]*>([\\s\\S]*?)<\\/${tag}>`, "gi");
  const out: string[] = [];
  let m: RegExpExecArray | null;
  while ((m = re.exec(block))) {
    const v = stripCDATA(m[1]).trim();
    if (v) out.push(v);
  }
  return out;
}

function extractProse(html: string): string {
  let scope = html;
  // Prefer the WordPress entry-content region if we can locate it.
  const ecStart = html.search(/class="[^"]*entry-content[^"]*"/i);
  if (ecStart !== -1) {
    const gt = html.indexOf(">", ecStart);
    if (gt !== -1) scope = html.slice(gt + 1);
  }
  const paras: string[] = [];
  const re = /<p\b[^>]*>([\s\S]*?)<\/p>/gi;
  let m: RegExpExecArray | null;
  while ((m = re.exec(scope))) {
    const text = stripTags(m[1]);
    if (text.length > 40) paras.push(text);
  }
  return paras.join("\n\n");
}

export async function fetchBlog(days: number, full: boolean): Promise<BlogPost[]> {
  const { xml } = await fetchFeedXml();
  const cutoff = Date.now() - days * 86_400_000;
  const items: BlogPost[] = [];

  const itemRe = /<item\b[^>]*>([\s\S]*?)<\/item>/gi;
  let im: RegExpExecArray | null;
  while ((im = itemRe.exec(xml))) {
    const block = im[1];
    const title = decodeEntities(extractFirst(block, "title") ?? "").trim();
    let link = extractFirst(block, "link") ?? "";
    if (!link) link = (extractFirst(block, "guid") ?? "").trim();
    link = decodeEntities(link).trim();
    const pubDate = extractFirst(block, "pubDate") ?? "";
    const categories = extractAll(block, "category").map(decodeEntities);
    const teaser = stripTags(extractFirst(block, "description") ?? "");

    const ts = pubDate ? Date.parse(pubDate) : NaN;
    if (!Number.isNaN(ts) && ts < cutoff) continue;

    items.push({
      title,
      url: link,
      date: Number.isNaN(ts) ? "" : new Date(ts).toISOString(),
      pubDate,
      categories,
      teaser,
    });
  }

  if (full) {
    for (const it of items) {
      if (!it.url) continue;
      try {
        const html = await fetchArticleHtml(it.url);
        it.fullText = html ? extractProse(html) : "";
      } catch {
        it.fullText = "";
      }
    }
  }

  return items;
}

function parseArgs(argv: string[]) {
  const days = argv.includes("--days")
    ? parseInt(argv[argv.indexOf("--days") + 1] ?? "30", 10) || 30
    : 30;
  return { days, json: argv.includes("--json"), full: argv.includes("--full") };
}

if (import.meta.main) {
  const { days, json, full } = parseArgs(process.argv.slice(2));
  try {
    const posts = await fetchBlog(days, full);
    if (json) {
      console.log(JSON.stringify(posts, null, 2));
    } else if (posts.length === 0) {
      console.log(`[UNAVAILABLE] No Lyn Alden blog posts in the last ${days}d.`);
    } else {
      for (const p of posts) {
        const d = p.date ? p.date.slice(0, 10) : "????-??-??";
        console.log(`[${d}] ${p.title} — ${p.url}`);
        if (full && p.fullText) {
          console.log(p.fullText.slice(0, 600) + (p.fullText.length > 600 ? "…" : ""));
          console.log();
        }
      }
    }
  } catch (e: any) {
    console.log(`[UNAVAILABLE] Blog feed fetch failed — ${e?.message ?? e}`);
    process.exit(0);
  }
}
