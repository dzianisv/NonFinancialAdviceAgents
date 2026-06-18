---
name: crypto-daytrading
description: The crypto day-trader desk. Use when the user wants to day-trade or earn daily income on crypto (BTC, ETH, SOL, HYPE and other fundamentally-sound tokens), proposes an intraday crypto signal, or grants Coinbase/CDP access and says "trade daily for income". It turns a crypto intraday hypothesis into order logic — but ONLY after the strategy-discovery-backtest gate returns PASS. It encodes the crypto-specific realities (24/7 bars, taker/maker fees, funding, thin alt liquidity, exchange/custody risk) and the daily operating loop (notification-first). Never places a live order on an unbacktested rule. Educational, not advice.
license: MIT
compatibility: opencode
metadata:
  audience: builders
  domain: systematic-trading
  role: daytrade-desk
---

# Crypto Day-Trading Desk

Turns a crypto intraday idea into a daily, notification-first order routine — **gated by
`strategy-discovery-backtest`**. No rule trades until it PASSes there.

> Educational analysis, not financial advice. Crypto is high-vol; size for ruin-avoidance.

## Hard order of operations
1. **Idea -> `strategy-discovery-backtest` FIRST.** No exceptions. A "trade BTC daily" request enters
   the gate before any order logic exists.
2. Gate **PASS** -> build the daily loop below. Gate **FAIL** -> report "no edge", trade nothing.
3. Paper / notification mode -> human sign-off -> live with code-side hard caps.

## Universe
Tier-1 (deep liquidity, run signals here first): **BTC, ETH, SOL**. Tier-2 (fundamentally-sound,
thinner — wider slippage, smaller size): **HYPE** and peers. Alt liquidity is regime-dependent; a
backtest on calm-market spreads lies about a stressed exit. Size Tier-2 down hard.

## Crypto-specific realities the backtest MUST model
- **24/7, no close.** Signals decide on prior *bar* (e.g. prior 1h/4h close), not prior day.
- **Fees dominate intraday.** Coinbase retail taker ~0.4–0.6%; CDP/pro maker ~0.05–0.1%. A scalp that
  needs many round-trips dies on fees unless it is maker-passive. State break-even turnover.
- **Funding** on perps (if used) is a real carry cost/income — model it, both signs.
- **Slippage scales with size vs book depth.** Worst on Tier-2 in a drawdown — the moment you need out.
- **Gaps / liquidations / exchange outage** — 24/7 means a 30% candle while you sleep. Hard stops in
  code, not in the LLM.
- **Custody / counterparty** — exchange risk is non-zero; do not run size you cannot afford to lose to
  an exchange failure.

## Candidate signal families (must each pass the gate before use)
- **Trend / breakout** on 1h–4h (momentum persists in crypto historically — but costs eat the chop).
- **Mean-reversion** on stretched intraday moves (works in range regimes, bleeds in trends — regime
  filter mandatory).
- **Cross-asset / dominance** (BTC-dominance or ETH/BTC ratio gating alt entries).
- **Vol-targeting overlay** — scale exposure inverse to realized vol; the single most robust crypto knob.
None of these is assumed to work. Each is a hypothesis the gate must confirm net-of-cost, OOS.

## Daily operating loop (notification-first)
```
1. INGEST    pull 24/7 bars (ccxt / exchange API) for the universe; realized vol; funding.
2. REGIME    trend vs range vs crisis -> exposure multiplier (regime-detection).
3. SIGNAL    the PASSED strategy's entry/exit on prior-bar close. No look-ahead.
4. SIZE      vol-target + Tier-2 haircut + per-asset cap.
5. RISK      risk-management veto: per-trade stop, daily-loss kill, max gross. Deterministic, in code.
6. ORDERS    compute deltas, prefer maker/limit to cut fees; mark expected slippage.
7. NOTIFY    send proposed orders + plain rationale + risk report to the human.
8. EXECUTE   human approves (until go-live signed off) -> CDP CLI / Coinbase places orders.
9. LOG       append every signal/order/fill to an immutable audit log; mark P&L net of fees.
```

## Hard caps (deterministic code, outside the LLM)
Per-trade stop-loss, **daily max-loss kill switch**, max gross exposure, per-asset cap, Tier-2 size
haircut, max round-trips/day (fee-budget). The LLM proposes; this layer disposes. Cannot be overridden
by a prompt.

## Output (daily)
```
<crypto-daytrade-report as_of="...">
  <regime>trend|range|crisis -> exposure x</regime>
  <signals>per-asset in/out on prior bar</signals>
  <orders>side / size / limit px / expected slippage / fee — NOTIFICATION ONLY</orders>
  <risk>stops, daily-loss budget used, gross, caps OK?</risk>
  <pnl net_of_fees="true">today / week, vs hold-BTC benchmark</pnl>
  <verdict>trade | stand down (regime/cost/risk) — reason</verdict>
</crypto-daytrade-report>
```
Close with: *educational analysis, not advice; backtested rule, you approve the orders.*

## Integration
- Execution venue: **Coinbase CDP CLI** (track E of @GOAL.md). Notification-first until paper-validated.
- The live ~$177k book (`crypto/GOAL.md`) is a SEPARATE ledger — a day-trade sleeve is carved
  explicitly and capped; never silently mix with the long-term crypto allocation.
- Gate: `strategy-discovery-backtest`. Risk veto: `risk-management`. Regime: `regime-detection`.
