---
name: analyse-onchain-lens
description: "Analyst lens for reading Bitcoin's on-chain valuation state — MVRV-Z, NUPL, realized price, Puell multiple, LTH/STH supply, exchange flows, miner behavior. Interprets raw on-chain numbers into a buy/hold/trim zone verdict and confidence level. Use when asked \"is BTC cheap or expensive on-chain\", \"what do on-chain metrics say\", \"MVRV/NUPL/Puell analysis\", \"where is BTC in its cycle\", \"long-term holder behavior\", \"whale flows\", \"is this a bottom\". Depends on [[crypto-onchain-data]] for raw numbers; this skill interprets them. Educational, not advice."
license: MIT
compatibility: opencode
metadata:
  audience: crypto-allocators-and-treasury-managers
  domain: bitcoin-onchain-valuation
  role: onchain-analysis-and-zone-lens
  source: "On-chain valuation practice — MVRV-Z, NUPL, Puell, LTH/STH, exchange flows (distilled 2026-06)"
---

# Analysis: On-Chain Valuation Lens (cost-basis → crowd psychology → miner stress → zone verdict)

Apply this lens to **interpret raw on-chain numbers** into a cycle-phase zone verdict with a confidence level.
This skill is the **interpretation layer only**; raw metric fetching lives in `[[crypto-onchain-data]]`
(`python3 .agents/skills/crypto-onchain-data/onchain_fetch.py`). It is the rigorous on-chain answer to
"where is BTC in its cycle" — one structured pillar within the broader `analyse-onchain` lens-stack.

## The unifying worldview (everything connects to this)

On-chain data is the **aggregate cost-basis and behavior ledger of every Bitcoin holder** — the closest thing
crypto has to a fundamental valuation model. **MVRV-Z measures whether market value is above or below
realized value** (the aggregate cost basis): it is the single most cycle-reliable indicator because it
captures whether the crowd is sitting on enough profit to sell. **NUPL maps unrealized profit/loss to crowd
psychology phases** — from capitulation through euphoria — giving the MVRV-Z signal a behavioral reading.
The **realized price is the floor that long-term holders defend**: price trading below realized price means
most holders are underwater, which historically marks capitulation bottoms. **Puell tells you when miners
are under structural sell pressure**, since miners are the only obligate sellers in the ecosystem. Together
these metrics answer one master question: *are holders in profit enough to sell, or underwater enough to
capitulate?* No single metric is sufficient — read all of them together; conflicts mean no extreme signal,
stay patient.

## Core mental models (the load-bearing ones)

1. **MVRV-Z: the cycle-phase thermometer.** >7 = historically reliable top zone (price far above aggregate
   cost basis, crowd in heavy profit); <0 = capitulation/accumulation (market value below realized value);
   1–4 = no extreme signal, mid-cycle. → `[[crypto-onchain-data]]`
2. **NUPL: profit/loss to crowd psychology.** >0.75 = euphoria (trim tilt); 0.5–0.75 = belief/greed;
   0.25–0.5 = optimism; 0–0.25 = hope; <0 = capitulation (accumulate). The phase labels matter because
   they map behavior: euphoric crowds sell; capitulating crowds have already sold. → `[[crypto-onchain-data]]`
3. **Realized price: the cycle-bottom anchor.** It is the market's aggregate cost basis — the price at which
   each coin last moved, averaged across supply. Price below realized price = bear market capitulation; the
   realized price acts as a gravitational floor that long-term holders defend. → `[[crypto-onchain-data]]`
4. **Puell multiple: miner stress and forced selling.** >4 = miners over-earning relative to their 365d
   average (sell pressure, often coincides with tops); <0.5 = miner capitulation (historically a buy signal
   as forced sellers exhaust). Miners are the only agents who *must* sell to cover costs. → `[[crypto-onchain-data]]`
5. **LTH supply: smart money accumulation vs distribution.** Rising LTH supply = long-term holders
   accumulating, illiquid supply growing (bullish); sharply falling LTH supply = distribution into strength
   (caution). The LTH/STH split exposes *who* is moving coins. → `[[crypto-onchain-data]]`
