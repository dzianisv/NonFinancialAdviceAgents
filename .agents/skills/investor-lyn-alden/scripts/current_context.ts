#!/usr/bin/env bun
/**
 * current_context.ts — "What is Lyn Alden saying NOW" orchestrator.
 *
 * Runs the blog / X / Nostr fetchers in parallel and renders a single
 * markdown brief (or JSON). Each source degrades independently to a loud
 * [UNAVAILABLE] line so one dead source never blocks the others.
 */

import { fetchBlog, type BlogPost } from "./fetch_blog";
import { fetchX, type XPost } from "./fetch_x";
import { fetchNostr, type NostrNote } from "./fetch_nostr";

function parseArgs(argv: string[]) {
  const days = argv.includes("--days")
    ? parseInt(argv[argv.indexOf("--days") + 1] ?? "30", 10) || 30
    : 30;
  return { days, json: argv.includes("--json") };
}

function snippet(s: string, n = 180): string {
  const clean = s.replace(/\s+/g, " ").trim();
  return clean.length > n ? clean.slice(0, n) + "…" : clean;
}

if (import.meta.main) {
  const { days, json } = parseArgs(process.argv.slice(2));
  const now = new Date().toISOString();

  const [blogR, xR, nostrR] = await Promise.allSettled([
    fetchBlog(days, false),
    fetchX(days),
    fetchNostr(days),
  ]);

  const blog: BlogPost[] = blogR.status === "fulfilled" ? blogR.value : [];
  const x: XPost[] = xR.status === "fulfilled" ? xR.value : [];
  const nostr: NostrNote[] = nostrR.status === "fulfilled" ? nostrR.value : [];

  const blogErr = blogR.status === "rejected" ? String(blogR.reason?.message ?? blogR.reason) : null;
  const xErr = xR.status === "rejected" ? String(xR.reason?.message ?? xR.reason) : null;
  const nostrErr = nostrR.status === "rejected" ? String(nostrR.reason?.message ?? nostrR.reason) : null;

  if (json) {
    console.log(
      JSON.stringify(
        { blog, x, nostr, generatedAt: now, days }, null, 2
      )
    );
    process.exit(0);
  }

  const lines: string[] = [];
  lines.push(`# Lyn Alden — current context (last ${days}d, as of ${now})`);
  lines.push("");

  lines.push("## Blog");
  if (blog.length === 0) {
    lines.push(`- [UNAVAILABLE] ${blogErr ?? `no blog posts in last ${days}d`}`);
  } else {
    for (const p of blog) {
      const d = p.date ? p.date.slice(0, 10) : "????-??-??";
      lines.push(`- ${d} — [${p.title}](${p.url}) — ${snippet(p.teaser, 160)}`);
    }
  }
  lines.push("");

  lines.push("## X (@LynAldenContact)");
  if (x.length === 0) {
    lines.push(`- [UNAVAILABLE] ${xErr ?? `no parseable tweets in last ${days}d`}`);
  } else {
    for (const p of x) {
      const d = p.date.slice(0, 10);
      const from = p.reposted_from ? ` @${p.reposted_from}` : "";
      lines.push(`- ${d} [${p.kind}${from}] ${snippet(p.text)} — ${p.url}`);
    }
  }
  lines.push("");

  lines.push("## Nostr (lyn@primal.net)");
  if (nostr.length === 0) {
    lines.push(`- [UNAVAILABLE] ${nostrErr ?? `no Nostr events in last ${days}d`}`);
  } else {
    for (const n of nostr) {
      const d = n.date.slice(0, 10);
      const from = n.reposted_from ? ` from:${n.reposted_from.slice(0, 12)}…` : "";
      lines.push(`- ${d} [${n.kind}${from}] ${snippet(n.text)} — https://primal.net/e/${n.id}`);
    }
  }
  lines.push("");

  lines.push("---");
  lines.push(
    "Tactical/time-stamped — her current views decay; re-run before quoting as current."
  );

  console.log(lines.join("\n"));
}
