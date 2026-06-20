export const meta = {
  name: 'research-trend-stocks',
  description: 'Research-first trend-stock discovery pipeline: quantitative pre-screen → EDGAR×phrase + WebSearch×angle fan-out (50+ parallel HTTP agents, no browser serialization) → non-obvious beneficiary mapping → skeptic filter → multi-lens-quorum. v2: replaced single-browser journalism readers with independent-tap parallelism.',
  phases: [
    { title: 'Pre-screen', detail: 'Run emerging_scan.py --top N; produce ranked ticker list with momentum/vol scores' },
    { title: 'Journalism', detail: 'EDGAR×phrase (30 agents) + WebSearch×angle (25 agents) fan-out — all independent HTTP taps, no browser serialization' },
    { title: 'Beneficiary', detail: 'Map non-obvious beneficiary chains from the journalism findings' },
    { title: 'Skeptic', detail: 'Kill overhyped (+150% 12mo), require concrete catalyst + timeline' },
    { title: 'Quorum', detail: 'Route survivors to multi-lens-quorum for defended buy/hold/pass verdict' },
    { title: 'Report', detail: 'Write dated research report + log to forecast-ledger' },
  ],
}

// Explicit model — OpenCode's default model picker can fail when copilot model-list fetch is flaky.
const MODEL = 'claude-sonnet-4'

const SKILL = '/Users/engineer/workspace/backtest/.agents/skills'
const SCAN_PY = `${SKILL}/trend-stock-research/scripts/emerging_scan.py`
const VELOCITY_PY = `${SKILL}/trend-stock-research/scripts/mention_velocity.py`
const LEDGER_PY = `${SKILL}/forecast-ledger/ledger.py`

// Inputs via args
const REPORT_DATE = (args && args.date) || '2026-06-16'
const TOP_N = (args && args.top) || 25
const THEMES = (args && args.themes) || ''  // optional comma-sep override; '' = let scan decide
const PORTFOLIO = (args && args.portfolio) || ''
const MODE = (args && args.mode) || 'weekly'  // weekly (full) | daily (ingest-only, stops after journalism)

// Schemas for structured subagent outputs
const SCAN_SCHEMA = {
  type: 'object',
  properties: {
    tickers: { type: 'array', items: { type: 'object', properties: {
      symbol: { type: 'string' }, name: { type: 'string' }, theme: { type: 'string' },
      mom_6m: { type: 'number' }, vol_ratio: { type: 'number' }, score: { type: 'number' },
    }, required: ['symbol', 'theme', 'score'] } },
    themes: { type: 'array', items: { type: 'string' } },
    scan_date: { type: 'string' },
  },
  required: ['tickers', 'themes'],
}

const JOURNALISM_SCHEMA = {
  type: 'object',
  properties: {
    theme: { type: 'string' },
    findings: { type: 'array', items: { type: 'object', properties: {
      ticker: { type: 'string' }, company: { type: 'string' },
      headline: { type: 'string' }, source: { type: 'string' }, source_url: { type: 'string' },
      demand_inflection: { type: 'string', description: '2-4 sentences: what structural shift is driving demand?' },
      supply_constraint: { type: 'string', description: '1-2 sentences: why supply can\'t catch up (if applicable)' },
      catalyst: { type: 'string', description: 'Specific upcoming event/date that triggers the move' },
      timeline: { type: 'string', description: 'When does the catalyst resolve? (e.g. Q3 earnings, Dec 2026)' },
      what_would_change_mind: { type: 'string', description: 'Name the ONE thing that kills this thesis' },
      confidence: { type: 'string', enum: ['HIGH', 'MEDIUM', 'LOW'] },
      already_extended: { type: 'boolean', description: 'True if already up >100% in 6 months' },
    }, required: ['ticker', 'headline', 'source', 'demand_inflection', 'confidence'] } },
    summary: { type: 'string' },
  },
  required: ['theme', 'findings', 'summary'],
}

