# Token Selection — BTC-as-Hurdle (for alts)
> Source: Lyn Alden's "price everything in BTC" / value-accrual framework — see `analytics-lyn-alden` (already distilled) and the repo's `crypto/InfraTokens.md`. Distilled 2026-06.

## Core thesis
For any altcoin, the only question that matters is: **does it beat just holding Bitcoin?** Price everything **in BTC**, not in dollars — a token can 3× in USD and still *lose* against BTC, in which case owning it was a mistake. BTC is the **hurdle rate** of the asset class. The base rate is brutal, so the default answer for an alt is **no** unless it clears a demanding, explicit value-accrual filter.

## Key frameworks / mental models
- **Denominate in BTC.** Chart the token's price *in BTC* and its *BTC-denominated trend*. USD gains during a BTC bull are not alpha — they may be beta you'd have captured more cheaply by holding BTC.
- **The 6-point value-accrual filter.** An alt must plausibly pass *most* of these to justify a position over BTC:
  1. **Real fee → holder value accrual** — the protocol earns genuine fees that flow to token holders (not just emissions/inflation dressed up as "yield").
  2. **Enforced buyback/burn** — a credible, on-chain mechanism that ties usage to token value (not discretionary or promised).
  3. **Moat** — a durable network effect / switching cost / liquidity advantage, not a forkable feature.
  4. **Beats BTC in BTC-denominated trend** — the empirical test: is it actually out-trending BTC *in BTC terms*, not just rising in USD?
  5. **Low dilution** — modest, transparent emission schedule; not a VC/team unlock cliff that taxes holders.
  6. **Credible decentralization / security** — enough validator/node decentralization and security budget that it isn't a de-facto centralized app with a token.
- **Default to BTC.** If an alt can't clear the filter — especially #4 — the position defaults to BTC. No tilt, no DCA into it.

## Specific claims, mechanisms & data
- **Brutal base rate: 0 of 20 top alts beat BTC over 2017→2021.** The entire top-20 cohort underperformed simply holding Bitcoin across that full cycle — the empirical justification for treating BTC as the hurdle and alts as guilty-until-proven.
- **Most "yield" is emissions** — dilution disguised as return; the filter's #1/#2/#5 exist to catch exactly this.
- **The repo's infra-token work** (`crypto/InfraTokens.md`) applies a BTC-as-hurdle 6-point value-accrual screen; per repo memory, **HYPE was the only token passing** an earlier pass — illustrating how few clear the bar.

## How to APPLY (decision rules for alts)
1. **Re-denominate.** Pull the token's BTC pair and its BTC-denominated trend before anything else.
2. **Run the 6-point filter.** Be strict on #1 (real fees, not emissions), #2 (enforced, not promised), and #4 (actually out-trending BTC in BTC terms).
3. **If it fails — and most do — default to BTC.** Don't rationalize a USD chart.
4. **If it passes**, only *then* hand it to the execution layer (`04`) for a vol-target-sized, valuation-tilted DCA — and size it *smaller* than BTC to reflect higher idiosyncratic/failure risk (see `06`).
5. **Cross-ref** `analytics-lyn-alden` for the debasement / hardest-money logic behind the hurdle, and `crypto/InfraTokens.md` for the repo's worked screen.

## Caveats / where it hedges
- **Past base rates aren't destiny** — a genuinely novel value-accrual design *could* beat BTC; the filter exists to find the rare exception, not to ban all alts forever.
- **#4 is backward-looking** — out-trending BTC so far doesn't guarantee it continues; pair with the forward-looking #1–#3, #5–#6.
- **Alts carry stacked risks** BTC doesn't (smart-contract, governance, dilution, depeg) — see `06`; size accordingly.

## Memorable quotes
- "Bitcoin is the hurdle rate. If it doesn't beat BTC, in BTC, you should have just held BTC."
- "Most altcoin 'yield' is dilution wearing a costume."
- "Zero of the top twenty beat Bitcoin across the last full cycle — assume guilty until proven."
