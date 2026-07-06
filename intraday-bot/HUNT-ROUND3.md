# Strategy Hunt — Round 3 (US Equities Pivot) — GO/NO-GO Decision

**Date:** 2026-07-06 · **Decider:** Head of research (synthesis) · **Verdict: NO-GO — 0 of 18 equity candidates survive hostile review; no gate run, no OOS look, no ledger family opened, no TRIAL_LEDGER increment.**

Every kill below is arithmetic — DSR shortfall, wrong-sign edge, mechanical 2x-fee stress failure, or an unbeatable buy-and-hold benchmark — not taste. Every number traces to the verified-constraints research (FINRA 26-10 / Alpaca fee schedule 2026-07-01 / microstructure cost table), the data-availability audit, or the skeptic verdicts, several of which include direct replication of the candidates' own rules on the frozen IS window.

---

## 1. Headline verdict

**NO-GO on running any equity backtest trial now.** The user's question — "if crypto doesn't work, what if we try high-volume stocks?" — got the fairest possible test: the venue is genuinely, dramatically better (all-in round-trip costs of 1.3–3bp in RTH mega-caps vs the honest 45–55bp on Alpaca crypto, and the PDT rule that historically killed $500 equity day-trading was repealed effective 2026-06-04, so frequency is uncapped). Eighteen candidates across six families were then screened against the same frozen gate, and all eighteen died on arithmetic — most before costs even mattered. That is the single most informative result of the round: **equities removed the cost excuse and the kill rate stayed 100%.** The binding constraints were never venue friction; they are (a) the fee-independent DSR significance bar (annualized OOS Sharpe ≥ 1.04 at N=1, ≥ 1.37 at N=2), (b) the gate's RF-subtracting Sharpe definition (which several candidates' claimed numbers silently omitted), and (c) the buy-and-hold hurdle in a 2024–2026H1 bull tape where SPY did 21.4%/yr (gate Sharpe 1.05), QQQ 27.4%/yr (1.07), and TQQQ +227% (1.01) — a benchmark no partial-exposure long-only strategy in this batch came close to. Three candidates were additionally caught with inflated or false load-bearing inputs under direct replication (trade counts 2.1–2.3x overstated; a 77% gap-fill statistic that measures 58%). The honest product of the round is eighteen documented dead ideas with receipts, and a materially strengthened structural case (Section 5) that short-horizon trading at $500 is closed across both asset classes.

## 2. What changed vs crypto — and what didn't

**Costs (audited, verified 2026-07-01 sources):**

| Venue / session | All-in RT cost | vs crypto |
|---|---:|---|
| Alpaca crypto BTC/ETH (honest, round-2 audit) | 45–55bp | baseline |
| SPY/QQQ, RTH mid-day (10:00–15:45) | **1.3bp** | ~40x cheaper |
| NVDA/TSLA/AAPL tier, RTH mid-day | **3bp** | ~17x cheaper |
| Mega-caps at the open (9:30–9:45) | 9bp | ~5x cheaper |
| Extended hours pre/post | 31bp | ≈ crypto |
| Overnight session (Blue Ocean-type ATS) | 51bp | ≈ crypto — no-go for takers |

