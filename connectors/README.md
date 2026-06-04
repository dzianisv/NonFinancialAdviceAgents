# connectors/ — broker execution layer (notification-first)

Wires the desks to real brokers (**Robinhood** = track D, **Coinbase CDP** = track E) while enforcing the
GOAL invariants in deterministic code. **Educational analysis, not financial advice.**

## Files
- `hard_caps.py` — deterministic risk caps + kill switch (invariant #3). Per-order/position/gross notional
  caps, daily-loss kill, order-count budget, long-only default, `.KILL` file. **The agent cannot override
  these** — plain Python evaluated before any order.
- `notify_executor.py` — notification-first executor. `mode="notify"` (default) proposes order tickets +
  writes the audit log and **never contacts a broker**; `mode="paper"` targets testnet (Coinbase
  base-sepolia faucet); `mode="live"` is hard-gated (creds + `CONFIRM_LIVE`==today + strategy_ref + caps)
  and even then the real placement is a deliberate, unwired stub.
- `test_connectors.py` — proves caps reject bad orders, notify never places, live blocks without creds.
  Run: `python3 connectors/test_connectors.py` (13 checks).
- `audit_log.jsonl` — append-only audit trail (git-ignored).

## The invariants this layer enforces
1. **Backtest-before-trade** — an `Order` with no `strategy_ref` (a PASSed backtest) is rejected by caps.
2. **Notification-first** — default mode proposes; a human approves/places. Live is opt-in, daily-confirmed.
3. **Hard caps + kill switch outside the LLM** — `hard_caps.py`, deterministic.
4. **Honest reporting** — every order (proposed/rejected/blocked) is logged with its reason.

## Quick demo (no creds, nothing placed)
```
python3 connectors/notify_executor.py
```
Shows valid orders PROPOSED (human-approvable tickets), oversized + no-backtest orders REJECTED.

## Path to live (per the connector skills)
`skills/robinhood-connector` and `skills/coinbase-cdp-connector` document the staged path:
connector → notification → testnet/paper → (PASSed + paper-validated strategy + user sign-off) → live with
code-side caps. Live requires the user's credentials (Robinhood Agentic account / CDP API key) and is
intentionally never auto-wired.
