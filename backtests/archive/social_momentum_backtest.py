"""
Social/Momentum Stock Picking Backtest
Strategies A and B vs VOO baseline
"""

import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# ── Config ──────────────────────────────────────────────────────────────────
START          = "2019-07-01"
BACKTEST_START = "2020-01-01"
END            = "2026-05-27"
CAPITAL        = 1_000_000
RISK_FREE      = 0.04
CHART_PATH     = "report/img/social_momentum_backtest.png"

UNIVERSE = [
    "AAPL","MSFT","GOOGL","AMZN","META","NVDA","TSLA","JPM","V","MA",
    "UNH","HD","COST","NFLX","ADBE","CRM","NOW","INTU","QCOM","AVGO",
    "AMD","TXN","MU","LRCX","AMAT","KLAC","MRVL","ORCL","CRWD","NET",
    "ZS","DDOG","SNOW","SHOP","MELI","SE","PYPL","SQ","ROKU","UBER",
    "LYFT","ABNB","DASH","COIN","RBLX","U","PLTR","SOFI"
]

# ── Download price data ──────────────────────────────────────────────────────
print("Downloading price data...")
raw = yf.download(UNIVERSE + ["VOO"], start=START, end=END,
                  auto_adjust=True, progress=False)

# Handle multi-level columns from yfinance
if isinstance(raw.columns, pd.MultiIndex):
    prices = raw["Close"]
else:
    prices = raw

# Drop tickers with insufficient data in backtest window
available = []
for t in UNIVERSE:
    if t in prices.columns:
        count = prices[t].loc[BACKTEST_START:].notna().sum()
        if count > 60:
            available.append(t)

print(f"Available tickers: {len(available)}/{len(UNIVERSE)}")

px = prices[available + (["VOO"] if "VOO" in prices.columns else [])].ffill()

# Trading days in backtest window
bt_px = px.loc[BACKTEST_START:END]
trading_days = bt_px.index

# Monthly rebalance dates: last trading day of each calendar month
monthly_dates = (
    pd.Series(trading_days, index=trading_days)
    .resample("M")
    .last()
    .dropna()
    .values
)
monthly_dates = pd.DatetimeIndex(monthly_dates)

def safe_price(series, date):
    """Return last available price on or before date."""
    sub = series.loc[:date].dropna()
    return sub.iloc[-1] if len(sub) > 0 else np.nan

def lookback_price(series, date, days):
    """Return price ~`days` trading days before date."""
    sub = series.loc[:date].dropna()
    if len(sub) < days:
        return np.nan
    return sub.iloc[-days]

# ── Strategy A: Large-Cap Momentum Screen ──────────────────────────────────
def strategy_a(px, monthly_dates, available, capital):
    # We'll track share quantities
    holdings = {}   # ticker -> shares
    equity_by_date = {}

    for i, date in enumerate(monthly_dates):
        # Value current portfolio
        if holdings:
            curr_val = sum(
                holdings[t] * safe_price(px[t], date)
                for t in holdings
            )
        else:
            curr_val = capital

        # Score stocks
        scores = {}
        for t in available:
            try:
                p_now = safe_price(px[t], date)
                p_1m  = lookback_price(px[t], date, 21)
                p_3m  = lookback_price(px[t], date, 63)
                p_6m  = lookback_price(px[t], date, 126)
                sma50 = px[t].loc[:date].dropna().iloc[-50:].mean() if len(px[t].loc[:date].dropna()) >= 50 else np.nan

                if any(np.isnan([p_now, p_1m, p_3m, p_6m, sma50])):
                    continue
                if p_now <= sma50:  # trend filter
                    continue

                r1 = p_now / p_1m - 1
                r3 = p_now / p_3m - 1
                r6 = p_now / p_6m - 1
                score = 0.30 * r1 + 0.40 * r3 + 0.30 * r6
                scores[t] = score
            except Exception:
                continue

        top10 = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:10]
        if not top10:
            equity_by_date[date] = curr_val
            continue

        alloc = curr_val / len(top10)
        holdings = {}
        for t in top10:
            p = safe_price(px[t], date)
            if p > 0 and not np.isnan(p):
                holdings[t] = alloc / p

        equity_by_date[date] = curr_val

    # Build daily equity curve
    vals = []
    last_holdings = {}
    hi = 0  # index into monthly_dates

    for d in trading_days:
        # Update holdings on rebalance dates
        while hi < len(monthly_dates) and monthly_dates[hi] <= d:
            # Recalculate holdings at this monthly date
            md = monthly_dates[hi]
            if md in equity_by_date:
                # Rebuild holdings for this date
                scores = {}
                for t in available:
                    try:
                        p_now = safe_price(px[t], md)
                        p_1m  = lookback_price(px[t], md, 21)
                        p_3m  = lookback_price(px[t], md, 63)
                        p_6m  = lookback_price(px[t], md, 126)
                        sma50 = px[t].loc[:md].dropna().iloc[-50:].mean() if len(px[t].loc[:md].dropna()) >= 50 else np.nan
                        if any(np.isnan([p_now, p_1m, p_3m, p_6m, sma50])):
                            continue
                        if p_now <= sma50:
                            continue
                        r1 = p_now / p_1m - 1
                        r3 = p_now / p_3m - 1
                        r6 = p_now / p_6m - 1
                        scores[t] = 0.30*r1 + 0.40*r3 + 0.30*r6
                    except Exception:
                        continue
                top10 = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:10]
                if top10:
                    cv = equity_by_date[md]
                    alloc = cv / len(top10)
                    last_holdings = {}
                    for t in top10:
                        p = safe_price(px[t], md)
                        if p > 0 and not np.isnan(p):
                            last_holdings[t] = alloc / p
            hi += 1

        if last_holdings:
            v = sum(
                last_holdings[t] * safe_price(px[t], d)
                for t in last_holdings
            )
            vals.append(v if v > 0 else (vals[-1] if vals else capital))
        else:
            vals.append(vals[-1] if vals else capital)

    return pd.Series(vals, index=trading_days, dtype=float)


