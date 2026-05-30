#!/usr/bin/env python3
"""
Dip-Tranche Strategy Backtest  (2020-01-01 → today)
=====================================================
Simulates three deployment strategies for a $1M portfolio across VOO, QQQ, VXUS:

  Strategy A – Dip-Tranche (50 / 30 / 20)
    Bucket 1 (50% = $500K): lump-sum on day 1
    Bucket 2 (30% = $300K): DCA over 18 months, weekly instalments
    Bucket 3 (20% = $200K): tiered dip reserve
      Tier 1 (20% of reserve): 4 sub-tranches at price & time triggers
      Tier 2 (30% of reserve): 4 sub-tranches
      Tier 3 (50% of reserve): 4 sub-tranches
    Undeployed reserve earns money-market yield (~4% annualised, accrued weekly).

  Strategy B – Lump Sum:  100% deployed on day 1.
  Strategy C – Pure DCA:  18-month equal weekly instalments of full $1M.

Per-symbol trigger calibration:
  VOO  (S&P 500):     Tier triggers × 1.0  (baseline)
  QQQ  (Nasdaq-100):  Tier triggers × 1.4  (higher β)
  VXUS (International): same as VOO

Charts saved as <SYMBOL>_backtest.png in the working directory.
"""

import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ── Try installing yfinance if missing ──────────────────────────────────────
try:
    import yfinance as yf
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance", "-q"])
    import yfinance as yf

# ─────────────────────────────  CONFIG  ─────────────────────────────────────
PORTFOLIO       = 1_000_000
START           = "2020-01-01"
END             = "2026-05-28"
DCA_MONTHS      = 18            # length of DCA bucket
MM_YIELD_ANNUAL = 0.04          # money-market rate on idle reserve cash
COOLDOWN_WEEKS  = 3             # min weeks between any two sub-tranche fills
MAX_REARMS_PER_YEAR = 2         # how many times per year tiers can be re-armed

LUMP_PCT  = 0.50
DCA_PCT   = 0.30
RES_PCT   = 0.20

TIER1_SHARE = 0.20   # fraction of reserve
TIER2_SHARE = 0.30
TIER3_SHARE = 0.50   # must sum to 1.0

# Base triggers (VOO)
BASE_T1 = [-0.070, -0.085, -0.100]   # 3 price levels; 4th is time-based
BASE_T2 = [-0.120, -0.140, -0.160]
BASE_T3 = [-0.200, -0.250, -0.300]
BASE_REARM = -0.050   # recover above this → re-arm

SYMBOLS = {
    "VOO": {
        "name":   "Vanguard S&P 500 ETF",
        "mult":   1.0,
        "color":  "#4f81bd",
    },
    "QQQ": {
        "name":   "Invesco Nasdaq-100 ETF",
        "mult":   1.40,
        "color":  "#c0504d",
    },
    "VXUS": {
        "name":   "Vanguard Total International ETF",
        "mult":   1.0,
        "color":  "#9bbb59",
    },
}


def scaled_triggers(mult: float) -> dict:
    """Scale all tier thresholds by mult (deeper triggers for higher-β assets)."""
    return {
        "t1": [v * mult for v in BASE_T1],
        "t2": [v * mult for v in BASE_T2],
        "t3": [v * mult for v in BASE_T3],
        "t1_weeks": 2,
        "t2_weeks": 3,
        "t3_weeks": 4,
        "rearm": BASE_REARM * mult,
    }


# ─────────────────────────────  DATA  ───────────────────────────────────────
def fetch(symbol: str) -> pd.DataFrame:
    print(f"  Downloading {symbol} …", end=" ", flush=True)
    df = yf.Ticker(symbol).history(start=START, end=END, interval="1wk", auto_adjust=True)
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df = df[["Close"]].dropna()
    print(f"{len(df)} weekly bars")
    return df


