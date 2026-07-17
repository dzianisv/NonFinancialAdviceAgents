---
name: stocks-advisor-fast
description: Analyze stocks with a strict buy/hold/sell framework that separates business quality, valuation, technical entry, smart money, news, and analyst research. Use when the user wants a skeptical current-stock review with a specific focus on whether today is a good entry point.
---
Create a table with stocks as columns.
Use plain English. Keep it short. Be skeptical. Use current data. State the date and time of the data pull.
For each stock, research:

- Current price
- % change today
- % off 52-week high
- 5-day move
- 1-month move
- 6-month move
- Market cap
- P/E or forward P/E
- Latest quarterly earnings, revenue, and margin trend
- When will be next earnings call
- Recent analyst target changes
- Target range: low / average / high
- Hedge fund, insider, or short-seller activity in last 30 days
- Strongest bearish case

Use these rows:
- Position
- Fundamental Analysis
- Valuation Check
- Cycle Risk
- Technical Analysis / Entry Price
- Smart Money
- News Narrative
- Research Frims Consensus
- Research Firm View
- AI TipRank Forecast
- Main Bull Case
- Main Bear Case
- Conflict Flag
- Final Verdict

# Rules:
Buy means: good business, fair entry, trend not broken, upside still available.
Do not rate Buy just because the company is good.
Hold is valid when signals conflict.
If fundamentals are good but technicals are weak, usually Hold.
Do not invent claims without a source.
If source is missing, stale, or paywalled, say so.
Be skeptical of hype and post-rally optimism.
Keep each row short and specific.
For each row, give Buy / Hold / Sell.

# Smart Money 
Form 4 insider trades — SEC EDGAR search.
 https://www.sec.gov/search-filings
13F institutional holdings — SEC 13F data sets.
 https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets
13D / 13G big holders and activists — Investor.gov explains the filings and the 5% rule.
 https://www.investor.gov/introduction-investing/investing-basics/glossary/schedules-13d-and-13g
Short interest — Nasdaq short-interest release pages.
 https://www.nasdaq.com/press-release/ plus the company/period short-interest release pages.
8-K material events — SEC EDGAR search.
 https://www.sec.gov/search-filing

SEC EDGAR search (https://www.sec.gov/search-filings) for Form 4, 8-K, 13D/13G, and other filings. SEC also has public 13F data sets (https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets).
Investor.gov 13D/13G guide (https://www.investor.gov/introduction-investing/investing-basics/glossary/schedules-13d-and-13g) for a simple read on big holders and activists.
HoldingsChannel (https://www.holdingschannel.com/) for easy public 13F summaries from SEC filings.
WhaleWisdom (https://whalewisdom.com/) for 13F/13D/G tracking; useful, but some access is subscription-based.
EDGAR Atlas (https://edgar-atlas.com/) for a cleaner public view of insider activity, 8-Ks, and recent filings.
SecFilingDex (https://secfilingdex.com/) for faster SEC filing lookup with direct accession links.
Cboe U.S. Options Market Volume Summary (https://www.cboe.com/us/options/market_share/market/) for public options-volume / flow proxy.
Nasdaq short-interest releases (https://www.nasdaq.com/press-release/) for public short-interest updates.

Public Disclosures
https://disclosures-clerk.house.gov/PublicDisclosure
https://ethics.house.gov/financial-disclosure/
https://efd.senate.gov
https://efdsearch.senate.gov/search/home/


# Narative
Here are the cleanest public headline / feed pages I found. Morningstar documents RSS directly, FT has an open RSS-friendly Alphaville feed, Bloomberg markets and reporter pages show RSS feed links, and WSJ feed directories list public RSS endpoints.

## Financial Times
https://www.ft.com/markets
https://www.ft.com/companies
https://www.ft.com/world
## Reuters
https://www.reuters.com/finance
https://www.reuters.com/finance/markets
## Bloomberg
https://www.bloomberg.com/markets
https://www.bloomberg.com/authors/AU3gvCkensI/maria-eloisa-capurro
https://www.bloomberg.com/authors/AQhUYfOEw20/jonathan-ferro
## Wall Street Journal
https://wsj.com/finance
https://wsj.com/world
https://wsj.com/business
https://feeds.content.dowjones.io/public/rss/RSSMarketsMain
https://feeds.content.dowjones.io/public/rss/RSSWorldNews
## Morningstar
https://www.morningstar.com/stocks/xnas/${ticker}/news
https://www.morningstar.com/stocks
https://www.morningstar.com/funds
https://suppliers.morningstar.com/investor-relations/resources/rss/default.aspx
https://my.morningstar.com/my/feeds/rssintro.aspx

## TipRanks
https://www.tipranks.com/stocks/${ticker}/stock-news

## SeekingAlpha
https://seekingalpha.com/symbol/${ticker}
https://seekingalpha.com/stock-ideas
https://seekingalpha.com/editors-picks


# Research Firms Consenus
Use https://www.tipranks.com/stocks/${ticker}/forecast to get Stock Forecast & Price Target.
Use report just form top researches:
1/ JPMorgan
2/ Morgan Stanley
3/ Goldman Sachs
4/ BofA Securities
5/ Morningstar
6/ Citi
7/ Barclays

Consensus source order: 1. TipRanks forecast page 2. Named firms only: JPMorgan, Morgan Stanley, Goldman Sachs, BofA, Morningstar 3. Citi / Barclays only if available 4. If none of the above are available, say “source coverage incomplete” and stop Rules: - Do not use MarketBeat for consensus unless explicitly asked. - Do not substitute any other analyst-summary site for TipRanks. - Do not infer consensus from news articles or price pages. - Before writing the final verdict, verify the consensus row used the required sources.


# AI TipRank Forecast
https://www.tipranks.com/stocks/${ticker}/stock-analysis


# Research Firm View:
Check Morningstar, JPMorgan Research, Morgan Stanley Research, Goldman Sachs Research, and Bank of America Securities if available.
Use the firm’s own research page or published analyst note when possible.
Summarize the latest bullish and bearish views.
Mention recent rating or target changes when available.
If no recent coverage is found, say so.
## Resource URLs:
https://www.morningstar.com/
https://www.jpmorgan.com/insights/research
https://www.morganstanley.com/what-we-do/research
https://www.goldmansachs.com/insights/goldman-sachs-research
https://bofainsight.bankofamerica.com/



# Final Verdict:
Buy only if fundamentals are strong, valuation is fair, technicals are acceptable, smart-money/news risk is not negative, and upside is credible.
Hold if signals conflict or entry is poor.
Sell if fundamentals weaken, valuation is stretched, technicals break down, or bear risk dominates.
End with:
Confidence level: Low / Medium / High
Biggest thing to watch next
One sentence on what would change the verdict


