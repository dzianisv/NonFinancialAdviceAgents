# @MichaelBurryTraderBot — investor agent runbook

Live agent behind Telegram bot **@MichaelBurryTraderBot** (bot id `8642078678`).

## Ground truth (verified 2026-08-20)

| Field | Value |
|---|---|
| Owner | user `whoisdzianis` (telegram id `1916982742`), openclawbot user id `1` |
| Agent record | agents id **92**, subdomain `oc-30641f`, ns `tenant-oc-30641f` |
| **Runtime** | **hermes** (NOT openclaw) |
| Host | LXD VM `vmi3445496/oc-30641f`, `169.58.52.49:22000`, private `10.138.0.4` |
| Shell user | `root`, `HOME=/root` |
| Active profile | `investor` |
| **Skills dir** | **`/root/.hermes/profiles/investor/skills/`** |
| Workspace | `/root/.hermes/profiles/investor/workspace` |
| Telegram delivery | long-poll (no webhook) |

> ⚠️ `~/.hermes/skills/` is a DIFFERENT, mostly-empty dir (21 entries). The profile dir is the
> one that counts. Checking the wrong path is what made the agent report "NOT FOUND" for skills
> that were actually installed.

## Installed skills

`105 / 107` skill dirs from `.agents/skills/` are present, byte-identical to the local working copy:

| Skill | sha256 of SKILL.md | Status |
|---|---|---|
| `crypto-advisor` | `cc4f1ca4…91b8e1` | ✅ matches local |
| `stocks-advisor` | `d9788446…f5417` | ✅ matches local |
| `stocks-advisor-fast` | `1f6d5e72…310eb1` | ✅ matches local |

Total in profile: **207 entries**. Dependency closure of the three headline skills (68 skills incl.
`analyse-*`, `investor-*`, `read-news`, `reference-validator`, `skeptic`, `mkt`) is fully present.

Two deliberate exclusions:
- `watchlist-alerts` — has **no SKILL.md** (helper `README.md` + `.ts` only). Copied as plain files.
  `risk-desk` references it in comments only and explicitly does **not** import it (`risk-desk.ts:24`).
- `update-porfolio-positions` — untracked local-only WIP (note the typo in the dir name), never
  committed, so absent from GitHub. Not a dependency of any of the three skills. Commit it if wanted.

## Daily cron

```
id:       0f922569f2d9
name:     crypto-advisor-daily
schedule: 0 8 * * *   (UTC)
repeat:   forever
deliver:  telegram:1916982742
next run: 2026-08-21T08:00:00+00:00
```

Managed by hermes' native scheduler (`hermes cron list`). Do not hand-edit job files.

## Known capability gap

`crypto-advisor` is written for an orchestrator holding **TradingView MCP** tools. This agent has none,
so `analyse-technical` and most on-chain metrics come back `[UNAVAILABLE]` and the panel runs on
CoinGecko / DeFiLlama / Fear&Greed / Google-News RSS instead. Verified in a live 2-token smoke run:
Druckenmiller and Burniske seats correctly self-reported LOW conviction with `[UNAVAILABLE]` rather
than inventing levels. Wire a TradingView MCP in to close it.

## Installing / updating skills on this agent

`hermes skills install` hits the **unauthenticated GitHub API rate limit (60/hr)** and fails. Clone and
copy instead:

```sh
rm -rf /tmp/nfaa && git clone --depth 1 https://github.com/dzianisv/NonFinancialAdviceAgents /tmp/nfaa
cp -r /tmp/nfaa/.agents/skills/<NAME> /root/.hermes/profiles/investor/skills/<NAME>
```

Verify by checksum, never by asking the agent whether a skill is "loaded":

```sh
sha256sum /root/.hermes/profiles/investor/skills/crypto-advisor/SKILL.md
```

## ⚠️ Do not add a second Telegram consumer

The token must have exactly **one** consumer. Binding it to the openclaw tenant (`tenant-oc-6d376f`,
agents id 1443) as well causes two competing `getUpdates` long-polls, so replies come back
nondeterministically from whichever runtime won the race. Symptom: the bot answers as the right
persona but from the wrong filesystem. Keep the binding on hermes only.

## BotFather hazard

`/mybots` → selecting the bot resumed a **pending `/deletebot` flow** and asked for
`"Yes, I am totally sure."`. Send `/cancel` first. Use `/token` to read the token, never `/mybots`.
