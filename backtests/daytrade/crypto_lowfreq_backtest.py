"""
Crypto lower-frequency trend / regime-gated momentum through the strategy-discovery-backtest GATE.

The intraday SMA-trend candidate FAILED (crypto_trend_backtest.py): ~0.8 round-trips/day ->
~250-365%/yr cost drag; hold-BTC beat it IS and OOS. The gate pointed to LOWER FREQUENCY +
REGIME GATING (trade far less; stand down in chop). This script tests that honestly.

SPEC (falsifiable, written before fitting):
  Universe : BTC/USD, ETH/USD, SOL/USD (Coinbase, 1h bars resampled to DAILY).
  Candidates (each gated independently):
    1. TSMOM   : long if trailing N-day return > 0 (time-series momentum), else flat.
    2. SMA     : long if close > SMA(N) on daily bars, else flat.
    3. REGIME  : SMA trend gated by a BTC-market regime filter (only trade when BTC>SMA200d)
                 -> stand down the whole book in crypto-winter / chop.
  Decision : on PRIOR daily close (no look-ahead; signal shifted +1 day).
  Sizing   : vol-target to TARGET_VOL annualized, capped 1x, no-trade band.
  Costs    : Coinbase taker 0.50%/side base; also maker 0.10%; 2x-cost stress.
  Horizon  : multi-day holds (this is swing/position, NOT intraday — the honest answer the
             gate steers toward for income on majors).
  Economic reason: time-series momentum is a broad, cross-asset documented premium; at daily
             frequency turnover is low enough that costs may not dominate.

GATE: PASS only if OOS edge beats hold-BTC RISK-ADJUSTED (Sharpe) AND survives 2x cost stress
AND keeps a materially smaller drawdown. "no edge found" stays a valid result.
Educational analysis, not financial advice.
"""
import os, sys, itertools
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
import crypto_data
# use persistent cache if present (survives worktree teardown)
if os.path.isdir("/tmp/bt-cache"):
    crypto_data.CACHE = "/tmp/bt-cache"
from crypto_data import load_universe

BARS_PER_YEAR = 365  # daily, 24/7
RF = 0.04
IS_END = "2023-12-31"
OOS_START = "2024-01-01"
TARGET_VOL = 0.40
BAND = 0.10


def to_daily(df):
    o = df["close"].resample("1D").last().dropna()
    return o


def banded(target, band=BAND):
    tv = target.values
    out = np.zeros_like(tv); cur = 0.0
    for i in range(len(tv)):
        if abs(tv[i] - cur) > band:
            cur = tv[i]
        out[i] = cur
    return pd.Series(out, index=target.index)


def vol_scale(close, lookback=30):
    ret = close.pct_change()
    realized = ret.rolling(lookback).std() * np.sqrt(BARS_PER_YEAR)
    return (TARGET_VOL / realized).clip(upper=1.0).shift(1).fillna(0.0)


def sig_tsmom(close, n): return (close.pct_change(n) > 0).astype(float).shift(1).fillna(0.0)
def sig_sma(close, n):   return (close > close.rolling(n).mean()).astype(float).shift(1).fillna(0.0)


def asset_net(close, signal, cost):
    w = banded((signal * vol_scale(close)).clip(0, 1))
    ret = close.pct_change().fillna(0.0)
    turnover = w.diff().abs().fillna(w.abs())
    return w * ret - turnover * cost, w


def metrics(net, w):
    net = net.dropna()
    if len(net) < 30 or net.std() == 0: return None
    eq = (1 + net).cumprod()
    yrs = len(net) / BARS_PER_YEAR
    cagr = eq.iloc[-1] ** (1 / yrs) - 1 if eq.iloc[-1] > 0 else -1
    vol = net.std() * np.sqrt(BARS_PER_YEAR)
    sharpe = (net.mean() * BARS_PER_YEAR - RF) / vol if vol > 0 else 0
    dd = (eq / eq.cummax() - 1).min()
    rt_year = (w.diff().abs().fillna(0) > 0.01).sum() / (len(w) / BARS_PER_YEAR) / 2
    return dict(cagr=cagr, vol=vol, sharpe=sharpe, maxdd=dd, exposure=w.mean(),
                rt_year=rt_year, final=eq.iloc[-1], eq=eq)


def slice_p(s, start=None, end=None):
    if start: s = s[s.index >= pd.Timestamp(start, tz="UTC")]
    if end:   s = s[s.index <= pd.Timestamp(end, tz="UTC")]
    return s


def portfolio(daily, sigfn, n, cost, regime_close=None, regime_n=200, start=None, end=None):
    nets, ws = [], []
    # market regime filter (BTC > SMA200d): a single on/off gate for the whole book
    gate = None
    if regime_close is not None:
        g = (regime_close > regime_close.rolling(regime_n).mean()).astype(float).shift(1).fillna(0.0)
        gate = g
    for sym, c in daily.items():
        cc = slice_p(c, start, end)
        if len(cc) < n + 60: continue
        s = sigfn(cc, n)
        if gate is not None:
            s = s * slice_p(gate, start, end).reindex(cc.index).fillna(0.0)
        net, w = asset_net(cc, s, cost)
        nets.append(net.rename(sym)); ws.append(w.rename(sym))
    if not nets: return None, None
    M = pd.concat(nets, axis=1).fillna(0.0).mean(axis=1)
    W = pd.concat(ws, axis=1).fillna(0.0).mean(axis=1)
    return M, W


