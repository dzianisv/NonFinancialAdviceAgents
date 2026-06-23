#!/usr/bin/env bash
# PostToolUse(web_fetch) hook — logs every real fetch to /tmp/cc-fetches-{SESSION_ID}.jsonl
# Runs outside the LLM loop. Called by Claude Code after every web_fetch tool call.
# Input: JSON on stdin: { tool_name, tool_input: {url}, tool_response: {...}, session_id, ... }

set -euo pipefail

INPUT=$(cat)

SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"')
URL=$(echo "$INPUT" | jq -r '.tool_input.url // ""')
STATUS=$(echo "$INPUT" | jq -r '.tool_response.status // "unknown"')
SUCCESS=$(echo "$INPUT" | jq -r 'if (.tool_response.error // "") != "" then "false" else "true" end')

LOGFILE="/tmp/cc-fetches-${SESSION_ID}.jsonl"

if [[ -n "$URL" ]]; then
  echo "{\"url\":$(echo "$URL" | jq -R .), \"success\":$SUCCESS, \"status\":\"$STATUS\", \"ts\":\"$(date -u +%FT%TZ)\"}" >> "$LOGFILE"
fi

exit 0
