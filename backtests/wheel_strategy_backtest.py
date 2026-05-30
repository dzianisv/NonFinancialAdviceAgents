"""
Wheel/Theta Strategy Backtest - SIMULATION/APPROXIMATION
=========================================================
NOTE: This uses synthetic options pricing via Black-Scholes approximation.
No real historical options data is used. Results are illustrative only.

Strategies:
1. Cash-Secured Put (CSP) on SPY - monthly 30-delta puts
2. Covered Call (CC) overlay on VOO/SPY
3. The Wheel (CSP -> CC -> CSP cycling)

Baselines:
- VOO lump sum: 15.6% CAGR, Sharpe 0.69
- Pelosi portfolio: 20.0% CAGR, Sharpe 0.68
"""

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import norm
import warnings
warnings.filterwarnings('ignore')

# ── Parameters ──────────────────────────────────────────────────────────────
START = "2020-01-01"
END   = "2026-05-27"
CAPITAL = 1_000_000
RF_ANNUAL = 0.04
RF_MONTHLY = RF_ANNUAL / 12
VOL_RISK_PREMIUM = 1.2   # IV = realized vol * 1.2
DELTA_TARGET = 0.30      # 30-delta options
T = 1/12                 # 1-month expiry

# ── Data ────────────────────────────────────────────────────────────────────
print("Downloading SPY data...")
spy_raw = yf.download("SPY", start="2019-06-01", end=END, auto_adjust=True, progress=False)
spy = spy_raw["Close"]
if isinstance(spy, pd.DataFrame):
    spy = spy.iloc[:, 0]
spy = spy.squeeze().dropna()

# ── Helper: realized vol (21-day) ───────────────────────────────────────────
def realized_vol(prices, window=21):
    log_rets = np.log(prices / prices.shift(1)).dropna()
    return log_rets.rolling(window).std() * np.sqrt(252)

