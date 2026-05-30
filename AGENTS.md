# AGENTS.md — Repo Conventions & Agent Instructions

> **Read @GOAL.md first.** It states the mission, the bubble evidence, and the done/not-done
> checklist. Then @strategy/README.md for the current strategy (v3). Everything in this repo serves
> that goal.

## Repository Purpose

Backtest investment strategies to answer one mission — deploy $1M with crash protection in a possible
AI bubble, run by an agentic team. **The mission is defined in @GOAL.md; start there.**
Some results are also published as Telegraph posts.

## Directory Structure

```
/
├── GOAL.md              # The mission (read first)
├── strategy/            # The strategy evolution: README + v1/v2/v3.md (v3 is current)
├── research/            # Research library (AI-bubble, crash protection, frameworks, the $1M playbook)
├── backtests/           # All backtest + publisher scripts (run from repo root)
│   └── results/         # Cached *_summary.txt text output from backtests
├── skills/              # opencode SKILL.md modules for the agentic hedge-fund team
├── report/              # Generated outputs: report/img/ (chart PNGs), report/writeups/ (published md)
├── archive/             # session.txt log, skills.zip backup
├── .telegraph_token     # Telegraph API token (DO NOT COMMIT to public repos)
├── .telegraph_path_v2   # V2 report path
├── README.md            # Project overview / navigation hub
└── AGENTS.md            # This file
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
  `tax-loss-harvesting`, `fundamental-analysis`, and the top-level `agentic-fund-orchestration`. See
  @skills/README.md. Frontmatter must keep `compatibility: opencode`. The committed
  `dip-tranches-strategy/SKILL.md` was once mangled to whitespace — the canonical copies are restored;
  `archive/skills.zip` is the backup archive.

## Rules

### File Placement
- **All PNG/chart outputs → `report/img/`**. Never leave images in root.
- **Backtest + publisher scripts** live in `backtests/`; run them **from the repo root** (e.g.
  `python3 backtests/crash_protection_backtest.py`) so the `report/img/` output path resolves correctly.
- **Summary text files** live in `backtests/results/`.

### Backtest Scripts Convention
- Each script is self-contained: downloads data, runs strategy, prints results, saves chart to `report/img/`.
- Use `yfinance` for price data, `matplotlib` for charts, `pandas`/`numpy` for computation.
- pandas frequency string: use `'M'` not `'ME'` (system pandas version).
- yfinance multi-ticker download returns multi-level columns: access via `data['Close']`.
- Handle missing/delisted tickers gracefully (skip, don't crash).
- Always use only past data for signals (no look-ahead bias).
- Risk-free rate: 4% (2020-2026 era), 3% (2005-2020 era), 5% (1999-2005 era).
- Starting capital: $1,000,000 unless specified otherwise.

### Publishing
- Charts are uploaded to Imgur (Client-ID: `546c25a59c58ad7`) then embedded in Telegraph.
- Telegraph token is in `.telegraph_token`.
- Published page paths stored in `.telegraph_path` (v1) and `.telegraph_path_v2` (v2).
- Publisher scripts: `backtests/publish_report.py` (v1 Dip-Tranche), `backtests/publish_report_v2.py` (v2 Strategy Deep-Dive).

### Secrets
- `.telegraph_token` — do not commit to public repos.
- Imgur Client-ID is hardcoded (public, read-only upload).

## Published Reports

| Report | URL | Script |
|--------|-----|--------|
| V1: Dip-Tranche Strategy | [telegra.ph](https://telegra.ph/Dip-Tranche-Strategy-SP-500-Nasdaq-100-International--Backtest-20202026-05-28) | `backtests/publish_report.py` |
| V2: 8 Strategies Deep-Dive | [telegra.ph](https://telegra.ph/8-Strategies-vs-Pelosi--McCaul-Deep-Dive-Backtest-20202026-05-28) | `backtests/publish_report_v2.py` |

## Strategy Index

| Script | Strategy | Period | Key Result |
|--------|----------|--------|------------|
| `backtests/backtest.py` | Dip-Tranche (VOO/QQQ/VXUS) | 2020-2026 | Beats DCA on VXUS only |
| `backtests/tech_concentration_backtest.py` | Mag7, AI/Semis, TQQQ+SMA | 2020-2026 | 38-46% CAGR, -50% DD |
| `backtests/social_momentum_backtest.py` | Large-cap momentum screens | 2020-2026 | 33-45% CAGR |
| `backtests/sector_rotation_backtest.py` | Sector ETF rotation (4 variants) | 2020-2026 | 21% CAGR, -17% DD |
| `backtests/quality_factor_backtest.py` | Momentum + low-vol factor | 2020-2026 | 19% CAGR, -16% DD |
| `backtests/wheel_strategy_backtest.py` | Options wheel simulation | 2020-2026 | 10% CAGR (underperforms) |
| `backtests/momentum_backtest.py` | Dual momentum ETFs | 2020-2026 | 18.8% CAGR |
| `backtests/pead_backtest.py` | Gap-up momentum (mislabeled PEAD) | 2020-2026 | 16% CAGR |
| `backtests/insider_backtest.py` | Berkshire 13F copy | 2020-2026 | 15.8% CAGR (~SPY) |
| `backtests/value_factor_backtest.py` | Morningstar-proxy value+momentum | 2020-2026 | 26% CAGR, 0.99 Sharpe |
| `backtests/era_2005_2020_backtest.py` | Multi-strategy 2005-2020 test | 2005-2020 | Quality Factor best |
| `backtests/congressional_backtest.py` | Pelosi/McCaul tracker | 2020-2026 | Pelosi 20%, McCaul 28% |
| `backtests/crash_protection_backtest.py` | All-weather/trend/permanent vs S&P/QQQ | 2000-2026 | Defensive Sharpe 0.65-0.69 vs S&P 0.38; DD −16% vs −55% |

## Known Issues / Caveats

1. **Survivorship bias**: AI/Semis and Social Momentum universes are hindsight-selected. Results inflate CAGR by 5-15%.
2. **Quality Factor Sharpe overstated**: Monthly-only equity marking understates volatility.
3. **PEAD script mislabeled**: Tests gap-up momentum, not actual post-earnings drift (no real earnings dates).
4. **Options strategies synthetic**: Wheel/covered call use Black-Scholes approximations, not real option prices.
5. **Sector Rotation fails in 1999-2005**: Momentum chases tech into bubble, doesn't protect in crash.
6. **Transaction costs not modeled**: High-turnover strategies (AI/Semis, Social Momentum) would lose 1-2.5% CAGR to costs.
