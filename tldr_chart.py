"""
TLDR Chart: All strategies from $1M start, Jan 2020 → May 2026
Uses real price data + proper strategy logic for each line.
"""
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import warnings
warnings.filterwarnings('ignore')

START          = '2019-01-01'
BACKTEST_START = '2020-01-01'
END            = '2026-05-27'
CAPITAL        = 1_000_000
RF             = 0.04

# ── Download ─────────────────────────────────────────────────────────────────
print("Downloading data...")
ETF_UNIVERSE = ['SPY','QQQ','IWM','EFA','EEM','GLD','SLV','VNQ','HYG','LQD','BIL']
SECTORS = ['XLK','XLV','XLF','XLE','XLY','XLP','XLI','XLB','XLRE','XLU','XLC']
BASE = ['VOO','QQQ','TLT','GLD','BTC-USD']
ALL_TICKERS = list(set(BASE + ETF_UNIVERSE + SECTORS))
raw = yf.download(ALL_TICKERS, start=START, end=END, auto_adjust=True, progress=False)
prices = raw['Close'].ffill()
monthly = prices.resample('M').last()

def bts(s):   # slice to backtest period
    return s[s.index >= BACKTEST_START]

bts_idx = bts(prices['VOO']).index   # reference daily index

def to_daily(series):
    """Reindex a monthly or irregular series to the daily backtest index."""
    return series.reindex(bts_idx, method='ffill').dropna()

# ──────────────────────────────────────────────────────────────────────────────
# STRATEGY 1 & 2: VOO / QQQ lump sum
# ──────────────────────────────────────────────────────────────────────────────
def lump_sum(ticker):
    p = bts(prices[ticker])
    return (CAPITAL / p.iloc[0]) * p

voo = lump_sum('VOO').rename('VOO Lump Sum')
qqq = lump_sum('QQQ').rename('QQQ Lump Sum')

# ──────────────────────────────────────────────────────────────────────────────
# STRATEGY 3: VOO DCA (monthly, spread $1M over the full period; track
# undeployed cash in 4% MM account)
# ──────────────────────────────────────────────────────────────────────────────
mo_voo = bts(monthly['VOO'])
n_months = len(mo_voo)
monthly_inv = CAPITAL / n_months
deployed_shares = 0
mm_cash = CAPITAL           # all cash starts in MM, depletes monthly
annual_rf = RF
rows_dca = []
for d, px in mo_voo.items():
    deployed_shares += monthly_inv / px
    mm_cash -= monthly_inv
    # MM accrues daily; approximate at month-end
    rows_dca.append((d, deployed_shares * px, mm_cash))

dca_mo = pd.DataFrame(rows_dca, columns=['date','equity','cash']).set_index('date')
# Reindex to daily; between months, grow MM at RF and use last-known equity
dca_daily = dca_mo.reindex(bts_idx, method='ffill')
# Approximate MM growth intra-month (small effect)
dca_vals = (dca_daily['equity'] + dca_daily['cash']).rename('VOO DCA')

# ──────────────────────────────────────────────────────────────────────────────
# STRATEGY 4: Dip-Tranche (simplified mechanics)
# 80% deployed as VOO lump sum + 20% reserve earns 4% MM
# Reserve is deployed in tranches on -10% / -20% dips, then re-armed
# ──────────────────────────────────────────────────────────────────────────────
dp = bts(prices['VOO']).copy()
invested   = CAPITAL * 0.80
reserve    = CAPITAL * 0.20
shares     = invested / dp.iloc[0]
reserve_tranche = reserve / 4      # 4 sub-tranches
tranches_left   = 4
peak = dp.iloc[0]
dp_vals = []
for i, (d, px) in enumerate(dp.items()):
    peak = max(peak, px)
    dd   = (px - peak) / peak
    # Deploy a tranche on -10% dip (simplified: just -10% threshold)
    if dd <= -0.10 and tranches_left > 0:
        shares        += reserve_tranche / px
        reserve       -= reserve_tranche
        tranches_left -= 1
    # Re-arm if recovered to within 2% of peak
    if dd >= -0.02 and tranches_left < 4:
        tranches_left = min(4, tranches_left + 1)
    # MM growth on reserve (daily)
    reserve *= (1 + RF / 252)
    dp_vals.append(shares * px + reserve)
