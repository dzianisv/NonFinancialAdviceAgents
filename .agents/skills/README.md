# Skills — Agentic Investment Portfolio Manager

opencode-compatible `SKILL.md` modules for an automated, agent-driven investment portfolio.
Each is self-contained with YAML frontmatter (`name`, `description`, `license`, `compatibility: opencode`).

**All skills are educational frameworks, not personalized financial advice.**

---

## Quick Install (any AI agent)

One command installs the full skill set from `dzianisv/backtest`:

```bash
# Claude Code
npx -y skills add dzianisv/backtest --agent claude-code

# opencode
npx -y skills add dzianisv/backtest --agent opencode

# hermes-agent
npx -y skills add dzianisv/backtest --agent hermes-agent

# openclaw  (with script files — required for watch.py / ledger.py)
npx --yes skills add dzianisv/backtest \
  --agent openclaw --yes --copy --dangerously-accept-openclaw-risks
```

Or install individual skills by adding `--skill <name>`:
```bash
npx -y skills add dzianisv/backtest --skill 13f-watch --agent claude-code
npx -y skills add dzianisv/backtest --skill congressman-stock-watch --agent opencode
```

> The `skills` npm package (v1.5+) supports all agents above. If `npx` isn't available, install once:
> `npm install -g skills`

### hermes-agent (alternative: URL install)

```bash
# Install individual skills by raw URL
hermes skills install https://raw.githubusercontent.com/dzianisv/backtest/main/.agents/skills/13f-watch/SKILL.md
hermes skills install https://raw.githubusercontent.com/dzianisv/backtest/main/.agents/skills/congressman-stock-watch/SKILL.md
hermes skills install https://raw.githubusercontent.com/dzianisv/backtest/main/.agents/skills/trend-stock-research/SKILL.md
hermes skills install https://raw.githubusercontent.com/dzianisv/backtest/main/.agents/skills/hedge-fund-manager/SKILL.md
```

### Setup prompt (all agents)

After installing, paste **[INVESTOR-SETUP-PROMPT.md](INVESTOR-SETUP-PROMPT.md)** to your agent — works on openclaw, hermes-agent, Claude Code, opencode, or any agent with the skills loaded.

The prompt tells the agent to:
1. Verify all skills loaded
2. Run 13F + congressional + trending stock research immediately
3. Register 4 recurring cron jobs (daily regime, weekly 13F, weekly congress, weekly trend research)

---

## The watchlist pipeline

```
13f-watch (institutional filings, weekly)
    +
congressman-stock-watch (STOCK Act disclosures, weekly)
    ↓
multi-lens-quorum (judge: should I buy this?)
    ↓
superforecasting (when + probability)
    ↓
trend-stock-research (weekly — reads journalism, surfaces narratives)
```

`hedge-fund-manager` orchestrates the daily loop. `agentic-fund-orchestration` wires it all together.

---

## Skill index

### Watchlist / discovery (the inbound pipeline)

| Skill | Role | Cadence |
|-------|------|---------|
| [13f-watch](13f-watch/SKILL.md) | Pull new institutional 13F buys; dedupe ledger | weekly |
| [congressman-stock-watch](congressman-stock-watch/SKILL.md) | Pull STOCK Act purchase disclosures; dedupe ledger | weekly |
| [trend-stock-research](trend-stock-research/SKILL.md) | Read financial journalism; surface emerging tickers | weekly |
| [hedge-fund-13f-analysis](hedge-fund-13f-analysis/SKILL.md) | Deep-read a single 13F filing (EDGAR) | on-demand |

### Judgment (quorum + forecasting)

| Skill | Role |
|-------|------|
| [multi-lens-quorum](multi-lens-quorum/SKILL.md) | Convene 4-7 lenses → verdict without averaging away dissent |
| [superforecasting](superforecasting/SKILL.md) | Dated market-outcome → scored probability + falsifiable triggers |
| [prediction-market-odds](prediction-market-odds/SKILL.md) | Polymarket / Kalshi / FedWatch crowd odds |
| [analyst-derivatives-positioning](analyst-derivatives-positioning/SKILL.md) | Futures + options positioning, OI, skew |
| [forecast-ledger](forecast-ledger/SKILL.md) | Brier + calibration scoring loop (ledger.py) |

### Portfolio operations