const BENEFICIARY_SCHEMA = {
  type: 'object',
  properties: {
    chains: { type: 'array', items: { type: 'object', properties: {
      primary: { type: 'string' }, beneficiaries: { type: 'array', items: { type: 'string' } },
      logic: { type: 'string' }, conviction: { type: 'string' },
    }, required: ['primary', 'beneficiaries', 'logic'] } },
  },
  required: ['chains'],
}

const SKEPTIC_SCHEMA = {
  type: 'object',
  properties: {
    survivors: { type: 'array', items: { type: 'object', properties: {
      ticker: { type: 'string' }, thesis: { type: 'string' },
      catalyst: { type: 'string' }, timeline: { type: 'string' },
      return_12m: { type: 'number' }, passed: { type: 'boolean' },
      kill_reason: { type: 'string' },
    }, required: ['ticker', 'passed'] } },
    killed: { type: 'array', items: { type: 'string' } },
  },
  required: ['survivors', 'killed'],
}

const QUORUM_SCHEMA = {
  type: 'object',
  properties: {
    ticker: { type: 'string' },
    verdict: { type: 'string', enum: ['BUY', 'SCALE_IN', 'WATCHLIST', 'PASS'] },
    consensus: { type: 'string' },
    dissent: { type: 'string' },
    sizing: { type: 'string' },
    invalidation: { type: 'string' },
    confidence: { type: 'string', enum: ['low', 'medium', 'high'] },
  },
  required: ['ticker', 'verdict', 'consensus', 'confidence'],
}

// ---------- Phase 1: PRE-SCREEN (quantitative scan) ----------
phase('Pre-screen')
const scanResult = await agent(
  `Run the quantitative pre-screen for trend stocks.\n\n` +
  `Execute: python3 ${SCAN_PY} --top ${TOP_N}\n\n` +
  `If the script is not found or fails, fall back to using yfinance directly:\n` +
  `- Screen the 180-name universe (see ${SKILL}/trend-stock-research/SKILL.md for the ticker list)\n` +
  `- Rank by: 6-month momentum, volume ratio vs 50d avg, relative strength\n` +
  `- Return the top ${TOP_N} with their scores and theme classification\n\n` +
  `Also run mention velocity if available: python3 ${VELOCITY_PY}\n` +
  `Group results by THEME (AI/semis, energy transition, biotech, defense, fintech, etc.).\n` +
  `Date: ${REPORT_DATE}`,
  { label: 'prescreen', phase: 'Pre-screen', schema: SCAN_SCHEMA, model: MODEL }
)

if (!scanResult || !scanResult.tickers || !scanResult.tickers.length) {
  log('FATAL: pre-screen returned no tickers; aborting.')
  return { error: 'pre-screen empty', date: REPORT_DATE }
}

const themes = THEMES ? THEMES.split(',').map(t => t.trim()) : (scanResult.themes || ['general'])

// Theme-validation gate: if user specified themes, filter tickers to matching themes only
let tickers = scanResult.tickers
if (THEMES) {
  const themeLower = themes.map(t => t.toLowerCase())
  const filtered = tickers.filter(t =>
    !t.theme || themeLower.some(th => (t.theme || '').toLowerCase().includes(th) || th.includes((t.theme || '').toLowerCase()))
  )
  if (filtered.length >= 3) {
    tickers = filtered
    log(`Theme filter: kept ${tickers.length}/${scanResult.tickers.length} tickers matching themes: ${themes.join(', ')}`)
  } else {
    log(`Theme filter: only ${filtered.length} matched (keeping all ${tickers.length} to avoid empty pipeline)`)
  }
}
log(`Pre-screen: ${tickers.length} tickers across ${themes.length} themes: ${themes.join(', ')}`)

// ---------- Phase 2: JOURNALISM — EDGAR×phrase + WebSearch×angle fan-out ----------
// v2 lesson: prior version fanned N agents onto ONE shared browser → serialized → timeouts.
// Fix: every agent hits an INDEPENDENT tap (EDGAR HTTP or WebSearch). True parallel breadth.
phase('Journalism')