# ─────────────────────────────  ENGINE  ─────────────────────────────────────
def run_strategy(df: pd.DataFrame, cfg: dict, symbol: str) -> dict:
    """Simulate the dip-tranche strategy and return a result dict."""
    closes  = df["Close"].values
    dates   = df.index
    n       = len(closes)
    trg     = scaled_triggers(cfg["mult"])

    # Dollar allocations
    lump_amt  = PORTFOLIO * LUMP_PCT
    dca_total = PORTFOLIO * DCA_PCT
    res_total = PORTFOLIO * RES_PCT
    dca_weekly = dca_total / (DCA_MONTHS * 4.33)

    t1_amt = res_total * TIER1_SHARE
    t2_amt = res_total * TIER2_SHARE
    t3_amt = res_total * TIER3_SHARE

    # Sub-tranche amounts: 4 equal pieces per tier
    tranche_usd = {}
    for tier, pool in [(1, t1_amt), (2, t2_amt), (3, t3_amt)]:
        for sub in range(4):
            tranche_usd[(tier, sub)] = pool / 4.0

    # State
    shares       = lump_amt / closes[0]   # deploy lump sum immediately
    res_cash     = res_total              # reserve (earns MM yield while idle)
    dca_cash     = dca_total             # DCA bucket
    fired        = set()                  # (tier, sub) pairs already deployed
    tier_bar     = {}                     # bar index when tier first triggered
    last_buy     = -COOLDOWN_WEEKS
    rearms_yr    = 0
    cur_year     = dates[0].year
    mm_weekly    = (1 + MM_YIELD_ANNUAL) ** (1 / 52) - 1

    portfolio_vals = np.zeros(n)
    reserve_vals   = np.zeros(n)
    trades         = []

    # Log lump-sum entry
    trades.append(dict(date=dates[0], tier=0, sub=0, reason="lump_sum",
                       price=closes[0], amount=lump_amt,
                       shares=lump_amt / closes[0]))

    dca_end = min(int(DCA_MONTHS * 4.33), n)

    for i, (date, price) in enumerate(zip(dates, closes)):
        yr = date.year
        if yr != cur_year:
            cur_year  = yr
            rearms_yr = 0

        # Rolling 52-week high (up to bar i)
        h52 = closes[max(0, i - 52): i + 1].max()
        dd  = (price - h52) / h52   # ≤ 0

        # ── Money-market yield on idle reserve ───────────────────────────
        res_cash *= (1 + mm_weekly)

        # ── DCA bucket ───────────────────────────────────────────────────
        if 0 < i < dca_end and dca_cash > 0:
            buy = min(dca_weekly, dca_cash)
            shares    += buy / price
            dca_cash  -= buy
            trades.append(dict(date=date, tier=-1, sub=i, reason="dca",
                               price=price, amount=buy, shares=buy / price))

        # ── Re-arm check ─────────────────────────────────────────────────
        if dd > trg["rearm"] and fired and rearms_yr < MAX_REARMS_PER_YEAR:
            fired    = set()
            tier_bar = {}
            rearms_yr += 1

        # ── Tier logic ───────────────────────────────────────────────────
        def fire(tier, sub, reason):
            nonlocal res_cash, shares, last_buy
            key = (tier, sub)
            if key in fired or res_cash < 1:
                return False
            amt = min(tranche_usd[key], res_cash)
            sh  = amt / price
            shares   += sh
            res_cash -= amt
            fired.add(key)
            last_buy = i
            trades.append(dict(date=date, tier=tier, sub=sub, reason=reason,
                               price=price, amount=amt, shares=sh))
            return True

        ok = (i - last_buy) >= COOLDOWN_WEEKS

        for sub_i, thr in enumerate(trg["t1"]):
            if ok and dd <= thr:
                if fire(1, sub_i, f"price_t1_{sub_i}"):
                    ok = False
                    tier_bar.setdefault(1, i)

        if 1 in tier_bar and ok:
            if (i - tier_bar[1]) >= trg["t1_weeks"] and dd <= trg["t1"][0]:
                if fire(1, 3, "time_t1"):
                    ok = False

        for sub_i, thr in enumerate(trg["t2"]):
            if ok and dd <= thr:
                if fire(2, sub_i, f"price_t2_{sub_i}"):
                    ok = False
                    tier_bar.setdefault(2, i)

        if 2 in tier_bar and ok:
            if (i - tier_bar[2]) >= trg["t2_weeks"] and dd <= trg["t2"][0]:
                if fire(2, 3, "time_t2"):
                    ok = False

        for sub_i, thr in enumerate(trg["t3"]):
            if ok and dd <= thr:
                if fire(3, sub_i, f"price_t3_{sub_i}"):
                    ok = False
                    tier_bar.setdefault(3, i)

        if 3 in tier_bar and ok:
            if (i - tier_bar[3]) >= trg["t3_weeks"] and dd <= trg["t3"][0]:
                fire(3, 3, "time_t3")

        portfolio_vals[i] = shares * price + res_cash + dca_cash
        reserve_vals[i]   = res_cash

    return dict(dates=dates, closes=closes, portfolio=portfolio_vals,
                reserve=reserve_vals, trades=trades, trg=trg,
                res_total=res_total, final_res_cash=res_cash)


