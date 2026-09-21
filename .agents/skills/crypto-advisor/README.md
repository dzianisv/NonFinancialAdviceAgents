# crypto-advisor

Multi-token crypto portfolio analyzer. Runs a **3-layer hedge fund structure** (Research → Panel → Report) per token and outputs BUY / BUY(small) / HOLD / SELL signals with a F&G-governed position cap.

> Educational only. Not financial advice. No leverage. Ever.

## Architecture

```mermaid
flowchart TD
    SETUP["⚙️ Pre-loop setup (once)\nF&G index · current_context.ts --days 30\n→ lyn_current_context.md (book-wide, not per-token)"]

    SETUP -->|"run dir + lyn_current_context.md ready"| CIO

    CIO["🎯 CIO\n11 tokens · one at a time (chart slot)"]

    CIO -->|"token + price_usd"| RESEARCH

    subgraph RESEARCH["① Research Desk — parallel, each analyst owns its data"]
        TA["analyse-technical\n📊 TradingView MCP\nOHLCV · RSI · BB · MACD · MAs"]
        FUND["analyse-onchain\n🌐 MVRV-Z · realized price · NUPL\nPuell · LTH/STH · exchange flows"]
        OC["analyse-defi\n🌐 DeFiLlama\nTVL · fee distribution · accrual"]
        MACRO["analyse-macro\n🌐 GLI · M2 · DXY · ETF flows\nmacro headlines · halving cycle"]
        SM["analyse-smartmoney\n🌐 whale flows · exchange inflows\nOTC · positioning"]
    end

    BRIEF["📄 CIO consolidates\none briefing package per token\n+ Lyn current views injected"]

    TA -->|"technical brief"| BRIEF
    FUND -->|"fundamental brief"| BRIEF
    OC -->|"on-chain brief"| BRIEF
    MACRO -->|"macro brief"| BRIEF
    SM -->|"smart money brief"| BRIEF
    SETUP -->|"lyn_current_context.md"| BRIEF

    BRIEF -->|"briefing"| PANEL

    subgraph PANEL["② Investment Panel — parallel, each seat reads the brief + votes"]
        G["investor-benjamin-graham\nValue school\nGraham / Klarman"]
        B["investor-warren-buffett\nQuality school\nBuffett / Fisher"]
        D["investor-ray-dalio\nCycle school\nDalio / Templeton"]
        DR["investor-stanley-druckenmiller\nTrend school\nDruckenmiller / Carver"]
        LA["investor-lyn-alden\nDebasement school\nAlden — BTC-as-hurdle\n📡 reads live current views from briefing"]
        BU["analyse-defi\nOn-chain school\nBurniske"]
    end

    G -->|"BULLISH / NEUTRAL / BEARISH + reason"| QUORUM
    B -->|"vote"| QUORUM
    D -->|"vote"| QUORUM
    DR -->|"vote"| QUORUM
    LA -->|"vote"| QUORUM
    BU -->|"vote"| QUORUM

    QUORUM["③ CIO conviction-weighted synthesis\nweigh vote × conviction, not headcount\nCORE lens for this token leads\nHIGH CORE dissent caps at SPLIT\n→ BULLISH / SPLIT / BEARISH / UNCERTAIN"]

    QUORUM --> GOV["F&G Governor Cap\nExtreme Fear → max 4\nFear → max 6"]
    GOV --> CRITIC["④ Verdict critics\nall tokens reviewed\nrevise every FLAG"]
    CRITIC --> CITES["⑤ Citation repair gate\nVERIFIED / PARTIAL only\nrepair or fail closed"]
    CITES --> SKEPTIC["⑥ Skeptic repair gate\nPASS + 0 challenges\nrepair or fail closed"]
    SKEPTIC --> OUT["📋 Final Report\nonly after both gates PASS\nACTIVE / WATCH / HOLD / SELL"]
```

## Layers

### Layer 1 — Research Desk (data gatherers, no votes)

| Analyst | Skill | Data source |
|---|---|---|
| Technical | [`analyse-technical`](../analyse-technical/SKILL.md) | TradingView MCP — OHLCV, RSI, BB, MACD, MAs |
| BTC valuation | [`analyse-onchain`](../analyse-onchain/SKILL.md) | MVRV-Z, realized price, NUPL, Puell, LTH/STH supply, exchange flows |
| On-chain DeFi | [`analyse-defi`](../analyse-defi/SKILL.md) | DeFiLlama: TVL, fee distribution, protocol accrual |
| Macro | [`analyse-macro`](../analyse-macro/SKILL.md) | GLI, M2, DXY, ETF flows, halving cycle, macro headlines |
| Smart money | [`analyse-smartmoney`](../analyse-smartmoney/SKILL.md) | Whale flows, exchange inflows/outflows, OTC desk, positioning |

