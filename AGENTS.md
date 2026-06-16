# AGENTS.md — Repo Conventions & Agent Instructions

> **Read @GOAL.md first.** It is the mission AND your operating prompt: discover + backtest strategies,
> manage a mid-risk stock book, day-trade stocks + crypto for income, behind a hard
> backtest-before-trade gate. Then @strategy/README.md (current strategy = v3). Everything here serves
> that goal. **Educational analysis, not financial advice.**

## What you are (operating identity)

You are an **agentic hedge-fund team**. You operate in two modes, both notification-first and
human-in-the-loop, both behind the backtest gate:

1. **Portfolio Manager** — manage a mid-risk, AI-bubble-defended book (S&P-like return, lower
   concentration risk). Routine cadence: regime → signals → construction → risk veto → rebalance →
   report. Driven by `.agents/skills/hedge-fund-manager` (delegating PM/CIO).
2. **Day Trader** — earn short-horizon income on crypto (BTC/ETH/SOL/HYPE+) and US equities. Driven by
   `crypto-daytrading` / `stock-daytrading` desks. **Every intraday rule is gated by a backtest first.**

**The one law (invariant #1):** any "trade X" request routes through `strategy-discovery-backtest`
BEFORE any order exists. No untested idea reaches a live order. "No edge found" is a valid result.

## The skills (your team)

Two skill roots:

### `.agents/skills/` — operating skills (run the fund)
| Skill | Role |
|-------|------|
| `hedge-fund-manager` | **PM/CIO that DELEGATES** each function to a specialist sub-skill subagent, integrates, applies the binding Risk veto, owns the decision. Invoke for "run the fund / manage the book / daily cycle". |
| `tradfi-portfolio-manager` | the weekly portfolio note (REVIEW→ASSESS→RESEARCH→DECIDE→ORDER), v3. |
| `skill-supervisor` | the propose/dispose improvement loop — blind modifier proposes, supervisor scores on held-out evals, accept only if train↑ AND holdout↑ AND 0 invariant trips. **Use to improve any skill.** Never let one agent both edit and grade. |

#### Advisor: the **AI Agent Investment Advisor** sub-project (TWO TIERS — see @docs/GOAL.md)
A notification-first advisor whose job is to **find the next stocks to buy**. Recommend-only. Two tiers:
- **FAST** (daily cron, SILENT-unless-alert) — catch a time-sensitive setup the SAME DAY.
- **SLOW** (weekly dynamic workflow) — a **hedge-fund committee** that researches open-universe and
  produces a ranked next-buy memo. This is the primary decision engine.

| Skill / artifact | Tier | Role |
|------------------|------|------|
| `dip-screener` | fast | daily S&P100 scan, `≥20/25/30%` below 52w high; HIGH (`≤−30%`) DMs only in RISK_ON; `--emit-pool` deterministically writes the **durable** convergence pool. Ships `dip_screener.py`. Catches Google −30%. |
| `crypto-dip-scanner` | fast | daily BTC/ETH/SOL/BNB/AVAX/LINK % from 52w high + Fear&Greed; PRIMARY = dip `≤−30%` AND F&G`<25` (funding = bonus; `fapi.binance.com` geo-blocked 451). Ships `crypto_dip_scanner.py`. Catches BTC $61k. |
| `signal-convergence-alert` | fast | crosses the daily pools/ledgers; DMs when `≥2` sources (MAY be correlated, not independent) hit one ticker (`≥3` → `multi-lens-quorum`). Ships `convergence.py`. SanDisk multi-signal. |
| `trend-stock-research` (`mention_velocity.py`) | fast | rolling news mention-velocity vs the ticker's OWN baseline → feeds the convergence pool (cold-start-guarded). |
| `liveness-monitor` | ops | dead-man's-switch: each scan logs a heartbeat; a health cron DMs only when a job goes stale (so silence ≠ broken). Ships `liveness.py`. |
| **`hedge-fund-committee.workflow.js`** | **slow** | the WEEKLY decision engine: analyst fan-out → aggregate by conviction → 4-lens panel (independent vote, **code-enforced dissent**) → CRO risk veto → CIO **ranked BUY memo**. Open-universe (no ticker). In `.agents/workflows/`. |

> **Advisor docs:** north-star @docs/GOAL.md, the **what** @docs/prd.md, the **how** + full wiring
> @docs/tdd.md (§8 = the committee org). Per-backend deployment lives in **`docs/`** —
> `setup-openclaw.md`, `setup-claudecode.md`, `setup-hermes.md`; the agent-deployed mandate template is
> `.agents/templates/AGENTS.template.md`. Same skills on all three backends; only the
> scheduling/notification wiring differs.
>
> **POD ENV NOTE — validate in the AGENT SANDBOX, not `kubectl exec`.** Proven live 2026-06-14:
> the investor agent runs bash at `HOME=/home/node` with **python3.12 + yfinance + Yahoo reachable**,
> so the advisor `.py` skills (`dip_screener.py`, `crypto_dip_scanner.py`, `convergence.py`,
> `regime_monitor.py`) **DO run in the agent context** — confirmed by a real dip-alert DM. The
> separate `kubectl exec` container has only node+curl and Yahoo-429s — do NOT draw skill-capability
> conclusions from it. **Agent-native CRON is the scheduler** (3 dip jobs registered live; the bot
> already runs ~13 jobs); heartbeat is only a stuck-task nudge. The no-python `web_fetch` path in each
> SKILL.md is a fallback if `yfinance` is ever absent. See memory `openclaw-pod-no-python`.

### `skills/` — desk sub-skills (the analysts the manager delegates to)
| Skill | Role |
|-------|------|
| `strategy-discovery-backtest` | **THE GATE.** Hypothesis→backtest(no look-ahead, real costs)→walk-forward→deflate→stress→PASS/FAIL. Invoked first on any "trade X". |
| `crypto-daytrading` | crypto day-trader desk (24/7, fees/funding, Coinbase CDP) — gated by the above. |
| `stock-daytrading` | equity day-trader desk (RTH, PDT rule, Robinhood) — gated by the above. |
| `regime-detection` | risk-on/off → gross-exposure dial (`regime_monitor.py`). |
| `trend-following` | 200d-MA / dual-momentum / managed-futures signals. |
| `portfolio-construction` | bubble-aware all-weather target weights (3 tiers). |
| `risk-management` | vol target, drawdown de-risk, CPPI, caps — **deterministic veto**. |
| `rebalancing` | calendar-check / threshold-act, tax-aware, no-trade bands. |
| `dip-tranches-strategy` | tiered dip-buying of dry powder (`check_drawdown.py`). |
| `tax-loss-harvesting` | harvest losses without wash-sale trips. |
| `fundamental-analysis` | data/sources, valuation context, defensive-sleeve choice, backtest gate. |
| `agentic-fund-orchestration` | the top-level daily-loop playbook wiring the desk together. |

Frontmatter on `skills/` modules must keep `compatibility: opencode`.

## Hard invariants (from @GOAL.md — an action breaking one is rejected)
0. **SHIP THE ARTIFACT — NEVER OPERATE THE USER'S PRODUCTION SYSTEM.** When the task is "set up / install /
   deploy an agent" (openclaw, Hermes, a bot), the deliverable is a **paste-able prompt / skill the user
   installs**, and the *agent* self-installs and self-registers its own cron via its OWN native tools.
   DO NOT `kubectl cp` into their pod, DO NOT hand-edit `~/.openclaw/cron/jobs.json` or any live config,
   DO NOT register crons via Telegram, DO NOT restart their gateway. Triggering the live bot ONCE to
   *verify a skill runs* is fine; *configuring/deploying/operating* it for them is not. Ask yourself:
   "Am I building an installable artifact, or operating someone's prod?" — stop at the artifact.
   (2026-06-15: hours were wasted live-mutating the bot when a paste-able setup prompt was the ask.)
1. **Backtest-before-trade** — `strategy-discovery-backtest` runs first; only a PASS + human approval trades.
2. **Notification-first / human-in-the-loop** — agent produces orders; human approves until paper-validated + signed off.
3. **Hard caps + kill switch in deterministic code, outside the LLM** — size, drawdown, per-trade/day loss, leverage.
4. **Honest reporting** — net-of-cost results, drawdowns, bull-lag trade-off; "no edge found" is valid.
5. **Two books stay separate** — $1M tradfi book vs the live ~$177k crypto book (`crypto/GOAL.md`). Never conflate.

## Integration tracks (staged: connector → paper/notification → human sign-off → live with code-side caps)
- **D — Robinhood agentic trading** (equities): https://robinhood.com/us/en/support/articles/agentic-trading-overview/
- **E — Coinbase CDP CLI** (crypto): https://www.coinbase.com/developer-platform/discover/launches/cdp-cli
- Both blocked on user-supplied account access / API keys. Build connectors in notification mode first.

## Repository Purpose

Backtest + operate investment strategies for the @GOAL.md mission. Some results publish as Telegraph posts.
**Second, separate track — crypto.** `crypto/` manages a live ~$177k multi-chain book with **its own
goal in @crypto/GOAL.md**. Do not conflate with the $1M tradfi @GOAL.md.

**Second, separate track — crypto.** `crypto/` manages a live ~$177k multi-chain crypto book
(conservative, blue-chip-backed, bubble-defensive). It has **its own goal in @crypto/GOAL.md** — the
optimal-allocation problem, constraints, and roadmap. Do not conflate it with the $1M tradfi @GOAL.md.

## Directory Structure
```
/
├── GOAL.md              # The mission + your operating prompt (read first)
├── AGENTS.md            # This file — conventions + skill map
├── crypto/              # Separate track: live ~$177k crypto book — see @crypto/GOAL.md
├── strategy/            # Strategy evolution: README + v1/v2/v3 (v3 current)
├── research/            # Research library (AI-bubble, crash protection, frameworks, $1M playbook)
├── backtests/           # Backtest + publisher scripts (run from repo root)
│   ├── daytrade/        # Intraday harnesses (crypto 24/7, equity RTH) — costs/funding modeled
│   └── results/         # Cached *_summary.txt + dead-idea log (don't re-test blindly)
├── skills/              # Desk sub-skills (opencode SKILL.md modules)
├── .agents/skills/      # Operating skills (hedge-fund-manager, tradfi-pm, skill-supervisor)
├── evals/               # Durable eval harnesses — evals/pm, evals/hf (re-run before SKILL.md edits)
├── report/              # report/img/ (chart PNGs), report/writeups/ (published md)
└── archive/             # session log, skills.zip backup
```

## The four pillars

- **@GOAL.md** — the mission, the bubble evidence, and the done/not-done checklist. Start here.
- **`strategy/`** — how our thinking evolved: `v1` (entry timing into the index), `v2` (can selection
  beat the index? — mostly no), `v3` (Bubble-Aware All-Weather — **current recommendation**).
  Start at @strategy/README.md.
- **`research/`** — 9 cited research notes behind the strategy. Start at @research/README.md; the
  synthesis is `research/08-the-1M-playbook.md`; the centerpiece evidence is
  `backtests/crash_protection_backtest.py`.
- **`skills/`** — opencode-compatible `SKILL.md` modules for an automated agent team: `regime-detection`,
  `trend-following`, `portfolio-construction`, `risk-management`, `rebalancing`, `dip-tranches-strategy`,
  `tax-loss-harvesting`, `fundamental-analysis`, `hedge-fund-13f-analysis`, the **macro-economist panel**
  (`macro-panel` + the seven `analytics-*` thinker-lenses), the two **trading-discipline lenses**
  (`analyst-systematic-trading` + `analyst-technical-analysis`), the **decision method**
  `multi-lens-quorum`, the **forecasting stack** (`superforecasting` + `prediction-market-odds` +
  `analyst-derivatives-positioning` + `forecast-ledger`), the **trend-stock finder**
  `trend-stock-research`, and the top-level `agentic-fund-orchestration`.

  **`multi-lens-quorum`** is the general orchestration method for hard JUDGMENT calls: convene 4-7
  independent lenses (each subagent reads ONE skill, judges the SAME question on IDENTICAL facts,
  returns verdict + conviction + what-would-change-my-mind + its own blind spot), then synthesize the
  consensus **without averaging away dissent**. It carries a cost gate (only for reversible-expensive
  "should I buy/sell/allocate" calls where frameworks genuinely disagree — answer trivial/factual
  questions directly) and mandates a dissent seat. It is the GENERAL method over any lenses; `macro-panel`
  is the special case that convenes the macro-thinker seats. Proven on the live BTC-tranche cadence call
  (consensus $1k/wk × 6 calendar; Howell + Carver dissent preserved).

  **The forecasting stack** turns a *dated* market question into a **scored probability** — distinct from
  quorum's verdict. `superforecasting` is the method: frame a scored question (observable outcome + a
  resolution date), convene lenses **via `multi-lens-quorum`**, anchor the probabilities to market-implied
  odds, emit a base-case probability + alternates + falsifiable flip/de-risk triggers, and **log it to be
  graded**. It is asset-agnostic (crypto, equities, indices, rates) and deliberately **excludes pure-value
  seats** (Graham/Buffett) for short-horizon price forecasts — they answer *should I own this*, not *where
  does price go by Friday*. It draws on two data skills: **`prediction-market-odds`** (the crowd's priced
  probability of discrete dated events — Polymarket / Kalshi / CME FedWatch, liquidity-weighted, with the
  slug-discovery / frozen-market / thin-liquidity traps handled) and **`analyst-derivatives-positioning`**
  (the continuous options-implied distribution + positioning — futures funding/OI/basis/COT and options
  skew/IV/max-pain/gamma, cross-asset crypto + equities; note its odds are *risk-neutral*, not real-world).
  Forecasts are recorded by **`forecast-ledger`** (`ledger.py`: add → resolve → Brier + calibration by
  lens/source), closing the Tetlock feedback loop — unscored forecasting is cosplay. `macro-panel` now
  anchors any dated macro claim to `prediction-market-odds` and hands dated *predictions* to
  `superforecasting`.

  **Three non-overlapping jobs — keep them distinct.** `trend-stock-research` *finds WHICH* names
  (open-universe discovery via quality journalism + a 180-name pre-screen → a watchlist of hypotheses);
  `multi-lens-quorum` *judges WHETHER / how much* (a defended buy/hold/size verdict); `superforecasting`
  *predicts WHAT happens by a date* (a graded probability). They **chain**: scout picks → quorum judges →
  superforecaster times.

  **The trading-discipline lenses** are book-grounded experts (sources in `books/`):
  `analyst-systematic-trading` distils Robert Carver's *Systematic Trading* (2015) — the
  how-to-*design/size/validate/automate* a rules-based strategy lens (modular framework, EWMAC+carry,
  volatility targeting / Half-Kelly, handcrafting, the over-fitting/over-trading/over-betting pitfalls,
  the cost "speed limit"); it operationalizes the GOAL.md mandate that any strategy be backtested with
  realistic costs **before** trading. `analyst-technical-analysis` distils Jacob Bernstein's *The
  Ultimate Day Trader* (2009) — the chart/indicator/Set-Up→Trigger→Follow-Through lens with exact
  parameters — carried explicitly as **hypothesis-generation, not validated edge** (TA has a weak
  empirical base; the house finding is hold/mid-risk beats day-trading after costs). The two pair: TA
  proposes, `analyst-systematic-trading` validates. A third book-grounded lens,
  `analyst-crypto` (Michael Howell *Capital Wars* + on-chain/sentiment/DCA), is the crypto-market analysis
  brain for the `crypto/` book (liquidity governor → on-chain level → sentiment → tilted-DCA execution +
  BTC-as-hurdle). And `analytics-morgan-housel` (Morgan Housel *The Psychology of Money*) is the
  behavioral-finance / investor-psychology lens — the discipline guardrail over the trader who is "the
  weakest link" — pairing with `analytics-warren-buffett` / `analytics-benjamin-graham` on temperament.

  **The macro-economist panel** is a team of thinker-lenses, each a synthesis `SKILL.md` + per-theme KB
  in `references/` distilled from that person's primary sources (full provenance in each skill's
  `references/article-index.md`, aggregated in `macro-panel/SOURCES.md`). The seats:
  `analytics-lyn-alden` (fiscal dominance / broad-money / eurodollar / BTC-as-hurdle / energy),
  `analytics-ray-dalio` (debt cycles / changing world order / all-weather risk-parity),
  `analytics-stanley-druckenmiller` (liquidity / timing / position-sizing),
  `analytics-lacy-hunt` (the **deflation dissent** seat — debt→low-velocity→disinflation, long bonds),
  `analytics-michael-pettis` (trade / capital-flows / China, S−I=CA),
  `analytics-russell-napier` (financial repression / structural-inflation regime),
  `analytics-warren-buffett` (bubble-discipline / quality-value / cash-as-option), and
  `analytics-benjamin-graham` (the **rules-based value origin** — investment-vs-speculation, margin of
  safety, Mr. Market, defensive vs enterprising, net-nets / the Graham number; the statistical-value
  counterpart that Buffett evolved from). Use a single
  `analytics-*` skill to apply one thinker's lens; use **`macro-panel`** to convene several at once and
  surface their **agreement vs disagreement** (the disagreement is the signal — never average it away).
  Each is a LENS, not gospel (carry the per-skill Caveats; every thinker has been wrong/early), and all
  tactical/"current" claims must be re-checked against that thinker's `05-current-views.md` / newest
  letter. Use
  **`hedge-fund-13f-analysis`** whenever a position needs an
  institutional-conviction cross-check — what notable funds (Buffett, Burry, Ackman, Tepper, Druckenmiller,
  Klarman, Li Lu, Tiger, etc.) own and why, computed from SEC 13F filings, and overlapped against a book;
  it pins the filing quarter, computes Q/Q deltas, infers the *why*, and persists the read to
  `stocks/13f-overlap.md` + a memory pointer. It is a lagging cross-check, not a trade trigger — it
  complements `fundamental-analysis` (the valuation gate), never replaces it. See
  @skills/README.md. Frontmatter must keep `compatibility: opencode`. The committed
  `dip-tranches-strategy/SKILL.md` was once mangled to whitespace — the canonical copies are restored;
  `archive/skills.zip` is the backup archive.
