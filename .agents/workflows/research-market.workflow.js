export const meta = {
  name: 'research-market',
  description: 'Unified portfolio-aware research (crypto + equities). An LLM CIO discovers the available skills live and decides the screening strategy and desk — then the team runs: screen → gather → consolidate → panel → decide → report → ledger. NOTHING about the roster or tickers is hardcoded here; this script only dispatches the full skill names the CIO returns. All substance lives in .agents/skills.',
  phases: [
    { title: 'Intake', detail: 'CIO reads mandate, decides screen strategy + assembles desk (no tickers)' },
    { title: 'ThemeCycle', detail: 'assess whether the theme/sector is already extended; if so, widen to adjacent laggards' },
    { title: 'Screen', detail: 'research team autonomously finds 5-10 candidates via web search + screener logic' },
    { title: 'Gather', detail: 'parallel data seats (manager-selected), each following its own skill' },
    { title: 'Consolidate', detail: 'manager-selected desk skill merges seats into one brief' },
    { title: 'Panel', detail: 'manager-selected lenses debate + non-voting behavioral guardrail' },
    { title: 'Decide', detail: 'manager-selected chair: portfolio-aware buy/sell decision' },
    { title: 'Report', detail: 'write markdown research report to disk' },
    { title: 'Ledger', detail: 'log the dated chair call per asset to the forecast-ledger' },
  ],
}

// Explicit model — use 'sonnet' (resolves in Claude Code runtime) not 'claude-sonnet-4' (doesn't resolve).
const MODEL = 'sonnet'

const SKILL = '/Users/engineer/workspace/backtest/.agents/skills'
const LEDGER_PY = `${SKILL}/forecast-ledger/ledger.py`

// Inputs via args (no long text here). Date can't come from Date.now() (throws in this runtime).
// The query is interpreted by the LLM CIO (Phase 0) which DISCOVERS skills live — no hardcoded roster.
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
    screen_scope: { type: 'string' },    // what universe/sector/theme to screen
    screen_criteria: { type: 'string' }, // what makes a good candidate
  },
  required: ['asset_class', 'side', 'portfolio_provided', 'portfolio_summary',
    'gather_skills', 'panel_skills', 'desk_skill', 'chair_skill', 'screen_scope', 'screen_criteria'],
}

const THEME_SCHEMA = {
  type: 'object',
  properties: {
    extended: { type: 'boolean' },
    cycle_position: { type: 'string', enum: ['early', 'mid', 'late', 'extended'] },
    evidence: { type: 'string' },
    adjusted_scope: { type: 'string' },
    adjusted_criteria: { type: 'string' },
  },
  required: ['extended', 'cycle_position', 'adjusted_scope', 'adjusted_criteria'],
}

const SCREEN_SCHEMA = {
  type: 'object',
  properties: {
    candidates: { type: 'array', items: { type: 'object', properties: {
      ticker: { type: 'string' },
      name: { type: 'string' },
      thesis: { type: 'string' },
      catalyst: { type: 'string' },
      valuation_gap: { type: 'string' },
      why_not_yet_surged: { type: 'string' },
      current_price: { type: 'string' },
      consensus_pt: { type: 'string' },
      above_consensus_pt: { type: 'boolean' },
    }, required: ['ticker', 'thesis'] } },
    excluded: { type: 'array', items: { type: 'string' } },
    screen_notes: { type: 'string' },
  },
  required: ['candidates'],
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
    verdict: { type: 'string', enum: ['BUY_NOW', 'ADD', 'SCALE', 'DCA', 'BUY_ON_TOUCH', 'HOLD', 'WAIT', 'TRIM', 'AVOID'] },
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
      action: { type: 'string' },         // e.g. ACCUMULATE / PROBE / WATCHLIST / AVOID / BUY_ON_TOUCH
      entry_trigger: { type: 'string' },  // for BUY_ON_TOUCH: the specific price/condition e.g. "$31 limit bid"
      invalidation: { type: 'string' },
    }, required: ['asset'] } },
  },
  required: ['answer', 'decision', 'tranche_plan', 'agreement', 'disagreement'],
}

