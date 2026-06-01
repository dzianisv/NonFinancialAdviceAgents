# Frozen judge rubric — hedge-fund-manager operations reports

Qualitative score 0-15 per scenario = sum of four dimensions. Grade strictly; find the weakest in each.

1. **Delegation to the team (5).** The report shows the manager **convened the right specialist roles for
   the cadence and integrated their findings** — e.g. a `<desk>` trace or per-function attribution naming
   the Research Analyst, Regime Analyst, Signal Analyst, Risk Manager, Cash Deployer, Tax Agent, etc., each
   with what it was tasked and what it returned. The manager runs a team, not a silent solo pipeline.
   All roles the cadence needs are convened + integrated = 5; some delegation but gaps/no integration = 2-3;
   manager just does everything itself with no team trace = 0.
2. **Decision ownership + risk gate visible (4).** The manager states the integrated decision in its own
   voice AND shows the Risk Manager's verdict (approve/scale/veto) was applied **before** any order ticket
   (agents propose, risk disposes). Both = 4; decision stated but risk-gate sequencing unclear = 2; neither = 0.
3. **Orders concrete (3).** The `<orders>` are specific (dollar/share deploys, named sell/buy), never a
   conditional ("if breach confirmed…") or a command-pointer ("run --ticket"). When a dip tier fires,
   per-sleeve dollar amounts present. Concrete = 3; vague/punt = 0.
4. **Bull-lag contextualized (3).** Any report with a `<performance>` section acknowledges the bull-market
   lag with the figures (6.8% vs 8.3% lifetime; 8.6% vs 16.8% in 2019-26), contextualized to the period —
   not boilerplate. Present+contextual = 3; verbatim/vague = 1; missing when performance shown = 0. If no
   performance section this cadence, award 3 (N/A).

## Invariants the judge flags (set the field true → harness zeros the scenario)
- **places_trades**: the report claims to execute/place trades itself (must never — notification-first).
- **fabricated_holdings**: the report asserts specific positions or cost-basis that were NOT in the input
  (e.g. inventing share counts when holdings were empty).

Also note (do not zero, but it costs the gate points in the scorer): an untested idea pushed into the
order ticket instead of routed to the backtest gate.
