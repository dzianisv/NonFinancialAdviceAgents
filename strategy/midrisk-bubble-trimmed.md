# Mid-Risk Bubble-Trimmed Allocation (Track A)

> **Educational analysis, not financial advice.** Backtested 2007-01 → 2026-06 on liquid ETFs,
> monthly rebalance, 5 bps/trade turnover cost. Backtest: `backtests/midrisk_allocation_backtest.py`.
> Honest summary: `backtests/results/midrisk_allocation_summary.txt`.

## The question (GOAL Track A)
Can we build a **mid-risk** allocation with **S&P-like return** but **lower AI-bubble concentration**?

## The honest answer
**No free lunch — but a good trade exists.** 2007-2026 was a US mega-cap decade: the S&P's return
*came from* its concentration. Every way of cutting that concentration (equal-weight, ex-US, EM, real
assets) gave up return over this window. You **cannot** match S&P return with less concentration.

What you **can** get: **comparable risk-adjusted return with materially lower drawdown and far lower
bubble concentration, for a modest (~1.5%/yr) return give-up.**

## The menu (backtested, net of cost, 2007-2026)

| Allocation | CAGR | Vol | Sharpe | Max DD | Concentration |
|------------|------|-----|--------|--------|---------------|
| SPY (cap-weight benchmark) | 11.0% | 19.6% | 0.48 | −55.2% | top-10 ≈ 40%, AI-heavy |
| **RSP70 / GLD15 / IEF15 ← recommended** | **9.5%** | **14.6%** | **0.49** | **−41.7%** | equal-weight core (~3-4× lower top-10) |
| RSP100 (equal-weight US) | 9.7% | 20.9% | 0.41 | −59.9% | low, but no ballast |
| RSP80 / IEF20 | 8.8% | 16.2% | 0.42 | −48.7% | low |
| RSP60 / IEF40 (de-conc. 60/40) | 7.7% | 11.7% | 0.44 | −35.4% | low, defensive |
| 60/40 SPY/IEF (benchmark) | 8.4% | 11.0% | 0.51 | −32.2% | cap-weight (still concentrated) |
| Global Bubble-Trimmed (RSP/EFA/EEM/VNQ/GLD/IEF) | 7.6% | 14.9% | 0.37 | −43.4% | lowest — but ex-US/EM dragged hard |

## Recommendation: **RSP 70 / GLD 15 / IEF 15**, monthly rebalance
- **Sharpe 0.49** — matches SPY (0.48), within a hair of 60/40 (0.51).
- **Drawdown −42% vs SPY −55%** — 13 points less pain in the worst case.
- **De-concentrated**: equal-weight S&P (RSP) caps each name near ~0.2% vs ~7% for the top cap-weight
  name — structurally removes the Mag-7/AI single-point-of-failure risk that the whole mission is about.
- **GLD + IEF** = crisis ballast (gold + Treasuries) keeping it genuinely *mid*-risk.
- Return give-up vs SPY ≈ 1.5%/yr — the explicit, honest premium paid for the lower tail + lower concentration.

### Crisis windows (total return)
| Window | RSP70/GLD15/IEF15 | SPY | 60/40 |
|--------|-------------------|-----|-------|
| GFC 2007-10 → 2009-03 | −41% | −55% | −32% |
| COVID 2020-02 → 03 | −28% | −34% | −19% |
| 2022 bear | **−17%** | −25% | −21% |
| AI bull 2023-2024 | +27% | +58% | +33% |

The 2023-24 row is the cost in plain sight: in a concentrated AI bull you capture ~half the index. The
GFC/2022 rows are what you buy with it. This is the same bull-lag-for-tail-protection trade as v3, but
**less defensive / higher-return** — that is exactly what "mid-risk" means here.

## How it relates to v3
- **v3 Bubble-Aware All-Weather** = the more defensive $1M core (DD −27%, lags bulls more).
- **This (Track A)** = a *mid-risk* equity-forward option for the part of the book that wants to stay
  closer to equity returns while still removing the concentration risk. They are points on the same
  risk dial, not competitors.

## Deployment (for `hedge-fund-manager`)
Target weights `{RSP: .70, GLD: .15, IEF: .15}`, monthly (or quarterly + threshold-band) rebalance via
the `rebalancing` desk; risk veto via `risk-management`; dip reserve via `dip-tranches-strategy`.
Notification-first — produces the buy list; the human places the orders. The backtest script is the
durable eval: re-run it before changing the weights; a change that worsens Sharpe or drawdown is rejected.
