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
