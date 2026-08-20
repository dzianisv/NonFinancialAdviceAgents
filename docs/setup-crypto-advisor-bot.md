# Setup: crypto-advisor on the Telegram trader bot (@MichaelBurryTraderBot)

**How to use this:** paste the prompt block below to the bot in one message. The *agent* installs its own
skills and registers its own cron job with its native tools. Nobody hand-edits the bot's internals.

> Recommend-only / educational. The agent never trades.

## Verified prerequisites (checked 2026-08-20)

| Item | Status |
|---|---|
| Repo `dzianisv/NonFinancialAdviceAgents` | public (`dzianisv/backtest` redirects here) |
| `crypto-advisor/SKILL.md` on `main` | sha256 `cc4f1ca4…` — identical to local working copy |
| All 16 dependency `SKILL.md` files on `main` | HTTP 200 |
| `@MichaelBurryTraderBot` reachable | ❌ **unresponsive** — no reply to 5 messages; last bot output 2026-06-21 |

Bring the agent back online before pasting, then verify with `/help` or a plain ping.

## Skill set installed

```
crypto-advisor                                          ← orchestrator
analyse-technical  analyse-onchain  analyse-defi        ← Phase 1 Research Desk
analyse-macro      analyse-smartmoney
investor-benjamin-graham   investor-warren-buffett      ← Phase 2 Investment Panel
investor-ray-dalio         investor-stanley-druckenmiller
investor-lyn-alden         (analyse-defi doubles as the Burniske seat)
read-news  narrative-news  reference-validator          ← sourcing + citation post-hook
crypto-token-screener  skeptic  mkt                     ← screening, skeptic gate, buy-alerts
```

## 📋 PASTE THIS TO THE BOT

```text
<role>
You own this task inside your own runtime. Configure and execute it end-to-end with your native tools
(terminal, skill_manage, cron). Do not ask me to SSH into your host.
</role>

<goal>
1) Install the crypto-advisor skill + all its dependency skills from the public repo
   dzianisv/NonFinancialAdviceAgents.
2) Create a durable DAILY cron job that runs crypto-advisor and delivers the report to this Telegram chat.
</goal>

<execution>
STEP 1 — INSTALL SKILLS (one command, from your workspace dir):
  npx -y skills add dzianisv/NonFinancialAdviceAgents --agent openclaw --yes --copy --dangerously-accept-openclaw-risks

  Skills are nested under .agents/skills/ in that repo. If discovery fails, fall back to per-skill URL
  install of each SKILL.md from:
  https://raw.githubusercontent.com/dzianisv/NonFinancialAdviceAgents/main/.agents/skills/<NAME>/SKILL.md

  Required skill list (crypto-advisor + dependencies):
  crypto-advisor
  analyse-technical, analyse-onchain, analyse-defi, analyse-macro, analyse-smartmoney
  investor-benjamin-graham, investor-warren-buffett, investor-ray-dalio,
  investor-stanley-druckenmiller, investor-lyn-alden
  read-news, narrative-news, reference-validator, crypto-token-screener, skeptic, mkt

STEP 2 — VERIFY THE LOAD LIST (a SKILL.md on disk is NOT a loaded skill):
  node openclaw.mjs skills list --agent investor --json
  Every skill above must show "eligible": true AND "modelVisible": true.
  Report the exact JSON rows for crypto-advisor and the 5 investor-* skills.

STEP 3 — CREATE THE DAILY CRON (native scheduler only; never hand-edit ~/.openclaw/cron/jobs.json):
  schedule: 0 8 * * *   (08:00 daily, your local TZ — state which TZ you used)
  target:   telegram, this chat
  prompt:   "Load the crypto-advisor skill and execute EVERY mandatory step end-to-end: per-token
             sequential data pull, Phase 1 Research Desk (5 researchers), CIO briefing package,
             Phase 2 Investment Panel (6 investors), conviction-weighted verdict, Portfolio Governor
             cap, Verdict Critic for EVERY token, citation validation, then send the Telegram daily
             recap. Universe: BTC ETH SOL TON HYPE AAVE JUP UNI AERO PUMP LINK.
             Educational only, not financial advice."

STEP 4 — RUN ONCE NOW as a smoke test and send the output here.
</execution>

<constraints>
- Current-run command output only. No claims without evidence.
- Note honestly which tools you lack (e.g. TradingView MCP) and degrade the run rather than fabricating data.
- Never print credentials.
</constraints>

<output>
Return a compact status table: skills installed (count + names), load-list verification result,
cron job id + schedule + next run, smoke-test result. Mark anything unproven as BLOCKED.
</output>
```

## Known degradation on this host

`crypto-advisor` assumes **TradingView MCP tools in the orchestrator**. The openclaw investor agent has no
TradingView MCP, so `tv_data_package` will be empty and the `analyse-technical` brief degrades to
`INSUFFICIENT DATA`. Either wire a TradingView MCP into the agent, or accept a run driven by the on-chain /
DeFi / macro / smart-money seats only — and require the agent to say so rather than invent price levels.

## Verify after install

```sh
node openclaw.mjs skills list --agent investor --json | grep -E 'crypto-advisor|investor-|analyse-'
```
Each row must show `"eligible": true` AND `"modelVisible": true`. `skills add` can exit 0 having installed
nothing — "installation complete" is not proof, the load list is.