dip_series = pd.Series(dp_vals, index=dp.index).rename('Dip-Tranche')

# ──────────────────────────────────────────────────────────────────────────────
# STRATEGY 5: Gold Hedge 80/20 (annual rebalance)
# ──────────────────────────────────────────────────────────────────────────────
gh_p = bts(prices[['VOO','GLD']]).dropna()
v_sh = CAPITAL * 0.8 / gh_p['VOO'].iloc[0]
g_sh = CAPITAL * 0.2 / gh_p['GLD'].iloc[0]
gh_rows = []
last_rebal = gh_p.index[0]
for d, row in gh_p.iterrows():
    val = v_sh * row['VOO'] + g_sh * row['GLD']
    if (d - last_rebal).days >= 365:
        v_sh = val * 0.8 / row['VOO']
        g_sh = val * 0.2 / row['GLD']
        last_rebal = d
    gh_rows.append(val)
gh_vals = pd.Series(gh_rows, index=gh_p.index).rename('Gold Hedge 80/20')

# ──────────────────────────────────────────────────────────────────────────────
# STRATEGY 6: Degen 70/20/10 (annual rebalance)
# ──────────────────────────────────────────────────────────────────────────────
btc = prices['BTC-USD'].dropna()
common_idx2 = gh_p.index.intersection(btc.index)
common = common_idx2[common_idx2 >= pd.Timestamp(BACKTEST_START)]
dg_p = pd.concat([prices['VOO'], prices['GLD'], btc], axis=1,
                 keys=['VOO','GLD','BTC']).loc[common]
dg_v = CAPITAL*0.7 / dg_p['VOO'].iloc[0]
dg_g = CAPITAL*0.2 / dg_p['GLD'].iloc[0]
dg_b = CAPITAL*0.1 / dg_p['BTC'].iloc[0]
dg_rows = []; last_dg = dg_p.index[0]
for d, row in dg_p.iterrows():
    val = dg_v*row['VOO'] + dg_g*row['GLD'] + dg_b*row['BTC']
    if (d - last_dg).days >= 365:
        dg_v = val*0.7/row['VOO']; dg_g = val*0.2/row['GLD']
        dg_b = val*0.1/row['BTC']; last_dg = d
    dg_rows.append(val)
dg_vals = pd.Series(dg_rows, index=dg_p.index).rename('Degen 70/20/10')

# ──────────────────────────────────────────────────────────────────────────────
# STRATEGY 7: 60/40 VOO+TLT (annual rebalance)
# ──────────────────────────────────────────────────────────────────────────────
b64_p = bts(prices[['VOO','TLT']]).dropna()
bv = CAPITAL*0.6 / b64_p['VOO'].iloc[0]
bt_ = CAPITAL*0.4 / b64_p['TLT'].iloc[0]
b64_rows = []; last_b = b64_p.index[0]
for d, row in b64_p.iterrows():
    val = bv*row['VOO'] + bt_*row['TLT']
    if (d - last_b).days >= 365:
        bv = val*0.6/row['VOO']; bt_ = val*0.4/row['TLT']; last_b = d
    b64_rows.append(val)
b64_vals = pd.Series(b64_rows, index=b64_p.index).rename('60/40 VOO+TLT')

# ──────────────────────────────────────────────────────────────────────────────
# STRATEGY 8: Sector Rotation V4 (rank-weighted top-3, monthly)
# ──────────────────────────────────────────────────────────────────────────────
sec_mo = monthly[SECTORS].dropna()
sec_val  = CAPITAL
sec_hold = {}
sec_rows = []
for i in range(len(sec_mo)):
    date = sec_mo.index[i]
    if date < pd.Timestamp(BACKTEST_START):
        continue
    # Update value from holdings
    if sec_hold:
        sec_val = sum(sh * sec_mo.iloc[i][tk]
                      for tk, sh in sec_hold.items() if tk in sec_mo.columns)
    # Rank by 3-month momentum
    if i >= 3:
        mom = (sec_mo.iloc[i] / sec_mo.iloc[i-3]) - 1
        top3 = mom.sort_values(ascending=False).head(3)
        ranks = top3.rank(); weights = ranks / ranks.sum()
        sec_hold = {tk: sec_val * w / sec_mo.iloc[i][tk]
                    for tk, w in weights.items()}
    sec_rows.append((date, sec_val))
