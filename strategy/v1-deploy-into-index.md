# Strategy v1 — Deploy into the index (entry timing)

> **Status: superseded by [v3](v3-bubble-aware-all-weather.md).** Educational analysis, not advice.

## The question

We have $1M cash and want broad-market exposure (VOO / QQQ / VXUS). **How should we time the
entry** — drop it all in at once (lump sum), spread it evenly (DCA), or hold some back to
**buy the dips**? Is there a deployment schedule that improves the outcome?

## What we tested

`backtests/backtest.py` + `backtests/quarterly_fan_chart.py` + `backtests/quarterly_starts_backtest.py`,
over 2020-01-01 → 2026-05-27, $1M split into three buckets:

| Bucket | Allocation | Deployment |
|--------|:---:|---|
| Foundation | 50% ($500K) | Lump-sum on day 1 |
| DCA | 30% ($300K) | Equal weekly instalments over 18 months |
| Dip Reserve | 20% ($200K) | Tiered tranches triggered by drawdown from the 52-week high |

Dip-reserve tiers (VOO/VXUS baseline; QQQ thresholds ×1.4 for its higher vol): Tier 1 at
−7/−8.5/−10% (20% of reserve), Tier 2 at −12/−14/−16% (30%), Tier 3 at −20/−25/−30% (50%),
each with a time-based catch-all. Full write-up: [`../report/writeups/dip-tranche-strategy-backtest.md`](../report/writeups/dip-tranche-strategy-backtest.md).

## Result

| Symbol | Dip-tranche CAGR | Lump-sum CAGR | DCA CAGR | Strategy max DD |
|--------|:---:|:---:|:---:|:---:|
| VOO | 15.1% | **15.8%** | 14.6% | −22.5% |
| QQQ | 19.6% | **21.7%** | 17.6% | −31.2% |
| VXUS | **10.6%** | 10.2% | 10.3% | −26.6% |

- **Lump-sum won on CAGR for VOO and QQQ** — markets rise more often than they fall, so cash held
  back for dips is mostly cash drag. This is the well-documented "lump sum beats DCA ~⅔ of the time."
- **Dip-tranches only beat both benchmarks in VXUS**, where slower, choppier international recoveries
  reward tiered entry. The structure shines when the asset *grinds sideways/down*, not when it rips.
- The dip structure **did reduce drawdown** modestly and made the entry psychologically easier.

## Why it was superseded

v1 answered *when to buy* but quietly assumed the answers to two bigger questions were "the index"
and "it'll be fine":

1. **It never questioned *what* to hold.** 2020-2026 was a near-uninterrupted bull dominated by
   mega-cap tech — exactly the concentration we're now worried about. A 2020-2026 backtest *can't*
   tell you how to survive a bubble burst; there wasn't one in the window.
2. **It never priced the left tail.** Entry timing changes the outcome by a percent or two; a
   −55% (S&P) or −83% (QQQ) drawdown changes it by half. Optimizing the small lever while ignoring
   the big one is the wrong problem.

**What survived into v3:** the *dip-reserve mechanic* is genuinely useful — it's kept as the cash-
deployment layer (the `dip-tranches-strategy` skill), but now it feeds a **de-concentrated, all-weather
target mix** rather than 100% index, and it's sized as dry powder *for* a crash rather than a timing trick.

## Provenance
`backtests/backtest.py`, `backtests/quarterly_fan_chart.py`, `backtests/quarterly_starts_backtest.py`,
`backtests/results/` summaries, and `report/writeups/dip-tranche-strategy-backtest.md`.