// EDGAR demand-signal phrases (supply/capacity language that appears in 8-K/10-K/10-Q)
const DEMAND_PHRASES = [
  'capacity constrained', 'record backlog', 'sole supplier',
  'lead times extended', 'supply agreement', 'qualified second source',
]

// WebSearch angles: snippets carry enough signal (ticker + inflection) without full-text browser
const SEARCH_ANGLES = [
  'demand inflection catalyst earnings',
  'supply constraint pricing power',
  'non-obvious beneficiary picks-and-shovels',
  'insider buying institutional accumulation',
  'analyst upgrade emerging growth secular',
]

// EDGAR fan-out: (theme × phrase) → ~30 independent HTTP agents, no browser
const edgarTasks = themes.flatMap(theme => {
  const themeTickers = tickers.filter(t => t.theme === theme || !t.theme).map(t => t.symbol)
  const startDt = REPORT_DATE.slice(0, 7) + '-01'
  return DEMAND_PHRASES.map(phrase => () => agent(
    `Search SEC EDGAR full-text search for demand-signal language in recent filings.\n\n` +
    `EDGAR full-text API (plain HTTP — no browser needed, call via WebFetch):\n` +
    `https://efts.sec.gov/LATEST/search-index?q="${phrase}"&forms=8-K,10-K,10-Q&dateRange=custom&startdt=${startDt}&enddt=${REPORT_DATE}\n\n` +
    `Steps:\n` +
    `1. WebFetch the URL above. It returns JSON with hits[].file_date, hits[]._source.period_of_report,\n` +
    `   hits[]._source.entity_name, hits[]._source.file_num, hits[].accession_no.\n` +
    `2. Filter hits where entity_name matches a focus ticker (case-insensitive).\n` +
    `3. For each match: set source="SEC EDGAR", source_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK="+entity_name.\n` +
    `4. Infer demand_inflection from the phrase context + entity context.\n\n` +
    `Focus tickers: ${themeTickers.join(', ')}\n` +
    `Theme: ${theme} | Phrase: "${phrase}"\n\n` +
    `Output schema fields required: ticker, company, headline (use phrase as headline), source, source_url,\n` +
    `demand_inflection, confidence (HIGH/MEDIUM/LOW based on how directly the ticker is named).\n` +
    `Set already_extended: false (you have no price data).\n` +
    `Return theme: "${theme}".\n` +
    `Return empty findings array if no focus ticker appears in hits. Do NOT fabricate.\n` +
    `Date: ${REPORT_DATE}`,
    { label: `edgar-${theme.slice(0,8)}-${phrase.slice(0,10).replace(/ /g,'_')}`, phase: 'Journalism', schema: JOURNALISM_SCHEMA, model: MODEL }
  ))
})

// WebSearch fan-out: (theme × angle) → ~25 independent search agents
const webSearchTasks = themes.flatMap(theme => {
  const themeTickers = tickers.filter(t => t.theme === theme || !t.theme).map(t => t.symbol)
  return SEARCH_ANGLES.map(angle => () => agent(
    `Search for demand-inflection signals using WebSearch (snippets carry the key data — no browser needed).\n\n` +
    `Use the WebSearch tool with these queries (try both):\n` +
    `1. "${theme} ${angle} ${REPORT_DATE.slice(0, 7)}"\n` +
    `2. "${themeTickers.slice(0, 3).join(' OR ')} ${angle}"\n\n` +
    `From SEARCH SNIPPETS:\n` +
    `- Extract: ticker, company, headline (snippet title), source (publication), source_url\n` +
    `- Infer: demand_inflection (what structural shift does this snippet signal?)\n` +
    `- Estimate: catalyst, timeline, confidence (HIGH/MEDIUM/LOW)\n` +
    `- Set already_extended: false (you have no price data)\n\n` +
    `Rules:\n` +
    `- Only report findings where the snippet directly mentions a focus ticker.\n` +
    `- Do NOT click through to articles — snippets only (avoids paywall blocks).\n` +
    `- Do NOT fabricate. Empty findings array if nothing relevant.\n` +
    `Focus tickers: ${themeTickers.join(', ')}\n` +
    `Theme: ${theme} | Angle: ${angle}\n` +
    `Return theme: "${theme}".\n` +
    `Date: ${REPORT_DATE}`,
    { label: `wsearch-${theme.slice(0,8)}-${angle.slice(0,14).replace(/ /g,'_')}`, phase: 'Journalism', schema: JOURNALISM_SCHEMA, model: MODEL }
  ))
})

