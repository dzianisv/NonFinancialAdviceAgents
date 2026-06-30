# Grounding the Stock / Portfolio-Management Skills in the Canonical Investment Books

**Purpose.** Audit the repo's stock & portfolio-management skills against the durable, implementable
principles of the field's best investment books, identify gaps, and propose concrete edits. **This is a
proposal document — no skill files were edited and nothing was committed.** Educational analysis, not advice.

**Scope note on paths.** The task brief named some files that no longer exist under those names. The audit
targets *as they exist on disk today* are:

| Brief name | Actual file on disk |
|---|---|
| `.agents/skills/strategy-discovery-backtest/SKILL.md` (backtest gate) | The gate lives inside `.agents/skills/analyse-fundamental/SKILL.md` ("The backtest gate") and `.agents/skills/agentic-fund-orchestration/SKILL.md` ("Pitfalls to design against"). There is **no standalone discovery-backtest skill** — see Gap G0. |
| `.agents/skills/stock-daytrading/SKILL.md` | **Does not exist.** GOAL.md workstream B calls for it; only `backtests/daytrade/*.py` scripts exist. See Gap G0. |
| `.agents/skills/hedge-fund-manager/SKILL.md` | Renamed → `.agents/skills/agentic-fund-orchestration/SKILL.md` (team orchestration) |
| `.agents/skills/tradfi-portfolio-manager/SKILL.md` | **Removed.** No tradfi PM skill on disk; `.agents/skills/defi-portfolio-manager/SKILL.md` is the crypto analogue. See Gap G0. |
| desk sub-skills | `.agents/skills/{regime-detection, trend-following, portfolio-construction, risk-management, rebalancing, tax-loss-harvesting, analyse-fundamental}` + `.agents/skills/dip-tranches-strategy` — all present. |

GOAL.md (`<context-foundation>`) and AGENTS.md still reference `hedge-fund-manager` and
`tradfi-portfolio-manager` as if present — a **doc-vs-disk drift** flagged as Gap G0.

---

## 1. Principles table — the durable rules, operationalized

Each row: a *specific, actionable* rule (not a summary), the book/author it comes from, and how to encode it
in a systematic skill.

