#!/usr/bin/env python3
"""analyst-smartmoney-13f — dedup ledger + manager roster for the 13F buy-watcher.

The script owns the DETERMINISTIC parts: who we track, and what we've ALREADY recommended
(so the same ticker is never recommended twice per quarter). The judgment parts — pulling
filings, reading puts-vs-longs, interpreting WHY — are the agent's job via the analyst-smartmoney-13f
SKILL.md (which leans on hedge-fund-13f-analysis).

Dedup scope: ticker + quarter. Same name can surface again in a new quarter if managers
show fresh action — each quarterly filing cycle is independent.

Storage: JSONL at $THIRTEENF_LEDGER or .cache/analyst-smartmoney-13f/recommended.jsonl
Roster:  JSON  at .cache/analyst-smartmoney-13f/roster.json (falls back to the verified default below)

Roster has two buckets:
  - "conviction"        — fundamental stock-picking managers. Drive the 0-100 composite score
                           and T1/T2/T3/SKIP tiering (see SKILL.md SCORE/TIER sections).
  - "institutional-flow" — multi-manager pod shops / macro / systematic funds whose single 13F
                           line is a statistical or non-representative slice of the real book
                           (see per-manager "note" in the roster for the specific reason).
                           These NEVER independently create or promote a candidate — they can only
                           attach as corroboration metadata onto an EXISTING conviction-bucket
                           candidate, via `corroborate` (not `record`), hard-capped at
                           FLOW_CORROBORATION_CAP distinct managers per ticker+quarter.

Usage:
  watch.py roster
  watch.py seen <TICKER> --quarter 2026Q1   # exit 0 = already recommended this quarter (SKIP); exit 1 = NEW
  watch.py record --ticker LULU --manager klarman --quarter 2026Q1 --action new \
                  [--reason "..."] [--price 230] [--source "EDGAR CIK 0001061768"]
                  # refuses if --manager resolves to an institutional-flow bucket manager
  watch.py corroborate --ticker LULU --quarter 2026Q1 --manager citadel [--source "..."]
                  # attaches flow corroboration to an EXISTING record; refuses if no prior
                  # record exists, or if --manager is not an institutional-flow manager
  watch.py list [--since YYYY-MM-DD]
"""
import argparse, json, os, sys
from datetime import date

_SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SKILL_DIR, "..", "..", ".."))
LEDGER = os.environ.get("THIRTEENF_LEDGER", os.path.join(_REPO_ROOT, ".cache", "analyst-smartmoney-13f", "recommended.jsonl"))
ROSTER = os.path.join(os.path.dirname(LEDGER), "roster.json")