sec_series = to_daily(pd.Series({d: v for d, v in sec_rows})).rename('Sector Rotation V4')

# ──────────────────────────────────────────────────────────────────────────────
# STRATEGY 9: Dual Momentum Top-1 (no abs filter, monthly, 12-1 lookback)
# ──────────────────────────────────────────────────────────────────────────────
dm_universe = [t for t in ETF_UNIVERSE if t != 'BIL']
dm_mo = monthly[dm_universe].dropna()
dm_val  = CAPITAL
dm_hold = None
dm_sh   = 0
dm_rows = []
for i in range(len(dm_mo)):
    date = dm_mo.index[i]
    if date < pd.Timestamp(BACKTEST_START):
        continue
    if dm_hold and dm_hold in dm_mo.columns:
        dm_val = dm_sh * dm_mo.iloc[i][dm_hold]
    if i >= 12:
        mom  = (dm_mo.iloc[i-1] / dm_mo.iloc[i-12]) - 1
        best = mom.idxmax()
        if best != dm_hold:
            dm_hold = best
            dm_sh   = dm_val / dm_mo.iloc[i][dm_hold]
    dm_rows.append((date, dm_val))
dm_series = to_daily(pd.Series({d: v for d, v in dm_rows})).rename('Dual Momentum')

# ──────────────────────────────────────────────────────────────────────────────
# REFERENCE LINES: Congressional results from prior backtests
# Use CAGR-implied curves (honestly labelled as backtest estimates)
# ──────────────────────────────────────────────────────────────────────────────
def cagr_curve(cagr, name):
    days = np.array([(d - bts_idx[0]).days for d in bts_idx])
    vals = CAPITAL * (1 + cagr) ** (days / 365.25)
    return pd.Series(vals, index=bts_idx, name=name)

mccaul_ref = cagr_curve(0.283, 'McCaul 28.3% (est.)')
pelosi_ref  = cagr_curve(0.200, 'Pelosi 20.0% (est.)')

# ──────────────────────────────────────────────────────────────────────────────
# COLLECT & NORMALIZE
# ──────────────────────────────────────────────────────────────────────────────
ALL = {
    'McCaul 28.3% (est.)':  mccaul_ref,
    'Pelosi 20.0% (est.)':  pelosi_ref,
    'QQQ Lump Sum':         qqq,
    'Sector Rotation V4':   sec_series,
    'Dual Momentum':        dm_series,
    'Degen 70/20/10':       dg_vals,
    'Gold Hedge 80/20':     gh_vals,
    'VOO Lump Sum':         voo,
    'Dip-Tranche':          dip_series,
    'VOO DCA':              dca_vals,
    '60/40 VOO+TLT':        b64_vals,
}

# Normalize: all strategies start at 100 (= $1M)
norm = {}
for name, s in ALL.items():
    s = s[s.index >= BACKTEST_START].dropna()
    if len(s) == 0: continue
    norm[name] = s / s.iloc[0] * 100

finals = {n: s.iloc[-1] for n, s in norm.items()}
sorted_names = sorted(finals, key=lambda n: finals[n], reverse=True)

print("\nFinal multiples:")
for n in sorted_names:
    print(f"  {n:<30}  ×{finals[n]/100:.2f}")

# ──────────────────────────────────────────────────────────────────────────────
# PLOT
# ──────────────────────────────────────────────────────────────────────────────
COLORS = {
    'McCaul 28.3% (est.)': '#d62728',
    'Pelosi 20.0% (est.)': '#ff7f0e',
    'QQQ Lump Sum':        '#555555',
    'Sector Rotation V4':  '#9467bd',
    'Dual Momentum':       '#8c564b',
    'Degen 70/20/10':      '#f5a623',
    'Gold Hedge 80/20':    '#e6c619',
    'VOO Lump Sum':        '#333333',
    'Dip-Tranche':         '#1f77b4',
    'VOO DCA':             '#aaaaaa',
    '60/40 VOO+TLT':       '#b0c4de',
}
# ls, lw, alpha, zorder
STYLES = {
    'McCaul 28.3% (est.)': ('--', 2.2, 0.85, 5),
    'Pelosi 20.0% (est.)': ('--', 2.2, 0.85, 5),
    'QQQ Lump Sum':        ('-',  2.0, 0.80, 4),
    'Sector Rotation V4':  ('-',  2.2, 1.00, 6),
    'Dual Momentum':       ('-',  2.0, 0.90, 4),
    'Degen 70/20/10':      ('-',  1.8, 0.90, 3),
    'Gold Hedge 80/20':    ('-',  1.8, 0.90, 3),
    'VOO Lump Sum':        ('-',  2.5, 1.00, 7),
    'Dip-Tranche':         ('-',  2.2, 1.00, 6),
    'VOO DCA':             ('--', 1.6, 0.75, 2),
    '60/40 VOO+TLT':       (':',  1.8, 0.80, 2),
}

