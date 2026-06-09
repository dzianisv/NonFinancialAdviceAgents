---
name: crypto-token-screener
description: Screen crypto tokens for real, BTC-beating fundamentals — find the "next HYPE" or judge whether a token (HYPE, AAVE, JUP, ASTER, PUMP, SOL, a new launch) is worth owning vs just holding Bitcoin. Use for "is this token a real infra token", "what could be the next HYPE", "does this token have real fundamentals", "screen these tokens", "is X overpriced vs BTC", "find undervalued real-cashflow tokens". Applies a 6-point value-accrual filter with BTC as the hurdle rate. Notification-first; educational, not financial advice. NOT for answering an investor's buy/sell/timing question (use crypto-advisor) or backtesting a trading strategy (use the backtest gate).
license: MIT
compatibility: opencode (needs network for DefiLlama + CoinGecko APIs)
metadata:
  audience: builders
  domain: systematic-trading
  role: screener
---

# Crypto Token Screener

Decide whether a crypto token has *real, durable, BTC-beating* fundamentals — or is a story priced in
USD that bleeds against Bitcoin. Produces a ranked candidate table, not advice. The reference rationale
is `crypto/InfraTokens.md`; the latest run lands in `crypto/next-hype-candidates.md`.

## Core premise (non-negotiable)
**Bitcoin is the hurdle rate.** Price every token *in BTC*, not USD. A token only earns a place if it
plausibly beats simply holding BTC. The base rate is brutal: 2017→2021 **0 of 20** top alts made a new
BTC-denominated high; the median top-300 alt falls **−90% vs BTC within 10–20 months**; only ETH/BNB/
(maybe) SOL ever durably beat BTC. So every candidate is a **satellite you expect to lose vs BTC most
of the time** — size accordingly, and default a token's weight to zero until it clears the filter.

## The 6-point filter (a HARD gate — a token must pass to rank)
1. **Organic, growing revenue** — real fees, rising run-rate. Reject incentivized/airdrop-farmed or
   wash-traded volume (e.g. volume that mirrors a CEX 1:1, or a protocol DefiLlama delisted as a "black
   box" — ASTER is the standing example: treat its numbers as unverifiable, exclude it).
2. **Enforced fee→token accrual** — fees automatically buy back/burn the token (HYPE routes ~97% of
   fees to its buyback). **Discretionary** buybacks (governance/team can switch them off, or have
   publicly questioned them — JUP) score as a FAIL on enforcement, not a pass.
3. **Category leadership / moat** — #1 or a credible path to it in its vertical.
4. **Beats BTC** — positive BTC-denominated trend over the screen window. This is the filter that kills
   most candidates; a cheap token in a BTC-downtrend is a value trap, not a buy.
5. **Clean FDV / low forward dilution** — mcap/FDV near 1 is clean; a large gap plus a near-term team/
   investor unlock cliff is a structural headwind. Check the unlock schedule.
6. **Durable through a bear** — revenue must survive a downturn. Lending/stablecoin fees (AAVE) are
   durable; perp/trading fees are cyclical; memecoin-launch fees (PUMP) are reflexive and collapse with
   sentiment. Rate each: durable / cyclical / reflexive.

A token that fails #1, #2, or is wash-flagged is **rejected outright**. A token that passes #1–3,5,6 but
fails #4 (BTC-trend) is a **watch-list value bet**, not a buy — name the BTC-relative inflection it needs.

## Procedure

1. **Decide the universe.** Either screen the default watchlist or take the user's token list. To add a
   token you need its DefiLlama fees slug and its CoinGecko id.
2. **Pull the raw numbers — run the bundled script (do not hand-fetch):**
   ```bash
   python3 skills/crypto-token-screener/scripts/screen.py --days 90
   # custom list / window / ad-hoc token:
   python3 skills/crypto-token-screener/scripts/screen.py --watchlist mylist.json --days 180
   python3 skills/crypto-token-screener/scripts/screen.py --token hyperliquid:hyperliquid
   ```
   It returns, per token: holder revenue (1y), 30d run-rate, mcap, P/E (mcap÷holder-rev), holder yield,
   mcap/FDV, and **% vs BTC** over the window. Use `/Users/engineer/.venv/bin/python3` if system python
   lacks stdlib networking.
3. **Fix coverage gaps before judging.** A `holder_rev_1y = n/a` means DefiLlama lacks a holdersRevenue
   series for that slug — a coverage gap, **NOT** proof of zero accrual (it returns n/a for AAVE/JUP/
   edgeX whose buybacks are live). Correct the slug, or source the buyback from the protocol's docs/IR
   and label it `[from IR, not DefiLlama]`. Never report a fabricated figure; print `n/a` and say so.
4. **Apply the 6-point filter to each token** using the numbers + the value-accrual mechanism you
   confirmed (enforced vs discretionary). For #2 and #6 the script can't decide — you must read the
   protocol's actual buyback rule and revenue type.
5. **Rank and write the report** to `crypto/next-hype-candidates.md` (see output format). Lead with the
   honest meta-finding: how many candidates clear ALL six (usually very few — the BTC-trend filter is
   the killer).

## Output format
A dated markdown report with: a one-line honest meta-finding, then a **ranked shortlist** where each
candidate carries its numbers + a per-filter PASS/PARTIAL/FAIL line + the single biggest risk, then a
**watch-list** (real but failing one filter) and an **avoid** list (failed a hard filter, with the
reason). Close with the educational-not-advice line. Keep every number traceable to the script run or a
cited source.

<example>
### 🥇 LIGHTER (LIT) — passes the BTC-trend filter
Holder rev re-accelerating ~$53–77M/yr · mcap ~$378M · P/E ~6x · **+99% vs BTC/30d** ✅ · mcap/FDV ~0.22.
Filters: 1 PASS* (revenue re-accelerating off a post-incentive washout) · 2 ~PASS (live revenue-funded
buyback) · 3 PASS (top-4 perp DEX, zk wash-resistant) · 4 **PASS** · 5 PARTIAL · 6 UNPROVEN.
Biggest risk: Dec-2026 team/investor unlock cliff into still-maturing organic revenue.
</example>

## Invariants
- **BTC is the benchmark in every verdict** — state each token's BTC-relative trend, never just USD price.
- **Never report a number the script printed as `n/a` as if it were real**, and never invent a buyback
  figure — cite DefiLlama or the protocol's IR.
- **Exclude wash-flagged protocols** (DefiLlama-delisted / CEX-mirrored volume) from ranking; list them
  under avoid with the reason.
- **Educational, not financial advice. Notification-first** — output a screen, never an order.

## Done when
- Every token in the universe has a filled row (script numbers, gaps labeled) and a 6-point verdict.
- The report names how many candidates clear all six, the single best candidate + its biggest risk, and
  separates watch (BTC-trend fail) from avoid (hard-filter fail).
- `crypto/next-hype-candidates.md` is written/updated and dated, every number traceable.
