"""
Dual Momentum Strategy Backtest (Gary Antonacci's approach)
Period: 2020-01-01 to 2026-05-27
Starting capital: $1,000,000

Strategy:
- Cross-sectional momentum: rank ETF universe by 12-1 month momentum
- Absolute momentum filter: if top asset has negative momentum vs BIL (T-bills), go to cash
- Monthly rebalancing
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

# ─── Parameters ─────────────────────────────────────────────────────────────
START_DATE = '2019-01-01'   # extra history for momentum lookback
BACKTEST_START = '2020-01-01'
END_DATE = '2026-05-27'
INITIAL_CAPITAL = 1_000_000
RISK_FREE_RATE = 0.04
MOMENTUM_LOOKBACK = 12   # months
SKIP_LAST = 1            # skip most recent month (reversal avoidance)

# ETF Universe
UNIVERSE = ['SPY', 'QQQ', 'IWM', 'EFA', 'EEM', 'TLT', 'GLD', 'SLV', 'VNQ', 'HYG', 'LQD', 'BIL']
SAFE_HAVEN = 'BIL'   # T-bill ETF, used for absolute momentum filter and cash

print("=" * 70)
print("DUAL MOMENTUM STRATEGY BACKTEST")
print("=" * 70)
print(f"Universe: {UNIVERSE}")
print(f"Period: {BACKTEST_START} to {END_DATE}")
print(f"Starting Capital: ${INITIAL_CAPITAL:,.0f}")
print(f"Momentum: {MOMENTUM_LOOKBACK}-{SKIP_LAST} month")
print()

# ─── Download Data ────────────────────────────────────────────────────────────
print("Downloading price data...")
all_tickers = list(set(UNIVERSE + ['VOO']))
raw = yf.download(all_tickers, start=START_DATE, end=END_DATE, auto_adjust=True, progress=False)
prices = raw['Close'].ffill()
print(f"Downloaded {len(prices)} trading days")
print()

# ─── Monthly Resampling ──────────────────────────────────────────────────────
monthly_prices = prices.resample('M').last()

# ─── Helper Functions ─────────────────────────────────────────────────────────

def compute_momentum(monthly_prices, date_idx):
    """Compute 12-1 month momentum for all tickers at given month index."""
    if date_idx < MOMENTUM_LOOKBACK:
        return None
    
    end_price = monthly_prices.iloc[date_idx - SKIP_LAST]
    start_price = monthly_prices.iloc[date_idx - MOMENTUM_LOOKBACK]
    momentum = (end_price / start_price) - 1
    return momentum


def run_dual_momentum(top_n=3, use_abs_momentum=True, universe=None):
    """
    Run dual momentum strategy.
    
    top_n: number of top momentum assets to hold
    use_abs_momentum: if True, switch to BIL if top asset has negative momentum
    universe: list of tickers to use (default: UNIVERSE minus BIL)
    """
    if universe is None:
        universe = [t for t in UNIVERSE if t != SAFE_HAVEN]
    
    portfolio_values = []
    holdings = {}
    cash = INITIAL_CAPITAL
    current_value = INITIAL_CAPITAL
    
    # Filter to backtest period
    backtest_months = monthly_prices[monthly_prices.index >= BACKTEST_START]
    
    trades = []
    monthly_returns = []
    prev_value = INITIAL_CAPITAL
    
    for i, (date, row) in enumerate(backtest_months.iterrows()):
        # Get the index in the full monthly_prices dataframe
        full_idx = monthly_prices.index.get_loc(date)
        
        # Compute momentum
        mom = compute_momentum(monthly_prices, full_idx)
        
        if mom is None:
            portfolio_values.append({'date': date, 'value': current_value})
            continue
        
        # Rank universe by momentum
        universe_mom = mom[universe].dropna()
        if len(universe_mom) == 0:
            portfolio_values.append({'date': date, 'value': current_value})
            continue
        
        ranked = universe_mom.sort_values(ascending=False)
        top_assets = ranked.head(top_n).index.tolist()
        
        # Absolute momentum filter: check if top asset beats T-bills
        if use_abs_momentum:
            bil_mom = mom.get(SAFE_HAVEN, 0)
            top_asset_mom = ranked.iloc[0]
            if top_asset_mom < bil_mom:
                # Go to safe haven
                top_assets = [SAFE_HAVEN]
        
        # Equal weight allocation
        weight = 1.0 / len(top_assets)
        new_holdings = {asset: weight for asset in top_assets}
        
        # Calculate current portfolio value using today's prices
        if holdings:
            current_value = sum(
                shares * monthly_prices.loc[date, asset]
                for asset, shares in holdings.items()
                if asset in monthly_prices.columns
            )
        
        # Rebalance
        holdings = {}
        for asset, w in new_holdings.items():
            alloc = current_value * w
            price = monthly_prices.loc[date, asset]
            if not np.isnan(price) and price > 0:
                holdings[asset] = alloc / price
            
        trades.append({
            'date': date,
            'assets': top_assets,
            'momentum': {a: universe_mom.get(a, ranked.get(a, 0)) for a in top_assets}
        })
        
        # Record monthly return
        monthly_return = (current_value / prev_value) - 1 if prev_value > 0 else 0
        monthly_returns.append(monthly_return)
        prev_value = current_value
        
        portfolio_values.append({'date': date, 'value': current_value})
    
    # Final value calculation
    final_prices = monthly_prices.iloc[-1]
    if holdings:
        final_value = sum(
            shares * final_prices.get(asset, 0)
            for asset, shares in holdings.items()
            if asset in final_prices.index and not np.isnan(final_prices.get(asset, np.nan))
        )
    else:
        final_value = current_value
    
    return pd.DataFrame(portfolio_values).set_index('date'), monthly_returns, trades, final_value


def compute_stats(portfolio_df, monthly_returns, final_value):
    """Compute performance statistics."""
    if portfolio_df.empty:
        return {}
    
    values = portfolio_df['value']
    
    # CAGR
    start_val = values.iloc[0]
    end_val = final_value
    
    start_date = values.index[0]
    end_date_actual = values.index[-1]
    years = (end_date_actual - start_date).days / 365.25
    
    if years > 0 and start_val > 0:
        cagr = (end_val / start_val) ** (1 / years) - 1
    else:
        cagr = 0
    
    total_return = (end_val / start_val) - 1
    
    # Max Drawdown
    running_max = values.cummax()
    drawdown = (values - running_max) / running_max
    max_dd = drawdown.min()
    
    # Sharpe Ratio (monthly)
    if len(monthly_returns) > 1:
        ret_series = pd.Series(monthly_returns)
        monthly_rf = RISK_FREE_RATE / 12
        excess_returns = ret_series - monthly_rf
        sharpe = (excess_returns.mean() / excess_returns.std()) * np.sqrt(12)
    else:
        sharpe = 0
    
    return {
        'final_value': end_val,
        'total_return': total_return,
        'cagr': cagr,
        'max_drawdown': max_dd,
        'sharpe': sharpe,
        'years': years
    }


# ─── VOO Benchmarks ──────────────────────────────────────────────────────────
print("Computing benchmarks...")

# VOO Lump Sum
voo_prices = prices['VOO'][prices.index >= BACKTEST_START]
voo_start = voo_prices.iloc[0]
voo_end = voo_prices.iloc[-1]
voo_shares = INITIAL_CAPITAL / voo_start
voo_values = voo_shares * voo_prices

voo_years = (voo_prices.index[-1] - voo_prices.index[0]).days / 365.25
voo_cagr = (voo_end / voo_start) ** (1 / voo_years) - 1
voo_total_return = (voo_end / voo_start) - 1

voo_running_max = voo_values.cummax()
voo_dd = ((voo_values - voo_running_max) / voo_running_max).min()

voo_daily_returns = voo_prices.pct_change().dropna()
voo_sharpe = ((voo_daily_returns.mean() - RISK_FREE_RATE/252) / voo_daily_returns.std()) * np.sqrt(252)

print(f"  VOO Lump Sum: CAGR={voo_cagr:.1%}, Sharpe={voo_sharpe:.2f}, MaxDD={voo_dd:.1%}")

# VOO DCA (monthly $1k investments, scaled to match initial capital equivalent)
dca_dates = pd.date_range(BACKTEST_START, END_DATE, freq='MS')
total_months = len(dca_dates)
monthly_dca = INITIAL_CAPITAL / total_months  # spread total capital over period
dca_shares = 0
dca_invested = 0
dca_values = []
for d in voo_prices.resample('M').last().index:
    if d in prices.index or True:
        try:
            price_at_date = voo_prices.asof(d)
            dca_shares += monthly_dca / price_at_date
            dca_invested += monthly_dca
            dca_values.append({'date': d, 'value': dca_shares * price_at_date})
        except:
            pass

dca_df = pd.DataFrame(dca_values).set_index('date')
dca_final = dca_df['value'].iloc[-1] if not dca_df.empty else INITIAL_CAPITAL
dca_cagr = (dca_final / INITIAL_CAPITAL) ** (1 / voo_years) - 1

print(f"  VOO DCA: CAGR={dca_cagr:.1%}")
print()

# ─── Run Strategy Variants ───────────────────────────────────────────────────
print("Running momentum strategy variants...")
print()

variants = [
    {'top_n': 1, 'use_abs_momentum': False, 'name': 'Top-1 (no abs filter)'},
    {'top_n': 1, 'use_abs_momentum': True,  'name': 'Top-1 + Abs Filter'},
    {'top_n': 3, 'use_abs_momentum': False, 'name': 'Top-3 (no abs filter)'},
    {'top_n': 3, 'use_abs_momentum': True,  'name': 'Top-3 + Abs Filter'},
    {'top_n': 5, 'use_abs_momentum': False, 'name': 'Top-5 (no abs filter)'},
    {'top_n': 5, 'use_abs_momentum': True,  'name': 'Top-5 + Abs Filter'},
]

results = []
portfolio_series = {}

for v in variants:
    pf_df, monthly_rets, trades, final_val = run_dual_momentum(
        top_n=v['top_n'],
        use_abs_momentum=v['use_abs_momentum']
    )
    stats = compute_stats(pf_df, monthly_rets, final_val)
    stats['name'] = v['name']
    results.append(stats)
    portfolio_series[v['name']] = pf_df['value']
    print(f"  {v['name']:30s}  CAGR={stats.get('cagr',0):.1%}  "
          f"Sharpe={stats.get('sharpe',0):.2f}  "
          f"MaxDD={stats.get('max_drawdown',0):.1%}  "
          f"Final=${stats.get('final_value',0):,.0f}")

print()

# ─── Summary Table ───────────────────────────────────────────────────────────
print("=" * 90)
print(f"{'Strategy':<32} {'Final Value':>14} {'Total Ret':>10} {'CAGR':>8} {'Sharpe':>8} {'Max DD':>8} {'Beats Pelosi':>13}")
print("-" * 90)

# Benchmarks
print(f"{'VOO Lump Sum (benchmark)':<32} ${INITIAL_CAPITAL*(1+voo_total_return):>13,.0f} {voo_total_return:>9.1%} {voo_cagr:>7.1%} {voo_sharpe:>7.2f} {voo_dd:>7.1%} {'NO':>13}")
print(f"{'VOO DCA (benchmark)':<32} ${dca_final:>13,.0f} {(dca_final/INITIAL_CAPITAL-1):>9.1%} {dca_cagr:>7.1%} {'N/A':>7} {'N/A':>7} {'NO':>13}")
print(f"{'Pelosi Tracker (reference)':<32} {'~$2.97M':>14} {'~197%':>10} {'20.0%':>8} {'0.68':>8} {'-42.7%':>8} {'BASELINE':>13}")
print(f"{'McCaul Tracker (reference)':<32} {'~$5.53M':>14} {'~453%':>10} {'28.3%':>8} {'0.91':>8} {'-43.9%':>8} {'YES':>13}")
print("-" * 90)

best_strategy = None
best_cagr = 0

for r in results:
    beats_pelosi = "YES ✓" if r.get('cagr', 0) > 0.20 else "no"
    beats_voo = r.get('cagr', 0) > voo_cagr
    final_val = r.get('final_value', INITIAL_CAPITAL)
    total_ret = r.get('total_return', 0)
    cagr = r.get('cagr', 0)
    sharpe = r.get('sharpe', 0)
    max_dd = r.get('max_drawdown', 0)
    
    print(f"  {r['name']:<30} ${final_val:>13,.0f} {total_ret:>9.1%} {cagr:>7.1%} {sharpe:>7.2f} {max_dd:>7.1%} {beats_pelosi:>13}")
    
    if cagr > best_cagr:
        best_cagr = cagr
        best_strategy = r

print("=" * 90)
print()

if best_strategy:
    print(f"BEST VARIANT: {best_strategy['name']}")
    print(f"  CAGR:         {best_strategy['cagr']:.2%}")
    print(f"  Sharpe:       {best_strategy['sharpe']:.2f}")
    print(f"  Max Drawdown: {best_strategy['max_drawdown']:.2%}")
    print(f"  Final Value:  ${best_strategy['final_value']:,.0f}")
    print(f"  Beats Pelosi (20% CAGR): {'YES' if best_strategy['cagr'] > 0.20 else 'NO'}")
    print(f"  Beats VOO Lump Sum ({voo_cagr:.1%}): {'YES' if best_strategy['cagr'] > voo_cagr else 'NO'}")

# ─── Plotting ─────────────────────────────────────────────────────────────────
print()
print("Generating charts...")

fig = plt.figure(figsize=(16, 12))
gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.4, wspace=0.3)

# Plot 1: Portfolio value over time
ax1 = fig.add_subplot(gs[0, :])

# Plot VOO
ax1.plot(voo_values.index, voo_values.values / INITIAL_CAPITAL * 100,
         'k-', linewidth=2, label=f'VOO Lump Sum ({voo_cagr:.1%} CAGR)', alpha=0.8)

# Color cycle for strategies
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

for i, (name, series) in enumerate(portfolio_series.items()):
    if series.empty:
        continue
    normalized = series / INITIAL_CAPITAL * 100
    cagr = results[i].get('cagr', 0)
    lw = 2.5 if '+' in name else 1.5
    ls = '-' if '+' in name else '--'
    ax1.plot(normalized.index, normalized.values,
             color=colors[i % len(colors)], linewidth=lw, linestyle=ls,
             label=f'{name} ({cagr:.1%} CAGR)', alpha=0.9)

ax1.axhline(y=100, color='gray', linestyle=':', linewidth=1, alpha=0.5)
ax1.set_title('Dual Momentum Strategy: Portfolio Value (2020–2026)', fontsize=14, fontweight='bold')
ax1.set_ylabel('Portfolio Value (% of Initial)', fontsize=11)
ax1.set_xlabel('')
ax1.legend(loc='upper left', fontsize=8, ncol=2)
ax1.grid(True, alpha=0.3)
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0f}%'))

# Plot 2: CAGR comparison bar chart
ax2 = fig.add_subplot(gs[1, 0])

strategy_names = [r['name'].replace(' (no abs filter)', '\n(no filter)').replace(' + Abs Filter', '\n+AbsFilter') for r in results]
cagrs = [r.get('cagr', 0) * 100 for r in results]

bars = ax2.bar(range(len(results)), cagrs, color=[colors[i % len(colors)] for i in range(len(results))], alpha=0.8)
ax2.axhline(y=voo_cagr * 100, color='black', linestyle='--', linewidth=2, label=f'VOO ({voo_cagr:.1%})')
ax2.axhline(y=20.0, color='red', linestyle='--', linewidth=2, label='Pelosi (20.0%)')
ax2.set_xticks(range(len(results)))
ax2.set_xticklabels(strategy_names, fontsize=7, rotation=20, ha='right')
ax2.set_ylabel('CAGR (%)', fontsize=11)
ax2.set_title('CAGR by Strategy', fontsize=12, fontweight='bold')
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3, axis='y')

for bar, val in zip(bars, cagrs):
    ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.2,
             f'{val:.1f}%', ha='center', va='bottom', fontsize=8)

# Plot 3: Risk-Return scatter
ax3 = fig.add_subplot(gs[1, 1])

for i, r in enumerate(results):
    ax3.scatter(abs(r.get('max_drawdown', 0)) * 100, r.get('cagr', 0) * 100,
                color=colors[i % len(colors)], s=100, zorder=5)
    ax3.annotate(r['name'].split(' ')[0] + ' ' + r['name'].split(' ')[1],
                 (abs(r.get('max_drawdown', 0)) * 100, r.get('cagr', 0) * 100),
                 textcoords='offset points', xytext=(5, 5), fontsize=7)

ax3.scatter(abs(voo_dd) * 100, voo_cagr * 100, color='black', s=150, marker='*',
            label='VOO', zorder=6)
ax3.scatter(42.7, 20.0, color='red', s=150, marker='*', label='Pelosi', zorder=6)
ax3.scatter(43.9, 28.3, color='purple', s=150, marker='*', label='McCaul', zorder=6)

ax3.set_xlabel('Max Drawdown (%)', fontsize=11)
ax3.set_ylabel('CAGR (%)', fontsize=11)
ax3.set_title('Risk-Return Profile', fontsize=12, fontweight='bold')
ax3.legend(fontsize=9)
ax3.grid(True, alpha=0.3)

plt.suptitle('Dual Momentum ETF Strategy Backtest (2020–2026)\n$1M Starting Capital, Monthly Rebalancing',
             fontsize=14, fontweight='bold', y=1.01)

output_path = 'report/img/momentum_backtest.png'
plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
print(f"Chart saved to: {output_path}")
plt.close()

print()
print("=" * 70)
print("BACKTEST COMPLETE")
print("=" * 70)
print(f"Script: /home/ubuntu/projects/investor/momentum_backtest.py")
print(f"Chart:  /home/ubuntu/projects/investor/momentum_backtest.png")
