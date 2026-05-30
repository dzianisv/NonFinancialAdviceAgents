#!/usr/bin/env python3
"""
v3 Proxy Backtest (2000-2026)
=============================
Tests the v3 Balanced allocation through 2000-2026 using long-history proxies
for ETFs that were not yet trading.  The central question: does the actual v3
Balanced portfolio hold up through dot-com, GFC, COVID, and 2022, or is the
thesis just backsight?

v3 Balanced weights (fully deployed):
    RSP  18%  US large-cap equal-weight
    VXUS 12%  International
    AVUV  8%  US small/mid-value
    USMV  7%  Min-vol / quality
    GLD  10%  Gold
    DBMF 10%  Trend / managed futures
    TLT   7%  Long Treasuries
    SCHP  3%  TIPS
    SGOV 22%  Dry powder (dip reserve) — earns T-bill
    BTAL  3%  Tail / anti-beta

Proxy mapping (return-splice: real ETF returns when available, proxy before):
    RSP   → VFINX (pre-2003, cap-wt S&P — UNDERSTATES eq-wt de-concentration)
    VXUS  → VGTSX (whole history; VXUS 2011+ spliced on)
    AVUV  → VISVX (pre-2019, passive small-value — slight understatement of
              Avantis profitability screen)
    USMV  → VFINX (pre-2011, plain S&P — UNDERSTATES min-vol drawdown cushion)
    GLD   → GC=F  (pre-2004 gold futures)
    DBMF  → TSMOM proxy (pre-2019: multi-asset 12m momentum S&P/bond/gold;
              simple but captures crisis alpha better than 200d SMA)
    TLT   → VUSTX (pre-2002, Vanguard Long Treasury)
    SCHP  → VIPSX (pre-2010, Vanguard Inflation-Protected)
    SGOV  → CASH accrual (T-bill; no download needed)
    BTAL  → CASH (pre-2011 — UNDERSTATES crash protection; conservative)

NOTE: educational backtest, not investment advice. Caveats printed at the end.
"""

import time
import warnings
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

warnings.filterwarnings('ignore')

# =============================================================================
# PARAMETERS
# =============================================================================
WARMUP_START = '1999-06-01'   # extra history for 12m momentum warmup
START        = '2000-01-01'   # metrics reported from here
END          = '2026-05-27'
INITIAL_CAPITAL = 1_000_000

# v3 Balanced target weights
V3_WEIGHTS = {
    'RSP_sleeve':  0.18,
    'VXUS_sleeve': 0.12,
    'AVUV_sleeve': 0.08,
    'USMV_sleeve': 0.07,
    'GLD_sleeve':  0.10,
    'DBMF_sleeve': 0.10,
    'TLT_sleeve':  0.07,
    'SCHP_sleeve': 0.03,
    'SGOV_sleeve': 0.22,
    'BTAL_sleeve': 0.03,
}
assert abs(sum(V3_WEIGHTS.values()) - 1.0) < 1e-9, "Weights must sum to 1"

# Risk-sleeve weights (non-SGOV), used for pro-rata deployment
RISK_SLEEVES = [k for k in V3_WEIGHTS if k != 'SGOV_sleeve']

# =============================================================================
# TIME-VARYING RISK-FREE RATE (copied from crash_protection_backtest.py)
# =============================================================================
def rf_for(date):
    y = date.year
    if y <= 2001: return 0.055   # 2000-2001 high rates
    if y <= 2004: return 0.015   # post dot-com cuts
    if y <= 2007: return 0.045   # mid-2000s
    if y <= 2015: return 0.001   # ZIRP
    if y <= 2019: return 0.018   # gradual hikes
    if y <= 2021: return 0.001   # COVID ZIRP
    if y <= 2023: return 0.045   # hiking cycle
    return 0.043                 # 2024+

RF_AVG = 0.025  # whole-period Sharpe denominator

# =============================================================================
# DATA DOWNLOAD
# =============================================================================
PROXY_TICKERS = [
    'VFINX',   # S&P 500 proxy for RSP (pre-2003) + USMV (pre-2011) + TSMOM
    'VGTSX',   # Vanguard Total Intl → VXUS proxy
    'VISVX',   # Vanguard Small Value → AVUV proxy
    'GC=F',    # Gold futures → GLD proxy (and TSMOM)
    'VUSTX',   # Vanguard LT Treasury → TLT proxy (and TSMOM)
    'VIPSX',   # Vanguard Inflation-Protected → SCHP proxy
]
REAL_TICKERS = [
    'RSP',
    'VXUS',
    'AVUV',
    'USMV',
    'GLD',
    'DBMF',
    'TLT',
    'SCHP',
    'BTAL',
    'QQQ',
]
ALL_TICKERS = PROXY_TICKERS + REAL_TICKERS


def robust_download(tickers, **kw):
    """Download with retry for any ticker that comes back all-NaN (yfinance cache locks).
    Adapted from crash_protection_backtest.py."""
    raw = yf.download(tickers, **kw)
    # handle MultiIndex or single-ticker
    if isinstance(raw.columns, pd.MultiIndex):
        px = raw['Close'].copy()
    else:
        px = raw[['Close']].copy() if 'Close' in raw.columns else raw.copy()
        if len(tickers) == 1:
            px.columns = tickers
    for attempt in range(4):
        missing = [t for t in tickers if t not in px.columns or px[t].dropna().empty]
        if not missing:
            break
        time.sleep(2)
        r2 = yf.download(missing, **kw)
        if isinstance(r2.columns, pd.MultiIndex):
            c2 = r2['Close']
        else:
            c2 = r2[['Close']].copy() if 'Close' in r2.columns else r2.copy()
            if len(missing) == 1:
                c2.columns = missing
        for t in missing:
            if t in c2.columns and not c2[t].dropna().empty:
                px[t] = c2[t]
    return px


