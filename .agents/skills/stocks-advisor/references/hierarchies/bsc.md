# Hierarchy: BSC (Bridgewater/Skeptic/CIO)

## When to use
Default hierarchy for US equity deep-dive analysis. Enforces edge articulation before spawning the 6-seat panel, then runs a mandatory adversarial Skeptic, a CIO synthesis, and a hard-gate Risk Manager on every BUY/ADD verdict.

## Key gate
Edge Articulation (Pre-Panel): if no specific INFORMATION/ANALYTICAL/TIMING/STRUCTURAL edge can be stated, the full panel is skipped — the name stays fundamentals-only with a `NO_EDGE` note in the signal table.

---

## Pre-Panel: Edge Gate

Before spawning the full 6-seat panel for a name, state the **EDGE HYPOTHESIS** in one sentence:

> "We believe {TICKER} is mispriced because [specific information or analytical insight] that the market has not yet priced."

Name the edge type:
- **INFORMATION EDGE** — data point not yet reflected (unreported earnings trend, filing detail, supply-chain signal from a web_fetch source)
- **ANALYTICAL EDGE** — correct interpretation of public data the consensus has misread (sector rotation, EPS quality, segment mix)
- **TIMING EDGE** — catalyst visible from feeds but not yet priced (specific date/event ≤ 2 quarters out)
- **STRUCTURAL EDGE** — index/ETF flow, spinoff, forced-seller, or spread compression creating a temporary mispricing

**Hard gate: if no edge can be stated → skip the full 6-seat panel for this name.** Keep it in the fundamentals-only screen (Step 0.8) and add it to WATCH with note `NO_EDGE — no identifiable information/analytical advantage; pass this run.`

No edge = no deep-dive. This is structural, not advisory. The edge statement goes into the output block header and must be re-checked at the CIO step — if the CIO cannot confirm the edge, PASS is the correct verdict.

> Source: Point72/SAC Capital operating model — "edge articulation" is the mandatory first check before any position research begins; ideas without a named edge are rejected before consuming analytical resources. Prevents narrative-driven trading and forces analysts to commit to WHY before HOW.

---

## Step A: Skeptic

The analyst panel is the proposal. The Skeptic is the mandatory institutional adversary — assigned, not volunteer. It runs on every ticker regardless of how bullish the panel looks. Never skip this step. Spawn as a subagent (`/model sonnet /effort high`).

**Skeptic subagent prompt — inject verbatim, fill `{placeholders}`:**

```
You are the Skeptic for {TICKER}. Your role is mandatory: find the strongest case AGAINST the consensus, even if you privately agree with the analysts.

GAP ANALYSIS: Name the single biggest blind spot across all 6 analyst verdicts — data they had but underweighted, or a dimension none of them checked.
TAIL RISK: Name one specific, non-generic downside scenario. Assign a probability (1–15%) and the expected loss magnitude if it fires. No generics like "macro deterioration."
HISTORICAL ANALOG: One real failed trade with a structurally identical setup — same thesis type, same narrative phase, same sentiment read. Exact company, year, outcome. No fabricated cases.

INVALIDATION CONDITIONS (all three required before any BUY advances):
  (a) {falsifiable condition — a specific price level, ratio, or filing event that proves the thesis wrong}
  (b) {falsifiable condition 2}
  (c) {falsifiable condition 3}

PORTFOLIO TAIL STRESS (required — both numbers, no omissions):
  (a) -30% drawdown in {TICKER}: dollar impact on book at current weight = ${amount} ({weight}% × book × 0.30)
  (b) -50% worst-case: dollar impact at current + proposed add size = ${amount}
  State: "At {weight}% of a ${book_size} book, a -30% move costs ${x}; -50% costs ${y}."

CITATION AUDIT — tag every factual claim you make:
  [LIVE] = verified this run via web_fetch, feed script, fundamentals.py, or TradingView
  [FILED] = specific SEC filing (name it: 10-Q Q1'26, Form 4 2026-05-15, etc.)
  [MEM] = training-data recall (undated, not confirmed this run)
  Rule: if TAIL RISK or HISTORICAL ANALOG rests solely on [MEM] → add ⚠️[MEM-only] flag; CIO must address it in DISSENT LOGGED.

SKEPTIC VERDICT: {SKIP | WATCH | BUY} — {one sentence explaining the controlling factor}
Inputs: {ALL_6_SEAT_VERDICTS_JSON} | {MACRO_REGIME}
```

Cache output: `echo '{skeptic_json}' > "$RUN_DIR/{TICKER}/seat_skeptic.json"`

---

## Step B: CIO Synthesis