// ---------- Phase 0: INTAKE (CIO discovers skills live + plans the desk -- no tickers) ----------
phase('Intake')
const plan = await agent(
  `You are the CIO. A mandate arrived. Your job: decide the screening strategy and assemble the desk. You do NOT pick specific tickers -- your research team handles that.\n` +
  `FIRST discover the available skills live (list ${SKILL}/ and read each SKILL.md description -- do NOT rely on memory), THEN return the research plan naming every component by its real discovered directory name.\n` +
  `RAW QUERY: ${QUESTION}\nPORTFOLIO PASSED BY CALLER: ${RAW_PORTFOLIO || '(none -- caller gave no holdings; do NOT invent any)'}\nAs-of: ${REPORT_DATE}\n\n` +
  `Set screen_scope (what universe/sector/theme to screen, e.g. "AI supply chain semiconductors -- mid/small cap names not yet surged") and screen_criteria (what makes a good candidate, e.g. "valuation gap vs peers, upcoming catalysts, supply inflection point").\n` +
  `Do NOT populate assets[] -- leave it empty or omit it. The screening team decides which stocks to analyze.\n` +
  `Keep all existing skill-discovery instructions for gather_skills, panel_skills, desk_skill, chair_skill.`,
  { label: 'manager-intake', phase: 'Intake', schema: PLAN_SCHEMA, model: MODEL })

if (!plan) { log('FATAL: manager returned no plan; aborting.'); return { error: 'no plan from manager' } }

// Resolve plan -> run inputs (all manager-driven; safe fallbacks only for emptiness, never fabricate holdings).
const ASSET_CLASS = plan.asset_class || 'equities'
// ASSETS is let -- Screen phase will populate it.
let ASSETS = []
// Optional forced override: if caller explicitly passed assets via ARGS, use them (bypasses screener).
const FORCED_ASSETS = (Array.isArray(ARGS.assets) && ARGS.assets.length) ? ARGS.assets.map(a => String(a).toUpperCase()) : []
const portfolioProvided = !!(plan.portfolio_provided && RAW_PORTFOLIO)
const PORTFOLIO = portfolioProvided ? (plan.portfolio_summary || RAW_PORTFOLIO)
  : 'NO PORTFOLIO PROVIDED by the user. Do NOT assume, invent, or carry over any holdings. Answer at the market/asset level with general sizing/risk discipline only.'
const FOCUS = plan.focus || ''
const FRAMING = plan.chair_framing || ''
const FEEDS = (Array.isArray(plan.feeds) && plan.feeds.length) ? plan.feeds : []
// Cap gather+panel to keep total agents = ASSETS x (MAX_GATHER + MAX_PANEL) manageable.
// With 13 assets x (3+3) = 78 agents -- completes in ~10 min. Uncapped -> 100+ agents -> 30+ min stall.
const MAX_GATHER = 3
const MAX_PANEL = 3
const gatherSkills = (Array.isArray(plan.gather_skills) ? plan.gather_skills : []).filter(Boolean).slice(0, MAX_GATHER)
const panelSkills = (Array.isArray(plan.panel_skills) ? plan.panel_skills : []).filter(Boolean).slice(0, MAX_PANEL)
if (plan.gather_skills && plan.gather_skills.length > MAX_GATHER) log(`Gather capped ${plan.gather_skills.length}->${MAX_GATHER}: dropped ${plan.gather_skills.slice(MAX_GATHER).join(', ')}`)
if (plan.panel_skills && plan.panel_skills.length > MAX_PANEL) log(`Panel capped ${plan.panel_skills.length}->${MAX_PANEL}: dropped ${plan.panel_skills.slice(MAX_PANEL).join(', ')}`)
const guardrailSkill = plan.guardrail_skill || ''
const deskSkill = plan.desk_skill || ''
const chairSkill = plan.chair_skill || ''

