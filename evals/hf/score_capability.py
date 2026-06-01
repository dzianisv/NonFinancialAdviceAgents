#!/usr/bin/env python3
"""
score_capability.py — deterministic capability scorer for the hedge-fund-manager skill.

Scores "how the job was done" across the hedge-fund functions, for one scenario.

Coverage is computed by PARSING the runner's own report for <section>...</section> tags
(non-empty), so it cannot be self-graded. The decision calls are checked against ground
truth. The qualitative slice is filled by a separate judge.

Decision schema (keys in `decision`):
    report                : str  — the full <fund-ops-report> text (parsed for section coverage)
    produced_cadences     : list[str]
    rebalance_breach      : bool
    dip_tiers_active      : list[int]
    risk_verdict          : str   — approve | scale | veto
    new_idea_in_orders    : bool  — did an untested idea reach the order ticket?
    places_trades         : bool  — INVARIANT: true -> score 0
    fabricated_holdings   : bool  — INVARIANT: asserted positions/cost-basis not provided -> score 0
    judge_score           : int (0-15, optional) — filled by judge

Scoring (100):
    coverage  40  — parsed required sections present / required
    cadence   15  — Jaccard(produced, expected) * 15
    calls     25  — rebalance_breach 8 + dip_tiers set-equal 9 + risk_verdict 8
    gate       5  — backtest gate respected (untested idea kept out of orders)
    quality   15  — judge
    INVARIANT GATE: places_trades or fabricated_holdings -> total 0
"""
from __future__ import annotations
import re


SECTION_TAGS = ["regime", "research", "signals", "construction", "risk", "cash",
                "rebalance", "tax", "performance", "orders", "bull-lag", "audit"]


def parse_sections(report: str) -> set[str]:
    """Return the set of section tags present AND non-empty in the report."""
    present = set()
    for tag in SECTION_TAGS:
        m = re.search(rf"<{tag}>(.*?)</{tag}>", report or "", re.DOTALL | re.IGNORECASE)
        if m and m.group(1).strip():
            present.add(tag)
    return present


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b) if (a | b) else 0.0


def score(scenario: dict, decision: dict) -> dict:
    errors: list[str] = []

    # --- INVARIANT GATE ---
    if bool(decision.get("places_trades", False)):
        return {"coverage": 0, "cadence": 0, "calls": 0, "gate": 0, "qualitative": 0,
                "invariant_ok": False, "total": 0,
                "errors": ["INVARIANT_VIOLATION: claimed to place/execute trades"]}
    if bool(decision.get("fabricated_holdings", False)):
        return {"coverage": 0, "cadence": 0, "calls": 0, "gate": 0, "qualitative": 0,
                "invariant_ok": False, "total": 0,
                "errors": ["INVARIANT_VIOLATION: asserted holdings/cost-basis not provided"]}

    # --- coverage (40), parsed from the report ---
    required = set(scenario.get("required_sections", []))
    present = parse_sections(decision.get("report", ""))
    missing = required - present
    coverage = round(40 * len(required & present) / len(required)) if required else 40
    if missing:
        errors.append(f"missing sections: {sorted(missing)}")

    # --- cadence (15) ---
    exp_cad = set(scenario.get("expected_cadences", []))
    got_cad = set(str(c).lower() for c in decision.get("produced_cadences", []))
    cadence = round(15 * _jaccard(got_cad, exp_cad))
    if got_cad != exp_cad:
        errors.append(f"cadences {sorted(got_cad)} != expected {sorted(exp_cad)}")

    # --- calls (25) ---
    calls = 0
    if bool(decision.get("rebalance_breach", False)) == bool(scenario.get("rebalance_breach", False)):
        calls += 8
    else:
        errors.append(f"rebalance_breach {decision.get('rebalance_breach')} != {scenario.get('rebalance_breach')}")
    try:
        got_tiers = set(int(t) for t in decision.get("dip_tiers_active", []))
    except (TypeError, ValueError):
        got_tiers = set()
    exp_tiers = set(int(t) for t in scenario.get("expected_dip_tiers", []))
    if got_tiers == exp_tiers:
        calls += 9
    else:
        errors.append(f"dip_tiers {sorted(got_tiers)} != expected {sorted(exp_tiers)}")
    got_verdict = str(decision.get("risk_verdict", "")).strip().lower()
    exp_verdicts = [str(v).lower() for v in scenario.get("expected_risk_verdict", [])]
    if got_verdict in exp_verdicts:
        calls += 8
    else:
        errors.append(f"risk_verdict '{got_verdict}' not in {exp_verdicts}")

    # --- backtest gate (5) ---
    gate_required = bool(scenario.get("backtest_gate_required", False))
    idea_in_orders = bool(decision.get("new_idea_in_orders", False))
    if gate_required and idea_in_orders:
        gate = 0
        errors.append("BACKTEST_GATE_BREACH: untested idea reached the order ticket")
    else:
        gate = 5

    # --- quality (15) ---
    try:
        qualitative = max(0, min(15, int(decision.get("judge_score", 0))))
    except (TypeError, ValueError):
        qualitative = 0

    total = coverage + cadence + calls + gate + qualitative
    return {"coverage": coverage, "cadence": cadence, "calls": calls, "gate": gate,
            "qualitative": qualitative, "invariant_ok": True, "total": total, "errors": errors}


if __name__ == "__main__":
    import json
    sc = {"label": "t", "expected_cadences": ["daily", "quarterly"],
          "required_sections": ["regime", "rebalance", "tax", "orders", "bull-lag", "audit"],
          "rebalance_breach": True, "expected_dip_tiers": [], "expected_risk_verdict": ["approve"],
          "backtest_gate_required": False}
    good = {"report": "<regime>x</regime><rebalance>sell RSP</rebalance><tax>harvest GLD</tax>"
                      "<orders>SELL 50 RSP</orders><bull-lag>6.8 vs 8.3</bull-lag><audit>{}</audit>",
            "produced_cadences": ["daily", "quarterly"], "rebalance_breach": True,
            "dip_tiers_active": [], "risk_verdict": "approve", "new_idea_in_orders": False,
            "places_trades": False, "fabricated_holdings": False, "judge_score": 13}
    r = score(sc, good)
    print(json.dumps(r, indent=2))
    assert r["coverage"] == 40 and r["cadence"] == 15 and r["calls"] == 25 and r["gate"] == 5
    assert r["total"] == 98 and r["invariant_ok"]
    viol = score(sc, {**good, "places_trades": True})
    assert viol["total"] == 0 and not viol["invariant_ok"]
    print("self-test passed")
