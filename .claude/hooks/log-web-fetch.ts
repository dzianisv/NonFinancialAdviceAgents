#!/usr/bin/env bun
/**
 * postToolUse hook — logs every real web_fetch call to /tmp/cc-fetches-{SESSION_ID}.jsonl
 * Works across Claude Code AND Copilot CLI (payload formats differ — both handled).
 *
 * Claude Code input:  { session_id, tool_input: {url}, tool_response: {error?, status?} }
 * Copilot CLI input:  { sessionId?, toolName, toolArgs: '{"url":"..."}', timestamp, cwd }
 */

const input = await Bun.stdin.text()
const event = JSON.parse(input)

// Normalize session ID across runtimes
const sessionId: string = event.session_id ?? event.sessionId ?? "unknown"

// Normalize URL: Claude Code puts it in tool_input.url; Copilot CLI puts it in toolArgs (JSON string)
let url: string = event.tool_input?.url ?? ""
if (!url && event.toolArgs) {
  try { url = JSON.parse(event.toolArgs)?.url ?? "" } catch {}
}

// Normalize error/status
const hasError: boolean = !!(event.tool_response?.error ?? event.toolError)
const status: string = String(event.tool_response?.status ?? event.toolStatus ?? "unknown")

if (!url) process.exit(0)

const logFile = `/tmp/cc-fetches-${sessionId}.jsonl`
const entry = JSON.stringify({
  url,
  success: !hasError,
  status,
  ts: new Date().toISOString(),
})

await Bun.write(Bun.file(logFile), 
  (await Bun.file(logFile).exists() ? await Bun.file(logFile).text() : "") + entry + "\n"
)

process.exit(0)
