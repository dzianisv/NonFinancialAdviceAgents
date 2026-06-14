#!/usr/bin/env python3
"""congressman-stock-watch — STOCK Act dedup ledger manager.

The HTTP fetching is done by the LLM agent (via WebFetch on capitoltrades.com).
This script only manages the dedup ledger so tickers are never proposed twice.

Usage:
  watch.py seen <TICKER>                  # exit 0=already recommended; exit 1=NEW
  watch.py record --ticker NVDA --member "Nancy Pelosi" --chamber house \\
                  --date 2026-01-15 --amount "$1,000,001+" --action purchase \\
                  [--reason "..."] [--committee "Science, Space & Technology"]
  watch.py list [--since YYYY-MM-DD]
"""
import argparse
import json
import os
import sys
from datetime import date, datetime

LEDGER = os.environ.get("CONGRESS_LEDGER", os.path.join("congress", "recommended.jsonl"))


def _load() -> list:
    if not os.path.exists(LEDGER):
        return []
    with open(LEDGER) as f:
        return [json.loads(l) for l in f if l.strip()]


def cmd_seen(a):
    t = a.ticker.upper()
    hit = [r for r in _load() if r["ticker"].upper() == t]
    if hit:
        r = hit[0]
        print(f"SEEN {t} — recommended {r['recommended_on']} via {r['member']} ({r['chamber']}); SKIP")
        sys.exit(0)
    print(f"NEW {t} — not yet recommended; ok to propose")
    sys.exit(1)


def cmd_record(a):
    try:
        datetime.strptime(a.date, "%Y-%m-%d")
    except ValueError:
        print(f"error: --date must be YYYY-MM-DD, got '{a.date}'", file=sys.stderr)
        sys.exit(2)
    rows = _load()
    t = a.ticker.upper()
    if any(r["ticker"].upper() == t for r in rows):
        print(f"skip: {t} already recommended — dedup rule", file=sys.stderr)
        sys.exit(3)
    entry = {
        "ticker": t,
        "member": a.member,
        "chamber": a.chamber,
        "transaction_date": a.date,
        "amount": a.amount or "",
        "action": a.action,
        "reason": a.reason or "",
        "committee": a.committee or "",
        "recommended_on": date.today().isoformat(),
    }
    os.makedirs(os.path.dirname(LEDGER) or ".", exist_ok=True)
    with open(LEDGER, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"recorded {t}  {a.member}  {a.chamber}  {a.date}  ({a.action})")


def cmd_list(a):
    rows = _load()
    if a.since:
        rows = [r for r in rows if r["recommended_on"] >= a.since]
    if not rows:
        print("(none)")
        return
    for r in sorted(rows, key=lambda r: r["recommended_on"]):
        print(f'{r["recommended_on"]}  {r["ticker"]:<6}  {r["member"]} [{r["chamber"]}]  '
              f'{r.get("amount","")}  {r.get("reason","")}')


def main():
    p = argparse.ArgumentParser(description="congressman-stock-watch dedup ledger")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("seen", help="check if ticker already recommended")
    s.add_argument("ticker")
    s.set_defaults(fn=cmd_seen)

    s = sub.add_parser("record", help="record a new recommendation")
    s.add_argument("--ticker", required=True)
    s.add_argument("--member", required=True)
    s.add_argument("--chamber", required=True, choices=["house", "senate"])
    s.add_argument("--date", required=True, help="transaction date YYYY-MM-DD")
    s.add_argument("--amount", default="")
    s.add_argument("--action", required=True, choices=["purchase", "exchange"])
    s.add_argument("--reason", default="")
    s.add_argument("--committee", default="")
    s.set_defaults(fn=cmd_record)

    s = sub.add_parser("list", help="list all recommended tickers")
    s.add_argument("--since", help="YYYY-MM-DD filter")
    s.set_defaults(fn=cmd_list)

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
