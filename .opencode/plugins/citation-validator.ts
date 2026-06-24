/**
 * citation-validator.ts — OpenCode plugin
 * Thin adapter: calls the universal citation-validator.ts script on session.idle.
 * The script handles URL extraction, cold re-fetch, and decision output.
 *
 * Place in .opencode/plugins/ (project) or ~/.config/opencode/plugins/ (global).
 */
import type { Plugin } from "@opencode-ai/plugin"

const VALIDATOR = "/Users/engineer/workspace/backtest/.claude/hooks/citation-validator.ts"

export const CitationValidator: Plugin = async ({ $, directory }) => {
  return {
    "session.idle": async (event: any) => {
      // Build a normalized payload matching the universal script's expected format
      const messages: any[] = event?.messages ?? event?.session?.messages ?? []
      const lastAssistant = [...messages].reverse().find((m: any) => m.role === "assistant")
      const responseText: string = typeof lastAssistant?.content === "string"
        ? lastAssistant.content
        : Array.isArray(lastAssistant?.content)
          ? lastAssistant.content.map((c: any) => c?.text ?? "").join("")
          : ""

      if (!responseText.trim()) return

      const payload = JSON.stringify({
        response: responseText,
        sessionId: event?.session?.id ?? "opencode-unknown",
      })

      // Run the universal validator; it logs to logs/citation-errors.log
      // and prints warnings to stderr. OpenCode does not honor block decisions
      // from plugins, so we just capture stderr output for visibility.
      const result = await $`echo ${payload} | bun ${VALIDATOR}`.nothrow().cwd(directory)
      if (result.stderr) console.warn(result.stderr.toString())
    },
  }
}
