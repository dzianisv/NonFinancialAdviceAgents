export const meta = {
  name: 'research-market',
  description: 'Unified portfolio-aware research (crypto + equities). An LLM MANAGER discovers the available skills live and decides everything — assets, data seats, news feeds, panel lenses, consolidation desk, chair — then the desk runs: gather → consolidate → panel → decide → ledger. NOTHING about the roster is hardcoded here; this script only dispatches the full skill names the manager returns. All substance lives in .agents/skills.',
  phases: [
    { title: 'Intake', detail: 'manager discovers skills live, interprets the query → assets, seats, feeds, panel, desk, chair' },
    { title: 'Gather', detail: 'parallel data seats (manager-selected), each following its own skill' },
    { title: 'Consolidate', detail: 'manager-selected desk skill merges seats into one brief' },
    { title: 'Panel', detail: 'manager-selected lenses debate + non-voting behavioral guardrail' },
    { title: 'Decide', detail: 'manager-selected chair: portfolio-aware buy/sell decision' },
    { title: 'Ledger', detail: 'log the dated chair call per asset to the forecast-ledger' },
  ],
}

// Explicit model — use 'sonnet' (resolves in Claude Code runtime) not 'claude-sonnet-4' (doesn't resolve).
const MODEL = 'sonnet'

const SKILL = '/Users/engineer/workspace/backtest/.agents/skills'
const LEDGER_PY = `${SKILL}/forecast-ledger/ledger.py`

// Inputs via args (no long text here). Date can't come from Date.now() (throws in this runtime).
// The query is interpreted by the LLM MANAGER (Phase 0) which DISCOVERS skills live — no hardcoded roster.
// PORTABILITY: some runtimes (OpenCode) deliver `args` as an object; others (Claude Code Workflow tool)
// deliver it as a JSON STRING. Normalize to an object or EVERY field silently defaults (the "no question"
// trap that wastes a full run). Never assume args is an object.
const ARGS = (typeof args === 'string')
  ? (() => { try { return JSON.parse(args) || {} } catch (e) { return { query: args } } })()
  : (args && typeof args === 'object' ? args : {})
const REPORT_DATE = ARGS.date || '2026-06-15'
// Accept both 'question' and 'query' keys — callers use both interchangeably.
const QUESTION = ARGS.question || ARGS.query || '(no question provided)'
const RAW_PORTFOLIO = ARGS.portfolio || ''   // empty = caller gave none; manager must NOT invent one
const ANCHOR = ARGS.anchor || ''             // optional seed; '' → Gather fetches LIVE

const PLAN_SCHEMA = {
  type: 'object',
  properties: {
    asset_class: { type: 'string' },
    assets: { type: 'array', items: { type: 'string' } },
    side: { type: 'string' },
    horizon: { type: 'string' },
    portfolio_provided: { type: 'boolean' },
    portfolio_summary: { type: 'string' },
    gather_skills: { type: 'array', items: { type: 'string' } },
    feeds: { type: 'array', items: { type: 'string' } },
    panel_skills: { type: 'array', items: { type: 'string' } },
    guardrail_skill: { type: 'string' },
    desk_skill: { type: 'string' },
    chair_skill: { type: 'string' },
    chair_framing: { type: 'string' },
    focus: { type: 'string' },
    notes: { type: 'string' },
  },
  required: ['asset_class', 'assets', 'side', 'portfolio_provided', 'portfolio_summary',
    'gather_skills', 'panel_skills', 'desk_skill', 'chair_skill'],
}

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
    verdict: { type: 'string', enum: ['BUY_NOW', 'ADD', 'SCALE', 'DCA', 'HOLD', 'WAIT', 'TRIM', 'AVOID'] },
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
    // Per-asset conviction so the ledger logs a CALIBRATED probability per asset instead of one panel-level
    // number for all. Optional — the ledger falls back to the panel bull-fraction if absent/malformed.
    per_asset: { type: 'array', items: { type: 'object', properties: {
      asset: { type: 'string' },
      conviction: { type: 'string', enum: ['high', 'medium', 'low'] },
      prob: { type: 'number' },           // 0..1 chance the bull thesis plays out by the horizon
      action: { type: 'string' },         // e.g. ACCUMULATE / PROBE / WATCHLIST / AVOID
      invalidation: { type: 'string' },
    }, required: ['asset'] } },
  },
  required: ['answer', 'decision', 'tranche_plan', 'agreement', 'disagreement'],
}

