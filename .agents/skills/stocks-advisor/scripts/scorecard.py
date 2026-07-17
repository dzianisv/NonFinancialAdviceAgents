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

def check_exhaustion(d):
    """Guard against the 'trend broken -> sell today' rules firing on a name that has
    ALREADY crashed: deep drawdown + oversold RSI means the trend-exit was months ago,
    not today, and a fresh sell/trim call now is selling INTO the hole, not managing
    risk out of it.

    Thresholds: RSI(14) < 40 (oversold-ish, not yet a V-bottom reversal, but no longer
    momentum-driven selling either) AND drawdown from the 52-week high beyond -25%
    (a shallow pullback is not exhaustion; a name cut by a quarter or more, with RSI
    already washed out, is). Both numbers come straight from fundamentals.py -- no
    TradingView dependency, so this also protects the fundamentals-only screen (Step
    0.8) and DEGRADED_TECH mode, not just the deep-dive panel.

    Returns a dict when exhausted (reason + concrete stop/bounce levels the scorecard
    basis string can print), or None when the name is not in an exhausted state (the
    normal trend/value/quality/growth rules then decide as before).
    """
    rsi = _num(d, "rsi14")
    dd = _num(d, "dd_from_52wh")
    if rsi is None or dd is None or not (rsi < 40 and dd <= -25):
        return None

    price = _num(d, "price")
    ma50 = _num(d, "ma50")
    ma200 = _num(d, "ma200")
    stop = _num(d, "swing_low_20d")
    if stop is None:
        stop = _num(d, "52w_low")

    # Bounce target = the nearest MA still above price (the MA it's below) -- the
    # closer one is the more actionable near-term reclaim level, not the ultimate target.
    candidates = [(name, lvl) for name, lvl in (("50d MA", ma50), ("200d MA", ma200))
                  if lvl is not None and price is not None and lvl > price]
    bounce_name, bounce_level = (min(candidates, key=lambda x: x[1]) if candidates else (None, None))

    return {
        "rsi": rsi, "dd": dd, "stop": stop,
        "bounce_name": bounce_name, "bounce_level": bounce_level,
        "reason": f"RSI {rsi:.0f} (oversold) after {dd:.0f}% drawdown from 52w high — exhaustion, not fresh momentum",
    }

def event_soon_flag(d, action):
    """Non-gating earnings-timing annotation -- fires when a print is <=10 trading
    days out (fundamentals.py's days_to_earnings, best-effort/yfinance-calendar-sourced).
    NEVER feeds into decide(): the scorecard ACTION stays pure VALUE x TREND regardless
    of this flag. Attaches a 'stage ACTION after print' note only when the ACTION is
    already TRIM/ADD/EXIT -- it annotates the decided action, it does not decide it."""
    days = _num(d, "days_to_earnings")
    if days is None or days < 0 or days > 10:
        return None
    edate = d.get("next_earnings_date") or "date unknown"
    flag = f"EVENT_SOON ({int(days)}d to earnings, {edate})"
    if action in ("TRIM", "ADD", "EXIT"):
        flag += f" — stage {action} after print"
    return flag

# ---- deterministic decision tree ------------------------------------------

