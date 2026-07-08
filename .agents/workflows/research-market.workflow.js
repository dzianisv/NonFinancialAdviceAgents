export const meta = {
  name: 'research-market-workflow',
  description: 'Unified portfolio-aware research (crypto + equities). An LLM CIO discovers the available skills live and decides the screening strategy and desk — then the team runs: screen → gather → consolidate → panel → decide → report → ledger. NOTHING about the roster or tickers is hardcoded here; this script only dispatches the full skill names the CIO returns. All substance lives in .agents/skills. Two extra modes: strategy="trend-discovery" (CIO-selectable at Intake) runs a quant pre-screen + EDGAR/WebSearch journalism fan-out + beneficiary mapping + skeptic filter before handing survivors to the standard gather/panel/decide pipeline (supersedes the old standalone research-trend-stocks workflow). args.mode="holdings-sweep" bypasses discovery entirely and instead reviews every HELD position from positions.csv (ADD/HOLD/TRIM/EXIT).',
  // NOTE: this list must match the actual phase() call titles used at runtime (both modes), exactly --
  // a prior consolidation left it out of sync (a fake 'HoldingsSweep' title that's never called, and
  // 'CIO-Review' declared-but-unused). Shared titles (Consolidate/Panel/Report/Ledger) are used by BOTH
  // discovery and holdings-sweep mode with different content; each detail notes which mode(s) apply.
  phases: [
    { title: 'LoadState', detail: 'read cross-run state file (prior screened tickers + verdicts) [discovery mode]' },
    { title: 'Intake', detail: 'CIO reads mandate, decides screen strategy (standard | trend-discovery) + assembles desk (no tickers) [discovery mode]' },
    { title: 'ThemeCycle', detail: 'assess whether the theme/sector is already extended; if so, widen to adjacent laggards [discovery mode]' },
    { title: 'Screen', detail: 'standard: research team autonomously finds 5-10 candidates via web search + screener logic. trend-discovery: quant pre-screen -> EDGAR+WebSearch journalism fan-out -> beneficiary mapping -> skeptic filter [discovery mode; also re-run per CIO-Review iteration]' },
    { title: 'NewsFetch', detail: 'pre-fetch WSJ + FT + Bloomberg headlines into local article cache; gather agents query BM25 instead of hitting live URLs [discovery mode]' },
    { title: 'Gather', detail: 'parallel data seats (manager-selected), each following its own skill [discovery mode]' },
    { title: 'Consolidate', detail: 'manager-selected desk skill merges seats into one brief [discovery mode]. holdings-sweep: merges per-position panel verdicts + trend-screen rows into one report (pure JS, no extra LLM call)' },
    { title: 'Panel', detail: 'manager-selected lenses debate + non-voting behavioral guardrail [discovery mode]. holdings-sweep: one 6-seat BSC panel agent per single-name/hold-only-tagged holding' },
    { title: 'Decide', detail: 'manager-selected chair: portfolio-aware buy/sell decision [discovery mode]' },
    { title: 'CIO-Review', detail: 'CIO decides STOP (have a BUY / exhausted) or CONTINUE (screen a fresh slice) [discovery mode, iterative re-screen loop]' },
    { title: 'SaveState', detail: 'persist screened tickers + per-asset verdicts for the next run [discovery mode]' },
    { title: 'Report', detail: 'write markdown research report to disk [both modes]' },
    { title: 'Ledger', detail: 'log the dated chair call (discovery) or panel verdict (holdings-sweep) per asset to the forecast-ledger [both modes]' },
    { title: 'LoadPositions', detail: 'read positions.csv and parse Position/Quantity/Type/Unrealized_PnL rows [holdings-sweep mode]' },
    { title: 'Classify', detail: 'classify each Stock-type ticker as single-name vs ETF/fund [holdings-sweep mode]' },
    { title: 'TrendScreen', detail: 'lightweight batched trend-only screen for ETF/commodity-trust holdings [holdings-sweep mode]' },
  ],
}

// Explicit model — use 'sonnet' (resolves in Claude Code runtime) not 'claude-sonnet-4' (doesn't resolve).
const MODEL = 'sonnet'

const SKILL = '/Users/engineer/workspace/backtest/.agents/skills'
const LEDGER_PY = `${SKILL}/forecast-ledger/ledger.py`
// trend-discovery strategy (folded in from the retired research-trend-stocks workflow) — script paths
// corrected here: the original workflow pointed at a non-existent 'trend-stock-research' skill dir; the
// real skill is 'stocks-trend-screener' and mention_velocity.py lives at its root, not under scripts/.
const TREND_SCAN_PY = `${SKILL}/stocks-trend-screener/scripts/emerging_scan.py`
const TREND_VELOCITY_PY = `${SKILL}/stocks-trend-screener/mention_velocity.py`
// holdings-sweep mode — full-book review of HELD positions (vs discovery of new names)
const POSITIONS_CSV = '/Users/engineer/workspace/backtest/.cache/stocks-daily/positions.csv'

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
const MODE = ARGS.mode || 'discovery'        // 'discovery' (default, this file's original behavior) | 'holdings-sweep'
// Explicit caller override for screen strategy (docs: AGENTS.md/README/SKILLS-MAP tell callers to pass
// args.strategy:"trend-discovery"). Validated against the same enum as PLAN_SCHEMA.strategy; '' = caller
// gave none, so the CIO decides at Intake as before. When set, it is a DETERMINISTIC override applied
// after the Intake plan comes back -- the CIO may not veto an explicit caller arg.
const STRATEGY_ARG = (ARGS.strategy === 'trend-discovery' || ARGS.strategy === 'standard') ? ARGS.strategy : ''
// Caller-supplied hold-only mandate (holdings-sweep mode only). This workflow is a NEUTRAL analyst --
// it does not hardcode any ticker as un-sellable. A caller who wants a hold-only clamp on specific
// positions passes them here (array or comma-separated string, same normalize-both-shapes pattern as
// ARGS above). The OTHER accepted source is positions.csv itself: rows the USER tagged with a
// hold-only Type (e.g. 'crypto-beta') in that caller-maintained data file -- see runHoldingsSweep.
const HOLD_ONLY_ARG = (Array.isArray(ARGS.hold_only) ? ARGS.hold_only
  : (typeof ARGS.hold_only === 'string' && ARGS.hold_only.trim() ? ARGS.hold_only.split(',') : []))
  .map(t => String(t).trim().toUpperCase()).filter(Boolean)
const HOLD_ONLY_ARG_SET = new Set(HOLD_ONLY_ARG)

const PLAN_SCHEMA = {
  type: 'object',
  properties: {
    asset_class: { type: 'string' },
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
    strategy: { type: 'string', enum: ['standard', 'trend-discovery'] }, // screening strategy for the Screen phase
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
      selection_reason: { type: 'string' }, // why this ticker was selected by the screener (thesis/catalyst/valuation gap)
      rejection_reason: { type: 'string' }, // for AVOID/WAIT: exactly what failed the margin-of-safety test
    }, required: ['asset'] } },
  },
  required: ['answer', 'decision', 'tranche_plan', 'agreement', 'disagreement'],
}

// Iterative-search review verdict. Code only reads verdict/next_scope/next_criteria (+rationale for logs);
// the CIO may return extra fields -- ignore them.
const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['STOP', 'CONTINUE'] },
    rationale: { type: 'string' },
    next_scope: { type: 'string' },
    next_criteria: { type: 'string' },
  },
  required: ['verdict'],
}

// ============================================================================
// trend-discovery strategy — superseded-by research-market-workflow trend-discovery strategy.
// Folded in from the retired standalone research-trend-stocks.workflow.js (deleted). Ported faithfully:
// quant pre-screen -> EDGAR-x-phrase + WebSearch-x-angle parallel journalism fan-out -> non-obvious
// beneficiary mapping -> skeptic filter. Survivors are handed back as SCREEN_SCHEMA candidates so every
// downstream phase (Gather/Consolidate/Panel/Decide/Report/Ledger, the CIO-Review re-screen loop) runs
// completely unchanged for both strategies. Only the Screen phase branches on STRATEGY.
// ============================================================================