print("Downloading proxy tickers...")
px_proxy = robust_download(
    PROXY_TICKERS,
    start=WARMUP_START, end=END, auto_adjust=True, progress=False
).ffill()

print("Downloading real ETF tickers...")
px_real = robust_download(
    REAL_TICKERS,
    start=WARMUP_START, end=END, auto_adjust=True, progress=False
).ffill()

# Merge on a common daily index
all_px = px_proxy.join(px_real, how='outer')

print(f"\nRaw shape: {all_px.shape}")
for t in ALL_TICKERS:
    if t in all_px.columns and not all_px[t].dropna().empty:
        s = all_px[t].dropna()
        print(f"  {t}: {s.index[0].date()} -> {s.index[-1].date()}  ({len(s)} days)")
    else:
        print(f"  {t}: MISSING")

# =============================================================================
# CASH ACCRUAL SERIES  (from crash_protection_backtest.py)
# =============================================================================
cal = all_px.index
cash_series = pd.Series(1.0, index=cal)
prev = None
acc = 1.0
for d in cal:
    if prev is not None:
        days = (d - prev).days
        acc *= (1 + rf_for(d)) ** (days / 365.25)
    cash_series[d] = acc
    prev = d
cash_series = cash_series * 100.0  # arbitrary base

# =============================================================================
# HELPERS
# =============================================================================

def compute_metrics(equity, rf=RF_AVG):
    """CAGR / Sharpe / Sortino / MaxDD / Calmar. Adapted from crash_protection_backtest.py."""
    equity = equity.dropna()
    if len(equity) < 2:
        return {'CAGR': 0, 'Sharpe': 0, 'Sortino': 0, 'MaxDD': 0, 'Calmar': np.nan, 'Final': np.nan}
    yrs = (equity.index[-1] - equity.index[0]).days / 365.25
    cagr = (equity.iloc[-1] / equity.iloc[0]) ** (1 / yrs) - 1 if yrs > 0 else 0
    r = equity.pct_change().dropna()
    sharpe = (r.mean() * 252 - rf) / (r.std() * np.sqrt(252)) if r.std() > 0 else 0
    downside = r[r < 0].std() * np.sqrt(252)
    sortino = (r.mean() * 252 - rf) / downside if downside > 0 else 0
    dd = equity / equity.cummax() - 1
    maxdd = dd.min()
    calmar = cagr / abs(maxdd) if maxdd < 0 else np.nan
    return {'CAGR': cagr, 'Sharpe': sharpe, 'Sortino': sortino,
            'MaxDD': maxdd, 'Calmar': calmar, 'Final': equity.iloc[-1]}


def month_end_dates(idx, start, end):
    """Return list of month-end trading dates within [start, end].
    Adapted from crash_protection_backtest.py — uses 'M' groupby to avoid
    deprecated 'ME' freq string issues."""
    mask = (idx >= start) & (idx <= end)
    sub = idx[mask]
    out = []
    for (y, m), grp in pd.Series(sub, index=sub).groupby([sub.year, sub.month]):
        out.append(grp.iloc[-1])
    return out


def static_portfolio(sleeve_px, weights, start, end, rebal='Y', name='Portfolio'):
    """Fixed-weight basket with periodic rebalancing (annual or monthly).
    sleeve_px: DataFrame of price series (one column per sleeve).
    weights: dict sleeve_name -> weight.
    Adapted from crash_protection_backtest.py."""
    cols = [t for t in weights if t in sleeve_px.columns]
    w = np.array([weights[t] for t in cols])
    w = w / w.sum()
    px = sleeve_px[cols].copy()
    mask = (px.index >= start) & (px.index <= end)
    px = px[mask].dropna(how='all').ffill()
    if len(px) < 2:
        return pd.Series(dtype=float, name=name)

    # rebalance dates
    if rebal == 'Y':
        rebs = set()
        for yr, grp in px.groupby(px.index.year):
            rebs.add(grp.index[0])
    elif rebal == 'M':
        rebs = set(g.index[0] for _, g in px.groupby([px.index.year, px.index.month]))
    else:
        rebs = {px.index[0]}
    rebs.add(px.index[0])

    wmap = {t: w[j] for j, t in enumerate(cols)}
    capital = float(INITIAL_CAPITAL)
    shares = {}
    equity = pd.Series(index=px.index, dtype=float)
    for i, d in enumerate(px.index):
        if shares:
            capital = sum(sh * px.loc[d, t] for t, sh in shares.items()
                          if pd.notna(px.loc[d, t]))
        if d in rebs:
            avail = [t for t in cols if pd.notna(px.loc[d, t]) and px.loc[d, t] > 0]
            wsum = sum(wmap[t] for t in avail)
            shares = {}
            if wsum > 0:
                for t in avail:
                    shares[t] = capital * (wmap[t] / wsum) / px.loc[d, t]
        equity.iloc[i] = capital
    equity.name = name
    return equity


# =============================================================================
# RETURN SPLICE
# =============================================================================

