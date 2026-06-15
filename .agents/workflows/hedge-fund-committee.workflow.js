export const meta = {
  name: 'hedge-fund-committee',
  description: 'Hedge-fund org of agent-employees: analyst fan-out -> aggregate -> investor panel (independent vote + dissent) -> risk veto -> CIO decision memo. Reuses existing skills as employees. RECOMMEND-ONLY.',
  whenToUse: 'Weekly investment committee, or a deep decision on one ticker. The SLOW/deliberative tier (the daily cron dip/convergence alerts are the separate FAST tier).',
  phases: [
    { title: 'Analysts' },
    { title: 'Aggregate' },
    { title: 'Committee' },
    { title: 'Risk' },
    { title: 'Decision' },
  ],
}

// args (optional): { ticker: "GOOGL" } to deep-dive ONE name, else the full weekly sweep.
const FOCUS = (args && args.ticker) ? String(args.ticker).toUpperCase() : null

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
const reports = (await parallel(desks.map(d => () =>
  agent(d.prompt + ' Educational only, recommend-only. Mark anything you could not fetch [unverified] — NEVER fabricate a number, price, or headline.',
    { label: `analyst:${d.desk}`, phase: 'Analysts', schema: REPORT })
))).filter(Boolean)

// ── PHASE 2 — CHIEF OF STAFF: aggregate into ONE briefing packet ─────────────
// Plain code first (cheap, deterministic): cluster by ticker, count independent desks (convergence).
phase('Aggregate')
const byTicker = {}
for (const r of reports) for (const c of (r.candidates || [])) {
  const t = (c.ticker || '').toUpperCase().trim()
  if (!t) continue
  const e = (byTicker[t] ||= { ticker: t, desks: new Set(), notes: [] })
  e.desks.add(r.desk)
  e.notes.push(`${r.desk}: ${c.thesis} [${c.evidence}]`)
}
const clustered = Object.values(byTicker)
  .map(e => ({ ticker: e.ticker, n_desks: e.desks.size, desks: [...e.desks], notes: e.notes }))
  .sort((a, b) => b.n_desks - a.n_desks)
const macro = reports.find(r => r.desk === 'macro-regime' || r.desk === 'focus-research')
const TOP = clustered.slice(0, FOCUS ? 1 : 5)
log(`Aggregated ${clustered.length} names; convergence top: ${TOP.map(t => `${t.ticker}(${t.n_desks} desks)`).join(', ') || 'none'}`)
if (!TOP.length) return { regime: macro?.summary, note: 'No candidates surfaced this cycle. No action.', reports }

// ── PHASE 3 — INVESTMENT COMMITTEE (panel) ───────────────────────────────────
// Each lens votes INDEPENDENTLY (parallel = no anchoring on peers). Dissent is preserved, never averaged.
phase('Committee')
const LENSES = [
  'analytics-warren-buffett', 'analytics-benjamin-graham', 'analytics-stanley-druckenmiller',
  'analytics-lyn-alden', 'analytics-lacy-hunt', 'fundamental-analysis',
]
const judged = await parallel(TOP.map(cand => () =>
  parallel(LENSES.map(lens => () =>
    agent(
      `Apply ONLY the /${lens} lens to: BUY/ADD/HOLD/TRIM/SELL ${cand.ticker}? ` +
      `Macro backdrop: ${macro?.summary || '[unknown]'}. ` +
      `Why it surfaced (${cand.n_desks} independent desks): ${cand.notes.join(' | ')}. ` +
      `Commit your OWN verdict before considering any other lens. Give verdict, conviction 1-5, one reason ` +
      `grounded in a real fact, the invalidation trigger, and your lens's structural blind spot. Recommend-only.`,
      { label: `vote:${cand.ticker}:${lens.replace('analytics-', '')}`, phase: 'Committee', schema: VOTE })
      .then(v => ({ lens, ...v }))
  )).then(votes => ({ ...cand, votes: votes.filter(Boolean) }))
))

// ── PHASE 4 — RISK (CRO holds the binding veto + sizing) ─────────────────────
phase('Risk')
const risked = await parallel(judged.filter(Boolean).map(j => () =>
  agent(
    `You are the CRO. Apply /risk-management to a proposed position in ${j.ticker}. ` +
    `Regime: ${macro?.summary || '[unknown]'}. Committee votes: ${JSON.stringify(j.votes.map(v => ({ l: v.lens, vd: v.verdict, c: v.conviction })))}. ` +
    `VETO if: RISK_OFF regime, or this would take any name >10% of book, or sector already concentrated. ` +
    `Else PASS with a max size (% of book). Deterministic risk discipline, not opinion.`,
    { label: `risk:${j.ticker}`, phase: 'Risk', schema: RISK })
    .then(risk => ({ ...j, risk }))
)).then(a => a.filter(Boolean))

// ── PHASE 5 — CIO writes ONE decision memo (mandatory dissent log) ────────────
phase('Decision')
const memo = await agent(
  `You are the PM/CIO. Write the INVESTMENT COMMITTEE MEMO from this packet.\n` +
  `REGIME/FED: ${macro?.summary || '[unknown]'}\n` +
  `CANDIDATES (votes + risk gate): ${JSON.stringify(risked)}\n\n` +
  `Rules:\n` +
  `- RECOMMEND-ONLY. Educational, not advice. Any actionable trade still requires the backtest gate + human approval.\n` +
  `- Per name: the committee decision (BUY/ADD/HOLD/TRIM/SELL/PASS), conviction, sizing (only if risk=PASS), invalidation trigger.\n` +
  `- MANDATORY DISSENT LOG: for every name, surface the strongest MINORITY view verbatim — never average dissent away. ` +
  `If Lacy Hunt (deflation) or any lens dissented, quote it. A unanimous panel is a flag, not a comfort.\n` +
  `- Note convergence (how many independent desks surfaced each name).\n` +
  `- A "WHAT WE COULD NOT VERIFY" section listing every [unverified] item and any desk that was rate-limited.\n` +
  `- 13F lag 45d, STOCK Act lag 30-45d — state it.\n` +
  `Format tight and skimmable.`,
  { label: 'cio-memo', phase: 'Decision' }
)

return { regime: macro?.summary, convergence: TOP, memo }