// ---------- Phase 0: INTAKE (manager discovers skills live + plans the desk) ----------
phase('Intake')
const plan = await agent(
  `Follow ${SKILL}/research-manager/SKILL.md as the intake/triage desk head. FIRST discover the available skills ` +
  `live (list ${SKILL}/ and read each SKILL.md description — do NOT rely on memory), THEN return the research plan ` +
  `naming every component by its real discovered directory name.\n` +
  `RAW QUERY: ${QUESTION}\nPORTFOLIO PASSED BY CALLER: ${RAW_PORTFOLIO || '(none — caller gave no holdings; do NOT invent any)'}\nAs-of: ${REPORT_DATE}`,
  { label: 'manager-intake', phase: 'Intake', schema: PLAN_SCHEMA, model: MODEL })

if (!plan) { log('FATAL: manager returned no plan; aborting.'); return { error: 'no plan from manager' } }

// Resolve plan → run inputs (all manager-driven; safe fallbacks only for emptiness, never fabricate holdings).
// Prefer caller-supplied asset_class/assets over manager inference — avoids crypto default when query is clearly equities.
const CALLER_CLASS = ARGS.asset_class || ''
const CALLER_ASSETS = (Array.isArray(ARGS.assets) && ARGS.assets.length) ? ARGS.assets : []
const ASSET_CLASS = CALLER_CLASS || plan.asset_class || 'equities'
const ASSETS = (CALLER_ASSETS.length ? CALLER_ASSETS : (Array.isArray(plan.assets) && plan.assets.length) ? plan.assets : ['UNKNOWN']).map(a => String(a).toUpperCase())
const ASSET_LIST = ASSETS.join(', ')
const portfolioProvided = !!(plan.portfolio_provided && RAW_PORTFOLIO)
const PORTFOLIO = portfolioProvided ? (plan.portfolio_summary || RAW_PORTFOLIO)
  : 'NO PORTFOLIO PROVIDED by the user. Do NOT assume, invent, or carry over any holdings. Answer at the market/asset level with general sizing/risk discipline only.'
const FOCUS = plan.focus || ''
const FRAMING = plan.chair_framing || ''
const FEEDS = (Array.isArray(plan.feeds) && plan.feeds.length) ? plan.feeds : []
// Cap gather+panel to keep total agents = ASSETS × (MAX_GATHER + MAX_PANEL) manageable.
// With 13 assets × (3+3) = 78 agents — completes in ~10 min. Uncapped → 100+ agents → 30+ min stall.
const MAX_GATHER = 3
const MAX_PANEL = 3
const gatherSkills = (Array.isArray(plan.gather_skills) ? plan.gather_skills : []).filter(Boolean).slice(0, MAX_GATHER)
const panelSkills = (Array.isArray(plan.panel_skills) ? plan.panel_skills : []).filter(Boolean).slice(0, MAX_PANEL)
if (plan.gather_skills && plan.gather_skills.length > MAX_GATHER) log(`Gather capped ${plan.gather_skills.length}→${MAX_GATHER}: dropped ${plan.gather_skills.slice(MAX_GATHER).join(', ')}`)
if (plan.panel_skills && plan.panel_skills.length > MAX_PANEL) log(`Panel capped ${plan.panel_skills.length}→${MAX_PANEL}: dropped ${plan.panel_skills.slice(MAX_PANEL).join(', ')}`)
const guardrailSkill = plan.guardrail_skill || ''
const deskSkill = plan.desk_skill || ''
const chairSkill = plan.chair_skill || ''

