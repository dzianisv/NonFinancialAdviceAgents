#!/usr/bin/env python3
"""
trend-scout — DON'T-MISS coverage scan (broad universe, not just the 9 themes).

Purpose: so a future NVDA/SanDisk-type breakout in ANY corner of the market lands on your radar,
even if it isn't in a pre-chosen theme basket. Scans ~180 liquid US names across all sectors and
surfaces what's WAKING UP, split by stage so you catch early movers AND know which names already ran.

This is a RADAR (awareness/coverage), NOT a buy signal and NOT alpha. Strong relative strength =
"this is moving, look at it"; the multi-lens-quorum decides if it's a buy or a late chase. Stage 0
proved there's no mechanical edge here — coverage is the value, judgment is separate.

Per name vs SPY: RS_3m / RS_6m (strength), accel (1m vs prior-3m pace = is it speeding up = EARLY),
ext = % above 200d MA (how far it's already run). Score favors strong + accelerating + not-yet-extreme
(to catch moves earlier). Output: EARLY MOVERS (act-worthy radar) + ALREADY EXTENDED (don't-miss but late).

Usage: python3 emerging_scan.py [--top 20] [--period 400d]
Educational, not advice. Radar only — route anything interesting to multi-lens-quorum.
"""
import os, sys, argparse, warnings
warnings.filterwarnings("ignore")
from theme_radar import fetch, ret, above_200, HERE


def load_universe():
    with open(os.path.join(HERE, "universe.txt")) as f:
        return sorted({t.strip() for t in f.read().replace("\n", ",").split(",") if t.strip()})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--period", default="400d")
    args = ap.parse_args()

    uni = load_universe()
    close = fetch(uni + ["SPY"], args.period)
    if "SPY" not in close.columns:
        sys.exit("ERROR: SPY not fetched.")
    spy = close["SPY"]
    spy3, spy6, spy1 = ret(spy, 63), ret(spy, 126), ret(spy, 21)

    rows = []
    for t in uni:
        if t not in close.columns:
            continue
        r3, r6, r1 = ret(close[t], 63), ret(close[t], 126), ret(close[t], 21)
        if r3 is None or r6 is None:
            continue
        ext, _ = above_200(close[t])
        rs3 = r3 - spy3 if spy3 is not None else 0
        rs6 = r6 - spy6 if spy6 is not None else 0
        accel = (r1 - r3 / 3.0) if r1 is not None else 0   # last month vs prior-3m monthly pace
        rows.append({"t": t, "rs3": rs3, "rs6": rs6, "accel": accel, "ext": ext, "r6": r6})

    # strong = positive 6m relative strength (it's outperforming = "moving")
    strong = [x for x in rows if x["rs6"] > 0]
    # EARLY = strong, accelerating, not-yet-extreme extension (<40% above 200dMA or no MA yet)
    early = [x for x in strong if x["accel"] > 0 and (x["ext"] is None or x["ext"] < 0.40)]
    early.sort(key=lambda x: (x["accel"] + x["rs3"]), reverse=True)
    # EXTENDED = strong but already far above trend (don't-miss, but late)
    ext = [x for x in strong if x["ext"] is not None and x["ext"] >= 0.40]
    ext.sort(key=lambda x: x["ext"], reverse=True)

    def fmt(x):
        e = f"{x['ext']*100:+.0f}%>MA" if x["ext"] is not None else "  n/a"
        return (f"  {x['t']:<6} 6m {x['r6']*100:+5.0f}%  RS6 {x['rs6']*100:+5.0f}%  "
                f"accel {x['accel']*100:+4.0f}%  {e:>9}")

    print(f"\nTREND-SCOUT — DON'T-MISS coverage scan  |  {len(strong)}/{len(rows)} names outperforming SPY")
    print("RADAR only (awareness, not a buy signal). Route anything you act on to multi-lens-quorum.")
    print("=" * 78)
    print(f"\n## EARLY MOVERS — strong + accelerating + not-yet-extended (catch these earlier)")
    for x in early[:args.top]:
        print(fmt(x))
    print(f"\n## ALREADY EXTENDED — strong but far above trend (don't-miss, but likely LATE to chase)")
    for x in ext[:max(8, args.top // 2)]:
        print(fmt(x))
    print("\naccel>0 = speeding up (earlier in the move). ext = % above 200d MA (how far it already ran).")
    print("Coverage layer: surfaces strength anywhere in the universe so you don't MISS it. The quorum")
    print("judges buy vs late-chase. Educational, not advice. Weak/no mechanical edge — this is a radar.")


if __name__ == "__main__":
    main()