// All agents hit independent taps → true parallel breadth (16-slot cap queues excess, all complete)
log(`Journalism v2: launching ${edgarTasks.length} EDGAR + ${webSearchTasks.length} WebSearch agents`)
const rawResults = await parallel([...edgarTasks, ...webSearchTasks])

// Consolidate findings by theme, deduplicate by ticker+headline
const findingsByTheme = {}
for (const result of rawResults) {
  if (!result || !result.findings) continue
  const th = result.theme || themes[0]
  if (!findingsByTheme[th]) findingsByTheme[th] = []
  for (const finding of result.findings) {
    const key = `${finding.ticker}|${finding.headline}`
    if (!findingsByTheme[th].some(f => `${f.ticker}|${f.headline}` === key)) {
      findingsByTheme[th].push(finding)
    }
  }
}

const journalism = themes.map(theme => ({
  theme,
  findings: findingsByTheme[theme] || [],
  summary: findingsByTheme[theme] && findingsByTheme[theme].length
    ? `${(findingsByTheme[theme] || []).length} findings (EDGAR + WebSearch fan-out)`
    : '[UNAVAILABLE]',
}))

const totalFindings = journalism.reduce((sum, j) => sum + (j.findings ? j.findings.length : 0), 0)
const agentsReturned = rawResults.filter(Boolean).length
log(`Journalism v2: ${totalFindings} findings from ${agentsReturned}/${edgarTasks.length + webSearchTasks.length} agents across ${themes.length} themes`)

// In daily/ingest mode, stop here and write partial results
if (MODE === 'daily') {
  const ingestPath = `/Users/engineer/workspace/backtest/research/trend-ingest.${REPORT_DATE}.md`
  await agent(
    `Write to ${ingestPath} a markdown summary of today's journalism ingest:\n` +
    `Date: ${REPORT_DATE}\nThemes: ${themes.join(', ')}\n` +
    `Findings:\n${JSON.stringify(journalism, null, 1)}\n` +
    `Write VERBATIM. Create parent dirs if needed.`,
    { label: 'write-ingest', phase: 'Journalism', model: MODEL }
  )
  log(`Daily ingest written: ${ingestPath}`)
  return { mode: 'daily', ingestPath, themes, totalFindings, tickers: tickers.length }
}

// ---------- Phase 3: BENEFICIARY MAPPING (non-obvious second-order picks) ----------
phase('Beneficiary')
const beneficiaryResult = await agent(
  `You are mapping NON-OBVIOUS BENEFICIARY CHAINS from the journalism findings.\n\n` +
  `For each strong demand-inflection signal found, ask:\n` +
  `- Who ELSE benefits that the market hasn't priced in?\n` +
  `- What's the picks-and-shovels play?\n` +
  `- What's the supply-chain chokepoint that gets pricing power?\n` +
  `- Is there a mid-cap/small-cap riding the same wave as the obvious large-cap?\n\n` +
  `Rules:\n` +
  `- The PRIMARY ticker is what journalism found; BENEFICIARIES are the non-obvious plays\n` +
  `- Each chain needs a clear LOGIC (why this benefits)\n` +
  `- Conviction: high/medium/low based on how direct the link is\n` +
  `- Ignore beneficiaries already in the top-25 scan (those are obvious)\n\n` +
  `JOURNALISM FINDINGS:\n${JSON.stringify(journalism, null, 1)}\n` +
  `SCAN TICKERS (exclude these as beneficiaries — they're already obvious):\n${tickers.map(t => t.symbol).join(', ')}`,
  { label: 'beneficiary-map', phase: 'Beneficiary', schema: BENEFICIARY_SCHEMA, model: MODEL }
)

