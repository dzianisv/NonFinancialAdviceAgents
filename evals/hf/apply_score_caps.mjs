// DETERMINISTIC hard-cap layer for the hedge-fund-committee blind eval.
// The blind LLM judge produces a per-dimension score, but hard penalties must NOT depend on the judge
// remembering a rubric line — they are enforced HERE in code from the run's machine-readable output.
// The judge does the soft, nuanced scoring; this script applies the non-negotiable caps.
//
// Usage:
//   node apply_score_caps.mjs '<judgeJson>' '<runJson>'      (args)  OR  echo '{judge,run}' | node ... (stdin)
//   node apply_score_caps.mjs --selftest
//
// judgeJson = the judge's {score, ...}.  runJson = the workflow return {flagged_drops, plans, ...}.
// Prints {raw_score, final_score, caps_fired:[{cap, ceiling, reason}]}.

const ACTIONABLE = new Set(['SCALE_IN', 'STARTER_PROBE', 'STAGE_ON_TRIGGER'])

export function applyCaps(rawScore, run) {
  const caps = []
  const flagged = (run && run.flagged_drops) || []
  const plans = (run && run.plans) || []
  // CAP 1 — FLAGSHIP-EXCLUSION (the fatal one): a narrative/high-conviction name was discovered but never
  // reached the panel. Defeats the system's core purpose → hard ceiling 35 regardless of polish.
  if (flagged.length > 0) caps.push({ cap: 'FLAGSHIP_EXCLUSION', ceiling: 35, reason: `${flagged.length} discovered name(s) dropped before the panel: ${flagged.map(f => f.ticker).join(', ')}` })
  // CAP 2 — ALL-PASS: candidates reached the panel but NONE produced an actionable plan. The signature
  // "NO-machine" failure → ceiling 45.
  if (plans.length > 0 && !plans.some(p => ACTIONABLE.has(p.action))) caps.push({ cap: 'ALL_PASS', ceiling: 45, reason: `${plans.length} candidate(s) panelled, zero actionable (all PASS/WATCH/NO_NEW_RISK)` })
  const ceiling = caps.length ? Math.min(...caps.map(c => c.ceiling)) : 100
  const final = Math.min(Number(rawScore), ceiling)
  return { raw_score: Number(rawScore), final_score: final, caps_fired: caps }
}

function selftest() {
  const t = []
  const eq = (got, exp, name) => t.push([JSON.stringify(got) === JSON.stringify(exp), name, got])
  eq(applyCaps(88, { flagged_drops: [], plans: [{ action: 'SCALE_IN' }] }).final_score, 88, 'clean run unchanged')
  eq(applyCaps(88, { flagged_drops: [{ ticker: 'SNDK' }], plans: [{ action: 'SCALE_IN' }] }).final_score, 35, 'flagship drop caps to 35 even on a high raw score')
  eq(applyCaps(80, { flagged_drops: [], plans: [{ action: 'PASS' }, { action: 'WATCH' }] }).final_score, 45, 'all-PASS caps to 45')
  eq(applyCaps(30, { flagged_drops: [{ ticker: 'X' }], plans: [] }).final_score, 30, 'cap never RAISES a low score')
  eq(applyCaps(90, { flagged_drops: [{ ticker: 'X' }], plans: [{ action: 'PASS' }] }).final_score, 35, 'both caps → tightest (35) wins')
  let failed = 0
  for (const [ok, name, got] of t) { console.log(`${ok ? 'PASS' : 'FAIL'}: ${name}${ok ? '' : ` (got ${got})`}`); if (!ok) failed++ }
  if (failed) { console.error(`\n${failed} cap-logic failure(s)`); process.exit(1) }
  console.log('\nSCORE-CAP LOGIC OK')
}

async function readStdin() { let s = ''; for await (const c of process.stdin) s += c; return s.trim() }

if (process.argv[2] === '--selftest') { selftest() }
else {
  let judge, run
  if (process.argv[2] && process.argv[3]) { judge = JSON.parse(process.argv[2]); run = JSON.parse(process.argv[3]) }
  else { const all = JSON.parse(await readStdin()); judge = all.judge; run = all.run }
  const out = applyCaps(judge.score, run)
  console.log(JSON.stringify(out, null, 2))
  if (out.caps_fired.length) console.error(`\n⚠ HARD CAP(S) FIRED: ${out.caps_fired.map(c => `${c.cap}→${c.ceiling}`).join(', ')} — judge's ${out.raw_score} capped to ${out.final_score}.`)
}
