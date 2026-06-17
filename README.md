# Financial Advisor Agent — Agentic Hedge-Fund + Crypto Workflows

> ⚠️ **Educational analysis only — not financial advice.** Past backtest performance does not guarantee future results. Validate with a fee-only fiduciary before deploying real capital.

A portable skill+workflow layer that turns **Claude Code, openclaw, or hermes** into a proactive financial advisor — watching markets daily and surfacing time-sensitive setups before they're missed.

The agent proposes; the human approves every order. Recommend-only, always.

## How it works

Two tiers run on any backend. FAST catches same-day setups; SLOW produces a weekly buy brief.

```
                      DATA SOURCES
  yfinance | FRED | alternative.me | EDGAR | FT/WSJ | Polymarket
                         |
          +--------------+---------------+
          |                              |
   FAST (daily cron)             SLOW (weekly workflow)
   scan -> gate -> DM            hedge-fund-committee
          |                              |
  dip-screener                   1. COLLECT  (x6 parallel)
  crypto-dip-scanner                regime, fomc, 13f,
  regime-detection                  congress, news, dips
  fomc-monitor                           |
  trend-stock-research           2. PANEL  (multi-lens-quorum)
          |                         4+ analyst lenses
  signal-convergence-alert               |
  (>=2 sources match)            3. DECIDE
          |                         risk veto -> buy brief
          +-------------+---------------+
                        |
                   DM to owner
              (silent when nothing fires)
                        |
       +-----------------------------------+
       | Claude Code  |  openclaw  | hermes |
       +-----------------------------------+
```

- **FAST** -- daily cron fires each scanner independently. A gate must pass (e.g. stock -30% from 52w high AND regime=RISK_ON) before a DM is sent; otherwise the job is silent. The convergence alert cross-references all pools and DMs when the same ticker appears in 2+ sources.
- **SLOW** -- a weekly multi-agent workflow fans out 6 research desks in parallel, ranks candidates by source count, runs each through a 4-lens analyst panel (Buffett, Druckenmiller, Alden, fundamentals), applies a binding risk-management veto, and produces a ranked buy brief with staged entry plans.
- **Backend** -- same ~60 skills install identically onto Claude Code, openclaw, or hermes. Only the scheduling primitive differs.

---

## Installation

### Prerequisites

- **Python 3** with `yfinance` — used by the data-pulling `.py` scripts bundled in `.agents/skills/` (e.g. `dip_screener.py`, `crypto_dip_scanner.py`, `ledger.py`). Install once: `pip install yfinance`.
- **Claude Code ≥ v2.1.154** with Dynamic Workflows enabled (`/config`) — required to run `/hedge-fund-committee`, `/research-market`, and the other slash-command workflows.
- **`opencode-drawer-workflows` plugin (v1.6.0+)** — required to run `.workflow.js` files from OpenCode sessions. Provides tools: `workflow`, `workflow_status`, `workflow_stop`, `workflow_save_run`. Install:
  1. Add `"opencode-drawer-workflows"` to the `plugin` array in `~/.config/opencode/opencode.json`
  2. `cd ~/.config/opencode && npm install opencode-drawer-workflows`
  3. Restart OpenCode. Workflow scripts live in `.agents/workflows/` (main: `hedge-fund-committee.workflow.js`).
  4. Run via: `workflow` tool with `script_path: ".agents/workflows/hedge-fund-committee.workflow.js"`

### Skills

Skills live in `.agents/skills/`. A `.claude/skills` symlink already points there, making every skill in that directory available to Claude Code when you open the repo:

```
.claude/skills -> ../.agents/skills   # already present in the repo
```

To install skills onto another runtime (openclaw, hermes, Cursor):

| Runtime | Command |
|---|---|
| **Claude Code** | `npx skills add dzianisv/financial-advisor-agents` (auto-detected) |
| **openclaw** | `npx skills add dzianisv/financial-advisor-agents --agent openclaw --copy` |
| **hermes** | `npx skills add dzianisv/financial-advisor-agents --agent hermes-agent --copy` |

`--copy` ships the bundled Python scripts alongside each `SKILL.md` (needed for data-pulling skills). Without `--copy`, skills install but the `.py` helpers that pull live prices are absent.

