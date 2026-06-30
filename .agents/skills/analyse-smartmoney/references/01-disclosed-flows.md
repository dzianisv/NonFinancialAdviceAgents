# Disclosed Flows: 13F / 13D / Form 4 / PTR

Disclosed flows are the subset of smart-money signals that are **legally reported, binding, and traceable to a specific filer**. Unlike market-implied signals, these describe real capital committed by identifiable actors with skin-in-the-game accountability. The trade-off is lag: by the time a disclosure is public, the position may have changed.

---

## Form 4 — SEC Insider Transactions (fastest real-money feed)

**What it is.** Officers, directors, and 10%-or-greater shareholders of US public companies must report every purchase, sale, or option exercise within **2 business days** of the transaction. Filed on SEC EDGAR.

**Official free source.** https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=4 — also available in bulk at https://efts.sec.gov/LATEST/search-index?q=%22form+4%22

**What to extract.** Transaction type (purchase P vs. sale S), shares, price, whether the trade was open-market vs. automatic (Rule 10b5-1 plan), title of the filer (CEO/CFO weight higher than VP), and whether multiple insiders traded in the same direction within a short window (**cluster buy** or **cluster sell**).

**The read.** The academic literature (Seyhun 1998, Lakonishok-Lee 2001, Jeng-Metrick-Zeckhauser 2003, Cohen-Malloy-Pomorski 2012) establishes the following:

- **Buying is informative; selling is not.** Insider buying predicts excess returns of approximately +4–6%/year in the Lakonishok-Lee dataset. Insider selling does not significantly predict underperformance — insiders sell for liquidity, diversification, and tax reasons unrelated to their view.
- **Cluster buys dominate singles.** When three or more independent insiders at the same company buy in an open-market transaction within a 30-day window, the signal is meaningfully stronger than any single insider purchase.
- **CEO and CFO weight higher.** These officers have the broadest information set. A director-only buy at a large-cap is weaker than a CEO open-market purchase.
- **Opportunistic beats routine.** Cohen-Malloy-Pomorski (2012) distinguish opportunistic insiders (buy outside typical patterns) from routine insiders (buy on predictable schedules, likely diversification). Opportunistic insider returns are dramatically higher (~8% alpha) vs. routine traders (~1%).
- **Exclude Rule 10b5-1 automatic plans from the bullish read.** Pre-programmed sales are not informative about current management view.

**Lag and limits.** 2-business-day lag is the legal maximum; most trades are reported within 1–2 days of execution. The signal window is short — filing is not equivalent to the trade date. Cross-reference transaction date vs. filing date explicitly.

**Buy-side only asymmetry.** Because selling is uninformative directionally, the smart-money signal from Form 4 is **asymmetric**: cluster buys are the primary trigger. Cluster sells are a flag for *caution on longs* but not a reliable short signal.

---

## 13F — Institutional Holdings Quarterly Filings (long-only snapshot, 45-day lag)

**What it is.** Investment managers with ≥$100M in 13(f) securities must disclose their long-US-equity holdings quarterly, within 45 days of quarter-end. Filed on SEC EDGAR.

**Official free source.** https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=13F — or via bulk EDGAR API: https://data.sec.gov/submissions/

**What to extract.** Changes in share count quarter-over-quarter per filer, number of filers increasing vs. decreasing positions (breadth), concentration of new positions, and sector rotation signals.

**The read.** 13F clustering — when a large number of independent institutions increase a position in the same quarter — is the primary signal. A single large-fund 13F increase is noise; widespread accumulation across many independent mandates is pattern.

**Critical limits:**
- **45-day lag.** The filing describes positions as of quarter-end, published up to 45 days later. By the time you read it, the position may be partially or fully unwound.
- **Long-only, no shorts.** 13F reports long equity positions only. Short positions, options exposure (puts as protection), swaps, and non-US holdings are excluded or reported at notional, not net delta. A fund that appears to hold 10M shares of a stock may have an offsetting short position you cannot see.
- **Cloning-a-hedged-book pitfall.** The most dangerous 13F error is treating a reported long position as a clean directional bet when the fund may be long-equity / short-index or long-equity / long-put-protection. You are reading one leg of what may be a multi-leg strategy.
- **Cloning famous 13Fs is crowded.** Public 13F aggregators (Dataroma, WhaleWisdom, GuruFocus) index the same filings simultaneously. The edge in a famous manager's position from a filing published today has already been partially arbitraged.

