#!/usr/bin/env python3
"""
evaluate_hf.py — score a hedge-fund-manager decisions file against scenario ground truth.

Usage:
    python3 evals/hf/evaluate_hf.py --decisions <decisions.jsonl> [--judge <judgments.jsonl>]

decisions.jsonl: one JSON/line per scenario (see score_capability.py schema; must include `report`).
judgments.jsonl (optional): one/line with keys: label, places_trades, fabricated_holdings, qualitative (0-15).

The judge fields (invariants + qualitative) are kept SEPARATE from the runner (anti-self-grading);
coverage is parsed from the report text by the scorer, not taken on the runner's word.
"""
import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from score_capability import score  # noqa: E402


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
            dec["places_trades"] = j.get("places_trades", dec.get("places_trades", False))
            dec["fabricated_holdings"] = j.get("fabricated_holdings", dec.get("fabricated_holdings", False))
            dec["judge_score"] = j.get("qualitative", 0)
        r = score(sc, dec)
        split = sc.get("split", "train")
        agg[split].append(r["total"])
        rows.append((label, split, r))

    print(f"{'label':<18}{'split':<9}{'cov':>4}{'cad':>4}{'call':>5}{'gate':>5}{'qual':>5}{'tot':>5}  notes")
    print("-" * 92)
    for label, split, r in rows:
        notes = "VIOL " if not r["invariant_ok"] else ""
        notes += "; ".join(r.get("errors", []))
        print(f"{label:<18}{split:<9}{r['coverage']:>4}{r['cadence']:>4}{r['calls']:>5}"
              f"{r['gate']:>5}{r['qualitative']:>5}{r['total']:>5}  {notes}")
    print("-" * 92)
    for split in ("train", "holdout"):
        xs = agg[split]
        if xs:
            print(f"  {split:<8} mean total: {sum(xs)/len(xs):6.1f}   (n={len(xs)})")
    allx = agg["train"] + agg["holdout"]
    if allx:
        print(f"  {'ALL':<8} mean total: {sum(allx)/len(allx):6.1f}   (n={len(allx)})")
    viol = sum(1 for _, _, r in rows if not r["invariant_ok"])
    print(f"  invariant violations: {viol}")


if __name__ == "__main__":
    main()
