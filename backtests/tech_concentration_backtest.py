import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

START = '2020-01-01'
END = '2026-05-27'
INITIAL = 1_000_000
RF = 0.04  # risk-free rate

def download(tickers, start, end):
    data = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
    if isinstance(tickers, list) and len(tickers) > 1:
        return data['Close']
    else:
        return data['Close'].to_frame(tickers if isinstance(tickers, str) else tickers[0])

def calc_metrics(values):
    values = pd.Series(values).dropna()
    total_days = (values.index[-1] - values.index[0]).days
    years = total_days / 365.25
    cagr = (values.iloc[-1] / values.iloc[0]) ** (1 / years) - 1
    daily_ret = values.pct_change().dropna()
    sharpe = (daily_ret.mean() - RF/252) / daily_ret.std() * np.sqrt(252)
    roll_max = values.cummax()
    dd = (values - roll_max) / roll_max
    max_dd = dd.min()
    return {
        'Final Value': values.iloc[-1],
        'CAGR': cagr,
        'Sharpe': sharpe,
        'Max Drawdown': max_dd
    }

# ── Download all needed data ──────────────────────────────────────────────────
print("Downloading data...")
mag7 = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA']
semis = ['NVDA','AMD','AVGO','QCOM','TXN','AMAT','LRCX','KLAC','MU','MRVL',
         'MSFT','GOOGL','AMZN','META','ORCL','CRM']
all_tickers = list(set(mag7 + semis + ['VOO','QQQ','TQQQ','BIL']))

prices = download(all_tickers, START, END)
prices = prices.ffill()

# ── Benchmarks ────────────────────────────────────────────────────────────────
def lump_sum(ticker):
    s = prices[ticker].dropna()
    s = s[s.index >= START]
    val = INITIAL * s / s.iloc[0]
    return val

voo_vals = lump_sum('VOO')
qqq_vals = lump_sum('QQQ')

# ── Strategy A: Mag7 Equal Weight Quarterly Rebalance ─────────────────────────
def strategy_a():
    holdings = {t: INITIAL/7 for t in mag7}
    dates = prices.index
    portfolio = []
    last_rebal = None

    for i, date in enumerate(dates):
        # check quarterly rebalance
        if last_rebal is None or (date - last_rebal).days >= 90:
            total = sum(holdings[t] / prices[t].iloc[i-1] * prices[t].loc[date]
                       if i > 0 else holdings[t]
                       for t in mag7)
            # Actually just track shares
            if last_rebal is None:
                shares = {t: (INITIAL/7) / prices[t].loc[date] for t in mag7}
            else:
                total_val = sum(shares[t] * prices[t].loc[date] for t in mag7)
                shares = {t: (total_val/7) / prices[t].loc[date] for t in mag7}
            last_rebal = date

        total_val = sum(shares[t] * prices[t].loc[date] for t in mag7)
        portfolio.append({'date': date, 'value': total_val})

    df = pd.DataFrame(portfolio).set_index('date')['value']
    return df

# ── Strategy B: AI/Semis Momentum Monthly ─────────────────────────────────────
def strategy_b():
    portfolio = []
    shares = {}
    last_rebal = None
    TOP_N = 8

    for i, date in enumerate(prices.index):
        rebal = False
        if last_rebal is None:
            rebal = True
        elif date.month != last_rebal.month:
            rebal = True

        if rebal:
            # compute 3-month (63-day) momentum
            lookback = 63
            if i >= lookback:
                mom = {}
                for t in semis:
                    if t in prices.columns:
                        past = prices[t].iloc[i-lookback]
                        curr = prices[t].loc[date]
                        if past > 0:
                            mom[t] = (curr / past) - 1
                top = sorted(mom, key=mom.get, reverse=True)[:TOP_N]
            else:
                top = semis[:TOP_N]

            if not shares:
                # initial
                alloc = INITIAL / TOP_N
                shares = {t: alloc / prices[t].loc[date] for t in top}
            else:
                total_val = sum(shares.get(t, 0) * prices[t].loc[date]
                               for t in shares if t in prices.columns)
                alloc = total_val / TOP_N
                shares = {t: alloc / prices[t].loc[date] for t in top}
            last_rebal = date

        total_val = sum(shares.get(t, 0) * prices[t].loc[date]
                       for t in shares if t in prices.columns)
        portfolio.append({'date': date, 'value': total_val})

    df = pd.DataFrame(portfolio).set_index('date')['value']
    return df

# ── Strategy C: TQQQ with 200-day SMA filter (weekly check) ───────────────────
def strategy_c():
    portfolio = []
    cash_rate_daily = (1 + RF) ** (1/252) - 1

    qqq = prices['QQQ']
    tqqq = prices['TQQQ']
    bil = prices['BIL']

    # compute 200-day SMA
    sma200 = qqq.rolling(200).mean()

    position = None  # 'tqqq' or 'cash'
    shares = 0
    cash = 0
    value = INITIAL
    last_check = None

    for i, date in enumerate(prices.index):
        check = False
        if last_check is None:
            check = True
        elif (date - last_check).days >= 7:
            check = True

        if check:
            above = (not np.isnan(sma200.loc[date])) and (qqq.loc[date] > sma200.loc[date])
            if above:
                new_pos = 'tqqq'
            else:
                new_pos = 'cash'

            if new_pos != position:
                # liquidate
                if position == 'tqqq':
                    value = shares * tqqq.loc[date]
                elif position == 'cash':
                    value = cash
                else:
                    value = INITIAL

                # enter
                if new_pos == 'tqqq':
                    shares = value / tqqq.loc[date]
                    cash = 0
                else:
                    cash = value
                    shares = 0
                position = new_pos
            last_check = date

        # daily value
        if position == 'tqqq':
            value = shares * tqqq.loc[date]
        elif position == 'cash':
            cash *= (1 + cash_rate_daily)
            value = cash

        portfolio.append({'date': date, 'value': value})

    df = pd.DataFrame(portfolio).set_index('date')['value']
    return df

