---
name: stock-forecast-analysis
description: "Reproduces TipRanks' AI Stock Analysis report (the /stocks/{ticker}/stock-analysis page) for one US equity — an LLM-synthesized 0-100 rating (>=70 Outperform / 40-69 Neutral / <40 Underperform), the AI's OWN 12-month price target (distinct from analyst consensus), Positive/Negative Factors, and the full section stack: Business Overview, Financial Statement Overview with Income/Balance/CashFlow sub-scores (0-100), Technical Analysis (MAs/MACD/RSI/STOCH), Valuation & KPIs, Analyst Forecast, Earnings Call Summary + guidance, Risk Analysis, Peer Comparison, Corporate Events. Conductor: routes each section to an existing analyse-* / earnings / news seat, then synthesizes a transparent, weight-disclosed score. Use for \"analyse/forecast stock X\", \"AI stock analysis of X\", \"what's the outlook / rating / price target on X\", \"is X outperform\". Educational, AI-generated, may contain errors, not advice; analysis is not a trade trigger — route live orders through strategy-discovery-backtest."
license: MIT
compatibility: opencode
metadata:
  audience: equity-allocators-and-stock-pickers
  domain: ai-equity-analysis-report-generation
  role: tipranks-ai-analyst-report-conductor
  source: "Reverse-engineered from the live TipRanks AI Stock Analysis report (https://www.tipranks.com/stocks/{ticker}/stock-analysis, NVDA/AAPL fetched 2026-07-20) + glossary/a/ai-stock-analysis. TipRanks does not disclose its score weights or LLM prompt; the section weights here are ours, inferred from the report's own emphasis, not theirs. See references/."
---

# Stock Forecast Analysis — reproduce the TipRanks AI Analyst Report (conductor)

Generate the same report a user sees on **`https://www.tipranks.com/stocks/{ticker}/stock-analysis`**: an LLM-synthesized **0-100 rating**, the AI's **own 12-month price target**, **Positive / Negative Factors**, and the full multi-section report. This is a **conductor lens** — it does not fetch raw data itself; it routes each report section to an existing seat (context-firewall subagents), then the main agent (the "AI analyst") synthesizes the rating, target, and narrative.

> AI-generated. May contain errors. Educational only — not advice and **not a trade trigger**. Under Law #0 any actual "buy/sell X" routes through `strategy-discovery-backtest` first. Re-pull before acting.

## Copy the RIGHT product (this is the mistake to avoid)

TipRanks runs **two** different products; do not conflate them:

| | **Smart Score** (`/stocks/{ticker}`) | **AI Stock Analysis** (`/stocks/{ticker}/stock-analysis`) ← **this skill** |
|---|---|---|
| Score | **1-10** quantitative | **0-100**, LLM-generated (selectable model) |
| Method | 8 fixed factors, weighted formula | LLM synthesizes structured data into a report + score + target |
| Inputs | analyst ratings, insider Form-4, blogger, crowd, 13F, news, technicals, fundamentals | **financial statements, earnings-call transcript, SEC 8-K filings, technical indicators, peers** |
| Price target | n/a (Smart Score has none) | the **AI's own** target, which routinely **diverges** from analyst consensus (live NVDA: AI $223 vs consensus $309.94) |
| Output | one number + factor bars | a **multi-section narrative report** (below) |

This skill reproduces the **AI Stock Analysis report**. It does **not** lean on 13F / Form-4 / blogger / crowd sentiment — those are Smart Score factors and are visibly absent from the AI report's drivers. If the user wants the 1-10 Smart Score instead, tell them and route to `analyse-sellside` + `analyse-smartmoney` + `analyse-fundamental`.

## The report sections → seat routing

The AI report is a fixed section stack. Reproduce every section; route each to its owning seat via a subagent, then synthesize. Grounding sources and section weights are in `references/`.