# ── Strategy B: High-Momentum Volatility-Adjusted ──────────────────────────
def strategy_b(px, monthly_dates, available, capital):
    rebalance_holdings = {}  # date -> holdings dict

    curr_val = capital
    prev_holdings = {}

    for i, date in enumerate(monthly_dates):
        if prev_holdings:
            curr_val = sum(
                prev_holdings[t] * safe_price(px[t], date)
                for t in prev_holdings
            )

        mom = {}
        vol = {}
        for t in available:
            try:
                series = px[t].loc[:date].dropna()
                if len(series) < 63:
                    continue
                p_now = series.iloc[-1]
                p_3m  = series.iloc[-63]
                r3 = p_now / p_3m - 1
                if np.isnan(r3):
                    continue
                daily_ret = series.iloc[-30:].pct_change().dropna()
                rv30 = daily_ret.std() * np.sqrt(252)
                if rv30 <= 0 or np.isnan(rv30):
                    continue
                mom[t] = r3
                vol[t] = rv30
            except Exception:
                continue

        top8 = sorted(mom.keys(), key=lambda x: mom[x], reverse=True)[:8]
        if not top8:
            rebalance_holdings[date] = prev_holdings
            continue

        inv_vols = {t: 1.0 / vol[t] for t in top8 if t in vol}
        total_inv = sum(inv_vols.values())
        weights = {t: iv / total_inv for t, iv in inv_vols.items()}

        new_holdings = {}
        for t in top8:
            p = safe_price(px[t], date)
            w = weights.get(t, 1.0 / len(top8))
            if p > 0 and not np.isnan(p):
                new_holdings[t] = (curr_val * w) / p

        rebalance_holdings[date] = new_holdings
        prev_holdings = new_holdings

    # Build daily equity curve
    vals = []
    current_h = {}
    ri = 0
    rdates = sorted(rebalance_holdings.keys())

    for d in trading_days:
        while ri < len(rdates) and rdates[ri] <= d:
            current_h = rebalance_holdings[rdates[ri]]
            ri += 1

        if current_h:
            v = sum(
                current_h[t] * safe_price(px[t], d)
                for t in current_h
            )
            vals.append(v if v > 0 else (vals[-1] if vals else capital))
        else:
            vals.append(vals[-1] if vals else capital)

    return pd.Series(vals, index=trading_days, dtype=float)


# ── Run strategies ───────────────────────────────────────────────────────────
print("Running Strategy A (this may take a minute)...")
eq_a = strategy_a(px, monthly_dates, available, CAPITAL)

print("Running Strategy B...")
eq_b = strategy_b(px, monthly_dates, available, CAPITAL)

# VOO lump sum
if "VOO" in px.columns:
    voo_s = px["VOO"].loc[BACKTEST_START:END].dropna()
    eq_voo = (voo_s / voo_s.iloc[0]) * CAPITAL
else:
    print("WARNING: VOO not available, using flat baseline")
    eq_voo = pd.Series([CAPITAL] * len(trading_days), index=trading_days, dtype=float)