log(`INTAKE -- class: ${ASSET_CLASS} | screen_scope: ${plan.screen_scope || '?'} | screen_criteria: ${plan.screen_criteria || '?'} | side: ${plan.side || '?'} | portfolio: ${portfolioProvided ? 'provided' : 'NONE (market-level)'} | gather: ${gatherSkills.length} | feeds: ${FEEDS.length} | panel: ${panelSkills.length} | desk: ${deskSkill || '?'} | chair: ${chairSkill || '?'}`)
if (FOCUS) log(`INTAKE focus: ${FOCUS}`)
if (plan.notes) log(`INTAKE notes: ${plan.notes}`)
if (QUESTION === '(no question provided)') log('WARNING: no question passed -- running with empty question.')
if (!gatherSkills.length) log('WARNING: manager selected no gather seats -- brief will be empty.')
if (!panelSkills.length) log('WARNING: manager selected no panel lenses -- no votes will be cast.')
if (!deskSkill || !chairSkill) log('WARNING: manager did not name a desk and/or chair skill.')

// ---------- Phase 0.5: THEME CYCLE CHECK ----------
phase('ThemeCycle')
const themeCycle = await agent(
  `Assess whether the investment theme is already extended (price has run hard, most names above fair value).\n\n` +
  `Theme/sector: "${plan.screen_scope}"\nAs-of: ${REPORT_DATE}\n\n` +
  `Steps:\n` +
  `1. Check the representative sector ETF (e.g. SOXX for semis, BOTZ for AI) — is it near multi-year highs?\n` +
  `2. Check how many sector names trade above analyst consensus price target\n` +
  `3. Check whether recent sector momentum has been driven by a small number of mega-caps vs broad participation\n\n` +
  `If extended=true: set adjusted_scope to a DIFFERENT universe that likely lagged (e.g. adjacent supply-chain tiers, smaller names, different geography). Set adjusted_criteria to describe what value/catalyst looks like in that adjacent universe — let the screener decide HOW to find good candidates.\n` +
  `If NOT extended: set adjusted_scope and adjusted_criteria identical to the input scope/criteria.\n` +
  `Be honest. State the evidence briefly.`,
  { label: 'theme-cycle', phase: 'ThemeCycle', schema: THEME_SCHEMA, model: MODEL }
)
if (themeCycle) {
  log(`ThemeCycle: ${themeCycle.cycle_position} | extended: ${themeCycle.extended} | ${themeCycle.evidence || ''}`)
  if (themeCycle.extended && themeCycle.adjusted_scope) {
    log(`ThemeCycle: scope widened → "${themeCycle.adjusted_scope}"`)
    plan.screen_scope = themeCycle.adjusted_scope
    plan.screen_criteria = themeCycle.adjusted_criteria || plan.screen_criteria
  }
}

// ---------- Phase 1: SCREEN -- research team autonomously finds candidates ----------
// Screening always runs. No discovery_mode toggle. The team decides which stocks to analyze.
// Exception: if caller forced ARGS.assets, skip screener (explicit override).
if (FORCED_ASSETS.length) {
  ASSETS = FORCED_ASSETS
  log(`Screen: BYPASSED -- caller forced assets: ${ASSETS.join(', ')}`)
} else {
  phase('Screen')
  log(`Screen: searching sector "${plan.screen_scope}" | criteria: ${plan.screen_criteria}`)
  const screened = await agent(
    `Task: Screen for investment candidates.\n\n` +
    `Sector/universe: "${plan.screen_scope}"\n` +
    `What makes a good candidate: "${plan.screen_criteria}"\n\n` +
    `How to screen:\n` +
    `1. Search for sector ETF holdings (e.g. SOXX, SMH, XSD, FTXL for AI semis) -- look at mid/small cap names\n` +
    `2. Search analyst screener reports, "undiscovered AI plays", "semiconductor value", "AI supply chain small cap"\n` +
    `3. Check recent earnings call transcripts for AI demand signals from lesser-known vendors\n` +
    `4. Apply the criteria above to filter candidates: ${plan.screen_criteria}\n\n` +
    `For each candidate, fetch and include: current price, analyst consensus price target, whether current price is above consensus PT (above_consensus_pt).\n` +
    `Return 5-10 tickers with thesis, catalyst, valuation_gap, why_not_yet_surged.\n` +
    `HARD RULES: Real NYSE/NASDAQ tickers only. No ETFs, no indexes. No already-surged mega-caps unless NEW catalyst.\n` +
    `Aim for diverse names across the supply chain (memory, EDA, packaging, test equipment, networking, power mgmt).`,
    { label: 'sector-screen', phase: 'Screen', schema: SCREEN_SCHEMA, model: MODEL }
  )
  if (screened && Array.isArray(screened.candidates) && screened.candidates.length) {
    const tickers = screened.candidates
      .map(c => String(c.ticker || '').toUpperCase().replace(/[^A-Z0-9]/g, ''))
      .filter(t => /^[A-Z][A-Z0-9]{1,5}$/.test(t))
    if (tickers.length) {
      ASSETS = tickers
      log(`Screen: ${tickers.length} candidates found: ${tickers.join(', ')}`)
      if (screened.screen_notes) log(`Screen notes: ${screened.screen_notes}`)
    } else {
      log('WARNING: screener returned no valid tickers -- aborting.')
      return { error: 'screener returned no valid tickers' }
    }
  } else {
    log('WARNING: screener returned nothing -- aborting.')
    return { error: 'screener returned nothing' }
  }
}

