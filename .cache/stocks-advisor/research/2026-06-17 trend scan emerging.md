# Trend Stock Research — 2026-06-17

> **Hypothesis generation, NOT buy recommendations.** Educational analysis only.
> Each candidate requires multi-lens-quorum validation before any position sizing.
> Scanner = radar; journalism = judgment; this report = watchlist of hypotheses.

---

## Method

1. **Quantitative pre-screen** — `emerging_scan.py` (182-name universe): 73/182 outperforming SPY.
   Focus on EARLY MOVERS (6m return positive, <30% above 200d MA, positive acceleration)
   rather than EXTENDED names (semis: MU +324%, MRVL +230%, ARM +203% — too late).

2. **Thematic journalism reading** — 7 Google News RSS feeds (380+ articles scanned):
   transformer shortage, copper deficit, datacenter power/SMR, HBM bottleneck,
   defense backlogs, GOES electrical steel, cybersecurity demand.

3. **Deep article read** — POWER Magazine "Transformers in 2026: Shortage, Scramble, or
   Self-Inflicted Crisis?" (Jan 2026) — dense data on supply/demand imbalance.

4. **3-question skeptic filter** applied per candidate (see below).

---

## Scanner Snapshot (top early movers, not extended)

| Ticker | 6m Return | Accel | % Above 200d MA | Theme |
|--------|-----------|-------|-----------------|-------|
| OKTA   | +29%      | +24%  | +34%            | Cybersecurity / Identity |
| FCX    | +49%      | +4%   | +30%            | Copper deficit |
| NET    | +14%      | +14%  | +11%            | Edge security / AI |
| TDY    | +22%      | +3%   | +7%             | Defense electronics |
| CCJ    | +18%      | +1%   | +5%             | Uranium / Nuclear |
| LMT    | +13%      | +10%  | +1%             | Defense prime |
| DUK    | +11%      | +6%   | +3%             | Regulated utility + DC load |

**Not in scanner but thematically relevant:**