log(`INTAKE — class: ${ASSET_CLASS} | assets: ${ASSET_LIST} | side: ${plan.side || '?'} | portfolio: ${portfolioProvided ? 'provided' : 'NONE (market-level)'} | gather: ${gatherSkills.length} | feeds: ${FEEDS.length} | panel: ${panelSkills.length} | desk: ${deskSkill || '?'} | chair: ${chairSkill || '?'}`)
if (FOCUS) log(`INTAKE focus: ${FOCUS}`)
if (plan.notes) log(`INTAKE notes: ${plan.notes}`)
if (QUESTION === '(no question provided)') log('WARNING: no question passed — running with empty question.')
if (!gatherSkills.length) log('WARNING: manager selected no gather seats — brief will be empty.')
if (!panelSkills.length) log('WARNING: manager selected no panel lenses — no votes will be cast.')
if (!deskSkill || !chairSkill) log('WARNING: manager did not name a desk and/or chair skill.')

// Per-asset context builder — each agent focuses on ONE asset, avoiding giant multi-asset context blowup.
const ctxFor = (asset) =>
  `Question: ${QUESTION}\nAsset class: ${ASSET_CLASS}\nFocus asset: ${asset}\nAll assets in this research: ${ASSET_LIST}\nDesk focus: ${FOCUS || 'none'}\nPortfolio: ${PORTFOLIO}\nNews feeds: ${FEEDS.length ? FEEDS.join(', ') : '(none)'}\nAs-of: ${REPORT_DATE}`
const seedNote = ANCHOR ? `\nSeed (verify+extend): ${ANCHOR}` : `\nNo seed — fetch LIVE; never fabricate, mark UNAVAILABLE if gated.`

// ---------- Phase 1: GATHER — per-asset pipeline (each asset × all gather skills in parallel) ----------
// Old: one agent covers ALL assets per skill → massive context, stalls on large lists.
// New: pipeline(assets) so each asset gets dedicated gather agents → O(1 asset) wall-clock.
phase('Gather')
const gatherByAsset = await pipeline(
  ASSETS,
  async (asset) => {
    const seats = await parallel(gatherSkills.map(skill => () =>
      agent(
        `Follow ${SKILL}/${skill}/SKILL.md as a DATA-ONLY gather seat (no buy/sell opinion). Focus on: ${asset} only.\n${ctxFor(asset)}${seedNote}`,
        { label: `${skill}:${asset}`, phase: 'Gather', schema: DATA_SCHEMA, model: MODEL }
      )
    ))
    const filled = seats.map((r, i) => (r && r.findings) ? r
      : { seat: gatherSkills[i], status: 'UNAVAILABLE', findings: [], summary: `[UNAVAILABLE: ${gatherSkills[i]} seat failed]` })
    const missing = filled.filter(r => r.status === 'UNAVAILABLE').map(r => r.seat)
    if (missing.length) log(`Gather ${asset}: UNAVAILABLE: ${missing.join(', ')}`)
    return { asset, seats: filled, complete: missing.length === 0 }
  }
)
const gatherComplete = gatherByAsset.filter(Boolean).every(r => r.complete)
log(`Gather: ${gatherByAsset.filter(Boolean).length}/${ASSETS.length} assets complete`)

// ---------- Phase 2: CONSOLIDATE — per-asset desk brief ----------
phase('Consolidate')
const briefByAsset = await pipeline(
  gatherByAsset.filter(Boolean),
  async ({ asset, seats, complete }) => {
    const brief = await agent(
      `Follow ${SKILL}/${deskSkill}/SKILL.md. Focus on: ${asset}.\n${ctxFor(asset)}\nCompleteness: ${complete ? 'All seats returned.' : 'INCOMPLETE — surface DATA GAPS; do not paper over.'}\nRAW DATA:\n${JSON.stringify(seats, null, 1)}`,
      { label: `${deskSkill}:${asset}`, phase: 'Consolidate', model: MODEL }
    )
    return { asset, brief: brief || '[UNAVAILABLE: desk returned nothing]' }
  }
)
log(`Consolidate: ${briefByAsset.filter(Boolean).length}/${ASSETS.length} briefs`)

