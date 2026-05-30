# 04 — Asset-Allocation Frameworks, Side by Side

*The canonical "lazy" / all-weather portfolios as concrete ETF recipes, with the
historical shape from research + our backtest (note 03). Educational, not advice.*

## Quick comparison

| Portfolio | Recipe (equal unless noted) | Long-run CAGR* | Max DD* | Best at | Weak spot |
|-----------|------------------------------|:----:|:----:|---------|-----------|
| **100% S&P 500** | VOO/VTI | ~10% (1926+) | −50% to −55% | bull markets | bursting bubbles, lost decades |
| **60/40** | 60 VTI / 40 BND(or TLT) | ~8% | −30% | growth shocks (bonds help) | inflation (2022) |
| **Permanent Portfolio** | 25 VTI / 25 TLT / 25 GLD / 25 SGOV | ~7-8.5% | **~−16%** | every regime a little | strong equity bulls; Oct 2022 |
| **Golden Butterfly** | 20 VTI / 20 AVUV / 20 TLT / 20 SGOV / 20 GLD | ~9-10% | ~−18% | prosperity tilt + protection | inflation, equity bulls |
| **All-Weather (Dalio retail)** | 30 VTI / 40 TLT / 15 IEF / 7.5 GLD / 7.5 DBC | ~7-8% | ~−20% | growth-led drawdowns | 2022 (duration heavy) |
| **Ivy / GTAA (Faber)** | 5-asset + 200d MA timing | equity-like, bond-like DD | ~−15% | protracted crashes | whipsaw, fast V-shapes |
| **Dual Momentum (GEM)** | switch SPY/ex-US/bonds monthly | ~10%+ | ~−20-34% | trending markets | choppy markets, 2020 V-shape |

*Numbers blend cited research (portfoliocharts.com, optimizedportfolio.com) and our 2000-2026 backtest.
They vary by window and data source — treat as directional.

## The four macro regimes (why all-weather works)

Dalio's framing: you never know which is coming, so hold something that wins in each.

| Regime | Wins | Examples |
|--------|------|----------|
| Growth ↑ (prosperity) | stocks, small-cap value, credit | 1982-2000, 2009-2021 |
| Growth ↓ (recession/deflation) | long Treasuries, cash | 2008, Mar 2020 |
| Inflation ↑ | gold, commodities, TIPS, real assets | 1970s, 2022 |
| Inflation ↓ / tight money | cash, T-bills | 1981, 2022 cash leg |

The S&P 500 is a concentrated bet on **one** regime (growth ↑). At CAPE ~41 with ~40% AI concentration,
that bet is more lopsided than usual (note 01).

## Concrete ETF building blocks

| Sleeve | Tickers | Role |
|--------|---------|------|
| US large cap | VOO, VTI, SPLG/SPYM, IVV | core growth |
| US small-cap value | AVUV, VBR, VISVX | prosperity tilt, value premium |
| International | VXUS, VEA, VWO | de-concentrate from US/AI |
| Long Treasuries | TLT, VGLT | deflation/recession hedge |
| Intermediate Treasuries | IEF, VGIT | milder duration |
| Short bonds / cash | SGOV, BIL, USFR, SHY | dry powder, tight-money hedge |
| Gold | GLD, IAU, GLDM | inflation/debasement hedge |
| Commodities | PDBC, DBC, COMT | inflation hedge (broader than gold) |
| Trend / managed futures | DBMF, KMLM, CTA, RSST | crisis alpha |
| Min-vol / quality equity | USMV, SPLV, QUAL | cushioned beta |
| Covered-call income | JEPI, JEPQ, SPYI | income, lower drawdown |
| Tail / anti-beta | TAIL, SWAN, BTAL | convex fast-crash hedge |
| TIPS | SCHP, VTIP, LTPZ | explicit inflation protection |

## How to choose among them

- **Want simplicity + low drawdown, accept lagging bulls:** Permanent Portfolio or Golden Butterfly.
- **Want more upside, still diversified:** Golden Butterfly or a 60/40 *plus* gold + trend.
- **Worried specifically about an AI/concentration unwind:** de-concentrate the equity sleeve
  (equal-weight RSP, international VXUS, value AVUV) and add trend (DBMF) — see note 08.
- **Want a rules-based "get out" mechanism:** overlay the 200-day MA rule (Faber GTAA) or Dual Momentum
  on the equity sleeve, accepting whipsaw risk.

## Key caveat for *today's* starting point
Permanent Portfolio / All-Weather historically leaned on a **40-year bond bull** and gold's run.
From 2026's lower-yield, high-equity-valuation base, **don't assume bonds repeat their 2000-2008 hedge
magnitude.** This is why note 08 emphasizes *trend-following + gold + de-concentrated equity + T-bills*
over a duration-heavy classic risk-parity stack.

## Sources
portfoliocharts.com (Permanent, Golden Butterfly), optimizedportfolio.com (all portfolios, RPAR, JEPI),
lazyportfolioetf.com, mebfaber.com (GTAA/Ivy timing model), bridgewater All-Weather public writeups,
and `backtests/crash_protection_backtest.py` in this repo.