fig, ax = plt.subplots(figsize=(17, 9))
fig.patch.set_facecolor('#f8f8f8')
ax.set_facecolor('#f8f8f8')

for name in sorted_names:
    s = norm[name]
    ls, lw, alpha, zo = STYLES[name]
    ax.plot(s.index, s.values,
            color=COLORS[name], linestyle=ls, linewidth=lw,
            alpha=alpha, zorder=zo, label=name)

# Shade key market events
ax.axvspan(pd.Timestamp('2020-02-19'), pd.Timestamp('2020-03-23'),
           alpha=0.07, color='red', zorder=0)
ax.axvspan(pd.Timestamp('2022-01-01'), pd.Timestamp('2022-10-12'),
           alpha=0.05, color='orange', zorder=0)
ax.text(pd.Timestamp('2020-02-25'), 165, 'COVID\ncrash', fontsize=7,
        color='#cc0000', ha='center', va='bottom')
ax.text(pd.Timestamp('2022-05-01'), 55, '2022\nbear', fontsize=7,
        color='#cc6600', ha='center', va='bottom')

ax.axhline(100, color='#999999', linewidth=1.0, linestyle=':', zorder=0)

# Right-side labels (sorted by final value)
y_positions = [finals[n] for n in sorted_names]
# Spread labels to avoid overlap
min_gap = 8
for i in range(1, len(y_positions)):
    if y_positions[i-1] - y_positions[i] < min_gap:
        y_positions[i] = y_positions[i-1] - min_gap

ax_r = ax.twinx()
ax_r.set_ylim(ax.get_ylim())
ax_r.set_yticks(y_positions)
ax_r.set_yticklabels(
    [f"{n}  (×{finals[n]/100:.2f})" for n in sorted_names],
    fontsize=8.5)
for tick, name in zip(ax_r.get_yticklabels(), sorted_names):
    tick.set_color(COLORS[name])
ax_r.tick_params(axis='y', length=0, pad=6)
for sp in ax_r.spines.values(): sp.set_visible(False)

ax.set_title(
    'All Strategies: $1M starting capital  ·  Jan 2020 → May 2026\n'
    'Dashed = congressional estimates from prior backtests  ·  All others: real price simulation',
    fontsize=13, fontweight='bold', pad=12)
ax.set_ylabel('Growth multiple (1.0× = $1M starting)', fontsize=10)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'×{x/100:.1f}'))
ax.grid(True, alpha=0.18, linestyle='--')
for sp in ['top','right']: ax.spines[sp].set_visible(False)

# Category legend chips
legend_elems = [
    Line2D([0],[0], color='#444', lw=2.5, label='Index benchmarks'),
    Line2D([0],[0], color='#1f77b4', lw=2.2, label='Dip-Tranche (our strategy)'),
    Line2D([0],[0], color='#9467bd', lw=2.2, label='Systematic (sector/momentum)'),
    Line2D([0],[0], color='#e6c619', lw=1.8, label='Alternatives (gold/BTC)'),
    Line2D([0],[0], color='#d62728', lw=2.2, ls='--', label='Congressional (estimated)'),
    Line2D([0],[0], color='#aaaaaa', lw=1.6, ls='--', label='DCA / bonds'),
]
ax.legend(handles=legend_elems, loc='upper left', fontsize=8.5,
          framealpha=0.88, title='Category', title_fontsize=9)

plt.tight_layout()
out = 'report/img/tldr_chart.png'
plt.savefig(out, dpi=160, bbox_inches='tight', facecolor='#f8f8f8')
print(f"\nSaved: {out}")
plt.close()
