export const meta = {
  name: 'hedge-fund-committee',
  description: 'Find the next stocks to BUY and hand over a STAGED ENTRY plan. A hedge-fund org of agent-employees DISCOVERS candidates (FT/WSJ/Reddit news + 13F/congress/dips/macro), aggregates by conviction, a panel votes on OWNERSHIP vs TIMING separately (4 skeptics + 1 PM advocate who builds the bull case), risk vetoes/sizes, and the CIO issues a scale-in plan (start small now, add on triggers) — not a binary buy/pass. Open-universe research, no ticker needed. RECOMMEND-ONLY.',
  whenToUse: 'PRIMARY: "what should I buy this week / next picks" — open-universe discovery, NO ticker. The SLOW/deliberative tier (daily cron dip/convergence alerts are the separate FAST tier). SECONDARY (optional): pass args:{ticker} only to deep-dive a name you ALREADY have.',
  phases: [
    { title: 'Analysts' },
    { title: 'Aggregate' },
    { title: 'Committee' },
    { title: 'Risk' },
    { title: 'Decision' },
  ],
}

// args (optional): { ticker: "GOOGL" } to deep-dive ONE name, else the full discovery sweep.
//                  { portfolio: "<holdings text/CSV>" } to ground sizing/concentration in the REAL book.
const FOCUS = (args && args.ticker) ? String(args.ticker).toUpperCase() : null
const PORTFOLIO = (args && args.portfolio) ? String(args.portfolio) : null
const BOOK_NOTE = PORTFOLIO
  ? `CURRENT BOOK (ground all sizing/concentration in this — do NOT invent weights):\n${PORTFOLIO}`
  : `NO current portfolio was supplied. Do NOT invent any "existing X% of book" weight. Treat sizes as ` +
    `CEILINGS for a NEW position assuming ZERO current exposure (single-name cap 10%); explicitly caveat ` +
    `that the owner must verify against the actual book before sizing.`

// ── Schemas ────────────────────────────────────────────────────────────────
const REPORT = {
  type: 'object',
  properties: {
    desk: { type: 'string' },
    summary: { type: 'string' },
    candidates: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          ticker: { type: 'string' },
          thesis: { type: 'string' },
          conviction: { type: 'integer', minimum: 1, maximum: 5 },
          evidence: { type: 'string' },     // a REAL fetched fact, or "[unverified]"
        },
        required: ['ticker', 'thesis', 'evidence'],
      },
    },
    unverified: { type: 'string' },          // anything it could not fetch
  },
  required: ['desk', 'summary', 'candidates'],
}
// A vote answers TWO SEPARATE questions — this split is the fix for the "NO-machine": a great business
// worth OWNING can still be a WAIT on timing, and that must NOT collapse to PASS. `own` = the business/
// value judgment (ignore short-term tape); `today` = the timing judgment (what to do RIGHT NOW).
const VOTE = {
  type: 'object',
  properties: {
    own: { type: 'string', enum: ['YES', 'NO'] },              // worth OWNING at this price over 12-24mo, IGNORING timing
    today: { type: 'string', enum: ['STARTER', 'WAIT', 'AVOID'] }, // RIGHT NOW: small first tranche / wait for trigger / not worth owning
    conviction: { type: 'integer', minimum: 1, maximum: 5 },
    reason: { type: 'string' },
    add_trigger: { type: 'string' },          // the dated/price event that would make you ADD the next tranche
    invalidation: { type: 'string' },
    blind_spot: { type: 'string' },          // mandatory: what this lens is structurally bad at
  },
  required: ['own', 'today', 'conviction', 'reason', 'add_trigger', 'invalidation', 'blind_spot'],
}
const RISK = {
  type: 'object',
  properties: {
    gate: { type: 'string', enum: ['PASS', 'VETO'] },
    reason: { type: 'string' },
    max_size_pct: { type: 'number' },
  },
  required: ['gate', 'reason'],
}

