# stocks-advisor

Analyzes individual stocks one at a time — runs a **4-seat analyst panel** (fundamental / technical / narrative / sentiment) per stock and outputs a concrete **entry plan** (price zone + bar-close trigger + market-based stop) with a **BUY / WATCH / SKIP** decision.

Input: user-supplied ticker list, a Google Sheet of holdings, or stocks discovered live from a named market theme.

> Educational analysis, not financial advice. Single stocks are satellites; the index is the bar.

## Architecture

```mermaid
flowchart TD
    USER(["User prompt"])

    MEM["Step -1 · Load prior memory
bun portfolio-memory/recall.ts"]
    SHEET["Step 0 · Load Google Sheet (optional)
gws sheets +read
ticker, qty, cost_basis, pnl_pct"]
    SEED["Step 1 · Seed todo list
INSERT INTO todos per ticker"]

    subgraph SEQ ["Sequential per-stock loop — ONE ticker at a time (shared TradingView slot)"]
        direction TB

        subgraph TVPULL ["Data pull — orchestrator only, subagents cannot call MCP"]
            direction LR
            TV1["TradingView MCP
chart_set_symbol NASDAQ: NYSE:
D OHLCV 365d summary + 250 bars
study values: RSI, BB, MACD, Volume
W OHLCV 210 bars
capture_screenshot"]
            FYFI["fundamentals.py (yfinance)
price, ma50, ma200, vs200d
fwdPE, PEG, rev growth
FCF yield, ROE
short pct, inst pct, rec_mean"]
        end

        PKG["Assemble data package
TradingView + yfinance merged
+ prior_context injected"]

        subgraph SEATS ["4 seats — PARALLEL subagents (receive injected package only)"]
            direction LR
            SF["Fundamental
FCF yield, PE, PEG
rev growth, moat
margin of safety
STRONG / GOOD / FAIR / POOR"]
            ST["Technical Bernstein
Setup, Trigger, Follow-Through
RSI, BB, MACD, MAs
bar-close trigger, stop, target
SETUP_NAMED / NO_SETUP / BROKEN"]
            SN["Narrative Macro
web_fetch 2+ real URLs
FT, WSJ, Bloomberg, Reuters
theme phase classification
EARLY / MID / LATE / FADING"]
            SS["Sentiment Positioning
short pct, inst pct, rec_mean
RSI extension, volume
contrarian read
QUIET_ACCUM / NEUTRAL / CROWDED / EXTREME"]
        end

        VDT["Verdict decision table
BUY: Fund GTE GOOD AND SETUP_NAMED AND MID or EARLY AND not EXTREME
WATCH: Fund GTE GOOD but NO_SETUP
SKIP: Fund POOR or LATE or FADING or BROKEN
SKIP dominates"]

        PERSIST["UPDATE stock_analysis
bun portfolio-memory/remember.ts"]

        TV1 --> PKG
        FYFI --> PKG
        PKG --> SEATS
        SF & ST & SN & SS --> VDT
        VDT --> PERSIST
    end

    SIGNAL["Signal table
Ticker, Decision, Conv, Entry zone, Trigger, Theme"]
    CHAIR[["stock-chair
portfolio synthesis, sizing, concentration"]]

    USER --> MEM --> SHEET --> SEED --> SEQ
    PERSIST --> SIGNAL --> CHAIR
```

## Two input modes

| Mode | Input | Verdicts |
|---|---|---|
| **Watchlist / Theme discovery** | Explicit tickers or live theme discovery | BUY / WATCH / SKIP |
| **Portfolio review** | Google Sheet URL (holdings + cost basis) | HOLD / ADD / TRIM / EXIT + tax-harvest table |

## The 4 seats

| Seat | Lens | Output |
|---|---|---|
| **Fundamental** | FCF yield, PE, PEG, margins, moat — margin of safety at current price? | STRONG / GOOD / FAIR / POOR |
| **Technical** (Bernstein) | Set-Up → Trigger → Follow-Through. Named setup + bar-close trigger + market-based stop. No trigger = no trade. | SETUP_NAMED / NO_SETUP / BROKEN |
| **Narrative / Macro** | `web_fetch` ≥2 real URLs. Theme phase classification. Verbatim quotes only — no fabrication. | EARLY / MID / LATE / FADING |
| **Sentiment** | Contrarian read: short%, institutional%, analyst consensus, RSI extension | QUIET_ACCUM / NEUTRAL / CROWDED / EXTREME |

## Verdict rules

```
BUY   = Fundamental ≥ GOOD  AND  SETUP_NAMED  AND  phase ∈ {EARLY,MID}  AND  Sentiment ≠ EXTREME
WATCH = Fundamental ≥ GOOD  BUT  NO_SETUP (wait for trigger)
SKIP  = Fundamental = POOR  OR   phase ∈ {LATE,FADING}  OR  Technical = BROKEN
SKIP dominates all other signals.
Conviction 1–5: start at 3, ±1 per alignment signal.
```

## Hard constraints

- **TradingView MCP lives only in the orchestrator** — subagents receive injected data, cannot call MCP.
- **One chart slot** — data pull is strictly sequential, one ticker at a time.
- **ETF / sleeve allocation** → `tradfi-portfolio-manager`. This skill is individual stocks only.
- **Portfolio synthesis** → `stock-chair`. This skill stops at per-name entry plans.

## Layout

| Path | What |
|---|---|
| `SKILL.md` | Full operating instructions |
| `scripts/fundamentals.py` | yfinance data helper — writes `{TICKER}.json.out.json` |
