#!/usr/bin/env python3
"""analyst-smartmoney-13f — dedup ledger + manager roster for the 13F buy-watcher.

The script owns the DETERMINISTIC parts: who we track, and what we've ALREADY recommended
(so the same ticker is never recommended twice per quarter). The judgment parts — pulling
filings, reading puts-vs-longs, interpreting WHY — are the agent's job via the analyst-smartmoney-13f
SKILL.md (which leans on hedge-fund-13f-analysis).

Dedup scope: ticker + quarter. Same name can surface again in a new quarter if managers
show fresh action — each quarterly filing cycle is independent.

Storage: JSONL at $THIRTEENF_LEDGER or .cache/13F/recommended.jsonl
Roster:  JSON  at .cache/13F/roster.json (falls back to the verified default below)

Usage:
  watch.py roster
  watch.py seen <TICKER> --quarter 2026Q1   # exit 0 = already recommended this quarter (SKIP); exit 1 = NEW
  watch.py record --ticker LULU --manager burry --quarter 2026Q1 --action new \
                  [--reason "..."] [--price 230] [--source "EDGAR CIK 1649339"]
  watch.py list [--since YYYY-MM-DD]
"""
import argparse, json, os, sys
from datetime import date

_SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SKILL_DIR, "..", "..", ".."))
LEDGER = os.environ.get("THIRTEENF_LEDGER", os.path.join(_REPO_ROOT, ".cache", "13F", "recommended.jsonl"))
ROSTER = os.path.join(os.path.dirname(LEDGER), "roster.json")

# Verified CIKs only (SEC EDGAR). Honesty rule: never fabricate a CIK — unknowns are resolved
# at runtime by the agent via EDGAR company search, then added to 13f/roster.json.
DEFAULT_ROSTER = {
    "burry": {"fund": "Scion Asset Management", "cik": "0001649339", "note": "files PUTS often — bearish, not buys"},
    "buffett": {"fund": "Berkshire Hathaway", "cik": "0001067983"},
    "ackman": {"fund": "Pershing Square", "cik": "0001336528"},
    "klarman": {"fund": "Baupost Group", "cik": "0001061768"},
    "li-lu": {"fund": "Himalaya Capital", "cik": "0001709323"},
}


def _load():
    if not os.path.exists(LEDGER):
        return []
    with open(LEDGER) as f:
        return [json.loads(l) for l in f if l.strip()]


def _save(rows):
    os.makedirs(os.path.dirname(LEDGER) or ".", exist_ok=True)
    with open(LEDGER, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def _roster():
    if os.path.exists(ROSTER):
        with open(ROSTER) as f:
            return json.load(f)
    return DEFAULT_ROSTER


def roster(a):
    for k, v in _roster().items():
        note = f'  ({v["note"]})' if v.get("note") else ""
        print(f'  {k:10} CIK {v.get("cik","?")}  {v.get("fund","")}{note}')


def seen(a):
    t = a.ticker.upper()
    q = a.quarter
    hit = [r for r in _load() if r["ticker"].upper() == t and r["quarter"] == q]
    if hit:
        r = hit[0]
        print(f'SEEN {t} {q} — recommended {r["recommended_on"]} via {r["manager"]}; SKIP')
        sys.exit(0)
    print(f"NEW {t} {q} — not yet recommended this quarter; ok to propose")
    sys.exit(1)


def record(a):
    rows = _load()
    t = a.ticker.upper()
    q = a.quarter
    if any(r["ticker"].upper() == t and r["quarter"] == q for r in rows):
        print(f"skip: {t} {q} already recommended — dedup rule, not recording again", file=sys.stderr)
        sys.exit(3)
    rows.append({
        "ticker": t, "manager": a.manager, "quarter": q, "action": a.action,
        "reason": a.reason or "", "price_at_rec": a.price, "source": a.source or "",
        "recommended_on": date.today().isoformat(),
    })
    _save(rows)
    print(f"recorded {t}  via {a.manager}  {q}  ({a.action})")


def list_(a):
    rows = _load()
    if a.since:
        rows = [r for r in rows if r["recommended_on"] >= a.since]
    if not rows:
        print("(none)")
        return
    for r in sorted(rows, key=lambda r: r["recommended_on"]):
        px = f' @{r["price_at_rec"]}' if r.get("price_at_rec") else ""
        print(f'{r["recommended_on"]}  {r["ticker"]:6}{px}  {r["manager"]} {r["quarter"]} [{r["action"]}]  {r.get("reason","")}')


def main():
    p = argparse.ArgumentParser(description="analyst-smartmoney-13f dedup ledger + roster")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("roster").set_defaults(fn=roster)
    s = sub.add_parser("seen")
    s.add_argument("ticker")
    s.add_argument("--quarter", required=True, help="e.g. 2026Q1 — dedup is scoped per quarter")
    s.set_defaults(fn=seen)
    s = sub.add_parser("record")
    s.add_argument("--ticker", required=True); s.add_argument("--manager", required=True)
    s.add_argument("--quarter", required=True); s.add_argument("--action", required=True,
                   choices=["new", "add"], help="new=initiation, add=increased stake (puts/trims/exits are NOT buys)")
    s.add_argument("--reason"); s.add_argument("--price"); s.add_argument("--source"); s.set_defaults(fn=record)
    s = sub.add_parser("list"); s.add_argument("--since"); s.set_defaults(fn=list_)
    a = p.parse_args(); a.fn(a)


if __name__ == "__main__":
    main()
