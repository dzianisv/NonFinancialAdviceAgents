#!/usr/bin/env python3
"""
Crash-Protection Backtest (2000-2026)
=====================================
Directly answers the question: "Why not just hold the S&P 500 or QQQ if we
might be in an AI bubble like the dot-com bubble?"

Compares all-equity buy & hold against a set of downside-protection / all-weather
portfolios across the two biggest bubble-burst regimes in modern history
(dot-com 2000-2002, GFC 2007-2009) plus COVID-2020 and the 2022 bond+stock drawdown.

Long, clean total-return history is obtained from Vanguard index MUTUAL FUNDS
(dividends auto-reinvested by yfinance auto_adjust) plus gold futures:
    VFINX  - S&P 500 index (since 1976)        -> US large cap
    VISVX  - Small-Cap Value index (since 1998) -> SCV tilt (Golden Butterfly)
    VUSTX  - Long-Term Treasury (since 1986)    -> long bonds
    VFITX  - Intermediate-Term Treasury         -> intermediate bonds
    GC=F   - Gold futures (since ~2000)         -> gold / real asset
    QQQ    - Nasdaq-100 ETF (since 1999)        -> the "tech/AI" comparison
Cash is modelled by accruing a time-varying T-bill rate.

Strategies:
    1. S&P 500 Buy & Hold            (the default everyone defaults to)
    2. Nasdaq-100 Buy & Hold (QQQ)   (the AI/tech-heavy default)
    3. 60/40 (S&P / Long Treasury)   (classic balanced)
    4. Permanent Portfolio           (25% stock / 25% LT bond / 25% gold / 25% cash)
    5. Golden Butterfly              (20% LC / 20% SCV / 20% LT bond / 20% cash / 20% gold)
    6. All-Weather proxy             (30% stock / 40% LT bond / 15% IT bond / 15% gold)
    7. Dual Momentum (GEM)           (absolute+relative momentum; risk-off to bonds)
    8. Trend-Following S&P (200d SMA)(hold S&P above 200d MA, else T-bills)

NOTE: educational backtest, not advice. Caveats printed at the end.
"""

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# PARAMETERS
# =============================================================================
START = '2000-01-01'
END = '2026-05-27'
INITIAL_CAPITAL = 1_000_000

# Time-varying risk-free (T-bill) assumption by era (annualised)
def rf_for(date):
    y = date.year
    if y <= 2001: return 0.055   # 2000-2001 high rates
    if y <= 2004: return 0.015   # post dot-com cuts
    if y <= 2007: return 0.045   # mid-2000s
    if y <= 2015: return 0.001   # ZIRP
    if y <= 2019: return 0.018   # gradual hikes
    if y <= 2021: return 0.001   # COVID ZIRP
    if y <= 2023: return 0.045   # hiking cycle
    return 0.043                 # 2024+

RF_AVG = 0.025  # for Sharpe across the whole period

# =============================================================================
# DATA
# =============================================================================
print("Downloading data (2000-2026)...")
TICKERS = ['VFINX', 'VISVX', 'VUSTX', 'VFITX', 'GC=F', 'QQQ']

def robust_download(tickers, **kw):
    """Download, retrying any ticker that comes back all-NaN (yfinance cache locks)."""
    import time
    raw = yf.download(tickers, **kw)
    px = raw['Close'].copy()
    for attempt in range(4):
        missing = [t for t in tickers if t not in px.columns or px[t].dropna().empty]
        if not missing:
            break
        time.sleep(2)
        r2 = yf.download(missing, **kw)
        c2 = r2['Close']
        if isinstance(c2, pd.Series):
            c2 = c2.to_frame(missing[0])
        for t in missing:
            if t in c2.columns and not c2[t].dropna().empty:
                px[t] = c2[t]
    return px

prices = robust_download(TICKERS, start='1999-06-01', end=END, auto_adjust=True, progress=False).ffill()

print(f"Raw shape: {prices.shape}")
for t in TICKERS:
    if t in prices.columns and not prices[t].dropna().empty:
        s = prices[t].dropna()
        print(f"  {t}: {s.index[0].date()} -> {s.index[-1].date()}  ({len(s)} days)")
    else:
        print(f"  {t}: MISSING")

# Build a cash index that accrues the time-varying T-bill rate (daily compounding)
cal = prices.index
cash_factor = pd.Series(1.0, index=cal)
prev = None
acc = 1.0
for d in cal:
    if prev is not None:
        days = (d - prev).days
        acc *= (1 + rf_for(d)) ** (days / 365.25)
    cash_factor[d] = acc
    prev = d
prices['CASH'] = cash_factor * 100  # arbitrary base level

