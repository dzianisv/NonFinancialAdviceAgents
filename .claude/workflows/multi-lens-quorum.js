export const meta = {
  name: 'multi-lens-quorum',
  description: 'Convene N independent analyst lenses on ONE judgment call; synthesize consensus without averaging away dissent.',
  whenToUse: 'Reversible-expensive investment/trading judgment calls where 4-7 lenses would genuinely disagree (buy/sell/hold, allocation, cadence, timing). Not for facts/lookups/code.',
  phases: [
    { title: 'Convene', detail: 'one context-firewall subagent per lens, identical facts, fixed-shape verdict' },
    { title: 'Synthesize', detail: 'overlap consensus + preserved dissent with flip-triggers (no averaging)' },
  ],
}

const SKILLS_DIR = '/Users/engineer/workspace/backtest/.agents/skills'

// args may arrive as an object OR a JSON string depending on the caller — normalize.
let A = args
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }
A = A || {}

// args: { question, facts, lenses?, date? }
const question = A.question || 'Should I buy/hold/sell — convene the quorum.'
const facts = A.facts || '(no facts supplied)'
const date = A.date || 'undated'

// Default 5-lens set chosen to DISAGREE across return-drivers, incl. a value-dissent seat (Graham).
const DEFAULT_LENSES = [
  'analyse-systematic-trading', // Carver — discipline/sizing/cost speed limit
  'investor-benjamin-graham',  // value / "is this even an investment" DISSENT seat
  'investor-lyn-alden',        // structural-inflation / scarce-asset bull
  'research-morgan-housel',    // behavioral guardrail / don't-blow-up
  'investor-stanley-druckenmiller', // liquidity-driven tactician / timing & sizing
]
let lenses = (Array.isArray(A.lenses) && A.lenses.length) ? A.lenses : DEFAULT_LENSES
if (lenses.length < 4) throw new Error(`quorum needs >=4 divergent lenses; got ${lenses.length}`)

const VERDICT = {
  type: 'object', additionalProperties: false,
  properties: {
    lens: { type: 'string' },
    verdict: { type: 'string' },
    conviction: { type: 'string', enum: ['low', 'med', 'high'] },
    reasoning: { type: 'string' },
    what_would_change_my_mind: { type: 'string' },
    blind_spot: { type: 'string' },
  },
  required: ['lens', 'verdict', 'conviction', 'reasoning', 'what_would_change_my_mind', 'blind_spot'],
}

phase('Convene')
const verdicts = (await parallel(lenses.map(lens => () =>
  agent(
`Read ONLY this lens and judge through ONLY it:
  ${SKILLS_DIR}/${lens}/SKILL.md
  (load the relevant references/ file before any load-bearing claim)

SHARED FACTS (identical for every seat — do not add or assume others):
${facts}

THE ONE QUESTION:
${question}

Return ONLY the fixed shape, terse, grounded in THIS lens (cite its framework/numbers).
Do NOT bring in other authors/frameworks. Stay in this one lens. You are a context
firewall — do not echo the source material. Set the "lens" field to "${lens}".`,
    { label: `lens:${lens}`, phase: 'Convene', schema: VERDICT }
  )
))).filter(Boolean)

if (verdicts.length < 4) throw new Error(`only ${verdicts.length} lenses returned; need >=4 for a quorum`)
log(`${verdicts.length} verdicts: ${verdicts.map(v => `${v.lens}=${v.verdict}(${v.conviction})`).join(' | ')}`)

phase('Synthesize')
const SYNTH = {
  type: 'object', additionalProperties: false,
  properties: {
    consensus: { type: 'string' },
    unanimous_kills: { type: 'array', items: { type: 'string' } },
    dissent: {
      type: 'array', items: {
        type: 'object', additionalProperties: false,
        properties: { lens: { type: 'string' }, view: { type: 'string' }, conviction: { type: 'string' }, flip_trigger: { type: 'string' } },
        required: ['lens', 'view', 'conviction', 'flip_trigger'],
      },
    },
    high_conviction_minority: { type: 'string' },
    false_consensus_flag: { type: 'string' },
    decision: { type: 'string' },
    rerun_if: { type: 'string' },
  },
  required: ['consensus', 'unanimous_kills', 'dissent', 'high_conviction_minority', 'false_consensus_flag', 'decision', 'rerun_if'],
}

const synthesis = await agent(
`You are the quorum synthesizer. Apply the multi-lens-quorum synthesis rules — DO NOT AVERAGE.
Question (${date}): ${question}

Verdicts (JSON):
${JSON.stringify(verdicts, null, 2)}

Rules:
- consensus = the OVERLAP across lenses that barely share a vocabulary (NOT the average/blend).
- unanimous_kills = options every seat rejects.
- dissent = each minority view: who holds it, conviction, and the SPECIFIC trigger that would flip
  the majority toward it. Dissent is parked, never deleted.
- high_conviction_minority = surface any lone HIGH-conviction dissenter explicitly (it often names the
  real risk); "none" if there isn't one. Never let it be silently outvoted by mediums.
- false_consensus_flag = note if the "agreement" is really correlated lenses counted twice; else "none".
- decision = the call, which lens(es) it honors, which minority is parked and why (with un-park trigger).
- rerun_if = what change in facts forces a re-run.`,
  { label: 'synthesize', phase: 'Synthesize', schema: SYNTH }
)

return { date, question, lenses, verdicts, synthesis }
