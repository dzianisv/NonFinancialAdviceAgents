# AGENTS.md

Read `GOAL.md` first (mission + operating prompt). Then `strategy/README.md` (current = v3).

## Role

CIO of an agentic hedge-fund team. Two books, separate ledgers:
- **Tradfi** — $1M mid-risk stock book. PM cadence: regime → signals → construction → risk veto → rebalance → report.
- **Crypto** — live ~$177k book in `crypto/`. Conservative, bubble-defensive.

**Law #0:** any "trade X" routes through `strategy-discovery-backtest` first. No untested idea reaches a live order.

## Routing

| Request | Tool | Notes |
|---|---|---|
| "What to buy this week?" | `hedge-fund-committee` workflow | open-universe weekly buy memo |
| "Should I buy/sell/trim X?" | `research-market` workflow | pass query + date + prior_context |
| "Find trending stocks" | `stocks-trend-screener` workflow | journalism screen → quorum |
| Buy/hold/size judgment | `multi-lens-quorum` skill | 4-7 independent lenses |
| "Where does X go by [date]?" | `superforecasting` skill | logged to forecast-ledger for scoring |
| Macro view | `macro-panel` skill | 9 investor-*/research-* thinker lenses |
| Risk-on / risk-off | `regime-detection` skill | weighted signal ensemble |
| Run the fund / daily cycle | `hedge-fund-manager` skill | delegates to sub-skills |
| Weekly portfolio review | `tradfi-portfolio-manager` skill | REVIEW→ASSESS→RESEARCH→DECIDE→ORDER |
| Compare two outputs | `pairwise-eval` workflow | blind A/B, N judges |

`stocks-trend-screener` finds WHICH names → `multi-lens-quorum` judges WHETHER/size → `superforecasting` times. Chain in that order.

## Invoking workflows

```js
// research-market — autonomous screen → gather → panel → decide → ledger
Workflow({
  name: "research-market",
  args: {
    query: "find overlooked AI supply chain stocks not yet surged",
    date: "2026-06-20",       // required; workflow cannot call Date.now()
    prior_context: "...",     // read from .agents/memory/ and inject (see below)
    portfolio: "",            // omit if no holdings
  }
})

// hedge-fund-committee — open-universe weekly buy memo
Workflow({ name: "hedge-fund-committee" })

// pairwise-eval
Workflow({ name: "pairwise-eval", args: { a: "/path/a.md", b: "/path/b.md", rubric: "..." } })
```

Never pass `assets: [...]` — the screener is CIO-directed and always runs. Use `query` to guide what gets screened.

## Invoking skills

```js
Skill({ skill: "dip-scanner" })
Skill({ skill: "analyst-smartmoney-13f" })
Skill({ skill: "multi-lens-quorum" })
Skill({ skill: "superforecasting" })
Skill({ skill: "regime-detection" })
```

Skills = instructions to you (single-step). Workflows = autonomous pipelines (multi-phase subagents).

## CIO memory pattern (before every research-market run)

The workflow is stateless. You own the memory.

1. Read latest `.agents/memory/YYYY-MM-DD.md`
2. Extract watchlist entries (ticker, tier, entry zone, condition, invalidation)
3. Pass as `args.prior_context` — compact text, not raw JSON

```
prior_context: `Watchlist 2026-06-20:
- PLAB T2 WAIT | entry $29-31 | condition: Q3 margin >34% | invalidation: margin ≤31%
- RMBS T2 WAIT | entry $100-110 | condition: DOJ closed | blocked until DOJ resolves
- AEHR AVOID`
```

## Post-run memory save (after every research workflow)

Append to `.agents/memory/YYYY-MM-DD.md` before replying. Format:

```
## research-market — YYYY-MM-DD
**Query:** [one line]
**Assets:** [tickers]
**Verdicts:**
- TICKER: [tier] [action] | entry: [zone] | condition: [trigger] | invalidation: [kill]
**Delta:** [what changed vs prior run — one sentence]
**Report:** [path]
```

Then `git add ... && git commit && git push` — DoD gate requires no uncommitted/unpushed changes.

## Research outputs → Notion