// ── PHASE 1 — ANALYST FAN-OUT (employees gather, do NOT decide) ──────────────
// Each runs ONE skill via the agent and returns a structured report. Parallel, fault-isolated.
phase('Analysts')
const DESKS = [
  { desk: 'macro-regime',        prompt: 'You are the macro/regime analyst. Run /regime-detection AND /fomc-monitor. Summary = regime (RISK_ON/NEUTRAL/RISK_OFF) + exposure dial + Fed tone/next-meeting. candidates: [] unless a regime/Fed shift implies a specific tilt.' },
  { desk: 'institutional-flows', prompt: 'You are the institutional-flows analyst. Run /13f-watch (Burry/Buffett/Ackman/Klarman/Li Lu). Return ONLY new, deduped institutional BUYS as candidates (source=13F, evidence=fund+filing). Drop puts/trims/exits. State the 45-day lag.' },
  { desk: 'political-flows',     prompt: 'You are the political-flows analyst. Run /congressman-stock-watch (last 90d). Return only NEW deduped congressional PURCHASES as candidates (evidence=member+date+amount). State the 30-45d disclosure lag. If the source is rate-limited, say so and return [].' },
  { desk: 'news-narrative',      prompt: 'You are the news/narrative analyst. Surface the themes the financial press + retail are converging on, and the specific tickers with a LIVE catalyst. SOURCES (use them, do not just count RSS): run /trend-stock-research for the mention-velocity baseline, THEN actually READ headlines/leads via WebSearch + WebFetch across FT, WSJ, Bloomberg, Reuters AND retail sentiment (Reddit r/stocks, r/wallstreetbets, r/investing). For each candidate give evidence = a real dated headline/source you actually read (outlet + date), and tag PRICED_IN vs ACTIONABLE (still early). Prefer non-obvious names where a narrative is BUILDING over weeks (the SanDisk pattern), not already-extended momentum. Never invent a headline or a number; mark anything you could not read [unverified].' },
  { desk: 'equity-dips',         prompt: 'You are the equity dip analyst. Run /dip-screener. Return HIGH/MEDIUM dips (>=25% below 52w high) as candidates (evidence=pct_from_high + 200dMA). Quality names only; a dip is a candidate, not a buy.' },
  { desk: 'crypto',              prompt: 'You are the crypto desk analyst. Run /crypto-dip-scanner. Return coins >=30% below 52w high as candidates with Fear&Greed in evidence. Note BTC-as-hurdle. Funding may be [unverified] (geo-block).' },
  { desk: 'crowd-odds',          prompt: 'You are the crowd-odds analyst. Run /prediction-market-odds for the macro/Fed/index markets that matter this week. Summary = what the crowd is pricing + implication for equities. candidates only if a market implies a specific name.' },
]
const desks = FOCUS
  ? [{ desk: 'focus-research', prompt: `Deep-research ${FOCUS}: run /fundamental-analysis + /trend-stock-research + check /13f-watch and /congressman-stock-watch for ${FOCUS}. Return ${FOCUS} as a candidate with the strongest REAL evidence (valuation, FCF, who owns it, live catalyst).` }]
  : DESKS
// DESK-HEALTH ACCOUNTING: every desk is ALWAYS represented in `reports`, even on death/error.
// A desk that returns [] (ran, found nothing) MUST be distinguishable from one that errored — otherwise
// a silently-dropped crypto/congress desk reads as "nothing to buy there" when it actually never ran.
const reports = await parallel(desks.map(d => () =>
  agent(d.prompt + ' Educational only, recommend-only. Mark anything you could not fetch [unverified] — NEVER fabricate a number, price, or headline.',
    { label: `analyst:${d.desk}`, phase: 'Analysts', schema: REPORT })
    // Tag with OUR controlled key — never rely on the agent's free-text `desk` field for lookups.
    .then(r => r
      ? { ...r, _key: d.desk, _status: 'ran' }
      : { _key: d.desk, _status: 'errored', summary: '[desk returned no result — agent died/timed out]', candidates: [] })
    .catch(err => ({ _key: d.desk, _status: 'errored', summary: `[desk threw: ${String(err).slice(0, 120)}]`, candidates: [] }))
))

