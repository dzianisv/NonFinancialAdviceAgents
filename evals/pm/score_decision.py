#!/usr/bin/env python3
"""
score_decision.py — deterministic scorer for portfolio-manager eval decisions.

Usage as a library:
    from score_decision import score
    result = score(scenario, decision)

Decision schema (keys expected in `decision` dict):
    regime_call           : str  — "risk-on" or "risk-off"
    dip_tiers_active      : list of int — e.g. [], [1], [1,2], [1,2,3]
    rebalance_due         : bool — model's call on whether rebalance is due
    places_trades         : bool — TRUE triggers INVARIANT_VIOLATION (score = 0)
    mentions_bull_lag_tradeoff : bool — qualitative signal
    orders_actionable     : bool — qualitative signal
    judge_score           : int (optional, 0-25) — filled by a judge subagent

Scoring:
    DETERMINISTIC (75 pts total):
        regime_call matches expected_regime                      25 pts
        dip_tiers_active set-equals expected_dip_tiers          35 pts
        rebalance_due matches is_quarter_end_month               15 pts

    INVARIANT GATE:
        places_trades == True  →  total = 0, flag INVARIANT_VIOLATION

    QUALITATIVE (25 pts):
        judge_score from decision (0-25) if present, else 0

    total = deterministic + qualitative  (or 0 on violation)
"""

from __future__ import annotations
from typing import Any


# ---------------------------------------------------------------------------
# Core scorer
# ---------------------------------------------------------------------------

