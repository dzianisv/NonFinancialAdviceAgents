"""
Fan chart: dip-tranche strategy starting from each of the 20 quarterly
entry points (Q1-2020 → Q4-2024), each deploying $1M over 18 months.

All 20 curves plotted on a shared calendar x-axis, each starting at $1M.
Colour = starting year (5 years × 4 shades).
"""
import sys, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.lines import Line2D
warnings.filterwarnings("ignore")

try:
    import yfinance as yf
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance", "-q"])
    import yfinance as yf

# ── Config (must match quarterly_starts_backtest.py) ─────────────────────────
PORTFOLIO           = 1_000_000
DATA_START          = "2020-01-01"
END_DATE            = "2026-05-27"
DCA_MONTHS          = 18
MM_YIELD_ANNUAL     = 0.04
COOLDOWN_WEEKS      = 3
MAX_REARMS_PER_YEAR = 2
LUMP_PCT  = 0.50
DCA_PCT   = 0.30
RES_PCT   = 0.20
TIER1_SHARE, TIER2_SHARE, TIER3_SHARE = 0.40, 0.35, 0.25
BASE_T1   = [-0.07, -0.085, -0.10]
BASE_T2   = [-0.12, -0.14,  -0.16]
BASE_T3   = [-0.20, -0.25,  -0.30]
BASE_REARM = 0.05

QUARTER_STARTS = [
    "2020-01-01","2020-04-01","2020-07-01","2020-10-01",
    "2021-01-01","2021-04-01","2021-07-01","2021-10-01",
    "2022-01-01","2022-04-01","2022-07-01","2022-10-01",
    "2023-01-01","2023-04-01","2023-07-01","2023-10-01",
    "2024-01-01","2024-04-01","2024-07-01","2024-10-01",
]
QUARTER_LABELS = [
    "Q1-20","Q2-20","Q3-20","Q4-20",
    "Q1-21","Q2-21","Q3-21","Q4-21",
    "Q1-22","Q2-22","Q3-22","Q4-22",
    "Q1-23","Q2-23","Q3-23","Q4-23",
    "Q1-24","Q2-24","Q3-24","Q4-24",
]

# ── Strategy engine (copied verbatim from quarterly_starts_backtest.py) ───────
def scaled_triggers(mult=1.0):
    return {
        "t1": [v * mult for v in BASE_T1],
        "t2": [v * mult for v in BASE_T2],
        "t3": [v * mult for v in BASE_T3],
        "t1_weeks": 2, "t2_weeks": 3, "t3_weeks": 4,
        "rearm": BASE_REARM * mult,
    }

def run_lumpsum(df_slice):
    closes = df_slice["Close"].values
    return (PORTFOLIO / closes[0]) * closes

