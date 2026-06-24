#!/usr/bin/env bash
# Stop hook — citation validator
# Fires when Claude finishes a turn. Parses the last assistant message for
# [T1]/[T2]/[T3] citation URLs, cross-checks against the real fetch log written
# by log-web-fetch.sh, and flags any cited URL that was never actually fetched.
# This runs fully outside the LLM — no agent can hide a hallucinated citation.
#
# Input: JSON on stdin: { session_id, transcript_path, ... }

set -euo pipefail

INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"')
TRANSCRIPT=$(echo "$INPUT" | jq -r '.transcript_path // ""')

FETCH_LOG="/tmp/cc-fetches-${SESSION_ID}.jsonl"
ERROR_LOG="/Users/engineer/workspace/backtest/logs/citation-errors.log"
mkdir -p /Users/engineer/workspace/backtest/logs

# ── 1. Extract cited URLs from the transcript (last assistant message) ───────
# Look for lines matching: [T1] https://... or [T2] https://... or [T3] https://...
CITED_URLS=""
if [[ -n "$TRANSCRIPT" && -f "$TRANSCRIPT" ]]; then
  # Transcript is JSONL; get the last assistant message text
  LAST_MSG=$(jq -r 'select(.role=="assistant") | .content // ""' "$TRANSCRIPT" 2>/dev/null | tail -1)
  CITED_URLS=$(echo "$LAST_MSG" | grep -oP '\[T[123]\]\s+https?://\S+' | grep -oP 'https?://\S+' || true)
fi

# Fallback: scan all assistant messages if last-only found nothing
if [[ -z "$CITED_URLS" && -n "$TRANSCRIPT" && -f "$TRANSCRIPT" ]]; then
  CITED_URLS=$(jq -r 'select(.role=="assistant") | .content // ""' "$TRANSCRIPT" 2>/dev/null \
    | grep -oP '\[T[123]\]\s+https?://\S+' | grep -oP 'https?://\S+' || true)
fi

if [[ -z "$CITED_URLS" ]]; then
  # No citations found — nothing to validate
  exit 0
fi

# ── 2. Load set of URLs that were actually fetched this session ──────────────
FETCHED_URLS=""
if [[ -f "$FETCH_LOG" ]]; then
  FETCHED_URLS=$(jq -r 'select(.success=="true") | .url' "$FETCH_LOG" 2>/dev/null || true)
fi

# ── 3. Diff: cited but not fetched = hallucinated ────────────────────────────
TS=$(date -u +%FT%TZ)
FAILURES=0

while IFS= read -r url; do
  [[ -z "$url" ]] && continue
  if ! echo "$FETCHED_URLS" | grep -qF "$url"; then
    echo "${TS}	${SESSION_ID}	HALLUCINATED_CITATION	${url}" >> "$ERROR_LOG"
    FAILURES=$((FAILURES + 1))
  fi
done <<< "$CITED_URLS"

# ── 4. Emit feedback to Claude Code if failures found ────────────────────────
# Exit 0 but write to stdout — Claude Code shows this in the session.
if [[ $FAILURES -gt 0 ]]; then
  echo "⚠️  CITATION VALIDATOR: $FAILURES cited URL(s) were never fetched this turn (hallucinated). See logs/citation-errors.log." >&2
fi

# Clean up fetch log for this session
rm -f "$FETCH_LOG"

exit 0
