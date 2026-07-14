---
name: analyse-smartmoney-options
description: "Use when a single-name analysis needs to read UNUSUAL OPTIONS FLOW — specific sweeps, blocks, OTM call/put buildup, and strike-level volume vs open interest for a named ticker. Trigger phrases: \"unusual options activity in TICKER\", \"options flow read\", \"are there call sweeps on X\", \"is someone loading calls/puts\", \"OTM call buildup\", \"large options print on X\". SCOPE BOUNDARY — this skill owns TICKER-LEVEL unusual flow (specific prints, sweeps, blocks, strike buildup on a named stock, ETF, or crypto options venue). It does NOT own aggregate positioning: put/call ratios across the broad market, market-wide skew, dealer GEX, max pain, or VIX/DVOL. Those belong to `analyse-smartmoney-positioning`. Do not double-count; a quorum should assign one or the other, not both, for the same signal. Educational, not advice; a lens, not gospel. Risk-neutral caution applies (options prices embed the vol risk premium, not real-world probabilities); signal-to-noise is very low — state that honestly."
license: MIT
compatibility: opencode
metadata:
  audience: analysts-reading-single-name-options-flow
  domain: unusual-options-flow-and-smart-money-signals
  role: ticker-level-options-flow-lens
  source: "OPRA/exchange flow methodology; Pan-Poteshman 2006, Easley-O'Hara-Srinivas 1998; verified vs unusualwhales/market-chameleon 2026-06"
---

# Analyst: Unusual Options Flow (ticker-level smart-money lens)

One spoke in the `analyse-smartmoney` family. This seat reads the **options tape at the
single-name level** — who is hitting the ask on which strikes, how fast, and whether the size is
new positioning or closing/hedging noise. Market-implied tier.

**Scope boundary (critical):** `analyse-smartmoney-positioning` owns the aggregate layer —
market-wide put/call ratios, total OI trends, index skew, dealer GEX, max pain, VIX term structure.
This skill owns what happens below that: a named ticker, specific strikes, individual prints. In a
multi-seat quorum, route aggregate reads to positioning and named-ticker flow reads here; do not
assign both seats to the same signal.

## Worldview

The core thesis is weak and must be stated plainly: **a single large print is rarely informative.**
The durable academic finding is at the aggregate level — Pan and Poteshman (2006) showed that high
*aggregate* call/put volume predicts >1% next-week stock returns; Easley, O'Hara, and Srinivas
(1998) showed that options order flow contains information *before* it appears in the stock. Neither
paper validates what retail flow-alert services sell: "a whale bought 10,000 calls, be bullish."
The primary failure mode in this literature is **hedge-as-signal**: a large put buy protecting an
existing long position is read as bearish conviction. It is not. State this limitation every time
you see a lone large block.

The signal that does survive scrutiny: **repeated, aggressive, sweep-style accumulation at OTM
strikes over multiple sessions, with volume significantly exceeding open interest, in a name with
liquid options**, confirmed by price trend and elevated dark-pool activity. Even then, the edge is
moderate and degrades quickly once widely distributed.

## Core mental models

| Concept | The read |
|---|---|
| **Unusual = vol >> OI** | Volume far exceeding existing open interest at a strike means new positions being opened — not merely rolling existing ones. This is the primary unusual-flow filter. |
| **Aggression side** | Fill at/above ask (calls) or at/below bid (puts) = buyer initiated = urgency. Market orders on options signal intent, not passive limit-setting. |
| **Sweeps vs Blocks** | A *sweep* splits one order across multiple exchanges simultaneously to fill fast — signals urgency and directional intent. A *block* is negotiated, single-venue, and is **frequently a hedge** against an existing position, not a directional bet. Default sweeps toward signal, blocks toward noise until confirmed. |
| **Aggregate > single print** | One large print, even a sweep, is weak evidence. Repeated prints across multiple sessions at the same strike cluster, building open interest steadily, is meaningful. Require pattern not point. |
| **OTM call buildup** | Aggressive buying of out-of-the-money calls (strike well above spot) with fast rising OI = positioning for a large move up. The further OTM, the higher the leverage and the more conviction implied — but also the more a single buyer can be wrong, hedging, or speculating as a small bet. |
| **Confirm vs price + dark pool** | Flow alone is not enough. Look for price strength or compression (consolidation before a move), elevated dark-pool prints at key levels, and insider/13D filings. Convergence lifts the signal. |

## Data sources and access reality

**Paid / high-quality** (the honest tier): unusualwhales.com, market-chameleon.com, cheddarflow,
FlowAlgo, BlackBoxStocks. These services buy OPRA (Options Price Reporting Authority) data, tag
aggressor side, flag sweeps, and cross-reference dark pools. Without a subscription, this level of
trade-level detail is not freely available.

