# Frozen judge rubric — tradfi-portfolio-manager weekly notes

Qualitative score 0-25 per note = sum of five dimensions. Grade strictly; find the weakest dimension in
each note. Award a dimension's max only if you actively looked for a flaw and found none.

1. **Bull-lag acknowledgment (6).** The note acknowledges the strategy's bull-market lag with specific
   numbers (e.g. 6.8% vs 8.3% lifetime; 8.6% vs 16.8% in 2019-26) **and contextualizes it to this week's
   regime/action** rather than pasting an identical boilerplate sentence. Specific + contextualized = 6;
   specific but verbatim boilerplate reused across notes = 4; vague = 2; absent = 0.

2. **Dip orders actionable (6).** If a dip tier fires, the note states per-sleeve **dollar** deploy amounts
   (tier% × $220K, split pro-rata weight/0.78) with correct arithmetic (check the largest sleeve). Correct
   = 6; wrong arithmetic = ≤3; punted to "run --ticket" when a tier fired = 0. No tier this week = N/A,
   award 6.

3. **Regime clarity (4).** Gives a score, or explicitly states the price-vs-200d-MA fallback and that the
   full score was not computed; **and** states the flip's session-persistence status OR that session
   history is unavailable — required even when the regime call is obvious from magnitude. Complete = 4;
   missing the session-persistence caveat = 3; partial = 2; missing = 0.

4. **Rebalance concreteness (4).** Quarter-end → concrete drift-check instruction with exact thresholds
   (>±20% relative or >±5% absolute, else hold). Non-quarter-end → correctly waived. Concrete/correct = 4;
   vague = 2; "pending verification"/"TBD" = 0.

5. **Action resolution (5).** The `<action>` line states what the PM determined.
   - A **documented, data-gated risk control** is CONCRETE correct behavior, not a punt: deploying Tier 1+2
     now while holding the Tier-3 sub-tranche pending a systemic-event check (VIX>40 / credit spreads) when
     that live data is unavailable is the strategy's written sell-discipline. Stating it explicitly = full
     marks.
   - A **lazy conditional** ("if breach confirmed…") or a **command-pointer** ("run --ticket for orders")
     in place of a determined action = 0.
   Concrete (incl. documented data-gated pause) = 5; lazy conditional / command-pointer = 0.

**places_trades** = true only if the note claims to execute/place trades itself (never should — it's
notification-first). True → the harness invariant gate zeros the whole score.

## Frozen invariants (never optimization targets; an edit that breaks one is auto-rejected)
- notification-first / never places trades
- the **Tier-3 systemic-event pause** (data-gated discretionary hold of the last sub-tranche) must remain
  present — it may be re-worded, never removed to chase points
- backtest-gate, risk caps, crypto separation