def splice(proxy_series, real_series, name='spliced'):
    """Combine proxy and real ETF into one continuous price series via RETURN splice.
    Uses proxy returns where real ETF has no data, real ETF returns otherwise.
    No look-ahead: we simply use whichever series has data on a given date.
    Returns a price series starting at 100.0 on the first available date."""
    # align on union of dates
    combined = pd.DataFrame({'proxy': proxy_series, 'real': real_series})
    # compute daily returns from each; prefer real when available
    proxy_ret = combined['proxy'].pct_change()
    real_ret  = combined['real'].pct_change()
    # use real return when real has valid data (non-NaN), else proxy
    merged_ret = proxy_ret.copy()
    has_real = combined['real'].notna() & combined['real'].gt(0)
    # find the first real date
    first_real = combined['real'].first_valid_index()
    if first_real is not None:
        # from first_real onward, use real returns (if actually a number), else proxy
        # Gate on real_ret.notna() (not has_real) so the launch day itself — where
        # real_ret is NaN because pct_change() has no prior price — falls back to
        # the proxy return instead of propagating NaN → fillna(0) artifact.
        use_real = real_ret.notna()
        merged_ret.loc[first_real:] = np.where(
            use_real.loc[first_real:],
            real_ret.loc[first_real:],
            proxy_ret.loc[first_real:]
        )
    # compound from a base of 100
    merged_ret = merged_ret.fillna(0.0)
    price = (1 + merged_ret).cumprod() * 100.0
    price.name = name
    return price


# =============================================================================
# TSMOM PROXY  (for DBMF managed-futures sleeve, per D2)
# =============================================================================

def tsmom_proxy(sp_series, bond_series, gold_series, cash_series_in):
    """Multi-asset 12-month time-series momentum managed-futures proxy.

    Monthly, for each of [S&P (VFINX), long bond (VUSTX), gold (GC=F)]:
      - Compute trailing 12-month (252-trading-day) return using ONLY past data.
      - If positive: hold that asset that month.
      - If negative or NaN: hold CASH.
    Equal-weight the three sleeves. Rebalance at each month-end.
    Returns a daily price equity curve starting at 100.0.

    NO LOOK-AHEAD: signal at month-end d uses price[d] / price[d-252] - 1.
    The position set at d is carried into the next month.
    """
    # build a dataframe of the underlying price series
    assets = pd.DataFrame({
        'sp':   sp_series,
        'bond': bond_series,
        'gold': gold_series,
        'cash': cash_series_in,
    }).ffill()

    # get all month-end dates across the full data range
    full_idx = assets.index
    rebal_dates = month_end_dates(full_idx, full_idx[0], full_idx[-1])
    rebal_set = set(rebal_dates)

    # precompute returns from each series
    # We'll track shares in each of the 3 sub-strategies + cash
    # Each sub-strategy holds either the asset or cash (1/3 of capital each)
    # We'll represent the three sub-strategies as three separate positions

    capital = 100.0  # base = 100
    # initial positions: all cash
    holdings = {
        'sp':   {'in_asset': False, 'shares_asset': 0.0, 'shares_cash': capital / 3 / assets['cash'].iloc[0]},
        'bond': {'in_asset': False, 'shares_asset': 0.0, 'shares_cash': capital / 3 / assets['cash'].iloc[0]},
        'gold': {'in_asset': False, 'shares_asset': 0.0, 'shares_cash': capital / 3 / assets['cash'].iloc[0]},
    }

    equity = pd.Series(index=full_idx, dtype=float)
    full_idx_list = list(full_idx)
    idx_loc = {d: i for i, d in enumerate(full_idx_list)}

    for i, d in enumerate(full_idx_list):
        # Mark to market
        row = assets.iloc[i]
        total = 0.0
        for aname, pos in holdings.items():
            ak = aname  # 'sp', 'bond', 'gold'
            if pos['in_asset']:
                total += pos['shares_asset'] * row[ak]
            else:
                total += pos['shares_cash'] * row['cash']
        equity.iloc[i] = total

        # Rebalance at month-end
        if d in rebal_set:
            loc = i
            if loc < 252:
                # not enough history: stay in cash, rebalance cash shares
                sub_cap = total / 3.0
                cash_px = row['cash']
                for aname in ['sp', 'bond', 'gold']:
                    holdings[aname] = {
                        'in_asset': False,
                        'shares_asset': 0.0,
                        'shares_cash': sub_cap / cash_px if cash_px > 0 else 0.0,
                    }
            else:
                sub_cap = total / 3.0
                p_now = assets.iloc[loc]
                p_past = assets.iloc[loc - 252]
                cash_px = p_now['cash']
                for aname in ['sp', 'bond', 'gold']:
                    past_px = p_past[aname]
                    now_px  = p_now[aname]
                    if (pd.notna(past_px) and pd.notna(now_px) and
                            past_px > 0 and now_px > 0):
                        mom = now_px / past_px - 1
                        if mom > 0:
                            holdings[aname] = {
                                'in_asset': True,
                                'shares_asset': sub_cap / now_px,
                                'shares_cash': 0.0,
                            }
                        else:
                            holdings[aname] = {
                                'in_asset': False,
                                'shares_asset': 0.0,
                                'shares_cash': sub_cap / cash_px if cash_px > 0 else 0.0,
                            }
                    else:
                        # missing data: hold cash
                        holdings[aname] = {
                            'in_asset': False,
                            'shares_asset': 0.0,
                            'shares_cash': sub_cap / cash_px if cash_px > 0 else 0.0,
                        }

    equity.name = 'TSMOM_proxy'
    return equity


