export const meta = {
  name: 'weekly-brief',
  description: 'Weekly investment brief: collect signals, cross-reference, parallel quorum, risk veto, synthesize',
  phases: [
    { title: 'Collect' },
    { title: 'Quorum' },
    { title: 'Synthesize' },
  ],
}

// PHASE 1 — collect every signal in parallel (each agent runs one skill, returns structured findings)
phase('Collect')
const CAND_SCHEMA = {
  type: 'object',
  properties: {
    candidates: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          ticker: { type: 'string' },
          source: { type: 'string' },
          note: { type: 'string' },
        },
        required: ['ticker', 'source'],
      },
    },
    summary: { type: 'string' },
  },
  required: ['candidates', 'summary'],
}

const signals = await parallel([
  () => agent('Run /regime-detection. Return regime + exposure + 1-line rationale as the summary; candidates [].', { label: 'regime', schema: CAND_SCHEMA }),
  () => agent('Run /fomc-monitor. Summary = tone + next meeting + priced move; candidates [].', { label: 'fed', schema: CAND_SCHEMA }),
  () => agent('Run /13f-watch. Return NEW deduped institutional buys as candidates (source=13F).', { label: '13f', schema: CAND_SCHEMA }),
  () => agent('Run /congressman-stock-watch (90d). NEW deduped purchases as candidates (source=congress).', { label: 'congress', schema: CAND_SCHEMA }),
  () => agent('Read /tmp/narrative.jsonl + run /trend-stock-research broad. Tickers with live catalysts as candidates (source=journalism).', { label: 'journalism', schema: CAND_SCHEMA }),
  () => agent('Read /tmp/dip_candidates.jsonl. Each as a candidate (source=dip).', { label: 'dips', schema: CAND_SCHEMA }),
]).then(r => r.filter(Boolean))

// Cross-reference: a ticker surfaced by >=2 sources = elevated conviction. Dedup, count sources.
const bySources = {}
for (const s of signals) for (const c of (s.candidates || [])) {
  (bySources[c.ticker] ||= new Set()).add(c.source)
}
const ranked = Object.entries(bySources)
  .map(([ticker, srcs]) => ({ ticker, sources: [...srcs], n: srcs.size }))
  .sort((a, b) => b.n - a.n)
const top = ranked.slice(0, 5)
log(`Collected ${ranked.length} candidates; top ${top.length} by source-convergence: ${top.map(t => `${t.ticker}(${t.n})`).join(', ')}`)

// PHASE 2 — quorum: each top candidate judged by independent lenses IN PARALLEL
phase('Quorum')
const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['BUY', 'ADD', 'HOLD', 'TRIM', 'SELL'] },
    conviction: { type: 'integer', minimum: 1, maximum: 5 },
    reason: { type: 'string' },
    invalidation: { type: 'string' },
    dissent: { type: 'string' },
  },
  required: ['verdict', 'conviction', 'reason', 'invalidation'],
}
const LENSES = ['analytics-warren-buffett', 'analytics-stanley-druckenmiller', 'analytics-lyn-alden', 'fundamental-analysis']

const judged = await parallel(top.map(t => () =>
  parallel(LENSES.map(lens => () =>
    agent(`Apply /${lens} to: should I BUY/HOLD/SELL ${t.ticker}? It surfaced from ${t.sources.join('+')}. Give verdict, conviction 1-5, one reason, what would change your mind, your blind spot.`,
      { label: `${t.ticker}:${lens}`, phase: 'Quorum', schema: VERDICT_SCHEMA })
  )).then(votes => ({ ticker: t.ticker, sources: t.sources, votes: votes.filter(Boolean) }))
))

// PHASE 3 — risk veto + synthesize
phase('Synthesize')
const risked = await parallel(judged.filter(Boolean).map(j => () =>
  agent(`Apply /risk-management VETO to a proposed BUY of ${j.ticker}. Quorum votes: ${JSON.stringify(j.votes)}. VETO if it takes any name >10% of book or regime is RISK_OFF. Return PASS or VETO + reason.`,
    { label: `risk:${j.ticker}`, phase: 'Synthesize' })
    .then(verdict => ({ ...j, risk: verdict }))
))

const brief = await agent(
  `Write the INVESTMENT BRIEF. Inputs:\nSIGNALS: ${JSON.stringify(signals.map(s => s.summary))}\nCANDIDATES+QUORUM+RISK: ${JSON.stringify(risked.filter(Boolean))}\n` +
  `Format: header (REGIME/FED), PRIORITY ACTIONS, NEW BUY IDEAS (only risk=PASS, with quorum conviction + dissent + invalidation), HOLDS, COULD NOT VERIFY. ` +
  `State 13F (45d) + STOCK Act (30-45d) lag. RECOMMEND-ONLY, educational. Preserve dissent — do not average it away.`,
  { label: 'brief', phase: 'Synthesize' }
)

return brief