const chains = (beneficiaryResult && beneficiaryResult.chains) || []
log(`Beneficiary: ${chains.length} chains mapped`)

// ---------- Phase 4: SKEPTIC FILTER (kill overhyped, require catalyst) ----------
phase('Skeptic')

// Combine scan tickers + beneficiary tickers for the skeptic to evaluate
const allCandidates = [
  ...tickers.map(t => t.symbol),
  ...chains.flatMap(c => c.beneficiaries || [])
].filter((v, i, a) => a.indexOf(v) === i)  // dedupe

// Pre-flag tickers journalism already marked as extended
const extendedFromJournalism = journalism.flatMap(j => (j.findings || []).filter(f => f.already_extended).map(f => f.ticker)).filter(Boolean)

const skepticResult = await agent(
  `You are the SKEPTIC FILTER. Your job is to KILL bad ideas before they waste quorum time.\n\n` +
  `For EACH candidate ticker, apply these 4 kill tests:\n` +
  `1. Has it already run +150% in the last 12 months? → KILL (you're late)\n` +
  `   PRE-FLAGGED as already extended (>100% in 6mo): ${extendedFromJournalism.join(', ') || 'none'}\n` +
  `2. Is there a CONCRETE catalyst with a specific DATE/TIMELINE? → Required to pass\n` +
  `3. Can you name the BUYER — who specifically will buy this stock in the next 3-6 months?\n` +
  `4. Does the journalism cite what_would_change_mind? If the invalidator has ALREADY happened → KILL\n\n` +
  `Use yfinance (via bash: python3 -c "import yfinance; ...") to check 12-month returns.\n` +
  `Pre-flagged tickers still need yfinance confirmation (journalism may be stale).\n` +
  `Any ticker that fails ANY question gets killed with a reason.\n\n` +
  `CANDIDATES: ${allCandidates.join(', ')}\n` +
  `JOURNALISM CONTEXT:\n${JSON.stringify(journalism, null, 1)}\n` +
  `BENEFICIARY CHAINS:\n${JSON.stringify(chains, null, 1)}\n` +
  `Date: ${REPORT_DATE}`,
  { label: 'skeptic-filter', phase: 'Skeptic', schema: SKEPTIC_SCHEMA, model: MODEL }
)

const survivors = (skepticResult && skepticResult.survivors) ? skepticResult.survivors.filter(s => s.passed) : []
const killed = (skepticResult && skepticResult.killed) || []
log(`Skeptic: ${survivors.length} survived, ${killed.length} killed`)

if (!survivors.length) {
  log('No survivors passed the skeptic filter. Writing empty report.')
  const emptyPath = `/Users/engineer/workspace/backtest/research/trend-stocks.${REPORT_DATE}.md`
  await agent(
    `Write to ${emptyPath}:\n# Trend Stock Research — ${REPORT_DATE}\n\n` +
    `## Result: NO SURVIVORS\n\nAll ${allCandidates.length} candidates killed by skeptic filter.\n` +
    `Killed: ${killed.join(', ')}\n\nThis is a valid result — "no edge found" is honest.\n` +
    `Write VERBATIM.`,
    { label: 'write-empty', phase: 'Skeptic', model: MODEL }
  )
  return { mode: MODE, date: REPORT_DATE, survivors: 0, killed: killed.length, reportPath: emptyPath }
}

// ---------- Phase 5: QUORUM (multi-lens verdict per survivor) ----------
phase('Quorum')

// Cap at 5 survivors to keep quorum cost bounded (16 agent limit shared across lenses)
const quorumCandidates = survivors.slice(0, 5)

