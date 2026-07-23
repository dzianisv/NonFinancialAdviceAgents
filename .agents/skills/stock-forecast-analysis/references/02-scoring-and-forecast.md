# 02 — Scoring rubric, section sub-scores & AI price target

How to turn each report section into a 0-100 sub-score, compose the headline 0-100 rating, and build the
AI's own 12-month target. **These weights and thresholds are OURS** — inferred from the report's visible
emphasis (`references/01`) and the anomalies literature — **not disclosed by TipRanks.** State that every
run. TipRanks' actual score is one LLM's opinion on a selectable model; we make ours transparent instead.

## Section weights (the 0-100 rating)

Derived from the NVDA report's own summary, which ranks its drivers: financials (heavy) > earnings call >
technicals (offset) > valuation (offset) > analyst support > risk/events.

| Sub-score | Weight | Why this weight |
|---|---|---|
| Financial statements (Income/Balance/CashFlow avg) | **35%** | The report leads with it; fundamentals/quality carry the most durable edge (Piotroski 2000, Novy-Marx 2013, Sloan 1996) |
| Earnings call & guidance | **20%** | The report cites it second; guidance direction + surprise drives PEAD (Bernard-Thomas 1989) |
| Technical momentum | **15%** | Named as the offset; 12-1 momentum is a real anomaly (Jegadeesh-Titman 1993) but noisy short-term |
| Valuation | **15%** | Named as an offset ("premium"); value premium is real but slow (Fama-French) |
| Analyst forecast support | **10%** | Corroboration only — consensus level is optimism-biased and weak standalone; revisions matter more |
| Risk & corporate events | **5%** | Tail/context, rarely the swing factor |

`rating = round(Σ wᵢ × subᵢ)`, clamp 0-100. **Missing sub-score → drop it and re-normalize the remaining
weights to sum to 1.** Never score a missing section 0.

**Outlook buckets (inferred, not published — see `references/01`):** `>=70 Outperform · 40-69 Neutral ·
<40 Underperform`.

## Per-section 0-100 scoring rules

### Financial Statement Overview (35%) — three 0-100 sub-scores, then average
Score each statement 0-100; the section sub-score is their mean (weight cash flow slightly higher if you
want to reward earnings quality). Anchor to concrete thresholds so it is reproducible, not vibes:

**Income Statement (0-100):** start 50.
- Gross margin vs sector: top-tercile +15, bottom −15.
- Operating margin trend (3y): rising +10, falling −10.
- Revenue growth (YoY): >25% +15, 10-25% +8, <0 −15.
- Net margin > 15% +10.
Clamp 0-100. (NVDA-like: 90s.)

**Balance Sheet (0-100):** start 50.
- Net debt/EBITDA: <0 (net cash) +20, <1 +10, >3 −15, >5 −25.
- Current ratio >1.5 +8; <1 −10.
- Equity trend rising +7.
- Goodwill/assets > 40% −8 (roll-up risk).
Clamp. (Low-debt compounder: 90s.)

**Cash Flow (0-100):** start 50.
- FCF margin (FCF/rev): >20% +20, 10-20% +10, <0 −20.
- FCF/net income (quality): >0.9 +12, <0.6 −12 (accruals red flag, Sloan 1996).
- OCF growth 3y positive +8.
- Buyback+dividend funded by FCF (not debt) +5.
Clamp.

### Earnings call & guidance (20%) → 0-100
Route to `hedgefund-jpmorgan-earnings` + transcript. Start 50.
- Last quarter: beat both rev & EPS +15; miss both −20; mixed 0.
- Guidance vs prior/consensus: raised +20, in-line +5, cut −25.
- Management call sentiment (transcript): clearly positive +10, negative −10.
- Capital returns announced (buyback/dividend raise) +5.
Clamp.

### Technical momentum (15%) → 0-100
Route to `analyse-technical` (`ta.py`). Start 50.
- Price vs 200-DMA: above +15, below −15.
- Price vs 50-DMA: above +8, below −8.
- MACD histogram: positive +8, negative −8.
- RSI: 45-65 +5 (healthy); >75 −8 (overbought); <30 −5 (weak, but possible washout).
- 12-1 momentum top-quintile +10, bottom-quintile −10.
Clamp. Report the Bullish/Neutral/Bearish sentiment label alongside.