# =============================================================================
# BUILD SLEEVE PRICE SERIES
# =============================================================================

def build_sleeves(all_px, cash_series):
    """Construct one continuous price series per v3 sleeve via return-splicing.

    All series are indexed on all_px.index.
    Price level is arbitrary (starts at 100 on first available date).
    Returns a dict: sleeve_name -> pd.Series of daily prices.
    """
    def get(ticker):
        if ticker in all_px.columns:
            return all_px[ticker].copy()
        return pd.Series(dtype=float, index=all_px.index)

    vfinx = get('VFINX')
    vgtsx = get('VGTSX')
    visvx = get('VISVX')
    vustx = get('VUSTX')
    vipsx = get('VIPSX')
    gcf   = get('GC=F')
    rsp   = get('RSP')
    vxus  = get('VXUS')
    avuv  = get('AVUV')
    usmv  = get('USMV')
    gld   = get('GLD')
    dbmf  = get('DBMF')
    tlt   = get('TLT')
    schp  = get('SCHP')
    btal  = get('BTAL')

    sleeves = {}

    # RSP: real RSP (2003+) spliced onto VFINX (pre-2003)
    sleeves['RSP_sleeve']  = splice(vfinx, rsp, 'RSP_sleeve')

    # VXUS: real VXUS (2011+) spliced onto VGTSX for full history
    sleeves['VXUS_sleeve'] = splice(vgtsx, vxus, 'VXUS_sleeve')

    # AVUV: real AVUV (2019+) spliced onto VISVX (1998+)
    sleeves['AVUV_sleeve'] = splice(visvx, avuv, 'AVUV_sleeve')

    # USMV: real USMV (2011+) spliced onto VFINX (pre-2011)
    sleeves['USMV_sleeve'] = splice(vfinx, usmv, 'USMV_sleeve')

    # GLD: real GLD (2004+) spliced onto GC=F gold futures
    sleeves['GLD_sleeve']  = splice(gcf, gld, 'GLD_sleeve')

    # TLT: real TLT (2002+) spliced onto VUSTX
    sleeves['TLT_sleeve']  = splice(vustx, tlt, 'TLT_sleeve')

    # SCHP: real SCHP (2010+) spliced onto VIPSX (mid-2000+)
    # Note: VIPSX only starts ~2000-06, so there may be a short gap at start;
    # dates before VIPSX start will be NaN → static_portfolio handles via pro-rata
    sleeves['SCHP_sleeve'] = splice(vipsx, schp, 'SCHP_sleeve')

    # DBMF: real DBMF (2019+) spliced onto TSMOM proxy
    tsmom = tsmom_proxy(vfinx, vustx, gcf, cash_series)
    sleeves['DBMF_sleeve'] = splice(tsmom, dbmf, 'DBMF_sleeve')

    # SGOV: pure CASH accrual (T-bill) — NOT downloaded
    sleeves['SGOV_sleeve'] = cash_series.copy().rename('SGOV_sleeve')

    # BTAL: real BTAL (2011+) spliced onto CASH (pre-2011 — conservative)
    sleeves['BTAL_sleeve'] = splice(cash_series, btal, 'BTAL_sleeve')

    return sleeves


# =============================================================================
# v3 WITH DIP LADDER  (stateful daily simulation)
# =============================================================================