| # | Principle (actionable) | Book / source | How to operationalize in a skill |
|---|---|---|---|
| P1 | **Margin of safety**: buy/size only when price sits well below a *conservatively* estimated intrinsic value; the gap absorbs estimation error. | Graham, *The Intelligent Investor* [1] | For any discretionary single-name sleeve, require an explicit `intrinsic_value_range` and a `margin_of_safety_pct`; reject if price > low end of range. For systematic books, the analogue is *valuation-aware sizing* (de-risk when CAPE/earnings-yield spread is thin). |
| P2 | **Mr. Market is a servant, not a master**: treat volatility as opportunity to be exploited by rule, not panic to be mirrored. | Graham [1] | Already the spirit of `dip-tranches` (buy declines) and `rebalancing` (trim winners) — make the framing explicit: drawdowns are *inputs to a buy schedule*, not signals to capitulate. |
| P3 | **Defensive default + 25–75% equity band**: most investors should index broadly, hold a stock/bond split inside a 25–75% band, and use mechanical rules over active selection. | Graham [1] | `portfolio-construction` tiers already do this; state the explicit equity floor/ceiling band (never <25%, never >75% equity beta for a "defensive/balanced" mandate). |
| P4 | **The Cost Matters Hypothesis**: after costs, active management underperforms the index by exactly its costs; minimize fees, turnover, and taxes — they are the one variable you control. | Bogle, *Common Sense on Mutual Funds* [2] | Every skill that trades must report **net-of-cost** results AND an explicit **cost/turnover budget**. Default to the cheap ETF; a strategy must *beat the index net of all-in cost* to allocate. |
| P5 | **Reversion to the mean (RTM)**: top-rated past performers revert to average in 3–5 years; do not chase recent winners. | Bogle [2] | Backtest gate must penalize strategies selected *because* of recent outperformance; require out-of-sample / walk-forward windows; deflate Sharpe for # of trials. |
| P6 | **Diversification is the only free lunch — diversify across *return drivers*, not just names**; combine asset classes with low/negative correlation. | Swensen, *Unconventional Success* [3]; Markowitz via Swensen | `portfolio-construction` diversifies across sleeves; make the *effective-number-of-bets* and *cross-sleeve correlation* an explicit construction check, not just a count of tickers. |
| P7 | **Disciplined rebalancing back to target weights** captures the diversification premium and enforces buy-low/sell-high. | Swensen [3]; Bernstein/Ferri | `rebalancing` already encodes calendar-check/threshold-act — good; tie it to a *rebalancing bonus* rationale and contrarian framing. |
| P8 | **Risk parity / balance across the four economic environments** (rising & falling growth × rising & falling inflation): allocate by *risk contribution*, not dollars, so no single environment dominates. | Dalio, *Principles* / All Weather [4] | `portfolio-construction` names the four regimes — strengthen by adding an explicit **risk-contribution check** (what % of portfolio *variance* comes from equities?) not just a dollar weight. Flag "equity with a bond sidecar." |
| P9 | **Harvest multiple, lowly-correlated factor premia** (value, momentum, carry, defensive, trend): diversifying across factors can ~halve vol and ~double Sharpe vs cap-weight. | Ilmanen, *Expected Returns* [5] | `analyse-fundamental` + `trend-following` cover value/momentum/trend; make *factor diversification* a first-class construction goal and document expected-return decomposition per sleeve. |
| P10 | **Value + momentum are negatively correlated (~−0.49)** — combining them is portfolio construction's "holy grail," higher Sharpe than either alone. | Asness/Moskowitz/Pedersen, *Value and Momentum Everywhere* (JF 2013) [6] | `analyse-fundamental` should pair its value screens with the momentum sleeve *deliberately* (not as separate bets), citing the negative correlation as the reason. |
| P11 | **Risk = probability of *permanent* loss of capital, and it lives where it's least perceived**; practice defensive investing; outcome ≠ probability. | Marks, *The Most Important Thing* [7] | `risk-management` is vol/drawdown-based — add the *permanent-impairment* lens: distinguish recoverable drawdown (index) from permanent loss (single-name blowup, leverage wipeout). Risk is highest when complacency is highest. |
| P12 | **Second-level thinking**: edge comes from a *non-consensus, correct* view; the consensus is already in the price. | Marks [7]; semi-strong EMH (Bogle/Malkiel) | `analyse-fundamental` already says public ratings are in the price — generalize: any signal must articulate *what the market is missing* or default to beta. |
| P13 | **Cycles are dependable; calibrate aggressiveness to where the pendulum sits** (euphoria → caution, panic → aggression). | Marks [7] | This is exactly `regime-detection`'s job — add a *sentiment/positioning* leg (the pendulum) to complement the price/credit/vol legs. |
| P14 | **Barbell**: combine very safe assets with a small, capped, convex tail bet; avoid the fragile "medium-risk" middle; **via negativa** (remove fragility first). | Taleb, *Antifragile* [8] | `portfolio-construction`'s dry-powder + optional TAIL/BTAL sleeve is a soft barbell — make the *convex tail sleeve* and the *avoid-the-fragile-middle* logic explicit; `risk-management` should think in *fragility removal* (kill leverage, caps) before optimization. |
| P15 | **Behavioral guardrails**: loss aversion (~2× pain), overconfidence / illusion of skill, anchoring to entry price, narrow framing. Pre-commit to rules to neutralize them. | Kahneman, *Thinking, Fast and Slow* [9] | Every discretionary judgment call in a skill ("pause the last sub-tranche", "insist on stock-picking") should carry a *bias warning* and a pre-committed rule. Decide the rule *before* the drawdown. |
| P16 | **Valuation is a *range*, not a point**; don't bury uncertainty in the discount rate; average/normalize inputs; market price is a check on your bias. | Damodaran, *Valuation* / 10 Rules for Uncertainty [10] | `analyse-fundamental` already says DCF fair value is a range (Damodaran-cited) — extend: any intrinsic-value output must be an interval with a confidence, normalized inputs, and a stated bias check. |
| P17 | **Magic Formula**: rank by earnings yield (EBIT/EV) + return on capital, buy a basket of the top names; mechanical, unemotional value+quality. | Greenblatt, *The Little Book That Beats the Market* [11] | Already listed as a candidate screen in `analyse-fundamental` — keep it *gated* by the backtest gate (it must clear net-of-cost vs the index before allocating). |
| P18 | **Trend-following / time-series momentum is "crisis alpha"** — positive in 8 of 10 largest 60/40 drawdowns over 137 yrs; the alpha is largely from vol-scaling. | AQR (Hurst/Ooi/Pedersen); cited in `trend-following` | Already well-encoded; keep the known-weakness honesty (V-crashes, whipsaw). |
| P19 | **Skin in the game / honest reporting**: forecasts with no downside accountability are noise; report failures and "no edge found" as first-class results. | Taleb [8]; repo GOAL invariant 4 | Already a GOAL invariant — ensure each skill's contract surfaces honest net-of-cost edge and crisis drawdown, never the green PnL alone. |

