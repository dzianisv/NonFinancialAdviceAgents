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

## Weekly cron

```
id:       0f922569f2d9
name:     crypto-advisor-weekly
schedule: 0 8 * * 1   (Monday 08:00 UTC)
repeat:   forever
deliver:  telegram:1916982742
skill:    crypto-advisor
workdir:  /root/.hermes/profiles/investor/workspace
model:    gpt-5.4
provider: custom:litellm
```

Managed by hermes' native scheduler (`hermes cron list`). Do not hand-edit job files.

## Report quality gates

The installed `crypto-advisor` skill fails closed:

- Citation validation must contain only `VERIFIED` or `PARTIAL`; skipped validation, `NOT_FOUND`, and
  `FETCH_FAILED` trigger a bounded repair loop.
- Every non-HOLD token requires at least one accepted citation.
- The skeptic must return `PASS` with zero challenges.
- A remaining failure delivers only `QUALITY GATE FAILED — report not delivered`; it does not send the
  draft report or publish it.

The canonical `report.md` artifact is created only after both gates pass.

## Why `crypto-daily` does not run on Hermes

`crypto-daily` is a local publication wrapper. It expects TradingView MCP, Notion MCP, a logged-in
Chrome/X session, and a personal `telegram-cli` session. The Hermes investor profile does not expose
those tools. Schedule `crypto-advisor` instead and let Hermes cron deliver the final report to
Telegram. The report degrades unavailable TradingView/on-chain inputs to `[UNAVAILABLE]` rather than
inventing data.

Attach the skill explicitly with `--skill crypto-advisor`; prompt-only discovery leaves cron
preflight unable to validate the dependency.

## Manual trigger

On Hermes v0.20.4, `/cron` is not registered as a Telegram slash command. Use:

```sh
hermes -p investor cron run 0f922569f2d9 --accept-hooks
```

This command is synchronous. When invoked through the agent's terminal tool, run it with
`background=true` and no timeout. A foreground terminal call is killed after 120 seconds and leaves
the execution ledger in `unknown`. Confirm success with:

```sh
hermes -p investor cron runs 0f922569f2d9 --limit 5
hermes -p investor cron list
```

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

Quality-gate version verified 2026-08-21:

```
SKILL.md  aa80c907a069d88965e0f1f128d91ba737b070096a8811b93bfb5bd7e2f601e0
README.md 579eee62bd54e168ee00f4d406d03e847c3fd061c036faa22acff072a51d1fb2
```

## Latest end-to-end validation

Execution `435c011414384b24864eb8447f4b342d` completed and delivered on 2026-08-21:

- 11/11 token sections present.
- 11/11 verdict critics present.
- Citation gate: 13 VERIFIED, 4 PARTIAL, 0 NOT_FOUND, 0 FETCH_FAILED.
- Skeptic gate: PASS, 0 challenges.
- Telegram delivery contained the complete report and the quality-gate PASS summary.

## Weekly stocks plan review

```
id:       c6be6f07a468
name:     stocks-advisor-weekly
schedule: 0 3 * * 2   (Monday 20:00 Pacific during daylight time)
repeat:   forever
deliver:  telegram:1916982742
skills:   stocks-advisor, tradfi-portfolio-manager, stock-chair
workdir:  /root/.hermes/profiles/investor/workspace
model:    gpt-5.4
provider: custom:litellm
```

Each run resolves spreadsheet `1aunLbpNGo85WqrMHiIsy6nFUija4Lnjot-rIhE-pGU8`, sheet id
`881284498`, through `gws` at runtime. The tab title and contribution rows are never cached or
hardcoded. The parser treats the tab as a recurring-contribution plan, not a quantity/cost-basis
ledger.

The stocks cron fails closed unless:

- every detected instrument row is accounted for exactly once;
- the individual-stock panel writes separate seat, skeptic, CIO, risk, and verdict JSON artifacts;
- `tradfi-portfolio-manager` produces its literal weekly-note tags and covers every ETF sleeve;
- crypto rows are explicitly excluded from the equity analysis;
- degraded technical mode contains no BUY;
- `quality_gate.json` and `report.md` both exist.

Execution `3a2b282859a043cd94d16dec471b0464` completed and delivered on 2026-08-21:

- Runtime sheet resolution and fresh snapshots passed.
- Parsed accounting reconciled: 26 detected rows, 19 source rows, 7 ignored rows, 0 duplicate refs.
- Ten unique symbols were accounted for: 1 stock, 4 ETF sleeves, 5 crypto/stablecoin rows excluded.
- All required stock panel JSON artifacts were valid and non-empty.
- ETF weekly-note tags, stock-chair isolation, degraded-mode rules, and source appendix passed.
- Telegram delivery succeeded with `QUALITY GATE PASS`.

The prior skill ambiguity was caused by a backup directory inside the active profile skills tree.
It was moved intact to `/root/.hermes/backups/`; do not store backups beneath the active
`/root/.hermes/profiles/investor/skills/` directory.

## ⚠️ Do not add a second Telegram consumer

The token must have exactly **one** consumer. Binding it to the openclaw tenant (`tenant-oc-6d376f`,
agents id 1443) as well causes two competing `getUpdates` long-polls, so replies come back
nondeterministically from whichever runtime won the race. Symptom: the bot answers as the right
persona but from the wrong filesystem. Keep the binding on hermes only.

## BotFather hazard

`/mybots` → selecting the bot resumed a **pending `/deletebot` flow** and asked for
`"Yes, I am totally sure."`. Send `/cancel` first. Use `/token` to read the token, never `/mybots`.
