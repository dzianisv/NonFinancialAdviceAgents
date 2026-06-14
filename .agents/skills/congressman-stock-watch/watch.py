#!/usr/bin/env python3
"""congressman-stock-watch — STOCK Act dedup ledger + live disclosure fetcher.

Fetches from housestockwatcher.com + senatestockwatcher.com, filters for PURCHASES,
deduplicates against a JSONL ledger so the same ticker is never proposed twice.

Usage:
  watch.py recent [--days 90]             # fetch + print recent PURCHASE transactions
  watch.py roster                         # show tracked chambers (House + Senate)
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
from datetime import date, datetime, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError
from collections import defaultdict

LEDGER = os.environ.get("CONGRESS_LEDGER", os.path.join("congress", "recommended.jsonl"))

# Primary + fallback sources (tried in order)
HOUSE_APIS = [
    "https://housestockwatcher.com/api/transactions",
    "https://house-stock-watcher-data.s3-us-east-2.amazonaws.com/data/all_transactions.json",
]
SENATE_APIS = [
    "https://senatestockwatcher.com/api/transactions",
    "https://senate-stock-watcher-data.s3-us-east-2.amazonaws.com/data/all_transactions.json",
]
# Keep legacy names for backwards compat
HOUSE_API = HOUSE_APIS[0]
SENATE_API = SENATE_APIS[0]

PURCHASE_KEYWORDS = {"purchase", "buy", "bought", "exchange (partial)"}
SKIP_KEYWORDS = {"sale", "sale (partial)", "sale (full)", "sale_full", "sale_partial"}

AMOUNT_ORDER = [
    "$1,000,001+",
    "$500,001 - $1,000,000",
    "$250,001 - $500,000",
    "$100,001 - $250,000",
    "$50,001 - $100,000",
    "$15,001 - $50,000",
    "$1,001 - $15,000",
]


def _fetch_json(url: str) -> list:
    try:
        req = Request(url, headers={"User-Agent": "congressman-stock-watch/1.0 (educational)"})
        with urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except URLError as e:
        print(f"[WARN] fetch failed {url}: {e}", file=sys.stderr)
        return []


def _fetch_json_with_fallback(urls: list) -> list:
    for url in urls:
        result = _fetch_json(url)
        if result:
            return result
        print(f"[INFO] trying next fallback...", file=sys.stderr)
    return []


def _load() -> list:
    if not os.path.exists(LEDGER):
        return []
    with open(LEDGER) as f:
        return [json.loads(l) for l in f if l.strip()]


def _save(rows: list):
    os.makedirs(os.path.dirname(LEDGER) or ".", exist_ok=True)
    with open(LEDGER, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def _is_purchase(tx_type: str) -> bool:
    t = tx_type.lower().strip().replace("_", " ").replace("-", " ")
    if any(t == s or t.startswith(s) for s in SKIP_KEYWORDS):
        return False
    return t in PURCHASE_KEYWORDS or "purchase" in t


def _amount_rank(amount_str: str) -> int:
    a = (amount_str or "").strip()
    try:
        return AMOUNT_ORDER.index(a)
    except ValueError:
        return len(AMOUNT_ORDER)


def fetch_recent(days: int) -> list:
    cutoff = (datetime.now() - timedelta(days=days)).date()
    rows = []

    # House
    for tx in _fetch_json_with_fallback(HOUSE_APIS):
        tx_date_str = tx.get("transaction_date") or tx.get("disclosure_date") or ""
        try:
            tx_date = datetime.strptime(tx_date_str[:10], "%Y-%m-%d").date()
        except ValueError:
            continue
        if tx_date < cutoff:
            continue
        tx_type = tx.get("type") or tx.get("transaction_type") or ""
        if not _is_purchase(tx_type):
            continue
        ticker = (tx.get("ticker") or "").upper().strip()
        if not ticker or ticker in ("N/A", "--", ""):
            continue
        rows.append({
            "ticker": ticker,
            "member": tx.get("representative") or tx.get("name") or "Unknown",
            "chamber": "house",
            "transaction_date": tx_date_str[:10],
            "disclosure_date": tx.get("disclosure_date", "")[:10],
            "amount": tx.get("amount") or "",
            "asset_description": tx.get("asset_description") or tx.get("asset") or "",
        })

    # Senate
    for tx in _fetch_json_with_fallback(SENATE_APIS):
        tx_date_str = tx.get("transaction_date") or tx.get("disclosure_date") or ""
        try:
            tx_date = datetime.strptime(tx_date_str[:10], "%Y-%m-%d").date()
        except ValueError:
            continue
        if tx_date < cutoff:
            continue
        tx_type = tx.get("type") or tx.get("transaction_type") or ""
        if not _is_purchase(tx_type):
            continue
        ticker = (tx.get("ticker") or "").upper().strip()
        if not ticker or ticker in ("N/A", "--", ""):
            continue
        rows.append({
            "ticker": ticker,
            "member": tx.get("senator") or tx.get("name") or "Unknown",
            "chamber": "senate",
            "transaction_date": tx_date_str[:10],
            "disclosure_date": tx.get("disclosure_date", "")[:10],
            "amount": tx.get("amount") or "",
            "asset_description": tx.get("asset_description") or tx.get("asset") or "",
        })

    return rows


def cmd_recent(a):
    rows = fetch_recent(a.days)
    if not rows:
        print(f"(no purchase disclosures found in last {a.days} days — "
              "both APIs returned empty or are unreachable; verify housestockwatcher.com + senatestockwatcher.com)")
        return

    # Cluster by ticker
    clusters: dict[str, list] = defaultdict(list)
    for r in rows:
        clusters[r["ticker"]].append(r)

    # Sort: cluster size desc, then amount rank asc (lower = bigger)
    ranked = sorted(clusters.items(),
                    key=lambda kv: (-len(kv[1]), min(_amount_rank(x["amount"]) for x in kv[1])))

    already = {r["ticker"].upper() for r in _load()}

    print(f"{'TICKER':<8} {'CLUSTER':>7} {'AMOUNT':<28} {'MEMBERS'}")
    print("-" * 80)
    for ticker, txs in ranked:
        status = "[SEEN]" if ticker in already else "[NEW] "
        members = ", ".join(sorted({t["member"] for t in txs}))
        best_amount = sorted(txs, key=lambda x: _amount_rank(x["amount"]))[0]["amount"]
        dates = sorted(t["transaction_date"] for t in txs)
        print(f"{status} {ticker:<8} {len(txs):>3} buy(s)  {best_amount:<28} {members}")
        print(f"         dates: {dates[0]} … {dates[-1]}")


def cmd_roster(a):
    print("Tracked chambers: House (housestockwatcher.com) + Senate (senatestockwatcher.com)")
    print("All members who file STOCK Act disclosures are tracked automatically.")
    print(f"Ledger: {LEDGER}")


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
        print(f"skip: {t} already recommended — dedup rule, not recording again", file=sys.stderr)
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

    s = sub.add_parser("recent", help="fetch + print recent PURCHASE transactions")
    s.add_argument("--days", type=int, default=90)
    s.set_defaults(fn=cmd_recent)

    sub.add_parser("roster", help="show data sources").set_defaults(fn=cmd_roster)

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