---

## 2. Per-skill audit

Legend — **Covered** = principle already encoded well; **Gaps** = canonical principle missing/weak;
**Contradictions** = anything against best practice. Proposed edits quote the current text and give a
replacement tagged with the principle/book.

### 2.1 `.agents/skills/portfolio-construction/SKILL.md`

| | |
|---|---|
| **Covered** | Four macro regimes named (P8 Dalio); de-concentrated equity core + diversifiers + dry powder (P6 Swensen, P14 barbell-ish); defense-lags-in-bulls honesty; risk-tier tables; trend as crisis alpha (P18). |
| **Gaps** | (a) Dollar weights only — **no risk-contribution check** (P8 Dalio risk parity: "is this equity with a bond sidecar?"). (b) Diversification is counted by *sleeve*, not by **effective number of bets / cross-sleeve correlation** (P6 Swensen). (c) The tail sleeve is "optional ≤3%" — the **barbell logic (safe core + convex tail, avoid fragile middle) is not stated** (P14 Taleb). (d) No explicit **equity floor/ceiling band** (P3 Graham 25–75%). (e) No **valuation-aware tilt** linking CAPE/earnings-yield-spread to the equity weight (P1 Graham, P13 Marks). |
| **Contradictions** | None material. Keeping Treasuries modest vs classic All-Weather is *defended* by the 2022 duration lesson — that's a reasonable, documented deviation from Dalio, not an error. |

**Proposed edits:**

- **E-PC1 (P8 Dalio risk parity).** After the "Sizing mechanics" bullet *"Within sleeves, default to the
  listed weights…"* add:
  > **Check risk contribution, not just dollars.** Compute each sleeve's share of total portfolio
  > *variance* (weight × vol × correlation), not its dollar weight. If equities contribute >~60% of
  > variance while sitting at ~45% of dollars, the book is "equity with a bond sidecar" (Dalio) — raise
  > the true diversifiers (gold/trend/TIPS) or scale equity down until no single environment dominates.

- **E-PC2 (P14 Taleb barbell).** Reframe the tail row. Current: *"Tail / anti-beta (optional) | TAIL / BTAL
  | 2% | 3% | 2%"*. Add a sentence under "Why this shape":
  > **Barbell, not a smooth middle (Taleb, *Antifragile*).** The book is deliberately a *safe core
  > (T-bills + Treasuries + gold) + a small, capped, convex tail sleeve* — avoid loading the fragile
  > "medium-risk" middle (levered equity, high-yield credit, illiquid yield-chase) that blows up in
  > exactly the regime the tail sleeve is meant to cover.