def decide(val, trend, qual, grow, weight_pct, mktcap, hold_only, exh=None,
           dd=None, vs200=None, vs50=None, gain_pct=None):
    """Returns (action, basis). Order matters — first match wins.

    dd / vs200 / vs50 / gain_pct are the raw position-context numbers the EARLY
    TREND-BREAK EXIT (rule 0.7) needs: drawdown from the 52w high, distance vs the
    200d/50d MA, and the unrealized gain% off cost basis. They default to None so
    the tree degrades gracefully (rule 0.7 simply doesn't fire) when a caller has
    no position/price context — every other rule is unchanged."""
    # 0. concentration override (risk management trumps thesis — applies even to a
    #    caller-flagged hold-only position: a 20%+ single-name weight is idiosyncratic
    #    risk regardless of mandate. For hold-only names, TRIM here means rotate within
    #    the caller's own mandate, not exit to cash or any asset class this script picks.)
    if weight_pct is not None and weight_pct >= 15:
        redeploy = " — rotate proceeds within the caller's hold-only mandate, not to cash" if hold_only else ""
        return "TRIM", f"single-name concentration {weight_pct:.0f}% > 15% cap — trim to manage risk, independent of thesis{redeploy}"

    # 0.5 EXHAUSTION GUARD — a broken trend (trend<=-2, i.e. below BOTH the 50d and 200d
    # MA) does not by itself mean "sell today". Rules 1/2/5 below all fire on trend<=-2
    # and would call EXIT on a name that is simply trend-following-correct but already
    # priced in. If the name is ALSO oversold + deep-drawdown (check_exhaustion), the
    # trend-exit was months ago, not now: selling at RSI<40 after a >25% crash is selling
    # LOW, not managing risk. Override to HOLD-with-a-stop / bounce-target instead of a
    # fresh EXIT/TRIM call. This does NOT touch rule 3 (TRIM extended winners), which
    # requires trend>=1 (uptrend) — structurally incompatible with an exhausted/crashed
    # state, so genuinely extended names still trim exactly as before.
    if trend <= -2 and exh is not None:
        stop_txt = f"${exh['stop']:.2f} (recent swing low)" if exh.get("stop") is not None else "the recent swing low"
        if exh.get("bounce_level") is not None:
            bounce_txt = f"${exh['bounce_level']:.2f} ({exh['bounce_name']})"
        else:
            bounce_txt = "the MA it's below"
        return "HOLD", (
            f"EXIT MISSED, not EXIT NOW — {exh['reason']}. The trend-exit was months ago; "
            f"selling into an oversold crash is selling low. HOLD with a stop below "
            f"{stop_txt}, or trim into a bounce toward {bounce_txt}. Don't sell into the hole."
        )

    # 0.7 EARLY TREND-BREAK EXIT — the NEM/MRVL missed-exit fix, the whole point of this
    # rule set. It fires the exit while it is STILL ACTIONABLE, before a rolling-over winner
    # decays into the crashed/oversold state that the exhaustion guard (0.5) then locks into
    # HOLD. On the drawdown timeline it sits strictly BETWEEN the healthy state and 0.5:
    #   healthy (at highs, uptrend)                     -> rules 2/3 (HOLD / TRIM-if-heavy)
    #   >>> trend just broke, drawdown STILL MODERATE   -> THIS rule (TRIM / EXIT)  <<<
    #   already crashed (RSI<40 AND dd<=-25)            -> rule 0.5 exhaustion guard (HOLD)
    # NON-OVERLAP with 0.5 is guaranteed on the DRAWDOWN axis alone: this rule requires
    # dd > -25 (still shallow), 0.5 requires dd <= -25 — they cannot both be eligible for the
    # same name regardless of RSI, so adding this rule cannot break the "don't sell the bottom"
    # guard. And 0.5 is checked first, so even at the boundary the guard wins.
    #
    # Trigger = trend flipped down (price BELOW the 200d MA — the disciplined trend break NEM
    # and MRVL both crossed) AND drawdown is still MODERATE (-25% < dd <= -8%: past noise at the
    # very top, but not yet exhaustion) AND the position is DECISION-RELEVANT: weight-heavy
    # and/or a large locked-in winner. The size×gain gate is what earns the whipsaw cost — it
    # fires LOUDEST on big extended winners breaking down (the NEM signature: 8% of book, +100%)
    # and stays SILENT on small/no-gain positions, where a 200d wobble is just noise.
    #   TRIM = first/normal break of a still-intact-thesis winner — partial, protect the gain.
    #   EXIT = confirmed breakdown (below BOTH 50d & 200d) AND deteriorating fundamentals
    #          (declining EPS or shrinking revenue) — trend break + broken thesis, cut it.
    # Honest limitation: trend-break exits WHIPSAW (a name can break the 200d and reclaim it).
    # We accept that cost ONLY because the size×gain weighting confines the rule to positions
    # where riding a +100% winner back to breakeven is the far more expensive error. This does
    # NOT "never miss an exit"; it catches the actionable window NEM/MRVL blew through.
    if vs200 is not None and dd is not None and vs200 < 0 and -25 < dd <= -8:
        heavy = weight_pct is not None and weight_pct >= 5
        big_winner = gain_pct is not None and gain_pct >= 50
        sizeable_winner = (weight_pct is not None and weight_pct >= 3
                           and gain_pct is not None and gain_pct >= 25)
        if heavy or big_winner or sizeable_winner:
            below_both = vs50 is not None and vs50 < 0
            thesis_broken = qual <= -1 or grow <= -1
            g = f"+{gain_pct:.0f}% gain" if gain_pct is not None else "unrealized winner"
            w = f", {weight_pct:.0f}% of book" if weight_pct is not None else ""
            if below_both and thesis_broken:
                return "EXIT", (
                    f"EARLY TREND-BREAK EXIT — broke below BOTH 50d & 200d with deteriorating "
                    f"fundamentals while still only {dd:.0f}% off the 52w high ({g}{w}): confirmed "
                    f"breakdown of a broken-thesis name — exit now, before it becomes the crashed "
                    f"oversold name that can only be held. Trend-break exits can whipsaw; the size×gain "
                    f"weight is why this one is worth acting on."
                )
            return "TRIM", (
                f"EARLY TREND-BREAK EXIT (NEM/MRVL lesson) — {g}{w} just broke its 200d trend while "
                f"still only {dd:.0f}% off its 52w high: MODERATE drawdown, NOT yet exhausted — this is "
                f"the actionable exit window. TRIM now to protect the gain; do NOT wait for the -30/-42% "
                f"oversold print, by then rule 0.5 correctly forbids selling the bottom. First break of a "
                f"still-intact thesis = partial trim (whipsaw risk), not a full exit."
            )

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