6. **Exchange net flows: supply pressure signal.** Sustained net outflows = coins leaving exchanges, supply
   removed from immediate sell pressure (bullish); sustained net inflows = coins moving to exchanges,
   sell pressure building. A single day is noise; a week or more of trend is signal. → `[[crypto-onchain-data]]`
7. **Confirmation beats any single metric.** Conflicts between metrics → no extreme zone, stay patient and
   DCA at base rate. ≥3 metrics aligned in the same direction → HIGH confidence zone call. → `[[crypto-onchain-data]]`

## How to apply the lens (decision procedure)

1. **Pull raw numbers** via `[[crypto-onchain-data]]`:
   ```
   python3 .agents/skills/crypto-onchain-data/onchain_fetch.py
   ```
   Confirm each metric has an `asof` timestamp before proceeding — stale data is worse than no data.

2. **Score each metric independently** using the thresholds in Core Mental Models:
   - `ACCUMULATE` — metric is in the historically cheap/capitulation zone
   - `NEUTRAL` — metric shows no extreme signal (mid-range)
   - `TRIM` — metric is in the historically expensive/euphoria zone
   - `[UNAVAILABLE]` — data could not be fetched; do not impute

3. **Count the signals.** Tally ACCUMULATE vs TRIM scores across all available metrics.
   - ≥3 aligned → proceed to zone call with HIGH or MED confidence
   - 2 aligned, rest NEUTRAL → MED confidence
   - Split (ACCUMULATE and TRIM both present) → no extreme, FAIR VALUE / LOW confidence

4. **State the zone with confidence:**
   - `DEEP VALUE` — MVRV-Z <0 or ≥3 ACCUMULATE signals (HIGH/MED confidence)
   - `FAIR VALUE` — no extremes, signals mixed or neutral (LOW confidence)
   - `ELEVATED` — 2–3 TRIM signals, MVRV-Z 4–7 range (MED confidence)
   - `EXTREME` — MVRV-Z >7 or ≥4 TRIM signals (HIGH confidence)

5. **State the invalidation condition.** What specific metric crossing what threshold would change the verdict?
   (e.g., "Verdict flips to ELEVATED if MVRV-Z crosses above 4 or LTH supply begins declining.")

6. **Honesty pass.** Note any metrics that are UNAVAILABLE, any conflicts, and remind that this is a
   *zone* call, not a top/bottom prediction. Every metric decays — re-pull before any deploy decision.

## Routing table

| Question is about… | Data source |
|---|---|
| MVRV-Z value, reading, interpretation | `[[crypto-onchain-data]]` → `onchain_fetch.py` |
| NUPL phase, crowd psychology, unrealized P/L | `[[crypto-onchain-data]]` → `onchain_fetch.py` |
| Realized price, aggregate cost basis, "is price below realized price" | `[[crypto-onchain-data]]` → `onchain_fetch.py` |
| Puell multiple, miner behavior, miner capitulation | `[[crypto-onchain-data]]` → `onchain_fetch.py` |
| LTH/STH supply split, long-term holder accumulation vs distribution | `[[crypto-onchain-data]]` → `onchain_fetch.py` |
| Exchange inflows/outflows, supply on exchanges, sell pressure | `[[crypto-onchain-data]]` → `onchain_fetch.py` |
| Overall zone verdict, confidence, "is BTC cheap or expensive" | This skill — run all metrics, score, output verdict |
| How to size deployment, DCA schedule, vol target | `analyse-onchain` → `references/04-execution-dca-and-sizing.md` |
| Liquidity governor, global liquidity cycle, Howell phases | `analyse-onchain` → `references/01-global-liquidity-and-btc.md` |

## Output contract

Structured result for every call:

