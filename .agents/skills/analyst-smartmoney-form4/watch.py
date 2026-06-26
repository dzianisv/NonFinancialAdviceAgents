#!/usr/bin/env python3
"""analyst-smartmoney-form4 — dedup ledger for the Form 4 insider-buying tracker.

The script owns the DETERMINISTIC parts: what we've ALREADY recommended (so the same
ticker is never recommended twice per transaction month). The judgment parts — fetching
Form 4 filings from EDGAR/OpenInsider, filtering to open-market purchases, identifying
clusters, checking opportunistic vs routine — are the agent's job via the SKILL.md.

Dedup scope: ticker + transaction month (YYYY-MM). Same ticker can resurface in a new
month if fresh insider cluster activity appears.

Storage: JSONL at $FORM4_LEDGER or .agents/skills/analyst-smartmoney-form4/form4/recommended.jsonl

Usage:
  watch.py seen --ticker AAPL --window 2026-06   # exit 0 = SKIP (already recommended this month); exit 1 = NEW
  watch.py record --ticker AAPL --insider "Tim Cook" --role CEO --company "Apple Inc" \\
                  --transaction-date 2026-06-15 --amount 2000000 --cluster-size 3 \\
                  --action purchase --reason "cluster buy, CEO + CFO + Director"
  watch.py list
"""
import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

LEDGER = os.environ.get(
    "FORM4_LEDGER",
    os.path.join(
        os.path.dirname(__file__), "form4", "recommended.jsonl"
    ),
)


def _load():
    p = Path(LEDGER)
    if not p.exists():
        return []
    with open(p) as f:
        return [json.loads(line) for line in f if line.strip()]


def _save(rows):
    p = Path(LEDGER)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def seen(a):
    t = a.ticker.upper()
    w = a.window  # YYYY-MM
    hit = [
        r for r in _load()
        if r["ticker"].upper() == t and r.get("window") == w
    ]
    if hit:
        r = hit[0]
        print(
            f"SEEN {t} {w} — recommended {r['recommended_on']} "
            f"via {r.get('insider', '?')} ({r.get('role', '?')}); SKIP"
        )
        sys.exit(0)
    print(f"NEW {t} {w} — not yet recommended this month; ok to propose")
    sys.exit(1)


def record(a):
    rows = _load()
    t = a.ticker.upper()
    # Derive window from transaction_date (YYYY-MM-DD → YYYY-MM)
    w = a.transaction_date[:7]
    if any(r["ticker"].upper() == t and r.get("window") == w for r in rows):
        print(
            f"skip: {t} {w} already recommended — dedup rule, not recording again",
            file=sys.stderr,
        )
        sys.exit(3)
    rows.append(
        {
            "ticker": t,
            "insider": a.insider,
            "role": a.role,
            "company": a.company,
            "transaction_date": a.transaction_date,
            "amount": a.amount,
            "cluster_size": a.cluster_size,
            "action": a.action,
            "reason": a.reason or "",
            "window": w,
            "recommended_on": date.today().isoformat(),
        }
    )
    _save(rows)
    print(
        f"recorded {t}  insider={a.insider}  role={a.role}  "
        f"date={a.transaction_date}  cluster={a.cluster_size}  ({a.action})"
    )


def list_(a):
    rows = _load()
    if not rows:
        print("(none)")
        return
    for r in sorted(rows, key=lambda r: r["recommended_on"]):
        amt = f' ${r["amount"]:,}' if r.get("amount") else ""
        print(
            f'{r["recommended_on"]}  {r["ticker"]:6}{amt}  '
            f'{r.get("insider","?")} [{r.get("role","?")}]  '
            f'cluster={r.get("cluster_size","?")}  {r.get("reason","")}'
        )


def main():
    p = argparse.ArgumentParser(
        description="analyst-smartmoney-form4 dedup ledger"
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # seen subcommand
    s = sub.add_parser(
        "seen",
        help="Check if ticker+window already recommended (exit 0=SKIP, exit 1=NEW)",
    )
    s.add_argument("--ticker", required=True, help="Stock ticker, e.g. AAPL")
    s.add_argument(
        "--window",
        required=True,
        help="Transaction month YYYY-MM — dedup is scoped per month",
    )
    s.set_defaults(fn=seen)

    # record subcommand
    s = sub.add_parser("record", help="Record a new insider-buy recommendation")
    s.add_argument("--ticker", required=True)
    s.add_argument("--insider", required=True, help="Insider full name")
    s.add_argument("--role", required=True, help="e.g. CEO, CFO, Director")
    s.add_argument("--company", required=True, help="Company name")
    s.add_argument(
        "--transaction-date",
        required=True,
        dest="transaction_date",
        help="YYYY-MM-DD of the open-market purchase",
    )
    s.add_argument(
        "--amount",
        required=True,
        type=int,
        help="Dollar amount of the purchase",
    )
    s.add_argument(
        "--cluster-size",
        required=True,
        dest="cluster_size",
        type=int,
        help="Number of insiders buying in the same window",
    )
    s.add_argument(
        "--action",
        required=True,
        choices=["purchase"],
        help="Only open-market purchases qualify (sells are NOT recorded)",
    )
    s.add_argument("--reason", default="", help="Optional free-text rationale")
    s.set_defaults(fn=record)

    # list subcommand
    s = sub.add_parser("list", help="Print all records in the ledger")
    s.set_defaults(fn=list_)

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
