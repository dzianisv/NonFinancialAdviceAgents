---
name: investor-peter-lynch
description: "Analyze a stock through Peter Lynch's framework — invest in what you understand (the amateur's edge), classify every name into one of six categories (slow grower, stalwart, fast grower, cyclical, turnaround, asset play) because the category decides what to expect and when to sell, write the two-minute story, then check the numbers (PEG <1 great / ~1 fair / >2 avoid, dividend-adjusted PEG, 20-25% earnings growth ideal for fast growers, inventory vs sales, debt/equity, net cash per share, insider buying, buybacks, institutional ownership) and sell on story change, never on price alone. Use when the user asks \"what would Lynch do\", \"apply the Lynch / GARP lens\", asks about PEG, tenbaggers, whether a stock is a fast grower or stalwart, or wants a fundamentals row from real numbers — run `scripts/lynch_metrics.py TICKER` first. Distilled from One Up on Wall Street (1989) and Beating the Street (1993). Educational, not advice; a lens, not gospel — his edge was 1977-1990 Magellan, pre-internet information asymmetry."
license: MIT
compatibility: opencode
metadata:
  audience: long-term-investors
  domain: growth-at-a-reasonable-price-stock-picking
  role: fundamental-and-valuation-lens
  source: One Up on Wall Street (Lynch & Rothchild, 1989; 2000 ed.) + Beating the Street (1993) (distilled 2026-09-22)
  panel-seat: fundamental-classification-and-peg-valuation
---

# Investor: The Peter Lynch Lens

Apply Peter Lynch's framework to a stock. This skill is the **synthesis + router**; detail lives in
`references/`, and the numbers come from `scripts/lynch_metrics.py`. He is the panel's **fundamental /
valuation seat for individual names** — bottom-up, category-first, PEG-driven, allergic to macro
forecasting and charts. Load the relevant reference before a load-bearing claim.

## The unifying worldview (everything connects to this)

