# SKILLS-MAP — When & How to Run Each Skill

Quick-reference trigger model. Full architecture diagrams: `.agents/skills/README.md`.

---

## Decision tree: what to invoke for what question

```
QUESTION TYPE
     │
     ├── "run the fund / daily cycle"
     │        → hedge-fund-manager (PM/CIO, delegates everything)
     │
     ├── "weekly portfolio review"
     │        → tradfi-portfolio-manager (REVIEW→ASSESS→RESEARCH→DECIDE→ORDER)
     │
     ├── "should I buy/sell X?" (known ticker)
     │        → research-market workflow  (crypto OR equity path auto-detected)
     │
     ├── "what should I buy this week?" (open universe)
     │        → hedge-fund-committee workflow  (weekly, no ticker needed)
     │
     ├── "should I buy/hold/size X?" (pure judgment)
     │        → multi-lens-quorum  (4-7 independent analyst lenses)
     │
     ├── "find trending stocks"
     │        → research-trend-stocks workflow  (EDGAR×phrase + WebSearch×angle, ~50 agents)
     │
     ├── "where does X go by [date]?"
     │        → superforecasting  (scenarios × probabilities; scored by forecast-ledger)
     │
     ├── "what does the macro panel think?"
     │        → macro-panel  (7 thinker personas; surfaces agreement vs dissent)
     │
     ├── "risk-on or risk-off?"
     │        → regime-detection  (signal ensemble → exposure dial)
     │
     ├── "trade X" / "day-trade for income"
     │        → strategy-discovery-backtest FIRST (THE GATE — PASS required)
     │          → crypto-daytrading or stock-daytrading (only on PASS + human approval)
     │
     └── "manage my crypto book"
              → crypto-advisor  (loads analyst-crypto internally — don't double-call)
```

---

## Trigger model per skill

### Cron / scheduled (run automatically, notify only on signal)

| Skill | Cadence | Trigger type |
|-------|---------|-------------|
| dip-screener | daily | silent-unless-signal |
| regime-detection | daily | silent-unless-transition |
| signal-convergence-alert | daily | silent-unless-≥2-pool-hits |
| feed-fomc | daily | silent-unless-fed-event |
| trend-stock-research (mention_velocity.py) | daily | feeds convergence pool |
| 13f-watch | weekly | silent-unless-new-filing |
| 13d-watch | weekly | silent-unless-activist->5% |
| congressman-stock-watch | weekly | silent-unless-new-disclosure |
| portfolio-monitor | weekly | silent-unless-discipline-breach |

### On-demand (user or orchestrator triggers)

| Skill | Invoked by | Notes |
|-------|-----------|-------|
| hedge-fund-committee workflow | weekly review session | open-universe, no ticker |
| research-market workflow | "should I buy/sell X?" | passes question + portfolio + date |
| research-trend-stocks workflow | "find trending stocks" | wide-parallel HTTP fan-out |
| multi-lens-quorum | any judgment call | convenes 4-7 lenses on identical brief |
| macro-panel | "what does macro say?" | 7 thinker personas |
| superforecasting | "where does X go by date?" | logs to forecast-ledger |
| tradfi-portfolio-manager | weekly note | REVIEW→ASSESS→RESEARCH→DECIDE→ORDER |
| hedge-fund-manager | "run the fund" | PM/CIO that delegates all of the above |
| crypto-advisor | "manage crypto book" | includes analyst-crypto internally |
| defi-portfolio-manager | "manage DeFi positions" | separate from tradfi book |

### Always-first gate (invariant — never bypass)

| Skill | Gate condition |
|-------|----------------|
| strategy-discovery-backtest | any "trade X" / "day-trade" request |

### Internal / consumed by orchestrators only

These are sub-skills. Call them via their orchestrator, not directly:

`regime-detection` (inside hedge-fund-manager), `analyst-crypto` (inside crypto-advisor),
`crypto-research-desk`, `stock-research-desk`, `crypto-chair`, `stock-chair`,
`research-manager`, `portfolio-construction`, `risk-management`, `rebalancing`,
`dip-tranches-strategy`, `tax-loss-harvesting`, `trend-following`, all `feed-*` adapters,
all `analytics-*` lenses (consumed by macro-panel or multi-lens-quorum),
all `analyst-*` lenses (consumed by multi-lens-quorum).

### Evaluation / quality (meta — not part of the fund loop)

| Skill | When |
|-------|------|
| skill-supervisor | before shipping any SKILL.md edit |
| hedge-fund-committee-eval | after running hedge-fund-committee workflow |
| crypto-workflow-eval | after running research-market workflow (crypto) |

### Deprecated — do not use

| Skill | Superseded by |
|-------|---------------|
| liveness-monitor | agent-native cron heartbeat |
| agentic-fund-orchestration | hedge-fund-manager |

---

## Parallel-agent suitability

Critical rule: fan out only when each agent has an INDEPENDENT resource tap.

| Workflow | Parallel-safe? | Why |
|----------|---------------|-----|
| research-trend-stocks | YES | EDGAR queries + WebSearch calls — independent HTTP per agent |
| hedge-fund-committee | YES | 6 collector agents hit independent sources (13F, congress, feeds…) |
| research-market (gather phase) | YES | each gather seat is a different skill/source |
| multi-lens-quorum | YES | each lens reads same brief independently |
| macro-panel | YES | each thinker-persona is stateless |
| trend-stock-research (old v1) | NO | readers shared the one Chrome browser → serialized, timeouts |
| bypass-paywalls | NO | drives a single Chrome session — sequential only |
| any skill using chrome-devtools | NO | chrome-devtools MCP is a singleton — never fan out onto it |

Rule restated: N agents on 1 serialized device = queue, not parallelism.
Replace browser reads with EDGAR-phrase + WebSearch agents for breadth; demote browser to a single optional depth-pass.

---

## Consolidation findings (session 1)

Skills audited: 63 total.

| Cluster | Count | Decision |
|---------|-------|---------|
| Active, distinct gap | 52 | keep |
| Deprecated (liveness-monitor, agentic-fund-orchestration) | 2 | archived |
| Analytics lenses (analytics-*) | 9 | keep — consumed as seats by quorum + panel |
| Analyst lenses (analyst-*) | 4 | keep — methodology-based, different from thinker-personas |
| Feed adapters (feed-*) | 8 | keep — each normalizes a distinct source |

No consolidation needed beyond the 2 already-deprecated. Duplication risk is semantic, not structural:
- `trend-stock-research` (WHO) vs `multi-lens-quorum` (WHETHER) vs `superforecasting` (WHEN) — non-overlapping.
- `crypto-advisor` vs `analyst-crypto` — advisor LOADS analyst; never call both separately.
- `macro-panel` vs `multi-lens-quorum` — macro-panel = thinker personas on macro; quorum = any lens on any question.
