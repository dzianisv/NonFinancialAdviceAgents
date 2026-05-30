#!/usr/bin/env python3
"""
Era 2005-2020 Backtest: Testing strategies across the pre-COVID era.
Includes 2008 financial crisis, QE bull market, and late cycle.
"""

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# PARAMETERS
# =============================================================================
START = '2005-01-01'
END = '2020-01-01'
TQQQ_START = '2010-03-01'
INITIAL_CAPITAL = 1_000_000
RF_RATE = 0.03

# =============================================================================
# DATA DOWNLOAD
# =============================================================================
print("Downloading data...")

# All tickers we need
sector_tickers = ['XLK', 'XLF', 'XLE', 'XLV', 'XLI', 'XLY', 'XLP', 'XLB', 'XLU', 'QQQ']
dual_mom_tickers = ['SPY', 'QQQ', 'IWM', 'EFA', 'EEM', 'TLT', 'GLD', 'VNQ', 'HYG', 'LQD']
quality_tickers = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'JNJ', 'V', 'PG', 'HD', 'KO', 'PEP',
    'MRK', 'ABBV', 'TMO', 'ACN', 'ADBE', 'QCOM', 'TXN', 'HON', 'LOW', 'UNP',
    'CAT', 'GE', 'RTX', 'LMT', 'BA', 'IBM', 'INTC', 'CSCO', 'WMT', 'DIS',
    'CMCSA', 'VZ', 'T', 'PFE', 'AMGN', 'MDT', 'CVX', 'XOM', 'GS', 'JPM'
]
other_tickers = ['SPY', 'TQQQ', 'BIL']

all_tickers = list(set(sector_tickers + dual_mom_tickers + quality_tickers + other_tickers))
all_tickers.sort()

data = yf.download(all_tickers, start='2004-01-01', end=END, auto_adjust=True, progress=False)
prices = data['Close'].copy()
prices = prices.ffill()

print(f"Data shape: {prices.shape}")
print(f"Date range: {prices.index[0].date()} to {prices.index[-1].date()}")
print(f"Available tickers: {prices.columns.tolist()[:10]}... ({len(prices.columns)} total)")

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def compute_metrics(equity_curve, rf=RF_RATE):
    """Compute CAGR, Sharpe, Max Drawdown from an equity Series."""
    if equity_curve.empty or len(equity_curve) < 2:
        return {'CAGR': 0, 'Sharpe': 0, 'MaxDD': 0, 'Final': 0}
    
    total_days = (equity_curve.index[-1] - equity_curve.index[0]).days
    total_years = total_days / 365.25
    
    final = equity_curve.iloc[-1]
    initial = equity_curve.iloc[0]
    
    cagr = (final / initial) ** (1 / total_years) - 1 if total_years > 0 else 0
    
    daily_ret = equity_curve.pct_change().dropna()
    if len(daily_ret) > 0 and daily_ret.std() > 0:
        sharpe = (daily_ret.mean() * 252 - rf) / (daily_ret.std() * np.sqrt(252))
    else:
        sharpe = 0
    
    rolling_max = equity_curve.cummax()
    drawdown = (equity_curve - rolling_max) / rolling_max
    max_dd = drawdown.min()
    
    return {'CAGR': cagr, 'Sharpe': sharpe, 'MaxDD': max_dd, 'Final': final}


def get_monthly_dates(prices_df, start, end):
    """Get month-end dates within range."""
    mask = (prices_df.index >= start) & (prices_df.index <= end)
    monthly = prices_df[mask].resample('M').last().index
    # Map back to actual trading days
    actual_dates = []
    for m in monthly:
        subset = prices_df.index[(prices_df.index.year == m.year) & (prices_df.index.month == m.month)]
        if len(subset) > 0:
            actual_dates.append(subset[-1])
    return actual_dates


# =============================================================================
# STRATEGY 1: SPY BUY & HOLD
# =============================================================================
def strategy_spy_hold(prices_df, start, end):
    """Simple SPY buy and hold."""
    mask = (prices_df.index >= start) & (prices_df.index <= end)
    spy = prices_df.loc[mask, 'SPY'].dropna()
    equity = INITIAL_CAPITAL * (spy / spy.iloc[0])
    equity.name = 'SPY Buy&Hold'
    return equity