| Report section (verbatim from the page) | Owning seat / source (route here) | What it contributes |
|---|---|---|
| **Rating (0-100) + Outperform/Neutral/Underperform** | the conductor (synthesis) | headline score — composed from the sub-scores below |
| **AI Price Target + Action (Reiterated/Raised/Lowered)** | the conductor + `analyse-technical` (price), `analyse-fundamental` (fair value) | AI's own 12-mo target — **distinct** from consensus |
| **Summary + Positive Factors / Negative Factors** | the conductor (synthesis over all seats) | 2-3 named bull drivers + named bear drivers |
| **Business Overview & Revenue Model** | `analyse-fundamental` + `web_fetch` company profile | what the company does / how it makes money |
| **Financial Statement Overview** + **Income / Balance Sheet / Cash Flow sub-scores (0-100)** | `analyse-fundamental` (EDGAR XBRL / yfinance) | quality of the three statements, each scored 0-100 |
| **Technical Analysis** (50/100/200-DMA, MACD, RSI, STOCH, sentiment) | `analyse-technical` (`scripts/ta.py`) | trend + momentum read |
| **Valuation & KPIs** (P/E, PEG, P/B, P/S, P/FCF, EV ratios, div yield, growth) | `analyse-fundamental` | valuation context |
| **Analyst Forecast** (consensus, 1Y target, # analysts, EPS/Rev FY) | `analyse-sellside` | the *consensus* view — shown as context, NOT the AI target |
| **Earnings Call Summary + sentiment + Company Guidance** | `hedgefund-jpmorgan-earnings` + transcript `web_fetch` | latest call: positive/negative updates + guidance figures |
| **Risk Analysis** (# risk factors, top category, new risks) | `web_fetch` latest 10-K/10-Q risk factors (EDGAR) | disclosed risk profile |
| **Peer Comparison** (peer 0-100 ratings + financials table) | run this skill's scoring across 3-5 peers | relative standing |
| **Corporate Events** (recent 8-K, sentiment-tagged) | `read-news` / `web_fetch` EDGAR 8-K feed | material recent events |

Section weights for the 0-100 score are a **default we chose** (inferred from the report's own emphasis — see `references/02`), not disclosed by TipRanks. State this every run.

## The 0-100 score composition (transparent — TipRanks' is not)

TipRanks' NVDA report literally explains its own score: *"scores highly due to outstanding financial performance (profitability, cash flow, balance sheet strength) and an earnings call that reinforced strong guidance… main offset is weak near-term technical momentum… valuation remaining premium and a very low dividend yield."* That tells us the visible drivers. Reproduce with an explicit weighting (0-100 each sub-score, weighted sum):

| Sub-score (0-100) | Weight | Seat | Driver |
|---|---|---|---|
| **Financial statements** (avg of Income/Balance/CashFlow sub-scores) | **35%** | `analyse-fundamental` | profitability, margins, leverage, cash generation, earnings quality |
| **Earnings call & guidance** | **20%** | `hedgefund-jpmorgan-earnings` | beat/miss, guidance direction, demand visibility, capital returns |
| **Technical momentum** | **15%** | `analyse-technical` | price vs 50/100/200-DMA, MACD, RSI, STOCH |
| **Valuation** | **15%** | `analyse-fundamental` | P/E, PEG, P/FCF vs history & peers (premium = drag) |
| **Analyst forecast support** | **10%** | `analyse-sellside` | consensus rating + implied upside as corroboration |
| **Risk & corporate events** | **5%** | EDGAR / `read-news` | risk-factor load, event sentiment |

`rating = round(Σ wᵢ × subᵢ)`, clamped 0-100. **Outlook buckets (inferred from live data — 70→Outperform, 63/61→Neutral):** **>=70 Outperform · 40-69 Neutral · <40 Underperform.** The exact TipRanks threshold is undisclosed; state that we inferred ~70.

**Missing section = re-normalize the remaining weights**, never score a missing section 0 (that biases the rating down). If <4 of 6 sub-scores have data, cap confidence LOW.

## AI price target (the AI's own, not the consensus)

The defining feature of this report is a target that can **disagree** with Wall Street (NVDA: AI $223 vs consensus $309.94, a −28% gap). Build it independently, then show it beside the consensus:

- **AI target** = `0.55 × (forward EPS × justified forward P/E)` + `0.30 × (current price × (1 + momentum-drift))` + `0.15 × (median analyst target, shrunk 20-30% toward price)`. Fundamentals-and-price-anchored, only lightly tied to the optimistic consensus.
- **Action** label vs the prior target/price: **Raised / Lowered / Reiterated**.
- **Show both** the AI target and the analyst consensus target with the gap and a one-line reason for any divergence (e.g. "AI discounts consensus on premium valuation + weak technicals").

If forward EPS is `UNAVAIL`, widen the target to a range and say so — never invent EPS.

## Decision procedure

1. **Pin the run** — `ticker`, company name, `as_of`, `current_price` (from `ta.py` or a fetched quote).
2. **Fan out to the section seats** (subagents = context firewall). Each reads ONLY its `SKILL.md` and returns its section + the 1-3 numbers that drive its sub-score. The main agent never loads all raw data.
3. **Score each sub-score 0-100** per `references/02`; mark missing ones `UNAVAIL` and re-normalize weights.
4. **Compose the 0-100 rating**, label the outlook bucket, compute **confidence** from coverage.
5. **Build the AI price target** + Action; place it next to the analyst consensus with the gap.
6. **Write the narrative sections** in the TipRanks section order (Summary → Positive/Negative Factors → vs-SPY Snapshot → Forecast → Business Overview → Earnings Call → Financial Statement Overview + Breakdown table → Technical → Risk → Peers → Corporate Events), each sub-score shown as `<number> <word-label>`, every load-bearing figure cited to a page fetched **this run**.
7. **Peer comparison** — run steps 2-4 on 3-5 named peers (lighter pass) to place the ticker's rating in context.
8. **Skeptic gate (mandatory — hard invariant #6).** Spawn the `skeptic` skill on the target, the sub-scores, and any guidance/mechanics claims. Present only after PASS or all challenges resolved with fetched data.
9. **Emit the output contract**, dated, with the AI-generated caveat and invalidation.

## Grounding & anti-hallucination (non-negotiable)

- Every load-bearing number (a sub-score's driver, a guidance figure, a DMA, a target) must trace to a page a seat `web_fetch`ed **this run**, or to `ta.py` / `analyse-fundamental` output this run. No number from memory.
- Cite as `[Tn] https://exact-url (YYYY-MM-DD) — "verbatim figure"`. Source name alone is not a citation.
- **Never fabricate a TipRanks score, weight, or LLM prompt** — they are undisclosed. Our weights are ours; say so.
- Missing section = `UNAVAIL` (loud) + re-normalize; never a silent 0.
- If <2 seats return real data: output `INSUFFICIENT_DATA` — no rating, no target.

## Sub-score → word label (TipRanks prints a word next to every number)

TipRanks never shows a bare number; each 0-100 sub-score carries a sentiment word (live NVDA: Income `98 Very Positive`, Balance `94 Very Positive`, Cash Flow `96 Very Positive`). Reproduce that. The bands are **ours** (inferred — TipRanks doesn't publish them); state so once per run:

| Sub-score | Label |
|---|---|
| **>=85** | Very Positive |
| **70-84** | Positive |
| **45-69** | Neutral |
| **30-44** | Negative |
| **<30** | Very Negative |

The headline 0-100 rating keeps the **outlook** words (>=70 Outperform · 40-69 Neutral · <40 Underperform). Peer overall ratings in the peer table use the same outlook words.

## What each seat must return to fill the TipRanks layout

The terse "1-3 driver numbers" is not enough to render the report the way the page looks. Each seat returns its sub-score **plus** the display fields below (all cited, this run). Missing field = `UNAVAIL` (loud), never blank.

- **`analyse-fundamental` (financials):** the three sub-scores + the **multi-year Breakdown table** — TTM and up to 5 fiscal years for: Total Revenue, Gross Profit, EBITDA, Net Income, Total Assets, Cash & ST Investments, Total Debt, Total Liabilities, Stockholders Equity, Free Cash Flow, Operating Cash Flow. TipRanks shows this exact grid.
- **`analyse-fundamental` (snapshot + KPIs):** Market Cap, Dividend Yield, Avg Volume (3M), P/E, Beta, Revenue Growth, EPS Growth, Sector, Industry, Employees, Country; **Share Statistics** (EPS TTM, Shares Outstanding, 10/30-day avg volume); **Financial Highlights & Ratios** (PEG, P/B, P/S, P/FCF, EV/EBITDA, EV/Revenue).
- **`analyse-fundamental` / profile (business overview):** a **Company Description** paragraph + a **How the Company Makes Money** paragraph (segments / revenue model).
- **`analyse-technical`:** Sentiment word; Last Price; **Price Trends** 50/100/200-DMA each with value + Positive/Negative vs price; **Market Momentum** MACD/RSI/STOCH each with value + Positive/Negative/Neutral; a 2-3 sentence narrative like TipRanks writes.
- **`hedgefund-jpmorgan-earnings`:** Earnings Call Date + quarter tag + Next Earnings Date; Sentiment word; a summary paragraph; **Positive Updates** and **Negative Updates** each as *named* items (bold title + figure); a **Company Guidance** paragraph of the actual guided figures.
- **`analyse-sellside`:** the Forecast card — 1Y consensus target, upside %, Rating Consensus word, # Analysts, EPS Forecast (FY), Revenue Forecast (FY).
- **Risk seat (EDGAR):** the TipRanks sentence form — "<Company> disclosed **N** risk factors in its most recent report; the most in the '<category>' category" + "Latest Risks Added: **N** New Risks" + any material flag.
- **Peer seat:** each peer's overall 0-100 + outlook word, and a **Financial Indicators** table (Market Cap, P/E, ROE, Dividend Yield, Revenue Growth, EPS Growth), plus a Sector overall rating.
- **Corporate events:** dated, sentiment-tagged 8-K-derived events.

## Output contract (render in this TipRanks section order)

Emit clean Markdown — headings, cards, and tables so it reads like the page. Every `[T?]` is a real citation to a page fetched this run.

```
# <Company> (<TICKER>) — AI Stock Analysis        as-of <date> · <EXCH>:<TICKER> · last $<price>
Model: <model producing this>  ·  AI-generated, may contain errors  ·  weights are OURS, not TipRanks'

**Rating: <0-100>  <Outperform | Neutral | Underperform>**
**Price Target: $<t>   ▲/▼ (<u>% <Upside|Downside>)**   ·   Action: <Reiterated | Raised | Lowered>   ·   Date: <mm/dd/yy>
> vs Analyst Consensus $<c> (<consensus rating>, <n> analysts) — gap <g>%: <one-line why the AI target diverges>

<Summary — 3-4 sentences: the drivers that lift the score and the offsets that cap it.>

## Positive Factors
**<Named factor>** — <2-3 sentences with the driving number.>
**<Named factor>** — <2-3 sentences with the driving number.>

## Negative Factors
**<Named factor>** — <2-3 sentences with the driving number.>
**<Named factor>** — <2-3 sentences with the driving number.>

## <Company> vs. SPY — Snapshot
Market Cap <> · Dividend Yield <> · Avg Volume (3M) <> · P/E <> · Beta <> · Revenue Growth <> · EPS Growth <> · Sector <> · Industry <> · Employees <> · Country <>   [T?]
**Share Statistics:** EPS (TTM) <> · Shares Outstanding <> · 30-Day Avg Volume <>
**Financial Highlights & Ratios:** PEG <> · P/B <> · P/S <> · P/FCF <> · EV/EBITDA <> · EV/Revenue <>   [T?]

## Forecast  (analyst consensus — context, NOT the AI target)
1Y Price Target $<c> · Upside <u>% · Rating Consensus <Strong Buy..Sell> · # Analysts <n> · EPS Forecast (FY) <> · Revenue Forecast (FY) <>   [T?]

## Business Overview & Revenue Model
**Company Description:** <what the company does.>
**How the Company Makes Money:** <segments / revenue model.>   [T?]

## Earnings Call Summary — Sentiment <Positive | Neutral | Negative>
Earnings Call Date: <date> (<Qx-FY>)  ·  Next Earnings Date: <date>
<summary paragraph>
**Positive Updates:** **<named>** — <figure/why>
**Negative Updates:** **<named>** — <figure/why>
**Company Guidance:** <the guided figures — revenue, margin, EBITDA, units, capital returns.>   [T?]

## Financial Statement Overview
<summary sentence on statement quality.>
**Income Statement <0-100> <label>  ·  Balance Sheet <0-100> <label>  ·  Cash Flow <0-100> <label>**

| Breakdown            | TTM | FY<y> | FY<y-1> | FY<y-2> | FY<y-3> |
|----------------------|-----|-------|---------|---------|---------|
| Total Revenue        |     |       |         |         |         |
| Gross Profit         |     |       |         |         |         |
| EBITDA               |     |       |         |         |         |
| Net Income           |     |       |         |         |         |
| Total Assets         |     |       |         |         |         |
| Cash & ST Investments|     |       |         |         |         |
| Total Debt           |     |       |         |         |         |
| Stockholders Equity  |     |       |         |         |         |
| Free Cash Flow       |     |       |         |         |         |
| Operating Cash Flow  |     |       |         |         |         |
[T?]

## Technical Analysis — Sentiment <Bullish | Neutral | Bearish>
Last Price <x>
**Price Trends:** 50DMA <> (<Positive|Negative>) · 100DMA <> (<Positive|Negative>) · 200DMA <> (<Positive|Negative>)
**Market Momentum:** MACD <> (<Positive|Negative>) · RSI <> (<Neutral|Overbought|Oversold>) · STOCH <> (<Neutral|Overbought|Oversold>)
<2-3 sentence narrative read.>   [T?]

## Risk Analysis
<Company> disclosed <n> risk factors in its most recent report; the most in the "<category>" category. Latest Risks Added: <n> New Risks. <one-line material flag if any.>   [T?]

## Peers Comparison — Overall Rating
| Name   | Overall Rating       | Market Cap | P/E | ROE | Div Yield | Rev Growth | EPS Growth |
|--------|----------------------|------------|-----|-----|-----------|------------|------------|
| <TICKER> | <score> <outlook>  |            |     |     |           |            |            |
| <peer> | <score> <outlook>    |            |     |     |           |            |            |
Sector: <score>   [T?]

## Corporate Events
- <date> — <event> (<sentiment>)   [T?]

────────────────────────────────────────────────────────────
### Score Composition  (transparent — OUR weights; TipRanks' are undisclosed)
Financials 35%×<sub> · Earnings 20%×<sub> · Technicals 15%×<sub> · Valuation 15%×<sub> · Analyst 10%×<sub> · Risk/Events 5%×<sub> = **<0-100>**
Sub-score label bands (ours, inferred): >=85 Very Positive · 70-84 Positive · 45-69 Neutral · 30-44 Negative · <30 Very Negative
Outlook buckets (ours, inferred): >=70 Outperform · 40-69 Neutral · <40 Underperform
**Confidence:** <HIGH | MED | LOW>  (coverage <N>/6 sub-scores)
**Invalidation:** <the change that drops a bucket — e.g. "FY guidance cut or loss of 200-DMA → Underperform">
> **Disclaimer.** Automatically generated by an AI system; may contain inaccuracies — not financial
> advice. The score, weights, and label bands are OURS (inferred from the report's emphasis), NOT
> TipRanks'. Educational only, NOT a trade trigger — route live orders through
> strategy-discovery-backtest. Re-pull before acting.
```

**Confidence rule:** HIGH = 6/6 sub-scores present and financials+earnings agree in direction; MED = 4-5 present or mixed; LOW = 4 present or one sub-score dominates; `INSUFFICIENT_DATA` = <4 sub-scores or <2 seats returned data.

## Worked example

<example>
User: "Do the TipRanks AI stock analysis on NVDA."

<thinking>
This is the /stock-analysis report → reproduce the full section stack + 0-100 score + AI target.
Fan out to the seats, sub-score each section, compose, then skeptic-gate. Illustrative — re-pull live.
</thinking>

Fan-out (each from its seat, this run):
- `analyse-fundamental`: Income 98, Balance 94, Cash Flow 96 (rev TTM $253B, FCF $119B, low debt) → financials sub **96** [T1]. Valuation premium (P/E 31, P/FCF 47) → valuation sub **45** [T5].
- `analyse-technical` (`ta.py`): last 201.7; below 50DMA(209.8), above 200DMA(192.2); MACD +0.15 weak, RSI 48 → technicals sub **50**, Neutral [T2].
- `hedgefund-jpmorgan-earnings`: Q1 beat, guided Q2 rev $91B ±2%, record FCF, $80B buyback; call sentiment Positive → earnings sub **90** [T3].
- `analyse-sellside`: consensus Strong Buy, 1Y $309.94, 37 analysts → analyst sub **85** [T4].
- Risk/events: 24 risk factors, recent events positive (buyback, board) → risk/events sub **70** [T6].

Rating = .35(96)+.20(90)+.15(50)+.15(45)+.10(85)+.05(70) = 33.6+18+7.5+6.75+8.5+3.5 = **77.85 → 78 → Outperform.**
(Live TipRanks shows 79 — same bucket, transparent composition.)

AI target: fwd EPS 8.99 × justified P/E ~30 = $270; blended with price-drift and shrunk consensus → **~$235**, below the $309.94 consensus (AI discounts the premium valuation + weak technicals). Skeptic-gated before presenting.

```
# Nvidia (NVDA) — AI Stock Analysis        as-of 2026-07-20 · NASDAQ:NVDA · last $201.68
Model: Claude (conductor) + section seats  ·  AI-generated, may contain errors  ·  weights are OURS

**Rating: 78  Outperform**
**Price Target: ~$235   ▲ (16% Upside)**   ·   Action: Reiterated   ·   Date: 07/20/26
> vs Analyst Consensus $309.94 (Strong Buy, 37 analysts) — gap −24%: AI discounts premium valuation + soft technicals

Nvidia scores highly on outstanding profitability, cash generation, and balance-sheet strength, reinforced
by an earnings call that reaffirmed strong guidance and large shareholder returns. The offsets are weak
near-term technical momentum (below key moving averages, negative MACD) and a premium valuation.

## Positive Factors
**Product Leadership** — Repeated benchmark dominance and the fastest product ramp signal a durable edge,
driving preferential hyperscaler adoption, high switching costs, and platform lock-in.

## Negative Factors
**Premium Valuation** — At P/E ~31 and P/FCF ~47, the multiple already prices in years of flawless
execution, leaving little margin for a demand air-pocket.

## Financial Statement Overview
Best-in-class margins, growth, and cash generation; main risk is sustainability of elevated margins.
**Income Statement 98 Very Positive · Balance Sheet 94 Very Positive · Cash Flow 96 Very Positive**

| Breakdown       | TTM     | Jan 2026 | Jan 2025 |
|-----------------|---------|----------|----------|
| Total Revenue   | 253.49B | 215.94B  | 130.50B  |
| Net Income      | 159.61B | 120.07B  | 72.88B   |
| Free Cash Flow  | 119.08B | 96.68B   | 60.85B   |
[T1]

## Technical Analysis — Sentiment Neutral
Last Price 201.68
**Price Trends:** 50DMA 209.81 (Negative) · 100DMA 198.51 (Positive) · 200DMA 192.20 (Positive)
**Market Momentum:** MACD 0.15 (Negative) · RSI 48.22 (Neutral) · STOCH 72.47 (Neutral)
Below the 50-DMA but above the 200-DMA with soft MACD → a Neutral trend read.  [T2]

## Earnings Call Summary — Sentiment Positive
Earnings Call Date: May 20 2026 (Q1-2027) · Next Earnings Date: Aug 26 2026
**Company Guidance:** Q2 revenue $91B ±2%, non-GAAP gross margin ~75%, $80B buyback authorization, ~50% of
FCF returned.  [T3]

────────────────────────────────────────────────────────────
### Score Composition (transparent — OUR weights; TipRanks' undisclosed)
Financials 35%×96 · Earnings 20%×90 · Technicals 15%×50 · Valuation 15%×45 · Analyst 10%×85 · Risk/Events 5%×70 = **78**
**Confidence:** HIGH (6/6 sub-scores)   **Invalidation:** FY guidance cut or loss of 200-DMA → Neutral
> Disclaimer: AI-generated, may contain errors; weights/labels ours, not TipRanks'. Educational, not a trade trigger.
```
(Live TipRanks shows 79 — same bucket, transparent composition. The full run renders every section above,
each with its word-label and citation; this example is abridged.)
</example>

## Honesty rules

- **Reproduce the AI report, not the Smart Score** — 0-100, narrative sections, AI's own target. Do not slip 13F/Form-4/blogger/crowd back in; they belong to the other product.
- **State the section weights every run** and that they are ours (inferred), not TipRanks' (undisclosed — never invent them or the score threshold).
- **Show the AI target beside the consensus** with the gap — the divergence is the point, not an error to hide.
- **The AI report is LLM output** — label it as such, may contain errors (TipRanks says so on its own page).
- **Missing section = UNAVAIL + re-normalize**, never a silent 0.
- **Skeptic gate before presenting** any price level / guidance / mechanics claim — not optional.
- **Analysis ≠ trade.** No output here is an order; Law #0 routes live trades through `strategy-discovery-backtest`.
- **Date the read** + give the invalidation that drops a bucket.

## Done when

The analysis (1) pinned ticker/company/date/price, (2) **reproduced every AI-report section in TipRanks' order and visual style** (header rating card, Positive/Negative Factors as named titles, vs-SPY snapshot, Forecast card, Business Overview, Earnings Call with Positive/Negative Updates + Guidance, Financial Statement Overview with the multi-year Breakdown table, Technical, Risk, Peers table, Corporate Events) by routing to its seat via context-firewall subagents, (3) scored each section 0-100, **printed each as `<number> <word-label>`** (Very Positive…Very Negative), and marked missing ones `UNAVAIL` + re-normalized, (4) composed a **0-100 rating + Outperform/Neutral/Underperform** with the transparent weight breakdown shown, (5) built the **AI's own price target + Action** and displayed it beside the analyst consensus with the gap, (6) ran a **peer comparison**, (7) passed the **skeptic gate**, and (8) emitted the output contract dated, with the AI-generated caveat, confidence, and invalidation — never presenting the rating as a recommendation.