// ---------- Phase 3: PANEL — per-asset lenses (each asset × all panel skills in parallel) ----------
phase('Panel')
const panelByAsset = await pipeline(
  briefByAsset.filter(Boolean),
  async ({ asset, brief }) => {
    const votes = await parallel(panelSkills.map(skill => () =>
      agent(
        `Apply the lens in ${SKILL}/${skill}/SKILL.md. Focus ONLY on: ${asset}.\n${ctxFor(asset)}\nReturn seat (=${skill}), read, verdict, sizing, flip-condition, confidence.\n=== BRIEF (${asset}) ===\n${brief}`,
        { label: `${skill}:${asset}`, phase: 'Panel', schema: PANEL_SCHEMA, model: MODEL }
      )
    ))
    const filled = votes.map((v, i) => v || { seat: panelSkills[i], read: '[UNAVAILABLE: seat failed]', verdict: 'WAIT', confidence: 'low' })
    return { asset, brief, votes: filled }
  }
)
log(`Panel: ${panelByAsset.filter(Boolean).length}/${ASSETS.length} assets voted`)

// Guardrail — cross-asset (reads all briefs; non-voting process check only).
const allBriefs = briefByAsset.filter(Boolean).map(b => `=== ${b.asset} ===\n${b.brief}`).join('\n\n')
const guardrail = guardrailSkill ? await agent(
  `Follow ${SKILL}/${guardrailSkill}/SKILL.md as a NON-VOTING guardrail (no BUY/SELL verdict). Question: ${QUESTION}\nAssets: ${ASSET_LIST}\nAssess: FOMO-vs-anchoring trap, staged scale-in soundness, sizing survivable to -50%, one guardrail rule per asset.\n${allBriefs}`,
  { label: guardrailSkill, phase: 'Panel', model: MODEL }) : '(no guardrail skill selected)'

// Flatten all per-asset votes for report/ledger compatibility.
const verdicts = panelByAsset.filter(Boolean)
  .flatMap(({ asset, votes }) => votes.map(v => ({ ...v, asset })))
log(`Panel: ${verdicts.filter(v => v.read.indexOf('[UNAVAILABLE') === -1).length}/${verdicts.length} total votes cast`)

// ---------- Phase 4: DECIDE — cross-asset chair ranks all assets ----------
phase('Decide')
const totalVotes = verdicts.filter(v => v.read.indexOf('[UNAVAILABLE') === -1).length
const decision = await agent(
  `Follow ${SKILL}/${chairSkill}/SKILL.md to chair the committee.\nQuestion: ${QUESTION}\nAssets: ${ASSET_LIST}\nChair framing: ${FRAMING || 'none'}\nPortfolio: ${PORTFOLIO}\n` +
  `Populate per_asset[] for EVERY asset (${ASSET_LIST}): {asset, conviction high|medium|low, prob 0..1 bull thesis by ${REPORT_DATE.slice(0,4)}-12-31, action, invalidation}. Rank by conviction — do NOT give every asset the same prob.\n` +
  `EXACT VOTING-SEAT COUNT = ${totalVotes}. verdict_tally buckets MUST sum to ${totalVotes}.\n` +
  `=== PER-ASSET PANEL VERDICTS ===\n${JSON.stringify(panelByAsset.filter(Boolean), null, 1)}\n=== GUARDRAIL (non-voting) ===\n${guardrail}`,
  { label: chairSkill || 'chair-decision', phase: 'Decide', schema: DECISION_SCHEMA, model: MODEL })

