#!/usr/bin/env bash
set -euo pipefail

# read_article.sh — fetch full body of a (possibly paywalled) article URL.
#
# Usage: read_article.sh <url> [--no-cache]
# Outputs: article title + full body text to stdout
# Side effect: ingests into article cache via fetch_article.py --ingest
# Exit code: 0=success, 1=unavailable (paywall/error)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FETCH_PY="/Users/engineer/workspace/backtest/.agents/scripts/feeds/fetch_article.py"
CHROME="/Users/engineer/.agents/skills/chrome-use/scripts/chrome-use"

# ---------------------------------------------------------------------------
# Args
# ---------------------------------------------------------------------------
URL="${1:-}"
NO_CACHE=0

if [[ -z "$URL" ]]; then
  echo "Usage: read_article.sh <url> [--no-cache]" >&2
  exit 1
fi

for arg in "${@:2}"; do
  if [[ "$arg" == "--no-cache" ]]; then
    NO_CACHE=1
  fi
done

# ---------------------------------------------------------------------------
# 1. Cache check
# ---------------------------------------------------------------------------
if [[ "$NO_CACHE" -eq 0 ]]; then
  CACHED=$(python3 "$FETCH_PY" --search "$URL" --limit 1 2>/dev/null || true)
  if [[ -n "$CACHED" ]]; then
    echo "$CACHED"
    exit 0
  fi
fi

# ---------------------------------------------------------------------------
# 2. Detect outlet
# ---------------------------------------------------------------------------
METHOD="ARCHIVE_PH_CHROME"
if echo "$URL" | grep -qiE '(^https?://)?(www\.)?wsj\.com'; then
  METHOD="WAYBACK"
fi

# ---------------------------------------------------------------------------
# 3. Methods
# ---------------------------------------------------------------------------

archive_ph_chrome() {
  local url="$1"

  if [[ ! -x "$CHROME" ]]; then
    echo "[chrome-use not found at $CHROME — skipping archive.ph method]" >&2
    return 1
  fi

  "$CHROME" open "https://archive.ph/newest/${url}" || true
  sleep 10

  BODY=$("$CHROME" eval "
    (() => {
      const article = document.querySelector('#CONTENT, #article, article, main, .article-wrap, .article-body');
      if (article) return article.innerText.substring(0, 8000);
      const body = document.body.cloneNode(true);
      body.querySelectorAll('header, nav, footer, [id=\"HEAD\"], #shareTools, .archiveMetadata').forEach(el => el.remove());
      return body.innerText.substring(0, 8000);
    })()
  " 2>&1) || true

  TITLE=$("$CHROME" eval "document.title" 2>&1) || true

  if echo "$BODY" | grep -qiE 'security check|captcha|cloudflare|ddos'; then
    echo "[UNAVAILABLE - archive.ph CAPTCHA: open https://archive.ph in Chrome and solve the CAPTCHA, then retry]" >&2
    return 1
  fi

  if [[ -z "$BODY" ]]; then
    echo "[UNAVAILABLE - archive.ph returned empty body]" >&2
    return 1
  fi

  python3 "$FETCH_PY" --ingest --url "$url" --title "$TITLE" --body "$BODY" --source "archive.ph" || true
  echo "$BODY"
  return 0
}

wayback() {
  local url="$1"
  local archive_url="https://web.archive.org/web/2/${url}"

  HTML=$(curl -sL --max-time 30 \
    -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36" \
    "$archive_url" 2>/dev/null) || true

  if [[ -z "$HTML" ]]; then
    echo "[UNAVAILABLE - Wayback returned empty response for $url]" >&2
    return 1
  fi

  BODY=$(python3 - <<'PYEOF'
import sys, re
html = sys.stdin.read()
html = re.sub(r'<(script|style|nav|header|footer)[^>]*>.*?</\1>', '', html, flags=re.DOTALL|re.IGNORECASE)
text = re.sub(r'<[^>]+>', ' ', html)
text = re.sub(r'\s+', ' ', text).strip()
print(text[:8000])
PYEOF
  <<< "$HTML") || true

  if echo "$BODY" | grep -qiE 'Subscribe to read|sign in to read'; then
    echo "[UNAVAILABLE - Wayback only has paywall snapshot for $url]" >&2
    return 1
  fi

  TITLE=$(python3 - <<'PYEOF'
import sys, re
html = sys.stdin.read()
m = re.search(r'<title[^>]*>(.*?)</title>', html, re.DOTALL|re.IGNORECASE)
print(m.group(1).strip() if m else '')
PYEOF
  <<< "$HTML") || true

  python3 "$FETCH_PY" --ingest --url "$url" --title "$TITLE" --body "$BODY" --source "wayback" || true
  echo "$BODY"
  return 0
}

# ---------------------------------------------------------------------------
# 4. Dispatch
# ---------------------------------------------------------------------------
case "$METHOD" in
  WAYBACK)
    if ! wayback "$URL"; then
      echo "[UNAVAILABLE - Wayback failed for $URL; trying archive.ph fallback]" >&2
      if ! archive_ph_chrome "$URL"; then
        echo "[UNAVAILABLE - all methods failed for $URL]" >&2
        exit 1
      fi
    fi
    ;;
  ARCHIVE_PH_CHROME|*)
    if ! archive_ph_chrome "$URL"; then
      echo "[UNAVAILABLE - archive.ph/chrome failed for $URL; trying Wayback fallback]" >&2
      if ! wayback "$URL"; then
        echo "[UNAVAILABLE - all methods failed for $URL]" >&2
        exit 1
      fi
    fi
    ;;
esac
