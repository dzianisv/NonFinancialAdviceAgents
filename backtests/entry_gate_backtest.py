#!/usr/bin/env python3
"""
Law #0 validation backtest for the stocks-trend-screener ENTRY GATE.

Tests ONLY the price/momentum portion of entry_timing.py's entry_verdict():
BUY_NOW / BUY_PULLBACK / WAIT_RECLAIM classification.

It does NOT test revenue_acceleration()/fundamental-acceleration — that cannot be
backtested honestly on yfinance (survivorship bias + financial restatements =
look-ahead risk). That limitation is stated explicitly in the printed caveats.

Self-contained: download -> compute -> backtest -> print -> chart.
Run: /Users/engineer/.venv/bin/python3 backtests/entry_gate_backtest.py
"""
import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNIVERSE_FILE = os.path.join(
    REPO, ".agents/skills/stocks-trend-screener/scripts/universe.txt"
)
IMG_OUT = os.path.join(REPO, "report/img/entry_gate_backtest.png")

CAPITAL = 1_000_000.0
COST_ONE_WAY = 0.0005      # 5 bps each way => 10 bps round-trip, turnover-based
MIN_HISTORY = 210          # entry_timing.py len(s) < 210 skip-check
DEEP_DD_BASKET_N = 10      # anti-thesis: 10 deepest 52w drawdown names

# ---------------------------------------------------------------------------
# Signal primitives — copied VERBATIM from the source (see task spec / source files)
# ---------------------------------------------------------------------------

def rsi(close, period=14):
    close = pd.Series(close)
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    alpha = 1 / period
    avg_gain = gain.ewm(alpha=alpha, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=alpha, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)


def ma_slope(ma_series, n=10):
    ma = pd.Series(ma_series).dropna()
    if len(ma) < 2:
        return 'flat'
    actual_n = min(n, len(ma) - 1)
    if actual_n < 1:
        return 'flat'
    prev = ma.iloc[-1 - actual_n]
    curr = ma.iloc[-1]
    if prev == 0 or np.isnan(prev) or np.isnan(curr):
        return 'flat'
    val = (curr - prev) / prev * 100
    if val > 0.5:
        return 'rising'
    elif val < -0.5:
        return 'falling'
    return 'flat'


def weinstein_stage(price_series, weekly_ma_series):
    price = pd.Series(price_series)
    ma = pd.Series(weekly_ma_series)
    n = min(10, max(2, len(ma) - 1))
    slope = ma_slope(ma, n=n)
    last_price = price.iloc[-1]
    last_ma = ma.iloc[-1]
    if last_price >= last_ma and slope == 'rising':
        return 2
    if last_price < last_ma and slope == 'falling':
        return 4
    if last_price >= last_ma:
        return 3
    else:
        return 1


def ret(series, days):
    s = series.dropna()
    if len(s) < days + 1:
        return None
    return float(s.iloc[-1] / s.iloc[-1 - days] - 1.0)


def entry_verdict(price, ma50, ma200, slope_200d, pct_vs_50d, rsi14, stage, rs_6m):
    if any(v is None for v in (price, ma50, ma200, pct_vs_50d, rsi14, stage, rs_6m)):
        return "UNAVAILABLE"
    uptrend_intact = price > ma200 and slope_200d == "rising"
    extended = (pct_vs_50d > 15.0) or (rsi14 > 70.0) or (stage == 3)
    if price <= ma200 or slope_200d == "falling":
        return "WAIT_RECLAIM"
    elif uptrend_intact and extended:
        return "BUY_PULLBACK"
    elif uptrend_intact and (0.0 <= pct_vs_50d <= 15.0) and (40.0 <= rsi14 <= 65.0) and stage == 2 and rs_6m > 0:
        return "BUY_NOW"
    else:
        if uptrend_intact:
            if extended or rs_6m <= 0 or rsi14 > 65 or stage != 2:
                return "BUY_PULLBACK"
            else:
                return "BUY_NOW"
        else:
            return "WAIT_RECLAIM"


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

