#!/usr/bin/env python3
"""
trend-scout entry_timing.py — list-level ENTRY TIMING + fundamental-acceleration radar.

Educational, not financial advice.

This script is DESCRIPTIVE trend context for an existing candidate list (where is the
name vs its 200d/50d, what's the invalidation level). It does NOT discover new ideas.

*** BACKTEST RESULT — DO NOT USE AS A RETURN-PREDICTIVE FILTER (2026-07-21) ***
The BUY_NOW vs WAIT_RECLAIM gate FAILED Law #0 (backtests/entry_gate_backtest.py,
1993-2026, ~180-name universe). BUY_NOW did NOT beat WAIT_RECLAIM on forward returns;
at 12mo it INVERTED (BUY_NOW 22.1% vs WAIT_RECLAIM 27.4%). As a monthly strategy it
underperformed simply holding the whole universe on BOTH Sharpe (0.82 vs 0.89) and
drawdown (-56% vs -49%), and stayed 100% invested through every crash (the per-name
gate is not a portfolio risk gate). Conclusion: this is a constant long-tilt on a
survivorship-biased winners list, not a timing edge. Use the verdicts ONLY as human-
readable trend context + invalidation levels, NEVER to rank, gate, or size buys. Entry
edge (if any) comes from buying quality weakness (dip-scanner) + PORTFOLIO-level risk
(regime-detection/sizing), not from this momentum state.

Fundamental fields are sourced from yfinance and are point-in-time-UNSAFE for
backtesting (survivorship/restatement risk). For rigorous historical testing,
upgrade to point-in-time vendors like Sharadar or SimFin.

Any live action from this output must be routed through multi-lens-quorum and
then pass the skeptic gate before execution.
"""
import argparse
import json
import os
import sys
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import yfinance as yf

HERE = os.path.dirname(os.path.abspath(__file__))
TA_DIR = os.path.abspath(os.path.join(HERE, "..", "..", "analyse-technical", "scripts"))
FUND_DIR = os.path.abspath(os.path.join(HERE, "..", "..", "stocks-advisor", "scripts"))
for p in (TA_DIR, FUND_DIR):
    if p not in sys.path:
        sys.path.append(p)

from theme_radar import fetch, ret  # noqa: E402
from ta import ma_slope, rsi, support_resistance, weinstein_stage  # noqa: E402
from fundamentals import fundamentals as fetch_fundamentals  # noqa: E402

UNAVAILABLE = "UNAVAILABLE"
UNKNOWN = "UNKNOWN"


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def _to_float(x):
    try:
        v = float(x)
        return None if np.isnan(v) else v
    except Exception:
        return None


def _pct_vs(price, ma):
    if price is None or ma in (None, 0):
        return None
    return (price / ma - 1.0) * 100.0


def _format_money(x):
    return f"${x:.2f}" if isinstance(x, (int, float)) and np.isfinite(x) else UNAVAILABLE


def _extract_revenue_from_frame(df):
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return None

    names = {
        "total revenue",
        "totalrevenue",
        "revenue",
        "operating revenue",
        "operatingrevenue",
        "net sales",
    }

    row_key = None
    for idx in df.index:
        norm = str(idx).strip().lower().replace("_", " ")
        norm2 = norm.replace(" ", "")
        if norm in names or norm2 in {n.replace(" ", "") for n in names}:
            row_key = idx
            break

    ser = None
    if row_key is not None:
        ser = pd.to_numeric(df.loc[row_key], errors="coerce")
    else:
        col_key = None
        for col in df.columns:
            norm = str(col).strip().lower().replace("_", " ")
            norm2 = norm.replace(" ", "")
            if norm in names or norm2 in {n.replace(" ", "") for n in names}:
                col_key = col
                break
        if col_key is not None:
            ser = pd.to_numeric(df[col_key], errors="coerce")

    if ser is None:
        return None

    ser = ser.dropna()
    if ser.empty:
        return None

    idx = pd.to_datetime(ser.index, errors="coerce")
    valid = ~idx.isna()
    ser = ser[valid]
    idx = idx[valid]
    if len(ser) == 0:
        return None

    ser.index = idx
    ser = ser.sort_index()
    ser = ser[~ser.index.duplicated(keep="last")]
    return ser


def quarterly_revenue_series(symbol):
    t = yf.Ticker(symbol)
    for attr in ("quarterly_financials", "quarterly_income_stmt"):
        try:
            frame = getattr(t, attr, None)
            if callable(frame):
                frame = frame()
        except Exception:
            frame = None
        ser = _extract_revenue_from_frame(frame)
        if ser is not None and len(ser) >= 3:
            return ser
    return None


