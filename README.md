# Financial Advisor Agent — Agentic Hedge-Fund + Crypto Workflows

> ⚠️ **Educational analysis only — not financial advice.** Past backtest performance does not guarantee future results. Validate with a fee-only fiduciary before deploying real capital.

A portable skill+workflow layer that turns **Claude Code, openclaw, or hermes** into a proactive financial advisor — watching markets daily and surfacing time-sensitive setups before they're missed.

The agent proposes; the human approves every order. Recommend-only, always.

---

## Installation

### Prerequisites

- **Python 3** with `yfinance` — used by the data-pulling `.py` scripts bundled in `.agents/skills/` (e.g. `dip_screener.py`, `crypto_dip_scanner.py`, `ledger.py`). Install once: `pip install yfinance`.
- **Claude Code ≥ v2.1.154** with Dynamic Workflows enabled (`/config`) — required to run `/research-crypto-market` and the other slash-command workflows.

### Skills

Skills live in `.agents/skills/`. A `.claude/skills` symlink already points there, making every skill in that directory available to Claude Code when you open the repo:

```
.claude/skills -> ../.agents/skills   # already present in the repo
```

To install skills onto another runtime (openclaw, hermes, Cursor):

| Runtime | Command |
|---|---|
| **Claude Code** | `npx skills add dzianisv/backtest` (auto-detected) |
| **openclaw** | `npx skills add dzianisv/backtest --agent openclaw --copy` |
| **hermes** | `npx skills add dzianisv/backtest --agent hermes-agent --copy` |

`--copy` ships the bundled Python scripts alongside each `SKILL.md` (needed for data-pulling skills). Without `--copy`, skills install but the `.py` helpers that pull live prices are absent.

### Research workflows (Claude Code only)

The three research workflow scripts live in `crypto/workflows/`. Symlinks in `.claude/workflows/` register them as slash commands — they are already present in this repo:

```
.claude/workflows/research-crypto-market.js  -> ../../crypto/workflows/research-crypto-market.js
.claude/workflows/research-stock-market.js   -> ../../crypto/workflows/research-stock-market.js
.claude/workflows/pairwise-eval.js           -> ../../crypto/workflows/pairwise-eval.js
```

To use them from another project, copy to `~/.claude/workflows/`:

```bash
cp backtest/.claude/workflows/research-crypto-market.js ~/.claude/workflows/
cp backtest/.claude/workflows/research-stock-market.js ~/.claude/workflows/
cp backtest/.claude/workflows/pairwise-eval.js ~/.claude/workflows/
```

> On macOS/Linux the symlinks resolve automatically. On Windows, copy the real files from `crypto/workflows/` instead.

---

## Quick Start

### Plain-language (always works)

```
"research whether I should buy ETH, I hold 20% SOL"
"should I trim NVDA — I'm 40% in it"
```

Claude routes to the right workflow and passes your portfolio as args.

### Slash commands

With the repo open in Claude Code, the three workflows are available as:

```
/research-crypto-market
/research-stock-market
/pairwise-eval
```

### Explicit Workflow tool form

Use this when you want to pass specific args (ticker, date, portfolio):

**Crypto buy/sell research** (`research-crypto-market`):

```js
Workflow({
  scriptPath: "/Users/engineer/workspace/backtest/crypto/workflows/research-crypto-market.js",
  args: {
    question:  "BTC reached 65k from the drop to 61k. I hold 30% in COIN. Should I buy BTC today?",
    portfolio: "~30% of book in COIN (levered crypto-beta proxy); no direct BTC; remainder unspecified.",
    date:      "2026-06-15",   // required — Date.now() is unavailable in the workflow runtime
    anchor:    ""              // optional seed price; leave "" to let Gather fetch live
  }
})
```

**Equity buy/sell/trim research** (`research-stock-market`):

```js
Workflow({
  scriptPath: "/Users/engineer/workspace/backtest/crypto/workflows/research-stock-market.js",
  args: {
    question:  "NVDA is up ~40% off its April low and I hold 12% of the book in it. Should I trim or add a cheaper AI-semi name?",
    portfolio: "~12% of book in NVDA; no other semis; equity risk from risk-capital sleeve only.",
    date:      "2026-06-15",
    ticker:    "NVDA",         // optional hint for the ledger row; chair drives the call
    anchor:    ""
  }
})
```

