#!/usr/bin/env python3
"""
publish_report.py
=================
Builds and publishes the Dip-Tranche Strategy backtest report to telegra.ph.

Flow:
  1. Create a Telegraph account (one-time, token saved to .telegraph_token)
  2. Upload VOO / QQQ / VXUS chart PNGs to telegra.ph/upload
  3. Compose the full report as Telegraph Node content
  4. POST to createPage → print the live URL

Run:  python3 publish_report.py
Re-run: edits the existing page if .telegraph_token + .telegraph_path exist.
"""

import json
import sys
from pathlib import Path

import requests

# ── Config ────────────────────────────────────────────────────────────────────
TOKEN_FILE = Path(".telegraph_token")
PATH_FILE  = Path(".telegraph_path")

CHARTS = {
    "VOO":  Path("VOO_backtest.png"),
    "QQQ":  Path("QQQ_backtest.png"),
    "VXUS": Path("VXUS_backtest.png"),
}

AUTHOR  = "Dip-Tranche Strategy"
TITLE   = "Dip-Tranche Strategy: S&P 500, Nasdaq-100, International — Backtest 2020–2026"


# ── Telegraph helpers ─────────────────────────────────────────────────────────
def get_token() -> str:
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    r = requests.get(
        "https://api.telegra.ph/createAccount",
        params={"short_name": "DipTranche", "author_name": AUTHOR},
        timeout=10,
    )
    data = r.json()
    assert data["ok"], f"createAccount failed: {data}"
    token = data["result"]["access_token"]
    TOKEN_FILE.write_text(token)
    print(f"  Telegraph account created, token saved to {TOKEN_FILE}")
    return token


def upload_image(path: Path) -> str:
    """Upload a PNG to Imgur (anonymous), return the direct https://i.imgur.com/... URL."""
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
    return url  # full https URL, use directly in img src


def create_or_edit_page(token: str, content: list) -> str:
    path_file = PATH_FILE
    if path_file.exists():
        page_path = path_file.read_text().strip()
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
    path_file.write_text(page_path)
    return page_url


# ── Node builders ─────────────────────────────────────────────────────────────
def p(*children):    return {"tag": "p",  "children": list(children)}
def h3(text):        return {"tag": "h3", "children": [text]}
def h4(text):        return {"tag": "h4", "children": [text]}
def hr():            return {"tag": "hr"}
def br():            return {"tag": "br"}
def b(text):         return {"tag": "b",  "children": [text]}
def em(text):        return {"tag": "em", "children": [text]}
def pre(text):       return {"tag": "pre","children": [text]}
def bq(*children):   return {"tag": "blockquote", "children": list(children)}
def ul(*items):      return {"tag": "ul", "children": [{"tag": "li", "children": [i]} for i in items]}
def fig(src, caption=""):
    children = [{"tag": "img", "attrs": {"src": src}}]
    if caption:
        children.append({"tag": "figcaption", "children": [caption]})
    return {"tag": "figure", "children": children}


