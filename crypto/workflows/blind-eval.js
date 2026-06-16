export const meta = {
  name: 'blind-eval',
  description: 'Blind measurement half of the improvement loop: fan out N judges over already-produced research reports (read by file). No workflow nesting — target runs are orchestrated externally (Workflow tool), this only scores. Judges see ONLY the report; never the code, the rubric author, or any prior score.',
  phases: [{ title: 'Judge', detail: 'N blind judges per report, median of judges, drop outlier' }],
}

// Why this is separate from improve-workflow: nested workflow() of a heavy target throws/returns null
// in this runtime, so the loop CANNOT self-run the target. The supervisor runs the target (Workflow tool)
// and passes report PATHS here. Measurement is a workflow; running+editing stays orchestrator-driven.
// Default proof-cases: blind-rank a known-BAD report (iter1, news seat failed) vs a known-GOOD one
// (iter4). A trustworthy blind judge must score iter4 > iter1. Override via args.cases when available.
const Q = 'BTC reached 65k$ from the drop to 61k$. I hold 30% in COIN. I don\'t have BTC direct exposure. Should I buy it today?'
const P = '~30% COIN; no direct BTC; ~$0.5M risk capital.'
const DEFAULT_CASES = [
  { question: Q, portfolio: P, reportPath: '/Users/engineer/workspace/backtest/crypto/eval/iter1.report.md' },
  { question: Q, portfolio: P, reportPath: '/Users/engineer/workspace/backtest/crypto/eval/iter4.report.md' },
]
const CASES = (args && args.cases && args.cases.length) ? args.cases : DEFAULT_CASES
const JUDGES = (args && args.judges) || 3
log(`blind-eval: ${CASES.length} case(s), ${JUDGES} judges each`)

const JUDGE_SCHEMA = {
  type: 'object',
  properties: {
    score: { type: 'number' },                         // 0-100
    evidence_grounding: { type: 'number' },            // 0-50 sub-score (>=50% of weight on grounding)
    module_gaps: { type: 'array', items: { type: 'object', properties: {
      module: { type: 'string' }, gap: { type: 'string' } } } },
    one_line: { type: 'string' },
  },
  required: ['score', 'module_gaps'],
}

const JUDGE_RUBRIC =
  `You are an INDEPENDENT, HARSH research grader. You see ONLY the report below. You do NOT know who wrote the ` +
  `workflow, you have NO prior score, there is NO target to hit. Grade 0-100 on YOUR OWN merits. Most real-world ` +
  `research answers are MEDIOCRE — anchor your scale so 50 = competent-but-with-real-holes, 70 = solid, ` +
  `85+ = genuinely excellent with the evidence actually present. Do NOT cluster every report at 85-90.\n` +
  `EVIDENCE GROUNDING is >=50% of the score and is the FLOOR, not a bonus:\n` +
  `- A DECISION-CRITICAL evidence category that is missing/[UNAVAILABLE] caps the report HARD even if honestly ` +
  `flagged. Honesty avoids the fabrication cap; it does NOT restore the missing evidence. For a "buy TODAY" ` +
  `timing question, the news/catalyst read is decision-critical: if the news seat DID NOT RUN, grounding <=25/50 ` +
  `and TOTAL <= 65. If TWO+ critical categories (e.g. news AND ETF-flows AND on-chain core) are absent, TOTAL <= 55.\n` +
  `- Every quantitative claim must be sourced+dated; wide ranges from JS-snippets or unresolved conflicts ($54k vs ` +
  `$76k) are soft evidence — dock for them.\n` +
  `The remaining <=50%: answers the actual question, portfolio-aware (buy AND sell), disagreement preserved, ` +
  `disciplined actionable plan with invalidation, calibration (uniform "medium" across all seats = under-calibrated, dock it).\n` +
  `Hard caps (lowest wins): fabricated number/odds-from-digest -> 40; ignores the portfolio -> 50; a category ` +
  `SILENTLY dropped (not flagged) -> 60; a decision-critical category [UNAVAILABLE] -> 65.\n` +
  `Set evidence_grounding (0-50) explicitly. Return module_gaps naming the weakest sections. Be harsh; a report ` +
  `that cannot see its single most decision-relevant input is NOT an 88.`

phase('Judge')
const scored = await pipeline(CASES, async (c) => {
  const prompt = `${JUDGE_RUBRIC}\n\nQUESTION ASKED: ${c.question}\nPORTFOLIO: ${c.portfolio}\n\n` +
    `Use the Read tool on ${c.reportPath} to load the report (that file is the only thing you may see), then score it.`
  const judges = (await parallel(Array.from({ length: JUDGES }, (_, j) => () =>
    agent(prompt, { label: `judge:${j}:${c.reportPath.split('/').pop()}`, phase: 'Judge', schema: JUDGE_SCHEMA })
  ))).filter(Boolean)
  // median, drop furthest outlier
  let xs = judges.map(s => s.score)
  if (xs.length > 2) { const m = xs.reduce((a, b) => a + b, 0) / xs.length
    let wi = 0, wd = -1; xs.forEach((v, i) => { const d = Math.abs(v - m); if (d > wd) { wd = d; wi = i } })
    xs = xs.filter((_, i) => i !== wi) }
  xs.sort((a, b) => a - b)
  const mid = Math.floor(xs.length / 2)
  const median = xs.length ? (xs.length % 2 ? xs[mid] : (xs[mid - 1] + xs[mid]) / 2) : null
  return { reportPath: c.reportPath, median, judge_scores: judges.map(s => s.score),
    gaps: judges.flatMap(s => s.module_gaps || []) }
})

const overall = scored.filter(s => s.median != null)
const mean = overall.length ? overall.reduce((a, s) => a + s.median, 0) / overall.length : null
log(`Blind eval done: ${overall.map(s => `${s.reportPath.split('/').pop()}=${s.median}`).join('  ')}`)
return { mean, perCase: scored }