- **E-PC3 (P3 Graham band).** Add to "Mandatory framing":
  > **Equity-beta band.** Keep equity beta within a stated band per mandate (Graham's 25–75% rule):
  > never below ~25% (you must participate) nor above the tier's ceiling (you must survive). The tiers
  > above already sit in this band — state it as a hard rail.

- **E-PC4 (P1 Graham / P13 Marks valuation-aware tilt).** Add a bullet to "Sizing mechanics":
  > **Valuation-aware equity tilt (optional, slow).** When the earnings-yield-minus-bond-yield spread is
  > thin and CAPE is extreme (the current AI-bubble setup), bias toward the lower equity-beta tier — a
  > margin-of-safety tilt (Graham), calibrated to where the cycle pendulum sits (Marks), *not* a
  > market-timing call. Move one tier at most; never zero out.

### 2.2 `.agents/skills/regime-detection/SKILL.md`

| | |
|---|---|
| **Covered** | Ensemble + persistence/hysteresis (anti-whipsaw); never fully exit (floor); 200dma/credit/vol/curve/breadth; crisis-window backtesting; "dial not forecast" honesty. Strong on P13 (cycles) mechanics. |
| **Gaps** | (a) No **sentiment/positioning leg** — Marks' pendulum is about *psychology* (euphoria↔panic); the current ensemble is all price/credit/vol with no positioning/sentiment input (P13). (b) No explicit link to **valuation extremes** (CAPE/concentration) as a slow strategic tilt (P1/P11 — "risk is highest where least perceived"). |
| **Contradictions** | None. |

**Proposed edits:**

- **E-RD1 (P13 Marks pendulum).** Add a row to the signal ensemble table:
  > `| Sentiment / positioning (AAII bull-bear, put/call, fund-flow, NAAIM) | 1 | extreme fear | extreme greed | contrarian; Marks' pendulum — euphoria is risk, panic is opportunity |`
  And note: weight it low and use it *contrarian* (extreme greed = trim, extreme fear = a green light to
  re-risk *with* the trend, never to catch a falling knife alone).

- **E-RD2 (P11 Marks / P1 Graham).** Add to "What each signal is good/bad at":
  > **Valuation/concentration (CAPE, top-10 weight):** not a timing signal (it can stay extreme for
  > years) but a *strategic vigilance raiser* — "risk is highest where it's least perceived" (Marks).
  > When CAPE and concentration are extreme, bias the floor and the asymmetric bands toward defense.

### 2.3 `.agents/skills/trend-following/SKILL.md`

| | |
|---|---|
| **Covered** | P18 crisis alpha (AQR-cited), three variants, vol-scaling insight, MTUM warning, V-crash/whipsaw honesty, repo backtest evidence. Excellent. |
| **Gaps** | Minor: doesn't explicitly state the **value+momentum negative-correlation pairing** (P10 Asness) — trend/momentum is presented standalone, not as the complement to the value sleeve. |
| **Contradictions** | None. |

**Proposed edit:**

- **E-TF1 (P10 Asness).** Add to "Hand-offs":
  > **Pair with value, deliberately.** Time-series/cross-sectional momentum is *negatively correlated
  > (~−0.49) with value* (Asness/Moskowitz/Pedersen, *Value and Momentum Everywhere*, JF 2013) — combining
  > the trend sleeve with the value screens in `analyse-fundamental` raises Sharpe more than either
  > alone. Construct them as one paired bet, not two independent ones.

### 2.4 `.agents/skills/risk-management/SKILL.md`

| | |
|---|---|
| **Covered** | Vol-targeting, drawdown de-risk, CPPI, caps, fractional-Kelly cap, trend-exit-over-stop, stressed-correlation monitoring, deterministic-veto framing, crisis-window testing. Very strong, P14-aligned (via negativa: caps + kill switch first). |
| **Gaps** | (a) **Permanent vs recoverable loss not distinguished** (P11 Marks) — the layer is all about *drawdown %*, but a −20% index drawdown (recoverable) and a −20% from a single-name/leverage blowup (often permanent) are treated identically. (b) **"Risk is highest where least perceived"** (P11) — low realized vol *invites* over-sizing; the vol-target rule can lever *into* complacency right before a vol spike (the 2018 XIV / risk-parity failure mode). Needs a guardrail. |
| **Contradictions** | None — but see the vol-targeting caveat above; it's a known fragility, not an error. |

**Proposed edits:**

- **E-RM1 (P11 Marks).** Add a layer 7 to "Layered defenses":
  > **7. Permanent-impairment screen.** Separate *recoverable* drawdown (diversified index/sleeve — wait
  > and rebalance) from *permanent* loss (single-name blow-up, levered wipeout, un-named-yield default).
  > Hard-cap any position whose loss is plausibly permanent far tighter than a diversified sleeve. "Risk
  > is the probability of *permanent* loss of capital" (Marks) — vol is a proxy, not the definition.

- **E-RM2 (P11 / P14).** Add to "Pitfalls":
  > **Vol-targeting levers into complacency.** Realized vol is lowest right before stress (risk is
  > highest where least perceived — Marks). Cap the *up*-sizing the vol-target can do after a calm period,
  > and floor position vol estimates with a longer/stressed window so a quiet tape can't push gross to the
  > cap just before a spike (the risk-parity / short-vol failure mode).

### 2.5 `.agents/skills/rebalancing/SKILL.md`

| | |
|---|---|
| **Covered** | Calendar-check/threshold-act, no-trade bands, net-of-cost, tax-aware ordering (cashflows first, tax-advantaged first, TLH, long-term holding). Strongly P4 (costs) and P7 (disciplined rebalancing) aligned. |
| **Gaps** | (a) The **contrarian/diversification-premium *rationale*** (P2 Mr. Market, P7 Swensen) is implicit — rebalancing *is* systematic buy-low/sell-high, worth stating to keep the operator from overriding it in a euphoric tape. (b) No mention of the **behavioral value** of the rule (P15 Kahneman — it neutralizes anchoring/loss-aversion). |
| **Contradictions** | None. |

**Proposed edit:**

- **E-RB1 (P2/P7/P15).** Add to "Mandatory framing":
  > **Why it works beyond cost control.** Rebalancing is *mechanical contrarianism* — it trims what
  > Mr. Market over-loves and buys what he over-hates (Graham), harvesting the rebalancing/diversification
  > premium (Swensen). It also neutralizes anchoring and loss-aversion (Kahneman) by pre-committing the
  > trade. Do not suspend the rule because a sleeve "feels" like it should keep running.

### 2.6 `.agents/skills/tax-loss-harvesting/SKILL.md`

| | |
|---|---|
| **Covered** | Wash-sale mechanics, partner-ETF pairs, specific-lot/HIFO, cross-account traps, dip-tranche pairing, state rules, the "free lunch" framing. Directly serves P4 (cost/tax minimization — the controllable variable). Thorough. |
| **Gaps** | Minor: doesn't connect to the broader **"costs/taxes are the one thing you control"** Bogle thesis (P4) as the *organizing why*; it reads as standalone mechanics. |
| **Contradictions** | None. |

**Proposed edit:**

- **E-TLH1 (P4 Bogle).** Add one line to "Mandatory framing":
  > **Why TLH matters at all (Bogle).** Taxes and costs are the part of returns you actually control;
  > the Cost Matters Hypothesis says minimizing them is a *certain* edge where alpha is uncertain. TLH is
  > one of the few reliably positive-expected-value levers in a taxable book.

### 2.7 `.agents/skills/analyse-fundamental/SKILL.md`

| | |
|---|---|
| **Covered** | The backtest gate (P5 RTM-aware, point-in-time, crisis windows, deflate-for-trials); SPIVA-honest verdict; value/quality/Magic-Formula/Piotroski/momentum screens (P9, P17); MOAT-ETF-as-proxy; Damodaran "fair value is a range" (P16); semi-strong-EMH "ratings are in the price" (P12). The most book-grounded skill already. |
| **Gaps** | (a) **Margin of safety not named as a sizing rule** (P1 Graham) — value screens are present but the *price-below-conservative-value* discipline and an explicit MoS% aren't. (b) **Value+momentum pairing** (P10 Asness) — momentum is "the one factor that beat SPY" but isn't deliberately *combined* with value for the negative-correlation Sharpe gain. (c) Damodaran range is cited only in the Morningstar overlay, not as a **general output requirement** (P16). |
| **Contradictions** | None — the SPIVA honesty is exactly right and should be preserved. |

**Proposed edits:**

- **E-FA1 (P1 Graham margin of safety).** In "When the user *insists* on a stock-picking sleeve", add:
  > **Require a margin of safety (Graham).** Each name needs an explicit conservative
  > intrinsic-value *range* and a stated margin-of-safety %; buy only when price is below the low end of
  > the range. No MoS → no position. This is the discretionary analogue of the backtest gate.

- **E-FA2 (P10 Asness).** In "The screens the analyst can compute", add after the Momentum bullet:
  > **Combine value and momentum, don't choose.** They are negatively correlated (~−0.49; Asness et al.,
  > JF 2013) — a value+momentum *composite* historically beats either alone on Sharpe. When both clear the
  > gate, run them as one sleeve, not two.

