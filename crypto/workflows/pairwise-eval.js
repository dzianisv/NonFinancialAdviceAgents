export const meta = {
  name: 'pairwise-eval',
  description: 'Reliable blind SELECTION for the improvement loop: N judges decide which of two research reports (A vs B) better answers the question. Pairwise preference beats pointwise absolute scoring (which clusters/fluctuates). Position-randomized by judge index to kill position bias. Judges see only the reports. Returns the winner + vote split — the accept/reject signal the loop needs.',
  phases: [{ title: 'Compare', detail: 'N blind judges, A/B order swapped by index, majority vote' }],
}

// Why pairwise not pointwise: research (Zheng 2023 / AlpacaEval / MT-Bench) shows LLM judges are far more
// stable comparing two outputs than assigning an absolute score. Pointwise gave iter1=88/iter4=89 then
// 63.5/64 — no separation. Pairwise asks only "which is better", no calibrated scale to game.
const A_PATH = (args && args.a) || '/Users/engineer/workspace/backtest/crypto/eval/iter1.report.md'  // hypothesis: WORSE (news seat failed)
const B_PATH = (args && args.b) || '/Users/engineer/workspace/backtest/crypto/eval/iter4.report.md'  // hypothesis: BETTER (complete)
const QUESTION = (args && args.question) ||
  'BTC reached 65k$ from the drop to 61k$. I hold 30% in COIN. I don\'t have BTC direct exposure. Should I buy it today?'
const N = (args && args.judges) || 5

const VOTE_SCHEMA = {
  type: 'object',
  properties: {
    winner: { type: 'string', enum: ['FIRST', 'SECOND', 'TIE'] },  // which SHOWN report (position), not which file
    why: { type: 'string' },
    key_differentiator: { type: 'string' },
  },
  required: ['winner', 'why'],
}

const RUBRIC =
  `You are a blind, skeptical research grader. Two reports answer the SAME question. Decide which BETTER answers ` +
  `it — you do NOT assign scores, you pick the better one. Judge on: does it answer the question for THIS ` +
  `portfolio (buy AND sell), is the EVIDENCE actually present and sourced (a report that has its decision-` +
  `critical data — news/catalysts for a "buy today" timing question, ETF flows, on-chain — beats one that is ` +
  `missing it, even if the gap is honestly flagged), disagreement preserved, disciplined plan with invalidation, ` +
  `calibration. Penalize a report whose key evidence section DID NOT RUN. If genuinely indistinguishable, TIE — ` +
  `but prefer to pick. Return winner = FIRST or SECOND (the position shown) + the key differentiator.`

phase('Compare')
// Position-randomize deterministically by judge index (no Math.random in this runtime):
// even judges see A as FIRST; odd judges see B as FIRST. Map the positional vote back to the file.
const votes = (await parallel(Array.from({ length: N }, (_, j) => () => {
  const aFirst = (j % 2 === 0)
  const firstPath = aFirst ? A_PATH : B_PATH
  const secondPath = aFirst ? B_PATH : A_PATH
  const prompt = `${RUBRIC}\n\nQUESTION: ${QUESTION}\n\n` +
    `Use the Read tool on BOTH files (they are the only thing you may see), then decide:\n` +
    `FIRST report:  ${firstPath}\nSECOND report: ${secondPath}\n` +
    `Reply winner=FIRST or SECOND.`
  return agent(prompt, { label: `judge${j}-${aFirst ? 'A1st' : 'B1st'}`, phase: 'Compare', schema: VOTE_SCHEMA })
    .then(v => {
      if (!v) return null
      // translate positional winner -> file label A/B
      let pick = 'TIE'
      if (v.winner === 'FIRST') pick = aFirst ? 'A' : 'B'
      else if (v.winner === 'SECOND') pick = aFirst ? 'B' : 'A'
      return { judge: j, shown_a_first: aFirst, pick, why: v.why, diff: v.key_differentiator }
    })
}))).filter(Boolean)

const aWins = votes.filter(v => v.pick === 'A').length
const bWins = votes.filter(v => v.pick === 'B').length
const ties = votes.filter(v => v.pick === 'TIE').length
const winner = aWins > bWins ? 'A' : bWins > aWins ? 'B' : 'TIE'
log(`Pairwise: A(${A_PATH.split('/').pop()})=${aWins}  B(${B_PATH.split('/').pop()})=${bWins}  tie=${ties} -> winner ${winner}`)
return {
  winner, a_path: A_PATH, b_path: B_PATH, a_wins: aWins, b_wins: bWins, ties,
  // accept signal for the loop: candidate (B) is accepted iff it strictly wins the majority
  accept_B_over_A: bWins > aWins, votes,
}
