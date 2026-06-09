---
name: strategy-discovery-backtest
description: The keystone gate that turns any "trade X" request into a discovered, backtested, honestly-reported strategy BEFORE any order is placed. Use this whenever the user (or another skill) wants to trade, day-trade, or deploy a new strategy on stocks or crypto, asks "should we trade X", proposes a signal/edge, or any time an untested idea is about to reach an order. It encodes the pipeline hypothesis -> data -> backtest (no look-ahead, realistic costs) -> walk-forward / out-of-sample -> deflated Sharpe -> paper -> gate. Output is a PASS/FAIL verdict with net-of-cost metrics; "no edge found" is a valid, valuable result. This skill is the enforcement of the backtest-before-trade invariant — nothing trades that did not pass here. Educational, not advice.
license: MIT
compatibility: opencode
metadata:
  audience: builders
  domain: systematic-trading
  role: gate
---

# Strategy Discovery & Backtest (the gate)

**This skill is the law: no strategy reaches a live order without a PASS here.** It is invoked first
whenever anyone says "trade X", "day-trade Y", or "deploy this idea". It either returns a backtested,
human-approvable strategy or an honest "no edge found".

> Educational analysis, not financial advice. Backtests do not guarantee future results.

## When to run (trigger)
- A "trade / day-trade / deploy" request for any asset (stock or crypto).
- A new signal hypothesis from any analyst skill that wants to size capital.
- Any edit to an existing strategy's rules (re-run the gate; rules changed = unproven again).

## The pipeline (do every stage; do not skip to orders)

```
0. SPEC      Write the strategy as a falsifiable contract before touching data:
             universe, entry, exit, sizing, rebalance/hold horizon, costs assumed,
             the ONE economic reason an edge should exist. No reason -> stop.
1. DATA      Point-in-time only. Decide on prior close / prior bar. No survivorship
             (note delisted-name gap for crypto + equities). Split: in-sample (IS)
             vs out-of-sample (OOS) up front — never tune on OOS.
2. BACKTEST  Vectorized run on IS. Net of costs ALWAYS (see cost model). Produce the
             full metrics contract. Look-ahead check: shift signals +1 bar, confirm
             results don't collapse (if they do, you had leakage).
3. WALK-FWD  Re-fit / re-select on rolling IS windows, score only on the next OOS
             window. Report OOS metrics — these are the ones that count.
4. DEFLATE   Deflate Sharpe for the number of trials tried (multiple-testing). Many
             configs tested -> a high in-sample Sharpe is expected by luck. Haircut it.
5. REGIMES   Run across crisis + calm windows relevant to the asset (equities:
             2000-02, 2008, 2020-03, 2022; crypto: 2018, 2021-22 LUNA/FTX, 2025 draw).
6. STRESS    Double the cost assumption; add slippage on the worst 5% of bars; delay
             fills one bar. If edge dies, it was a cost mirage — FAIL.
7. VERDICT   PASS only if OOS edge survives deflation + stress AND the economic reason
             still holds. Else FAIL = "no edge found" (a real, valuable result).
8. GATE      PASS -> hand to paper/notification stage + request human sign-off.
             Never auto-promote IS-only results to live.
```

## Cost model (the #1 killer — never run gross)
| Venue | Commission | Spread/slippage | Other |
|-------|-----------|-----------------|-------|
| US equities (Robinhood) | ~$0 | 1–5 bps liquid, more on small caps | SEC/TAF fees, PDT rule <$25k |
| Crypto (Coinbase/CDP) | 0.4–0.6% taker retail; ~0.05–0.1% pro/maker | 1–10 bps majors, wide on alts | funding on perps, 24/7 gaps |

Day-trading turns over fast — costs compound per trade. A strategy that needs 50 round-trips/week must
clear ~50× the per-trade cost in edge. State the break-even turnover explicitly.

## Metrics contract (report every one, net of costs)
CAGR, Sharpe, Sortino, Calmar, max & current drawdown, realized vs target vol, exposure, **turnover**,
**round-trips/day**, win rate + payoff, profit factor, **break-even cost**, deflated Sharpe, OOS-vs-IS
decay, time-in-drawdown. For day-trading also: avg hold, slippage as % of gross edge, worst-day loss.

## Honest-result rules (anti-overfit, anti-reward-hack)
- Report **OOS** numbers as the headline; IS is context only.
- Disclose how many configurations you tried (trials) — it drives the deflation haircut.
- If edge < doubled costs, it is **FAIL**, regardless of IS beauty.
- "No edge found" after an honest run is a **success of the process**, not a failure to fix by loosening.
- Never tune parameters to pass; never relax the cost model to pass. That is reward-hacking the gate.

## Output format
```
<discovery-backtest>
  <spec>universe / entry / exit / sizing / horizon / economic reason</spec>
  <data>period, source, IS/OOS split, point-in-time note</data>
  <results net_of_cost="true">
    <in_sample>...metrics...</in_sample>
    <out_of_sample>...metrics...   <!-- headline -->
    <walk_forward>...OOS by window...</walk_forward>
    <stress>doubled costs / delayed fills / crisis windows</stress>
    <deflated_sharpe trials="N">...</deflated_sharpe>
  </results>
  <verdict>PASS | FAIL(no edge) — one-line reason, net-of-cost edge stated</verdict>
  <gate>if PASS: paper-trade plan + the human sign-off this needs before live</gate>
</discovery-backtest>
```

## Where artifacts live
- Backtest scripts: `backtests/` (run from repo root; self-contained; yfinance/ccxt data).
- Crypto-specific harness: `backtests/daytrade/` (24/7 bars, funding, taker fees).
- Honest summaries: `backtests/results/`.
- The strategy write-up (if PASS): `strategy/` with an OOS results table + crisis windows.
- Every passing strategy gets a durable eval (see `skill-supervisor`) re-run before any rule edit.

## Hand-off
- **PASS** -> `crypto-daytrading` / `stock-daytrading` / `hedge-fund-manager` may turn it into order
  logic, still notification-first, still behind human sign-off and code-side hard caps.
- **FAIL** -> log the dead idea in `backtests/results/` (so we do not re-test it blindly) and report.

This gate is non-negotiable. It is invariant #1 of @GOAL.md made executable.