# Verified CIKs only (SEC EDGAR). Honesty rule: never fabricate a CIK — unknowns are resolved
# at runtime by the agent via EDGAR company search, then added to 13f/roster.json.
#
# Burry/Scion (CIK 0001649339) is no longer tracked — no current 13F coverage (last filing
# 2025Q3, none since).
#
# bucket="conviction"        -> drives composite scoring + T1/T2/T3/SKIP tiering.
# bucket="institutional-flow" -> corroboration only; can NEVER independently create or promote
#                                 a candidate (see corroborate()/record() below).
#
# universe="top5-aum" -> CORRECTION (2026-07-14): a prior draft tagged Bridgewater/Citadel/
#                        Millennium/Renaissance/Point72 as "top-5 hedge funds" without verifying
#                        against an actual AUM ranking — that set was WRONG (Point72 and
#                        Renaissance are not top-5 by AUM; Point72 ~$41.5B is well below the
#                        other four, and Renaissance's only sourced AUM figure is stale/2021).
#                        Verified directly against SEC EDGAR (data.sec.gov/submissions, CIK +
#                        active 13F-HR filer confirmed 2026-07-14) plus cited AUM disclosures
#                        (Reuters/firm sites/P&I, as-of dates vary — figures use different AUM
#                        definitions: net investor capital vs total FUM vs regulatory AUM, so
#                        this is a best-effort ranking, not one standardized SEC metric):
#                          Man Group plc        ~$227.6B total FUM   (FY2025, man.com)
#                          Bridgewater           ~$92B  net capital  (2025, Reuters)
#                          Millennium            ~$92B  net capital  (Jul-2026, mlp.com)
#                          Elliott Investment Mgmt ~$80B net capital (2026, weakly sourced)
#                          Citadel Advisors      ~$67B+ net capital  (Jan-2026, CNBC/LCH)
#                        vs. Point72 ~$41.5B (clearly excluded) and Renaissance ~$130B-but-2021
#                        (stale, flagged as an unresolved discrepancy — not included in the
#                        top5-aum tag pending a current figure). The 5 managers tagged
#                        "top5-aum" below are consumed by `scripts/top5-13f-report.ts` (the
#                        cross-fund 13F holdings/report aggregator) as its default universe.
#                        Renaissance and Point72 remain valid institutional-flow managers for
#                        `corroborate` (dozens-of-books / systematic dilution still applies to
#                        their single 13F line) — they are simply no longer mislabeled top-5-AUM.
DEFAULT_ROSTER = {
    "buffett": {"fund": "Berkshire Hathaway Inc", "cik": "0001067983", "bucket": "conviction"},
    "ackman": {"fund": "Pershing Square Capital Management, L.P.", "cik": "0001336528", "bucket": "conviction"},
    "klarman": {"fund": "Baupost Group LLC/MA", "cik": "0001061768", "bucket": "conviction"},
    "li-lu": {"fund": "Himalaya Capital Management LLC", "cik": "0001709323", "bucket": "conviction"},
    "bridgewater": {
        "fund": "Bridgewater Associates, LP", "cik": "0001350694", "bucket": "institutional-flow",
        "universe": "top5-aum",
        "note": "Bridgewater's 13F only covers its long US-equity book; it misses the firm's "
                 "dominant macro/rates/FX/commodities derivatives book entirely, so the 13F is a "
                 "small, non-representative slice of the actual fund — not a read on Dalio's real "
                 "macro view. Tracked here as one of the verified top-5 hedge funds by AUM "
                 "(~$92B, 2025, Reuters) — see universe=top5-aum note above.",
    },
    "citadel": {
        "fund": "Citadel Advisors LLC", "cik": "0001423053", "bucket": "institutional-flow",
        "universe": "top5-aum",
        "note": "Citadel Advisors LLC is a multi-manager \"pod shop\" running dozens of independent "
                 "internal books plus heavy options/hedges; a single 13F line aggregates many "
                 "uncorrelated, frequently-offsetting bets, so ownership is statistical/aggregated "
                 "noise, not one fund manager's thesis. Citadel Advisors LLC (the hedge fund, files "
                 "13F) is legally distinct from Citadel Securities (the market maker/broker-dealer) "
                 "— never call Citadel Advisors a market maker. Tracked here as one of the verified "
                 "top-5 hedge funds by AUM (~$67B+, Jan-2026, CNBC/LCH).",
    },
    "millennium": {
        "fund": "Millennium Management LLC", "cik": "0001273087", "bucket": "institutional-flow",
        "universe": "top5-aum",
        "note": "Same multi-manager pod-shop structure as Citadel — dozens of independent books, "
                 "options-heavy, aggregated 13F obscures any single thesis. Tracked here as one of "
                 "the verified top-5 hedge funds by AUM (~$92B net investor capital, Jul-2026, "
                 "mlp.com).",
    },
    "elliott": {
        "fund": "Elliott Investment Management L.P.", "cik": "0001791786", "bucket": "institutional-flow",
        "universe": "top5-aum",
        "note": "Activist/event-driven multi-strategy fund — concentrated, high-conviction-looking "
                 "positions (33 holdings, ~$20B reported 2026Q1), but tracked here as flow (not "
                 "conviction) purely on the top-5-AUM selection criterion (~$80B, 2026), not a "
                 "judgment that its 13F is statistical noise. Current EDGAR filer is Elliott "
                 "Investment Management L.P. (CIK 0001791786, active); the predecessor entity "
                 "Elliott Management Corp (CIK 0001048445) last filed for 2020Q3 and is not used.",
    },
    "man-group": {
        "fund": "Man Group plc", "cik": "0001637460", "bucket": "institutional-flow",
        "universe": "top5-aum",
        "note": "Man Group plc (London-listed) files a single group-level 13F under CIK 0001637460 "
                 "covering its aggregate US 13(f) securities book across investment divisions (Man "
                 "AHL, Man GLG, Man Numeric, etc.) — confirmed as an active 13F-HR filer on EDGAR "
                 "(latest period 2026-03-31, filed 2026-05-15). Its ~$227.6B headline AUM (FY2025, "
                 "man.com) is TOTAL funds under management, including long-only and private-markets "
                 "assets beyond hedge-fund/liquid-alts strategies — not a pure hedge-fund AUM figure "
                 "and not directly comparable to the other four managers' net-investor-capital "
                 "figures. Tracked here as one of the verified top-5 by AUM per the criterion above; "
                 "no substitute fund was used.",
    },
    "renaissance": {
        "fund": "Renaissance Technologies LLC", "cik": "0001037389", "bucket": "institutional-flow",
        "note": "Systematic/quantitative shop — positions are statistically-driven signal outputs, "
                 "not fundamental conviction; treat as pure flow. NOT tagged universe=top5-aum: its "
                 "only sourced AUM figure (~$130B) is stale (P&I, 2021) — an unresolved discrepancy, "
                 "not a confirmed current top-5 ranking (see universe=top5-aum note above).",
    },
    "point72": {
        "fund": "Point72 Asset Management, L.P.", "cik": "0001603466", "bucket": "institutional-flow",
        "note": "Same multi-manager pod-shop structure as Citadel/Millennium — options-heavy, "
                 "aggregated book, no single thesis. NOT tagged universe=top5-aum: sourced AUM "
                 "(~$41.5B, late 2025, Wikipedia/firm) is well below the other four top-5 managers "
                 "— a prior draft incorrectly included Point72 in a 'top-5' set; corrected 2026-07-14.",
    },
}

