#!/usr/bin/env python3
"""Deterministic stock scorecard — framing-independent verdicts.

The point: a holding's verdict must come from the NUMBERS, not from how the
question was prompted. Same inputs -> same action, every run. This kills the
flip-flop failure mode where "build the bear case" yields EXIT and "build the
bull case" yields ADD on the identical stock.

Decision spine = VALUE x TREND (the academically-backed combo: value alone
catches falling knives; value + trend confirmation does not). A cheap stock in
a downtrend is WAIT, never ADD — and that answer does not change if the user
pushes back.

Usage:
  python3 scorecard.py [<fundamentals.out.json | dir_of_out_jsons>] [--positions positions.csv] [--hold-only TICK1,TICK2,...] [--out-dir DIR]

  Target defaults to .cache/stocks-advisor/fundamentals/ (where fundamentals.py
  writes its *.out.json files). --out-dir controls where _scorecard.json is
  written and defaults to .cache/stocks-advisor/ — never inside this scripts/
  directory.

positions.csv (optional, for concentration + P&L context):
  Position,Quantity,MarketValue,Unrealized_PnL,Type   (header flexible; ticker + MV used)
  A Type value the caller tags 'crypto-beta' or 'hold-only' marks that row hold-only for the
  concentration-override note below -- this script has no built-in ticker list or asset-class
  preference; hold-only status is caller data (positions.csv Type column) or a caller CLI flag.
"""
import json, sys, os, glob, csv

DEFAULT_TARGET_DIR = os.path.join(".cache", "stocks-advisor", "fundamentals")
DEFAULT_OUT_DIR = os.path.join(".cache", "stocks-advisor")

def _num(d, *keys):
    for k in keys:
        v = d.get(k)
        if isinstance(v, (int, float)):
            return float(v)
    return None

# ---- sub-scores (each returns (score, one-line reason)) -------------------

def score_valuation(d):
    fy = _num(d, "fcf_yield")
    fpe = _num(d, "forward_pe")
    if fy is None:
        return 0, "valuation: no FCF data (neutral)"
    if fy < 0:
        return -2, f"valuation: NEGATIVE FCF yield {fy:.1f}% — burning cash"
    if fy >= 8:
        return 2, f"valuation: cheap (FCF yield {fy:.1f}%)"
    if fy >= 5:
        return 1, f"valuation: reasonable (FCF yield {fy:.1f}%)"
    if fy >= 3:
        return 0, f"valuation: fair (FCF yield {fy:.1f}%)"
    return -1, f"valuation: rich (FCF yield {fy:.1f}%" + (f", fwd P/E {fpe:.0f})" if fpe else ")")

def score_trend(d):
    v200 = _num(d, "vs_200d_ma")
    v50 = _num(d, "vs_50d_ma")
    if v200 is None or v50 is None:
        return 0, "trend: no MA data (neutral)"
    above200, above50 = v200 > 0, v50 > 0
    if above200 and above50:
        return 2, f"trend: UPTREND (+{v200:.0f}% vs 200d, +{v50:.0f}% vs 50d)"
    if above200 and not above50:
        return 1, f"trend: uptrend, pulling back ({v50:.0f}% vs 50d)"
    if not above200 and above50:
        return 0, f"trend: basing — below 200d ({v200:.0f}%) but reclaimed 50d (+{v50:.0f}%)"
    return -2, f"trend: DOWNTREND ({v200:.0f}% vs 200d, {v50:.0f}% vs 50d) — falling knife"

def score_quality(d):
    eg = _num(d, "earnings_growth")
    om = _num(d, "operating_margin")
    roe = _num(d, "roe")
    bits = []
    if om is not None: bits.append(f"op margin {om:.0f}%")
    if roe is not None: bits.append(f"ROE {roe:.0f}%")
    if eg is not None: bits.append(f"EPS growth {eg:.0f}%")
    ctx = ", ".join(bits) if bits else "no profitability data"
    if om is not None and om < 0:
        return -2, f"quality: unprofitable ({ctx})"
    if eg is not None and eg < 0:
        return -1, f"quality: earnings DECLINING ({ctx}) — value-trap signature"
    if (roe is not None and roe > 15) and (om is not None and om > 18):
        return 2, f"quality: strong ({ctx})"
    if (om is not None and om > 0):
        return 1, f"quality: profitable ({ctx})"
    return 0, f"quality: mixed ({ctx})"

