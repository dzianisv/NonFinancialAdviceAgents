#!/usr/bin/env python3
"""Standalone evidence check for the mkt AAPL $272 alert (id: aapl-below-272-awy9).

Reproduces the alert's stated reasoning -- 17/210 completed weekly closes in
$260-$280, daily 200-SMA $272.45, weekly 50-SMA $265.98, weekly 30-SMA $275.47,
through completed bars on 2026-07-10 -- from a fresh yfinance pull, under BOTH
Close conventions (auto_adjust=True, dividend-adjusted total-return; and
auto_adjust=False, the actual unadjusted quoted price). Writes a dated evidence
artifact to backtests/results/aapl_alert_272_verification.txt and exits nonzero
if the unadjusted figures do not match the alert's stated values.

Independent of backtests/aapl_entry_trigger_backtest.py: no shared cache, retry
framework, or CLI flag. A price-level alert must track the actual quoted price,
so auto_adjust=False is the correct convention for this check -- the timing
backtest deliberately uses auto_adjust=True (total-return) for account-growth
simulation, which is a different question and belongs in that file only.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf

CUTOFF = "2026-07-10"
BUCKET_LOW, BUCKET_HIGH = 260.0, 280.0
WEEKLY_BAR_COUNT = 210
DAILY_SMA_DAYS = 200
WEEKLY_SMA_A_WEEKS = 50
WEEKLY_SMA_B_WEEKS = 30
STATED_BUCKET_COUNT = 17
STATED_SMA200_DAILY = 272.45
STATED_SMA50_WEEKLY = 265.98
STATED_SMA30_WEEKLY = 275.47
SOURCE_URL = "https://finance.yahoo.com/quote/AAPL/history"
TOL = 0.01  # one-cent tolerance

RESULTS_PATH = Path(__file__).resolve().parent / "results" / "aapl_alert_272_verification.txt"


def download_close(auto_adjust: bool) -> pd.Series:
    """Fresh AAPL daily Close from yfinance. Straightforward pull, no retry/cache
    layer -- if this fails, fail loudly rather than silently masking a stale read."""
    df = yf.download(["AAPL"], start="1999-01-01", auto_adjust=auto_adjust, progress=False)
    if df is None or df.empty:
        raise RuntimeError(f"yfinance AAPL download failed (auto_adjust={auto_adjust}): empty frame")
    close = df["Close"]["AAPL"] if isinstance(df["Close"], pd.DataFrame) else df["Close"]
    return close.dropna().sort_index().round(2)


def metrics(daily_close: pd.Series, cutoff: pd.Timestamp) -> dict:
    """Slice to completed bars <= cutoff BEFORE resampling/rolling, then compute
    the four alert figures from exactly the last WEEKLY_BAR_COUNT weekly bars."""
    daily = daily_close.loc[daily_close.index <= cutoff]
    weekly = daily.resample("W-FRI").last().dropna()
    if len(weekly) and daily.index.max() < weekly.index[-1]:
        weekly = weekly.iloc[:-1]  # drop an in-progress trailing week
    window = weekly.iloc[-WEEKLY_BAR_COUNT:]
    bucket = window[(window >= BUCKET_LOW) & (window < BUCKET_HIGH)]

    sma200 = daily.rolling(DAILY_SMA_DAYS).mean().iloc[-1] if len(daily) >= DAILY_SMA_DAYS else float("nan")
    sma50w = window.iloc[-WEEKLY_SMA_A_WEEKS:].mean() if len(window) >= WEEKLY_SMA_A_WEEKS else float("nan")
    sma30w = window.iloc[-WEEKLY_SMA_B_WEEKS:].mean() if len(window) >= WEEKLY_SMA_B_WEEKS else float("nan")

    return {
        "weekly_bar_count": len(window),
        "weekly_start": window.index[0], "weekly_end": window.index[-1],
        "bucket_count": len(bucket),
        "sma200_daily": round(float(sma200), 2),
        "sma50_weekly": round(float(sma50w), 2),
        "sma30_weekly": round(float(sma30w), 2),
    }


def main() -> int:
    cutoff = pd.Timestamp(CUTOFF)
    pulled_at = datetime.now(timezone.utc)

    adj = metrics(download_close(auto_adjust=True), cutoff)
    unadj = metrics(download_close(auto_adjust=False), cutoff)

    lines = []

    def out(msg=""):
        print(msg)
        lines.append(str(msg))

    out("=" * 100)
    out("AAPL $272 ALERT -- EVIDENCE VERIFICATION (mkt alert id: aapl-below-272-awy9)")
    out("=" * 100)
    out(f"Source            : {SOURCE_URL}")
    out(f"Pulled at (UTC)   : {pulled_at.isoformat(timespec='seconds')}")
    out(f"Completed-bar cutoff (sliced before any resample/rolling): {cutoff.date()}")
    out(f"Bucket definition : ${BUCKET_LOW:.0f} <= weekly close < ${BUCKET_HIGH:.0f}")
    out(f"Weekly window     : last {WEEKLY_BAR_COUNT} completed W-FRI bars ending on/before cutoff")
    out("")
    out(f"{'Metric':<22}{'Alert-stated':<16}{'auto_adjust=True':<20}auto_adjust=False")
    out("-" * 100)
    out(f"{'Bucket count':<22}{STATED_BUCKET_COUNT}/{WEEKLY_BAR_COUNT:<12}"
        f"{adj['bucket_count']}/{adj['weekly_bar_count']:<17}{unadj['bucket_count']}/{unadj['weekly_bar_count']}")
    out(f"{'Daily 200-SMA':<22}${STATED_SMA200_DAILY:<15}${adj['sma200_daily']:<19}${unadj['sma200_daily']}")
    out(f"{'Weekly 50w SMA':<22}${STATED_SMA50_WEEKLY:<15}${adj['sma50_weekly']:<19}${unadj['sma50_weekly']}")
    out(f"{'Weekly 30w SMA':<22}${STATED_SMA30_WEEKLY:<15}${adj['sma30_weekly']:<19}${unadj['sma30_weekly']}")
    out("")
    out(f"Weekly window used  : {unadj['weekly_start'].date()} -> {unadj['weekly_end'].date()} "
        f"({unadj['weekly_bar_count']} bars)")
    out("")
    out("Price-level alerts (e.g. this $272 threshold) must track the actual quoted Close a "
        "human sees, so auto_adjust=False (unadjusted) is the correct convention here. "
        "Total-return backtests instead use auto_adjust=True (dividend-adjusted Close) because "
        "they simulate account growth including reinvested dividends. The two series diverge "
        "over long windows whenever dividends were paid without an offsetting split.")

    ok = (
        unadj["bucket_count"] == STATED_BUCKET_COUNT
        and unadj["weekly_bar_count"] == WEEKLY_BAR_COUNT == adj["weekly_bar_count"]
        and abs(unadj["sma200_daily"] - STATED_SMA200_DAILY) <= TOL
        and abs(unadj["sma50_weekly"] - STATED_SMA50_WEEKLY) <= TOL
        and abs(unadj["sma30_weekly"] - STATED_SMA30_WEEKLY) <= TOL
    )
    out("")
    out("=" * 100)
    out("VERDICT: " + ("REPRODUCED (unadjusted Close matches alert-stated evidence)" if ok
                        else "NOT REPRODUCED -- see per-metric deltas above"))
    out("=" * 100)

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text("\n".join(lines) + "\n")
    out(f"\nEvidence artifact written to {RESULTS_PATH}")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
