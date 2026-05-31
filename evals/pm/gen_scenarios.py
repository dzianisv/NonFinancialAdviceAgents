#!/usr/bin/env python3
"""
gen_scenarios.py — download ^GSPC history and compute deterministic ground truth
for a set of historical dates.  Writes evals/pm/scenarios/scenarios.jsonl.

Logic:
  - sp_252d_high  : rolling max of prior 252 trading-day closes (NO look-ahead)
  - sp_200d_ma    : rolling 200-day mean          (NO look-ahead)
  - drawdown_pct  : sp_close / sp_252d_high - 1
  - dip_tiers     : cumulative — tier1 if dd <= -0.07, tier2 if dd <= -0.12,
                    tier3 if dd <= -0.20
  - regime        : "risk-on" if sp_close > sp_200d_ma, else "risk-off"
  - is_quarter_end_month : month in {3, 6, 9, 12}
"""

import json
import pathlib
import sys

import numpy as np
import pandas as pd
import yfinance as yf

# ---------------------------------------------------------------------------
# Hardcoded scenarios — (label, target_date, split)
# covering: deep crashes, calm bulls, mild dip, quarter-end, near 52w high
# ---------------------------------------------------------------------------
RAW_SCENARIOS = [
    # Deep crashes
    ("GFC_peak_fall",    "2008-10-15", "train"),
    ("GFC_trough",       "2009-03-09", "holdout"),
    ("dotcom_bear",      "2002-07-23", "train"),
    ("covid_crash",      "2020-03-20", "train"),
    # Calm bull runs
    ("bull_2017",        "2017-06-15", "train"),
    ("bull_2021",        "2021-04-15", "holdout"),
    ("bull_2013_qend",   "2013-09-16", "train"),   # also near quarter-end month
    # Mild dip (Q4 2018 selloff)
    ("mild_dip_2018",    "2018-12-21", "train"),
    # Quarter-end date in bull
    ("qend_2019",        "2019-12-31", "holdout"),
    # Near 52-week high (low drawdown)
    ("near_high_2020",   "2020-01-17", "train"),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def dip_tiers(drawdown_pct: float) -> list:
    """Return list of active tier ints given drawdown_pct (negative number)."""
    tiers = []
    if drawdown_pct <= -0.07:
        tiers.append(1)
    if drawdown_pct <= -0.12:
        tiers.append(2)
    if drawdown_pct <= -0.20:
        tiers.append(3)
    return tiers


def snap_to_prior_trading_day(date: pd.Timestamp, index: pd.DatetimeIndex) -> pd.Timestamp:
    """Return `date` if it exists in `index`, else the last trading day before it."""
    if date in index:
        return date
    earlier = index[index < date]
    if len(earlier) == 0:
        raise ValueError(f"No trading day on or before {date} in data")
    snapped = earlier[-1]
    return snapped


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Download full history — period since 2001 (need 252 bars of runway before 2002)
    print("Downloading ^GSPC …")
    ticker = yf.Ticker("^GSPC")
    raw = ticker.history(start="2001-01-01", auto_adjust=True)
    if raw.empty:
        sys.exit("ERROR: yfinance returned empty data for ^GSPC")

    closes = raw["Close"].sort_index()
    closes.index = closes.index.tz_localize(None)  # strip timezone for clean comparison

    # Pre-compute rolling windows — these use *all* prior data up to each day (no look-ahead)
    # shift(1) so the window ending at day T does NOT include day T's bar
    # Actually we want trailing including current day — standard rolling includes current row
    # rolling(252).max() at position i = max of [i-251 .. i] — correct trailing window
    rolling_252_high = closes.rolling(window=252, min_periods=200).max()
    rolling_200_ma   = closes.rolling(window=200, min_periods=150).mean()

    scenarios = []
    snaps = []  # track any date snaps

    for label, date_str, split in RAW_SCENARIOS:
        target = pd.Timestamp(date_str)
        actual = snap_to_prior_trading_day(target, closes.index)
        if actual != target:
            snaps.append((label, date_str, actual.strftime("%Y-%m-%d")))

        sp_close     = float(closes.loc[actual])
        high_252     = float(rolling_252_high.loc[actual])
        ma_200       = float(rolling_200_ma.loc[actual])
        drawdown     = sp_close / high_252 - 1
        tiers        = dip_tiers(drawdown)
        regime       = "risk-on" if sp_close > ma_200 else "risk-off"
        qend         = actual.month in {3, 6, 9, 12}

        rec = {
            "label":                  label,
            "target_date":            date_str,
            "actual_date":            actual.strftime("%Y-%m-%d"),
            "split":                  split,
            "sp_close":               round(sp_close, 2),
            "sp_252d_high":           round(high_252, 2),
            "sp_200d_ma":             round(ma_200, 2),
            "drawdown_pct":           round(drawdown * 100, 2),   # stored as percent for readability
            "drawdown_frac":          round(drawdown, 6),          # raw fraction for scoring
            "expected_dip_tiers":     tiers,
            "expected_regime":        regime,
            "is_quarter_end_month":   qend,
        }
        scenarios.append(rec)

    # Write JSONL
    out_dir = pathlib.Path(__file__).parent / "scenarios"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "scenarios.jsonl"
    with open(out_path, "w") as f:
        for s in scenarios:
            f.write(json.dumps(s) + "\n")

    print(f"\nWrote {len(scenarios)} scenarios → {out_path}\n")

    # Print table
    col_w = [20, 12, 10, 10, 10, 10, 16, 10, 8]
    headers = ["label", "actual_date", "sp_close", "52w_high", "dd_%", "200d_ma", "dip_tiers", "regime", "qend?"]
    sep = "  ".join("-" * w for w in col_w)
    header_row = "  ".join(h.ljust(w) for h, w in zip(headers, col_w))
    print(header_row)
    print(sep)
    for s in scenarios:
        row = [
            s["label"].ljust(col_w[0]),
            s["actual_date"].ljust(col_w[1]),
            f"{s['sp_close']:>9.2f} ",
            f"{s['sp_252d_high']:>9.2f} ",
            f"{s['drawdown_pct']:>+8.2f}% ",
            f"{s['sp_200d_ma']:>9.2f} ",
            str(s["expected_dip_tiers"]).ljust(col_w[6]),
            s["expected_regime"].ljust(col_w[7]),
            str(s["is_quarter_end_month"]).ljust(col_w[8]),
        ]
        print("  ".join(row))

    if snaps:
        print("\nDate snaps (no bar on target date → snapped to prior trading day):")
        for label, orig, snapped in snaps:
            print(f"  {label}: {orig} → {snapped}")
    else:
        print("\nNo date snaps — all target dates had bars.")


if __name__ == "__main__":
    main()