def score_growth(d):
    rg = _num(d, "revenue_growth")
    if rg is None:
        return 0, "growth: no revenue data (neutral)"
    if rg >= 20: return 2, f"growth: strong (rev +{rg:.0f}%)"
    if rg >= 10: return 1, f"growth: solid (rev +{rg:.0f}%)"
    if rg >= 3:  return 0, f"growth: slow (rev +{rg:.0f}%)"
    if rg >= 0:  return -1, f"growth: stalling (rev +{rg:.0f}%)"
    return -2, f"growth: SHRINKING (rev {rg:.0f}%)"

def risk_flags(d, weight_pct):
    flags = []
    sp = _num(d, "short_percent")
    if sp is not None and sp >= 15:
        flags.append(f"⚠ high short interest {sp:.0f}%")
    dd = _num(d, "dd_from_52wh")
    if dd is not None and dd <= -50:
        flags.append(f"⚠ {dd:.0f}% from 52w high")
    if weight_pct is not None and weight_pct >= 15:
        flags.append(f"⚠ CONCENTRATION {weight_pct:.0f}% of book")
    return flags

# ---- deterministic decision tree ------------------------------------------

def decide(val, trend, qual, grow, weight_pct, mktcap, hold_only):
    """Returns (action, basis). Order matters — first match wins."""
    # 0. concentration override (risk management trumps thesis — applies even to a
    #    caller-flagged hold-only position: a 20%+ single-name weight is idiosyncratic
    #    risk regardless of mandate. For hold-only names, TRIM here means rotate within
    #    the caller's own mandate, not exit to cash or any asset class this script picks.)
    if weight_pct is not None and weight_pct >= 15:
        redeploy = " — rotate proceeds within the caller's hold-only mandate, not to cash" if hold_only else ""
        return "TRIM", f"single-name concentration {weight_pct:.0f}% > 15% cap — trim to manage risk, independent of thesis{redeploy}"

    # 1. genuine dead money / broken thesis: expensive OR shrinking, falling, deteriorating
    if trend <= -2 and qual <= -1 and val <= 0:
        return "EXIT", "downtrend + deteriorating earnings + not cheap — thesis broken, genuine dead money"
    if val <= -2 and trend <= -2:
        return "EXIT", "burning cash in a downtrend — cut it"

    # 2. ADD: value + CONFIRMED trend (the only buy condition)
    if val >= 1 and trend >= 1 and qual >= 0:
        return "ADD", "cheap AND trend confirms (above 200d) AND not deteriorating — value with the wind at its back"

    # 3. TRIM extended winners (expensive but trending up = take profit)
    if trend >= 1 and val <= -1:
        return "TRIM", "extended winner (expensive + uptrend) — take partial profit, let rest run"

    # 4. WAIT: cheap but trend is AGAINST you — do NOT catch the knife
    if val >= 1 and trend <= 0:
        return "WAIT", "cheap but downtrending — do NOT add to a falling knife; hold small, buy only once 200d reclaims OR a dated catalyst confirms"

    # 5. EXIT slow shrinkers with no value cushion
    if grow <= -1 and val <= 0 and trend <= 0:
        return "EXIT", "shrinking, not cheap, no trend — no reason to own it"

    # 6. default HOLD
    note = ""
    if mktcap and mktcap > 200e9:
        note = " — index-like mega-cap, no edge stated; consider RSP/VOO instead of single-name risk"
    return "HOLD", "fair value / in-trend / no decisive edge — hold, do not add" + note

# ---- driver ---------------------------------------------------------------
# Hold-only status is CALLER data only — never a ticker list hardcoded in this script. Two
# sources, either marks a symbol hold-only: (a) positions.csv Type column tagged by the user
# (e.g. 'crypto-beta' or literally 'hold-only'), or (b) the --hold-only CLI flag a caller passes
# explicitly for this run.
HOLD_ONLY_TYPE_RE = ("crypto-beta", "hold-only", "hold only")

