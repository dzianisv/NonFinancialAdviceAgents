---
name: prediction-market-odds
description: Use when a forecast or analysis needs the crowd's PRICED probability of a dated, observable outcome — Fed/FOMC rate decisions, CPI/inflation prints, elections, token unlocks, ETF rulings, "will BTC hold $X by [date]", "what are the odds of Y". Reference skill: how to pull live odds from Polymarket (Gamma API), Kalshi, and CME FedWatch, weight them by liquidity, and avoid the standard traps (slug-guessing, frozen/settled markets, thin or non-monotonic legs). Consumed by superforecasting and macro-panel as their market-anchor input. Educational, not advice; odds drift — re-pull before acting.
license: MIT
compatibility: opencode
metadata:
  audience: forecasters-and-analysts-anchoring-to-crowd-odds
  domain: prediction-market-data-access
  role: data-source-reference
  source: "verified live against Polymarket Gamma API 2026-06-11; Kalshi + CME FedWatch as corroborating venues"
---

# Prediction-Market Odds (the crowd's priced probability)

A prediction market price **is** an implied probability — thousands of betting wallets aggregating
dispersed information (Hayek; Hanson; Wolfers & Zitzewitz). For any **dated, observable** outcome it beats
your own guess. This skill = the HOW: find the market, read the odds, weight by liquidity, dodge the traps.

## When to use vs not

**Use when** the question has a **dated + observable resolution** a market would price: FOMC/rate
decisions, CPI/PCE prints, elections, token unlocks, ETF approvals, "BTC ≤$X by [date]".

**Do NOT use when** there's no tradeable resolution (vague "is crypto healthy"), or the question is a
fact/definition. No market = no anchor; don't fabricate one.

## Venue menu (pull the relevant one; corroborate across ≥2 when liquid)

| Venue | Best for | Access |
|---|---|---|
| **Polymarket** | Crypto prices, macro, politics, general — deepest crypto | Gamma API (below), no key |
| **Kalshi** | Regulated US econ — CPI, Fed, jobs, GDP (often deeper than PM on prints) | `api.elections.kalshi.com/trade-api/v2` (public read) |
| **CME FedWatch** | Fed-funds path from futures (not a bet market, but the rate-path benchmark) | cmegroup.com (JS-rendered — use search/snippet) |

## Polymarket Gamma API — the working recipe

**Discovery = `public-search`. Do NOT guess slugs** (slug-guessing 404s — the #1 failure):

```bash
# 1. DISCOVER the event by keyword (returns slug, ticker, title, description)
curl -s "https://gamma-api.polymarket.com/public-search?q=fed%20decision%20june&limit_per_type=5"

# 2. FETCH the event's markets + odds by slug
curl -s "https://gamma-api.polymarket.com/events?slug=fed-decision-in-june-825"
#    each market has: outcomes, outcomePrices (stringified arrays), volume, liquidity, endDate
```

Read it: `outcomePrices[0]` = implied P(Yes) (e.g. `"0.9905"` = 99.05%). For a grouped event (Fed
decision = many brackets), iterate the sub-markets; each bracket's Yes price is its probability. The
`/markets?closed=false` *list* endpoint is unfiltered junk — never browse it for discovery, always
`public-search`.

## Weight by liquidity — signal vs noise

A price is only as good as the money behind it. Read `volume` + `liquidity` on every market:

| Liquidity / volume | Treat as |
|---|---|
| **> ~$1M vol** | Hard signal — anchor to it |
| **~$50k–$1M** | Usable — corroborate |
| **< ~$50k vol** | Soft/noise — flag, never anchor |

State the volume next to every number you quote. A $5k-volume leg is one trader, not "the market."

## Traps (each one bit a real pull)

| Trap | Symptom | Fix |
|---|---|---|
| **Slug-guessing** | `cpi-june-2026` → 404 | Use `public-search`; real slug was `may-inflation-us-annual` |
| **Frozen / settled** | `endDate` already passed; price stuck at 0.99/0.01 | It's a final snapshot, NOT live-tradeable — say so |
| **Thin leg** | <$50k vol, wide bid/ask | Soft signal only; flag it |
| **Non-monotonic ladder** | P(>8%) > P(>5%) — internally impossible | Mispriced illiquid leg; discard that leg, not the market |
| **Multi-outcome doesn't sum to 1** | brackets sum to 1.05 | Normalize, or report raw + note the vig |
| **Stale snapshot** | quoting yesterday's odds | Timestamp the pull (UTC); odds drift, re-pull near events |

## Output (when feeding a forecast)

Per outcome: **implied P + venue + volume + pull-timestamp**, e.g.
`P(FOMC hold, Jun) = 99.1% (Polymarket, $76M vol, pulled 2026-06-10 09:13 UTC)`.
Cross-venue: if Polymarket and Kalshi/FedWatch disagree, report the spread — don't average silently.

## Common mistakes

- Quoting a number with **no volume** beside it → can't tell signal from one-trader noise.
- Browsing `/markets` list to "find" a market → junk; use `public-search`.
- Treating a **settled** market as a live forecast.
- Inventing odds when **no market exists** → say "no tradeable market," fall back to economist consensus.

> Educational, not advice. Odds drift — timestamp every pull and re-fetch before a dated catalyst.