> **`analyse-onchain` vs `analyse-defi` — two layers of "on-chain", different assets.** `analyse-onchain` reads the cost-basis and holder behavior of a monetary asset (BTC/ETH/SOL); `analyse-defi` reads protocol fundamentals of a DeFi token (AAVE/UNI/JUP/AERO…). They are complementary seats, not duplicates.
>
> | | `analyse-onchain` | `analyse-defi` |
> |---|---|---|
> | **Question** | "Is **BTC** cheap or expensive in its cycle?" | "Does **this protocol's token** capture real value?" |
> | **Asset** | Bitcoin / L1 monetary assets | DeFi protocol tokens |
> | **Framework** | Cycle/valuation — MVRV-Z, NUPL, realized price, Puell, LTH/STH, exchange flows | Burniske value-accrual — revenue, TVL, fee distribution |
> | **Data source** | `crypto-onchain-data` (Glassnode/CryptoQuant style) | DeFiLlama |
> | **Output** | Zone verdict (DEEP VALUE → EXTREME) + confidence | BULLISH / NEUTRAL / BEARISH vote + reason |

### Layer 2 — Investment Panel (read briefing, vote per school)

| Seat | Skill | School |
|---|---|---|
| Value | [`investor-benjamin-graham`](../investor-benjamin-graham/SKILL.md) | Graham (*The Intelligent Investor* ch.20) / Klarman |
| Quality | [`investor-warren-buffett`](../investor-warren-buffett/SKILL.md) | Buffett / Fisher (*Common Stocks and Uncommon Profits*) |
| Cycle | [`investor-ray-dalio`](../investor-ray-dalio/SKILL.md) | Dalio / Templeton ("maximum pessimism") |
| Trend | [`investor-stanley-druckenmiller`](../investor-stanley-druckenmiller/SKILL.md) | Druckenmiller / Carver (*Systematic Trading*) |
| Debasement | [`investor-lyn-alden`](../investor-lyn-alden/SKILL.md) | Alden (*Broken Money*) — fiscal dominance, scarce-asset, BTC-as-hurdle; **reads live 30d macro context from `current_context.ts` injected into briefing** |
| On-chain | [`analyse-defi`](../analyse-defi/SKILL.md) | Burniske (*Cryptoassets* value-accrual) — dual role: research + vote |

### Layer 3 — CIO (conviction-weighted synthesis → signal → governor → quality gates → report)

The draft is never delivered directly. Every token first receives a verdict critic. The complete draft
then passes a citation repair loop and a separate skeptic repair loop. Any remaining `NOT_FOUND`,
`FETCH_FAILED`, skipped validation, or skeptic challenge blocks Telegram and Notion delivery; warning
labels are not treated as a pass.

## Signal table

The conviction-weighted `quorum_verdict` — not a seat count — drives the signal; deterministic **zone** and
**trend** gates still hard-cap what BULLISH can buy.

```
quorum_verdict = BULLISH  + zone ∈ {DEEP_VALUE, FAIR_VALUE} + weekly_closes ≥ 200  → BUY
quorum_verdict = BULLISH  + zone = ELEVATED                                        → HOLD (await pullback)
quorum_verdict = BULLISH  + zone = EXTREME                                         → HOLD (extended, avoid)
quorum_verdict = BULLISH  + weekly_closes < 200                                    → BUY(small)
quorum_verdict = SPLIT    + zone = DEEP_VALUE + bull lean                          → BUY(small)
quorum_verdict = BEARISH                                                           → SELL
else                                                                              → HOLD
```

## Governor cap

| F&G regime | Max simultaneous active buys |
|---|---|
| Extreme Fear (0–24) | 4 |
| Fear (25–49) | 6 |
| Neutral+ (50–100) | no cap |

Rank by `bull_weight` (conviction-weighted lean) ascending, downgrade lowest-conviction buys to WATCH.

## Token universe

BTC · ETH · SOL · TON · HYPE · AAVE · JUP · UNI · AERO · PUMP · LINK

## Related docs

- [`docs/crypto-advisor-panel.prd.md`](../../docs/crypto-advisor-panel.prd.md) — design rationale, school citations
- [`docs/crypto-advisor-panel.tdd.md`](../../docs/crypto-advisor-panel.tdd.md) — data contracts, runtime adapters
- [`SKILL.md`](SKILL.md) — full orchestration instructions for the agent