### Workflows (Claude Code only)

Workflow scripts live in `.agents/workflows/`. Symlinks in `.claude/workflows/` register them as slash commands — present in this repo:

```
.claude/workflows/hedge-fund-committee.js   -> ../../.agents/workflows/hedge-fund-committee.workflow.js
.claude/workflows/research-market.js        -> ../../.agents/workflows/research-market.workflow.js
.claude/workflows/pairwise-eval.js          -> ../../.agents/workflows/pairwise-eval.workflow.js
.claude/workflows/multi-lens-quorum.js      # direct workflow (not a symlink)
.claude/workflows/trend-stock-research.js   # direct workflow (not a symlink)
```

To use them from another project, copy to `~/.claude/workflows/`:

```bash
cp financial-advisor-agents/.claude/workflows/*.js ~/.claude/workflows/
```

> On macOS/Linux the symlinks resolve automatically. On Windows, copy the real files from `.agents/workflows/` instead.

---

## Quick Start

### Plain-language (always works)

```
"research whether I should buy ETH, I hold 20% SOL"
"should I trim NVDA — I'm 40% in it"
```

Claude routes to the right workflow and passes your portfolio as args.

### Slash commands

With the repo open in Claude Code, the workflows are available as:

```
/hedge-fund-committee    ← weekly equity committee → staged buy brief
/research-market         ← ad-hoc crypto or equity research question
/pairwise-eval           ← blind A/B comparison of two research reports
/multi-lens-quorum       ← convene N independent analyst lenses on a judgment call
/trend-stock-research    ← research-first trend-stock screen → nominees for quorum
```

### OpenCode workflow execution

OpenCode runs workflow scripts through its installed `workflow` tool from the `opencode-drawer-workflows` plugin. The plugin supplies the workflow primitives used by `.agents/workflows/*.workflow.js`; pass the script and arguments with the Drawers tool schema:

```json
{
  "script_path": ".agents/workflows/research-market.workflow.js",
  "args": {
    "question": "Should I buy BTC today?",
    "portfolio": "no direct BTC",
    "date": "2026-06-17"
  }
}
```

### Explicit Workflow tool form

Use this when you want to pass specific args (ticker, date, portfolio):

**Ad-hoc research — crypto** (`research-market`):

```js
Workflow({
  scriptPath: "./.agents/workflows/research-market.workflow.js",
  args: {
    question:  "BTC reached 65k from the drop to 61k. I hold 30% in COIN. Should I buy BTC today?",
    portfolio: "~30% of book in COIN (levered crypto-beta proxy); no direct BTC.",
    date:      "2026-06-16",   // required — Date.now() is unavailable in the workflow runtime
    anchor:    ""              // optional seed price; leave "" to let Gather fetch live
  }
})
```

**Ad-hoc research — equity / mixed** (`research-market`):

```js
Workflow({
  scriptPath: "./.agents/workflows/research-market.workflow.js",
  args: {
    question:  "NVDA pulled back 15% from ATH. I'm 40% concentrated in it. Should I trim?",
    portfolio: "40% NVDA, remainder unspecified. $1M tradfi book, no leverage.",
    date:      "2026-06-16"
    // assets + tickers are extracted from `question` by the manager LLM — no separate ticker arg needed
  }
})
```

**Weekly equity committee** (`hedge-fund-committee`):

```js
Workflow({
  scriptPath: "./.agents/workflows/hedge-fund-committee.workflow.js",
  args: { date: "2026-06-16" }  // no ticker needed — open-universe discovery
})
// Output: reports/hedge-fund-brief-<date>.md (30-sec read) + reports/hedge-fund-committee-<date>.md (full memo)
```

**Blind A/B comparison of two research reports** (`pairwise-eval`):

```js
Workflow({
  scriptPath: "./.agents/workflows/pairwise-eval.workflow.js",
  args: {
    a:        "/path/to/iter1.report.md",   // hypothesis: worse (baseline)
    b:        "/path/to/iter2.report.md",   // hypothesis: better (candidate)
    question: "BTC reached 65k from 61k. I hold 30% in COIN. Should I buy today?",
    judges:   5                             // number of blind judges; default 5
  }
})
```

### Output

Each research workflow writes:

