---
name: analyse-sellside
description: "Analyst lens for sell-side and independent equity research — Wall Street analyst consensus ratings (Strong Buy...Strong Sell), mean/high/low price targets, implied upside, rating dispersion, and rating momentum (net upgrades/downgrades), plus independent research (Morningstar fair value/moat/star rating, CFRA, Zacks Rank). Grounded ONLY via web_fetch of public pages — Yahoo Finance analyst tab, TipRanks, MarketBeat, Zacks, Finviz, StockAnalysis.com, Nasdaq analyst-research, WSJ research-ratings, Morningstar public quote pages. No terminal, no paid API, no TradingView, no yfinance. Use when asked \"what do analysts think of X\", \"what's the price target on X\", \"is X rated buy or sell\", \"any upgrades or downgrades on X\", \"Morningstar fair value / moat on X\", \"analyst consensus\", \"sell-side view on X\", \"is Wall Street bullish on this stock\". Structurally biased toward Buy/Hold — the headline consensus rating is a weak-to-contrarian standalone signal; dispersion, revision momentum, and the independent-research gap carry the real information. Educational, not advice."
license: MIT
compatibility: opencode
metadata:
  audience: equity-allocators
  domain: sell-side-equity-research
  role: analyst-rating-and-price-target-lens
  source: "Public analyst-rating aggregators (Yahoo Finance, TipRanks, MarketBeat, Zacks, Finviz, StockAnalysis.com, Nasdaq, WSJ, Morningstar) — web_fetch only, no terminal/paid API (distilled 2026-07)"
---

# Analyst: Sell-Side & Independent Research Lens

Read what the Street and the independent research houses have actually published on a ticker — consensus
rating, price targets, dispersion, and rating momentum — and turn it into one structured verdict. This is a
**seat**, not a conductor: it fetches, classifies, and returns one block. It does not synthesize across
seats (that is the CIO/chair's job) and it does not trade.

> Educational only. A sell-side rating is not a forecast and this skill's output is not a recommendation.

## Hard constraint — web_fetch only

This seat runs as a subagent with **no TradingView and no yfinance**. Every number in the output must trace
to a page `web_fetch`ed **this run**. If a runtime cache/artifact is ever produced, it goes under
`.cache/analyse-sellside/` — never inside this skill directory.

## How to read a sell-side report (methodology)

**What a rating actually means.** "Buy" / "Overweight" / "Outperform" from an investment bank means the
analyst expects the stock to outperform their coverage universe or benchmark over ~12 months — it is a
relative call, not a promise, and it says nothing about entry price or timing. The **price target (PT)** is
the analyst's 12-month fair-value estimate, usually a DCF or multiple applied to a forward estimate — treat
it as a point estimate with wide, usually unstated, error bars, not a guarantee.

**Sell-side is structurally biased long.** Across the Street, "Sell" ratings are rare — on most large-cap
names the distribution runs roughly Buy > Hold >> Sell, with Sell often in the low single digits as a
percentage of all ratings outstanding. This is a well-documented structural bias, not noise: issuing a
public Sell risks damaging the bank's access to management (earnings calls, roadshows, future underwriting
mandates), so analysts more often quietly stop covering a name or downgrade to Hold than publish Sell. **A
rare Sell rating from a sell-side firm is informationally louder than a Buy from the same firm** — read it
that way.

**Sell-side vs. independent research — read them differently.**
| | Sell-side (Goldman, Morgan Stanley, BofA, JPMorgan, Bernstein, UBS, Barclays, Wells Fargo, Jefferies…) | Independent (Morningstar, CFRA, Zacks) |
|---|---|---|
| Revenue model | Trading, banking, underwriting relationships with the covered company | Subscription research sold to investors — no banking relationship with the issuer |
| Conflict | Structural pressure toward Buy/Hold | Free to publish Sell/Hold without relationship risk |
| Output shape | Rating + PT, 12-month relative | Morningstar: fair value estimate + moat (Wide/Narrow/None) + uncertainty + star rating (1-5, contrarian: 5-star = most undervalued); Zacks: quant Rank (1 Strong Buy - 5 Strong Sell), driven by earnings-estimate revisions; CFRA: quant + fundamental blended score |
| Use here | Consensus level, dispersion, momentum | Cross-check the sell-side rating against a non-conflicted fair-value view |

**Price target vs. thesis.** A PT without the thesis behind it is close to useless — the same $250 PT can
sit on a bull case (multiple expansion) or a bear-adjacent case (target is barely above the current price,
i.e. de-facto Hold dressed as Buy). Always compute **implied upside/downside vs. the current price**, and
where the fetched page states the thesis driver (margin expansion, new product, multiple re-rating), report
it in one line.

