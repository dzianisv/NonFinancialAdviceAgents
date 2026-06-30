# GOAL — Proactive Investment Advisor

AI skills + workflows that turn any AI agent (Claude Code, OpenClaw, Hermes) into a **proactive,
notification-first investment advisor** behind a hard backtest-before-trade gate.

> Educational analysis only — not financial advice. Human approves every action.

## Mission

The owner manages a $1M tradfi book + a ~$177k crypto book and has no time to research. Reach a state
where the owner never again misses a time-sensitive setup like:
- **Google (GOOGL), Spring 2025** — quality stock −30% from 52w high.
- **SanDisk (WDC), Sept 2025** — AI-supply-chain narrative built over weeks in FT/WSJ.
- **BTC, April 2025** — $61k, −43% from ATH, Fear&Greed sub-20, funding negative.

Each was obvious in hindsight, time-boxed (days), and missed because nobody was watching.
The advisor surfaces them **same-day, with a defended verdict**, before the window closes.

## What it does

- Watches markets daily — dips, regime shifts, Fed moves, congressional trades, 13F filings, news narratives.
- Sends a DM the same day a real setup appears (silent otherwise — no noise).
- Runs a weekly investment brief: signals → quorum verdict → risk veto → ranked buy/sell ideas.
- **Recommend-only.** No trades placed without your sign-off. Hard caps live in deterministic code.

## Two books (one advisor, separate ledgers)

The advisor manages BOTH books through the same skill/workflow stack. Research workflows
(`research-market`, `hedge-fund-committee`) route to the right desks automatically based on the
question's asset class. Accounting stays separate — never conflate P&L across books.

### Book 1: Tradfi (~$1M)

**Strategy:** Bubble-Aware All-Weather (v3) — RSP 70% / GLD 15% / IEF 15%.
**Goal:** S&P-like return, less AI-bubble concentration. Backtested: −42% max DD vs S&P −55%.
**Details:** `strategy/v3-bubble-aware-all-weather.md`

### Book 2: Crypto (~$177k)

**Strategy:** Risk-aware yield — maximize sustainable net yield on stable sleeve, capital preservation first.
**Goal:** No dollar sits idle; no dollar takes unpriced risk.

#### The control loop (5 standing jobs)

| Job | Trigger | Action |
|-----|---------|--------|
| **Deploy** | Cash sits idle > 3 days | Move to best C1-passing venue with capacity |
| **Monitor** | Continuous (`portfolio.py`) | Track blended yield, idle $, concentration, collateral grade |
| **Rotate** | Venue yield falls below clean frontier or collateral degrades | Exit to better eligible venue |
| **Rebalance** | Sleeve/position drifts outside band | Trim/add back to target |
| **Defend** | Crypto risk-off (BTC/ETH trend break, funding/vol spike, depeg/exploit) | Raise stable/gold weight, cut satellite |

#### Hard constraints (C1–C9)

| # | Constraint | Setting |
|---|---|---|
| C1 | **Collateral whitelist.** T-bills, BTC, ETH, SOL-staking, overcollateralized loans only. No reflexive/synthetic dollars, no PT/looped/long-tail. | per `research/10-crypto-lp-yield-state.md` |
| C2 | Position concentration ≤ X% of book per vault/pool | 15% |
| C3 | Protocol concentration ≤ Y% across all pools of one protocol | 25% |
| C4 | Chain concentration ≤ Z% per chain outside Ethereum/Base | 10% |
| C5 | Capacity — deposit ≤ 10% of pool TVL | 10% |
| C6 | Liquidity — ≥ L% redeemable within D days | *investor input needed* |
| C7 | Satellite cap (high-risk/perp-LP/points) ≤ S% total | 5% |
| C8 | Sleeve bands — stable/ETH/SOL/BTC/gold/satellite within target ranges | *investor input needed* |
| C9 | No idle cash below clean frontier longer than 3 days | 3 days |

#### Optimization (two layers, top-down)

1. **Strategic sleeves** — split across `{stable-yield, ETH, SOL, BTC, gold, satellite}`. Policy choice
   from investor risk tolerance / horizon / liquidity, not yield-driven.
2. **Within stable sleeve** — constrained yield-maximization: maximize `Σ wᵢ · r_netᵢ` subject to C1–C8.

**Optimal** = on the efficient frontier: no feasible reallocation raises net yield without violating a constraint.

#### Required investor inputs (unchecked = undefined)