// ASSET_LIST computed here, AFTER screener has populated ASSETS.
const ASSET_LIST = ASSETS.join(', ')

const abovePT = (screened && Array.isArray(screened.candidates) ? screened.candidates : []).filter(c => c.above_consensus_pt)
if (abovePT.length) log(`Screen: ${abovePT.length} candidates above consensus PT (chair will judge): ${abovePT.map(c => c.ticker).join(', ')}`)

// Per-asset context builder -- each agent focuses on ONE asset, avoiding giant multi-asset context blowup.
const ctxFor = (asset) =>
  `Question: ${QUESTION}\nAsset class: ${ASSET_CLASS}\nFocus asset: ${asset}\nAll assets in this research: ${ASSET_LIST}\nDesk focus: ${FOCUS || 'none'}\nPortfolio: ${PORTFOLIO}\nNews feeds: ${FEEDS.length ? FEEDS.join(', ') : '(none)'}\nAs-of: ${REPORT_DATE}`
const seedNote = ANCHOR ? `\nSeed (verify+extend): ${ANCHOR}` : `\nNo seed -- fetch LIVE; never fabricate, mark UNAVAILABLE if gated.`

// ---------- Phase 2: GATHER -- per-asset pipeline (each asset x all gather skills in parallel) ----------
// Old: one agent covers ALL assets per skill -> massive context, stalls on large lists.
// New: pipeline(assets) so each asset gets dedicated gather agents -> O(1 asset) wall-clock.
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

// ---------- Phase 3: CONSOLIDATE -- per-asset desk brief ----------
phase('Consolidate')
const briefByAsset = await pipeline(
  gatherByAsset.filter(Boolean),
  async ({ asset, seats, complete }) => {
    const brief = await agent(
      `Follow ${SKILL}/${deskSkill}/SKILL.md. Focus on: ${asset}.\n${ctxFor(asset)}\nCompleteness: ${complete ? 'All seats returned.' : 'INCOMPLETE -- surface DATA GAPS; do not paper over.'}\nRAW DATA:\n${JSON.stringify(seats, null, 1)}`,
      { label: `${deskSkill}:${asset}`, phase: 'Consolidate', model: MODEL }
    )
    return { asset, brief: brief || '[UNAVAILABLE: desk returned nothing]' }
  }
)
log(`Consolidate: ${briefByAsset.filter(Boolean).length}/${ASSETS.length} briefs`)

// ---------- Phase 4: PANEL -- per-asset lenses (each asset x all panel skills in parallel) ----------
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

// Guardrail -- cross-asset (reads all briefs; non-voting process check only).
const allBriefs = briefByAsset.filter(Boolean).map(b => `=== ${b.asset} ===\n${b.brief}`).join('\n\n')
const guardrail = guardrailSkill ? await agent(
  `Follow ${SKILL}/${guardrailSkill}/SKILL.md as a NON-VOTING guardrail (no BUY/SELL verdict). Question: ${QUESTION}\nAssets: ${ASSET_LIST}\nAssess: FOMO-vs-anchoring trap, staged scale-in soundness, sizing survivable to -50%, one guardrail rule per asset.\n${allBriefs}`,
  { label: guardrailSkill, phase: 'Panel', model: MODEL }) : '(no guardrail skill selected)'

