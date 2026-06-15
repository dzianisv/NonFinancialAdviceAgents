---
name: prediction-market-odds
description: Use when a forecast or analysis needs the crowd's PRICED probability of a dated, observable outcome — Fed/FOMC rate decisions, CPI/inflation prints, elections, token unlocks, ETF rulings, "will BTC hold $X by [date]", "what are the odds of Y". Reference skill: how to pull live odds from Polymarket (Gamma API), Kalshi, and CME FedWatch, weight them by liquidity, and avoid the standard traps (slug-guessing, frozen/settled markets, thin or non-monotonic legs). Consumed by superforecasting and macro-panel as their market-anchor input. Educational, not advice; odds drift — re-pull before acting.
license: MIT
compatibility: opencode
metadata:
  audience: forecasters-and-analysts-anchoring-to-crowd-odds
  domain: prediction-market-data-access
  role: data-source-reference
  source: "verified live 2026-06-15: Polymarket Gamma API + ZQ-futures-implied (NY Fed + Yahoo) as the two anchor venues; Kalshi KXFEDDECISION corroborates when traded (Fed legs often null)"
---

# Prediction-Market Odds (the crowd's priced probability)

## HARD TRIGGER — read this first (added after a real miss)

The instant you are about to **state a probability for a dated, observable outcome** (FOMC hold/cut/hike,
CPI print, election, ETF ruling, "BTC ≤$X by [date]"), you MUST pull it with this skill — **before** you
type the number. This fires even mid-analysis: if a sentence you're writing contains "% odds", "priced",
"~X% chance", "markets expect" about such an outcome, STOP and run the recipe below.

**Anti-pattern that bit us (2026-06-15):** quoting FOMC odds from a WebSearch *summary* / news blurb
(IndexBox digest). Result: "93% hold" (real: 99.45%) and "70% hike by Dec" (real: ~32% — the digest had
it **backwards**). News digests paraphrase and invert market numbers. A WebSearch result is NEVER an
acceptable source for a priced probability — it's a pointer to *go pull the market*. If you find yourself
citing a number you did not get from `gamma-api.polymarket.com` / Kalshi / FedWatch this turn, you have
already failed; delete the number and run the recipe.

If the skill isn't in your surfaced list, it's still on disk — `grep -ril polymarket .agents/skills/` and
read it. Don't skip it because it wasn't pre-loaded.

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
| **Polymarket** | Crypto prices, macro, politics, general — deepest crypto + deepest Fed-decision pool | Gamma API (below), no key |
| **Kalshi** | Regulated US econ — CPI, jobs, GDP. (Fed-decision legs are often **untraded**, see below) | `api.elections.kalshi.com/trade-api/v2` (public read) |
| **CME FedWatch (ZQ-implied)** | Fed-funds path — the rate-path benchmark, computed first-hand from futures | `python3.12 fedwatch_zq.py` — do NOT scrape the JS FedWatch page |

### Fed rate-path: compute it from ZQ futures, don't scrape FedWatch

The cmegroup.com FedWatch page is JS-rendered and unreachable from a sandbox; its % is only obtainable
via a WebSearch *summary* — which is the exact second-hand trap that bit us. FedWatch is just arithmetic
on CME 30-Day Fed Funds futures (ZQ), and ZQ quotes ARE fetchable. So compute it:

```bash
python3.12 fedwatch_zq.py            # nearest two FOMC meetings: implied P(hold)/P(cut)/P(hike) + sources
```

Pulls current target+EFFR (NY Fed markets API) and ZQ prices (Yahoo chart API), both no-key/live; solves
the post-meeting implied rate per the standard FedWatch method. Use this as the **second venue** to
corroborate Polymarket's Fed-decision odds. Prints `[UNAVAILABLE]` per leg if a source is down — never a
guessed number.

### Kalshi Fed markets — verified series + the untraded-leg gotcha

The Fed-decision series is **`KXFEDDECISION`** (per-meeting; legs `-H0` hold, `-C25` cut 25bp, `-C26`
cut >25, `-H25`/`-H26` hike). Pull live quotes:
```bash
curl -s "https://api.elections.kalshi.com/trade-api/v2/events?series_ticker=KXFEDDECISION&limit=200"     # find the <YY><MON> event ticker, e.g. KXFEDDECISION-26JUL
curl -s "https://api.elections.kalshi.com/trade-api/v2/markets?event_ticker=KXFEDDECISION-26JUL&limit=50" # yes_bid/yes_ask/last_price in cents, volume
```
**Gotcha (verified 2026-06-15):** Kalshi's Fed-decision legs frequently have `yes_bid/yes_ask/last_price/
volume = null` (no liquidity — the pool sits on Polymarket). A null-quote leg is NOT a probability; treat
it as `[no Kalshi quote]` and fall back to the **ZQ-implied** number as your second venue. Do NOT report a
null as 0% or 50%. (`KXFED` is a separate *range* series — also thin; prefer `KXFEDDECISION`.)

## Polymarket Gamma API — the working recipe

**Discovery = `public-search`. Do NOT guess slugs, do NOT browse `/markets` list** (the list returns thousands of unfiltered markets including novelty/entertainment — always search):

For **macro markets** relevant to equities, run these searches (one WebFetch per query):
```
WebFetch: https://gamma-api.polymarket.com/public-search?q=fed+rate+decision&limit_per_type=5
WebFetch: https://gamma-api.polymarket.com/public-search?q=federal+reserve+2026&limit_per_type=5
WebFetch: https://gamma-api.polymarket.com/public-search?q=recession+2026&limit_per_type=5
WebFetch: https://gamma-api.polymarket.com/public-search?q=S%26P+500&limit_per_type=5
WebFetch: https://gamma-api.polymarket.com/public-search?q=CPI+inflation&limit_per_type=5
```

Filter results: KEEP only markets where the `question` or `title` contains at least one of:
  `Fed`, `FOMC`, `rate`, `recession`, `CPI`, `inflation`, `GDP`, `S&P`, `cut`, `hike`, `basis point`
DISCARD any market about sports, entertainment, gaming (GTA, elections unrelated to economy), celebrities.

Then for each relevant market slug:
```bash
# FETCH the event's markets + odds by slug
curl -s "https://gamma-api.polymarket.com/events?slug=<slug-from-search>"
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

**Cross-venue is mandatory for Fed/FOMC odds — never single-venue.** Report ≥2 venues and state
agreement vs divergence; if they disagree by >5pts, show the spread, don't average silently. The second
venue is the **ZQ-implied** number (`fedwatch_zq.py`) when Kalshi's leg is null/untraded. Example
(live 2026-06-15):
```
P(June hold): Polymarket 99.45% ($114M vol) | ZQ-implied ~100% (move +1.2bp) | Kalshi [no quote]  -> AGREE
P(July hold): Polymarket 93.5%  ($10M vol)  | ZQ-implied 90.5% (10% cut priced) | Kalshi [no quote] -> AGREE (3pt)
```

## Common mistakes

- Quoting a number with **no volume** beside it → can't tell signal from one-trader noise.
- Browsing `/markets` list to "find" a market → junk; use `public-search`.
- Treating a **settled** market as a live forecast.
- Inventing odds when **no market exists** → say "no tradeable market," fall back to economist consensus.

> Educational, not advice. Odds drift — timestamp every pull and re-fetch before a dated catalyst.