def revenue_acceleration(symbol):
    ser = quarterly_revenue_series(symbol)
    if ser is None or len(ser) < 3:
        return UNKNOWN, None, None, None, None

    # Prefer YoY growth acceleration when enough quarterly history exists.
    # Spec fallback: if fewer than 8 quarters are available, use QoQ growth acceleration.
    s = ser.astype(float)
    eps = 0.01  # 1 percentage-point tolerance = FLAT

    if len(s) >= 8:
        prev_base = s.iloc[-5]
        prior_base = s.iloc[-6]
        if prev_base and prior_base:
            recent = s.iloc[-1] / prev_base - 1.0
            prior = s.iloc[-2] / prior_base - 1.0
            diff = recent - prior
            if diff > eps:
                return "ACCELERATING", "YoY", recent, prior, s
            if diff < -eps:
                return "DECELERATING", "YoY", recent, prior, s
            return "FLAT", "YoY", recent, prior, s

    prev = s.iloc[-2]
    prior2 = s.iloc[-3]
    if prev and prior2:
        recent = s.iloc[-1] / prev - 1.0
        prior = s.iloc[-2] / prior2 - 1.0
        diff = recent - prior
        if diff > eps:
            return "ACCELERATING", "QoQ_FALLBACK", recent, prior, s
        if diff < -eps:
            return "DECELERATING", "QoQ_FALLBACK", recent, prior, s
        return "FLAT", "QoQ_FALLBACK", recent, prior, s

    return UNKNOWN, None, None, None, s


def entry_verdict(price, ma50, ma200, slope_200d, pct_vs_50d, rsi14, stage, rs_6m):
    if any(v is None for v in (price, ma50, ma200, pct_vs_50d, rsi14, stage, rs_6m)):
        return UNAVAILABLE, UNAVAILABLE, UNAVAILABLE, UNAVAILABLE

    uptrend_intact = price > ma200 and slope_200d == "rising"
    extended = (pct_vs_50d > 15.0) or (rsi14 > 70.0) or (stage == 3)

    if price <= ma200 or slope_200d == "falling":
        verdict = "WAIT_RECLAIM"
        entry_trigger = f"close above 200d ({_format_money(ma200)})"
        entry_zone = entry_trigger
    elif uptrend_intact and extended:
        verdict = "BUY_PULLBACK"
        lo, hi = ma50 * 0.99, ma50 * 1.01
        entry_zone = f"{_format_money(lo)}-{_format_money(hi)}"
        entry_trigger = f"pullback to 50d around {_format_money(ma50)}"
    elif uptrend_intact and (0.0 <= pct_vs_50d <= 15.0) and (40.0 <= rsi14 <= 65.0) and stage == 2 and rs_6m > 0:
        verdict = "BUY_NOW"
        lo = min(price, ma50 * 1.01)
        hi = max(price, ma50 * 1.03)
        entry_zone = f"{_format_money(lo)}-{_format_money(hi)}"
        entry_trigger = f"trend intact above rising 200d ({_format_money(ma200)})"
    else:
        # Tie-break rule for mixed signals:
        # if trend is intact but any caution flag exists (extension or non-positive RS),
        # classify as BUY_PULLBACK; otherwise BUY_NOW. If trend not intact -> WAIT_RECLAIM.
        if uptrend_intact:
            if extended or rs_6m <= 0 or rsi14 > 65 or stage != 2:
                verdict = "BUY_PULLBACK"
                lo, hi = ma50 * 0.99, ma50 * 1.01
                entry_zone = f"{_format_money(lo)}-{_format_money(hi)}"
                entry_trigger = f"pullback to 50d around {_format_money(ma50)}"
            else:
                verdict = "BUY_NOW"
                lo = min(price, ma50 * 1.01)
                hi = max(price, ma50 * 1.03)
                entry_zone = f"{_format_money(lo)}-{_format_money(hi)}"
                entry_trigger = f"trend intact above rising 200d ({_format_money(ma200)})"
        else:
            verdict = "WAIT_RECLAIM"
            entry_trigger = f"close above 200d ({_format_money(ma200)})"
            entry_zone = entry_trigger

    # Invalidation policy: use a close below the 200d MA for all verdicts.
    invalidation = f"close below 200d ({_format_money(ma200)})"
    return verdict, entry_zone, invalidation, entry_trigger


