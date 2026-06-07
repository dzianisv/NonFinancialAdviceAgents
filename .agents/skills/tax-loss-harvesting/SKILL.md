---
name: tax-loss-harvesting
description: Practical playbook for tax-loss harvesting (TLH) with US broad-market index ETFs — selling positions at a loss to offset capital gains and up to $3,000/year of ordinary income, while staying invested via a "partner" ETF that tracks the same market without triggering wash sale rules. Use this whenever the user mentions tax-loss harvesting, TLH, wash sales, harvesting losses, swapping VOO for IVV or SPLG, offsetting capital gains, carrying forward losses, the $3K ordinary income deduction, or asks what to do with a position that's underwater in a taxable account. Trigger even when the user only describes the situation ("my VOO is down 18% and I have gains elsewhere this year, can I do something?") without using the term TLH. Always note this is general tax information, not personalized tax advice — a CPA should review before execution at meaningful dollar amounts.
license: MIT
compatibility: opencode
metadata:
  audience: retail-investors
  domain: personal-finance
  jurisdiction: us-federal
---

# Tax-Loss Harvesting (TLH) for Broad-Market Index ETFs

A practical playbook for harvesting capital losses on US broad-market index ETF positions (VOO, IVV, SPLG/SPYM, VTI, SPY, etc.) without losing market exposure, while staying compliant with the IRS wash sale rule.

## Mandatory framing

Always remind the user of the following:

- This is **general tax information**, not personalized tax advice. The user should consult a CPA before executing TLH at meaningful dollar amounts (>$10K of harvested loss).
- TLH only matters in **taxable brokerage accounts**. Inside IRAs, 401(k)s, HSAs, and other tax-advantaged accounts, losses are not harvestable and gains are not currently taxable.
- The "substantially identical" question for ETF-to-ETF swaps of the same index is the **consensus interpretation among tax practitioners but has never been explicitly ruled on by the IRS**. Conservative CPAs may recommend swapping to a different index.
- TLH is a tax-deferral strategy, not a tax-elimination strategy. The harvested loss reduces your cost basis in the new position, so future gains will be larger.

## What TLH is and why it works

TLH means selling a security at a loss to realize a capital loss for tax purposes. Realized losses can:

1. **Offset realized capital gains** dollar-for-dollar (short-term gains first, then long-term).
2. **Offset up to $3,000/year of ordinary income** if losses exceed gains.
3. **Carry forward indefinitely** into future tax years if not fully used.

For a high earner in a 37% federal + state bracket, harvesting a $50K loss against a $50K short-term gain can be worth ~$20K in real tax savings. The dollar value scales with the loss size and the user's marginal rate.

The catch: the user usually wants to *stay invested* in the same market. Selling VOO at a loss and sitting in cash means missing the rebound. The solution is to swap into a "partner" ETF — one that tracks essentially the same exposure but isn't legally "substantially identical."

## The wash sale rule (IRS Section 1091)