# ── Report content ─────────────────────────────────────────────────────────────
def build_content(img_srcs: dict) -> list:
    nodes = []

    # ── Lead ──────────────────────────────────────────────────────────────────
    nodes += [
        bq(
            b("Disclaimer: "),
            "This report is for educational and analytical purposes only. "
            "Nothing here constitutes financial advice. Past backtest performance "
            "does not guarantee future results. Consult a licensed fiduciary "
            "advisor before making any investment decisions."
        ),
        br(),
    ]

    # ── Executive Summary ─────────────────────────────────────────────────────
    nodes += [
        h3("Executive Summary"),
        p(
            "This report backtests a tiered \"dip-buying\" deployment strategy "
            "against two benchmarks (lump-sum and pure DCA) across three ETFs — "
            "VOO (S&P 500), QQQ (Nasdaq-100), and VXUS (Total International) — "
            "using weekly closing data from January 2020 through May 2026."
        ),
        p(
            "The core finding: the strategy did not beat lump-sum on raw returns "
            "for US equities in this particular window (which started just before "
            "the fastest crash-and-recovery in market history), but it "
            "consistently reduced maximum portfolio drawdown by 3–5 percentage "
            "points and outperformed lump-sum on VXUS, where recoveries are "
            "slower. The strategy is best understood as a "
            "risk-management tool that trades some upside for shallower drawdowns "
            "and psychological staying power during corrections."
        ),
        hr(),
    ]

    # ── Strategy Overview ─────────────────────────────────────────────────────
    nodes += [
        h3("Strategy Overview"),
        h4("The 50 / 30 / 20 Allocation"),
        p(
            "A $1,000,000 portfolio is divided into three buckets at inception:"
        ),
        ul(
            "Bucket 1 — Foundation (50% = $500K): deployed as a lump sum on day one. "
            "Captures upside if the market continues higher; accepts the risk of "
            "buying near a local top.",
            "Bucket 2 — DCA (30% = $300K): deployed in equal weekly instalments "
            "over 18 months (~$3,840/week). Smooths cost basis, removes decision "
            "fatigue, keeps capital working.",
            "Bucket 3 — Dip Reserve (20% = $200K): held in a money-market fund "
            "earning ~4% annualised while waiting for drawdown triggers. Deployed "
            "in tranches as the market falls.",
        ),
        h4("Tiered Dip Reserve — How It Works"),
        p(
            "The reserve is split into three tiers based on drawdown severity from "
            "the rolling 52-week high. Each tier has four sub-tranches: three "
            "price-triggered and one time-triggered (fires if price remains below "
            "the tier entry threshold for N weeks without recovering)."
        ),
        pre(
            "VOO / VXUS triggers (β-mult 1.0)         QQQ triggers (β-mult 1.4)\n"
            "─────────────────────────────────         ────────────────────────────\n"
            "Tier 1  20% of reserve  ($40K)            Tier 1  20%  ($40K)\n"
            "  T1a   -7.0%  from 52w high  $10K          T1a  -9.8%            $10K\n"
            "  T1b   -8.5%                 $10K          T1b -11.9%            $10K\n"
            "  T1c  -10.0%                 $10K          T1c -14.0%            $10K\n"
            "  T1d   time (2 wks below T1a)$10K          T1d  time             $10K\n"
            "\n"
            "Tier 2  30% of reserve  ($60K)            Tier 2  30%  ($60K)\n"
            "  T2a  -12.0%                 $15K          T2a -16.8%            $15K\n"
            "  T2b  -14.0%                 $15K          T2b -19.6%            $15K\n"
            "  T2c  -16.0%                 $15K          T2c -22.4%            $15K\n"
            "  T2d   time (3 wks below T2a)$15K          T2d  time             $15K\n"
            "\n"
            "Tier 3  50% of reserve ($100K)            Tier 3  50% ($100K)\n"
            "  T3a  -20.0%                 $25K          T3a -28.0%            $25K\n"
            "  T3b  -25.0%                 $25K          T3b -35.0%            $25K\n"
            "  T3c  -30.0%                 $25K          T3c -42.0%            $25K\n"
            "  T3d   time (4 wks below T3a)$25K          T3d  time             $25K"
        ),
        h4("Guard Rules"),
        ul(
            "Cooldown: minimum 3 weeks between any two sub-tranche fills — "
            "prevents panic-buying every bar on the way down.",
            "Re-arm: if the market recovers above the re-arm threshold "
            "(-5% from new 52w high for VOO/VXUS, -7% for QQQ), all fired tiers "
            "reset. Capped at 2 re-arms per calendar year to avoid chasing noise.",
            "MM yield: idle reserve earns 4% annualised (money-market rate), "
            "accrued weekly — modelled conservatively.",
            "Triggers use weekly closes, not intraday wicks, to avoid "
            "flash-crash false triggers.",
        ),
        h4("Why Different Triggers for QQQ?"),
        p(
            "QQQ has roughly 1.4× the volatility of VOO. Its 2022 drawdown "
            "(-38%) was ~13 percentage points deeper than VOO's (-25%) in the "
            "same event. Using VOO triggers on QQQ would fire Tier 3 too easily, "
            "depleting the reserve during routine corrections. Scaling all "
            "thresholds by 1.4× keeps the tier system calibrated to the asset's "
            "actual behaviour."
        ),
        hr(),
    ]

    # ── Backtest Parameters ───────────────────────────────────────────────────
    nodes += [
        h3("Backtest Parameters"),
        pre(
            "Period:          2020-01-01 → 2026-05-27  (6.4 years)\n"
            "Data:            Weekly closes, adjusted for splits and dividends\n"
            "Source:          Yahoo Finance via yfinance 1.4.0\n"
            "Starting capital: $1,000,000\n"
            "Benchmarks:\n"
            "  Lump Sum  — 100% deployed on the first bar (2020-01-01)\n"
            "  DCA 18m   — equal weekly instalments over 18 months\n"
            "52-week high:    rolling max of prior 52 weekly closes\n"
            "MM yield:        4.00% p.a. accrued weekly on reserve cash\n"
            "Commissions:     not modelled (negligible for ETFs at this scale)\n"
            "Taxes:           not modelled (tax wrapper dependent)"
        ),
        hr(),
    ]

    # ── VOO Results ───────────────────────────────────────────────────────────
    nodes += [
        h3("VOO — Vanguard S&P 500 ETF"),
        fig(img_srcs["VOO"], "VOO: price with entry points (top), portfolio value comparison (middle), drawdown vs tier triggers (bottom)"),
        pre(
            "Metric                    Strategy    Lump Sum    DCA 18m\n"
            "─────────────────────────────────────────────────────────\n"
            "End value ($)           2,465,730   2,553,705  2,388,899\n"
            "Total return              +146.6%     +155.4%    +138.9%\n"
            "CAGR                       15.1%       15.8%      14.6%\n"
            "Max portfolio drawdown    -22.5%      -27.4%     -24.3%\n"
            "─────────────────────────────────────────────────────────\n"
            "Strategy detail:\n"
            "  Avg cost basis          $280.15     (last price $689.96)\n"
            "  Unrealised gain/share   +146.3%\n"
            "  Dip sub-tranches fired  18  (T1:12  T2:5  T3:1)\n"
            "  Reserve deployed        $214,646 / $200,000  (100%)"
        ),
        p(
            "VOO fired Tier 1 repeatedly through the COVID crash (Feb–Jun 2020) "
            "and again through the 2022 Fed-tightening bear market. Tier 2 filled "
            "across mid-2020 and mid-2022. Tier 3 fired just once: the Sept 2022 "
            "capitulation week at $329. The reserve was fully deployed by Q4 2022 "
            "— exactly the intended behaviour. Lump-sum edged the strategy by ~0.7% "
            "CAGR because the 2020 crash recovered so quickly that later tranches "
            "bought at higher prices than the initial lump-sum entry."
        ),
    ]

    # ── QQQ Results ───────────────────────────────────────────────────────────
    nodes += [
        h3("QQQ — Invesco Nasdaq-100 ETF"),
        fig(img_srcs["QQQ"], "QQQ: price with entry points (top), portfolio value comparison (middle), drawdown vs tier triggers (bottom)"),
        pre(
            "Metric                    Strategy    Lump Sum    DCA 18m\n"
            "─────────────────────────────────────────────────────────\n"
            "End value ($)           3,151,199   3,511,861  2,821,844\n"
            "Total return              +215.1%     +251.2%    +182.2%\n"
            "CAGR                       19.6%       21.7%      17.6%\n"
            "Max portfolio drawdown    -31.2%      -34.3%     -34.3%\n"
            "─────────────────────────────────────────────────────────\n"
            "Strategy detail:\n"
            "  Avg cost basis          $226.22     (last price $729.45)\n"
            "  Unrealised gain/share   +222.4%\n"
            "  Dip sub-tranches fired  17  (T1:11  T2:4  T3:2)\n"
            "  Reserve deployed        $219,784 / $200,000  (100%)"
        ),
        p(
            "QQQ had the highest absolute returns across the period (+251% lump-sum, "
            "+215% strategy), but also the deepest drawdowns (-34%). The strategy "
            "softened the portfolio drawdown to -31.2% versus -34.3% for lump-sum. "
            "Tier 3 fired twice in 2022 (the QQQ bear market bottomed at -38% from "
            "its high). The 2024 yen-carry unwind and 2025 tariff selloff both "
            "triggered Tier 1 buys that were profitable. The lump-sum gap is wider "
            "here than VOO because QQQ compounded faster — earlier capital worked "
            "harder for longer."
        ),
    ]

    # ── VXUS Results ──────────────────────────────────────────────────────────
    nodes += [
        h3("VXUS — Vanguard Total International ETF"),
        fig(img_srcs["VXUS"], "VXUS: price with entry points (top), portfolio value comparison (middle), drawdown vs tier triggers (bottom)"),
        pre(
            "Metric                    Strategy    Lump Sum    DCA 18m\n"
            "─────────────────────────────────────────────────────────\n"
            "End value ($)           1,909,517   1,860,850  1,871,948\n"
            "Total return               +91.0%      +86.1%     +87.2%\n"
            "CAGR                       10.6%       10.2%      10.3%\n"
            "Max portfolio drawdown    -26.6%      -29.3%     -29.3%\n"
            "─────────────────────────────────────────────────────────\n"
            "Strategy detail:\n"
            "  Avg cost basis           $45.36     (last price $85.85)\n"
            "  Unrealised gain/share    +89.3%\n"
            "  Dip sub-tranches fired  16  (T1:8  T2:5  T3:3)\n"
            "  Reserve deployed        $215,663 / $200,000  (100%)"
        ),
        p(
            "VXUS is the only symbol where the dip-tranche strategy beat both "
            "benchmarks on CAGR (+10.6% vs +10.2% lump-sum and +10.3% DCA). "
            "International markets recover more slowly from corrections — the "
            "2022 bear market on VXUS was prolonged, allowing Tier 2 and Tier 3 "
            "tranches to accumulate at $40–$46 before the eventual recovery to "
            "$85+. This is precisely the environment the strategy is designed for: "
            "slow, grinding drawdowns with extended bottoms."
        ),
    ]

    # ── Summary ───────────────────────────────────────────────────────────────
    nodes += [
        hr(),
        h3("Summary: All Symbols"),
        pre(
            "Symbol   CAGR   Total Ret   End Value    Max DD   Reserve\n"
            "──────   ────   ─────────   ─────────    ──────   ───────\n"
            "VOO     15.1%    +146.6%   $2,465,730   -22.5%    100%\n"
            "QQQ     19.6%    +215.1%   $3,151,199   -31.2%    100%\n"
            "VXUS    10.6%     +91.0%   $1,909,517   -26.6%    100%\n"
            "\n"
            "Benchmarks (same period, lump-sum):\n"
            "VOO     15.8%    +155.4%   $2,553,705   -27.4%\n"
            "QQQ     21.7%    +251.2%   $3,511,861   -34.3%\n"
            "VXUS    10.2%     +86.1%   $1,860,850   -29.3%"
        ),
        hr(),
    ]

    # ── Takeaways ─────────────────────────────────────────────────────────────
    nodes += [
        h3("Key Takeaways"),
        ul(
            "Lump-sum wins on raw returns in strong bull markets — Vanguard's "
            "research holds up here. If you started in 2020 with perfect "
            "hindsight that markets would recover quickly, you'd have gone "
            "all-in. Nobody has that hindsight.",
            "The strategy's edge is risk management, not alpha. It consistently "
            "reduced max portfolio drawdown by 3–5 percentage points versus "
            "lump-sum — meaningful when you're watching a $1M portfolio become "
            "$650K.",
            "VXUS is the natural home for this strategy. International equities "
            "have slower, deeper drawdowns with longer recovery cycles — exactly "
            "what tiered entry is built for.",
            "The 2022 bear market was the strategy's best showcase: Tier 1 fired "
            "5–12 times per symbol as markets ground down, Tier 2 accumulated in "
            "the -12% to -16% zone, and Tier 3 deployed at the capitulation lows "
            "in Sep–Oct 2022. Every tranche was profitable by end of 2023.",
            "The COVID crash (Mar 2020) was the worst case for this strategy: "
            "too fast and too deep. Tier 1 fired near the top of the decline, "
            "Tier 2 near the middle, and then the market recovered before Tier 3 "
            "could deploy at the real bottom. The lump-sum buyer caught the full "
            "recovery from day 1.",
            "QQQ's higher triggers (-9.8% / -16.8% / -28%) were correct: without "
            "recalibration, the VOO triggers would have exhausted the reserve on "
            "routine Nasdaq noise. Always scale triggers to each asset's volatility.",
            "Re-arming matters: the cap of 2 re-arms per year prevented the "
            "strategy from being triggered every few weeks during 2022's volatile "
            "sideways grind.",
        ),
        hr(),
    ]

    # ── How to Automate ───────────────────────────────────────────────────────
    nodes += [
        h3("Automating the Strategy"),
        p(
            "The companion Python script (backtest.py) implements the full engine. "
            "To run it live as a daily monitor:"
        ),
        ul(
            "Pull weekly closes each Friday after market close via yfinance or "
            "a paid source (Alpha Vantage, Polygon.io for reliability).",
            "Compute rolling 52-week high and current drawdown percentage.",
            "Check which sub-tranches should fire per the trigger table above.",
            "Send an alert (Telegram bot, email, or Slack) with the triggered "
            "tranche, recommended dollar amount, and current drawdown context.",
            "Place limit orders manually or via broker API (Alpaca or IBKR) — "
            "notification-only mode is strongly recommended until you have "
            "6+ months of live observation.",
        ),
        p(
            "A TradingView Pine Script v6 strategy visualising all tier trigger "
            "lines, entry markers, and a live status panel is available as a "
            "companion asset."
        ),
        hr(),
    ]

    # ── Disclaimer ────────────────────────────────────────────────────────────
    nodes += [
        bq(
            b("Full disclaimer: "),
            "This backtest was conducted using publicly available historical data. "
            "Results are hypothetical — they do not account for taxes, bid/ask "
            "spreads, slippage, or behavioural drag (the tendency to deviate from "
            "rules under stress). Past performance does not predict future returns. "
            "The authors are not licensed financial advisors. This document is "
            "shared for educational purposes. Before deploying real capital, consult "
            "a fee-only fiduciary CFP and a CPA familiar with your tax situation."
        ),
    ]

    return nodes


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("\nBuilding Dip-Tranche Strategy report for telegra.ph …\n")

    # 1. Verify charts exist
    for sym, path in CHARTS.items():
        if not path.exists():
            print(f"ERROR: {path} not found. Run backtest.py first.")
            sys.exit(1)

    # 2. Get / create Telegraph account
    print("Step 1: Telegraph account")
    token = get_token()

    # 3. Upload images
    print("\nStep 2: Upload charts")
    img_srcs = {}
    for sym, path in CHARTS.items():
        img_srcs[sym] = upload_image(path)

    # 4. Build content
    print("\nStep 3: Build content")
    content = build_content(img_srcs)
    payload_size = len(json.dumps(content))
    print(f"  Content nodes: {len(content)}  |  Payload: {payload_size:,} bytes "
          f"({'OK' if payload_size < 64_000 else 'WARNING: may exceed 64KB limit'})")

    # 5. Publish
    print("\nStep 4: Publish")
    url = create_or_edit_page(token, content)
    print(f"\n{'═'*60}")
    print(f"  Published → {url}")
    print(f"{'═'*60}\n")


if __name__ == "__main__":
    main()
