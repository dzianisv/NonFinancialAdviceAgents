export const meta = {
  name: 'trend-stock-research',
  description: 'Research-first trend-stock screen: prescreen -> parallel journalism reading -> non-obvious beneficiary mapping -> 3-question skeptic filter -> rank + route to multi-lens-quorum (nominate only, never auto-trade).',
  whenToUse: 'Find trendy/emerging stocks before the move; "what should I buy", "next NVDA/SanDisk", "what is waking up", weekly trend watchlist.',
  phases: [
    { title: 'Prescreen', detail: 'run emerging_scan.py -> hot themes (WHERE to read, not picks)' },
    { title: 'Read', detail: 'one subagent per theme x source (SA/WSJ/FT/EDGAR), facts only' },
    { title: 'Map', detail: 'synthesize findings -> candidates + non-obvious beneficiary chain' },
    { title: 'Skeptic', detail: 'one subagent per candidate: 3-question hard filter, most die' },
    { title: 'Rank', detail: 'rank survivors -> output table + killed-list + route to quorum' },
  ],
}

const REPO = '/Users/engineer/workspace/backtest'
const SCAN = `${REPO}/.agents/skills/trend-stock-research/scripts/emerging_scan.py`
const PY = '/Users/engineer/.venv/bin/python3'

// args may arrive as an object OR a JSON string depending on the caller — normalize.
let A = args
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }
A = A || {}

// args: { prompt, context?, date?, themes?, sources? }
const prompt = A.prompt || 'Find non-obvious emerging trend stocks right now.'
const context = A.context || ''
const date = A.date || 'today'
const N_THEMES = A.themes || 3
const SOURCES = (Array.isArray(A.sources) && A.sources.length) ? A.sources : ['Seeking Alpha', 'Wall Street Journal', 'Financial Times', 'SEC EDGAR']

phase('Prescreen')
const THEMES = {
  type: 'object', additionalProperties: false,
  properties: {
    scanner_output: { type: 'string' },
    hot_themes: {
      type: 'array', items: {
        type: 'object', additionalProperties: false,
        properties: { theme: { type: 'string' }, stage: { type: 'string' }, note: { type: 'string' } },
        required: ['theme', 'stage', 'note'],
      },
    },
  },
  required: ['scanner_output', 'hot_themes'],
}

const pre = await agent(
`Step 1 prescreen for trend-stock-research. Run the scanner and report HOT NEIGHBORHOODS only
(do NOT pick stocks here — the scan just says where to point the reading).
Run: ${PY} ${SCAN} --top 25
Also weave in any themes implied by this user context: ${context || '(none)'}
Return the scanner output (trimmed to the ranked table) + 3-5 hot themes, each with stage
(EARLY/MID/EXTENDED) and a one-line note. Most real winners will NOT appear here yet — that's expected.`,
  { label: 'prescreen', phase: 'Prescreen', schema: THEMES }
)

const themes = (pre.hot_themes || []).slice(0, N_THEMES)
if (!themes.length) throw new Error('prescreen produced no themes')
log(`themes: ${themes.map(t => `${t.theme}(${t.stage})`).join(', ')}`)

phase('Read')
const FINDING = {
  type: 'object', additionalProperties: false,
  properties: {
    theme: { type: 'string' }, source: { type: 'string' },
    demand_inflections: { type: 'array', items: { type: 'string' } },
    companies: { type: 'array', items: { type: 'string' } },
    bottleneck_quotes: { type: 'array', items: { type: 'string' } },
    non_obvious: { type: 'array', items: { type: 'string' } },
    citations: { type: 'array', items: { type: 'string' } },
    read_ok: { type: 'boolean' },
  },
  required: ['theme', 'source', 'demand_inflections', 'companies', 'bottleneck_quotes', 'non_obvious', 'citations', 'read_ok'],
}

const pairs = []
for (const t of themes) for (const s of SOURCES) pairs.push({ theme: t.theme, source: s })

const findings = (await parallel(pairs.map(p => () =>
  agent(
`You are a financial research READER. Read ${p.source} for "${p.theme}" and extract FACTS ONLY.

Reading paywalled sources: use a browser tool. Prefer the chrome-devtools MCP — navigate_page to the
article URL, then evaluate_script returning document.body.innerText (the user's Chrome has
bypass-paywalls, so FT/WSJ/SA/Bloomberg open). For SEC EDGAR use the free full-text API
(https://efts.sec.gov/LATEST/search-index?q=...). Do NOT use plain web fetch on FT/WSJ/SA — it paywalls.

Hunt for: demand inflections (a NEW use case creating demand supply can't meet), supply-chain
bottlenecks, capacity/backlog/shortage/sole-supplier language, and NON-OBVIOUS beneficiaries that
screen as a different sector.

For every source you cite, include >=1 EXTRACTABLE fact (a quote, number, date, or named person) in
citations[]. If you cannot extract a specific fact, you did not actually read it: set read_ok=false
and return empty arrays. Do NOT speculate, do NOT recommend. Facts only.`,
    { label: `read:${p.source.split(' ')[0]}/${p.theme}`.slice(0, 40), phase: 'Read', schema: FINDING }
  )
))).filter(Boolean).filter(f => f.read_ok)