### Valuation (15%) → 0-100
Route to `analyse-fundamental`. Start 55 (slightly generous — good companies deserve some premium).
- Fwd P/E vs 5-yr own median: cheap tercile +15, expensive tercile −15.
- PEG: <1 +12, 1-2 +3, >3 −12.
- P/FCF vs peers: cheap +10, expensive −10.
- EV/EBITDA vs sector: cheap +8, expensive −8.
Clamp. A premium name (NVDA) lands ~40-50 here — a deliberate offset, matching the real report.

### Analyst forecast support (10%) → 0-100
Route to `analyse-sellside`. Start 50.
- Consensus: Strong Buy +20, Buy +10, Hold 0, Sell −20.
- Net estimate revisions (30d): up >5% +15, down >5% −15 (revisions > level).
- Implied upside on **median** target: >25% +10, <0 −10.
Clamp. Note: this section corroborates; it does not set the AI target.

### Risk & corporate events (5%) → 0-100
Start 50.
- Risk-factor count vs sector norm: far above −8; new material risks added −10.
- Recent 8-K events net sentiment: positive +10, negative −10.
- Going-concern / restatement / SEC action language: −40 (hard flag).
Clamp.

## Confidence
- **HIGH** = 6/6 sub-scores present AND financials + earnings agree in direction.
- **MED** = 4-5 present, or top sub-scores mixed.
- **LOW** = exactly 4 present, or one sub-score dominates the rating.
- **INSUFFICIENT_DATA** = <4 sub-scores or <2 seats returned data → emit no rating/target.

## AI price target (the AI's own — must be able to diverge from consensus)

The whole point of the AI report is a target that can disagree with the Street (NVDA AI $223 vs consensus
$309.94). Build it fundamentals-and-price-anchored, only lightly tied to consensus:

```
justified_fwd_PE = clamp( sector_median_PE × quality_multiplier , floor, cap )
   quality_multiplier = 1 + 0.15·(financials_sub−50)/50 − 0.10·(valuation_premium_flag)
fundamental_anchor  = forward_EPS × justified_fwd_PE
momentum_anchor     = current_price × (1 + drift)         # drift = f(technical_sub): +0..+15% up, −0..−15% down
consensus_anchor    = median_analyst_target × (1 − shrink)  # shrink 0.20–0.30 toward price (optimism haircut)

AI_target = 0.55·fundamental_anchor + 0.30·momentum_anchor + 0.15·consensus_anchor
```

- **Action** label vs the prior AI target (or vs price if no prior): **Raised / Lowered / Reiterated**.
- **Always print the gap** to the analyst consensus and a one-line reason for divergence (premium
  valuation, weak technicals, guidance cut, etc.). The divergence is the signal, not a bug.
- If `forward_EPS` is `UNAVAIL`: drop the fundamental_anchor, widen to a **range** from the momentum and
  shrunk-consensus anchors, and flag reduced confidence. Never invent EPS.

## Bull / bear cases (Positive / Negative Factors)
- **Positive Factors** = the 2-3 highest-scoring sub-sections, each named (e.g. "Cash generation",
  "Guidance") with the driving number.
- **Negative Factors** = the 2-3 lowest-scoring, each named (e.g. "Premium valuation", "Weak momentum").
- This is the transparent analogue of TipRanks' "Bulls Say / Bears Say" — every factor shows its number.

## Why these departures from a naive TipRanks clone (the honest edge)
- **Revisions over levels** for the analyst section — static Buy/Hold is optimism-biased and weak
  standalone (Barber-Lehavy-McNichols-Trueman); the *change* carries the signal.
- **Valuation as a real offset** — a premium name should lose points here even if fundamentals are elite;
  this is exactly what the live NVDA report does ("valuation remaining premium").
- **Shrink the consensus target** — mean sell-side targets are structurally optimistic; shrinking toward
  price corrects it and is what lets the AI target diverge downward like the real product.
- **Accruals / FCF-quality check** in the cash-flow score — guards against high-reported-earnings,
  low-cash traps (Sloan 1996).

## Academic anchors (cited by name; verify before quoting a number)
Jegadeesh-Titman (1993, momentum); Carhart (1997); Bernard-Thomas (1989, PEAD); Chan-Jegadeesh-Lakonishok
(1996, revisions); Piotroski (2000, F-score); Sloan (1996, accruals); Novy-Marx (2013, gross profitability);
Barber-Lehavy-McNichols-Trueman (analyst recs); Da-Engelberg-Gao (2011, attention).
