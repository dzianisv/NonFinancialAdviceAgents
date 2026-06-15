export const meta = {
  name: 'hedge-fund-committee',
  description: 'Find the next stocks to BUY. A hedge-fund org of agent-employees DISCOVERS candidates (13F/congress/news/dips/regime), aggregates by conviction, an investor panel votes (independent + dissent), risk vetoes/sizes, and the CIO issues a ranked BUY list. Open-universe research — no ticker needed. RECOMMEND-ONLY.',
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
const VOTE = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['BUY', 'ADD', 'HOLD', 'TRIM', 'SELL', 'PASS'] },
    conviction: { type: 'integer', minimum: 1, maximum: 5 },
    reason: { type: 'string' },
    invalidation: { type: 'string' },
    blind_spot: { type: 'string' },          // mandatory: what this lens is structurally bad at
  },
  required: ['verdict', 'conviction', 'reason', 'invalidation', 'blind_spot'],
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
  { desk: 'news-narrative',      prompt: 'You are the news/narrative analyst. Run /trend-stock-research (broad). Surface the 3-5 themes journalists are converging on + specific tickers with a LIVE catalyst as candidates (evidence=a real headline you actually read). Never invent a headline.' },
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
// GATE before the expensive committee. The old top-5 fill admitted mechanical single-source dips with
// no convergence and no conviction — spending a 4-lens panel just to PASS on them and bloating the memo.
// A name EARNS the committee only if it shows convergence (n_sources>=2) OR a desk's high conviction
// (>=4). If nothing clears (a genuinely thin week), fall back to the 2 best single-source names as
// WATCH-ONLY rather than forcing a full slate — and tell the CIO it was thin so the memo says so.
let TOP, thinWeek = false
if (FOCUS) {
  TOP = clustered.slice(0, 1)
} else {
  const gated = clustered.filter(c => c.n_sources >= 2 || c.max_conviction >= 4)
  if (gated.length) {
    TOP = gated.slice(0, 7)
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
// 4 lenses on 4 ORTHOGONAL axes — no double-counting. (Was: Buffett + fundamental-analysis, which both
// key off "wide-moat name at a low multiple" → one value vote wearing two hats, which manufactured an ADD
// lean on every split. Replaced fundamental-analysis with superforecasting for a genuinely independent
// outside-view/base-rate axis.) Graham overlaps Buffett; Lyn-Alden overlaps Hunt — both still excluded.
const LENSES = [
  'analytics-warren-buffett',         // quality / business-value (moat + intrinsic value)
  'analytics-stanley-druckenmiller',  // timing / liquidity / tape
  'analytics-lacy-hunt',              // PROTECTED deflation / macro-dissent seat
  'superforecasting',                 // outside view / base rates / calibrated probability — NOT a value echo
]
const judged = await parallel(TOP.map(cand => () =>
  parallel(LENSES.map(lens => () =>
    agent(
      `Apply ONLY the /${lens} lens to: BUY/ADD/HOLD/TRIM/SELL ${cand.ticker}? ` +
      `Macro backdrop: ${macro?.summary || '[unknown]'}. ` +
      `Surfaced by ${cand.n_sources} source(s)${cand.flow_only ? ' — ALL are 30-45d LAGGED 13F/congress flows (context only, NOT a time-sensitive signal)' : ''} (note: sources may be correlated, not independent): ${cand.notes.join(' | ')}. ` +
      `Commit your OWN verdict before considering any other lens. Give verdict, conviction 1-5, one reason ` +
      `grounded in a real fact, the invalidation trigger, and your lens's structural blind spot. Recommend-only.`,
      { label: `vote:${cand.ticker}:${lens.replace('analytics-', '')}`, phase: 'Committee', schema: VOTE })
      .then(v => ({ lens, ...v }))
  )).then(votes => ({ ...cand, votes: votes.filter(Boolean) }))
))

// CODE-ENFORCED DISSENT: compute the strongest opposing voice to the modal action in JS — do NOT let
// the CIO turn decide whether dissent survives. This literal MUST be echoed in the memo.
const BULL = new Set(['BUY', 'ADD']), BEAR = new Set(['SELL', 'TRIM', 'PASS']), HOLD = new Set(['HOLD'])
function minorityVote(votes) {
  if (!votes || !votes.length) return null
  const bull = votes.filter(v => BULL.has(v.verdict))
  const bear = votes.filter(v => BEAR.has(v.verdict))
  const hold = votes.filter(v => HOLD.has(v.verdict))
  // HOLD is dissent against ANY action-majority (don't-add vs a bullish modal, don't-cut vs a bearish modal).
  // Old bug: HOLD was in neither set, so a 2-ADD/2-HOLD split returned null — losing the dissent on the
  // exact case the mechanism exists for. Now: opposing pool = everyone NOT on the modal action side.
  const bullish = bull.length >= bear.length
  const pool = bullish ? [...bear, ...hold] : [...bull, ...hold]
  if (!pool.length) return null   // genuinely unanimous on one action side → no dissent
  return pool.slice().sort((a, b) => b.conviction - a.conviction)[0]  // its most-convicted opposing voice
}
const withDissent = judged.filter(Boolean).map(j => ({ ...j, minority: minorityVote(j.votes) }))

// ── PHASE 4 — RISK (CRO holds the binding veto + sizing) ─────────────────────
phase('Risk')
const risked = await parallel(withDissent.map(j => () =>
  agent(
    `You are the CRO. Apply /risk-management to a proposed position in ${j.ticker}. ` +
    `Regime: ${macro?.summary || '[unknown]'}. Committee votes: ${JSON.stringify(j.votes.map(v => ({ l: v.lens, vd: v.verdict, c: v.conviction })))}. ` +
    `${BOOK_NOTE} ` +
    `VETO if: RISK_OFF regime, or this would take any name >10% of book, or (only if a book is supplied) the sector is already concentrated. ` +
    `Else PASS with a max size. Deterministic risk discipline, not opinion. Never fabricate a portfolio weight.`,
    { label: `risk:${j.ticker}`, phase: 'Risk', schema: RISK })
    .then(risk => ({ ...j, risk }))
)).then(a => a.filter(Boolean))

// ── PHASE 5 — CIO writes TWO artifacts: a 1-min BRIEF + the full audit MEMO ────
// The owner is a busy PM. The BRIEF is the 30-second read (what / how much / why). The full MEMO is the
// audit trail behind it. Length discipline: verbatim dissent ONLY on actionable verdicts; PASS/HOLD get
// one line. The CEILING caveat is stated ONCE. §"could not verify" must NOT repeat the coverage-table notes.
phase('Decision')
const memo = await agent(
  `You are the PM/CIO. Write TWO markdown files from this packet — a short BRIEF and a full MEMO.\n` +
  `REGIME/FED: ${macro?.summary || '[unknown]'}\n` +
  `DESK COVERAGE (ran/empty/FAILED + n candidates): ${JSON.stringify(coverage)}\n` +
  `THIN WEEK (no name cleared the n_sources>=2 OR conviction>=4 gate; the names below are WATCH-ONLY ` +
  `fallbacks, not earned candidates): ${thinWeek}\n` +
  `CANDIDATES (votes + risk gate): ${JSON.stringify(risked)}\n\n` +

  `=== FILE 1 — THE BRIEF (\`reports/hedge-fund-brief-<date>.md\`) — the busy-PM 1-minute read, MAX ~20 lines ===\n` +
  `Start with "# BUY BRIEF — <date>". Then:\n` +
  `- ONE bottom-line action line (e.g. "No initiations — defer to <event>" or "BUY X, watch Y,Z").\n` +
  `- ONE regime line: regime + exposure dial + the single biggest event risk.\n` +
  `- A DECISIONS TABLE, one row per name: | Ticker | Verdict | Size ceiling (%) | One-line why | Dissent |. ` +
  `Verdict ∈ BUY/ADD/HOLD/TRIM/SELL/PASS. Size only if risk=PASS, else "—". "Dissent" = the minority lens ` +
  `name + ≤6-word gist, or "unanimous (FLAG)" if minority is null.\n` +
  `- A "Watch next" line: the 1-2 names to re-test + the dated catalyst that flips them.\n` +
  `- A "Coverage" line: which desks were empty/FAILED (one phrase) if any.\n` +
  `NO verbatim quotes, NO per-name prose in the brief. It must fit one screen.\n\n` +

  `=== FILE 2 — THE FULL MEMO (\`reports/hedge-fund-committee-<date>.md\`) — the audit trail ===\n` +
  `Start with "# INVESTMENT COMMITTEE MEMO — <date>". Rules:\n` +
  `- State the CEILING caveat ONCE in the header (sizes are ceilings for a NEW position assuming ZERO ` +
  `current exposure, 10% single-name cap; owner verifies vs the real book). Do NOT repeat it per name.\n` +
  `- ${BOOK_NOTE.split('\n')[0]}\n` +
  `- §Regime & Fed. §Desk-coverage table (one row/desk: status ran/empty/FAILED + n + gap); call empty ` +
  `crypto/political/news desks a coverage hole, not "nothing to buy". Dead desks: ${JSON.stringify(deadDesks)}.\n` +
  `- Per name: decision, conviction, size (if risk=PASS), invalidation trigger.\n` +
  `- DISSENT (code-enforced \`minority\` field — NOT your choice): quote the lens + reason VERBATIM ONLY for ` +
  `names with an ACTIONABLE verdict (BUY/ADD/TRIM/SELL). For PASS/HOLD names, compress the minority to ONE ` +
  `line (lens + one-clause reason). Never drop it, never average it, never substitute your own. If minority ` +
  `is null, say "unanimous — FLAG, not comfort" in one line.\n` +
  `- Convergence: n_sources per name; FLAG any flow_only name "13F/congress only — 30-45d lagged". If THIN ` +
  `WEEK is true, say so up top: nothing cleared the gate, these are watch-only.\n` +
  `- §"WHAT WE COULD NOT VERIFY": list ONLY items NOT already in the desk-coverage table's gap column ` +
  `(do not duplicate it). If everything is already covered there, write "See coverage table." and stop.\n` +
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
return { regime: macro?.summary, coverage, dead_desks: deadDesks, thin_week: thinWeek, convergence: TOP, brief_path: briefPath, report_path: reportPath, memo }