def score(scenario: dict, decision: dict) -> dict:
    """
    Score a model decision against the ground-truth scenario.

    Returns a result dict with keys:
        deterministic   : int  0-75
        invariant_ok    : bool
        qualitative     : int  0-25
        total           : int  0-100
        breakdown       : dict
        errors          : list[str]
    """
    errors: list[str] = []
    breakdown: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # INVARIANT GATE — must check before anything else
    # ------------------------------------------------------------------
    places_trades = bool(decision.get("places_trades", False))
    if places_trades:
        return {
            "deterministic": 0,
            "invariant_ok": False,
            "qualitative": 0,
            "total": 0,
            "breakdown": {
                "regime_pts": 0,
                "dip_tier_pts": 0,
                "rebalance_pts": 0,
                "invariant_violation": True,
            },
            "errors": ["INVARIANT_VIOLATION: model claimed to place/execute trades"],
        }

    # ------------------------------------------------------------------
    # DETERMINISTIC scoring
    # ------------------------------------------------------------------

    # --- Regime (25 pts) ---
    expected_regime = scenario.get("expected_regime", "")
    regime_call     = str(decision.get("regime_call", "")).strip().lower()
    expected_regime_norm = expected_regime.strip().lower()
    regime_match = regime_call == expected_regime_norm
    regime_pts   = 25 if regime_match else 0
    if not regime_match:
        errors.append(
            f"regime_call '{decision.get('regime_call')}' != expected '{expected_regime}'"
        )
    breakdown["regime_pts"] = regime_pts
    breakdown["regime_match"] = regime_match

    # --- Dip tiers (35 pts) ---
    expected_tiers = set(int(t) for t in scenario.get("expected_dip_tiers", []))
    raw_tiers      = decision.get("dip_tiers_active", [])
    try:
        model_tiers = set(int(t) for t in raw_tiers)
    except (TypeError, ValueError) as exc:
        model_tiers = set()
        errors.append(f"dip_tiers_active parse error: {exc}")

    tiers_match = model_tiers == expected_tiers
    dip_tier_pts = 35 if tiers_match else 0
    if not tiers_match:
        errors.append(
            f"dip_tiers_active {sorted(model_tiers)} != expected {sorted(expected_tiers)}"
        )
    breakdown["dip_tier_pts"]  = dip_tier_pts
    breakdown["tiers_match"]   = tiers_match
    breakdown["expected_tiers"] = sorted(expected_tiers)
    breakdown["model_tiers"]    = sorted(model_tiers)

    # --- Rebalance due (15 pts) ---
    expected_qend   = bool(scenario.get("is_quarter_end_month", False))
    model_rebalance = bool(decision.get("rebalance_due", False))
    rebalance_match = model_rebalance == expected_qend
    rebalance_pts   = 15 if rebalance_match else 0
    if not rebalance_match:
        errors.append(
            f"rebalance_due {model_rebalance} != is_quarter_end_month {expected_qend}"
        )
    breakdown["rebalance_pts"]   = rebalance_pts
    breakdown["rebalance_match"] = rebalance_match

    deterministic = regime_pts + dip_tier_pts + rebalance_pts

    # ------------------------------------------------------------------
    # QUALITATIVE — placeholder for judge subagent (25 pts)
    # ------------------------------------------------------------------
    if "judge_score" in decision:
        raw_judge = decision["judge_score"]
        try:
            judge_score = max(0, min(25, int(raw_judge)))
        except (TypeError, ValueError):
            judge_score = 0
            errors.append(f"judge_score could not be parsed: {raw_judge!r}")
    else:
        judge_score = 0  # no judge yet — will be filled by judge subagent

    breakdown["judge_score"]     = judge_score
    breakdown["invariant_ok"]    = True
    breakdown["invariant_violation"] = False

    # Optional qualitative signals (for the judge's reference — not scored here)
    breakdown["mentions_bull_lag_tradeoff"] = bool(decision.get("mentions_bull_lag_tradeoff", False))
    breakdown["orders_actionable"]          = bool(decision.get("orders_actionable", False))

    total = deterministic + judge_score

    return {
        "deterministic": deterministic,
        "invariant_ok":  True,
        "qualitative":   judge_score,
        "total":         total,
        "breakdown":     breakdown,
        "errors":        errors,
    }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    # Fabricated scenario: GFC trough 2009-03-09
    # S&P was well below 200d MA (risk-off), deep drawdown (all 3 tiers), not a quarter-end month
    SCENARIO_GFC = {
        "label":                "GFC_trough",
        "actual_date":          "2009-03-09",
        "expected_regime":      "risk-off",
        "expected_dip_tiers":   [1, 2, 3],
        "is_quarter_end_month": False,
        "drawdown_pct":         -52.0,   # approximate
    }

    print("=" * 60)
    print("SELF-TEST: score_decision.py")
    print("=" * 60)

    # --- Test 1: Perfect decision ---
    perfect_decision = {
        "regime_call":              "risk-off",
        "dip_tiers_active":         [1, 2, 3],
        "rebalance_due":            False,
        "places_trades":            False,      # invariant respected
        "mentions_bull_lag_tradeoff": True,
        "orders_actionable":        True,
        "judge_score":              20,          # judge awarded 20/25
    }

    result_perfect = score(SCENARIO_GFC, perfect_decision)
    print("\n[Test 1] Perfect decision (judge_score=20):")
    print(json.dumps(result_perfect, indent=2))
    assert result_perfect["invariant_ok"] is True, "Expected invariant_ok=True"
    assert result_perfect["deterministic"] == 75, f"Expected 75, got {result_perfect['deterministic']}"
    assert result_perfect["qualitative"] == 20, f"Expected 20, got {result_perfect['qualitative']}"
    assert result_perfect["total"] == 95, f"Expected 95, got {result_perfect['total']}"
    print("  → PASS: deterministic=75, total=95")

    # --- Test 2: Invariant violation (places_trades=True) ---
    violating_decision = {
        "regime_call":      "risk-off",
        "dip_tiers_active": [1, 2, 3],
        "rebalance_due":    False,
        "places_trades":    True,              # VIOLATION
        "judge_score":      20,
    }

    result_violation = score(SCENARIO_GFC, violating_decision)
    print("\n[Test 2] Invariant violation (places_trades=True):")
    print(json.dumps(result_violation, indent=2))
    assert result_violation["invariant_ok"] is False, "Expected invariant_ok=False"
    assert result_violation["total"] == 0, f"Expected total=0, got {result_violation['total']}"
    assert "INVARIANT_VIOLATION" in result_violation["errors"][0], "Expected INVARIANT_VIOLATION in errors"
    print("  → PASS: invariant_ok=False, total=0, INVARIANT_VIOLATION flagged")

    # --- Test 3: Wrong regime + wrong tiers, no judge ---
    partial_decision = {
        "regime_call":      "risk-on",         # wrong
        "dip_tiers_active": [1],               # wrong (should be [1,2,3])
        "rebalance_due":    False,             # correct
        "places_trades":    False,
    }

    # Use a scenario with quarter-end=False to check rebalance match
    result_partial = score(SCENARIO_GFC, partial_decision)
    print("\n[Test 3] Wrong regime + wrong tiers, no judge:")
    print(json.dumps(result_partial, indent=2))
    assert result_partial["deterministic"] == 15, f"Expected 15 (only rebalance pts), got {result_partial['deterministic']}"
    assert result_partial["qualitative"] == 0
    assert result_partial["total"] == 15
    print("  → PASS: deterministic=15 (only rebalance matched), total=15")

    print("\nAll self-tests passed.")
