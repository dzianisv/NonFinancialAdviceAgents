---
name: bypass-paywalls
description: "Interactive paywall bypass using chrome-use + bypass-paywalls-clean extension for FT, WSJ, Bloomberg, and other paywalled news sites. Use when automated RSS teasers aren't enough and the user needs the full article body. Triggers: 'read this article', 'bypass paywall', 'get the full article', 'I need more than the teaser', 'read behind paywall'. NOT for automated cron — this is interactive, requires user's Chrome running with the extension installed."
compatibility: opencode
metadata:
  audience: crypto-research-pipeline
  domain: news-reading
  role: interactive-tool
  tier: paywall-bypass
---

# bypass-paywalls (interactive paywall bypass via chrome-use)

Interactive fallback for reading full article bodies behind paywalls. Uses the user's real Chrome
browser with the `bypass-paywalls-clean` extension. **Not automatable on cron** — requires the user's
Chrome running on their machine.

The automated feed-* skills (feed-ft, feed-wsj, feed-bloomberg) handle daily headline/teaser ingestion
via RSS; this skill handles ad-hoc full-article reads when a specific article matters for research.

## Prerequisites

1. **Chrome running** on the user's machine with remote debugging enabled (DevToolsActivePort).
2. **bypass-paywalls-clean extension installed:**
   - Repo: `https://gitlab.com/nickkdev/bypass-paywalls-chrome-clean` (or GitHub mirror)
   - Install: clone repo → Chrome → `chrome://extensions` → Developer mode on → "Load unpacked" → select the cloned directory
   - The extension updates periodically as sites change paywall implementations — pull the repo occasionally.
3. **chrome-use skill available** — it connects to the user's running Chrome via DevToolsActivePort autoConnect.

## How bypass-paywalls-clean works

BPC modifies HTTP headers per-domain:
- Removes/clears metered-paywall cookies (e.g. FT's `next-flags`, WSJ's `djcs_route`)
- Spoofs `Referer` to Google/Twitter (many paywalls grant free access from social links)
- Spoofs `User-Agent` to Googlebot for sites that whitelist crawler access
- Disables paywall-enforcement JavaScript on specific domains

**Supported sites (partial list):** FT, WSJ, Bloomberg, NYT, The Atlantic, The Economist, Barron's,
The Information, Business Insider, Washington Post, Wired, Medium, and 100+ others.

**Does NOT work for:** Sites requiring active login with no soft/metered paywall (e.g. some Bloomberg
Terminal-only content, proprietary databases). BPC bypasses metered/JS paywalls, not hard auth gates.

**Legal:** ToS violation for most sites. Widely used for personal reading. Not redistribution. YELLOW
risk — treat as personal research tool, never bulk-scrape or redistribute content.

## Workflow

1. User provides a URL (or the agent identifies a high-priority article from an RSS headline).
2. Load the `chrome-use` skill.
3. Navigate to the URL in the user's Chrome (`chrome-use` → open page).
4. Wait for page load. Dismiss cookie/consent banners if they appear (search snapshot for
   "accept", "consent", "cookie" patterns and click through).
5. Take a snapshot — the full article body should be visible (BPC has already modified the headers).
6. Extract the article text from the snapshot. Clean up nav/ads/sidebar noise — keep headline,
   byline, date, and body paragraphs.
7. Return the extracted text to the caller (narrative-news, trend-stock-research, or the user).

## Storing extracted articles

After extraction, the article can be stored in the news DB for downstream use:

```bash
bun .agents/scripts/feeds/feed_manual.ts \
  --url "<article-url>" \
  --title "<headline>" \
  --body "<extracted body text>" \
  --source "ft-manual"   # or "wsj-manual", "bloomberg-manual"
```

Or the agent can write directly to `.db/news.db` via the news_db module if in a TS context.

## Limitations

- **NOT automatable** — requires user's Chrome running with the extension. No cron, no CI, no MCP pod.
- **Rate:** reasonable personal use only. Do not bulk-scrape 100 articles. Read what you need for the
  current research brief.
- **Extension staleness:** sites change paywall implementations; BPC needs periodic `git pull` updates.
  If an article still shows a paywall wall after BPC, the extension may need updating.
- **Bloomberg:** hit-or-miss. Some Bloomberg articles bypass cleanly; others (Terminal-gated) do not.
  Degrade to `[UNAVAILABLE]` when it doesn't work.
- **Cloudflare:** some sites (archive.today, occasionally Bloomberg) throw Cloudflare challenges even
  in a real browser — wait/retry once, then degrade.

## When to use vs when NOT to use

| Situation | Use this skill? |
|-----------|----------------|
| User asks to read a specific paywalled article | YES |
| High-priority article for a research brief, teaser insufficient | YES |
| Daily automated feed ingestion | NO — use feed-ft / feed-wsj / feed-bloomberg |
| Bulk ingestion of 50+ articles | NO — rate/ToS concern |
| RSS teaser is sufficient for the task | NO — unnecessary |
| Headless/CI/MCP environment (no user Chrome) | NO — won't work |

## Cross-references

- [[feed-ft]] — automated FT RSS adapter (headlines + teasers)
- [[feed-wsj]] — automated WSJ RSS adapter (headlines + teasers; Wayback for bodies)
- [[feed-bloomberg]] — automated Bloomberg adapter (headlines only)
- [[chrome-use]] — the browser-control skill this depends on
- [[narrative-news]] — downstream consumer of extracted articles
- [[trend-stock-research]] — downstream consumer; §"How to read articles" documents the same ladder

> Personal research tool. Not redistribution. Educational, not advice.
