# Hierarchy: PANEL (Investor Panel)

## When to use
Two-layer decision chain: a plain, persona-free research desk assembles the facts, then six named investor
seats each read the *whole* briefing and vote independently. Best for names where you want the historical
"how would Buffett / Druckenmiller / Dalio / Alden / Graham / Hunt actually read this" lens made explicit and
auditable, rather than folded into one CIO's prose. Candidate hierarchy — unscored, eval pending (see the
table in `SKILL.md`).

## Key mechanism
**Layer 1 = research desk, no personas.** The briefing arrives pre-assembled (Steps 0.8/1 of `SKILL.md`:
`fundamentals.py` + TradingView + narrative/news + smart-money flows + sell-side consensus + macro regime).
This hierarchy does not build that briefing and does not run a fact-gathering seat of its own — it consumes
what already exists in `$RUN_DIR/{TICKER}/data_package.json` and the seat briefs from Step 0.8/1. If those
briefs were not produced this run, go back and produce them first; do not let a Layer-2 seat improvise facts.

**Layer 2 = the Investor Panel.** Six named investor seats read the **full** briefing (never a slice) and
vote **independently and in parallel** — no seat sees another seat's vote before committing its own. A
deterministic conviction-weighted quorum recipe (not a CIO's prose judgment) turns the six votes into a
**CHAIN READ**. The printed **ACTION** is always the Step 0.82 scorecard's verbatim output — see §AUTHORITY.

---

## Pre-Panel: Briefing sections (Layer 1, reused — do not rebuild)

The briefing has **N = 6 sections**. Each is either populated with real, this-run evidence or `DARK`
(`INSUFFICIENT_DATA` / `[UNAVAILABLE]` / no real fetch happened):

| # | Section | Source |
|---|---|---|
| 1 | Fundamentals | `fundamentals.py` (yfinance) — valuation, quality, growth, drawdown |
| 2 | Technicals | TradingView `data_get_study_values` (RSI/BB/MACD/Volume) + MA levels, or DEGRADED_TECH trend-only |
| 3 | Narrative / News | web_fetch + `feeds/wsj.ts` / `feeds/ft.ts` — theme phase, catalysts |
| 4 | Smart-Money / Flows | insider (Form 4 via finviz), institutional ownership, 13F deltas |
| 5 | Sell-side / Consensus | analyst rating, PT dispersion, momentum (2-of-3 rule) |
| 6 | Macro / Regime | Step 0.9 macro-regime paragraph — rates, USD, liquidity backdrop |

Assemble these into one shared `briefing_package.md` per ticker (mirrors `crypto-advisor`'s Phase-1 → Phase-2
handoff) and pass the **whole document** to every seat. Count how many of the 6 are DARK — this count feeds
the DATA-COVERAGE GATE below.

---

## Layer 2 — Investor Panel seats

| Seat | Loads skill | Lens |
|---|---|---|
| **Buffett** | `investor-warren-buffett` | Quality / moat / owner-earnings — durable competitive advantage, pricing power |
| **Druckenmiller** | `investor-stanley-druckenmiller` | Trend / liquidity / timing — is the tape confirming, is liquidity supportive |
| **Dalio** | `investor-ray-dalio` | Cycle / regime / positioning — where are we in the debt/growth cycle, who's crowded |
| **Alden** | `investor-lyn-alden` | Monetary / fiscal / narrative — fiscal dominance, real rates, debasement backdrop |
| **Graham** | `investor-benjamin-graham` | Deep-value / margin-of-safety — downside protection at today's price |
| **Hunt** (protected dissent seat) | `research-lacy-hunt` | Deflation / debt-drag dissent — the standing adversary to the other five's growth/inflation framing |

**Hunt is a protected seat, not a tie-breaker.** It runs on every ticker regardless of how aligned the other
five look, and its verbatim reasoning is never averaged into silence (see §Quorum step, rule 3).

---

## Seat prompt — spawn all six in parallel, independently

**Hard rule (mandatory, print at the top of every seat's prompt): "Commit your OWN view before considering
any other seat."** Each seat is spawned as a separate subagent (`/model sonnet /effort high`) that receives
only the briefing package and its own lens skill — never another seat's vote. No cross-talk, no sequential
chaining, no seat is told what a prior seat said. Votes are never averaged into one blended read at the seat
level; averaging happens only in the deterministic quorum step, and only for OWN/TODAY leans, never for the
reasoning text.

**Investor seat subagent prompt — inject verbatim, fill `{placeholders}`:**

```
You are {SEAT NAME}, applying the {LENS} framework. Load the {SKILL} skill before answering. You are voting
on {TICKER} independently — you have not seen and must not guess at any other seat's vote. Commit your OWN
view before considering any other seat.

Read the FULL briefing package below (all 6 sections — do not skip any). Do not fetch new data; if a section
is DARK/INSUFFICIENT_DATA, say so — do not fill the gap from memory.

Before voting, NAME the single strongest piece of opposing evidence in the briefing (for a bearish lean: the
sell-side consensus/PTs, insider buys, bullish narrative items; for a bullish lean: the bear items) and engage
it in one line. A vote that never cites the opposing case is INVALID — the quorum step must reject and
respawn it.

OWN (worth owning 12–24mo, from your school's lens only): YES | NO
TODAY:
  - holdings path: {ADD | HOLD | TRIM | EXIT}
  - watchlist path: {BUY | WATCH | SKIP}
CONVICTION: HIGH | MED | LOW  ← how strongly THIS briefing supports YOUR school's read on THIS ticker, not
  generic confidence
REASON (≤3 lines, cite specific briefing numbers, tag every factual claim's provenance):
  [FROZEN] = a quant fact fixed in the briefing at Layer-1 assembly time (fundamentals.py / TradingView pull,
             same for every seat this run)
  [LIVE]   = a fact the briefing's Layer-1 desk itself web_fetched this run (news, filing, feed-script record)
  [MEM⚠]   = your own training-data recall, NOT present anywhere in the briefing — flag it; a vote resting
             solely on [MEM⚠] is weak evidence and must be named in DISSENT LOGGED if it drives the vote
  Every non-[FROZEN] claim in your vote carries inline outlet+date from the briefing (e.g. "CNBC 2026-03-05"),
  not just a tag.
INVALIDATION: {one sentence — what specific fact, if it changed, would flip your OWN or TODAY call}
  Invalidation items MUST be facts that would prove the current thesis/action WRONG (e.g. for a TRIM: FCF
  stabilizing, a favorable ruling, flows turning positive). A condition that reinforces or escalates the
  existing action is NOT an invalidation — direction-check each item before printing.
  For a HOLD or TRIM vote specifically: the invalidation MUST be the bearish/downside condition that would
  prove the HOLD/TRIM thesis wrong (a price level breaking down, guidance cut, margin/FCF deterioration,
  covenant or ruling risk) — not a bullish upside condition. A bullish-only invalidation attached to a
  HOLD/TRIM vote is INVALID, same as a vote that never engaged the opposing evidence — the quorum step must
  reject and respawn it.

Briefing package: {FULL_BRIEFING_PACKAGE_MD}
```

**Hunt's seat gets two additional required fields** (the tail-stress + historical-analog mechanism, carried
over from the `bsc` hierarchy's Skeptic step — Hunt is this panel's standing adversary):

```
TAIL RISK: one specific, non-generic downside scenario if the deflation/debt-drag read is right. Probability
  (1–15%) and expected loss magnitude. No generic "macro deterioration."
PORTFOLIO TAIL STRESS (both numbers, no omissions):
  (a) -30% drawdown in {TICKER}: dollar impact at current weight = ${amount} ({weight}% × book × 0.30)
  (b) -50% worst case: dollar impact at current + proposed size = ${amount}
HISTORICAL ANALOG: one real case with a structurally identical setup (same debt/growth phase). Exact name,
  year, outcome — no fabricated cases. Tag provenance per the rule above.
```

Cache each vote: `echo '{seat_vote_json}' > "$RUN_DIR/{TICKER}/vote_{seat}.json"` (six files: `vote_buffett.json`,
`vote_druckenmiller.json`, `vote_dalio.json`, `vote_alden.json`, `vote_graham.json`, `vote_hunt.json`).

---

## Quorum step (deterministic recipe — not a CIO's judgment call)

1. **Weight each vote by conviction.** HIGH = 3, MED = 2, LOW = 1.
2. **Compute two leans, both directions:**
   - `own_lean = Σ(weight where OWN=YES) − Σ(weight where OWN=NO)`
   - `today_lean = Σ(weight where TODAY leans buy-side: ADD/BUY) − Σ(weight where TODAY leans sell-side: EXIT/TRIM/SKIP)`
     (HOLD/WATCH contribute 0 to `today_lean` — they are not an abstention from OWN, only from TODAY.)
3. **Hunt's dissent is never averaged away.** Regardless of what the weighted leans say, Hunt's OWN/TODAY
   vote and REASON print **verbatim** in the output block's DISSENT LOGGED field whenever Hunt's OWN or TODAY
   differs from the majority lean. This is a structural print requirement, not conditional on whether Hunt
   "loses" the weighting.
3a. **Echo-chamber check.** If all 6 seats agree, verify each engaged the opposing evidence (per the seat
    prompt's hard requirement). Unanimity without engagement = echo chamber, flag it in the output.
4. **Map the leans to CHAIN READ:**
   - **BUY-leaning / ADD-leaning** — `own_lean` clearly positive AND `today_lean` clearly positive AND no
     unrebutted HIGH-conviction dissent from Hunt.
   - **SPLIT** — `own_lean` and `today_lean` point different directions, or Hunt's HIGH-conviction dissent
     stands unaddressed.
   - **SELL-leaning / EXIT-leaning / TRIM-leaning** — both leans clearly negative.
   - **UNCERTAIN** — DATA-COVERAGE GATE fired (see §AUTHORITY) — do not manufacture a directional read from a
     briefing that was mostly dark.
5. **Show the math.** Print `QUORUM MATH` with the raw weights for **all six seats, no omissions** — this is
   what makes every seat's per-seat CONVICTION label mechanical, not decorative: each seat's HIGH/MED/LOW is
   the literal weight (3/2/1) that goes into the `own_lean`/`today_lean` sum below, e.g.:
   `own_lean = (Buffett HIGH+3) + (Druckenmiller MED+2) + (Dalio MED+2) + (Alden HIGH+3) + (Graham LOW+1) − (Hunt HIGH−3) = +8`.

Final CONVICTION (1–5, auditable, same clamp style as `bsc`'s CIO step) is **not** a separately-eyeballed
number — it is derived mechanically from the same `own_lean`/`today_lean` sums printed in `QUORUM MATH`
directly above, which are themselves built from all six seats' conviction weights per rule 1. No seat's
CONVICTION label is decorative: all six are already inside `own_lean`/`today_lean` before this step runs.
Hunt is the one seat that additionally gets a **named, standalone** adjustment on top of that shared
aggregate (the protected-dissent penalty below) — that is what makes Hunt's line look different in the
formula, not that the other five don't count.

Formula: start at 3; +1 if `own_lean` ≥ +6; +1 if `today_lean` and `own_lean` agree in sign; −1 if Hunt is
HIGH-conviction dissent; −1 if DATA-COVERAGE GATE capped the read; −1 if PEG > 2 or negative FCF yield in the
Fundamentals section. Clamp 1–5. When printing the final `CONVICTION: {N}/5` line in the output block, name
which terms fired (see Output shape) so the all-six-seats-to-one-number chain stays visible end to end.

---

## AUTHORITY (non-negotiable — matches Step 0.82 of `SKILL.md`, no override language anywhere in this file)

- **The printed ACTION is always the Step 0.82 scorecard's verbatim output.** This hierarchy's quorum produces
  a **CHAIN READ**, which is informational — a second, independently-computed opinion sitting next to the
  scorecard, never a replacement for it.
- **Divergence is logged, not resolved by prose.** When CHAIN READ disagrees with the scorecard ACTION, print
  `DISSENT LOGGED` naming exactly which seats diverged and why (Hunt's dissent per rule 3 above always
  appears here when applicable, whether or not it drove the disagreement).
- **Reconcile note (mandatory whenever CHAIN READ ≠ ACTION).** Print one line immediately under `CHAIN READ`:
  `(informational only; ACTION is the binding scorecard call — divergence from CHAIN READ is expected, not an
  error)`. This line is required every time the two point different directions (e.g. `ACTION: HOLD` next to
  `CHAIN READ: TRIM-leaning`) — without it, a reader (or judge) sees the two lines stacked with no bridge and
  reads it as an unreconciled internal contradiction rather than the intended second opinion. This is a
  wording note only — it does not grant this hierarchy any authority to change, soften, or re-derive ACTION;
  ACTION still comes verbatim from Step 0.82, unmodified. Omit the line only when CHAIN READ and ACTION agree
  in direction. Example:
  ```
  ACTION: HOLD
  CHAIN READ: TRIM-leaning
  (informational only; ACTION is the binding scorecard call — divergence from CHAIN READ is expected, not an
  error)
  ```
- **POLICY NOTE** carries any documented caller-mandate clamp applied to the ACTION this run (e.g. "caller
  flagged hold-only — TRIM means rotate, not exit to cash"), or `"n/a"`.
- **The only two sanctioned ACTION modifiers are (a) a documented caller-mandate clamp (POLICY NOTE) and
  (b) the Risk Manager's hard gate below — which may only downgrade a BUY/ADD, never upgrade any ACTION.**
  No seat vote, no CHAIN READ, and no quorum math may itself change the printed ACTION.
- **DATA-COVERAGE GATE:** count how many of the 6 briefing sections (§Pre-Panel) are DARK this run. If **≥2 of
  6 are dark**, CHAIN READ is capped at `HOLD` (holdings path) or `WATCH` (watchlist path) regardless of what
  the weighted leans alone would otherwise produce, and the output block prints `DATA COVERAGE: N/M` (e.g.
  `DATA COVERAGE: 4/6 — Smart-Money and Sell-side dark this run`). This mirrors the `bsc` hierarchy's
  DATA-COVERAGE GATE and the crypto-advisor UNCERTAIN → HOLD gate: thin briefs must not manufacture a
  directional verdict.

---

## Step C: Risk Manager (hard gate, only fires when ACTION = BUY/ADD)

Identical mechanism to the `bsc` hierarchy's Risk Manager — run inline (not a subagent), skip entirely when
ACTION is WATCH/SKIP/HOLD/TRIM/EXIT/PASS.

```
You are the Risk Manager for {TICKER} (ACTION: {BUY|ADD}, conviction: {N}/5). Check constraints only — not
thesis quality. First breach blocks, no override.
Rule 1: Position ≥ 10% of book → BLOCKED: "concentration cap — no ADD until trimmed below 8%."
Rule 2: Primary factor group ≥ 25% of book → BLOCKED: "factor concentration limit."
Rule 3: Cash < $2,000 → BLOCKED: "insufficient cash for minimum position."
Rule 4: Conviction ≤ 2/5 → BLOCKED: "below minimum conviction threshold."
If no rule fires → APPROVED.
Position size (APPROVED): conviction × 2% × total_book, capped at (10% − current_weight).

Output:
STATUS: {APPROVED | BLOCKED}
POSITION SIZE: {$amount, % of book} or "n/a"
REASON: {rule fired, or "all constraints clear — factor headroom: {pct}%"}
```

**Verdict flow after Risk Manager:** if APPROVED → ACTION stands; if BLOCKED → ACTION downgrades to
WATCH/HOLD (the sanctioned downgrade from §AUTHORITY). Log the block reason in the output block.

Cache output: `echo '{risk_json}' > "$RUN_DIR/{TICKER}/seat_risk.json"`

---

## Output shape

```
ACTION: {BUY|WATCH|SKIP|PASS}   or {ADD|HOLD|TRIM|EXIT}   — Step 0.82 scorecard verbatim, or the Risk Manager's downgrade
CHAIN READ: {BUY-leaning|SPLIT|SELL-leaning|UNCERTAIN}  or {ADD-leaning|SPLIT|EXIT-leaning|UNCERTAIN} — quorum's own read, informational only
{print ONLY when CHAIN READ's direction ≠ ACTION's direction:}
(informational only; ACTION is the binding scorecard call — divergence from CHAIN READ is expected, not an error)

SEAT VOTES
 Buffett (Quality/moat)         : OWN {YES/NO}  TODAY {ADD/HOLD/TRIM/EXIT}  CONV {H/M/L} — {≤3-line reason w/ provenance tags}
 Druckenmiller (Trend/timing)   : OWN {YES/NO}  TODAY {...}  CONV {H/M/L} — {...}
 Dalio (Cycle/regime)           : OWN {YES/NO}  TODAY {...}  CONV {H/M/L} — {...}
 Alden (Monetary/fiscal)        : OWN {YES/NO}  TODAY {...}  CONV {H/M/L} — {...}
 Graham (Deep-value/MoS)        : OWN {YES/NO}  TODAY {...}  CONV {H/M/L} — {...}
 Hunt (Deflation dissent)       : OWN {YES/NO}  TODAY {...}  CONV {H/M/L} — {...} [TAIL RISK + STRESS + ANALOG]
 (every CONV above is a real weight, not decorative — each feeds QUORUM MATH below per rule 1)

QUORUM MATH: own_lean = {sum shown per seat, all six, e.g. "(Buffett HIGH+3) + (Druckenmiller MED+2) + ... − (Hunt HIGH−3)"} = {total} | today_lean = {sum shown per seat, all six} = {total}
DISSENT LOGGED: {Hunt's verbatim dissent when applicable, and any CHAIN-READ-vs-ACTION disagreement, naming the diverging seats}
POLICY NOTE: {caller-mandate clamp applied, or "n/a"}
CONVICTION: {1–5}/5 — base 3 {+1 own_lean≥+6 if fired} {+1 leans agree in sign if fired} {−1 Hunt HIGH dissent if fired} {−1 gate capped if fired} {−1 PEG/FCF red flag if fired} — derived from the own_lean/today_lean sums above, i.e. all six seats' weights, not from Hunt's line alone
Entry zone  : ${low}–${high}
Trigger     : {bar-close above/below X on timeframe Y}
Stop        : ${level} ({basis})
Sizing      : {Risk Manager APPROVED $X (N% book) | BLOCKED: reason | N/A (not BUY/ADD)}
Invalidation: {3 falsifiable conditions — thesis-break, not just the price stop. Each MUST be a fact that
  would prove the current thesis/action WRONG (e.g. for a TRIM: FCF stabilizing, a favorable ruling, flows
  turning positive) — a condition that reinforces or escalates the existing action is NOT an invalidation.
  For ACTION = HOLD or TRIM specifically: the FIRST listed condition MUST be the bearish/thesis-wrong
  condition (a price level or fundamental trigger that proves the HOLD/TRIM wrong) — do not lead with a
  bullish upside condition and do not bury the bearish one inside "Portfolio tail stress" / TAIL RISK below.
  TAIL RISK (Hunt's section) is a separate, additional disclosure and is never a substitute for a bearish
  condition in this primary Invalidation slot.}
Portfolio tail stress: {Hunt's -30%/-50% dollar-impact numbers at current weight}
DATA COVERAGE: {N}/6 briefing sections had real evidence this run — {name any DARK section} | GATE: {capped at HOLD/WATCH | not triggered}
```

Execution entry: one P0/P1/P2/P3 row in the run's final EXECUTION TABLE (Step 3.6 of `SKILL.md`).

> Source: crypto-advisor's Investment Panel (Phase 2) — six independent investor-school votes on one shared,
> pre-assembled briefing, synthesized by conviction (HIGH=3/MED=2/LOW=1) rather than headcount, with a
> CORE-lens dissent that caps the verdict at SPLIT rather than being outvoted. Surowiecki, *Wisdom of Crowds*
> (2004) — independent judgment before aggregation beats sequential/cross-talking deliberation, which is why
> every seat commits before seeing any other seat's vote. Bridgewater ILC design principle — a standing
> institutional adversary (here, Hunt) whose dissent cannot structurally be averaged into silence.