// Flatten all per-asset votes for report/ledger compatibility.
const verdicts = panelByAsset.filter(Boolean)
  .flatMap(({ asset, votes }) => votes.map(v => ({ ...v, asset })))
log(`Panel: ${verdicts.filter(v => v.read.indexOf('[UNAVAILABLE') === -1).length}/${verdicts.length} total votes cast`)

// ---------- Phase 5: DECIDE -- cross-asset chair ranks all assets ----------
phase('Decide')
const totalVotes = verdicts.filter(v => v.read.indexOf('[UNAVAILABLE') === -1).length
const decision = await agent(
  `Follow ${SKILL}/${chairSkill}/SKILL.md to chair the committee.\nQuestion: ${QUESTION}\nAssets: ${ASSET_LIST}\nChair framing: ${FRAMING || 'none'}\nPortfolio: ${PORTFOLIO}\n` +
  `Populate per_asset[] for EVERY asset (${ASSET_LIST}): {asset, conviction high|medium|low, prob 0..1 bull thesis by ${REPORT_DATE.slice(0,4)}-12-31, action, invalidation}. Rank by conviction -- do NOT give every asset the same prob.\n` +
  `For assets near but not yet at their entry zone: use action BUY_ON_TOUCH and set entry_trigger to the specific limit price or condition (e.g. "bid $31 limit", "buy on touch of 200d MA $28.50").\n` +
  `EXACT VOTING-SEAT COUNT = ${totalVotes}. verdict_tally buckets MUST sum to ${totalVotes}.\n` +
  `=== PER-ASSET PANEL VERDICTS ===\n${JSON.stringify(panelByAsset.filter(Boolean), null, 1)}\n=== GUARDRAIL (non-voting) ===\n${guardrail}`,
  { label: chairSkill || 'chair-decision', phase: 'Decide', schema: DECISION_SCHEMA, model: MODEL })

// ---------- RE-SCREEN LOOP ----------
// If chair issued zero BUY/ADD and dominant rejection is valuation, re-screen once with a
// cheaper/adjacent scope and run the FULL pipeline on the new names. The _rescreened flag
// prevents infinite loops (cap = 1 retry). Workflow must resolve autonomously — never hand
// "look deeper" back to the user.
const bullActions = ['BUY_NOW', 'ADD', 'SCALE', 'DCA', 'BUY_ON_TOUCH']
const hasBuySignal = decision && Array.isArray(decision.per_asset) &&
  decision.per_asset.some(a => bullActions.includes(String(a.action || '').toUpperCase()))
const valuationRejection = decision && decision.decision &&
  (decision.decision.toLowerCase().includes('margin of safety') ||
   decision.decision.toLowerCase().includes('already priced') ||
   decision.decision.toLowerCase().includes('above fair value') ||
   decision.decision.toLowerCase().includes('overvalued'))

