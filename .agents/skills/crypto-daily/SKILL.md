---
name: crypto-daily
description: >
  Daily crypto publishing workflow. Finds today's completed crypto-portfolio-manager analysis,
  then publishes three outputs: (1) Notion page with full report, (2) Telegram post to the
  @CryptoAiInvestor channel, (3) short tweet on X.com. If today's analysis is missing or stale
  (>12h), re-runs crypto-portfolio-manager first. Triggers on: "/crypto-daily", "post crypto
  daily", "publish today's crypto report", "send telegram crypto update", "tweet crypto signals".
compatibility: opencode
---

# /crypto-daily

Publish today's crypto portfolio analysis to Notion, Telegram, and X.com.

> Educational only. Not financial advice. No leverage. Ever.

---

## Prerequisites (one-time setup)

| Credential / Skill | Where it lives | Used for |
|---|---|---|
| `NOTION_TOKEN` | `~/.env.d/notion.env` | Creating Notion pages |
| `NOTION_PARENT_PAGE_ID` | `~/.env.d/notion.env` (or prompt user) | Where to create the page |
| **telegram-cli skill** | `~/.agents/skills/telegram-cli/` | Posting to Telegram channel |
| **chrome-use skill** | `~/.agents/skills/chrome-use/` | Tweeting on X.com |
| Chrome running + logged into X.com | Real Chrome with DevTools allowed | chrome-use requires live Chrome session |

Load Notion creds: `source ~/.env.d/notion.env`  
Telegram-cli script: `~/.agents/skills/telegram-cli/telegram-cli.py`  
Chrome-use binary: `~/.agents/skills/chrome-use/scripts/chrome-use`

---

## Step 0 — Find today's analysis

**0a. Determine today's date** (never call `Date.now()` directly in skill instructions — use shell):
```bash
TODAY=$(date +%F)   # e.g. 2026-06-23
```

**0b. Check if today's run exists:**
```bash
REPORT="research/crypto-portfolio-${TODAY}.md"
MEMORY=".agents/memory/${TODAY}.md"

# Check report file exists and is fresh (< 12h)
if [ -f "$REPORT" ]; then
  AGE_SECS=$(( $(date +%s) - $(stat -f %m "$REPORT" 2>/dev/null || stat -c %Y "$REPORT") ))
  [ "$AGE_SECS" -lt 43200 ] && FRESH=true || FRESH=false
else
  FRESH=false
fi
```

**0c. If NOT fresh:** invoke `crypto-portfolio-manager` first (full run, all 7 tokens), then return here.  
**If fresh:** continue to Step 1 with the existing `$REPORT` file.

---

## Step 1 — Extract content from today's report

Read the report file and extract:

```bash
source ~/.env.d/notion.env   # loads NOTION_TOKEN and NOTION_PARENT_PAGE_ID
REPORT_CONTENT=$(cat "$REPORT")
```

Pull the three payload sections from the report:
1. **Signal table** — the `=== CRYPTO PORTFOLIO RUN ===` block
2. **Telegram recap** — the block starting with `📊 Daily Crypto Brief`
3. **Key facts for tweet** — top signal + top catalyst from Block 2

If the Telegram recap section is missing from the report, construct it per the `crypto-portfolio-manager` Step 5 format using the signal table and Block 2 verdicts already in the report.

---

## Step 2 — Create Notion page

Use the Notion API to create a new page under the parent page.

```bash
source ~/.env.d/notion.env

# Build the page title
TITLE="📊 Crypto Daily — ${TODAY}"

# Run the Notion publisher script
python3 .agents/skills/crypto-daily/scripts/notion_publish.py \
  --token    "$NOTION_TOKEN" \
  --parent   "$NOTION_PARENT_PAGE_ID" \
  --title    "$TITLE" \
  --report   "$REPORT"
```

The script (`scripts/notion_publish.py`) converts the Markdown report to Notion blocks and POSTs to the Notion API. It prints the URL of the created page on success:

```
✅ Notion page created: https://www.notion.so/Crypto-Daily-2026-06-23-<id>
```

**If `NOTION_PARENT_PAGE_ID` is not set**, prompt the user:
```
⚠️  NOTION_PARENT_PAGE_ID not set. Open Notion, navigate to the target page,
    copy its ID from the URL (the 32-char hex after the last dash), and set:
    export NOTION_PARENT_PAGE_ID=<id>
```

**Fallback** if the API fails: open `https://notion.so` in Chrome-use and create the page manually:
```bash
CHROME=~/.agents/skills/chrome-use/scripts/chrome-use
$CHROME open "https://notion.so"
$CHROME snapshot -i
# Find the "New page" or "+" button, click it, type the title, paste content
```

---

## Step 3 — Post to Telegram channel via telegram-cli skill

**Invoke the `telegram-cli` skill**, then send the daily recap to @CryptoAiInvestor.

**3a. Extract the recap from the report:**
```bash
RECAP=$(python3 - << 'PY'
import re, sys
content = open("research/crypto-portfolio-$(date +%F).md").read()
# Extract the block between the telegram recap backtick fences
m = re.search(r'```\n(📊 Daily Crypto Brief.*?)```', content, re.DOTALL)
print(m.group(1).strip() if m else "")
PY
)

# Telegram hard limit is 4096 chars — trim if needed
RECAP=$(echo "$RECAP" | head -c 4000)
```

