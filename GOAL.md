# What We're Building

A set of AI **skills and workflows** that turn any AI agent (Claude Code, OpenClaw, Hermes) into a proactive investment advisor.

> Educational analysis only — not financial advice. Human approves every action.

## What it does

- Watches markets daily — dips, regime shifts, Fed moves, congressional trades, hedge-fund 13Fs
- Sends a DM the same day a real setup appears (silent otherwise — no noise)
- Runs a weekly investment brief: signals → quorum verdict → risk veto → buy/sell/hold ideas
- **Recommend-only.** No trades placed without your sign-off. Hard caps live in code.

## Two books

| Book | Size | Strategy |
|------|------|---------|
| **Tradfi** | ~$1M | RSP 70% / GLD 15% / IEF 15% — S&P-like return, less AI-bubble concentration. Backtested: −42% max DD vs S&P −55%. |
| **Crypto** | ~$177k | Yield-first: maximize sustainable net yield on stable sleeve; capital preservation first; no idle cash sits at 0%. |

## What's installed (~60 skills + 1 workflow)

**Signal skills** — regime-detection, fomc-monitor, dip-screener, crypto-dip-scanner, trend-stock-research, 13f-watch, congressman-stock-watch, feed-{bloomberg,ft,wsj,coindesk,…}

**Analysis skills** — macro-panel (7 thinker lenses), multi-lens-quorum (buy/sell/hold verdict), superforecasting, fundamental-analysis, analyst-{technical,systematic,crypto,derivatives}

**Portfolio skills** — portfolio-monitor, risk-management, hedge-fund-manager, tradfi-portfolio-manager, defi-portfolio-manager, forecast-ledger

**Workflow** — `hedge-fund-committee` (weekly parallel fan-out: news → price-ground → quorum → CIO brief → staged buy plan)

## Three backends, same skills

| Backend | Install |
|---------|---------|
| **Claude Code** | `npx -y skills add dzianisv/financial-advisor-agents` |
| **OpenClaw** | `npx --yes skills add dzianisv/financial-advisor-agents --agent openclaw --yes --copy --dangerously-accept-openclaw-risks` |
| **Hermes** | `npx -y skills add dzianisv/financial-advisor-agents --agent hermes-agent` |

Workflows install via repo clone — see **[docs/InstallPrompt.md](docs/InstallPrompt.md)** for a paste-and-go setup prompt.

## Hard rules

1. **Backtest before any strategy goes live.** No untested idea reaches an order.
2. **Human in the loop.** Agent proposes; you approve.
3. **No fabricated data.** Source down → `[UNAVAILABLE]`, never an invented price.
4. **Risk management has veto.** RISK_OFF regime → no new buys.
5. **Two books are separate ledgers.** Never conflate tradfi and crypto.
