#!/usr/bin/env python3
"""
Fundamental Stock-Selection Backtest — do real value/quality/moat screens beat the index?
=========================================================================================
The repo's earlier "Morningstar"/"value" backtests used PRICE proxies (distance-from-high),
not real fundamentals — and the crude version lost to VOO. This script answers the question
properly using the INVESTABLE versions of each stock-selection methodology: factor & strategy
ETFs whose index rules ARE the screen. That sidesteps the two traps of DIY fundamental
backtests (look-ahead bias from using today's fundamentals on past dates; survivorship bias
from only testing current index members) because each ETF rebalanced live, in real time.

Most relevant to the user's question:
  MOAT  = VanEck Morningstar Wide Moat ETF — literally implements Morningstar's stock picking:
          buy attractively-priced stocks with WIDE economic moats, using Morningstar analyst
          FAIR-VALUE estimates + MOAT ratings. If Morningstar's process beats the index, MOAT shows it.

Strategy ETFs tested vs SPY (each over its OWN full live history for a fair comparison):
  MOAT  Morningstar wide-moat + fair value     (2012-04)   <- "use Morningstar to pick stocks?"
  COWZ  Free-cash-flow yield ("cash cows")      (2016-12)   <- ~Acquirer's-Multiple / FCF value
  RPV   S&P 500 Pure Value                       (2006-03)   <- deep value factor (covers GFC)
  VLUE  MSCI USA Value Factor                    (2013-04)
  SPHQ  S&P 500 Quality                          (2005-12)   <- quality (covers GFC)
  QUAL  MSCI USA Quality Factor                  (2013-07)
  MTUM  MSCI USA Momentum Factor                 (2013-04)
  SCHD  Quality dividend                         (2011-10)
  NOBL  Dividend Aristocrats                      (2013-10)
  USMV  Min Volatility                            (2011-10)

Educational only — not advice. Caveats at the end.
"""
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import warnings, time
warnings.filterwarnings('ignore')

END = '2026-05-27'
RF = 0.02

STRATS = {
    'MOAT': 'Morningstar Wide-Moat (fair value + moat)',
    'COWZ': 'FCF Yield "Cash Cows"',
    'RPV':  'S&P 500 Pure Value',
    'VLUE': 'MSCI USA Value Factor',
    'SPHQ': 'S&P 500 Quality',
    'QUAL': 'MSCI USA Quality Factor',
    'MTUM': 'MSCI USA Momentum Factor',
    'SCHD': 'Quality Dividend',
    'NOBL': 'Dividend Aristocrats',
    'USMV': 'Min Volatility',
}
TICKERS = ['SPY'] + list(STRATS)

def robust_download(tickers, **kw):
    raw = yf.download(tickers, **kw)
    px = raw['Close'].copy()
    for _ in range(4):
        missing = [t for t in tickers if t not in px.columns or px[t].dropna().empty]
        if not missing:
            break
        time.sleep(2)
        c2 = yf.download(missing, **kw)['Close']
        if isinstance(c2, pd.Series):
            c2 = c2.to_frame(missing[0])
        for t in missing:
            if t in c2.columns and not c2[t].dropna().empty:
                px[t] = c2[t]
    return px

print("Downloading total-return ETF data...")
prices = robust_download(TICKERS, start='2005-01-01', end=END, auto_adjust=True, progress=False).ffill()
for t in TICKERS:
    s = prices[t].dropna() if t in prices.columns else pd.Series(dtype=float)
    print(f"  {t}: {s.index[0].date() if len(s) else 'MISSING'} ({len(s)} days)")

def metrics(px, rf=RF):
    px = px.dropna()
    if len(px) < 2:
        return None
    yrs = (px.index[-1] - px.index[0]).days / 365.25
    cagr = (px.iloc[-1] / px.iloc[0]) ** (1 / yrs) - 1
    r = px.pct_change().dropna()
    sharpe = (r.mean() * 252 - rf) / (r.std() * np.sqrt(252)) if r.std() > 0 else 0
    maxdd = (px / px.cummax() - 1).min()
    return {'CAGR': cagr, 'Sharpe': sharpe, 'MaxDD': maxdd, 'years': yrs}

