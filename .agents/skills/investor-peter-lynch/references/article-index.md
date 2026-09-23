# Peter Lynch — Source Index
> Compiled 2026-09-22 for the investor-peter-lynch Agent Skill. Primary corpus = two books (print / e-book; no free authoritative full-text URL — do not link pirated copies). Chapter titles below are from the published tables of contents; page numbers vary by edition, so references cite chapter, not page. No verbatim quotes are asserted beyond short, widely-reproduced phrases.

## A. Books (primary corpus)
| Work | Edition used | Chapters most relied on | Note |
|---|---|---|---|
| *One Up on Wall Street: How to Use What You Already Know to Make Money in the Market* — Peter Lynch with John Rothchild | Simon & Schuster 1989; Millennium ed. 2000 (new introduction) | Intro; Part I Ch. 1-5 (worldview, "Is This a Good Market? Please Don't Ask"); Part II Ch. 6-15 (Ch. 7 six categories; Ch. 8 perfect stock; Ch. 9 stocks I'd avoid; Ch. 10 earnings; Ch. 11 two-minute drill; Ch. 12 getting the facts; Ch. 13 some famous numbers; Ch. 14 rechecking the story; Ch. 15 final checklist); Part III Ch. 16-20 (portfolio, buy/sell, silliest things, options/futures/shorts). | Core of the lens. All thresholds in `04-metrics-and-thresholds.md` come from Ch. 10 and Ch. 13. |
| *Beating the Street* — Peter Lynch with John Rothchild | Simon & Schuster 1993 (rev. 1994) | Intro "Escape from Bondage"; Ch. 1 "The Miracle of St. Agnes" (25 Golden Rules at end of Ch. 1/in the book's closing); Ch. 2 "The Weekend Worrier"; Ch. 3 "A Tour of the Fund House"; Ch. 4-6 Magellan years; Ch. 8-17 sector/ case chapters (retail, restaurants, S&Ls Ch. 10-12, utilities, cyclicals Ch. 16 "Nuts and Bolts", Fannie Mae Ch. 18); "25 Golden Rules". | Applied cases and portfolio practice; source for "know what you own", rotation, number of stocks. |
| *Learn to Earn* — Lynch & Rothchild (1995) | — | Not used. | Beginner primer; nothing beyond the two above. |

## B. Secondary / verification (public, reachable 2026-09-22 unless noted)
| Item | URL | Note |
|---|---|---|
| Fidelity "Peter Lynch" investor page (Lynch's own rules/articles) | https://www.fidelity.com/learning-center/trading-investing/peter-lynch | Reachability not verified this run; Fidelity hosts Lynch's short essays on "invest in what you know", PEG. |
| Wikipedia — Peter Lynch | https://en.wikipedia.org/wiki/Peter_Lynch | Magellan record (1977-1990, ~29.2%/yr) and bibliography. |
| Wikipedia — PEG ratio | https://en.wikipedia.org/wiki/PEG_ratio | Attribution of PEG popularization to Lynch; the <1 / 1 / >2 framing. |
| PBS Frontline "Betting on the Market" interview (1996) | https://www.pbs.org/wgbh/pages/frontline/shows/betting/pros/lynch.html | Lynch on amateurs, "know what you own"; may be archived. |

## C. Data sources used by `scripts/lynch_metrics.py`
| Source | What | Note |
|---|---|---|
| yfinance (Yahoo Finance) | price, market cap, trailing/forward P/E, annual EPS/revenue/inventory/debt/cash/CF, dividends, institutional %, share count, earnings dates | Unofficial API; rate limits and missing fields are reported as MISSING with reason. |
| SEC EDGAR companyfacts (XBRL) `https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json` | fallback for EPS, revenue, inventory, debt, equity, shares | Requires User-Agent "name email" (env `SEC_UA`). US filers only (TSM is a 20-F filer: 10-K tags may be absent). |
| `analyse-smartmoney-form4/fetch_form4.py` | Form 4 open-market buys/sells, 90 days | Reused, not duplicated. |