**Dispersion and momentum carry more signal than the consensus level.** Two stocks can both show "Buy,
consensus PT $200" — one with 25 analysts clustered $190-$210 (tight, high agreement) and one with 25
analysts spread $130-$300 (wide, genuine disagreement about the outcome). The first is a low-information
consensus call; the second says the Street itself doesn't know what this company is worth — that dispersion
is itself the finding. Likewise, a stock quietly accumulating **net upgrades** over the last 60-90 days
(rating momentum) is a different, more current signal than the static "17 Buy, 5 Hold, 1 Sell" snapshot,
which may be stale by months.

## The honest base-rate / skeptic note (state this every run)

**Consensus rating LEVEL is a weak-to-contrarian standalone predictor.** A "Strong Buy" consensus is at
least as often a symptom of a crowded trade as it is an edge — by the time coverage is near-unanimously
bullish, the marginal informed buyer has often already bought, and the stock's expectations bar is high
(same crowding failure mode as `analyse-smartmoney`'s "CROWDED" read and `analyse-sentiment`'s
extreme-greed band). Two well-known findings back this up, stated at the level of confidence memory
supports (re-verify before quoting a precise number):
- **Downgrades carry more price-moving information than upgrades** (Womack, *Journal of Finance*, 1996) —
  because downgrades are the rarer, costlier-to-issue action given the structural long bias above, a
  downgrade is a stronger signal than an upgrade of equal magnitude.
- **Aggregate analyst recommendation levels have historically shown only weak standalone predictive power
  once transaction costs are applied** — the academic "profit from the prophets" literature (Barber,
  Lehavy, McNichols & Trueman and related work) finds most of the exploitable signal sits in the *change*
  (revisions, upgrade/downgrade flow) rather than the static rating level.

**Therefore weight in this order:** (1) independent fair-value gap (Morningstar/CFRA, least conflicted),
(2) rating dispersion (wide = the Street itself disagrees, discount the consensus), (3) rating momentum
(net upgrades/downgrades over the trailing quarter), (4) the static consensus rating level — dead last,
context only. Never emit a BULLISH read on consensus level alone.

## Grounding procedure (do this in order; stop early once the signal is clear)

`{TICKER}` = the ticker under review. Reconcile conflicting numbers by **preferring the most recently
dated page** and reporting the range from the others as corroboration — never silently average across
sources.

1. **Yahoo Finance analyst page** — `https://finance.yahoo.com/quote/{TICKER}/analysis`
   Gives: mean/high/low PT, number of analysts, recommendation rating (Yahoo's scale runs 1.0 = Strong Buy
   to 5.0 = Strong Sell — **lower number is more bullish**, do not invert this). This is the primary source
   for `pt_mean`, `pt_high`, `pt_low`, `num_analysts`.
2. **StockAnalysis.com forecast page** — `https://stockanalysis.com/stocks/{TICKER}/forecast/`
   Cross-check PT and consensus; often states implied upside % directly and a rating-count breakdown.
3. **TipRanks forecast page** — `https://www.tipranks.com/stocks/{TICKER}/forecast`
   Gives Buy/Hold/Sell analyst-count breakdown and, for the visible top analysts, named firm + rating + PT
   + date — this is the primary source for any per-firm citation.
4. **MarketBeat price-target page** — `https://www.marketbeat.com/stocks/{EXCHANGE}/{TICKER}/price-target/`
   Gives a dated ratings-history table (firm, action [upgrade/downgrade/initiate/reiterate], from-rating,
   to-rating, date) — the primary source for `rating_momentum`. Count net upgrades minus downgrades over
   the trailing ~90 days from this table.
5. **Nasdaq analyst research page** — `https://www.nasdaq.com/market-activity/stocks/{TICKER}/analyst-research`
   Secondary corroboration for the upgrade/downgrade table if MarketBeat is unavailable or thin.
6. **Zacks quote page** — `https://www.zacks.com/stock/quote/{TICKER}`
   Gives the Zacks Rank (1 Strong Buy - 5 Strong Sell, quant/earnings-revision-driven — a genuinely
   independent methodology, not a repackaged sell-side average). Record as part of `independent_view`.
7. **Finviz quote page** — `https://finviz.com/quote.ashx?t={TICKER}`
   Fast cross-check: single consensus "Recom" score (1-5) and a single "Target Price" number. Use only to
   sanity-check step 1-2, not as a primary source if it conflicts.