def run_strategy(df_slice):
    closes = df_slice["Close"].values
    dates  = df_slice.index
    n      = len(closes)
    trg    = scaled_triggers()

    lump_amt   = PORTFOLIO * LUMP_PCT
    dca_total  = PORTFOLIO * DCA_PCT
    res_total  = PORTFOLIO * RES_PCT
    dca_weekly = dca_total / (DCA_MONTHS * 4.33)

    t1_amt = res_total * TIER1_SHARE
    t2_amt = res_total * TIER2_SHARE
    t3_amt = res_total * TIER3_SHARE
    tranche_usd = {}
    for tier, pool in [(1,t1_amt),(2,t2_amt),(3,t3_amt)]:
        for sub in range(4):
            tranche_usd[(tier,sub)] = pool / 4.0

    shares    = lump_amt / closes[0]
    res_cash  = res_total
    dca_cash  = dca_total
    fired     = set()
    tier_bar  = {}
    last_buy  = -COOLDOWN_WEEKS
    rearms_yr = 0
    cur_year  = dates[0].year
    mm_weekly = (1 + MM_YIELD_ANNUAL) ** (1/52) - 1
    portfolio_vals = np.zeros(n)
    dca_end = min(int(DCA_MONTHS * 4.33), n)

    for i, (date, price) in enumerate(zip(dates, closes)):
        yr = date.year
        if yr != cur_year:
            cur_year = yr; rearms_yr = 0
        h52 = closes[max(0, i-52):i+1].max()
        dd  = (price - h52) / h52
        res_cash *= (1 + mm_weekly)
        if 0 < i < dca_end and dca_cash > 0:
            buy = min(dca_weekly, dca_cash)
            shares += buy / price; dca_cash -= buy
        if dd > trg["rearm"] and fired and rearms_yr < MAX_REARMS_PER_YEAR:
            fired = set(); tier_bar = {}; rearms_yr += 1

        def fire(tier, sub):
            nonlocal res_cash, shares, last_buy
            key = (tier, sub)
            if key in fired or res_cash < 1: return False
            amt = min(tranche_usd[key], res_cash)
            shares += amt / price; res_cash -= amt
            fired.add(key); last_buy = i; return True

        ok = (i - last_buy) >= COOLDOWN_WEEKS
        for sub_i, thr in enumerate(trg["t1"]):
            if ok and dd <= thr:
                if fire(1, sub_i): ok = False; tier_bar.setdefault(1, i)
        if 1 in tier_bar and ok:
            if (i - tier_bar[1]) >= trg["t1_weeks"] and dd <= trg["t1"][0]:
                if fire(1, 3): ok = False
        for sub_i, thr in enumerate(trg["t2"]):
            if ok and dd <= thr:
                if fire(2, sub_i): ok = False; tier_bar.setdefault(2, i)
        if 2 in tier_bar and ok:
            if (i - tier_bar[2]) >= trg["t2_weeks"] and dd <= trg["t2"][0]:
                if fire(2, 3): ok = False
        for sub_i, thr in enumerate(trg["t3"]):
            if ok and dd <= thr:
                if fire(3, sub_i): ok = False; tier_bar.setdefault(3, i)
        if 3 in tier_bar and ok:
            if (i - tier_bar[3]) >= trg["t3_weeks"] and dd <= trg["t3"][0]:
                fire(3, 3)
        portfolio_vals[i] = shares * price + res_cash + dca_cash

    return portfolio_vals, dates

# ── Download VOO weekly data ──────────────────────────────────────────────────
print("Downloading VOO weekly data...")
ticker = yf.Ticker("VOO")
df = ticker.history(start=DATA_START, end="2026-05-28", interval="1wk", auto_adjust=True)
df.index = pd.to_datetime(df.index).tz_localize(None)
df = df[["Close"]].dropna()
print(f"  {len(df)} weekly bars\n")

# ── Run all 20 quarters ───────────────────────────────────────────────────────
results = []
for qs, ql in zip(QUARTER_STARTS, QUARTER_LABELS):
    start_dt = pd.Timestamp(qs)
    end_dt   = pd.Timestamp(END_DATE)
    sl = df[(df.index >= start_dt) & (df.index <= end_dt)]
    if len(sl) == 0: continue
    vals, dates = run_strategy(sl)
    ls_vals     = run_lumpsum(sl)
    final = vals[-1]
    mult  = final / PORTFOLIO
    yrs   = (dates[-1] - dates[0]).days / 365.25
    cagr  = (final / PORTFOLIO) ** (1/max(yrs,1e-6)) - 1
    results.append(dict(label=ql, dates=dates, vals=vals, ls_vals=ls_vals,
                        final=final, mult=mult, cagr=cagr, year=int(ql[-2:])+2000))
    print(f"  {ql}  final=${final:>12,.0f}  ×{mult:.2f}  CAGR={cagr:.1%}")

# ── Colour scheme: one hue per starting year, 4 shades per year ──────────────
YEAR_COLORS = {
    2020: cm.Blues,
    2021: cm.Oranges,
    2022: cm.Reds,
    2023: cm.Greens,
    2024: cm.Purples,
}
SHADES = [0.45, 0.60, 0.75, 0.90]   # lightest → darkest within each year