You cannot claim a capital loss if you buy a **substantially identical** security within the **30 days before or after** the sale. The disallowed loss gets added to the cost basis of the replacement shares (so it's not permanently lost — just deferred).

Key facts most users get wrong:
- **The 30-day window is symmetric** — 30 days before AND 30 days after the sale. So 61 days total around the harvest date.
- **The rule applies across all the user's accounts**, including their spouse's and their IRAs. Buying VOO in an IRA within 30 days of selling VOO at a loss in a taxable account triggers a wash sale.
- **Reinvested dividends count as purchases**. If the user has automatic dividend reinvestment on, dividends paid within 30 days of a loss-sale can trigger partial wash sales on the reinvested portion.
- **Buying the partner ETF is not a wash sale** if the two ETFs are not substantially identical (see below).

## Partner ETF strategy

The standard approach: hold one S&P 500 ETF as your primary position, and use a different S&P 500 ETF from another issuer as your TLH partner.

### Recommended pairs for the S&P 500
| Primary | Partner option A | Partner option B |
|---|---|---|
| VOO (Vanguard) | IVV (iShares/BlackRock) | SPLG/SPYM (State Street) |
| IVV (iShares) | VOO (Vanguard) | SPLG/SPYM (State Street) |
| SPLG/SPYM (State Street) | VOO (Vanguard) | IVV (iShares) |

All three track the S&P 500 with expense ratios of 0.02-0.03% and have essentially identical performance.

### Why these are (probably) not "substantially identical"
- Different issuers, different fund structures, different share lots.
- The tax community's consensus view: same-index ETFs from different issuers are not substantially identical.
- **Caveat:** the IRS has never explicitly ruled on this. A very conservative CPA might recommend a different-index partner.

### More conservative alternative: different index
If the user (or their CPA) wants extra safety, swap to a fund tracking a different but highly correlated index:
- **VTI** (Vanguard Total Stock Market) — tracks CRSP US Total Market Index. ~85% overlap with S&P 500 but adds mid/small-caps.
- **SCHB** (Schwab US Broad Market) — similar total-market exposure.
- **ITOT** (iShares Core S&P Total US Stock Market) — total market index.

These are unambiguously not substantially identical to an S&P 500 fund.

### Total US market primary positions
| Primary | Partner option A | Partner option B |
|---|---|---|
| VTI | ITOT | SCHB |
| ITOT | VTI | SCHB |

## The TLH workflow

When the user has an unrealized loss they want to harvest:

1. **Check the loss is worth harvesting.** Rule of thumb: at least 1-2% of position value as a loss, or $500-$1,000 minimum (depending on portfolio size). Trading costs and effort make tiny harvests not worthwhile.

2. **Check the 30-day window in both directions.** Has the user (or their spouse, or their IRA, or automatic dividend reinvestment) bought the same ETF in the last 30 days? If yes, harvesting now creates a partial wash sale on those shares. Either wait, or accept that portion of the loss won't be currently deductible.

3. **Turn off dividend reinvestment** on the position being sold. This prevents accidental wash sales from upcoming distributions.

4. **Sell the position with a loss** (specific-lot identification preferred — see below).

5. **Same day, buy the partner ETF** in equivalent dollar amount. Don't wait — you don't want to be out of the market during a recovery.

6. **Wait 31+ days** before making any further buys of the original ETF in any account.

7. **After 31 days, optionally swap back** to the original. This second swap is itself a small taxable event (gain or loss on the partner ETF holding period), so often not worth doing if the partner is an acceptable long-term holding.

8. **Track the harvested loss** for tax filing (your broker reports this on Form 1099-B in January, but verify).

## Specific-lot identification (critical)

If the user has accumulated the position over time, different share lots have different cost bases. To maximize harvested loss:

- Use **"Specific Lot ID"** or **"Highest In, First Out (HIFO)"** as the cost basis method.
- This sells the lots with the highest cost basis first, maximizing the realized loss.
- The default is usually **FIFO (First In, First Out)**, which is rarely optimal for TLH.
- Most brokers (Fidelity, Schwab, Vanguard, IBKR) let you change this per-account or per-trade. Set it before the sale, not after.

## How much harvested loss can the user use?

In a given tax year (current US tax law as of 2025-2026):

1. **Losses offset gains first**, in this order:
   - Short-term losses offset short-term gains.
   - Long-term losses offset long-term gains.
   - Excess of one type can offset the other.
2. **Up to $3,000 of net losses** offset ordinary income ($1,500 if married filing separately).
3. **Any remaining loss carries forward** to future years indefinitely with the same rules.

Practical implication: harvesting a $100K loss in one year when you have no gains saves you $3K of ordinary income that year (tax value: $3K × marginal rate) + $97K of carryforward usable against future gains. Still valuable, just not all at once.

## TLH in dip-tranche strategies

TLH pairs naturally with the dip-tranches buying strategy. When a market drawdown triggers Tier 2 or Tier 3 buys, the user likely also has older lots showing losses. Concretely:

- **On Tier 2+ triggers (-12% or worse):** check existing taxable positions for harvestable losses. Sell the underwater lots, buy the partner ETF. Then continue with the planned tier-buy in the partner ETF (or in the original, if outside the 30-day window of any prior buy — easier to just buy the partner).
- **Track which ETF is "current primary"** after a swap. After a TLH swap, the partner is now the primary, and the old primary becomes the available partner for the next harvest.

This is one of the few "free lunches" in retail investing — the same drawdown that triggers buying-the-dip can also generate meaningful tax savings.

## Common pitfalls

1. **The 401(k) wash sale trap.** If the user has S&P 500 exposure in their 401(k) (most target-date funds and most company default funds do), buying the same fund there within 30 days of a taxable-account loss-sale triggers a wash sale. Many 401(k) holdings are automatic (payroll contributions) and easy to forget.

2. **Spouse account wash sales.** A spouse buying the same ETF within 30 days also counts. This often surprises couples filing jointly.

3. **Robo-advisor TLH coordination.** Wealthfront, Betterment, and similar do automated TLH. If the user holds the same ETFs in a robo account and a self-managed account, the robo's auto-buys can trigger wash sales on the manual harvests. Resolution: use different ETFs across the two accounts.

4. **Holding partner ETF too short.** If the user swaps back from the partner to the original within 30 days at a gain, that's fine but realizes a short-term gain. Better: hold the partner for at least the 30-day window, ideally just keep holding it.

5. **Harvesting when bracket is unusually low.** TLH is most valuable in high-income years. If the user is in a low bracket this year (sabbatical, gap year, early retirement before SS), harvesting losses is less valuable than realizing gains at the 0% long-term capital gains rate (available below ~$47K single / ~$94K MFJ in 2025).

## State tax considerations

Most states with income tax conform to federal treatment of capital losses, but some have quirks:
- **California, New Jersey:** Capital losses can offset income similarly to federal.
- **States with no income tax (TX, FL, WA, etc.):** No state-level TLH benefit.
- **Some states have different $3K limits** or carryforward rules.

The user's CPA should check state rules. Federal benefit is the bulk of the value either way.

## Live data and automation

For implementing TLH detection in code, see **`references/data-sources.md`** in this skill. Key points:

- **TLH needs lot-level cost basis data, not just market prices.** This means the broker's API or CSV export — not public price feeds like yfinance.
- **Broker APIs with cost basis access:** Alpaca (free, US equities only), Interactive Brokers (TWS/Web API, comprehensive), Schwab (developer API post-TD migration). Fidelity and Vanguard have no retail API — use CSV export.
- **Public price data (yfinance, Alpha Vantage, Twelve Data, Polygon)** is only useful for the *current price* leg of the unrealized P/L computation. The user must supply or import the cost basis separately.
- **Wash-sale detection across accounts** is the hardest part — no single API sees taxable + IRA + spouse + 401(k) together. Most realistic solution: a simple spreadsheet log of all ETF buys across all accounts, scanned for matches within the 30-day window before any harvest.
- **Automation rule:** flag opportunities, don't auto-execute. The decision involves tax-year context, bracket forecasting, and wash-sale checks that benefit from human review.

Load `references/data-sources.md` when the user asks about: building a TLH scanner, broker APIs, cost basis tracking, wash-sale detection automation, or production implementation.

## How to apply this skill

When a user has a TLH scenario, walk through:

1. **Confirm it's a taxable account.** (If retirement account, stop here and explain why TLH doesn't apply.)

