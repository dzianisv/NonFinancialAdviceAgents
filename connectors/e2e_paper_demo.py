"""
End-to-end PAPER demo — the GOAL.md end-to-end flow, minus live placement.

Simulates exactly what happens when the user says "trade daily for income":
  regime read -> backtest gate check -> desk builds target orders -> deterministic hard caps
  -> notification-first executor -> human-approvable tickets + immutable audit log.

NO credentials, NO broker contact, NO live orders. The ONLY step missing vs production is swapping
mode="notify" -> mode="live" with the user's Robinhood/Coinbase creds + sign-off. This proves the
whole pipeline is wired and governed.

Run: python3 connectors/e2e_paper_demo.py
Educational analysis, not financial advice.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from hard_caps import Order, BookState, CapConfig
from notify_executor import run_batch

TODAY = "2026-06-03"   # passed in, not read from the clock (deterministic demo)


def gate_status():
    """What has PASSed the strategy-discovery-backtest gate, per the committed backtests."""
    return {
        # track A: PASSED — deployable mid-risk allocation
        "midrisk_alloc": {
            "passed": True,
            "ref": "backtests/midrisk_allocation_backtest.py:RSP70/GLD15/IEF15",
            "targets": {"RSP": 0.70, "GLD": 0.15, "IEF": 0.15},
            "venue": "robinhood",
        },
        # track C: NOT passed for live alpha (REGIME-SMA is a drawdown control, paper-only)
        "crypto_regime_sma": {
            "passed": False,
            "ref": "backtests/daytrade/crypto_lowfreq_backtest.py:REGIME-SMA",
            "note": "drawdown control, not alpha — paper only until a maker-fill model PASSes",
            "venue": "coinbase-cdp",
        },
    }


def build_orders(nav, gate):
    """Desk turns PASSed strategies into target orders. Unpassed strategies propose nothing live."""
    orders, skipped = [], []
    for name, s in gate.items():
        if not s["passed"]:
            skipped.append((name, s.get("note", "not passed")))
            continue
        for sym, wt in s["targets"].items():
            notional = round(nav * wt, 0)
            # chunk into <= per-order cap so the demo shows the cap working, not failing
            chunk = 5000
            while notional > 0:
                n = min(chunk, notional)
                orders.append(Order(sym, "buy", n, s["venue"], s["ref"]))
                notional -= n
    return orders, skipped


def main():
    print("=" * 78)
    print("END-TO-END PAPER DEMO — 'trade daily for income' (notification mode, no creds)")
    print("=" * 78)
    nav = 100_000.0
    print(f"\nas_of: {TODAY}   demo NAV: ${nav:,.0f}\n")

    # 1. regime (stub read — in production from regime-detection / regime_monitor.py)
    print("1. REGIME      risk-on/neutral -> exposure 1.0 (demo stub; prod: regime-detection desk)")

    # 2. gate status
    gate = gate_status()
    print("2. GATE        backtest-before-trade status:")
    for k, s in gate.items():
        mark = "PASS" if s["passed"] else "HOLD"
        print(f"               [{mark}] {k}: {s['ref']}")
        if not s["passed"]:
            print(f"                      -> {s['note']}")

    # 3. desk builds orders from PASSed strategies only
    orders, skipped = build_orders(nav, gate)
    print(f"\n3. DESK        built {len(orders)} target orders from PASSed strategies; "
          f"{len(skipped)} strategy(ies) on hold")

    # 4+5. caps + notification-first executor (raise gross cap to fit the $100k demo book)
    cfg = CapConfig(max_position_notional=80_000, max_gross_notional=120_000, max_orders_per_day=100)
    book = BookState()
    print("4. CAPS+NOTIFY deterministic hard caps -> notification-first tickets:\n")
    results = run_batch(orders, book, cfg, mode="notify", now=TODAY)
    proposed = [r for r in results if r["result"] == "PROPOSED"]
    rejected = [r for r in results if r["result"] != "PROPOSED"]
    for r in proposed:
        print(f"   PROPOSED   {r['ticket']}")
    for r in rejected:
        print(f"   {r['result']:10s} {r.get('reason','')}")

    # 6. report
    print("\n5. REPORT")
    by_sym = {}
    for r in proposed:
        o = r["order"]; by_sym[o["symbol"]] = by_sym.get(o["symbol"], 0) + o["notional"]
    for sym, tot in sorted(by_sym.items()):
        print(f"     {sym:6s} ${tot:>10,.0f}  ({tot/nav:.0%} of NAV)")
    print(f"     {'TOTAL':6s} ${sum(by_sym.values()):>10,.0f} proposed for human approval")
    for name, why in skipped:
        print(f"     HOLD   {name}: {why}")

    print("\n" + "-" * 78)
    print("Every order above is NOTIFICATION-ONLY — a human places/approves them. Nothing was sent")
    print("to any broker. To go live: connect Robinhood/Coinbase creds, set CONFIRM_LIVE, and the")
    print("SAME pipeline runs in mode='live' behind the same deterministic caps. Audit log written.")
    print("Educational analysis, not financial advice.")


if __name__ == "__main__":
    main()
