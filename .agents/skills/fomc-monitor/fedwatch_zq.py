#!/usr/bin/env python3.12
"""
FOMC rate-path probability from CME 30-Day Fed Funds futures (ZQ) — the CME
FedWatch methodology, computed from DIRECTLY-FETCHABLE quotes.

Why this exists: the cmegroup.com FedWatch page is JS-rendered and frequently
unreachable from a sandbox, so the published % is only obtainable via a WebSearch
*summary* (second-hand, has been wrong/inverted). ZQ futures quotes ARE fetchable
(Yahoo chart API), and FedWatch IS just arithmetic on those quotes. So we compute
the implied hold/cut/hike probability ourselves — durable, first-hand, no JS page.

Method (standard FedWatch):
  * A ZQ contract cash-settles to the AVERAGE daily EFFR over its delivery month.
  * implied month-average rate = 100 - futures_price.
  * A meeting mid-month splits the month into d_before days at the OLD rate and
    d_after days at the NEW (post-decision) rate:
        avg = (d_before*r_start + d_after*r_end) / days_in_month
    Solve for r_end. The implied move = r_end - r_start.
  * Probability of a 25bp move = |move| / 0.25 (capped at 1.0); the complement is
    P(hold). Sign gives cut vs hike.
  * For the SECOND meeting, r_start chains from the first meeting's r_end.

Sources (all fetched live, no API key):
  * Current EFFR + target range : NY Fed markets API (markets.newyorkfed.org)
  * ZQ futures prices           : Yahoo chart API (query1.finance.yahoo.com)

Run:  python3.12 fedwatch_zq.py
Prints both nearest meetings' implied path + sources + as-of dates.
Never fabricates: if a source is unreachable it prints [UNAVAILABLE] for that leg.
"""
import json, urllib.request, urllib.parse, sys

UA = {"User-Agent": "Mozilla/5.0"}

# CME month codes: F=Jan G=Feb H=Mar J=Apr K=May M=Jun N=Jul Q=Aug U=Sep V=Oct X=Nov Z=Dec
MONTH_CODE = {1:"F",2:"G",3:"H",4:"J",5:"K",6:"M",7:"N",8:"Q",9:"U",10:"V",11:"X",12:"Z"}
DAYS_IN_MONTH = {1:31,2:28,3:31,4:30,5:31,6:30,7:31,8:31,9:30,10:31,11:30,12:31}


def _get(url, timeout=20):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read().decode()


def current_policy_rate():
    """Return (effr, target_low, target_high, as_of) from the NY Fed. Raises on failure."""
    d = json.loads(_get("https://markets.newyorkfed.org/api/rates/unsecured/effr/last/1.json"))
    r = d["refRates"][0]
    return r["percentRate"], r["targetRateFrom"], r["targetRateTo"], r["effectiveDate"]


def zq_price(year, month):
    """Front-of-month ZQ futures price from Yahoo, e.g. ZQM26.CBT. Returns (price, sym) or (None, sym)."""
    sym = f"ZQ{MONTH_CODE[month]}{year % 100:02d}.CBT"
    try:
        d = json.loads(_get("https://query1.finance.yahoo.com/v8/finance/chart/" + urllib.parse.quote(sym)))
        return d["chart"]["result"][0]["meta"]["regularMarketPrice"], sym
    except Exception:
        return None, sym


def implied_end_rate(price, r_start, meeting_effective_day, days_in_month):
    """Solve the post-meeting EFFR implied by the contract month-average price."""
    avg = 100.0 - price
    d_before = meeting_effective_day - 1          # days the OLD rate is in effect
    d_after = days_in_month - d_before
    r_end = (avg * days_in_month - d_before * r_start) / d_after
    return avg, r_end


def classify(move, hold_band=0.0125):
    """Map an implied move (in %) to (label, p_hold, p_move). hold_band ~ half a 'noise' bp cushion."""
    if abs(move) < hold_band:
        return "HOLD", 1.0, 0.0
    p_move = min(abs(move) / 0.25, 1.0)
    return ("CUT" if move < 0 else "HIKE"), 1.0 - p_move, p_move


def compute(meetings):
    """meetings = [(label, year, month, meeting_effective_day), ...] in chronological order.
    Returns a list of dicts; chains r_start across meetings. Prints nothing."""
    effr, lo, hi, asof = current_policy_rate()
    out = {"policy": {"effr": effr, "target": [lo, hi], "as_of": asof}, "meetings": []}
    r_start = effr
    for label, yr, mo, eff_day in meetings:
        price, sym = zq_price(yr, mo)
        if price is None:
            out["meetings"].append({"label": label, "status": "UNAVAILABLE", "symbol": sym})
            continue
        avg, r_end = implied_end_rate(price, r_start, eff_day, DAYS_IN_MONTH[mo])
        move = r_end - r_start
        lbl, p_hold, p_move = classify(move)
        out["meetings"].append({
            "label": label, "symbol": sym, "price": price,
            "implied_avg": round(avg, 4), "r_start": round(r_start, 4),
            "r_end": round(r_end, 4), "move_bp": round(move * 100, 1),
            "decision": lbl, "p_hold": round(p_hold, 4), "p_move": round(p_move, 4),
        })
        r_start = r_end
    return out


if __name__ == "__main__":
    # Default: June 17, 2026 (eff 06-18) and July 29, 2026 (eff 07-30).
    # Pass alternates as argv: label,YYYY,MM,effday  (repeatable).
    meetings = []
    for a in sys.argv[1:]:
        lbl, y, m, dd = a.split(",")
        meetings.append((lbl, int(y), int(m), int(dd)))
    if not meetings:
        meetings = [("June 2026", 2026, 6, 18), ("July 2026", 2026, 7, 30)]

    try:
        res = compute(meetings)
    except Exception as e:
        print(f"[UNAVAILABLE] policy-rate source unreachable: {e!r}")
        sys.exit(1)

    p = res["policy"]
    print(f"CME FedWatch-implied rate path (ZQ futures method)")
    print(f"Current: EFFR {p['effr']}%  target {p['target'][0]}-{p['target'][1]}%  (NY Fed, as of {p['as_of']})")
    print(f"Futures: CME 30-Day Fed Funds (ZQ), Yahoo chart API, pulled live")
    print("-" * 60)
    for m in res["meetings"]:
        if m.get("status") == "UNAVAILABLE":
            print(f"{m['label']:<12} [UNAVAILABLE] ({m['symbol']} not fetchable)")
            continue
        line = (f"{m['label']:<12} {m['symbol']}={m['price']}  "
                f"implied move {m['move_bp']:+.1f}bp  ->  "
                f"P(HOLD)={m['p_hold']*100:.1f}%")
        if m["decision"] != "HOLD":
            line += f"  P({m['decision']} 25bp)={m['p_move']*100:.1f}%"
        print(line)
