#!/usr/bin/env bun
/**
 * agentStop / Stop hook — citation validator
 * Works across Claude Code AND Copilot CLI (payload formats differ — both handled).
 *
 * Claude Code input:  { session_id, transcript_path }
 * Copilot CLI input:  { sessionId?, agentResponse?, cwd, timestamp }
 *
 * Parses last agent response for [T1]/[T2]/[T3] URLs, diffs against the real
 * fetch log written by log-web-fetch.ts, flags hallucinated citations.
 */

import { join } from "path"

const REPO = "/Users/engineer/workspace/backtest"
const CITATION_RX = /\[T[123]\]\s+(https?:\/\/\S+)/g

const input = await Bun.stdin.text()
const event = JSON.parse(input)

const sessionId: string = event.session_id ?? event.sessionId ?? "unknown"
const transcriptPath: string = event.transcript_path ?? ""
// Copilot CLI may pass the agent response text directly
const directResponse: string = event.agentResponse ?? event.response ?? ""
const fetchLog = `/tmp/cc-fetches-${sessionId}.jsonl`
const errorLog = join(REPO, "logs/citation-errors.log")

// ── 1. Extract cited URLs — try transcript first, then direct response ────
const cited: string[] = []

const extractFromText = (text: string) => {
  for (const match of text.matchAll(CITATION_RX)) {
    cited.push(match[1].replace(/[.,;)]+$/, ""))
  }
}

if (transcriptPath) {
  try {
    const transcript = await Bun.file(transcriptPath).text()
    const lines = transcript.split("\n").filter(Boolean)
    const assistantLines = lines
      .map(l => { try { return JSON.parse(l) } catch { return null } })
      .filter(m => m?.role === "assistant")
    extractFromText(assistantLines.map(m => m?.content ?? "").join("\n"))
  } catch {}
}

// Copilot CLI: agentResponse is the text payload
if (cited.length === 0 && directResponse) {
  extractFromText(directResponse)
}

if (cited.length === 0) process.exit(0)

// ── 2. Load actually-fetched URLs ─────────────────────────────────────────
const fetched = new Set<string>()
try {
  const raw = await Bun.file(fetchLog).text()
  for (const line of raw.split("\n").filter(Boolean)) {
    try {
      const { url, success } = JSON.parse(line)
      if (success) fetched.add(url)
    } catch {}
  }
} catch {}

// ── 3. Diff — cited but not fetched = hallucinated ────────────────────────
const ts = new Date().toISOString()
const failures: string[] = []

for (const url of cited) {
  if (!fetched.has(url)) failures.push(url)
}

if (failures.length > 0) {
  await Bun.mkdir(join(REPO, "logs"), { recursive: true })
  const existing = await Bun.file(errorLog).exists() ? await Bun.file(errorLog).text() : ""
  const newLines = failures.map(u => `${ts}\t${sessionId}\tHALLUCINATED_CITATION\t${u}`).join("\n")
  await Bun.write(errorLog, existing + newLines + "\n")
  process.stderr.write(`⚠️  [citation-validator] ${failures.length} cited URL(s) never fetched — see logs/citation-errors.log\n`)
}

// ── 4. Clean up session fetch log ─────────────────────────────────────────
try { await Bun.file(fetchLog).unlink() } catch {}

process.exit(0)
