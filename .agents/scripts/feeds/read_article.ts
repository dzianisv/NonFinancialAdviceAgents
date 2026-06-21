#!/usr/bin/env bun
// read_article.ts — fetch full body of a (possibly paywalled) article URL.
// Usage: bun read_article.ts <url> [--no-cache]
// Ladder: cache → Wayback (WSJ/others) → archive.ph CDP (FT) → direct fetch
// Skipped: Bing cache (DNS dead), Google cache (error page), archive.ph curl (CAPTCHA)

import { $ } from "bun";

const FETCH_PY = "/Users/engineer/workspace/backtest/.agents/scripts/feeds/fetch_article.py";
const CHROME = "/Users/engineer/.agents/skills/chrome-use/scripts/chrome-use";

const UA =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";

const argv = process.argv.slice(2);
const url = argv.find((a) => !a.startsWith("--"));
const noCache = argv.includes("--no-cache");

if (!url) {
  console.error("Usage: bun read_article.ts <url> [--no-cache]");
  process.exit(1);
}

function stripHtml(html: string): string {
  return html
    .replace(/<(script|style|nav|header|footer|noscript)[^>]*>[\s\S]*?<\/\1>/gi, "")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

const PAYWALL_RE = /subscribe to read|sign in to read|subscription required/i;
const CAPTCHA_RE = /security check|captcha|cloudflare|ddos-guard|verify you are human/i;

function isValidContent(text: string): boolean {
  if (text.length < 500) return false;
  if (PAYWALL_RE.test(text)) return false;
  if (CAPTCHA_RE.test(text)) return false;
  // Nav-stripped check: remove short lines (nav/menu items) and re-check length
  const meaningful = text
    .split("\n")
    .filter((l) => l.trim().length > 40)
    .join(" ");
  return meaningful.length > 300;
}

async function ingest(targetUrl: string, title: string, body: string, source: string) {
  await $`python3 ${FETCH_PY} --ingest --url ${targetUrl} --title ${title} --body ${body} --source ${source}`
    .quiet()
    .nothrow();
}

// 1. Cache check
if (!noCache) {
  try {
    const cached = await $`python3 ${FETCH_PY} --by-url ${url}`.json();
    if (cached?.body && !cached.body.startsWith("[UNAVAILABLE")) {
      process.stdout.write(cached.body);
      process.exit(0);
    }
  } catch {
    // cache miss — continue
  }
}

// 2. Wayback Machine — works for WSJ; FT serves paywall page → isValidContent rejects
async function tryWayback(targetUrl: string): Promise<string> {
  const resp = await fetch(`https://web.archive.org/web/2/${targetUrl}`, {
    headers: { "User-Agent": UA },
  });
  if (!resp.ok) throw new Error(`Wayback HTTP ${resp.status}`);

  // Verify Wayback didn't redirect to a completely different domain
  const finalUrl = resp.url;
  const targetDomain = new URL(targetUrl).hostname.replace(/^www\./, '');
  if (!finalUrl.includes(targetDomain)) {
    throw new Error(`Wayback: redirected away from ${targetDomain} to ${finalUrl}`);
  }

  const html = await resp.text();
  const text = stripHtml(html).substring(0, 8000);
  if (!isValidContent(text)) throw new Error("Wayback: paywall/invalid content");
  const titleMatch = html.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
  const title = titleMatch ? titleMatch[1].trim() : "";
  await ingest(targetUrl, title, text, "wayback");
  return text;
}

// 3. archive.ph via Chrome CDP — required for FT (hard paywall); Chrome must be running
async function tryArchivePh(targetUrl: string): Promise<string> {
  try {
    await $`${CHROME} open ${"https://archive.ph/newest/" + targetUrl}`.quiet();
  } catch {
    throw new Error("archive.ph: Chrome not running or chrome-use unavailable");
  }

  // Poll until tab URL is on archive.ph (max 20s); guards against extracting wrong tab
  let onArchive = false;
  for (let i = 0; i < 10; i++) {
    await Bun.sleep(2_000);
    const currentUrl = await $`${CHROME} eval ${"location.href"}`.text().catch(() => "");
    if (/archive\.(ph|today|is|fo|md|li)/i.test(currentUrl)) { onArchive = true; break; }
  }
  if (!onArchive) throw new Error("archive.ph: tab never landed on archive domain (wrong tab active?)");

  const extractJs = `(() => {
    const a = document.querySelector('#CONTENT, #article, article, main, .article-wrap, .article-body');
    if (a) return a.innerText.substring(0, 8000);
    const b = document.body.cloneNode(true);
    b.querySelectorAll('header,nav,footer,[id="HEAD"],#shareTools,.archiveMetadata').forEach(e => e.remove());
    return b.innerText.substring(0, 8000);
  })()`;

  const body = await $`${CHROME} eval ${extractJs}`.text();
  const title = await $`${CHROME} eval ${"document.title"}`.text();

  if (CAPTCHA_RE.test(body)) {
    process.stderr.write(
      "[CAPTCHA] Open https://archive.ph in Chrome, solve CAPTCHA, then retry.\n"
    );
    throw new Error("archive.ph: CAPTCHA detected");
  }
  if (!isValidContent(body)) throw new Error("archive.ph: invalid/empty content");

  await ingest(targetUrl, title.trim(), body, "archive.ph");
  return body;
}

// 4. Direct fetch — last resort for soft-paywall / open sites
async function tryDirect(targetUrl: string): Promise<string> {
  const resp = await fetch(targetUrl, { headers: { "User-Agent": UA } });
  if (!resp.ok) throw new Error(`Direct fetch HTTP ${resp.status}`);
  const html = await resp.text();
  const text = stripHtml(html).substring(0, 8000);
  if (!isValidContent(text)) throw new Error("Direct: paywall/invalid content");
  const titleMatch = html.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
  const title = titleMatch ? titleMatch[1].trim() : "";
  await ingest(targetUrl, title, text, "direct");
  return text;
}

// Dispatch
const isFT = /\bft\.com\b/i.test(url);

// FT: archive.ph first (Wayback is blocked by FT's paywall wall)
// All others: Wayback first, archive.ph fallback, direct last
const methods = isFT
  ? [tryArchivePh, tryDirect]
  : [tryWayback, tryArchivePh, tryDirect];

const errors: string[] = [];
for (const method of methods) {
  try {
    process.stdout.write(await method(url));
    process.exit(0);
  } catch (e) {
    errors.push(String(e));
  }
}

process.stderr.write(`[UNAVAILABLE - all methods failed for ${url}]\n`);
for (const e of errors) process.stderr.write(`  ${e}\n`);
process.exit(1);