# =============================================================================
# STRATEGY 2: SECTOR ROTATION V4 (RANK-WEIGHTED)
# =============================================================================
def strategy_sector_rotation(prices_df, start, end):
    """Monthly sector rotation, rank-weighted top half by 3-month momentum."""
    tickers = [t for t in sector_tickers if t in prices_df.columns]
    rebal_dates = get_monthly_dates(prices_df, start, end)
    
    mask = (prices_df.index >= start) & (prices_df.index <= end)
    daily_idx = prices_df.index[mask]
    
    equity = pd.Series(index=daily_idx, dtype=float)
    capital = INITIAL_CAPITAL
    holdings = {}  # ticker -> shares
    
    prev_date = None
    for i, date in enumerate(daily_idx):
        if prev_date is not None and holdings:
            # Update capital based on price changes
            day_pnl = 0
            for t, shares in holdings.items():
                if t in prices_df.columns:
                    p_today = prices_df.loc[date, t]
                    p_yesterday = prices_df.loc[prev_date, t]
                    if pd.notna(p_today) and pd.notna(p_yesterday) and p_yesterday > 0:
                        day_pnl += shares * (p_today - p_yesterday)
            capital += day_pnl
        
        # Rebalance on rebal dates
        if date in rebal_dates:
            # Calculate 3-month (63 trading day) momentum
            lookback_idx = prices_df.index.get_loc(date)
            if lookback_idx < 63:
                equity.iloc[i] = capital
                prev_date = date
                continue
            
            mom = {}
            for t in tickers:
                p_now = prices_df.iloc[lookback_idx][t]
                p_past = prices_df.iloc[lookback_idx - 63][t]
                if pd.notna(p_now) and pd.notna(p_past) and p_past > 0:
                    mom[t] = p_now / p_past - 1
            
            if len(mom) < 2:
                equity.iloc[i] = capital
                prev_date = date
                continue
            
            # Rank and take top half
            ranked = sorted(mom.items(), key=lambda x: x[1], reverse=True)
            n_hold = len(ranked) // 2
            top = ranked[:n_hold]
            
            # Rank-weighted: weight proportional to rank (best gets highest weight)
            ranks = list(range(n_hold, 0, -1))  # n_hold, n_hold-1, ..., 1
            total_rank = sum(ranks)
            weights = {top[j][0]: ranks[j] / total_rank for j in range(n_hold)}
            
            # Allocate capital
            holdings = {}
            for t, w in weights.items():
                p = prices_df.loc[date, t]
                if pd.notna(p) and p > 0:
                    holdings[t] = (capital * w) / p
        
        equity.iloc[i] = capital
        prev_date = date
    
    equity.name = 'Sector Rotation V4'
    return equity


# =============================================================================
# STRATEGY 3: DUAL MOMENTUM TOP-1
# =============================================================================
def strategy_dual_momentum(prices_df, start, end):
    """12-1 month momentum, hold #1 pick monthly."""
    tickers = [t for t in dual_mom_tickers if t in prices_df.columns]
    rebal_dates = get_monthly_dates(prices_df, start, end)
    
    mask = (prices_df.index >= start) & (prices_df.index <= end)
    daily_idx = prices_df.index[mask]
    
    equity = pd.Series(index=daily_idx, dtype=float)
    capital = INITIAL_CAPITAL
    current_ticker = None
    shares = 0
    
    prev_date = None
    for i, date in enumerate(daily_idx):
        if prev_date is not None and current_ticker and shares > 0:
            p_today = prices_df.loc[date, current_ticker]
            p_yesterday = prices_df.loc[prev_date, current_ticker]
            if pd.notna(p_today) and pd.notna(p_yesterday) and p_yesterday > 0:
                capital += shares * (p_today - p_yesterday)
        
        if date in rebal_dates:
            # 12-1 month momentum (skip most recent month)
            lookback_idx = prices_df.index.get_loc(date)
            if lookback_idx < 252:
                equity.iloc[i] = capital
                prev_date = date
                continue
            
            mom = {}
            for t in tickers:
                p_now = prices_df.iloc[lookback_idx - 21][t]  # skip 1 month
                p_past = prices_df.iloc[lookback_idx - 252][t]  # 12 months ago
                if pd.notna(p_now) and pd.notna(p_past) and p_past > 0:
                    mom[t] = p_now / p_past - 1
            
            if mom:
                best = max(mom, key=mom.get)
                current_ticker = best
                p = prices_df.loc[date, current_ticker]
                if pd.notna(p) and p > 0:
                    shares = capital / p
                else:
                    shares = 0
        
        equity.iloc[i] = capital
        prev_date = date
    
    equity.name = 'Dual Momentum Top-1'
    return equity


