---
name: hedgefund-morgan-stanley-dcf
description: "Morgan-Stanley-VP-style DCF valuation for ONE ticker. Pulls real historical financials (revenue, operating margin, FCF, capex, shares, beta, net debt) and builds an auditable 5-year discounted-cash-flow model: explicit revenue projection with stated growth assumptions, operating-margin path from the historical trend, year-by-year FCF, a WACC estimate showing the CAPM inputs, terminal value by BOTH exit-multiple and perpetuity-growth, a sensitivity table (fair value across discount rate x terminal growth), DCF-implied value vs market price, an under/fair/over-valued verdict, and the key assumptions that break the model. IB valuation-memo format with tables and explicit arithmetic. Every input is pulled at runtime (scripts/dcf_pull.py over yfinance) — no assumption is invented, all are grounded in pulled history and labelled. Triggers: \"run a DCF on <ticker>\", \"what's the intrinsic value of X\", \"is X over or undervalued\", \"discounted cash flow for X\", \"fair value estimate for X\"."
license: MIT
compatibility: opencode
metadata:
  audience: equity-allocators
  domain: equity-valuation
  role: valuation-analyst
  persona: morgan-stanley-vp
---

# hedgefund-morgan-stanley-dcf

Persona: a **Morgan Stanley VP** writing an investment-banking valuation memo. The persona is a **STYLE and
format, NOT a claim of affiliation** with Morgan Stanley — say so in the memo header.

## Input template (user fills this)

```
Persona: Morgan Stanley VP
Ticker: {ONE ticker}
(optional) Override assumptions: {e.g. "cap terminal growth at 2.5%", "use 5yr rev CAGR of 12%"}
```

One ticker per run. Output = an IB-style valuation memo with tables + explicit math (format below).

## No-fabrication guardrail (non-negotiable)

**Every number in this memo is either (a) pulled at runtime from `scripts/dcf_pull.py` (yfinance historical
financials), or (b) an ASSUMPTION explicitly labelled as such and grounded in that pulled history, with the
arithmetic shown so it is auditable.** No revenue figure, margin, FCF, beta, share count, or discount-rate
input is recalled from memory or invented. **If the core series (revenue) cannot be pulled, output
`INSUFFICIENT` and stop — do NOT produce a DCF on missing data.** If beta is missing, either state the
cost-of-equity assumption explicitly and show it, or output INSUFFICIENT — never silently fill a WACC input.

## Genuinely new (no DCF skill existed) — but still reuse the venv + snapshot

- **Historical series** (the DCF's raw material) → `scripts/dcf_pull.py` (this skill; yfinance financials,
  cashflow, balance sheet). This is the ONE place the numbers come from.
- **Current snapshot cross-check** (price, PE, analyst count) → `stocks-advisor`'s `fundamentals.py` if a
  second read is useful. Do not duplicate its logic.
- Uses the repo venv: `/Users/engineer/.venv/bin/python3`.

## Procedure

1. **Pull the real history:**
   ```bash
   mkdir -p .cache/hedgefund-dcf
   echo '{"symbol":"ORCL"}' > .cache/hedgefund-dcf/ORCL.in.json
   /Users/engineer/.venv/bin/python3 .agents/skills/hedgefund-morgan-stanley-dcf/scripts/dcf_pull.py \
     .cache/hedgefund-dcf/ORCL.in.json --out-dir .cache/hedgefund-dcf/
   # -> .cache/hedgefund-dcf/ORCL.dcf.json : revenue[], operating_margin[], free_cash_flow[], capex[],
   #    diluted_shares[], effective_tax_rate[], beta, shares_outstanding, net_debt, rev_cagr_pct, notes[]
   ```
   **Read `notes[]` first** — it flags the model-breakers (missing revenue → INSUFFICIENT; negative recent
   FCF → project from a normalized FCF and say so; missing beta → WACC caveat).