// ── PHASE 2 — CHIEF OF STAFF: aggregate into ONE briefing packet ─────────────
// Plain code first (cheap, deterministic): cluster by ticker, count SOURCES (not "independent desks" —
// 13F + a value lens can echo the SAME fact, so n_sources is crowdedness, NOT proven triangulation).
phase('Aggregate')
const FLOW_DESKS = new Set(['institutional-flows', 'political-flows'])  // 30-45d LAGGED — context, not time-sensitive
// Desk-coverage roster: ran (found names) / empty (ran, nothing) / FAILED (errored/died). The CIO MUST
// surface this so an absent crypto/congress desk is a LOUD gap, never silent "nothing to buy".
const coverage = reports.map(r => ({
  desk: r._key,
  status: r._status === 'errored' ? 'FAILED' : ((r.candidates || []).length ? 'ran' : 'empty'),
  n: (r.candidates || []).length,
  note: r._status === 'errored' ? r.summary : (r.unverified || null),
}))
const deadDesks = coverage.filter(c => c.status === 'FAILED').map(c => c.desk)
log(`Desk coverage: ${coverage.map(c => `${c.desk}=${c.status}(${c.n})`).join(', ')}`)
const byTicker = {}
for (const r of reports) for (const c of (r.candidates || [])) {
  const t = (c.ticker || '').toUpperCase().trim()
  if (!t) continue
  const e = (byTicker[t] ||= { ticker: t, sources: new Set(), notes: [], maxConv: 0 })
  e.sources.add(r._key)
  e.maxConv = Math.max(e.maxConv, Number(c.conviction) || 0)
  e.notes.push(`${r._key}: ${c.thesis} [${c.evidence}]`)
}
const clustered = Object.values(byTicker).map(e => {
  const srcs = [...e.sources]
  const flow_only = srcs.every(s => FLOW_DESKS.has(s))   // ONLY 13F/congress surfaced it → lagged, low time-sensitivity
  return { ticker: e.ticker, n_sources: e.sources.size, sources: srcs, flow_only, max_conviction: e.maxConv, notes: e.notes }
}).sort((a, b) =>
  // rank by source count, but a fresh (non-flow) signal outranks a flow-only one at equal count
  (b.n_sources - a.n_sources) || (a.flow_only === b.flow_only ? 0 : a.flow_only ? 1 : -1)
)
const macro = reports.find(r => r._key === 'macro-regime' || r._key === 'focus-research')
// GATE before the expensive committee. A name EARNS the committee if it shows convergence (n_sources>=2)
// OR a desk's high conviction (>=4) OR it is a NARRATIVE thesis from the news desk. That last clause is
// the SanDisk fix: convergence LAGS — by the time a 2nd desk corroborates a story it is already priced.
// The whole edge (Google -30%, SanDisk's weeks-long FT/WSJ build) is catching a live-catalyst narrative
// while only the news desk sees it, single-source. Gating discovery on convergence would defeat the
// system's core purpose, so a news-narrative name always reaches the panel — the panel can still PASS it.
const NARRATIVE_DESKS = new Set(['news-narrative'])
let TOP, thinWeek = false
if (FOCUS) {
  TOP = clustered.slice(0, 1)
} else {
  const gated = clustered.filter(c =>
    c.n_sources >= 2 ||
    c.max_conviction >= 4 ||
    c.sources.some(s => NARRATIVE_DESKS.has(s)))   // live-catalyst news thesis reaches the panel even single-source
  if (gated.length) {
    // Rank narrative names up so they aren't crowded out of the cap by mechanical dips.
    TOP = gated.slice().sort((a, b) => {
      const an = a.sources.some(s => NARRATIVE_DESKS.has(s)) ? 1 : 0
      const bn = b.sources.some(s => NARRATIVE_DESKS.has(s)) ? 1 : 0
      return (bn - an) || (b.n_sources - a.n_sources) || (b.max_conviction - a.max_conviction)
    }).slice(0, 8)
  } else {
    thinWeek = true
    TOP = clustered.slice().sort((a, b) => b.max_conviction - a.max_conviction).slice(0, 2)
  }
}
log(`Aggregated ${clustered.length} names; panel sees ${TOP.length}${thinWeek ? ' (THIN WEEK — watch-only fallback)' : ''}: ${TOP.map(t => `${t.ticker}(${t.n_sources}src,c${t.max_conviction}${t.flow_only ? ',flow-only' : ''})`).join(', ') || 'none'}`)
if (!TOP.length) return { regime: macro?.summary, coverage, dead_desks: deadDesks, note: 'No candidates surfaced this cycle. No action.', reports }

