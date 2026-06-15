export const meta = {
  name: 'crypto-panel-review',
  description: 'Portfolio-aware crypto research: gather data → consolidate brief → analyst+macro panel → chair buy/sell decision → ledger. All substance lives in .agents/skills; this script only orchestrates.',
  phases: [
    { title: 'Gather', detail: 'parallel data seats, each following its own skill' },
    { title: 'Consolidate', detail: 'research-desk skill merges seats into one brief' },
    { title: 'Panel', detail: 'analyst + macro lenses + non-voting behavioral guardrail' },
    { title: 'Decide', detail: 'crypto-chair skill: portfolio-aware buy/sell decision' },
    { title: 'Ledger', detail: 'log the dated chair call to the forecast-ledger' },
  ],
}

const SKILL = '/Users/engineer/workspace/backtest/.agents/skills'
const LEDGER_PY = `${SKILL}/forecast-ledger/ledger.py`

// Inputs via args (no long text in this script). Date can't come from Date.now() (throws in this runtime).
const REPORT_DATE = (args && args.date) || '2026-06-15'
const QUESTION = (args && args.question) ||
  'BTC reached 65k$ from the drop to 61k$. I hold 30% in COIN. I don\'t have BTC direct exposure. Should I buy it today?'
const PORTFOLIO = (args && args.portfolio) ||
  '~30% of book in COIN (Coinbase equity, a levered crypto-beta proxy); no direct BTC; remainder unspecified. Crypto risk from ~$0.5M risk capital only.'
// Optional seed; default '' so Gather fetches LIVE (no stale-number bias).
const ANCHOR = (args && args.anchor) || ''

const DATA_SCHEMA = {
  type: 'object',
  properties: {
    seat: { type: 'string' },
    findings: { type: 'array', items: { type: 'object', properties: {
      metric: { type: 'string' }, value: { type: 'string' }, asof: { type: 'string' }, source: { type: 'string' },
    }, required: ['metric', 'value'] } },
    summary: { type: 'string' },
    unavailable: { type: 'array', items: { type: 'string' } },
  },
  required: ['seat', 'findings', 'summary'],
}

const PANEL_SCHEMA = {
  type: 'object',
  properties: {
    seat: { type: 'string' }, read: { type: 'string' },
    verdict: { type: 'string', enum: ['BUY_NOW', 'SCALE', 'DCA', 'WAIT', 'AVOID'] },
    sizing: { type: 'string' }, flip: { type: 'string' },
    confidence: { type: 'string', enum: ['low', 'medium', 'high'] },
  },
  required: ['seat', 'read', 'verdict', 'confidence'],
}

const DECISION_SCHEMA = {
  type: 'object',
  properties: {
    answer: { type: 'string' },
    buy_side: { type: 'string' },
    sell_side: { type: 'string' },
    agreement: { type: 'array', items: { type: 'string' } },
    disagreement: { type: 'array', items: { type: 'string' } },
    verdict_tally: { type: 'string' },
    decision: { type: 'string' },
    tranche_plan: { type: 'string' },
    key_risks: { type: 'array', items: { type: 'string' } },
    invalidation: { type: 'string' },
    confidence: { type: 'string' },
  },
  required: ['answer', 'decision', 'tranche_plan', 'agreement', 'disagreement'],
}

const ctx = `Question: ${QUESTION}\nPortfolio: ${PORTFOLIO}\nAs-of: ${REPORT_DATE}`
const seedNote = ANCHOR ? `\nSeed (verify+extend): ${ANCHOR}` : `\nNo seed — fetch LIVE; never fabricate, mark UNAVAILABLE if gated.`

