#!/usr/bin/env bun
/**
 * citation-validator.ts — Universal citation validation hook
 *
 * Fires at turn end on ANY agent, ANY runtime:
 *   Claude Code  → Stop event          (.claude/settings.json)
 *   Copilot CLI  → agentStop event     (.github/hooks/citation-validator.json)
 *   OpenCode     → session.idle event  (.opencode/plugins/citation-validator.ts calls this)
 *
 * Algorithm (no two-phase log/diff — cold re-fetch only):
 *   1. Extract the last assistant response from the event payload
 *   2. Find ALL citation-context URLs (T1/T2/T3, markdown links, Source: lines, numbered refs)
 *   3. Re-fetch each URL cold (HEAD then GET fallback) — independent of what the agent claimed
 *   4. On failure: emit decision:"block" + additionalContext → agent must re-fetch and correct
 *   5. Log all results to logs/citation-errors.log (cross-run audit trail)
 *   6. Max-retry guard (3 retries) prevents infinite block loops
 *
 * Input (stdin): runtime-specific JSON — all formats normalized below.
 * Output (stdout): JSON decision for runtimes that support blocking (Claude Code, Copilot CLI).
 *   - All OK  → exit 0 (no output = fall-through, agent turn accepted)
 *   - Failures → { "decision": "block", "reason": "...", "additionalContext": "..." }
 */

import { join } from "path"
import { existsSync, mkdirSync, appendFileSync, readFileSync } from "fs"

// ── Config ────────────────────────────────────────────────────────────────────
const REPO = process.env.CITATION_VALIDATOR_REPO ?? process.cwd()
const ERROR_LOG = join(REPO, "logs", "citation-errors.log")
const MAX_RETRIES = 3
const FETCH_TIMEOUT_MS = 8000

