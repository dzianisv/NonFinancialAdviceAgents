#!/usr/bin/env python3
"""
liveness.py — dead-man's-switch for the advisor's daily cron jobs.

The advisor is SILENT-unless-alert by design, so "nothing fired" is indistinguishable from
"everything broke". This closes that gap:
  - `log`   : each daily cron appends a heartbeat (even on NO_REPLY) so we KNOW it ran.
  - `check` : a health cron reads the ledger and emits STALE jobs (DM-worthy) — alert ONLY when
              an expected job hasn't logged within max-age. If all fresh → exit 0, prints ALL_FRESH.

Ledger: $LIVENESS_LEDGER or ~/.openclaw/workspace/investor/liveness.jsonl
Educational/ops tooling — no market data, no fabrication.

Usage:
    python3 liveness.py log --job dip-screener --detail "10 HIGH dips, regime RISK_ON, 0 alerted"
    python3 liveness.py check --expect dip-screener,crypto-dip-scanner,signal-convergence,regime-fed,journalism --max-age-hours 26
"""
from __future__ import annotations
import argparse, json, os, sys
from datetime import datetime, timedelta, timezone

LEDGER = os.environ.get("LIVENESS_LEDGER", os.path.expanduser("~/.openclaw/workspace/investor/liveness.jsonl"))


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(ts: str) -> datetime | None:
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def cmd_log(job: str, detail: str) -> int:
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    rec = {"job": job, "ts": _now().isoformat(), "detail": detail or ""}
    with open(LEDGER, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print(f"logged {job} @ {rec['ts']}")
    return 0


def cmd_check(expect: list[str], max_age_hours: float) -> int:
    last: dict[str, datetime] = {}
    last_detail: dict[str, str] = {}
    if os.path.exists(LEDGER):
        with open(LEDGER) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                j, dt = r.get("job"), _parse(r.get("ts", ""))
                if not j or dt is None:
                    continue
                if j not in last or dt > last[j]:
                    last[j] = dt
                    last_detail[j] = r.get("detail", "")
    cutoff = _now() - timedelta(hours=max_age_hours)
    stale = []
    for j in expect:
        if j not in last:
            stale.append(f"{j}: NEVER logged")
        elif last[j] < cutoff:
            age_h = (_now() - last[j]).total_seconds() / 3600
            stale.append(f"{j}: last logged {last[j].isoformat()} ({age_h:.0f}h ago > {max_age_hours}h)")
    out = {
        "status": "STALE" if stale else "ALL_FRESH",
        "stale": stale,
        "fresh": {j: {"ts": last[j].isoformat(), "detail": last_detail.get(j, "")}
                  for j in expect if j in last and last[j] >= cutoff},
    }
    print(json.dumps(out, indent=2))
    return 1 if stale else 0


def main() -> None:
    ap = argparse.ArgumentParser(description="advisor cron dead-man's-switch")
    sub = ap.add_subparsers(dest="cmd", required=True)
    pl = sub.add_parser("log")
    pl.add_argument("--job", required=True)
    pl.add_argument("--detail", default="")
    pc = sub.add_parser("check")
    pc.add_argument("--expect", required=True, help="comma-separated expected job names")
    pc.add_argument("--max-age-hours", type=float, default=26.0)
    a = ap.parse_args()
    if a.cmd == "log":
        sys.exit(cmd_log(a.job, a.detail))
    else:
        sys.exit(cmd_check([s.strip() for s in a.expect.split(",") if s.strip()], a.max_age_hours))


if __name__ == "__main__":
    main()