# =============================================================================
# HELPERS
# =============================================================================
def compute_metrics(equity, rf=RF_AVG):
    equity = equity.dropna()
    if len(equity) < 2:
        return {'CAGR': 0, 'Sharpe': 0, 'Sortino': 0, 'MaxDD': 0, 'Calmar': 0, 'Final': np.nan}
    yrs = (equity.index[-1] - equity.index[0]).days / 365.25
    cagr = (equity.iloc[-1] / equity.iloc[0]) ** (1 / yrs) - 1 if yrs > 0 else 0
    r = equity.pct_change().dropna()
    sharpe = (r.mean() * 252 - rf) / (r.std() * np.sqrt(252)) if r.std() > 0 else 0
    downside = r[r < 0].std() * np.sqrt(252)
    sortino = (r.mean() * 252 - rf) / downside if downside > 0 else 0
    dd = (equity / equity.cummax() - 1)
    maxdd = dd.min()
    calmar = cagr / abs(maxdd) if maxdd < 0 else np.nan
    return {'CAGR': cagr, 'Sharpe': sharpe, 'Sortino': sortino,
            'MaxDD': maxdd, 'Calmar': calmar, 'Final': equity.iloc[-1]}


def month_end_dates(idx, start, end):
    mask = (idx >= start) & (idx <= end)
    sub = idx[mask]
    out = []
    for (y, m), grp in pd.Series(sub, index=sub).groupby([sub.year, sub.month]):
        out.append(grp.iloc[-1])
    return out


def static_portfolio(prices_df, weights, start, end, rebal='Y', name='Portfolio'):
    """Buy-and-hold a fixed-weight basket with periodic rebalancing.
    weights: dict ticker -> weight (must sum ~1). Daily marked, rebalanced on
    calendar (rebal='Y' annual, 'M' monthly)."""
    cols = [t for t in weights if t in prices_df.columns]
    w = np.array([weights[t] for t in cols])
    w = w / w.sum()
    px = prices_df[cols].copy()
    mask = (px.index >= start) & (px.index <= end)
    px = px[mask].dropna(how='all').ffill()
    if len(px) < 2:
        return pd.Series(dtype=float, name=name)

    # rebalance dates
    if rebal == 'Y':
        rebs = set()
        for yr, grp in px.groupby(px.index.year):
            rebs.add(grp.index[0])
    elif rebal == 'M':
        rebs = set(g.index[0] for _, g in px.groupby([px.index.year, px.index.month]))
    else:
        rebs = {px.index[0]}
    rebs.add(px.index[0])

    wmap = {t: w[j] for j, t in enumerate(cols)}
    capital = INITIAL_CAPITAL
    shares = {}
    equity = pd.Series(index=px.index, dtype=float)
    for i, d in enumerate(px.index):
        if shares:
            capital = sum(sh * px.loc[d, t] for t, sh in shares.items() if pd.notna(px.loc[d, t]))
        if d in rebs:
            avail = [t for t in cols if pd.notna(px.loc[d, t]) and px.loc[d, t] > 0]
            wsum = sum(wmap[t] for t in avail)
            shares = {}
            if wsum > 0:
                for t in avail:
                    shares[t] = capital * (wmap[t] / wsum) / px.loc[d, t]
        equity.iloc[i] = capital
    equity.name = name
    return equity


def trend_following_sp(prices_df, start, end, ticker='VFINX', name='Trend-Following S&P (200d)'):
    """Hold S&P when price > 200-day SMA, else cash. Checked at month end."""
    px = prices_df[ticker].copy()
    sma = px.rolling(200).mean()
    cash = prices_df['CASH']
    mask = (px.index >= start) & (px.index <= end)
    idx = px.index[mask]
    rebs = set(month_end_dates(prices_df.index, start, end))
    capital = INITIAL_CAPITAL
    in_mkt = True
    sh_eq = capital / px[idx[0]]
    sh_cash = 0.0
    equity = pd.Series(index=idx, dtype=float)
    for i, d in enumerate(idx):
        capital = sh_eq * px[d] + sh_cash * cash[d]
        if d in rebs and pd.notna(sma[d]):
            want = px[d] > sma[d]
            if want and not in_mkt:
                sh_eq = capital / px[d]; sh_cash = 0.0; in_mkt = True
            elif not want and in_mkt:
                sh_cash = capital / cash[d]; sh_eq = 0.0; in_mkt = False
        equity.iloc[i] = capital
    equity.name = name
    return equity