def main():
    print("Loading Coinbase 1h bars (cached) -> resample daily ...")
    raw = load_universe(["BTC/USD", "ETH/USD", "SOL/USD"], "1h")
    daily = {k: to_daily(v) for k, v in raw.items()}
    btc = daily["BTC/USD"]

    TAKER, MAKER = 0.005, 0.001
    candidates = {
        "TSMOM": (sig_tsmom, [30, 60, 90], None),
        "SMA":   (sig_sma,   [50, 100, 200], None),
        "REGIME-SMA (BTC>200d gate)": (sig_sma, [50, 100, 200], btc),
    }

    # benchmark
    def hold(sym, start=None, end=None):
        c = slice_p(daily[sym], start, end)
        return metrics(c.pct_change().fillna(0.0), pd.Series(1.0, index=c.index))
    hold_btc_oos = hold("BTC/USD", OOS_START, None)

    results = []
    for name, (fn, ns, reg) in candidates.items():
        # IS selection by Sharpe
        is_scores = []
        for n in ns:
            net, w = portfolio(daily, fn, n, TAKER, regime_close=reg, end=IS_END)
            m = metrics(net, w) if net is not None else None
            if m: is_scores.append((n, m))
        if not is_scores: continue
        best_n = max(is_scores, key=lambda r: r[1]["sharpe"])[0]
        # OOS at chosen n
        net, w = portfolio(daily, fn, best_n, TAKER, regime_close=reg, start=OOS_START)
        oos = metrics(net, w)
        net_m, _ = portfolio(daily, fn, best_n, MAKER, regime_close=reg, start=OOS_START)
        oos_mk = metrics(net_m, _)
        net_2x, _ = portfolio(daily, fn, best_n, 2 * TAKER, regime_close=reg, start=OOS_START)
        oos_2x = metrics(net_2x, _)
        results.append((name, best_n, oos, oos_mk, oos_2x))
        print(f"\n=== {name}  (IS-best N={best_n}) ===")
        for tag, m in [("OOS taker 0.5%", oos), ("OOS maker 0.1%", oos_mk), ("OOS 2x stress", oos_2x)]:
            if m: print(f"  {tag:16s} Sharpe {m['sharpe']:5.2f}  CAGR {m['cagr']:7.1%}  "
                        f"DD {m['maxdd']:6.1%}  exp {m['exposure']:.2f}  rt/yr {m['rt_year']:.0f}")

    print(f"\n  Benchmark hold BTC (OOS): Sharpe {hold_btc_oos['sharpe']:.2f}  "
          f"CAGR {hold_btc_oos['cagr']:.1%}  DD {hold_btc_oos['maxdd']:.1%}")

    # VERDICT per candidate
    print("\n=== GATE VERDICTS ===")
    best = None
    for name, n, oos, oos_mk, oos_2x in results:
        ok = (oos and oos["sharpe"] > 0
              and oos["sharpe"] >= hold_btc_oos["sharpe"]
              and oos_2x and oos_2x["sharpe"] > 0
              and oos["maxdd"] > hold_btc_oos["maxdd"])  # less negative DD
        v = "PASS" if ok else "FAIL (no edge)"
        why = ""
        if not ok and oos:
            if oos["sharpe"] < hold_btc_oos["sharpe"]: why = "Sharpe < hold-BTC"
            elif oos_2x and oos_2x["sharpe"] <= 0: why = "dies under 2x cost"
            elif oos["maxdd"] <= hold_btc_oos["maxdd"]: why = "DD not better than hold"
        print(f"  {name:32s} N={n}  {v}  {why}")
        if ok and (best is None or oos["sharpe"] > best[2]["sharpe"]):
            best = (name, n, oos)

    # chart best (or best-Sharpe) OOS vs hold
    try:
        pick = best if best else max(results, key=lambda r: (r[2]["sharpe"] if r[2] else -9))
        name, n, oos = pick[0], pick[1], pick[2]
        fig, ax = plt.subplots(figsize=(11, 6))
        ax.plot(oos["eq"].index, oos["eq"].values, lw=1.7, label=f"{name} N={n} (net taker 0.5%)")
        ax.plot(hold_btc_oos["eq"].index, hold_btc_oos["eq"].values, lw=1.2, alpha=0.8, label="Hold BTC")
        tag = "PASS" if best else "best candidate (still FAIL)"
        ax.set_title(f"Crypto lower-freq trend — OOS {OOS_START}+ — {tag}\n(educational, not advice)")
        ax.set_ylabel("growth of $1 (net of cost)"); ax.legend(); ax.grid(alpha=0.3)
        out = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "report", "img", "crypto_lowfreq_trend.png"))
        fig.tight_layout(); fig.savefig(out, dpi=110)
        print(f"\n  chart -> {out}")
    except Exception as e:
        print("  chart skipped:", str(e)[:80])

    print("\n  " + ("PASS found — see verdicts above." if best else
          "No PASS — for majors, hold still beats systematic trend after costs (honest)."))


if __name__ == "__main__":
    main()