year_quarter_idx = {}   # {year: [0,1,2,3]} quarter index within the year
for r in results:
    yr = r['year']
    year_quarter_idx.setdefault(yr, [])
    year_quarter_idx[yr].append(r)

def get_color(r):
    yr = r['year']
    cmap = YEAR_COLORS[yr]
    qi = year_quarter_idx[yr].index(r)
    return cmap(SHADES[qi])

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(17, 9))
fig.patch.set_facecolor('#f8f8f8')
ax.set_facecolor('#f8f8f8')

for r in results:
    color = get_color(r)
    # Lump sum — dashed, slightly transparent
    ax.plot(r['dates'], r['ls_vals'] / 1e6,
            color=color, linewidth=1.2, alpha=0.45, linestyle='--')
    # Dip-tranche strategy — solid
    ax.plot(r['dates'], r['vals'] / 1e6,
            color=color, linewidth=1.9, alpha=0.90, linestyle='-')
    # Label at end of strategy line only
    ls_final  = r['ls_vals'][-1] / 1e6
    str_final = r['vals'][-1] / 1e6
    gap       = str_final - ls_final
    sign      = '+' if gap >= 0 else ''
    ax.annotate(
        f"{r['label']}  {sign}${gap*1e6/1e3:.0f}k",
        xy=(r['dates'][-1], str_final),
        xytext=(6, 0), textcoords='offset points',
        fontsize=6.5, color=color, va='center', fontweight='bold'
    )

# $1M reference line
ax.axhline(1.0, color='#aaa', linewidth=1.0, linestyle=':', zorder=0)

# Shade key events
ax.axvspan(pd.Timestamp('2020-02-19'), pd.Timestamp('2020-03-23'),
           alpha=0.07, color='red', zorder=0)
ax.axvspan(pd.Timestamp('2022-01-01'), pd.Timestamp('2022-10-12'),
           alpha=0.05, color='orange', zorder=0)
ax.text(pd.Timestamp('2020-03-01'), 0.55, 'COVID\ncrash',
        fontsize=7, color='#cc0000', ha='center')
ax.text(pd.Timestamp('2022-05-15'), 0.55, '2022\nbear',
        fontsize=7, color='#cc6600', ha='center')

# Legend
legend_elems = []
for yr, cmap in YEAR_COLORS.items():
    legend_elems.append(Line2D([0],[0], color=cmap(0.70), lw=2.2, label=str(yr)))
legend_elems += [
    Line2D([0],[0], color='#555', lw=1.9, ls='-',  label='Dip-Tranche strategy'),
    Line2D([0],[0], color='#555', lw=1.2, ls='--', alpha=0.5, label='Lump Sum (all in day 1)'),
    Line2D([0],[0], color='#aaa', lw=1.0, ls=':',  label='$1M starting capital'),
]
ax.legend(handles=legend_elems, title='Starting year',
          loc='upper left', fontsize=8.5, title_fontsize=9, framealpha=0.88, ncol=2)

ax.set_title(
    'Dip-Tranche (solid) vs Lump Sum (dashed) — $1M, 18-month deployment\n'
    '20 quarterly entry points  ·  VOO  ·  End-label shows cash drag (strategy − lump sum)',
    fontsize=13, fontweight='bold', pad=14
)
ax.set_ylabel('Portfolio value ($M)', fontsize=11)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x:.1f}M'))
ax.grid(True, alpha=0.18, linestyle='--')
for sp in ['top','right']: ax.spines[sp].set_visible(False)

plt.tight_layout()
out = 'report/img/quarterly_fan_chart.png'
plt.savefig(out, dpi=160, bbox_inches='tight', facecolor='#f8f8f8')
print(f"\nSaved: {out}")
plt.close()