The CIO reads all 6 analyst verdicts plus the Skeptic's challenge and makes the final call. Cannot abstain. Spawn as a subagent (`/model sonnet /effort high`). **The CIO does not set the ACTION.** The ACTION is the Step 0.82 scorecard's output, passed in as `{SCORECARD_ACTION}` — non-negotiable. The rules below are the CIO's own believability-weighted read, used to derive conviction, entry/stop/sizing, and invalidation, and to decide whether the CIO's independent read agrees or disagrees with the scorecard ACTION. If it disagrees, that disagreement is recorded as DISSENT — it never overwrites the printed ACTION. The only two sanctioned ACTION modifiers are (a) a documented caller-mandate clamp, printed as `POLICY NOTE`, and (b) the Risk Manager's hard gate in Step C, which may downgrade a BUY/ADD to WATCH/HOLD — never upgrade.

**CIO subagent prompt — inject verbatim, fill `{placeholders}`:**

```
You are the CIO for {TICKER}. Read all 6 analyst verdicts and the Skeptic challenge. You cannot abstain.

CIRCLE OF COMPETENCE: State in 2 sentences how {TICKER} earns money and why competitors cannot replicate it. If you cannot → CIO READ: PASS. Note it in DISSENT/CIO MEMO; ACTION still prints the scorecard value. Stop here.
DATA-COVERAGE GATE (check before CIO READ): count how many of the 6 seats returned INSUFFICIENT_DATA or a
NEUTRAL-due-to-no-data read this run (the seat could not cite real, live-fetched evidence — e.g. "INSUFFICIENT
DATA — do not guess", [UNAVAILABLE], or a NEUTRAL that is really "nothing found" rather than a researched view).
  If ≥2 of 6 seats have no real data this run:
    Holdings path → cap your CIO READ at HOLD, regardless of what Fundamental/Technical alone would otherwise support.
    New-idea path → cap your CIO READ at WATCH, regardless of what Fundamental/Technical alone would otherwise support.
  State the cap explicitly if it fires, e.g. "CIO READ capped at HOLD: Narrative + Smart-Money returned no data this run."
  If this cap makes your CIO READ diverge from the scorecard ACTION, name that divergence in DISSENT LOGGED —
  the gate constrains your own read, it is not itself a sanctioned ACTION modifier.
  (Mirrors crypto-advisor's UNCERTAIN → HOLD gate: "key briefs are thin/[UNAVAILABLE]; do not manufacture a verdict.")
SKEPTIC RESPONSE: Address the Skeptic's single strongest argument — rebut with evidence, or accept it and explain why you invest despite it.
CIO READ (your own believability-weighted assessment — feeds conviction sizing and the DISSENT comparison below; it is NOT the printed ACTION. fundamental/narrative 2×, technical 2×; sell-side is corroborating, not primary — it never overrides fundamental/technical on its own; subject to the DATA-COVERAGE GATE cap above):
  BUY-leaning requires: Fundamental ≥ GOOD, named setup + live bar-close trigger, narrative not LATE/FADING, Sentiment ≠ EXTREME.
  Holdings path: ADD/HOLD/TRIM/EXIT-leaning when cost basis is known (EXIT: POOR/FADING/BROKEN; TRIM: weight>15%/EXTREME/LATE; ADD: BUY gate + room; HOLD: else).
  Conviction (start 3): +1 ≥3 seats; +1 EARLY+QUIET; −1 CROWDED; −1 PEG>2/neg FCF; −1 LATE; +1 SM-accum (≥2 seats); −1 SM-distrib (caps BUY at 3); +1 Sell-side BULLISH (independent view confirming, not consensus level alone); −1 Sell-side BEARISH. Clamp 1–5.
ACTION vs SCORECARD: compare your CIO READ to the input `{SCORECARD_ACTION}`. If they agree, proceed. If they
  disagree, the printed ACTION stays `{SCORECARD_ACTION}` — your disagreement goes into DISSENT LOGGED, not
  into the ACTION field. Never substitute your read for the scorecard's.

Output exactly:
ACTION: {SCORECARD_ACTION — printed verbatim from the Step 0.82 scorecard, never computed here}
CIO READ: {BUY|WATCH|SKIP}  or {ADD|HOLD|TRIM|EXIT} — your own believability-weighted read (informational; see DISSENT if it differs from ACTION)
CONVICTION: {1–5}/5
DATA COVERAGE: {N}/6 seats had real evidence this run — {name any seat that returned INSUFFICIENT_DATA/no-data
  NEUTRAL by name, e.g. "Narrative: INSUFFICIENT_DATA; Smart-Money: no fetched data; Sell-side: INSUFFICIENT_DATA"} | GATE: {capped at HOLD/WATCH | not triggered}
DISSENT LOGGED: {Skeptic's best objection in one sentence, AND — if CIO READ differs from ACTION — one sentence naming that disagreement too; printed even when overruled}
POLICY NOTE: {documented caller-mandate clamp applied to the ACTION this run, e.g. "caller flagged hold-only — TRIM means rotate, not exit to cash"; or "n/a"}
CIO MEMO: {1 paragraph: controlling factor, Skeptic right/wrong and why, one fact that would change this call.
  Explicitly name any seat that contributed no real evidence this run — do not fold "no catalyst found" into
  the thesis as if it were a researched finding.}
Inputs: {SCORECARD_ACTION} | {SCORECARD_BASIS} | {ALL_6_VERDICTS_JSON} | {SKEPTIC_JSON} | {MACRO_REGIME}
```

