#!/usr/bin/env python3
"""
evaluate.py — score a decisions file against scenario ground truth.

Usage:
    python3 evals/pm/evaluate.py --decisions <decisions.jsonl> [--judge <judgments.jsonl>]

decisions.jsonl: one JSON/line, keys: label, regime_call, dip_tiers_active, rebalance_due
judgments.jsonl (optional, from a judge): label, places_trades, mentions_bull_lag,
    orders_actionable, qualitative (0-25)

Prints per-scenario breakdown + aggregate split by train/holdout. The judge fields
(invariant + qualitative) are kept SEPARATE from the model under test (anti-self-grading).
"""
import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from score_decision import score  # noqa: E402


def _load(path):
    out = {}
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if line:
            o = json.loads(line)
            out[o["label"]] = o
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--decisions", required=True)
    ap.add_argument("--judge", default=None)
    ap.add_argument("--scenarios", default=str(HERE / "scenarios" / "scenarios.jsonl"))
    a = ap.parse_args()

    scenarios = _load(a.scenarios)
    decisions = _load(a.decisions)
    judge = _load(a.judge) if a.judge else {}

    rows, agg = [], {"train": [], "holdout": []}
    for label, sc in scenarios.items():
        dec = dict(decisions.get(label, {}))
        if label in judge:
            j = judge[label]
            dec["places_trades"] = j.get("places_trades", False)
            dec["judge_score"] = j.get("qualitative", 0)
        r = score(sc, dec)
        split = sc.get("split", "train")
        agg[split].append(r["total"])
        rows.append((label, split, r))

    print(f"{'label':<18}{'split':<9}{'det':>5}{'qual':>6}{'inv':>5}{'total':>7}  notes")
    print("-" * 78)
    for label, split, r in rows:
        inv = "ok" if r["invariant_ok"] else "VIOL"
        notes = ",".join(r.get("errors", []))
        print(f"{label:<18}{split:<9}{r['deterministic']:>5}{r['qualitative']:>6}{inv:>5}{r['total']:>7}  {notes}")
    print("-" * 78)
    for split in ("train", "holdout"):
        xs = agg[split]
        if xs:
            print(f"  {split:<8} mean total: {sum(xs)/len(xs):6.1f}   (n={len(xs)})")
    allx = agg["train"] + agg["holdout"]
    print(f"  {'ALL':<8} mean total: {sum(allx)/len(allx):6.1f}   (n={len(allx)})")
    viol = sum(1 for _, _, r in rows if not r["invariant_ok"])
    print(f"  invariant violations: {viol}")


if __name__ == "__main__":
    main()