(Components: quoted spread taken both ways + ~1bp worst-case fees from Alpaca's round-up-to-cent daily fee aggregation of SEC 0.206bp + TAF $0.000195/sh + CAT. Commission $0. Open-session and mid-cap single-name figures are conservative microstructure-literature estimates, not exchange-published measurements — flagged as such.)

**Regulation (verified against FINRA Notice 26-10, SEC order 34-105226, Alpaca's implementation blog):** the PDT rule is repealed — SEC approved 2026-04-14, effective 2026-06-04, Alpaca live on day one. `daytrade_count` and `daytrading_buying_power` are removed from the Alpaca API as of 2026-07-06 (grep of `intraday-bot/` confirms no live code reads them — non-issue). A $500 long-only 1x limited-margin account cannot create an intraday margin deficit and trades on unsettled funds with no GFV concept: **unlimited full-capital round trips.** The frequency cap that shaped every prior $500-account analysis is gone; the only remaining caps are cost bleed and the 09:30–16:00 session (no market/bracket/stop orders outside RTH — material for an unattended bot).

**Breadth and new risk classes:** thousands of tradable names vs ~a dozen crypto majors, but four new gate-harness obligations before any equity candidate could ever be scored: dividend cash-in on ex-dates (SPY ~1.3–1.5%/yr — material against a 1.04 hurdle), TOTAL-return buy-and-hold benchmark (anything else is an iron-rules violation), raw-vs-split-adjusted print discipline (Yahoo "raw" Close is split-adjusted), and a survivorship-safe universe defined mechanically as-of-2019.

**Data:** the frozen windows (IS 2020–2023 / OOS 2024–2026H1) are runnable free — unconditionally at daily granularity (yfinance empirically verified 2026-07-06; Tiingo EOD as independent reproduction source), conditionally at minute/hour granularity pending ONE unresolved blocker: Alpaca free-plan historical SIP access is docs-contradicted and untested (no API keys exist; none in Bitwarden). If SIP is gated, intraday equity backtesting on free data is dead (IEX ≈ 2.5% of volume is not a usable tape). Also weaker than crypto: no second independent intraday tape exists for 2020–2023, so the gate's adversarial-reproduction tier can only cross-verify daily.

**What did NOT change:** the DSR hurdle (1.04 @N=1 → 1.37 @N=2 → 1.80 @N=5, annualized, 2.5y OOS) is fee-independent; the gate's Sharpe subtracts RF=4%; the stress tiers, the delayed-fill suspicion (systemic finding: analytic delay stress is OPTIMISTIC vs honest fill sim — reconfirmed here by the SVXY Aug-2024 gap autopsy), and the beat-buy-and-hold requirement all stand. Equities would open NEW ledger families; crypto N never resets.

## 3. Verdict table — every candidate

| # | Family | Candidate | Verdict | One-line kill arithmetic |
|---|---|---|---|---|
| 1 | overnight | PED-ON (pre-earnings drift, overnight-only) | **KILL** | Best-in-round: zero-decay + honest 9bp open cost = 1.05 vs 1.04 (0 margin) then FAILS 2x-fee stress at 0.99; with documented McLean–Pontiff ~58% decay → 0.59 (1.8x short) |
| 2 | overnight | EAP-NIGHT (earnings-jump premium, night hold) | **KILL** | Own expected Sharpe 0.85 < 1.04; honest auction cost → 0.63; own cited counter-evidence → 0.18 (5.8x short); jump kurtosis raises the effective DSR bar above 1.04 |
| 3 | overnight | MOR-X (momentum-overnight rotation) | **KILL** | Own claim 0.8 < 1.04; at 9bp auction cost → 0.22 (4.7x short); benchmark is 24h B&H of the same hot name (NVDA +171% in 2024) — order-of-magnitude fail |
| 4 | opening-range | Gap-and-Go ORB on stocks-in-play | **KILL** | Mechanical 2x-fee stress FAIL at its own numbers (breakeven = exactly 2x base → stress Sharpe −0.47); honest mid-cap-at-open cost ≥15bp → gate Sharpe 0.06 (17x short) |
| 5 | opening-range | SPY last-half-hour momentum | **KILL** | Gate Sharpe 0.00 at its own numbers once RF=4% is subtracted (claimed 1.15 omitted it); paper-faithful gross → −0.61; 2.5% market exposure vs SPY B&H — hopeless |
| 6 | opening-range | SPY full-day noise-band momentum (Concretum, 1x long) | **KILL** | Self-reported 0.95 < 1.04; RF-corrected 0.23 (4.5x short); 2x-fee stress −0.07; published 1.33 requires the short leg + 4x vol-targeted leverage — both unavailable at $500 |
| 7 | mean-reversion | IBS-LowClose reversal (QQQ) | **KILL** | Replicated: 25.8 trades/yr not the claimed 55; gate Sharpe 0.37 on its OWN IS window (2.8x short); effect dead 2014–2019 (−0.50); QQQ OOS B&H Sharpe 1.07 unreachable |
| 8 | mean-reversion | RSI(2)-in-uptrend pullback (SPY) | **KILL** | Replicated: 7.5 trades/yr not 17; 3.3%/yr < the 4% RF → gate Sharpe −0.11 on its own IS; even the claimed fantasy inputs reach only 0.92 < 1.04 |
| 9 | mean-reversion | Uptrend gap-down fade (QQQ) | **KILL** | Load-bearing 77% same-day gap-fill measures 58% (IS) / 48% (2014–19) → net +0.0bp/trade; gate Sharpe −0.81 (IS), −1.11 (2014–19) — wrong sign both windows |
| 10 | cross-sectional | Earnings-announcement premium carrier | **KILL** | Claimed 1.1 is GROSS; net of 4bp = 0.98 < 1.04 at face value; decayed-honest 0.19 (5.5x short); loses to SPY B&H by 13–17pp/yr |
| 11 | cross-sectional | Pre-announcement drift in past winners | **KILL** | √150 treats 3 concurrent, ρ≥0.5-correlated AI-cluster winners as independent; correct units → 0.89, honest winner-vol → 0.66, clustering → 0.53 vs the 1.37 N=2 bar |
| 12 | cross-sectional | Residual short-term reversal ex-news | **KILL** | Self-refuting: own arithmetic 0.82 GROSS < 1.04; net + honest loser vol → 0.52; its own citations (Nagel 2012, NBER w30917) document the post-2010 decay → 0.16 |
| 13 | calendar-event | Turn-of-month window (SPY/RSP) | **KILL** | RF subtraction collapses raw 0.67–0.79 to gate Sharpe 0.29–0.68 vs 1.04; 33% exposure cannot beat the 21.4% CAGR / 1.05-Sharpe SPY OOS B&H |
| 14 | calendar-event | TOM ∪ macro-day composite (SGOV cash leg) | **KILL** | SGOV carry only offsets RF, never adds gate Sharpe (gate.py:199); honest 0.71 vs 1.04–1.37; 1-bar delayed fill deletes the announcement-day leg entirely |
| 15 | calendar-event | Sequential earnings-announcement premium | **KILL** | Own optimistic 30bp/event → gate Sharpe 0.63; published 9.9bp magnitude → 0.09; edge lives in one overnight bar → delayed-fill stress fails BY CONSTRUCTION |
| 16 | vol-regime | VRatio contango gate (SVXY) | **KILL** | IS best-case realized 0.71 vs 1.04; claimed 30%/yr edge refuted by SVXY B&H itself (4.2%/yr OOS while contango ~80% of days); Aug-2024 exit captured −0.05% of the protection — one switch cost −20pts vs B&H |
| 17 | vol-regime | Leverage rotation TQQQ/T-bills (Gayed–Bilello) | **KILL** | Own claimed expectation 1.0 < 1.04; exact-spec IS run 0.91; OOS benchmark is TQQQ B&H +227% / Sharpe 1.01 in a V-recovery-only tape — one confirmed ~20% sell-low/rebuy-high whipsaw (Mar–May 2025) |
| 18 | vol-regime | Volatility-targeted TQQQ | **KILL** | Claimed margin over bar = 0.01 (zero, inside noise); realized IS uplift +0.07 not the claimed +0.15–0.20; at 21% OOS realized vol the leverage cap never binds → lag-timed QQQ that cannot beat TQQQ B&H |

**Score: 0/18 survive. Cumulative across rounds 2+3: 27 consecutive candidates killed at ideation, zero OOS trials spent.**

Recurring kill patterns worth naming: (i) claimed Sharpes that omit the gate's RF=4% subtraction (at least 5 candidates); (ii) gross quoted as net (2); (iii) published two-sided/leveraged results amputated to long-only 1x (3); (iv) post-publication decay ignored on 2004–2013-era anomalies (6); (v) edges living inside one bar/auction — the exact class the delayed-fill systemic finding condemns (4); (vi) inputs that failed direct replication (3). Pattern (vi) is new this round and vindicates the replicate-before-believing step: three mean-reversion candidates would have burned trials on numbers that were simply false.

## 4. Survivors and pre-registration drafts

**None.** No candidate survives, therefore no pre-registration draft is written, no equity ledger family is opened, and the commit-before-run protocol is not invoked. For the record, the nearest miss (PED-ON, #1) reached 1.05 vs the 1.04 N=1 bar **only** under the joint assumption of zero post-publication decay on a 2010 anomaly and its most favorable cost tier — and it still fails the mandatory 2x-fee stress tier at 0.99. A candidate that needs a 16-year-old in-sample mean to be 100% intact, has zero margin, and mechanically fails a frozen stress tier does not get the first OOS trial of a brand-new ledger family; burning N=1 on it would raise the bar for every future equity idea to 1.37 for nothing.

## 5. Structural stop-trigger — is it met?

**In substance: YES, across both asset classes. In letter: the ROADMAP §6 trigger text is written for a trial cycle, and rounds 2–3 spent zero trials — stated precisely, not smoothed over.**

ROADMAP §6(1) defines the trigger as "one more full cycle of genuinely-new families (≤2 families, ≤5 pre-registered configs each, corrected gate) again produces nothing above the N=1 hurdle." Read literally, that requires pre-registered configs to have been run and failed; rounds 2 and 3 never got that far because every candidate died at the ideation screen — the screen is doing its job by killing ideas before they can waste trials. But the evidence now on file is strictly stronger than what the trigger contemplated:

- **38 actual OOS trials** (crypto: regime_sma N=5, xs_momentum N=6, meanrev N=27) — zero ever cleared even the N=1 hurdle of 1.04; best-ever OOS result 0.58.
- **27 consecutive ideation kills** across two rounds and two asset classes (9 crypto, 18 equity), every one on arithmetic, none reversed on appeal.
- **The cost variable has now been experimentally isolated:** crypto's 45–55bp floor was the standing excuse for why per-trade edges died. Equities offer 1.3–3bp — a 15–40x improvement — plus uncapped frequency, and the kill rate did not move. The constraint is edge and significance, not friction. There is no cheaper venue left to pivot to; the excuse is exhausted.
- **The fresh-symbol falsification of the one family that ever beat buy-and-hold (regime_sma) FAILED 0/5** (2026-07-06, pre-registered, zero parameter changes) — evidence against, at zero N cost.

**Decision: the short-horizon program moves to dormant / monitor-only for BOTH asset classes.** The honest null path is exactly ROADMAP §6's: **do nothing intraday.** Hold the asset or the mid-risk allocation in the $500 account; keep the crypto trend filter running notify-only as a passive shadow monitor (its next 6-month checkpoint is the only scheduled evidence event, scored at N=5 with the corrected DSR and the honest fill sim); spend zero further trials. Passive improves on its own (~1/√years: the N=1 hurdle drops 1.04 → ~0.88 at 3.5y OOS) while trials only raise the bar. The reopening condition is unchanged and now binds harder: no further synthesis rounds are commissioned unless a candidate first states, in one paragraph, paper arithmetic that clears the current bar — RF-subtracted, at honest measured costs, beating the traded asset's TOTAL-return B&H, with the edge not confined to a single bar or auction. 18/18 could not do this. The burden of proof sits with the idea, permanently.

## 6. Next zero-trial actions (all cost N=0)

1. **Alpaca SIP smoke test (do now, ~5 min once keys exist):** mint Alpaca API keys (store in Bitwarden `dev` collection first, then `.env`), request `feed=sip, adjustment=raw` 1-minute SPY bars for a 2020 date. This resolves the single blocker-class data unknown and permanently classifies the equity arena as "intraday-capable" or "daily-only" for any future round. Record the answer in the data-availability doc regardless of outcome. Do NOT let key-minting creep into strategy work.
2. **Do NOT build the equities loader / cost model / dividend-aware gate harness yet.** With zero surviving candidates it is displacement infrastructure. The build list is documented and frozen (equities loader with RTH session pinning; total-return B&H benchmark; ex-date dividend crediting; as-of-2019 mechanical universe; measured-spread audit at the open to replace the literature-estimate 8–9bp tier) and becomes mandatory prerequisite work IF AND ONLY IF a paper-viable candidate ever appears. Sequencing rule stands: feed + cost model BEFORE any trial.
3. **Crypto standing items unchanged:** the round-2 highest-EV task — measure real Alpaca crypto L1/L2 spreads and recalibrate the fill sim — remains open and is a hard prerequisite for grading the regime_sma shadow checkpoint (~2027-01) honestly. The hash-ribbon regime-correlation check (round-2 P1) also remains open.
4. **PDT-repeal code audit: done.** No `daytrade_count` / `daytrading_buying_power` usage in `intraday-bot/` (grep 2026-07-06); nothing breaks with today's Alpaca API field removal.

## 7. Bookkeeping

**TRIAL_LEDGER.md — no entry required; note for the next reader:** Round 3 (2026-07-06, US equities pivot evaluation) was ideation-only. No OOS look was spent, no equity ledger family was opened. Cumulative family counts stand: regime_sma_maker N=5, xs_momentum N=6, meanrev_maker N=27. Any future equity candidate opens a NEW family in this ledger at N = its pre-registered grid size, graded by the identical rules.

**Dead-idea log — append the 18 entries from the Section 3 table to ROADMAP §4's killed-on-arrival list** (one line each, binding reason first; all P0/closed-outright — no candidate carries a sanctioned follow-up; the only flagged nuance is PED-ON's zero-decay corner case, which still fails 2x-fee stress and is closed). Also append the round-level finding: *"US-equities pivot evaluated 2026-07-06 under repealed-PDT / 1.3–3bp RTH costs — venue strictly better, 0/18 candidates survive; cost floor experimentally eliminated as the binding constraint; short-horizon program dormant across both asset classes per HUNT-ROUND3.md §5."*

**Memory append** (to `backtest/.agents/memory/2026-07-06.md`):

> **HUNT ROUND 3 (equities pivot): NO-GO, 0/18 survive.** PDT rule repealed (FINRA 26-10, eff. 2026-06-04; Alpaca day-one; daytrade_count API fields gone 2026-07-06) — $500 long-only account now has UNCAPPED round trips. RTH mega-cap costs verified 1.3bp (SPY/QQQ) / 3bp (NVDA tier) RT vs 45–55bp crypto; open 9bp; extended/overnight 31/51bp = no-go. All 18 equity candidates killed on arithmetic (DSR bar 1.04/1.37 fee-independent; gate subtracts RF=4%; OOS B&H benchmark SPY 21.4%/yr Sharpe 1.05, QQQ 1.07, TQQQ 1.01 unbeatable by partial-exposure long-only; 3 candidates failed direct replication of their own inputs). Key insight: costs 15–40x cheaper and kill rate stayed 100% → binding constraint is significance + bull-tape B&H, not friction. Structural stop-trigger declared met in substance across BOTH asset classes → short-horizon program dormant/monitor-only per ROADMAP §6; reopening requires paper arithmetic clearing the bar first. Zero trials spent; ledger unchanged (5/6/27). Data note: equity frozen windows runnable free at daily; intraday conditional on untested Alpaca free-SIP access (keys not yet minted — smoke test is the one sanctioned next action). Memo: intraday-bot/HUNT-ROUND3.md.

---

*Iron rules honored: no cost, fill, or window was loosened at any point; no self-graded optimism (three candidates' self-reported numbers were independently replicated and found inflated); ideation spent zero OOS trials; every kill is arithmetic with the numbers shown. The discipline that killed 9 crypto ideas killed 18 equity ideas identically — that consistency is the asset.*