# Hard cap on distinct institutional-flow managers that count as corroboration per ticker+quarter.
# Anything beyond this is still recorded (audit trail) but flagged as non-counting.
FLOW_CORROBORATION_CAP = 2


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
    """Load the roster, stripping any leading-underscore metadata keys (e.g. "_meta" —
    provenance/selection-criterion notes, not a trackable manager) so they never leak into
    roster(), record(), corroborate(), or _roster_normalized() as a fake manager entry."""
    if os.path.exists(ROSTER):
        with open(ROSTER) as f:
            raw = json.load(f)
    else:
        raw = DEFAULT_ROSTER
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def _normalize_manager(name):
    """Canonical manager key: trimmed + lowercased. Applied consistently to both the
    --manager argument and roster keys before lookup, so 'Citadel', 'CITADEL', and
    ' citadel ' all resolve to the same institutional-flow entry as 'citadel' — an
    unknown/misspelled manager must never silently fall through as conviction-bucket."""
    return (name or "").strip().lower()


def _roster_normalized():
    return {_normalize_manager(k): v for k, v in _roster().items()}


def roster(a):
    rmap = _roster()
    conviction = {k: v for k, v in rmap.items() if v.get("bucket", "conviction") == "conviction"}
    flow = {k: v for k, v in rmap.items() if v.get("bucket", "conviction") == "institutional-flow"}

    print("CONVICTION (drives scoring/tiering)")
    for k, v in conviction.items():
        note = f'  ({v["note"]})' if v.get("note") else ""
        print(f'  {k:12} CIK {v.get("cik","?")}  {v.get("fund","")}{note}')

    print()
    print("INSTITUTIONAL-FLOW (corroboration only, capped, never independently qualifies a candidate or promotes a tier)")
    for k, v in flow.items():
        tag = "  [top5-aum]" if v.get("universe") == "top5-aum" else ""
        note = f'  ({v["note"]})' if v.get("note") else ""
        print(f'  {k:12} CIK {v.get("cik","?")}  {v.get("fund","")}{tag}{note}')


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
    rmap = _roster_normalized()
    manager = _normalize_manager(a.manager)
    entry = rmap.get(manager)
    if entry is None:
        valid = ", ".join(sorted(rmap.keys())) or "(roster is empty)"
        print(
            f"error: manager '{a.manager}' not found in roster — refusing to create an ad-hoc "
            f"conviction record (an unknown manager must never silently become a conviction "
            f"manager). Add it to roster.json first if this is a genuine new conviction manager. "
            f"Valid roster keys: {valid}",
            file=sys.stderr,
        )
        sys.exit(2)
    bucket = entry.get("bucket", "conviction")
    if bucket == "institutional-flow":
        print(
            f"error: '{manager}' is an institutional-flow bucket manager "
            f"({entry.get('fund','?')}) — it can never independently create a candidate. "
            f"Use '$W corroborate --ticker {a.ticker} --quarter {a.quarter} --manager {manager}' "
            f"instead, after an existing conviction-bucket record for this ticker+quarter.",
            file=sys.stderr,
        )
        sys.exit(2)

    rows = _load()
    t = a.ticker.upper()
    q = a.quarter
    if any(r["ticker"].upper() == t and r["quarter"] == q for r in rows):
        print(f"skip: {t} {q} already recommended — dedup rule, not recording again", file=sys.stderr)
        sys.exit(3)
    rows.append({
        "ticker": t, "manager": manager, "quarter": q, "action": a.action,
        "reason": a.reason or "", "price_at_rec": a.price, "source": a.source or "",
        "recommended_on": date.today().isoformat(), "bucket": "conviction",
    })
    _save(rows)
    print(f"recorded {t}  via {manager}  {q}  ({a.action})")


