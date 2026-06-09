---
name: coinbase-cdp-connector
description: Connector for executing crypto orders via the Coinbase CDP CLI / MCP — in NOTIFICATION and TESTNET (paper) mode by default, with a documented, hard-gated path to live. Use when the user wants to wire the crypto desk to Coinbase, asks to place/route crypto orders, grants a CDP API key, or asks how the agent reaches Coinbase. Default is notification-first (the agent proposes orders; a human approves); testnet uses base-sepolia faucet funds (no mainnet money). Live execution is hard-gated behind creds + explicit daily confirmation + a PASSed backtest + code-side caps. This is GOAL track E. Educational, not advice.
license: MIT
compatibility: opencode
metadata:
  audience: builders
  domain: systematic-trading
  role: connector
---

# Coinbase CDP Connector (track E)

Routes the crypto desk's orders to **Coinbase CDP** — notification-first, testnet-capable, live behind
a hard gate. **No order is placed that did not pass `strategy-discovery-backtest`** (invariant #1).

> Educational analysis, not financial advice. The agent proposes; a human disposes.

## What CDP is
`@coinbase/cdp-cli` is a unified CLI for the Coinbase Developer Platform that **doubles as an MCP server
+ agent skill** — giving Claude Code tool-calling access to CDP wallets, trading, payments, onchain ops.
- Requires **Node.js 22+**.
- Auth: an **API key JSON** downloaded from the Coinbase Developer Portal (user supplies, out-of-band).
- **Testnet**: `cdp evm faucet address=<addr> network=base-sepolia token=eth|usdc|eurc|cbbtc` — real
  paper trading with **no mainnet funds**. This is our paper venue.
- Verify install: `cdp evm accounts list`.
- Official agent skill: https://docs.cdp.coinbase.com/cdp-cli/skill

## Setup (staged — connector → testnet → live)
1. **Install (no key needed to inspect):** `npx @coinbase/cdp-cli@latest --help`. As an MCP server it can
   be added to Claude Code; as a skill it exposes CDP tools.
2. **Testnet / paper (no mainnet money):** create an account `cdp evm accounts create name=paper-wallet`,
   fund via the base-sepolia faucet, and route the desk's orders through `connectors/notify_executor.py`
   in `mode="paper"`. Validate the daily loop end-to-end with play money.
3. **Live (hard-gated):** only after a strategy PASSes the gate, paper-validates, and the user signs off:
   set `CDP_API_KEY_JSON=/path/to/key.json` and `CONFIRM_LIVE=<today's date>`, and deliberately wire the
   real `cdp` trade call in the executor's live stub. Code-side caps (`connectors/hard_caps.py`) apply
   to every order regardless of mode.

## Operating mode (default = notify)
The desk (`crypto-daytrading` or `hedge-fund-manager`) produces an order list; each `Order` carries a
`strategy_ref` to the PASSed backtest. `connectors/notify_executor.py`:
- **notify** (default): validate vs hard caps → append to the immutable audit log → emit the order ticket
  for the human. **Never contacts Coinbase.** No creds needed.
- **paper**: same, routed to base-sepolia testnet (faucet funds) once a key is present.
- **live**: refuses unless creds present AND `CONFIRM_LIVE` matches today AND strategy_ref set AND caps
  pass — and even then the real placement is a deliberate, separately-wired stub (never auto-placed).

## Hard caps (deterministic, outside the LLM — invariant #3)
`connectors/hard_caps.py`: per-order / per-position / gross notional caps, daily-loss kill, order-count
budget, long-only by default, and a `.KILL` file kill switch. The agent cannot override these — they are
plain Python evaluated before any order.

## Crypto specifics to keep honest
Taker ~0.4-0.6% retail vs maker ~0.05-0.1% — model the fee you will actually pay (see
`strategy-discovery-backtest`). 24/7 gaps; exchange/custody risk; size Tier-2 tokens (e.g. HYPE) down.
The current backtested status: **no crypto day-trade strategy has PASSed** — REGIME-SMA is a drawdown
control, not alpha, pending a maker-fill model. **Until a PASS, this connector proposes nothing to trade.**

## Definition of done (GOAL track E)
- [x] Connector works in **notification mode** (no creds) — `notify_executor.py`, tested.
- [x] **Testnet/paper path** documented (base-sepolia faucet).
- [x] **Documented live path** behind creds + confirmation + caps + sign-off.
- [ ] Live trading — requires the user's CDP API key + a PASSed, paper-validated strategy + sign-off.