```
METRIC SCORES
┌──────────────────┬──────────┬──────────────┬───────────────────────┐
│ Metric           │ Value    │ Signal       │ As-of                 │
├──────────────────┼──────────┼──────────────┼───────────────────────┤
│ MVRV-Z           │ <value>  │ ACCUMULATE / NEUTRAL / TRIM / [UNAVAILABLE] │ <date> │
│ NUPL             │ <value>  │ …            │ <date>                │
│ Realized Price   │ $<value> │ …            │ <date>                │
│ Puell Multiple   │ <value>  │ …            │ <date>                │
│ LTH Supply trend │ <trend>  │ …            │ <date>                │
│ Exchange flows   │ <net>    │ …            │ <date>                │
└──────────────────┴──────────┴──────────────┴───────────────────────┘

ZONE VERDICT:   [DEEP VALUE / FAIR VALUE / ELEVATED / EXTREME]
CONFIDENCE:     [HIGH / MED / LOW]
SIGNAL COUNT:   [N ACCUMULATE, M TRIM, K NEUTRAL, J UNAVAILABLE]
INVALIDATION:   [specific metric crossing specific threshold that flips the verdict]
NOTE:           Educational only — zone call, not buy/sell advice. Re-pull before acting.
```

## Example

<example>
User: "What do on-chain metrics say about BTC right now?"

Lens response: "Pull raw numbers via `crypto-onchain-data`:

METRIC SCORES (example readings — re-pull for live):
- MVRV-Z: 1.8 → NEUTRAL (1–4 range, no extreme)
- NUPL: 0.42 → NEUTRAL (optimism phase, no extreme)
- Realized Price: $48,200 vs spot $62,500 → NEUTRAL (price above realized, not capitulation; not extended)
- Puell Multiple: 0.6 → ACCUMULATE (approaching miner stress threshold <0.5, elevated sell pressure relief)
- LTH Supply: rising 3 consecutive months → ACCUMULATE (smart money accumulating, illiquid supply growing)
- Exchange net flows: −18,400 BTC net outflow past 14 days → ACCUMULATE (supply leaving exchanges)

SIGNAL COUNT: 3 ACCUMULATE, 0 TRIM, 3 NEUTRAL
ZONE VERDICT: FAIR VALUE leaning DEEP VALUE — signals are constructive but MVRV-Z and NUPL show no extreme cheapness
CONFIDENCE: MED (3 of 6 metrics aligned ACCUMULATE; the two headline metrics are neutral)
INVALIDATION: Verdict flips to ELEVATED if MVRV-Z crosses 4.0 or NUPL enters belief phase (>0.5) with exchange inflows turning positive.
NOTE: On-chain alone is one pillar. Route through `analyse-onchain` for the liquidity governor (Howell phases) before sizing a deploy decision."
</example>

## Honesty rules (non-negotiable)

- **Output zones, not calls.** This skill returns DEEP VALUE / FAIR VALUE / ELEVATED / EXTREME — never
  "buy now", "sell today", or a price target. Zone is a probability weight, not a trigger.
- **No single metric is sufficient.** Always run all available metrics; state every UNAVAILABLE explicitly.
  A verdict built on 2 metrics is weaker than one built on 6 — say so.
- **Conflicts are data.** If MVRV-Z says TRIM while exchange flows say ACCUMULATE, the honest output is
  FAIR VALUE / LOW confidence, not a cherry-picked bullish read.
- **Every metric decays — re-pull live** (Glassnode, LookIntoBitcoin, CryptoQuant) before any deploy
  decision. The `asof` field is mandatory; do not interpret a reading without it.
- **This is one pillar.** On-chain valuation is the *level* in the `analyse-onchain` lens-stack — it does
  not replace the liquidity governor (the tide) or sentiment (the modulator). Always note whether on-chain
  and liquidity are aligned or in tension.
- **Educational only.** This is not financial advice. Zone calls are analytical outputs, not instructions.

## Done when

The analysis (1) fetches **all six metrics** via `[[crypto-onchain-data]]` with confirmed `asof` timestamps,
(2) scores each metric independently as ACCUMULATE / NEUTRAL / TRIM / [UNAVAILABLE], (3) counts signal
alignment and resolves to one of the four **zone verdicts** with a **confidence level**, (4) states a clear
**invalidation condition**, and (5) notes any conflicts honestly and reminds that on-chain is one pillar —
the liquidity governor in `analyse-onchain` sits above it.
