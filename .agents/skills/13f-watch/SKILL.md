---
name: 13f-watch
description: Use when watching recent 13F filings to PROPOSE new stock buy-candidates from what super-investors just bought — "scan recent 13F filings", "what did Burry/Buffett/Ackman just buy", "propose stocks from 13F", "13F watchlist", "run the 13F watcher", or on a schedule/cron. Finds NEW initiations + cross-fund conviction clusters, filters out puts/trims/exits, and DEDUPES against everything already recommended so the same ticker is never proposed twice. Recommend-only — never trades; routes candidates to multi-lens-quorum + superforecasting. Educational, not advice; 13F is a 45-day-lagged, long-only, US-equity snapshot.
license: MIT
compatibility: opencode
metadata:
  audience: trend-and-value-investors-following-institutional-flow
  domain: institutional-flow-watchlist
  role: 13f-buy-watcher-and-deduper
  source: "extends hedge-fund-13f-analysis with a watch cadence + dedup ledger (watch.py)"
---

# 13F Watch (propose new buys from recent filings, never repeat one)

Scan recent 13F filings for a roster of super-investors, surface what they **newly bought**, and propose
the **un-proposed** ones as buy-candidates. The point is a *standing watchlist that never repeats itself* —
every ticker is deduped against the ledger before it's proposed.

**REQUIRED SUB-SKILL: `hedge-fund-13f-analysis`** for the actual filing-reading (EDGAR, aggregators,
deltas, the puts caveat, the output contract). This skill adds the **watch cadence + dedup + propose**
loop on top.

## Recommend-only (hard rule)

This **proposes / notifies** — it **never trades** and never sizes a real order. Output is a candidate
list routed to the decision pipeline. Educational, not advice. (Matches the repo's notification-first /
human-signs-every-trade invariant.)

## The loop

```bash
W="python3 .agents/skills/13f-watch/watch.py"   # ledger at $THIRTEENF_LEDGER or ./13f/recommended.jsonl

$W roster                       # who we track (Burry/Buffett/Ackman/Klarman/Li Lu + any in 13f/roster.json)
```

1. **Pull recent filings** for each roster manager (`hedge-fund-13f-analysis` method: EDGAR
   `infotable.xml` first, aggregators to corroborate). Resolve any missing CIK via EDGAR company search;
   add it to `13f/roster.json`.
2. **Keep only BUYS.** New initiations (`new`) and meaningful adds (`add`). **Drop puts, trims, exits.**
   A 13F PUT is bearish — never propose it as a buy (Burry files them often; the roster flags him).
3. **Rank by conviction**, strongest first:
   - **Cross-fund cluster** — ≥2 roster managers initiating/holding the same name (highest signal).
   - **Position size** — large % of the manager's 13F AUM = high conviction.
   - **Fresh initiation** in a beaten-down name > a small top-up.
4. **DEDUPE — the core rule.** For each candidate: `W seen <TICKER>`.
   - exit 0 (`SEEN … SKIP`) → **already recommended, drop it.** Do not propose again.
   - exit 1 (`NEW`) → ok to propose.
5. **Propose the NEW ones** (recommend-only): ticker, manager(s), quarter, action, the WHY (1-2 lines),
   put-checked. Then **record each** so it's never repeated:
   `W record --ticker LULU --manager burry --quarter 2026Q1 --action new --reason "..." --source "EDGAR CIK 1649339"`
   (`record` also refuses a duplicate ticker — belt-and-suspenders on the dedup rule.)
6. **Hand off, don't decide.** Each fresh candidate → `multi-lens-quorum` (buy/size verdict) →
   `superforecasting` (where does it go by the next catalyst). This skill only *finds + dedupes*.
7. **Notify** the proposed list (with the skipped-as-seen count for transparency).

## Cadence

13F deadlines: ~**Feb 14 / May 15 / Aug 14 / Nov 14** (45 days after quarter-end); filings trickle in
during the ~6 weeks before. A **weekly** scan catches new filings without spamming; dedup makes re-runs
safe (already-proposed names just get skipped). Run heavier during filing windows, lighter otherwise.

## Common mistakes

| Mistake | Fix |
|---|---|
| Propose a PUT as a buy | Check the line type; puts are bearish — drop them (esp. Burry) |
| Re-propose a name from last quarter | `W seen` before every proposal; dedup by ticker |
| Treat 13F as a real-time signal | 45-day lag, long-only US equity snapshot — it's a *finder*, not a trigger |
| Count a trim/exit as a buy | Only `new`/`add` are buys |
| Skip the raw infotable | Aggregators drop positions — reconcile surprises against EDGAR (hedge-fund-13f-analysis rule) |
| Auto-buy / size an order | Recommend-only. Route to quorum + superforecasting; human signs. |

## Fit

A **WHICH-finder** (sibling to `trend-stock-research`) feeding the pipeline: **13f-watch finds →
`multi-lens-quorum` judges → `superforecasting` times.** Backed by `watch.py` (roster + dedup ledger).

> Educational, not advice. 13F is 45-day-lagged and long-only. Recommend-only — never trades.
