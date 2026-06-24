---
name: analysis-sentiment
description: "Analyst lens for reading crypto market sentiment — Fear & Greed index, funding rates, long/short ratio, social volume, Google Trends, options skew, retail vs institutional divergence. Interprets crowd psychology signals as contrarian indicators. Use when asked \"what is market sentiment right now\", \"is crypto overheated\", \"fear and greed\", \"funding rates analysis\", \"is retail FOMO or panic\", \"sentiment-based entry\", \"is the crowd too bullish/bearish\". Depends on [[derivatives-positioning-data]] for funding/skew. Contrarian lens: extreme fear = accumulate; extreme greed = trim. Educational, not advice."
license: MIT
compatibility: opencode
metadata:
  audience: crypto-allocators-and-treasury-managers
  domain: crypto-market-analysis
  role: sentiment-contrarian-analysis-lens
  source: "Crowd psychology + derivatives market structure (distilled 2026-06)"
---

# Analyst: The Crypto Sentiment Lens (crowd psychology → contrarian signal)

Apply this **sentiment-as-contrarian-modulator** lens to *how market psychology is read and how it biases
the deployment decision*. This skill is a **focused specialist**; it sits inside the four-pillar stack
managed by `analyst-crypto` and extends the sentiment pillar with full metric resolution.
Load `[[derivatives-positioning-data]]` for live funding rates, OI, and options skew before any load-bearing
claim. All outputs are educational — a lens, not financial advice.

## The unifying worldview

Sentiment is a **contrarian modulator, not a primary signal**. Markets cycle through fear and greed because
human psychology is consistent — capitulation creates bottoms, euphoria creates tops. The **Fear & Greed
index** captures the composite of volatility, momentum, social volume, dominance, and trends into a single
0–100 reading. **Funding rates on perpetuals** show real-money conviction: persistently positive = crowded
longs needing unwinding; deeply negative = shorts crowded and squeezable. **Social volume and Google Trends**
measure retail attention — a *lagging* indicator of crowd entry, peaking after the smart money has already
positioned. **Options 25-delta skew** measures whether hedgers are paying up for puts (fear) or calls
(greed). The signal is always: *what is the crowd doing, and what does contrarianism demand?*

Sentiment never acts alone. Extreme readings can persist for weeks. The lens calibrates the *tilt* on top
of what on-chain valuation and the liquidity governor have already decided — it amplifies conviction in a
cheap zone, and raises caution in a rich one.

## Core mental models (the load-bearing ones)

1. **Fear & Greed index bands.** Extreme Fear (0–25) = contrarian buy zone; Extreme Greed (75–100) =
   trim/caution zone. Neutral (40–60) = no sentiment edge; do not force a contrarian call there.
2. **Funding rates as real-money conviction proxy.** Persistently positive (+0.05–0.1%/8h) with rising open
   interest = crowded longs → squeeze-down risk. Deeply negative = shorts crowded → squeeze-up risk.
   Single-session spikes are noise; look for multi-day persistence across major venues.
3. **Long/short ratio (retail perps).** Ratio >70% longs = historically bearish (retail over-levered into the
   move); ratio >70% shorts = squeeze setup. Source via CoinGlass cross-exchange aggregate.
4. **Social volume and Google Trends as lagging retail FOMO indicator.** A spike in both = late-cycle retail
   entry; absence/flat = early-cycle or sustained bear. Never use as a leading signal alone.
5. **Options 25-delta skew.** Positive skew (puts expensive) = fear and hedging demand; negative skew (calls
   expensive) = euphoria and upside-chase. Source via Deribit or `[[derivatives-positioning-data]]`.
6. **Sentiment is a modulator, not a timer.** Extreme readings can persist for weeks without resolving.
   Combine with on-chain zone (`analyst-crypto` pillar 2) for higher-confidence signals.
7. **Divergence is the most powerful signal.** Price falling + Fear & Greed turning up from extreme-fear =
   likely bottom forming. Price rising + Greed near extreme = distribution risk. Divergence between metrics
   (e.g., funding positive but social volume flat) = mixed conviction, size down.

## How to apply the lens (decision procedure)

1. **Fetch Fear & Greed** via WebFetch `https://api.alternative.me/fng/?limit=7` — get 7-day history to
   assess direction (improving vs. deteriorating), not just spot value.
2. **Fetch funding rates** via WebFetch CoinGlass (`https://www.coinglass.com/FundingRate`) or Deribit
   perpetual API — record 8h rate for BTC and ETH, note persistence (days positive/negative).
