"""
Post-Earnings Announcement Drift (PEAD) Proxy Strategy Backtest
Gap-Up Earnings Momentum: Enter stocks that gap up >5% on earnings day
Universe: S&P 500 large caps
Period: 2020-01-01 to 2026-05-27
"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ── Universe ──────────────────────────────────────────────────────────────────
UNIVERSE = [
    'AAPL','MSFT','GOOGL','AMZN','META','NVDA','JPM','V','MA','UNH',
    'JNJ','PG','KO','PEP','COST','HD','SBUX','DIS','NFLX','ADBE',
    'CRM','NOW','INTU','QCOM','AVGO','TXN','AMD','ORCL','CSCO','WMT',
    'AMGN','GILD','LLY','TMO','ABT','BAC','WFC','GS','MS','CVX',
    'XOM','COP','NEE','CAT','DE','HON','UPS','FDX','TSLA','PYPL',
    'SQ','ROKU','ZM','SHOP'
]

START = '2019-10-01'   # extra history for gap detection
END   = '2026-05-27'
BACKTEST_START = '2020-01-01'

INITIAL_CAPITAL = 1_000_000
MAX_POSITIONS   = 10
HOLD_DAYS       = 60
GAP_THRESHOLD   = 0.05   # 5% overnight gap
RISK_FREE_RATE  = 0.04

# Approximate earnings months per quarter (companies report ~1 month after quarter end)
# Q4 → Jan/Feb, Q1 → Apr/May, Q2 → Jul/Aug, Q3 → Oct/Nov
EARNINGS_MONTHS = {1, 2, 4, 5, 7, 8, 10, 11}

def download_data(tickers, start, end):
    print(f"Downloading price data for {len(tickers)} tickers...")
    raw = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
    if isinstance(raw.columns, pd.MultiIndex):
        close = raw['Close']
        open_ = raw['Open']
        volume = raw['Volume']
    else:
        close = raw[['Close']]
        open_ = raw[['Open']]
        volume = raw[['Volume']]
    close  = close.ffill().dropna(how='all', axis=1)
    open_  = open_.ffill().dropna(how='all', axis=1)
    volume = volume.ffill().dropna(how='all', axis=1)
    print(f"  Got data for {close.shape[1]} tickers, {close.shape[0]} days")
    return close, open_, volume

def detect_gap_up_signals(close, open_, volume):
    """
    Detect earnings gap-up signals:
    - Day must be in an earnings month
    - Overnight gap (open / prev_close - 1) > GAP_THRESHOLD
    - Volume on gap day > 1.5x 20-day avg (confirms unusual activity)
    Returns dict: date -> list of tickers with gap-up signal
    """
    print("Detecting gap-up earnings signals...")
    
    prev_close = close.shift(1)
    gap = (open_ / prev_close) - 1
    
    vol_ma20 = volume.rolling(20).mean()
    vol_ratio = volume / vol_ma20
    
    signals = {}  # date -> [tickers]
    
    dates = close.index
    for i, date in enumerate(dates):
        if date < pd.Timestamp(BACKTEST_START):
            continue
        if date.month not in EARNINGS_MONTHS:
            continue
        
        day_gap = gap.loc[date]
        day_vol = vol_ratio.loc[date]
        
        # Gap up > threshold AND volume spike
        triggered = day_gap[
            (day_gap > GAP_THRESHOLD) & (day_vol > 1.5)
        ].index.tolist()
        
        if triggered:
            signals[date] = triggered
    
    total_signals = sum(len(v) for v in signals.values())
    print(f"  Found {total_signals} gap-up signals across {len(signals)} dates")
    return signals

def run_backtest(close, signals):
    """
    Portfolio backtest:
    - On signal day+1, enter equal-weight position (up to MAX_POSITIONS)
    - Hold for HOLD_DAYS trading days
    - Rebalance to equal weight daily
    """
    print("Running backtest...")
    
    dates = close.index[close.index >= pd.Timestamp(BACKTEST_START)]
    
    portfolio_value = INITIAL_CAPITAL
    cash = INITIAL_CAPITAL
    positions = {}  # ticker -> {shares, entry_date, exit_date}
    
    portfolio_values = []
    
    # Pre-build a set of signal entry dates
    entry_signals = {}  # entry_date -> [tickers]
    for sig_date, tickers in signals.items():
        # Enter next trading day
        sig_idx = close.index.get_loc(sig_date)
        if sig_idx + 1 < len(close.index):
            entry_date = close.index[sig_idx + 1]
            if entry_date not in entry_signals:
                entry_signals[entry_date] = []
            entry_signals[entry_date].extend(tickers)
    
    for date in dates:
        # 1. Exit positions that have hit their hold period
        to_exit = []
        for ticker, pos in positions.items():
            hold = (close.index.get_loc(date) - close.index.get_loc(pos['entry_date']))
            if hold >= HOLD_DAYS:
                to_exit.append(ticker)
        
        for ticker in to_exit:
            pos = positions.pop(ticker)
            if ticker in close.columns:
                price = close.loc[date, ticker]
                if pd.notna(price):
                    cash += pos['shares'] * price
        
        # 2. Enter new positions if signals and room available
        if date in entry_signals:
            new_tickers = entry_signals[date]
            # Filter: not already in portfolio, price available
            new_tickers = [t for t in new_tickers 
                          if t not in positions 
                          and t in close.columns
                          and pd.notna(close.loc[date, t])]
            
            slots_available = MAX_POSITIONS - len(positions)
            if slots_available > 0 and new_tickers:
                # Rebalance existing positions to make room
                # Equal weight across all (current + new, up to max)
                to_enter = new_tickers[:slots_available]
                
                # Sell some existing to fund new entries if needed
                n_total = len(positions) + len(to_enter)
                n_total = min(n_total, MAX_POSITIONS)
                
                # Calculate total portfolio value
                total_val = cash
                for t, pos in positions.items():
                    if t in close.columns and pd.notna(close.loc[date, t]):
                        total_val += pos['shares'] * close.loc[date, t]
                
                # Target allocation per position
                target_per_pos = total_val / n_total if n_total > 0 else total_val
                
                # Liquidate excess from existing positions if overweight
                for t in list(positions.keys()):
                    if t in close.columns and pd.notna(close.loc[date, t]):
                        price = close.loc[date, t]
                        current_val = positions[t]['shares'] * price
                        if current_val > target_per_pos * 1.1:
                            excess_shares = (current_val - target_per_pos) / price
                            positions[t]['shares'] -= excess_shares
                            cash += excess_shares * price
                
                # Enter new positions
                for t in to_enter[:MAX_POSITIONS - len(positions)]:
                    price = close.loc[date, t]
                    alloc = min(target_per_pos, cash * 0.99)
                    if alloc > 100 and price > 0:
                        shares = alloc / price
                        positions[t] = {
                            'shares': shares,
                            'entry_date': date,
                        }
                        cash -= shares * price
        
        # 3. Mark to market
        total_val = cash
        for t, pos in positions.items():
            if t in close.columns:
                price = close.loc[date, t]
                if pd.notna(price):
                    total_val += pos['shares'] * price
        
        portfolio_values.append({'date': date, 'value': total_val, 'positions': len(positions)})
    
    pv = pd.DataFrame(portfolio_values).set_index('date')
    print(f"  Backtest complete. Final value: ${pv['value'].iloc[-1]:,.0f}")
    return pv

def calc_metrics(pv_series, rf=RISK_FREE_RATE):
    """Calculate CAGR, Sharpe, Max Drawdown"""
    values = pv_series.dropna()
    
    start_val = values.iloc[0]
    end_val   = values.iloc[-1]
    n_years   = (values.index[-1] - values.index[0]).days / 365.25
    
    cagr = (end_val / start_val) ** (1 / n_years) - 1
    
    daily_ret = values.pct_change().dropna()
    excess    = daily_ret - rf / 252
    sharpe    = excess.mean() / excess.std() * np.sqrt(252) if excess.std() > 0 else 0
    
    rolling_max = values.cummax()
    drawdown    = (values - rolling_max) / rolling_max
    max_dd      = drawdown.min()
    
    return {'CAGR': cagr, 'Sharpe': sharpe, 'MaxDD': max_dd}

def plot_results(pv, voo_pv, output_path):
    fig = plt.figure(figsize=(16, 12))
    gs  = gridspec.GridSpec(3, 2, figure=fig, hspace=0.4, wspace=0.3)
    
    ax1 = fig.add_subplot(gs[0, :])
    ax2 = fig.add_subplot(gs[1, 0])
    ax3 = fig.add_subplot(gs[1, 1])
    ax4 = fig.add_subplot(gs[2, :])
    
    # Normalize to 1
    strat_norm = pv['value'] / pv['value'].iloc[0]
    voo_norm   = voo_pv / voo_pv.iloc[0]
    
    # Align
    common = strat_norm.index.intersection(voo_norm.index)
    strat_norm = strat_norm.loc[common]
    voo_norm   = voo_norm.loc[common]
    
    # ── Plot 1: Equity Curve ─────────────────────────────────────────────────
    ax1.plot(strat_norm.index, strat_norm.values, 'steelblue', lw=2, label='PEAD Gap-Up Strategy')
    ax1.plot(voo_norm.index,   voo_norm.values,   'orange',    lw=1.5, alpha=0.8, label='VOO (Benchmark)')
    ax1.set_title('PEAD Gap-Up Earnings Momentum — Equity Curve (2020–2026)', fontsize=13, fontweight='bold')
    ax1.set_ylabel('Growth of $1')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x:.1f}'))
    
    # ── Plot 2: Drawdown ─────────────────────────────────────────────────────
    roll_max = strat_norm.cummax()
    dd = (strat_norm - roll_max) / roll_max * 100
    ax2.fill_between(dd.index, dd.values, 0, color='red', alpha=0.4)
    ax2.plot(dd.index, dd.values, 'red', lw=0.8)
    ax2.set_title('Strategy Drawdown (%)', fontsize=11)
    ax2.set_ylabel('Drawdown %')
    ax2.grid(True, alpha=0.3)
    
    # ── Plot 3: Number of Positions ──────────────────────────────────────────
    ax3.fill_between(pv.index, pv['positions'].values, 0, color='steelblue', alpha=0.4)
    ax3.set_title('Number of Active Positions', fontsize=11)
    ax3.set_ylabel('Positions')
    ax3.set_ylim(0, MAX_POSITIONS + 1)
    ax3.grid(True, alpha=0.3)
    
    # ── Plot 4: Rolling 12M Returns ──────────────────────────────────────────
    strat_ret_12m = strat_norm.pct_change(252) * 100
    voo_ret_12m   = voo_norm.pct_change(252) * 100
    ax4.plot(strat_ret_12m.index, strat_ret_12m.values, 'steelblue', lw=1.5, label='PEAD Strategy')
    ax4.plot(voo_ret_12m.index,   voo_ret_12m.values,   'orange',    lw=1.5, alpha=0.8, label='VOO')
    ax4.axhline(0, color='black', lw=0.8)
    ax4.set_title('Rolling 12-Month Return (%)', fontsize=11)
    ax4.set_ylabel('Return %')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.suptitle('Post-Earnings Announcement Drift (PEAD) — Gap-Up Momentum Strategy', 
                 fontsize=15, fontweight='bold', y=1.01)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Chart saved to {output_path}")

def main():
    print("=" * 65)
    print("  PEAD Gap-Up Earnings Momentum Backtest")
    print("  2020-01-01 to 2026-05-27  |  $1,000,000 starting capital")
    print("=" * 65)
    
    # Download data
    close, open_, volume = download_data(UNIVERSE, START, END)
    
    # Download VOO benchmark
    print("Downloading VOO benchmark...")
    voo_raw = yf.download('VOO', start=BACKTEST_START, end=END, auto_adjust=True, progress=False)
    voo_close = voo_raw['Close'].squeeze()
    
    # Detect signals
    signals = detect_gap_up_signals(close, open_, volume)
    
    # Run backtest
    pv = run_backtest(close, signals)
    
    # Metrics
    m_strat = calc_metrics(pv['value'])
    
    # VOO metrics
    voo_val = INITIAL_CAPITAL * (voo_close / voo_close.iloc[0])
    m_voo   = calc_metrics(voo_val)
    
    # Pelosi baseline
    pelosi = {'CAGR': 0.200, 'Sharpe': 0.68, 'MaxDD': -0.30}  # approximate
    
    # Print results
    print()
    print("=" * 65)
    print("  PERFORMANCE SUMMARY")
    print("=" * 65)
    print(f"{'Metric':<22} {'PEAD Strategy':>14} {'VOO':>12} {'Pelosi':>10}")
    print("-" * 65)
    print(f"{'CAGR':<22} {m_strat['CAGR']:>13.1%} {m_voo['CAGR']:>11.1%} {pelosi['CAGR']:>9.1%}")
    print(f"{'Sharpe Ratio':<22} {m_strat['Sharpe']:>13.2f} {m_voo['Sharpe']:>11.2f} {pelosi['Sharpe']:>9.2f}")
    print(f"{'Max Drawdown':<22} {m_strat['MaxDD']:>13.1%} {m_voo['MaxDD']:>11.1%} {pelosi['MaxDD']:>9.1%}")
    print(f"{'Final Value':<22} ${pv['value'].iloc[-1]:>13,.0f}")
    print(f"{'Avg Positions':<22} {pv['positions'].mean():>13.1f}")
    print("-" * 65)
    
    beats_pelosi = m_strat['CAGR'] > pelosi['CAGR']
    print(f"\n  Beats Pelosi (20% CAGR): {'YES ✓' if beats_pelosi else 'NO ✗'}")
    print(f"  Beats VOO   (15.6% CAGR): {'YES ✓' if m_strat['CAGR'] > 0.156 else 'NO ✗'}")
    print("=" * 65)
    
    # Plot
    plot_results(pv, voo_val, 'report/img/pead_backtest.png')
    
    print("\nFiles written:")
    print("  /home/ubuntu/projects/investor/pead_backtest.py")
    print("  /home/ubuntu/projects/investor/pead_backtest.png")

if __name__ == '__main__':
    main()