// ── PHASE 3 — INVESTMENT COMMITTEE (panel) ───────────────────────────────────
// Each lens votes INDEPENDENTLY (parallel = no anchoring on peers). Dissent is preserved, never averaged.
phase('Committee')
// 5 seats. Four ORTHOGONAL skeptic/judgment lenses PLUS a PM/RISK-TAKER ADVOCATE. The old all-skeptic
// panel was a structural NO-machine: every fresh -30% dip is below its 200dMA (Druckenmiller auto-PASS),
// "could fall further" (superforecaster), a long-duration asset into the recession (Hunt) — so the tool
// built to CATCH -30% dips reflexively rejected every -30% dip. The advocate's job is to build the
// strongest evidence-based BULL case and propose a STAGED entry; it argues for ownership, the skeptics
// pressure-test it, and the CRO + the deterministic plan keep it honest. (Graham overlaps Buffett;
// Lyn-Alden overlaps Hunt — excluded. fundamental-analysis overlapped Buffett — replaced by superforecasting.)
const LENSES = [
  { key: 'pm-advocate',                     skill: null },                            // OFFENSE: builds the bull case + staged entry
  { key: 'analytics-warren-buffett',        skill: 'analytics-warren-buffett' },      // quality / business-value
  { key: 'analytics-stanley-druckenmiller', skill: 'analytics-stanley-druckenmiller' }, // timing / liquidity / tape
  { key: 'analytics-lacy-hunt',             skill: 'analytics-lacy-hunt' },           // PROTECTED deflation / macro-dissent seat
  { key: 'superforecasting',                skill: 'superforecasting' },              // outside view / base rates
]
const TWO_Q = `Answer TWO SEPARATE questions and DO NOT let one bleed into the other:\n` +
  `(1) own: is this worth OWNING at this price on a 12-24 month horizon, IGNORING short-term timing/tape? YES or NO.\n` +
  `(2) today: what to do RIGHT NOW — STARTER (a small first tranche is justified now), WAIT (worth owning but hold fire until your named add_trigger), or AVOID (not worth owning at all).\n` +
  `A wonderful business worth owning can still be a WAIT on timing — that is expected, not a contradiction, and it is NOT an AVOID. ` +
  `Give conviction 1-5, one reason grounded in a REAL fact, the add_trigger (price/event that earns the next tranche), the invalidation, and your lens's structural blind spot. Recommend-only.`