**3b. Send via telegram-cli:**
```bash
TELEGRAM_CLI=~/.agents/skills/telegram-cli/telegram-cli.py

python3 "$TELEGRAM_CLI" send @CryptoAiInvestor "$RECAP"
```

**3c. Verify delivery:**
```bash
# Read the last message to confirm it arrived
python3 "$TELEGRAM_CLI" read @CryptoAiInvestor --limit 1
```

Expected output: the sent message appears as the most recent message.

**Error handling:**
| Error | Fix |
|---|---|
| `session not authenticated` | `python3 "$TELEGRAM_CLI" login` |
| `ChatWriteForbiddenError` | Account must be admin of @CryptoAiInvestor — add via Telegram app → channel info → Administrators |
| `UsernameNotOccupiedError` | Channel username changed — confirm the correct handle |
| Recap empty | Check report file exists and contains `📊 Daily Crypto Brief` block |

> ⚠️ telegram-cli uses your **personal** Telegram account (Telethon session at `~/.config/telethon/`). The account must be a channel admin to post. Check admin status first if the send fails.

---

## Step 4 — Post tweet on X.com via chrome-use skill

**Invoke the `chrome-use` skill**, then compose and post a ≤ 280 char tweet.

**4a. Build the tweet (≤ 280 chars):**

Template:
```
🔮 Crypto {DATE} | F&G {value} Extreme Fear
BUY(small): {top 2-3 tokens} {price + 1-word catalyst each}
{dominant macro driver in 1 line}
DYOR. Not advice. #Bitcoin #DeFi #Crypto #quantarena.xyz
```

Example:
```
🔮 Crypto 2026-06-23 | F&G 23 Extreme Fear
BUY(small): AAVE $71 (RWA catalyst), LINK $7.6 (RSI 23), BTC $62k
AI/tech selloff = dip. Trend bearish — tranches only.
DYOR. Not advice. #Bitcoin #DeFi #quantarena.xyz
```

**Always verify ≤ 280 chars before proceeding:**
```bash
echo -n "$TWEET" | wc -c   # must be ≤ 280
```

**4b. Post via chrome-use — step by step:**

```bash
CHROME=~/.agents/skills/chrome-use/scripts/chrome-use

# 1. Open the X.com compose URL (requires Chrome to be running + logged in)
$CHROME open "https://x.com/compose/tweet"
sleep 3

# 2. Snapshot interactive elements to get @eN refs
$CHROME snapshot -i
# Look for: [textbox] "What is happening?!" or similar compose input → assign it @e_compose

# 3. Type the tweet (use `type` not `fill` — X.com watches keystrokes)
$CHROME type @e_compose "$TWEET"
sleep 1

# 4. Re-snapshot to get fresh refs after typing
$CHROME snapshot -i
# Look for: [button] "Post" or [button] "Tweet" → assign it @e_post

# 5. Click Post
$CHROME click @e_post
sleep 2

# 6. Screenshot proof of the posted tweet
$CHROME screenshot /tmp/tweet_proof_$(date +%F).png
```

> **@eN refs are dynamic** — the actual ref numbers from `snapshot -i` will differ each run. Read the snapshot output, find the compose textbox and Post button by their label, and use those refs. Never hardcode `@e1` or `@e_compose` — those are placeholders showing the pattern.

> **If x.com redirects to login:** open `https://x.com` in Chrome manually, log in, then retry.

**4c. Embed the screenshot inline:**
```
view /tmp/tweet_proof_{date}.png
```
(Call the `view` tool on the file path to embed the image in your reply.)

---

## Step 5 — Report results

Print a summary of all three publishing actions:

```
=== /crypto-daily COMPLETE — {DATE} ===

📓 Notion:   ✅ https://www.notion.so/Crypto-Daily-{date}-{id}
             (or ❌ <error message>)

💬 Telegram: ✅ Sent to @CryptoAiInvestor (msg_id={id})
             (or ❌ <error message>)

🐦 X.com:    ✅ Posted (screenshot attached)
             (or ❌ <error message>)
```

Attach the tweet screenshot inline (call `view` tool on the screenshot path).  
If any step failed, report the error clearly — do NOT silently skip.

---

## Scheduling

```
/loop interval=24h   ← runs once per day at this interval
/stop                ← cancel
```

For cron, add to `crontab`:
```
0 9 * * * cd /Users/engineer/workspace/backtest && copilot "run /crypto-daily"
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Notion: `401 Unauthorized` | Re-check `NOTION_TOKEN` in `~/.env.d/notion.env` |
| Notion: `404 object not found` | `NOTION_PARENT_PAGE_ID` wrong — re-copy from Notion URL |
| Telegram: `session not authenticated` | `python3 telegram-cli.py login` |
| Telegram: `ChatWriteForbiddenError` | Add account as admin of @CryptoAiInvestor |
| X.com: wrong `@eN` ref | Re-run `$CHROME snapshot -i` and use the new ref |
| X.com: not logged in | Log in manually in Chrome, then retry |
| Analysis stale | Delete `research/crypto-portfolio-{today}.md` and re-invoke |