def dual_momentum_gem(prices_df, start, end, name='Dual Momentum (GEM)'):
    """Gary Antonacci's Global Equity Momentum, simplified:
    Monthly: if S&P 12m total return > T-bill 12m return -> hold the better of
    S&P (VFINX) vs intl (use QQQ as growth proxy unavailable intl long history,
    so use VFINX vs VISVX as the two risk assets); else hold long Treasury (VUSTX).
    Absolute momentum (vs cash) is the crash protection."""
    risk = ['VFINX', 'VISVX']
    safe = 'VUSTX'
    cash = 'CASH'
    rebs = month_end_dates(prices_df.index, start, end)
    mask = (prices_df.index >= start) & (prices_df.index <= end)
    idx = prices_df.index[mask]
    capital = INITIAL_CAPITAL
    holding = None
    shares = 0.0
    equity = pd.Series(index=idx, dtype=float)
    rebset = set(rebs)
    for i, d in enumerate(idx):
        if holding is not None and shares > 0:
            capital = shares * prices_df.loc[d, holding]
        if d in rebset:
            loc = prices_df.index.get_loc(d)
            if loc >= 252:
                p_now = prices_df.iloc[loc]
                p_past = prices_df.iloc[loc - 252]
                cash_ret = p_now['CASH'] / p_past['CASH'] - 1
                moms = {t: p_now[t] / p_past[t] - 1 for t in risk
                        if pd.notna(p_now[t]) and pd.notna(p_past[t]) and p_past[t] > 0}
                best = max(moms, key=moms.get) if moms else None
                if best is not None and moms[best] > cash_ret:
                    target = best
                else:
                    target = safe  # risk-off
                if target != holding:
                    holding = target
                    shares = capital / prices_df.loc[d, holding]
        equity.iloc[i] = capital
    equity.name = name
    return equity


# =============================================================================
# RUN STRATEGIES (full 2000-2026)
# =============================================================================
print("\nBuilding strategies (2000-2026)...")
strategies = {}
strategies['S&P 500 Buy&Hold'] = static_portfolio(prices, {'VFINX': 1}, START, END, 'Y', 'S&P 500 Buy&Hold')
# QQQ only from 1999-03; full-period
strategies['Nasdaq-100 (QQQ) Buy&Hold'] = static_portfolio(prices, {'QQQ': 1}, START, END, 'Y', 'Nasdaq-100 (QQQ) Buy&Hold')
strategies['60/40 (S&P/LT Bond)'] = static_portfolio(prices, {'VFINX': .6, 'VUSTX': .4}, START, END, 'Y', '60/40 (S&P/LT Bond)')
strategies['Permanent Portfolio'] = static_portfolio(prices, {'VFINX': .25, 'VUSTX': .25, 'GC=F': .25, 'CASH': .25}, START, END, 'Y', 'Permanent Portfolio')
strategies['Golden Butterfly'] = static_portfolio(prices, {'VFINX': .2, 'VISVX': .2, 'VUSTX': .2, 'CASH': .2, 'GC=F': .2}, START, END, 'Y', 'Golden Butterfly')
strategies['All-Weather (proxy)'] = static_portfolio(prices, {'VFINX': .30, 'VUSTX': .40, 'VFITX': .15, 'GC=F': .15}, START, END, 'Y', 'All-Weather (proxy)')
strategies['Dual Momentum (GEM)'] = dual_momentum_gem(prices, START, END)
strategies['Trend-Following S&P (200d)'] = trend_following_sp(prices, START, END)

# =============================================================================
# FULL-PERIOD RESULTS
# =============================================================================
print("\n" + "=" * 92)
print("FULL PERIOD 2000-2026  (start $1,000,000)")
print("=" * 92)
rows = []
for name, eq in strategies.items():
    m = compute_metrics(eq)
    rows.append({'Strategy': name,
                 'CAGR': f"{m['CAGR']*100:.1f}%",
                 'Sharpe': f"{m['Sharpe']:.2f}",
                 'Sortino': f"{m['Sortino']:.2f}",
                 'MaxDD': f"{m['MaxDD']*100:.1f}%",
                 'Calmar': f"{m['Calmar']:.2f}" if not np.isnan(m['Calmar']) else 'n/a',
                 'Final $': f"${m['Final']:,.0f}"})
full_df = pd.DataFrame(rows)
print(full_df.to_string(index=False))