def run_lumpsum(df: pd.DataFrame) -> np.ndarray:
    closes = df["Close"].values
    shares = PORTFOLIO / closes[0]
    return shares * closes


def run_dca(df: pd.DataFrame) -> np.ndarray:
    closes    = df["Close"].values
    n         = len(closes)
    n_weeks   = min(int(DCA_MONTHS * 4.33), n)
    weekly    = PORTFOLIO / n_weeks
    shares, cash = 0.0, float(PORTFOLIO)
    out = np.zeros(n)
    for i, price in enumerate(closes):
        if i < n_weeks and cash > 0:
            buy = min(weekly, cash)
            shares += buy / price
            cash   -= buy
        out[i] = shares * price + cash
    return out


# ─────────────────────────────  METRICS  ─────────────────────────────────────
def metrics(vals: np.ndarray, dates) -> dict:
    total_ret = (vals[-1] - PORTFOLIO) / PORTFOLIO
    yrs       = (dates[-1] - dates[0]).days / 365.25
    cagr      = (vals[-1] / PORTFOLIO) ** (1 / yrs) - 1
    run_max   = np.maximum.accumulate(vals)
    max_dd    = ((vals - run_max) / run_max).min()
    return dict(end=vals[-1], total_ret=total_ret, cagr=cagr, max_dd=max_dd)


