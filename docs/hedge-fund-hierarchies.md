# Hedge Fund Decision Hierarchies

Comparison of investment decision architectures across top funds — for implementation in the stocks-advisor skill.

---

## Bridgewater Associates (Ray Dalio) — *Idea Meritocracy*

```mermaid
flowchart TD
    AP["ANALYST PANEL
    5 seats in parallel
    Fundamental · Technical · Narrative
    Sentiment · Smart-Money
    Each returns verdict + rationale
    independently — no coordination"]

    SK["SKEPTIC
    Reads all 5 analyst verdicts
    Writes strongest possible case AGAINST consensus
    Must name:
    (a) what analysts are missing
    (b) tail risk not priced
    (c) historical analog where this trade failed
    Output: 3-paragraph challenge + counter-verdict"]

    CIO["CIO SYNTHESIS
    Reads analysts + Skeptic
    Must address Skeptic's best argument explicitly
    Applies circle-of-competence check:
    'Do we actually understand this business?'
    If thesis unclear → PASS
    Output: BUY/WATCH/SKIP + conviction 1–5
    + paragraph explaining why Skeptic was/wasn't right"]

    RM["RISK MANAGER
    BUY verdicts only
    Checks:
    (a) position already >10% of book → BLOCK
    (b) factor concentration >25% → FLAG
    (c) cash available for proposed size
    Output: APPROVED (with $ size) or BLOCKED (with reason)"]

    OUT["FINAL VERDICT
    Ticker · BUY/WATCH/SKIP · Conviction · Size · Trigger"]

    AP --> SK --> CIO --> RM --> OUT

    style SK fill:#ff6b6b,color:#fff
    style CIO fill:#4ecdc4,color:#fff
    style RM fill:#45b7d1,color:#fff
```

**Key principle:** The Skeptic seat is structural — not a human raising their hand, but a dedicated agent whose entire job is to break the consensus thesis. CIO cannot issue a verdict without explicitly addressing the Skeptic's best argument.

---

## Tiger Global / Robertson Cubs — *Concentrated Conviction*

```mermaid
flowchart TD
    AN["ANALYST
    Bottom-up thesis:
    5-yr FCF + ROIC model
    Why does this business compound?
    What is the moat's half-life?
    Output: thesis + 5-yr price target"]

    SH["SECTOR HEAD
    Cross-book sanity check:
    Is this the best expression of this theme?
    Do we already own a better version?
    Comparable valuation check
    Output: BEST-IN-CLASS or REDUNDANT"]

    PM["PM / CIO
    Narrative coherence check:
    Does the thesis hold for 3–5 years?
    No committee — PM decides alone
    Position SIZE = conviction signal
    Top 10 positions = 60–70% of AUM
    Output: sizing decision (0% → 5–15%)"]

    EX["EXECUTION
    No separate approval
    PM calls directly
    Thesis breaks → immediate exit
    No averaging down on broken thesis"]

    OUT["POSITION
    Concentrated · Long-term · High-conviction
    Max 15–20 names in core book"]

    AN --> SH --> PM --> EX --> OUT

    style PM fill:#f7dc6f,color:#333
```

**Key principle:** Position size IS the conviction vote. No formal scoring rubric — if PM believes it, they size it. No committee dilutes the thesis. Faster kill on thesis breaks than any other style.

---

## Citadel (Ken Griffin) — *Multi-Pod with Central Risk*

```mermaid
flowchart TD
    POD["INDEPENDENT POD PM
    Generates alpha idea
    Entry/exit model
    VaR within pod budget
    Full P&L accountability
    Pods do NOT see each other's books"]

    PR["POD RISK CHECK
    VaR impact within pod budget
    Factor exposure within pod limits
    Output: APPROVED / REDUCE SIZE"]

    CR["CENTRAL RISK (firm-wide)
    Real-time across ALL pods simultaneously
    Gross/net limits
    Cross-pod correlation
    Sector concentration
    Can force reduction or exit INTRADAY
    Output: GREEN / REDUCE / EXIT"]

    GR["GRIFFIN / CRO LAYER
    Quarterly capital reallocation
    Underperforming pods get shrunk
    No recourse for PM
    Override any position at will"]

    OUT["TRADE
    Executed — but Central Risk
    monitors continuously post-trade"]

    POD --> PR --> CR --> GR
    CR -->|real-time monitor| OUT
    POD --> OUT

    style CR fill:#e74c3c,color:#fff
    style GR fill:#8e44ad,color:#fff
```

**Key principle:** Independent pods compete for capital. Central Risk sees everything; pods see nothing of each other. Griffin reallocates capital quarterly — chronic underperformers lose budget, not just positions.

---

## Renaissance Technologies (Simons) — *Pure Quant Signal Committee*

```mermaid
flowchart TD
    SIG["SIGNAL RESEARCH
    Researcher proposes signal hypothesis
    Raw backtest on full history
    No human narrative — only statistics"]

    PEER["PEER STATISTICAL REVIEW
    Overfitting check
    Data-snooping audit
    Walk-forward OOS validation on held-out data
    Committee consensus required — no single person gates
    Output: PASS / FAIL / REVISE"]

    PAPER["PAPER PORTFOLIO
    Tiny initial allocation (0.1% sizing)
    Live Sharpe vs model assumption
    Execution slippage check
    Duration: weeks–months"]

    SCALE["SCALE-UP
    If live Sharpe holds → increase allocation
    Signals are ensemble-combined
    No human at trade level — 100% automated
    Medallion capped to employees only
    (deliberate alpha preservation)"]

    OUT["AUTOMATED EXECUTION
    Millisecond latency
    No discretionary override at trade level"]

    SIG --> PEER --> PAPER --> SCALE --> OUT

    style PEER fill:#27ae60,color:#fff
    style OUT fill:#2c3e50,color:#fff
```

