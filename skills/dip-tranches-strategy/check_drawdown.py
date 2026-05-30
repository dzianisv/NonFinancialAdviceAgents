#!/usr/bin/env python3
"""
check_drawdown.py — Daily dip-tranche monitor for S&P 500 ETFs.

Computes current drawdown from 52-week high and determines which sub-tranches
of the dip-tranche strategy should fire.

Usage:
    python check_drawdown.py                       # default VOO, $200K reserve
    python check_drawdown.py --ticker IVV
    python check_drawdown.py --reserve 500000      # $500K dip reserve
    python check_drawdown.py --json                # JSON output for automation

Requires: pip install yfinance

For more reliable production use, swap the data source. See references/data-sources.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta


@dataclass
class SubTranche:
    name: str
    trigger_pct: float       # drawdown from 52w high to trigger (negative)
    amount: float            # USD to deploy
    weeks_below_threshold: int = 0  # for time-based triggers (0 = price trigger only)


@dataclass
class TierPlan:
    tier: int
    trigger_pct: float
    total_amount: float
    sub_tranches: list[SubTranche]


def build_plan(reserve: float) -> list[TierPlan]:
    """Build the standard 20/30/50 tier plan from the dip-tranches-strategy skill."""
    t1_amt = reserve * 0.20  # Tier 1 = 20% of reserve
    t2_amt = reserve * 0.30  # Tier 2 = 30% of reserve
    t3_amt = reserve * 0.50  # Tier 3 = 50% of reserve

    return [
        TierPlan(
            tier=1,
            trigger_pct=-7.0,
            total_amount=t1_amt,
            sub_tranches=[
                SubTranche("1a", -7.0, t1_amt / 4),
                SubTranche("1b", -8.5, t1_amt / 4),
                SubTranche("1c", -10.0, t1_amt / 4),
                SubTranche("1d", -7.0, t1_amt / 4, weeks_below_threshold=2),
            ],
        ),
        TierPlan(
            tier=2,
            trigger_pct=-12.0,
            total_amount=t2_amt,
            sub_tranches=[
                SubTranche("2a", -12.0, t2_amt / 4),
                SubTranche("2b", -14.0, t2_amt / 4),
                SubTranche("2c", -16.0, t2_amt / 4),
                SubTranche("2d", -12.0, t2_amt / 4, weeks_below_threshold=3),
            ],
        ),
        TierPlan(
            tier=3,
            trigger_pct=-20.0,
            total_amount=t3_amt,
            sub_tranches=[
                SubTranche("3a", -20.0, t3_amt / 4),
                SubTranche("3b", -25.0, t3_amt / 4),
                SubTranche("3c", -30.0, t3_amt / 4),
                SubTranche("3d", -20.0, t3_amt / 4, weeks_below_threshold=4),
            ],
        ),
    ]


def fetch_price_data(ticker: str) -> tuple[float, float, str]:
    """
    Returns (current_close, 52w_high, as_of_date_str).
    Uses yfinance. Replace this function to swap data sources.
    """
    try:
        import yfinance as yf
    except ImportError:
        print("ERROR: yfinance not installed. Run: pip install yfinance", file=sys.stderr)
        sys.exit(1)

    end = datetime.now()
    start = end - timedelta(days=400)

    t = yf.Ticker(ticker)
    hist = t.history(start=start, end=end, interval="1d")

    if hist.empty:
        raise RuntimeError(f"No data returned for {ticker}. Yahoo may be rate-limiting.")

    last_year = hist.tail(252)  # ~52 weeks of trading days
    high_52w = float(last_year["High"].max())
    current = float(hist["Close"].iloc[-1])
    as_of = hist.index[-1].strftime("%Y-%m-%d")

    return current, high_52w, as_of


def evaluate(current: float, high_52w: float, plan: list[TierPlan]) -> dict:
    """Determine which sub-tranches are triggered by the current drawdown."""
    drawdown_pct = (current - high_52w) / high_52w * 100

    triggered: list[dict] = []
    pending: list[dict] = []

    for tier in plan:
        for sub in tier.sub_tranches:
            if sub.weeks_below_threshold > 0:
                # Time-based triggers can't be evaluated from a single snapshot.
                # Surface them as informational only.
                continue

            trigger_price = high_52w * (1 + sub.trigger_pct / 100)
            entry = {
                "tier": tier.tier,
                "sub_tranche": sub.name,
                "trigger_pct": sub.trigger_pct,
                "trigger_price": round(trigger_price, 2),
                "amount_usd": round(sub.amount, 2),
            }
            if drawdown_pct <= sub.trigger_pct:
                triggered.append(entry)
            else:
                pending.append(entry)

    return {
        "drawdown_pct": round(drawdown_pct, 2),
        "triggered": triggered,
        "pending": pending,
    }


def format_text_report(ticker: str, current: float, high_52w: float,
                       as_of: str, reserve: float, result: dict) -> str:
    lines = [
        f"=== Dip-Tranche Monitor — {ticker} ===",
        f"As of:        {as_of}",
        f"Current:      ${current:,.2f}",
        f"52-week high: ${high_52w:,.2f}",
        f"Drawdown:     {result['drawdown_pct']:.2f}%",
        f"Dip reserve:  ${reserve:,.0f}",
        "",
    ]

    if result["triggered"]:
        lines.append(f"** {len(result['triggered'])} SUB-TRANCHE(S) TRIGGERED **")
        for t in result["triggered"]:
            lines.append(
                f"  Tier {t['tier']}-{t['sub_tranche']}: "
                f"buy ${t['amount_usd']:,.0f} at limit ${t['trigger_price']:.2f} "
                f"({t['trigger_pct']:.1f}% from high)"
            )
        lines.append("")
    else:
        lines.append("No price-based triggers fired. Hold position.")
        lines.append("")

    if result["pending"]:
        lines.append("Pending price levels (set limit orders):")
        for p in result["pending"][:6]:  # show next few
            lines.append(
                f"  Tier {p['tier']}-{p['sub_tranche']}: "
                f"${p['amount_usd']:,.0f} @ ${p['trigger_price']:.2f} "
                f"({p['trigger_pct']:.1f}%)"
            )

    lines.append("")
    lines.append("Reminder: this is an analytical tool, not financial advice.")
    lines.append("Use weekly closes for actual trigger decisions, not snapshot prints.")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Dip-tranche drawdown monitor")
    parser.add_argument("--ticker", default="VOO", help="ETF ticker (default: VOO)")
    parser.add_argument("--reserve", type=float, default=200_000,
                        help="Dip reserve size in USD (default: 200000)")
    parser.add_argument("--json", action="store_true", help="Output JSON for automation")
    args = parser.parse_args()

    current, high_52w, as_of = fetch_price_data(args.ticker)
    plan = build_plan(args.reserve)
    result = evaluate(current, high_52w, plan)

    if args.json:
        output = {
            "ticker": args.ticker,
            "as_of": as_of,
            "current": current,
            "high_52w": high_52w,
            "reserve": args.reserve,
            **result,
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        print(format_text_report(args.ticker, current, high_52w, as_of,
                                 args.reserve, result))


if __name__ == "__main__":
    main()
