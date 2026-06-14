# Proactive Advisor on OpenClaw

Native primitive: **heartbeat**. Every `heartbeat.every` (15m), agent reads its workspace `HEARTBEAT.md`
and acts. No external cron, no secrets. This is the proactive engine.

## 1. Install skills (into the investor agent)

```sh
cd ~/.openclaw/workspace/investor
HOME="${OPENCLAW_HOME_DIR:-$HOME}" npx --yes skills add dzianisv/backtest \
  --agent openclaw --yes --copy --dangerously-accept-openclaw-risks
```
`--copy` is REQUIRED (pulls `dip_screener.py`, `crypto_dip_scanner.py`, `regime_monitor.py`, `watch.py`).

If repo nesting (`.agents/skills/`) breaks discovery, copy dirs into the deployment skills path directly
(`kubectl cp .agents/skills/<name> <pod>:/app/shared/skills/investor/<name>`).

## 2. Verify load (the ONLY proof that counts)

```sh
cd /app && node openclaw.mjs skills list --agent investor --json
```
Each of `dip-screener`, `crypto-dip-scanner`, `regime-detection`, `fomc-monitor`,
`trend-stock-research`, `13f-watch`, `congressman-stock-watch`, `multi-lens-quorum`,
`risk-management`, `signal-convergence-alert` must show `eligible:true` AND `modelVisible:true`.
A SKILL.md on disk is NOT a loaded skill.

## 3. Drop the mandate + playbook into the workspace

```sh
cp .agents/setup/AGENTS.template.md    ~/.openclaw/workspace/investor/AGENTS.md
cp .agents/setup/HEARTBEAT.template.md ~/.openclaw/workspace/investor/HEARTBEAT.md
```
`AGENTS.md` = standing mandate (boot). `HEARTBEAT.md` = the 15-min time-gated playbook (every tick).

## 4. Confirm heartbeat config

In `openclaw-rc.d/openclaw.json` → `agents.defaults.heartbeat` (already present):
```json
{ "every": "15m", "target": "last", "lightContext": true, "skipWhenBusy": true,
  "model": "litellm/gpt-5-mini" }
```
- `every:15m` → fires often enough to hit every 15-min schedule slot.
- `lightContext:true` → loads only HEARTBEAT.md (cheap). Keep it.
- `target:"last"` → DMs the owner's last channel. For a fixed DM target set `to:"<telegram-id>"`.
- `model: gpt-5-mini` → cheap for the every-tick clock-check; the brief itself can escalate.

Per-agent override (if investor needs its own cadence) — add `heartbeat` under the investor entry in
`agents.list`. Default inherited config is fine.

## 5. Why heartbeat, not agent cron

OpenClaw agent-side cron tools were flagged (incident #1787). Heartbeat + a time-gated `HEARTBEAT.md`
is the reliable in-pod proactive path: deterministic clock-check each tick, state file prevents
double-fire. No external scheduler, survives pod restart (files are in the persistent workspace).

## 6. Smoke test

```sh
# Force a tick by messaging the agent:
python3 ~/.claude/skills/telegram-cli-tool/telegram-cli.py ask @MichaelBurryTraderBot \
  "Run your 07:45 HEARTBEAT task now: dip-screener + regime. DM me any HIGH dip in RISK_ON." --wait 120
```
Expect: a dip list (or "no HIGH dips") + regime verdict, using live yfinance data. If it fabricates a
number or skips the regime gate → fix the skill, re-verify load.

## Done when
- [ ] 10 skills `eligible:true && modelVisible:true` for agent `investor`.
- [ ] `AGENTS.md` + `HEARTBEAT.md` in `~/.openclaw/workspace/investor/`.
- [ ] Heartbeat fires, runs the due slot, DMs only on a real alert, silent otherwise.
- [ ] State file `.heartbeat-state.json` written (no double-fire same day).