# ─────────────────────────────  REPORT  ─────────────────────────────────────
def print_report(symbol: str, cfg: dict, res: dict, lump: np.ndarray, dca: np.ndarray):
    dates = res["dates"]
    sm = metrics(res["portfolio"], dates)
    lm = metrics(lump,            dates)
    dm = metrics(dca,             dates)

    dip_trades  = [t for t in res["trades"] if t["tier"] > 0]
    deployed    = sum(t["amount"] for t in dip_trades)
    undeployed  = res["final_res_cash"]
    total_cost  = sum(t["amount"] for t in res["trades"] if t["tier"] >= 0)
    total_sh    = sum(t["shares"] for t in res["trades"] if t["tier"] >= 0)
    avg_cb      = total_cost / total_sh if total_sh > 0 else 0
    last_px     = res["closes"][-1]

    tier_cnt = {}
    for t in dip_trades:
        tier_cnt[t["tier"]] = tier_cnt.get(t["tier"], 0) + 1

    trg = res["trg"]
    print(f"\n{'═'*66}")
    print(f"  {symbol}  ·  {cfg['name']}")
    print(f"  Period: {dates[0].date()} → {dates[-1].date()}"
          f"  ({(dates[-1]-dates[0]).days/365.25:.1f} yrs)")
    print(f"  Tier triggers (% from 52w high):")
    print(f"    T1: {[f'{v:.1%}' for v in trg['t1']]}  (β-mult {cfg['mult']:.1f})")
    print(f"    T2: {[f'{v:.1%}' for v in trg['t2']]}")
    print(f"    T3: {[f'{v:.1%}' for v in trg['t3']]}")
    print(f"{'─'*66}")
    print(f"  {'Metric':<28}{'Strategy':>11}{'Lump Sum':>11}{'DCA 18m':>11}")
    print(f"{'─'*66}")
    print(f"  {'End value':<28}${sm['end']:>9,.0f}  ${lm['end']:>9,.0f}  ${dm['end']:>9,.0f}")
    print(f"  {'Total return':<28}{sm['total_ret']:>10.1%}  {lm['total_ret']:>9.1%}  {dm['total_ret']:>9.1%}")
    print(f"  {'CAGR':<28}{sm['cagr']:>10.1%}  {lm['cagr']:>9.1%}  {dm['cagr']:>9.1%}")
    print(f"  {'Max portfolio drawdown':<28}{sm['max_dd']:>10.1%}  {lm['max_dd']:>9.1%}  {dm['max_dd']:>9.1%}")
    print(f"{'─'*66}")
    print(f"  Strategy detail:")
    print(f"    Last price:              ${last_px:>8.2f}")
    print(f"    Avg cost basis (all):    ${avg_cb:>8.2f}")
    print(f"    Unrealised gain/loss:    {(last_px - avg_cb) / avg_cb:>8.1%} per share")
    print(f"    Reserve deployed:        ${deployed:>8,.0f} / ${res['res_total']:,.0f}"
          f"  ({deployed/res['res_total']:.0%})")
    print(f"    MM cash still earning:   ${undeployed:>8,.0f}")
    print(f"    Dip sub-tranches fired:  {len(dip_trades)}")
    for tier in sorted(tier_cnt):
        print(f"      Tier {tier}: {tier_cnt[tier]} / 4 sub-tranches fired")
    print(f"{'═'*66}")

    # Dip trade log
    if dip_trades:
        print(f"\n  Dip entries for {symbol}:")
        print(f"  {'Date':<12} {'Tier':>4} {'Sub':>4} {'Reason':<16} {'Price':>8} {'Amount':>10}")
        print(f"  {'─'*12} {'─'*4} {'─'*4} {'─'*16} {'─'*8} {'─'*10}")
        for t in dip_trades:
            print(f"  {str(t['date'].date()):<12} {t['tier']:>4} {t['sub']:>4} "
                  f"{t['reason']:<16} ${t['price']:>7.2f} ${t['amount']:>9,.0f}")


