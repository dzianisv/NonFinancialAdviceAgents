# Proactive Advisor on OpenClaw

Native primitive: **agent cron** (primary) + **heartbeat** (light backup). Verified live 2026-06-14:
the investor agent has native cron and already runs the daily/weekly loop. No external scheduler, no secrets.

## 1. Install skills (into the agent's runtime skills dir)

The agent runs bash in a sandbox at `HOME=/home/node`; its skills live at
`/home/node/.openclaw/workspace/investor/skills/`. (This is NOT the `kubectl exec` container — that one
has no python. The agent sandbox HAS python3.12 + yfinance + Yahoo access.) Have the agent pull each skill
from the repo:

```sh
B=https://raw.githubusercontent.com/dzianisv/backtest/main/.agents/skills
S=~/.openclaw/workspace/investor/skills
for k in dip-screener crypto-dip-scanner signal-convergence-alert; do
  mkdir -p $S/$k
  curl -sL -o $S/$k/SKILL.md $B/$k/SKILL.md
done
curl -sL -o $S/dip-screener/dip_screener.py            $B/dip-screener/dip_screener.py
curl -sL -o $S/crypto-dip-scanner/crypto_dip_scanner.py $B/crypto-dip-scanner/crypto_dip_scanner.py
curl -sL -o $S/signal-convergence-alert/convergence.py  $B/signal-convergence-alert/convergence.py
```
(`npx skills add dzianisv/backtest --agent openclaw --copy` also works if discovery handles the nested
`.agents/skills/` layout; the curl path is deterministic.)

## 2. Verify the skill actually runs (the only proof that counts)

Trigger the live agent, don't infer from `kubectl exec`:
```
python3 ~/.openclaw/workspace/investor/skills/crypto-dip-scanner/crypto_dip_scanner.py --json
```
Expect real JSON with `high_52w_usd` + `pct_from_high` fields + a Fear&Greed value. If it fabricates a
number or errors → fix before scheduling.

## 3. Schedule via AGENT CRON (primary)

The agent already runs ~13 cron jobs (regime `0 8 * * 1-5`, journalism `15 8 * * 1-5`, weekly 13F/congress
`0/5 9 * * 1`, weekly brief `30 9 * * 1`). Add the 3 proactive dip jobs — **SILENT unless the gate fires**:

| Name | Schedule (UTC) | Prompt |
|------|----------------|--------|
| Daily stock dip scan | `45 7 * * 1-5` | Run `dip_screener.py --json` + regime-detection. DM ONLY if a HIGH dip (`pct_from_high<=-30`) AND regime=RISK_ON. Else `NO_REPLY`. |
| Daily crypto dip scan | `50 7 * * *` | Run `crypto_dip_scanner.py --json`. DM ONLY if any coin `pct_from_high<=-30` AND `fear_greed.value<25`. Else `NO_REPLY`. |
| Daily signal convergence | `30 8 * * 1-5` | Run `convergence.py --json --min-sources 2`. DM ONLY if any ticker `n_sources>=2`. Else `NO_REPLY`. |

Ask the agent to register them with its cron tool (it returns a UUID per job). Verify: ask it to list cron jobs.

## 4. heartbeat = light backup only

`agents.defaults.heartbeat { every:15m, lightContext, target:last }` stays for a lightweight "did regime/Fed
change" nudge. Do NOT put the full scans in a `HEARTBEAT.md` — cron owns the schedule; a scan-running
HEARTBEAT.md double-fires what cron already does (we removed ours).

## 5. Feedback loop — forecast-ledger (reuse, don't rebuild)

The weekly-brief cron prompt should `forecast-ledger add` each DM'd buy idea (ticker, action, ref price,
resolution date), and a weekly/quarterly job should `forecast-ledger score`/`report` for 30/60/90d hit-rate
by source. See `.agents/skills/forecast-ledger`.

## Done when
- [ ] 3 skills present + runnable in the agent sandbox (real `--json` output, no fabrication).
- [ ] 3 dip cron jobs registered (UUIDs) alongside the existing loop; each SILENT-unless-alert.
- [ ] No scan-running HEARTBEAT.md (cron owns the schedule).
- [ ] Weekly brief logs calls to forecast-ledger.
