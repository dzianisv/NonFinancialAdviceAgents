// Regression guard for the hedge-fund-committee discovery GATE contract.
// The fatal SanDisk bug: a single-source NARRATIVE name (SNDK, conviction 3) was filtered out before the
// panel. This test pins the contract so it can never silently regress.  Run: `node test_gate_contract.mjs`
//
// Constraint: the workflow runs in a sandbox that forbids importing local modules, so the gate predicate
// cannot be shared via `import` and the test cannot execute the real function directly. Rather than fragile
// regex-eval of the whole predicate, this test does two robust things:
//   PART A — SOURCE INVARIANT (the real regression guard): assert the actual workflow source still contains
//            the narrative clause and that NARRATIVE_DESKS still includes the news seats. Removing the
//            narrative clause (the exact SanDisk regression) makes this FAIL.
//   PART B — BEHAVIOURAL CONTRACT: a small mirror of the predicate documents expected admit/drop outcomes.
//            (Clearly a mirror — Part A is what binds it to the real code.)

import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const here = dirname(fileURLToPath(import.meta.url))
const WORKFLOW = resolve(here, '../../.agents/workflows/hedge-fund-committee.workflow.js')
const src = readFileSync(WORKFLOW, 'utf8')
let failed = 0
const check = (ok, msg) => { console.log(`${ok ? 'PASS' : 'FAIL'}: ${msg}`); if (!ok) failed++ }

// ── PART A — SOURCE INVARIANT (binds the test to the real workflow code) ─────
const NEWS_SEATS = ['news-ft', 'news-wsj', 'news-tradepress', 'news-reddit']
const ndMatch = src.match(/const NARRATIVE_DESKS = new Set\(\[([^\]]*)\]\)/)
check(!!ndMatch, 'workflow defines a NARRATIVE_DESKS set')
if (ndMatch) {
  const nd = new Set(ndMatch[1].split(',').map(s => s.trim().replace(/['"]/g, '')).filter(Boolean))
  for (const seat of NEWS_SEATS) check(nd.has(seat), `NARRATIVE_DESKS includes '${seat}'`)
}
// The narrative clause MUST appear inside the `gated` filter — this is the line whose removal caused the
// SanDisk miss. A simple substring check is robust where full-expression parsing is brittle.
const gateRegion = (src.match(/const gated = clustered\.filter\(c =>[\s\S]{0,400}?if \(gated\.length\)/) || [''])[0]
check(/c\.sources\.some\(s => NARRATIVE_DESKS\.has\(s\)\)/.test(gateRegion),
  'gate admits a single-source NARRATIVE name (c.sources.some(... NARRATIVE_DESKS ...) clause present)')
check(/c\.n_sources >= 2/.test(gateRegion) && /c\.max_conviction >= 4/.test(gateRegion),
  'gate still also admits convergence (n_sources>=2) and high conviction (>=4)')

// ── PART B — BEHAVIOURAL CONTRACT (mirror of the predicate, for documentation) ──
const NARRATIVE_DESKS = new Set(NEWS_SEATS)
const gateMirror = (c) => c.n_sources >= 2 || c.max_conviction >= 4 || c.sources.some(s => NARRATIVE_DESKS.has(s))
const cases = [
  ['SNDK-class single-source narrative (the fatal case)', { n_sources: 1, max_conviction: 3, sources: ['news-ft'] }, true],
  ['narrative from any feed seat', { n_sources: 1, max_conviction: 1, sources: ['news-reddit'] }, true],
  ['cross-source convergence', { n_sources: 2, max_conviction: 2, sources: ['equity-dips', 'institutional-flows'] }, true],
  ['high-conviction single dip', { n_sources: 1, max_conviction: 4, sources: ['equity-dips'] }, true],
  ['low-signal single dip (correctly excluded)', { n_sources: 1, max_conviction: 2, sources: ['equity-dips'] }, false],
]
for (const [name, cand, mustPass] of cases) check(gateMirror(cand) === mustPass, `behaviour: ${name}`)

if (failed) { console.error(`\n${failed} GATE CONTRACT VIOLATION(S) — a discovered narrative name could be filtered before the panel (the SanDisk failure mode).`); process.exit(1) }
console.log('\nGATE CONTRACT OK — verified against the real workflow source (Part A) + behaviour (Part B).')