- `research/research.crypto.<date>.md` or `research/research.stock.<date>.md` — the full report.
- A dated row in the `forecast-ledger` (`ledger.py`) — tracked for Brier-score grading.

### Deeper docs

| Doc | Purpose |
|---|---|
| `crypto/crypto.goal.md` | Crypto book mission + constraints |
| `crypto/crypto.prd.md` | Feature spec for the crypto workflow |
| `crypto/crypto.tdd.md` | Architecture + wiring diagrams |
| `crypto/eval/IMPROVE-LOOP.md` | How to improve a workflow with pairwise-eval |

---

## Install once, then just chat

One command installs every skill onto your agent. It auto-detects the host (Claude Code, openclaw, hermes, Cursor, +others), pulls all skills, and wires them in:

```bash
npx skills add dzianisv/financial-advisor-agents
```

That's the whole setup. **You don't run a workflow or type a slash command** — the skills route themselves from what you say. After install, just ask:

```
"Should I buy the dip on BTC today?"          → crypto-dip-scanner / analyst-crypto
"What did Buffett just buy?"                   → 13f-watch
"Run the weekly committee."                    → agentic-fund-orchestration
"What's the market regime right now?"          → regime-detection
"What would Lyn Alden think of this?"          → analytics-lyn-alden
"Is there a multi-source convergence signal?"  → signal-convergence-alert
```

Each skill's description is written as a routing trigger, so the right desk answers the right question with no ceremony.

### Per-runtime install

| Runtime | Command |
|---|---|
| **Claude Code** | `npx skills add dzianisv/financial-advisor-agents` (auto-detected) |
| **openclaw** | `npx skills add dzianisv/financial-advisor-agents --agent openclaw --copy` |
| **hermes** | `npx skills add dzianisv/financial-advisor-agents --agent hermes-agent --copy` |

`--copy` ships the Python helper scripts alongside each `SKILL.md` (needed for the data-pulling skills). For scheduled/proactive operation (daily scans + weekly committee), see [`docs/`](docs/) — `setup-claudecode.md`, `setup-openclaw.md`, `setup-hermes.md`.

### The multi-agent workflows (Claude Code only)