# =============================================================================
# CRISIS-WINDOW ANALYSIS  (the heart of the "why not S&P/QQQ" answer)
# =============================================================================
print("\n" + "=" * 92)
print("CRISIS WINDOWS — total return & max drawdown during each bubble/crash")
print("=" * 92)
crises = [
    ('Dot-com bust', '2000-03-24', '2002-10-09'),
    ('Global Financial Crisis', '2007-10-09', '2009-03-09'),
    ('COVID crash', '2020-02-19', '2020-03-23'),
    ('2022 stocks+bonds', '2022-01-03', '2022-10-12'),
    ('Recovery to today', '2009-03-09', END),
]
for cname, cs, ce in crises:
    print(f"\n--- {cname}  ({cs} -> {ce}) ---")
    rr = []
    for name, eq in strategies.items():
        sub = eq[(eq.index >= cs) & (eq.index <= ce)].dropna()
        if len(sub) < 2:
            rr.append({'Strategy': name, 'Total Return': 'n/a', 'MaxDD': 'n/a'})
            continue
        tot = sub.iloc[-1] / sub.iloc[0] - 1
        dd = (sub / sub.cummax() - 1).min()
        rr.append({'Strategy': name,
                   'Total Return': f"{tot*100:+.1f}%",
                   'MaxDD': f"{dd*100:.1f}%"})
    print(pd.DataFrame(rr).to_string(index=False))

# =============================================================================
# DECADE: 2000-2010 — "the lost decade" for the S&P
# =============================================================================
print("\n" + "=" * 92)
print("THE LOST DECADE 2000-01-01 -> 2009-12-31  (S&P went nowhere for 10 yrs)")
print("=" * 92)
rr = []
for name, eq in strategies.items():
    sub = eq[(eq.index >= '2000-01-01') & (eq.index <= '2009-12-31')].dropna()
    if len(sub) < 2:
        rr.append({'Strategy': name, 'CAGR': 'n/a', 'Total': 'n/a', 'MaxDD': 'n/a'})
        continue
    m = compute_metrics(sub)
    rr.append({'Strategy': name,
               'CAGR': f"{m['CAGR']*100:.1f}%",
               'Total': f"{(sub.iloc[-1]/sub.iloc[0]-1)*100:+.1f}%",
               'MaxDD': f"{m['MaxDD']*100:.1f}%"})
print(pd.DataFrame(rr).to_string(index=False))

# =============================================================================
# CHART
# =============================================================================
print("\nGenerating chart...")
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 11), gridspec_kw={'height_ratios': [3, 1]})
colors = plt.cm.tab10(np.linspace(0, 1, len(strategies)))
for (name, eq), c in zip(strategies.items(), colors):
    lw = 2.2 if 'S&P 500' in name or 'Nasdaq' in name else 1.4
    ax1.plot(eq.index, eq.values, label=name, linewidth=lw, color=c)
ax1.set_yscale('log')
ax1.set_title('Crash-Protection Backtest 2000-2026: All-Equity vs Defensive Portfolios ($1M start)', fontsize=13)
ax1.set_ylabel('Portfolio Value (log scale)')
ax1.legend(loc='upper left', fontsize=8, ncol=2)
ax1.grid(True, alpha=0.3)
ax1.axhline(INITIAL_CAPITAL, color='gray', ls='--', alpha=0.5)
# shade crises
for cname, cs, ce in crises[:4]:
    ax1.axvspan(pd.Timestamp(cs), pd.Timestamp(ce), color='red', alpha=0.07)

# drawdown panel
for (name, eq), c in zip(strategies.items(), colors):
    if 'S&P 500' in name or 'Permanent' in name or 'Trend' in name or 'Nasdaq' in name:
        dd = (eq / eq.cummax() - 1) * 100
        ax2.plot(dd.index, dd.values, label=name, linewidth=1.2, color=c)
ax2.set_title('Drawdowns (selected strategies)', fontsize=11)
ax2.set_ylabel('Drawdown %')
ax2.legend(loc='lower left', fontsize=8)
ax2.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/img/crash_protection_backtest.png', dpi=150)
print("Chart saved to report/img/crash_protection_backtest.png")

# =============================================================================
# CAVEATS
# =============================================================================
print("\n" + "=" * 92)
print("CAVEATS")
print("=" * 92)
print("""
1. Mutual-fund proxies (VFINX/VUSTX/VISVX/VFITX) are total-return (divs reinvested);
   QQQ is total-return via auto_adjust. Gold (GC=F) has no yield so price = TR.
2. CASH accrues a piecewise-constant T-bill estimate, not actual SOFR/T-bill prints.
3. No transaction costs / taxes. Static portfolios rebalance annually (low turnover);
   Dual Momentum & Trend-Following trade monthly (modest turnover).
4. Dual Momentum here uses VFINX vs VISVX as the two risk assets (no long intl history
   in this basket) — a simplification of true GEM (US vs ex-US).
5. 2000-2002 'All-Weather' & 'Golden Butterfly' benefit from gold's bull run and the
   bond bull market — both tailwinds may not repeat from today's lower-yield start.
6. Survivorship/look-ahead controlled: signals use only trailing data; SMA/momentum
   computed on past prices; rebalances at month/year boundaries.
""")
print("BACKTEST COMPLETE")