// ---------- Phase 5: WRITE REPORT ----------
const reportPath = `/Users/engineer/workspace/backtest/research/research.${ASSET_CLASS}.${REPORT_DATE}.md`
// Per-asset vote table: one row per asset × lens combination.
const seatRows = panelByAsset.filter(Boolean).flatMap(({ asset, votes }) =>
  votes.map(v => `| ${asset} | ${v.seat} | **${v.verdict}** | ${v.confidence} |`)
).join('\n')
const seatDetail = panelByAsset.filter(Boolean).map(({ asset, votes }) =>
  `### ${asset}\n` + votes.map(v =>
    `**${v.seat}** — ${v.verdict} (${v.confidence}): ${v.read}\n- Sizing: ${v.sizing || 'n/a'} · Flips if: ${v.flip || 'n/a'}`
  ).join('\n\n')
).join('\n\n---\n\n')
const reportMd = `# Research — ${ASSET_LIST} (${ASSET_CLASS}) — ${REPORT_DATE}

> Question: ${QUESTION}
> Portfolio: ${PORTFOLIO}
> Desk assembled by \`research-manager\`: gather [${gatherSkills.join(', ')}] · panel [${panelSkills.join(', ')}] · desk ${deskSkill} · chair ${chairSkill}.
> Generated by \`research-market\`. Educational, not advice; re-pull before acting.
${gatherComplete ? '' : `\n> **⚠ INCOMPLETE DATA:** Some gather seats unavailable. Treat with caution.\n`}
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
| Asset | Seat | Verdict | Confidence |
|---|---|---|---|
${seatRows}

## Seat detail
${seatDetail}

## Behavioral guardrail (non-voting)
${guardrail}

---
*Consolidated brief (raw evidence) not persisted — available in the workflow return value \`brief\` field.*
`
// Write + VERIFY + retry — an LLM "Write this file" agent can silently no-op, so never trust it: confirm the
// bytes landed on disk and retry once, then surface LOUDLY rather than claim a path that doesn't exist.
let reportOk = false
for (let attempt = 1; attempt <= 2 && !reportOk; attempt++) {
  await agent(`Use the Write tool to create EXACTLY this file:\n${reportPath}\nWrite this content VERBATIM (no edits/summary). Create parent dirs. After writing, run Bash \`wc -c < ${reportPath}\` to confirm. Reply with just the byte count.\n--- BEGIN ---\n${reportMd}\n--- END ---`,
    { label: attempt === 1 ? 'write-report' : `write-report-retry${attempt}`, phase: 'Decide', model: MODEL })
  const check = await agent(`Run Bash EXACTLY: \`test -f ${reportPath} && wc -c < ${reportPath} || echo MISSING\`. Reply with ONLY the byte count number, or the word MISSING.`,
    { label: `verify-report-${attempt}`, phase: 'Decide', model: MODEL })
  const bytes = parseInt(String(check).replace(/[^0-9]/g, ''), 10) || 0
  reportOk = String(check).indexOf('MISSING') === -1 && bytes > 1000
  log(reportOk ? `Report written + verified (${bytes} bytes): ${reportPath}`
    : `WARNING: write-report attempt ${attempt} did NOT persist (saw: ${String(check).slice(0, 40)}). ${attempt < 2 ? 'Retrying.' : 'GIVING UP — report NOT on disk; downstream must use the returned `decision`/`brief` fields.'}`)
}

