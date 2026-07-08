# Hierarchy: Millennium Management

## When to use
Millennium's capital-allocator model — Englander does not trade; he allocates capital to 100+ independent PM pods. Use when the mandate is disciplined risk-budget management with automated hard stops, cross-pod diversification, and PM accountability by P&L. Best fit: portfolio with many independent positions where each position should be treated as an autonomous sub-portfolio bet, not a single-book thesis.

## Key gate
Drawdown Hard Stop (Step C): if a PM's allocated capital falls below the drawdown threshold (-5% to -15% depending on strategy type), the risk system cuts positions automatically with no override path — not even Englander can override an automatic stop. This is the defining mechanism: the risk rules are the product.

## Action authority
This hierarchy sizes and risk-gates a position — PM VERDICT, STRATEGY HEAD VERDICT, and RISK SYSTEM VERDICT are
submission/sizing statuses, not the BUY/WATCH/HOLD-family ACTION label. The ACTION is the Step 0.82 scorecard's
output, non-negotiable, and is printed alongside this chain's sizing output regardless of what this chain
concludes. The automated drawdown stop governs position SIZE (it may force size to zero), not the scorecard
ACTION field itself; if this chain's read of the position conflicts with the scorecard ACTION, log it as DISSENT.

---

## Step A: PM Idea Submission

Each pod PM submits an idea with a mandatory thesis and position sizing within their allocated capital. Unlike Citadel, Millennium pods have more autonomy in strategy type — equity L/S, quant, macro, credit, commodities all coexist. The constraint is the capital budget, not the strategy type.

**PM Idea prompt — inject verbatim, fill `{placeholders}`:**

```
You are a Pod PM at Millennium Management for {TICKER}. You manage an independent book within your allocated capital of ${POD_CAPITAL}.

THESIS (mandatory — 3 components):
  (a) What is the specific alpha source? (information advantage / analytical edge / timing edge / structural mispricing)
  (b) What is the catalyst that realizes the value within {HOLDING_PERIOD}?
  (c) What is the falsification condition — the single event that would prove this wrong?

POSITION SIZING:
  Max single position = 10% of your allocated capital (hard limit, cannot be overridden)
  Proposed size: {$amount, % of pod capital}
  Kelly fraction check: Edge × (B+1)/B ≤ proposed size % (conservative Kelly, B = reward/risk ratio)
  If Kelly fraction < proposed size → reduce to Kelly fraction

ENTRY/EXIT:
  Entry: {price zone or trigger}
  Stop: {structural stop — cannot be >8% below entry for equity L/S}
  Target: {price target}
  Holding period: {days/weeks — Millennium is NOT a long-duration fund}

OUTPUT:
TICKER: {ticker}
ALPHA SOURCE: {type — one sentence}
CATALYST: {specific event, date if known}
FALSIFICATION: {the one event that ends the trade}
PROPOSED SIZE: {$amount, % pod capital}
KELLY CHECK: {Kelly fraction vs proposed — PASS if proposed ≤ Kelly}
ENTRY: {$price or condition}
STOP: {$price — max -8% from entry for equity L/S}
TARGET: {$price}
HOLDING PERIOD: {estimate}
PM VERDICT: {SUBMIT | HOLD | REJECT}

Portfolio inputs: pod_capital=${POD_CAPITAL}, pod_drawdown_remaining=${DD_REMAINING}, pod_drawdown_limit={DD_LIMIT_PCT}%
```

Cache output: `echo '{pm_json}' > "$RUN_DIR/{TICKER}/seat_pm.json"`

---

## Step B: Strategy Head Review

Millennium groups pods by strategy type. Each strategy head reviews submissions within their domain — equity L/S PMs report to the equity head, quant PMs to the quant head, etc. The strategy head is NOT a trading supervisor; they check:
1. Is this idea already running in another pod in the same strategy?
2. Does it conflict with a firm-level macro view?
3. Does the PM have track record in this type of trade?

```
You are the {STRATEGY_TYPE} Head at Millennium for {TICKER}.

REDUNDANCY CHECK: Is any other PM in your strategy already running a materially identical bet?
  If YES: {name PM, describe overlap} — the newer submission should differentiate or withdraw.
  If NO: CLEAR

MACRO ALIGNMENT: Does this trade conflict with the firm's current macro positioning?
  Firm macro view: {FIRM_MACRO_VIEW}
  This trade: {PM_THESIS}
  Conflict? {YES — specify / NO}
  Note: conflict is NOT an automatic block — it must be flagged, PM must acknowledge.

PM TRACK RECORD: Does this PM have demonstrated edge in this trade TYPE?
  Track record in {TRADE_TYPE}: {strong / acceptable / first attempt}
  If first attempt at this trade type → size limit: 5% of pod capital (not 10%)

OUTPUT:
REDUNDANCY: {CLEAR | OVERLAP — {PM, description}}
MACRO CONFLICT: {NONE | FLAGGED — {description, PM must acknowledge}}
TRACK RECORD: {STRONG | ACCEPTABLE | FIRST ATTEMPT (size capped at 5%)}
STRATEGY HEAD VERDICT: {APPROVED | APPROVED WITH FLAG | BLOCKED}
NOTES: {any condition attached to approval}
```

Cache output: `echo '{strategy_head_json}' > "$RUN_DIR/{TICKER}/seat_strategy_head.json"`