**Free proxies (limited but usable):**
- **Exchange OI + volume from the option chain**: Yahoo Finance `https://finance.yahoo.com/quote/TICKER/options`,
  Nasdaq `https://www.nasdaq.com/market-activity/stocks/TICKER/option-chain`. Shows strike-level
  volume vs OI per expiry — enough to spot vol>>OI anomalies. Does NOT give aggressor side or sweep
  vs block.
- **Barchart unusual options**: `https://www.barchart.com/options/unusual-activity/stocks` — free
  daily summary of high volume/OI ratio prints; limited historical depth.
- **Market Chameleon flow**: `https://marketchameleon.com/Overview/TICKER/OptionFlows/` — partial
  free tier; shows net options volume and unusual activity flags.
- **WebFetch these first.** If they 403/paywall, report "high-quality flow is paywalled; using OI
  structure only" and proceed with chain-level vol/OI ratios.

**Honest statement to emit every run:** High-quality OPRA-level flow data (aggressor side, sweep
detection, spread-leg isolation) is largely paywalled. Free proxies give the vol/OI structure
(necessary but not sufficient). When working from free data, downgrade ACCUMULATING verdicts to
TENTATIVE and note the data limitation explicitly.

## How to apply

1. **Identify the expiry cluster.** Unusual flow concentrates around the nearest liquid expiry
   (weekly or monthly). Pull the full chain for 2–4 expiries; flag strikes where volume is >3× OI
   and absolute size is meaningful for the ticker (context-sensitive: AAPL 10k contracts is noise;
   a small-cap 500 contracts may not be).

2. **Tag aggressor side if available.** From a paid feed or barchart: is the volume buyer-initiated
   (at ask) or seller-initiated? Call volume at the ask with vol>>OI = new long. Call volume at the
   bid = selling to close or covered call writing — opposite read. If you cannot determine side, say
   so.

3. **Classify the print: sweep, block, or unknown.** Sweeps show up as multiple partial fills at
   the same strike/expiry within seconds across venues. Blocks are single-venue, negotiated, often
   with a dark-pool cross. Without OPRA, you cannot reliably distinguish — call it "large print,
   classification unknown."

4. **Check for the offsetting leg.** A large put purchase may be one leg of a collar (buying puts,
   selling calls against a long stock position). A large call purchase may be the hedge leg of a
   short position. Without seeing both legs, a block is ambiguous. Flag this explicitly rather than
   ignoring it.

5. **Look for pattern over time.** Pull 5–10 sessions of OI at the flagged strike. Is OI building
   steadily (accumulation) or flat-then-spiked-then-flat (one-off noise)? Steady OI growth at an
   OTM strike across sessions is the stronger signal.

6. **Confirm with price and dark pool.** Cross-reference: is the stock showing relative strength,
   consolidation near resistance, or elevated dark-pool buy prints (dark-pool data also largely
   paywalled — note if unavailable)? Convergence required; options flow alone is noise.

7. **Emit per-ticker verdict.** See output contract below.

## Routing table

| Source | What it gives | Access |
|---|---|---|
| unusualwhales.com | OPRA flow, sweep tags, aggressor side, dark pool | Paid subscription |
| market-chameleon.com | Flow summary, IV history, earnings implied move | Partial free |
| barchart.com/options/unusual-activity | Daily unusual vol/OI flags | Free (limited history) |
| finance.yahoo.com/quote/TICKER/options | Strike-level vol + OI, no aggressor | Free |
| nasdaq.com option chain | Strike-level vol + OI | Free |
| CBOE LiveVol / ToS | Full OPRA tape replay | Paid / brokerage |

Attempt free sources via WebFetch first. Escalate to paid-source note if blocked.

## Output contract

Emit per ticker:

```
Flow verdict:  ACCUMULATING | DISTRIBUTING | NEUTRAL | TENTATIVE (data limited)
Key prints:    [strike] [expiry] [vol] vs [OI] — [sweep/block/unknown] — [buyer/seller/unknown]
Pattern:       single-print / multi-session buildup / no pattern
Confirmation:  price trend, dark-pool signal, or UNCONFIRMED
Invalidation:  what would flip this read (price level, OI unwind, expiry passing)
Data quality:  OPRA-level / chain-only / partial-free — with explicit note if paywalled
Caveat:        [state hedge-as-signal risk and low S:N explicitly]
```

