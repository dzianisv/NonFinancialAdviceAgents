# Hierarchy: Citadel

## When to use
Citadel multi-pod architecture — highest-frequency risk monitoring of any tested hierarchy. Use when the mandate is active portfolio management with intraday risk constraints, cross-pod correlation control, and capital reallocation based on PM track records. Best fit: large diversified book where each position is an independent pod-style bet.

## Key gate
Central Risk (Step C): a firm-wide real-time layer that sees ALL positions simultaneously and can force reduction or exit intraday — the PM has no recourse. This is structurally different from an advisory review: Central Risk acts, it doesn't recommend.

## Action authority
This hierarchy sizes and risk-gates a position — POD VERDICT, POD RISK VERDICT, and CENTRAL RISK VERDICT are
submission/sizing statuses, not the BUY/WATCH/HOLD-family ACTION label. The ACTION is the Step 0.82 scorecard's
output, non-negotiable, and is printed alongside this chain's sizing output regardless of what this chain
concludes. Central Risk's REDUCE/EXIT authority governs position SIZE (it may force size to zero), not the
scorecard ACTION field itself; if Central Risk's read of the position conflicts with the scorecard ACTION,
log it as DISSENT.

---

## Step A: Pod PM — Alpha Idea

The Pod PM generates an alpha idea with a defined entry/exit model. Critically, VaR must be within the pod's allocated risk budget *before* the idea reaches the next layer. If VaR would exceed pod budget at the proposed size → size down until it fits, or don't submit.

**Pod PM prompt — inject verbatim, fill `{placeholders}`:**

```
You are the Pod PM for {TICKER}. Generate a alpha idea within your pod's risk budget.

EDGE ARTICULATION: State the specific edge — information, analytical, timing, or structural. If you cannot name a specific edge this idea has over the market right now → REJECT. Do not proceed.

ENTRY MODEL:
  Entry price zone: {price range with rationale}
  Bar-close trigger: {exact condition that confirms entry — no trigger = no trade}
  Market-based stop: {stop level derived from price structure, not arbitrary %}
  Target: {price target with timeframe}

VAR ESTIMATE: Estimate the 1-day 95% VaR at the proposed position size. Must be ≤ {POD_VAR_BUDGET}% of pod AUM.
  If VaR > budget → reduce size to fit. Report final size and VaR.

OUTPUT:
TICKER: {ticker}
EDGE TYPE: {INFORMATION | ANALYTICAL | TIMING | STRUCTURAL}
EDGE STATEMENT: {one sentence — why do we know this and others don't?}
ENTRY ZONE: {$price range}
TRIGGER: {exact bar-close condition}
STOP: {$price or structural level}
TARGET: {$price, timeframe}
PROPOSED SIZE: {$amount, % of pod AUM}
VAR: {1-day 95% VaR as % of pod AUM}
POD VERDICT: {SUBMIT | HOLD | REJECT}

Portfolio inputs: pod_aum=${POD_AUM}, pod_var_budget={POD_VAR_PCT}%, ticker_current_weight={W}%
```

Cache output: `echo '{pod_json}' > "$RUN_DIR/{TICKER}/seat_pod.json"`

---

## Step B: Pod Risk Check

Runs inline — not a subagent. Checks VaR and factor exposure against this specific pod's limits. Central Risk (Step C) handles firm-wide constraints. A pod can pass Step B and still be blocked by Step C.

```
You are the Pod Risk Officer for {TICKER}.

CHECKS:
1. VaR within pod budget: {POD_VAR_ACTUAL}% ≤ {POD_VAR_BUDGET}% → PASS / FAIL
2. Factor exposure: does this add unacceptable concentration within this pod's existing positions? → PASS / FLAG
3. Liquidity: can we exit this position in one day at the proposed size without moving the market? → PASS / FLAG

OUTPUT:
VAR CHECK: {PASS | FAIL} — {VaR actual}% vs {budget}%
FACTOR CHECK: {PASS | FLAG} — {factor, exposure %} 
LIQUIDITY CHECK: {PASS | FLAG} — {ADV %, estimated market impact}
POD RISK VERDICT: {APPROVED | REDUCED | BLOCKED}
FINAL SIZE: {$amount after any reduction}
```

Cache output: `echo '{pod_risk_json}' > "$RUN_DIR/{TICKER}/seat_pod_risk.json"`

---

## Step C: Central Risk — Firm-Wide Real-Time