# ── Helper: BS 30-delta put premium approximation ──────────────────────────
def bs_put_premium(S, iv_annual, T=1/12, rf=RF_ANNUAL, delta_target=0.30):
    """
    Find strike K such that put delta = -delta_target, then price it.
    For a put: delta = N(d1) - 1  =>  d1 = N_inv(1 - delta_target)
    K = S * exp(-d1*sigma*sqrt(T) + (rf - 0.5*sigma^2)*T)
    """
    sigma = iv_annual
    d1_target = norm.ppf(1 - delta_target)  # ~= -0.524 for 30-delta
    K = S * np.exp(-d1_target * sigma * np.sqrt(T) + (rf - 0.5*sigma**2) * T)
    # BS put price
    d1 = (np.log(S/K) + (rf + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    put = K * np.exp(-rf*T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    return K, max(put, 0.0)

def bs_call_premium(S, iv_annual, T=1/12, rf=RF_ANNUAL, delta_target=0.30):
    """
    Find strike K such that call delta = delta_target.
    For a call: delta = N(d1)  =>  d1 = N_inv(delta_target)
    """
    sigma = iv_annual
    d1_target = norm.ppf(delta_target)   # ~= -0.524 → strike above S
    K = S * np.exp(-d1_target * sigma * np.sqrt(T) + (rf - 0.5*sigma**2) * T)
    d1 = (np.log(S/K) + (rf + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    call = S * norm.cdf(d1) - K * np.exp(-rf*T) * norm.cdf(d2)
    return K, max(call, 0.0)

# ── Build monthly trading calendar ──────────────────────────────────────────
spy_start = spy[spy.index >= START]
monthly_starts = spy_start.resample("MS").first().index  # month starts
monthly = []
for ms in monthly_starts:
    # first available trading day of month
    avail = spy_start[spy_start.index >= ms]
    if len(avail) == 0:
        continue
    open_day = avail.index[0]
    # last available trading day of same month
    me = ms + pd.offsets.MonthEnd(0)
    avail_end = spy_start[spy_start.index <= me]
    if len(avail_end) == 0:
        continue
    close_day = avail_end.index[-1]
    if open_day < close_day:
        monthly.append((open_day, close_day))

print(f"Trading months: {len(monthly)}")

rv = realized_vol(spy)

# ── Performance metrics ──────────────────────────────────────────────────────
def cagr(values, dates):
    years = (dates[-1] - dates[0]).days / 365.25
    return (values[-1] / values[0]) ** (1/years) - 1

def sharpe(daily_returns, rf=RF_ANNUAL):
    excess = daily_returns - rf/252
    if excess.std() == 0:
        return 0
    return excess.mean() / excess.std() * np.sqrt(252)

def max_drawdown(values):
    arr = np.array(values)
    peak = np.maximum.accumulate(arr)
    dd = (arr - peak) / peak
    return dd.min()

# ═══════════════════════════════════════════════════════════════════════════
# STRATEGY 1: Cash-Secured Put (CSP)
# ═══════════════════════════════════════════════════════════════════════════
print("\nRunning Strategy 1: Cash-Secured Put...")

csp_dates = [spy_start.index[0]]
csp_vals  = [CAPITAL]
cash = CAPITAL

for open_day, close_day in monthly:
    S_open  = spy_start[open_day]
    S_close = spy_start[close_day]

    # IV estimate: realized vol at open * risk premium
    rv_val = rv.get(open_day, np.nan)
    if np.isnan(rv_val) or rv_val <= 0:
        rv_val = 0.20
    iv = rv_val * VOL_RISK_PREMIUM

    # 1 contract = 100 shares; how many contracts fit in cash?
    contracts = int(cash / (S_open * 100))
    if contracts < 1:
        contracts = 1
    notional = contracts * 100 * S_open

    K, premium_per_share = bs_put_premium(S_open, iv)
    total_premium = premium_per_share * 100 * contracts

    # Cash not used earns risk-free
    idle_cash = cash - notional
    rf_income = idle_cash * RF_MONTHLY

    if S_close < K:
        # Assigned: buy shares at K, immediately mark to S_close
        assignment_loss = (K - S_close) * 100 * contracts
        pnl = total_premium - assignment_loss + rf_income
    else:
        pnl = total_premium + rf_income

    cash += pnl

    # daily interpolation for drawdown tracking
    mask = (spy_start.index > open_day) & (spy_start.index <= close_day)
    days = spy_start[mask]
    for d in days.index:
        csp_dates.append(d)
        csp_vals.append(cash)

csp_series = pd.Series(csp_vals, index=csp_dates).sort_index()
csp_daily_ret = csp_series.pct_change().dropna()

csp_cagr = cagr(csp_vals, csp_dates)
csp_sharpe = sharpe(csp_daily_ret)
csp_dd = max_drawdown(csp_vals)

# ═══════════════════════════════════════════════════════════════════════════
# STRATEGY 2: Covered Call overlay on SPY buy-and-hold
# ═══════════════════════════════════════════════════════════════════════════
print("Running Strategy 2: Covered Call...")

cc_dates = [spy_start.index[0]]
shares = CAPITAL / spy_start.iloc[0]
cc_cash = 0.0
cc_vals = [CAPITAL]

for open_day, close_day in monthly:
    S_open  = spy_start[open_day]
    S_close = spy_start[close_day]

    rv_val = rv.get(open_day, np.nan)
    if np.isnan(rv_val) or rv_val <= 0:
        rv_val = 0.20
    iv = rv_val * VOL_RISK_PREMIUM

    contracts = int(shares / 100)
    if contracts < 1:
        # track without options
        mask = (spy_start.index > open_day) & (spy_start.index <= close_day)
        days = spy_start[mask]
        for d in days.index:
            cc_dates.append(d)
            cc_vals.append(shares * spy_start[d] + cc_cash)
        continue

    K_call, premium_per_share = bs_call_premium(S_open, iv)
    total_premium = premium_per_share * 100 * contracts

    if S_close > K_call:
        # Called away: sell at K_call, not S_close
        effective_price = K_call
        shares_sold = contracts * 100
        cc_cash += shares_sold * effective_price + total_premium
        shares -= shares_sold
        # Immediately rebuy at S_close to stay invested
        rebuy = int(cc_cash / S_close)
        shares += rebuy
        cc_cash -= rebuy * S_close
    else:
        cc_cash += total_premium

    mask = (spy_start.index > open_day) & (spy_start.index <= close_day)
    days = spy_start[mask]
    for d in days.index:
        cc_dates.append(d)
        cc_vals.append(shares * spy_start[d] + cc_cash)

cc_series = pd.Series(cc_vals, index=cc_dates).sort_index()
cc_daily_ret = cc_series.pct_change().dropna()

cc_cagr = cagr(cc_vals, cc_dates)
cc_sharpe = sharpe(cc_daily_ret)
cc_dd = max_drawdown(cc_vals)

# ═══════════════════════════════════════════════════════════════════════════
# STRATEGY 3: The Wheel (CSP → CC → CSP)
# ═══════════════════════════════════════════════════════════════════════════
print("Running Strategy 3: The Wheel...")

whl_dates = [spy_start.index[0]]
whl_vals  = [CAPITAL]
whl_cash  = CAPITAL
whl_shares = 0
whl_mode   = "CSP"          # start selling puts
whl_assignment_price = None

for open_day, close_day in monthly:
    S_open  = spy_start[open_day]
    S_close = spy_start[close_day]

    rv_val = rv.get(open_day, np.nan)
    if np.isnan(rv_val) or rv_val <= 0:
        rv_val = 0.20
    iv = rv_val * VOL_RISK_PREMIUM

    portfolio_val = whl_cash + whl_shares * S_open

    if whl_mode == "CSP":
        contracts = int(whl_cash / (S_open * 100))
        if contracts < 1:
            contracts = 1
        notional = contracts * 100 * S_open
        K, prem = bs_put_premium(S_open, iv)
        total_prem = prem * 100 * contracts
        idle = whl_cash - notional
        rf_inc = idle * RF_MONTHLY

        if S_close < K:
            # Assigned – buy shares at strike K (worse than market)
            # Cash was used as collateral; now convert to shares
            cost_basis = K * 100 * contracts   # what we pay for shares
            whl_cash = whl_cash - cost_basis + total_prem + rf_inc
            whl_shares += contracts * 100
            whl_assignment_price = K
            whl_mode = "CC"
        else:
            whl_cash += total_prem + rf_inc

    else:  # CC mode
        contracts = int(whl_shares / 100)
        if contracts >= 1:
            K_call, prem = bs_call_premium(S_open, iv)
            total_prem = prem * 100 * contracts

            if S_close > K_call:
                # Called away
                whl_cash += contracts * 100 * K_call + total_prem
                whl_shares -= contracts * 100
                whl_mode = "CSP"
                whl_assignment_price = None
            else:
                whl_cash += total_prem
                # Check if recovered to assignment price
                if whl_assignment_price and S_close >= whl_assignment_price:
                    # Sell shares at market, return to CSP
                    whl_cash += whl_shares * S_close
                    whl_shares = 0
                    whl_mode = "CSP"

    mask = (spy_start.index > open_day) & (spy_start.index <= close_day)
    days = spy_start[mask]
    for d in days.index:
        whl_dates.append(d)
        whl_vals.append(whl_cash + whl_shares * spy_start[d])

whl_series = pd.Series(whl_vals, index=whl_dates).sort_index()
whl_daily_ret = whl_series.pct_change().dropna()

whl_cagr = cagr(whl_vals, whl_dates)
whl_sharpe = sharpe(whl_daily_ret)
whl_dd = max_drawdown(whl_vals)

# ═══════════════════════════════════════════════════════════════════════════
# BASELINE: VOO Buy-and-Hold
# ═══════════════════════════════════════════════════════════════════════════
print("Computing VOO baseline...")
voo_raw = yf.download("VOO", start=START, end=END, auto_adjust=True, progress=False)
voo = voo_raw["Close"]
if isinstance(voo, pd.DataFrame):
    voo = voo.iloc[:, 0]
voo = voo.squeeze().dropna()
voo_norm = CAPITAL * voo / voo.iloc[0]
voo_ret = voo.pct_change().dropna()
voo_cagr = cagr(voo_norm.values, voo_norm.index)
voo_sharpe = sharpe(voo_ret)
voo_dd = max_drawdown(voo_norm.values)

# ═══════════════════════════════════════════════════════════════════════════
# CHART
# ═══════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(2, 1, figsize=(14, 10))

ax = axes[0]
ax.plot(voo_norm.index, voo_norm.values/1e6, label=f"VOO B&H ({voo_cagr:.1%} CAGR)", color='gray', linewidth=2)
ax.plot(csp_series.index, np.array(csp_vals[:len(csp_series)])/1e6, label=f"CSP ({csp_cagr:.1%} CAGR)", color='blue', linewidth=1.8)
ax.plot(cc_series.index, np.array(cc_vals[:len(cc_series)])/1e6, label=f"Covered Call ({cc_cagr:.1%} CAGR)", color='green', linewidth=1.8)
ax.plot(whl_series.index, np.array(whl_vals[:len(whl_series)])/1e6, label=f"Wheel ({whl_cagr:.1%} CAGR)", color='darkorange', linewidth=1.8)
ax.set_title("Wheel/Theta Strategy Backtest — $1M Starting Capital\n⚠ SIMULATION using Black-Scholes approximation — NOT real options data", fontsize=12)
ax.set_ylabel("Portfolio Value ($M)")
ax.legend(loc='upper left')
ax.grid(True, alpha=0.3)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x:.2f}M'))

# Drawdown chart
ax2 = axes[1]
def dd_series(vals, dates):
    arr = np.array(vals)
    peak = np.maximum.accumulate(arr)
    return pd.Series((arr - peak)/peak * 100, index=dates[:len(arr)])

ax2.fill_between(voo_norm.index, (voo_norm.values/np.maximum.accumulate(voo_norm.values) - 1)*100, 0, alpha=0.3, color='gray', label='VOO')
csp_dd_s = dd_series(csp_vals, csp_dates)
cc_dd_s  = dd_series(cc_vals, cc_dates)
whl_dd_s = dd_series(whl_vals, whl_dates)
ax2.plot(csp_dd_s.index, csp_dd_s.values, color='blue', linewidth=1.2, label='CSP')
ax2.plot(cc_dd_s.index, cc_dd_s.values, color='green', linewidth=1.2, label='Covered Call')
ax2.plot(whl_dd_s.index, whl_dd_s.values, color='darkorange', linewidth=1.2, label='Wheel')
ax2.set_ylabel("Drawdown (%)")
ax2.set_title("Drawdown")
ax2.legend(loc='lower left')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("report/img/wheel_strategy_backtest.png", dpi=150, bbox_inches='tight')
print("Chart saved.")

# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════
print()
print("=" * 65)
print("  WHEEL / THETA STRATEGY BACKTEST — SIMULATION RESULTS")
print("  Period: 2020-01-01 to 2026-05-27  |  Starting Capital: $1M")
print("  ⚠  APPROXIMATION: synthetic BS pricing, no real options data")
print("=" * 65)
print(f"{'Strategy':<28} {'CAGR':>8} {'Sharpe':>8} {'Max DD':>9} {'Final $':>12}")
print("-" * 65)
print(f"{'VOO Buy & Hold':<28} {voo_cagr:>8.2%} {voo_sharpe:>8.2f} {voo_dd:>9.2%} ${voo_norm.values[-1]/1e6:>10.3f}M")
print(f"{'Cash-Secured Put (CSP)':<28} {csp_cagr:>8.2%} {csp_sharpe:>8.2f} {csp_dd:>9.2%} ${csp_vals[-1]/1e6:>10.3f}M")
print(f"{'Covered Call Overlay':<28} {cc_cagr:>8.2%} {cc_sharpe:>8.2f} {cc_dd:>9.2%} ${cc_vals[-1]/1e6:>10.3f}M")
print(f"{'The Wheel':<28} {whl_cagr:>8.2%} {whl_sharpe:>8.2f} {whl_dd:>9.2%} ${whl_vals[-1]/1e6:>10.3f}M")
print("=" * 65)
print()
print("  BASELINES TO BEAT:")
print(f"    VOO lump sum target:  15.6% CAGR, Sharpe 0.69")
print(f"    Pelosi portfolio:     20.0% CAGR, Sharpe 0.68")
print()
print("  BEATS VOO CAGR (>15.6%)?")
print(f"    CSP:           {'✓ YES' if csp_cagr > 0.156 else '✗ NO '} ({csp_cagr:.2%})")
print(f"    Covered Call:  {'✓ YES' if cc_cagr > 0.156 else '✗ NO '} ({cc_cagr:.2%})")
print(f"    Wheel:         {'✓ YES' if whl_cagr > 0.156 else '✗ NO '} ({whl_cagr:.2%})")
print()
print("  BEATS PELOSI (>20.0%)?")
print(f"    CSP:           {'✓ YES' if csp_cagr > 0.20 else '✗ NO '} ({csp_cagr:.2%})")
print(f"    Covered Call:  {'✓ YES' if cc_cagr > 0.20 else '✗ NO '} ({cc_cagr:.2%})")
print(f"    Wheel:         {'✓ YES' if whl_cagr > 0.20 else '✗ NO '} ({whl_cagr:.2%})")
print()
print("  BEATS VOO SHARPE (>0.69)?")
print(f"    CSP:           {'✓ YES' if csp_sharpe > 0.69 else '✗ NO '} ({csp_sharpe:.2f})")
print(f"    Covered Call:  {'✓ YES' if cc_sharpe > 0.69 else '✗ NO '} ({cc_sharpe:.2f})")
print(f"    Wheel:         {'✓ YES' if whl_sharpe > 0.69 else '✗ NO '} ({whl_sharpe:.2f})")
print()
print("  NOTE: Simulation uses Black-Scholes 30-delta approximation with")
print("  IV = realized 21-day vol × 1.2 vol-risk-premium. No transaction")
print("  costs, slippage, or early assignment modeled. Results are")
print("  directionally illustrative, not investment advice.")
print("=" * 65)
