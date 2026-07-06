# Strategy Discovery Plan

Goal: find one strategy that clears Stage 1 of the [readiness checklist](TDD.md#readiness-checklist). Written 2026-07-02, after three gate cycles produced 0 PASS from 3 candidates.

## The one lesson that shapes everything below

The gate works; the *ideas* were the problem. All three failures were signals any agent can compute cheaply from public price data — and the repo's own standing finding says exactly that: **anything cheap to compute from public data is already priced in**. So discovery is not "test more parameter variations" (that actively hurts — every trial raises the deflated-Sharpe bar the family must clear). Discovery is **finding better hypothesis families**, each with a stated economic reason someone pays us.

Where edge can plausibly live for a $500 account:
1. **Capacity-constrained niches** — things too small for professionals to bother with. $500 is an advantage here, not a handicap: we fit where funds can't.
2. **Getting paid for a service** — providing liquidity (maker rebates — partially validated: our fill simulator showed the maker mechanism itself works), taking the other side of forced flows (liquidations, funding resets).
3. **Behavior overlays, not prediction** — the regime filter's drawdown-halving was real; it failed significance, not economics. Risk-management edges survive longer than prediction edges.

## Answers to the two standing questions

**Should we read books about intraday trading?** Yes — but the systematic-trading kind, not the "day trade for a living" kind, and we read them the way this repo already does: distill → falsifiable spec → gate. We already own and distilled three relevant ones (`books/`):
- **Carver, *Systematic Trading*** — the best fit for our pipeline: position sizing, forecast combination, trading-speed-vs-cost math. Primary source for the next hypothesis batch.
- **Bernstein, *The Ultimate Day Trader*** — already distilled into `investor-bernstein-intraday` with exact parameters (10/8 MA channel, 28-period momentum, 16-bar breakout, 30-min opening range, 4× volume spikes, MACD 9/18 divergence). The skill itself says: hypothesis generator, not validated alpha. That is a **ready-made backlog of ~7 pre-registered specs** nobody has gated yet.
- **Howell, *Capital Wars*** — liquidity-cycle regime inputs; feeds overlay hypotheses, not entry signals.
Worth adding (one at a time, only when the current backlog runs dry): Chan (*Algorithmic Trading* — mean-reversion/momentum with honest OOS discussion), Aronson (*Evidence-Based Technical Analysis* — the data-mining-bias bible; sharpens the gate itself), López de Prado (*Advances in Financial ML* — we already use his deflated Sharpe).

**Should we mine Reddit/forums for working strategies?** As a *hypothesis mine*, yes; as a source of "working strategies", no. Anything posted publicly with a backtest screenshot is overfit, already arbitraged, or survivorship-biased — by the time it's on r/algotrading it is dead on arrival. The mining rules:
- Extract the **mechanism** claimed (who pays and why), never the parameters or the "results".
- Check the dead-idea log first (`backtests/results/`) — we do not re-test buried families.
- Re-derive the spec ourselves, pre-register it, gate it. Expect a ~0 hit rate; the cost per idea is low, so a rare survivor pays for the sweep.

## About "Bitcoin is 63k — looks like opportunity"

That instinct is a **portfolio question, not an intraday-bot question** — route it to the crypto book's machinery (`multi-lens-quorum`, `dip-tranches-strategy`, the committee), which exists precisely to judge dip entries with staged sizing on the $177k book. Two honest observations from our own data:
- The deployed trend filter is currently **flat on purpose**: BTC is below its 50-day average, and the backtest says buying into that state was the money-losing side of the trade. "Feels like opportunity" during a drawdown is exactly the feeling the gate exists to check.
- If the hypothesis is "buy X% drawdowns and hold weeks", that is a swing/position strategy — testable, but through the dip-tranches framework on the main book, not the $500 intraday bot.

## The plan

**Phase 0 — already running (free).** The notify-mode shadow deployment accumulates forward out-of-sample evidence for the regime filter — the exact "fresh evidence" its FAIL verdict asked for. Zero cost, zero risk. Review its journal monthly.

**Phase 1 — hypothesis harvest (1–2 days of agent work).** Build a backlog of 10–20 specs, each a falsifiable contract: entry/exit/sizing, the ONE economic reason, expected turnover, break-even cost, family classification vs the dead-idea log.
Sources, in order of expected quality:
1. Carver distillation → 3–5 specs (forecast-strength sizing, speed-matched-to-cost variants of trend, carry).
2. Bernstein skill → gate the ~7 named setups as ONE pre-registered family batch (they share a worldview; they share a trial budget).
3. Funding/basis carry on perps — the one repo-flagged lead never tested (paper-only design; leverage stays banned, so this targets the *paper track* and a future >$2k account).
4. Event/flow mechanisms: liquidation cascades, funding-rate flips, exchange-listing effects — mined from literature + forums under the mining rules above.

**Phase 2 — prioritize by (economic-reason strength × cost-to-test), pre-register.** Every spec's full grid is written into a trial ledger BEFORE any backtest runs. Families, not variations: one declared grid, one shot, per family.

**Phase 3 — gate in batches of ~3.** The harness makes a batch roughly a day of compute + verification. Every candidate gets the full treatment: walk-forward, deflated Sharpe, stress tiers, independent adversarial verification. FAILs go to the dead-idea log with exact assumptions.

**Phase 4 — act on the outcome, either way.**
- A PASS → Stage 2 of the readiness checklist (60-day paper track) — no shortcuts.
- Two to three batches with no PASS → we accept the (now heavily replicated) conclusion that no retail-computable intraday edge survives costs at this scale, and redirect: (a) deploy the regime overlay as *drawdown control* on the main crypto book, where its value is real even without significance-grade alpha; (b) grow the account past $2k, where margin/perps unlock the carry family properly.

**Budget discipline:** the deflated-Sharpe penalty is the whole game. The trial ledger is append-only; June-2026 and July-2026 trials already count against their families. Any temptation to "just try one more window" is spending significance we don't have.

## What we will NOT do

- No parameter re-tuning of the three failed families (SMA-trend, cross-sectional momentum, 5m mean-reversion).
- No copying strategies with claimed track records from forums, YouTube, or courses.
- No loosening of costs, fills, or dates — a PASS earned that way trades real money on a fiction.
- No live trading on gut feel about "opportunity", at any BTC price.