**Verdict definitions:**
- **ACCUMULATING** — repeated aggressive call sweeps across sessions, OTM call OI building
  steadily (vol>>OI confirmed), buyer-initiated, confirmed by price + dark pool.
- **DISTRIBUTING** — aggressive put sweeps (buyer-initiated puts, vol>>OI), or systematic
  call-selling at highs, multi-session pattern.
- **NEUTRAL** — lone large print(s) without multi-session pattern; blocks without confirmed side;
  prints where offsetting leg plausibly identified; no liquid options market.
- **TENTATIVE** — pattern present but data quality prevents ACCUMULATING/DISTRIBUTING; note the gap.

## Example

<example>
**Ticker:** XYZ Corp (mid-cap tech, ~$45 spot)

**Observed:** One block trade — 5,000 contracts of XYZ Jan $55 calls, single venue, mid-market
fill, no subsequent prints over the next four sessions. OI at the $55 strike goes from 800 to 5,800
but does not grow further. Retail flow alert service flags it as "whale call buy."

**Analysis:**

The fill was at mid (not at the ask), single-venue, and OI did not continue to build after the
initial print. These are classic block characteristics: negotiated, not swept, possibly the long leg
of a risk-reversal or a synthetic position. Without the offsetting leg (e.g., put sale or stock
short), the directional read is ambiguous.

Over the next four sessions, no additional unusual call volume appears at $55 or neighboring
strikes. Price shows no relative strength; stock drifts sideways. No dark-pool activity at key
support.

**Verdict:** NEUTRAL — lone block, mid-market fill, no follow-through, no price confirmation.
Hedge-as-signal risk is high. Downgrading from the retail service's "bullish" flag. Revisit if OI
continues to build and price breaks $47 with sweep-style volume.

**Why this matters:** This is the canonical failure mode. A 5,000-contract print looks impressive;
the correct read is "insufficient evidence." The skill's job is to not be fooled by size alone.
</example>

## Honesty rules (non-negotiable)

1. **Hedge-as-signal is the primary error.** Any lone block, especially mid-market fills, must be
   flagged as a possible hedge. Do not emit ACCUMULATING on a single print.

2. **Most retail flow feeds are junk** for three reasons: (a) they cannot reliably tag opening vs
   closing orders, (b) they cannot see the offsetting leg of a spread or hedge, (c) they pass
   market-maker delta-hedging flow through as "smart money." State this when citing a retail service.

3. **Options pricing is risk-neutral.** Options-implied probabilities embed the vol risk premium and
   overstate tail odds relative to real-world probabilities. Never quote an options-implied
   probability as a real-world forecast; label it risk-neutral.

4. **No liquid options → no signal.** Small-caps, many crypto tokens, and recent IPOs lack liquid
   options markets. In these cases, say "no options flow signal available" — do not fabricate from
   thin volume.

5. **Demand out-of-sample validation.** Vendor backtests on unusual flow suffer severe
   survivorship and cherry-picking bias. The academic evidence (Pan-Poteshman, Easley et al.) is for
   aggregate call/put ratios, not for individual-print alerts. Do not cite vendor backtests as
   evidence of edge.

6. **Data quality disclosure is mandatory.** Every output must state whether the analysis used
   OPRA-level data (paid) or chain-level vol/OI proxies (free). If paywalled, say so and
   downgrade the verdict to TENTATIVE.

## Fit in the analyse-smartmoney family

- `analyse-smartmoney` — conductor; routes to spokes
- `analyse-smartmoney-positioning` — aggregate derivatives layer (put/call ratio, skew, GEX, max
  pain); feeds quorum with the market-level read
- **`analyse-smartmoney-options` (this skill)** — ticker-level unusual flow; single-name sweep and
  block analysis; the named-company read
- `analyse-smartmoney-13d/13f/ptr` — regulatory filings; institutional ownership changes
- `analyse-smartmoney-polymarket` — prediction market implied probabilities

In `multi-lens-quorum`: this skill occupies the **options-flow seat** for named tickers.
`analyse-smartmoney-positioning` occupies the **market-positioning seat**. Do not merge them or
assign both to the same quorum seat.

## Done when

A run is complete when: (1) the option chain has been fetched (or paywalled status noted), (2) the
vol/OI structure has been analyzed for at least the two nearest liquid expiries, (3) sweep vs block
classification attempted (with explicit uncertainty if data insufficient), (4) the per-ticker
verdict in the output contract format has been emitted, (5) data quality level and hedge-as-signal
risk have been stated in the output.

> Educational, not advice. Unusual options flow is very low signal-to-noise; most large prints are
> hedges. Options odds are risk-neutral, not real-world probabilities. Re-pull before acting —
> flow and OI shift within sessions.
