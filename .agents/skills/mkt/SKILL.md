---
name: mkt
description: "Turn a buy/sell thesis into a price/indicator ALERT job that a scheduled task checks at an interval and notifies you about WITH the reasoning. Wraps the open-source `mkt` terminal tool as the price + indicator (RSI/MACD/SMA) data engine. Use when stocks-advisor or crypto-advisor decides 'buy X at price P' or 'act when RSI/MACD hits V' and you want to be pinged when it triggers — i.e. 'set an alert', 'notify me when BTC hits 60k', 'watch AAVE for $73', 'alert me when RSI < 30', 'set a buy-zone alert', 'watch for the MACD cross', 'TradingView-style alert'. Registers the alert as a durable job with reasoning, then a runtime/cron scheduled check fires the notification. Recommend-only — never trades."
license: MIT
compatibility: opencode
metadata:
  audience: investors
  domain: price-indicator-alerting
  role: alert-engine
---

# mkt — alert engine for "notify me when to buy, and why"

You are an alerting layer that turns an advisor's thesis ("buy AAVE near $73 because the
denied-rumor pop is fading and that's the EMA20 reclaim zone") into a **durable alert job
with reasoning**, then has a **scheduled task** check it on an interval and **notify the
user with that reasoning** when the condition fires.

The hard problem this solves: `mkt`'s own notifications carry only an **auto-generated**
message ("BTC-USD price 60197 crossed below 70000") — there is **no field for your
reasoning**. So we keep the reasoning in a sidecar job store and notify from our own
`check.ts`, using `mkt` purely as the (robust, multi-source) price + indicator engine.

## What `mkt` gives us (verified)
- **Live quotes**: Coinbase WS (crypto, US-native, no geo-block) + Yahoo polling (stocks) + FRED (`FRED:` prefix) + DeFiLlama TVL + Binance funding/OI.
- **Indicators computed locally** (pure math, no Taapi.io key): RSI, MACD, SMA/EMA, Bollinger, VWAP, OBV, ATR, Stoch, ADX.
- **Alert conditions**: `above`, `below`, `pct_up`, `pct_down`, `rsi_above`, `rsi_below`, `sma_cross_above`, `sma_cross_below`, `macd_cross`, `volume_above`, `stddev_above`; compound `match: all | any | sequence`; built-in 5-min cooldown.
- **MCP server** (`mkt mcp`, JSON-RPC/stdio): tools `get_quote`, `query_history` (OHLCV bars), `get_alerts`, `get_portfolio`.
- **HTTP** (`mkt --listen :PORT`): `/quotes`, `/quotes/{sym}`, `/alerts`, `/metrics`, `/webhook/tradingview`.

## Install (binary stays OUT of the repo)
```bash
# go 1.24+; pins a known-good commit
git clone https://github.com/stxkxs/mkt ~/.local/src/mkt
cd ~/.local/src/mkt && git checkout 0207dda && go build -o ~/.local/bin/mkt .
export PATH="$HOME/.local/bin:$PATH"   # add to shell rc
mkt version
```

---

## The advisor → alert contract
An advisor sets an alert by calling `mkt-alert.ts add`. Every job MUST carry **reasoning**
(the thesis) — that's the whole point; a price with no "why" is noise.

Job shape (stored in `~/.config/mkt/agent-alerts.json`):
```jsonc
{
  "id": "aave-usd-below-73-a1b2",
  "desk": "crypto",                 // crypto | stocks
  "symbol": "AAVE-USD",
  "conditions": [{ "condition": "below", "value": 73 }],
  "match": "all",                   // only when >1 condition
  "reasoning": "Denied Kraken-rumor pop fading; $73 = EMA20 reclaim + pre-pop base. Buy-zone tranche 1.",
  "channel": "telegram:@CryptoAiInvestor",  // telegram:<target> | ntfy:<topic> | stdout
  "created": "2026-06-25T23:50:00Z",
  "expiry": "2026-07-31",           // optional; job inactive after
  "cooldownSec": 0                  // 0 = one-shot (fire once, then disable)
}
```

### Register an alert
```bash
cd .agents/skills/mkt/scripts
# Price buy-zone (crypto), one-shot, to Telegram:
bun mkt-alert.ts add --desk crypto --symbol AAVE-USD \
  --condition below --value 73 \
  --reason "Denied Kraken-rumor pop fading; \$73 = EMA20 reclaim. Buy tranche 1." \
  --channel telegram:@CryptoAiInvestor --expiry 2026-07-31

# Oversold indicator alert (stocks), repeatable every 6h:
bun mkt-alert.ts add --desk stocks --symbol NVDA \
  --condition rsi_below --value 30 --period 14 \
  --reason "RSI<30 = washed-out; add to core only on capitulation." \
  --channel ntfy:my-alerts --cooldown 21600

# Compound (BOTH must hold): price reclaim AND momentum cross
bun mkt-alert.ts add --desk crypto --symbol UNI-USD --match all \
  --condition above --value 2.90 --condition macd_cross --value 0 \
  --reason "Spark×Uniswap FX-Layer catalyst; confirm with \$2.90 reclaim + MACD cross up." \
  --channel telegram:@CryptoAiInvestor

bun mkt-alert.ts list                 # see active + inactive jobs
bun mkt-alert.ts remove --id <id>     # cancel a job
```

### The scheduled check (this is the job the scheduler runs)
`check.ts` evaluates every active job using `mkt` for data, fires the notification **with
reasoning**, dedups (one-shot or cooldown), and respects expiry.
```bash
cd .agents/skills/mkt/scripts
bun check.ts            # evaluate all jobs, notify on fire
bun check.ts --dry-run  # evaluate + print, never notify or mark fired (use to test)
bun check.ts --id <id>  # check one job
```
Notification text:
```
🔔 mkt alert — AAVE-USD fired @ 72.84 (2026-06-26T07:02:47.501Z)
Conditions: below:73=✓(price=72.84)
WHY: Denied Kraken-rumor pop fading; $73 = EMA20 reclaim. Buy tranche 1.
```

