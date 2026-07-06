# Intraday-Bot Research Roadmap — 2026-07-02

Head of research, next-cycle plan. Scope unchanged: $500 Alpaca crypto account, long-only spot, no leverage/shorts/derivatives, 5m–1d bars, 0.15%/0.25% maker/taker per side (~30bp maker / ~50bp taker round trip). Gate unchanged: OOS Sharpe > 0 net of costs, DSR prob ≥ 0.95, all stress tiers simultaneously, beat buy-and-hold risk-adjusted, independent adversarial reproduction. IS = 2020–2023, OOS = 2024–2026H1, fixed before tuning.

---

## 1. Where we stand

0/3 strategies passed the gate this cycle, all independently verified: `regime_sma_maker` has a real-looking edge (OOS Sharpe +0.58, CAGR +19.2%, maxDD −27.7% vs hold-BTC −53%, beats buy-and-hold) but failed on statistical significance and its honest bar-by-bar fill sim goes Sharpe-negative under the 1-bar-delayed-fill tier; `xs_momentum` is a textbook overfit (IS +1.77 → OOS −0.57, loses to equal-weight hold of its own universe); `meanrev_maker`'s gross edge is negative before fees (OOS −10.3), so the signal family — not the execution layer — is dead. The two killers this project keeps meeting are round-trip costs (30–50bp swamps any edge below ~2x that per trade at realistic frequencies) and significance (nothing has yet cleared even the single-trial DSR hurdle of annualized Sharpe ~1.04 on the 2.5y OOS window). The one live evidence stream is the notify-mode shadow deployment of the trend filter, which is accumulating pre-registered forward daily bars (~365/yr) — the only kind of data that can lower the hurdle without spending trials.

---

## 2. Step 0 — fix the gate itself (mandatory before any new trial)

The DSR audit root-caused a units bug in `core/gate.py`. Every DSR number in `results/*.json` is wrong in magnitude.

**The bug.** `deflated_sharpe_ratio()` (`core/gate.py:279`) defaults `sharpe_var_trials` to `1.0` when the caller omits it, and the call site (`core/gate.py:515`) never passes it. So `E[maxSR]` (lines 282–285) is computed in units of the SR-estimator's *standard deviation* (0.5198 for N=2), while the observed Sharpe passed in is in *per-bar* units (0.576/√365 = 0.0301). Under the null the cross-trial variance of per-bar SR estimates is ~1/T = 1/913, so the threshold is √913 ≈ 30.2x too large; line 292 then multiplies the mis-scaled gap by √(T−1), manufacturing |z| ~ √T garbage (the reported z = −14.8 / −15.0 / −40.2). Fingerprint confirming root cause: 0.5197553/√913 = 0.0172014, exactly the correct per-bar E[maxSR] for N=2. The docstring's claim that var=1.0 is "a conservative default per the paper's guidance" is false — it equals an annualized-equivalent noise-Sharpe threshold of **9.9**, which no strategy could ever clear. The bug scales with T: at 5m bars (T=262,944) the variance default is off by a factor ~T (≈260,000x; threshold off ~√T ≈ 513x), so any 1h/5m candidate would report DSR prob ≈ 0 regardless of true quality. Secondary defect: line 515 also omits skew/kurtosis of the OOS returns (defaults 0/3) — numerically minor (BTC z 0.391 → 0.395).