// ---------- Phase 6: LEDGER (one row per REAL asset; pseudo-screen tokens excluded) ----------
phase('Ledger')
const bull = ['BUY_NOW', 'ADD', 'SCALE', 'DCA']
// Per-asset implied prob: use only that asset's panel votes (not the full cross-asset pool).
const horizon = REPORT_DATE.slice(0, 4) + '-12-31'
const votingLenses = panelSkills.join(', ') || 'panel'
const impliedProbFor = (asset) => {
  const assetVotes = verdicts.filter(v => v.asset === asset && v.verdict && v.read.indexOf('[UNAVAILABLE') === -1)
  const bullVotes = assetVotes.filter(v => bull.indexOf(v.verdict) !== -1).length
  return assetVotes.length ? (bullVotes / assetVotes.length) : 0.5
}
// Fallback for ledger tally log
const votes = verdicts.filter(v => v && v.verdict && v.read.indexOf('[UNAVAILABLE') === -1)
const bullCount = votes.filter(v => bull.indexOf(v.verdict) !== -1).length
const impliedProb = votes.length ? (bullCount / votes.length) : 0.5
// Only log CLEAN TICKERS. The manager sometimes adds a pseudo-asset (e.g. "ALTS-OPEN-SCREEN") to trigger a
// screen; that is a directive, not a tradeable forecast, and must NEVER become a dated ledger row.
const LEDGER_ASSETS = ASSETS.filter(a => /^[A-Z0-9]{2,6}$/.test(a))
const skippedLedger = ASSETS.filter(a => !/^[A-Z0-9]{2,6}$/.test(a))
if (skippedLedger.length) log(`Ledger: skipping non-ticker pseudo-assets: ${skippedLedger.join(', ')}`)
// ONE-LINE summary only — never dump the full multi-paragraph chair verdict into the CSV --q field (it bloats
// the ledger with literal newlines). Collapse whitespace and cap length.
const oneLine = (s) => String(s || '').replace(/\s+/g, ' ').trim().slice(0, 180)
const ledgerQ = oneLine(decision.decision || decision.answer || '(none)')
const ledgerFlip = oneLine(decision.invalidation) || 'n/a'
// Per-asset conviction map (chair-provided). Falls back to the panel bull-fraction when an asset is absent or
// its prob is not a sane 0..1 number — so the ledger never logs a fabricated or out-of-range probability.
const perAsset = Array.isArray(decision.per_asset) ? decision.per_asset : []
const probFor = (asset) => {
  const hit = perAsset.find(e => e && String(e.asset || '').toUpperCase() === asset)
  const p = hit && Number(hit.prob)
  return (typeof p === 'number' && p > 0 && p <= 1) ? p : impliedProbFor(asset)
}
const flipFor = (asset) => {
  const hit = perAsset.find(e => e && String(e.asset || '').toUpperCase() === asset)
  return oneLine(hit && hit.invalidation) || ledgerFlip
}
const ledgerLogs = await parallel(LEDGER_ASSETS.map(asset => () =>
  agent(
    `Use Bash to run EXACTLY (appends one dated forecast row):\n\n` +
    `python3 ${LEDGER_PY} add --asset ${asset} --q ${JSON.stringify('panel chair call (' + asset + '): ' + ledgerQ)} ` +
    `--p ${probFor(asset).toFixed(2)} --by ${JSON.stringify(horizon)} --lens ${JSON.stringify(votingLenses)} ` +
    `--source research-market --flip ${JSON.stringify(flipFor(asset))} --created ${JSON.stringify(REPORT_DATE)}\n\n` +
    `--p is the chair's per-asset conviction (fallback = per-asset panel tally) — do not change it. If "id exists", re-run once with --id ${asset.toLowerCase()}-${REPORT_DATE}-panel. Reply with the CLI's stdout line.`,
    { label: `ledger-${asset}`, phase: 'Ledger', model: MODEL }))
)
const ledgerLog = LEDGER_ASSETS.map((a, i) => `${a}: ${ledgerLogs[i]}`).join(' | ')
log(`Ledger: ${ledgerLog}`)

return { reportPath, reportPersisted: reportOk, asset_class: ASSET_CLASS, assets: ASSETS, plan, decision, verdicts,
  panelByAsset, briefByAsset, guardrail, complete: gatherComplete,
  ledger: { impliedProb, horizon, lenses: votingLenses, logged: LEDGER_ASSETS, skipped: skippedLedger, result: ledgerLog } }
