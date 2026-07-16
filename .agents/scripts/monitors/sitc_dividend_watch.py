#!/usr/bin/env python3
"""
sitc_dividend_watch.py — portable, dependency-free SITE Centers (NYSE:SITC) special-distribution monitor.

WHY THIS EXISTS (relationship to dividend_watch.ts — reuse/port, not a duplicate):
  .agents/scripts/monitors/dividend_watch.ts is the macOS front-end. It pulls data through the user's
  REAL Chrome via chrome-use (to dodge datacenter-IP 403s) and pings Telegram via telegram-cli. Neither
  dependency exists on the Hermes control-plane host (no Bun runtime, no chrome-use, no user Telethon
  session). This script is the SAME watcher re-expressed in Python 3 stdlib so it runs anywhere python3
  exists. It shares the identical on-disk state schema (seenExDates / notifiedActionDates /
  notifiedPostPayDates) so the two front-ends are interoperable rather than divergent copies.

WHAT IT WATCHES (SITC pays lumpy liquidation special distributions; the only edge in holding the stub is
whether each special re-prices the stock by MORE or LESS than the cash paid):
  1. NEW distribution declared           -> a history row not seen before
  2. UPCOMING action date within N days  -> the RECORD date for due-bill specials (ex-date after record),
                                            otherwise the ex-date
  3. POST-PAYMENT payout confirmation     -> first run on/after the payment date: verify cash posted and
                                            review selling the stub. This is the "next payout" alert.

HARD INVARIANT — ALERT ONLY. This script NEVER places an order, never contacts a broker, never trades.
It only fetches public data, updates idempotent state, and prints an actionable notice for a human.

DELIVERY. Prints an ===ALERT=== block to stdout when actionable, otherwise a one-line NO_ACTION summary.
The Hermes cron that runs this forwards an owner Telegram message ONLY when stdout contains ===ALERT===,
so days with nothing to do stay silent (no repeated notifications).

DATA SOURCE (tried in order, first success wins): stockanalysis.com API, then Nasdaq API. Both verified
reachable (HTTP 200) from the Hermes host on 2026-07-15.

OPTIONAL NOTION AUDIT. If NOTION_TOKEN and NOTION_PAGE_ID are set, appends one audit paragraph per run to
that page. Absent token -> silently skipped (Hermes has no Notion integration yet; this activates the
moment a scoped integration token is provisioned).

Usage:
  python3 sitc_dividend_watch.py                      # default: SITC, stdout notify
  python3 sitc_dividend_watch.py SITC ARE O           # multiple tickers
  python3 sitc_dividend_watch.py --summary            # also print a NO_ACTION status line
  python3 sitc_dividend_watch.py --exit-on-alert      # exit 10 when an alert fired (for tests/automation)
  STATE_DIR=/path python3 sitc_dividend_watch.py      # override state directory
  SITC_TODAY=2026-07-31 python3 sitc_dividend_watch.py  # override "today" (testing only)
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import date, datetime, timezone
from pathlib import Path

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)
STATE_DIR = Path(os.environ.get("STATE_DIR", str(Path.home() / ".config/dividend-watch")))
UPCOMING_DAYS = int(os.environ.get("UPCOMING_DAYS", "14"))
ACTION_LEAD_DAYS = int(os.environ.get("ACTION_LEAD_DAYS", "7"))
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_PAGE_ID = os.environ.get("NOTION_PAGE_ID", "")


def today() -> str:
    return os.environ.get("SITC_TODAY") or date.today().isoformat()


def days_between(a: str, b: str) -> int:
    """date(a) - date(b) in whole days. Positive when a is later than b."""
    return (date.fromisoformat(a) - date.fromisoformat(b)).days


def amt_num(a) -> float:
    s = "".join(ch for ch in str(a) if (ch.isdigit() or ch == "."))
    try:
        return float(s) if s else 0.0
    except ValueError:
        return 0.0


def _http_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read().decode("utf-8", "replace"))


def _mmddyyyy_to_iso(s: str) -> str:
    s = (s or "").strip()
    if not s or s.upper() in ("N/A", "--"):
        return ""
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%b %d, %Y"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return ""


def fetch_stockanalysis(ticker: str):
    """Return (history, info, source) or None. history rows: {dt, amt, record, pay}."""
    try:
        j = _http_json(f"https://stockanalysis.com/api/symbol/s/{ticker}/dividend")
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, TimeoutError):
        return None
    data = (j or {}).get("data") or {}
    raw = data.get("history") or []
    if not raw:
        return None
    hist = []
    for r in raw:
        hist.append(
            {
                "dt": (r.get("dt") or "").strip(),
                "amt": r.get("amt") or "",
                "record": (r.get("record") or "").strip(),
                "pay": (r.get("pay") or "").strip(),
            }
        )
    return hist, data.get("infoTable") or {}, "stockanalysis.com/api/symbol/s/%s/dividend" % ticker


def fetch_nasdaq(ticker: str):
    try:
        j = _http_json(
            f"https://api.nasdaq.com/api/quote/{ticker}/dividends?assetclass=stocks"
        )
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, TimeoutError):
        return None
    rows = (((j or {}).get("data") or {}).get("dividends") or {}).get("rows") or []
    if not rows:
        return None
    hist = []
    for r in rows:
        dt = _mmddyyyy_to_iso(r.get("exOrEffDate") or "")
        if not dt:
            continue
        hist.append(
            {
                "dt": dt,
                "amt": r.get("amount") or "",
                "record": _mmddyyyy_to_iso(r.get("recordDate") or ""),
                "pay": _mmddyyyy_to_iso(r.get("paymentDate") or ""),
            }
        )
    if not hist:
        return None
    return hist, {}, f"api.nasdaq.com/api/quote/{ticker}/dividends"


def fetch_ticker(ticker: str):
    for fetcher in (fetch_stockanalysis, fetch_nasdaq):
        got = fetcher(ticker)
        if got:
            return got
    return None


def load_state(ticker: str) -> dict:
    f = STATE_DIR / f"{ticker}.json"
    if f.exists():
        try:
            return json.loads(f.read_text())
        except (ValueError, OSError):
            pass
    return {}


def save_state(ticker: str, st: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    (STATE_DIR / f"{ticker}.json").write_text(json.dumps(st, indent=2, sort_keys=False))


def notion_audit(line: str) -> str:
    if not NOTION_TOKEN or not NOTION_PAGE_ID:
        return "skipped(no_token)"
    payload = json.dumps(
        {
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": line[:1900]}}]},
                }
            ]
        }
    ).encode()
    req = urllib.request.Request(
        f"https://api.notion.com/v1/blocks/{NOTION_PAGE_ID}/children",
        data=payload,
        method="PATCH",
        headers={
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return f"ok(http{resp.status})"
    except urllib.error.HTTPError as e:
        return f"error(http{e.code})"
    except (urllib.error.URLError, ValueError, TimeoutError) as e:
        return f"error({type(e).__name__})"


def process_ticker(ticker: str, force_summary: bool) -> bool:
    """Return True if an alert fired."""
    now = today()
    got = fetch_ticker(ticker)
    if not got:
        print(f"WARN [{ticker}] data fetch failed on {now} — no source reachable.")
        return False
    history, info, source = got

    st = load_state(ticker)
    seen = set(st.get("seenExDates") or [])
    notified_action = set(st.get("notifiedActionDates") or [])
    had_postpay_state = isinstance(st.get("notifiedPostPayDates"), list)
    notified_postpay = set(st.get("notifiedPostPayDates") or [])
    target_delivered = dict(st.get("targetDelivered") or {})

    alerts = []
    first_run = len(seen) == 0

    # 1) NEW distributions. Skip on the very first run so we don't fire the whole backlog as "new".
    fresh = [r for r in history if r["dt"] and r["dt"] not in seen]
    if not first_run:
        for r in fresh:
            alerts.append(
                f"NEW {ticker} distribution: {r['amt']} | ex {r['dt']} | record {r['record']} | pay {r['pay']}"
            )
    for r in history:
        if r["dt"]:
            seen.add(r["dt"])

    # On first sight of this state, seed strictly-past payments so we never replay historical payouts.
    if not had_postpay_state:
        for r in history:
            if r["pay"] and days_between(now, r["pay"]) > 0:
                notified_postpay.add(f"{r['dt']}|{r['record']}|{r['pay']}")

    lead_window = max(UPCOMING_DAYS, ACTION_LEAD_DAYS)
    for r in history:
        dt, rec, pay = r["dt"], r["record"], r["pay"]
        action_key = f"{dt}|{rec}|{pay}"
        due_bill = bool(dt and rec and days_between(dt, rec) > 0) and bool(
            pay and days_between(pay, rec) >= 0
        )
        action_date = rec if due_bill else dt

        # 2) Upcoming action date.
        if action_date:
            action_days = days_between(action_date, now)
            if 0 <= action_days <= lead_window and action_key not in notified_action:
                if due_bill:
                    alerts.append(
                        f"ACTION {ticker} record date in {action_days}d ({rec}): {r['amt']}. "
                        f"Hold through payment {pay}; do not sell during the due-bill window. "
                        f"Review selling on the next market session after payment. (alert only — no trade)"
                    )
                else:
                    alerts.append(
                        f"ACTION {ticker} ex-date in {action_days}d ({dt}): {r['amt']}. "
                        f"Hold through the record date, then review selling. (alert only — no trade)"
                    )
                notified_action.add(action_key)

        # 3) Post-payment payout confirmation (the "next payout" alert). Fires first run on/after pay.
        if pay and days_between(now, pay) >= 0 and action_key not in notified_postpay:
            alerts.append(
                f"PAYOUT {ticker} payment date {pay} reached for {r['amt']} (ex {dt or 'unknown'}). "
                f"Verify the cash posted to the Roth IRA, then review selling the stub on the next "
                f"market session. (alert only — no trade, no order placed)"
            )
            notified_postpay.add(action_key)
            target_delivered[action_key] = now

    # Persist idempotent state.
    st["seenExDates"] = sorted(seen)
    st["reactedExDates"] = sorted(set(st.get("reactedExDates") or []))
    st["notifiedActionDates"] = sorted(notified_action)
    st["notifiedPostPayDates"] = sorted(notified_postpay)
    st["targetDelivered"] = target_delivered
    st["lastRun"] = now
    save_state(ticker, st)

    ex = info.get("exdiv") if isinstance(info, dict) else None
    annual = info.get("annual") if isinstance(info, dict) else None
    summary = (
        f"{ticker}: {len(history)} distributions on record | next/last ex {ex or history[0]['dt']} | "
        f"annual {annual or '?'} | src {source} | {now}"
    )

    fired = bool(alerts)
    payout_fired = any(a.startswith("PAYOUT ") for a in alerts)
    audit_line = f"[sitc-dividend-watch {now}] {summary} | alerts={len(alerts)}"
    audit_status = notion_audit(audit_line + ((" | " + " || ".join(alerts)) if alerts else " | no action"))

    if fired:
        block = "\n".join(alerts)
        print("===ALERT===")
        print(f"SITC dividend-watch {now}")
        print(summary)
        print("")
        print(block)
        if payout_fired:
            print("")
            print("SELF_DISABLE: target payout delivered — this alert-only cron may now be disabled; "
                  "state is idempotent so it will not re-notify regardless.")
        print(f"notion_audit={audit_status}")
        print("===END===")
    else:
        print(f"NO_ACTION {summary} | notion_audit={audit_status}")
        if force_summary:
            print(f"===STATUS===\nSITC dividend-watch {now} — no action.\n{summary}\n===END===")
    return fired


def main() -> int:
    argv = sys.argv[1:]
    force_summary = "--summary" in argv
    exit_on_alert = "--exit-on-alert" in argv
    tickers = [a.upper() for a in argv if not a.startswith("--")] or ["SITC"]
    any_alert = False
    for t in tickers:
        try:
            any_alert = process_ticker(t, force_summary) or any_alert
        except Exception as e:  # never crash a cron on one bad ticker
            print(f"ERROR [{t}] {type(e).__name__}: {e}")
    if exit_on_alert and any_alert:
        return 10
    return 0


if __name__ == "__main__":
    sys.exit(main())
