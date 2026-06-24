---
session: ses_123e
updated: 2026-06-18T19:00:17.892Z
---

# Session Summary

## Goal
Read ALL ~68 SKILL.md files in `.agents/skills/`, classify each by category, extract internal delegation/routing, external data sources, and outputs, then produce a complete structured map with ASCII delegation trees for every orchestrator skill.

## Constraints & Preferences
- Must read every single SKILL.md — no skipping
- Group skills by category (orchestrator, analytical-lens, thinker-persona, data-gather, news-feed, decision-chair, monitor/screener, strategy, connector, evaluation, operations)
- For orchestrators, show delegation trees as ASCII art
- Focus especially on skills that delegate to other skills as subagents
- Return the COMPLETE structured map

## Progress
### Done
- [x] Listed all 68 skill directories (+ README, INSTALL-OPENCLAW.md, INVESTOR-SETUP-PROMPT.md = 72 entries total)
- [x] Read 25 SKILL.md files (batch 1: 12 skills, batch 2: 13 skills) — see File Operations
- [x] Identified key orchestrators and their delegation patterns from the 25 read so far

### In Progress
- [ ] Still need to read ~43 remaining SKILL.md files to complete the map

### Blocked
- (none)

## Key Decisions
- **Batch-parallel reads**: Reading SKILL.md files in parallel batches of 12-13 for speed
- **Orchestrators prioritized in batch 2**: Read hedge-fund-manager, multi-lens-quorum, macro-panel, crypto-advisor, research-manager, narrative-news, signal-convergence-alert, tradfi-portfolio-manager, superforecasting first since they are the primary delegators
- **`agentic-fund-orchestration` is DEPRECATED**: Superseded by `hedge-fund-manager`; retained for docs only

## Next Steps
1. Read remaining ~43 SKILL.md files in parallel batches. Unread directories:
   - `analytics-ray-dalio`, `analytics-russell-napier`, `analytics-stanley-druckenmiller`, `analytics-warren-buffett`
   - `bypass-paywalls`, `coinbase-cdp-connector`, `congressman-stock-watch`
   - `crypto-chair`, `crypto-dip-scanner`, `crypto-liquidity-data`, `crypto-news-store`, `crypto-onchain-data`, `crypto-research-desk`, `crypto-token-screener`, `crypto-workflow-eval`
   - `defi-portfolio-manager`, `dip-screener`, `dip-tranches-strategy`
   - `feed-bitcoinmagazine`, `feed-bloomberg`, `feed-coindesk`, `feed-cointelegraph`, `feed-decrypt`, `feed-ft`, `feed-theblock`, `feed-wsj`
   - `feed-fomc`, `forecast-ledger`, `fundamental-analysis`
   - `hedge-fund-13f-analysis`, `hedge-fund-committee-eval`
   - `liveness-monitor`
   - `portfolio-construction`, `portfolio-monitor`, `prediction-market-odds`
   - `rebalancing`, `regime-detection`, `risk-management`, `robinhood-connector`
   - `skill-supervisor`, `stock-chair`, `stock-research-desk`
   - `strategy-discovery-backtest`, `tax-loss-harvesting`, `trend-following`
2. Classify all 68 skills into categories
3. Build ASCII delegation trees for all orchestrators
4. Produce the final complete structured map

## Critical Context
- **Delegation patterns discovered so far:**
  - `hedge-fund-manager` (PM/CIO) → delegates to: `research-manager`, `regime-detection`, `signal-convergence-alert`, `portfolio-construction`, `risk-management`, `dip-tranches-strategy`, `rebalancing`, `tax-loss-harvesting`, `tradfi-portfolio-manager` (weekly note)
  - `multi-lens-quorum` → spawns 4–7 subagents each loading ONE `analytics-*` or `analyst-*` lens skill; general method over any lenses
  - `macro-panel` → routes to 7 thinker seats: `analytics-lyn-alden`, `analytics-ray-dalio`, `analytics-stanley-druckenmiller`, `analytics-lacy-hunt`, `analytics-michael-pettis`, `analytics-russell-napier`, `analytics-warren-buffett`
  - `crypto-advisor` → orchestrates `regime-detection`, `dip-tranches-strategy`, `risk-management`
  - `research-manager` → dynamically discovers all skills via filesystem listing, assembles desk plan naming gather seats, news feeds, panel lenses, consolidation desk, and chair
  - `narrative-news` → orchestrates `feed-decrypt`, `feed-cointelegraph`, `feed-coindesk`, `feed-theblock`, `feed-bitcoinmagazine`, `feed-ft`, `feed-wsj`, `feed-bloomberg` → `crypto-news-store`
  - `signal-convergence-alert` → reads pools from `dip-screener`, narrative/journalism, `13f-watch`, `congressman-stock-watch`; routes hits to `multi-lens-quorum` + `superforecasting`
  - `13d-watch` → routes candidates to `multi-lens-quorum` + `superforecasting`
  - `13f-watch` → depends on `hedge-fund-13f-analysis`; routes candidates to `multi-lens-quorum` + `superforecasting`
  - `superforecasting` → uses `prediction-market-odds`, `analyst-derivatives-positioning`; writes to `forecast-ledger`; distinct from `multi-lens-quorum` (verdict vs forecast)
  - `crypto-daytrading` / `stock-daytrading` → gated by `strategy-discovery-backtest`
  - `tradfi-portfolio-manager` → reads `regime-detection`, `dip-tranches-strategy`, `risk-management`, strategy v3 docs
  - `trend-stock-research` → journalism-first method; uses `bypass-paywalls` for reading articles