3. **Fetch long/short ratio** via WebFetch CoinGlass cross-exchange aggregate — note the exact ratio and which
   direction it has trended over the past 24–48h.
4. **Check options skew and OI** via `[[derivatives-positioning-data]]` — pull 25-delta put/call skew and
   open interest for BTC options to confirm or refute the perp-funding signal.
5. **Score each metric** on a five-point scale: `FEAR_EXTREME` / `FEAR` / `NEUTRAL` / `GREED` / `GREED_EXTREME`.
6. **State composite sentiment posture** — the plurality or consensus reading across all metrics — and derive
   the **contrarian implication**: `ACCUMULATE` / `HOLD` / `TRIM` / `WAIT` (when metrics conflict and no
   clear majority).
7. **Note divergences** — any metric moving against the composite (e.g., social volume surging while funding
   turns negative) is the most actionable observation; flag it explicitly.

## Routing table

| Question is about… | Load |
|---|---|
| Fear & Greed raw value, historical trend, composite index methodology | WebFetch `https://api.alternative.me/fng/?limit=30` |
| Funding rates, open interest, perpetuals market structure, squeeze risk | `[[derivatives-positioning-data]]` + CoinGlass |
| Long/short ratio, retail over-leverage, cross-exchange aggregate | CoinGlass long/short endpoint |
| Options skew, put/call ratio, gamma exposure, max pain | `[[derivatives-positioning-data]]` (Deribit/Laevitas) |
| Social volume, Google Trends, retail attention spikes | LunarCrush social volume, Google Trends (manual fetch) |
| How sentiment integrates into the full four-pillar deploy decision | `analyst-crypto` (the synthesis lens) |
| On-chain valuation zone, MVRV-Z, realized price | `analyst-crypto` → `references/02-onchain-valuation.md` |

## Output contract

Return a structured list followed by a composite posture block:

```
| Metric              | Value          | Signal         | As-of      | Source URL                                         |
|---------------------|----------------|----------------|------------|----------------------------------------------------|
| Fear & Greed        | 23 (7d avg 27) | FEAR_EXTREME   | 2026-06-22 | https://api.alternative.me/fng/?limit=7            |
| BTC Funding Rate    | +0.03%/8h      | NEUTRAL        | 2026-06-22 | https://www.coinglass.com/FundingRate              |
| Long/Short Ratio    | 58% long       | NEUTRAL        | 2026-06-22 | https://www.coinglass.com/LongShortRatio           |
| 25-delta Skew (BTC) | +4.2%          | FEAR           | 2026-06-22 | https://www.deribit.com/statistics/BTC/volatility-smile |
| Social Volume       | flat/low       | NEUTRAL        | 2026-06-22 | https://trends.google.com/trends/explore?q=bitcoin |

Composite posture: FEAR
Contrarian implication: ACCUMULATE (tilt buy schedule; confirm on-chain zone first)
Key divergences: Funding not yet negative despite extreme F&G — longs not fully flushed; size tranches, not full deploy.
```

No buy/sell call. No price targets. Posture is a *tilt modifier* for a DCA schedule already governed by
`analyst-crypto`; it does not override the liquidity governor.

## Citation rule — no URL = not a source

Every external claim (news event, data point, quote, analysis) MUST include ALL THREE:
1. **Full URL** fetched: `https://exact-page-url` (specific article, not homepage or search page)
2. **Date** (ISO): `YYYY-MM-DD` (publication or as-of date)
3. **Verbatim quote**: exact words from the page, copied not paraphrased

Format in output: `[TIER] https://exact-url (YYYY-MM-DD) — "verbatim quote"`

**Never write:**
- Source name alone (`CoinDesk`, `Bloomberg`) — without URL it is hallucination bait
- A quote without its URL
- A URL without a date
- Anything paraphrased from memory without a prior web_fetch call

**If fetch failed:** `[FETCH FAILED: https://...] — not counted toward minimum`
**If < 2 real sources:** output `INSUFFICIENT_DATA — do not guess`

## Done when

The analysis (1) fetches and ages all five metric sources before drawing any conclusion, (2) scores each
metric on the five-point scale, (3) derives a **composite posture** with an explicit **contrarian
implication**, (4) flags all **divergences** between metrics as the primary actionable observation, (5)
hands off to `analyst-crypto` for integration with on-chain valuation and the liquidity governor, and
(6) makes no buy/sell call — only a tilt direction and confidence level.