| Skill | Role |
|-------|------|
| [hedge-fund-manager](hedge-fund-manager/SKILL.md) | PM/CIO delegating to specialist sub-skills |
| [tradfi-portfolio-manager](tradfi-portfolio-manager/SKILL.md) | Weekly portfolio note (REVIEW→ASSESS→RESEARCH→DECIDE→ORDER) |
| [agentic-fund-orchestration](agentic-fund-orchestration/SKILL.md) | Daily loop playbook |
| [regime-detection](regime-detection/SKILL.md) | Risk-on/off → gross-exposure dial |
| [portfolio-construction](portfolio-construction/SKILL.md) | Bubble-aware all-weather target weights |
| [risk-management](risk-management/SKILL.md) | Vol target, drawdown de-risk, CPPI, caps — deterministic veto |
| [rebalancing](rebalancing/SKILL.md) | Calendar-check / threshold-act, tax-aware |
| [dip-tranches-strategy](dip-tranches-strategy/SKILL.md) | Tiered dip-buying of dry powder |
| [tax-loss-harvesting](tax-loss-harvesting/SKILL.md) | Harvest losses without wash-sale trips |
| [fundamental-analysis](fundamental-analysis/SKILL.md) | Valuation research + backtest gate |
| [trend-following](trend-following/SKILL.md) | 200d-MA / dual-momentum / managed-futures signals |

### Macro analyst panel (thinker lenses)

| Skill | Thinker |
|-------|---------|
| [macro-panel](macro-panel/SKILL.md) | Conductor — convenes the panel, surfaces agreement vs disagreement |
| [analytics-lyn-alden](analytics-lyn-alden/SKILL.md) | Fiscal dominance / broad-money / BTC-as-hurdle |
| [analytics-ray-dalio](analytics-ray-dalio/SKILL.md) | Debt cycles / all-weather risk-parity |
| [analytics-stanley-druckenmiller](analytics-stanley-druckenmiller/SKILL.md) | Liquidity / timing / position-sizing |
| [analytics-lacy-hunt](analytics-lacy-hunt/SKILL.md) | Deflation dissent — debt→low-velocity→disinflation |
| [analytics-michael-pettis](analytics-michael-pettis/SKILL.md) | Trade / capital-flows / China |
| [analytics-russell-napier](analytics-russell-napier/SKILL.md) | Financial repression / structural-inflation |
| [analytics-warren-buffett](analytics-warren-buffett/SKILL.md) | Bubble-discipline / quality-value / cash-as-option |
| [analytics-benjamin-graham](analytics-benjamin-graham/SKILL.md) | Rules-based value origin — margin of safety, Mr. Market |
| [analytics-morgan-housel](analytics-morgan-housel/SKILL.md) | Behavioral-finance / investor-psychology guardrail |

### Trading desks + execution

| Skill | Role |
|-------|------|
| [strategy-discovery-backtest](./strategy-discovery-backtest/SKILL.md) | **THE GATE** — hypothesis→backtest→PASS/FAIL |
| [crypto-daytrading](./crypto-daytrading/SKILL.md) | Crypto intraday income desk |
| [stock-daytrading](./stock-daytrading/SKILL.md) | Equity intraday income desk |
| [crypto-advisor](./crypto-advisor/SKILL.md) | Crypto buy-the-dip / DCA advisor |
| [coinbase-cdp-connector](./coinbase-cdp-connector/SKILL.md) | Coinbase CDP CLI/MCP execution |
| [robinhood-connector](./robinhood-connector/SKILL.md) | Robinhood agentic MCP execution |

### Analytics / book-grounded lenses

| Skill | Source |
|-------|--------|
| [analyst-systematic-trading](analyst-systematic-trading/SKILL.md) | Robert Carver *Systematic Trading* |
| [analyst-technical-analysis](analyst-technical-analysis/SKILL.md) | Jacob Bernstein *The Ultimate Day Trader* |
| [analyst-crypto](analyst-crypto/SKILL.md) | Michael Howell *Capital Wars* + on-chain |
| [skill-supervisor](skill-supervisor/SKILL.md) | Propose/dispose improvement loop |

---

## Runnable helpers

- `13f-watch/watch.py` — dedup ledger + roster for institutional filings.
- `congressman-stock-watch/watch.py` — STOCK Act fetch + dedup ledger.
- `forecast-ledger/ledger.py` — Brier/calibration scoring for dated forecasts.
- `regime-detection/regime_monitor.py` — daily regime score → exposure multiplier.
- `dip-tranches-strategy/check_drawdown.py` — drawdown-from-52w-high → which tranche fires.

## Provenance

Backtest evidence in `../research/` and `../backtests/`. Strategy written up in `../strategy/` (v3 current).
Run notification-first; paper-trade before live; hard caps in code outside the LLM.
