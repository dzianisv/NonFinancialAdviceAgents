---
name: hedge-fund-13f-analysis
description: Check what notable hedge funds and super-investors own and why, using SEC 13F filings, and cross-reference them against a portfolio. Use when the user asks "what do hedge funds hold", "check the 13F", "who owns this stock", "what is Buffett/Burry/Ackman/Tepper/Druckenmiller/Klarman/Li Lu/Tiger buying", "which of my stocks do big managers hold", "is smart money buying X", "13F overlap", or wants to validate/challenge a position against institutional conviction. Covers reading filings from EDGAR + aggregators (dataroma, whalewisdom, 13f.info, hedgefollow), computing quarter-over-quarter add/trim/new/exit deltas, interpreting WHY a manager bought, and storing the insight. Educational, not advice; 13F is a 45-day-lagged, long-only, US-equity snapshot — not a real-time trade signal.
license: MIT
compatibility: opencode
metadata:
  audience: systematic-investors
  domain: equity-research
  role: institutional-flow-analyst
---

# Hedge-Fund 13F Analysis

Read what institutional managers own, compute what changed last quarter, infer *why*, and
cross-reference against a portfolio. **13F is a lagged snapshot, not a trade signal** — treat
overlap as a *conviction cross-check*, never as a reason to skip your own valuation work.

## What a 13F is (and is NOT)

A 13F-HR is a quarterly SEC filing required of managers with >$100M in US "13(f) securities".
- **Lag:** due **45 days after quarter-end** (Q1 → ~May 15, Q2 → ~Aug 14, Q3 → ~Nov 14, Q4 → ~Feb 14). Today's "latest" is the most recent quarter whose deadline has passed.
- **Long-only US equity:** shows US-listed long positions + *disclosed* options (puts/calls appear as notional). **Does NOT show** shorts, cash, bonds, commodities, non-US listings, or crypto. A "100% GOOG" 13F may be a hedged book — the filing only shows one leg.
- **Stale by design:** a manager may have already sold what the filing shows. Use it for *thesis* and *direction*, not timing.

## Sources (primary first)

1. **SEC EDGAR** (authoritative): full-text search https://efts.sec.gov/LATEST/search-index?q=... or browse `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=<cik>&type=13F`. The `infotable.xml` / `form13f.xml` is the raw holdings. **Always reconcile a surprising number against the raw infotable** — secondary summaries drop positions (e.g. a fund's META line omitted by an aggregator).
2. **dataroma.com** — curated ~80 *value/long-only* super-investors; great for "grand portfolio" most-held + per-manager activity. Under-counts growth/quant/crypto.
3. **13f.info** — clean per-manager filing history with Q-over-Q share counts; best for computing deltas.
4. **whalewisdom.com** — heatmaps, most-held, ownership history (some pages gate/404).
5. **hedgefollow.com** — broader hedge-fund universe per-stock pages (who's buying/selling a ticker); catches multi-strats dataroma misses.

## The method

1. **Pin the quarter.** State explicitly which quarter (e.g. "Q1 2026, period 3/31/2026, filed ~5/15/2026"). If the newest quarter isn't aggregated yet, use the prior one and **say so**.
2. **Pull holdings** for each target manager from EDGAR (or 13f.info), capture: ticker, shares, market value, % of 13F AUM.
3. **Compute the delta** vs the *prior* quarter's filing per position → classify **NEW / ADDED / UNCHANGED / TRIMMED / EXITED** (EXITED = present last quarter, absent now). Deltas drive the insight; a static holding list does not.
4. **Map share classes:** GOOG↔GOOGL, BRK.A↔BRK.B, fund-specific ADRs (TSM, ASML NY registry). Treat as the same economic bet; note which class.
5. **Flag options:** if a line is a PUT, it's bearish/hedge — never count it as a long conviction buy (Burry frequently files puts).
6. **Infer WHY** (the point of the exercise): combine the position size, the delta, the manager's known style, and the name's setup. Examples:
   - Buffett *adding* GOOG at scale → quality + reasonable valuation conviction from a value lens.
   - Burry *initiating* a beaten-down non-AI name (PYPL, ADBE) → contrarian deep-value / mean-reversion.
   - Multiple unrelated funds *initiating the same name same quarter* (AVGO across Druckenmiller + Loeb + Tiger) → emerging consensus, higher signal.
   - Two respected funds on *opposite sides* (CVNA: Viking +162% vs Coatue −65%) → genuinely contested; lower signal, size small.
   - A marquee holder *exiting* a name you own (Baupost exits FIS, Berkshire exits UNH) → a real caution flag worth a re-underwrite.
7. **Cross-reference a portfolio:** intersect the user's ticker list with each manager's current holdings. Report overlaps as a table: `ticker | fund | size | action | one-line why`. Then bucket: (a) consensus-validated names, (b) divergences vs your own thesis, (c) **orphans** no fundamental fund owns (you're on your own — size for that).

## Output contract

Produce a table with columns: **Ticker · Fund · Size ($ or % of 13F) · Q/Q Action · Why/Note (+ filing quarter)**.
Then three callouts:
- **Consensus** — names multiple respected managers hold/added (cross-check passed).
- **Divergence** — where smart money disagrees with the held view (flag, don't auto-act).
- **Orphans** — names no tracked super-investor owns; thesis stands alone.

## Honesty rules (non-negotiable)

- **Never fabricate a share count, %, or action.** If a figure can't be verified against a filing/aggregator, write `unverified` and say what would confirm it (e.g. "pull infotable.xml from EDGAR CIK …").
- **Don't infer a thesis the manager didn't state** beyond what style + the trade plainly imply; label inference as inference.
- **State the lag every time.** A 13F overlap is a *lagging conviction cross-check*, not a buy/sell trigger. It complements `fundamental-analysis` (your own valuation gate), it does not replace it.
- Quant-shop ownership (Renaissance, Citadel, Millennium, Jane Street, AQR, DE Shaw, Two Sigma) is **statistical flow, not thesis** — flag it as low fundamental conviction, don't read it as a smart-money endorsement.

## Store the insight

13F reads are reusable and decay slowly (quarterly). Persist them so the next session builds on them:
- Write a dated overlap doc to `stocks/13f-overlap.md` (or the relevant book's folder) — table + the three callouts + the quarter pinned.
- Save a one-line memory pointer when a finding changes a position thesis (e.g. "Burry initiated PYPL Q1'26 — validates the deep-value hold"; "Berkshire + Viking both exited UNH Q1'26 — re-underwrite").
- On the next quarterly filing, **diff against the stored doc** rather than starting cold — the *change* in who-owns-what is itself the signal.

## Done when

A pinned-quarter overlap table exists with verified (or explicitly `unverified`) numbers, each row
has a WHY, the three callouts (consensus / divergence / orphan) are filled, and any thesis-changing
finding is persisted to a doc + a memory pointer.
