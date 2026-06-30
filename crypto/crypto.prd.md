# Crypto Research & Decision — PRD (1-min read)

> What the product must do. Pairs with [crypto.goal.md](crypto.goal.md) (why) and [crypto.tdd.md](crypto.tdd.md) (how).

## Users & jobs

- **PM (owner):** "Is it good to buy BTC now, and how much?" → wants a defended, staged answer, not a guess.
- **Daily proactive loop:** silent unless a tripwire fires (dip + extreme fear, or a material catalyst).

## Functional requirements

### FR1 — Ingest ALL material, price-affecting inputs (the completeness contract)
The consolidated brief MUST cover every category below. A missing category is a defect, not a degradation.
1. **Price & trend** — spot, 52w high, 200d & 200-week MA.
2. **On-chain valuation** — MVRV-Z, NUPL, realized price, Puell, hashrate.
3. **Derivatives / positioning** — funding, basis, OI, liquidations, skew, DVOL, option walls.
4. **Macro** — CPI/PCE, FOMC tone & rate path, real yields.
5. **Liquidity flows** — global liquidity (Howell), net Fed liquidity, M2, DXY, **spot ETF net flows**.
6. **Sentiment / regime** — Fear & Greed, equity regime cross-check.
7. **Priced probabilities** — Polymarket/Kalshi FOMC + BTC price ladder.
8. **News / narrative — REQUIRED, currently MISSING.** Read crypto + macro press for catalysts: corporate
   treasury buys (e.g. Strategy/MSTR), ETF approvals/flows, regulation, hacks/exploits, exchange events.
   - **Sources (tiered):** crypto-native — **Decrypt, CoinDesk, CoinTelegraph, The Block, Bitcoin Magazine**;
     credible macro — **FT, WSJ, Bloomberg, Reuters** (paywalled → headlines/RSS or `[UNAVAILABLE]`);
     hard events — **spot-ETF flows (Farside/SoSoValue), SEC filings, incident reports**.
   - **Extract, not dump:** dominant narrative, narrative velocity, catalysts, and a **"priced-in?" check**.
   - **Guardrail:** news is lagging/reflexive → it is **context + disconfirmation**, never a buy/sell trigger.

### FR2 — Pipeline: gather → consolidate → panel → decide → log
Fan-out data retrieval (incl. FR1.8) → one sourced brief → multi-lens panel debate → chair decision → log to ledger.