# ── Performance metrics ──────────────────────────────────────────────────────
def calc_metrics(equity, rf=RISK_FREE):
    equity = equity.dropna()
    n_years = (equity.index[-1] - equity.index[0]).days / 365.25
    cagr = (equity.iloc[-1] / equity.iloc[0]) ** (1 / n_years) - 1

    daily_ret = equity.pct_change().dropna()
    excess = daily_ret - rf / 252
    sharpe = (excess.mean() / excess.std()) * np.sqrt(252) if excess.std() > 0 else np.nan

    rolling_max = equity.cummax()
    drawdown = (equity - rolling_max) / rolling_max
    max_dd = drawdown.min()

    total_ret = equity.iloc[-1] / equity.iloc[0] - 1
    return dict(cagr=cagr, sharpe=sharpe, max_dd=max_dd,
                total_ret=total_ret, final_val=equity.iloc[-1])


m_a   = calc_metrics(eq_a)
m_b   = calc_metrics(eq_b)
m_voo = calc_metrics(eq_voo)

# ── Print summary ────────────────────────────────────────────────────────────
print("\n" + "="*72)
print(f"{'SOCIAL / MOMENTUM BACKTEST  (2020-01-01 → 2026-05-27)':^72}")
print("="*72)
print(f"{'Strategy':<32} {'CAGR':>8} {'Sharpe':>8} {'Max DD':>8} {'Final $':>13}")
print("-"*72)

rows = [
    ("Strategy A: Momentum Screen",  m_a),
    ("Strategy B: Vol-Adj Momentum", m_b),
    ("── VOO Lump Sum (computed)",   m_voo),
]
for name, m in rows:
    print(f"{name:<32} {m['cagr']:>7.1%} {m['sharpe']:>8.2f} "
          f"{m['max_dd']:>7.1%} ${m['final_val']:>12,.0f}")

print("-"*72)
print("Published baselines:")
print(f"  {'VOO Lump Sum':<30} {'15.6%':>7}   {'0.69':>6}")
print(f"  {'Pelosi Portfolio':<30} {'20.0%':>7}   {'0.68':>6}")
print("="*72)

print(f"\nBeats VOO CAGR  (15.6%):")
print(f"  Strategy A: {'YES' if m_a['cagr'] > 0.156 else 'NO '}  ({m_a['cagr']:.1%})")
print(f"  Strategy B: {'YES' if m_b['cagr'] > 0.156 else 'NO '}  ({m_b['cagr']:.1%})")
print(f"\nBeats Pelosi CAGR (20.0%):")
print(f"  Strategy A: {'YES' if m_a['cagr'] > 0.200 else 'NO '}  ({m_a['cagr']:.1%})")
print(f"  Strategy B: {'YES' if m_b['cagr'] > 0.200 else 'NO '}  ({m_b['cagr']:.1%})")


# ── Chart ────────────────────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9),
                                gridspec_kw={"height_ratios": [3, 1]})
fig.subplots_adjust(hspace=0.35)

ax1.plot(eq_a.index,   eq_a   / CAPITAL * 100,
         label=f"Strategy A  ({m_a['cagr']:.1%} CAGR)", lw=1.8, color="#2196F3")
ax1.plot(eq_b.index,   eq_b   / CAPITAL * 100,
         label=f"Strategy B  ({m_b['cagr']:.1%} CAGR)", lw=1.8, color="#4CAF50")
ax1.plot(eq_voo.index, eq_voo / CAPITAL * 100,
         label=f"VOO Lump Sum ({m_voo['cagr']:.1%} CAGR)", lw=1.5,
         color="#FF9800", ls="--")
ax1.axhline(100, color="gray", lw=0.8, ls=":")
ax1.set_title("Social / Momentum Backtest — Growth of $1M (2020–2026)",
              fontsize=13, fontweight="bold")
ax1.set_ylabel("Portfolio Value (% of initial)")
ax1.legend(fontsize=9)
ax1.grid(alpha=0.3)

def dd_series(eq):
    return (eq - eq.cummax()) / eq.cummax() * 100

ax2.fill_between(eq_a.index,   dd_series(eq_a),   0, alpha=0.5, color="#2196F3", label="Strategy A")
ax2.fill_between(eq_b.index,   dd_series(eq_b),   0, alpha=0.4, color="#4CAF50", label="Strategy B")
ax2.fill_between(eq_voo.index, dd_series(eq_voo), 0, alpha=0.3, color="#FF9800", label="VOO")
ax2.set_title("Drawdown (%)")
ax2.set_ylabel("Drawdown (%)")
ax2.legend(fontsize=8)
ax2.grid(alpha=0.3)

plt.savefig(CHART_PATH, dpi=150, bbox_inches="tight")
print(f"\nChart saved → {CHART_PATH}")
