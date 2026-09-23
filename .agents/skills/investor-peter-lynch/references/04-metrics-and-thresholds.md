# Metrics Checklist — Lynch's Numbers and the Thresholds He Actually Gave
> Source: *One Up on Wall Street* Ch. 10 "Earnings, Earnings, Earnings" (P/E, growth), Ch. 13 "Some Famous Numbers" (percent of sales, PEG, dividend-adjusted PEG, cash position, debt factor, dividends, book value, hidden assets, cash flow, inventories, pension plans, growth rate, the bottom line), Ch. 15 "The Final Checklist"; *Beating the Street* Ch. 1 (25 Golden Rules), Ch. 10-12 (S&Ls; book value and equity/assets), Ch. 16 (cyclicals). Distilled 2026-09-22. Thresholds below are the ones he stated; where he gave a rule of thumb rather than a number, that is said.

## Core thesis
Earnings and assets are what a stock is ultimately worth (Ch. 10). The price is only interesting relative to earnings and their growth. The numbers are a checklist to test the story, and the balance sheet is the first thing to read.

## The checklist with thresholds

| # | Metric | Lynch's rule (chapter) | How the script computes it |
|---|---|---|---|
| 1 | **P/E vs growth rate** | The P/E of a fairly priced company equals its earnings growth rate (Ch. 10; Ch. 13 "Growth rate"). P/E at half the growth rate is very positive; P/E at twice the growth rate is very negative. Also compare the P/E to the company's **own historical range** and to the industry; a P/E far above its own history is a warning (Ch. 10). | trailing P/E (yfinance), forward P/E (yfinance), EPS growth TTM-YoY and 3-5y CAGR (yfinance annual EPS, fallback SEC XBRL `EarningsPerShareDiluted`). |
| 2 | **PEG** | P/E ÷ long-term earnings growth: **<1 is a bargain, ~1 fair, ≥2 avoid** (Ch. 13, "Growth rate"; the 0.5 / 1 / 2 framing). Use a multi-year growth rate, not one hot year. Not meaningful for cyclicals at peak earnings or for negative growth. | `PEG = trailing P/E ÷ (EPS growth % using the 3-5y CAGR when available, else TTM)`; prints both bases. |
| 3 | **Dividend-adjusted PEG** | Add the dividend yield to the growth rate: (growth + yield) ÷ P/E — **<1 poor, 1.5 okay, ≥2 what you're looking for** (Ch. 13). Equivalently, P/E ÷ (growth + yield): **<0.5 great, ~0.67 okay, >1 poor**. | Both the Lynch ratio (growth+yield)/PE and its reciprocal are printed. |
| 4 | **Earnings growth rate (fast growers)** | 20-25%/yr is the ideal band; **>25% is suspicious** — usually a hot industry, hard to sustain, and the P/E is priced for it (Ch. 7; Ch. 13). Stalwarts ~10-12%; slow growers ~2-4%. | EPS growth CAGR and TTM; category heuristic uses these bands. |
| 5 | **Debt / equity ("the debt factor")** | Normal balance sheet: roughly 75% equity / 25% debt (Ch. 13, "The Debt Factor"). For **turnarounds**, debt is the survival question — Chrysler had >$1B cash vs manageable debt; judge **debt type** (bank/short-term "due on demand" is dangerous; long-term funded debt gives time). Lower is better; a company with no debt cannot go bankrupt. | total debt / shareholders' equity (yfinance balance sheet, fallback SEC XBRL); prints debt type split when available. |
| 6 | **Cash per share net of debt** | Net cash = cash + marketable securities − long-term debt, per share; subtract from price to find what you are paying for the operating business (Ch. 13, "The Cash Position", Ford example: $16.30/sh net cash vs $38 price). | (cash & ST investments − total debt) / shares; also price minus net cash. |
| 7 | **Inventory growth vs sales growth** | If inventories grow faster than sales, it is a red flag — goods are piling up (Ch. 13, "Inventories"; Ch. 14). Conversely, inventories falling at a depressed cyclical/turnaround is the first sign of a turn. | YoY inventory growth vs YoY revenue growth; flag `INVENTORY_OUTPACING_SALES` if inventory % > revenue % by a clear margin; `NO_INVENTORY` for asset-light firms. |
| 8 | **Institutional ownership** | Low institutional ownership and little analyst coverage is a positive (Ch. 8, "Perfect stock" attributes; Ch. 15). High institutional ownership means the story is discovered. | yfinance `heldPercentInstitutions`; no fixed threshold from Lynch — the script labels <30% low, >80% crowded (script heuristic, not his number). |
| 9 | **Insider buying / selling** | Insider **buying** is a strong positive — there is only one reason to buy (Ch. 8, Ch. 13 "Insiders"). Insider **selling** means little (taxes, diversification, tuition) *unless* many insiders sell at once. | `fetch_form4.py --days 90 --json` → open-market buy/sell counts and $ totals; 10b5-1 sales tagged. |
| 10 | **Buybacks** | The simplest, best way to reward shareholders; reduces share count and lifts EPS (Ch. 8, Ch. 13). Prefer to diworsification. | share count trend over 3-5 years (yfinance / SEC `dei:EntityCommonStockSharesOutstanding`), % change per year. |
| 11 | **Dividend record (stalwarts / slow growers)** | Prefer companies that have raised dividends for 20-30 years without interruption; dividend keeps a company from diworsifying; check that it can be maintained in a recession (Ch. 13, "Dividends"). | yield (yfinance), consecutive years of increases from the dividend history (yfinance actions), else MISSING. |
| 12 | **Book value / equity** | Book value is often unrelated to real value: inventories, plant, and goodwill can be overstated (a trap), while land, brands, patents, and old real estate can be understated (hidden assets) (Ch. 13, "Book Value", "More Hidden Assets"). Do not buy on P/B alone. For S&Ls/banks: equity/assets and book value matter more (*Beating the Street*, Ch. 10-12). | price/book printed with the caveat; no threshold. |
| 13 | **Hidden assets** | Real estate at cost, tax-loss carryforwards, subsidiary stakes, brand names, patents, subscriber bases, cash-rich parents — the asset-play category (Ch. 13). | Not computable from feeds → script prints `MANUAL_CHECK`. |
| 14 | **Free cash flow** | Cash left after capex; prefer companies that do not need heavy reinvestment to stay in place (Ch. 13, "Cash Flow"). | operating CF − capex (yfinance cashflow); FCF yield = FCF / market cap. |
| 15 | **Cash flow per share vs price ("10x rule")** | A $20 stock with $2/sh annual cash flow is a 10-to-1 ratio, the standard minimum; $20 with $4/sh (5-to-1) is exciting (Ch. 13, "Cash Flow"). | price / operating-CF-per-share; flags ≤5x as attractive, ~10x standard, >20x rich. |
| 16 | **Percent of sales** | If a product excites you, ask what percent of the company's sales it represents; a hit product in a giant is irrelevant to the stock (Ch. 13, "Percent of Sales"). | Not computable from feeds → `MANUAL_CHECK` (segment note from 10-K). |
| 17 | **Pension obligations** | For turnarounds, check that pension assets exceed vested liabilities (Ch. 13, "Pension Plans"). | `MANUAL_CHECK`. |

