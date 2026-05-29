"""
Berkshire 13F Copy Strategy Backtest
Follows Berkshire Hathaway's quarterly 13F disclosures with 45-day lag
Period: 2020-01-01 to 2026-05-27
"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ── 13F Holdings Timeline ─────────────────────────────────────────────────────
# Quarter end date → portfolio weights (from public 13F filings)
# Implemented with 45-day lag from quarter end
HOLDINGS = {
    # Q4 2019 → implement ~Feb 14, 2020
    '2019-12-31': {'AAPL': 0.40, 'BAC': 0.12, 'KO': 0.08, 'AXP': 0.08, 'KHC': 0.05,
                   'WFC': 0.09, 'USB': 0.04, 'MCO': 0.03, 'DVA': 0.02, 'JPM': 0.02, 'OTHER': 0.07},
    # Q1 2020 → implement ~May 15, 2020
    '2020-03-31': {'AAPL': 0.40, 'BAC': 0.12, 'KO': 0.08, 'AXP': 0.08, 'KHC': 0.05,
                   'USB': 0.04, 'MCO': 0.03, 'DVA': 0.02, 'OTHER': 0.18},
    # Q2 2020 → implement ~Aug 14, 2020
    '2020-06-30': {'AAPL': 0.44, 'BAC': 0.11, 'KO': 0.07, 'AXP': 0.07, 'KHC': 0.04,
                   'USB': 0.04, 'MCO': 0.03, 'DVA': 0.02, 'OTHER': 0.18},
    # Q3 2020 → implement ~Nov 14, 2020
    '2020-09-30': {'AAPL': 0.47, 'BAC': 0.11, 'KO': 0.07, 'AXP': 0.07, 'KHC': 0.04,
                   'USB': 0.03, 'MCO': 0.03, 'OTHER': 0.18},
    # Q4 2020 → implement ~Feb 14, 2021
    '2020-12-31': {'AAPL': 0.44, 'BAC': 0.12, 'KO': 0.07, 'AXP': 0.07, 'KHC': 0.04,
                   'ABBV': 0.02, 'MRK': 0.02, 'VZ': 0.03, 'USB': 0.03, 'MCO': 0.03, 'OTHER': 0.13},
    # Q1 2021 → implement ~May 17, 2021
    '2021-03-31': {'AAPL': 0.42, 'BAC': 0.13, 'KO': 0.07, 'AXP': 0.08, 'KHC': 0.04,
                   'VZ': 0.04, 'USB': 0.03, 'MCO': 0.03, 'ABBV': 0.02, 'OTHER': 0.14},
    # Q2 2021 → implement ~Aug 14, 2021
    '2021-06-30': {'AAPL': 0.40, 'BAC': 0.14, 'KO': 0.07, 'AXP': 0.08, 'KHC': 0.04,
                   'VZ': 0.04, 'USB': 0.03, 'MCO': 0.03, 'OTHER': 0.17},
    # Q3 2021 → implement ~Nov 15, 2021
    '2021-09-30': {'AAPL': 0.41, 'BAC': 0.14, 'KO': 0.08, 'AXP': 0.08, 'KHC': 0.04,
                   'VZ': 0.03, 'USB': 0.03, 'MCO': 0.03, 'OTHER': 0.16},
    # Q4 2021 → implement ~Feb 14, 2022
    '2021-12-31': {'AAPL': 0.41, 'BAC': 0.14, 'KO': 0.08, 'AXP': 0.08, 'KHC': 0.04,
                   'USB': 0.03, 'MCO': 0.03, 'OTHER': 0.19},
    # Q1 2022 → implement ~May 16, 2022
    '2022-03-31': {'AAPL': 0.38, 'BAC': 0.11, 'KO': 0.08, 'AXP': 0.07, 'KHC': 0.04,
                   'CVX': 0.08, 'OXY': 0.04, 'HPQ': 0.02, 'ATVI': 0.02, 'MCO': 0.03, 'OTHER': 0.13},
    # Q2 2022 → implement ~Aug 15, 2022
    '2022-06-30': {'AAPL': 0.38, 'BAC': 0.11, 'KO': 0.08, 'AXP': 0.07, 'KHC': 0.03,
                   'CVX': 0.08, 'OXY': 0.06, 'HPQ': 0.02, 'ATVI': 0.02, 'MCO': 0.03, 'OTHER': 0.12},
    # Q3 2022 → implement ~Nov 14, 2022
    '2022-09-30': {'AAPL': 0.39, 'BAC': 0.11, 'KO': 0.08, 'AXP': 0.08, 'KHC': 0.03,
                   'CVX': 0.07, 'OXY': 0.06, 'HPQ': 0.02, 'MCO': 0.03, 'OTHER': 0.13},
    # Q4 2022 → implement ~Feb 14, 2023
    '2022-12-31': {'AAPL': 0.38, 'BAC': 0.11, 'KO': 0.09, 'AXP': 0.08, 'KHC': 0.03,
                   'CVX': 0.07, 'OXY': 0.04, 'MCO': 0.03, 'OTHER': 0.17},
    # Q1 2023 → implement ~May 15, 2023
    '2023-03-31': {'AAPL': 0.45, 'BAC': 0.10, 'KO': 0.08, 'AXP': 0.07, 'KHC': 0.03,
                   'CVX': 0.06, 'OXY': 0.04, 'MCO': 0.03, 'OTHER': 0.14},
    # Q2 2023 → implement ~Aug 14, 2023
    '2023-06-30': {'AAPL': 0.46, 'BAC': 0.10, 'KO': 0.08, 'AXP': 0.07, 'KHC': 0.03,
                   'CVX': 0.05, 'OXY': 0.04, 'MCO': 0.03, 'OTHER': 0.14},
    # Q3 2023 → implement ~Nov 14, 2023
    '2023-09-30': {'AAPL': 0.50, 'BAC': 0.09, 'KO': 0.07, 'AXP': 0.06, 'KHC': 0.03,
                   'CVX': 0.05, 'OXY': 0.04, 'MCO': 0.02, 'OTHER': 0.14},
    # Q4 2023 → implement ~Feb 14, 2024
    '2023-12-31': {'AAPL': 0.50, 'BAC': 0.09, 'KO': 0.07, 'AXP': 0.06, 'KHC': 0.03,
                   'CVX': 0.04, 'OXY': 0.04, 'MCO': 0.02, 'OTHER': 0.15},
    # Q1 2024 → implement ~May 15, 2024
    '2024-03-31': {'AAPL': 0.40, 'BAC': 0.10, 'KO': 0.09, 'AXP': 0.08, 'KHC': 0.03,
                   'CVX': 0.04, 'OXY': 0.05, 'MCO': 0.03, 'OTHER': 0.18},
    # Q2 2024 → implement ~Aug 14, 2024
    '2024-06-30': {'AAPL': 0.30, 'BAC': 0.10, 'KO': 0.10, 'AXP': 0.09, 'KHC': 0.03,
                   'CVX': 0.04, 'OXY': 0.06, 'MCO': 0.03, 'OTHER': 0.25},
    # Q3 2024 → implement ~Nov 14, 2024
    '2024-09-30': {'AAPL': 0.26, 'BAC': 0.09, 'KO': 0.11, 'AXP': 0.10, 'KHC': 0.03,
                   'CVX': 0.04, 'OXY': 0.07, 'MCO': 0.03, 'OTHER': 0.27},
    # Q4 2024 → implement ~Feb 14, 2025
    '2024-12-31': {'AAPL': 0.28, 'BAC': 0.08, 'KO': 0.11, 'AXP': 0.10, 'KHC': 0.03,
                   'CVX': 0.04, 'OXY': 0.07, 'MCO': 0.03, 'OTHER': 0.26},
    # Q1 2025 → implement ~May 15, 2025
    '2025-03-31': {'AAPL': 0.28, 'BAC': 0.08, 'KO': 0.11, 'AXP': 0.10, 'KHC': 0.03,
                   'CVX': 0.04, 'OXY': 0.07, 'MCO': 0.03, 'OTHER': 0.26},
}

# Tradeable tickers (exclude OTHER which represents smaller/unknown positions)
TICKERS = ['AAPL', 'BAC', 'KO', 'AXP', 'KHC', 'ABBV', 'MRK', 'VZ', 'CVX', 'OXY', 'HPQ', 'ATVI', 'USB', 'MCO', 'WFC', 'DVA', 'JPM']

START_DATE = '2019-12-01'  # fetch extra for price data
END_DATE = '2026-05-27'
BACKTEST_START = '2020-01-01'
INITIAL_CAPITAL = 1_000_000
RISK_FREE_RATE = 0.04
LAG_DAYS = 45

def get_rebalance_schedule():
    """Build list of (rebalance_date, weights_dict) with 45-day lag."""
    schedule = []
    for qend_str, weights in HOLDINGS.items():
        qend = datetime.strptime(qend_str, '%Y-%m-%d')
        rebalance_date = qend + timedelta(days=LAG_DAYS)
        # Normalize weights excluding OTHER
        tradeable = {k: v for k, v in weights.items() if k != 'OTHER'}
        total = sum(tradeable.values())
        normalized = {k: v / total for k, v in tradeable.items()}
        schedule.append((rebalance_date, normalized))
    schedule.sort(key=lambda x: x[0])
    return schedule

def download_prices(tickers, start, end):
    """Download adjusted close prices."""
    print("Downloading price data...")
    all_tickers = tickers + ['VOO']
    data = yf.download(all_tickers, start=start, end=end, auto_adjust=True, progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        prices = data['Close']
    else:
        prices = data
    prices = prices.ffill().dropna(how='all')
    print(f"Downloaded {len(prices)} trading days, {len(prices.columns)} tickers")
    return prices

def run_berkshire_backtest(prices, schedule):
    """Simulate Berkshire 13F copy strategy."""
    # Filter to backtest period
    bt_prices = prices[prices.index >= BACKTEST_START].copy()
    
    portfolio_values = []
    shares = {}
    cash = INITIAL_CAPITAL
    current_weights = {}
    
    # Convert schedule to dict for lookup
    rebalance_dict = {pd.Timestamp(d): w for d, w in schedule}
    rebalance_dates = sorted(rebalance_dict.keys())
    
    # Find first rebalance after backtest start
    first_rebalance_idx = next((i for i, d in enumerate(rebalance_dates) 
                                 if d >= pd.Timestamp(BACKTEST_START)), 0)
    
    # Use last known holdings before start if available
    pre_start = [(d, w) for d, w in schedule if d < pd.Timestamp(BACKTEST_START)]
    if pre_start:
        # Apply most recent pre-start holdings on day 1
        last_pre = pre_start[-1]
        rebalance_dates.insert(0, pd.Timestamp(BACKTEST_START))
        rebalance_dict[pd.Timestamp(BACKTEST_START)] = last_pre[1]
    
    next_rebalance_idx = 0
    
    for date in bt_prices.index:
        # Check if rebalance needed
        while (next_rebalance_idx < len(rebalance_dates) and 
               rebalance_dates[next_rebalance_idx] <= date):
            target_weights = rebalance_dict[rebalance_dates[next_rebalance_idx]]
            
            # Calculate current portfolio value
            port_val = cash
            for ticker, sh in shares.items():
                if ticker in bt_prices.columns and not pd.isna(bt_prices.loc[date, ticker]):
                    port_val += sh * bt_prices.loc[date, ticker]
            
            # Rebalance to target weights
            new_shares = {}
            new_cash = port_val  # start with full value, allocate below
            
            for ticker, weight in target_weights.items():
                if ticker in bt_prices.columns:
                    price = bt_prices.loc[date, ticker]
                    if not pd.isna(price) and price > 0:
                        allocation = port_val * weight
                        new_shares[ticker] = allocation / price
                        new_cash -= allocation
            
            shares = new_shares
            cash = new_cash
            current_weights = target_weights
            next_rebalance_idx += 1
        
        # Calculate daily portfolio value
        port_val = cash
        for ticker, sh in shares.items():
            if ticker in bt_prices.columns:
                price = bt_prices.loc[date, ticker]
                if not pd.isna(price):
                    port_val += sh * price
        
        portfolio_values.append({'date': date, 'value': port_val})
    
    return pd.DataFrame(portfolio_values).set_index('date')

def run_voo_backtest(prices):
    """Buy and hold VOO from start."""
    bt_prices = prices[prices.index >= BACKTEST_START]['VOO'].dropna()
    initial_price = bt_prices.iloc[0]
    shares = INITIAL_CAPITAL / initial_price
    values = bt_prices * shares
    return values.to_frame('value')

def calculate_metrics(portfolio_df, label="Strategy"):
    """Calculate CAGR, Sharpe, Max Drawdown."""
    values = portfolio_df['value']
    
    # CAGR
    start_val = values.iloc[0]
    end_val = values.iloc[-1]
    n_years = (values.index[-1] - values.index[0]).days / 365.25
    cagr = (end_val / start_val) ** (1 / n_years) - 1
    
    # Daily returns
    daily_returns = values.pct_change().dropna()
    
    # Sharpe Ratio (annualized)
    excess_returns = daily_returns - RISK_FREE_RATE / 252
    sharpe = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)
    
    # Max Drawdown
    cummax = values.cummax()
    drawdown = (values - cummax) / cummax
    max_dd = drawdown.min()
    
    # Total return
    total_return = (end_val / start_val - 1) * 100
    
    return {
        'label': label,
        'cagr': cagr * 100,
        'sharpe': sharpe,
        'max_dd': max_dd * 100,
        'total_return': total_return,
        'end_value': end_val,
        'n_years': n_years
    }

def plot_results(berkshire_df, voo_df, berk_metrics, voo_metrics):
    """Create comparison chart."""
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    # Normalize to $1
    berk_norm = berkshire_df['value'] / berkshire_df['value'].iloc[0]
    voo_norm = voo_df['value'] / voo_df['value'].iloc[0]
    
    ax1 = axes[0]
    ax1.plot(berk_norm.index, berk_norm.values, label=f"Berkshire 13F Copy ({berk_metrics['cagr']:.1f}% CAGR)", 
             color='#1f77b4', linewidth=2)
    ax1.plot(voo_norm.index, voo_norm.values, label=f"VOO Buy & Hold ({voo_metrics['cagr']:.1f}% CAGR)", 
             color='#ff7f0e', linewidth=2, linestyle='--')
    ax1.set_title('Berkshire 13F Copy Strategy vs VOO (2020–2026)', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Portfolio Growth ($1 = start)')
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x:.1f}'))
    
    # Drawdown chart
    ax2 = axes[1]
    berk_dd = (berkshire_df['value'] / berkshire_df['value'].cummax() - 1) * 100
    voo_dd = (voo_df['value'] / voo_df['value'].cummax() - 1) * 100
    ax2.fill_between(berk_dd.index, berk_dd.values, 0, alpha=0.4, color='#1f77b4', label='Berkshire 13F Copy')
    ax2.fill_between(voo_dd.index, voo_dd.values, 0, alpha=0.3, color='#ff7f0e', label='VOO')
    ax2.set_title('Drawdown Comparison', fontsize=12)
    ax2.set_ylabel('Drawdown (%)')
    ax2.set_xlabel('Date')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('report/img/insider_backtest.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Chart saved to insider_backtest.png")

def main():
    print("=" * 60)
    print("  BERKSHIRE 13F COPY STRATEGY BACKTEST")
    print("  Period: 2020-01-01 to 2026-05-27")
    print("  Capital: $1,000,000 | 45-day lag")
    print("=" * 60)
    
    # Build rebalance schedule
    schedule = get_rebalance_schedule()
    print(f"\nRebalance schedule: {len(schedule)} events")
    
    # Download prices
    prices = download_prices(TICKERS, START_DATE, END_DATE)
    
    # Run backtests
    print("\nRunning Berkshire 13F Copy backtest...")
    berkshire_df = run_berkshire_backtest(prices, schedule)
    
    print("Running VOO benchmark...")
    voo_df = run_voo_backtest(prices)
    
    # Align dates
    common_idx = berkshire_df.index.intersection(voo_df.index)
    berkshire_df = berkshire_df.loc[common_idx]
    voo_df = voo_df.loc[common_idx]
    
    # Calculate metrics
    berk_metrics = calculate_metrics(berkshire_df, "Berkshire 13F Copy")
    voo_metrics = calculate_metrics(voo_df, "VOO Buy & Hold")
    
    # Baselines
    pelosi_cagr = 20.0
    pelosi_sharpe = 0.68
    
    # Print results
    print("\n" + "=" * 60)
    print("  PERFORMANCE SUMMARY")
    print("=" * 60)
    print(f"\n{'Metric':<25} {'Berkshire 13F':>15} {'VOO B&H':>12} {'Pelosi*':>10}")
    print("-" * 65)
    print(f"{'CAGR':<25} {berk_metrics['cagr']:>14.1f}% {voo_metrics['cagr']:>11.1f}% {pelosi_cagr:>9.1f}%")
    print(f"{'Sharpe Ratio':<25} {berk_metrics['sharpe']:>15.2f} {voo_metrics['sharpe']:>12.2f} {pelosi_sharpe:>10.2f}")
    print(f"{'Max Drawdown':<25} {berk_metrics['max_dd']:>14.1f}% {voo_metrics['max_dd']:>11.1f}%")
    print(f"{'Total Return':<25} {berk_metrics['total_return']:>14.1f}% {voo_metrics['total_return']:>11.1f}%")
    print(f"{'End Value ($1M start)':<25} ${berk_metrics['end_value']:>13,.0f} ${voo_metrics['end_value']:>10,.0f}")
    print(f"{'Years':<25} {berk_metrics['n_years']:>15.1f} {voo_metrics['n_years']:>12.1f}")
    print("-" * 65)
    print("* Pelosi baseline: reported externally, not simulated here")
    
    print("\n  BEAT BASELINES?")
    print(f"  vs VOO  (15.6% CAGR): {'✓ YES' if berk_metrics['cagr'] > 15.6 else '✗ NO '} — {berk_metrics['cagr']:.1f}% vs 15.6%")
    print(f"  vs Pelosi (20.0% CAGR): {'✓ YES' if berk_metrics['cagr'] > 20.0 else '✗ NO '} — {berk_metrics['cagr']:.1f}% vs 20.0%")
    print(f"  Sharpe vs VOO  (0.69): {'✓ YES' if berk_metrics['sharpe'] > 0.69 else '✗ NO '} — {berk_metrics['sharpe']:.2f} vs 0.69")
    print(f"  Sharpe vs Pelosi (0.68): {'✓ YES' if berk_metrics['sharpe'] > 0.68 else '✗ NO '} — {berk_metrics['sharpe']:.2f} vs 0.68")
    
    # Plot
    plot_results(berkshire_df, voo_df, berk_metrics, voo_metrics)
    
    print("\n" + "=" * 60)
    print(f"  CAGR:    {berk_metrics['cagr']:.2f}%")
    print(f"  Sharpe:  {berk_metrics['sharpe']:.3f}")
    print(f"  Max DD:  {berk_metrics['max_dd']:.2f}%")
    print("=" * 60)

if __name__ == '__main__':
    main()