**Key principle:** Statistical threshold is the gate, not a person. No single researcher can push a signal live alone. Signals graduate from 0.1% to full allocation by proving live Sharpe — not by convincing a committee.

---

## Soros / Quantum Fund — *Macro Reflexivity*

```mermaid
flowchart TD
    MAC["MACRO THESIS (Soros)
    Global macro frame
    Reflexivity hypothesis:
    'The market IS the data — our
    positioning feeds back into the thesis'
    Output: directional bias + narrative"]

    EXP["TRADE EXPRESSION (Druckenmiller)
    Select instrument for the thesis
    Initial sizing + stop logic
    Output: position + entry"]

    MON["POSITION MONITOR
    Price action = thesis confirmation signal
    Market moves WITH thesis → ADD
    (adding to winners is systematic)
    Market moves AGAINST → re-examine, not double-down"]

    REF["REFLEXIVITY GATE
    Is our position size now large enough
    to itself be moving the market?
    If yes → throttle / close
    (Soros closes positions that become
    'too right' — own success ends the trade)"]

    SOV["SOROS OVERRIDE
    Unilateral at any point
    Famous: told Druckenmiller to 2× the
    GBP short AFTER max size was declared
    No committee overrides this"]

    OUT["EXIT
    When reflexive cycle reverses
    Soros calls the turn"]

    MAC --> EXP --> MON --> REF --> SOV --> OUT
    MON -->|confirms| EXP

    style SOV fill:#e67e22,color:#fff
    style REF fill:#c0392b,color:#fff
```

**Key principle:** Reflexivity — the fund's own positioning is a market input that can accelerate the thesis. Self-referential feedback is a feature. Soros exits when he's "too right" and his size is itself distorting the market.

---

## Point72 / SAC Capital (Cohen) — *Edge-First + Conviction Scoring*

```mermaid
flowchart TD
    AN["ANALYST
    Idea + mandatory EDGE STATEMENT:
    'Why do I know this and others don't?'
    No edge statement = rejected before scoring
    Output: thesis + edge articulation"]

    EV["EDGE VALIDATOR
    Scores edge specificity 1–5
    Below 3 → REJECT (no further review)
    Types: information edge / analytical edge /
    timing edge / structural edge
    Output: EDGE SCORE + gate decision"]

    CV["CONVICTION SCORER (PM)
    Scores idea 1–10
    Portfolio fit check
    Sector sizing
    7+ → Cohen sees it directly
    Output: conviction score + recommended size"]

    RK["RISK OVERLAY
    Factor exposure check
    Drawdown budget
    Can force size reduction
    Track record determines PM budget"]

    CO["COHEN SEAT
    Reviews all ideas scored 7+
    Direct adversarial probe of thesis
    ('What's the bear case?')
    Override at will
    Capital pulled from chronic underperformers"]

    OUT["TRADE
    Executed with conviction-scaled size"]

    AN --> EV -->|score ≥ 3| CV --> RK --> CO --> OUT
    EV -->|score < 3| REJECT["REJECT"]

    style EV fill:#e74c3c,color:#fff
    style CO fill:#8e44ad,color:#fff
    style REJECT fill:#95a5a6,color:#fff
```

**Key principle:** Edge articulation is mandatory before any analysis begins. "Why do I know this and others don't?" If the analyst can't answer that question specifically, the idea is rejected. This is what differentiates Point72 from narrative-driven funds.

---

## Comparison Table

| Fund | Seats | Key Gate | Alpha Source | Kill Mechanism | Speed |
|---|---|---|---|---|---|
| **Bridgewater** | Analyst→Skeptic→CIO→Risk | Skeptic must be rebutted | Idea meritocracy | CIO denies on weak rebuttal | Days |
| **Tiger** | Analyst→Sector Head→PM | PM sizing = conviction | 5-yr compound thesis | PM exits on thesis break instantly | Days–weeks |
| **Citadel** | Pod PM→Central Risk→Griffin | Central Risk real-time | Multi-pod diversification | Central Risk intraday force-exit | Minutes–hours |
| **RenTech** | Signal→Peer Review→Paper→Scale | Statistical OOS validation | Ensemble signal alpha | Live Sharpe gate — signal dropped | Milliseconds |
| **Soros** | Macro→Expression→Monitor→Reflex | Soros unilateral override | Macro reflexivity | Soros calls the reflexive reversal | Hours–days |
| **Point72** | Analyst→Edge→Conviction→Risk→Cohen | Edge score ≥ 3 required | Sector specialist + edge | Cohen capital pull from PM | Days |

---

## AI Implementation Priority

| Fund | Ease to implement | Unique value it adds | Recommend? |
|---|---|---|---|
| Bridgewater | ✅ Already done (23/25) | Adversarial Skeptic | **Default — ship it** |
| Point72 | ✅ High | Edge-articulation gate kills weak ideas early | **Next to test** |
| Tiger | ✅ High | Thesis coherence check + concentration filter | **High value** |
| Soros | 🟡 Medium | Reflexivity loop (needs market feedback) | Good for macro skill |
| Citadel | 🟡 Medium | Multi-PM capital competition | Interesting but complex |
| RenTech | ❌ Low | Pure quant — needs real backtested signals | Not applicable to qualitative skill |