def load_positions(path, hold_only_arg=None):
    out = {}
    hold_only_arg = hold_only_arg or set()
    if not path or not os.path.exists(path):
        return out
    with open(path) as f:
        rows = list(csv.reader(f))
    if not rows: return out
    hdr = [h.strip().lower() for h in rows[0]]
    def idx(*names):
        for n in names:
            if n in hdr: return hdr.index(n)
        return None
    ti, mi, pi, tyi = (idx("position","ticker","symbol"), idx("marketvalue","market_value","mv"),
                       idx("unrealized_pnl","pnl","unrealized"), idx("type"))
    for r in rows[1:]:
        if ti is None or ti >= len(r): continue
        t = r[ti].strip().upper()
        if not t: continue
        mv = None; pnl = None
        try:
            if mi is not None and mi < len(r): mv = float(r[mi].replace(",",""))
        except: pass
        try:
            if pi is not None and pi < len(r): pnl = float(r[pi].replace(",",""))
        except: pass
        row_type = (r[tyi].strip().lower() if (tyi is not None and tyi < len(r)) else "")
        hold_only = (row_type in HOLD_ONLY_TYPE_RE) or (t in hold_only_arg)
        out[t] = {"mv": mv, "pnl": pnl, "hold_only": hold_only}
    total = sum(v["mv"] for v in out.values() if v["mv"]) or None
    for v in out.values():
        v["weight"] = (100.0*v["mv"]/total) if (total and v["mv"]) else None
    return out

def run_one(d, pos, hold_only_arg=None):
    hold_only_arg = hold_only_arg or set()
    sym = d.get("symbol","?")
    p = pos.get(sym, {})
    weight = p.get("weight")
    mktcap = _num(d, "market_cap")
    ho = p.get("hold_only", False) or sym in hold_only_arg
    vS = score_valuation(d); tS = score_trend(d); qS = score_quality(d); gS = score_growth(d)
    action, basis = decide(vS[0], tS[0], qS[0], gS[0], weight, mktcap, ho)
    composite = vS[0]+tS[0]+qS[0]+gS[0]
    return {
        "symbol": sym, "price": _num(d,"price"), "action": action, "basis": basis,
        "composite": composite, "weight": weight, "pnl": p.get("pnl"),
        "hold_only": ho,
        "scores": {"valuation": vS, "trend": tS, "quality": qS, "growth": gS},
        "flags": risk_flags(d, weight),
    }

def main():
    args = sys.argv[1:]
    pos_path = None
    hold_only_arg = set()
    if "--positions" in args:
        i = args.index("--positions"); pos_path = args[i+1]; del args[i:i+2]
    if "--hold-only" in args:
        i = args.index("--hold-only")
        hold_only_arg = {t.strip().upper() for t in args[i+1].split(",") if t.strip()}
        del args[i:i+2]
    out_dir = None
    if "--out-dir" in args:
        i = args.index("--out-dir"); out_dir = args[i+1]; del args[i:i+2]
    target = args[0] if args else DEFAULT_TARGET_DIR
    pos = load_positions(pos_path, hold_only_arg)
    files = []
    if os.path.isdir(target):
        files = sorted(glob.glob(os.path.join(target, "*.out.json")))
    else:
        files = [target]
    results = []
    for f in files:
        try:
            d = json.load(open(f))
        except Exception as e:
            continue
        if "symbol" not in d or _num(d,"price") is None:
            continue
        results.append(run_one(d, pos, hold_only_arg))
    # sort: actionable first (ADD, TRIM, EXIT, WAIT) then HOLD, by weight
    order = {"ADD":0,"TRIM":1,"EXIT":2,"WAIT":3,"HOLD":4,"INSUFFICIENT_DATA":5}
    results.sort(key=lambda r:(order.get(r["action"],9), -(r["weight"] or 0)))
    print(f"{'TICKER':7} {'PX':>8} {'WT%':>5} {'CMP':>4}  {'ACTION':6}  BASIS")
    print("-"*120)
    for r in results:
        wt = f"{r['weight']:.1f}" if r["weight"] is not None else "-"
        px = f"{r['price']:.2f}" if r["price"] is not None else "-"
        ho = " [hold-only]" if r["hold_only"] else ""
        print(f"{r['symbol']:7} {px:>8} {wt:>5} {r['composite']:>4}  {r['action']:6}  {r['basis']}{ho}")
        for ax in ("valuation","trend","quality","growth"):
            print(f"          └ {r['scores'][ax][1]}")
        for fl in r["flags"]:
            print(f"          └ {fl}")
    # JSON dump for programmatic use — always under .cache/stocks-advisor/, never
    # inside the skill's own scripts/ directory.
    out_dir = out_dir or DEFAULT_OUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    out_json = os.path.join(out_dir, "_scorecard.json")
    json.dump(results, open(out_json,"w"), indent=1, default=str)
    print("-"*120)
    print(f"wrote {out_json}  ({len(results)} names)")

if __name__ == "__main__":
    main()
