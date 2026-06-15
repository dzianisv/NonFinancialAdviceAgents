#!/usr/bin/env python3
"""forecast-ledger — log dated probabilistic forecasts, resolve them, score calibration.

Why: a forecast you never grade is an opinion. Tetlock's whole finding is that forecasters
improve ONLY via scored feedback (Brier + calibration). This is that feedback loop.

Storage: one JSON object per line (JSONL) at $FORECAST_LEDGER or ./forecasts/ledger.jsonl

Usage:
  ledger.py add --asset BTC --q "BTC <=$50k before 2026-07-01" --p 0.65 --by 2026-07-01 \
                [--source "superforecasting; Polymarket $42M"] [--lens macro,onchain,prediction-market] [--id SLUG]
  ledger.py resolve <id> <yes|no> [--on YYYY-MM-DD] [--note "..."]
  ledger.py list [--open | --due | --all]     # default: open
  ledger.py score [--by lens|source]          # Brier + calibration over resolved forecasts
"""
import argparse, json, os, sys
from datetime import date

LEDGER = os.environ.get("FORECAST_LEDGER", os.path.join("forecasts", "ledger.jsonl"))


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


def _slug(asset, q, created):
    base = "".join(c if c.isalnum() else "-" for c in q.lower())
    while "--" in base:
        base = base.replace("--", "-")
    base = base.strip("-")[:40].strip("-")
    return f"{created}-{asset.lower()}-{base}"


def add(a):
    rows = _load()
    created = a.created or date.today().isoformat()
    rid = a.id or _slug(a.asset, a.q, created)
    if any(r["id"] == rid for r in rows):
        sys.exit(f"id exists: {rid}")
    if not (0.0 <= a.p <= 1.0):
        sys.exit("--p must be 0..1")
    rows.append({
        "id": rid, "created": created, "asset": a.asset,
        "question": a.q, "prob": a.p, "horizon": a.by,
        "source": a.source or "", "lenses": a.lens.split(",") if a.lens else [],
        "flip": a.flip or "",  # invalidation: the condition that would prove this call wrong
        "status": "open", "outcome": None, "resolved_on": None, "note": "",
    })
    _save(rows)
    print(f"added {rid}  p={a.p}  by {a.by}")


def resolve(a):
    rows = _load()
    out = a.outcome.lower() in ("yes", "y", "true", "1", "hit")
    for r in rows:
        if r["id"] == a.id:
            r_on = a.on or date.today().isoformat()
            if r["horizon"] > r_on:
                print(f"WARNING: resolving before horizon {r['horizon']} — outcome may not be known yet",
                      file=sys.stderr)
            r.update(status="resolved", outcome=out, resolved_on=r_on, note=a.note or r.get("note", ""))
            _save(rows)
            br = (r["prob"] - (1.0 if out else 0.0)) ** 2
            print(f"resolved {a.id}  outcome={out}  predicted={r['prob']}  brier={br:.3f}")
            return
    sys.exit(f"id not found: {a.id}")


def list_(a):
    rows = _load()
    today = date.today().isoformat()
    if a.all:
        sel = rows
    elif a.due:
        sel = [r for r in rows if r["status"] == "open" and r["horizon"] <= today]
    else:  # bare `list` and explicit `--open` are the same view by design: open forecasts
        sel = [r for r in rows if r["status"] == "open"]
    if not sel:
        print("(none)")
        return
    for r in sel:
        due = "  ** DUE **" if r["status"] == "open" and r["horizon"] <= today else ""
        oc = "" if r["outcome"] is None else f"  -> {'HIT' if r['outcome'] else 'MISS'}"
        print(f'{r["id"]}\n    p={r["prob"]}  by {r["horizon"]}  [{r["status"]}]{due}{oc}  {r["question"]}')
        if r.get("flip"):
            print(f'    flip: {r["flip"]}')


def score(a):
    rows = [r for r in _load() if r["status"] == "resolved"]
    if not rows:
        print("no resolved forecasts yet")
        return
    def brier(rs):
        return sum((r["prob"] - (1.0 if r["outcome"] else 0.0)) ** 2 for r in rs) / len(rs)
    base = sum(1 for r in rows if r["outcome"]) / len(rows)
    print(f"resolved: {len(rows)}   base rate (hit freq): {base:.2%}")
    print(f"Brier (lower=better, 0.25=coinflip, 0=perfect): {brier(rows):.3f}")
    # calibration: predicted-prob deciles vs observed hit frequency
    print("\ncalibration  [bin] n  predicted -> observed")
    for lo in [i / 10 for i in range(10)]:
        b = [r for r in rows if lo <= r["prob"] < lo + 0.1 or (lo == 0.9 and r["prob"] == 1.0)]
        if b:
            pred = sum(r["prob"] for r in b) / len(b)
            obs = sum(1 for r in b if r["outcome"]) / len(b)
            flag = ""
            if len(b) >= 3:  # don't flag mis/over-confidence on noise
                flag = "  <-- overconfident" if pred - obs > 0.15 else ("  <-- underconfident" if obs - pred > 0.15 else "")
            note = "" if len(b) >= 3 else "  (n<3: noise)"
            print(f"  [{lo:.1f}-{lo+0.1:.1f}] n={len(b)}  {pred:.0%} -> {obs:.0%}{flag}{note}")
    if a.by:
        key = "lenses" if a.by == "lens" else "source"
        print(f"\nBrier by {a.by}:")
        groups = {}
        for r in rows:
            if a.by == "lens":
                keys = r.get("lenses") or ["(none)"]
            else:
                keys = [r.get("source") or "(none)"]
            for k in keys:
                groups.setdefault(k, []).append(r)
        for k, rs in sorted(groups.items(), key=lambda kv: brier(kv[1])):
            print(f"  {brier(rs):.3f}  (n={len(rs)})  {k}")


def main():
    p = argparse.ArgumentParser(description="forecast-ledger: log, resolve, score probabilistic forecasts")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("add"); s.add_argument("--asset", required=True); s.add_argument("--q", required=True)
    s.add_argument("--p", type=float, required=True); s.add_argument("--by", required=True)
    s.add_argument("--source"); s.add_argument("--lens"); s.add_argument("--id")
    s.add_argument("--flip", help="invalidation: the condition that would prove this call wrong")
    s.add_argument("--created", help="forecast date YYYY-MM-DD (default today) — backdate a past call"); s.set_defaults(fn=add)
    s = sub.add_parser("resolve"); s.add_argument("id"); s.add_argument("outcome")
    s.add_argument("--on"); s.add_argument("--note"); s.set_defaults(fn=resolve)
    s = sub.add_parser("list"); s.add_argument("--open", action="store_true"); s.add_argument("--due", action="store_true")
    s.add_argument("--all", action="store_true"); s.set_defaults(fn=list_)
    s = sub.add_parser("score"); s.add_argument("--by", choices=["lens", "source"]); s.set_defaults(fn=score)
    a = p.parse_args(); a.fn(a)


if __name__ == "__main__":
    main()
