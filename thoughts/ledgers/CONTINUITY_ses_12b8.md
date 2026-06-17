---
session: ses_12b8
updated: 2026-06-17T21:59:13.675Z
---

# Session Summary

## Goal
Build or find a universal workflow CLI runner that executes `.agents/workflows/*.workflow.js` files from any agent backend (OpenClaw, Hermes, OpenCode) — not tied to OpenCode's plugin system.

## Constraints & Preferences
- Solution must work across OpenClaw, Hermes, and OpenCode agents
- User frustrated with over-engineering — wants practical, working solution fast
- No permanent changes to global OpenCode config (`/Users/engineer/.config/opencode/opencode.json`)
- Caveman communication style preferred

## Progress
### Done
- [x] Deleted `scripts/opencode-workflow-runner.mjs` and `tests/opencode-workflow-runner.test.mjs` (superseded by Drawers plugin)
- [x] Rewrote README `### OpenCode workflow execution` section with Drawers `script_path` + `args` schema
- [x] Created `.agents/knowledgebase/project-overview.md`
- [x] Closed GitHub issues #41 (superseded) and #42 (duplicate)
- [x] Smoke-tested via temporary wrapper: `opencode run` → `workflow` tool launched `wf_kvpflmoh` (pairwise-eval), completed 6.6s
- [x] Identified root cause: `opencode-drawer-workflows@1.6.0` missing default export — temp `export default WorkflowsPlugin` wrapper fixed it
- [x] Restored global config and deleted temp wrapper

### In Progress
- [ ] Research/design universal workflow CLI runner (user's latest question, unanswered)

### Blocked
- `opencode-drawer-workflows@1.6.0` ships only named export `WorkflowsPlugin`; OpenCode plugin loader expects default export → plugin silently fails without wrapper
- No answer yet on whether a standalone CLI exists or needs building

## Key Decisions
- **Delete custom runner instead of maintaining both**: Drawers plugin provides same capability with less maintenance
- **Pivot goal to universal CLI**: User wants cross-agent solution, not OpenCode-only plugin fix
- **User quote**: "took too much effort and solution wasn't built. is there an universal workflow cli runner that will allow to run a workflow from any agent, including openclaw, hermes, opencode?"

## Next Steps
1. Read `opencode-drawer-workflows/dist/lib.js` to determine if workflow engine is usable standalone (separate from plugin wrapper)
2. Determine what globals workflow scripts expect (`agent()`, `pipeline()`, `parallel()`, `phase()`, `log()`, `args`, `budget`, `workflow()`)
3. Assess feasibility of thin CLI wrapper around the engine that any agent can invoke via shell
4. Build or recommend solution

## Critical Context
- Workflow files at `.agents/workflows/*.workflow.js` use DSL globals: `agent()`, `pipeline()`, `parallel()`, `phase()`, `log()`, `args`, `budget`, `workflow()`
- Package structure: `dist/index.js` = OpenCode plugin interface; `dist/lib.js` = workflow engine runtime
- Working wrapper pattern: `import { WorkflowsPlugin } from "file:///...dist/index.js"; export default WorkflowsPlugin;`
- Smoke `wf_kvpflmoh` completed but child judge step had `status_error` (session `ses_1286d4bcaffeD6cyal50A5z4KG`) — tool registration works, business logic didn't execute cleanly
- Global config line 17: `"opencode-drawer-workflows"` — currently broken without wrapper
- Agent backends in user's ecosystem: OpenClaw (VMs), Hermes (gateway), OpenCode (CLI/TUI)
- Installed plugin path: `/Users/engineer/.config/opencode/node_modules/opencode-drawer-workflows/`

## File Operations
### Read
- `/Users/engineer/.config/opencode/.opencode/package.json`
- `/Users/engineer/.config/opencode/dcp.jsonc`
- `/Users/engineer/.config/opencode/node_modules/@opencode-ai/plugin/dist/example.js`
- `/Users/engineer/.config/opencode/node_modules/@opencode-ai/plugin/package.json`
- `/Users/engineer/.config/opencode/node_modules/opencode-drawer-workflows/README.md`
- `/Users/engineer/.config/opencode/node_modules/opencode-drawer-workflows/dist/index.js`
- `/Users/engineer/.config/opencode/node_modules/opencode-drawer-workflows/dist/lib.js`
- `/Users/engineer/.config/opencode/node_modules/opencode-drawer-workflows/package.json`
- `/Users/engineer/.config/opencode/node_modules/opencode-scheduler/dist/index.js`
- `/Users/engineer/.config/opencode/node_modules/opencode-supermemory/dist/index.js`
- `/Users/engineer/.config/opencode/node_modules/opencode-supermemory/package.json`
- `/Users/engineer/.config/opencode/opencode.json`
- `/Users/engineer/.config/opencode/package.json`
- `/Users/engineer/workspace/backtest/.agents/knowledgebase/project-overview.md`
- `/Users/engineer/workspace/backtest/.agents/workflows/hedge-fund-committee.workflow.js`
- `/Users/engineer/workspace/backtest/.agents/workflows/pairwise-eval.workflow.js`
- `/Users/engineer/workspace/backtest/.agents/workflows/research-market.workflow.js`
- `/Users/engineer/workspace/backtest/.agents/workflows/research-trend-stocks.workflow.js`
- `/Users/engineer/workspace/backtest/.gitignore`
- `/Users/engineer/workspace/backtest/GOAL.md`
- `/Users/engineer/workspace/backtest/README.md`
- `/Users/engineer/workspace/backtest/scripts/opencode-workflow-runner.mjs`
- `/Users/engineer/workspace/backtest/strategy/README.md`
- `/Users/engineer/workspace/backtest/tests/opencode-workflow-runner.test.mjs`

### Modified
- `README.md` — rewrote workflow execution section (uncommitted)
- `.agents/knowledgebase/project-overview.md` — created (untracked)
- `scripts/opencode-workflow-runner.mjs` — deleted (uncommitted)
- `tests/opencode-workflow-runner.test.mjs` — deleted (uncommitted)
