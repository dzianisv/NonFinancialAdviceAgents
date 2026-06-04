"""
Tests for the notification-first executor + hard caps.
Proves: caps reject bad orders; notify mode NEVER places; live is hard-gated without creds.
Run: python3 connectors/test_connectors.py
"""
import os, sys, tempfile
sys.path.insert(0, os.path.dirname(__file__))
from hard_caps import Order, BookState, CapConfig, check, would_pass, CapViolation
from notify_executor import execute, run_batch

PASS = 0
FAIL = 0


def ok(cond, msg):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print(f"  FAIL: {msg}")


def tmp_audit():
    fd, p = tempfile.mkstemp(suffix=".jsonl"); os.close(fd); return p


def main():
    cfg = CapConfig()
    A = tmp_audit()

    # 1. caps: per-order notional
    ok(not would_pass(Order("X", "buy", 6000, "robinhood", "ref"), BookState(), cfg),
       "per-order cap should reject $6000 > $5000")
    ok(would_pass(Order("X", "buy", 4000, "robinhood", "ref"), BookState(), cfg),
       "$4000 within caps should pass")

    # 2. caps: no strategy_ref => backtest-before-trade violation
    ok(not would_pass(Order("X", "buy", 100, "robinhood", ""), BookState(), cfg),
       "missing strategy_ref must reject (backtest-before-trade)")

    # 3. caps: shorting disabled
    ok(not would_pass(Order("X", "sell", 1000, "robinhood", "ref"), BookState(), cfg),
       "selling with no position (short) must reject when allow_shorts=False")

    # 4. caps: position cap (post-trade)
    b = BookState(positions={"X": 24000})
    ok(not would_pass(Order("X", "buy", 3000, "robinhood", "ref"), b, cfg),
       "position cap: 24000+3000 > 25000 must reject")

    # 5. caps: daily loss kill
    b = BookState(realized_pnl_today=-2500)
    ok(not would_pass(Order("X", "buy", 100, "robinhood", "ref"), b, cfg),
       "daily loss -2500 <= -2000 must kill")

    # 6. caps: kill switch file
    kf = tmp_audit() + ".KILL"; open(kf, "w").close()
    kcfg = CapConfig(kill_switch_file=kf)
    ok(not would_pass(Order("X", "buy", 100, "robinhood", "ref"), BookState(), kcfg),
       "kill switch file must block all")
    os.remove(kf)

    # 7. notify mode never places — result is PROPOSED, no creds touched
    r = execute(Order("BTC-USD", "buy", 3000, "coinbase-cdp", "ref"), BookState(), cfg,
                mode="notify", now="2026-06-03", audit_path=A)
    ok(r["result"] == "PROPOSED", f"notify mode should PROPOSE, got {r['result']}")
    ok("ticket" in r, "notify result should carry a human-approvable ticket")

    # 8. live mode blocked without creds + without CONFIRM_LIVE
    os.environ.pop("ROBINHOOD_AGENT_CONNECTED", None)
    os.environ.pop("CONFIRM_LIVE", None)
    r = execute(Order("RSP", "buy", 1000, "robinhood", "ref"), BookState(), cfg,
                mode="live", now="2026-06-03", audit_path=A)
    ok(r["result"] == "LIVE_BLOCKED", f"live without creds must block, got {r['result']}")
    ok("missing creds" in r["reason"], "live block reason should cite missing creds")

    # 9. live mode: even WITH creds + confirm, real call is never auto-wired
    os.environ["ROBINHOOD_AGENT_CONNECTED"] = "1"
    os.environ["CONFIRM_LIVE"] = "2026-06-03"
    r = execute(Order("RSP", "buy", 1000, "robinhood", "ref"), BookState(), cfg,
                mode="live", now="2026-06-03", audit_path=A)
    ok(r["result"] == "LIVE_NOT_WIRED",
       f"live with creds should still NOT place (deliberate stub), got {r['result']}")
    os.environ.pop("ROBINHOOD_AGENT_CONNECTED", None); os.environ.pop("CONFIRM_LIVE", None)

    # 10. batch compounds caps across orders (gross cap)
    bigcfg = CapConfig(max_order_notional=50000, max_position_notional=50000, max_gross_notional=10000)
    res = run_batch([Order(f"S{i}", "buy", 4000, "robinhood", "ref") for i in range(5)],
                    BookState(), bigcfg, mode="notify", now="2026-06-03", audit_path=A)
    rejected = [r for r in res if r["result"] == "REJECTED"]
    ok(len(rejected) >= 1, "gross cap should reject later orders in the batch once $10k gross hit")

    os.remove(A)
    print(f"\n{PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