`npx skills add` installs **skills**, not the dynamic [Workflow](https://code.claude.com/docs/en/workflows) scripts (the committee / panel orchestrators). Those are a Claude-Code-native feature — they live in `.claude/workflows/` and Claude Code exposes any `.js` there as a `/<name>` command. Two ways to get them:

```bash
# Option A — clone the repo, open Claude Code in it; the workflows are project /commands
git clone https://github.com/dzianisv/financial-advisor-agents && cd financial-advisor-agents
#   → /hedge-fund-committee   /research-market   /pairwise-eval   /multi-lens-quorum   /trend-stock-research

# Option B — make them global (available in every project)
cp financial-advisor-agents/.claude/workflows/*.js ~/.claude/workflows/
```

Then run e.g. `/hedge-fund-committee` or `/research-market`. (Needs Claude Code ≥ v2.1.154 with Dynamic workflows enabled in `/config`. Workflows are a Claude Code feature — openclaw/hermes use the skills, which orchestrate via their own primitives.)

> Note: some `.claude/workflows/*.js` entries are symlinks to `.agents/workflows/` (they resolve on macOS/Linux; on Windows copy the real files). `multi-lens-quorum.js` and `trend-stock-research.js` are standalone files in `.claude/workflows/` directly.

---

## Two active workstreams

### 1. Stocks / TradFi portfolio workflow

Manages a **~$1M tradfi book** (RSP 70 / GLD 15 / IEF 15 baseline) through an AI-bubble environment. Runs the loop: **regime-detect → scan → committee → human-approve → execute → report**.

Key artifacts:

| Artifact | Purpose |
|---|---|
| [`GOAL.md`](GOAL.md) | Mission + bubble evidence + done/not-done checklist |
| [`strategy/v3`](strategy/v3-bubble-aware-all-weather.md) | Bubble-Aware All-Weather strategy (the recommended allocation) |
| [`docs/prd.md`](docs/prd.md) | Features, cadence, personas |
| [`docs/tdd.md`](docs/tdd.md) | Architecture, wiring diagrams, data contracts |
| [`.agents/workflows/hedge-fund-committee.workflow.js`](.agents/workflows/) | Weekly committee → ranked next-buy memo |

**Status:** fast-tier daily scanners live on openclaw (cron + liveness); weekly committee workflow validated (3 iterations); congress stock-watch wired (`congress/`).

---

### 2. Crypto portfolio workflow

Manages a **~$177k crypto book** with a BTC-as-hurdle filter — only deploy into tokens that pass the 6-point infrastructure value-accrual test (HYPE the current benchmark).

Full spec: [`crypto/`](crypto/) — `crypto.goal.md` · `crypto.prd.md` · `crypto.tdd.md` · `crypto.loop.md`

**Status:** skill tree designed + specced; G-Eval harness baselined (85/100); crypto.loop.md orchestrates daily dip-scan + weekly research desk cycle.

---

## Skills

### Workflows (5 total, all in `.claude/workflows/`)

| Slash command | Description |
|---|---|
| `/hedge-fund-committee` | Find the next stocks to BUY and hand over a STAGED ENTRY plan. Open-universe candidate discovery → panel vote → risk veto → scale-in plan. RECOMMEND-ONLY. |
| `/research-market` | Unified portfolio-aware research (crypto + equities). LLM manager discovers skills live, decides everything — assets, seats, panel, chair. Pass `question` + optional `portfolio` + `date`. |
| `/multi-lens-quorum` | Convene N independent analyst lenses on ONE judgment call; synthesize consensus without averaging away dissent. |
| `/trend-stock-research` | Research-first trend-stock screen: prescreen → parallel journalism → non-obvious beneficiary mapping → 3-question skeptic filter → route to multi-lens-quorum. |
| `/pairwise-eval` | Blind A/B comparison of two research reports — N position-randomized judges, majority vote. Used in the improve loop. |

### Data & monitoring

| Skill | Description |
|---|---|
| `13f-watch` | Watch 13F filings, surface new initiations + cross-fund conviction clusters; dedupes candidates |
| `congressman-stock-watch` | Congressional stock trades feed |
| `crypto-dip-scanner` | Daily BTC/ETH/SOL/BNB/AVAX dip scanner; alerts on -30%+ from 52w high + extreme fear |
| `dip-screener` | Equity dip screener |
| `dip-tranches-strategy` | Staged entry / tranche sizing for dip entries |
| `fomc-monitor` | Fed FOMC calendar, statement, and dot-plot monitor |
| `liveness-monitor` | Monitors that scheduled jobs are running; DMs on stale job |
| `portfolio-monitor` | Portfolio state monitor |
| `prediction-market-odds` | Polymarket / Kalshi odds for macro/market events |
| `regime-detection` | Market regime classifier (risk-on / risk-off / transition) |
| `signal-convergence-alert` | Multi-source convergence signal detector |

### Crypto data

| Skill | Description |
|---|---|
| `crypto-liquidity-data` | Crypto liquidity and ETF flow data seat |
| `crypto-onchain-data` | On-chain valuation data (MVRV-Z, NUPL, etc.) |
| `analyst-derivatives-positioning` | Derivatives and options positioning data seat |

### News feeds (feed-*)

| Skill | Description |
|---|---|
| `feed-bitcoinmagazine` | Bitcoin Magazine RSS/API adapter |
| `feed-coindesk` | CoinDesk RSS/API adapter |
| `feed-cointelegraph` | CoinTelegraph RSS/API adapter |
| `feed-decrypt` | Decrypt RSS/API adapter |
| `feed-theblock` | The Block RSS/API adapter |
| `feed-bloomberg` | Bloomberg macro/finance headline adapter |
| `feed-ft` | Financial Times headline adapter |
| `feed-wsj` | Wall Street Journal headline adapter |

### Research desks & chairs

| Skill | Description |
|---|---|
| `crypto-research-desk` | Consolidates crypto gather seats into one sourced brief |
| `stock-research-desk` | Consolidates equity gather seats into one sourced brief |
| `crypto-chair` | Crypto committee chair; portfolio-aware buy/sell decision |
| `stock-chair` | Equity committee chair; portfolio-aware buy/sell decision |
| `research-manager` | Intake/triage desk head; discovers skills live, assembles the research desk for any query |
| `narrative-news` | Consumes feed-* adapters → deduped events with priced-in tags |
| `crypto-news-store` | Dedup/state store for crypto news events |

### Analyst lenses (analyst-* / analytics-*)

| Skill | Description |
|---|---|
| `analyst-crypto` | Crypto analyst lens |
| `analyst-systematic-trading` | Systematic/quant trading lens |
| `analyst-technical-analysis` | Technical analysis lens |
| `analytics-benjamin-graham` | Value investing (Graham) lens |
| `analytics-lacy-hunt` | Deflationary/rates dissent lens (bear seat) |
| `analytics-lyn-alden` | Lyn Alden macro/monetary lens |
| `analytics-michael-pettis` | Global imbalances / trade lens (Pettis) |
| `analytics-morgan-housel` | Behavioral/sizing guardrail (non-voting) |
| `analytics-ray-dalio` | Macro cycles lens (Dalio) |
| `analytics-russell-napier` | Credit/financial repression lens (Napier) |
| `analytics-stanley-druckenmiller` | Macro momentum lens (Druckenmiller) |
| `analytics-warren-buffett` | Business quality / intrinsic value lens (equity only) |
| `macro-panel` | Multi-thinker macro panel conductor |
| `fundamental-analysis` | Equity fundamentals analysis |
| `superforecasting` | Tetlock-style probabilistic forecasting |

### Portfolio management

| Skill | Description |
|---|---|
| `agentic-fund-orchestration` | Top-level agentic hedge-fund orchestration playbook |
| `defi-portfolio-manager` | DeFi portfolio management |
| `hedge-fund-13f-analysis` | 13F filings analysis |
| `hedge-fund-manager` | Portfolio-level management and sizing |
| `multi-lens-quorum` | Convene N lenses on a judgment call |
| `portfolio-construction` | Portfolio construction and allocation |
| `rebalancing` | Rebalancing logic |
| `risk-management` | Risk management and position sizing |
| `tax-loss-harvesting` | Tax-loss harvesting |
| `tradfi-portfolio-manager` | TradFi portfolio manager skill |
| `trend-following` | Trend-following strategy |
| `trend-stock-research` | Research-first trend-stock screen |

### Evaluation & ops

| Skill | Description |
|---|---|
| `crypto-workflow-eval` | G-Eval harness for crypto workflow quality |
| `forecast-ledger` | Dated forecast log with Brier-score tracking |
| `hedge-fund-committee-eval` | Blind LLM judge for committee run quality |
| `skill-supervisor` | Skill quality supervision |

---

## Deployment targets

Same skills install onto any of:

| Runtime | Scheduling primitive | Notification |
|---|---|---|
| **Claude Code** | `/loop` + Routines + dynamic workflows | terminal / push |
| **openclaw** | `heartbeat` + `HEARTBEAT.md` | Telegram DM |
| **hermes-ai** | hermes scheduler | configured channel |

---

## Repository layout

```
GOAL.md                    # tradfi mission north-star
crypto/                    # crypto workflow spec (goal / prd / tdd / loop)
strategy/                  # v1→v3 strategy evolution; v3 = current recommended allocation
research/                  # cited research notes (AI bubble, crypto, macro, frameworks)
backtests/                 # runnable backtest scripts + cached results
docs/                      # prd / tdd / setup guides (openclaw / claude-code / hermes)
.agents/skills/            # all skill modules (SKILL.md + implementation)
.agents/workflows/         # multi-agent workflow scripts
congress/                  # congressional stock-watch feed
report/                    # generated charts + published write-ups
```

---

## Backtest summary (tradfi v3)

1. **Don't bet the whole $1M on cap-weight S&P/QQQ at CAPE ~41.** 2000-2026 backtest: S&P −55%, QQQ −83%; 2000-2009 was a lost decade.
2. **Selection isn't the edge.** Bottom-up stock-picking doesn't reliably beat a cheap index (backtests + SPIVA).
3. **The edge is structural.** De-concentrated diversification + trend/regime overlay (crisis alpha) + dip-reserve = caps left tail without a market call. → [`strategy/v3`](strategy/v3-bubble-aware-all-weather.md)

Tracking issue: https://github.com/dzianisv/financial-advisor-agents/issues/1