// ── URL extraction patterns ───────────────────────────────────────────────────
// Catches URLs in any citation context:
//   [T1] https://...          — tier-ranked sources (skill output)
//   [Source: https://...]     — inline source annotations
//   [text](https://...)       — markdown links
//   1. https://...            — numbered reference lists
//   Source: https://...       — plain "Source:" lines
//   > https://...             — blockquote citations
const CITATION_PATTERNS = [
  /\[T[123]\]\s+(https?:\/\/[^\s\)>,"]+)/g,          // [T1/T2/T3] urls
  /\[Source[:\s]+\s*(https?:\/\/[^\s\]\),"]+)/gi,    // [Source: url]
  /\]\((https?:\/\/[^\s\),"]+)\)/g,                  // markdown link targets [text](url)
  /^\s*(?:\d+\.|-|\*)\s+(https?:\/\/[^\s,"]+)/gm,   // numbered/bullet lists starting with url
  /^Source[:\s]+(https?:\/\/[^\s,"]+)/gim,            // Source: url lines
  /^>\s*(https?:\/\/[^\s,"]+)/gm,                    // blockquote urls
  /\[(?:\d+)\]\s*(https?:\/\/[^\s\],"]+)/g,          // [1] url reference style
]

function extractCitationUrls(text: string): string[] {
  const seen = new Set<string>()
  for (const rx of CITATION_PATTERNS) {
    rx.lastIndex = 0
    for (const m of text.matchAll(rx)) {
      const url = m[1].replace(/[.,;)\]]+$/, "").trim()
      if (url.startsWith("https://") || url.startsWith("http://")) seen.add(url)
    }
  }
  return [...seen]
}

// ── Payload normalization across runtimes ─────────────────────────────────────
function extractResponseText(event: Record<string, any>): string {
  // Claude Code Stop: transcript_path points to JSONL session file
  if (event.transcript_path) {
    try {
      const lines = readFileSync(event.transcript_path, "utf8").split("\n").filter(Boolean)
      return lines
        .map(l => { try { return JSON.parse(l) } catch { return null } })
        .filter((m): m is Record<string,any> => m?.role === "assistant")
        .map(m => typeof m.content === "string" ? m.content
                : Array.isArray(m.content) ? m.content.map((c: any) => c?.text ?? "").join("") : "")
        .join("\n")
    } catch {}
  }
  // Copilot CLI agentStop: agentResponse field
  if (event.agentResponse) return String(event.agentResponse)
  // OpenCode: passed directly via CLI arg (see opencode plugin)
  if (event.response) return String(event.response)
  return ""
}

function extractSessionId(event: Record<string, any>): string {
  return event.session_id ?? event.sessionId ?? `pid-${process.pid}`
}

function extractRetryCount(event: Record<string, any>): number {
  // Passed via env by the hook config to track retries
  return parseInt(process.env.CITATION_RETRY ?? "0", 10)
}

// ── Cold URL verification ─────────────────────────────────────────────────────
async function verifyUrl(url: string): Promise<{ url: string; ok: boolean; status: number; error?: string }> {
  // Skip localhost and non-HTTP URLs
  if (/^https?:\/\/(localhost|127\.|0\.0\.0\.0)/.test(url)) return { url, ok: true, status: 0 }
  try {
    // Try HEAD first (cheap), fall back to GET if HEAD not supported
    for (const method of ["HEAD", "GET"] as const) {
      const res = await fetch(url, {
        method,
        signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
        headers: { "User-Agent": "citation-validator/1.0" },
        redirect: "follow",
      })
      if (res.status !== 405) return { url, ok: res.ok, status: res.status }
    }
    return { url, ok: false, status: 405 }
  } catch (e: any) {
    return { url, ok: false, status: 0, error: String(e.message ?? e).slice(0, 120) }
  }
}

// ── Main ──────────────────────────────────────────────────────────────────────
const raw = await Bun.stdin.text()
let event: Record<string, any> = {}
try { event = JSON.parse(raw) } catch {}

const sessionId = extractSessionId(event)
const retryCount = extractRetryCount(event)
const responseText = extractResponseText(event)

if (!responseText.trim()) process.exit(0)

const urls = extractCitationUrls(responseText)
if (urls.length === 0) process.exit(0)

// ── Verify all URLs in parallel ───────────────────────────────────────────────
const results = await Promise.all(urls.map(verifyUrl))
const failures = results.filter(r => !r.ok)
const ts = new Date().toISOString()

// ── Log results ───────────────────────────────────────────────────────────────
mkdirSync(join(REPO, "logs"), { recursive: true })
for (const r of results) {
  const tag = r.ok ? "VERIFIED" : "FAILED"
  appendFileSync(ERROR_LOG, `${ts}\t${sessionId}\t${tag}\t${r.status}\t${r.url}${r.error ? "\t" + r.error : ""}\n`)
}

if (failures.length === 0) {
  process.stderr.write(`✅ [citation-validator] all ${results.length} citation URL(s) verified\n`)
  process.exit(0)
}

// ── Emit block decision (Claude Code + Copilot CLI honor this) ────────────────
if (retryCount >= MAX_RETRIES) {
  process.stderr.write(`⚠️  [citation-validator] ${failures.length} URL(s) failed after ${MAX_RETRIES} retries — accepting turn, see logs/citation-errors.log\n`)
  process.exit(0)
}

const failedList = failures.map(r => `  - ${r.url} (HTTP ${r.status}${r.error ? " — " + r.error : ""})`).join("\n")

// stdout → decision JSON consumed by the runtime hook handler
const decision = {
  decision: "block",
  reason: `Citation validation failed: ${failures.length} of ${results.length} URL(s) could not be verified.`,
  additionalContext: [
    `The following cited URLs returned errors when verified by the citation-validator hook:`,
    failedList,
    ``,
    `Please re-fetch each failed URL using web_fetch, quote verbatim text from the actual response,`,
    `and update your citations. If a URL is genuinely unreachable, mark it [FETCH FAILED: <reason>]`,
    `and do NOT cite it as a source.`,
    ``,
    `(Retry ${retryCount + 1}/${MAX_RETRIES})`,
  ].join("\n"),
}

process.stdout.write(JSON.stringify(decision) + "\n")
process.exit(0)