**The fix.** Default `var_sr` to the null per-bar SR-estimator variance `(1 − skew·SR + (kurt−1)/4·SR²)/n_obs` (or simply `1/n_obs`), or accept empirical cross-trial variance; have the caller at `gate.py:515` pass skew and raw kurtosis computed from the OOS net-return series. (The two audit inputs propose the same fix at different precision — moment-adjusted vs plain `1/n_obs`; take the moment-adjusted form, it's what Bailey–López de Prado specify.) Audit every other consumer of `deflated_sharpe_ratio` for the same default. Regenerate all `results/*.json` and correct the language in `RESULTS.md`/`TDD.md`.

**Corrected numbers** (reproduced bit-for-bit against committed code + data, then recomputed with real OOS moments — BTC skew +0.757, raw kurt 10.89; ETH +0.885/13.43):

| Strategy / leg | N trials | z (corrected) | DSR prob (corrected) | Old reported |
|---|---|---|---|---|
| regime_sma_maker BTC | 2 | +0.395 | 0.654 | z=−14.78, prob 0.00 |
| regime_sma_maker BTC | 5 (honest family count) | −0.284 | 0.388 | — |
| regime_sma_maker ETH | 2 | +0.130 | 0.552 | z=−15.05, prob 0.00 |
| regime_sma_maker ETH | 5 | −0.548 | 0.292 | — |

**Iron-rule caveat, stated explicitly:** fixing a units bug makes the gate *correct*, not looser. The 0.95 probability bar, the cost model, the fill sim, and the stress tiers are untouched. The honest statement replacing "z=−14.8" is: "DSR prob ~0.65 (BTC, N=2) — statistically indistinguishable from picking the best of 2 noise trials."

**No verdict flips.** 0/3 remains 0/3: `regime_sma_maker` still fails DSR ≥ 0.95 even corrected (0.65 best case), and its delayed-fill tier failure stands independently of the DSR fix; `xs_momentum` and `meanrev_maker` are dead on raw negative OOS Sharpe, for which no significance correction matters. Do not use the corrected numbers to justify deployment — the pre-registered notify-mode shadow run remains the right forward test.

---

## 3. The hurdles any idea must clear

**Required annualized OOS Sharpe for DSR prob ≥ 0.95** (corrected formula, Gaussian moments; verified against the gate's own math shape):

| N trials | 910 daily bars (~2.5y, current OOS) | 17,520 hourly (2y) | 262,944 5m (~2.5y) |
|---|---|---|---|
| 1 | 1.04 | 1.16 | 1.04 |
| 2 | 1.37 | 1.53 | 1.37 |
| 5 | 1.80 | 2.01 | 1.79 |
| 10 | 2.04 | 2.28 | 2.04 |
| 20 | 2.25 | 2.51 | 2.24 |
| 50 | 2.49 | 2.77 | 2.48 |

**Same hurdle vs OOS calendar span** (daily bars; hurdle scales ~1/√years):

| OOS years | N=1 | N=5 | N=20 | N=50 |
|---|---|---|---|---|
| 1 | 1.65 | 2.85 | 3.56 | 3.94 |
| 2.5 (now) | 1.04 | 1.80 | 2.25 | 2.49 |
| 5 (~2029) | 0.74 | 1.27 | 1.59 | 1.76 |
| 10 | 0.52 | 0.90 | 1.12 | 1.24 |

**Per-trade gross-edge floor** (net annualized Sharpe 1.0 target, 40% asset vol, iid trades):

| Trades/yr | Net edge needed | Gross needed (maker +30bp) | Gross needed (taker +50bp) |
|---|---|---|---|
| 12 | 333.3bp | 363.3bp | 383.3bp |
| 52 | 76.9bp | 106.9bp | 126.9bp |
| 150 | 26.7bp | 56.7bp | 76.7bp |
| 365 | 11.0bp | 41.0bp | 61.0bp |
| 1000 | 4.0bp | 34.0bp | 54.0bp |

(For Sharpe 1.5, scale the net column ×1.5: e.g. 500bp at 12/yr, 6bp at 1000/yr.)

**Implications.** There is no frequency band where the fee structure becomes irrelevant — it only changes the failure mode. At low frequency (12–52 trades/yr, the shape of our regime strategies) the required *net* edge per trade is 77–333bp, so costs are a rounding error next to the signal quality needed; at high frequency the gross floor asymptotes to the round-trip cost itself (34bp maker at 1000 trades/yr) and slippage/fill-probability risk dominates — the exact axis that already killed `meanrev_maker` and flipped `regime_sma_maker`'s delayed-fill tier negative. Bar granularity buys nothing: daily and 5m hurdles are identical at fixed calendar span, and 5m/1h autocorrelation means fine bars *overstate* effective T — a conservative grader should apply an effective-T deflator (block bootstrap), never treat finer bars as more evidence. More symbols don't substitute for more years either: at pairwise ρ = 0.6–0.85 (crypto majors), 10–20 coins give N_eff ≈ 1.2–1.4 — a variance-diversification lever, not independent evidence. Trials are brutally expensive (N=1→5 costs ~+0.75 required Sharpe); since nothing in this project's history has cleared even N=1's 1.04, any grid bigger than ~2–3 configs is self-defeating before it runs. The only viable shapes at 30bp RT are: (a) low-frequency strategies with genuinely huge per-trade edges (>100bp net), or (b) patient accumulation of forward calendar time on something already pre-registered. Nothing in the current pipeline is close to (a).

---

## 4. Ranked candidates

**None survive.** Both candidates that reached hostile review were killed (`verdict.survives = false` on each). The honest output of this cycle's ideation is an empty deployable list plus two documented dead-family entries — which is dead-idea-log value, not zero value. The ranked-candidate section of the next roadmap should only ever contain ideas that clear the Section 3 arithmetic *on paper* before a single OOS look is spent.

### Killed on arrival (append to dead-idea log)

- **btc_vol_regime_exposure_scaling** (vol-structure; Moreira–Muir exposure scaling, 3 bands, 8 trades/yr, maker-only): killed on DSR arithmetic — required OOS Sharpe 1.37 (N=2 at face value) to ~1.86 (honest N=6: BTC/ETH/SOL × 2 configs), unreachable for a 25–100%-invested defensive overlay whose literature benchmark is Sharpe *improvements* of a few tenths; net alpha ~2.8%/yr collapses to 0.4%/yr under the 2x-fee tier alone, with trades structurally clustered in the worst-vol windows the slippage tier punishes; mechanism transfer to BTC unproven (vol spikes accompany melt-ups, and the OOS window was a bull run); 20d-vol + 3-day hysteresis is too lagged to capture the 1–3-day tail events the edge lives in; overlap with the dead SMA-regime family asserted, never measured. Reviewer's salvage note: the one legitimate follow-up costs zero DSR budget — compute the correlation of the rv-percentile regime series against `regime_sma_maker`'s regime series; high correlation kills it permanently as a disguised retune, low correlation still doesn't justify trials until a design plausibly reaching Sharpe > 1.4 exists.
- **funding_extreme_contrarian_spot** (derivatives-positioning; buy spot at deep-negative funding percentile, 12 trades/yr): killed on DSR infeasibility (needs ~1.37 at N=2; realistic delivery ~0.2–0.6) despite clean cost math (90bp/trade net at base fees, 60bp at 2x — costs are *not* what kills it); same skeleton as the dead mean-reversion family with the input series swapped; funding troughs mechanically co-occur with liquidation-cascade days — the exact delayed-fill failure mode already demonstrated; evidence base self-rated WEAK (one hindsight-selected FTX-low anecdote plus a theory paper proving only that *funding* mean-reverts, not that spot price drifts up net of costs). Reviewer's note: if ever run, run once, exactly as pre-registered, solely to convert "maybe" into a documented dead family — no follow-on retunes on a lucky-looking result.

Standing dead families (firewalled, no retunes, each new trial raises its own DSR bar): BTC/ETH price-above-SMA variants; lookback-return cross-sectional momentum on this coin universe; 5-minute rolling z-score mean-reversion.

### Round-2 kills (2026-07-06, crypto — full arithmetic in `HUNT-ROUND2.md` §3; all firewalled)

1. **btc_hash_ribbon_capitulation_recovery** (P1) — honest Sharpe 0.40 vs 1.04 @N=1; ~1–2 completed OOS trades resolvable; lags price → likely inherits the dead price-SMA firewall. *Sanctioned free follow-up: regime-state correlation vs regime_sma_maker.*
2. **btc_onchain_fee_pressure_demand_proxy** (P0) — gross-vs-net fee-subtraction error; corrected Sharpe 0.00 at own fees, −0.26 to −1.04 at confirmed costs.
3. **cme_futures_lead_spot** (P1) — negative under 2x-fee stress at every real venue; assumed 10bp tier doesn't exist; delayed-fill erases a lead-lag arbs close in minutes.
4. **utc_hour_variance_drag_trim** (P0) — cost 66–330x gross edge; zero-fee ceiling 0.411; target hour measured on OOS (protocol violation).
5. **forced_deleveraging_reversion** (P1) — net 0.26–0.34 vs 1.37 @N=2; negative at 2x-fee; enters on worst-slippage bars, slippage unmodeled.
6. **stablecoin_basis_stress_filter** (P0) — zero-fee ceiling 0.495 vs 1.37; 0–1 qualifying depeg events in OOS.
7. **stablecoin_quotecurrency_routing_arb** (P0) — net −25bp/trade (Sharpe −1.56); triangle parity closed in microseconds vs 5m bars.
8. **btc_difficulty_adjustment_miner_capitulation_reversion** (P0) — net 0.17–0.36 vs 1.37; same causal story as regime_sma_maker which had a real 0.58 and still died on DSR.
9. **blue_chip_token_unlock_dip_reversion** (P1) — 4–11x short of 1.37; DOT "unlocks" are linear staking inflation (mechanism absent); realistic ~0–2 trades/yr.
10. **day-of-week / turn-of-month / session-open / expiry calendar effects (crypto)** (P0) — killed in round-1 addendum screening; entry restored here so the file matches the operative kill list.
11. **BTC-dominance / ETH-BTC ratio switching** (P0) — killed in round-1 addendum screening; entry restored here so the file matches the operative kill list.

### Round-3 kills (2026-07-06, US-equities pivot — full arithmetic in `HUNT-ROUND3.md` §3; all P0, firewalled)

Round-level finding: *US-equities pivot evaluated 2026-07-06 under repealed-PDT / 1.3–3bp RTH costs — venue strictly better, 0/18 candidates survive; the cost floor is experimentally eliminated as the binding constraint; short-horizon program dormant across both asset classes per HUNT-ROUND3.md §5.*

1. **PED-ON pre-earnings drift, overnight-only** — best-in-round: zero-decay + honest 9bp open-auction cost = 1.05 vs 1.04 (zero margin), then fails 2x-fee stress at 0.99; with McLean–Pontiff ~58% decay → 0.59.
2. **EAP-NIGHT earnings-jump premium night hold** — own expected 0.85 < 1.04; honest auction cost → 0.63; jump kurtosis raises the effective DSR bar further.
3. **MOR-X momentum-overnight rotation** — own claim 0.8 < 1.04; 9bp auction cost → 0.22; benchmark is 24h B&H of the same hot name (NVDA +171% in 2024).
4. **Gap-and-Go ORB on stocks-in-play** — mechanical 2x-fee stress FAIL at its own numbers (stress Sharpe −0.47); honest open cost ≥15bp → 0.06.
5. **SPY last-half-hour momentum** — gate Sharpe 0.00 once RF=4% is subtracted (claimed 1.15 omitted it); paper-faithful gross → −0.61.
6. **SPY full-day noise-band momentum (Concretum 1x long)** — self-reported 0.95 < 1.04; RF-corrected 0.23; published 1.33 needs short leg + 4x leverage, unavailable at $500.
7. **IBS-LowClose reversal (QQQ)** — replication caught 25.8 trades/yr not the claimed 55; gate Sharpe 0.37 on its OWN IS window; effect dead 2014–2019.
8. **RSI(2)-in-uptrend pullback (SPY)** — replication: 7.5 trades/yr not 17; 3.3%/yr < 4% RF → gate Sharpe −0.11 on its own IS.
9. **Uptrend gap-down fade (QQQ)** — load-bearing 77% gap-fill statistic measures 58% (IS) / 48% (2014–19); wrong-sign in both windows.
10. **Earnings-announcement premium carrier** — claimed 1.1 was GROSS; net 0.98 < 1.04 at face value; decayed-honest 0.19.
11. **Pre-announcement drift in past winners** — √150 treats 3 concurrent ρ≥0.5 AI-cluster names as independent; corrected 0.53–0.89 vs 1.37 @N=2.
12. **Residual short-term reversal ex-news** — own arithmetic 0.82 GROSS < 1.04; its own citations document the post-2010 decay → 0.16.
13. **Turn-of-month window (SPY/RSP)** — RF subtraction collapses raw 0.67–0.79 to 0.29–0.68; 33% exposure can't beat SPY OOS B&H (21.4%/yr, Sharpe 1.05).
14. **TOM ∪ macro-day composite (SGOV cash leg)** — SGOV carry only offsets RF, adds zero gate Sharpe; honest 0.71; delayed fill deletes the announcement-day leg.
15. **Sequential earnings-announcement premium** — own optimistic 30bp/event → 0.63; published 9.9bp → 0.09; single-bar edge fails delayed-fill by construction.
16. **VRatio contango gate (SVXY)** — IS best-case 0.71 vs 1.04; claimed 30%/yr refuted by SVXY B&H itself (4.2%/yr OOS while contango ~80% of days).
17. **Leverage rotation TQQQ/T-bills (Gayed–Bilello)** — own expectation 1.0 < 1.04; exact-spec IS 0.91; OOS benchmark TQQQ B&H +227%; one confirmed ~20% whipsaw (Mar–May 2025).
18. **Volatility-targeted TQQQ** — claimed margin over bar = 0.01 (inside noise); realized IS uplift +0.07 not +0.15–0.20; leverage cap never binds at 21% OOS vol.

**What the next cycle's ideation must produce:** genuinely new signal families whose *paper* arithmetic clears Section 3 — i.e., a credible path to annualized OOS Sharpe ≥ 1.37 at N=2, which at realistic frequencies means either >100bp/trade net edges (low-k) or a reliably-present ~10–40bp gross-over-cost edge repeated hundreds of times per year with maker fills surviving the delayed-fill tier (high-k). Candidates that can't state that path in one paragraph don't get a backtest.

---

## 5. Process changes (binding from this date)

1. **Fix the gate first** (Section 2). No new candidate is scored until `core/gate.py` passes `sharpe_var_trials` correctly and the OOS skew/kurt, and all historical `results/*.json` are regenerated.
2. **One central trial ledger.** Append-only, family-keyed, committed to git (`intraday-bot/TRIAL_LEDGER.md` or JSON next to `results/`): one row per config ever run against OOS — family id, exact param hash, git commit, IS Sharpe, OOS Sharpe, cumulative family N at run time. N is the running cumulative count per family, never resettable by renaming or "re-launching." `regime_sma_maker`'s honest count is **5, not 2** (per its own JSON note) — seed the ledger with 5 and grade it at N=5 (corrected DSR prob 0.388 BTC / 0.292 ETH) going forward.
3. **Pre-register before touching OOS.** Commit a frozen param grid (the commit is the timestamp) before any code sees 2024–2026H1 data; pick the winner using IS-only (2020–2023) expanding-window CV; run exactly one frozen config against OOS. Ledger N = the size of the pre-registered grid, not 1 — picking the IS winner is the multiple-comparison event.
4. **Hard cap ~5 configs per family**, enforced before running. At N=5 the current window demands Sharpe ≥ 1.80; a family needing more than 5 configs to find a candidate is itself evidence of fragility — shelve it. IS pre-filter: require IS Sharpe ≥ 1.5–2x the family's OOS hurdle at its current N before spending an OOS look at all.
5. **OOS is single-use per config.** One observation per config. A retune after seeing OOS is a new trial (N += 1) and must be evaluated on fresh forward bars, not re-scored against the window it just lost on.
6. **Dead-family firewall.** No trials inside the three dead families or the two killed-on-arrival entries above. Expected value is negative before the backtest runs.
7. **Session carry-forward.** Every future gate run reads the trial ledger first; "new investigation" framing does not reset N.

**Pre-registered fresh-symbol confirmation for the trend family (explicitly NOT a retune).** The context defines what would count as new evidence for `regime_sma_maker`: out-of-family confirmation on a pre-registered symbol set. Protocol: commit, before running anything, the exact frozen rule (identical 50d-SMA regime logic, identical maker execution, zero parameter changes) and the exact symbol list; run once; log the run in the ledger as confirmation evidence, not a new config. Honest framing of what this buys: because crypto majors correlate 0.6–0.85, N_eff for added symbols caps near 1.2–1.4 — this is a *falsification* test (a frozen-rule failure on new symbols is strong evidence against the family) far more than a significance booster. Do not present a cross-symbol pass as if it materially moved the DSR needle; the two inputs agree on this and the roadmap should not smooth it over.

**How shadow-run forward data will be scored.** The notify-mode deployment adds ~365 genuine forward daily bars/yr to `regime_sma_maker`'s (and only its) OOS evidence. Scoring rules: (a) fixed rule, zero adjustments after observation; (b) graded with the *corrected* DSR at the family's cumulative ledger N (5); (c) the delayed-fill stress tier must pass on the forward data too — the DSR fix does not amnesty the fill-sim failure; (d) expected payoff is the slow √years grind: 2.5y → 3.5y drops the N=1 hurdle 1.04 → ~0.88, so set review checkpoints (e.g., every 6 months) rather than peeking continuously — each peek-and-react is a trial.

---

## 6. The honest null path

If the next cycle also fails, the correct move is the one this repo has already validated: **do nothing intraday.** The repo's own gated study found hold/mid-risk beats day-trading after costs, and a separate standing prior ("scalable alpha is a mirage") records four other OOS-refuted signals this year (one hostile reviewer cited five — un-reconciled, flagging rather than smoothing; either count supports the same prior). For the $500 account that means: hold the asset (or the mid-risk allocation), keep the trend filter in notify-only shadow as a passive monitor, spend zero further trials.

**Evidence that would justify stopping intraday research entirely:**

1. **Structural:** the Section 3 arithmetic already shows the required Sharpe (1.04–2.49 depending on N) sits 2–4x above the best OOS result this project has ever produced (0.58), and the per-trade cost floor has no escape band at 30bp RT. If one more full cycle of genuinely-new families (≤2 families, ≤5 pre-registered configs each, corrected gate) again produces nothing above the N=1 hurdle, the base rate becomes 5+/5+ family failures and the structural argument is confirmed, not merely suspected.
2. **Forward:** the shadow run is the trend family's last live claim. If after ~12 more months of forward bars the frozen rule still fails corrected DSR at its honest N *or* still fails the delayed-fill tier on forward data, the family — and with it the only strategy that ever beat buy-and-hold here — is closed.
3. **Opportunity cost:** the window math says the passive path improves on its own (~1/√years) while research trials only raise the bar. When the do-nothing option strictly dominates the expected value of the next trial, stop. Archive the dead-idea log (`backtests/results/intraday_bot_summary.txt` plus Section 4 above) as the deliverable: knowing these families are dead, with receipts, is the asset.

No loosening of costs, fills, or windows to manufacture a PASS — under any outcome.

---

## Addendum — flow/event-driven direction (recovered from a crashed research branch)

The flow/event-driven ideation agent completed its analysis but crashed on output formatting; its findings were recovered from the transcript and belong in the dead-idea record. It screened 4 sub-signals and rejected all 4 — zero trial budget spent:

1. **US spot BTC/ETH ETF net flows** — rejected on data availability: free history (Farside) starts 2024-01 (BTC) / 2024-07 (ETH), so the fixed IS window (2020–2023) has zero flow data and nothing can be pre-registered on IS. Flows also chase recent returns, so the signal likely re-derives the dead price-above-SMA family. Revisit no earlier than ~2028 when the flow series spans enough calendar time to hold out an IS period.
2. **Stablecoin supply growth / SSR** — rejected on evidence and edge size: SSR is price-dominated (repackaged price mean-reversion, a dead family); the clean mint/burn variant has point-in-time-safe free data (DefiLlama) but only contested single-actor evidence (Griffin & Shams 2020, with CEPR counter-evidence) and an honest gross-edge estimate of ~10–30bp/trade, below the 60bp (2× round-trip) floor.
3. **Exchange listing/delisting events** — rejected on direction and universe: the documented "Coinbase effect" accrues *before* announcement and turns negative after, so the tradeable side is a fade requiring shorts (banned); Alpaca's universe contains only coins listed on major venues months-to-years earlier, so the event essentially never fires in-universe.
4. **Halving-cycle phase** — rejected on statistical power: two halvings in the whole 2020–2026 dataset; a filter that changes state twice cannot clear any DSR bar.