const TREND_SCAN_SCHEMA = {
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

const TREND_JOURNALISM_SCHEMA = {
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

const TREND_BENEFICIARY_SCHEMA = {
  type: 'object',
  properties: {
    chains: { type: 'array', items: { type: 'object', properties: {
      primary: { type: 'string' }, beneficiaries: { type: 'array', items: { type: 'string' } },
      logic: { type: 'string' }, conviction: { type: 'string' },
    }, required: ['primary', 'beneficiaries', 'logic'] } },
  },
  required: ['chains'],
}

const TREND_SKEPTIC_SCHEMA = {
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

// EDGAR demand-signal phrases (supply/capacity language that appears in 8-K/10-K/10-Q)
const TREND_DEMAND_PHRASES = [
  'capacity constrained', 'record backlog', 'sole supplier',
  'lead times extended', 'supply agreement', 'qualified second source',
]

// WebSearch angles: snippets carry enough signal (ticker + inflection) without full-text browser
const TREND_SEARCH_ANGLES = [
  'demand inflection catalyst earnings',
  'supply constraint pricing power',
  'non-obvious beneficiary picks-and-shovels',
  'insider buying institutional accumulation',
  'analyst upgrade emerging growth secular',
]

// ============================================================================
// holdings-sweep mode — full-book review of HELD positions (vs discovery of new names).
// Dispatch check lives further below (after these schemas are initialized) and short-circuits the
// entire discovery pipeline (LoadState/Intake/Screen/etc. never run for this mode).
// ============================================================================

const HOLDINGS_CLASSIFY_SCHEMA = {
  type: 'object',
  properties: {
    classifications: { type: 'array', items: { type: 'object', properties: {
      ticker: { type: 'string' },
      bucket: { type: 'string', enum: ['single-name', 'etf-fund'] },
      reason: { type: 'string' },
    }, required: ['ticker', 'bucket'] } },
  },
  required: ['classifications'],
}

const HOLDING_PANEL_SCHEMA = {
  type: 'object',
  properties: {
    ticker: { type: 'string' },
    final_verdict: { type: 'string', enum: ['ADD', 'HOLD', 'TRIM', 'EXIT'] },
    conviction: { type: 'number' },
    data_coverage: { type: 'string' },
    gate_triggered: { type: 'boolean' },
    dissent_logged: { type: 'string' },
    cio_memo: { type: 'string' },
    funding_pool_test: { type: 'string' }, // for TRIM/EXIT: states the 1-2Y growth + dividend check result
  },
  required: ['ticker', 'final_verdict', 'conviction', 'cio_memo'],
}

const HOLDINGS_TREND_SCHEMA = {
  type: 'object',
  properties: {
    rows: { type: 'array', items: { type: 'object', properties: {
      ticker: { type: 'string' },
      verdict: { type: 'string', enum: ['HOLD', 'TRIM'] },
      note: { type: 'string' },
    }, required: ['ticker', 'verdict'] } },
  },
  required: ['rows'],
}

// ---------- MODE DISPATCH: holdings-sweep bypasses the discovery pipeline entirely ----------
// Placed after every const/schema it (transitively) depends on has been initialized -- top-level `const`
// is in the temporal dead zone until its declaration line executes, and runHoldingsSweep (hoisted function
// declaration, defined near the end of this file) is CALLED here, not merely referenced.
if (MODE === 'holdings-sweep') {
  return await runHoldingsSweep()
}

// ---------- Phase -0.5: LOAD STATE (cross-run memory so the CIO avoids re-screening prior names) ----------
phase('LoadState')
const priorState = await agent(
  `Run Bash EXACTLY: \`cat /Users/engineer/workspace/backtest/research/.state/research-market.json 2>/dev/null || echo EMPTY\`. Reply with ONLY the file contents (raw JSON) or the word EMPTY.`,
  { label: 'load-state', phase: 'LoadState', model: MODEL })

// ---------- Phase 0: INTAKE (CIO discovers skills live + plans the desk -- no tickers) ----------
phase('Intake')
const plan = await agent(
  `You are the CIO. A mandate arrived. Your job: decide the screening strategy and assemble the desk. You do NOT pick specific tickers -- your research team handles that.\n` +
  `FIRST discover the available skills live (list ${SKILL}/ and read each SKILL.md description -- do NOT rely on memory), THEN return the research plan naming every component by its real discovered directory name.\n` +
  `RAW QUERY: ${QUESTION}\nPORTFOLIO PASSED BY CALLER: ${RAW_PORTFOLIO || '(none -- caller gave no holdings; do NOT invent any)'}\nAs-of: ${REPORT_DATE}\n\n` +
  `Set screen_scope (what universe/sector/theme to screen, e.g. "AI supply chain semiconductors -- mid/small cap names not yet surged") and screen_criteria (what makes a good candidate, e.g. "valuation gap vs peers, upcoming catalysts, supply inflection point").\n` +
  `Choose a screening strategy: set strategy="standard" (default -- web-search + screener-logic candidate hunt) OR strategy="trend-discovery" when the mandate is a BROAD momentum/trend hunt rather than a specific sector query -- trend-discovery runs a quantitative pre-screen (emerging_scan.py) then an EDGAR-filing + WebSearch journalism fan-out, non-obvious-beneficiary mapping, and a skeptic filter before candidates reach the desk. It is more expensive (50+ extra agents) -- only pick it when the mandate is genuinely open-ended trend discovery, not a targeted theme.\n` +
  (STRATEGY_ARG ? `CALLER PASSED AN EXPLICIT strategy ARG: "${STRATEGY_ARG}". This will be force-applied after you return regardless of what you set here -- you may still set strategy for your own reasoning, but it will be overridden.\n` : '') +
  `Do NOT populate assets[] -- leave it empty or omit it. The screening team decides which stocks to analyze.\n` +
  `Keep all existing skill-discovery instructions for gather_skills, panel_skills, desk_skill, chair_skill.` +
  `\nPRIOR-RUN STATE (already-screened tickers + verdicts from earlier runs — avoid repeating; the dedup list is enforced separately):\n${priorState}`,
  { label: 'manager-intake', phase: 'Intake', schema: PLAN_SCHEMA, model: MODEL })

if (!plan) { log('FATAL: manager returned no plan; aborting.'); return { error: 'no plan from manager' } }

// Deterministic override -- an explicit caller arg wins over the CIO's own choice (docs promise this).
if (STRATEGY_ARG && plan.strategy !== STRATEGY_ARG) {
  log(`INTAKE strategy: caller arg "${STRATEGY_ARG}" overrides CIO's choice "${plan.strategy || '(none)'}"`)
  plan.strategy = STRATEGY_ARG
}

const STRATEGY = (plan.strategy === 'trend-discovery') ? 'trend-discovery' : 'standard'
log(`INTAKE strategy: ${STRATEGY}`)

// Resolve plan -> run inputs (all manager-driven; safe fallbacks only for emptiness, never fabricate holdings).
const ASSET_CLASS = plan.asset_class || 'equities'
// ASSETS is let -- Screen phase will populate it.
let ASSETS = []
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

// ---------- Phase 1: SCREEN -- CIO-directed screener always runs ----------
let screened = null
{
  phase('Screen')
  if (STRATEGY === 'trend-discovery') {
    log(`Screen: trend-discovery strategy -- quant pre-screen + EDGAR/WebSearch journalism fan-out + beneficiary mapping + skeptic filter`)
    screened = await runTrendDiscoveryScreen()
  } else {
  log(`Screen: searching sector "${plan.screen_scope}" | criteria: ${plan.screen_criteria}`)
  screened = await agent(
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
  }
  if (screened && Array.isArray(screened.candidates) && screened.candidates.length) {
    const tickers = screened.candidates
      .map(c => String(c.ticker || '').toUpperCase().replace(/[^A-Z0-9]/g, ''))
      .filter(t => /^[A-Z][A-Z0-9]{1,5}$/.test(t))
    if (tickers.length) {
      ASSETS = tickers
      log(`Screen: ${tickers.length} candidates found: ${tickers.join(', ')}`)
      if (screened.screen_notes) log(`Screen notes: ${screened.screen_notes}`)
    } else {
      if (STRATEGY === 'trend-discovery' && screened) return await writeNoSurvivorsReport(screened)
      log('WARNING: screener returned no valid tickers -- aborting.')
      return { error: 'screener returned no valid tickers' }
    }
  } else {
    // trend-discovery: an empty candidate set after the skeptic filter (or an empty pre-screen) is a
    // legitimate, reportable outcome -- not a screener failure. The original standalone trend workflow
    // wrote an honest dated "NO SURVIVORS" report here and returned cleanly; the consolidation collapsed
    // this into a generic {error}. Restore that behavior for trend-discovery only -- standard screening
    // returning nothing is still a real failure.
    if (STRATEGY === 'trend-discovery' && screened) return await writeNoSurvivorsReport(screened)
    log('WARNING: screener returned nothing -- aborting.')
    return { error: 'screener returned nothing' }
  }
}

const abovePT = (screened && Array.isArray(screened.candidates) ? screened.candidates : []).filter(c => c.above_consensus_pt)
if (abovePT.length) log(`Screen: ${abovePT.length} candidates above consensus PT (chair will judge): ${abovePT.map(c => c.ticker).join(', ')}`)

const seedNote = ANCHOR ? `\nSeed (verify+extend): ${ANCHOR}` : `\nNo seed -- fetch LIVE; never fabricate, mark UNAVAILABLE if gated.`
const bullActions = ['BUY_NOW', 'ADD', 'SCALE', 'DCA', 'BUY_ON_TOUCH']

// ---------- NewsFetch: pre-populate article cache so gather agents query BM25 ----------
// Runs once after screen; all gather agents then call fetch_article.py --search instead of
// hitting live URLs. Cache stored at ~/.agents/cache/articles.db.
const FETCH_SCRIPT = `${SKILL}/../scripts/feeds/fetch_article.py`
const READ_SCRIPT = `${SKILL}/../scripts/feeds/read_article.ts`
const tickerList = ASSETS.join(' OR ')
if (FEEDS.length) {
  phase('NewsFetch')
  const feedTopics = [
    tickerList,
    plan.screen_scope || '',
  ].filter(Boolean).join(' ')
  await parallel(FEEDS.map(feedName => () =>
    agent(
      `Pre-fetch news headlines into the article cache for the gather phase.\n` +
      `Feed: ${feedName} (follow ${SKILL}/${feedName}/SKILL.md)\n` +
      `Topics to search: "${feedTopics}"\n` +
      `Steps:\n` +
      `1. Fetch headlines from the feed using the Google News RSS method documented in the skill (NOT direct site RSS).\n` +
      `2. For each headline relevant to [${ASSETS.join(', ')}] or the research theme, fetch the full article body:\n` +
      `   bun ${READ_SCRIPT} "<article-url>"\n` +
      `   This handles FT (via archive.ph/Chrome), WSJ (via Wayback), and BI automatically — no extension needed.\n` +
      `   The script caches results in SQLite automatically.\n` +
      `3. If read_article.ts returns [UNAVAILABLE - archive.ph CAPTCHA], skip that article and continue.\n` +
      `4. Return count of articles ingested and any errors.\n` +
      `HARD RULE: never fabricate body text. Teaser from RSS = OK. Invented prose = defect.`,
      { label: `newsfetch:${feedName}`, phase: 'NewsFetch', model: MODEL }
    )
  ))
  log(`NewsFetch: articles cached for gather agents (query via: python3 ${FETCH_SCRIPT} --search "<ticker>")`)
}

// ---------- Reusable per-batch pipeline: Gather -> Consolidate -> Panel (+guardrail) -> Decide ----------
// ONE function so the first batch and every CIO-driven re-screen iteration run identical logic.
// `tag`: '' for the first batch (phases/labels read "Gather"); 'rs1' etc for later iterations
// (phases/labels read "Gather (rs1)", "rs1-<skill>:<asset>") so logs stay distinct.
async function runPipeline(assets, tag) {
  const batchList = assets.join(', ')
  const lbl = (s) => tag ? `${tag}-${s}` : s          // namespaced agent label
  const ph = (s) => tag ? `${s} (${tag})` : s          // namespaced phase name
  // Per-asset context builder -- each agent focuses on ONE asset, avoiding giant multi-asset context blowup.
  // trend-discovery only: thread the screen's structured journalism findings (demand_inflection,
  // supply_constraint, catalyst, timeline, beneficiary chains) into Gather/Panel context. Without this the
  // 50+ journalism agents from the trend-discovery screen only ever filter tickers via the skeptic step --
  // their findings never reach the desk that actually forms a verdict.
  const journalismFor = (asset) => {
    if (STRATEGY !== 'trend-discovery' || !screened || !Array.isArray(screened.candidates)) return ''
    const c = screened.candidates.find(x => String(x.ticker || '').toUpperCase() === String(asset).toUpperCase())
    if (!c) return ''
    const parts = []
    if (Array.isArray(c.journalism) && c.journalism.length) parts.push(`Journalism findings (trend-discovery screen): ${JSON.stringify(c.journalism)}`)
    if (Array.isArray(c.beneficiary_chains) && c.beneficiary_chains.length) parts.push(`Beneficiary chains: ${JSON.stringify(c.beneficiary_chains)}`)
    return parts.length ? `\n${parts.join('\n')}` : ''
  }
  const ctxFor = (asset) =>
    `Question: ${QUESTION}\nAsset class: ${ASSET_CLASS}\nFocus asset: ${asset}\nAll assets in this research: ${batchList}\nDesk focus: ${FOCUS || 'none'}\nPortfolio: ${PORTFOLIO}\nNews feeds: ${FEEDS.length ? FEEDS.join(', ') : '(none)'}\nArticle cache: python3 ${FETCH_SCRIPT} --search "${asset}" --limit 5  (pre-fetched FT/WSJ/Bloomberg; query before hitting live URLs)\nFull article body: bun ${READ_SCRIPT} "<url>"  (FT→archive.ph/Chrome, WSJ→Wayback, no extension needed)\nAs-of: ${REPORT_DATE}${journalismFor(asset)}`

  // ---------- GATHER -- per-asset pipeline (each asset x all gather skills in parallel) ----------
  // Old: one agent covers ALL assets per skill -> massive context, stalls on large lists.
  // New: pipeline(assets) so each asset gets dedicated gather agents -> O(1 asset) wall-clock.
  phase(ph('Gather'))
  const gatherByAsset = await pipeline(
    assets,
    async (asset) => {
      const seats = await parallel(gatherSkills.map(skill => () =>
        agent(
          `Follow ${SKILL}/${skill}/SKILL.md as a DATA-ONLY gather seat (no buy/sell opinion). Focus on: ${asset} only.\n${ctxFor(asset)}${seedNote}`,
          { label: `${lbl(skill)}:${asset}`, phase: ph('Gather'), schema: DATA_SCHEMA, model: MODEL }
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
  log(`Gather${tag ? ` (${tag})` : ''}: ${gatherByAsset.filter(Boolean).length}/${assets.length} assets complete`)

  // ---------- CONSOLIDATE -- per-asset desk brief ----------
  phase(ph('Consolidate'))
  const briefByAsset = await pipeline(
    gatherByAsset.filter(Boolean),
    async ({ asset, seats, complete }) => {
      const brief = await agent(
        `Follow ${SKILL}/${deskSkill}/SKILL.md. Focus on: ${asset}.\n${ctxFor(asset)}\nCompleteness: ${complete ? 'All seats returned.' : 'INCOMPLETE -- surface DATA GAPS; do not paper over.'}\nRAW DATA:\n${JSON.stringify(seats, null, 1)}`,
        { label: `${lbl(deskSkill)}:${asset}`, phase: ph('Consolidate'), model: MODEL }
      )
      return { asset, brief: brief || '[UNAVAILABLE: desk returned nothing]' }
    }
  )
  log(`Consolidate${tag ? ` (${tag})` : ''}: ${briefByAsset.filter(Boolean).length}/${assets.length} briefs`)

  // ---------- PANEL -- per-asset lenses (each asset x all panel skills in parallel) ----------
  phase(ph('Panel'))
  const panelByAsset = await pipeline(
    briefByAsset.filter(Boolean),
    async ({ asset, brief }) => {
      const votes = await parallel(panelSkills.map(skill => () =>
        agent(
          `Apply the lens in ${SKILL}/${skill}/SKILL.md. Focus ONLY on: ${asset}.\n${ctxFor(asset)}\nReturn seat (=${skill}), read, verdict, sizing, flip-condition, confidence.\n=== BRIEF (${asset}) ===\n${brief}`,
          { label: `${lbl(skill)}:${asset}`, phase: ph('Panel'), schema: PANEL_SCHEMA, model: MODEL }
        )
      ))
      const filled = votes.map((v, i) => v || { seat: panelSkills[i], read: '[UNAVAILABLE: seat failed]', verdict: 'WAIT', confidence: 'low' })
      return { asset, brief, votes: filled }
    }
  )
  log(`Panel${tag ? ` (${tag})` : ''}: ${panelByAsset.filter(Boolean).length}/${assets.length} assets voted`)

  // Guardrail -- cross-asset (reads all briefs; non-voting process check only).
  const allBriefs = briefByAsset.filter(Boolean).map(b => `=== ${b.asset} ===\n${b.brief}`).join('\n\n')
  const guardrail = guardrailSkill ? await agent(
    `Follow ${SKILL}/${guardrailSkill}/SKILL.md as a NON-VOTING guardrail (no BUY/SELL verdict). Question: ${QUESTION}\nAssets: ${batchList}\nAssess: FOMO-vs-anchoring trap, staged scale-in soundness, sizing survivable to -50%, one guardrail rule per asset.\n${allBriefs}`,
    { label: lbl(guardrailSkill), phase: ph('Panel'), model: MODEL }) : '(no guardrail skill selected)'

  // Flatten all per-asset votes for report/ledger compatibility.
  const verdicts = panelByAsset.filter(Boolean)
    .flatMap(({ asset, votes }) => votes.map(v => ({ ...v, asset })))
  log(`Panel${tag ? ` (${tag})` : ''}: ${verdicts.filter(v => v.read.indexOf('[UNAVAILABLE') === -1).length}/${verdicts.length} total votes cast`)

  // ---------- DECIDE -- cross-asset chair ranks all assets in this batch ----------
  phase(ph('Decide'))
  const totalVotes = verdicts.filter(v => v.read.indexOf('[UNAVAILABLE') === -1).length
  const decision = await agent(
    `Follow ${SKILL}/${chairSkill}/SKILL.md to chair the committee.\nQuestion: ${QUESTION}\nAssets: ${batchList}\nChair framing: ${FRAMING || 'none'}\nPortfolio: ${PORTFOLIO}\n` +
    `Populate per_asset[] for EVERY asset (${batchList}): {asset, conviction high|medium|low, prob 0..1 bull thesis by ${REPORT_DATE.slice(0,4)}-12-31, action, entry_trigger, invalidation, selection_reason (1-2 sentences: why was this ticker selected — what thesis/catalyst/valuation gap made it a candidate), rejection_reason (1-2 sentences for AVOID/WAIT: what SPECIFICALLY failed the margin-of-safety test at the current price — e.g. already re-rated +X%, insider selling, no margin of safety; leave blank for BUY/BUY_ON_TOUCH actions)}. Rank by conviction -- do NOT give every asset the same prob.\n` +
    `For assets near but not yet at their entry zone: use action BUY_ON_TOUCH and set entry_trigger to the specific limit price or condition (e.g. "bid $31 limit", "buy on touch of 200d MA $28.50").\n` +
    `EXACT VOTING-SEAT COUNT = ${totalVotes}. verdict_tally buckets MUST sum to ${totalVotes}.\n` +
    `=== PER-ASSET PANEL VERDICTS ===\n${JSON.stringify(panelByAsset.filter(Boolean), null, 1)}\n=== GUARDRAIL (non-voting) ===\n${guardrail}`,
    { label: tag ? `${tag}-${chairSkill || 'chair-decision'}` : (chairSkill || 'chair-decision'), phase: ph('Decide'), schema: DECISION_SCHEMA, model: MODEL })

  return { assets, gatherByAsset, briefByAsset, panelByAsset, verdicts, guardrail, decision, gatherComplete }
}

// ---------- CIO-DRIVEN ITERATIVE SEARCH LOOP (max 3 iterations, code-enforced) ----------
// First batch runs the pipeline; then the CIO repeatedly decides STOP (have a BUY / exhausted) or
// CONTINUE (screen a DIFFERENT slice and run the pipeline again). Accumulators below carry the same
// shapes Report/Ledger read. `allScreened` is dedup memory within this run.
let allScreened = [...ASSETS]
let agg = await runPipeline(ASSETS, '')
let gatherByAsset = agg.gatherByAsset
let briefByAsset = agg.briefByAsset
let panelByAsset = agg.panelByAsset
let verdicts = agg.verdicts
let guardrail = agg.guardrail
let decision = agg.decision
let gatherComplete = agg.gatherComplete

// Persist state after the first batch (cross-run memory).
phase('SaveState'); await saveState()

for (let iter = 1; iter <= 3; iter++) {
  // Belt-and-suspenders: if we already hold a BUY signal, stop before even asking the CIO.
  const hasBuy = decision && Array.isArray(decision.per_asset) &&
    decision.per_asset.some(a => bullActions.includes(String(a.action || '').toUpperCase()))
  if (hasBuy) { log(`CIO-Review iter ${iter}: STOP — already have a BUY signal`); break }

  phase('CIO-Review')
  const review = await agent(
    `You are the CIO running an iterative search for a conviction BUY.\n` +
    `GOAL: find at least ONE high/medium-conviction BUY (action ACCUMULATE / BUY_NOW / ADD / SCALE / DCA / BUY_ON_TOUCH). ` +
    `SUCCESS: stop as soon as you have one, OR when the universe is genuinely exhausted and further screening is unlikely to help.\n` +
    `Original mandate: ${QUESTION}\nScreen scope so far: ${plan.screen_scope}\nScreen criteria so far: ${plan.screen_criteria}\n` +
    `Tickers screened this run already (do NOT re-screen these): ${allScreened.join(', ')}\n` +
    `Iterations remaining after this one: ${3 - iter}\n` +
    `PRIOR-RUN STATE: ${priorState}\n` +
    `=== LATEST CHAIR DECISION (what was tried + why rejected) ===\n${JSON.stringify(decision && decision.per_asset || [], null, 1)}\nDecision narrative: ${decision && decision.decision || ''}\n\n` +
    `Decide: should we STOP (we have a BUY, or the search is exhausted) or CONTINUE (screen a fresh, different slice)? ` +
    `If CONTINUE, give next_scope (a DIFFERENT universe/sector/tier than what's been tried — be specific) and next_criteria (what makes a good candidate there). ` +
    `Reason freely; you own the strategy. Return at minimum: verdict (STOP|CONTINUE), and if CONTINUE also next_scope and next_criteria.`,
    { label: `cio-review-${iter}`, phase: 'CIO-Review', schema: REVIEW_SCHEMA, model: MODEL })

  const verdict = String(review && review.verdict || 'STOP').toUpperCase()
  if (verdict !== 'CONTINUE') { log(`CIO-Review iter ${iter}: STOP — ${review && review.rationale || 'no continue'}`); break }

  const nextScope = review.next_scope || plan.screen_scope
  const nextCriteria = review.next_criteria || plan.screen_criteria
  phase(`Screen (rs${iter})`)
  log(`CIO-Review iter ${iter}: CONTINUE — next_scope "${nextScope}"`)
  const screened2 = await agent(
    `Task: Re-screen for investment candidates. The CIO directed a fresh slice — prior batches did not yield a conviction BUY.\n\n` +
    `Sector/universe: "${nextScope}"\n` +
    `What makes a good candidate: "${nextCriteria}"\n\n` +
    `How to screen:\n` +
    `1. EXCLUDE these already-screened tickers: ${allScreened.join(', ')}\n` +
    `2. Look for names that fit the new scope and have NOT already surged\n` +
    `3. Look one tier down the supply chain or in adjacent sub-sectors from the crowded names\n` +
    `4. Search analyst reports for "undiscovered", "overlooked", "laggard" in this universe\n\n` +
    `Return 5-10 tickers with thesis, catalyst, valuation_gap, why_not_yet_surged.\n` +
    `HARD RULES: Real NYSE/NASDAQ tickers only. No ETFs. No names already screened: ${allScreened.join(', ')}`,
    { label: `rescreen-${iter}`, phase: `Screen (rs${iter})`, schema: SCREEN_SCHEMA, model: MODEL }
  )
  const newTickers = screened2 && Array.isArray(screened2.candidates)
    ? screened2.candidates
        .map(c => String(c.ticker || '').toUpperCase().replace(/[^A-Z0-9]/g, ''))
        .filter(t => /^[A-Z][A-Z0-9]{1,5}$/.test(t))
        .filter(t => !allScreened.includes(t))
    : []
  if (!newTickers.length) { log(`CIO-Review iter ${iter}: screener returned no new names — stopping`); break }
  allScreened.push(...newTickers)
  log(`Screen (rs${iter}): ${newTickers.length} new candidates — running full pipeline: ${newTickers.join(', ')}`)

  const priorList = ASSETS.join(', ')          // names already analyzed BEFORE this iteration's batch
  const batchListStr = newTickers.join(', ')
  const batch = await runPipeline(newTickers, `rs${iter}`)

  // Merge this batch into the accumulators (same merge logic as the old re-screen block).
  ASSETS.push(...newTickers)
  verdicts.push(...batch.verdicts)
  panelByAsset.push(...batch.panelByAsset.filter(Boolean))
  briefByAsset.push(...batch.briefByAsset.filter(Boolean))
  gatherByAsset.push(...batch.gatherByAsset.filter(Boolean))
  gatherComplete = gatherComplete && batch.gatherComplete

  if (batch.decision) {
    const batchHasBuy = Array.isArray(batch.decision.per_asset) &&
      batch.decision.per_asset.some(a => bullActions.includes(String(a.action || '').toUpperCase()))
    if (batchHasBuy) {
      log(`Decide (rs${iter}): BUY signals found in re-screen batch — adopting its buy-side`)
      decision.answer = `[RE-SCREEN BATCH] ${batch.decision.answer}`
      decision.decision = `PRIOR BATCHES (${priorList}): zero buys — all extended.\n\nRE-SCREEN BATCH (${batchListStr}): ${batch.decision.decision}`
      decision.buy_side = batch.decision.buy_side
      decision.tranche_plan = batch.decision.tranche_plan
      decision.per_asset = [...(decision.per_asset || []), ...(batch.decision.per_asset || [])]
      decision.agreement = [...(decision.agreement || []), ...(batch.decision.agreement || [])]
      decision.disagreement = [...(decision.disagreement || []), ...(batch.decision.disagreement || [])]
      decision.key_risks = [...(decision.key_risks || []), ...(batch.decision.key_risks || [])]
    } else {
      log(`Decide (rs${iter}): re-screen batch also zero BUYs — concatenating narratives`)
      decision.decision = `${decision.decision}\n\nRE-SCREEN BATCH (${batchListStr}): ${batch.decision.decision}`
      decision.per_asset = [...(decision.per_asset || []), ...(batch.decision.per_asset || [])]
    }
  }

  phase('SaveState'); await saveState()
}

// ---------- SaveState helper (cross-run memory; called after first batch + each loop iteration) ----------
// Hoisted: `function` declarations are visible above their definition, so the calls earlier work.
async function saveState() {
  const stateObj = { date: REPORT_DATE, query: QUESTION, screened: allScreened,
    per_asset: (decision && decision.per_asset || []).map(a => ({ asset: a.asset, action: a.action, conviction: a.conviction, prob: a.prob })) }
  const json = JSON.stringify(stateObj, null, 2)
  await agent(`Use Bash to create the dir and write this file EXACTLY. Run:\nmkdir -p /Users/engineer/workspace/backtest/research/.state\ncat > /Users/engineer/workspace/backtest/research/.state/research-market.json <<'EOF_STATE'\n${json}\nEOF_STATE\nThen reply OK.`, { label: 'save-state', phase: 'SaveState', model: MODEL })
}

// ---------- Phase 6: WRITE REPORT ----------
phase('Report')
// Recompute the asset list from the FINAL ASSETS (the loop may have appended re-screen names; the
// initial ASSET_LIST const was captured before the loop and is now stale).
const FINAL_ASSET_LIST = ASSETS.join(', ')
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

// Build screener thesis lookup: ticker → {thesis, catalyst, valuation_gap, why_not_yet_surged}
const screenerMap = {}
const allCandidates = [
  ...(screened && Array.isArray(screened.candidates) ? screened.candidates : []),
]
for (const c of allCandidates) {
  const t = String(c.ticker || '').toUpperCase().replace(/[^A-Z0-9]/g, '')
  if (t) screenerMap[t] = c
}

// Per-asset reasoning block: one section per asset with why-selected + why-accepted/rejected
const perAssetDecisions = Array.isArray(decision.per_asset) ? decision.per_asset : []
const perAssetReasoning = ASSETS.map(asset => {
  const sc = screenerMap[asset] || {}
  const d = perAssetDecisions.find(e => e && String(e.asset || '').toUpperCase() === asset) || {}
  const panelEntry = (panelByAsset.find(p => p && p.asset === asset) || {})
  const votes = panelEntry.votes || []
  const voteSum = votes.map(v => `${v.seat}: ${v.verdict} (${v.confidence})`).join(', ')
  const action = String(d.action || '').toUpperCase()
  const isAvoid = ['AVOID', 'WAIT'].includes(action)

  const lines = [`### ${asset}  —  **${d.action || 'n/a'}** (conviction: ${d.conviction || 'n/a'})`]

  // Why selected
  if (sc.thesis || sc.catalyst || sc.why_not_yet_surged) {
    lines.push(`**Why selected by screener:**`)
    if (sc.thesis) lines.push(`- Thesis: ${sc.thesis}`)
    if (sc.catalyst) lines.push(`- Catalyst: ${sc.catalyst}`)
    if (sc.valuation_gap) lines.push(`- Valuation gap: ${sc.valuation_gap}`)
    if (sc.why_not_yet_surged) lines.push(`- Why not yet surged: ${sc.why_not_yet_surged}`)
  } else if (d.selection_reason) {
    lines.push(`**Why selected:** ${d.selection_reason}`)
  }

  // Panel split
  if (voteSum) lines.push(`**Panel split:** ${voteSum}`)

  // Chair verdict
  if (d.entry_trigger) lines.push(`**Entry:** ${d.entry_trigger}`)
  if (d.invalidation) lines.push(`**Invalidation:** ${d.invalidation}`)

  // Why rejected/accepted
  if (isAvoid && d.rejection_reason) {
    lines.push(`**Why rejected (${action}):** ${d.rejection_reason}`)
  } else if (!isAvoid && d.selection_reason) {
    lines.push(`**Why accepted:** ${d.selection_reason}`)
  }

  return lines.join('\n')
}).join('\n\n---\n\n')

// trend-discovery only: beneficiary chains + theme list + killed-ticker/reason list were part of the
// original standalone trend workflow's report and were dropped in the consolidation. Restore them.
const trendReportSection = (STRATEGY === 'trend-discovery' && screened) ? `
## Trend-discovery: themes scanned
${((screened.themes) || []).map(t => `- ${t}`).join('\n') || '(none)'}

## Trend-discovery: beneficiary chains
${((screened.chains) || []).map(c => `- **${c.primary}** -> ${(c.beneficiaries || []).join(', ')} (${c.conviction || 'n/a'} conviction): ${c.logic || ''}`).join('\n') || '(none mapped)'}

## Trend-discovery: killed by skeptic filter
${((screened.killedDetail) || []).map(k => `- **${k.ticker}**: ${k.kill_reason}`).join('\n') || '(none)'}
` : ''
const reportMd = `# Research -- ${FINAL_ASSET_LIST} (${ASSET_CLASS}) -- ${REPORT_DATE}

> Question: ${QUESTION}
> Portfolio: ${PORTFOLIO}
> Desk assembled by \`research-manager\`: gather [${gatherSkills.join(', ')}] * panel [${panelSkills.join(', ')}] * desk ${deskSkill} * chair ${chairSkill}.
> Generated by \`research-market-workflow\`. Educational, not advice; re-pull before acting.
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

## Per-asset reasoning
${perAssetReasoning}

## Panel votes
| Asset | Seat | Verdict | Confidence |
|---|---|---|---|
${seatRows}

## Seat detail
${seatDetail}
${trendReportSection}
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
    // Provenance: trend-originated buys must be discriminable from standard-strategy runs in ledger history.
    `--source ${STRATEGY === 'trend-discovery' ? 'research-market:trend-discovery' : 'research-market'} --flip ${JSON.stringify(flipFor(asset))} --created ${JSON.stringify(REPORT_DATE)}\n\n` +
    `--p is the chair's per-asset conviction (fallback = per-asset panel tally) -- do not change it. If "id exists", re-run once with --id ${asset.toLowerCase()}-${REPORT_DATE}-panel. Reply with the CLI's stdout line.`,
    { label: `ledger-${asset}`, phase: 'Ledger', model: MODEL }))
)
const ledgerLog = LEDGER_ASSETS.map((a, i) => `${a}: ${ledgerLogs[i]}`).join(' | ')
log(`Ledger: ${ledgerLog}`)

return { reportPath, reportPersisted: reportOk, asset_class: ASSET_CLASS, assets: ASSETS, plan, decision, verdicts,
  panelByAsset, briefByAsset, guardrail, complete: gatherComplete,
  ledger: { impliedProb, horizon, lenses: votingLenses, logged: LEDGER_ASSETS, skipped: skippedLedger, result: ledgerLog } }

// ============================================================================
// runTrendDiscoveryScreen — the trend-discovery Screen-phase strategy.
// superseded-by research-market-workflow trend-discovery strategy (this function IS that strategy;
// the standalone research-trend-stocks.workflow.js it was ported from has been deleted).
// Hoisted function declaration -- called earlier in the Screen phase, defined here for readability.
// Returns a SCREEN_SCHEMA-shaped object so every downstream phase runs unmodified.
// ============================================================================
async function runTrendDiscoveryScreen() {
  const TOP_N = ARGS.top || 25
  const THEMES_OVERRIDE = ARGS.themes || ''

  // ---- Pre-screen (quantitative scan) ----
  const scanResult = await agent(
    `Run the quantitative pre-screen for trend stocks.\n\n` +
    `Execute: python3 ${TREND_SCAN_PY} --top ${TOP_N}\n\n` +
    `If the script is not found or fails, fall back to using yfinance directly:\n` +
    `- Screen the 180-name universe (see ${SKILL}/stocks-trend-screener/SKILL.md for the ticker list)\n` +
    `- Rank by: 6-month momentum, volume ratio vs 50d avg, relative strength\n` +
    `- Return the top ${TOP_N} with their scores and theme classification\n\n` +
    `Also run mention velocity if available: python3 ${TREND_VELOCITY_PY}\n` +
    `Group results by THEME (AI/semis, energy transition, biotech, defense, fintech, etc.).\n` +
    `Date: ${REPORT_DATE}`,
    { label: 'trend-prescreen', phase: 'Screen', schema: TREND_SCAN_SCHEMA, model: MODEL }
  )

  if (!scanResult || !scanResult.tickers || !scanResult.tickers.length) {
    log('trend-discovery: pre-screen returned no tickers -- returning empty candidate set.')
    return { candidates: [], excluded: [], screen_notes: 'trend-discovery pre-screen returned empty' }
  }

  const themes = THEMES_OVERRIDE ? THEMES_OVERRIDE.split(',').map(t => t.trim()) : (scanResult.themes || ['general'])

  let tickers = scanResult.tickers
  if (THEMES_OVERRIDE) {
    const themeLower = themes.map(t => t.toLowerCase())
    const filtered = tickers.filter(t =>
      !t.theme || themeLower.some(th => (t.theme || '').toLowerCase().includes(th) || th.includes((t.theme || '').toLowerCase()))
    )
    if (filtered.length >= 3) {
      tickers = filtered
      log(`trend-discovery theme filter: kept ${tickers.length}/${scanResult.tickers.length} matching themes: ${themes.join(', ')}`)
    } else {
      log(`trend-discovery theme filter: only ${filtered.length} matched (keeping all ${tickers.length} to avoid empty pipeline)`)
    }
  }
  log(`trend-discovery pre-screen: ${tickers.length} tickers across ${themes.length} themes: ${themes.join(', ')}`)

  // ---- Journalism: EDGAR x phrase + WebSearch x angle fan-out -- independent HTTP taps, no browser ----
  const edgarTasks = themes.flatMap(theme => {
    const themeTickers = tickers.filter(t => t.theme === theme || !t.theme).map(t => t.symbol)
    const startDt = REPORT_DATE.slice(0, 7) + '-01'
    return TREND_DEMAND_PHRASES.map(phrase => () => {
      const encodedPhrase = phrase.replace(/ /g, '%20')
      return agent(
        `Search SEC EDGAR full-text search for demand-signal language in recent filings.\n\n` +
        `EDGAR full-text API (plain HTTP -- no browser needed, call via WebFetch):\n` +
        `https://efts.sec.gov/LATEST/search-index?q="${encodedPhrase}"&forms=8-K,10-K,10-Q&dateRange=custom&startdt=${startDt}&enddt=${REPORT_DATE}\n\n` +
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
        { label: `edgar-${theme.slice(0,8)}-${phrase.slice(0,10).replace(/ /g,'_')}`, phase: 'Screen', schema: TREND_JOURNALISM_SCHEMA, model: MODEL }
      ).then(r => r ? { ...r, theme } : null)  // override self-reported theme with authoritative closed-over value
    })
  })

  // WebSearch fan-out: (theme x angle)
  const webSearchTasks = themes.flatMap(theme => {
    const themeTickers = tickers.filter(t => t.theme === theme || !t.theme).map(t => t.symbol)
    return TREND_SEARCH_ANGLES.map(angle => () => agent(
      `Search for demand-inflection signals using WebSearch (snippets carry the key data -- no browser needed).\n\n` +
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
      `- Do NOT click through to articles -- snippets only (avoids paywall blocks).\n` +
      `- Do NOT fabricate. Empty findings array if nothing relevant.\n` +
      `Focus tickers: ${themeTickers.join(', ')}\n` +
      `Theme: ${theme} | Angle: ${angle}\n` +
      `Return theme: "${theme}".\n` +
      `Date: ${REPORT_DATE}`,
      { label: `wsearch-${theme.slice(0,8)}-${angle.slice(0,14).replace(/ /g,'_')}`, phase: 'Screen', schema: TREND_JOURNALISM_SCHEMA, model: MODEL }
    ).then(r => r ? { ...r, theme } : null))
  })

  // All agents hit independent taps -> true parallel breadth (16-slot cap queues excess, all complete)
  log(`trend-discovery journalism: launching ${edgarTasks.length} EDGAR + ${webSearchTasks.length} WebSearch agents`)
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
  log(`trend-discovery journalism: ${totalFindings} findings from ${agentsReturned}/${edgarTasks.length + webSearchTasks.length} agents across ${themes.length} themes`)

  // ---- Beneficiary mapping (non-obvious second-order picks) ----
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
    `- Ignore beneficiaries already in the top-${TOP_N} scan (those are obvious)\n\n` +
    `JOURNALISM FINDINGS:\n${JSON.stringify(journalism, null, 1)}\n` +
    `SCAN TICKERS (exclude these as beneficiaries -- they're already obvious):\n${tickers.map(t => t.symbol).join(', ')}`,
    { label: 'trend-beneficiary-map', phase: 'Screen', schema: TREND_BENEFICIARY_SCHEMA, model: MODEL }
  )

  const chains = (beneficiaryResult && beneficiaryResult.chains) || []
  log(`trend-discovery beneficiary: ${chains.length} chains mapped`)

  // ---- Skeptic filter (kill overhyped, require catalyst) ----
  const allCandidates = [
    ...tickers.map(t => t.symbol),
    ...chains.flatMap(c => c.beneficiaries || [])
  ].filter((v, i, a) => a.indexOf(v) === i)  // dedupe

  const extendedFromJournalism = journalism.flatMap(j => (j.findings || []).filter(f => f.already_extended).map(f => f.ticker)).filter(Boolean)

  const skepticResult = await agent(
    `You are the SKEPTIC FILTER. Your job is to KILL bad ideas before they waste desk time.\n\n` +
    `For EACH candidate ticker, apply these 4 kill tests:\n` +
    `1. Has it already run +150% in the last 12 months? -> KILL (you're late)\n` +
    `   PRE-FLAGGED as already extended (>100% in 6mo): ${extendedFromJournalism.join(', ') || 'none'}\n` +
    `2. Is there a CONCRETE catalyst with a specific DATE/TIMELINE? -> Required to pass\n` +
    `3. Can you name the BUYER -- who specifically will buy this stock in the next 3-6 months?\n` +
    `4. Does the journalism cite what_would_change_mind? If the invalidator has ALREADY happened -> KILL\n\n` +
    `Use yfinance (via bash: python3 -c "import yfinance; ...") to check 12-month returns.\n` +
    `Pre-flagged tickers still need yfinance confirmation (journalism may be stale).\n` +
    `Any ticker that fails ANY question gets killed with a reason.\n\n` +
    `CANDIDATES: ${allCandidates.join(', ')}\n` +
    `JOURNALISM CONTEXT:\n${JSON.stringify(journalism, null, 1)}\n` +
    `BENEFICIARY CHAINS:\n${JSON.stringify(chains, null, 1)}\n` +
    `Date: ${REPORT_DATE}`,
    { label: 'trend-skeptic-filter', phase: 'Screen', schema: TREND_SKEPTIC_SCHEMA, model: MODEL }
  )

  const survivors = (skepticResult && skepticResult.survivors) ? skepticResult.survivors.filter(s => s.passed) : []
  const killed = (skepticResult && skepticResult.killed) || []
  // Full kill detail (ticker + reason) for the report/no-survivors path -- the top-level `killed` field
  // above is just ticker strings; skepticResult.survivors carries kill_reason per evaluated candidate
  // (both passed and failed) so pull reasons from there and fall back to the bare ticker list.
  const killedDetail = (skepticResult && Array.isArray(skepticResult.survivors))
    ? skepticResult.survivors.filter(s => !s.passed).map(s => ({ ticker: s.ticker, kill_reason: s.kill_reason || '(no reason given)' }))
    : killed.map(t => ({ ticker: t, kill_reason: '(no reason given)' }))
  log(`trend-discovery skeptic: ${survivors.length} survived, ${killed.length} killed`)

  // Cap survivors -- downstream Gather+Panel run per-asset, so keep the candidate count bounded (the
  // journalism fan-out alone already spends 50+ agents; uncapped survivors would multiply that by
  // MAX_GATHER+MAX_PANEL each). Mirrors the original research-trend-stocks quorum cap rationale.
  const capped = survivors.slice(0, 5)
  if (survivors.length > capped.length) log(`trend-discovery: capping ${survivors.length} survivors to top ${capped.length} for the desk`)

  const candidates = capped.map(s => {
    const jFindings = journalism.flatMap(j => (j.findings || []).filter(f => f.ticker === s.ticker))
    const demandInflection = jFindings.map(f => f.demand_inflection).filter(Boolean).join(' | ') || ''
    const supplyConstraint = jFindings.map(f => f.supply_constraint).filter(Boolean).join(' | ') || ''
    // Beneficiary chains this ticker participates in (as primary or as a beneficiary) -- kept structured.
    const relatedChains = chains.filter(c => c.primary === s.ticker || (c.beneficiaries || []).includes(s.ticker))
    return {
      ticker: s.ticker,
      thesis: s.thesis || demandInflection || '(trend-discovery survivor -- see journalism findings)',
      catalyst: s.catalyst || '',
      valuation_gap: '',
      why_not_yet_surged: supplyConstraint || (s.timeline ? `catalyst timeline: ${s.timeline}` : ''),
      // Structured per-ticker journalism evidence -- threaded into Gather/Panel context via ctxFor() so the
      // 50+ journalism agents inform the desk's verdicts, not just the skeptic filter's pass/kill call.
      // Kept lean: structured fields only, never raw agent transcripts.
      journalism: jFindings.map(f => ({
        demand_inflection: f.demand_inflection, supply_constraint: f.supply_constraint,
        catalyst: f.catalyst, timeline: f.timeline, confidence: f.confidence,
        what_would_change_mind: f.what_would_change_mind, source: f.source,
      })),
      beneficiary_chains: relatedChains.map(c => ({ primary: c.primary, beneficiaries: c.beneficiaries, logic: c.logic, conviction: c.conviction })),
    }
  })

  return {
    candidates,
    excluded: killed,
    killedDetail,
    themes,
    chains,
    screen_notes: `trend-discovery: pre-screen ${tickers.length} -> journalism ${totalFindings} findings -> beneficiary ${chains.length} chains -> skeptic ${survivors.length}/${allCandidates.length} survived -> ${candidates.length} handed to the desk`,
  }
}

// ---------- No-survivors report (trend-discovery only) — restores behavior lost in the consolidation:
// when the skeptic filter kills every candidate (or the pre-screen itself returns empty), that is a
// legitimate, reportable outcome, not a generic screener failure. Writes a dated report with themes
// scanned + killed tickers/reasons and returns a clean {survivors:0,...} result (never {error}). Hoisted
// function declaration -- called from the Screen-phase result block above, defined here for readability.
// ----------
async function writeNoSurvivorsReport(screenedResult) {
  const killedList = (screenedResult && Array.isArray(screenedResult.killedDetail) && screenedResult.killedDetail.length)
    ? screenedResult.killedDetail
    : ((screenedResult && screenedResult.excluded) || []).map(t => ({ ticker: t, kill_reason: '(no reason given)' }))
  const themesScanned = (screenedResult && screenedResult.themes) || []
  const noSurvivorsPath = `/Users/engineer/workspace/backtest/research/research.${ASSET_CLASS}.${REPORT_DATE}.md`
  const noSurvivorsMd = `# Research -- NO SURVIVORS (${ASSET_CLASS}) -- ${REPORT_DATE}

> Question: ${QUESTION}
> Strategy: trend-discovery
> Generated by \`research-market-workflow\`. Educational, not advice; re-pull before acting.

## Verdict
**NO SURVIVORS** -- the skeptic filter killed every trend-discovery candidate this run (or the pre-screen returned no tickers). No BUY/HOLD/AVOID verdicts to report.

## Themes scanned
${themesScanned.length ? themesScanned.map(t => `- ${t}`).join('\n') : '(none returned)'}

## Killed tickers + reasons
${killedList.length ? killedList.map(k => `- **${k.ticker}**: ${k.kill_reason}`).join('\n') : '(none -- pre-screen itself returned empty)'}

## Screen notes
${(screenedResult && screenedResult.screen_notes) || '(none)'}
`
  let noSurvivorsOk = false
  for (let attempt = 1; attempt <= 2 && !noSurvivorsOk; attempt++) {
    await agent(`Use the Write tool to create EXACTLY this file:\n${noSurvivorsPath}\nWrite this content VERBATIM (no edits/summary). Create parent dirs. After writing, run Bash \`wc -c < ${noSurvivorsPath}\` to confirm. Reply with just the byte count.\n--- BEGIN ---\n${noSurvivorsMd}\n--- END ---`,
      { label: attempt === 1 ? 'write-no-survivors-report' : `write-no-survivors-report-retry${attempt}`, phase: 'Report', model: MODEL })
    const check = await agent(`Run Bash EXACTLY: \`test -f ${noSurvivorsPath} && wc -c < ${noSurvivorsPath} || echo MISSING\`. Reply with ONLY the byte count number, or the word MISSING.`,
      { label: `verify-no-survivors-report-${attempt}`, phase: 'Report', model: MODEL })
    const bytes = parseInt(String(check).replace(/[^0-9]/g, ''), 10) || 0
    noSurvivorsOk = String(check).indexOf('MISSING') === -1 && bytes > 200
    log(noSurvivorsOk ? `NO SURVIVORS report written + verified (${bytes} bytes): ${noSurvivorsPath}`
      : `WARNING: no-survivors report attempt ${attempt} did NOT persist. ${attempt < 2 ? 'Retrying.' : 'GIVING UP -- report NOT on disk.'}`)
  }
  return {
    survivors: 0, killed: killedList, themes: themesScanned,
    reportPath: noSurvivorsPath, reportPersisted: noSurvivorsOk,
    screen_notes: (screenedResult && screenedResult.screen_notes) || '',
  }
}

// ============================================================================
// runHoldingsSweep — args.mode === "holdings-sweep". Full-book review of HELD positions (vs discovery
// of new names). Reads positions.csv (Position,Quantity,Type,Unrealized_PnL). ETFs/commodity trusts get
// one cheap batched trend-only screen; single-name stocks and any hold-only-tagged positions each get
// ONE agent running the full stocks-advisor BSC hierarchy (6-seat panel + skeptic + CIO synthesis +
// DATA-COVERAGE GATE) internally in a single turn. This workflow is unbiased by default -- it has no
// opinion on any ticker. A position is policy-capped at ADD/HOLD (never TRIM/EXIT) ONLY if the CALLER
// said so, via one of two caller-supplied sources: (a) args.hold_only (explicit ticker list passed at
// invocation) or (b) the positions.csv Type column, which is USER-maintained data -- if the user tagged
// a row 'crypto-beta' or 'hold-only', that is the user specifying their own mandate, not a rule this
// workflow imposes. Hoisted function declaration; called from the MODE dispatch above.
// ============================================================================
async function runHoldingsSweep() {
  phase('LoadPositions')
  const csvRaw = await agent(
    `Run Bash EXACTLY: \`cat ${POSITIONS_CSV}\`. Reply with ONLY the raw file contents, nothing else.`,
    { label: 'load-positions', phase: 'LoadPositions', model: MODEL })

  const lines = String(csvRaw || '').split('\n').map(l => l.trim()).filter(Boolean)
  const dataLines = lines.filter(l => !/^Position\s*,\s*Quantity/i.test(l))
  const rows = dataLines.map(l => {
    const parts = l.split(',')
    return { position: (parts[0] || '').trim(), quantity: (parts[1] || '').trim(), type: (parts[2] || '').trim(), pnl: (parts[3] || '').trim() }
  }).filter(r => r.position && r.type)

  if (!rows.length) { log('FATAL: positions.csv parsed to zero rows; aborting holdings-sweep.'); return { error: 'positions.csv empty or unparsable', mode: 'holdings-sweep' } }

  const cashRows = rows.filter(r => /^cash$/i.test(r.type))
  // Rows the USER tagged hold-only in their own positions.csv (caller-maintained data, not a rule this
  // workflow invents). 'crypto-beta' is this book's existing tag; 'hold-only' is accepted generically
  // for any future caller mandate expressed the same way.
  const taggedHoldOnlyRows = rows.filter(r => /^crypto-beta$/i.test(r.type) || /^hold-only$/i.test(r.type))
  const commodityRows = rows.filter(r => /^comodity$/i.test(r.type) || /^commodity$/i.test(r.type))
  const stockRows = rows.filter(r => /^stock$/i.test(r.type))
  log(`holdings-sweep: ${rows.length} positions -- ${stockRows.length} Stock, ${taggedHoldOnlyRows.length} tagged hold-only, ${commodityRows.length} commodity, ${cashRows.length} cash (skipped)` +
    (HOLD_ONLY_ARG.length ? `; +${HOLD_ONLY_ARG.length} hold-only ticker(s) via args.hold_only` : ''))

  // ---- Classify Stock-type rows: single-name operating company vs ETF/index/sector fund ----
  // The Type column alone can't tell (VOO/XLE/SCHD are all Type=Stock) -- one LLM classification call,
  // not per-position, keeps this cheap while future-proofing against new tickers appearing in the book.
  phase('Classify')
  const classifyResult = stockRows.length ? await agent(
    `Classify each ticker below as either "single-name" (an individual operating company) or "etf-fund" ` +
    `(an ETF, index fund, sector fund, or closed-end fund -- anything that holds a basket rather than operating a business).\n` +
    `Examples of etf-fund: VOO, XLE, SCHD, VXUS, VWO, VEA, GDX, EWZ, ILF, SPLV, ROBO, URNM, GSY, RSP, VHT, XLI.\n` +
    `Examples of single-name: ACN, PYPL, NKE, MSFT, TSLA, AMD, GOOG.\n` +
    `Tickers: ${stockRows.map(r => r.position).join(', ')}\n` +
    `Return one classification per ticker.`,
    { label: 'classify-holdings', phase: 'Classify', schema: HOLDINGS_CLASSIFY_SCHEMA, model: MODEL }
  ) : { classifications: [] }

  const classMap = {}
  for (const c of (classifyResult && classifyResult.classifications) || []) {
    if (c && c.ticker) classMap[String(c.ticker).toUpperCase()] = c.bucket
  }
  const singleNameStocks = stockRows.filter(r => classMap[r.position.toUpperCase()] !== 'etf-fund')
  const etfStocks = stockRows.filter(r => classMap[r.position.toUpperCase()] === 'etf-fund')
  log(`holdings-sweep classify: ${singleNameStocks.length} single-name, ${etfStocks.length} ETF/fund (of ${stockRows.length} Stock-type rows)`)

  // Commodity trusts (PSLV, PHYS) hold bullion rather than operate a business -- bucket with ETFs.
  const etfBucket = [...etfStocks, ...commodityRows]
  // holdOnly flag: true iff the CALLER said so -- via positions.csv Type tag (taggedHoldOnlyRows) or
  // args.hold_only naming this ticker explicitly. No ticker is hardcoded as hold-only in this file.
  const panelBucket = [
    ...singleNameStocks.map(r => ({ ...r, holdOnly: HOLD_ONLY_ARG_SET.has(r.position.toUpperCase()) })),
    ...taggedHoldOnlyRows.map(r => ({ ...r, holdOnly: true })),
  ]

  // ---- ETF/commodity trend-only screen: ONE batched agent, not per-name (kept lean) ----
  phase('TrendScreen')
  const trendResult = etfBucket.length ? await agent(
    `Run a LIGHTWEIGHT trend-only screen (NOT a full fundamental panel) for these ETF/index/commodity-trust ` +
    `holdings. For each: check price vs 50d/200d moving average and recent momentum via TradingView MCP or a ` +
    `quick price fetch. Verdict is HOLD by default; only flag TRIM if the fund is decisively broken-trend ` +
    `(price well below both 50d and 200d MA with no reversal signal) -- ETFs are diversified, so this is a ` +
    `coarse screen, not a sell recommendation engine.\n` +
    `Holdings: ${etfBucket.map(r => `${r.position} (qty ${r.quantity}, unrealized P&L ${r.pnl})`).join('; ')}\n` +
    `Date: ${REPORT_DATE}`,
    { label: 'etf-trend-screen', phase: 'TrendScreen', schema: HOLDINGS_TREND_SCHEMA, model: MODEL }
  ) : { rows: [] }
  const trendRows = (trendResult && trendResult.rows) || []
  log(`holdings-sweep trend-screen: ${trendRows.length} ETF/commodity rows screened`)

  // ---- Single-name + caller-tagged hold-only: ONE 6-seat BSC panel agent per ticker, batched under the concurrency cap ----
  // Plain parallel() -- the platform auto-queues past its concurrency cap (established precedent: the
  // trend-discovery journalism fan-out above routinely runs 50+ agents this way).
  phase('Panel')
  log(`holdings-sweep panel: fanning out ${panelBucket.length} per-name agents`)
  const panelResults = await parallel(panelBucket.map(r => () => {
    const holdOnlyNote = r.holdOnly
      ? `\nCALLER MANDATE -- this position was flagged hold-only by the caller (positions.csv Type tag or ` +
        `args.hold_only), not by this workflow. FINAL VERDICT must be ADD or HOLD ONLY -- never TRIM or EXIT on ` +
        `this ticker in this run, regardless of what the panel/skeptic finds. Run the analysis exactly as ` +
        `unbiased as any other ticker; only the final verdict is clamped -- state that explicitly in the CIO ` +
        `memo if the underlying analysis would otherwise have supported a sell.`
      : ''
    return agent(
      `You are running a full holdings review for ONE position: ${r.position} (qty ${r.quantity}, unrealized P&L ${r.pnl}).\n` +
      `Do this yourself, in this ONE turn -- do NOT spawn subagents, you are already the leaf-level worker:\n` +
      `1. Gather data yourself: fundamentals + TradingView MCP price/indicators + a recent-news check. For the ` +
      `smart-money/insider seat use Form 4 via https://openinsider.com/screener?s=${r.position} -- if that returns ` +
      `403/blocked, fall back to https://finviz.com/quote.ashx?t=${r.position} (Insider Trading table) as documented. ` +
      `For the sell-side seat web_fetch analyst consensus/price-target pages per the analyse-sellside skill ` +
      `(Yahoo Finance analysis tab, StockAnalysis.com forecast, TipRanks, MarketBeat, Zacks, Morningstar) -- ` +
      `no fetched page = INSUFFICIENT_DATA for that seat, never guess a rating or PT.\n` +
      `2. Run the 6-seat panel using the verbatim seat prompts in ${SKILL}/stocks-advisor/references/seat-prompts.md ` +
      `(Fundamental/Buffett, Technical/Druckenmiller, Narrative-Macro, Sentiment-Positioning, Smart-Money, Sell-Side) -- ` +
      `apply each seat's framework yourself, one at a time, to the data you gathered.\n` +
      `3. Apply the BSC hierarchy in ${SKILL}/stocks-advisor/references/hierarchies/bsc.md: mandatory Skeptic step, ` +
      `then CIO Synthesis -- INCLUDING the DATA-COVERAGE GATE (>=2/6 seats with no real data caps the verdict at HOLD).\n` +
      `4. Use HOLDINGS-PATH vocabulary: FINAL VERDICT must be one of ADD | HOLD | TRIM | EXIT (cost basis is known ` +
      `from the unrealized P&L given above).\n` +
      `5. FUNDING-POOL TEST -- if your verdict would be TRIM or EXIT, only let it stand if BOTH (a) no realistic ` +
      `1-2 year growth catalyst AND (b) no dividend yield good enough to justify holding for income; otherwise ` +
      `downgrade to HOLD and say so in funding_pool_test. State the test result explicitly either way.${holdOnlyNote}\n` +
      `Date: ${REPORT_DATE}\n` +
      `Return: ticker=${r.position}, final_verdict, conviction (1-5), data_coverage ("N/6 seats had real evidence"), ` +
      `gate_triggered (bool), dissent_logged, cio_memo, funding_pool_test.`,
      { label: `holding-panel:${r.position}`, phase: 'Panel', schema: HOLDING_PANEL_SCHEMA, model: MODEL }
    )
  }))
  const panelVerdicts = panelResults.map((v, i) => {
    const r = panelBucket[i]
    const filled = v || {
      ticker: r.position, final_verdict: 'HOLD', conviction: 0,
      data_coverage: '0/6 -- agent failed', gate_triggered: true, cio_memo: '[UNAVAILABLE: panel agent failed]',
    }
    // Code-enforced clamp -- the CALLER MANDATE prompt note above is advisory only; an LLM panel agent can
    // still return TRIM/EXIT despite the instruction. Force HOLD here so the caller's mandate is guaranteed,
    // not merely requested. Raw (pre-clamp) verdict kept in panel_verdict for transparency -- the
    // report/consumer can see what the panel actually concluded before the clamp. This clamp only fires for
    // rows the caller flagged (r.holdOnly) -- untagged positions always get the panel's unbiased verdict.
    if (r.holdOnly && ['TRIM', 'EXIT'].includes(filled.final_verdict)) {
      filled.panel_verdict = filled.final_verdict
      filled.final_verdict = 'HOLD'
      filled.policy_note = 'clamped: caller-flagged HOLD-ONLY'
    }
    return filled
  })
  log(`holdings-sweep panel: ${panelVerdicts.filter(v => v.final_verdict !== 'HOLD').length}/${panelVerdicts.length} non-HOLD verdicts`)

  // ---- Consolidate: merge per-name verdicts into one report (pure JS -- each panel agent already
  // returned a final structured verdict, so no extra LLM synthesis step is needed here) ----
  phase('Consolidate')
  const panelTableRows = panelVerdicts.map(v => {
    const src = panelBucket.find(r => r.position === v.ticker) || {}
    return `| ${v.ticker} | ${src.quantity || ''} | ${src.pnl || ''} | **${v.final_verdict}** | ${v.conviction}/5 | ${v.data_coverage || ''} |`
  }).join('\n')
  const trendTableRows = trendRows.map(t => {
    const src = etfBucket.find(r => r.position === t.ticker) || {}
    return `| ${t.ticker} | ${src.quantity || ''} | ${src.pnl || ''} | **${t.verdict}** | ${t.note || ''} |`
  }).join('\n')
  const panelDetail = panelVerdicts.map(v =>
    `### ${v.ticker} -- ${v.final_verdict} (conviction ${v.conviction}/5)\n` +
    `**Data coverage:** ${v.data_coverage || 'n/a'}${v.gate_triggered ? ' -- GATE TRIGGERED' : ''}\n` +
    `**Dissent:** ${v.dissent_logged || 'none'}\n` +
    `**CIO memo:** ${v.cio_memo || ''}\n` +
    (v.funding_pool_test ? `**Funding-pool test:** ${v.funding_pool_test}\n` : '') +
    (v.policy_note ? `**Policy:** ${v.policy_note} (raw panel verdict: ${v.panel_verdict})\n` : '')
  ).join('\n\n---\n\n')

  const addCount = panelVerdicts.filter(v => v.final_verdict === 'ADD').length
  const trimExitCount = panelVerdicts.filter(v => v.final_verdict === 'TRIM' || v.final_verdict === 'EXIT').length
  const holdCount = panelVerdicts.length - addCount - trimExitCount
  // Action summary: one scannable line per non-HOLD verdict (SELL/TRIM/EXIT first, then ADD), the
  // controlling reason truncated to keep it a one-liner -- same "lead with the actions" convention as
  // stocks-daily/crypto-daily's Telegram ACTION SUMMARY, adapted to this markdown report surface.
  const actionEmoji = { ADD: '🟢', TRIM: '🔴', EXIT: '🔴' }
  const actionLines = panelVerdicts
    .filter(v => v.final_verdict !== 'HOLD')
    .sort((a, b) => (a.final_verdict === 'ADD' ? 1 : 0) - (b.final_verdict === 'ADD' ? 1 : 0))
    .map(v => `${actionEmoji[v.final_verdict] || '🟡'} ${v.ticker} ${v.final_verdict} -- ${String(v.cio_memo || v.funding_pool_test || '').slice(0, 90)}`)
    .join('\n')

  // ---- Report: write + VERIFY + retry (mirrors the discovery-mode Report phase above) ----
  phase('Report')
  const reportPath = `/Users/engineer/workspace/backtest/research/holdings-sweep.${REPORT_DATE}.md`
  const reportMd = `# Holdings Sweep -- ${REPORT_DATE}

> Full-book review of ${rows.length} HELD positions (${panelBucket.length} full BSC panel, ${etfBucket.length} ETF/commodity trend-only, ${cashRows.length} cash skipped).
> Source: ${POSITIONS_CSV}
> Generated by \`research-market-workflow\` (holdings-sweep mode). Educational, not advice; re-pull before acting.

## Summary
**${addCount} ADD** | ${holdCount} HOLD | ${trimExitCount} TRIM/EXIT

## Action summary
${actionLines || '(no ADD/TRIM/EXIT this run -- every position HOLD)'}

## Single-name + hold-only-tagged panel (full BSC hierarchy)
| Ticker | Qty | Unrealized P&L | Verdict | Conviction | Data coverage |
|---|---|---|---|---|---|
${panelTableRows}

## ETF / commodity trend-only screen
| Ticker | Qty | Unrealized P&L | Verdict | Note |
|---|---|---|---|---|
${trendTableRows || '(none)'}

## Panel detail
${panelDetail}

## Cash (skipped)
${cashRows.map(r => `- ${r.position}: ${r.quantity}`).join('\n') || '(none)'}
`
  let reportOk = false
  for (let attempt = 1; attempt <= 2 && !reportOk; attempt++) {
    await agent(`Use the Write tool to create EXACTLY this file:\n${reportPath}\nWrite this content VERBATIM (no edits/summary). Create parent dirs. After writing, run Bash \`wc -c < ${reportPath}\` to confirm. Reply with just the byte count.\n--- BEGIN ---\n${reportMd}\n--- END ---`,
      { label: attempt === 1 ? 'write-holdings-report' : `write-holdings-report-retry${attempt}`, phase: 'Report', model: MODEL })
    const check = await agent(`Run Bash EXACTLY: \`test -f ${reportPath} && wc -c < ${reportPath} || echo MISSING\`. Reply with ONLY the byte count number, or the word MISSING.`,
      { label: `verify-holdings-report-${attempt}`, phase: 'Report', model: MODEL })
    const bytes = parseInt(String(check).replace(/[^0-9]/g, ''), 10) || 0
    reportOk = String(check).indexOf('MISSING') === -1 && bytes > 500
    log(reportOk ? `Holdings-sweep report written + verified (${bytes} bytes): ${reportPath}`
      : `WARNING: write-holdings-report attempt ${attempt} did NOT persist. ${attempt < 2 ? 'Retrying.' : 'GIVING UP -- report NOT on disk; downstream must use the returned verdicts field.'}`)
  }

  // ---- Ledger: one row per panel-reviewed ticker (ETF trend-only rows skipped -- a coarse screen isn't a dated forecast) ----
  phase('Ledger')
  const horizon = REPORT_DATE.slice(0, 4) + '-12-31'
  const verdictProb = { ADD: 0.7, HOLD: 0.5, TRIM: 0.3, EXIT: 0.15 }
  const ledgerLogs = await parallel(panelVerdicts.map(v => () =>
    agent(
      `Use Bash to run EXACTLY (appends one dated forecast row):\n\n` +
      `python3 ${LEDGER_PY} add --asset ${v.ticker} --q ${JSON.stringify('holdings-sweep panel: ' + String(v.cio_memo || v.final_verdict).slice(0, 160))} ` +
      `--p ${(verdictProb[v.final_verdict] ?? 0.5).toFixed(2)} --by ${JSON.stringify(horizon)} --lens stocks-advisor-bsc ` +
      `--source research-market-workflow-holdings-sweep --flip ${JSON.stringify(String(v.dissent_logged || 'thesis break').slice(0, 160))} --created ${JSON.stringify(REPORT_DATE)}\n\n` +
      `If "id exists", re-run once with --id ${String(v.ticker).toLowerCase()}-${REPORT_DATE}-holdings. Reply with the CLI's stdout line.`,
      { label: `ledger-holding-${v.ticker}`, phase: 'Ledger', model: MODEL }))
  )
  log(`holdings-sweep ledger: ${panelVerdicts.length} entries logged`)

  return {
    mode: 'holdings-sweep', date: REPORT_DATE, reportPath, reportPersisted: reportOk,
    totalPositions: rows.length, panelCount: panelBucket.length, etfCount: etfBucket.length, cashSkipped: cashRows.length,
    verdicts: panelVerdicts, trend: trendRows,
    summary: { add: addCount, hold: holdCount, trimExit: trimExitCount },
  }
}