def v3_with_dip_ladder(sleeves, weights, sp_series, start, end,
                       name='v3 + Dip Ladder'):
    """Same allocation as v3_static, but the 22% SGOV reserve deploys into risk
    sleeves on S&P drawdown milestones.

    Dip tiers (each fires ONCE, tracked by `fired` state):
        Tier 1: S&P drawdown <= -7%  → deploy 20% of ORIGINAL reserve
        Tier 2: S&P drawdown <= -12% → deploy 30% of ORIGINAL reserve
        Tier 3: S&P drawdown <= -20% → deploy 50% of ORIGINAL reserve

    At each trigger, cash is moved from the reserve into the risk sleeves
    pro-rata to their *target* weights (normalised within the 78% risk book).

    Drawdown = VFINX close / (trailing 252-day rolling max of VFINX close) - 1.
    Checked at month-end only, using only trailing data.
    One-way: no refill after deployment.
    """
    # Build sleeve DataFrame
    sleeve_names = list(weights.keys())
    px = pd.DataFrame({s: sleeves[s] for s in sleeve_names})
    mask = (px.index >= start) & (px.index <= end)
    px = px[mask].dropna(how='all').ffill()
    if len(px) < 2:
        return pd.Series(dtype=float, name=name), []

    # S&P series for drawdown signal (trailing 252d max, strictly trailing)
    sp = sp_series.copy()
    sp = sp[sp.index >= WARMUP_START]
    sp_roll_max = sp.rolling(252, min_periods=1).max()

    # Target weights and risk-book proportions for pro-rata deployment
    reserve_key  = 'SGOV_sleeve'
    reserve_w    = weights[reserve_key]          # 0.22
    risk_w       = {k: v for k, v in weights.items() if k != reserve_key}
    risk_w_total = sum(risk_w.values())          # 0.78
    risk_prop    = {k: v / risk_w_total for k, v in risk_w.items()}

    # Initial shares — buy at first date according to target weights
    capital = float(INITIAL_CAPITAL)
    d0 = px.index[0]
    shares = {}
    for s in sleeve_names:
        p = px.loc[d0, s]
        if pd.notna(p) and p > 0:
            shares[s] = capital * weights[s] / p
        else:
            shares[s] = 0.0

    rebs = set(month_end_dates(px.index, start, end))

    # Annual rebalance dates (first trading day of each year)
    annual_rebs = set()
    for yr, grp in px.groupby(px.index.year):
        annual_rebs.add(grp.index[0])
    annual_rebs.add(d0)

    # Tier state
    fired = {1: False, 2: False, 3: False}
    tier_thresholds = {1: -0.07, 2: -0.12, 3: -0.20}
    tier_fractions  = {1: 0.20,  2: 0.30,  3: 0.50}
    deployment_log  = []  # list of dicts

    # --- Effective weights for the annual rebalance (one-way: no SGOV refill) ---
    # After a tier fires, SGOV's weight is permanently reduced by the deployed
    # fraction and the risk sleeves' proportional split is preserved.  The annual
    # rebalance always uses eff_weights (not the original V3_WEIGHTS) so that
    # previously deployed reserve stays deployed.  Total eff_weights sums to 1.
    eff_weights = dict(weights)  # mutable copy; updated on each deployment

    equity = pd.Series(index=px.index, dtype=float)

    for i, d in enumerate(px.index):
        # Mark to market
        cap = sum(shares[s] * px.loc[d, s] for s in sleeve_names
                  if pd.notna(px.loc[d, s]))
        equity.iloc[i] = cap
        capital = cap

        # --- Annual rebalance (skip first date, handled at init) ---
        # Uses eff_weights (post-deployment) so SGOV is never refilled above
        # the level it currently sits at after any fired tiers.
        if d in annual_rebs and i > 0:
            avail = [s for s in sleeve_names
                     if pd.notna(px.loc[d, s]) and px.loc[d, s] > 0]
            wsum  = sum(eff_weights[s] for s in avail)
            if wsum > 0:
                for s in avail:
                    shares[s] = capital * (eff_weights[s] / wsum) / px.loc[d, s]

        # --- Month-end dip-ladder check (after marking, before next day) ---
        if d in rebs:
            if d in sp_roll_max.index and pd.notna(sp_roll_max[d]):
                sp_dd = sp.get(d, np.nan)
                if pd.notna(sp_dd) and sp_roll_max[d] > 0:
                    drawdown = sp_dd / sp_roll_max[d] - 1
                else:
                    drawdown = 0.0
            else:
                drawdown = 0.0

            for tier in [1, 2, 3]:
                if not fired[tier] and drawdown <= tier_thresholds[tier]:
                    fired[tier] = True
                    # Deploy a fraction of the CURRENT SGOV sleeve value (not
                    # inception capital) so the amount scales with the portfolio.
                    sgov_px  = px.loc[d, reserve_key]
                    sgov_val = shares[reserve_key] * sgov_px if pd.notna(sgov_px) else 0.0
                    deploy_amount = sgov_val * tier_fractions[tier]
                    deploy_amount = min(deploy_amount, sgov_val)
                    if deploy_amount > 0 and pd.notna(sgov_px) and sgov_px > 0:
                        # --- Renormalize over risk sleeves with valid prices ---
                        # Only debit SGOV for the amount that can actually be
                        # placed (conserves total value even if a sleeve is NaN).
                        avail_rs = {rs: risk_prop[rs] for rs in RISK_SLEEVES
                                    if pd.notna(px.loc[d, rs]) and px.loc[d, rs] > 0}
                        rs_prop_sum = sum(avail_rs.values())
                        if rs_prop_sum > 0:
                            # Debit SGOV shares
                            shares[reserve_key] -= deploy_amount / sgov_px
                            # Credit risk sleeves (renormalized to conserve value)
                            for rs, prop in avail_rs.items():
                                shares[rs] += deploy_amount * (prop / rs_prop_sum) / px.loc[d, rs]
                            # --- Update effective weights (one-way, no refill) ---
                            # The deployed fraction permanently reduces SGOV's
                            # weight and is redistributed to risk sleeves in
                            # proportion to their current eff_weights.
                            deployed_w_fraction = (deploy_amount / capital
                                                   if capital > 0 else 0.0)
                            eff_weights[reserve_key] = max(
                                0.0, eff_weights[reserve_key] - deployed_w_fraction
                            )
                            risk_eff_total = sum(
                                eff_weights[rs] for rs in RISK_SLEEVES
                            )
                            if risk_eff_total > 0:
                                for rs in RISK_SLEEVES:
                                    eff_weights[rs] += (
                                        deployed_w_fraction
                                        * (eff_weights[rs] / risk_eff_total)
                                    )
                            deployment_log.append({
                                'Tier': tier,
                                'Date': d.date(),
                                'S&P_DD': f"{drawdown*100:+.1f}%",
                                'Deployed_$': f"${deploy_amount:,.0f}",
                            })
                            print(f"  DIP LADDER TIER {tier} FIRED: {d.date()} | "
                                  f"S&P DD={drawdown*100:+.1f}% | Deployed ${deploy_amount:,.0f}")

    equity.name = name
    return equity, deployment_log


# =============================================================================
# v3 NO-TREND SENSITIVITY
# Build v3 Static but with DBMF 10% reallocated pro-rata to other risk sleeves.
# =============================================================================