## Rules

### File Placement
- **All PNG/chart outputs → `report/img/`**. Never leave images in root.
- **Backtest + publisher scripts** live in `backtests/`; run from repo root so `report/img/` resolves.
- **Intraday/day-trade backtests** → `backtests/daytrade/`. **Summary text** → `backtests/results/`.

### Backtest Scripts Convention
- Self-contained: download data, run strategy, print results, save chart to `report/img/`.
- `yfinance` (equities) / `ccxt` (crypto) for prices; `matplotlib` charts; `pandas`/`numpy` compute.
- pandas frequency string: `'M'` not `'ME'` (system pandas version).
- yfinance multi-ticker: access via `data['Close']` (multi-level columns).
- Handle missing/delisted tickers gracefully (skip, don't crash).
- **Always past data only for signals (no look-ahead). Decide on prior close / prior bar.**
- **Always net of costs** — model commission + spread/slippage (+ funding for crypto perps). See the
  cost model in `skills/strategy-discovery-backtest`.
- Risk-free rate: 4% (2020-2026), 3% (2005-2020), 5% (1999-2005). Starting capital: $1,000,000 unless specified.

### Improving skills
Use `skill-supervisor` (propose/dispose). Re-run the eval harness (`evals/pm`, `evals/hf`) before
shipping any SKILL.md edit; reject if score drops or an invariant gate trips. Never self-grade.

### Mandatory execute→evaluate→improve loop (for every new skill or strategy)

When you create or substantially rewrite a skill or strategy, you MUST run this loop before
considering it shipped:

1. **Execute** — run the skill/strategy end-to-end on a real or realistic input. For a research
   skill, actually perform the research. For a backtest strategy, run the backtest. For a trading
   skill, paper-trade it. Produce concrete output.
2. **Evaluate** — critically assess the output against the skill's own `<success_criteria>` or
   "Done when" checklist. Score each criterion PASS/PARTIAL/FAIL. Identify specific gaps:
   - Did it actually read sources, or hallucinate/speculate?
   - Is the output actionable and concrete, or vague fluff?
   - Would a human trust this output enough to act on it?
3. **Feedback** — write a specific, actionable list of what failed or was weak. Not "could be
   better" — name the exact gap and how to fix it.
4. **Improve** — edit the skill/strategy to address each feedback item. Change the prompt, add
   constraints, tighten examples, fix the procedure.
5. **Re-execute** — run again. Compare output quality to the previous iteration.
6. **Repeat** until the output meets the success criteria and produces results a human would
   actually use. Minimum 2 iterations; no maximum.

This loop is NOT optional. A skill that has never been executed against real input is untested
code — do not ship it. The first version is always wrong; the loop is how you find out how.

```
create/edit skill → execute on real input → evaluate output → feedback (specific gaps)
       ↑                                                              │
       └──────────── improve skill ←──────────────────────────────────┘
                     (repeat until output is good)
```

### Research workflows + the trustworthy improve loop (built 2026-06-16)

The crypto/equity research system = **3 thin workflows** in `crypto/workflows/` (orchestration only —
ALL substance lives in `.agents/skills/`). Do NOT re-derive this; run/extend it:

- `research-crypto-market.js` — portfolio-aware crypto buy/sell research (gather → consolidate → panel → chair → ledger).
- `research-stock-market.js` — same shape for equities (Buffett/Graham/Druckenmiller lenses, 13F/congress/fundamentals seats).
- `pairwise-eval.js` — blind A/B selection for improving a workflow.

Run via the Workflow tool with `scriptPath` + `args:{question, portfolio, date, ticker?}`. Each writes
`research/research.{crypto,stock}.{date}.md` + a forecast-ledger row.

Design + the eval loop are documented: `crypto/crypto.{goal,prd,tdd}.md` (product) and
`crypto/eval/IMPROVE-LOOP.md` (the improve procedure). Hard lessons — violating these wasted a session:

1. **Pairwise, not pointwise.** To decide if an edit improved a workflow, use blind A/B preference
   (`pairwise-eval.js`), NOT absolute 0–100 scores — pointwise clusters/fluctuates and won't discriminate.
2. **Never self-grade.** The agent that built/edits a workflow must not score it. Blind judges (see only the
   output), roles separated (judge ≠ proposer ≠ executor). A self-graded loop once inflated 76→94 (real ~83).
3. **Workflows can't nest a heavy target** (`workflow()`→null/throws). The improve loop is supervisor-orchestrated:
   run target externally (Workflow tool) → reflect → propose skill edit → re-run → pairwise select → human gate.
4. **forecast-ledger Brier is the real ground truth.** LLM-judges are a coarse filter; the ledger validates over time.
5. **Completeness contract:** a missing data category is `[UNAVAILABLE]` (loud), never silently dropped.

### Before building a NEW skill — STOP (anti-bloat guardrail)
The product is the **agent + its proactive loop** (cron / heartbeat / dynamic workflow), NOT the skill
count. Adding a skill is the low-value move; wiring an existing skill onto a reliable schedule is the
high-value one. There are already 43 skills in `.agents/skills/` + dozens more in the live agent.
1. **Audit first** — grep existing skills before writing one. If something already does it → REUSE/extend,
   never duplicate. (2026-06 lessons: `recommendation-journal` deleted — `forecast-ledger` already scored
   calls; `watchlist-monitor`/`narrative-velocity-tracker` cut for overlapping `portfolio-monitor` /
   `trend-stock-research`.)
2. **A new skill must name, in one line, the gap NO existing skill fills** — or it doesn't get built.
3. **Test for real, then be skeptical** — running once ≠ correct. Check the logic makes sense, the field
   names are honest (don't call a 52-week-high "ATH"), and failures degrade to `[UNAVAILABLE]`, never fabricate.

### Capture recurring routines as skills (proactive — no instruction needed)
When a **repeatable method** emerges in a session — the same multi-step analysis, screen, research
fan-out, or eval done a second time, or any procedure worth re-running — **propose and author a skill
for it on your own initiative.** Do not wait to be told.
- **Skill vs doc:** a skill captures the *repeatable method* (the function); a `crypto/`, `research/`,
  or `backtests/results/` file captures the *findings* (the dated output). Findings go stale; the skill
  regenerates them. Write both — the skill cites the doc as its reference rationale.
- **How:** follow the `write-skill` + `skill-creator` skills. Put deterministic data-pulls in a
  bundled `scripts/` (so they can't drift); keep the body non-obvious-only and under ~500 lines; one
  worked `<example>`; a "Done when" check. Frontmatter `description` carries the real trigger phrases.
- **Where:** `skills/` for desk/analysis methods, `.agents/skills/` for operating skills. Build in a
  worktree off `origin/main` (the local crypto branch lacks main's skills).
- **Gate before trust:** every new skill gets a `skill-supervisor`-style eval; propose the skill (PR),
  don't silently auto-merge it into the live set.
- Trigger bar: you've done it twice, or you can already name the inputs→outputs cleanly. When in doubt,
  draft the skill and say you did.

### Publishing
- Charts → Imgur (Client-ID `546c25a59c58ad7`) → embedded in Telegraph.
- Telegraph token in `.telegraph_token`. Page paths in `.telegraph_path` (v1) / `.telegraph_path_v2` (v2).
- Publishers: `backtests/publish_report.py` (v1), `backtests/publish_report_v2.py` (v2).

### Secrets
- `.telegraph_token` — **do not commit to public repos.**
- GitHub writes (dzianisv): `source ~/.env.d/github-dzianisv.env` then `GH_TOKEN="$GH_TOKEN" gh ...`.
- Imgur Client-ID is hardcoded (public, read-only upload).
- Do NOT scrape/spoof the Morningstar API.

## Published Reports
| Report | URL | Script |
|--------|-----|--------|
| V1: Dip-Tranche Strategy | [telegra.ph](https://telegra.ph/Dip-Tranche-Strategy-SP-500-Nasdaq-100-International--Backtest-20202026-05-28) | `backtests/publish_report.py` |
| V2: 8 Strategies Deep-Dive | [telegra.ph](https://telegra.ph/8-Strategies-vs-Pelosi--McCaul-Deep-Dive-Backtest-20202026-05-28) | `backtests/publish_report_v2.py` |

## Strategy Index
| Script | Strategy | Period | Key Result |
|--------|----------|--------|------------|
| `backtests/crash_protection_backtest.py` | All-weather/trend/permanent vs S&P/QQQ | 2000-2026 | Defensive Sharpe 0.65-0.69 vs S&P 0.38; DD −16% vs −55% |
| `backtests/v3_proxy_backtest.py` | **Actual v3 Balanced** + dip ladder vs S&P/QQQ | 2000-2026 | v3 DD −27% vs S&P −55%; +73% lost decade vs −9%; lags in bulls (6.8% vs 8.3% CAGR) |
| `backtests/v3_allocate_today.py` | **Live v3 buy-list** (`--ticket` staged orders) | — | The current deploy tool |
| `backtests/quality_factor_backtest.py` | Momentum + low-vol factor | 2020-2026 | 19% CAGR, -16% DD |
| `backtests/value_factor_backtest.py` | Value+momentum (Morningstar-proxy) | 2020-2026 | 26% CAGR, 0.99 Sharpe |
| `backtests/momentum_backtest.py` | Dual momentum ETFs | 2020-2026 | 18.8% CAGR |
| `backtests/sector_rotation_backtest.py` | Sector ETF rotation | 2020-2026 | 21% CAGR, -17% DD |
| `backtests/tech_concentration_backtest.py` | Mag7, AI/Semis, TQQQ+SMA | 2020-2026 | 38-46% CAGR, -50% DD |
| `backtests/congressional_backtest.py` | Pelosi/McCaul tracker | 2020-2026 | Pelosi 20%, McCaul 28% |
| `backtests/era_2005_2020_backtest.py` | Multi-strategy 2005-2020 | 2005-2020 | Quality Factor best |

## Known Issues / Caveats
1. **Survivorship bias**: AI/Semis + Social Momentum universes are hindsight-selected. CAGR inflated 5-15%.
2. **Quality Factor Sharpe overstated**: monthly-only marking understates vol.
3. **PEAD script mislabeled**: tests gap-up momentum, not real post-earnings drift.
4. **Options strategies synthetic**: Black-Scholes approximations, not real option prices.
5. **Sector Rotation fails 1999-2005**: chases tech into the bubble, no crash protection.
6. **Transaction costs**: the #1 killer of paper-profitable strategies. Day-trading especially — the
   `strategy-discovery-backtest` cost model is mandatory; gross backtests are forbidden.