# ─────────────────────────────  PLOT  ───────────────────────────────────────
def plot(symbol: str, cfg: dict, res: dict, lump: np.ndarray, dca: np.ndarray):
    dates  = res["dates"]
    closes = res["closes"]
    trg    = res["trg"]
    color  = cfg["color"]

    # Rolling 52-week high
    h52 = pd.Series(closes, index=dates).rolling(52, min_periods=1).max().values
    dd_pct = (closes - h52) / h52 * 100

    fig, axes = plt.subplots(3, 1, figsize=(14, 15), sharex=True)
    fig.suptitle(f"{symbol} — {cfg['name']}  |  Dip-Tranche Backtest 2020–2026",
                 fontsize=13, fontweight="bold", y=0.995)

    # ── Panel 1: price + entry markers ──────────────────────────────────
    ax = axes[0]
    ax.plot(dates, closes, color=color, linewidth=1.6, label="Weekly close")
    ax.plot(dates, h52,    color="#aaa", linewidth=1, linestyle="--", alpha=0.7,
            label="52-week high")

    tier_colors = {1: "#00b4d8", 2: "#f4a261", 3: "#e63946"}
    plotted = set()
    dip_trades = [t for t in res["trades"] if t["tier"] > 0]
    for t in dip_trades:
        tc    = tier_colors[t["tier"]]
        lbl   = f"Tier {t['tier']}" if t["tier"] not in plotted else ""
        ax.scatter(t["date"], t["price"], color=tc, s=80, zorder=5, label=lbl)
        plotted.add(t["tier"])

    ax.set_ylabel("Price ($)", fontsize=10)
    ax.set_title("Price Chart + Dip Entry Points", fontsize=10)
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(True, alpha=0.25)

    # ── Panel 2: portfolio comparison ───────────────────────────────────
    ax = axes[1]
    ax.plot(dates, res["portfolio"] / 1e6, color="#00b4d8", linewidth=2.2,
            label="Dip-Tranche Strategy")
    ax.plot(dates, lump / 1e6, color="#f4a261", linewidth=1.5, linestyle="--",
            label="Lump Sum")
    ax.plot(dates, dca / 1e6, color="#57cc99", linewidth=1.5, linestyle="-.",
            label="Pure DCA (18m)")
    ax.axhline(1.0, color="#888", linewidth=0.7, linestyle=":")
    ax.set_ylabel("Portfolio Value ($M)", fontsize=10)
    ax.set_title("Portfolio Value: Strategy vs Benchmarks", fontsize=10)
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(True, alpha=0.25)

    # ── Panel 3: drawdown + tier lines ──────────────────────────────────
    ax = axes[2]
    ax.fill_between(dates, dd_pct, 0, where=(dd_pct < 0),
                    color="#e63946", alpha=0.35, label="Drawdown from 52w high")
    ax.plot(dates, dd_pct, color="#e63946", linewidth=0.9)

    tier_line_colors = (
        [(trg["t1"][i], "#00b4d8") for i in range(3)] +
        [(trg["t2"][i], "#f4a261") for i in range(3)] +
        [(trg["t3"][i], "#e63946") for i in range(3)]
    )
    for lvl, lc in tier_line_colors:
        ax.axhline(lvl * 100, color=lc, linewidth=0.8, linestyle="--", alpha=0.65)

    ax.set_ylabel("Drawdown (%)", fontsize=10)
    ax.set_xlabel("Date", fontsize=10)
    ax.set_title("Drawdown vs Tier Trigger Levels", fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.25)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_major_locator(mdates.YearLocator())

    plt.tight_layout(rect=[0, 0, 1, 0.995])
    out = Path(f"report/img/{symbol}_backtest.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Chart saved → {out}")


# ─────────────────────────────  SUMMARY TABLE  ───────────────────────────────
def summary_table(results: dict):
    print(f"\n{'═'*72}")
    print(f"  SUMMARY — All symbols, Dip-Tranche Strategy")
    print(f"{'─'*72}")
    print(f"  {'Symbol':<6} {'CAGR':>8} {'Total Ret':>10} {'End Val':>12} "
          f"{'MaxDD':>8} {'Reserve%':>10}")
    print(f"{'─'*72}")
    for sym, (res, lump, dca, cfg) in results.items():
        m = metrics(res["portfolio"], res["dates"])
        dep_pct = (res["res_total"] - res["final_res_cash"]) / res["res_total"]
        print(f"  {sym:<6} {m['cagr']:>8.1%} {m['total_ret']:>10.1%} "
              f"  ${m['end']:>10,.0f} {m['max_dd']:>8.1%} {dep_pct:>9.0%}")
    print(f"{'═'*72}")


# ─────────────────────────────  MAIN  ───────────────────────────────────────
def main():
    print("\nDip-Tranche Strategy Backtest")
    print(f"Period: {START} → {END}  |  Portfolio: ${PORTFOLIO:,.0f}\n")

    out_dir = Path(".")
    all_results = {}

    for symbol, cfg in SYMBOLS.items():
        print(f"\n── {symbol} ──────────────────────────────────────────")
        df   = fetch(symbol)
        res  = run_strategy(df, cfg, symbol)
        lump = run_lumpsum(df)
        dca  = run_dca(df)

        print_report(symbol, cfg, res, lump, dca)
        plot(symbol, cfg, res, lump, dca)

        all_results[symbol] = (res, lump, dca, cfg)

    summary_table(all_results)
    print("\nDone. PNG charts saved in current directory.\n")


if __name__ == "__main__":
    main()