def make_no_trend_weights():
    """v3 weights with DBMF sleeve redistributed pro-rata to the other risk sleeves."""
    dbmf_w = V3_WEIGHTS['DBMF_sleeve']
    other_risk = {k: v for k, v in V3_WEIGHTS.items()
                  if k not in ('DBMF_sleeve', 'SGOV_sleeve')}
    other_total = sum(other_risk.values())
    new_w = dict(V3_WEIGHTS)
    new_w['DBMF_sleeve'] = 0.0
    for k in other_risk:
        new_w[k] += dbmf_w * (other_risk[k] / other_total)
    # SGOV stays the same
    return {k: v for k, v in new_w.items() if v > 0}


# =============================================================================
# REAL-ETF-ERA TABLE (2019-09 to 2026, no proxies)
# =============================================================================

def real_etf_era_portfolios(all_px, cash_series, start='2019-09-01', end=END):
    """Build v3 static using ONLY the real ETFs (no proxies).
    Common start ~2019-09 when AVUV launched. Compare vs S&P and QQQ.

    Returns dict of equity curves.
    """
    # Real ETF tickers matching each sleeve
    real_map = {
        'RSP':  0.18,
        'VXUS': 0.12,
        'AVUV': 0.08,
        'USMV': 0.07,
        'GLD':  0.10,
        'DBMF': 0.10,
        'TLT':  0.07,
        'SCHP': 0.03,
        'CASH': 0.22,
        'BTAL': 0.03,
    }
    # Build a px DataFrame including CASH
    px_era = all_px.copy()
    px_era['CASH'] = cash_series

    results = {}
    results['v3 Real ETFs'] = static_portfolio(
        px_era, real_map, start, end, 'Y', 'v3 Real ETFs'
    )
    results['S&P 500'] = static_portfolio(
        px_era, {'VFINX': 1.0}, start, end, 'Y', 'S&P 500'
    )
    results['QQQ'] = static_portfolio(
        px_era, {'QQQ': 1.0}, start, end, 'Y', 'QQQ'
    )
    return results


# =============================================================================
# MAIN: BUILD SLEEVES AND RUN STRATEGIES
# =============================================================================
print("\nBuilding proxy sleeve series...")
sleeves = build_sleeves(all_px, cash_series)

# Combine into a DataFrame for static_portfolio
sleeve_df = pd.DataFrame(sleeves)

print("\nBuilding v3 strategies...")

v3_static_eq = static_portfolio(
    sleeve_df, V3_WEIGHTS, START, END, 'Y', 'v3 Static'
)

print("\nRunning v3 + dip ladder simulation...")
sp_vfinx = all_px['VFINX'].copy() if 'VFINX' in all_px.columns else pd.Series(dtype=float)
v3_dip_eq, dip_log = v3_with_dip_ladder(
    sleeves, V3_WEIGHTS, sp_vfinx, START, END, 'v3 + Dip Ladder'
)

no_trend_w = make_no_trend_weights()
v3_no_trend_eq = static_portfolio(
    sleeve_df, no_trend_w, START, END, 'Y', 'v3 No-Trend'
)

# Use VFINX directly for cleaner S&P reference (not RSP sleeve)
sp_direct_px = sleeve_df.copy()
sp_direct_px['SP500'] = all_px['VFINX'].copy() if 'VFINX' in all_px.columns else pd.Series(dtype=float)
sp500_eq = static_portfolio(sp_direct_px, {'SP500': 1.0}, START, END, 'Y', 'S&P 500')

qqq_px = sleeve_df.copy()
qqq_px['QQQ'] = all_px['QQQ'].copy() if 'QQQ' in all_px.columns else pd.Series(dtype=float)
qqq_eq = static_portfolio(qqq_px, {'QQQ': 1.0}, START, END, 'Y', 'QQQ')

strategies = {
    'v3 Static':       v3_static_eq,
    'v3 + Dip Ladder': v3_dip_eq,
    'v3 No-Trend':     v3_no_trend_eq,
    'S&P 500':         sp500_eq,
    'QQQ':             qqq_eq,
}

# =============================================================================
# OUTPUT: FULL-PERIOD TABLE
# =============================================================================
print("\n" + "=" * 100)
print("FULL PERIOD 2000-2026  (start $1,000,000)")
print("=" * 100)
rows = []
for sname, eq in strategies.items():
    m = compute_metrics(eq)
    rows.append({
        'Strategy': sname,
        'CAGR':    f"{m['CAGR']*100:.1f}%",
        'Sharpe':  f"{m['Sharpe']:.2f}",
        'Sortino': f"{m['Sortino']:.2f}",
        'MaxDD':   f"{m['MaxDD']*100:.1f}%",
        'Calmar':  f"{m['Calmar']:.2f}" if pd.notna(m['Calmar']) else 'n/a',
        'Final $': f"${m['Final']:,.0f}" if pd.notna(m['Final']) else 'n/a',
    })
full_df = pd.DataFrame(rows)
print(full_df.to_string(index=False))

