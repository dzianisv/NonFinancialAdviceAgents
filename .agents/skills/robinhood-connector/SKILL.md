---
name: robinhood-connector
description: Connector for executing US equity orders via Robinhood agentic trading (MCP) — in NOTIFICATION mode by default, with a documented, hard-gated path to live. Use when the user wants to wire the stock desk to Robinhood, asks to place/route equity orders, connects the Robinhood agent, or asks how the agent reaches Robinhood. Default is notification-first (the agent proposes orders; a human approves). Live execution is hard-gated behind a connected Robinhood Agentic account + explicit daily confirmation + a PASSed backtest + code-side caps + the PDT rule. This is GOAL track D. Educational, not advice.
license: MIT
compatibility: opencode
metadata:
  audience: builders
  domain: systematic-trading
  role: connector
---

# Robinhood Connector (track D)

Routes the stock desk's orders to **Robinhood agentic trading** — notification-first, live behind a hard
gate. **No order is placed that did not pass `strategy-discovery-backtest`** (invariant #1).

> Educational analysis, not financial advice. The agent proposes; a human disposes.

## What Robinhood agentic trading is
Robinhood lets you connect a third-party AI agent to a **dedicated Robinhood Agentic account** over
**MCP** (Model Context Protocol). Endpoint: `https://agent.robinhood.com/mcp/trading`.
- **Add to Claude Code:** `claude mcp add robinhood-trading --transport http https://agent.robinhood.com/mcp/trading`
- **Onboarding (user, desktop):** authenticate the agent + create the Agentic account. The agent can then
  read all accounts/positions/orders and **place trades**. *"You are ultimately responsible for the trades
  your AI agent places."* Trades are confined to the dedicated Agentic account.
- The agent CAN execute without human approval if configured that way — **we deliberately do NOT**; we run
  notification-first and keep code-side caps.

## Setup (staged — connector → notification → live)
1. **Add the MCP connection** (above). Read-only inspection (positions/balances) is safe to wire first.
2. **Notification mode (default):** the desk produces orders; route them through
   `connectors/notify_executor.py` in `mode="notify"`. The agent **proposes**; the human places/approves
   in the Robinhood app. No auto-execution.
3. **Live (hard-gated):** only after a strategy PASSes the gate, paper-validates, and the user signs off:
   set `ROBINHOOD_AGENT_CONNECTED=1` and `CONFIRM_LIVE=<today's date>`, and deliberately wire the real
   MCP `place_order` call in the executor's live stub. Hard caps apply to every order.

## PDT — a hard equity constraint (read before trading)
Pattern-Day-Trader rule: **under $25k account equity, max 3 day-trades per 5 business days.** A multi-name
intraday strategy is **not runnable** under $25k regardless of backtest. The connector tracks an
order-count budget; the desk must check the PDT counter before proposing intraday round-trips. (Backtested
status: **no equity intraday strategy has PASSed** — for income, the mid-risk allocation, track A, is the
evidence-backed route; this connector is then a *rebalancing/allocation* executor, not a day-trade one.)

## Operating mode (default = notify)
`connectors/notify_executor.py`, `mode="notify"`: validate vs hard caps → append to the immutable audit
log → emit the order ticket for the human. **Never contacts Robinhood.** No creds needed.
`mode="live"` refuses unless `ROBINHOOD_AGENT_CONNECTED` + `CONFIRM_LIVE`==today + strategy_ref + caps
pass — and even then real placement is a deliberate, separately-wired stub (never auto-placed).

## Hard caps (deterministic, outside the LLM — invariant #3)
`connectors/hard_caps.py`: per-order / per-position / gross notional caps, daily-loss kill, order-count
(PDT/fee) budget, long-only by default, `.KILL` file kill switch. The agent cannot override these.

## Definition of done (GOAL track D)
- [x] Connector works in **notification mode** (no creds) — `notify_executor.py`, tested.
- [x] MCP connection + onboarding documented; read-then-propose flow defined.
- [x] **Documented live path** behind a connected Agentic account + confirmation + caps + sign-off + PDT.
- [ ] Live trading — requires the user's connected Robinhood Agentic account + a PASSed, paper-validated
      strategy (or the track-A allocation) + sign-off.
