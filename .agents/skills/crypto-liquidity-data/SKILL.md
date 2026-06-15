---
name: crypto-liquidity-data
description: Data-only gather seat — pull global + US liquidity-flow data that drives risk assets/BTC. Use when a workflow/agent needs Howell global-liquidity direction, Fed balance sheet, RRP, TGA, global M2, DXY, and 2y/10y yields as raw inputs (no buy/sell opinion). Triggers — "pull liquidity data", "net Fed liquidity", "global M2 / DXY", crypto-panel Gather phase.
license: MIT
compatibility: opencode
metadata:
  role: data-source-reference
  domain: macro-liquidity-data
---

# Liquidity-flows data (gather seat)

DATA ONLY. No opinion on what to buy. Numbers with `as-of` + `source`; `[UNAVAILABLE]` when not fetchable — **never fabricate**.

## Pull these
- **Global liquidity (Howell / CrossBorder Capital):** current level + DIRECTION (expanding/contracting) + cycle timing. Ground on Howell's own framing when sources conflict (retail proxies often say "expanding" when Howell says the cycle has rolled over).
- **US net liquidity:** Fed balance sheet (WALCL) trend, RRP level/trend, TGA level/trend, QT pace.
- **Broad money:** US M2 YoY + MoM direction; global M2 in USD direction if available.
- **Dollar:** DXY level + short-term trend.
- **Rates:** US 2y, 10y, the 2s10s curve.

## Sources (one fetch at a time)
- Fed B/S / RRP / TGA / M2 / yields: FRED (`WALCL`, `RRPONTSYD`, `WTREGEN`, `M2SL`, `DGS2`, `DGS10`) via WebFetch.
- Global liquidity: WebSearch for the latest Howell / CrossBorder Capital commentary; quote his direction + cycle call.
- DXY: Yahoo/TradingEconomics.

## Output contract
`{metric, value, asof, source}` per item + a one-line `summary` stating the **marginal direction** of liquidity (tightening/easing) as a fact, plus any stock-vs-flow tension (e.g. M2 stock still growing while the flow rolls over). Note conflicts; don't resolve them silently.

## Done when
Each item is a sourced number/direction with as-of or an explicit `[UNAVAILABLE]`.
