#!/usr/bin/env bun
/**
 * fetch_x.ts — Lyn Alden (@LynAldenContact) X/Twitter fetcher.
 *
 * Uses the public Twitter syndication timeline-profile endpoint, extracts the
 * embedded __NEXT_DATA__ JSON, and walks it for tweet objects. Defensive: if
 * the canonical `entries` path is missing it recursively searches for any
 * objects carrying a `full_text` field. Never crashes — degrades to a loud
 * [UNAVAILABLE] line and exit 0.
 */

const SCREEN_NAME = "LynAldenContact";
// The classic syndication.twitter.com host frequently 429s from server IPs;
// cdn.syndication.twimg.com serves the identical __NEXT_DATA__ payload and is
// far more reliable, so we try it first and fall back to the classic host.
const HOSTS = [
  `https://cdn.syndication.twimg.com/srv/timeline-profile/screen-name/${SCREEN_NAME}`,
  `https://syndication.twitter.com/srv/timeline-profile/screen-name/${SCREEN_NAME}`,
];
const UA =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";
const TIMEOUT_MS = 15_000;

export interface XPost {
  kind: "tweet" | "reply" | "repost";
  text: string;
  date: string; // ISO
  url: string;
  likes: number;
  retweets: number;
  reposted_from?: string;
}

async function timedFetch(url: string): Promise<string> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      headers: {
        "User-Agent": UA,
        Accept: "text/html,application/xhtml+xml,*/*",
        "Accept-Language": "en-US,en;q=0.9",
      },
      signal: ctrl.signal,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.text();
  } finally {
    clearTimeout(t);
  }
}

function extractNextData(html: string): any {
  const m = html.match(
    /<script id="__NEXT_DATA__" type="application\/json">([\s\S]*?)<\/script>/
  );
  if (!m) throw new Error("__NEXT_DATA__ script not found");
  return JSON.parse(m[1]);
}

/** Recursively collect objects that look like tweets (have full_text). */
function findTweetObjects(node: any, acc: any[], seen = new Set<any>()): void {
  if (!node || typeof node !== "object") return;
  if (seen.has(node)) return;
  seen.add(node);
  if (Array.isArray(node)) {
    for (const v of node) findTweetObjects(v, acc, seen);
    return;
  }
  if (typeof node.full_text === "string" && (node.id_str || node.id)) {
    acc.push(node);
  }
  for (const k of Object.keys(node)) findTweetObjects(node[k], acc, seen);
}

/** Pull tweet objects from canonical entries[].content.tweet path. */
function tweetsFromEntries(json: any): any[] | null {
  const entries = json?.props?.pageProps?.timeline?.entries;
  if (!Array.isArray(entries)) return null;
  const out: any[] = [];
  for (const e of entries) {
    const tw = e?.content?.tweet ?? e?.tweet;
    if (tw && typeof tw.full_text === "string") out.push(tw);
  }
  return out.length ? out : null;
}

function classify(tw: any): { kind: XPost["kind"]; src: any } {
  if (tw.retweeted_status) return { kind: "repost", src: tw.retweeted_status };
  if (tw.in_reply_to_screen_name) return { kind: "reply", src: tw };
  return { kind: "tweet", src: tw };
}

function toPost(tw: any): XPost | null {
  const { kind, src } = classify(tw);
  const text: string = (src.full_text ?? tw.full_text ?? "").trim();
  const created = src.created_at ?? tw.created_at;
  const ts = created ? Date.parse(created) : NaN;
  if (Number.isNaN(ts)) return null;

  const id = src.id_str ?? src.id ?? tw.id_str ?? tw.id;
  const author =
    kind === "repost"
      ? src.user?.screen_name ?? src.user?.screen_name_str
      : SCREEN_NAME;
  const url = `https://x.com/${author ?? SCREEN_NAME}/status/${id}`;

  return {
    kind,
    text,
    date: new Date(ts).toISOString(),
    url,
    likes: Number(tw.favorite_count ?? src.favorite_count ?? 0) || 0,
    retweets: Number(tw.retweet_count ?? src.retweet_count ?? 0) || 0,
    ...(kind === "repost" && author ? { reposted_from: author } : {}),
  };
}

export async function fetchX(days: number): Promise<XPost[]> {
  let html = "";
  let lastErr: any = null;
  for (const url of HOSTS) {
    try {
      html = await timedFetch(url);
      if (html) break;
    } catch (e) {
      lastErr = e;
    }
  }
  if (!html) throw new Error(`all syndication hosts failed — ${lastErr?.message ?? lastErr}`);
  const json = extractNextData(html);

  let raw = tweetsFromEntries(json);
  if (!raw) {
    const acc: any[] = [];
    findTweetObjects(json, acc);
    raw = acc;
  }
  if (!raw || raw.length === 0) throw new Error("no tweet objects in payload");

  const cutoff = Date.now() - days * 86_400_000;
  const seen = new Set<string>();
  const posts: XPost[] = [];
  for (const tw of raw) {
    const p = toPost(tw);
    if (!p) continue;
    if (Date.parse(p.date) < cutoff) continue;
    const key = p.url;
    if (seen.has(key)) continue;
    seen.add(key);
    posts.push(p);
  }
  posts.sort((a, b) => Date.parse(b.date) - Date.parse(a.date));
  return posts;
}

function parseArgs(argv: string[]) {
  const days = argv.includes("--days")
    ? parseInt(argv[argv.indexOf("--days") + 1] ?? "30", 10) || 30
    : 30;
  return { days, json: argv.includes("--json") };
}

if (import.meta.main) {
  const { days, json } = parseArgs(process.argv.slice(2));
  try {
    const posts = await fetchX(days);
    if (posts.length === 0) {
      console.log(
        `[UNAVAILABLE] X syndication returned no parseable tweets — none within ${days}d window`
      );
      process.exit(0);
    }
    if (json) {
      console.log(JSON.stringify(posts, null, 2));
    } else {
      for (const p of posts) {
        const d = p.date.slice(0, 10);
        const from = p.reposted_from ? ` @${p.reposted_from}` : "";
        const snippet = p.text.replace(/\s+/g, " ").slice(0, 200);
        console.log(
          `${d} [${p.kind}${from}] ${snippet}  (♥${p.likes} ↻${p.retweets}) ${p.url}`
        );
      }
    }
  } catch (e: any) {
    console.log(
      `[UNAVAILABLE] X syndication returned no parseable tweets — ${e?.message ?? e}`
    );
    process.exit(0);
  }
}
