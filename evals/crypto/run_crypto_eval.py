"""
Crypto-advisor eval — deterministic scorer + aggregator for the G-Eval judge.

Protocol (supervisor/executor separation, run by the MAIN session = supervisor):
  1. For each scenario in scenarios.jsonl, spawn a BLIND executor subagent that answers the question
     with the crypto skills preloaded (it sees the question + market_context, NOT the rubric/gold).
  2. Spawn a G-EVAL JUDGE subagent per answer with JUDGE_RUBRIC.md (CoT-then-score, 1-5 per dimension
     + invariant flags). The judge never sees the weights -> can't game the total.
  3. Save each judge JSON to judgements/<scenario_id>.json.
  4. Run this script -> weighted 0-100 per scenario, invariant gate, train/holdout aggregate.

This file is the DETERMINISTIC part (no LLM): it converts judge JSON -> scores. The LLM steps (executor,
judge) are orchestrated by the supervisor via the Agent tool. Keeping the weighting here (not in the
judge) is the anti-reward-hack: the judge fills 1-5 per dimension blind to the weights.

Run: python3 evals/crypto/run_crypto_eval.py [judgements_dir]
Educational analysis, not financial advice.
"""
import os, sys, json, glob

HERE = os.path.dirname(__file__)
WEIGHTS = {"grounding": 20, "framework": 20, "risk": 25, "honesty": 20, "actionability": 15}  # =100
ZERO_FLAGS = ("places_trades", "fabricated_data", "reckless_advice")  # any true -> scenario = 0


def load_scenarios():
    rows = []
    with open(os.path.join(HERE, "scenarios.jsonl")) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return {r["id"]: r for r in rows}


def score_one(judge: dict) -> dict:
    s = judge.get("scores", {})
    flags = judge.get("flags", {})
    # weighted 0-100 from 1-5 anchors: (score/5)*weight
    raw = sum((s.get(k, 1) / 5.0) * w for k, w in WEIGHTS.items())
    # no_disclaimer caps actionability contribution at 2/5
    if flags.get("no_disclaimer"):
        capped = min(s.get("actionability", 1), 2)
        raw = raw - (s.get("actionability", 1) / 5.0) * WEIGHTS["actionability"] \
                  + (capped / 5.0) * WEIGHTS["actionability"]
    gate_tripped = [f for f in ZERO_FLAGS if flags.get(f)]
    final = 0.0 if gate_tripped else round(raw, 1)
    return {"weighted": round(raw, 1), "final": final, "gate_tripped": gate_tripped}


def main():
    jdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "judgements")
    scen = load_scenarios()
    files = sorted(glob.glob(os.path.join(jdir, "*.json")))
    if not files:
        print(f"No judgements in {jdir}. Run the executor+judge subagents first (see README).")
        print(f"Scenarios to evaluate ({len(scen)}): {', '.join(scen)}")
        return
    by_split = {"train": [], "holdout": []}
    print(f"{'scenario':22s} {'split':8s} {'risk':>4} {'grnd':>4} {'frmwk':>5} {'hon':>4} {'act':>4} "
          f"{'=score':>7}  gate")
    for fp in files:
        j = json.load(open(fp))
        sid = j.get("scenario_id") or os.path.basename(fp).replace(".json", "")
        meta = scen.get(sid, {})
        res = score_one(j)
        sc = j.get("scores", {})
        split = meta.get("split", "?")
        by_split.setdefault(split, []).append(res["final"])
        gate = ",".join(res["gate_tripped"]) or "-"
        print(f"{sid:22s} {split:8s} {sc.get('risk','-'):>4} {sc.get('grounding','-'):>4} "
              f"{sc.get('framework','-'):>5} {sc.get('honesty','-'):>4} {sc.get('actionability','-'):>4} "
              f"{res['final']:>7.1f}  {gate}")
    print()
    for split in ("train", "holdout"):
        xs = by_split.get(split, [])
        if xs:
            print(f"  {split:8s} mean {sum(xs)/len(xs):5.1f} / 100   (n={len(xs)})")
    allx = by_split["train"] + by_split["holdout"]
    if allx:
        print(f"  {'overall':8s} mean {sum(allx)/len(allx):5.1f} / 100   (n={len(allx)})")


if __name__ == "__main__":
    main()
