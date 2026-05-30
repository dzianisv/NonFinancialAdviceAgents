---
name: fundamental-analysis
description: The security-analyst agent for a systematic fund — defines exactly what data it reads (prices, yfinance fundamentals, SEC EDGAR financials, FRED macro, Morningstar fair-value/moat where accessible), what it screens on (value, quality, FCF yield, moat, momentum), and the hard rule that NO signal or screen may trade until it beats its benchmark in an out-of-sample, cost-aware backtest. Use this whenever the user asks how the analyst works, what data/sources it uses, whether it should pick individual undervalued stocks (e.g., via Morningstar fair value / economic moat / star ratings), whether it uses fundamentals like P/E, P/B, EV/EBIT, ROE, ROIC, FCF, Piotroski F-score, Magic Formula, or whether strategies are backtested before deployment. Trigger when the user questions whether the design is "just design" or wants the analyst's concrete mechanics. Educational, not advice; be honest that bottom-up stock-picking rarely beats a cheap index net of costs.
license: MIT
compatibility: opencode
metadata:
  audience: systematic-investors
  domain: equity-research
  role: research-analyst
---

# Fundamental Analysis (the Analyst Agent)

This skill makes the analyst **concrete**: its inputs, sources, screens, outputs, and the
non-negotiable rule that gates everything — **a signal does not trade until a backtest says it
should.** It also encodes an honest, evidence-based verdict on what the analyst is *for*.

## The verdict that shapes everything (read first)

We backtested the **investable versions** of the major stock-selection methods vs SPY over each
ETF's full live history (`backtests/fundamental_screens_backtest.py`):

| Methodology (ETF) | CAGR vs SPY | Beat SPY? | Higher Sharpe? |
|---|---|:--:|:--:|
| **Morningstar wide-moat + fair value (MOAT)** | 13.5% vs 14.7% | **no** | no |
| FCF yield / cash cows (COWZ) | 12.8% vs 15.4% | no | no |
| Pure value (RPV) | 9.2% vs 11.2% | no | no |
| Value factor (VLUE) | 13.7% vs 14.8% | no | no |
| Quality (SPHQ / QUAL) | ~10-13.6% | no | no |
| **Momentum (MTUM)** | 16.3% vs 14.8% | **yes** | ~tie |
| Dividend / min-vol (SCHD/NOBL/USMV) | lagged | no | no |

**Only 1 of 10 (momentum) beat SPY on return; 0 of 10 beat it on Sharpe — including the ETF that
literally implements Morningstar's stock picking.** This is consistent with SPIVA (most active
selection lags a cheap index, especially in a mega-cap-led bull).

**Therefore the analyst's job is NOT "use Morningstar to find undervalued stocks that beat the
market."** That is a low-base-rate bet. The analyst has three jobs where it *does* add value:

1. **Pick the defensive equity sleeve** (the screens cut 2022 drawdowns ~in half: COWZ −8%, RPV −11%,
   SCHD −15%, USMV −17% vs SPY −24.5%) — implemented as **cheap ETFs**, not a hand-rolled stock book.
2. **Provide valuation/earnings context** to the regime + PM agents (CAPE, concentration, credit,
   earnings revisions, sector breadth).
3. **Validate every proposed signal** through the backtest gate below.

## What the analyst reads (data sources)

| Source | What it provides | Cost | Caveat |
|--------|------------------|------|--------|
| **yfinance** | prices, `.info`/`.financials`/`.balance_sheet` fundamentals (P/E, P/B, ROE, margins, debt, FCF) | free | **point-in-time UNSAFE** — gives *today's* fundamentals; do NOT backtest stock screens on it (look-ahead) |
| **SEC EDGAR** (companyfacts API) | filed financial statements, point-in-time, free | free | parsing effort; US only |
| **FRED** | macro: CAPE inputs, yield curve, HY OAS, rates | free | the regime/context backbone |
| **Morningstar** (fair value, moat, star rating) | the actual moat + fair-value ratings | Direct/API is **institutional, expensive**; morningstar.com retail is manual, not a clean API | hard to get programmatically at retail scale; **MOAT ETF is the investable proxy** |
| **Sharadar / SimFin / Financial Modeling Prep / Tiingo** | **point-in-time, survivorship-safe** fundamentals | ~$10-150/mo | the ONLY correct source for backtesting fundamental screens |
| Tiingo / Polygon | clean prices for live signals | ~$10+/mo | cross-check vs yfinance before trading |