8. **Morningstar public quote page** — `https://www.morningstar.com/stocks/{EXCHANGE}/{TICKER}/quote`
   Gives star rating (1-5, contrarian scale — 5-star means most undervalued vs. Morningstar's fair value),
   fair value estimate, moat (Wide/Narrow/None), uncertainty rating. This is the primary source for
   `independent_view`. If the page is paywalled/blocked, mark `independent_view: null` — do not guess a
   Morningstar rating from memory.
9. **WSJ Research Ratings page** (optional, if reachable) —
   `https://www.wsj.com/market-data/quotes/{TICKER}/research-ratings`
   Sometimes gives a rating distribution and a few individual firm rating/PT/date rows — additional
   per-firm corroboration only.

**Stop early** once ≥2 independent pages (step 1 or 2, plus one of 3/4) give a consistent consensus + PT
picture and step 4 or 5 gives a usable momentum read. Always attempt step 8 (Morningstar) — the independent
view is the highest-weighted input per the base-rate note above.

## Anti-hallucination rule (non-negotiable)

Name a firm, an individual analyst, a specific rating, a specific price target, or a specific date **only
if it appears verbatim on a page `web_fetch`ed this run**. Never:
- State "Goldman Sachs has a Buy rating and $250 PT" unless a fetched page literally shows that firm, that
  rating, and that number together.
- Fill in a plausible-sounding aggregate (mean PT, analyst count) from training memory when a fetch failed.
- Average or interpolate between sources to produce a cleaner number than either source actually stated.

If fewer than 2 real fetched sources agree on the aggregate consensus, or all fetch attempts fail: output
`read: INSUFFICIENT_DATA` and every unresolved field as `null` — do not guess.

## Output contract

```json
{
  "seat": "sellside",
  "ticker": "string",
  "as_of": "YYYY-MM-DD",
  "read": "BULLISH | NEUTRAL | BEARISH | INSUFFICIENT_DATA",
  "consensus_rating": "Strong Buy | Buy | Hold | Sell | Strong Sell | null",
  "num_analysts": "int | null",
  "pt_mean": "number | null",
  "pt_high": "number | null",
  "pt_low": "number | null",
  "current_price": "number | null",
  "implied_upside_pct": "number | null",
  "dispersion": "TIGHT | WIDE | UNKNOWN",
  "rating_momentum": "UPGRADING | STABLE | DOWNGRADING | UNKNOWN",
  "momentum_detail": "string — e.g. '3 upgrades vs 1 downgrade, trailing 90d (MarketBeat)'",
  "independent_view": {
    "source": "Morningstar | Zacks | CFRA | null",
    "star_rating": "int 1-5 | null",
    "fair_value": "number | null",
    "moat": "Wide | Narrow | None | null",
    "zacks_rank": "int 1-5 | null"
  },
  "firm_ratings": [
    {"firm": "string", "rating": "string", "pt": "number", "date": "YYYY-MM-DD", "url": "https://..."}
  ],
  "conviction": "HIGH | MED | LOW",
  "disagreement_with_price": "string — one line: does the aggregate PT + independent view agree with, or diverge from, the current price and each other",
  "sources": ["https://... (every URL actually fetched)"],
  "notes": "string — caveats, INSUFFICIENT_DATA fields, crowding/base-rate flag if consensus is near-unanimous"
}
```

**`read` assignment rule:**
- `BULLISH` requires **at least two** of: (a) independent view (Morningstar/Zacks) agrees directionally,
  (b) dispersion TIGHT, (c) rating_momentum UPGRADING. A lone "Strong Buy" consensus with WIDE dispersion
  and no independent confirmation is **NEUTRAL**, not BULLISH — that is the crowding trap this skill exists
  to catch.
- `BEARISH` mirrors the above: independent view bearish/overvalued AND (WIDE dispersion or DOWNGRADING
  momentum).
- `NEUTRAL` otherwise, including a genuinely mixed or single-signal case.
- `INSUFFICIENT_DATA` per the anti-hallucination rule above.

**Conviction rule:** HIGH = independent view + dispersion + momentum all align; MED = 2 of 3 align; LOW = 1
of 3 or the read leans only on the raw consensus level.

## Worked example

<example>
User: "What's the sell-side and independent read on ORCL?"

<thinking>
Fetch Yahoo analyst page, StockAnalysis.com, TipRanks, MarketBeat, Zacks, Morningstar in order. Illustrative
readings below — re-pull all live pages before using this for anything real.
</thinking>

Fetched:
- `https://finance.yahoo.com/quote/ORCL/analysis` (2026-07-06) — mean PT $210, high $260, low $165, 32
  analysts, recommendation 2.1 (≈ "Buy" on Yahoo's 1-5 scale).
- `https://stockanalysis.com/stocks/ORCL/forecast/` (2026-07-05) — consensus "Buy", PT range corroborates
  Yahoo within a few dollars, implied upside ~9% vs. current price $193.
- `https://www.tipranks.com/stocks/ORCL/forecast` (2026-07-04) — 18 Buy / 11 Hold / 3 Sell among visible
  analysts; named firms with recent dated ratings include one bank at "Outperform, $230 PT (2026-06-28)".
- `https://www.marketbeat.com/stocks/NYSE/ORCL/price-target/` (2026-07-03) — ratings-history table shows 2
  upgrades and 3 downgrades in the trailing 90 days → net **DOWNGRADING** momentum.
- `https://www.zacks.com/stock/quote/ORCL` (2026-07-06) — Zacks Rank 3 (Hold), independent quant read
  weaker than the sell-side consensus.
- `https://www.morningstar.com/stocks/xnys/orcl/quote` (2026-07-02) — 3-star rating (fairly valued), Wide
  moat, fair value estimate $195 — essentially in line with the current price, not undervalued.

Reconciliation: consensus rating and dispersion look bullish-ish (18 Buy dominant, PT range $165-$260 is
wide relative to mean → WIDE), but **both independent sources (Zacks Hold-3, Morningstar fair-value ≈
current price) disagree with the sell-side lean, and momentum is net DOWNGRADING**. Two of three
higher-weighted inputs (independent view, momentum) do not confirm — read stays NEUTRAL despite a
Buy-heavy headline count. This is exactly the crowding pattern the base-rate note warns about.

```json
{
  "seat": "sellside",
  "ticker": "ORCL",
  "as_of": "2026-07-06",
  "read": "NEUTRAL",
  "consensus_rating": "Buy",
  "num_analysts": 32,
  "pt_mean": 210,
  "pt_high": 260,
  "pt_low": 165,
  "current_price": 193,
  "implied_upside_pct": 8.8,
  "dispersion": "WIDE",
  "rating_momentum": "DOWNGRADING",
  "momentum_detail": "2 upgrades vs 3 downgrades, trailing 90d (MarketBeat ratings-history table)",
  "independent_view": {
    "source": "Morningstar",
    "star_rating": 3,
    "fair_value": 195,
    "moat": "Wide",
    "zacks_rank": 3
  },
  "firm_ratings": [
    {"firm": "unnamed bank (TipRanks-listed)", "rating": "Outperform", "pt": 230, "date": "2026-06-28", "url": "https://www.tipranks.com/stocks/ORCL/forecast"}
  ],
  "conviction": "MED",
  "disagreement_with_price": "Sell-side headline count leans Buy (18/11/3), but both independent sources price it near fair value and momentum is net downgrading — headline rating is not confirmed by the higher-weighted inputs.",
  "sources": [
    "https://finance.yahoo.com/quote/ORCL/analysis",
    "https://stockanalysis.com/stocks/ORCL/forecast/",
    "https://www.tipranks.com/stocks/ORCL/forecast",
    "https://www.marketbeat.com/stocks/NYSE/ORCL/price-target/",
    "https://www.zacks.com/stock/quote/ORCL",
    "https://www.morningstar.com/stocks/xnys/orcl/quote"
  ],
  "notes": "Wide dispersion + net downgrading momentum + independent fair-value ≈ current price all argue against reading the Buy-heavy headline count as bullish. Re-pull before acting; all figures illustrative-dated 2026-07."
}
```
</example>

## SOURCES discipline

Every material number in the output (`pt_mean`, `consensus_rating`, `rating_momentum`, `independent_view`,
any `firm_ratings` entry) must be traceable to an entry in `sources`. Format inline citations the same way
as the other `analyse-*` seats: `[Tn] https://exact-url (YYYY-MM-DD) — "verbatim figure or quote"`.

- **Never** write a source name alone ("per TipRanks…") without the fetched URL.
- **Never** state a per-firm rating/PT without a URL + date from a page that actually names that firm.
- **If a fetch fails**, log it as `[FETCH FAILED: https://...]` and do not count it toward the minimum.
- **If fewer than 2 real sources** corroborate the aggregate consensus: `read: INSUFFICIENT_DATA`, all
  unresolved fields `null`, and say so plainly in `notes` — do not guess.
- Any runtime artifact this skill produces (cached fetch results, run logs) belongs under
  `.cache/analyse-sellside/`, never inside the skill directory.

## Done when

The analysis (1) fetched the aggregate consensus + PT from **at least two independent aggregator pages**
(Yahoo/StockAnalysis.com/TipRanks), (2) computed `implied_upside_pct` against a stated current price,
(3) classified **dispersion** (TIGHT/WIDE) from the high/low PT spread, (4) derived **rating_momentum** from
a dated upgrade/downgrade table (MarketBeat or Nasdaq), (5) attempted the **independent view**
(Morningstar/Zacks) and recorded it or explicitly `null`, (6) named any per-firm rating only where a fetched
page names that firm, (7) applied the `read` assignment rule — never BULLISH on consensus level alone, and
(8) emitted the output contract with every claim traceable to a listed source.
</content>