- [ ] Max tolerable drawdown on whole book in −60% crypto move
- [ ] Time horizon — when is this capital needed?
- [ ] Liquidity need — how much withdrawable within 1/7/30 days?
- [ ] Stable vs directional split target
- [ ] KYC willingness for RWA T-bill products (BUIDL/USTB/USDY)
- [ ] Per-protocol trust caps or exclusions
- [ ] Self-custody preference for blue-chip spot

#### Current state (2026-05-30)

| Metric | Value |
|---|---|
| Total | ~$177,145 |
| Stablecoins | $122k (69%) |
| Blended yield (live) | ~1.7% (~$2,989/yr) |
| Stables earning <3% | ~$104k |

Interim target: reallocate ~$113k idle stables → ~4.5% clean frontier = **$7,058/yr** (+$4,069 uplift).

**Tooling:** `crypto/portfolio.py` (live tracker), `crypto/STRATEGY.md` (target allocation + venue menu).

## Installed (~60 skills + 1 workflow)

**Signals** — regime-detection, feed-fomc, dip-scanner, trend-stock-research, signal-convergence-alert, analyse-smartmoney-13f, analyse-smartmoney-ptr, feed-{bloomberg,ft,wsj,coindesk,…}

**Analysis** — macro-panel (7 thinker lenses), multi-lens-quorum (buy/sell/hold verdict), superforecasting, analyse-fundamental, analyst-{systematic,derivatives}, research-{technical,onchain}

**Portfolio** — portfolio-monitor, risk-management, hedge-fund-manager, tradfi-portfolio-manager, defi-portfolio-manager, forecast-ledger

**Workflow** — `hedge-fund-committee` (weekly parallel fan-out: news → price-ground → quorum → CIO brief → staged buy plan)

## Three backends, same portable skills

Design rule: **lean on each platform's native primitives — don't reinvent scheduling or state.**

| Backend | Install | Scheduling | State | Notification |
|---------|---------|-----------|-------|--------------|
| **Claude Code** | `npx -y skills add dzianisv/financial-advisor-agents` | cron → `claude -p` + dynamic workflows | auto-memory + dedup ledgers | terminal / push |
| **OpenClaw** | `npx --yes skills add dzianisv/financial-advisor-agents --agent openclaw --yes --copy --dangerously-accept-openclaw-risks` | agent-native CRON (heartbeat = backup) | memory + workspace files | Telegram DM |
| **Hermes** | `npx -y skills add dzianisv/financial-advisor-agents --agent hermes-agent` | hermes scheduler | preloaded skill sessions | configured channel |

Setup prompts: `docs/InstallPrompt.md`. Per-backend wiring: `docs/setup-{openclaw,claudecode,hermes}.md`.

## Hard rules (invariants — an action breaking one is rejected)

1. **Backtest before trade.** `strategy-discovery-backtest` runs first; only PASS + human approval trades.
2. **Human in the loop.** Agent proposes; human approves. Notification-first until paper-validated.
3. **No fabricated data.** Source down → `[UNAVAILABLE]`, never an invented price.
4. **Risk management has veto.** RISK_OFF regime → no new buy alerts (logged to watchlist only).
5. **Two books: one advisor, separate ledgers.** Never conflate tradfi and crypto accounting.
6. **Hard caps in code, outside the LLM.** Size, drawdown, per-trade/day loss, leverage.

## Scope

**IN:** daily dip scans (stock + crypto), regime/Fed monitoring, journalism narrative accumulation,
signal convergence, weekly brief, crypto yield monitoring + rotation, proactive scheduling on 3 backends, recommend-only DMs.

**OUT:** auto-trading (recommend-only; execution tracks D/E in AGENTS.md), paid data feeds,
intraday day-trading (gated by backtest skill, separate workstream).

## Done (advisor sub-project — all [x] or deferred)

- [x] dip-scanner (unified equity+crypto), signal-convergence-alert — built + evaluated on live data.
- [x] 3-backend proactive setup documented (heartbeat / cron / hermes scheduler).
- [x] Skills deployed + validated on LIVE openclaw (2026-06-14): python3.12+yfinance in agent bash; live DM fired.
- [x] Agent-native CRON owns the schedule (3 dip jobs + regime 08:00, journalism 08:15, weekly brief Mon).
- [x] forecast-ledger wired: each DM'd call logged; 30/60/90d hit-rate scored in weekly brief.
- [x] claude-code backend validated: skills load as `/commands`, run clean on live data.
- [~] hermes backend: DEFERRED — no instance available. Setup documented; same skills apply when ready.
- [x] Crypto book audited, tracker built (`portfolio.py`), strategy written (`STRATEGY.md`).
- [ ] Investor inputs captured for C6/C8 — policy defaults set, not confirmed.
- [ ] Crypto transition executed (investor signs).
