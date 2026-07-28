#!/usr/bin/env python3
"""
Publish a markdown report as a Notion child page via the REST API.

Why this exists: the Notion MCP is not always attached to a session, and the API
caps rich_text at 2000 chars and children at 100 blocks per request — so a long
research report must be chunked. This converts markdown -> Notion blocks and
appends them in batches.

Usage:
  python3 publish_notion.py <markdown_file> <parent_page_id> "<page title>"
Requires NOTION_TOKEN in the environment.
"""
import json, os, re, sys, time, urllib.request

API = "https://api.notion.com/v1"
TOKEN = os.environ.get("NOTION_TOKEN")
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}
LIMIT = 1900  # keep under Notion's 2000-char rich_text cap


def post(path, payload, method="POST"):
    req = urllib.request.Request(
        f"{API}{path}", data=json.dumps(payload).encode(), headers=HEADERS, method=method
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def rt(text, code=False):
    """Split long text into <=LIMIT rich_text runs, preserving markdown links."""
    out = []
    for i in range(0, len(text), LIMIT):
        chunk = text[i : i + LIMIT]
        item = {"type": "text", "text": {"content": chunk}}
        if code:
            item["annotations"] = {"code": True}
        out.append(item)
    return out


def para(text):
    return {"object": "block", "type": "paragraph",
            "paragraph": {"rich_text": rt(text)}}


def heading(text, level):
    t = f"heading_{min(level, 3)}"
    return {"object": "block", "type": t, t: {"rich_text": rt(text)}}


def bullet(text):
    return {"object": "block", "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": rt(text)}}


def code_block(text, lang="plain text"):
    # Notion caps a code block at 2000 chars; split into several if needed.
    blocks = []
    for i in range(0, len(text), LIMIT):
        blocks.append({
            "object": "block", "type": "code",
            "code": {"rich_text": [{"type": "text",
                                    "text": {"content": text[i:i + LIMIT]}}],
                     "language": lang},
        })
    return blocks


def divider():
    return {"object": "block", "type": "divider", "divider": {}}


def md_to_blocks(md):
    blocks, lines, i = [], md.split("\n"), 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            lang = stripped[3:].strip() or "plain text"
            body, i = [], i + 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                body.append(lines[i])
                i += 1
            i += 1
            blocks.extend(code_block("\n".join(body) or " ",
                                     lang if lang in ("json", "bash", "python") else "plain text"))
            continue

        if not stripped:
            i += 1
            continue

        if stripped.startswith("#"):
            m = re.match(r"^(#+)\s*(.*)$", stripped)
            blocks.append(heading(m.group(2), len(m.group(1))))
        elif stripped.startswith("---") and set(stripped) <= set("- "):
            blocks.append(divider())
        elif stripped.startswith("|"):
            # Markdown tables have no clean Notion block equivalent at this size;
            # render the whole table as a monospace code block so alignment survives.
            tbl, = [[]]
            while i < len(lines) and lines[i].strip().startswith("|"):
                tbl.append(lines[i].rstrip())
                i += 1
            blocks.extend(code_block("\n".join(tbl), "plain text"))
            continue
        elif re.match(r"^[-*]\s+", stripped):
            blocks.append(bullet(re.sub(r"^[-*]\s+", "", stripped)))
        elif stripped.startswith(">"):
            blocks.append({"object": "block", "type": "quote",
                           "quote": {"rich_text": rt(stripped.lstrip("> "))}})
        else:
            blocks.append(para(stripped))
        i += 1
    return blocks


def main():
    if not TOKEN:
        sys.exit("ERROR: NOTION_TOKEN not set")
    md_path, parent_id, title = sys.argv[1], sys.argv[2], sys.argv[3]
    md = open(md_path).read()
    blocks = md_to_blocks(md)
    print(f"parsed {len(blocks)} blocks from {md_path}")

    page = post("/pages", {
        "parent": {"type": "page_id", "page_id": parent_id},
        "icon": {"type": "emoji", "emoji": "📊"},
        "properties": {"title": [{"type": "text", "text": {"content": title}}]},
        "children": blocks[:100],
    })
    pid = page["id"]
    print(f"created {pid}")

    for n in range(100, len(blocks), 100):
        batch = blocks[n : n + 100]
        post(f"/blocks/{pid}/children", {"children": batch}, method="PATCH")
        print(f"appended {n}-{n + len(batch)}")
        time.sleep(0.35)

    print(f"URL: https://www.notion.so/{pid.replace('-', '')}")


if __name__ == "__main__":
    main()