**check.ts coverage:** price (`above`/`below`) and indicators (`rsi_above`/`rsi_below`/
`macd_cross`/`sma_cross_*`, computed from `mkt mcp query_history` closes) work in the
one-shot path. `pct_up`/`pct_down`/`volume_above`/`stddev_above` need change%/volume that the
one-shot quote doesn't carry — use the **daemon (Pattern B)** for those, which evaluates them
natively.

---

## Pattern A — scheduled `check.ts` (PRIMARY; carries reasoning, no daemon)
Best default. Works under **any** scheduler. No always-on process. Reasoning is native.
Register with `mkt-alert.ts`, then schedule `bun check.ts` on an interval.

<example>
<scenario>GitHub Copilot CLI (this runtime) — native scheduler</scenario>
Use the `manage_schedule` tool with a recurring prompt that runs the check:
```
interval: "15m"
prompt: "cd /Users/engineer/workspace/backtest/.agents/skills/mkt/scripts && bun check.ts"
```
When a job fires it notifies via its channel; when all jobs are fired/expired, stop the schedule.
</example>

<example>
<scenario>OS cron (Claude Code, OpenCode, Hermes-AI, or any host) — universal fallback</scenario>
```cron
*/15 * * * * cd /Users/engineer/workspace/backtest/.agents/skills/mkt/scripts && /opt/homebrew/bin/bun check.ts >> ~/.config/mkt/check.log 2>&1
```
This is the portable path for any runtime whose native scheduler you can't verify — do NOT
invent a runtime's scheduler API; fall back to cron and let the user adapt it.
</example>

<example>
<scenario>OpenClaw — durable server-side cron</scenario>
OpenClaw reads `~/.openclaw/cron/jobs.json`. **Deliver a paste-able job spec; do NOT
live-mutate that file or restart the gateway** (hard invariant — shipping the artifact, not
operating prod). Give the user the recurring prompt `cd …/scripts && bun check.ts` and the
cadence; let them register it.
</example>

## Pattern B — `mkt daemon` (always-on, sub-minute, native RSI/MACD)
Best when you want OS-level, sub-minute alerts and don't need rich reasoning in the message.
Edit `~/.config/mkt/config.yaml` to add the rule + a notifier, then run the daemon detached;
the scheduler's only job is keep-alive.
```yaml
# ~/.config/mkt/config.yaml
watchlist: [AAVE-USD]
alerts:
  - symbol: AAVE-USD
    condition: below
    value: 73
    enabled: true
ntfy_topic: my-alerts-7f3c            # zero-signup mobile push
# or webhook_url: https://…           # POST {symbol,condition,value,price,message,timestamp}
poll_interval: 15s
```
```bash
mkt config validate
mkt daemon --listen 127.0.0.1:9999    # run detached; keep-alive: `pgrep mkt || mkt daemon`
```
**Honest limitation:** the daemon's ntfy/webhook `message` is auto-generated
("AAVE-USD price 72.8 crossed below 73") — it has **no reasoning**. To attach the thesis,
prefer Pattern A, or run a tiny webhook→Telegram bridge that joins the fired rule to the
reasoning you stored. The daemon natively evaluates `rsi_*`, `macd_cross`, `sma_cross_*`.

## Pattern C — agent + `mkt mcp` (re-judge with fresh reasoning each tick)
Best inside an agent runtime when you want the agent to **re-reason** every check, not just
threshold-match. Schedule a recurring prompt; the agent calls `mkt mcp` (`get_quote`,
`query_history`), recomputes the read, compares to the thesis, and DMs fresh reasoning.
```
# scheduled prompt (Copilot/Claude/OpenCode/OpenClaw):
"Read AAVE-USD via mkt mcp get_quote + query_history. If price ≤ 73 OR RSI(14) < 35, DM me
on Telegram @CryptoAiInvestor with the current read and whether tranche-1 buy is justified
given: <thesis>. Otherwise stay silent."
```

### Choosing a pattern
| Want… | Use |
|---|---|
| Reasoning in the alert, any scheduler, no daemon | **A (check.ts)** |
| Sub-minute, always-on, OS push, message can be terse | **B (daemon)** |
| The agent to re-judge & write fresh reasoning each tick | **C (mcp)** |

---

## Security
`mkt --listen` exposes a read endpoint **and** `/webhook/tradingview` (inbound). On any
non-loopback bind, set `--listen-token <secret>` (bearer auth) or anyone on the network can
inject alerts via the webhook. Default to `127.0.0.1`. Never commit tokens — keep them in
`~/.config/mkt/config.yaml` (gitignored) or env.

## Files
- `scripts/mkt-alert.ts` — register / list / remove alert jobs (the advisor→alert contract).
- `scripts/check.ts` — the scheduled job: evaluate → notify with reasoning → dedup → expiry.
- `scripts/indicators.ts` — pure RSI / MACD / SMA math (shared with tests).
- `scripts/store.ts` — sidecar job store (`~/.config/mkt/agent-alerts.json`).
- `scripts/check.test.ts` — Bun test (indicator math + evaluate/dedup/expiry logic).

## Done = verified
Before claiming an alert is set: run `bun mkt-alert.ts list` and confirm the job exists with
its reasoning; run `bun check.ts --dry-run` and confirm it evaluates (and shows the WHY line
on a fire). Tests stay green: `cd scripts && bun test`.