const lensPrompt = (cand, lens) => {
  const ctx = `Macro backdrop: ${macro?.summary || '[unknown]'}. ` +
    `Surfaced by ${cand.n_sources} source(s)${cand.flow_only ? ' — ALL are 30-45d LAGGED 13F/congress flows (context only, NOT time-sensitive)' : ''} (sources may be correlated, not independent): ${cand.notes.join(' | ')}. `
  return lens.skill
    ? `Apply ONLY the /${lens.skill} lens to ${cand.ticker}. ${ctx}Commit your OWN view before considering any other seat. ${TWO_Q}`
    : `You are the PM / RISK-TAKER ADVOCATE on the investment committee — the seat that TAKES positions, not just avoids losses. ` +
      `Build the STRONGEST evidence-based BULL case for ${cand.ticker} and the asymmetry in this setup, then propose a STAGED entry. ${ctx}` +
      `You may vote today=AVOID ONLY if the thesis is genuinely broken (a real moat breach / fundamental impairment), not merely because the tape is weak or a macro event looms — weak tape is a reason to stage smaller, not to avoid. Default to own=YES with a small STARTER and a concrete add_trigger when a quality franchise is marked down. ${TWO_Q}`
}
const judged = await parallel(TOP.map(cand => () =>
  parallel(LENSES.map(lens => () =>
    agent(lensPrompt(cand, lens),
      { label: `vote:${cand.ticker}:${lens.key.replace('analytics-', '')}`, phase: 'Committee', schema: VOTE })
      .then(v => ({ lens: lens.key, ...v }))
  )).then(votes => ({ ...cand, votes: votes.filter(Boolean) }))
))

// ── PHASE 4 — RISK (CRO holds the binding veto + sizing) ─────────────────────
phase('Risk')
const risked = await parallel(judged.filter(Boolean).map(j => () =>
  agent(
    `You are the CRO. Apply /risk-management to a proposed position in ${j.ticker}. ` +
    `Regime: ${macro?.summary || '[unknown]'}. Committee votes: ${JSON.stringify(j.votes.map(v => ({ l: v.lens, own: v.own, today: v.today, c: v.conviction })))}. ` +
    `${BOOK_NOTE} ` +
    `VETO if: RISK_OFF regime, or this would take any name >10% of book, or (only if a book is supplied) the sector is already concentrated. ` +
    `Else PASS with a max size. Note the engine STAGES entries (a STARTER is a small first tranche, typically ~20-30% of the max size), ` +
    `so a PASS gate blocks even the starter; size the CEILING, the engine sizes the tranche. Deterministic risk discipline, not opinion. Never fabricate a portfolio weight.`,
    { label: `risk:${j.ticker}`, phase: 'Risk', schema: RISK })
    .then(risk => ({ ...j, risk }))
)).then(a => a.filter(Boolean))

// ── DETERMINISTIC STAGED-ENTRY PLAN (code, not LLM) ──────────────────────────
// Separate OWNERSHIP (own=YES count) from TIMING (today). A name a majority would OWN, that clears the
// CRO gate, becomes a SCALE_IN (start small now, add on triggers) — NOT a PASS. This is the structural
// cure for the NO-machine: the timing skeptics set the ADD triggers, they no longer veto the starter.
function stagedPlan(j) {
  const votes = j.votes || []
  const n = votes.length || 1
  const ownYes = votes.filter(v => v.own === 'YES')
  const starterNow = votes.filter(v => v.today === 'STARTER')
  const avoid = votes.filter(v => v.today === 'AVOID')
  if (j.risk && j.risk.gate === 'VETO') return { action: 'NO_NEW_RISK', own_yes: ownYes.length, n, starter_now: starterNow.length, note: `CRO veto: ${j.risk.reason || ''}` }
  if (ownYes.length >= Math.ceil(n / 2) && starterNow.length >= 1) return { action: 'SCALE_IN', own_yes: ownYes.length, n, starter_now: starterNow.length }        // own-majority + someone wants in now
  if (ownYes.length >= Math.ceil(n / 2)) return { action: 'STAGE_ON_TRIGGER', own_yes: ownYes.length, n, starter_now: 0 }                                            // worth owning, but all say WAIT → 0 now, add on trigger
  if (ownYes.length >= 1 && starterNow.length >= 1) return { action: 'STARTER_PROBE', own_yes: ownYes.length, n, starter_now: starterNow.length }                    // minority ownership + a STARTER → small probe
  if (ownYes.length >= 1) return { action: 'WATCH', own_yes: ownYes.length, n, starter_now: 0 }                                                                      // someone sees ownership, nobody wants in yet
  return { action: 'PASS', own_yes: 0, n, starter_now: 0 }                                                                                                           // nobody would own it → true reject
}
// CODE-ENFORCED DISSENT: the strongest voice OPPOSING the plan (a skeptic if we're buying; the advocate
// if we're passing). Computed in JS so the CIO can't average it away — MUST be echoed verbatim in the memo.
function minorityVote(votes, action) {
  if (!votes || !votes.length) return null
  const buying = ['SCALE_IN', 'STAGE_ON_TRIGGER', 'STARTER_PROBE', 'WATCH'].includes(action)
  const pool = buying ? votes.filter(v => v.own === 'NO' || v.today === 'AVOID')  // who argued against owning
                      : votes.filter(v => v.own === 'YES')                         // who argued FOR owning (the advocate we overrode)
  if (!pool.length) return null
  return pool.slice().sort((a, b) => b.conviction - a.conviction)[0]
}
const decided = risked.map(j => {
  const plan = stagedPlan(j)
  return { ...j, plan, minority: minorityVote(j.votes, plan.action) }
})

