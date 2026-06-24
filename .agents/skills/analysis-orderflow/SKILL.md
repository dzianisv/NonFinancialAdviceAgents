---
name: analysis-orderflow
description: "Analyst lens for BTC market microstructure and order flow — bid/ask depth, open interest, liquidation levels, spot vs perp divergence, CVD (cumulative volume delta), bid-ask imbalance, whale order clusters, CME gap. Reads who is actually buying/selling at the margin. Use when asked \"where are the liquidations\", \"is there buying or selling pressure\", \"order flow analysis\", \"CME gap\", \"open interest and liquidations\", \"where will price be forced to go\", \"microstructure read\", \"is this a real move or a fakeout\". Depends on [[derivatives-positioning-data]]. Educational, not advice."
license: MIT
compatibility: opencode
metadata:
  audience: crypto-allocators-and-treasury-managers
  domain: crypto-market-analysis
  role: order-flow-and-microstructure-lens
  source: "Market microstructure practice + Coinglass/CME futures data (distilled 2026-06)"
---

# Analyst: Order Flow & Market Microstructure Lens

Apply this lens to read **who is actually buying and selling at the margin** — not where price has been,
but what the order book, open interest, liquidation clusters, and CVD are *forcing* it to do next.
This is the **microstructure layer** beneath the on-chain and liquidity lenses; it answers short-horizon
questions the valuation lens cannot. Depends on **[[derivatives-positioning-data]]** for live Coinglass data.
Educational, not advice; a lens, not gospel.

## The unifying worldview

Price is the result of **order flow imbalances**. Every candle is a negotiation between resting bids/asks
and aggressive market orders. The market structure lens reads *who is doing what* at the margin: large
passive bids create support (they absorb selling); large asks create resistance (they absorb buying).

**Open interest accumulation with price shows conviction**; OI drop with a price move exposes it as
liquidation-driven — mechanically forced, therefore less reliable and often reversing once the clusters
are swept. **Liquidation clusters are visible gravity wells** — price is attracted to them before reversing,
because the exchange needs to fill stop-market orders sitting at those levels. The **CVD (cumulative volume
delta)** strips the candle narrative away and tells you whether aggressive buyers or sellers are actually
behind the move. **CME gaps fill with ~80% frequency** and act as magnetic pull targets regardless of trend.

The honest limit of this lens: microstructure signals operate on hours-to-days timescales; they are
*flow-and-mechanics reads*, not thesis vehicles. They cannot override a dominant liquidity or valuation
regime — they route *within* it. A liquidation hunt does not reverse a bear market; it produces a bounce inside one.

## Core mental models (the load-bearing ones)

1. **CVD divergence.** Price rising + CVD falling = sellers absorbing the move (supply overwhelming
   aggressive buyers) → **bearish**. Price falling + CVD rising = buyers absorbing the selling (demand
   floor forming under price) → potential **reversal signal**. CVD confirming the price direction =
   trend continuation. CVD is the truth strip underneath the candle's narrative.

2. **OI + price regime.** Rising price + rising OI = new longs entering (trend continuation, real demand).
   Rising price + falling OI = short squeeze (mechanical, less reliable; often reverses once shorts are
   exhausted). Falling price + rising OI = new shorts entering (trend continuation bearish). Falling price
   + falling OI = long liquidation cascade (mechanically driven; watch for reversal after clusters swept).

3. **Liquidation clusters (Coinglass heatmap).** Dense clusters of stop-loss / liquidation orders above
   or below spot are **price magnets**. Price tends to sweep them — triggering cascades — then reverse once
   the mechanical fuel is spent. Clusters on both sides = chop / indecision. One-sided cluster above with
   few below = hunt-upward pattern (and vice versa).

4. **Bid/ask depth imbalance.** Large resting bids (passive buy walls) = support levels; large asks
   (passive sell walls) = resistance levels. Watch for **spoofing**: orders that vanish when price
   approaches — not real support/resistance. Whale order blocks that have been tested and held multiple
   times are more reliable than TA trend lines.

5. **Spot vs perp premium (basis).** Spot price trading at a *premium* over perp = real spot buying
   pressure driving the move (reliable). Perp price at a *premium* over spot = leveraged speculation in
   futures without spot conviction (less reliable, often a setup for a funding-driven flush). Also cross-check
   funding rate: persistently positive = crowded longs, setup for long squeeze.

6. **CME gap.** Unfilled gaps in CME BTC futures (formed over the weekend when crypto trades but CME is
   closed) act as fill targets with ~80% frequency. Gap up → fill often comes on the next open or within
   days. Gap down → price tends to rally back to fill. CME gap + liquidation cluster at the same level =
   high-conviction gravity zone.