def load_universe():
    with open(UNIVERSE_FILE) as f:
        raw = f.read().strip()
    tickers = [t.strip().upper() for t in raw.split(",") if t.strip()]
    # de-dup preserve order
    seen = set()
    out = []
    for t in tickers:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def download(tickers):
    import yfinance as yf
    all_t = list(dict.fromkeys(tickers + ["SPY"]))
    print(f"Downloading {len(all_t)} tickers (universe {len(tickers)} + SPY) period=max ...")
    data = yf.download(all_t, period="max", interval="1d",
                       auto_adjust=False, progress=False, threads=True)
    close = data["Close"].copy()
    # keep only columns actually returned with some data
    close = close.dropna(axis=1, how="all")
    got = [c for c in close.columns]
    missing = [t for t in all_t if t not in got]
    print(f"Downloaded {len(got)}/{len(all_t)} tickers with data. "
          f"Missing/empty: {missing if missing else 'none'}")
    return close


# ---------------------------------------------------------------------------
# Signal computation (no look-ahead: uses only data up to & including date t)
# ---------------------------------------------------------------------------

def compute_verdict_for_symbol(s, spy_up_to_t):
    """s = symbol Close series up to & including t; spy_up_to_t = SPY Close up to t."""
    if len(s) < MIN_HISTORY:
        return None
    price = s.iloc[-1]
    ma50 = s.rolling(50).mean().iloc[-1]
    ma200_series = s.rolling(200).mean()
    ma200 = ma200_series.iloc[-1]
    rsi_series = rsi(s, 14).dropna()
    if len(rsi_series) == 0 or np.isnan(ma50) or np.isnan(ma200):
        return None
    rsi14 = rsi_series.iloc[-1]
    weekly_close = s.resample("W").last().dropna()
    weekly_30w = weekly_close.rolling(30).mean()
    if weekly_30w.dropna().empty:
        return None
    stage = weinstein_stage(weekly_close, weekly_30w)
    slope_200d = ma_slope(ma200_series, n=10)
    rs6_raw = ret(s, 126)
    spy6_raw = ret(spy_up_to_t, 126)
    if rs6_raw is None or spy6_raw is None:
        return None
    rs_6m = rs6_raw - spy6_raw
    pct_vs_50d = (price / ma50 - 1.0) * 100.0
    return entry_verdict(price, ma50, ma200, slope_200d, pct_vs_50d,
                         rsi14, stage, rs_6m)


# ---------------------------------------------------------------------------
# Backtest driver
# ---------------------------------------------------------------------------

def month_end_dates(index):
    """Trading-day month-end anchors (last available trading day each month)."""
    s = pd.Series(index, index=index)
    grp = s.groupby([index.year, index.month]).last()
    return pd.DatetimeIndex(sorted(grp.values))


def fwd_return(series, t_date, months):
    """Price return from close at/after t_date to close ~months later.
    Uses the first trading day >= target calendar date."""
    approx_days = int(round(months * 21))
    s = series.dropna()
    if t_date not in s.index:
        # snap to nearest prior trading day present
        pos_arr = s.index.get_indexer([t_date], method="ffill")
        if pos_arr[0] == -1:
            return None
        pos = pos_arr[0]
    else:
        pos = s.index.get_loc(t_date)
    fwd_pos = pos + approx_days
    if fwd_pos >= len(s):
        return None
    return float(s.iloc[fwd_pos] / s.iloc[pos] - 1.0)


def deep_drawdown_pct(s):
    """% below 252-trading-day high, as of last bar. Returns negative number."""
    if len(s) < 60:
        return None
    window = s.iloc[-252:] if len(s) >= 252 else s
    hi = window.max()
    if hi == 0 or np.isnan(hi):
        return None
    return float(s.iloc[-1] / hi - 1.0)  # <= 0