---

## 13D / 13G — Activist and Large-Holder Filings (near-real-time for large stakes)

**What it is.** Any person or entity that acquires more than 5% of a public company's voting shares must file Schedule 13D (activist intent: intends to influence management) or 13G (passive: no intent to influence) within **10 calendar days** of crossing the 5% threshold. Amendments are required whenever material changes occur.

**Official free source.** https://efts.sec.gov/LATEST/search-index?q=%22SC+13D%22 and https://efts.sec.gov/LATEST/search-index?q=%22SC+13G%22

**What to extract.** Filer identity, percentage owned, stated purpose (Item 4 of 13D is the key — this is where activists disclose board replacement, merger, or strategic review intent), and subsequent amendments that signal accumulation or exit.

**The read.** 13D filings signal activist intent and are among the most powerful event-driven catalysts in disclosed flows because they combine real capital (≥5% stake = meaningful economic exposure) with stated intent to change corporate structure. 13G (passive) filings are accumulation signals from large institutions that have crossed a significant ownership threshold. Both are near-real-time for the initial crossing (10-day window), making them faster than 13F for detecting large position builds.

---

## PTR — Congressional STOCK Act Periodic Transaction Reports (alpha contested post-2012)

**What it is.** Under the STOCK Act (2012), US senators, representatives, and senior executive branch officials must report personal securities transactions within **45 days** of trade date (extended deadline from the original 30 days). Filed with:
- House: https://disclosures.house.gov/
- Senate: https://efts.senate.gov/

**What to extract.** Transaction type (purchase/sale), asset ticker, amount range (reports use ranges: $1K–$15K, $15K–$50K, $50K–$100K, $100K–$250K, $250K–$500K, $500K–$1M, >$1M), committee membership of the filer, and timing relative to known legislation or regulatory events.

**The read — with strong caveats.** Pre-STOCK Act academic research found significant alpha in congressional trades:
- Ziobrowski et al. (2004, 2011) found senators earned +6–12%/year excess return, representatives +6%/year — interpreted as information advantage from committee membership.
- Post-STOCK Act evidence is sharply weaker and contested: Eggers and Hainmueller (2013) found the edge largely disappeared after 2004; Chen and Sacerdote (NBER working paper 2024) find that post-STOCK Act congressional trades perform similarly to uninformed retail investors, with residual alpha concentrated in House and Senate leadership with oversight of specific sectors.

**Honesty flag.** Congressional PTR is the **lowest-reliability disclosed-flow signal** in this family. Treat it as a corroborating signal only when confirmed by higher-reliability flows (Form 4, 13F). Do not use PTR as a primary trigger. The 45-day lag combined with contested alpha means a congressional buy signal is weak evidence at best.

---

## Cross-signal reading for disclosed flows

When multiple disclosed-flow sources align, the weight of evidence is meaningfully higher than any single source. The following cross-signal reads are the most reliable:

| Pattern | Interpretation |
|---|---|
| Form 4 cluster buy + 13F institutional accumulation (same ticker, same period) | Strongest disclosed-flow ACC signal — insiders buying AND institutions increasing = two independent classes of real money converging |
| 13D activist filing + Form 4 cluster buy by incumbent management | Management buying after activist announcement = insiders expect the activist thesis to succeed, or are defending against forced sale at a low price |
| Congressional PTR buy alone | Weak signal; 45-day lag, contested alpha — treat as background color only |
| Form 4 cluster sell + 13F net reduction | Caution flag on longs, but selling is less informative than buying; confirm with market-implied signals before acting |

---

*Sources: Seyhun (1998), Lakonishok-Lee (2001), Jeng-Metrick-Zeckhauser (2003), Cohen-Malloy-Pomorski (2012), Ziobrowski et al. (2004, 2011), Eggers-Hainmueller (2013), Chen-Sacerdote NBER (2024). See `references/book-index.md` for full citations and honesty flags.*
