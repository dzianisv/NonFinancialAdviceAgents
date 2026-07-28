#!/usr/bin/env bun
/**
 * Publish a markdown file as a Notion child page.
 *
 * Usage:
 *   bun .agents/scripts/publish/notion_publish.ts \
 *     --file research/foo.md --parent <32-hex-page-id> --title "My Title"
 *
 * Token resolution order: $NOTION_TOKEN, then the `notion` MCP entry in
 * ~/.config/opencode/opencode.json. Never printed.
 *
 * Markdown tables are emitted as `code` blocks: Notion's table block requires a
 * fixed column count declared up front and nested table_row children, which
 * breaks on the ragged tables these reports contain. A monospace code block
 * preserves alignment and is lossless, which matters more than native styling
 * for an audit artifact.
 */

const NOTION_VERSION = "2022-06-28";
const MAX_BLOCKS_PER_CALL = 100;
const MAX_RICH_TEXT = 1900; // Notion hard limit is 2000; leave headroom.

function arg(name: string): string | undefined {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 ? process.argv[i + 1] : undefined;
}

async function resolveToken(): Promise<string> {
  if (process.env.NOTION_TOKEN) return process.env.NOTION_TOKEN;
  const cfgPath = `${process.env.HOME}/.config/opencode/opencode.json`;
  const raw = await Bun.file(cfgPath).text();
  const m = raw.match(/"NOTION_TOKEN"\s*:\s*"([^"]+)"/);
  if (!m) throw new Error("NOTION_TOKEN not found in env or opencode.json");
  return m[1];
}

/** Split any string into <=MAX_RICH_TEXT chunks so Notion never 400s. */
function richText(s: string) {
  const out: any[] = [];
  for (let i = 0; i < Math.max(s.length, 1); i += MAX_RICH_TEXT) {
    out.push({ type: "text", text: { content: s.slice(i, i + MAX_RICH_TEXT) } });
  }
  return out;
}

function para(s: string) {
  return { object: "block", type: "paragraph", paragraph: { rich_text: richText(s) } };
}

function heading(level: number, s: string) {
  const t = `heading_${Math.min(level, 3)}` as const;
  return { object: "block", type: t, [t]: { rich_text: richText(s) } } as any;
}

function codeBlock(s: string, lang = "plain text") {
  return {
    object: "block",
    type: "code",
    code: { rich_text: richText(s), language: lang },
  };
}

/** Strip markdown emphasis so Notion plain text stays readable. */
function clean(s: string): string {
  return s
    .replace(/\*\*(.+?)\*\*/g, "$1")
    .replace(/`(.+?)`/g, "$1")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, "$1 ($2)")
    .trim();
}

function mdToBlocks(md: string): any[] {
  const lines = md.split("\n");
  const blocks: any[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const t = line.trim();

    if (!t) { i++; continue; }

    // fenced code
    if (t.startsWith("```")) {
      const buf: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) buf.push(lines[i++]);
      i++;
      blocks.push(codeBlock(buf.join("\n") || " "));
      continue;
    }

    // table -> code block (see header comment for why)
    if (t.startsWith("|")) {
      const buf: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        buf.push(clean(lines[i].trim()));
        i++;
      }
      blocks.push(codeBlock(buf.join("\n")));
      continue;
    }

    if (/^---+$/.test(t)) {
      blocks.push({ object: "block", type: "divider", divider: {} });
      i++;
      continue;
    }

    const h = t.match(/^(#{1,6})\s+(.*)$/);
    if (h) {
      blocks.push(heading(h[1].length, clean(h[2])));
      i++;
      continue;
    }

    const bullet = t.match(/^[-*]\s+(.*)$/);
    if (bullet) {
      blocks.push({
        object: "block",
        type: "bulleted_list_item",
        bulleted_list_item: { rich_text: richText(clean(bullet[1])) },
      });
      i++;
      continue;
    }

    const num = t.match(/^\d+\.\s+(.*)$/);
    if (num) {
      blocks.push({
        object: "block",
        type: "numbered_list_item",
        numbered_list_item: { rich_text: richText(clean(num[1])) },
      });
      i++;
      continue;
    }

    if (t.startsWith(">")) {
      blocks.push({
        object: "block",
        type: "quote",
        quote: { rich_text: richText(clean(t.replace(/^>\s?/, ""))) },
      });
      i++;
      continue;
    }

    blocks.push(para(clean(t)));
    i++;
  }
  return blocks;
}

async function notion(token: string, path: string, method: string, body: any) {
  const res = await fetch(`https://api.notion.com/v1${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      "Notion-Version": NOTION_VERSION,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  const json = await res.json();
  if (!res.ok) throw new Error(`Notion ${method} ${path} -> ${res.status}: ${JSON.stringify(json).slice(0, 400)}`);
  return json as any;
}

const file = arg("file");
const parent = arg("parent");
const title = arg("title");
if (!file || !parent || !title) {
  console.error("usage: --file <md> --parent <page_id> --title <title>");
  process.exit(1);
}

const token = await resolveToken();
const md = await Bun.file(file).text();
const blocks = mdToBlocks(md);

const page = await notion(token, "/pages", "POST", {
  parent: { page_id: parent },
  properties: { title: { title: [{ type: "text", text: { content: title } }] } },
  children: blocks.slice(0, MAX_BLOCKS_PER_CALL),
});

let appended = Math.min(blocks.length, MAX_BLOCKS_PER_CALL);
while (appended < blocks.length) {
  const chunk = blocks.slice(appended, appended + MAX_BLOCKS_PER_CALL);
  await notion(token, `/blocks/${page.id}/children`, "PATCH", { children: chunk });
  appended += chunk.length;
}

console.log(JSON.stringify({ ok: true, page_id: page.id, url: page.url, blocks: blocks.length }, null, 2));
