#!/usr/bin/env bun
import { mkdirSync } from "fs";
import path from "path";

const SKILL_DIR = path.resolve(import.meta.dir, "..");
const KB_DIR = path.join(SKILL_DIR, "kb");
const INDEX_FILE = path.join(SKILL_DIR, "references", "article-index.md");

const SUPPLEMENTAL_URLS = [
  "https://www.lynalden.com/broken-money-explainer-video/",
  "https://www.lynalden.com/the-power-of-nostr/",
  "https://www.lynalden.com/the-stolguard-incident/",
  "https://www.lynalden.com/twitter-compromised/",
];

const EXCLUDE_SLUGS = new Set([
  "",
  "about-lyn-alden",
  "contact",
  "legal",
  "privacy-policy",
  "support",
  "premium",
  "members",
  "login",
  "feed",
  "investment-calculator",
  "investing-newsletter",
  "newsletter-archives",
  "archives",
  "broken-money",
]);

const UA = "curl/7.88.1";

function extractUrls(content: string): string[] {
  const re = /https:\/\/www\.lynalden\.com\/([^/ )>\n\r"']+)\//g;
  const urls: string[] = [];
  let m: RegExpExecArray | null;
  while ((m = re.exec(content)) !== null) {
    urls.push(`https://www.lynalden.com/${m[1]}/`);
  }
  return urls;
}

function isValidUrl(url: string): boolean {
  try {
    const u = new URL(url);
    if (u.search) return false; // no query strings
    const parts = u.pathname.replace(/^\//, "").replace(/\/$/, "").split("/");
    if (parts.length !== 1) return false; // only top-level slugs
    const slug = parts[0];
    if (EXCLUDE_SLUGS.has(slug)) return false;
    if (slug.startsWith("wp-")) return false;
    if (url.includes("/wp-content/") || url.includes("/wp-json/") || url.includes("xmlrpc.php"))
      return false;
    // must match lynalden slug pattern
    if (!/^[a-z0-9-]+$/.test(slug)) return false;
    return true;
  } catch {
    return false;
  }
}

function slugFromUrl(url: string): string {
  const u = new URL(url);
  return u.pathname.replace(/^\//, "").replace(/\/$/, "");
}

function extractMeta(html: string, property: string): string {
  const re = new RegExp(
    `<meta[^>]+property=["']${property}["'][^>]+content=["']([^"']*?)["']`,
    "i"
  );
  let m = re.exec(html);
  if (m) return m[1];
  // Try reversed attribute order
  const re2 = new RegExp(
    `<meta[^>]+content=["']([^"']*?)["'][^>]+property=["']${property}["']`,
    "i"
  );
  m = re2.exec(html);
  return m ? m[1] : "";
}

function extractTitle(html: string): string {
  const re = /<h1[^>]*class=["'][^"']*entry-title[^"']*["'][^>]*>([\s\S]*?)<\/h1>/i;
  let m = re.exec(html);
  if (!m) {
    const re2 = /<h1[^>]*>([\s\S]*?)<\/h1>/i;
    m = re2.exec(html);
  }
  return m ? stripTags(m[1]).trim() : "";
}

function extractBody(html: string): string {
  const re = /<div[^>]+class=["'][^"']*entry-content[^"']*["'][^>]*>([\s\S]*?)<\/div>\s*<\/article>/i;
  let m = re.exec(html);
  if (!m) {
    // Try broader match
    const re2 = /<div[^>]+class=["'][^"']*entry-content[^"']*["'][^>]*>([\s\S]*)/i;
    m = re2.exec(html);
    if (!m) return "";
    // Find closing </div> at same nesting level
    let depth = 1;
    let i = 0;
    const s = m[1];
    let end = s.length;
    while (i < s.length && depth > 0) {
      const open = s.indexOf("<div", i);
      const close = s.indexOf("</div>", i);
      if (close === -1) break;
      if (open !== -1 && open < close) {
        depth++;
        i = open + 4;
      } else {
        depth--;
        if (depth === 0) {
          end = close;
          break;
        }
        i = close + 6;
      }
    }
    return s.slice(0, end);
  }
  return m[1];
}

function stripTags(html: string): string {
  return html.replace(/<[^>]+>/g, "");
}

function unescapeHtml(s: string): string {
  return s
    .replace(/&amp;/g, "&")
    .replace(/&#038;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#8217;/g, "'")
    .replace(/&#8216;/g, "'")
    .replace(/&#8220;/g, '"')
    .replace(/&#8221;/g, '"')
    .replace(/&#8230;/g, "...")
    .replace(/&hellip;/g, "...")
    .replace(/&ndash;/g, "–")
    .replace(/&mdash;/g, "—")
    .replace(/&nbsp;/g, " ")
    .replace(/&lsquo;/g, "'")
    .replace(/&rsquo;/g, "'")
    .replace(/&ldquo;/g, '"')
    .replace(/&rdquo;/g, '"')
    .replace(/&#[0-9]+;/g, (e) => {
      const code = parseInt(e.slice(2, -1), 10);
      return String.fromCharCode(code);
    });
}

function htmlToMarkdown(html: string): string {
  let md = html;

  // Strip script/style/noscript blocks
  md = md.replace(/<script[\s\S]*?<\/script>/gi, "");
  md = md.replace(/<style[\s\S]*?<\/style>/gi, "");
  md = md.replace(/<noscript[\s\S]*?<\/noscript>/gi, "");

  // Strip figure blocks (share/social widgets)
  md = md.replace(/<figure[\s\S]*?<\/figure>/gi, "");

  // Strip WordPress footer boilerplate
  md = md.replace(/<p[^>]*>[\s\S]*?The post[\s\S]*?appeared first on[\s\S]*?<\/p>/gi, "");

  // Headings
  md = md.replace(/<h6[^>]*>([\s\S]*?)<\/h6>/gi, (_, t) => `###### ${stripTags(t).trim()}\n\n`);
  md = md.replace(/<h5[^>]*>([\s\S]*?)<\/h5>/gi, (_, t) => `##### ${stripTags(t).trim()}\n\n`);
  md = md.replace(/<h4[^>]*>([\s\S]*?)<\/h4>/gi, (_, t) => `#### ${stripTags(t).trim()}\n\n`);
  md = md.replace(/<h3[^>]*>([\s\S]*?)<\/h3>/gi, (_, t) => `### ${stripTags(t).trim()}\n\n`);
  md = md.replace(/<h2[^>]*>([\s\S]*?)<\/h2>/gi, (_, t) => `## ${stripTags(t).trim()}\n\n`);
  md = md.replace(/<h1[^>]*>([\s\S]*?)<\/h1>/gi, (_, t) => `# ${stripTags(t).trim()}\n\n`);

  // Bold / italic
  md = md.replace(/<strong[^>]*>([\s\S]*?)<\/strong>/gi, (_, t) => `**${stripTags(t).trim()}**`);
  md = md.replace(/<b[^>]*>([\s\S]*?)<\/b>/gi, (_, t) => `**${stripTags(t).trim()}**`);
  md = md.replace(/<em[^>]*>([\s\S]*?)<\/em>/gi, (_, t) => `*${stripTags(t).trim()}*`);
  md = md.replace(/<i[^>]*>([\s\S]*?)<\/i>/gi, (_, t) => `*${stripTags(t).trim()}*`);

  // Links
  md = md.replace(/<a[^>]+href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi, (_, href, text) => {
    const t = stripTags(text).trim();
    return t ? `[${t}](${href})` : href;
  });

  // Images
  md = md.replace(/<img[^>]+>/gi, (tag) => {
    const src = /src=["']([^"']+)["']/.exec(tag)?.[1] ?? "";
    const alt = /alt=["']([^"']*?)["']/.exec(tag)?.[1] ?? "";
    return src ? `![${alt}](${src})` : "";
  });

  // Lists
  md = md.replace(/<li[^>]*>([\s\S]*?)<\/li>/gi, (_, t) => `- ${stripTags(t).trim()}\n`);
  md = md.replace(/<\/?[uo]l[^>]*>/gi, "\n");

  // Blockquotes
  md = md.replace(/<blockquote[^>]*>([\s\S]*?)<\/blockquote>/gi, (_, content) => {
    const text = stripTags(content)
      .trim()
      .split("\n")
      .map((l) => `> ${l}`)
      .join("\n");
    return `\n${text}\n\n`;
  });

  // Paragraphs and line breaks
  md = md.replace(/<\/p>/gi, "\n\n");
  md = md.replace(/<p[^>]*>/gi, "");
  md = md.replace(/<br\s*\/?>/gi, "\n");

  // Strip remaining tags
  md = md.replace(/<[^>]+>/g, "");

  // Unescape HTML entities
  md = unescapeHtml(md);

  // Collapse excessive blank lines
  md = md.replace(/\n{3,}/g, "\n\n");

  return md.trim();
}

interface Article {
  url: string;
  slug: string;
  title: string;
  date: string;
  description: string;
  wordCount: number;
}

async function fetchArticle(
  url: string
): Promise<{ ok: true; article: Article } | { ok: false; reason: string }> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30000);
  try {
    const res = await fetch(url, {
      headers: { "User-Agent": UA },
      signal: controller.signal,
    });
    clearTimeout(timeout);
    if (!res.ok) return { ok: false, reason: `HTTP ${res.status}` };
    const html = await res.text();

    const title = extractTitle(html) || slugFromUrl(url);
    const date = extractMeta(html, "article:published_time").slice(0, 10) || "unknown";
    const description = unescapeHtml(extractMeta(html, "og:description"));
    const bodyHtml = extractBody(html);
    const bodyMd = htmlToMarkdown(bodyHtml);
    const wordCount = bodyMd.split(/\s+/).filter(Boolean).length;
    const slug = slugFromUrl(url);

    const frontmatter = `---\ntitle: ${title.replace(/:/g, "&#58;")}\nurl: ${url}\ndate: ${date}\n---\n\n# ${title}\n\n${bodyMd}`;
    const outPath = path.join(KB_DIR, `${slug}.md`);
    await Bun.write(outPath, frontmatter);

    return { ok: true, article: { url, slug, title, date, description, wordCount } };
  } catch (e: unknown) {
    clearTimeout(timeout);
    const msg = e instanceof Error ? e.message : String(e);
    return { ok: false, reason: msg };
  }
}

async function main() {
  mkdirSync(KB_DIR, { recursive: true });

  // Collect URLs
  const indexContent = await Bun.file(INDEX_FILE).text();
  const fromIndex = extractUrls(indexContent);
  const all = [...new Set([...fromIndex, ...SUPPLEMENTAL_URLS])].filter(isValidUrl);
  all.sort();

  console.log(`Total URLs to process: ${all.length}`);

  const successes: Article[] = [];
  const failures: { url: string; reason: string }[] = [];

  for (let i = 0; i < all.length; i++) {
    const url = all[i];
    const result = await fetchArticle(url);
    if (result.ok) {
      const a = result.article;
      console.log(`[${i + 1}/${all.length}] ${url} - ${a.title} (${a.wordCount} words)`);
      successes.push(a);
    } else {
      console.log(`[FAIL] ${url} - ${result.reason}`);
      failures.push({ url, reason: result.reason });
    }
    if (i < all.length - 1) await Bun.sleep(350);
  }

  // Generate INDEX.md
  const sorted = [...successes].sort((a, b) => {
    if (a.date === "unknown" && b.date === "unknown") return a.title.localeCompare(b.title);
    if (a.date === "unknown") return 1;
    if (b.date === "unknown") return -1;
    return b.date.localeCompare(a.date);
  });

  const rows = sorted
    .map((a) => {
      const summary = (a.description || "").slice(0, 140);
      return `| ${a.date} | [${a.title}](./${a.slug}.md) | ${a.slug} | ${summary} |`;
    })
    .join("\n");

  const indexMd = `# Lyn Alden Article Knowledge Base

Built: 2026-06-29 | Total: ${successes.length} articles

| Date | Title | Slug | Summary |
|------|-------|------|---------|
${rows}
`;

  await Bun.write(path.join(KB_DIR, "INDEX.md"), indexMd);

  console.log(`\n✓ Downloaded: ${successes.length} articles`);
  console.log(`✗ Failed: ${failures.length} articles`);
  if (failures.length > 0) {
    console.log("Failed URLs:");
    for (const f of failures) {
      console.log(`  - ${f.url}: ${f.reason}`);
    }
  }
}

main();