def run():
    tickers = load_universe()
    print(f"Universe: {len(tickers)} tickers from universe.txt")
    close = download(tickers)
    universe = [t for t in tickers if t in close.columns]
    spy = close["SPY"].dropna() if "SPY" in close.columns else None
    if spy is None:
        raise SystemExit("SPY missing — cannot compute RS or benchmark.")

    all_dates = close.index
    m_ends = month_end_dates(all_dates)
    # only months where SPY has >=210 history (so RS + benchmark defined)
    m_ends = [d for d in m_ends if len(spy.loc[:d]) >= MIN_HISTORY]
    if not m_ends:
        raise SystemExit("No evaluable months.")
    print(f"Evaluation months: {len(m_ends)}  "
          f"({pd.Timestamp(m_ends[0]).date()} -> {pd.Timestamp(m_ends[-1]).date()})")

    # ---- Panel of verdicts + forward returns ----
    # verdict_at[month_date] = {ticker: verdict}
    horizons = [1, 3, 6, 12]
    cohorts = ["BUY_NOW", "BUY_PULLBACK", "WAIT_RECLAIM"]
    # pooled forward returns: fwd[cohort][h] = list of returns
    fwd = {c: {h: [] for h in horizons} for c in cohorts}

    verdict_by_month = {}   # date -> {ticker: verdict}
    dd_by_month = {}        # date -> {ticker: dd_pct}

    for d in m_ends:
        vmap = {}
        ddmap = {}
        spy_up = spy.loc[:d]
        for t in universe:
            if t == "SPY":
                continue
            s = close[t].loc[:d].dropna()
            if len(s) < MIN_HISTORY:
                continue
            v = compute_verdict_for_symbol(s, spy_up)
            if v is None or v == "UNAVAILABLE":
                continue
            vmap[t] = v
            dd = deep_drawdown_pct(s)
            if dd is not None:
                ddmap[t] = dd
            # forward returns for the discriminative panel
            if v in cohorts:
                for h in horizons:
                    fr = fwd_return(close[t], d, h)
                    if fr is not None:
                        fwd[v][h].append(fr)
        verdict_by_month[d] = vmap
        dd_by_month[d] = ddmap

    # ---- Part 1 table ----
    def stats(lst):
        if not lst:
            return (0, np.nan, np.nan, np.nan)
        a = np.array(lst)
        return (len(a), a.mean(), np.median(a), (a > 0).mean())

    part1_lines = []
    part1_lines.append("=" * 78)
    part1_lines.append("PART 1 — DISCRIMINATIVE TEST (pooled ticker-month forward returns)")
    part1_lines.append("=" * 78)
    header = f"{'Cohort':<14}{'Horizon':>8}{'N':>8}{'Mean%':>10}{'Median%':>10}{'HitRate%':>10}"
    part1_lines.append(header)
    part1_lines.append("-" * 78)
    part1_mean = {c: {} for c in cohorts}
    for c in cohorts:
        for h in horizons:
            n, mean, med, hit = stats(fwd[c][h])
            part1_mean[c][h] = mean
            part1_lines.append(
                f"{c:<14}{str(h)+'mo':>8}{n:>8}"
                f"{mean*100 if not np.isnan(mean) else float('nan'):>10.2f}"
                f"{med*100 if not np.isnan(med) else float('nan'):>10.2f}"
                f"{hit*100 if not np.isnan(hit) else float('nan'):>10.2f}"
            )
        part1_lines.append("-" * 78)

    # ---- Part 2 strategies ----
    # Monthly returns arrays aligned to m_ends[i] -> m_ends[i+1]
    strat_names = ["BUY_NOW", "SPY_BH", "EW_UNIVERSE", "DEEP_DD_ANTI"]
    # store gross & net monthly returns and invested flag
    monthly = {s: {"gross": [], "net": [], "dates": []} for s in strat_names}
    buynow_invested_flags = []
    prev_basket = {s: set() for s in strat_names}

    def basket_month_return(basket, d_start, d_end):
        """equal-weight price return of basket held d_start->d_end."""
        rets = []
        for t in basket:
            s = close[t]
            r = period_return(s, d_start, d_end)
            if r is not None:
                rets.append(r)
        if not rets:
            return None
        return float(np.mean(rets))

    def apply_cost(prev_set, new_set, gross_ret):
        """turnover cost: names entering OR exiting pay one-way cost, weighted eq."""
        n_new = max(len(new_set), 1)
        # entering names: in new not in prev; exiting: in prev not in new
        entering = new_set - prev_set
        exiting = prev_set - new_set
        # cost as fraction of portfolio: eq-weight, so each name = 1/n_new of book.
        # entering names buy in (cost on their weight); exiting names sell out
        # (cost on prev weight). Approx: charge one-way on max(prev,new) weight.
        cost = 0.0
        cost += len(entering) * (1.0 / n_new) * COST_ONE_WAY
        n_prev = max(len(prev_set), 1)
        cost += len(exiting) * (1.0 / n_prev) * COST_ONE_WAY
        return gross_ret - cost

    for i in range(len(m_ends) - 1):
        d = m_ends[i]
        d1 = m_ends[i + 1]
        vmap = verdict_by_month[d]
        ddmap = dd_by_month[d]

        # basket selection per strategy (decided as of d, held d->d1)
        buynow = {t for t, v in vmap.items() if v == "BUY_NOW"}
        ew = set(vmap.keys())  # all with sufficient history & a computed verdict
        # deep drawdown: bottom N (most negative dd)
        dd_sorted = sorted(ddmap.items(), key=lambda kv: kv[1])
        deep = {t for t, _ in dd_sorted[:DEEP_DD_BASKET_N]}
        spy_set = {"SPY"}

        baskets = {"BUY_NOW": buynow, "SPY_BH": spy_set,
                   "EW_UNIVERSE": ew, "DEEP_DD_ANTI": deep}

        for sname in strat_names:
            b = baskets[sname]
            if sname == "BUY_NOW" and not b:
                gross = 0.0  # cash
                net = 0.0
                buynow_invested_flags.append(False)
                # exiting prior basket still costs to liquidate
                if prev_basket[sname]:
                    net = apply_cost(prev_basket[sname], set(), 0.0)
                prev_basket[sname] = set()
            else:
                if sname == "BUY_NOW":
                    buynow_invested_flags.append(True)
                gross = basket_month_return(b, d, d1)
                if gross is None:
                    gross = 0.0
                    net = 0.0
                    prev_basket[sname] = set()
                else:
                    net = apply_cost(prev_basket[sname], set(b), gross)
                    prev_basket[sname] = set(b)
            monthly[sname]["gross"].append(gross)
            monthly[sname]["net"].append(net)
            monthly[sname]["dates"].append(d1)

    # ---- equity curves & stats ----
    bt_dates = monthly["SPY_BH"]["dates"]
    rf = 0.035  # single blended risk-free — see caveat note in output
    n_months = len(bt_dates)
    years = n_months / 12.0

    def curve(rets):
        eq = CAPITAL * np.cumprod([1.0 + r for r in rets])
        return eq

    def perf(rets):
        r = np.array(rets, dtype=float)
        if len(r) == 0:
            return dict(cagr=np.nan, vol=np.nan, sharpe=np.nan, mdd=np.nan)
        eq = np.cumprod(1.0 + r)
        total = eq[-1]
        cagr = total ** (1.0 / years) - 1.0 if years > 0 else np.nan
        vol = r.std(ddof=1) * np.sqrt(12) if len(r) > 1 else np.nan
        mean_ann = r.mean() * 12
        sharpe = (mean_ann - rf) / vol if vol and not np.isnan(vol) and vol > 0 else np.nan
        peak = np.maximum.accumulate(eq)
        dd = eq / peak - 1.0
        mdd = dd.min()
        return dict(cagr=cagr, vol=vol, sharpe=sharpe, mdd=mdd)

    part2_lines = []
    part2_lines.append("=" * 96)
    part2_lines.append("PART 2 — ECONOMIC / STRATEGY TEST (monthly rebalance, $1,000,000 notional)")
    part2_lines.append(f"Period: {pd.Timestamp(bt_dates[0]).date()} -> {pd.Timestamp(bt_dates[-1]).date()}  "
                       f"({n_months} months, {years:.1f} yrs)  | risk-free (blended constant) = {rf*100:.1f}%")
    part2_lines.append("=" * 96)
    hd = (f"{'Strategy':<16}{'Basis':>7}{'CAGR%':>9}{'Vol%':>9}"
          f"{'Sharpe':>9}{'MaxDD%':>9}")
    part2_lines.append(hd)
    part2_lines.append("-" * 96)

    label_map = {"BUY_NOW": "BUY_NOW gate", "SPY_BH": "SPY buy&hold",
                 "EW_UNIVERSE": "EW universe", "DEEP_DD_ANTI": "DeepDD anti"}
    net_curves = {}
    for sname in strat_names:
        for basis in ["gross", "net"]:
            p = perf(monthly[sname][basis])
            part2_lines.append(
                f"{label_map[sname]:<16}{basis:>7}"
                f"{p['cagr']*100:>9.2f}{p['vol']*100:>9.2f}"
                f"{p['sharpe']:>9.2f}{p['mdd']*100:>9.2f}"
            )
        net_curves[sname] = curve(monthly[sname]["net"])
        part2_lines.append("-" * 96)

    invested_pct = 100.0 * np.mean(buynow_invested_flags) if buynow_invested_flags else 0.0
    part2_lines.append(f"BUY_NOW strategy invested (non-empty basket): "
                       f"{invested_pct:.1f}% of {len(buynow_invested_flags)} months "
                       f"(sat in cash {100-invested_pct:.1f}%)")

    # average basket size for BUY_NOW
    bn_sizes = [len({t for t, v in verdict_by_month[m_ends[i]].items() if v == 'BUY_NOW'})
                for i in range(len(m_ends) - 1)]
    part2_lines.append(f"BUY_NOW avg basket size when invested: "
                       f"{np.mean([x for x in bn_sizes if x > 0]) if any(bn_sizes) else 0:.1f} names")

    # ---- print everything ----
    out = []
    out += part1_lines
    out.append("")
    out += part2_lines
    out.append("")
    out += caveats(pd.Timestamp(bt_dates[0]).date(), pd.Timestamp(bt_dates[-1]).date())
    text = "\n".join(out)
    print(text)

    # ---- chart ----
    make_chart(bt_dates, net_curves, part1_mean, horizons, cohorts, label_map)
    print(f"\nChart saved: {IMG_OUT}")


