# 06 — Data Feeds, Broker APIs & Backtest Frameworks

*Free → paid, for an automated/agentic fund. Educational.*

## Market data

| Source | Cost | Good for | Caveats |
|--------|------|----------|---------|
| **yfinance** | free | research, backtesting, prototyping | no SLA, occasionally flaky, **no delisted names** (survivorship), don't use as sole live source |
| **FRED** (St. Louis Fed) | free | macro: yield curve, credit spreads (HY OAS), rates, employment | the gold standard for the **regime agent** |
| **Tiingo** | ~$10/mo | clean EOD, quant research; academic pricing | EOD-focused |
| **Polygon.io** | free 5/min (15-min delayed); paid real-time/tick | serious intraday/live | rate limits on free |
| **Alpha Vantage** | free ~25 calls/day; paid ~$29/mo | built-in technical indicators | free tier too thin for production |
| **Finnhub** | free ~60 calls/min (15-20 min delay) | prototyping | delayed on free |

**Recommendation:** yfinance + FRED for research; cross-check live signals against one paid source
(Tiingo or Polygon) before trading real money.

## Broker / execution APIs

| Broker | Library | Why |
|--------|---------|-----|
| **Alpaca** | `alpaca-py` | cloud-native REST + websockets; commission-free US stocks/ETFs/crypto/options; **up to 3 paper accounts**; same code for paper & live. Best low-friction start. |
| **Interactive Brokers** | `ib_async` (maintained fork of `ib_insync`) | institutional-grade execution, global/instrument coverage; needs TWS/IB Gateway running. Pro upgrade path. |

## Backtesting frameworks

| Framework | Strength | Note |
|-----------|----------|------|
| **vectorbt** | Numba-vectorized, very fast param sweeps & large universes | watch packaging; `vectorbt PRO` is the maintained commercial line |
| **`bt`** | clean tree-based allocation/rebalancing backtests | best for portfolio-level (weights, rebalance rules) — like our all-weather strategies |
| **backtrader** | easiest research→live with broker hooks | largely unmaintained since ~2018 |
| **zipline-reloaded** | event-driven equity-factor research | slow on minute data |
| **NautilusTrader** | fast production-grade event engine | when you outgrow the above |

**This repo** uses a hand-rolled vectorised/loop engine on pandas + yfinance (see `*_backtest.py`),
which is fine for daily-bar portfolio strategies and keeps dependencies minimal.

## Scheduling / orchestration
- **cron** on an always-on VM — simplest.
- **GitHub Actions** scheduled workflows — free, great for daily EOD jobs + audit logging via commits.
- **AWS Lambda + EventBridge** — serverless, event-driven.

For a daily-rebalanced fund, GitHub Actions or a small cron VM is sufficient and cheap.

## Practical daily pipeline (notification-first)
1. **~4:15pm ET:** pull EOD prices (yfinance) + macro (FRED).
2. Compute regime score, signals, target weights (note 05).
3. Risk layer checks caps/drawdown/vol; computes order deltas with no-trade bands.
4. **Notify** (email/Telegram/Slack) with the proposed trades + a plain-English rationale.
5. Human approves → execution agent places orders (Alpaca/IBKR). **Notification-only for the first
   6+ months** — automated trading bugs are expensive bugs.
6. Append everything to an immutable log; update the dashboard/metrics.

See `skills_tmp/data-sources.md` (recovered from `skills.zip`) for the dip-monitor's data-source notes.

## Sources
alpaca.markets, interactivebrokers (ib_async on GitHub), fred.stlouisfed.org, tiingo.com, polygon.io,
alphavantage.co, finnhub.io, autotradelab.com (backtester comparison), nb-data.com (best data APIs 2026).