### FR3 — Panel composition
Voting seats that can actually price crypto: analyse-onchain, derivatives, Druckenmiller, Alden, **Hunt (bear
dissent)**, Napier. Housel = **non-voting** behavioral guardrail. **No seat whose verdict is predetermined**
(e.g. Buffett can't value a cashless asset → excluded).

### FR4 — Outputs
Dated `research.crypto.{date}.md`; an immediate DM only on a tripwire; a weekly committee memo.

### FR5 — Validation loop
Every dated call → forecast-ledger (`add` on issue, `resolve`/`score` on date) → calibration by lens.

### FR6 — Per-source news-feed skill family (`feed-*`) *(extensible)*
FR1.8 needs sources. This family is **one small skill per outlet**, each a source adapter that normalizes that
outlet's quirks into a common record. Adding "other media like this" = adding one `feed-<name>` skill.
- **Crypto-native (RSS-first):** [[feed-coindesk]], [[feed-cointelegraph]], [[feed-decrypt]], [[feed-theblock]], [[feed-bitcoinmagazine]].
- **Credible macro (paywalled → headlines/RSS or `[UNAVAILABLE]`):** [[feed-ft]], [[feed-wsj]], [[feed-bloomberg]], [[feed-reuters]].
- Each feed skill **MUST** emit a normalized article record `{source, url (canonical), title, published_at, summary/body, lang, tags}`.
- Each **MUST** handle its own access method (RSS / API / scrape) and **MUST** degrade to `[UNAVAILABLE]` on paywall/failure — **never fabricate** a title or body.
- Each **MUST** be polite: conditional GET / ETag, rate-limit aware, backoff on 429.

## Acceptance criteria (testable)
- **AC1:** Given a same-day material catalyst (e.g. "Strategy raises reserves to $11B, buys more BTC"), the
  brief's news section names it **and** tags whether it's priced-in. *(Today: FAILS — no news seat.)*
- **AC2:** No probability appears that wasn't pulled live (no digest-sourced odds).
- **AC3:** Bear dissent is visible in the final memo, not averaged out.
- **AC4:** Every decision has a tranche plan + invalidation + a ledger entry.
- **AC5 (feed-*):** Each `feed-<name>` returns **≥1 normalized record** or a clean `[UNAVAILABLE]` — no half-records, no silent empty.
- **AC6 (feed-*):** Paywalled sources **never fabricate body text** (headline-only or `[UNAVAILABLE]` is acceptable; invented prose is a defect).
- **AC7 (feed-*):** Adding a new outlet requires **only a new `feed-<name>` skill** — no change to the gather/consolidate pipeline.

## Non-functional requirements (NFR)
- **NFR1 — Rate-limit/backoff:** every fan-out fetch (odds + data + `feed-*`) is 429-aware: exponential backoff, a cap on concurrent fetches, conditional-GET/ETag to skip unchanged. (Builds on the `feed-*` politeness rule in FR6.)
- **NFR2 — Catalyst dedup across outlets:** the same event reported by N outlets is **ONE** event carrying a `source_count` (crowdedness signal), **not** N catalysts.
- **NFR3 — Recency window:** "same-day material" = published within a rolling **24–48h** window **AND** above a materiality bar (moves price/odds, hard event, or top-tier source). Default window: **36h**. Older items are context, not catalysts.
- **NFR4 — Source-reliability weighting:** tiers `hard-events (ETF flows, SEC filings, incident reports) > tier-1 macro (FT/WSJ/Bloomberg/Reuters) > crypto-native`. **Conflict rule:** when a higher tier and lower tier disagree, the higher tier sets the fact; the lower tier is recorded as disputed, never silently averaged.
- **NFR5 — Token/cost budget:** ~**15 agent calls/run** (6 gather + 1 consolidate + 6 panel + 1 guardrail + 1 chair + 1 writer + 1 ledger). **Graceful degradation if exceeded:** drop optional `feed-*` outlets first (NFR4 lowest tier), then mark `[DEGRADED]` in the brief; **never** drop a required FR1 category silently (see NFR6).
- **NFR6 — Completeness enforcement (null-seat handling):** REQUIRED categories (FR1.1–FR1.8) must **never** be silently dropped. A failed required seat → loud `[UNAVAILABLE: <seat>]` in the brief **and** the run flagged `incomplete`; the pipeline never proceeds as if complete.
- **NFR7 — Reproducibility:** every brief/report carries a `run_id` + `git_sha` + per-figure timestamps so any run is auditable/replayable.

## Non-goals
Auto-trading; a "predictive" screener; custody/signing; averaging away disagreement into one number.

## Acceptance criteria — NFR (testable)
- **AC8 (NFR1):** A simulated `429` on any fetch triggers backoff + retry (not a crash); concurrent fetches stay ≤ the configured cap.
- **AC9 (NFR2):** Feed the same event from 3 outlets → brief shows **1** catalyst with `source_count=3`, not 3 catalysts.
- **AC10 (NFR3):** An item published 50h ago is **excluded** from catalysts (allowed only as context); a 12h-old material item is **included**.
- **AC11 (NFR4):** When a crypto-native outlet contradicts a hard-event source (e.g. ETF-flow data), the brief states the hard-event fact and tags the other as `disputed` — not an average.
- **AC12 (NFR5):** A run that would exceed the ~15-call budget sheds lowest-tier outlets and emits `[DEGRADED]`, while **all** FR1 required categories still appear (or `[UNAVAILABLE]`).
- **AC13 (NFR6):** Force a required seat to fail → brief contains `[UNAVAILABLE: <seat>]` **and** the run is flagged `incomplete`; it does not silently complete.
- **AC14 (NFR7):** Every emitted brief/report contains a non-empty `run_id`, `git_sha`, and timestamps on each figure.