# =============================================================================
# OUTPUT: CRISIS WINDOWS
# =============================================================================
crises = [
    ('Dot-com bust',         '2000-03-24', '2002-10-09'),
    ('Global Financial Crisis', '2007-10-09', '2009-03-09'),
    ('COVID crash',          '2020-02-19', '2020-03-23'),
    ('2022 stocks+bonds',    '2022-01-03', '2022-10-12'),
    ('Recovery to today',    '2009-03-09', END),
]
print("\n" + "=" * 100)
print("CRISIS WINDOWS — total return & max drawdown during each event")
print("=" * 100)
for cname, cs, ce in crises:
    print(f"\n--- {cname}  ({cs} -> {ce}) ---")
    rr = []
    for sname, eq in strategies.items():
        sub = eq[(eq.index >= cs) & (eq.index <= ce)].dropna()
        if len(sub) < 2:
            rr.append({'Strategy': sname, 'Total Return': 'n/a', 'MaxDD': 'n/a'})
            continue
        tot = sub.iloc[-1] / sub.iloc[0] - 1
        dd  = (sub / sub.cummax() - 1).min()
        rr.append({
            'Strategy': sname,
            'Total Return': f"{tot*100:+.1f}%",
            'MaxDD': f"{dd*100:.1f}%",
        })
    print(pd.DataFrame(rr).to_string(index=False))

# =============================================================================
# OUTPUT: LOST DECADE 2000-2009
# =============================================================================
print("\n" + "=" * 100)
print("LOST DECADE 2000-01-01 -> 2009-12-31  (S&P went nowhere for 10 years)")
print("=" * 100)
rr = []
for sname, eq in strategies.items():
    sub = eq[(eq.index >= '2000-01-01') & (eq.index <= '2009-12-31')].dropna()
    if len(sub) < 2:
        rr.append({'Strategy': sname, 'CAGR': 'n/a', 'Total': 'n/a', 'MaxDD': 'n/a'})
        continue
    m = compute_metrics(sub)
    rr.append({
        'Strategy': sname,
        'CAGR':  f"{m['CAGR']*100:.1f}%",
        'Total': f"{(sub.iloc[-1]/sub.iloc[0]-1)*100:+.1f}%",
        'MaxDD': f"{m['MaxDD']*100:.1f}%",
    })
print(pd.DataFrame(rr).to_string(index=False))

# =============================================================================
# OUTPUT: DIP LADDER DEPLOYMENT LOG
# =============================================================================
print("\n" + "=" * 100)
print("DIP LADDER DEPLOYMENT LOG")
print("=" * 100)
if dip_log:
    print(pd.DataFrame(dip_log).to_string(index=False))
else:
    print("  No tiers fired (no S&P drawdown exceeded the thresholds in the simulation window).")

# =============================================================================
# OUTPUT: REAL-ETF-ERA 2019-2026
# =============================================================================
print("\n" + "=" * 100)
print("REAL-ETF-ERA 2019-09 -> 2026  (no proxies — covers COVID + 2022)")
print("=" * 100)
era_results = real_etf_era_portfolios(all_px, cash_series, '2019-09-01', END)
rr = []
for sname, eq in era_results.items():
    m = compute_metrics(eq)
    rr.append({
        'Strategy': sname,
        'CAGR':   f"{m['CAGR']*100:.1f}%",
        'Sharpe': f"{m['Sharpe']:.2f}",
        'MaxDD':  f"{m['MaxDD']*100:.1f}%",
        'Final $': f"${m['Final']:,.0f}" if pd.notna(m['Final']) else 'n/a',
    })
print(pd.DataFrame(rr).to_string(index=False))

# =============================================================================
# CHART
# =============================================================================
print("\nGenerating chart...")
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 11),
                                gridspec_kw={'height_ratios': [3, 1]})

colors_map = {
    'v3 Static':       '#1f77b4',
    'v3 + Dip Ladder': '#2ca02c',
    'v3 No-Trend':     '#9467bd',
    'S&P 500':         '#d62728',
    'QQQ':             '#ff7f0e',
}
lw_map = {
    'S&P 500': 2.2,
    'QQQ':     2.2,
    'v3 Static':       1.8,
    'v3 + Dip Ladder': 1.8,
    'v3 No-Trend':     1.4,
}

for sname, eq in strategies.items():
    ax1.plot(eq.index, eq.values,
             label=sname,
             color=colors_map.get(sname, 'gray'),
             linewidth=lw_map.get(sname, 1.4))

ax1.set_yscale('log')
ax1.set_title(
    'v3 Proxy Backtest 2000-2026: v3 Balanced vs S&P 500 / QQQ ($1M start, log scale)',
    fontsize=13
)
ax1.set_ylabel('Portfolio Value (log scale)')
ax1.legend(loc='upper left', fontsize=9, ncol=2)
ax1.grid(True, alpha=0.3)
ax1.axhline(INITIAL_CAPITAL, color='gray', ls='--', alpha=0.5)

# shade crisis windows
crisis_colors = ['#ff4444', '#ff6600', '#4444ff', '#884400']
for (cname, cs, ce), ccol in zip(crises[:4], crisis_colors):
    ax1.axvspan(pd.Timestamp(cs), pd.Timestamp(ce), color=ccol, alpha=0.07)

# Drawdown panel
for sname, eq in strategies.items():
    dd = (eq / eq.cummax() - 1) * 100
    ax2.plot(dd.index, dd.values,
             label=sname,
             color=colors_map.get(sname, 'gray'),
             linewidth=lw_map.get(sname, 1.2))
ax2.set_title('Drawdown (all strategies)', fontsize=11)
ax2.set_ylabel('Drawdown %')
ax2.legend(loc='lower left', fontsize=8, ncol=3)
ax2.grid(True, alpha=0.3)
for (cname, cs, ce), ccol in zip(crises[:4], crisis_colors):
    ax2.axvspan(pd.Timestamp(cs), pd.Timestamp(ce), color=ccol, alpha=0.07)