# ── Strategy D: 80/20 VOO/TQQQ Quarterly Rebalance ───────────────────────────
def strategy_d():
    portfolio = []
    voo_shares = (INITIAL * 0.8) / prices['VOO'].iloc[0]
    tqqq_shares = (INITIAL * 0.2) / prices['TQQQ'].iloc[0]
    last_rebal = None

    for i, date in enumerate(prices.index):
        rebal = False
        if last_rebal is None:
            rebal = True
            last_rebal = date
        elif (date - last_rebal).days >= 90:
            rebal = True

        if rebal and i > 0:
            total_val = voo_shares * prices['VOO'].loc[date] + tqqq_shares * prices['TQQQ'].loc[date]
            voo_shares = (total_val * 0.8) / prices['VOO'].loc[date]
            tqqq_shares = (total_val * 0.2) / prices['TQQQ'].loc[date]
            last_rebal = date

        total_val = voo_shares * prices['VOO'].loc[date] + tqqq_shares * prices['TQQQ'].loc[date]
        portfolio.append({'date': date, 'value': total_val})

    df = pd.DataFrame(portfolio).set_index('date')['value']
    return df

print("Running strategies...")
a_vals = strategy_a()
b_vals = strategy_b()
c_vals = strategy_c()
d_vals = strategy_d()

# ── Compute metrics ───────────────────────────────────────────────────────────
strategies = {
    'VOO Lump Sum': voo_vals,
    'QQQ Lump Sum': qqq_vals,
    'A: Mag7 EW Quarterly': a_vals,
    'B: AI/Semis Momentum': b_vals,
    'C: TQQQ+SMA Filter': c_vals,
    'D: 80/20 VOO+TQQQ': d_vals,
}

results = {}
for name, vals in strategies.items():
    results[name] = calc_metrics(vals)

# ── Print table ───────────────────────────────────────────────────────────────
print("\n" + "="*80)
print(f"{'Strategy':<28} {'Final Value':>14} {'CAGR':>8} {'Sharpe':>8} {'Max DD':>9}")
print("="*80)

baselines = {
    'VOO Lump Sum':     {'CAGR': 0.156, 'Sharpe': 0.69},
    'QQQ Lump Sum':     {'CAGR': 0.217, 'Sharpe': None},
    'Pelosi':           {'CAGR': 0.200, 'Sharpe': 0.68},
    'McCaul':           {'CAGR': 0.283, 'Sharpe': 0.91},
}

for name, m in results.items():
    print(f"{name:<28} ${m['Final Value']:>13,.0f} {m['CAGR']:>7.1%} {m['Sharpe']:>8.2f} {m['Max Drawdown']:>8.1%}")

print("-"*80)
print("BASELINES (reference):")
for name, m in baselines.items():
    sharpe = f"{m['Sharpe']:.2f}" if m['Sharpe'] else "  N/A"
    print(f"  {name:<26} {'':>14} {m['CAGR']:>7.1%} {sharpe:>8}")
print("="*80)

# ── Chart ─────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(2, 1, figsize=(14, 10))
ax1, ax2 = axes

colors = ['#888888', '#444444', '#2196F3', '#FF5722', '#4CAF50', '#9C27B0']
labels = list(strategies.keys())

for (name, vals), color in zip(strategies.items(), colors):
    ax1.plot(vals.index, vals / 1e6, label=name, color=color,
             linewidth=2 if 'VOO' not in name and 'QQQ' != name.split()[0] else 1,
             linestyle='--' if name in ('VOO Lump Sum', 'QQQ Lump Sum') else '-')

ax1.set_title('Tech Concentration Strategies — Portfolio Value ($1M initial, 2020–2026)', fontsize=13)
ax1.set_ylabel('Portfolio Value ($M)')
ax1.legend(loc='upper left', fontsize=9)
ax1.grid(True, alpha=0.3)
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x:.1f}M'))

# drawdown
for (name, vals), color in zip(strategies.items(), colors):
    v = vals.dropna()
    dd = (v - v.cummax()) / v.cummax() * 100
    ax2.plot(dd.index, dd, label=name, color=color,
             linewidth=2 if 'VOO' not in name and 'QQQ' != name.split()[0] else 1,
             linestyle='--' if name in ('VOO Lump Sum', 'QQQ Lump Sum') else '-')

ax2.set_title('Drawdown (%)', fontsize=13)
ax2.set_ylabel('Drawdown (%)')
ax2.legend(loc='lower left', fontsize=9)
ax2.grid(True, alpha=0.3)
ax2.fill_between(dd.index, 0, 0, alpha=0)  # dummy

plt.tight_layout()
plt.savefig('report/img/tech_concentration_backtest.png', dpi=150, bbox_inches='tight')
print("\nChart saved to tech_concentration_backtest.png")