def period_return(s, d_start, d_end):
    s = s.dropna()
    def price_at(d):
        if d in s.index:
            return s.loc[d]
        pos = s.index.get_indexer([d], method="ffill")[0]
        if pos == -1:
            return None
        return s.iloc[pos]
    p0 = price_at(d_start)
    p1 = price_at(d_end)
    if p0 is None or p1 is None or p0 == 0 or np.isnan(p0) or np.isnan(p1):
        return None
    return float(p1 / p0 - 1.0)


def caveats(d0, d1):
    return [
        "=" * 96,
        "CAVEATS / HONEST LIMITATIONS",
        "=" * 96,
        "(0) SCOPE: Only the PRICE/MOMENTUM entry_verdict() is tested. The",
        "    fundamental/revenue-acceleration gate (revenue_acceleration()) is NOT",
        "    tested — quarterly financials on yfinance carry survivorship bias and",
        "    restatements (look-ahead risk). A BUY_NOW here is the price-gate leg only;",
        "    the live screener also requires a fundamental leg, so live BUY_NOW is a",
        "    STRICT SUBSET of what this backtest labels BUY_NOW.",
        "(a) FORWARD-SURVIVORSHIP BIAS: universe.txt is TODAY's ~180 large/mega-cap-",
        "    tilted names — today's survivors/winners projected backward. This is NOT a",
        "    point-in-time universe; it structurally inflates ALL cohorts' returns.",
        "(b) SINGLE DATA SOURCE: yfinance only, no independent price verification.",
        "(c) THIN EARLY SAMPLES: many names (PLTR, RGTI, IONQ, COIN...) IPO'd recently,",
        "    so early-year months have far fewer eligible tickers; cohort splits are",
        "    unstable pre-2015.",
        "(d) PRICE-RETURN ONLY: Close is split-adjusted but NOT dividend-adjusted, so",
        "    all CAGRs understate total return by roughly the dividend yield (SPY ~1.3%/",
        "    yr). This applies ~symmetrically across cohorts/benchmarks, so it does NOT",
        "    bias the BUY_NOW-vs-WAIT_RECLAIM comparison, but absolute CAGRs are low.",
        "(e) MODELING CHOICE: EW-universe is monthly-rebalanced equal-weight (not a",
        "    static buy-forever), to match the rebalance cadence of the other baskets.",
        "(f) COSTS: 10bps round-trip (5bps each way) charged turnover-based on names",
        "    entering/exiting the basket each rebalance. Both gross & net reported.",
        "(g) RISK-FREE: repo convention is 4% (2020-26)/3% (2005-20)/5% (1999-2005).",
        "    A single blended 3.5% constant is used for Sharpe across the whole window",
        "    to keep the comparison clean; it applies identically to every strategy so",
        "    it does not change the RANKING, only the absolute Sharpe level.",
        f"(h) REGIME NOTE: inspect the equity curve for 2020 COVID crash, 2022 bear,",
        f"    and choppy ranges — the BUY_NOW gate goes to cash in downtrends by",
        f"    construction (price<=ma200 or slope falling => WAIT_RECLAIM), so it should",
        f"    sidestep drawdowns but also lag sharp V-recoveries. Backtest window",
        f"    {d0} -> {d1}.",
    ]