plt.tight_layout()
out_path = 'report/img/v3_proxy_backtest.png'
plt.savefig(out_path, dpi=150)
print(f"Chart saved to {out_path}")
plt.close()

# =============================================================================
# CAVEATS
# =============================================================================
print("\n" + "=" * 100)
print("CAVEATS — proxy substitutions and what each under/overstates")
print("=" * 100)
print("""
PROXY SUBSTITUTIONS:

1. RSP (US large-cap equal-weight) pre-2003: VFINX (cap-weight S&P 500)
   → UNDERSTATES the de-concentration tilt of RSP; cap-weight will show higher
     concentration in mega-cap tech especially 1999-2000 and 2023-2026. The real
     RSP benefit (equal-weight reduces single-stock tail risk) is NOT captured
     before 2003.  Splice seam: 2003-04-30 (approximate RSP launch).

2. VXUS (international) pre-2011: VGTSX (Vanguard Total International mutual fund)
   → Reasonable proxy; VGTSX is the same index family. Minor tracking difference.
     Splice seam: 2011-01-26.

3. AVUV (US small/mid-value) pre-2019: VISVX (Vanguard Small Value index)
   → UNDERSTATES Avantis' profitability screen advantage. VISVX is passive index;
     AVUV uses profitability/value tilts that historically improved factor loading.
     The proxy is a conservative lower-bound for the sleeve.
     Splice seam: 2019-09-24 (AVUV launch).

4. USMV (min-vol / quality) pre-2011: VFINX (cap-weight S&P 500)
   → UNDERSTATES the drawdown cushion that min-vol actually provides. Pre-2011,
     this sleeve behaves like plain S&P — the 2000-2002 and 2007-2009 drawdowns
     will be WORSE than USMV would have actually been. Conservative for crisis
     protection claims.  Splice seam: 2011-10-18.

5. GLD (gold) pre-2004: GC=F (gold futures continuous contract)
   → Price return only (no yield — gold has none). The splice to GLD captures
     GLD's structure costs vs futures roll, but the direction is the same.
     Gold's 2001-2011 bull run is a real historical tailwind; repeat not guaranteed.
     Splice seam: 2004-11-18.

6. DBMF (trend / managed futures) pre-2019: multi-asset TSMOM proxy
   → Equal-weight 3-asset (S&P/long bond/gold) 12m time-series momentum,
     long-if-positive else CASH, rebalanced monthly. This SIMPLIFIES real managed
     futures: (a) only 3 assets vs 50+ in real CTA; (b) no leverage/shorting;
     (c) no commodity curve roll; (d) real DBMF tracks the SG CTA index.
     The proxy likely OVERSTATES managed futures' correlation to these three assets
     during quiet periods but UNDERSTATES it during broad trend regimes.
     Separately, report v3 No-Trend (DBMF weight redistributed) to isolate how
     much the trend sleeve drives the result.
     Splice seam: 2019-05-14 (DBMF launch).

7. SCHP (TIPS) pre-2010: VIPSX (Vanguard Inflation-Protected Securities fund)
   → Reasonable proxy; same index. VIPSX only starts ~2000-06, so the very early
     months of the backtest may have a small gap — handled by redistributing weight
     pro-rata across available sleeves in the static_portfolio function.
     Splice seam: 2010-08-05.

8. SGOV (dry powder) throughout: CASH accrual (piecewise-constant T-bill estimate)
   → SGOV is a 0-3 month T-bill ETF (launched 2020); the CASH proxy is a reasonable
     approximation. The piecewise T-bill rates used are estimates, not actual daily
     SOFR/T-bill prints. Slight overstatement of yield in low-rate periods possible.

9. BTAL (anti-beta tail protection) pre-2011: CASH
   → UNDERSTATES crash protection significantly. BTAL is long low-beta / short
     high-beta, which tends to RISE in market crashes. Substituting CASH means the
     3% tail sleeve shows near-zero crisis alpha before 2011. This is deliberately
     conservative — it will NOT inflate crisis numbers. Real BTAL effect is visible
     only post-2011.  Splice seam: 2011-09-14.

GENERAL CAVEATS:
10. No transaction costs, bid/ask spreads, or taxes. Annual rebalancing minimises
    turnover but real costs would modestly reduce all CAGRs.
11. Splice seams introduce regime discontinuities at the transition dates; return-
    splicing (not price-level splicing) removes the level jump but not factor
    composition differences.
12. TSMOM momentum signals use ONLY trailing 252-day data (no look-ahead).
    Dip-ladder drawdown uses trailing 252-day rolling max (no look-ahead).
    NOTE: warmup starts 1999-06-01 (~148 trading days before 2000-01-01), so
    the rolling-252 max is not fully warmed until ~mid-2001. Early-2000 dip
    thresholds are based on a shorter window — conservative (not look-ahead).
13. Annual rebalance rule: the dip-ladder simulation rebalances annually AND
    fires deployment tiers once each. After firing, the target weight for SGOV
    decreases and annual rebalance restores WHATEVER weight remains — there is no
    refill rule (one-way deployment is intentional conservatism).
14. Gold's bull market (2001-2011) and the 40-year bond bull market (1982-2020)
    are real historical tailwinds for gold/bond sleeves; both face structural
    headwinds from today's higher-yield / AI-driven starting point.
""")

print("=" * 100)
print("v3 PROXY BACKTEST COMPLETE")
print("=" * 100)