// ---------- Phase 1: GATHER (data only; each seat follows a skill) ----------
phase('Gather')
const gatherSpecs = [
  { label: 'odds', skill: 'prediction-market-odds' },
  { label: 'price+onchain', skill: 'crypto-onchain-data' },
  { label: 'derivatives', skill: 'analyst-derivatives-positioning' },
  { label: 'macro-prints', skill: 'fomc-monitor' },
  { label: 'liquidity-flows', skill: 'crypto-liquidity-data' },
  { label: 'sentiment-regime', skill: 'regime-detection' },
]
const gatherResults = await parallel(gatherSpecs.map(s => () =>
  agent(`Follow ${SKILL}/${s.skill}/SKILL.md as a DATA-ONLY gather seat (no buy/sell opinion). ${ctx}${seedNote}`,
    { label: s.label, phase: 'Gather', schema: DATA_SCHEMA })
))
// Completeness contract: a missing REQUIRED seat is a defect — never dropped, made LOUD.
const rawData = gatherResults.map((r, i) => (r && r.findings) ? r
  : { seat: gatherSpecs[i].label, status: 'UNAVAILABLE', findings: [], summary: `[UNAVAILABLE: ${gatherSpecs[i].label} seat failed to return]` })
const missingSeats = rawData.filter(r => r.status === 'UNAVAILABLE').map(r => r.seat)
const gatherComplete = missingSeats.length === 0
if (!gatherComplete) log(`WARNING: INCOMPLETE GATHER — UNAVAILABLE: ${missingSeats.join(', ')} (run not aborted; gap surfaced).`)
log(`Gather: ${rawData.length - missingSeats.length}/${gatherSpecs.length} seats returned`)

// ---------- Phase 2: CONSOLIDATE (research-desk skill) ----------
phase('Consolidate')
const completeNote = gatherComplete ? 'All categories returned.' : `INCOMPLETE — [UNAVAILABLE]: ${missingSeats.join(', ')}. Surface as DATA GAPS; do not paper over.`
const brief = await agent(
  `Follow ${SKILL}/crypto-research-desk/SKILL.md. ${ctx}\nCompleteness: ${completeNote}\nRAW DATA:\n${JSON.stringify(rawData, null, 1)}`,
  { label: 'consolidate', phase: 'Consolidate' })

// ---------- Phase 3: PANEL (each lens follows its skill, reasons over the brief) ----------
phase('Panel')
const lenses = [
  { seat: 'analyst-crypto', skill: 'analyst-crypto' },
  { seat: 'derivatives-positioning', skill: 'analyst-derivatives-positioning' },
  { seat: 'Druckenmiller', skill: 'analytics-stanley-druckenmiller' },
  { seat: 'Lyn Alden', skill: 'analytics-lyn-alden' },
  { seat: 'Lacy Hunt (dissent)', skill: 'analytics-lacy-hunt' },
  { seat: 'Russell Napier', skill: 'analytics-russell-napier' },
]
const verdicts = (await parallel(lenses.map(l => () =>
  agent(`Apply the lens in ${SKILL}/${l.skill}/SKILL.md to answer the question, reasoning ONLY over the brief (don't re-fetch). ${ctx}\nReturn seat, read, verdict (BUY_NOW/SCALE/DCA/WAIT/AVOID) for the question, sizing, flip-condition, confidence.\n=== BRIEF ===\n${brief}`,
    { label: l.seat, phase: 'Panel', schema: PANEL_SCHEMA })
))).map((r, i) => r || { seat: lenses[i].seat, read: '[UNAVAILABLE: seat failed]', verdict: 'WAIT', confidence: 'low' })
log(`Panel: ${verdicts.filter(v => v.read.indexOf('[UNAVAILABLE') === -1).length}/${lenses.length} seats voted`)

// Housel = NON-VOTING behavioral guardrail (process + sizing only).
const guardrail = await agent(
  `Follow ${SKILL}/analytics-morgan-housel/SKILL.md as a NON-VOTING guardrail (no BUY/SELL verdict). ${ctx}\nAssess: FOMO-vs-anchoring trap, is a tranche scale-in sound, is sizing survivable to -50%, one guardrail rule. Reason over the brief.\n=== BRIEF ===\n${brief}`,
  { label: 'Housel (guardrail)', phase: 'Panel' })

// ---------- Phase 4: DECIDE (crypto-chair skill — portfolio-aware buy/sell) ----------
phase('Decide')
const decision = await agent(
  `Follow ${SKILL}/crypto-chair/SKILL.md to chair the committee and answer the question for THIS portfolio. ${ctx}\n` +
  `=== BRIEF ===\n${brief}\n=== VOTING VERDICTS ===\n${JSON.stringify(verdicts, null, 1)}\n=== HOUSEL GUARDRAIL (non-voting) ===\n${guardrail}`,
  { label: 'chair-decision', phase: 'Decide', schema: DECISION_SCHEMA })