// ── PHASE 5 — CIO writes TWO artifacts: a 1-min BRIEF + the full audit MEMO ────
// The owner is a busy PM. The BRIEF is the 30-second read (what / how much / why). The full MEMO is the
// audit trail behind it. Length discipline: verbatim dissent ONLY on actionable verdicts; PASS/HOLD get
// one line. The CEILING caveat is stated ONCE. §"could not verify" must NOT repeat the coverage-table notes.
phase('Decision')
const memo = await agent(
  `You are the PM/CIO of a hedge fund that TAKES staged positions — your job is to hand the owner an ` +
  `ACTIONABLE staged-entry plan, not a wall of reasons to do nothing. Write TWO markdown files.\n` +
  `REGIME/FED: ${macro?.summary || '[unknown]'}\n` +
  `DESK COVERAGE (ran/empty/FAILED + n candidates): ${JSON.stringify(coverage)}\n` +
  `THIN WEEK (no name cleared the n_sources>=2 OR conviction>=4 gate; names below are WATCH-ONLY ` +
  `fallbacks, not earned candidates): ${thinWeek}\n` +
  `DECIDED CANDIDATES (each has \`votes\` with own/today, \`risk\` gate, code-computed \`plan.action\`, and \`minority\`): ${JSON.stringify(decided)}\n\n` +

  `HOW TO READ THE PLAN (code-computed, deterministic — you may NOT override it):\n` +
  `- own=YES/NO is the OWNERSHIP vote (worth owning 12-24mo); today=STARTER/WAIT/AVOID is the TIMING vote. They are SEPARATE.\n` +
  `- plan.action: SCALE_IN = owner-majority + someone wants in → START a small tranche NOW (~20-30% of the risk ceiling) and add on triggers. ` +
  `STAGE_ON_TRIGGER = worth owning but everyone says WAIT → 0% now, full tranche plan keyed to add_triggers. ` +
  `STARTER_PROBE = minority ownership + a STARTER vote → small probe only. WATCH = someone sees ownership, nobody wants in yet. ` +
  `PASS = nobody would own it (true reject). NO_NEW_RISK = CRO veto.\n` +
  `- A -30% quality name that a majority would OWN must come out as SCALE_IN or STAGE_ON_TRIGGER with concrete tranche sizes and add-triggers — NOT a bare PASS. That is the whole point.\n\n` +

  `=== FILE 1 — THE BRIEF (\`reports/hedge-fund-brief-<date>.md\`) — the busy-PM 1-minute read, MAX ~22 lines ===\n` +
  `Start with "# BUY BRIEF — <date>". Then:\n` +
  `- ONE bottom-line action line naming what to BUY now and what to stage (e.g. "STARTER 2% ADBE + 2% NOW today; stage adds post-FOMC / on 200dMA reclaim").\n` +
  `- ONE regime line: regime + exposure dial + the single biggest event risk.\n` +
  `- A DECISIONS TABLE, one row per name: | Ticker | Action | Buy now (%) | Add trigger | One-line why | Dissent |. ` +
  `Action = plan.action. "Buy now %" = the starter tranche for SCALE_IN/STARTER_PROBE (a real number ≤ the CRO ceiling), "0%" for STAGE_ON_TRIGGER/WATCH, "—" for PASS/NO_NEW_RISK. ` +
  `"Add trigger" = the dated/price event for the next tranche. "Dissent" = minority lens + ≤6-word gist, or "unanimous (FLAG)".\n` +
  `- A "Watch next" line: names to re-test + the dated catalyst that flips them.\n` +
  `- A "Coverage" line: which desks were empty/FAILED (one phrase) if any.\n` +
  `NO verbatim quotes, NO per-name prose in the brief. One screen.\n\n` +

  `=== FILE 2 — THE FULL MEMO (\`reports/hedge-fund-committee-<date>.md\`) — the audit trail ===\n` +
  `Start with "# INVESTMENT COMMITTEE MEMO — <date>". Rules:\n` +
  `- State the CEILING caveat ONCE in the header (sizes are ceilings for a NEW position assuming ZERO ` +
  `current exposure, 10% single-name cap; owner verifies vs the real book). Do NOT repeat it per name.\n` +
  `- ${BOOK_NOTE.split('\n')[0]}\n` +
  `- §Regime & Fed. §Desk-coverage table (one row/desk: status ran/empty/FAILED + n + gap); call empty ` +
  `crypto/political/news desks a coverage hole, not "nothing to buy". Dead desks: ${JSON.stringify(deadDesks)}.\n` +
  `- Per name: plan.action, the STAGED PLAN (buy-now tranche % + each add-trigger + the CRO ceiling), the ownership split (own=YES count / total) vs the timing split, and the invalidation. Make the staged entry concrete and numeric.\n` +
  `- DISSENT (code-enforced \`minority\` — NOT your choice): quote the lens + reason VERBATIM for any name we are BUYING (SCALE_IN/STARTER_PROBE/STAGE_ON_TRIGGER) — the owner must see the strongest bear case before committing capital. For WATCH/PASS, compress the minority (the overridden advocate) to ONE line. Never drop, average, or substitute it. If minority is null, say "unanimous — FLAG, not comfort".\n` +
  `- Convergence: n_sources per name; FLAG any flow_only name "13F/congress only — 30-45d lagged". If THIN WEEK, say so up top.\n` +
  `- §"WHAT WE COULD NOT VERIFY": list ONLY items NOT already in the desk-coverage table's gap column (no duplication). If all covered there, write "See coverage table." and stop.\n` +
  `- 13F lag 45d, STOCK Act 30-45d — state once.\n\n` +

  `DELIVERABLE STEPS:\n` +
  `1. bash \`date -u +%F\` for <date>. 2. \`mkdir -p reports\`. 3. Write BOTH files with the Write tool. ` +
  `4. Read back the first 3 lines of each to confirm.\n` +
  `Then return EXACTLY these two lines first:\n` +
  `"BRIEF SAVED: reports/hedge-fund-brief-<date>.md"\n` +
  `"REPORT SAVED: reports/hedge-fund-committee-<date>.md"\n` +
  `followed by the BRIEF markdown only (not the full memo). No preamble.`,
  { label: 'cio-memo', phase: 'Decision' }
)

// memo text leads with "BRIEF SAVED:" + "REPORT SAVED:" — the two durable artifacts the owner opens.
const briefPath = (memo.match(/BRIEF SAVED:\s*(\S+)/) || [])[1] || null
const reportPath = (memo.match(/REPORT SAVED:\s*(\S+)/) || [])[1] || null
const plans = decided.map(d => ({ ticker: d.ticker, action: d.plan.action, own: `${d.plan.own_yes}/${d.plan.n}`, gate: d.risk?.gate }))
return { regime: macro?.summary, coverage, dead_desks: deadDesks, thin_week: thinWeek, plans, convergence: TOP, brief_path: briefPath, report_path: reportPath, memo }