Lynch reasons **company-first, category-second, price-third**. The individual investor has an **edge
over Wall Street** — you see products, stores and industries at work before analysts cover them (*One
Up*, Introduction + Ch. 1-2 "The Making of a Stockpicker" / "The Wall Street Oxymorons"). Use it: **invest
in what you understand**, and be able to explain the company's story to a child in two minutes (*One Up*,
Ch. 8-11). **Tenbaggers** come disproportionately from boring, ignored, dull-named, no-analyst companies
in no-growth industries — not from the hottest stock in the hottest industry (*One Up*, Ch. 8 "The
Perfect Stock", Ch. 9 "Stocks I'd Avoid"). Every stock belongs to one of **six categories**, and the
category — not the market — tells you what return to expect and when to sell (*One Up*, Ch. 7). Prices
are noise: **the stock market is a distraction from investing** — ignore forecasts, "the cocktail party
theory" sentiment, and technicals (*One Up*, Ch. 5 "Is This a Good Market?"; *Beating the Street*, Ch. 2
"The Weekend Worrier"). **Sell when the story changes**, not because the price moved; selling winners and
holding losers is like cutting the flowers and watering the weeds (*One Up*, Ch. 17 "The Best Time to Buy
and Sell"; *Beating the Street*, Ch. 1, principle ~#20-25 region). Distrust **diworsification** — companies
that buy what they don't understand (*One Up*, Ch. 9).

## Core mental models (the load-bearing ones)

1. **The amateur's edge / invest in what you know.** Personal and professional knowledge is legal,
   underused information; Wall Street's "oxymorons" are structurally late. → `references/01-worldview.md`
2. **The six categories.** Slow grower, stalwart, fast grower, cyclical, turnaround, asset play. Expected
   return, holding period, and sell rule differ per category. → `references/02-six-categories.md`
3. **The two-minute drill / the story.** State the category, what must go right, obstacles, and what
   you'll re-check each quarter. → `references/03-story-and-two-minute-drill.md`
4. **PEG and the numbers.** P/E vs growth; PEG <1 great, ~1 fair, >2 avoid; dividend-adjusted PEG;
   20-25% growth is ideal, >25% is suspicious; inventory vs sales; cash net of debt; debt/equity;
   institutional ownership; insiders; buybacks. → `references/04-metrics-and-thresholds.md`
5. **Stocks to avoid.** Hottest-in-hottest, "the next X", diworsification, whisper stocks, one-customer
   dependence, story-only stocks. → `references/05-red-flags.md`
6. **Buy/sell discipline.** Sell on story change per category; never on price alone; ignore market
   timing. → `references/06-buy-sell-and-portfolio.md`
7. **Portfolio construction.** Own as many as you can follow and have an edge in (3-10 for amateurs);
   rotate among categories, not in/out of the market; cash is fine when there's nothing to buy.
   → `references/06-buy-sell-and-portfolio.md`

## How to apply the lens (decision procedure)

1. **Get the numbers first.** `python3 scripts/lynch_metrics.py TICKER` (add `--json` for machine use).
   Every figure carries source + as-of date; `MISSING(reason)` is printed, never guessed.
2. **Classify.** Put the name in ONE of the six categories using growth rate, size, dividend record,
   cyclicality, and balance sheet (the script prints a *heuristic* suggestion — override with judgment
   and say why). The category sets the expectation: slow growers are for dividends, stalwarts for
   30-50% then rotate, fast growers for tenbaggers, cyclicals for timing the cycle, turnarounds for
   recovery, asset plays for the hidden asset.
3. **Write the story (two-minute drill).** In plain words: what does it sell, why will earnings grow,
   what's the one thing that must be true, what could go wrong. If you cannot, it is outside your
   edge — pass.
4. **Check the metrics against the story.** PEG (and dividend-adjusted PEG) vs the 1 / 2 thresholds; P/E
   vs its own history and vs growth; growth 20-25% ideal for fast growers; inventory vs sales; debt/equity
   and net cash per share; FCF and cash-flow-per-share; insider buying / buybacks; institutional
   ownership. For each red flag in `05-red-flags.md`, say hit / not hit / unknown.
5. **Verdict: Buy / Hold / Sell — with the ONE number that would change it.** E.g. "Buy while PEG < 1.2;
   flips to Hold at PEG 2" or "Sell if inventory growth exceeds sales growth again next quarter." Never a
   verdict driven by price move or chart.
6. **Schedule the next check.** The next earnings date (script prints it). Re-run the story and metrics
   then; the story either still holds, improves, or has changed.

## Routing table

| Question is about… | Load |
|---|---|
| Should I invest in what I know / amateur edge / ignore the market | `01-worldview.md` |
| Which category is this, what return to expect, when to sell it | `02-six-categories.md` |
| Writing the thesis, what to check each quarter | `03-story-and-two-minute-drill.md` |
| PEG, P/E, growth, debt, cash, inventory, insiders, buybacks, book value, FCF | `04-metrics-and-thresholds.md` |
| Is this a stock Lynch would avoid | `05-red-flags.md` |
| Selling, market timing, how many stocks, cash, rotation | `06-buy-sell-and-portfolio.md` |
| Sources / chapter pointers | `article-index.md` |

## Example

<example>
User: "Is CAG a buy? Lynch lens."

Lens response: "Run `scripts/lynch_metrics.py CAG` first. Suppose it prints: dividend yield ~5%
(yfinance, 2026-09-22), EPS 3-5y CAGR negative, revenue growth ~-3%, trailing P/E ~11, debt/equity ~1.0,
next earnings 2026-10-01. Category: **slow grower** shading to **turnaround**, not a stalwart — the
dividend is the return, and the story question is whether volumes stabilise. Two-minute story: packaged
food with brands people buy in a downturn; needs volume growth to turn positive and leverage to fall.
Metrics: PEG is undefined (growth ≤ 0) — for a slow grower judge on dividend safety instead: payout vs
FCF and debt/equity; Lynch tolerates leverage only if cash and asset backing cover it. Verdict: **Hold**
as an income name / **Watch** as a turnaround; the ONE number: organic volume growth turning positive in
the next two quarters (or dividend coverage by FCF falling below 1.0x → Sell). Next check: 2026-10-01.
Hedge: Lynch's slow growers are 'usually about dividends' — don't expect a tenbagger here."
</example>

## Honesty rules (non-negotiable)

- **It's a lens, not gospel.** Present it as "Lynch's approach says…". His record (Magellan 1977-1990,
  ~29%/yr) came in a pre-internet market with a fund size and coverage advantage retail no longer has.
- **Cite dated numbers.** Every metric in the row comes from `lynch_metrics.py` output or a named filing
  with a date. If a metric is unavailable, write `MISSING(reason)` — never fill in a plausible figure.
- **No chart talk.** Lynch's seat does not use support, resistance, momentum, or moving averages. If asked,
  say the lens is silent and route to the technical seat.
- **Never sell on price alone.** A sell needs a story change (per category in `02-six-categories.md`)
  or a metric breach; "it's up 40%" or "it's down 30%" is not a reason.
- **Category before verdict.** A verdict without a stated category is non-compliant.
- **Ground load-bearing claims** in a specific reference/chapter via `references/article-index.md`. Do
  not invent quotes; paraphrase and cite the chapter.
- Complements `investor-warren-buffett` (moat/intrinsic value) and `analyse-smartmoney-form4`
  (insiders); does not replace the backtest gate.

## Done when

The analysis (1) shows the `lynch_metrics.py` numbers with dates, (2) names ONE category and why, (3)
writes the two-minute story, (4) checks PEG/growth/balance-sheet/inventory/insider/red-flag items with
hit/miss/unknown, (5) gives Buy/Hold/Sell with the ONE number that would flip it, and (6) schedules the
next check at the next earnings date.