// ---------- Phase 5: WRITE REPORT ----------
const reportPath = `/Users/engineer/workspace/backtest/research/research.crypto.${REPORT_DATE}.md`
const seatRows = verdicts.map(v => `| ${v.seat} | **${v.verdict}** | ${v.confidence} |`).join('\n')
const seatDetail = verdicts.map(v => `### ${v.seat} — ${v.verdict} (${v.confidence})\n${v.read}\n\n- **Sizing:** ${v.sizing || 'n/a'}\n- **Flips if:** ${v.flip || 'n/a'}`).join('\n\n')
const reportMd = `# Crypto Research — ${REPORT_DATE}

> Question: ${QUESTION}
> Portfolio: ${PORTFOLIO}
> Generated by \`crypto-panel-review\`. Educational, not advice; re-pull before acting.
${gatherComplete ? '' : `\n> **⚠ INCOMPLETE DATA:** UNAVAILABLE seats: ${missingSeats.join(', ')}. Treat with caution.\n`}
## Answer
**${decision.answer || decision.decision}**

## Decision
${decision.decision}

**Buy-side:** ${decision.buy_side || 'n/a'}
**Sell/trim-side:** ${decision.sell_side || 'n/a'}
**Tranche plan:** ${decision.tranche_plan}
**Verdict tally:** ${decision.verdict_tally || 'see table'}
**Invalidation:** ${decision.invalidation || 'n/a'}

### Agreement
${(decision.agreement || []).map(a => `- ${a}`).join('\n')}
### Disagreement (preserved)
${(decision.disagreement || []).map(d => `- ${d}`).join('\n')}
### Key risks
${(decision.key_risks || []).map(r => `- ${r}`).join('\n')}

## Panel votes
| Seat | Verdict | Confidence |
|---|---|---|
${seatRows}

## Seat detail
${seatDetail}

## Behavioral guardrail (Housel — non-voting)
${guardrail}

## Consolidated brief (evidence)
${brief}
`
await agent(`Use the Write tool to create EXACTLY this file:\n${reportPath}\nWrite this content VERBATIM (no edits/summary). Create parent dirs. Reply with just the path.\n--- BEGIN ---\n${reportMd}\n--- END ---`,
  { label: 'write-report', phase: 'Decide' })
log(`Report written: ${reportPath}`)

// ---------- Phase 6: LEDGER ----------
phase('Ledger')
const bull = ['BUY_NOW', 'SCALE', 'DCA']
const votes = verdicts.filter(v => v && v.verdict && v.read.indexOf('[UNAVAILABLE') === -1)
const bullCount = votes.filter(v => bull.indexOf(v.verdict) !== -1).length
const impliedProb = votes.length ? (bullCount / votes.length) : 0.5
const horizon = REPORT_DATE.slice(0, 4) + '-12-31'
const votingLenses = votes.map(v => v.seat).join(', ') || 'crypto-panel'
const ledgerLog = await agent(
  `Use Bash to run EXACTLY (appends one dated forecast row):\n\n` +
  `python3 ${LEDGER_PY} add --asset BTC --q ${JSON.stringify('crypto-panel chair call: ' + (decision.answer || decision.decision || '(none)'))} ` +
  `--p ${impliedProb.toFixed(2)} --by ${JSON.stringify(horizon)} --lens ${JSON.stringify(votingLenses)} ` +
  `--source crypto-panel-review --flip ${JSON.stringify(decision.invalidation || 'n/a')} --created ${JSON.stringify(REPORT_DATE)}\n\n` +
  `--p is derived from the voting tally (${bullCount}/${votes.length} deploy) — do not change it. If "id exists", re-run once with --id btc-${REPORT_DATE}-panel. Reply with the CLI's stdout line.`,
  { label: 'ledger-log', phase: 'Ledger' })
log(`Ledger: ${ledgerLog}`)

return { reportPath, decision, verdicts, guardrail, brief, complete: gatherComplete, missing: missingSeats,
  ledger: { impliedProb, horizon, lenses: votingLenses, result: ledgerLog } }