7. **Whale order blocks.** Large limit orders that have been tested and held define key S/R levels more
   reliably than TA lines because they represent *actual capital committed*. Levels where visible liquidity
   was absorbed without being broken are where institutions have shown their hand.

## How to apply the lens (decision procedure)

1. **Fetch funding rate + OI via [[derivatives-positioning-data]]** (Coinglass). Classify the OI regime
   (see mental model 2). Note whether funding is neutral, persistently positive (crowded longs), or
   negative (crowded shorts).

2. **Identify liquidation heatmap clusters** via WebFetch `coinglass.com/LiquidationMap`. Locate the
   nearest dense cluster above spot and below spot. Note which side has *more* fuel — that is the likely
   near-term target for a mechanical sweep.

3. **Check for CME gaps** via WebFetch (CME BTC futures chart, weekend open). Note gap level, direction
   (gap up or gap down), and distance from current spot. Mark as *open* or *filled*.

4. **Read spot vs perp premium** (Binance spot BTC price vs the perp contract). Is real spot or
   leveraged futures driving the move? Cross-confirm with funding rate.

5. **State the dominant flow** as one of:
   - **AGGRESSIVE BUYERS** — CVD rising with price, spot premium, OI expanding.
   - **AGGRESSIVE SELLERS** — CVD falling with price, perp premium flushing, OI expanding.
   - **BALANCED** — CVD flat, depth symmetric, no strong bias.
   - **LIQUIDATION-DRIVEN** — OI falling with price move, sweep of known cluster underway; mechanically
     forced, not conviction.

6. **Identify nearest gravity levels**: top liquidation cluster target, bottom liquidation cluster target,
   open CME gap target. These are the levels price is mechanically attracted to next.

7. **State the microstructure posture** as one of:
   - **BULLISH STRUCTURE** — CVD confirming, spot premium, OI rising with price, downside clusters swept.
   - **NEUTRAL** — mixed signals, balanced depth, no dominant flow.
   - **BEARISH STRUCTURE** — CVD diverging, perp premium, OI rising while price fades, upside clusters
     untouched.
   Plus the **key invalidation**: the level or signal change that flips the read.

## Routing table

| Question is about… | Load |
|---|---|
| Live funding rate, OI, options gamma/skew, perpetual premium | `[[derivatives-positioning-data]]` |
| Liquidation heatmap, where the stop clusters are | WebFetch `coinglass.com/LiquidationMap` |
| CME gap level and fill status | WebFetch CME BTC futures chart |
| On-chain valuation zone, MVRV-Z, realized price, NUPL | `analyst-crypto` → `references/02-onchain-valuation.md` |
| Global liquidity, the macro tide governing all of this | `analyst-crypto` → `references/01-global-liquidity-and-btc.md` |
| Sentiment, Fear & Greed, cycle phase | `analyst-crypto` → `references/03-sentiment-and-market-cycle.md` |
| Systematic sizing, vol-target, position sizing | `analyst-systematic-trading` |

## Output contract

Every microstructure read delivers:

| Field | Content |
|---|---|
| **Dominant flow** | AGGRESSIVE BUYERS / AGGRESSIVE SELLERS / BALANCED / LIQUIDATION-DRIVEN |
| **OI regime** | Which of the 4 OI+price regimes applies; funding rate bias |
| **Nearest gravity levels** | Top liquidation cluster (price, est. size), bottom cluster, open CME gap |
| **CME gap status** | OPEN (level + direction) or FILLED |
| **Microstructure posture** | BULLISH STRUCTURE / NEUTRAL / BEARISH STRUCTURE + key invalidation level |

No buy/sell call — structure and mechanics only. This lens does not override the liquidity governor
(`analyst-crypto`); it routes *within* the macro regime.

## Done when

The analysis (1) classifies the **OI regime** (trend continuation vs liquidation-driven), (2) identifies
the **dominant CVD flow** (aggressive buyers/sellers/balanced), (3) maps the **nearest liquidation cluster
gravity wells** above and below spot, (4) states **CME gap status** (open or filled, level), (5) reads
**spot vs perp premium** and funding rate bias, (6) outputs a clean **microstructure posture**
(BULLISH / NEUTRAL / BEARISH STRUCTURE) with a specific invalidation level, and (7) explicitly scopes the
read as a short-horizon mechanics lens, not a thesis vehicle — the liquidity governor and on-chain zone
remain the governing frame.