const quorumResults = await parallel(quorumCandidates.map(s => () => {
  const ticker = s.ticker
  const thesis = s.thesis || ''
  const catalyst = s.catalyst || ''
  const timeline = s.timeline || ''

  // Enrich with journalism context for this ticker
  const journalismForTicker = journalism.flatMap(j => (j.findings || []).filter(f => f.ticker === ticker))
  const demandInflection = journalismForTicker.map(f => f.demand_inflection).filter(Boolean).join(' | ') || '[not available]'
  const whatWouldChangeMind = journalismForTicker.map(f => f.what_would_change_mind).filter(Boolean).join(' | ') || '[not specified]'
  const supplyConstraint = journalismForTicker.map(f => f.supply_constraint).filter(Boolean).join(' | ') || '[none cited]'
  const sourceEvidence = journalismForTicker.map(f => `${f.headline} (${f.source})`).filter(Boolean).join('; ') || '[no sources]'

  return agent(
    `Follow ${SKILL}/multi-lens-quorum/SKILL.md to convene a quorum on this SINGLE stock.\n\n` +
    `QUESTION: Should we buy ${ticker} now?\n` +
    `THESIS: ${thesis}\n` +
    `CATALYST: ${catalyst}\n` +
    `TIMELINE: ${timeline}\n` +
    `DEMAND INFLECTION: ${demandInflection}\n` +
    `SUPPLY CONSTRAINT: ${supplyConstraint}\n` +
    `WHAT WOULD CHANGE MY MIND (invalidator): ${whatWouldChangeMind}\n` +
    `SOURCE EVIDENCE: ${sourceEvidence}\n` +
    `PORTFOLIO: ${PORTFOLIO || 'Not specified — answer at the ticker level with general sizing.'}\n` +
    `DATE: ${REPORT_DATE}\n\n` +
    `Each lens MUST address:\n` +
    `- Does the demand-inflection thesis hold from your framework's perspective?\n` +
    `- Is the invalidator (what_would_change_mind) likely or unlikely in your view?\n` +
    `- Given the catalyst + timeline, is the timing right or premature?\n\n` +
    `Use 4-5 lenses from: analytics-warren-buffett, analytics-stanley-druckenmiller, ` +
    `analyst-systematic-trading, analyst-technical-analysis, analytics-lyn-alden.\n` +
    `Return: ticker, verdict (BUY/SCALE_IN/WATCHLIST/PASS), consensus, dissent, sizing, invalidation, confidence.`,
    { label: `quorum-${ticker}`, phase: 'Quorum', schema: QUORUM_SCHEMA, model: MODEL }
  )
}))

const verdicts = quorumResults.map((r, i) => r || { ticker: quorumCandidates[i].ticker, verdict: 'PASS', consensus: '[UNAVAILABLE]', confidence: 'low' })
const buys = verdicts.filter(v => v.verdict === 'BUY' || v.verdict === 'SCALE_IN')
log(`Quorum: ${buys.length} BUY/SCALE_IN, ${verdicts.filter(v => v.verdict === 'WATCHLIST').length} WATCHLIST, ${verdicts.filter(v => v.verdict === 'PASS').length} PASS`)

// ---------- Phase 6: REPORT + LEDGER ----------
phase('Report')

const reportPath = `/Users/engineer/workspace/backtest/research/trend-stocks.${REPORT_DATE}.md`
const verdictRows = verdicts.map(v => `| ${v.ticker} | **${v.verdict}** | ${v.confidence} | ${v.consensus || ''} |`).join('\n')
const verdictDetail = verdicts.map(v => {
  // Look up journalism context for this ticker
  const jFindings = journalism.flatMap(j => (j.findings || []).filter(f => f.ticker === v.ticker))
  const demandInflection = jFindings.map(f => f.demand_inflection).filter(Boolean).join(' | ') || '[not available]'
  const catalyst = jFindings.map(f => f.catalyst).filter(Boolean).join(' | ') || '[not specified]'
  const sourceEvidence = jFindings.map(f => `${f.headline} (${f.source})`).filter(Boolean).join('; ') || '[no sources]'

  return `### ${v.ticker} — ${v.verdict} (${v.confidence})\n` +
    `**Consensus:** ${v.consensus}\n` +
    `**Dissent:** ${v.dissent || 'none'}\n` +
    `**Sizing:** ${v.sizing || 'n/a'}\n` +
    `**Invalidation:** ${v.invalidation || 'n/a'}\n` +
    `**Demand inflection:** ${demandInflection}\n` +
    `**Catalyst:** ${catalyst}\n` +
    `**Source:** ${sourceEvidence}`
}).join('\n\n')

