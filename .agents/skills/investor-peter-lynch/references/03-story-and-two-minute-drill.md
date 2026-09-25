# The Story and the Two-Minute Drill — What Must Be True, What to Check Each Quarter
> Source: *One Up on Wall Street* Ch. 11 "The Two-Minute Drill", Ch. 12 "Getting the Facts" (calling the company, visiting, annual reports), Ch. 13 "Some Famous Numbers", Ch. 14 "Rechecking the Story", Ch. 15 "The Final Checklist"; *Beating the Street* Ch. 1 "25 Golden Rules" (esp. "know what you own and why you own it"). Distilled 2026-09-22.

## Core thesis
Before buying, you must be able to deliver a two-minute monologue covering: (1) why you are interested, (2) what has to happen for the company to succeed, (3) the pitfalls in its path. The story must fit the category (`02-six-categories.md`) — a slow grower's story is about the dividend, a fast grower's is about where growth comes from, a turnaround's is about survival and recovery, an asset play's is about the asset and the catalyst. A story you cannot tell is a stock you should not own. After buying, the job is to **recheck the story every few months** — the earnings report is the natural checkpoint — and ask whether it is still on track, improving, or broken.

## The two-minute drill — what a complete story contains (Ch. 11)
1. **Category** and the one-line reason the stock is interesting *in that category*.
2. **What must go right** — the specific driver of higher earnings: more stores, new product cycle, price increases, cost cuts, debt paydown, an asset being sold, the cycle turning.
3. **Evidence the driver is real** — is the formula proven in more than one location/market (the fast-grower test); has the company done this before; is it in the numbers already (same-store sales, margins, backlog)?
4. **Obstacles / what could go wrong** — competition, debt, one big customer, regulatory change, an unproven expansion.
5. **The price test** — is the P/E in line with growth (PEG), is it out of line with its own history (see `04-metrics-and-thresholds.md`)?
6. **What you will check next quarter** — the 2-3 numbers that would prove the story right or wrong.

## Where the facts come from (Ch. 12)
- The annual report: balance sheet first (cash vs long-term debt, both trends), then the 10-year summary of earnings and dividends. He reads the balance sheet in a couple of minutes before anything else.
- Investor relations: call and ask specific questions (what's the growth plan, how are inventories, how's the competition). Prepare so you sound informed.
- Visiting the company/stores: judge the product and the customers, not the executive suite.
- Brokerage research is fine for facts, dangerous for conclusions.

## Rechecking the story (Ch. 14) — the quarterly checklist
| Category | What to re-check each quarter |
|---|---|
| Slow grower | Dividend maintained/raised; payout ratio; no diworsification; earnings not shrinking. |
| Stalwart | Earnings growth still ~10-12%; P/E not stretched vs history; product pipeline; how it fared in the last downturn. |
| Fast grower | Earnings growth still ~20-25%; expansion still has room (units, geographies); same-store sales positive; P/E not above growth rate; institutional ownership not yet crowded; balance sheet still clean. |
| Cyclical | Inventories vs sales; pricing; industry capacity announcements; where in the cycle. |
| Turnaround | Cash vs debt trend; debt type; cost cuts landing; the core business showing signs of life; no new dilution. |
| Asset play | Asset still there and unencumbered; debt not eating it; any catalyst (sale, spinoff, insider/raider buying). |

## Story stages he describes (Ch. 14, fast growers)
- **Start-up**: riskiest; the formula is unproven.
- **Rapid expansion**: the safest and most profitable phase to own — the formula works and there is still room to replicate it.
- **Mature/saturation**: growth slows, the company looks for new ways to grow (often diworsification); reclassify.

## How to APPLY (decision rules)
1. Do not write a verdict until the six drill items above are filled in plainly. Mark any item you cannot fill in as **UNKNOWN**; two or more UNKNOWNs on load-bearing items = pass.
2. Write the *falsifiable* story: the 2-3 numbers to check next quarter and the values that would break the story.
3. Schedule the next check at the next earnings date (the `lynch_metrics.py` output prints it; write `MISSING` if not available and set a calendar date instead).
4. At each check, output one of: **story intact / story improving / story changed**. Only "story changed" (or a metric breach from `04`) justifies a sell.
5. If the story has become "the stock is up / down a lot", that is not a story — return to step 1.

## Caveats / where he hedges
- The two-minute drill is a discipline against sloppiness, not a guarantee; he admits many of his stories were wrong (~40%).
- IR calls and visits were more informative pre-Reg FD (2000); today the same questions are answered in the 10-K/10-Q and earnings calls — use those.
- Rechecking must be about the business, not the price; he warns explicitly (Ch. 18) against letting price moves masquerade as story changes.