def make_chart(dates, net_curves, part1_mean, horizons, cohorts, label_map):
    os.makedirs(os.path.dirname(IMG_OUT), exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 11))
    dts = pd.to_datetime(dates)
    colors = {"BUY_NOW": "tab:green", "SPY_BH": "black",
              "EW_UNIVERSE": "tab:blue", "DEEP_DD_ANTI": "tab:red"}
    for sname, eq in net_curves.items():
        ax1.plot(dts, eq, label=label_map[sname], color=colors[sname], lw=1.6)
    ax1.set_yscale("log")
    ax1.set_title("Entry-gate backtest — equity curves (net of 10bps round-trip cost, log scale, price-return only)")
    ax1.set_ylabel("Portfolio value ($, log)")
    ax1.legend(loc="upper left")
    ax1.grid(True, which="both", alpha=0.3)

    # bar chart of mean fwd return by cohort by horizon
    x = np.arange(len(horizons))
    w = 0.25
    ccolor = {"BUY_NOW": "tab:green", "BUY_PULLBACK": "tab:orange",
              "WAIT_RECLAIM": "tab:red"}
    for i, c in enumerate(cohorts):
        vals = [part1_mean[c][h] * 100 for h in horizons]
        ax2.bar(x + (i - 1) * w, vals, w, label=c, color=ccolor[c])
    ax2.set_xticks(x)
    ax2.set_xticklabels([f"{h}mo" for h in horizons])
    ax2.axhline(0, color="gray", lw=0.8)
    ax2.set_title("Part 1 — mean forward return by cohort by horizon (pooled ticker-months)")
    ax2.set_ylabel("Mean forward return (%)")
    ax2.legend()
    ax2.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(IMG_OUT, dpi=110)
    plt.close()


if __name__ == "__main__":
    run()
