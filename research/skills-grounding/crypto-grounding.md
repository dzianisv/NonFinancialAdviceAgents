# Crypto Skills — Grounding Against the Canon

> **Educational analysis, not financial advice.** Research compiled 2026-06-05. Proposal only — this
> document does **not** edit the skills; it maps them to the best crypto-investing and trading literature
> and proposes concrete edits, each book-cited. Every empirical claim links its source.

## 0. Scope & inventory note

The task named four audit targets (`crypto-daytrading`, `crypto-advisor`, `dip-tranches-strategy`,
`strategy-discovery-backtest`). Two of those names do **not yet exist as files** — `crypto-daytrading` and
`strategy-discovery-backtest` are still *unbuilt* workstreams B/C in [`GOAL.md`](../../GOAL.md). The skills
that actually exist and govern crypto today are:

| Audit target (as named) | Actual file in repo | Status |
|---|---|---|
| crypto-advisor | [`.agents/skills/defi-portfolio-manager/SKILL.md`](../../.agents/skills/defi-portfolio-manager/SKILL.md) (v2.4) | exists — the de-facto crypto advisor |
| dip-tranches-strategy | [`skills/dip-tranches-strategy/SKILL.md`](../../skills/dip-tranches-strategy/SKILL.md) | exists — but it is an **S&P-500-ETF** skill, not crypto |
| crypto-daytrading | — | **not built** (GOAL workstream C) |
| strategy-discovery-backtest | — | **not built** (GOAL workstream B; cost-model rules live in `AGENTS.md` + `risk-management`) |
| (shared trading-discipline backbone) | [`skills/risk-management`](../../skills/risk-management/SKILL.md), [`skills/trend-following`](../../skills/trend-following/SKILL.md) | exist — generic, equity-flavoured |
| Crypto policy docs | [`GOAL.md §Book 2`](../../GOAL.md), [`crypto/STRATEGY.md`](../../crypto/STRATEGY.md), [`crypto/AGENTS.md`](../../crypto/AGENTS.md), [`crypto/btc-dex.md`](../../crypto/btc-dex.md) | exist |

**The single biggest structural finding:** the live crypto skill (`defi-portfolio-manager`) is a *yield/DeFi*
manager. It is excellent on smart-contract / depeg / custody-venue risk, but it has **no token-valuation
framework, no BTC-as-benchmark hurdle, no reflexivity discipline, and no R-multiple / expectancy machinery** —
because those belong to the *directional* and *day-trading* mandates that aren't built yet. The book canon
below is exactly the material those unbuilt skills should be authored from. So this audit doubles as the
**spec** for `crypto-daytrading` and `strategy-discovery-backtest`.

---

## 1. Principles table (book/source → operationalization)