## How to APPLY (decision rules)
1. Read the balance sheet first: cash trend, debt trend, debt type. A turnaround that fails the survival gate stops here.
2. Compute PEG with a multi-year growth rate; if growth ≤ 0 or the company is a cyclical near peak earnings, print PEG as **not meaningful** and say why.
3. Compare P/E to the company's own 5-10 year range (script prints where available; else MISSING and check the 10-K/StockAnalysis manually).
4. Flag inventory > sales growth, share count rising, institutional ownership crowded, insider open-market buying/selling.
5. For each item mark **PASS / FAIL / N/A / MISSING**; a verdict must cite the failing items.
6. Carry the source and as-of date of every number into the written row.

## Caveats / where he hedges
- His thresholds are rules of thumb from a higher-rate, higher-inflation era (1989); P/E-equals-growth was a market-wide observation, not a law. Today's median P/Es are higher; use the relative logic (P/E vs own history, vs growth) rather than absolute cutoffs.
- PEG is fragile: small changes in the growth estimate swing it; he explicitly prefers a long-term rate.
- He warns that earnings can be managed and that "book value" is frequently fiction; he trusts cash flow and the balance sheet more than EPS in turnarounds.
- Institutional-ownership and analyst-coverage levels are structurally higher now (index funds); the "undiscovered" signal is weaker.