log(`findings with real content: ${findings.length}/${pairs.length}`)
if (!findings.length) throw new Error('no source returned an extractable finding — browser/web access may be unavailable')

phase('Map')
const CANDIDATES = {
  type: 'object', additionalProperties: false,
  properties: {
    candidates: {
      type: 'array', items: {
        type: 'object', additionalProperties: false,
        properties: {
          ticker: { type: 'string' }, inflection: { type: 'string' }, bottleneck: { type: 'string' },
          obvious_leader: { type: 'string' }, non_obvious_why: { type: 'string' },
          sources: { type: 'array', items: { type: 'string' } },
        },
        required: ['ticker', 'inflection', 'bottleneck', 'obvious_leader', 'non_obvious_why', 'sources'],
      },
    },
  },
  required: ['candidates'],
}

const mapped = await agent(
`Step 3 — map demand inflections to NON-OBVIOUS beneficiaries. For each real inflection in the reader
findings below: (1) name the obvious leader (usually already priced), (2) the scarce INPUT that gates
the trend, (3) who CONTROLS that input (the find — oligopoly/monopoly share), (4) whether it hides in a
different sector (food co with a chip-substrate monopoly, steel co with a transformer-material monopoly).
Only include candidates GROUNDED in the findings' sources. Few good candidates beats many weak ones.

READER FINDINGS (JSON):
${JSON.stringify(findings, null, 2)}`,
  { label: 'map', phase: 'Map', schema: CANDIDATES }
)

const candidates = (mapped.candidates || [])
if (!candidates.length) throw new Error('no candidates mapped from findings')
log(`candidates: ${candidates.map(c => c.ticker).join(', ')}`)

phase('Skeptic')
const SKEPTIC = {
  type: 'object', additionalProperties: false,
  properties: {
    ticker: { type: 'string' },
    already_priced: { type: 'string' }, catalyst: { type: 'string' }, kills_it: { type: 'string' },
    verdict: { type: 'string', enum: ['KILLED', 'SURVIVED'] },
    confidence: { type: 'string', enum: ['HIGH', 'MED', 'LOW', ''] },
  },
  required: ['ticker', 'already_priced', 'catalyst', 'kills_it', 'verdict', 'confidence'],
}

const skeptic = (await parallel(candidates.map(c => () =>
  agent(
`Step 4 skeptic filter on ${c.ticker}. Answer ALL THREE with HARD thresholds — be ruthless, most die:
1) ALREADY PRICED? Pull real recent returns (yfinance/quote ok). >150% in 12mo => KILLED (no exceptions);
   >100% in 6mo => KILLED unless the catalyst is fully UNREALIZED; >50% above 200d MA => KILLED; at 52w
   highs with heavy coverage => watchlist only. State 12m return, 6m return, % vs 200d MA.
2) CONCRETE CATALYST + TIMELINE? A specific event in the next 1-4 quarters (price hike date, capacity
   online, contract award, spinoff, launch, regulatory deadline). "Eventually the market realizes" is
   NOT a catalyst -> drop.
3) WHAT KILLS IT? The single biggest specific risk. Can't name one -> you don't understand it -> drop.
Also: if ${c.ticker} is ALREADY publicly called part of this hot theme, it fails the non-obvious test.

Candidate context: inflection="${c.inflection}"; bottleneck="${c.bottleneck}"; obvious_leader="${c.obvious_leader}"; why_non_obvious="${c.non_obvious_why}".
Return the fixed shape with verdict KILLED or SURVIVED and a confidence for survivors.`,
    { label: `skeptic:${c.ticker}`, phase: 'Skeptic', schema: SKEPTIC }
  )
))).filter(Boolean)

const survivors = skeptic.filter(s => s.verdict === 'SURVIVED')
const killed = skeptic.filter(s => s.verdict === 'KILLED')
log(`skeptic: ${survivors.length} survived, ${killed.length} killed`)

phase('Rank')
const report = await agent(
`Step 5 — produce the final trend-stock-research output as MARKDOWN. Date: ${date}.
User asked: ${prompt}

SURVIVORS (JSON): ${JSON.stringify(survivors, null, 2)}
KILLED (JSON): ${JSON.stringify(killed, null, 2)}
CANDIDATE DETAIL (JSON): ${JSON.stringify(candidates, null, 2)}

Output EXACTLY these three parts:
1) Survivors table: | Ticker | Demand Inflection | Catalyst + When | Non-obvious Why | Already Priced? | Kills It | Confidence | Source |
2) Killed-list table: | Ticker | Failed On | Reason |
3) One closing line: "Routing [tickers] to multi-lens-quorum for buy/wait/late-chase judgment."
NOMINATE ONLY: do NOT make buy/sell calls, do NOT run the quorum, do NOT say what it would decide.`,
  { label: 'rank', phase: 'Rank' }
)

return { date, prompt, themes: themes.map(t => t.theme), n_findings: findings.length, n_candidates: candidates.length, survivors, killed, report }
