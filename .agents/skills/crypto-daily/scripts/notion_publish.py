#!/usr/bin/env python3
"""
notion_publish.py — Publish a Markdown report to a Notion page.

Usage:
  python3 notion_publish.py \
    --token ntn_xxx \
    --parent <parent_page_id> \
    --title "📊 Crypto Daily — 2026-06-23" \
    --report research/crypto-portfolio-2026-06-23.md

Prints the Notion page URL on success, exits non-zero on failure.
"""

import argparse
import json
import re
import sys

NOTION_VERSION = "2022-06-28"
API_BASE = "https://api.notion.com/v1"

try:
    import requests
    def _notion_request(method: str, endpoint: str, token: str, body: dict) -> dict:
        url = f"{API_BASE}{endpoint}"
        fn = requests.post if method == "POST" else requests.patch
        r = fn(url, json=body, headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        })
        if not r.ok:
            print(f"❌ Notion API error {r.status_code}: {r.text}", file=sys.stderr)
            sys.exit(1)
        return r.json()
    def api_post(endpoint, token, body): return _notion_request("POST",  endpoint, token, body)
    def api_patch(endpoint, token, body): return _notion_request("PATCH", endpoint, token, body)
except ImportError:
    import urllib.request, urllib.error
    def _notion_request(method, endpoint, token, body):
        url = f"{API_BASE}{endpoint}"
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Content-Type", "application/json; charset=utf-8")
        req.add_header("Notion-Version", NOTION_VERSION)
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            print(f"❌ Notion API error {e.code}: {e.read().decode()}", file=sys.stderr)
            sys.exit(1)
    def api_post(endpoint, token, body): return _notion_request("POST",  endpoint, token, body)
    def api_patch(endpoint, token, body): return _notion_request("PATCH", endpoint, token, body)


def md_to_notion_blocks(md: str) -> list:
    """
    Convert Markdown to Notion block objects.
    Handles: headings (# ## ###), bullets (- *), code fences, bold, paragraphs.
    Long text is split into 2000-char chunks (Notion rich_text limit).
    """
    blocks = []
    lines = md.split("\n")
    in_code = False
    code_lang = ""
    code_lines: list[str] = []

    def rich_text(text: str) -> list[dict]:
        """Split text into ≤2000-char rich_text chunks."""
        chunks = []
        while text:
            chunk, text = text[:2000], text[2000:]
            chunks.append({"type": "text", "text": {"content": chunk}})
        return chunks or [{"type": "text", "text": {"content": ""}}]

    def flush_code():
        nonlocal in_code, code_lang, code_lines
        content = "\n".join(code_lines)
        # Notion code blocks have a 2000-char limit per block — split if needed
        while content:
            chunk, content = content[:1990], content[1990:]
            blocks.append({
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [{"type": "text", "text": {"content": chunk}}],
                    "language": code_lang or "plain text",
                },
            })
        in_code = False
        code_lang = ""
        code_lines = []

    for line in lines:
        # Code fence toggle
        if line.startswith("```"):
            if not in_code:
                in_code = True
                code_lang = line[3:].strip() or "plain text"
            else:
                flush_code()
            continue

        if in_code:
            code_lines.append(line)
            continue

        # Headings
        if line.startswith("### "):
            blocks.append({
                "object": "block", "type": "heading_3",
                "heading_3": {"rich_text": rich_text(line[4:].strip())},
            })
        elif line.startswith("## "):
            blocks.append({
                "object": "block", "type": "heading_2",
                "heading_2": {"rich_text": rich_text(line[3:].strip())},
            })
        elif line.startswith("# "):
            blocks.append({
                "object": "block", "type": "heading_1",
                "heading_1": {"rich_text": rich_text(line[2:].strip())},
            })
        # Bullets
        elif re.match(r"^[-*]\s+", line):
            text = re.sub(r"^[-*]\s+", "", line)
            blocks.append({
                "object": "block", "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": rich_text(text)},
            })
        # Table rows → paragraph (Notion table blocks are complex; keep as text)
        elif line.startswith("|"):
            blocks.append({
                "object": "block", "type": "paragraph",
                "paragraph": {"rich_text": rich_text(line)},
            })
        # Horizontal rule → divider
        elif re.match(r"^---+$", line.strip()):
            blocks.append({"object": "block", "type": "divider", "divider": {}})
        # Blank line → skip (don't add empty paragraphs)
        elif line.strip() == "":
            continue
        # Regular paragraph
        else:
            blocks.append({
                "object": "block", "type": "paragraph",
                "paragraph": {"rich_text": rich_text(line)},
            })

    if in_code:
        flush_code()

    return blocks


def main():
    parser = argparse.ArgumentParser(description="Publish Markdown report to Notion")
    parser.add_argument("--token", required=True, help="Notion API token")
    parser.add_argument("--parent", required=True, help="Parent page ID (32-char hex)")
    parser.add_argument("--title", required=True, help="Page title")
    parser.add_argument("--report", required=True, help="Path to Markdown report file")
    args = parser.parse_args()

    # Read report
    try:
        with open(args.report) as f:
            md = f.read()
    except FileNotFoundError:
        print(f"❌ Report file not found: {args.report}", file=sys.stderr)
        sys.exit(1)

    # Notion API: max 100 blocks per request — batch
    all_blocks = md_to_notion_blocks(md)

    # Normalise parent ID (strip hyphens if user pasted URL form)
    parent_id = args.parent.replace("-", "")
    if len(parent_id) == 32:
        parent_id = f"{parent_id[:8]}-{parent_id[8:12]}-{parent_id[12:16]}-{parent_id[16:20]}-{parent_id[20:]}"

    # Create the page (first batch up to 100 blocks)
    first_batch = all_blocks[:100]
    payload = {
        "parent": {"type": "page_id", "page_id": parent_id},
        "properties": {
            "title": {
                "title": [{"type": "text", "text": {"content": args.title}}]
            }
        },
        "children": [],  # create empty; append blocks via PATCH
    }

    result = api_post("/pages", args.token, payload)
    page_id = result["id"]
    page_url = result.get("url", f"https://app.notion.com/p/{page_id.replace('-', '')}")

    # Append all blocks in batches of 50 via PATCH
    for i in range(0, len(all_blocks), 50):
        batch = all_blocks[i:i+50]
        api_patch(f"/blocks/{page_id}/children", args.token, {"children": batch})

    print(f"✅ Notion page created: {page_url}")
    return page_url


if __name__ == "__main__":
    main()
