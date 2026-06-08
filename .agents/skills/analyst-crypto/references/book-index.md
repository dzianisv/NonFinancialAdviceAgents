# Book Index & Provenance — analyst-crypto

What's distilled, from where, and what is live-data vs. book-grounded. This skill is a **methodology
synthesis**, so only the **liquidity pillar** is book-grounded; the rest is distilled practice over
live-data tools.

## Primary book (distilled — liquidity pillar)
- **Michael J. Howell, *Capital Wars: The Rise of Global Liquidity* (Palgrave Macmillan, 2020).**
  - Link: https://link.springer.com/book/10.1007/978-3-030-39288-8
  - Grounds: `references/01-global-liquidity-and-btc.md` (Global Liquidity framework, four-phase cycle,
    lead-lag in months, GLI composite, the three CB rules, refinancing-mechanism view, ~US$130tn size).
  - **Scope flag (load-bearing):** *Capital Wars* (2020) gives crises "every 8–10 years," a **41-month**
    trend baseline, and leads measured in **months** — it does **NOT** state a clean "5–6 year liquidity
    cycle," and it does **NOT** quantify a Bitcoin liquidity-beta (crypto appears only qualitatively as a
    "distrust" signal). The **5–6yr cycle and high-beta-BTC framing are LATER Howell / CrossBorder Capital**
    work (talks, notes, *Capital Wars* sequel material) — **not yet distilled in this repo.** Cite those
    claims as later-Howell, not as from this book.

## Later-Howell (distilled from web sources)
- **Michael Howell / CrossBorder Capital** — subsequent research introducing the ~5–6yr (65-month) liquidity
  cycle and the BTC-as-high-beta-liquidity-asset framing. **Distilled from CrossBorder/Capital Wars Substack +
  2024–26 interviews (web sources, listed in `01`).** See the "Later Howell (post-2020)" section of
  `references/01-global-liquidity-and-btc.md` for the grounded, attributed content (65-month re-fi cycle,
  11–13wk BTC lead, ~40% liquidity driver share, the 2026 debt-wall read). Honesty flag carried there: the
  "~0.9 correlation / 90% of BTC's move is liquidity" figure is **secondary (Raoul Pal) framing, not a precise
  Howell statistic.**

## Live-data tools (NOT books — re-pull before use)
These are the data sources behind pillars 2–3; readings **decay** and must be re-pulled:
- **LookIntoBitcoin** — MVRV-Z, NUPL, Puell, Pi Cycle, 200-week MA heatmap, realized price.
- **Glassnode** — on-chain valuation & behavioral (LTH supply, exchange flows, cohorts).
- **CryptoQuant** — exchange flows, miner flows, derivatives.
- **CoinGlass** — funding, open interest, liquidations (derivatives positioning).
- **Alternative.me** — Crypto Fear & Greed Index (sentiment, pillar 3).

## Cross-referenced repo skills (already distilled)
- **`analytics-lyn-alden`** — debasement / hardest-money logic and BTC-as-hurdle; grounds pillar 5
  (`05-token-selection-btc-as-hurdle.md`).
- **`analyst-systematic-trading`** (Carver, *Systematic Trading* 2015) — vol-target sizing, Half-Kelly,
  the cost speed limit; grounds the sizing in pillar 4 and the day-trading-fails finding in `06`.
- **`analytics-stanley-druckenmiller`** — liquidity/timing lens; complements pillar 1.
- **`analyst-technical-analysis`** — the discretionary, weak-evidence counterpart this skill answers
  (hypothesis-only; not a timing edge).
- **`risk-management`** / **`risk-assessment`** — downside, position survival, DeFi/protocol risk for `06`.

## Cross-referenced repo docs
- **`crypto/`** — the live ~$177k conservative crypto treasury this skill is the analysis brain for;
  `crypto/goal.md` (mandate) and `crypto/InfraTokens.md` (the worked BTC-as-hurdle 6-point screen; HYPE the
  lone earlier passer).

## House finding (repo memory)
- **Hold / mid-risk beats day-trading after costs** — encoded throughout pillar 4 and `06`. Pure TA
  day-timing does not beat valuation-and-sentiment-tilted DCA once realistic costs are applied.

## Honesty status of key numbers
- **Discredited:** Stock-to-Flow (~$500k projection vs ~$66k actual; auto-correlation flaw) — a **red flag**,
  never a signal (`02`).
- **Unverified:** sentiment-tilted-DCA Sharpe ~1.38 vs ~0.88 (self-reported by crypto-content sites) — quote
  the *direction*, not the magnitude (`03`).
- **Later-Howell, not this book:** 5–6yr (65-month) cycle, BTC liquidity beta — now **distilled from
  CrossBorder/Capital Wars Substack + 2024–26 interviews** in `01` (see scope flag above). Note: the
  "~0.9 correlation / 90% liquidity" figure is **secondary (Raoul Pal) framing, not a precise Howell stat.**
