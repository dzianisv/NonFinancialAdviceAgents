# Proactive Advisor on Claude Code

Native primitives — NO OS crontab (it's stateless and has no notify channel back to you):

| Primitive | Role here |
|---|---|
| **`/loop`** + `CronCreate`/`CronList`/`CronDelete` | recurring daily scans, **in-session** (agent stays alive → can notify via its own tools) |
| **`/goal`** | drive one run to a completion condition ("…until the INVESTMENT BRIEF is produced and sent") |
| **dynamic workflows** | the hedge-fund committee — analyst fan-out → aggregate → panel → risk → CIO memo (`.agents/workflows/hedge-fund-committee.workflow.js`) |
| **Routines** (cloud) or **Desktop scheduled tasks** | durable unattended cadence — runs with the machine/ session closed |
| **mobile push** + messaging connector (Telegram MCP) | the notify path — ping + full brief text |

Why not `cron → claude -p`: headless `claude -p` is one-shot and writes to stdout. To reach your
phone you'd bolt on an external sender. The native loop keeps a live agent that notifies itself.

## 1. Install skills

```bash
npx -y skills add dzianisv/backtest --agent claude-code
ls ~/.claude/skills/   # dip-screener, crypto-dip-scanner, signal-convergence-alert, regime-detection, ...
```

## 2. Durable cadence — Routines (recommended) or Desktop tasks

For runs that fire when your machine/session is closed, use **Routines** (Anthropic cloud, min interval
1h — fine, our slots are daily) or **Desktop scheduled tasks** (local, min 1m, has local files + venv).
One task per cadence slot; each runs the skill/workflow and notifies via its connector.

Example routine prompts (set schedule via `/schedule` in the CLI, or the Desktop task UI):
```
# daily 07:45 local, weekdays
/dip-screener — scan S&P100, check regime first. If a HIGH dip (>=-30%) in RISK_ON, push me the
alert + route to /multi-lens-quorum. Else stay silent.

# daily 07:50
/crypto-dip-scanner — alert only if a coin >=-30% from ATH AND Fear&Greed<25. Push me, else silent.

# Mon 09:30 — the weekly brief (runs the workflow)
Run /weekly-brief and send me the INVESTMENT BRIEF.
```
Routines run autonomously (no permission prompts). Wire a messaging connector so the push carries the
brief text; otherwise the mobile push pings you to open the result.

## 3. Interactive / always-on machine — `/loop` + `/goal`

When you keep a session open (or a dedicated always-on terminal), schedule in-session:

```text
/loop 0 7-9 * * 1-5  run the due daily advisor slot (dip → crypto → regime → journalism → convergence)
                     per .claude/loop.md; push me only real alerts
```
Or let Claude self-pace: `/loop run the daily advisor scan and push me only HIGH-conviction alerts`
(Claude picks the interval each iteration, shorter when markets active). Manage with `CronList` /
`CronDelete`. Note: session-scoped, **7-day expiry**, restored on `--resume`. For permanence use §2.

Put the daily playbook in `.claude/loop.md` (same time-gated logic as the openclaw `HEARTBEAT.md`):
the bare `/loop` then runs it each iteration.

Drive the weekly brief to a verified end-state with `/goal`:
```text
/goal the weekly INVESTMENT BRIEF has been produced via /weekly-brief (regime+fed+13F+congress+
narrative cross-referenced, quorum on top 5, risk veto applied) AND pushed to me — or stop after 25 turns
```
`/goal` re-runs turns until a fast model confirms the brief is built + sent. Pair with auto mode so each
turn runs unattended.

## 4. The committee = a dynamic workflow

The heavy synthesis is `.agents/workflows/hedge-fund-committee.workflow.js` (5 phases: analyst fan-out →
aggregate → investor panel votes independently → risk veto → CIO memo). Run via the Workflow tool
(`{scriptPath}`) or save as `/hedge-fund-committee` (`/workflows` → `s`). Deep-dive one ticker with
`args:{ticker:"GOOGL"}`. Returns the decision memo (with mandatory dissent log); the `/loop` or routine
pushes it to you. (Supersedes the old 3-phase `weekly-brief.workflow.js`.)

## 5. Notification

In-session/routine agent is ALIVE, so it notifies with its own tools — no external sender:
- **mobile push** — pings your phone when an alert fires / the brief is ready.
- **messaging connector** (Telegram MCP, etc.) — delivers the full brief text.
Configure the connector once; reference it in the loop/routine prompt ("push me", "send me").

## Done when
- [ ] `~/.claude/skills/` has all skills; `/weekly-brief` workflow saved.
- [ ] Durable cadence set (Routine or Desktop task per slot) OR an always-on `/loop` with `.claude/loop.md`.
- [ ] A test alert reaches your phone (push + connector), not just stdout.
- [ ] `/goal` drives the weekly brief to "produced + sent" without per-turn prompting.