Central Risk sees ALL pod positions simultaneously. It checks cross-pod correlation, gross/net limits, and sector concentration at the firm level. Can force reduction or exit on any position at any time with no recourse for the PM. This is the defining mechanism of the Citadel architecture.

**Central Risk prompt — inject verbatim, fill `{placeholders}`:**

```
You are Central Risk at Citadel. You have real-time visibility across ALL pods. Review the proposed {TICKER} position from {POD_NAME} in the context of the entire book.

CROSS-POD CORRELATION:
  Is any other pod already long the same underlying bet (even via different instruments)?
  Overlapping bets → effective concentration is HIGHER than it appears per pod.
  If effective concentration >15% of firm AUM in one factor → REDUCE to bring under 15%.

GROSS/NET LIMITS:
  Does this position push gross exposure above firm limit?
  Does it move net long/short exposure outside firm target range?
  If yes → FORCE REDUCTION to fit within limits.

SECTOR CONCENTRATION:
  What is current firm-wide weight in this sector/factor?
  If weight already ≥ 20% → ADD only if this is an explicit hedge. Else BLOCK.

DYNAMIC MONITORING NOTE: Post-approval, this position enters continuous monitoring. 
  If P&L deteriorates past pod drawdown limit (-{DRAWDOWN_LIMIT}% of pod AUM) → AUTOMATIC CUT, no PM override.
  If cross-pod correlation spikes intraday → REDUCE forced immediately.

OUTPUT:
CROSS-POD STATUS: {CLEAR | OVERLAP FOUND — {ticker/pod name, effective concentration}}
GROSS/NET STATUS: {CLEAR | LIMIT BREACH — {current vs limit}}
SECTOR STATUS: {CLEAR | CONCENTRATED — {sector, current weight%}}
CENTRAL RISK VERDICT: {GREEN — proceed at full size | REDUCE — {new size} | EXIT — immediate}
REASON: {one sentence on the controlling constraint}

Portfolio inputs: firm_gross={GROSS}%, firm_net={NET}%, sector_weight={SW}%, pod_drawdown_limit={DD_LIMIT}%, all_pod_positions={ALL_POSITIONS_JSON}
```

Cache output: `echo '{central_risk_json}' > "$RUN_DIR/{TICKER}/seat_central_risk.json"`

---

## Step D: Griffin / CRO Layer (Quarterly — capital reallocation only)

This step does NOT run per-position. It runs quarterly across all pods. Include in the portfolio synthesis output as a capital allocation signal.

```
CAPITAL REALLOCATION SIGNALS (quarterly review):
- Pods with risk-adjusted return below median for 2+ consecutive quarters → budget reduction 30–50%
- Pods with Sharpe > 1.5 over trailing 12 months → budget increase up to 2×
- Pods with max drawdown > {DD_THRESHOLD}% in any quarter → review + potential wind-down
- Griffin override: any position at will, any time, no stated reason required

OUTPUT IN PORTFOLIO SYNTHESIS:
PODS TO SCALE: {list with rationale}
PODS TO CUT: {list with rationale}
CAPITAL FREED: {$amount}
```

---

## Output shape

```
ACTION: {BUY|WATCH|SKIP|PASS}   or {ADD|HOLD|TRIM|EXIT}   — from the Step 0.82 scorecard (never computed by this chain)
TICKER: {ticker}
EDGE: {type — statement}
ENTRY ZONE: {price range}
TRIGGER: {bar-close condition}
STOP: {structural level}
TARGET: {price, timeframe}
POD SIZE: {$amount, % pod AUM}
VAR: {1-day 95% VaR}

Pod Risk: {APPROVED | REDUCED ($new_size) | BLOCKED}
Central Risk: {GREEN | REDUCE ($new_size) | EXIT}

FINAL SIZE: {$amount after all adjustments}
MONITORING: Position enters continuous intraday monitoring. Auto-cut at -{DD_LIMIT}% from peak.
DISSENT LOGGED: {any conflict between Central Risk's read and the scorecard ACTION — one sentence; "none" if aligned}
POLICY NOTE: {documented caller-mandate clamp applied, or "n/a"}

PORTFOLIO SYNTHESIS NOTE: Capital reallocation review due {QUARTER}. Underperforming pods flagged for budget reduction.
```

> Source: Institutional Multi-Strategy Risk Management — Citadel's edge is the Central Risk layer that operates orthogonally to pod-level management. Central Risk cannot be appealed; its authority is absolute and intraday. This architectural choice means Citadel can run 30+ uncorrelated pods without the systemic risk that typically accumulates in diversified portfolios.