def _gain_pct(mv, pnl):
    """Unrealized gain as % of COST BASIS (cost = mv - pnl), matching risk-desk's
    computeGainPct. Feeds the early trend-break exit's size×gain relevance gate. None
    when the position P&L context is missing or the cost basis is non-positive."""
    if mv is None or pnl is None:
        return None
    cost = mv - pnl
    if cost <= 0:
        return None
    return round(pnl / cost * 100.0, 1)

def run_one(d, pos, hold_only_arg=None):
    hold_only_arg = hold_only_arg or set()
    sym = d.get("symbol","?")
    p = pos.get(sym, {})
    weight = p.get("weight")
    mktcap = _num(d, "market_cap")
    ho = p.get("hold_only", False) or sym in hold_only_arg
    vS = score_valuation(d); tS = score_trend(d); qS = score_quality(d); gS = score_growth(d)
    exh = check_exhaustion(d)
    dd = _num(d, "dd_from_52wh"); vs200 = _num(d, "vs_200d_ma"); vs50 = _num(d, "vs_50d_ma")
    gain_pct = _gain_pct(p.get("mv"), p.get("pnl"))
    action, basis = decide(vS[0], tS[0], qS[0], gS[0], weight, mktcap, ho, exh,
                           dd=dd, vs200=vs200, vs50=vs50, gain_pct=gain_pct)
    composite = vS[0]+tS[0]+qS[0]+gS[0]
    # EVENT_SOON is a non-gating annotation ONLY -- it is computed from the ACTION
    # decide() already returned and appended to flags; it never feeds back into decide().
    flags = risk_flags(d, weight)
    es = event_soon_flag(d, action)
    if es:
        flags.append(es)
    if exh is not None:
        flags.append(f"⚠ EXHAUSTED: RSI {exh['rsi']:.0f}, {exh['dd']:.0f}% from 52w high")
    return {
        "symbol": sym, "price": _num(d,"price"), "action": action, "basis": basis,
        "composite": composite, "weight": weight, "pnl": p.get("pnl"),
        "hold_only": ho,
        "scores": {"valuation": vS, "trend": tS, "quality": qS, "growth": gS},
        "flags": flags,
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