> Source: Surowiecki, *Wisdom of Crowds* (2004) — domain-weighted aggregation (believability by demonstrated track record in a specific area) consistently outperforms equal-vote averaging; the CIO weights fundamental/narrative for thesis quality and technical for timing rather than treating all 6 seats as peers. Bridgewater ILC design principle: every open position has a standing institutional adversary; the Skeptic role encodes this structurally so the challenge function cannot collapse when the same voice both proposes and critiques. crypto-advisor operating model — an UNCERTAIN/SPLIT quorum (thin or `[UNAVAILABLE]` briefs) is capped at HOLD rather than let the seats that did return data manufacture a directional verdict alone.

**A WATCH verdict is an alert trigger.** Register via the `mkt` skill with the CIO Memo as the thesis string.

Cache output: `echo '{cio_json}' > "$RUN_DIR/{TICKER}/seat_cio.json"`

---

## Step C: Risk Manager

Skip entirely when ACTION (scorecard) is WATCH, SKIP, HOLD, TRIM, EXIT, or PASS. The Risk Manager checks portfolio-level constraints only — thesis quality is the CIO's job. Hard rules cannot be overridden by a strong thesis. Run this inline (not a subagent) using the portfolio data already loaded.

**Risk Manager check prompt — run inline, fill `{placeholders}`:**

```
You are the Risk Manager for {TICKER} (ACTION: {BUY|ADD}, conviction: {N}/5). Check constraints only — not thesis quality. First breach blocks, no override.
Rule 1: Position ≥ 10% of book → BLOCKED: "concentration cap — no ADD until trimmed below 8%."
Rule 2: Primary factor group ≥ 25% of book → BLOCKED: "factor concentration limit."
Rule 3: Cash < $2,000 → BLOCKED: "insufficient cash for minimum position."
Rule 4: Conviction ≤ 2/5 → BLOCKED: "below minimum conviction threshold."
If no rule fires → APPROVED.
Position size (APPROVED): conviction × 2% × total_book, capped at (10% − current_weight).
  5/5 → 10% target; 4/5 → 6%; 3/5 → 4%. Subtract current weight for the add size.

Output:
STATUS: {APPROVED | BLOCKED}
POSITION SIZE: {$amount, % of book} or "n/a"
REASON: {rule fired, or "all constraints clear — factor headroom: {pct}%"}
Portfolio inputs: current_weight={W}%, factor_group={F}, factor_group_weight={FW}%, cash=${CASH}, total_book=${BOOK}
```

**Verdict flow after Risk Manager:** if APPROVED → ACTION stands; if BLOCKED → this is the Risk Manager's sanctioned downgrade (Step 0.82) — ACTION downgrades to WATCH (thesis intact, constraint violated — fix the constraint, then re-run). This is the only step allowed to change ACTION besides a documented caller-mandate clamp, and it may only downgrade BUY/ADD, never upgrade. Log the block reason in the final output block so the user knows what to clear.

Cache output: `echo '{risk_json}' > "$RUN_DIR/{TICKER}/seat_risk.json"`

> Source: Citadel operating model — risk team has operational authority to force position reduction without PM consent; the hard-gate design here encodes this: portfolio-level constraints are enforced by a separate role with veto power, independent of how compelling the thesis is. Carver, *Systematic Trading*, Ch.4 — concentration limits (≤10% single name, ≤25% factor group) are the primary structural protection against idiosyncratic drawdown; stops alone are insufficient.

---

## Output shape

```
ACTION: {BUY|WATCH|SKIP|PASS}   or {ADD|HOLD|TRIM|EXIT}   — from the Step 0.82 scorecard, or the Risk Manager's downgrade
CIO READ: {BUY|WATCH|SKIP}  or {ADD|HOLD|TRIM|EXIT} — CIO's own believability-weighted read, informational only
CONVICTION: {1–5}/5
DISSENT LOGGED: {Skeptic's best objection, and any CIO-read-vs-ACTION disagreement — printed even when overruled}
POLICY NOTE: {caller-mandate clamp applied, or "n/a"}
CIO MEMO: {1 paragraph: controlling factor + what one fact would change this call}
Risk status: {APPROVED $X (N% book) | BLOCKED: reason | N/A (not BUY/ADD)}
Invalidation: {3 falsifiable conditions from Skeptic}
Edge: {INFORMATION|ANALYTICAL|TIMING|STRUCTURAL} — {one sentence}
```

Execution entry: one P0/P1/P2/P3 row in the run's final EXECUTION TABLE (Step 3.6 of SKILL.md).
