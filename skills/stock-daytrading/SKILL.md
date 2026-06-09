---
name: stock-daytrading
description: The stock day-trader desk. Use when the user wants to day-trade or earn short-horizon income on US equities/ETFs, proposes an intraday stock signal, or grants Robinhood access and says "day-trade for income". It turns an equity intraday hypothesis into order logic — but ONLY after the strategy-discovery-backtest gate returns PASS. It encodes equity-intraday realities (RTH only, PDT rule, spread/slippage, halts, hard-to-borrow shorts) and the daily loop (notification-first). Never places a live order on an unbacktested rule. Educational, not advice.
license: MIT
compatibility: opencode
metadata:
  audience: builders
  domain: systematic-trading
  role: daytrade-desk
---

# Stock Day-Trading Desk

Turns an equity intraday idea into a daily, notification-first order routine — **gated by
`strategy-discovery-backtest`**. No rule trades until it PASSes there.

> Educational analysis, not financial advice. Intraday equity edges are thin and cost-sensitive.

## Hard order of operations
1. **Idea -> `strategy-discovery-backtest` FIRST.** A "day-trade SPY" request enters the gate before
   any order logic exists.
2. Gate **PASS** -> build the daily loop. Gate **FAIL** -> report "no edge", trade nothing.
3. Paper / notification mode -> human sign-off -> live with code-side hard caps.

## Equity-intraday realities the backtest MUST model
- **Regular hours only** (09:30–16:00 ET) + open/close auctions; pre/post is thin. Overnight gap risk
  if held — a "day" trade that holds overnight is a different (gappy) strategy; model it as such.
- **PDT rule**: <$25k equity = max 3 day-trades / 5 business days. A high-frequency intraday strategy is
  **not runnable** under $25k — state this constraint up front; it can invalidate the whole idea.
- **Costs**: Robinhood ~$0 commission, but spread + slippage + SEC/TAF fees are real; payment-for-order-
  flow fills are not midpoint. Model 1–5 bps liquid large-caps, much more on small/illiquid.
- **Halts / LULD bands** — you cannot always exit when you want. Hard stops in code.
- **Shorting**: hard-to-borrow fees, locate availability, uptick constraints. A long-only intraday
  strategy avoids this; if the edge needs shorts, model borrow cost or it is fiction.
- **Liquidity vs size** — slippage scales with order size vs ADV; backtest on realistic fills.

## Candidate signal families (each must pass the gate before use)
- **Opening-range breakout** (first 15–30m range, momentum continuation) — classic, cost-sensitive.
- **Mean-reversion** on intraday over-extension (VWAP reversion) — regime-dependent.
- **Gap-and-go / gap-fade** on overnight gaps (needs real gap stats, not curve-fit).
- **Index/ETF momentum** (SPY/QQQ intraday trend with a vol filter) — most liquid, lowest cost.
None assumed to work. Each is a hypothesis the gate confirms net-of-cost, OOS, under the PDT constraint.

## Daily operating loop (notification-first)
```
1. INGEST    intraday bars (Alpaca/yfinance) for the universe; ATR/realized vol; gap stats.
2. REGIME    trend vs chop vs high-vol -> trade/stand-down + size (regime-detection).
3. SIGNAL    the PASSED strategy's entry/exit on prior-bar close (no look-ahead).
4. SIZE      vol-target, per-name cap, PDT-count check (don't exceed day-trade budget).
5. RISK      risk-management veto: per-trade stop, daily-loss kill, max gross, halt handling.
6. ORDERS    limit where possible to cut spread; mark expected slippage + fees.
7. NOTIFY    send proposed orders + rationale + risk report to the human.
8. EXECUTE   human approves (until go-live) -> Robinhood places orders.
9. LOG       append every signal/order/fill to an immutable audit log; P&L net of costs.
```

## Hard caps (deterministic code, outside the LLM)
Per-trade stop, **daily max-loss kill switch**, max gross, per-name cap, **PDT day-trade counter**,
max trades/day (fee + PDT budget). LLM proposes; this layer disposes; prompt cannot override.

## Output (daily)
```
<stock-daytrade-report as_of="...">
  <regime>trend|chop|high-vol -> trade/stand-down, size</regime>
  <pdt>day-trades used this 5-day window / 3 (if <$25k)</pdt>
  <signals>per-name in/out on prior bar</signals>
  <orders>side / size / limit px / expected slippage / fee — NOTIFICATION ONLY</orders>
  <risk>stops, daily-loss budget used, gross, caps OK?</risk>
  <pnl net_of_cost="true">today / week, vs hold-SPY benchmark</pnl>
  <verdict>trade | stand down (regime/PDT/cost/risk) — reason</verdict>
</stock-daytrade-report>
```
Close with: *educational analysis, not advice; backtested rule, you approve the orders.*

## Integration
- Execution venue: **Robinhood agentic trading** (track D of @GOAL.md). Notification-first until paper.
- This is the $1M tradfi book's **day-trade sleeve** — carved explicitly and capped, separate from the
  long-horizon v3 allocation; never let intraday risk leak into the core book.
- Gate: `strategy-discovery-backtest`. Risk veto: `risk-management`. Regime: `regime-detection`.