**Rule:** use yfinance/SEC for *current* screening and context; use a **point-in-time** vendor
(Sharadar/SimFin) the moment you backtest any fundamental screen — otherwise survivorship +
look-ahead bias will manufacture fake alpha (this is exactly the trap the repo's old price-proxy
"Morningstar" backtest fell into — it lost to VOO by −4.3%/yr).

## The screens the analyst can compute (if/when justified)
- **Value:** earnings yield (EBIT/EV), P/B, P/E, P/FCF. **Magic Formula** (Greenblatt): rank by
  earnings yield + return on capital, buy top 20-30.
- **Quality:** ROE/ROIC, low debt, stable earnings, **Piotroski F-score** (9-point).
- **FCF yield** ("cash cows"), **shareholder yield** (buybacks + dividends).
- **Moat/fair value:** Morningstar-style (proxy via MOAT ETF unless you license the data).
- **Momentum:** 12-1 month total return (the one factor that beat SPY here).

## The backtest gate (the answer to "does it backtest or not?")
**YES — mandatorily.** No screen, factor, or signal is allowed to allocate capital until it:
1. Beats its **benchmark** (usually SPY/VOO or the sleeve it would replace) on **risk-adjusted**
   terms (Sharpe/Calmar), **net of costs and turnover**, over an **out-of-sample** window;
2. Uses **point-in-time, survivorship-safe** data;
3. Survives the **crisis windows** (2008/2020/2022) without an unacceptable drawdown;
4. Is robust to small parameter changes (no overfitting; deflate Sharpe for # of trials).

If it fails the gate → the default is the **cheap ETF** (e.g., USMV/QUAL/COWZ) or just the index.
"Stock-picking has to earn its place; the index is the bar."

## Outputs (contract)
```json
{
  "as_of": "2026-05-29",
  "defensive_sleeve_choice": {"ticker": "USMV", "reason": "min-vol ETF; -9% DD in 2023-26 vs SPY -19%; beats a hand-rolled screen net of cost"},
  "context": {"sp500_cape": 41.6, "top10_weight": 0.40, "hy_oas_bps": 320, "earnings_revisions": "flat"},
  "proposed_signals": [{"name": "magic_formula_top30", "status": "REJECTED", "reason": "did not clear backtest gate net of costs vs VOO"}],
  "stock_basket": null
}
```

## When the user *insists* on a stock-picking sleeve
Cap it small (≤10-15% of equity), require it to clear the backtest gate on point-in-time data, accept
single-name and tax/turnover costs, and benchmark it honestly against the ETF it replaces. Know the
base rate: most such sleeves lag the index. Size it as a satellite, never the core.

## Optional Morningstar overlay (manual, context-only)
If you already have legitimate Morningstar access (personal/Investor account), you may use moat +
fair-value ratings as **one manual context lens** — a quality/valuation sanity-check before a
discretionary buy — NOT as an automated signal or the core.
- **Why only context:** Morningstar's ratings are *public information*, so they are already in the
  price (semi-strong EMH; Bogle, Malkiel). The productized version of exactly this process (the MOAT
  ETF) **lagged SPY** (13.5% vs 14.7%) — consuming their conclusions adds no alpha.
- **Do NOT scrape/spoof their API** for the pipeline: it breaks their ToS, is brittle (stale/wrong
  data is the worst failure mode for a fund), and your account only exposes *today's* rating — there
  is **no point-in-time history**, so a Morningstar-driven screen can never clear the backtest gate.
- A DCF "fair value" is an uncertain *range*, not a precise number (Damodaran) — weight it accordingly.
- **Net:** optional manual gut-check on individual names; the default remains the cheap ETF, and the
  backtest gate still governs any capital.

## Hand-offs
Feeds the **defensive sleeve choice** + valuation context to **portfolio-construction** and
**regime-detection**; routes any candidate signal to the backtest harness before **risk-management**
ever sees it. Momentum signals overlap with **trend-following**.
