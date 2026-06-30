# Installing the Investment-PM Skill Stack

How to install the full skill set from `dzianisv/backtest` onto any supported AI agent platform.

Skills: `analyse-smartmoney-13f`, `analyse-smartmoney-ptr`, `trend-stock-research`, `superforecasting`,
`multi-lens-quorum`, `analyse-smartmoney-polymarket`, `forecast-ledger`, `hedge-fund-13f-analysis`,
`macro-panel`, `investor-*`, `research-*`, `regime-detection`, `portfolio-construction`, `risk-management`,
and the rest. See `README.md` for the full index.

> **A SKILL.md on disk is NOT a loaded skill.** Always verify after install (see Verify section).

---

## Install via `npx skills` (all platforms)

The `skills` npm package supports Claude Code, opencode, hermes-agent, openclaw, and 30+ others.

```bash
# Claude Code
npx -y skills add dzianisv/backtest --agent claude-code

# opencode
npx -y skills add dzianisv/backtest --agent opencode

# hermes-agent
npx -y skills add dzianisv/backtest --agent hermes-agent

# openclaw (--copy required to include watch.py / ledger.py scripts)
npx --yes skills add dzianisv/backtest \
  --agent openclaw --yes --copy --dangerously-accept-openclaw-risks
```

**Individual skill install** (add `--skill <name>`):
```bash
npx -y skills add dzianisv/backtest --skill analyse-smartmoney-13f --agent claude-code
npx -y skills add dzianisv/backtest --skill analyse-smartmoney-ptr --agent opencode
npx -y skills add dzianisv/backtest --skill trend-stock-research --agent hermes-agent
```

---

## hermes-agent (alternative: URL install)

```bash
hermes skills install https://raw.githubusercontent.com/dzianisv/backtest/main/.agents/skills/analyse-smartmoney-13f/SKILL.md
hermes skills install https://raw.githubusercontent.com/dzianisv/backtest/main/.agents/skills/analyse-smartmoney-ptr/SKILL.md
hermes skills install https://raw.githubusercontent.com/dzianisv/backtest/main/.agents/skills/trend-stock-research/SKILL.md
hermes skills install https://raw.githubusercontent.com/dzianisv/backtest/main/.agents/skills/hedge-fund-manager/SKILL.md
hermes skills install https://raw.githubusercontent.com/dzianisv/backtest/main/.agents/skills/multi-lens-quorum/SKILL.md
hermes skills install https://raw.githubusercontent.com/dzianisv/backtest/main/.agents/skills/superforecasting/SKILL.md
hermes skills install https://raw.githubusercontent.com/dzianisv/backtest/main/.agents/skills/macro-panel/SKILL.md
hermes skills install https://raw.githubusercontent.com/dzianisv/backtest/main/.agents/skills/regime-detection/SKILL.md
hermes skills install https://raw.githubusercontent.com/dzianisv/backtest/main/.agents/skills/forecast-ledger/SKILL.md
hermes skills install https://raw.githubusercontent.com/dzianisv/backtest/main/.agents/skills/hedge-fund-13f-analysis/SKILL.md

# Verify
hermes skills list

# Launch with skills preloaded
hermes -s analyse-smartmoney-13f,analyse-smartmoney-ptr,trend-stock-research,hedge-fund-manager
```

---

## openclaw (per-agent install into the investor agent)

```sh
# Per-agent install — run on the deployment, HOME = openclaw home:
cd ~/.openclaw/workspace/investor
HOME="${OPENCLAW_HOME_DIR:-$HOME}" npx --yes skills add dzianisv/backtest \
  --agent openclaw --yes --copy --dangerously-accept-openclaw-risks
```

- `--copy` is **required** — it copies the full skill dir including `watch.py`, `ledger.py` scripts.
- Drop `cd …/investor` + add `--global` to install for every agent instead:
  ```sh
  HOME="${OPENCLAW_HOME_DIR:-$HOME}" npx --yes skills add dzianisv/backtest \
    --agent openclaw --yes --copy --dangerously-accept-openclaw-risks --global
  ```
- Private repo? The CLI needs git access (SSH key / `gh auth`) on the deployment.

### Discovery caveat

This repo nests skills under `.agents/skills/`, not the repo root. If `skills add` doesn't discover them,
use the vendored path: copy skill dirs into `OpenClawBot/openclaw-rc.d/skills/<name>/` (committed →
`seed-ops-tools.sh` copies them into `$SKILLS_DIR` on boot, no runtime fetch).

---

## Verify installed skills

**Claude Code:** Skills appear in `~/.claude/skills/`. Check with:
```bash
ls ~/.claude/skills/
```

**opencode:** Check `~/.config/opencode/skills/` or wherever your opencode skills dir is configured.

**hermes-agent:**
```bash
hermes skills list
# Each installed skill shows as a /slash-command
```

**openclaw** (MANDATORY — the only proof that counts):
```sh
cd /app && node openclaw.mjs skills list --agent investor --json
# Each skill must show: "eligible": true  AND  "modelVisible": true
```
`skills add` can exit 0 having installed nothing. "Installation complete" is not proof. Only the load-list is.

---

## Setup prompts (tell the agent to run + schedule)

**openclaw** → paste `openclaw-investor-setup-prompt.md` to your investor agent DM.

**hermes-agent** → paste `hermes-investor-setup-prompt.md` to your hermes session.

These prompts instruct the agent to:
1. Verify all skills loaded
2. Run 13F + Congressional + trending stock research immediately
3. Register recurring cron jobs (daily regime + weekly watchlists)

---

## Scheduling (openclaw native cron — in-pod, no secrets)

The investor agent runs inside the OpenClaw deployment with Telegram already wired. Use the
tenant cron store (`~/.openclaw/cron/jobs.json`) — no GitHub Actions, no external secrets.

The `openclaw-investor-setup-prompt.md` asks the agent to self-register 4 jobs:

| Job | Schedule | What it does |
|-----|----------|--------------|
| A: Daily regime check | Weekdays 08:30 UTC | regime-detection → RISK_ON/OFF + exposure dial |
| B: 13F watch | Monday 09:00 UTC | analyse-smartmoney-13f → new institutional buys (deduped) |
| C: Congressional watch | Monday 09:05 UTC | analyse-smartmoney-ptr → STOCK Act new buys (deduped) |
| D: Trend research | Monday 09:15 UTC | trend-stock-research → 3-5 emerging thesis candidates |

If the agent can't self-register (OpenClaw incident #1787 noted agent-side cron tools as flagged),
the deployment maintainer adds jobs to `jobs.json` directly. Still in-pod, no secrets.

---

## Dedup ledger paths (set before first run)

```bash
export THIRTEENF_LEDGER=~/.openclaw/workspace/investor/13f/recommended.jsonl
export CONGRESS_LEDGER=~/.openclaw/workspace/investor/congress/recommended.jsonl
```

The dedup ledgers make all runs idempotent — re-running never re-proposes a ticker.