- **Thinker-persona skills** (no delegation, standalone lenses): `analytics-benjamin-graham`, `analytics-lacy-hunt`, `analytics-lyn-alden`, `analytics-michael-pettis`, `analytics-morgan-housel` (+ 3 unread: ray-dalio, russell-napier, stanley-druckenmiller, warren-buffett)
- **Analyst skills** (standalone lenses, no delegation): `analyst-crypto`, `analyst-derivatives-positioning`, `analyst-systematic-trading`, `analyst-technical-analysis`
- **External data sources seen**: SEC EDGAR (13D/13G/13F), Coinglass, Deribit, CME, CBOE, VIX, COT/OCC, prediction markets (Polymarket/Kalshi), Seeking Alpha, WSJ, FT, various crypto news sites, on-chain data APIs

## File Operations
### Read
- `/Users/engineer/workspace/backtest/.agents/skills` (directory listing — 72 entries)
- `/Users/engineer/workspace/backtest/.agents/skills/13d-watch/SKILL.md`
- `/Users/engineer/workspace/backtest/.agents/skills/13f-watch/SKILL.md`
- `/Users/engineer/workspace/backtest/.agents/skills/agentic-fund-orchestration/SKILL.md`
- `/Users/engineer/workspace/backtest/.agents/skills/analyst-crypto/SKILL.md`
- `/Users/engineer/workspace/backtest/.agents/skills/analyst-derivatives-positioning/SKILL.md`
- `/Users/engineer/workspace/backtest/.agents/skills/analyst-systematic-trading/SKILL.md`
- `/Users/engineer/workspace/backtest/.agents/skills/analyst-technical-analysis/SKILL.md`
- `/Users/engineer/workspace/backtest/.agents/skills/analytics-benjamin-graham/SKILL.md`
- `/Users/engineer/workspace/backtest/.agents/skills/analytics-lacy-hunt/SKILL.md`
- `/Users/engineer/workspace/backtest/.agents/skills/analytics-lyn-alden/SKILL.md`
- `/Users/engineer/workspace/backtest/.agents/skills/analytics-michael-pettis/SKILL.md`
- `/Users/engineer/workspace/backtest/.agents/skills/analytics-morgan-housel/SKILL.md`
- `/Users/engineer/workspace/backtest/.agents/skills/crypto-advisor/SKILL.md`
- `/Users/engineer/workspace/backtest/.agents/skills/crypto-daytrading/SKILL.md`
- `/Users/engineer/workspace/backtest/.agents/skills/hedge-fund-manager/SKILL.md`
- `/Users/engineer/workspace/backtest/.agents/skills/macro-panel/SKILL.md`
- `/Users/engineer/workspace/backtest/.agents/skills/multi-lens-quorum/SKILL.md`
- `/Users/engineer/workspace/backtest/.agents/skills/narrative-news/SKILL.md`
- `/Users/engineer/workspace/backtest/.agents/skills/research-manager/SKILL.md`
- `/Users/engineer/workspace/backtest/.agents/skills/signal-convergence-alert/SKILL.md`
- `/Users/engineer/workspace/backtest/.agents/skills/stock-daytrading/SKILL.md`
- `/Users/engineer/workspace/backtest/.agents/skills/superforecasting/SKILL.md`
- `/Users/engineer/workspace/backtest/.agents/skills/tradfi-portfolio-manager/SKILL.md`
- `/Users/engineer/workspace/backtest/.agents/skills/trend-stock-research/SKILL.md`

### Modified
- (none)