if (!hasBuySignal && valuationRejection && !ARGS._rescreened) {
  log('RE-SCREEN: zero BUY signals + valuation rejection — re-running screener for beaten-down adjacent names')
  phase('ReScreen')
  const rescreenScope = (themeCycle && themeCycle.extended && themeCycle.adjusted_scope)
    ? themeCycle.adjusted_scope
    : `${plan.screen_scope} — focus on names that have NOT participated in the recent re-rating; look one tier down the supply chain or in adjacent sub-sectors`
  const rescreenCriteria = (themeCycle && themeCycle.extended && themeCycle.adjusted_criteria)
    ? themeCycle.adjusted_criteria
    : `${plan.screen_criteria}; prioritize names where the business quality is intact but the stock price has lagged the sector`
  const rescreened = await agent(
    `Task: Re-screen for investment candidates. The prior screen returned only expensive names — zero BUY signals, all rejected on valuation.\n\n` +
    `Sector/universe: "${rescreenScope}"\n` +
    `What makes a good candidate: "${rescreenCriteria}"\n\n` +
    `How to screen:\n` +
    `1. Actively avoid the same names from the prior screen: ${ASSET_LIST}\n` +
    `2. Look for names that have lagged the broader sector re-rating\n` +
    `3. Look one tier down the supply chain from the crowded mega-names\n` +
    `4. Search analyst reports for "undiscovered", "overlooked", "laggard" in this sector\n\n` +
    `Return 5-10 tickers with thesis, catalyst, valuation_gap, why_not_yet_surged.\n` +
    `HARD RULES: Real NYSE/NASDAQ tickers only. No ETFs. No names already in: ${ASSET_LIST}`,
    { label: 'rescreen', phase: 'ReScreen', schema: SCREEN_SCHEMA, model: MODEL }
  )
  const newTickers = rescreened && Array.isArray(rescreened.candidates)
    ? rescreened.candidates
        .map(c => String(c.ticker || '').toUpperCase().replace(/[^A-Z0-9]/g, ''))
        .filter(t => /^[A-Z][A-Z0-9]{1,5}$/.test(t))
        .filter(t => !ASSETS.includes(t))
    : []
  if (newTickers.length) {
    log(`ReScreen: ${newTickers.length} new candidates — running full pipeline: ${newTickers.join(', ')}`)
    const rsAssetList = newTickers.join(', ')
    const rsCtxFor = (asset) =>
      `Question: ${QUESTION}\nAsset class: ${ASSET_CLASS}\nFocus asset: ${asset}\nAll assets in this re-screen batch: ${rsAssetList}\nDesk focus: ${FOCUS || 'none'}\nPortfolio: ${PORTFOLIO}\nAs-of: ${REPORT_DATE}`

    // Gather
    phase('ReScreen-Gather')
    const rsGatherByAsset = await pipeline(
      newTickers,
      async (asset) => {
        const seats = await parallel(gatherSkills.map(skill => () =>
          agent(
            `Follow ${SKILL}/${skill}/SKILL.md as a DATA-ONLY gather seat (no buy/sell opinion). Focus on: ${asset} only.\n${rsCtxFor(asset)}${seedNote}`,
            { label: `rs-${skill}:${asset}`, phase: 'ReScreen-Gather', schema: DATA_SCHEMA, model: MODEL }
          )
        ))
        const filled = seats.map((r, i) => (r && r.findings) ? r
          : { seat: gatherSkills[i], status: 'UNAVAILABLE', findings: [], summary: `[UNAVAILABLE: ${gatherSkills[i]} seat failed]` })
        return { asset, seats: filled, complete: filled.every(r => r.status !== 'UNAVAILABLE') }
      }
    )

    // Consolidate
    phase('ReScreen-Consolidate')
    const rsBriefByAsset = await pipeline(
      rsGatherByAsset.filter(Boolean),
      async ({ asset, seats, complete }) => {
        const brief = await agent(
          `Follow ${SKILL}/${deskSkill}/SKILL.md. Focus on: ${asset}.\n${rsCtxFor(asset)}\nCompleteness: ${complete ? 'All seats returned.' : 'INCOMPLETE — surface DATA GAPS.'}\nRAW DATA:\n${JSON.stringify(seats, null, 1)}`,
          { label: `rs-${deskSkill}:${asset}`, phase: 'ReScreen-Consolidate', model: MODEL }
        )
        return { asset, brief: brief || '[UNAVAILABLE: desk returned nothing]' }
      }
    )

    // Panel
    phase('ReScreen-Panel')
    const rsPanelByAsset = await pipeline(
      rsBriefByAsset.filter(Boolean),
      async ({ asset, brief }) => {
        const votes = await parallel(panelSkills.map(skill => () =>
          agent(
            `Apply the lens in ${SKILL}/${skill}/SKILL.md. Focus ONLY on: ${asset}.\n${rsCtxFor(asset)}\nReturn seat, read, verdict, sizing, flip-condition, confidence.\n=== BRIEF (${asset}) ===\n${brief}`,
            { label: `rs-${skill}:${asset}`, phase: 'ReScreen-Panel', schema: PANEL_SCHEMA, model: MODEL }
          )
        ))
        const filled = votes.map((v, i) => v || { seat: panelSkills[i], read: '[UNAVAILABLE]', verdict: 'WAIT', confidence: 'low' })
        return { asset, brief, votes: filled }
      }
    )
    const rsVerdicts = rsPanelByAsset.filter(Boolean)
      .flatMap(({ asset, votes }) => votes.map(v => ({ ...v, asset })))
    log(`ReScreen-Panel: ${rsVerdicts.filter(v => v.read.indexOf('[UNAVAILABLE') === -1).length} votes cast`)

    // Decide
    phase('ReScreen-Decide')
    const rsTotalVotes = rsVerdicts.filter(v => v.read.indexOf('[UNAVAILABLE') === -1).length
    const rsDecision = await agent(
      `Follow ${SKILL}/${chairSkill}/SKILL.md to chair the committee.\nQuestion: ${QUESTION}\nAssets: ${rsAssetList}\nPortfolio: ${PORTFOLIO}\n` +
      `This is a RE-SCREEN batch — prior batch (${ASSET_LIST}) had zero BUY signals on valuation. These names were selected as adjacent laggards.\n` +
      `Populate per_asset[] for EVERY asset: {asset, conviction, prob 0..1, action, invalidation, entry_trigger}.\n` +
      `For assets near entry zone: use BUY_ON_TOUCH + entry_trigger.\n` +
      `EXACT VOTING-SEAT COUNT = ${rsTotalVotes}. verdict_tally MUST sum to ${rsTotalVotes}.\n` +
      `=== PER-ASSET PANEL VERDICTS ===\n${JSON.stringify(rsPanelByAsset.filter(Boolean), null, 1)}`,
      { label: `rs-${chairSkill}`, phase: 'ReScreen-Decide', schema: DECISION_SCHEMA, model: MODEL })

    // Merge re-screen results into main decision/report vars so the Report phase includes them
    if (rsDecision) {
      // Append re-screen assets to ASSETS list and merge verdicts for the report
      ASSETS.push(...newTickers)
      verdicts.push(...rsVerdicts)
      panelByAsset.push(...rsPanelByAsset.filter(Boolean))
      briefByAsset.push(...rsBriefByAsset.filter(Boolean))
      // Overwrite decision with re-screen decision if it has BUY signals; otherwise keep original
      const rsHasBuy = Array.isArray(rsDecision.per_asset) &&
        rsDecision.per_asset.some(a => bullActions.includes(String(a.action || '').toUpperCase()))
      if (rsHasBuy) {
        log(`ReScreen-Decide: BUY signals found in re-screen batch — using re-screen decision`)
        // Merge: combine agreement/disagreement, use re-screen answer/decision
        decision.answer = `[RE-SCREEN BATCH] ${rsDecision.answer}`
        decision.decision = `PRIOR BATCH (${ASSET_LIST}): zero buys — all extended.\n\nRE-SCREEN BATCH (${rsAssetList}): ${rsDecision.decision}`
        decision.buy_side = rsDecision.buy_side
        decision.tranche_plan = rsDecision.tranche_plan
        decision.per_asset = [...(decision.per_asset || []), ...(rsDecision.per_asset || [])]
        decision.agreement = [...(decision.agreement || []), ...(rsDecision.agreement || [])]
        decision.disagreement = [...(decision.disagreement || []), ...(rsDecision.disagreement || [])]
        decision.key_risks = [...(decision.key_risks || []), ...(rsDecision.key_risks || [])]
      } else {
        log(`ReScreen-Decide: re-screen batch also zero BUYs — both batches exhausted, reporting all`)
        decision.decision = `BATCH 1 (${ASSET_LIST}): zero buys.\nBATCH 2 re-screen (${rsAssetList}): zero buys.\n${rsDecision.decision}`
        decision.per_asset = [...(decision.per_asset || []), ...(rsDecision.per_asset || [])]
      }
    }
  } else {
    log('ReScreen: screener returned no new valid tickers — reporting original batch')
  }
}