# =============================================================================
# STRATEGY 4: QUALITY FACTOR TOP-15
# =============================================================================
def strategy_quality_factor(prices_df, start, end):
    """Monthly: rank by momentum + low vol composite, hold top 15 equal-weight."""
    available = [t for t in quality_tickers if t in prices_df.columns]
    rebal_dates = get_monthly_dates(prices_df, start, end)
    
    mask = (prices_df.index >= start) & (prices_df.index <= end)
    daily_idx = prices_df.index[mask]
    
    equity = pd.Series(index=daily_idx, dtype=float)
    capital = INITIAL_CAPITAL
    holdings = {}  # ticker -> shares
    
    prev_date = None
    for i, date in enumerate(daily_idx):
        if prev_date is not None and holdings:
            day_pnl = 0
            for t, sh in holdings.items():
                p_today = prices_df.loc[date, t]
                p_yesterday = prices_df.loc[prev_date, t]
                if pd.notna(p_today) and pd.notna(p_yesterday) and p_yesterday > 0:
                    day_pnl += sh * (p_today - p_yesterday)
            capital += day_pnl
        
        if date in rebal_dates:
            lookback_idx = prices_df.index.get_loc(date)
            if lookback_idx < 252:
                equity.iloc[i] = capital
                prev_date = date
                continue
            
            scores = {}
            for t in available:
                p_now = prices_df.iloc[lookback_idx][t]
                p_6m = prices_df.iloc[lookback_idx - 126][t]
                p_12m = prices_df.iloc[lookback_idx - 252][t]
                
                if pd.isna(p_now) or pd.isna(p_6m) or pd.isna(p_12m) or p_6m <= 0 or p_12m <= 0:
                    continue
                
                mom_6m = p_now / p_6m - 1
                mom_12m = p_now / p_12m - 1
                
                # 252-day volatility
                ret_series = prices_df[t].iloc[lookback_idx-252:lookback_idx+1].pct_change().dropna()
                if len(ret_series) < 100:
                    continue
                vol = ret_series.std() * np.sqrt(252)
                if vol <= 0:
                    continue
                inv_vol = 1.0 / vol
                
                scores[t] = 0.4 * mom_6m + 0.3 * mom_12m + 0.3 * inv_vol
            
            if len(scores) < 15:
                n_hold = max(1, len(scores))
            else:
                n_hold = 15
            
            ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:n_hold]
            
            # Equal weight
            holdings = {}
            w = 1.0 / n_hold
            for t, _ in ranked:
                p = prices_df.loc[date, t]
                if pd.notna(p) and p > 0:
                    holdings[t] = (capital * w) / p
        
        equity.iloc[i] = capital
        prev_date = date
    
    equity.name = 'Quality Factor Top-15'
    return equity


# =============================================================================
# STRATEGY 5: TQQQ + 200-DAY SMA
# =============================================================================
def strategy_tqqq_sma(prices_df, start, end):
    """Hold TQQQ when QQQ > 200-day SMA, else cash. Weekly check."""
    mask = (prices_df.index >= start) & (prices_df.index <= end)
    daily_idx = prices_df.index[mask]
    
    if 'TQQQ' not in prices_df.columns:
        print("  WARNING: TQQQ not available")
        return pd.Series(INITIAL_CAPITAL, index=daily_idx, name='TQQQ+SMA200')
    
    # Compute QQQ 200-day SMA
    qqq_sma200 = prices_df['QQQ'].rolling(200).mean()
    
    equity = pd.Series(index=daily_idx, dtype=float)
    capital = INITIAL_CAPITAL
    in_tqqq = False
    shares = 0
    last_check = None
    
    prev_date = None
    for i, date in enumerate(daily_idx):
        if prev_date is not None and in_tqqq and shares > 0:
            p_today = prices_df.loc[date, 'TQQQ']
            p_yesterday = prices_df.loc[prev_date, 'TQQQ']
            if pd.notna(p_today) and pd.notna(p_yesterday) and p_yesterday > 0:
                capital += shares * (p_today - p_yesterday)
        
        # Weekly check (every 5 trading days)
        if last_check is None or (i - (last_check if last_check else 0)) >= 5:
            last_check = i
            qqq_price = prices_df.loc[date, 'QQQ']
            sma_val = qqq_sma200.loc[date]
            
            if pd.notna(qqq_price) and pd.notna(sma_val):
                should_hold = qqq_price > sma_val
                
                if should_hold and not in_tqqq:
                    p = prices_df.loc[date, 'TQQQ']
                    if pd.notna(p) and p > 0:
                        shares = capital / p
                        in_tqqq = True
                elif not should_hold and in_tqqq:
                    in_tqqq = False
                    shares = 0
        
        equity.iloc[i] = capital
        prev_date = date
    
    equity.name = 'TQQQ+SMA200'
    return equity


