#!/usr/bin/env bun
// read_article.ts — fetch full body of a (possibly paywalled) article URL.
// Usage: bun read_article.ts <url> [--no-cache]
//
// Ladder:
//   1. Cache (SQLite)
//   2. Chrome live — uses user's logged-in Chrome session for FT/WSJ/Bloomberg
//      Requires Chrome running + user logged in. Content IS in DOM when subscribed.
//   3. Wayback Machine — headless, works for older WSJ/Bloomberg snapshots
//   4. Direct fetch — open/soft-paywall sites (Reuters, CoinDesk, Yahoo Finance, etc.)
//
// FT/WSJ/Bloomberg: Chrome live is the ONLY method that works (user's subscription).

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

// Outlets where Chrome live (user subscription) is the primary method
const SUBSCRIBED_RE = /\b(ft\.com|wsj\.com|bloomberg\.com)\b/i;

function stripHtml(html: string): string {
  return html
    .replace(/<(script|style|nav|header|footer|noscript)[^>]*>[\s\S]*?<\/\1>/gi, "")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

const PAYWALL_RE = /subscribe to read|sign in to read|subscription required|to continue reading|create an account|log in to read/i;
const CAPTCHA_RE = /security check|captcha|cloudflare|ddos-guard|verify you are human/i;

function isValidContent(text: string): boolean {
  if (text.length < 500) return false;
  if (PAYWALL_RE.test(text)) return false;
  if (CAPTCHA_RE.test(text)) return false;
  const meaningful = text.split("\n").filter((l) => l.trim().length > 40).join(" ");
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

// 2. Chrome live — navigate to actual article URL using user's logged-in Chrome session.
//    Works for FT/WSJ/Bloomberg if user is subscribed. Falls through if Chrome not running
//    or user not logged in (paywall detected in DOM).
async function tryChromeLive(targetUrl: string): Promise<string> {
  try {
    await $`${CHROME} open ${targetUrl}`.quiet();
  } catch {
    throw new Error("Chrome: not running or chrome-use unavailable");
  }

  // Poll until the active tab lands on the target domain (max 20s)
  const targetDomain = new URL(targetUrl).hostname.replace(/^www\./, "");
  let onTarget = false;
  for (let i = 0; i < 10; i++) {
    await Bun.sleep(2_000);
    const currentUrl = await $`${CHROME} eval ${"location.href"}`.text().catch(() => "");
    if (currentUrl.includes(targetDomain)) { onTarget = true; break; }
  }
  if (!onTarget) throw new Error(`Chrome: tab never landed on ${targetDomain} (wrong tab? login redirect?)`);

  // Outlet-specific article body selectors
  const extractJs = `(() => {
    const selectors = [
      // FT
      '[data-trackable="article-body"]', '.article__content-body', '.n-content-body',
      // WSJ
      '.article-content', '.article__body', '[class*="articleBody"]', '.article-wrap',
      // Bloomberg
      '.body-content', '[class*="body__content"]', '.fence-body',
      // Generic
      'article', 'main [class*="content"]', 'main',
    ];
    for (const sel of selectors) {
      const el = document.querySelector(sel);
      if (el && el.innerText.trim().length > 200) return el.innerText.substring(0, 10000);
    }
    // Fallback: strip nav/header/footer from body
    const b = document.body.cloneNode(true);
    b.querySelectorAll('header,nav,footer,aside,[role="banner"],[role="navigation"]').forEach(e => e.remove());
    return b.innerText.substring(0, 10000);
  })()`;

  const body = await $`${CHROME} eval ${extractJs}`.text();
  const title = await $`${CHROME} eval ${"document.title"}`.text();

  if (PAYWALL_RE.test(body)) {
    throw new Error(`Chrome: paywall in DOM — SETUP REQUIRED: open Chrome → sign in at ${targetDomain} with your subscription → retry.`);
  }
  if (CAPTCHA_RE.test(body)) {
    throw new Error(`Chrome: CAPTCHA on ${targetDomain} — solve it in Chrome, then retry.`);
  }
  if (!isValidContent(body)) throw new Error("Chrome: content too short or invalid");

  await ingest(targetUrl, title.trim(), body, `chrome-live:${targetDomain}`);
  return body;
}

// 3. Wayback Machine — headless; works for older WSJ/Bloomberg snapshots
async function tryWayback(targetUrl: string): Promise<string> {
  const resp = await fetch(`https://web.archive.org/web/2/${targetUrl}`, {
    headers: { "User-Agent": UA },
  });
  if (!resp.ok) throw new Error(`Wayback HTTP ${resp.status}`);

  const finalUrl = resp.url;
  const targetDomain = new URL(targetUrl).hostname.replace(/^www\./, "");
  if (!finalUrl.includes(targetDomain)) {
    throw new Error(`Wayback: redirected away from ${targetDomain} → ${finalUrl}`);
  }

  const html = await resp.text();
  const text = stripHtml(html).substring(0, 8000);
  if (!isValidContent(text)) throw new Error("Wayback: paywall or invalid content");
  const titleMatch = html.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
  const title = titleMatch ? titleMatch[1].trim() : "";
  await ingest(targetUrl, title, text, "wayback");
  return text;
}

// 4. Direct fetch — open/soft-paywall sites
async function tryDirect(targetUrl: string): Promise<string> {
  const resp = await fetch(targetUrl, { headers: { "User-Agent": UA } });
  if (!resp.ok) throw new Error(`Direct HTTP ${resp.status}`);
  const html = await resp.text();
  const text = stripHtml(html).substring(0, 8000);
  if (!isValidContent(text)) throw new Error("Direct: paywall or invalid content");
  const titleMatch = html.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
  const title = titleMatch ? titleMatch[1].trim() : "";
  await ingest(targetUrl, title, text, "direct");
  return text;
}

// Dispatch: subscribed outlets get Chrome live first; all others skip Chrome
const isSubscribed = SUBSCRIBED_RE.test(url);
const methods = isSubscribed
  ? [tryChromeLive, tryWayback, tryDirect]
  : [tryWayback, tryDirect];

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