// ---------- Phase 6: WRITE REPORT ----------
phase('Report')
const reportPath = `/Users/engineer/workspace/backtest/research/research.${ASSET_CLASS}.${REPORT_DATE}.md`
// Per-asset vote table: one row per asset x lens combination.
const seatRows = panelByAsset.filter(Boolean).flatMap(({ asset, votes }) =>
  votes.map(v => `| ${asset} | ${v.seat} | **${v.verdict}** | ${v.confidence} |`)
).join('\n')
const seatDetail = panelByAsset.filter(Boolean).map(({ asset, votes }) =>
  `### ${asset}\n` + votes.map(v =>
    `**${v.seat}** -- ${v.verdict} (${v.confidence}): ${v.read}\n- Sizing: ${v.sizing || 'n/a'} * Flips if: ${v.flip || 'n/a'}`
  ).join('\n\n')
).join('\n\n---\n\n')
const reportMd = `# Research -- ${ASSET_LIST} (${ASSET_CLASS}) -- ${REPORT_DATE}

> Question: ${QUESTION}
> Portfolio: ${PORTFOLIO}
> Desk assembled by \`research-manager\`: gather [${gatherSkills.join(', ')}] * panel [${panelSkills.join(', ')}] * desk ${deskSkill} * chair ${chairSkill}.
> Generated by \`research-market\`. Educational, not advice; re-pull before acting.
${gatherComplete ? '' : `\n> **WARNING INCOMPLETE DATA:** Some gather seats unavailable. Treat with caution.\n`}
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
*Consolidated brief (raw evidence) not persisted -- available in the workflow return value \`brief\` field.*
`
// Write + VERIFY + retry -- an LLM "Write this file" agent can silently no-op, so never trust it: confirm the
// bytes landed on disk and retry once, then surface LOUDLY rather than claim a path that doesn't exist.
let reportOk = false
for (let attempt = 1; attempt <= 2 && !reportOk; attempt++) {
  await agent(`Use the Write tool to create EXACTLY this file:\n${reportPath}\nWrite this content VERBATIM (no edits/summary). Create parent dirs. After writing, run Bash \`wc -c < ${reportPath}\` to confirm. Reply with just the byte count.\n--- BEGIN ---\n${reportMd}\n--- END ---`,
    { label: attempt === 1 ? 'write-report' : `write-report-retry${attempt}`, phase: 'Report', model: MODEL })
  const check = await agent(`Run Bash EXACTLY: \`test -f ${reportPath} && wc -c < ${reportPath} || echo MISSING\`. Reply with ONLY the byte count number, or the word MISSING.`,
    { label: `verify-report-${attempt}`, phase: 'Report', model: MODEL })
  const bytes = parseInt(String(check).replace(/[^0-9]/g, ''), 10) || 0
  reportOk = String(check).indexOf('MISSING') === -1 && bytes > 1000
  log(reportOk ? `Report written + verified (${bytes} bytes): ${reportPath}`
    : `WARNING: write-report attempt ${attempt} did NOT persist (saw: ${String(check).slice(0, 40)}). ${attempt < 2 ? 'Retrying.' : 'GIVING UP -- report NOT on disk; downstream must use the returned \`decision\`/\`brief\` fields.'}`)
}

