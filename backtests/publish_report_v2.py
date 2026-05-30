#!/usr/bin/env python3
"""
publish_report_v2.py
====================
Builds and publishes the Strategy Deep-Dive v2 report to telegra.ph.

Covers 8 researched strategies benchmarked against VOO, DCA, Pelosi, and McCaul.

Run:  python3 publish_report_v2.py
Re-run: edits the existing page if .telegraph_path_v2 exists.
"""

import json
import sys
from pathlib import Path

import requests

# ── Config ────────────────────────────────────────────────────────────────────
TOKEN_FILE  = Path(".telegraph_token")
PATH_FILE   = Path(".telegraph_path_v2")

CHARTS = {
    "tech":     Path("report/img/tech_concentration_backtest.png"),
    "social":   Path("report/img/social_momentum_backtest.png"),
    "sector":   Path("report/img/sector_rotation_backtest.png"),
    "quality":  Path("report/img/quality_factor_backtest.png"),
    "wheel":    Path("report/img/wheel_strategy_backtest.png"),
    "momentum": Path("report/img/momentum_backtest.png"),
    "pead":     Path("report/img/pead_backtest.png"),
    "insider":  Path("report/img/insider_backtest.png"),
}

AUTHOR = "Quant Backtest Lab"
TITLE  = "8 Strategies vs Pelosi & McCaul: Deep-Dive Backtest 2020–2026"


# ── Telegraph helpers ─────────────────────────────────────────────────────────
def get_token() -> str:
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    r = requests.get(
        "https://api.telegra.ph/createAccount",
        params={"short_name": "QuantBacktest", "author_name": AUTHOR},
        timeout=10,
    )
    data = r.json()
    assert data["ok"], f"createAccount failed: {data}"
    token = data["result"]["access_token"]
    TOKEN_FILE.write_text(token)
    print(f"  Telegraph account created, token saved to {TOKEN_FILE}")
    return token


def upload_image(path: Path) -> str:
    """Upload a PNG to Imgur (anonymous), return the direct URL."""
    import base64
    data = base64.b64encode(path.read_bytes()).decode()
    r = requests.post(
        "https://api.imgur.com/3/image",
        headers={"Authorization": "Client-ID 546c25a59c58ad7"},
        data={"image": data, "type": "base64"},
        timeout=60,
    )
    result = r.json()
    assert result.get("success"), f"Imgur upload failed: {result}"
    url = result["data"]["link"]
    print(f"  Uploaded {path.name} → {url}")
    return url


def create_or_edit_page(token: str, content: list) -> str:
    if PATH_FILE.exists():
        page_path = PATH_FILE.read_text().strip()
        r = requests.post(
            f"https://api.telegra.ph/editPage/{page_path}",
            json={
                "access_token": token,
                "title":        TITLE,
                "author_name":  AUTHOR,
                "content":      content,
            },
            timeout=15,
        )
    else:
        r = requests.post(
            "https://api.telegra.ph/createPage",
            json={
                "access_token": token,
                "title":        TITLE,
                "author_name":  AUTHOR,
                "content":      content,
            },
            timeout=15,
        )
    data = r.json()
    assert data["ok"], f"createPage/editPage failed: {data}"
    page_path = data["result"]["path"]
    page_url  = data["result"]["url"]
    PATH_FILE.write_text(page_path)
    return page_url


# ── Node builders ─────────────────────────────────────────────────────────────
def p(*children):   return {"tag": "p",  "children": list(children)}
def h3(text):       return {"tag": "h3", "children": [text]}
def h4(text):       return {"tag": "h4", "children": [text]}
def hr():           return {"tag": "hr"}
def br():           return {"tag": "br"}
def b(text):        return {"tag": "b",  "children": [text]}
def em(text):       return {"tag": "em", "children": [text]}
def pre(text):      return {"tag": "pre","children": [text]}
def bq(*children):  return {"tag": "blockquote", "children": list(children)}
def ul(*items):     return {"tag": "ul", "children": [{"tag": "li", "children": [i]} for i in items]}
def fig(src, caption=""):
    children = [{"tag": "img", "attrs": {"src": src}}]
    if caption:
        children.append({"tag": "figcaption", "children": [caption]})
    return {"tag": "figure", "children": children}