def corroborate(a):
    rmap = _roster_normalized()
    manager = _normalize_manager(a.manager)
    entry = rmap.get(manager)
    if entry is None:
        valid = ", ".join(sorted(rmap.keys())) or "(roster is empty)"
        print(
            f"error: manager '{a.manager}' not found in roster — add it to roster.json first. "
            f"Valid roster keys: {valid}",
            file=sys.stderr,
        )
        sys.exit(2)
    bucket = entry.get("bucket", "conviction")
    if bucket != "institutional-flow":
        print(
            f"error: '{manager}' is a conviction-bucket manager ({entry.get('fund','?')}) — "
            f"use '$W record' instead of 'corroborate' for conviction-bucket managers.",
            file=sys.stderr,
        )
        sys.exit(2)

    rows = _load()
    t = a.ticker.upper()
    q = a.quarter
    idx = next((i for i, r in enumerate(rows) if r["ticker"].upper() == t and r["quarter"] == q), None)
    if idx is None:
        print(
            f"error: no existing conviction-bucket candidate found for {t} {q} — institutional-flow "
            f"corroboration requires an existing '$W record' call; it cannot create a candidate on its own.",
            file=sys.stderr,
        )
        sys.exit(2)

    row = rows[idx]
    flow = row.setdefault("flow_corroboration", [])
    extra = row.setdefault("flow_corroboration_extra", [])
    if manager in flow or manager in extra:
        print(f"note: {manager} already corroborated {t} {q} — no change")
        return
    if len(flow) < FLOW_CORROBORATION_CAP:
        flow.append(manager)
        _save(rows)
        print(f"corroborated {t} {q} with {manager} ({len(flow)}/{FLOW_CORROBORATION_CAP} counted)")
    else:
        extra.append(manager)
        _save(rows)
        print(
            f"corroborated {t} {q} with {manager} — cap ({FLOW_CORROBORATION_CAP}) already reached; "
            f"recorded for audit trail only, does not add incremental signal"
        )


def list_(a):
    rows = _load()
    if a.since:
        rows = [r for r in rows if r["recommended_on"] >= a.since]
    if not rows:
        print("(none)")
        return
    for r in sorted(rows, key=lambda r: r["recommended_on"]):
        px = f' @{r["price_at_rec"]}' if r.get("price_at_rec") else ""
        bucket = r.get("bucket", "conviction")
        flow = r.get("flow_corroboration", [])
        extra = r.get("flow_corroboration_extra", [])
        flow_suffix = ""
        if flow:
            flow_suffix = f'  +{len(flow)} flow: {", ".join(flow)}'
            if extra:
                flow_suffix += f' (+{len(extra)} more not counted, cap={FLOW_CORROBORATION_CAP})'
        print(f'{r["recommended_on"]}  {r["ticker"]:6}{px}  {r["manager"]} [{bucket}] {r["quarter"]} [{r["action"]}]  {r.get("reason","")}{flow_suffix}')


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
    s = sub.add_parser("corroborate", help="attach institutional-flow corroboration to an existing conviction-bucket record")
    s.add_argument("--ticker", required=True); s.add_argument("--manager", required=True)
    s.add_argument("--quarter", required=True); s.add_argument("--source")
    s.set_defaults(fn=corroborate)
    s = sub.add_parser("list"); s.add_argument("--since"); s.set_defaults(fn=list_)
    a = p.parse_args(); a.fn(a)


if __name__ == "__main__":
    main()