// ---------- Phase 7: LEDGER (one row per REAL asset; pseudo-screen tokens excluded) ----------
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
// ONE-LINE summary only -- never dump the full multi-paragraph chair verdict into the CSV --q field (it bloats
// the ledger with literal newlines). Collapse whitespace and cap length.
const oneLine = (s) => String(s || '').replace(/\s+/g, ' ').trim().slice(0, 180)
const ledgerQ = oneLine(decision.decision || decision.answer || '(none)')
const ledgerFlip = oneLine(decision.invalidation) || 'n/a'
// Per-asset conviction map (chair-provided). Falls back to the panel bull-fraction when an asset is absent or
// its prob is not a sane 0..1 number -- so the ledger never logs a fabricated or out-of-range probability.
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
    `--p is the chair's per-asset conviction (fallback = per-asset panel tally) -- do not change it. If "id exists", re-run once with --id ${asset.toLowerCase()}-${REPORT_DATE}-panel. Reply with the CLI's stdout line.`,
    { label: `ledger-${asset}`, phase: 'Ledger', model: MODEL }))
)
const ledgerLog = LEDGER_ASSETS.map((a, i) => `${a}: ${ledgerLogs[i]}`).join(' | ')
log(`Ledger: ${ledgerLog}`)

return { reportPath, reportPersisted: reportOk, asset_class: ASSET_CLASS, assets: ASSETS, plan, decision, verdicts,
  panelByAsset, briefByAsset, guardrail, complete: gatherComplete,
  ledger: { impliedProb, horizon, lenses: votingLenses, logged: LEDGER_ASSETS, skipped: skippedLedger, result: ledgerLog } }