| Ticker | 6m Return | % Above 200d MA | Theme |
|--------|-----------|-----------------|-------|
| GEV    | +60%      | +28%            | Grid equipment (getting extended) |
| ETN    | +30%      | +11%            | Electrical infrastructure |
| CLF    | +3%       | +13%            | GOES steel monopoly (hasn't moved) |
| HUBB   | +18%      | +7%             | T&D electrical equipment |

**Explicitly excluded (too extended):**
MU (+324%), MRVL (+230%), ARM (+203%), INTC (+210%), AMD (+141%), CRWD (+45%/+40% above MA),
AMAT (+120%), LRCX (+130%), ON (+115%) — all AI/semi names, 78-161% above 200d MA.

---

## Theme 1: Transformer & T&D Equipment Supercycle

### Evidence (journalism-sourced)
- **POWER Magazine** (Jan 2026): Power-transformer demand up **119%** since 2019. Distribution up 34%.
  GSU demand up **274%**. Estimated **30% shortfall** for power transformers, 10% for distribution.
- Lead times: power transformers **128 weeks**, GSUs **144 weeks** (Wood Mackenzie Q2 2025).
- Prices: +77% power transformers, +45% GSUs, distribution up to +95% since 2019.
- **$1.8B in announced NA manufacturing expansions** — Hitachi ($1B+), Siemens ($150M Charlotte),
  Eaton ($340M SC), Prolec GE ($300M+), HD Hyundai Electric (+30% capacity by 2026).
- **55% of US distribution transformers** (~40M units) beyond expected service life.
- Not just transformers: HV switchgear +50%, MV circuit breakers +47% since 2021.
- **Energy News Beat** (Jun 16 2026): "US Grid Equipment Shortage Deepens."
- **TechCrunch**: Energy startup bet on 100-year-old grid tech paying off.
- **Fortune** (Jun 2026): "US AI Data Center Delays: 7 GW Capacity Crisis."

### Candidates

**ETN (Eaton) — Electrification infrastructure**
- $340M three-phase transformer factory (SC, target 2027). Data center power, EV charging.
- 6m: +30%, +11% above MA. Not yet crowded.
- *Skeptic filter:*
  1. Priced in? Partially — market knows data center demand. But $1.8B industry capex cycle is multi-year.
  2. Time horizon? 12-24 months (new factory production ramps 2027).
  3. What kills it? If data center buildout slows (regulatory, power access), or tariffs on copper/steel crush margins.
- **Confidence: 65%** — structural demand real, but P/E already elevated (~35x).

**HUBB (Hubbell) — T&D electrical equipment**
- Utility infrastructure spend: switchgear, breakers, transformers, wire. Grid modernization.
- 6m: +18%, +7% above MA. Under-followed relative to ETN.
- *Skeptic filter:*
  1. Priced in? Less than ETN — smaller, less AI-narrative coverage.
  2. Time horizon? 12-18 months (utility capex already accelerating).
  3. What kills it? Utility capex pullback, rate case compression, tariff-driven cost pressure.
- **Confidence: 60%** — solid secular tailwind, reasonable valuation, but niche.

---

## Theme 2: Copper Structural Deficit

### Evidence (journalism-sourced)
- **MiningVisuals** (Mar 2026): "Copper Market Balance: A Look at 2026 Deficit Forecasts."
- **S&P Global** (Jun 2026): "'Substantial Shortfall' in Copper Supply Widens as the Race for AI and
  Growing Defense Spending Add to Accelerating Demand."
- **CNBC**: "Copper shortage looms as tariff fears, mine disruptions fuel tightness."
- **Fortune**: "The future depends on copper, but a coming shortage makes it a 'systemic risk'."
- **CarbonCredits.com**: "Copper Prices Rise Past $14,000 as AI Demand, Peru Supply Shock, and
  Global Deficit Concerns Tighten Market."
- **Mining.com**: "Copper's next shortage is structural, not hype: analyst."
- **Reuters**: "Copper to hold gains in 2026 as mine disruptions fuel deficit."
- New mines take **10-15 years** from discovery to production. AI data centers + EVs + grid
  buildout (transformers need copper) compound structural demand.

### Candidate

**FCX (Freeport-McMoRan) — Largest public copper miner**
- 6m: +49%, +30% above MA, accel +4%. Scanner-confirmed outperformer.
- Copper at $14k/t. Peru supply shock + AI demand + defense.
- *Skeptic filter:*
  1. Priced in? Partially — copper at $14k is known. But deficit is WIDENING per S&P Global, not narrowing.
  2. Time horizon? 6-18 months (supply deficit structural; no new mega-mines before 2030).
  3. What kills it? China demand collapse (Pettis rebalancing risk), global recession, substitution.
- **Confidence: 70%** — structural supply deficit is real and worsening. Main risk is macro/China.

---

## Theme 3: Nuclear Renaissance / SMR / Uranium

### Evidence (journalism-sourced)
- **Meta** (Jun 2026): 6.6 GW nuclear energy projects announced. Deals with TerraPower, Oklo, X-energy.
- **Oklo Inc.** (Jun 2026): Meta agreement for 1.2 GW nuclear in Southern Ohio.
- **X-energy** (Jun 2026): Talen Energy evaluating GW-scale Xe-100 SMR deployment.
- **Reuters**: US targets 5 GW more nuclear through low-cost finance.
- **NuScale** Q1 2026 earnings: first SMR company reporting revenue growth path.
- **Fortune**: "Nuclear sees tipping point as Meta makes deals with Bill Gates' TerraPower, Sam Altman-backed Oklo."
- **Carnegie Endowment**: "Beyond the Hype: Assessing Hyperscaler Nuclear Commitments Against U.S. Energy Realities" — sober assessment of timeline risks.
- **CarbonCredits.com**: "2026: The Year Nuclear Power Reclaims Relevance With 15 Reactors."

### Candidate

**CCJ (Cameco) — Uranium supply**
- 6m: +18%, only +5% above MA. Very low extension = not crowded.
- Only major Western uranium miner. Contracting cycle favors producers.
- *Skeptic filter:*
  1. Priced in? Nuclear hype is known, but CCJ's actual uranium contracting cycle is multi-year and accelerating.
  2. Time horizon? 12-36 months (reactor commitments → fuel procurement 2-3 years ahead).
  3. What kills it? SMR timeline slippage (Carnegie warns), regulatory delays, Kazatomprom supply increase.
- **Confidence: 65%** — thesis is real but timeline risk is significant. CCJ is the shovel-seller.

---

## Theme 4: GOES Electrical Steel Monopoly

### Evidence (journalism-sourced)
- **Adafruit** (Apr 2026): "The AI Power Bottleneck: Data Centers Meet the Steel Monopoly."
- **The National Interest**: "The Little Monopoly Holding Back the Clean Energy Transition."
- **Utility Dive**: "Cleveland-Cliffs moves ahead with $150M electric transformer plant."
- **WPXI / Business Journals**: CLF's $170M Butler Works project survives federal review, on track for 2028.
- **Congressman Mike Kelly**: DOE finalized rule on grain-oriented electrical steel (GOES).
- **Fastmarkets**: "US construction slowed by difficulties to source electrical steel amid lack of investment."
- **Heatmap News**: "How Trump's Steel Tariffs Could Mess Up His AI Plans."
- **E&E News / Politico**: "Meet the metal that could transform the grid."
- CLF is the **sole US producer** of GOES — the magnetic steel core of every transformer. DOE rule
  mandates higher efficiency standards → more GOES per transformer → tighter supply.

### Candidate

**CLF (Cleveland-Cliffs) — GOES monopoly + transformer plant**
- 6m: +3%, +13% above MA. **Hasn't moved yet** — thesis is early.
- Sole US GOES producer. Building $150M transformer plant (vertical integration).
- DOE efficiency rule = more GOES per transformer = structural demand.
- *Skeptic filter:*
  1. Priced in? NO — CLF is treated as a cyclical steel stock, not a grid-monopoly story. Minimal AI-infrastructure narrative.
  2. Time horizon? 12-24 months (Butler Works 2028, transformer plant ramping, DOE rule taking effect).
  3. What kills it? Steel cycle downturn (CLF is still 70%+ auto/construction steel), tariff reversal on imported GOES, management execution risk.
- **Confidence: 60%** — most contrarian pick on the list. Monopoly position is real but buried under cyclical steel P&L. Needs the grid narrative to find it.

---

## Theme 5: Defense Record Backlogs

### Evidence (journalism-sourced)
- **BAE Systems**: Record backlog + $535M US Army deal.
- **Rocket Lab (RKLB)**: Hypersonics/HASTE defense upside identified by analysts.
- **Leonardo DRS**: Margins expanding on defense electronics.
- **Saab**: French NLAW order — NATO defense spend broadening.
- **RENK Group**: Guidance raised on defense vehicle demand.
- **Vishay (VSH)**: $1.6B backlog in defense/industrial electronics.
- NATO 2% GDP spending becoming 3% floor in multiple countries.
- Hypersonic/missile defense is the highest-growth sub-sector.

### Candidates

**LMT (Lockheed Martin) — Defense prime, missile/hypersonics**
- 6m: +13%, only +1% above MA, accelerating +10%. **Barely extended** — room to run.
- Record defense budgets, NATO spend, missile defense priority.
- *Skeptic filter:*
  1. Priced in? Defense primes always trade at a premium. But LMT at +1% above MA with +10% accel suggests new momentum.
  2. Time horizon? 6-24 months (budget cycle, new contract awards).
  3. What kills it? Budget sequestration, peace deal in Ukraine reducing NATO urgency, F-35 cost overruns.
- **Confidence: 60%** — solid, boring, dividend-paying compounder with accelerating momentum.

**TDY (Teledyne Technologies) — Defense electronics/instruments**
- 6m: +22%, +7% above MA. Under-followed defense tech.
- Imaging sensors, marine instruments, defense electronics. Niche but high-margin.
- *Skeptic filter:*
  1. Priced in? Less than LMT/RTX — TDY doesn't get the "defense narrative" coverage.
  2. Time horizon? 12-18 months.
  3. What kills it? Single-customer concentration risk, defense budget cuts.
- **Confidence: 55%** — less liquid, niche. Stronger as a "non-obvious beneficiary" play.

---

## Theme 6: Cybersecurity / Identity Management

### Evidence (journalism-sourced)
- **Motley Fool** (Jun 16 2026): "8 Best Cybersecurity Stocks for 2026."
- **Deloitte / NASCIO** (2026): Major cybersecurity study on state government spend.
- **IBM**: "Cybersecurity Trends 2026" — AI-driven threat landscape.
- **Accenture + Anthropic**: Partnership to "Secure, Scale AI-Driven Cybersecurity Operations."
- **CrowdStrike**: Q4 FY2026 earnings extend ARR scale and AI security focus.
- **Gartner**: Identifies top cybersecurity trends for 2026 — identity management a key vector.
- **Fortune Business Insights**: Identity Governance & Administration market growing through 2034.
- Identity is the perimeter in the AI age: every AI agent needs identity/access management.

### Candidates

**OKTA (Okta) — Identity management**
- 6m: +29%, +34% above MA, accelerating +24%. Strongest acceleration of all scanner names.
- Identity-as-a-service. Every AI agent, every SaaS app, every zero-trust architecture needs identity.
- *Skeptic filter:*
  1. Priced in? OKTA already ran from its 2024 lows. But identity-as-AI-perimeter is an emerging narrative, not fully discounted.
  2. Time horizon? 6-18 months (AI agent identity is an inflection point, not a mature story).
  3. What kills it? Competition from Microsoft Entra ID (bundled free), Breaches (OKTA had one in 2023 that damaged trust), slowing enterprise spend.
- **Confidence: 60%** — momentum is strong and the identity thesis is structural. But valuation is stretched and Microsoft bundling is a real threat.

**NET (Cloudflare) — Edge security + AI traffic**
- 6m: +14%, +11% above MA, accelerating +14%. Low extension, clean acceleration.
- AI inference at the edge, DDoS protection, developer-first security.
- *Skeptic filter:*
  1. Priced in? NET is a known growth name. But AI inference at the edge is a newer narrative with unclear TAM.
  2. Time horizon? 12-24 months (AI traffic growth → CDN/security demand).
  3. What kills it? Profitability keeps getting delayed, Amazon/Google price competition, recession hits enterprise spend.
- **Confidence: 55%** — secular tailwind, but profitability timeline unclear and valuation demands execution.

---

## Theme 7: Regulated Utilities with Data Center Load

### Candidate

**DUK (Duke Energy) — $103B plan, 14GW for data centers**
- 6m: +11%, only +3% above MA. Barely extended = not crowded at all.
- $103B capital plan through 2029. 14GW of new capacity planned for AI data center demand.
- Regulated returns = predictable earnings growth. Dividend ~4%.
- *Skeptic filter:*
  1. Priced in? DUK trades at regulated-utility multiples. The data center load growth is known but discounted conservatively.
  2. Time horizon? 12-36 months (capital plan execution).
  3. What kills it? Rate case denials, construction cost overruns, data center demand doesn't materialize as projected.
- **Confidence: 55%** — boring but reliable. The data center angle gives it secular growth above typical utility.

---

## Watchlist Summary (ranked by conviction)

| # | Ticker | Theme | 6m | %> MA | Confidence | Next Step |
|---|--------|-------|-----|-------|------------|-----------|
| 1 | **FCX** | Copper structural deficit | +49% | +30% | 70% | multi-lens-quorum (macro + Carver sizing) |
| 2 | **CCJ** | Uranium / nuclear renaissance | +18% | +5% | 65% | multi-lens-quorum (timeline risk assessment) |
| 3 | **ETN** | T&D electrification supercycle | +30% | +11% | 65% | multi-lens-quorum (valuation check) |
| 4 | **OKTA** | Identity / AI-era security | +29% | +34% | 60% | multi-lens-quorum (Microsoft threat) |
| 5 | **CLF** | GOES steel monopoly (contrarian) | +3% | +13% | 60% | Deeper journalism read on DOE rule impact |
| 6 | **LMT** | Defense backlogs | +13% | +1% | 60% | multi-lens-quorum (budget cycle) |
| 7 | **HUBB** | T&D electrical equipment | +18% | +7% | 60% | Compare to ETN (pick one) |
| 8 | **TDY** | Defense electronics | +22% | +7% | 55% | Niche — defer unless defense thesis strengthens |
| 9 | **NET** | Edge security / AI traffic | +14% | +11% | 55% | multi-lens-quorum (profitability timeline) |
| 10 | **DUK** | Utility + data center load | +11% | +3% | 55% | Boring but reliable — low urgency |

---

## What I'm NOT recommending (and why)

- **AI semis (MU, MRVL, ARM, AMD, AMAT, LRCX)** — all 100-324% extended, 78-161% above 200d MA. The trade already happened. Buying now = chasing.
- **CRWD** — cybersecurity leader but +45% 6m, +40% above MA. Extended.
- **GEV** — excellent grid thesis but +60% 6m, +28% above MA. Getting extended.
- **OKLO / SMR** — speculative SMR names. OKLO -24% 6m, -33% below MA (drawdown). Timeline risk per Carnegie Endowment.
- **VST (Vistra)** — nuclear fleet utility but -1% 6m, -7% below MA. Underperforming for a reason.
- **HBM plays** — the bottleneck is real but every HBM name (MU, SK Hynix) is already extended.

---

## Sources

### Articles read in full
- POWER Magazine, "Transformers in 2026: Shortage, Scramble, or Self-Inflicted Crisis?" (Jan 2, 2026)

### Headlines scanned (Google News RSS, 2026-06-17)
- 69 articles: "transformer shortage power grid 2026"
- 72 articles: "copper supply deficit shortage 2026"
- 52 articles: "data center power nuclear SMR gigawatts 2026"
- 68 articles: "HBM high bandwidth memory supply chain bottleneck"
- 40 articles: "GOES grain oriented electrical steel Cleveland Cliffs"
- 79 articles: "cybersecurity demand identity management 2026"
- Defense RSS: VSH, Leonardo DRS, Saab, RENK, BAE headlines

### Scanner
- `emerging_scan.py --top 25` (182-name universe, 73 outperforming SPY)
- Additional ticker checks via yfinance for GEV, CLF, ETN, CRWD, VST, HUBB, OKLO

---

---

## FCX Multi-Lens Quorum — 2026-06-17

> **Question:** FCX at $70.15 (52w high, +30% above 200d MA, P/E 37.1, P/B 5.17). Buy, hold, or avoid?
>
> **Method:** 6 independent lenses, same facts, independent verdicts. Synthesis preserves dissent.

### Shared Facts (presented to all lenses)

| Metric | Value |
|--------|-------|
| Price | $70.15 |
| 52-week high | $70.15 (AT the high) |
| 200d MA | $53.92 (+30% above) |
| 50d MA | $64.37 (+9% above) |
| 6-month return | +48% |
| P/E | 37.1 |
| P/B | 5.17 |
| EPS | $1.89 |
| BVPS | $13.57 |
| FCF | $1.7B |
| Market cap | $100.8B |
| FCF yield | ~1.7% |
| Copper price | ~$4.90/lb ($14k/t) |
| Graham Number | ~$24 (price = 2.9x GN) |
| Annualized vol | ~35-40% |

### Lens Verdicts

| # | Lens | Verdict | Conviction | Core Reasoning |
|---|------|---------|------------|----------------|
| 1 | **Buffett** (quality/moat) | **AVOID** | High | Commodity producer = no moat. P/E 37 for a cyclical miner is absurd. FCF yield 1.7% vs 4% risk-free. No margin of safety. Buffett sold his copper position (2023) — "we don't own commodities for the long run." |
| 2 | **Graham** (margin of safety) | **AVOID** | High | Price $70 vs Graham Number $24 = 2.9x overvaluation. P/B 5.17 vs Graham's 1.5x ceiling. P/E 37 vs Graham's 15x ceiling. FAILS every defensive-investor quantitative screen. Zero margin of safety — pure speculation. |
| 3 | **Housel** (behavioral) | **AVOID** | Medium | Buying at 52w high after +48% in 6 months = textbook performance-chasing. "The goalpost moved" — the thesis was copper deficit, but the entry is FOMO. Room for error = zero when buying at the top. Compounding's secret is survival, not timing the commodity cycle. |
| 4 | **Lyn Alden** (fiscal dominance/scarce assets) | **BUY small** | Medium | Copper is a scarce real asset in a fiscal-dominance regime. Electrification demand is structural (EVs, grid, data centers). Supply takes 10-15 years. In a debasement world, own the stuff you can't print. But size tiny — commodities are volatile and this is extended. |
| 5 | **Carver** (systematic/sizing) | **BUY small** | Medium | Trend is UP (price >> 200d MA). Systematic trend-followers are long here. BUT: at 35-40% vol and a 20% portfolio vol target, max position = 1-2% of book. Never size from conviction; size from volatility. The trend is the signal; the math caps the damage. |
| 6 | **Pettis** (China/trade/capital flows) | **CAUTIOUS — don't initiate** | Medium | China consumes ~55% of global copper. China's investment-led model is in secular rebalancing (overcapacity → deflation → reduced fixed-asset investment). If China reduces investment by even 5%, copper demand collapses regardless of EV/grid growth elsewhere. The deficit thesis assumes China demand holds — that's the Pettis risk. |

### Consensus (overlap across ALL 6 lenses)

**All 6 lenses agree on:**

1. **No full-sized position at this price.** Even the bulls (Alden, Carver) explicitly say "small" and cap at 1-2% of book.
2. **Zero margin of safety at $70.** Price = 2.9x Graham Number, at 52w high, after a +48% run. Every lens acknowledges this.
3. **The structural thesis (copper deficit) is real.** No lens disputes the supply/demand fundamentals. The disagreement is about whether that thesis justifies paying THIS price.
4. **Volatility is high (~35-40%).** All lenses that mention sizing agree this demands small position size regardless of conviction.

### Dissent (the disagreement IS the signal)

**The core split: VALUATION vs STRUCTURE**

| Camp | Lenses | Argument |
|------|--------|----------|
| **AVOID** (valuation wins) | Buffett, Graham, Housel | "The thesis is priced in. You're paying 37x earnings for a cyclical commodity miner at its high. No moat, no safety, pure FOMO." |
| **BUY small** (structure wins) | Alden, Carver | "Scarcity + trend. In a debasement world, own what can't be printed. The trend is up; math caps the size. You don't time — you participate." |
| **CAUTIOUS** (China risk) | Pettis | "The deficit thesis assumes China demand holds. It won't — secular rebalancing is underway. This is not a structural deficit; it's a cyclical one masked by a stimulus echo." |

**Pettis is the swing vote.** If China demand holds → Alden/Carver are right (structural deficit, price goes higher). If China rebalances → Buffett/Graham are right (cyclical peak, price mean-reverts). The Pettis lens turns the question from "is the thesis real?" to "is the thesis durable?"

### What Would Change Each Lens's Mind

| Lens | Flip condition |
|------|----------------|
| Buffett | FCX develops pricing power (impossible for a commodity) or price drops to 15x earnings (~$28) |
| Graham | Price drops below $24 (Graham Number) or below BVPS ($13.57) |
| Housel | You already own FCX from lower and are asking "hold?" not "buy" — then the behavioral bias is different |
| Alden | If global M2 contracts (disinflation wins over debasement), scarce-asset thesis weakens |
| Carver | If price breaks below 200d MA ($54) — trend-followers exit mechanically |
| Pettis | If China successfully rebalances toward consumption WITHOUT reducing copper demand (possible but unlikely) |

### Blind Spots (each lens's acknowledged weakness)

| Lens | Blind spot |
|------|------------|
| Buffett | Misses structural commodity supercycles entirely (sold silver too early, never bought gold) |
| Graham | Mechanical screens miss secular themes — would have screened out every commodity winner in history |
| Housel | Behavioral lens can't distinguish FOMO from legitimate trend-participation — all buying at highs "looks like" chasing |
| Alden | Debasement thesis can run early for years — real assets can still drop 50% in a liquidity crunch before her thesis plays out |
| Carver | Trend-following has no fundamental view — it rides bubbles up and gets stopped out on reversal (guaranteed late exit) |
| Pettis | China-rebalancing call has been "right but early" for 15 years. Timing is the achilles heel. |

### FINAL SYNTHESIS — Actionable Recommendation

**VERDICT: DO NOT INITIATE at $70.15.**

**Reasoning:** 4 of 6 lenses say avoid/don't initiate. The 2 bulls explicitly cap size at 1-2% of a $1M book ($10-20k) — which is a "don't fight the trend" toe-in, not a conviction position. The valuation case is overwhelming (every safety metric fails), the behavioral case against buying at 52w high after +48% is strong, and the Pettis China-risk is an under-appreciated structural threat to the deficit thesis.

**If you insist on participation** (because the structural copper thesis is compelling):

| Action | Level | Size |
|--------|-------|------|
| Stage 1 | Wait for -15% pullback (~$60, near 50d MA) | 1% of book ($10k) |
| Stage 2 | Wait for -25% pullback (~$53, near 200d MA) | 1.5% of book ($15k) |
| Stage 3 | If breaks below 200d MA ($54) | EXIT — trend broken |

**Hard rules:**
- Never exceed 2.5% of book in FCX (Carver vol-sizing math)
- Stop-loss: close below 200d MA for 5 consecutive days → exit all
- Do NOT chase at $70 — the entry is wrong even if the thesis is right

**What to monitor instead of buying:**
- China PMI + copper imports (Pettis risk gauge)
- FCX vs 200d MA — wait for a retest before entry
- Copper inventory levels (LME/COMEX) for real-time deficit confirmation

---

## Next actions

1. ~~Route FCX through `multi-lens-quorum`~~ ✅ Done (above)
2. Route CCJ and ETN through `multi-lens-quorum` for defended buy/hold verdict
3. Deep-read CLF journalism (the GOES monopoly thesis is the most contrarian and least priced-in)
4. Re-run scanner weekly — watch for CLF, LMT, DUK acceleration breakouts
5. Log any position entries to `forecast-ledger` for Brier-score tracking
6. **Set price alert: FCX at $60 (stage 1 entry) and $53 (stage 2 entry)**