- **E-FA3 (P16 Damodaran).** Promote the "fair value is a range" caveat from the Morningstar section into the
  **Outputs contract**: any `intrinsic_value` field must be an `{low, high, confidence}` interval with
  normalized inputs, never a point estimate.

### 2.8 `.agents/skills/agentic-fund-orchestration/SKILL.md` (the team playbook)

| | |
|---|---|
| **Covered** | Notification-first, deterministic caps/kill-switch, the analyst→PM→risk→execution loop, overfitting/look-ahead/survivorship/cost pitfalls (P4, P5, P19), net-of-cost metrics contract, walk-forward. Excellent governance. |
| **Gaps** | (a) No explicit **bias/behavioral guardrail** at the orchestration layer (P15 Kahneman — the LLM PM is itself overconfident; the doc bounds it with the risk layer but doesn't name the *behavioral* failure modes for the agents). (b) The metrics contract is performance/risk only — no **cost/turnover budget as a hard gate** (P4 is in "pitfalls" but not in the contract). |
| **Contradictions** | None. |

**Proposed edits:**

- **E-AFO1 (P15 Kahneman / P12 Marks).** Add to "Pitfalls to design against": *(currently ends "...LLM
  overconfidence (bound by the deterministic risk layer).")* — extend:
  > LLM/behavioral biases beyond overconfidence: **anchoring** (to the entry price or a prior thesis),
  > **narrow framing** (judging a trade in isolation, not at the book level), **recency/extrapolation**
  > (chasing the last regime). Counter each with a pre-committed rule and book-level (not trade-level)
  > evaluation (Kahneman). Demand a *second-level* thesis — what is the consensus and why is it wrong? — or
  > default to beta (Marks).

- **E-AFO2 (P4 Bogle).** Add to the "Metrics contract" line:
  > …plus an explicit **cost & turnover budget**: report all-in cost (commission + spread + impact + tax
  > drag) and assert the strategy beats its benchmark *net of that budget* — the Cost Matters Hypothesis
  > makes cost the one certain variable (Bogle).

### 2.9 `.agents/skills/dip-tranches-strategy/SKILL.md`

| | |
|---|---|
| **Covered** | Tiered deployment on drawdowns (P2 Mr. Market exploited by rule), lump-vs-DCA (Vanguard-cited), re-arm/timeout, "stop deploying if fundamentals crack" judgment, behavioral framing (avoids both failure modes). Strong P2 + P15. |
| **Gaps** | Minor: the "stop deploying if fundamentals crack" rule (step 6) is *discretionary* and could be tied to `regime-detection` / credit-spread signals to make it less of a judgment call (P11 Marks — distinguish recoverable dip from regime break). |
| **Contradictions** | None. |

**Proposed edit:**

- **E-DT1 (P11 Marks).** In execution rule 6, replace the purely-discretionary trigger with a
  semi-mechanical link:
  > Tie the "pause the last sub-tranches" decision to `regime-detection` / `risk-management` outputs (HY
  > OAS blowout, credit risk-off, CPPI floor near) so it distinguishes a *recoverable* index dip (keep
  > deploying) from a *regime break / permanent-impairment* scenario (pause) — Marks' recoverable-vs-
  > permanent-loss distinction — rather than relying on in-the-moment nerve.

---

## 3. Top 10 highest-impact edits (prioritized, book-cited)

Ranked by expected improvement to the book's *survival + honesty + return-per-unit-risk*, weighted by how
central the gap is to the AI-bubble-defense mission.

1. **E-PC1 — Risk-contribution check in `portfolio-construction`.** *(Dalio, All Weather/risk parity [4])*
   The single biggest structural gap: the book is built on dollar weights, so it can be "equity with a bond
   sidecar" and not know it. Add the variance-contribution check. **Highest impact** — it directly governs
   whether the all-weather claim is real.

2. **E-RM1 — Permanent vs recoverable loss screen in `risk-management`.** *(Marks [7])* Reframes the entire
   risk layer around *permanent* impairment, not just drawdown %; the cleanest way to keep the LLM from
   treating a single-name blowup like an index dip.

3. **E-FA1 — Margin-of-safety sizing rule in `analyse-fundamental`.** *(Graham [1])* The most-cited rule in
   investing is currently absent as an explicit gate on the discretionary sleeve. Closes the "value screens
   but no margin of safety" gap.

4. **E-PC2 — Explicit barbell framing + avoid the fragile middle in `portfolio-construction`.** *(Taleb [8])*
   Makes the safe-core-plus-convex-tail structure intentional and bans the medium-risk yield-chase that
   blows up in the defended regime. Direct AI-bubble-tail relevance.

5. **E-RD1 — Sentiment/positioning leg in `regime-detection`.** *(Marks, the pendulum [7])* The ensemble is
   all price/credit/vol with no *psychology* input — adding a contrarian sentiment leg is the missing half
   of cycle reading.

6. **E-AFO1 — Behavioral-bias guardrails at the orchestration layer.** *(Kahneman [9]; Marks second-level [7])*
   Names anchoring/narrow-framing/recency for the agent team and demands a second-level thesis or default to
   beta — hardens the whole loop against LLM overconfidence.

7. **E-FA2 / E-TF1 — Deliberately pair value + momentum (negative correlation).** *(Asness/Moskowitz/Pedersen,
   JF 2013 [6])* "Holy grail" of construction; the repo has both factors but treats them as separate bets.
   One change, two files, real Sharpe upside.

8. **E-RM2 — Cap vol-targeting's up-sizing into complacency.** *(Marks [7]; risk-parity failure mode)* Closes
   the "lever into the calm right before the spike" fragility — the exact mechanism that broke short-vol and
   risk-parity books in past shocks.

9. **E-AFO2 / (E-PC4, E-RD2) — Cost/turnover budget as a hard gate + valuation-aware tilt.** *(Bogle [2];
   Graham [1])* Make cost the certain edge (Bogle) and let extreme valuation slow-tilt the equity weight
   (Graham) — both cheap to add, both mission-central given CAPE ~41.6.

10. **G0 — Fix the doc-vs-disk drift and build the two missing skills.** GOAL.md/AGENTS.md still cite
    `hedge-fund-manager`, `tradfi-portfolio-manager`, and a `stock-daytrading` skill that don't exist on disk;
    there is no standalone discovery-backtest skill. Reconcile the names and stand up the missing
    `tradfi-portfolio-manager` (weekly PM loop, the tradfi analogue of `defi-portfolio-manager`) and
    `stock-daytrading` skills the GOAL's success criteria require. *(Not a book principle, but the highest-
    impact correctness gap for the stated mission.)*

---

## Sources

1. Benjamin Graham, *The Intelligent Investor* — margin of safety, Mr. Market, defensive vs enterprising
   investor, 25–75% band. Summaries: AAII "The Essence of the Benjamin Graham Approach"
   (https://www.aaii.com/journal/article/the-essence-of-the-benjamin-graham-approach);
   einvestingforbeginners "Defensive Investors: Rules from The Intelligent Investor"
   (https://einvestingforbeginners.com/defensive-investors-daah/).
2. John C. Bogle, *Common Sense on Mutual Funds* — Cost Matters Hypothesis, reversion to the mean, the
   relentless rules of humble arithmetic. Morningstar, "The Cost Matters Hypothesis"
   (https://www.morningstar.com/funds/cost-matters-hypothesis);
   Wikipedia (https://en.wikipedia.org/wiki/Common_Sense_on_Mutual_Funds).
3. David F. Swensen, *Unconventional Success* — six core asset classes, diversification as "the rare free
   lunch," disciplined rebalancing, low-cost index funds. Wikipedia
   (https://en.wikipedia.org/wiki/David_F._Swensen); OptimizedPortfolio Swensen review
   (https://www.optimizedportfolio.com/david-swensen-portfolio/).
4. Ray Dalio, *Principles* / Bridgewater All Weather — four economic environments, risk parity (allocate by
   risk contribution, not dollars), "equity with a bond sidecar." Bridgewater, "The All Weather Story"
   (https://www.bridgewater.com/research-and-insights/the-all-weather-story);
   OptimizedPortfolio (https://www.optimizedportfolio.com/all-weather-portfolio/).
5. Antti Ilmanen, *Expected Returns: An Investor's Guide to Harvesting Market Rewards* — multi-factor return
   drivers (market/value/momentum/carry/defensive); factor diversification ~halves vol, ~doubles Sharpe.
   AQR book page (https://www.aqr.com/Insights/Research/Book/Expected-Returns-An-Investors-Guide-to-Harvesting-Market-Rewards);
   CFA Institute Research Foundation
   (https://rpc.cfainstitute.org/sites/default/files/-/media/documents/book/rf-publication/2012/rf-v2012-n1-1-pdf.PDF).
6. Clifford Asness, Tobias Moskowitz, Lasse Pedersen, "Value and Momentum Everywhere," *Journal of Finance*
   (2013) — value/momentum negative correlation (~−0.49), combination raises Sharpe. AQR
   (https://www.aqr.com/Insights/Research/Journal-Article/Value-and-Momentum-Everywhere);
   SSRN (https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2174501).
7. Howard Marks, *The Most Important Thing* — second-level thinking, risk as probability of permanent loss
   ("risk resides where it is least perceived"), market-cycle pendulum, defensive investing.
   Columbia University Press (https://cup.columbia.edu/book/the-most-important-thing/9780231153683/);
   James Clear summary (https://jamesclear.com/book-summaries/the-most-important-thing-illuminated).
8. Nassim Nicholas Taleb, *Antifragile* — barbell strategy, via negativa, convex tail bets, skin in the game,
   avoiding the fragile middle. QuantifiedStrategies on the barbell
   (https://www.quantifiedstrategies.com/nassim-taleb-strategy/);
   grahammann.net book notes (https://grahammann.net/book-notes/antifragile-nassim-nicholas-taleb).
9. Daniel Kahneman, *Thinking, Fast and Slow* — loss aversion (~2× pain of loss), overconfidence / illusion
   of skill, anchoring, narrow framing. Wikipedia
   (https://en.wikipedia.org/wiki/Thinking,_Fast_and_Slow);
   Advisor Perspectives (https://www.advisorperspectives.com/articles/2012/06/05/daniel-kahneman-on-the-two-kinds-of-thinking-fast-and-slow).
10. Aswath Damodaran, *Valuation* / "10 Rules for Addressing Uncertainty" — valuation is a range not a point,
    don't bury uncertainty in the discount rate, normalize/average inputs, market price as a bias check.
    CFA Institute Enterprising Investor
    (https://blogs.cfainstitute.org/investor/2012/12/19/addressing-uncertainty-in-investment-valuations/);
    Damodaran, "DCF Myth 3" (https://aswathdamodaran.blogspot.com/2016/05/dcf-myth-3-you-cannot-do-valuation-when.html).
11. Joel Greenblatt, *The Little Book That Beats the Market* — Magic Formula (rank by earnings yield EBIT/EV
    + return on capital, buy a basket). Referenced via `analyse-fundamental` SKILL.md and standard
    descriptions of the formula.

*Educational analysis, not advice; you place the orders.*
