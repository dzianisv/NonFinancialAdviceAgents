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
        if os.path.basename(path) == "prices.json":
            continue   # price layer, not a pool panel
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


def load_prices():
    path = os.path.join(DATA, "prices.json")
    return json.load(open(path)) if os.path.exists(path) else {}


PRICES = load_prices()   # {kind: {date: usd_price}} for directional assets (eth/btc/sol)


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
        # accrue: realized APY (monthly) + price return for directional assets (eth/btc/sol)
        for k in list(holds):
            kind = panel[k]["kind"]
            ret = apy_realized(panel[k], t, t1) / 100.0 * (30.0 / 365.0)
            if kind in PRICES and t in PRICES[kind] and t1 in PRICES[kind]:
                ret += PRICES[kind][t1] / PRICES[kind][t] - 1.0   # price change over the month
            holds[k] *= (1 + ret)
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


# ---- agent-in-the-loop -----------------------------------------------------
# The AGENT is the decision-maker. We dump each rebalance date's world(t) (point-in-time,
# no look-ahead) to JSON; an LLM agent reads world(t) and returns target weights; we feed those
# back here and compare the agent's path to the deterministic baselines. Decisions carry forward
# between quarterly rebalances.
def rebalance_dates(quarterly=True):
    g = months(START, END)[:-1]
    return g[::3] if quarterly else g


def dump_worlds(panel, path):
    out = {t: world(panel, t) for t in rebalance_dates()}
    with open(path, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    return out


def decide_from_decisions(decisions):
    dates = sorted(decisions.keys())
    def decide(t, w, pf):
        elig = [d for d in dates if d <= t]
        return decisions[elig[-1]] if elig else {}
    return decide


def _row(name, r, panel):
    held_synth = any(any(k in ("susde",) and v > 1 for k, v in h[2].items()) for h in r["hist"])
    note = "HELD sUSDe (synthetic)!" if held_synth else ""
    return (f"{name:14} {r['final']:>11,.0f} {r['cagr']*100:>11.2f}% "
            f"{r['maxdd']*100:>7.1f}% {r['turnover_x']:>8.1f}x  {note}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2 and sys.argv[1] == "dump":
        panel = load_panel()
        path = os.path.join(HERE, "agent_worlds.json")
        dump_worlds(panel, path)
        print(f"dumped {len(rebalance_dates())} quarterly worlds → {path}")
        for t in rebalance_dates():
            avail = sorted(world(panel, t).keys())
            print(f"  {t}: {avail}")
    elif len(sys.argv) >= 3 and sys.argv[1] == "agent":
        panel = load_panel()
        decisions = json.load(open(sys.argv[2]))
        print(f"Universe ({len(panel)}), window {START}→{END}, ${CAPITAL:,.0f}, {TURNOVER_COST*1e4:.0f}bps cost\n")
        print(f"{'strategy':14} {'final$':>11} {'realized/yr':>12} {'maxDD':>8} {'turnover':>9}  notes")
        results = {}
        for name, fn in list(STRATEGIES.items()):
            results[name] = run(panel, fn)
            print(_row(name, results[name], panel))
        results["AGENT"] = run(panel, decide_from_decisions(decisions))
        print(_row("AGENT", results["AGENT"], panel))
        print("\nAgent decisions are quarterly target weights from an LLM reading point-in-time world(t).")
        # equity-curve chart
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import datetime as _dt
            fig, ax = plt.subplots(figsize=(9, 5), dpi=130)
            style = {"AGENT": ("#1f8a4c", 2.6), "chase_max": ("#d4341f", 1.6),
                     "equal_clean": ("#0f6fd1", 1.6), "all_aave": ("#888", 1.4),
                     "do_nothing": ("#bbb", 1.2)}
            for name, r in results.items():
                xs = [_dt.date.fromisoformat(h[0]) for h in r["hist"]]
                ys = [h[1] for h in r["hist"]]
                c, lw = style.get(name, ("#444", 1.4))
                ax.plot(xs, ys, label=f"{name}  {r['cagr']*100:.1f}%/yr  DD{r['maxdd']*100:.0f}%",
                        color=c, lw=lw)
            ax.axhline(CAPITAL, color="#ddd", lw=0.8)
            ax.set_title("Agent-in-the-loop backtest vs baselines (2024-07→2026-05, ETH −33%)",
                         fontweight="bold", fontsize=12, loc="left")
            ax.set_ylabel("Portfolio value ($)")
            ax.legend(frameon=False, fontsize=8.5, loc="upper left")
            for s in ("top", "right"):
                ax.spines[s].set_visible(False)
            fig.autofmt_xdate(); fig.tight_layout()
            out = os.path.join(HERE, "agent_backtest.png")
            fig.savefig(out, bbox_inches="tight")
            print(f"chart → {out}")
        except Exception as e:
            print(f"(chart skipped: {e})")
    else:
        main()
