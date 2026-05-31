#!/usr/bin/env python3
"""
Backtest simulator + baseline strategies.

Replays the cached point-in-time panel month by month over 2024-07 → 2026-05, no look-ahead
(a pool is only investable once it has history). Each strategy is a `decide(t, world, pf)`
function returning target weights; the simulator rebalances (with turnover cost) and accrues the
REALIZED quoted APY over each holding month. Reports realized yield, max drawdown, turnover.

These baselines are the BAR the agent must beat — especially `chase_max` (the naive yield-chaser),
which should rotate into spikes/synthetics that the rules-based `equal_clean` avoids.

Run: /Users/engineer/.venv/bin/python3 crypto/backtest/simulate.py
"""
from __future__ import annotations
import bisect
import datetime as dt
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

START, END = "2024-07-01", "2026-05-01"
CAPITAL = 100_000.0
TURNOVER_COST = 0.0005   # 5 bps per $ moved (gas + slippage proxy)


# ---- panel ----------------------------------------------------------------
def load_panel():
    panel = {}
    for path in sorted(glob.glob(os.path.join(DATA, "*.json"))):
        d = json.load(open(path))
        dates, apys = [], {}
        for r in d["series"]:
            if r["apy"] is None:
                continue
            dates.append(r["date"])
            apys[r["date"]] = r["apy"]
        dates.sort()
        panel[d["label"]] = {"kind": d["kind"], "dates": dates, "apy": apys,
                             "first": dates[0] if dates else "9999"}
    return panel


def apy_asof(p, t):
    """Latest quoted APY on or before t (what a depositor was earning at t)."""
    i = bisect.bisect_right(p["dates"], t) - 1
    return p["apy"][p["dates"][i]] if i >= 0 else None


def apy_realized(p, t0, t1):
    """Average quoted APY over [t0, t1) — the rate actually earned that month."""
    vals = [p["apy"][d] for d in p["dates"] if t0 <= d < t1]
    return sum(vals) / len(vals) if vals else (apy_asof(p, t0) or 0.0)


def months(start, end):
    y, m = int(start[:4]), int(start[5:7])
    out = []
    while f"{y:04d}-{m:02d}-01" <= end:
        out.append(f"{y:04d}-{m:02d}-01")
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return out


def world(panel, t):
    """What the agent/strategy can see at t: available pools, current + 30d-mean APY, kind."""
    w = {}
    for label, p in panel.items():
        if p["first"] > t:
            continue  # didn't exist yet
        cur = apy_asof(p, t)
        if cur is None:
            continue
        t30 = (dt.date.fromisoformat(t) - dt.timedelta(days=30)).isoformat()
        recent = [p["apy"][d] for d in p["dates"] if t30 <= d <= t]
        w[label] = {"kind": p["kind"], "apy": cur,
                    "apy_30d": sum(recent) / len(recent) if recent else cur}
    return w


# ---- strategies (decide -> target weights, rest is idle cash) --------------
def s_do_nothing(t, w, pf):
    return {}

def s_all_aave(t, w, pf):
    return {"aave_usdc_eth": 1.0} if "aave_usdc_eth" in w else {}

def s_chase_max(t, w, pf):
    best = max(w, key=lambda k: w[k]["apy"])
    return {best: 1.0}

def s_equal_clean(t, w, pf):
    """Rules proxy: equal-weight clean stable pools; never synthetic; cap 25% each."""
    clean = [k for k, v in w.items() if v["kind"] == "stable"]
    if not clean:
        return {}
    wt = min(0.25, 1.0 / len(clean))
    return {k: wt for k in clean}

STRATEGIES = {"do_nothing": s_do_nothing, "all_aave": s_all_aave,
              "chase_max": s_chase_max, "equal_clean": s_equal_clean}


# ---- simulator ------------------------------------------------------------
def run(panel, decide):
    grid = months(START, END)
    holds = {}            # label -> $
    cash = CAPITAL
    peak, maxdd, turnover = CAPITAL, 0.0, 0.0
    hist = []
    for i, t in enumerate(grid[:-1]):
        t1 = grid[i + 1]
        w = world(panel, t)
        total = cash + sum(holds.values())
        # rebalance to target
        target = decide(t, w, dict(holds))
        target = {k: v for k, v in target.items() if k in w}
        tw = sum(target.values())
        if tw > 1.0:
            target = {k: v / tw for k, v in target.items()}
        tgt_dollars = {k: total * v for k, v in target.items()}
        moved = sum(abs(tgt_dollars.get(k, 0) - holds.get(k, 0))
                    for k in set(holds) | set(tgt_dollars))
        cost = moved * TURNOVER_COST
        turnover += moved
        holds = tgt_dollars
        cash = total - sum(holds.values()) - cost
        # accrue realized APY over the month
        for k in list(holds):
            r = apy_realized(panel[k], t, t1) / 100.0
            holds[k] *= (1 + r * (30.0 / 365.0))
        val = cash + sum(holds.values())
        peak = max(peak, val)
        maxdd = min(maxdd, val / peak - 1)
        hist.append((t1, val, dict(holds)))
    final = hist[-1][1]
    yrs = len(grid[:-1]) / 12.0
    cagr = (final / CAPITAL) ** (1 / yrs) - 1
    return {"final": final, "cagr": cagr, "maxdd": maxdd,
            "turnover_x": turnover / CAPITAL, "hist": hist}


def main():
    panel = load_panel()
    print(f"Universe ({len(panel)}): " + ", ".join(f"{k}[{v['kind']}]" for k, v in panel.items()))
    print(f"Window {START} → {END},  ${CAPITAL:,.0f} start,  {TURNOVER_COST*1e4:.0f}bps turnover cost\n")
    print(f"{'strategy':14} {'final$':>11} {'realized/yr':>12} {'maxDD':>8} {'turnover':>9}  notes")
    for name, fn in STRATEGIES.items():
        r = run(panel, fn)
        # note: did it ever hold the synthetic trap?
        held_synth = any("susde" in h[2] and h[2]["susde"] > 1 for h in r["hist"])
        note = "held sUSDe (synthetic)!" if held_synth else ""
        print(f"{name:14} {r['final']:>11,.0f} {r['cagr']*100:>11.2f}% "
              f"{r['maxdd']*100:>7.1f}% {r['turnover_x']:>8.1f}x  {note}")
    print("\nAPY = DefiLlama quoted rate earned over each holding month (forward-quote proxy for "
          "realized). Tail depeg risk that did NOT occur in-window is invisible here — that's why "
          "the rules exist beyond the backtest.")


if __name__ == "__main__":
    main()
