# Crypto workflow — eval loop summary

Test input: *"BTC reached 65k$ from the drop to 61k$. I hold 30% in COIN. I don't have BTC direct exposure. Should I buy it today?"*

| Iter | Commit | Score | Fix shipped |
|---|---|---|---|
| 1 | 1bdf1e3 | 76 | baseline (thin workflow, skills); narrative-news seat failed at runtime |
| 2 | 75c8183 | 88 | deterministic `news_fetch.py` (RSS→store→ranked query) — Strategy $100M BTC-buy catalyst now surfaced (source_count 4, PRICED_IN) |
| 3 | 7feaa8d | 91 | spot-BTC-ETF net-flow line REQUIRED — loud `[UNAVAILABLE]`, no silent category drop |
| 4 | 60416e7 | 94 | deterministic `onchain_fetch.py` (bitcoin-data.com + cache-on-ratelimit) — MVRV-Z/NUPL/Puell reliably present |

**Converged at 94/100 (PLATEAU).** All three workflow failure modes fixed. Remaining gaps (spot-ETF flows, COIN options IV) are external **paid/bot-blocked** data — handled honestly as loud `[UNAVAILABLE]` carried into the decision, not workflow defects. Further score gains require buying data, not improving the workflow.

Consistent decision across iters: **No buy today** — COIN is already ~2-3x levered crypto-beta (not under-exposed); WAIT for the Jun-17 FOMC; then a small valuation-tilted DCA **funded by trimming COIN → direct BTC** (buy+sell), inside the ~$0.5M risk sleeve, survivable to −50%. 3-3/4-2 DCA-vs-WAIT split + Hunt deflation dissent preserved each run.