def composite_score(row):
    """
    0-100 composite weights:
    - 35% trend regime & entry cleanliness (BUY_NOW strongest, WAIT_RECLAIM weakest)
    - 20% relative strength (rs_6m weighted more than rs_3m)
    - 15% extension quality (non-extended setups score higher)
    - 30% fundamentals (rev/earnings growth + acceleration boost/penalty)
    """
    verdict = row.get("entry_verdict")
    if verdict == UNAVAILABLE:
        return 0.0

    rs3 = _to_float(row.get("rs_3m"))
    rs6 = _to_float(row.get("rs_6m"))
    pct50 = _to_float(row.get("pct_vs_50d"))
    rev = _to_float(row.get("revenue_growth"))
    epsg = _to_float(row.get("earnings_growth"))
    accel = row.get("accel")

    trend_pts = {"BUY_NOW": 35.0, "BUY_PULLBACK": 24.0, "WAIT_RECLAIM": 6.0}.get(verdict, 0.0)

    rs_pts = 0.0
    if rs6 is not None:
        rs_pts += _clamp((rs6 + 0.15) / 0.30, 0.0, 1.0) * 12.0
    if rs3 is not None:
        rs_pts += _clamp((rs3 + 0.10) / 0.20, 0.0, 1.0) * 8.0

    ext_pts = 0.0
    if pct50 is not None:
        if 0.0 <= pct50 <= 15.0:
            ext_pts = 15.0
        elif pct50 < 0.0:
            ext_pts = 10.0
        else:
            ext_pts = max(0.0, 15.0 - min(15.0, pct50 - 15.0))

    fund_pts = 0.0
    if rev is not None:
        fund_pts += _clamp(rev / 30.0, 0.0, 1.0) * 8.0
    if epsg is not None:
        fund_pts += _clamp(epsg / 30.0, 0.0, 1.0) * 8.0
    fund_pts += {
        "ACCELERATING": 14.0,
        "FLAT": 8.0,
        "DECELERATING": 2.0,
        "UNKNOWN": 6.0,
    }.get(accel, 6.0)

    penalty = 0.0
    if verdict == "WAIT_RECLAIM":
        penalty += 10.0
    if accel == "DECELERATING":
        penalty += 4.0

    total = trend_pts + rs_pts + ext_pts + fund_pts - penalty
    return round(_clamp(total, 0.0, 100.0), 1)


def _num_or_unavailable(v, nd=2):
    f = _to_float(v)
    if f is None:
        return UNAVAILABLE
    return round(f, nd)


