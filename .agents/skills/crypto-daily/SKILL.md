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

| Credential | Where it lives | Used for |
|---|---|---|
| `NOTION_TOKEN` | `~/.env.d/notion.env` | Creating Notion pages |
| `NOTION_PARENT_PAGE_ID` | `~/.env.d/notion.env` (or prompt user) | Where to create the page |
| Telegram session | `~/.config/telethon/session.dat.session` | Posting to channel |
| Chrome running | Real Chrome with DevTools allowed | Tweeting on X.com |

Load Notion creds: `source ~/.env.d/notion.env`  
Telegram-cli: `~/.agents/skills/telegram-cli/telegram-cli.py`  
Chrome-use: `~/.agents/skills/chrome-use/scripts/chrome-use`  

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

## Step 3 — Post to Telegram channel

Send the Telegram recap to @CryptoAiInvestor.

```bash
TELEGRAM=~/.agents/skills/telegram-cli/telegram-cli.py

# Extract the recap block from the report (starts with "📊 Daily Crypto Brief")
RECAP=$(python3 -c "
import sys
content = open('$REPORT').read()
start = content.find('📊 Daily Crypto Brief')
# Find the recap inside the triple backtick block
import re
m = re.search(r'\`\`\`\n(📊 Daily Crypto Brief.*?)\`\`\`', content, re.DOTALL)
print(m.group(1) if m else content[start:start+2000])
")

python3 "$TELEGRAM" send @CryptoAiInvestor "$RECAP"
```

**On success:** prints the message ID.  
**If `session not authenticated`:** run `python3 "$TELEGRAM" login` first.  
**If permission error** (not admin of channel): add the account as admin of @CryptoAiInvestor, then retry.

> ⚠️ The telegram-cli uses your personal Telegram account. The account must be an **admin** of @CryptoAiInvestor to post. Channel admins can be managed in Telegram → channel info → Administrators.

---

## Step 4 — Post tweet on X.com

Use `chrome-use` to compose and post a short tweet (≤ 280 chars) summarising today's top finding.

**4a. Build the tweet text** — one paragraph, ≤ 280 chars:

```
🔮 Crypto signals {DATE} (Extreme Fear, F&G {value}):
{Top 2-3 BUY(small) tokens} in DEEP_VALUE zone.
{1-line dominant catalyst from Block 2, with short URL if available.}
DYOR. Not advice.
#Bitcoin #DeFi #CryptoTrading
```

Example (must fit 280 chars):
```
🔮 Crypto 2026-06-23 | F&G 23 Extreme Fear
BUY(small): AAVE $71 (mGLOBAL on Aave Horizon), LINK $7.6 (RSI 23), BTC $62k
Tech selloff = dip. Trend still bearish — tranches only.
DYOR. Not advice. #Bitcoin #DeFi
```

**4b. Post via chrome-use:**

```bash
CHROME=~/.agents/skills/chrome-use/scripts/chrome-use
TWEET="<tweet text built in 4a>"

# Navigate to X.com compose
$CHROME open "https://x.com/compose/tweet"
sleep 2

# Snapshot to find the compose textbox
$CHROME snapshot -i

# Fill the tweet text (use type for inputs that watch keystrokes)
$CHROME type @e1 "$TWEET"   # @e1 = the tweet compose textbox ref from snapshot

# Find and click the "Post" button
$CHROME snapshot -i   # re-snapshot after typing to get fresh refs
# Click the Post / Tweet button (label varies: "Post", "Tweet")
$CHROME click @e_POST   # use the actual ref from snapshot

# Screenshot proof
$CHROME screenshot /tmp/tweet_proof_${TODAY}.png
```

> The exact `@eN` refs depend on the live page snapshot. Always re-snapshot after navigation or typing. If x.com redirects to login, the Chrome session is not authenticated — log in manually in Chrome first.

**On success:** screenshot `/tmp/tweet_proof_{date}.png` is attached to the reply.

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
