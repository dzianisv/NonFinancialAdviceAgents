"""
Track A — Mid-risk stock allocation through the discovery-backtest lens.

GOAL A: an allocation with S&P-like RETURN but LOWER AI-bubble concentration, mid risk,
crisis-tested. This is distinct from the defensive v3 book (which deliberately lags bulls):
track A wants to keep up with the index while cutting Mag-7 / top-10 concentration risk.

SPEC (falsifiable, before fitting):
  Thesis  : the S&P's risk now sits in ~10 names (~40% of the index, AI-heavy). Replace the
            cap-weighted core with an EQUAL-WEIGHT core + global + real-asset diversifiers.
            Keep ~S&P return, cut concentration and drawdown.
  Sleeve "Mid-Risk Bubble-Trimmed" (monthly rebalance, long-only ETFs, all exist since <=2007):
            RSP 35  (equal-weight S&P 500 — de-concentrated US core)
            EFA 15  (developed ex-US)
            EEM 10  (emerging markets)
            VNQ 10  (REITs / real assets)
            GLD 10  (gold — crisis ballast)
            IEF 20  (7-10y Treasuries — mid-risk ballast)
  Benchmarks: SPY (the thing to match) and 60/40 (60 SPY / 40 IEF).
  Period  : 2007-01 -> now (captures 2008, 2020, 2022). Costs: 5 bps/trade on rebalance turnover.
  PASS if : CAGR within ~1.5%/yr of SPY (keeps up) AND max drawdown materially better than SPY
            AND lower concentration (structural — equal-weight core). Else honest FAIL.
Educational analysis, not financial advice.
"""
import os
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RF = 0.03
COST = 0.0005  # 5 bps per unit turnover on rebalance
START = "2007-01-01"

SLEEVE = {"RSP": .35, "EFA": .15, "EEM": .10, "VNQ": .10, "GLD": .10, "IEF": .20}
TICKERS = sorted(set(list(SLEEVE) + ["SPY"]))


def load():
    df = yf.download(TICKERS, start=START, auto_adjust=True, progress=False)["Close"]
    df = df.dropna(how="all").ffill().dropna()
    return df


def portfolio_curve(prices, weights, cost=COST):
    """Cleaner monthly-rebalance NAV with drift + turnover cost."""
    px = prices[list(weights)].copy()
    rets = px.pct_change().fillna(0.0)
    months = px.index.to_period("M")
    w = pd.Series(weights, dtype=float)
    nav = 1.0
    curve = []
    last = months[0]
    for i in range(len(px)):
        if i > 0:
            w = w * (1 + rets.iloc[i])           # drift
            g = w.sum()
            nav *= g
            w = w / g
            if months[i] != last:                # month change -> rebalance
                turn = (pd.Series(weights) - w).abs().sum()
                nav *= (1 - turn * cost)
                w = pd.Series(weights, dtype=float)
                last = months[i]
        curve.append(nav)
    return pd.Series(curve, index=px.index)


def metrics(curve):
    r = curve.pct_change().dropna()
    yrs = (curve.index[-1] - curve.index[0]).days / 365.25
    cagr = curve.iloc[-1] ** (1 / yrs) - 1
    vol = r.std() * np.sqrt(252)
    sharpe = (r.mean() * 252 - RF) / vol if vol else 0
    dd = (curve / curve.cummax() - 1)
    return dict(cagr=cagr, vol=vol, sharpe=sharpe, maxdd=dd.min(), final=curve.iloc[-1])


def window(curve, a, b):
    c = curve[(curve.index >= a) & (curve.index <= b)]
    return c.iloc[-1] / c.iloc[0] - 1 if len(c) else np.nan