def build_rows(tickers):
    universe = sorted(set(tickers + ["SPY"]))
    close = fetch(universe, "3y")

    if "SPY" not in close.columns:
        raise RuntimeError("SPY missing from downloaded data.")

    spy = close["SPY"].dropna()
    spy3, spy6 = ret(spy, 63), ret(spy, 126)

    rows = []
    for symbol in tickers:
        row = {
            "symbol": symbol,
            "rs_3m": UNAVAILABLE,
            "rs_6m": UNAVAILABLE,
            "pct_vs_200d": UNAVAILABLE,
            "pct_vs_50d": UNAVAILABLE,
            "rsi14": UNAVAILABLE,
            "weinstein_stage": UNAVAILABLE,
            "ma200_slope": UNAVAILABLE,
            "revenue_growth": UNAVAILABLE,
            "earnings_growth": UNAVAILABLE,
            "accel": UNKNOWN,
            "accel_method": UNAVAILABLE,
            "entry_verdict": UNAVAILABLE,
            "entry_zone": UNAVAILABLE,
            "entry_trigger": UNAVAILABLE,
            "invalidation": UNAVAILABLE,
            "score": 0.0,
            "status": "ok",
        }

        try:
            f = fetch_fundamentals(symbol, period="1y")
            row["revenue_growth"] = _num_or_unavailable(f.get("revenue_growth"), nd=1)
            row["earnings_growth"] = _num_or_unavailable(f.get("earnings_growth"), nd=1)
        except Exception as e:
            row["status"] = f"fundamentals_unavailable: {type(e).__name__}: {e}"

        try:
            accel, method, _, _, _ = revenue_acceleration(symbol)
            row["accel"] = accel
            row["accel_method"] = method if method else UNAVAILABLE
        except Exception:
            row["accel"] = UNKNOWN
            row["accel_method"] = UNAVAILABLE

        if symbol not in close.columns:
            row["status"] = "price_unavailable: ticker not returned by yfinance"
            rows.append(row)
            continue

        s = close[symbol].dropna()
        if len(s) < 210:
            row["status"] = f"price_unavailable: insufficient history ({len(s)} bars)"
            rows.append(row)
            continue

        price = _to_float(s.iloc[-1])
        ma50_s = s.rolling(50).mean()
        ma200_s = s.rolling(200).mean()
        ma50 = _to_float(ma50_s.iloc[-1])
        ma200 = _to_float(ma200_s.iloc[-1])

        rsi_s = rsi(s, 14).dropna()
        rsi14 = _to_float(rsi_s.iloc[-1]) if len(rsi_s) else None

        weekly_close = s.resample("W").last().dropna()
        weekly_30w = weekly_close.rolling(30).mean()
        stage = None
        try:
            stage = int(weinstein_stage(weekly_close, weekly_30w))
        except Exception:
            stage = None

        slope_200d = ma_slope(ma200_s, n=10)

        rs3_raw = ret(s, 63)
        rs6_raw = ret(s, 126)
        rs3 = (rs3_raw - spy3) if (rs3_raw is not None and spy3 is not None) else None
        rs6 = (rs6_raw - spy6) if (rs6_raw is not None and spy6 is not None) else None

        pct200 = _pct_vs(price, ma200)
        pct50 = _pct_vs(price, ma50)

        try:
            support, _ = support_resistance(s)
            support = _to_float(support)
        except Exception:
            support = None

        verdict, entry_zone, invalidation, trigger = entry_verdict(
            price=price,
            ma50=ma50,
            ma200=ma200,
            slope_200d=slope_200d,
            pct_vs_50d=pct50,
            rsi14=rsi14,
            stage=stage,
            rs_6m=rs6,
        )

        row.update(
            {
                # RS definition mirrors theme_radar: ticker return minus SPY return.
                "rs_3m": _num_or_unavailable(rs3, nd=4),
                "rs_6m": _num_or_unavailable(rs6, nd=4),
                "pct_vs_200d": _num_or_unavailable(pct200, nd=2),
                "pct_vs_50d": _num_or_unavailable(pct50, nd=2),
                "rsi14": _num_or_unavailable(rsi14, nd=1),
                "weinstein_stage": stage if stage is not None else UNAVAILABLE,
                "ma200_slope": slope_200d if slope_200d in {"rising", "falling", "flat"} else UNAVAILABLE,
                "entry_verdict": verdict,
                "entry_zone": entry_zone,
                "entry_trigger": trigger,
                "invalidation": invalidation,
                "swing_support": _num_or_unavailable(support, nd=2),
            }
        )

        row["score"] = composite_score(row)
        rows.append(row)

    rows.sort(key=lambda x: x.get("score", 0), reverse=True)
    return rows


def print_table(rows):
    print(f"\nENTRY TIMING RADAR  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 140)
    print(
        f"{'SYM':<7}{'SCORE':>7}  {'VERDICT':<13}{'RS6':>8}{'%>200d':>9}{'%>50d':>8}"
        f"{'RSI14':>7}{'STG':>5} {'SLOPE200':>9} {'ACCEL':>13}  {'ENTRY_ZONE':<24} {'INVALIDATION':<24}"
    )
    print("-" * 140)
    for r in rows:
        print(
            f"{r['symbol']:<7}{r['score']:>7.1f}  {r['entry_verdict']:<13}{str(r['rs_6m']):>8}"
            f"{str(r['pct_vs_200d']):>9}{str(r['pct_vs_50d']):>8}{str(r['rsi14']):>7}"
            f"{str(r['weinstein_stage']):>5} {str(r['ma200_slope']):>9} {str(r['accel']):>13}  "
            f"{r['entry_zone']:<24} {r['invalidation']:<24}"
        )
    print("-" * 140)
    print("Momentum/trend is a timing gate only; route candidates to multi-lens-quorum + skeptic.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", required=True, help="Comma-separated symbols, e.g. NVDA,MU,ACN")
    ap.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = ap.parse_args()

    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    if not tickers:
        sys.exit("ERROR: --tickers is empty")

    rows = build_rows(tickers)

    out = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "benchmark": "SPY",
        "rows": rows,
    }

    if args.json:
        print(json.dumps(out, indent=2))
    else:
        print_table(rows)


if __name__ == "__main__":
    main()