---

## Step C: Risk Management System — Automated Hard Stop

Millennium's risk management is partially automated. The system continuously monitors each pod's P&L relative to its starting allocated capital for the period. When the drawdown limit is hit, positions are cut automatically — no human approval required, no override path.

**Risk System check prompt — run inline:**

```
You are Millennium's Risk Management System for {PM_NAME}'s pod.

DRAWDOWN STATUS:
  Pod starting capital this period: ${POD_START_CAPITAL}
  Current pod P&L: {PNL_PCT}% from start
  Drawdown limit for this strategy type: -{DD_LIMIT_PCT}%
  Drawdown used: {DD_USED_PCT}% of limit

IF DRAWDOWN LIMIT HIT: AUTOMATIC POSITION CUT — ALL positions reduced proportionally until pod is within limit. No override. No recourse.

POSITION HEADROOM:
  Does adding {TICKER} at {PROPOSED_SIZE} push the pod's expected drawdown past the limit under a -2σ scenario?
  Expected -2σ loss on {TICKER} position: {LOSS_EST}
  Current pod buffer before limit: ${BUFFER}
  Headroom check: {PASS if expected loss < 50% of buffer | WARN if 50-80% | BLOCK if >80%}

CROSS-POD CORRELATION:
  Is this {TICKER} exposure already present across other pods at the firm level?
  Firm-wide {TICKER} or same-factor exposure: {EXISTING_EXPOSURE_PCT}% of firm AUM
  Firm-level concentration limit: 10% of firm AUM in any single name/factor
  Status: {CLEAR | APPROACHING ({existing}%) | BLOCKED (>10%)}

OUTPUT:
DRAWDOWN STATUS: {CLEAR ({pct}% used of {limit}%) | WARNING ({pct}% — approaching limit) | BREACHED — AUTO CUT}
HEADROOM: {PASS | WARN | BLOCK}
CROSS-POD: {CLEAR | APPROACHING | BLOCKED}
RISK SYSTEM VERDICT: {GREEN | WARN — proceed with monitoring | CUT — automatic, no override}
AUTO-CUT TRIGGER: At {DD_REMAINING_PCT}% additional drawdown, all positions auto-cut proportionally.
```

Cache output: `echo '{risk_system_json}' > "$RUN_DIR/{TICKER}/seat_risk_system.json"`

---

## Step D: Englander Capital Allocation (Quarterly)

Izzy Englander does not make position decisions. He allocates capital budgets to PMs quarterly based on risk-adjusted return, drawdown behavior, and strategy diversification value. This is output in the portfolio synthesis — not per-position.

```
CAPITAL ALLOCATION SIGNALS (quarterly):
- PMs with Sharpe > 1.2 trailing 12 months AND drawdown never exceeded 50% of limit → INCREASE capital 25–100%
- PMs with Sharpe < 0.5 trailing 12 months → WARNING (one quarter to recover)
- PMs with Sharpe < 0.5 for 2+ consecutive quarters → CAPITAL REDUCTION 50% or termination
- PMs who hit automatic drawdown stop more than once → REVIEW: systematic issue vs bad luck?
- New PMs: start with minimum allocation; scale only after 2 quarters of positive risk-adjusted return

DIVERSIFICATION VALUE: Maintain <0.3 pairwise correlation between pod returns. If two pods are >0.4 correlated → reduce the smaller pod's budget or ask for strategy differentiation.

OUTPUT IN PORTFOLIO SYNTHESIS:
PODS TO SCALE: {list}
PODS ON WARNING: {list}
PODS TO WIND DOWN: {list}
DIVERSIFICATION STATUS: {any correlation issues flagged}
```

---

## Output shape

```
ACTION: {BUY|WATCH|SKIP|PASS}   or {ADD|HOLD|TRIM|EXIT}   — from the Step 0.82 scorecard (never computed by this chain)
TICKER: {ticker}
ALPHA SOURCE: {type — one sentence}
CATALYST: {specific event}
FALSIFICATION: {the event that ends the trade}

PM Size: {$amount, % pod capital} | Kelly check: {PASS/WARN}
Entry: {zone/condition} | Stop: {structural, max -8%} | Target: {price}
Holding period: {estimate}

Strategy Head: {APPROVED | APPROVED WITH FLAG | BLOCKED}
Risk System: {GREEN | WARN | CUT}

FINAL SIZE: {after all adjustments}
AUTO-CUT THRESHOLD: Position auto-cut if pod drawdown reaches -{DD_REMAINING}% additional from here.

MONITORING: Continuous. Position auto-cut at drawdown limit — no override exists.
DISSENT LOGGED: {any conflict between this chain's read and the scorecard ACTION — one sentence; "none" if aligned}
POLICY NOTE: {documented caller-mandate clamp applied, or "n/a"}
```

> Source: Millennium Management operates 100+ independent pods with different strategy mandates, all governed by the same capital-allocation and drawdown-limit framework. The key architectural insight: at Millennium, risk management IS the product. Englander's edge is not trading skill — it is the ability to find, vet, and optimally capital-allocate to hundreds of PMs, while the automated stop-loss system prevents any single bad bet from becoming a firm-level event. The risk rules are non-negotiable because they exist to protect other PMs' capital, not just the firm.