2. **Project 5 years of revenue — assumption, labelled and grounded.** Anchor the growth rate to the pulled
   `rev_cagr_pct` / `rev_yoy_pct` trend. State the exact rate(s) used and WHY (e.g. "FY1-2 at the trailing
   3yr CAGR X%, fading to Y% by FY5 toward GDP+"). Show each year: `Rev_t = Rev_{t-1} × (1+g_t)`.

3. **Operating-margin path — from the historical trend.** Use the pulled `operating_margin[]` series; hold
   flat at the trailing average, or ramp/compress with an explicit, justified reason. Show the assumed margin
   per year.

4. **Year-by-year FCF.** Build unlevered FCF explicitly:
   `EBIT_t = Rev_t × op_margin_t` → `NOPAT_t = EBIT_t × (1 − tax_rate)` (tax rate from pulled
   `effective_tax_rate[]`, stated) → `FCF_t = NOPAT_t + D&A − capex − ΔNWC`, using pulled capex/D&A intensity
   as % of revenue. If recent reported FCF is negative from a capex spike (see `notes[]`), normalize capex to
   a mid-cycle % and **state that explicitly** — a naive FCF-growth roll-forward is wrong here.

5. **WACC — show the CAPM inputs.** Cost of equity `Ke = Rf + β × ERP`; state Rf (cite a current 10yr yield
   source or label the assumption), pulled `beta`, and the equity risk premium used (label the assumption,
   ~4.5-5.5% typical — say which). Cost of debt from a cited/assumed rate × (1−tax). Weight by
   market cap vs `net_debt` (both pulled). Show the full `WACC = We·Ke + Wd·Kd·(1−t)` arithmetic.

6. **Terminal value — BOTH methods, show both:**
   - Perpetuity growth: `TV = FCF_5 × (1+g) / (WACC − g)`, g labelled (cap at long-run GDP ~2-3%).
   - Exit multiple: `TV = EBITDA_5 (or FCF_5) × exit_multiple`, multiple anchored to a cited peer/historical
     range. Report the implied-growth-vs-implied-multiple cross-check between the two.

7. **Discount to PV, bridge to per-share.** PV of FCF_1..5 + PV(TV) = enterprise value; `EV − net_debt =
   equity value`; `÷ shares_outstanding = fair value/share`. Show the discount factors.

8. **Sensitivity table** — fair value/share across a grid of **discount rate (rows) × terminal growth
   (cols)** (e.g. WACC ±1.5%, g 1.5-3.5%). This is the headline deliverable.

9. **Verdict** — DCF-implied fair value vs live market price: `UNDERVALUED / FAIRLY VALUED / OVERVALUED`
   with the % gap, then the **key assumptions that break the model** (the 2-3 inputs the valuation is most
   sensitive to, read off the sensitivity table + `notes[]`).

## Memo format

```
=== DCF VALUATION MEMO (Morgan Stanley lens) — <TICKER> — <YYYY-MM-DD> ===
(Style/persona only — NOT affiliated with Morgan Stanley. Educational, not advice.)
COMPANY / PRICE / SHARES / NET DEBT / BETA:   <pulled>
HISTORICAL (pulled, FY):   Revenue <..>  OpMargin% <..>  FCF <..>  Capex <..>   [asof yfinance]

ASSUMPTIONS (each labelled + grounded in the history above):
  Revenue growth:  FY1 <g1>% … FY5 <g5>%   (basis: <trailing CAGR / user override>)
  Operating margin: FY1 <m1>% … FY5 <m5>%  (basis: <trailing avg / ramp>)
  Tax rate: <t>%  (pulled eff. tax)   Capex: <c>% of rev  (basis)   ΔNWC: <..>
WACC:  Rf <..> + β <..> × ERP <..> = Ke <..>;  Kd <..>×(1−t);  We/Wd <..> → WACC <..>%

PROJECTED FCF (explicit):
  FY1..FY5  Rev → EBIT → NOPAT → FCF   (year-by-year table)

TERMINAL VALUE:
  Perpetuity (g=<..>): <..>    Exit-multiple (<x>×): <..>    cross-check: <..>

VALUE BRIDGE:  PV(FCF) <..> + PV(TV) <..> = EV <..>  − net debt <..> = equity <..>  ÷ shares = $<fair>/sh

SENSITIVITY ($/sh):     g=1.5%   2.0%   2.5%   3.0%   3.5%
  WACC <w-1.5>%          ...
  WACC <w>%              ...      <base>
  WACC <w+1.5>%          ...

VERDICT:  <UNDER/FAIR/OVER>-valued — fair $<x> vs market $<y> (<±z>%)
MODEL-BREAKERS:  <the 2-3 assumptions the value is most sensitive to; from sensitivity + notes[]>
DATA:  scripts/dcf_pull.py (yfinance) + <cited Rf/ERP/multiple sources> | asof <date>
```

If `dcf_pull.py` returned no revenue (or errored) → output only: `INSUFFICIENT — <reason from notes[]>`.

---
Educational, not financial advice. No leverage. Persona is a style, not a claim of firm affiliation.