2. **Identify the position(s) and unrealized loss size.** Ask the user for current price, cost basis, and share count if not provided.

3. **Check the 30-day window.** Ask about recent buys of the same ETF in any of the user's accounts (taxable, IRA, 401(k), spouse).

4. **Recommend the partner ETF.** Use the table above.

5. **Walk through the mechanics:** turn off DRIP, set specific-lot ID to HIFO, place the sell, place the partner buy same-day, wait 31+ days before further buys.

6. **Estimate the tax value of the harvested loss** based on the user's marginal rate and current-year gains, if they share that info. Otherwise, explain the framework (offset gains first, then $3K/year vs ordinary, then carryforward).

7. **Remind the user about CPA review and the framing caveats** at the end.

## Quick worked example

User scenario: $300K in VOO with $50K unrealized loss. No recent buys of VOO anywhere. Has $30K of short-term realized gains elsewhere this year. Marginal rate ~32% federal + 5% state.

Steps:
1. Set cost basis method to specific-lot / HIFO on the VOO position.
2. Turn off VOO dividend reinvestment.
3. Sell the underwater VOO lots realizing $50K loss.
4. Same day, buy $250K of IVV (the remaining $250K of basis).
5. Wait 31 days before any further VOO purchases anywhere.

Tax impact:
- $30K of short-term gains fully offset by $30K of short-term loss (assuming the VOO lots are short-term; if long-term, this still works with slightly different ordering).
- $3K of remaining loss offsets ordinary income this year (~$1,110 federal savings + ~$150 state).
- $17K of loss carries forward to next year.
- Total current-year tax savings: roughly $30K × 32% (federal STCG rate matches ordinary) + $3K × 32% + state portion ≈ $11,500-12,000.

The user is fully invested in S&P 500 exposure the whole time, has just changed tickers from VOO to IVV.
