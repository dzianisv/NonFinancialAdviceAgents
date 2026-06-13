# Installing the forecasting + 13F skills into an OpenClaw deployment

How to load the `superforecasting` / 13F watcher skill stack onto the **`investor`** agent in an OpenClaw
deployment (e.g. `@OpenClawBoxBot`, Telegram user `whoisdzianis`), and run the 13F watcher on a real
schedule. Skills live in this repo (`dzianisv/backtest`) under `.agents/skills/<name>/`.

> **A SKILL.md on disk is NOT a loaded skill.** Installation is not done until the runtime proves the
> agent can see it (verify step below). This mirrors `OpenClawBot/AGENTS.md`.

## The skill set

| Skill | Role |
|---|---|
| `superforecasting` | Dated market-outcome forecast → calibrated probability + triggers (asset-agnostic) |
| `multi-lens-quorum` | Convene N independent lenses → verdict (the forecast/quorum engine) |
| `prediction-market-odds` | Crowd odds for discrete dated events (Polymarket/Kalshi/FedWatch) |
| `analyst-derivatives-positioning` | Futures+options positioning, options-implied distribution (crypto+equities) |
| `forecast-ledger` | Brier/calibration scoring loop (`ledger.py`) |
| `13f-watch` | Watch recent 13F filings → propose NEW buys, dedup so none repeats (`watch.py`) |
| `hedge-fund-13f-analysis` | The filing-reading sub-skill `13f-watch` depends on |
| `analyst-crypto`, `analyst-technical-analysis`, `macro-panel`, `analytics-*` | Lens seats the quorum convenes |

These cross-reference each other (`REQUIRED SUB-SKILL:` markers), so install them together.

## Install via the `npx skills` CLI

The OpenClaw skill installer is the `skills` CLI. The exact invocation OpenClaw's bootstrap uses
(`OpenClawBot/bootstrap/seed-ops-tools.sh`):

```sh
# Per-agent install (into the investor agent's workspace) — run on the deployment, HOME = openclaw home:
cd ~/.openclaw/workspace/investor
HOME="${OPENCLAW_HOME_DIR:-$HOME}" npx --yes skills add dzianisv/backtest \
  --skill superforecasting \
  --agent openclaw --yes --copy --dangerously-accept-openclaw-risks
```

Repeat `--skill <name>` for each skill above, **or** install the whole repo's skill set at once by
omitting `--skill` (installs every SKILL.md the CLI discovers in the repo):

```sh
cd ~/.openclaw/workspace/investor
HOME="${OPENCLAW_HOME_DIR:-$HOME}" npx --yes skills add dzianisv/backtest \
  --agent openclaw --yes --copy --dangerously-accept-openclaw-risks
```

- `--copy` copies the skill dir **including its scripts** (`ledger.py`, `watch.py`) — required.
- Drop `cd …/investor` and add `--global` to install for **every** agent (into `~/.openclaw/skills`)
  instead of just the investor.
- Private repo? The CLI needs git access (SSH key / `gh auth`) on the deployment.

### Discovery caveat (verify, don't assume)

This repo nests skills under `.agents/skills/`, not the repo root. If `skills add` doesn't discover them
there, use the **vendored path** OpenClaw already supports: copy the skill dirs into
`OpenClawBot/openclaw-rc.d/skills/<name>/` (committed → `seed-ops-tools.sh` copies them into
`$SKILLS_DIR` on boot, no runtime fetch). Either way, the install is only real after the proof below.

## Verify (MANDATORY — the only proof that counts)

Inside the gateway pod, for the investor agent:

```sh
cd /app && node openclaw.mjs skills list --agent investor --json
# each installed skill must show  "eligible": true  AND  "modelVisible": true
```

`skills add` can exit 0 having installed nothing; "Installation complete" is **not** proof. Only the
load-list is.

## Scheduling the 13F watcher (native, zero secrets)

The investor agent **already lives inside the deployment** and already has Telegram wired (it is the bot).
So the watcher is scheduled with OpenClaw's **own per-tenant cron** — not GitHub Actions, not the
Claude-harness cron, neither of which belongs here. A GitHub Actions job would have to leave the pod and
re-authenticate back into the very gateway the agent already runs in (CANARY token, Telegram secrets) —
pointless. The native cron fires the agent **in place**, and it DMs you over its existing Telegram
connection. No external secrets at all.

OpenClaw's tenant cron store is `/home/node/.openclaw/cron/jobs.json` (the openclaw runtime scheduler,
seeded/merged by the provisioner). A job there runs the investor agent's `13f-watch` prompt on a schedule.
For 13F (quarterly deadlines ~Feb 14 / May 15 / Aug 14 / Nov 14) a **weekly** job is right — the
`watch.py` dedup ledger makes re-runs idempotent (already-proposed names are skipped). **Recommend-only:
scheduled runs cannot answer permission cards, so the agent only proposes; you act.**

**Set it up by pasting `openclaw-investor-setup-prompt.md` to the investor agent** — its STEP 3 asks the
agent to register the weekly native cron job itself. If the agent reports it cannot self-schedule (note:
agent-side cron *tools* were flagged in OpenClawBot incident #1787 — that is the in-conversation tool, not
necessarily the tenant `jobs.json` store), the deployment maintainer adds the job to the tenant cron store
directly. Either way: in-pod, no secrets.

## Paste-prompt for the investor agent

See `openclaw-investor-setup-prompt.md` (next to this file) — paste it to the investor agent to install the
skills and stand up the 13F watch loop.