| # | Principle | Book / source | How to operationalize (a rule an agent can run) |
|---|---|---|---|
| P1 | **Utility-token value trends to marginal cost of operation; only the winning *monetary* protocol accrues durable value.** Bitcoin is held for its own sake; utility chains face competition that competes their fee revenue away. | Lyn Alden, *Broken Money* + ["Why Most Cryptocurrencies Won't Accrue Value"](https://www.lynalden.com/why-most-cryptocurrencies-wont-accrue-value/) | For any non-BTC token, require a **named value-accrual mechanism** (enforced fee→holder claim). No mechanism → treat as marginal-cost commodity, satellite-only. |
| P2 | **BTC is the monetary base / benchmark; price everything *in BTC*.** | Alden *Broken Money*; Ammous *Bitcoin Standard* (salability + high stock-to-flow = the monetary winner) [src](https://jamesbachini.com/the-bitcoin-standard-summary/) | Make **BTC the hurdle rate**: an alt must beat BTC on a risk-adjusted, BTC-denominated basis to earn a directional slot, or it is dead weight. |
| P3 | **Empirically, almost no alt beats BTC over a cycle.** Across the top-300 alts the **median falls −90% vs BTC within 10–20 months** of its ATH; alts have lagged BTC four years running; ~2–3 (ETH/BNB/SOL) are the durable exceptions. | Study summarized at [Bitget](https://www.bitget.com/news/detail/12560604721961) / [Insider Monkey](https://www.insidermonkey.com/blog/why-most-altcoins-underperform-bitcoin-over-a-full-market-cycle-1773079/); [KuCoin: 4 yrs underperformance](https://www.kucoin.com/news/flash/altcoins-underperform-bitcoin-for-fourth-consecutive-year) | Default alt allocation ≈ 0. An alt enters only with (a) a P1 value-accrual mechanism AND (b) a BTC-relative trend that is *positive*. Size as a **survivable satellite**, never core. |
| P4 | **The rare defensible "infra" token is one with an *enforced* fee→holder buyback.** HYPE routes **~97% of protocol revenue** into automated on-chain HYPE buybacks (the Assistance Fund). | [crypto.news](https://crypto.news/why-hype-is-different-inside-hyperliquids-buyback/); [Tokenomics.com](https://tokenomics.com/articles/hyperliquid-tokenomics-how-hype-captures-65m-monthly-in-holder-revenue) | The **value-accrual test**: % of real (non-emission) revenue contractually returned to holders, the buyback observable on-chain, revenue not mostly token emissions. Pass → eligible infra satellite; fail → reject. |
| P5 | **Cryptoasset fundamental valuation: NVT (network value ÷ on-chain $ volume) + Metcalfe + a "three functions" lens (capital / consumption / network).** High NVT = rich; low = cheap. | Burniske & Tatar, *Cryptoassets* [review](https://www.coinfabrik.com/blog/a-review-on-cryptoasset-valuation-frameworks/); [NVT origin](https://medium.com/cryptolab/https-medium-com-kalichkin-rethinking-nvt-ratio-2cf810df0ab0) | Before any directional add, pull NVT vs its own history; flag rich (e.g. >2σ NVT) as a *trim*, cheap as an *add* candidate — never the sole signal, a sanity filter on price-vs-usage. |
| P6 | **Reflexivity: in crypto, price *drives* perceived fundamentals; booms are self-reinforcing then self-defeating.** Alts swing harder than BTC because the feedback loop is stronger. | Soros, *Alchemy of Finance* (reflexivity); [Decrypt on alts](https://decrypt.co/301314/george-soros-reflexivity-theory-altcoins-bitcoin); [Sesterce](https://medium.com/sesterce/the-reflexivity-of-crypto-markets-3457d1eac2d0) | At an ATH on a stretched multiple, **trim into strength** (treat the multiple as reflexive, not earned). Tag any "yield/valuation looks great because price is up" as a reflexivity flag in the report. |
| P7 | **Sound-money / low-time-preference framing.** Hard money (fixed supply, high stock-to-flow) rewards holding; this is the BTC-core thesis. | Ammous, *Bitcoin Standard* [summary](https://jamesbachini.com/the-bitcoin-standard-summary/); Alden *Broken Money* | The BTC sleeve is **held, not traded** ("hold, not trade" is already in the skill for staked majors — extend the framing to BTC explicitly and to the day-trade skill's bias). |
| P8 | **Self-custody: "Not your keys, not your coins."** Exchanges/custodial venues are risky and *unnecessary* for holding; hardware-wallet cold storage for anything not actively earning. | Antonopoulos, *Mastering Bitcoin* (cold storage, key mgmt) [src](https://cointelegraph.com/news/antonopoulos-your-keys-your-bitcoin-not-your-keys-not-your-bitcoin) | Directional/long-term BTC-ETH-SOL → cold storage off perp/exchange venues (already a `STRATEGY.md` §0 default; **promote it into the skill body** + a custody line in `btc-dex.md` and the day-trade skill). |
| P9 | **Risk comes first, profit second; "cut losses, cut losses, cut losses."** Survival > return. Position size matters more than entry. Risk ~1–2% of capital per trade. | Schwager, *Market Wizards* [src](https://liquidityfinder.com/news/the-market-wizards-rule-risk-comes-first-profits-come-second-2b38a) | The (unbuilt) day-trade skill must define the stop **before** entry and cap per-trade risk at a fixed fraction. Make this an invariant, not a guideline. |
| P10 | **Expectancy & R-multiples; position sizing is the lever.** Define 1R = initial risk (entry−stop). Judge a system by expectancy (avg R per trade) × frequency, sized by fractional position-sizing — not by win rate. | Van Tharp, *Trade Your Way to Financial Freedom* [src](https://traderlion.com/trading-books/trade-your-way-to-financial-freedom/) | Day-trade strategy report = `expectancy (R), # trades, win%, avg win/avg loss (R), position-sizing rule`. No strategy ships without a positive **net-of-cost** expectancy over a credible sample. |
| P11 | **No-look-ahead / no data-snooping / no survivorship; halve your backtest Sharpe before believing it.** The three biases all inflate results; expect live ≈ ½ backtest. | Ernie Chan, *Algorithmic Trading* / [Backtesting and its Pitfalls](https://epchan.com/img/links/Backtesting-and-its-Pitfalls.pdf) | Signals use only past data (already an `AGENTS.md` rule for tradfi — **extend to crypto**); use the historical (not current) token universe; discount the in-sample Sharpe by ~50% in the verdict; walk-forward before paper. |
| P12 | **Avoid ruin; barbell the book.** Risks at the tails are incomputable; size so a tail can't ruin you. Conservative core + small, capped, convex high-risk sleeve beats "medium risk everywhere." | Taleb, *Antifragile* / barbell [src](https://fourweekmba.com/barbell-strategy-taleb/) | The stable-core + capped-satellite structure **is** a barbell — name it as such; satellite sized so total loss is survivable (already a cap; tie it explicitly to ruin-avoidance and fractional-Kelly). |
| P13 | **Trend / absolute-momentum overlay for directional crypto** (own only while above long MA / beating cash). | Trend-following canon (Faber GTAA, Antonacci dual momentum) — repo `skills/trend-following` | Gate any directional crypto sleeve on a BTC/asset trend filter (200-day / weekly close); de-risk on a trend break. Already referenced in `STRATEGY.md` "Defend"; make it the *entry* condition for alts too (ties to P3b). |
| P14 | **Realistic crypto cost model: fees + funding + slippage + bridge/withdrawal + gas.** 24/7, higher vol; thin DEX depth means slip dominates on size. | `crypto/btc-dex.md` (own research); Chan (costs kill high-turnover edges) | Day-trade & discovery backtests must model **taker fees + funding + slippage on thin books + gas**; report net-of-all-cost edge. "No edge after costs" is a valid result (already a GOAL invariant). |

---

## 2. Per-skill audit

### 2a. `defi-portfolio-manager` (the live crypto advisor, v2.4)

| Principle | Covered? | Gap / note |
|---|---|---|
| P1 value-accrual test | ⚠️ partial | Rejects "APY mostly emissions" and "yield source you can't name" — a *yield* analogue. **No token-side value-accrual test** for a directional/satellite token (no fee→holder check). |
| P2 BTC-as-hurdle | ❌ | No benchmark framing. Directional sleeve is "BTC/ETH/SOL held," but nothing says an alt must beat BTC to earn a slot. |
| P3 alts ≈ 0 vs BTC | ⚠️ partial | "No long-tail / meme / governance-pump" rejects junk, but doesn't encode the *empirical base rate* (median alt −90% vs BTC) as the default-zero prior. |
| P4 HYPE-style buyback test | ❌ | Satellite is allowed if "audited, real-yield, >6mo, >$20M TVL" — venue-risk gates, **not** a value-accrual gate. HYPE/HLP appears in `STRATEGY.md` satellite with no fee→holder rationale. |
| P5 NVT / fundamental valuation | ❌ | None. Pure yield/risk lens. |
| P6 reflexivity | ⚠️ trace | `STRATEGY.md` Phase-2 trims HYPE "at ATH on ~100x multiple" — correct instinct but ad-hoc, not a named principle in the skill. |
| P7 sound money / hold-not-trade | ✅ (partial) | "held, not traded" for staked majors. BTC-core thesis not stated. |
| P8 self-custody | ✅ default, ⚠️ buried | A `STRATEGY.md` §0 *default*, not in the skill body's constraints. The skill's hard rule is "never custody keys" (agent-side), which is different from advising investor cold-storage. |
| P9–P11 trade discipline / backtest rigor | ➖ out of mandate | This is a yield manager; OK that R-multiples are absent — but "Validate before trusting a strategy" already nods at risk-adjusted backtest; could cite Chan's halve-the-Sharpe. |
| P12 barbell / ruin | ✅ implicitly | Stable core + ≤15% satellite "survivable if it zeros" = a barbell; not named. |
| P13 trend gate | ⚠️ partial | "Defend" raises stables on a BTC/ETH trend break — a *defense* trigger, not an *entry* gate for directional adds. |

**Strengths to preserve:** crypto-native risk taxonomy, no-shitty-assets reject list, live-data-only (never from
memory), caps-by-construction with explicit arithmetic, name-collision pool warnings, read-only invariant. These
are best-in-class and several already encode P12/P8/P11 informally.

### 2b. `dip-tranches-strategy`

| Principle | Covered? | Note |
|---|---|---|
| P9 risk-first / tranching | ✅ | Tiered deployment, dry-powder discipline, weekly-close (no intraday wick) = sound. |
| P10 sizing | ✅ (for DCA) | Bucket/tier sizing is explicit. |
| P11 no-look-ahead | ✅ | "weekly closes not intraday prints"; backtest caveats honest. |
| crypto fit | ❌ N/A | **This skill is S&P-500 ETFs only (VOO/IVV/SPLG/SPY).** Its −7/−12/−20% tiers are calibrated to equities that draw down ~20–55%. Crypto routinely draws down **60–80%** ([book audited −60% scenario](../../crypto/STRATEGY.md)). Applying these tiers to BTC would exhaust the reserve far too early. |

**Gap:** there is **no crypto dip/accumulation skill.** If the team wants a BTC DCA-the-dip framework, it needs
its *own* tiers (e.g. −20/−40/−60 from ATH), BTC-denominated, sound-money "hold" framing (P7), and self-custody
of accumulated coin (P8). Do **not** reuse the equity tiers.

### 2c. Shared backbone (`risk-management`, `trend-following`) and policy docs

| Principle | Where covered | Gap |
|---|---|---|
| P9 risk veto, caps, kill-switch | `risk-management` ✅ strong | Deterministic veto, vol-target, drawdown de-risk, ¼–½ Kelly *cap*, "test across 2008/2020/2022." Excellent — but **equity crisis windows**; add crypto crises (2018 −84%, May 2021, Nov 2022 FTX, 2025 deleverage). |
| P10 expectancy/R | `risk-management` ⚠️ | Kelly + "50–100 trades before trusting win-rate" is there; **R-multiple vocabulary absent** — add for the day-trade skill. |
| P11 backtest rigor | `AGENTS.md` ✅ "only past data (no look-ahead)" | Stated for tradfi backtests; **not** echoed in any crypto skill, and **no "halve the Sharpe" / data-snooping / historical-universe** rule anywhere. |
| P12 barbell, P13 trend | `trend-following` ✅, `risk-management` ✅ | Generic/equity ETFs (SPY/VTI/DBMF). Needs a crypto instantiation (BTC 200-day, funding-rate regime). |
| P14 cost model | `btc-dex.md` ✅ (venue costs) + `AGENTS.md` caveat #6 | Costs described qualitatively for *venues*; **no intraday crypto cost/funding/slippage model** for a backtest (because the day-trade skill isn't built). |

---

## 3. Prioritized top-10 highest-impact edits (book-cited)

Ranked by impact × how cheaply it closes a real gap. Edits 1–6 target the live `defi-portfolio-manager`;
7–10 are spec items for the unbuilt skills (the same gaps, where they'll bite hardest).

> Notation: **CURRENT** quotes the live line; **REPLACE** is the proposed text; **WHY** tags the principle/book.

---

**EDIT 1 — Add a token value-accrual test to the "No shitty assets" gate.** *(P1/P4 — Alden; HYPE buyback)*
`defi-portfolio-manager/SKILL.md`, in the "No shitty assets" section.

- CURRENT: *"**Keep only:** T-bills, BTC, ETH, SOL (+ liquid staking), other genuine majors, overcollateralized loans against those, and audited real-yield protocols (>6 months live, >$20M TVL, yield you can name)."*
- REPLACE (append a sentence): *"…yield you can name. **For any non-BTC *token* held directionally, also require a named, enforced value-accrual mechanism — a contractual fee→holder claim observable on-chain (e.g. Hyperliquid routes ~97% of protocol revenue to automated HYPE buybacks [crypto.news]). A token with no such mechanism trends to its marginal cost of operation under competition (Alden, *Broken Money*) and is satellite-only at most.**"*
- WHY: today the gate screens *venue/yield* risk but lets any "major" token in directionally with no value test. This is the single largest conceptual gap.

**EDIT 2 — Make BTC the benchmark / hurdle rate for the directional sleeve.** *(P2/P3 — Alden, Ammous; the −90%-vs-BTC base rate)*
In "Risk profile — MODERATE," the Blue-chip directional row.

- CURRENT: *"BTC, ETH, SOL — staked where the yield is real (jitoSOL, wstETH); held, not traded"*
- REPLACE: *"BTC is the **benchmark and hurdle**. ETH/SOL earn a slot only if they beat BTC risk-adjusted (BTC-denominated) and pass the EDIT-1 value-accrual test; default alt weight is **0**. Empirically the median top-300 alt falls −90% vs BTC within 10–20 months of its ATH and alts have lagged BTC four years running [Bitget/KuCoin] — so an alt is guilty until proven. Staked where the yield is real (jitoSOL, wstETH); held, not traded."*
- WHY: encodes the empirical base rate as the default-zero prior instead of relying on the analyst's discretion.

**EDIT 3 — Name reflexivity as a standing trim rule.** *(P6 — Soros)*
Add a bullet under "Decision principles."

- ADD: *"**Reflexivity (Soros).** In crypto, price drives perceived fundamentals; booms are self-reinforcing then self-defeating, and alts swing harder than BTC [Decrypt]. A token at an ATH on a stretched multiple is *reflexively* rich, not *earned* rich — **trim into strength** and flag any 'the yield/valuation looks great because price is up' reasoning as a reflexivity warning in the report."*
- WHY: `STRATEGY.md` already trims HYPE "at ATH on ~100x multiple" by instinct; this promotes the instinct to a named, repeatable rule.

**EDIT 4 — Add NVT / fundamental sanity check before a directional add.** *(P5 — Burniske & Tatar)*
Under "Decision principles" (or the Strategy Constructor brief).

- ADD: *"**Price-vs-usage check (Burniske & Tatar, *Cryptoassets*).** Before any directional add, pull the asset's **NVT** (network value ÷ on-chain $ volume) against its own history; treat a >2σ-rich NVT as a trim signal and a cheap NVT as an add candidate. A sanity filter, never the sole signal."*
- WHY: the skill has zero fundamental-valuation lens for the tokens it does hold.

**EDIT 5 — Promote investor self-custody from a buried default to a stated advisory constraint.** *(P8 — Antonopoulos)*
The skill's Constraints list currently covers only *agent-side* custody.

- CURRENT: *"**NEVER custody keys, sign, or broadcast.** Produce tickets; the investor executes."*
- REPLACE (append): *"…the investor executes. **Advise self-custody for the directional/long-term sleeve: blue-chip spot (BTC/ETH/SOL) belongs in hardware-wallet cold storage off exchange/perp venues — 'not your keys, not your coins' (Antonopoulos, *Mastering Bitcoin*); custodial venues are risky and unnecessary for coins that aren't actively earning.** Only assets actively earning a named yield stay on a venue, and only on a vetted one."*
- WHY: separates the agent's read-only rule from the investor-facing custody advice, which is currently only a `STRATEGY.md` §0 default and easy to miss.

**EDIT 6 — Name the barbell and tie satellite sizing to ruin-avoidance.** *(P12 — Taleb)*
"Construct into the bands" / satellite cap.

- CURRENT: *"Vetted satellite ≤15% … (sized so a total loss is survivable)"*
- REPLACE: *"Vetted satellite ≤15% … **The book is a Taleb barbell: a large overcollateralized stable+majors core (zero-ruin end) plus a small, capped, convex satellite (high-risk end) — sized via fractional-Kelly so a *total* loss of the satellite is survivable. Tail risks are incomputable; size for survival, not for the expected case (Taleb, *Antifragile*).**"*
- WHY: makes the existing structure's *rationale* explicit and ties the cap to a principle, hardening it against "just this once" creep.

---

*Edits 7–10 are spec lines for the two unbuilt skills — author them in from day one.*

**EDIT 7 — `crypto-daytrading` (to build): risk-first + R-multiple core as an invariant.** *(P9/P10 — Schwager, Van Tharp)*
- SPEC: *"Define the stop **before** entry; 1R = entry−stop. Cap per-trade risk at a fixed fraction (default 1% of book). Judge the strategy by **expectancy in R × frequency**, net of all costs, not by win rate (Van Tharp). 'Cut losses' is the first rule, not the last (Schwager). These are deterministic, code-side caps — not LLM discretion."*
- WHY: this is the discipline that separates a survivable day-trade book from a blow-up; bake it into the skill's contract.

**EDIT 8 — `strategy-discovery-backtest` (to build): no-look-ahead + halve-the-Sharpe.** *(P11 — Chan)*
- SPEC: *"Signals use only data available at decision time (no look-ahead); use the **historical** token universe (delisted/dead tokens included) to kill survivorship bias; limit free parameters to avoid data-snooping. **Discount the in-sample Sharpe by ~50% in the verdict** — expect live ≈ ½ backtest (Chan, *Backtesting and its Pitfalls*). Walk-forward → paper before any live path."*
- WHY: the only no-look-ahead rule today lives in `AGENTS.md` for *equity* backtests; crypto discovery needs its own, plus survivorship (delisted alts are the −90% graveyard) and the Sharpe haircut.

**EDIT 9 — `crypto-daytrading` (to build): full crypto cost model.** *(P14 — own `btc-dex.md`, Chan)*
- SPEC: *"Model **taker fee + funding rate + slippage on the actual book depth + bridge/withdrawal + gas** on every simulated trade; thin DEX depth means slip dominates on size ([btc-dex.md]). Report the **net-of-all-cost** edge; 'no edge after costs' is a valid, valuable result."*
- WHY: crypto's 24/7 funding and thin-book slippage are exactly where naive backtests lie; this is the cost reality already documented in `btc-dex.md`, lifted into the trading skill.

**EDIT 10 — A *crypto* dip/accumulation framework, distinct from the equity one.** *(P3/P7/P8 — base rate, sound money, custody)*
- SPEC (new skill or a clearly-labeled crypto mode): *"Do **not** reuse the S&P −7/−12/−20% tiers — crypto draws down 60–80%. Use BTC-denominated tiers (e.g. −20/−40/−60 from ATH), accumulate **BTC-core** (the monetary winner, held not traded — Alden/Ammous), move accumulated coin to **cold storage** (Antonopoulos), and keep alt accumulation ≈ 0 unless it passes the EDIT-1 value-accrual test."*
- WHY: `dip-tranches-strategy` is equity-only; pointing a crypto user at its tiers would exhaust the reserve at the first leg of a normal crypto drawdown.

---

## 4. Contradictions found (anything against best practice)

1. **`dip-tranches-strategy` mis-applied to crypto** would contradict P3/P12: equity tiers (−7/−12/−20) on an
   asset that routinely falls 60–80% empties the dry powder long before the real bottom. Not a flaw in the
   skill (it's explicitly an S&P-500 skill) — but a gap if anyone reaches for it on BTC. (See EDIT 10.)
2. **No outright contradictions** in `defi-portfolio-manager` — its gaps are *omissions* (no value-accrual / BTC-hurdle / reflexivity / NVT), not wrong rules. Its existing rules align well with Taleb (barbell), Antonopoulos (the read-only stance is custody-adjacent), and Chan (live-data, "validate before trusting").
3. **Minor:** `risk-management`'s "test across 2008, 2020, 2022" lists *equity* crises; for crypto it should add 2018 (−84%), 2021 deleveraging, Nov-2022 FTX, and 2025's washout. An omission, not a contradiction.

---

## 5. Sources

- Lyn Alden, *Broken Money* + ["Why Most Cryptocurrencies Won't Accrue Value"](https://www.lynalden.com/why-most-cryptocurrencies-wont-accrue-value/)
- Saifedean Ammous, *The Bitcoin Standard* — [summary](https://jamesbachini.com/the-bitcoin-standard-summary/)
- Chris Burniske & Jack Tatar, *Cryptoassets* — [framework review](https://www.coinfabrik.com/blog/a-review-on-cryptoasset-valuation-frameworks/); [NVT origin](https://medium.com/cryptolab/https-medium-com-kalichkin-rethinking-nvt-ratio-2cf810df0ab0)
- Andreas Antonopoulos, *Mastering Bitcoin* — [keys/custody](https://cointelegraph.com/news/antonopoulos-your-keys-your-bitcoin-not-your-keys-not-your-bitcoin)
- Jack Schwager, *Market Wizards* — [risk-first](https://liquidityfinder.com/news/the-market-wizards-rule-risk-comes-first-profits-come-second-2b38a)
- Van K. Tharp, *Trade Your Way to Financial Freedom* — [R-multiples/expectancy](https://traderlion.com/trading-books/trade-your-way-to-financial-freedom/)
- Ernie Chan, *Algorithmic Trading* — [Backtesting and its Pitfalls (PDF)](https://epchan.com/img/links/Backtesting-and-its-Pitfalls.pdf)
- Nassim Taleb, *Antifragile* — [barbell](https://fourweekmba.com/barbell-strategy-taleb/)
- George Soros, reflexivity — [Decrypt: alts vs BTC](https://decrypt.co/301314/george-soros-reflexivity-theory-altcoins-bitcoin); [Sesterce](https://medium.com/sesterce/the-reflexivity-of-crypto-markets-3457d1eac2d0)
- Altcoin −90%-vs-BTC base rate — [Bitget](https://www.bitget.com/news/detail/12560604721961); [Insider Monkey](https://www.insidermonkey.com/blog/why-most-altcoins-underperform-bitcoin-over-a-full-market-cycle-1773079/); [KuCoin: 4yrs](https://www.kucoin.com/news/flash/altcoins-underperform-bitcoin-for-fourth-consecutive-year)
- HYPE ~97% buyback — [crypto.news](https://crypto.news/why-hype-is-different-inside-hyperliquids-buyback/); [Tokenomics.com](https://tokenomics.com/articles/hyperliquid-tokenomics-how-hype-captures-65m-monthly-in-holder-revenue)
- Repo: [`crypto/btc-dex.md`](../../crypto/btc-dex.md) (venue cost/custody research)

*Educational analysis, not advice; you place the orders.*