const reportMd = `# Trend Stock Research — ${REPORT_DATE}

> Pipeline: pre-screen (${tickers.length} tickers) → journalism (${totalFindings} findings) → beneficiary (${chains.length} chains) → skeptic (${survivors.length}/${allCandidates.length} survived) → quorum (${verdicts.length} evaluated)
> Portfolio: ${PORTFOLIO || 'not specified'}
> Generated by \`research-trend-stocks\`. Educational, not advice.

## Summary

**${buys.length} actionable** | ${verdicts.filter(v => v.verdict === 'WATCHLIST').length} watchlist | ${verdicts.filter(v => v.verdict === 'PASS').length} pass | ${killed.length} killed by skeptic

## Verdicts

| Ticker | Verdict | Confidence | Consensus |
|---|---|---|---|
${verdictRows}

## Detail

${verdictDetail}

## Themes scanned
${themes.map(t => `- ${t}`).join('\n')}

## Killed by skeptic (${killed.length})
${killed.map(k => `- ${k}`).join('\n') || '(none)'}

## Beneficiary chains
${chains.map(c => `- **${c.primary}** → ${(c.beneficiaries || []).join(', ')} (${c.logic})`).join('\n') || '(none)'}

## Pre-screen top ${TOP_N}
${tickers.slice(0, 10).map(t => `- ${t.symbol} (${t.theme || '?'}) — score ${t.score}`).join('\n')}
${tickers.length > 10 ? `\n... and ${tickers.length - 10} more` : ''}
`

await agent(
  `Use the Write tool to create EXACTLY this file:\n${reportPath}\nWrite this content VERBATIM (no edits). Create parent dirs if needed. Reply with the path.\n--- BEGIN ---\n${reportMd}\n--- END ---`,
    { label: 'write-report', phase: 'Report', model: MODEL }
)
log(`Report written: ${reportPath}`)

// Ledger: log each BUY/SCALE_IN verdict
if (buys.length) {
  const horizon = REPORT_DATE.slice(0, 4) + '-12-31'
  await parallel(buys.map(b => () =>
    agent(
      `Use Bash to run:\npython3 ${LEDGER_PY} add ` +
      `--asset ${b.ticker} ` +
      `--q ${JSON.stringify('trend-stock quorum: ' + (b.consensus || b.verdict))} ` +
      `--p 0.65 --by ${JSON.stringify(horizon)} ` +
      `--lens trend-stock-research ` +
      `--source research-trend-stocks ` +
      `--flip ${JSON.stringify(b.invalidation || 'thesis break')} ` +
      `--created ${JSON.stringify(REPORT_DATE)}\n\n` +
      `If "id exists" error, append -trend to the id. Reply with stdout.`,
      { label: `ledger-${b.ticker}`, phase: 'Report', model: MODEL }
    )
  ))
  log(`Ledger: ${buys.length} entries logged`)
}

// Write to convergence pool for signal-convergence-alert
const poolPath = '~/.openclaw/workspace/investor/pools/narrative.jsonl'
if (buys.length) {
  const poolLines = buys.map(b => JSON.stringify({
    ticker: b.ticker, source: 'trend-stock-research', date: REPORT_DATE,
    signal: b.verdict, confidence: b.confidence,
  }))
  await agent(
    `Append these lines to ${poolPath} (create if missing):\n${poolLines.join('\n')}\n\nUse bash: mkdir -p ... && echo ... >> ...`,
    { label: 'pool-write', phase: 'Report', model: MODEL }
  )
  log(`Pool: ${buys.length} entries appended to narrative.jsonl`)
}

return {
  mode: MODE,
  date: REPORT_DATE,
  reportPath,
  themes,
  prescreenCount: tickers.length,
  journalismFindings: totalFindings,
  beneficiaryChains: chains.length,
  survivorCount: survivors.length,
  killedCount: killed.length,
  verdicts,
  buys: buys.map(b => b.ticker),
}