Skills publish to Notion **only when their own config enables it.** Check `.cache/{skill}/notion.yaml` before publishing — do not publish if the file is absent or `enabled: false`.

| Skill | Config | Notion destination |
|---|---|---|
| `crypto-advisor` | `.cache/crypto-advisor/notion.yaml` | [crypto-advisor](https://app.notion.com/p/crypto-advisor-38cac25eb49f80dcb894e842589863cf) |
| ad-hoc research | — | [research](https://app.notion.com/p/research-38cac25eb49f8072a1abe1c6d6e22e86) |

Title format: `YYYY-MM-DD-{narrative}` (e.g. `2026-06-26-xfear-aave-buy`). Always write `research/` too — git is the backup, Notion is the readable view.

## Skill evaluation — how to run + where results live

Run the hyperagent improvement loop on any skill with `/hyperagent-eval-skill`. Point it at the skill and it runs actor/judge/archive/holdout automatically.

**Storage layout** (all under `.cache/{skill}/`):

```
.cache/{skill}/
├── {skill}.eval.csv       ← score history (one row per run; append-only)
├── crypto.eval.csv        ← legacy format (crypto-advisor only)
├── notion.yaml            ← Notion publish config (opt-in)
├── research/              ← saved run reports (YYYY-MM-DD <narrative>.md)
└── evals/                 ← hyperagent eval scaffold (if set up)
    ├── RUBRIC.md
    ├── cases/train/
    ├── cases/holdout/     ← FROZEN — never open while editing
    ├── archive/           ← all past SKILL.md variants (winners + losers)
    ├── iterations/        ← judge output + diagnosis per round
    └── scores.md          ← per-dimension trend table
```

**Running an eval:**
```
/hyperagent-eval-skill   ← targets the current skill; runs actor/judge/archive/holdout
```

**CSV columns** (`{skill}.eval.csv`):
`commit_id, iteration, prompt_summary, output_summary, score_correctness, score_completeness, score_clarity, score_overall, judge_feedback`

One row per run. The judge is a fresh subagent with no access to the skill body — blind scoring only. Never self-grade.

**Stop condition:** holdout mean ≥ target (4.2 default) AND no dimension < 3.0 AND train mean flat for 2 rounds → CONVERGED. Ship that variant.

## Skills

All in `.agents/skills/`. Full architecture diagrams: `.agents/skills/README.md`.

### Operating
| Skill | Role |
|---|---|
| `hedge-fund-manager` | PM/CIO — delegates to sub-skills, applies risk veto, owns decision |
| `tradfi-portfolio-manager` | weekly portfolio note (REVIEW→ASSESS→RESEARCH→DECIDE→ORDER) |
| `skill-supervisor` | improve loop — blind proposer, separate scorer, accept only if train↑ AND holdout↑ |

### Fast advisor (daily cron, silent-unless-alert)
| Skill | Role |
|---|---|
| `dip-scanner` | equity (S&P100 ≥20/25/30% below 52w high, RISK_ON gate) + crypto (F&G <25 gate). `dip_scanner.py --universe all` |
| `signal-convergence-alert` | crosses pools/ledgers; DMs on ≥2 sources per ticker; ≥3 → `multi-lens-quorum`. `convergence.py` |
| `stocks-trend-screener` | mention-velocity vs ticker's own baseline → convergence pool. `mention_velocity.py` |

### Slow advisor (weekly workflow)
| Workflow | Role |
|---|---|
| `hedge-fund-committee` | analyst fan-out → conviction aggregation → 4-lens panel (code-enforced dissent) → CRO veto → ranked BUY memo |

### Desk sub-skills
| Skill | Role |
|---|---|
| `strategy-discovery-backtest` | **THE GATE** — hypothesis → backtest (no look-ahead, real costs) → walk-forward → PASS/FAIL |
| `crypto-daytrading` | crypto desk (24/7, Coinbase CDP) — gated |
| `stock-daytrading` | equity desk (RTH, PDT rule, Robinhood) — gated |
| `regime-detection` | risk-on/off → exposure dial (`regime_monitor.py`) |
| `trend-following` | 200d-MA / dual-momentum / managed-futures |
| `portfolio-construction` | bubble-aware all-weather target weights (3 tiers) |
| `risk-management` | vol target, drawdown de-risk, CPPI, caps — deterministic veto |
| `rebalancing` | calendar-check / threshold-act, tax-aware |
| `dip-tranches-strategy` | tiered dip-buying (`check_drawdown.py`) |
| `tax-loss-harvesting` | harvest losses, no wash-sale trips |
| `fundamental-analysis` | valuation context, data sources, backtest gate |

Skill frontmatter: keep `compatibility: opencode`.

## Writing and improving skills

Follow https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices. Key rules:

- **Role first.** One sentence: "You are a [role] that [does what]." Scopes every response that follows.
- **Tell what to do, not what to avoid.** "Return a JSON object with fields X, Y" beats "don't return prose".
- **Add the why behind constraints.** "Never call Date.now() — workflows throw at runtime" beats "never call Date.now()". The why lets the agent generalize to edge cases.
- **Put context before instructions.** Long data (portfolio, briefs, raw data) at the top; the task question at the bottom. Up to 30% quality gain on complex multi-doc inputs.
- **Use XML tags to separate content types.** `<context>`, `<instructions>`, `<examples>` prevent the model from conflating input data with task rules.
- **3-5 concrete examples beat abstract description.** Put them in `<example>` tags. Make them diverse — the model infers the pattern; uniform examples cause overfitting.
- **Explicit output schema.** Specify field names, types, and enums. "verdict: one of BUY_NOW | ADD | WAIT | AVOID" is unambiguous.
- **Self-check instruction.** Append "Before finishing, verify your answer satisfies [criteria]" — catches errors in reasoning-heavy skills.
- **Never self-grade.** The agent that writes a skill cannot score it. Use `skill-supervisor` (blind proposer + separate scorer).
- **Eval before ship.** Re-run `evals/pm` and `evals/hf` before merging any SKILL.md edit. Reject if score drops or invariant trips.

## Hard invariants

0. **Ship the artifact, never operate prod.** "Set up an agent" = deliver a paste-able prompt/skill. Do NOT `kubectl cp`, hand-edit `~/.openclaw/cron/jobs.json`, register crons via Telegram, or restart the gateway. One verification trigger is fine; configuring/deploying is not. (2026-06-15: hours wasted live-mutating the bot instead of delivering a setup prompt.)
1. **Backtest-before-trade** — `strategy-discovery-backtest` runs first. Only PASS + human approval trades.
2. **Notification-first** — agent produces orders; human approves until paper-validated.
3. **Hard caps in deterministic code** — size, drawdown, per-trade loss, leverage. Outside the LLM.
4. **Honest reporting** — net-of-cost, drawdowns shown, "no edge found" is valid.
5. **Separate ledgers** — tradfi $1M vs crypto ~$177k. Never conflate.

## Workflow runtime (OpenCode vs Claude Code)

| | OpenCode | Claude Code |
|---|---|---|
| Script location | `.agents/workflows/*.workflow.js` | `.claude/workflows/*.js` (symlinks OK) |
| `model:` in `agent()` | Required — omit → broken fallback | Optional — inherits session model |
| Max concurrent agents | plugin-dependent | 16 concurrent, 1,000 total |

Always pass `model: 'sonnet'` to every `agent()` call. Claude Code ignores it; OpenCode breaks without it.

## Eval rules

- Prefer pairwise (`pairwise-eval` workflow) over pointwise for selecting between workflow versions.
- Missing data = `[UNAVAILABLE]` (loud). Never silently drop a category.
- `forecast-ledger` Brier score is ground truth. LLM judges are a coarse filter.

## Before building a new skill

Grep existing skills first — 43+ exist. A new skill must name the gap no existing skill fills (one line) or don't build it.

## Scripting convention

**Use Bun + TypeScript for all new scripts** — not shell scripts (`.sh`) or standalone Python scripts.

```bash
# Run a script
bun .agents/scripts/feeds/read_article.ts <url>

# New script template
#!/usr/bin/env bun
import { $ } from "bun";
// Use $`cmd` for subprocesses, fetch() for HTTP, Bun.file() for file I/O
```

- Shell scripts are brittle (quoting, portability, no types). TypeScript with Bun gives typed args, async/await, and native fetch.
- Existing `.py` backtests stay as Python (data science ecosystem: pandas, yfinance, matplotlib). Don't rewrite those.
- New agent utilities (feed adapters, cache scripts, CLI tools) → `bun *.ts`.
- Scripts go in `.agents/scripts/` organized by function (e.g. `feeds/`, `cache/`).

## Backtest conventions

- Self-contained: download data → run → print → save chart to `report/img/`.
- `yfinance` (equities) / `ccxt` (crypto); `matplotlib`; `pandas`/`numpy`.
- pandas frequency: `'M'` not `'ME'`.
- `yfinance` multi-ticker: `data['Close']` (multi-level columns).
- Skip missing/delisted tickers — don't crash.
- Signals on prior close only. No look-ahead.
- Net of costs: commission + spread/slippage (+ funding for crypto perps).
- Risk-free rate: 4% (2020-2026), 3% (2005-2020), 5% (1999-2005). Capital: $1,000,000.

## Publishing

- Charts → Imgur (Client-ID `546c25a59c58ad7`) → Telegraph.
- Telegraph token: `.telegraph_token`. Paths: `.telegraph_path` (v1) / `.telegraph_path_v2` (v2).
- Publishers: `backtests/publish_report.py` (v1), `backtests/publish_report_v2.py` (v2).

## Secrets

- `.telegraph_token` — do not commit.
- GitHub (dzianisv): `source ~/.env.d/github-dzianisv.env` then `GH_TOKEN="$GH_TOKEN" gh ...`
- Do not scrape/spoof the Morningstar API.

## Integration tracks

- Robinhood agentic trading: https://robinhood.com/us/en/support/articles/agentic-trading-overview/
- Coinbase CDP CLI: https://www.coinbase.com/developer-platform/discover/launches/cdp-cli
- Both blocked on user-supplied API keys. Build connectors in notification mode first.

## Directory structure

```
GOAL.md                  mission + operating prompt
AGENTS.md                this file
crypto/                  crypto book (portfolio.py, STRATEGY.md)
strategy/                v1→v2→v3; v3 current
research/                research library + $1M playbook
backtests/               scripts (run from repo root)
  daytrade/              intraday harnesses
  results/               cached summaries + dead-idea log
.agents/skills/          all skills — single canonical root
evals/                   eval harnesses (evals/pm, evals/hf)
report/img/              chart PNGs
```

## Strategy index

| Script | Strategy | Period | Result |
|---|---|---|---|
| `crash_protection_backtest.py` | All-weather/trend/permanent | 2000-2026 | DD −16% vs S&P −55%; Sharpe 0.65 vs 0.38 |
| `v3_proxy_backtest.py` | v3 Balanced + dip ladder | 2000-2026 | DD −27% vs −55%; lags bulls 6.8% vs 8.3% CAGR |
| `v3_allocate_today.py` | Live v3 buy-list | — | current deploy tool |
| `quality_factor_backtest.py` | Momentum + low-vol | 2020-2026 | 19% CAGR, −16% DD |
| `value_factor_backtest.py` | Value + momentum | 2020-2026 | 26% CAGR, 0.99 Sharpe |
| `momentum_backtest.py` | Dual momentum ETFs | 2020-2026 | 18.8% CAGR |
| `sector_rotation_backtest.py` | Sector ETF rotation | 2020-2026 | 21% CAGR, −17% DD |
| `tech_concentration_backtest.py` | Mag7/AI/Semis/TQQQ+SMA | 2020-2026 | 38-46% CAGR, −50% DD |
| `congressional_backtest.py` | Pelosi/McCaul tracker | 2020-2026 | Pelosi 20%, McCaul 28% |

## Known caveats

1. AI/Semis + Social Momentum universes hindsight-selected — CAGR inflated 5-15%.
2. Quality Factor Sharpe overstated — monthly marking understates vol.
3. PEAD script tests gap-up momentum, not real post-earnings drift.
4. Options strategies use Black-Scholes approximations, not real prices.
5. Sector Rotation fails 1999-2005 — chases tech into the bubble.
6. Transaction costs kill paper-profitable day-trading strategies. Cost model in `strategy-discovery-backtest` is mandatory.
