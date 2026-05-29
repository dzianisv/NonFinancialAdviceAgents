# AGENTS.md — Repo Conventions & Agent Instructions

## Repository Purpose

Backtest investment strategies and publish results as Telegraph blog posts.

## Directory Structure

```
/
├── report/img/          # All generated chart PNGs (never in root)
├── reports/             # Legacy report artifacts
├── *.py                 # Backtest scripts and publishers
├── *_summary.txt        # Cached text output from backtests
├── .telegraph_token     # Telegraph API token (DO NOT COMMIT to public repos)
├── .telegraph_path      # V1 report path
├── .telegraph_path_v2   # V2 report path
├── README.md            # Project overview
└── AGENTS.md            # This file
```

## Rules

### File Placement
- **All PNG/chart outputs → `report/img/`**. Never leave images in root.
- **Backtest scripts** stay in root (flat structure, no src/ folder needed).
- **Summary text files** stay in root alongside their scripts.

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
- Publisher scripts: `publish_report.py` (v1 Dip-Tranche), `publish_report_v2.py` (v2 Strategy Deep-Dive).

### Secrets
- `.telegraph_token` — do not commit to public repos.
- Imgur Client-ID is hardcoded (public, read-only upload).

## Published Reports

| Report | URL | Script |
|--------|-----|--------|
| V1: Dip-Tranche Strategy | [telegra.ph](https://telegra.ph/Dip-Tranche-Strategy-SP-500-Nasdaq-100-International--Backtest-20202026-05-28) | `publish_report.py` |
| V2: 8 Strategies Deep-Dive | [telegra.ph](https://telegra.ph/8-Strategies-vs-Pelosi--McCaul-Deep-Dive-Backtest-20202026-05-28) | `publish_report_v2.py` |

## Strategy Index

| Script | Strategy | Period | Key Result |
|--------|----------|--------|------------|
| `backtest.py` | Dip-Tranche (VOO/QQQ/VXUS) | 2020-2026 | Beats DCA on VXUS only |
| `tech_concentration_backtest.py` | Mag7, AI/Semis, TQQQ+SMA | 2020-2026 | 38-46% CAGR, -50% DD |
| `social_momentum_backtest.py` | Large-cap momentum screens | 2020-2026 | 33-45% CAGR |
| `sector_rotation_backtest.py` | Sector ETF rotation (4 variants) | 2020-2026 | 21% CAGR, -17% DD |
| `quality_factor_backtest.py` | Momentum + low-vol factor | 2020-2026 | 19% CAGR, -16% DD |
| `wheel_strategy_backtest.py` | Options wheel simulation | 2020-2026 | 10% CAGR (underperforms) |
| `momentum_backtest.py` | Dual momentum ETFs | 2020-2026 | 18.8% CAGR |
| `pead_backtest.py` | Gap-up momentum (mislabeled PEAD) | 2020-2026 | 16% CAGR |
| `insider_backtest.py` | Berkshire 13F copy | 2020-2026 | 15.8% CAGR (~SPY) |
| `value_factor_backtest.py` | Morningstar-proxy value+momentum | 2020-2026 | 26% CAGR, 0.99 Sharpe |
| `era_2005_2020_backtest.py` | Multi-strategy 2005-2020 test | 2005-2020 | Quality Factor best |
| `congressional_backtest.py` | Pelosi/McCaul tracker | 2020-2026 | Pelosi 20%, McCaul 28% |

## Known Issues / Caveats

1. **Survivorship bias**: AI/Semis and Social Momentum universes are hindsight-selected. Results inflate CAGR by 5-15%.
2. **Quality Factor Sharpe overstated**: Monthly-only equity marking understates volatility.
3. **PEAD script mislabeled**: Tests gap-up momentum, not actual post-earnings drift (no real earnings dates).
4. **Options strategies synthetic**: Wheel/covered call use Black-Scholes approximations, not real option prices.
5. **Sector Rotation fails in 1999-2005**: Momentum chases tech into bubble, doesn't protect in crash.
6. **Transaction costs not modeled**: High-turnover strategies (AI/Semis, Social Momentum) would lose 1-2.5% CAGR to costs.