**Blind A/B comparison of two research reports** (`pairwise-eval`):

```js
Workflow({
  scriptPath: "/Users/engineer/workspace/backtest/crypto/workflows/pairwise-eval.js",
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
npx skills add dzianisv/backtest
```

That's the whole setup. **You don't run a workflow or type a slash command** — the skills route themselves from what you say. After install, just ask:

```
"Should I buy the dip on BTC today?"          → crypto-advisor
"Is HYPE a real infra token or just hype?"    → crypto-token-screener
"What did Buffett just buy?"                   → 13f-watch
"Run the weekly committee."                    → agentic-fund-orchestration
"What's the market regime right now?"          → regime-detection
```

Each skill's description is written as a routing trigger, so the right desk answers the right question with no ceremony.

### Per-runtime install

| Runtime | Command |
|---|---|
| **Claude Code** | `npx skills add dzianisv/backtest` (auto-detected) |
| **openclaw** | `npx skills add dzianisv/backtest --agent openclaw --copy` |
| **hermes** | `npx skills add dzianisv/backtest --agent hermes-agent --copy` |

`--copy` ships the Python helper scripts alongside each `SKILL.md` (needed for the data-pulling skills). For scheduled/proactive operation (daily scans + weekly committee), see [`docs/`](docs/) — `setup-claudecode.md`, `setup-openclaw.md`, `setup-hermes.md`.

### The multi-agent workflows (Claude Code only)

`npx skills add` installs **skills**, not the dynamic [Workflow](https://code.claude.com/docs/en/workflows) scripts (the committee / panel orchestrators). Those are a Claude-Code-native feature and travel a different way — they live in `.claude/workflows/` and Claude Code exposes any `.js` there as a `/<name>` command. Two ways to get them:

```bash
# Option A — clone the repo, open Claude Code in it; the workflows are project /commands
git clone https://github.com/dzianisv/backtest && cd backtest
#   → /hedge-fund-committee   /research-crypto-market   /research-stock-market   /research-crypto-market

# Option B — make them global (available in every project)
cp backtest/.claude/workflows/*.js ~/.claude/workflows/
```

Then run e.g. `/hedge-fund-committee` or `/research-crypto-market`. (Needs Claude Code ≥ v2.1.154 with Dynamic workflows enabled in `/config`. Workflows are a Claude Code feature — openclaw/hermes use the skills, which orchestrate via their own primitives; the everyday committee question is also answerable by the `agentic-fund-orchestration` skill, which installs normally.)

> Note: the `.claude/workflows/*.js` entries are symlinks to the canonical scripts in `.agents/workflows/` and `crypto/workflows/` — they resolve on macOS/Linux. On Windows, copy the real files from those dirs instead.

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

Core skills: `regime-detection` · `trend-stock-research` · `dip-screener` · `fomc-monitor` · `prediction-market-odds` · `forecast-ledger` · `hedge-fund-manager` · `superforecasting` · `macro-panel` · `multi-lens-quorum`

**Status:** fast-tier daily scanners live on openclaw (cron + liveness); weekly committee workflow validated (3 iterations); congress stock-watch wired (`congress/`).

---

### 2. Crypto portfolio workflow

Manages a **~$177k crypto book** with a BTC-as-hurdle filter — only deploy into tokens that pass the 6-point infrastructure value-accrual test (HYPE the current benchmark).

Full spec: [`crypto/`](crypto/) — `crypto.goal.md` · `crypto.prd.md` · `crypto.tdd.md` · `crypto.loop.md`

Core skills: `crypto-chair` · `crypto-research-desk` · `crypto-dip-scanner` · `crypto-liquidity-data` · `crypto-onchain-data` · `crypto-workflow-eval` · `analyst-crypto`

**Status:** skill tree designed + specced; G-Eval harness baselined (85/100); crypto.loop.md orchestrates daily dip-scan + weekly research desk cycle.

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

Tracking issue: https://github.com/dvashchuk/backtest/issues/1