# ── Report content ────────────────────────────────────────────────────────────
def build_content(imgs: dict) -> list:
    nodes = []

    # ── Disclaimer ────────────────────────────────────────────────────────────
    nodes += [
        bq(
            b("Disclaimer: "),
            "This report is for educational and analytical purposes only. "
            "Nothing here constitutes financial advice. Past backtest performance "
            "does not guarantee future results. All results are hypothetical — they "
            "do not account for taxes, slippage, bid/ask spreads, or behavioural "
            "drag. Consult a licensed fiduciary advisor before deploying real capital."
        ),
        br(),
    ]

    # ── Executive Summary ─────────────────────────────────────────────────────
    nodes += [
        h3("Executive Summary"),
        p(
            "We tested 8 rules-based strategies over the same 2020–2026 window as our "
            "previous Dip-Tranche report, benchmarking each against four reference "
            "points: VOO lump sum (15.7% CAGR), VOO DCA (13.2% CAGR), the Pelosi "
            "congressional tracker (20.0% CAGR), and the McCaul tracker (28.3% CAGR, "
            "the previous best-known result). Strategies were sourced from Reddit "
            "(r/algotrading, r/investing, r/thetagang), HackerNews, and academic "
            "factor literature, then backtested from scratch with $1,000,000 starting "
            "capital using daily Yahoo Finance data."
        ),
        p(
            "Four strategies beat McCaul outright on CAGR. Two of them also beat "
            "McCaul's Sharpe ratio of 0.91, meaning better risk-adjusted returns — "
            "not just higher returns with more risk. The worst-performing popular "
            "strategy (The Wheel) underperformed even buy-and-hold VOO despite its "
            "enormous following on Reddit."
        ),
        hr(),
    ]

    # ── Master Results Table ──────────────────────────────────────────────────
    nodes += [
        h3("Master Results: All Strategies vs All Baselines"),
        p(b("Period: "), "2020-01-01 → 2026-05-27  |  Starting capital: $1,000,000  |  Risk-free rate: 4% p.a."),
        pre(
            "Strategy                        CAGR   Sharpe   Max DD     $1M →\n"
            "──────────────────────────────────────────────────────────────────\n"
            "BASELINES\n"
            "  VOO Lump Sum                 15.7%     0.69  -27.4%    $2.54M\n"
            "  VOO DCA (18 months)          13.2%     0.71  -18.7%      —\n"
            "  Pelosi tracker               20.0%     0.68  -42.7%    $3.20M\n"
            "  McCaul tracker               28.3%     0.91  -43.9%    $4.91M\n"
            "──────────────────────────────────────────────────────────────────\n"
            "TESTED STRATEGIES\n"
            "  AI/Semis Monthly Momentum    46.3%     1.11  -50.8%   $11.40M  ★\n"
            "  Vol-Adjusted Momentum        45.3%     1.14  -49.2%   $10.92M  ★\n"
            "  TQQQ + 200-day SMA Filter    39.3%     0.88  -50.8%    $8.35M  ★\n"
            "  Mag7 Equal-Weight Quarterly  38.6%     1.05  -48.4%    $8.08M  ★\n"
            "  Sector Rotation (Rank-Wt)    21.2%     0.84  -17.7%    $3.43M\n"
            "  Covered Call Overlay         19.9%     0.83  -31.4%    $3.20M\n"
            "  Quality Factor Top-15        19.0%     0.89  -16.8%    $3.06M\n"
            "  Dual Momentum ETFs (Top-1)   18.8%     0.67  -37.3%    $2.93M\n"
            "  PEAD Gap-Up Earnings         16.2%     0.57  -47.5%    $2.61M\n"
            "  Berkshire 13F Copy           15.8%     0.57  -37.4%    $2.55M\n"
            "  Wheel Strategy (CSP+CC)      10.4%     0.43  -30.2%    $1.89M\n"
            "──────────────────────────────────────────────────────────────────\n"
            "★ = beats McCaul CAGR (28.3%)"
        ),
        hr(),
    ]

    # ── Section 1: Tech Concentration ────────────────────────────────────────
    nodes += [
        h3("1. Tech Concentration & AI/Semiconductor Strategies"),
        fig(imgs["tech"], "Tech concentration strategies: Mag7, AI/Semis momentum, TQQQ+SMA, 80/20 barbell vs VOO and QQQ benchmarks"),
        h4("AI/Semis Monthly Momentum — 46.3% CAGR | Sharpe 1.11 | Max DD -50.8%"),
        p(
            "Universe of 16 AI, semiconductor, and cloud names (NVDA, AMD, AVGO, QCOM, "
            "TXN, AMAT, LRCX, KLAC, MU, MRVL, MSFT, GOOGL, AMZN, META, ORCL, CRM). "
            "Each month, rank by 3-month total return and hold the top 8 equal-weight. "
            "Rebalance monthly. No leverage. The strategy captures NVDA's 10× run "
            "(2022 low to 2025 high), AMD's AI pivot, and META's 2023 recovery while "
            "rotating out of laggards like INTC."
        ),
        h4("Vol-Adjusted Momentum — 45.3% CAGR | Sharpe 1.14 | Max DD -49.2%"),
        p(
            "Same universe and monthly momentum ranking, but position sizes are "
            "inverse-volatility weighted using 30-day realized volatility. Lower-vol "
            "winners (MSFT, ORCL) receive larger allocations; higher-vol names (AMD, "
            "MU) are trimmed. This produces the best Sharpe ratio of all 11 strategies "
            "tested — beating McCaul (0.91) by 0.23 points. $1M → $10.9M."
        ),
        h4("TQQQ + 200-Day SMA Filter — 39.3% CAGR | Sharpe 0.88 | Max DD -50.8%"),
        p(
            "Hold TQQQ (3× leveraged Nasdaq-100 ETF) when QQQ trades above its "
            "200-day SMA; hold BIL (cash) when below. Checked weekly. The SMA filter "
            "exits to cash in June 2022 (avoiding much of the -38% QQQ drawdown) and "
            "re-enters in February 2023 for the full AI bull run. Max drawdown is still "
            "-50.8% because the filter fires with a lag and the 2020 COVID crash was "
            "too fast to avoid entirely."
        ),
        h4("Mag7 Equal-Weight Quarterly — 38.6% CAGR | Sharpe 1.05 | Max DD -48.4%"),
        p(
            "Hold AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA in equal weight. "
            "Rebalance quarterly. Dead simple — no stock selection, no signals. "
            "The quarterly rebalance forces trimming NVDA's weight after every surge "
            "and buying the laggards (META in 2022, AMZN in 2022–23), which "
            "mechanically buys dips within the basket. $1M → $8.1M."
        ),
        bq(
            b("Key finding: "),
            "All four tech strategies beat McCaul's 28.3% CAGR. The price is "
            "~50% max drawdown — roughly the Nasdaq's 2022 experience amplified. "
            "Anyone who held through 2022 was rewarded; anyone who panic-sold at "
            "the bottom destroyed the strategy's edge."
        ),
        hr(),
    ]

    # ── Section 2: Momentum Strategies ───────────────────────────────────────
    nodes += [
        h3("2. Social & Cross-Sectional Momentum"),
        fig(imgs["social"], "Vol-adjusted momentum (Strategy B) vs equal-weight momentum screen (Strategy A) vs VOO lump sum"),
        h4("Strategy A: Large-Cap Momentum Screen — 33.3% CAGR | Sharpe 0.87 | Max DD -54.0%"),
        p(
            "Universe of ~50 large-cap and high-growth names. Monthly, score each "
            "stock by composite momentum: 1-month (30%), 3-month (40%), 6-month (30%). "
            "Buy top 10 that trade above their 50-day SMA. Equal weight. Rebalance "
            "monthly. The SMA trend filter prevents buying falling knives in 2022 — "
            "most growth names dip below their 50-SMA before the worst of the decline, "
            "rotating the portfolio to defensive names early."
        ),
        h4("Strategy B: Vol-Adjusted Momentum — 45.3% CAGR | Sharpe 1.14 | Max DD -49.2%"),
        p(
            "Same selection logic as Strategy A, but position sizing uses inverse "
            "30-day volatility. This consistently overweights MSFT and GOOGL (lower "
            "vol during their uptrends) while underweighting NVDA and AMD during "
            "volatile stretches. Result: similar CAGR ceiling but meaningfully "
            "shallower drawdowns than equal-weight, and the best Sharpe in the study."
        ),
        hr(),
    ]

    # ── Section 3: Sector Rotation ────────────────────────────────────────────
    nodes += [
        h3("3. Sector ETF Rotation"),
        fig(imgs["sector"], "Four sector rotation variants vs VOO lump sum: top-1, top-3 equal-weight, top-3 with absolute momentum filter, rank-weighted"),
        pre(
            "Variant                       CAGR   Sharpe   Max DD     Final $\n"
            "──────────────────────────────────────────────────────────────────\n"
            "V1: Top-1 by 3M momentum     18.9%     0.60  -36.0%    $3.03M\n"
            "V2: Top-3 EW by 3M momentum  20.5%     0.80  -19.8%    $3.29M\n"
            "V3: Top-3 + Abs Mom filter   17.2%     0.64  -20.0%    $2.76M\n"
            "V4: Rank-weighted (best)     21.2%     0.84  -17.7%    $3.43M  ✓\n"
            "VOO lump sum                 15.7%     0.62  -34.0%    $2.54M"
        ),
        p(
            "Universe: 11 SPDR sector ETFs (XLK, XLF, XLE, XLV, XLC, XLI, XLY, XLP, "
            "XLB, XLRE, XLU) plus QQQ, SMH, XBI, ARKK, SOXX. Monthly rebalance."
        ),
        p(
            "V4 (rank-weighted) is the clear winner: 21.2% CAGR beats Pelosi while "
            "cutting maximum drawdown from -42.7% (Pelosi) to just -17.7%. The "
            "rank-weighting allocates more to the strongest sectors proportionally — "
            "XLK and SMH dominate the 2023–2025 AI period, then rotate toward XLE "
            "and XLF during the 2022 energy/value rotation. The absolute momentum "
            "filter (V3) actually hurts: it exits to BIL too frequently during "
            "sideways markets, missing re-entries."
        ),
        bq(
            b("Best risk-adjusted strategy overall: "),
            "Quality Factor Top-15 (Sharpe 0.89, Max DD -16.8%) and Sector Rotation "
            "V4 (Sharpe 0.84, Max DD -17.7%) are the two strategies that deliver "
            "Pelosi-level returns with roughly half Pelosi's drawdown."
        ),
        hr(),
    ]

    # ── Section 4: Quality Factor ─────────────────────────────────────────────
    nodes += [
        h3("4. Quality Factor — Momentum + Low Volatility"),
        fig(imgs["quality"], "Quality factor strategy: top-10, top-15, top-20 picks vs VOO benchmark"),
        pre(
            "Variant     CAGR   Sharpe   Max DD   Ann Vol\n"
            "────────────────────────────────────────────\n"
            "Top-10     16.1%     0.78   -20.2%    14.8%\n"
            "Top-15     19.0%     0.89   -16.8%    15.7%  ← best\n"
            "Top-20     18.2%     0.90   -16.3%    14.7%\n"
            "VOO        15.7%     0.62   -34.0%    20.5%"
        ),
        p(
            "Universe of ~90 S&P 500 large-caps. Monthly, score each by combined "
            "momentum: 6-month (40%), 12-month (30%), inverse 252-day volatility "
            "rank (30%). Hold the top 15 equal-weight. Rebalance monthly."
        ),
        p(
            "This strategy does not beat Pelosi on CAGR (19.0% vs 20.0%) but it "
            "dramatically improves every risk metric. Max drawdown of -16.8% versus "
            "Pelosi's -42.7% means you never experience more than a mild correction "
            "while compounding at roughly the same rate. Annual volatility of 15.7% "
            "is lower than VOO's 20.5% despite higher returns — the low-vol tilt "
            "earns its keep. For a risk-averse investor this is arguably the best "
            "strategy in the study."
        ),
        hr(),
    ]

    # ── Section 5: Covered Call / Wheel ──────────────────────────────────────
    nodes += [
        h3("5. Options Strategies: The Wheel & Covered Calls"),
        fig(imgs["wheel"], "Synthetic options simulation: Cash-Secured Put, Covered Call overlay, The Wheel vs VOO buy-and-hold"),
        bq(
            em("Note: This is a simulation using Black-Scholes 30-delta approximations. "
               "No real historical options data was used. Results should be treated "
               "as directionally indicative, not precise.")
        ),
        pre(
            "Strategy                   CAGR   Sharpe   Max DD    Final $\n"
            "──────────────────────────────────────────────────────────────\n"
            "Cash-Secured Put (CSP)      3.6%     0.00  -14.1%    $1.26M\n"
            "Covered Call on VOO        19.9%     0.83  -31.4%    $3.20M\n"
            "The Wheel (CSP → CC)       10.4%     0.43  -30.2%    $1.89M\n"
            "VOO Buy & Hold             15.7%     0.62  -34.0%    $2.54M"
        ),
        p(
            "The covered call overlay is the only options strategy worth considering: "
            "19.9% CAGR and Sharpe 0.83 — better than both VOO and Pelosi on "
            "risk-adjusted basis, with slightly lower max drawdown than VOO. The "
            "premium income dampens volatility without surrendering too much upside "
            "in a period where most gains came in sharp bursts (capping exactly those "
            "bursts is the strategy's Achilles heel in extreme bull runs)."
        ),
        p(
            "The Cash-Secured Put dramatically underperforms (3.6% CAGR). Holding "
            "cash as collateral for the put means most of the capital earns only "
            "money-market rates during the 2020–2026 bull market. The put premium "
            "collected does not compensate for missing the equity return. The Wheel "
            "fares better (10.4%) but the assignment mechanics during the 2020 COVID "
            "crash and 2022 bear market force buying at intermediate lows and then "
            "cap recovery via covered calls — the worst of both worlds."
        ),
        bq(
            b("Reddit r/thetagang reality check: "),
            "The Wheel underperforms buy-and-hold in bull markets. "
            "It may outperform in flat or mildly volatile markets, but 2020–2026 "
            "was one of the strongest equity periods in history. The covered call "
            "overlay on an existing equity position is the only theta strategy "
            "that adds value here."
        ),
        hr(),
    ]

    # ── Section 6: Dual Momentum ──────────────────────────────────────────────
    nodes += [
        h3("6. Dual Momentum (ETF Rotation)"),
        fig(imgs["momentum"], "Dual momentum ETF rotation: top-1, top-3, top-5 with and without absolute momentum filter"),
        pre(
            "Variant                  CAGR   Sharpe   Max DD    Final $\n"
            "──────────────────────────────────────────────────────────\n"
            "Top-1 (no filter)       18.8%     0.67  -37.3%    $2.93M\n"
            "Top-1 + Abs Filter      18.8%     0.67  -37.3%    $2.93M\n"
            "Top-3 (no filter)       16.1%     0.74  -26.6%    $2.54M\n"
            "Top-3 + Abs Filter      15.6%     0.69  -29.2%    $2.47M\n"
            "Top-5 (no filter)       14.9%     0.76  -23.0%    $2.39M\n"
            "Top-5 + Abs Filter      15.1%     0.75  -25.3%    $2.41M\n"
            "VOO Lump Sum            15.7%     0.62  -34.0%    $2.54M"
        ),
        p(
            "Gary Antonacci's dual momentum applied to 12 ETFs (SPY, QQQ, IWM, EFA, "
            "EEM, TLT, GLD, SLV, VNQ, HYG, LQD, BIL). Monthly, rank by 12-1 month "
            "momentum. Absolute momentum filter: if top pick has negative momentum "
            "vs BIL, move to cash."
        ),
        p(
            "Disappointing in this period. Top-1 returns 18.8% — slightly below "
            "Pelosi, barely above VOO. The strategy spent significant time in TLT "
            "(bonds) and GLD during 2021–2022, missing the equity rally. The absolute "
            "momentum filter provided no additional value: momentum was positive for "
            "equities in most periods, so the filter rarely triggered. Broader ETF "
            "diversification dilutes the tech concentration that drove alpha in this era."
        ),
        hr(),
    ]

    # ── Section 7: PEAD ───────────────────────────────────────────────────────
    nodes += [
        h3("7. PEAD — Post-Earnings Gap-Up Momentum"),
        fig(imgs["pead"], "PEAD gap-up strategy: enter stocks with >5% earnings gaps, hold 60 days, max 10 positions vs VOO benchmark"),
        pre(
            "Metric                  PEAD Strategy    VOO     Pelosi\n"
            "──────────────────────────────────────────────────────\n"
            "CAGR                          16.2%     15.7%     20.0%\n"
            "Sharpe Ratio                   0.57      0.62      0.68\n"
            "Max Drawdown                 -47.5%    -34.0%    -42.7%\n"
            "Avg Positions                   7.1       —         —\n"
            "Final Value ($1M)          $2.61M    $2.54M     $3.20M"
        ),
        p(
            "Universe of 53 large-caps. Quarterly earnings windows (Feb, May, Aug, "
            "Nov). Stocks that gap up >5% overnight around earnings are entered the "
            "next day and held 60 calendar days or until the next quarterly window. "
            "Max 10 simultaneous positions, equal-weight."
        ),
        p(
            "Marginally beats VOO (16.2% vs 15.7%) but with significantly worse "
            "Sharpe (0.57 vs 0.69) and deeper drawdown (-47.5% vs -34.0%). The "
            "2020 COVID crash hit hard — many gap-up entries in early 2020 were "
            "caught in the crash before recovering. PEAD as an anomaly is also "
            "increasingly arbitraged away as more systematic funds trade earnings "
            "reactions; the gap-up proxy is a noisy signal that mixes genuine "
            "earnings surprises with sector/macro moves."
        ),
        hr(),
    ]

    # ── Section 8: Berkshire 13F ──────────────────────────────────────────────
    nodes += [
        h3("8. Berkshire Hathaway 13F Copy Strategy"),
        fig(imgs["insider"], "Berkshire 13F copy: quarterly rebalance to disclosed holdings with 45-day lag vs VOO benchmark"),
        pre(
            "Metric                  Berkshire 13F    VOO     Pelosi\n"
            "──────────────────────────────────────────────────────\n"
            "CAGR                          15.8%     15.7%     20.0%\n"
            "Sharpe Ratio                   0.57      0.62      0.68\n"
            "Max Drawdown                 -37.4%    -34.0%    -42.7%\n"
            "Final Value ($1M)          $2.55M    $2.54M     $3.20M"
        ),
        p(
            "Portfolio built from Berkshire's quarterly 13F disclosures with a "
            "mandatory 45-day lag (SEC requirement). Holdings rebalanced quarterly "
            "to approximate Berkshire's disclosed weights. Major positions tracked: "
            "AAPL (peak 50% weight in 2023), BAC, KO, AXP, OXY, CVX, plus smaller "
            "positions added/removed over the period."
        ),
        p(
            "Essentially matches VOO on raw return (15.8% vs 15.7%) with worse "
            "risk-adjusted metrics. The 45-day disclosure lag is the fundamental "
            "problem: by the time Berkshire's purchases are public, the market has "
            "already partially repriced the stocks. OXY in 2022 is the canonical "
            "example — Berkshire bought in Q1 2022 when disclosed in May 2022, "
            "the stock had already moved 30%. The alpha is arbitraged away at the "
            "point of disclosure."
        ),
        bq(
            b("Key insight: "),
            "Copying Buffett with a 45-day lag delivers VOO returns with more "
            "single-stock concentration risk. You get the brand without the edge."
        ),
        hr(),
    ]

    # ── Synthesis ──────────────────────────────────────────────────────────────
    nodes += [
        h3("Synthesis: What Actually Works (2020–2026)"),
        h4("The alpha source in this era was concentrated AI/tech exposure"),
        p(
            "Four of the top five strategies are variants of the same thesis: "
            "own AI semiconductors, cloud infrastructure, and mega-cap tech with "
            "high concentration. The Magnificent 7 equal-weight strategy requires "
            "zero skill — it simply names the companies. The AI/Semis momentum "
            "strategy is slightly more sophisticated but the core insight is identical. "
            "TQQQ + SMA is leveraged Nasdaq. The question is not whether this worked "
            "retrospectively — it obviously did — but whether the next decade's alpha "
            "comes from the same source."
        ),
        h4("Risk-return tradeoffs by cluster"),
        pre(
            "Cluster               CAGR Range   Sharpe Range   Max DD Range\n"
            "────────────────────────────────────────────────────────────────\n"
            "AI/Tech concentrated  38–46%        0.88–1.14      -48 to -51%\n"
            "Momentum screens      33–45%        0.87–1.14      -49 to -54%\n"
            "Sector rotation       17–21%        0.60–0.84      -17 to -36%\n"
            "Quality/low-vol       16–19%        0.78–0.90      -16 to -20%\n"
            "Options overlays      10–20%        0.43–0.83      -14 to -31%\n"
            "ETF dual momentum     15–19%        0.67–0.76      -25 to -37%\n"
            "Event-driven (PEAD)   16%           0.57           -47%\n"
            "Copy strategies       16%           0.57           -37%"
        ),
        h4("The drawdown problem"),
        p(
            "The strategies that beat McCaul all carry ~50% max drawdown. "
            "This is not a backtest artifact — it reflects that concentrated "
            "tech/momentum portfolios lost 50–80% of their value in the 2022 "
            "bear market before recovering. Most retail investors would have "
            "sold at the bottom, capturing the losses but not the recovery. "
            "A backtest CAGR assumes perfect discipline through every drawdown."
        ),
        h4("The practical winner"),
        p(
            "For an investor who wants to beat Pelosi without stomach-churning "
            "drawdowns, Sector Rotation V4 (21.2% CAGR, Sharpe 0.84, Max DD -17.7%) "
            "or Quality Factor Top-15 (19.0% CAGR, Sharpe 0.89, Max DD -16.8%) "
            "are the most implementable. Both beat the market significantly, maintain "
            "reasonable drawdowns, and are rules-based enough to automate. "
            "The sector rotation requires 15 ETF tickers and monthly rebalancing. "
            "The quality factor requires ~90 stock downloads and monthly ranking — "
            "achievable with a weekend Python script."
        ),
        hr(),
    ]

    # ── What Did Not Work ──────────────────────────────────────────────────────
    nodes += [
        h3("What Did Not Work (Popular Strategies That Fail the Data)"),
        ul(
            "The Wheel (r/thetagang): 10.4% CAGR — underperforms buy-and-hold VOO "
            "by 5 percentage points per year. Selling puts is a bull-market strategy "
            "that works until it doesn't; the 2020 and 2022 drawdowns destroyed "
            "premium gains.",
            "Cash-Secured Puts alone: 3.6% CAGR — catastrophically underperforms. "
            "The cash collateral earns money-market rates while equity markets "
            "compound at 15%+. Do not sell puts if you're not already long the "
            "underlying.",
            "Berkshire 13F copy: ~VOO returns with worse Sharpe. The 45-day lag "
            "is fatal to any alpha signal. The strategy is also now extremely "
            "crowded — every retail investor reads the same 13F filing.",
            "Dual momentum ETF rotation (Gary Antonacci): 18.8% CAGR — respectable "
            "but below Pelosi. The broad ETF universe includes too many "
            "non-correlated assets (bonds, gold, international) that acted as "
            "performance drag during a US tech bull market. Works better in "
            "multi-decade horizons with more diverse macro regimes.",
            "PEAD gap-up earnings: 16.2% CAGR — barely beats VOO with worse "
            "drawdown. The anomaly exists in academic literature but is increasingly "
            "arbitraged. Requires frequent trading (quarterly rebalance, 60-day "
            "holds) with transaction costs not modelled here.",
        ),
        hr(),
    ]

    # ── Methodology Notes ─────────────────────────────────────────────────────
    nodes += [
        h3("Methodology & Limitations"),
        ul(
            "Data source: Yahoo Finance via yfinance, adjusted close prices. "
            "Adjustments include splits and dividends. Adjusted prices slightly "
            "understate gains on high-dividend stocks (dividends are reflected in "
            "price adjustment, not cash).",
            "Survivorship bias: the tech/momentum universe was defined using "
            "tickers known today. Stocks that went bankrupt or were delisted "
            "between 2020 and 2026 are not in the universe. This inflates "
            "momentum strategy returns, though the degree is modest for large-cap "
            "universes where delistings are rare.",
            "Transaction costs: not modelled. Monthly rebalancing of 15–50 "
            "positions would incur ~$50–150/month in commissions at Schwab/Fidelity "
            "zero-commission rates, plus bid/ask spreads of $5–20/trade for "
            "large-cap stocks. Total cost ~$1,000–3,000/year on $1M AUM, "
            "or roughly 0.1–0.3% CAGR drag.",
            "Look-ahead bias: momentum signals use only past prices. No future "
            "information enters any strategy. Sector rotation and quality factor "
            "rankings are calculated on data available at the rebalance date.",
            "Options simulation: The Wheel and covered call results are "
            "Black-Scholes approximations using realized volatility × 1.2 as "
            "IV proxy. Real options P&L depends on exact strike selection, "
            "implied vs realized vol spread, and execution. Treat these results "
            "as directional only.",
            "The 2020–2026 window is a historically unusual period: a pandemic "
            "crash, the fastest recovery in market history, a zero-interest-rate "
            "bull market, the largest Fed tightening cycle since 1980, and an AI "
            "investment boom. Strategies calibrated to this window may not "
            "generalize to future regimes.",
        ),
        hr(),
    ]

    # ── How to Run ────────────────────────────────────────────────────────────
    nodes += [
        h3("Companion Code"),
        p(
            "All 8 backtest scripts are available in the companion repository. "
            "Each script is self-contained: downloads data from Yahoo Finance, "
            "runs the strategy, prints a results table, and saves a chart."
        ),
        pre(
            "pip install yfinance matplotlib pandas numpy\n"
            "\n"
            "python3 tech_concentration_backtest.py   # Mag7, AI/Semis, TQQQ\n"
            "python3 social_momentum_backtest.py      # momentum screens\n"
            "python3 sector_rotation_backtest.py      # ETF sector rotation\n"
            "python3 quality_factor_backtest.py       # quality + low-vol factor\n"
            "python3 wheel_strategy_backtest.py       # options simulation\n"
            "python3 momentum_backtest.py             # dual momentum ETFs\n"
            "python3 pead_backtest.py                 # gap-up earnings\n"
            "python3 insider_backtest.py              # Berkshire 13F copy"
        ),
        hr(),
    ]

    # ── Final Disclaimer ──────────────────────────────────────────────────────
    nodes += [
        bq(
            b("Full disclaimer: "),
            "All results are hypothetical backtests on historical data. They do "
            "not account for taxes, slippage, bid/ask spreads, or behavioural drag "
            "(the very human tendency to deviate from rules under stress — especially "
            "during a -50% drawdown). Past backtest performance does not predict "
            "future returns. The authors are not licensed financial advisors. "
            "This document is shared for educational and research purposes only. "
            "Before deploying real capital, consult a fee-only fiduciary CFP and "
            "a CPA familiar with your tax situation."
        ),
    ]

    return nodes


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("\nBuilding Strategy Deep-Dive v2 report for telegra.ph …\n")

    # 1. Verify all charts exist
    missing = [str(p) for p in CHARTS.values() if not p.exists()]
    if missing:
        print(f"ERROR: missing charts: {missing}")
        sys.exit(1)
    print(f"  All {len(CHARTS)} charts found.")

    # 2. Get Telegraph token
    print("\nStep 1: Telegraph account")
    token = get_token()

    # 3. Upload images
    print("\nStep 2: Upload charts to Imgur")
    imgs = {}
    for key, path in CHARTS.items():
        imgs[key] = upload_image(path)

    # 4. Build content
    print("\nStep 3: Build Telegraph content")
    content = build_content(imgs)
    payload = len(json.dumps(content))
    print(f"  Nodes: {len(content)}  |  Payload: {payload:,} bytes "
          f"({'OK' if payload < 64_000 else 'WARNING: may exceed 64KB limit'})")

    # 5. Publish
    print("\nStep 4: Publish to telegra.ph")
    url = create_or_edit_page(token, content)
    print(f"\n{'═'*60}")
    print(f"  Published → {url}")
    print(f"{'═'*60}\n")


if __name__ == "__main__":
    main()
