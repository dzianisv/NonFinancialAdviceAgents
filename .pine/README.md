# .pine/ — TradingView alert mirrors of the Watchlist

Auto-generated Pine v6 indicators, one per symbol, that mirror the **Watchlist**
price/indicator triggers (Google Sheet `gid=143777201`) onto TradingView as a
reliable push-notification channel.

**Canonical trigger store is the mkt daemon** (`https://mkt.agentlabs.cc/alerts`),
not TradingView. These Pine files exist because mkt email delivery (Brevo) is
unreliable and the mkt price engine has had outages — TradingView push is a
dependable secondary surface. When the Watchlist changes, regenerate these files.

Each file defines `alertcondition()` calls. Every one compiles clean via
TradingView `pine_check` (0 errors, 0 warnings), verified 2026-07-21.

## Trigger map (as of 2026-07-21)

| File | Symbol | Conditions | mkt daemon job |
|---|---|---|---|
| GIS.pine | GIS | `< 31.50` | mirrored |
| EPAM.pine | EPAM | `< 76` | mirrored |
| ESTC.pine | ESTC | `< 55` | mirrored |
| DLB.pine | DLB | `< 48` | mirrored |
| CRCL.pine | CRCL | `< 60` | mirrored |
| AAPL.pine | AAPL | `< 274.58` | mirrored |
| AVGO.pine | AVGO | `< 341` | mirrored |
| GOOG.pine | GOOG | `< 320` (add), `> 380` (trim) | mirrored |
| MU.pine | MU | `< 486.58` | mirrored |
| SNDK.pine | SNDK | `< 788.13` | mirrored |
| NVDA.pine | NVDA | `< 165.02` | mirrored |
| SITC.pine | SITC | `< 3.90` | mirrored |
| MSFT.pine | MSFT | `> 410` | da9e88f9 |
| ORCL.pine | ORCL | `> 142` | 84e6062b |
| NBIS.pine | NBIS | reclaim 50DMA (`ta.crossover(close, sma50)`) | mirrored |
| BTC_USD.pine | BTC-USD | `< 57000` (Reserve #1), `< 50000` (accum), `< 48000` (Reserve #2), `> 80000` (fold), 14-RSI `< 30` | 0bd8b519 / c080d66c / 8ab93ee3 (+existing) |

## How to arm on TradingView

The MCP `alert_create` tool drives the *native price-alert* dialog and was
failing (`dom_fallback`, `price_set:false`) on 2026-07-21; the shared CDP chart
was also being externally re-symboled to ETHUSDT mid-session. Arm manually or
re-run when the chart session is exclusive:

1. Open the symbol's chart.
2. Pine editor → paste the matching `.pine` file → **Add to chart**.
3. Right-click chart → **Add alert** → Condition = the indicator →
   pick the `alertcondition` title → Once Per Bar Close → Create.
4. TradingView push/app notification is the reliable delivery channel.

Regenerate after any Watchlist edit so this mirror never drifts from the sheet.
