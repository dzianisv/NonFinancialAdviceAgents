# Project Knowledgebase

## Mission

- This repository is an educational, human-in-the-loop financial advisor and backtesting system.
- It proposes research, alerts, staged orders, and portfolio actions; the human approves execution.
- It must not operate or mutate production systems directly. Ship installable artifacts and prompts instead.
- Backtest-before-trade is the hard gate: no trading idea reaches an order without a cost-aware backtest.

## Start Here

- `GOAL.md` - mission, operating constraints, tradfi and crypto book definitions.
- `strategy/README.md` - strategy evolution; v3 is current.
- `AGENTS.md` - repo conventions, routing, invariants, and file-placement rules.
- `README.md` - install, workflow, runtime, and repository overview.

## Architecture

- `.agents/skills/` contains portable skill modules and helper scripts.
- `.agents/workflows/` contains portable workflow files such as `hedge-fund-committee.workflow.js`, `research-market.workflow.js`, and `pairwise-eval.workflow.js`.
- In OpenCode, run `.agents/workflows/*.workflow.js` through the `opencode-drawer-workflows` plugin using the workflow tool.
- In Claude Code, dynamic workflows run through native Workflow tooling and slash-command workflow entries under `.claude/workflows/`.

## Guardrails

- Keep tradfi and crypto books separate; never conflate accounting, risk, or ledgers.
- Educational analysis only; do not present outputs as personalized financial advice.
- Do not commit secrets, tokens, account access, or private production config.
- Generated charts and PNGs belong in `report/img/`.
- Backtests must be net of realistic costs, including spread, slippage, commissions, and funding where relevant.
