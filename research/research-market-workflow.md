# research-market workflow diagram

```mermaid
flowchart TD
    Q(["`**Query + Portfolio**
    question / assets / date`"]) --> MGR

    subgraph INTAKE["Phase 0 · Intake"]
        MGR["`**research-manager**
        discovers skills live
        → plans full roster`"]
    end

    MGR -->|gather_skills| GATHER
    MGR -->|panel_skills| PANEL
    MGR -->|desk_skill| DESK
    MGR -->|chair_skill| CHAIR

    subgraph GATHER["Phase 1 · Gather  (parallel data seats)"]
        direction LR
        subgraph REG["Regulatory filings"]
            G1[13F filings]
            G2[13D filings]
            G3[Congressional stock trades]
        end
        subgraph NEWS["News feeds"]
            G4[WSJ]
            G5[FT]
            G6[CoinTelegraph]
            G7[CoinDesk]
            G8[Decrypt.co]
        end
        subgraph MACRO["Macro / odds"]
            G9[Polymarket odds]
            G10[CPI data]
            G11[FOMC signals]
        end
        subgraph CHAIN["On-chain / market"]
            G12[crypto-onchain-data]
            G13[derivatives-positioning]
            G14[crypto-liquidity-data]
        end
    end

    GATHER --> DESK

    subgraph CONSOLIDATE["Phase 2 · Consolidate"]
        DESK["`**desk agent**
        merges all seats → one brief
        surfaces data gaps + canonical numbers`"]
    end

    DESK -->|brief| PANEL

    subgraph PANEL["Phase 3 · Panel  (parallel lenses)"]
        direction LR
        P1[investor-lyn-alden]
        P2[investor-ray-dalio]
        P3[investor-stanley-druckenmiller]
        P4[research-lacy-hunt]
        P5[research-russell-napier]
        P6[analyse-fundamental]
        P7[analyse-technical]
        P8[investor-warren-buffett]
        GRD["`**guardrail**
        *(non-voting)*
        FOMO / sizing / drawdown check`"]
    end

    PANEL -->|verdicts + guardrail| CHAIR

    subgraph DECIDE["Phase 4 · Decide"]
        CHAIR["`**chair agent**
        tallies votes, resolves disagreement
        → decision, tranche plan, per-asset conviction`"]
    end

    CHAIR --> RPT
    CHAIR --> LED

    subgraph OUTPUT["Output"]
        RPT["`📄 **research.{class}.{date}.md**
        answer · decision · panel votes
        tranche plan · risks · invalidation`"]
        LED["`📊 **forecast-ledger**
        one row per asset
        date · prob · horizon · lenses`"]
    end
```

## Phase summary

| Phase | What runs | Parallel? |
|---|---|---|
| **Intake** | research-manager (discovers skills live, plans roster) | no |
| **Gather** | N data seats (filings + news + macro + on-chain) | yes |
| **Consolidate** | 1 desk agent → single canonical brief | no |
| **Panel** | M lens agents + 1 non-voting guardrail | yes |
| **Decide** | 1 chair agent → structured decision | no |
| **Write** | write-report + verify (retry once) | no |
| **Ledger** | 1 row per asset via `ledger.py` | yes |

> N and M are **not hardcoded** — the manager picks them fresh each run based on the query, available skills, and asset class.