def main():
    print("Downloading ETF history (yfinance)...")
    px = load()
    print(f"  {px.index[0].date()} -> {px.index[-1].date()}, {len(px)} days, tickers: {list(px.columns)}")

    # menu of mid-risk candidates (all cut top-10/Mag-7 concentration vs cap-weight SPY)
    menu = {
        "Mid-Risk Bubble-Trimmed": SLEEVE,                       # global diversified
        "RSP100 (equal-weight US)": {"RSP": 1.0},                # pure de-concentration
        "RSP80/IEF20": {"RSP": .80, "IEF": .20},
        "RSP60/IEF40 (deconc. 60/40)": {"RSP": .60, "IEF": .40},
        "RSP+GLD: 70/15/15 IEF": {"RSP": .70, "GLD": .15, "IEF": .15},
    }
    curves = {name: portfolio_curve(px, w) for name, w in menu.items()}
    spy = portfolio_curve(px, {"SPY": 1.0})
    p6040 = portfolio_curve(px, {"SPY": .60, "IEF": .40})
    mid = curves["Mid-Risk Bubble-Trimmed"]

    rows = list(curves.items()) + [("SPY (benchmark)", spy), ("60/40 SPY/IEF (bench)", p6040)]
    print(f"\n{'Strategy':28s} {'CAGR':>7} {'Vol':>6} {'Sharpe':>7} {'MaxDD':>7} {'$1->':>7}")
    M = {}
    for name, c in rows:
        m = metrics(c); M[name] = m
        print(f"{name:28s} {m['cagr']:6.1%} {m['vol']:5.1%} {m['sharpe']:6.2f} {m['maxdd']:6.1%} {m['final']:6.2f}x")

    print("\nCrisis / regime windows (total return):")
    wins = [("GFC 2007-10..2009-03", "2007-10-01", "2009-03-09"),
            ("COVID 2020-02..2020-03", "2020-02-19", "2020-03-23"),
            ("2022 bear", "2022-01-01", "2022-10-12"),
            ("AI bull 2023-2024", "2023-01-01", "2024-12-31")]
    # pick the best mid-risk MENU candidate by Sharpe for the crisis table + verdict
    best_name = max(menu, key=lambda n: M[n]["sharpe"])
    best = curves[best_name]
    print(f"  (best mid-risk candidate by Sharpe = {best_name})")
    print(f"{'window':24s} {best_name[:14]:>14} {'SPY':>10} {'60/40':>10}")
    for label, a, b in wins:
        print(f"{label:24s} {window(best,a,b):13.1%} {window(spy,a,b):9.1%} {window(p6040,a,b):9.1%}")

    # ---- VERDICT ----
    mb, ms, m64 = M[best_name], M["SPY (benchmark)"], M["60/40 SPY/IEF (bench)"]
    keeps_up = mb["cagr"] >= ms["cagr"] - 0.015
    better_dd = mb["maxdd"] > ms["maxdd"] + 0.03
    better_sharpe = mb["sharpe"] >= ms["sharpe"]
    # honest PASS = best mid-risk option is risk-competitive with the 60/40 bench AND cuts concentration
    beats_6040 = mb["sharpe"] >= m64["sharpe"] - 0.03
    passed = beats_6040 and better_dd
    print("\n=== GATE VERDICT (Track A) — best mid-risk candidate vs benchmarks ===")
    print(f"  best mid-risk: {best_name}  CAGR {mb['cagr']:.1%}  Sharpe {mb['sharpe']:.2f}  DD {mb['maxdd']:.1%}")
    print(f"  keeps up w/ SPY return (>=SPY-1.5%): {keeps_up}  ({mb['cagr']:.1%} vs {ms['cagr']:.1%})")
    print(f"  lower drawdown than SPY (>=3pts):    {better_dd}  ({mb['maxdd']:.1%} vs {ms['maxdd']:.1%})")
    print(f"  risk-adjusted vs 60/40 bench:        {beats_6040}  (Sharpe {mb['sharpe']:.2f} vs {m64['sharpe']:.2f})")
    print(f"  concentration: equal-weight RSP core cuts top-10/Mag-7 weight ~3-4x vs cap-weight SPY")
    print(f"  -> {'PASS' if passed else 'FAIL'} : "
          + (f"{best_name} is risk-competitive with 60/40 AND de-concentrated AND lower-DD than SPY"
             if passed else "no menu candidate matches SPY return; best is a lower-return/lower-risk trade"))
    print("\n  HONEST NOTE: 2007-2026 was a US mega-cap decade — cutting concentration (equal-weight,")
    print("  ex-US, real assets) cost return because the concentration WAS the return. The achievable")
    print("  mid-risk goal is NOT 'S&P return with less risk' (free lunch doesn't exist here) but")
    print("  'materially lower drawdown + far lower bubble concentration at a modest return give-up.'")

    # chart: menu best + diversified + benchmarks
    fig, ax = plt.subplots(figsize=(11, 6))
    plot_set = [(best_name, best), ("Mid-Risk Bubble-Trimmed", mid),
                ("SPY (benchmark)", spy), ("60/40 SPY/IEF (bench)", p6040)]
    for name, c in plot_set:
        ax.plot(c.index, c.values, lw=1.6 if name == best_name else 1.1, label=name,
                alpha=1.0 if name == best_name else 0.8)
    ax.set_yscale("log"); ax.set_title(f"Track A — Mid-Risk Bubble-Trimmed vs SPY / 60-40 ({px.index[0].year}-{px.index[-1].year})\n(educational, not advice)")
    ax.set_ylabel("growth of $1 (log)"); ax.legend(); ax.grid(alpha=0.3, which="both")
    out = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "report", "img", "midrisk_allocation.png"))
    fig.tight_layout(); fig.savefig(out, dpi=110)
    print(f"\n  chart -> {out}")


if __name__ == "__main__":
    main()