# =============================================================================
# RUN BACKTESTS
# =============================================================================
print("\n" + "="*80)
print("RUNNING BACKTESTS: 2005-2020 ERA")
print("="*80)

print("\n1. SPY Buy & Hold...")
eq_spy = strategy_spy_hold(prices, START, END)

print("2. Sector Rotation V4...")
eq_sector = strategy_sector_rotation(prices, START, END)

print("3. Dual Momentum Top-1...")
eq_dual = strategy_dual_momentum(prices, START, END)

print("4. Quality Factor Top-15...")
eq_quality = strategy_quality_factor(prices, START, END)

print("5. TQQQ + SMA200 (2010-2020)...")
eq_tqqq = strategy_tqqq_sma(prices, TQQQ_START, END)

# =============================================================================
# RESULTS TABLE
# =============================================================================
print("\n" + "="*80)
print("MASTER RESULTS TABLE")
print("="*80)

strategies = {
    'SPY Buy&Hold': eq_spy,
    'Sector Rotation V4': eq_sector,
    'Dual Momentum Top-1': eq_dual,
    'Quality Factor Top-15': eq_quality,
    'TQQQ+SMA200 (2010-20)': eq_tqqq,
}

results = []
for name, eq in strategies.items():
    m = compute_metrics(eq)
    results.append({
        'Strategy': name,
        'CAGR': f"{m['CAGR']*100:.1f}%",
        'Sharpe': f"{m['Sharpe']:.2f}",
        'Max Drawdown': f"{m['MaxDD']*100:.1f}%",
        'Final Value': f"${m['Final']:,.0f}",
    })

results_df = pd.DataFrame(results)
print(results_df.to_string(index=False))

# =============================================================================
# SUB-PERIOD ANALYSIS
# =============================================================================
print("\n" + "="*80)
print("SUB-PERIOD ANALYSIS")
print("="*80)

periods = [
    ('2005-2007 (pre-crisis bull)', '2005-01-01', '2007-10-01'),
    ('2007-2009 (financial crisis)', '2007-10-01', '2009-03-01'),
    ('2009-2015 (recovery + QE bull)', '2009-03-01', '2015-01-01'),
    ('2015-2020 (late cycle)', '2015-01-01', '2020-01-01'),
]

for period_name, p_start, p_end in periods:
    print(f"\n--- {period_name} ---")
    period_results = []
    for name, eq in strategies.items():
        if 'TQQQ' in name and p_start < '2010-03-01':
            period_results.append({'Strategy': name, 'CAGR': 'N/A', 'MaxDD': 'N/A'})
            continue
        sub = eq[(eq.index >= p_start) & (eq.index <= p_end)]
        if len(sub) < 2:
            period_results.append({'Strategy': name, 'CAGR': 'N/A', 'MaxDD': 'N/A'})
            continue
        m = compute_metrics(sub)
        period_results.append({
            'Strategy': name,
            'CAGR': f"{m['CAGR']*100:.1f}%",
            'MaxDD': f"{m['MaxDD']*100:.1f}%",
        })
    print(pd.DataFrame(period_results).to_string(index=False))

# =============================================================================
# WIN RATE VS SPY BY YEAR
# =============================================================================
print("\n" + "="*80)
print("WIN RATE VS SPY BY YEAR")
print("="*80)

spy_annual = eq_spy.resample('Y').last().pct_change().dropna()

for name, eq in strategies.items():
    if 'TQQQ' in name:
        continue
    annual = eq.resample('Y').last().pct_change().dropna()
    # Align
    common = spy_annual.index.intersection(annual.index)
    wins = (annual[common] > spy_annual[common]).sum()
    total = len(common)
    print(f"  {name}: {wins}/{total} years beat SPY ({wins/total*100:.0f}%)")

# =============================================================================
# CHART
# =============================================================================
print("\nGenerating chart...")

fig, ax = plt.subplots(figsize=(14, 8))

for name, eq in strategies.items():
    ax.plot(eq.index, eq.values, label=name, linewidth=1.5)

ax.set_yscale('log')
ax.set_title('Era 2005-2020 Backtest: Strategy Comparison', fontsize=14)
ax.set_xlabel('Date')
ax.set_ylabel('Portfolio Value (log scale)')
ax.legend(loc='upper left', fontsize=10)
ax.grid(True, alpha=0.3)
ax.axhline(y=INITIAL_CAPITAL, color='gray', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig('report/img/era_2005_2020_backtest.png', dpi=150)
print("Chart saved to era_2005_2020_backtest.png")

print("\n" + "="*80)
print("BACKTEST COMPLETE")
print("="*80)