# =============================================================================
# HEAD-TO-HEAD vs SPY over each ETF's OWN full history (fair, same-window compare)
# =============================================================================
print("\n" + "=" * 100)
print("EACH STRATEGY vs SPY — over the strategy's own full live history (same window for both)")
print("=" * 100)
rows = []
for t, label in STRATS.items():
    s = prices[t].dropna()
    if len(s) < 60:
        continue
    start = s.index[0]
    spy = prices['SPY'][prices['SPY'].index >= start].dropna()
    common = s.index.intersection(spy.index)
    ms, msp = metrics(s.loc[common]), metrics(spy.loc[common])
    rows.append({
        'Strategy (ETF)': f"{t}",
        'Methodology': label,
        'Since': str(start.date()),
        'CAGR': f"{ms['CAGR']*100:.1f}%",
        'SPY CAGR': f"{msp['CAGR']*100:.1f}%",
        'Beat SPY?': 'YES' if ms['CAGR'] > msp['CAGR'] else 'no',
        'Sharpe': f"{ms['Sharpe']:.2f}",
        'SPY Sh': f"{msp['Sharpe']:.2f}",
        'MaxDD': f"{ms['MaxDD']*100:.0f}%",
        'SPY DD': f"{msp['MaxDD']*100:.0f}%",
    })
res = pd.DataFrame(rows)
print(res.to_string(index=False))
n_beat = sum(1 for r in rows if r['Beat SPY?'] == 'YES')
print(f"\n  Strategies that beat SPY on CAGR over their own history: {n_beat}/{len(rows)}")
print(f"  Strategies with HIGHER Sharpe than SPY: "
      f"{sum(1 for r in rows if float(r['Sharpe'])>float(r['SPY Sh']))}/{len(rows)}")

# =============================================================================
# CRISIS WINDOWS (drawdown defense of the screens)
# =============================================================================
print("\n" + "=" * 100)
print("CRISIS WINDOWS — total return (max drawdown). Defensive screens should lose less.")
print("=" * 100)
crises = [
    ('GFC 2007-09', '2007-10-09', '2009-03-09'),
    ('COVID 2020',  '2020-02-19', '2020-03-23'),
    ('2022 bear',   '2022-01-03', '2022-10-12'),
    ('AI bull 2023-26', '2023-01-01', END),
]
for cname, cs, ce in crises:
    print(f"\n--- {cname} ({cs} -> {ce}) ---")
    rr = []
    for t in TICKERS:
        sub = prices[t][(prices[t].index >= cs) & (prices[t].index <= ce)].dropna()
        if len(sub) < 2:
            rr.append({'ETF': t, 'Return': 'n/a', 'MaxDD': 'n/a'}); continue
        rr.append({'ETF': t,
                   'Return': f"{(sub.iloc[-1]/sub.iloc[0]-1)*100:+.1f}%",
                   'MaxDD': f"{(sub/sub.cummax()-1).min()*100:.0f}%"})
    print(pd.DataFrame(rr).to_string(index=False))

# =============================================================================
# COMMON-PERIOD equity curves (chart) from the latest common inception
# =============================================================================
common_start = max(prices[t].dropna().index[0] for t in TICKERS)
print(f"\nCommon period for chart: {common_start.date()} -> {END}")
sub = prices[prices.index >= common_start].dropna()
norm = sub / sub.iloc[0] * 1_000_000

fig, ax = plt.subplots(figsize=(14, 8))
for t in TICKERS:
    lw = 2.6 if t == 'SPY' else 1.3
    ax.plot(norm.index, norm[t], label=f"{t} ({STRATS.get(t,'S&P 500')[:28]})", linewidth=lw)
ax.set_yscale('log')
ax.set_title(f'Stock-Selection Strategy ETFs vs SPY (total return, $1M, {common_start.date()}-2026)', fontsize=12)
ax.set_ylabel('Value (log)')
ax.legend(loc='upper left', fontsize=8)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/img/fundamental_screens_backtest.png', dpi=150)
print("Chart saved to report/img/fundamental_screens_backtest.png")

print("\n" + "=" * 100)
print("CAVEATS")
print("=" * 100)
print("""
1. Strategy ETFs are SURVIVORSHIP/LOOK-AHEAD SAFE proxies for each screen: the index rules were
   applied live in real time, so this avoids the #1 DIY trap (using today's fundamentals on past dates).
2. They include real expense ratios (0.2-0.6%) but NOT the investor's trading costs/taxes.
3. Each ETF is judged over ITS OWN history vs SPY in the same window — different windows are not
   directly comparable across rows (RPV/SPHQ include the GFC; the 2013-cohort does not).
4. An ETF is only an APPROXIMATION of the pure academic strategy (Magic Formula, Piotroski, etc.):
   indexes add liquidity screens, caps, and reconstitution rules.
5. MOAT is the closest investable proxy to "use Morningstar fair-value + moat ratings to pick stocks."
""")
print("DONE")
