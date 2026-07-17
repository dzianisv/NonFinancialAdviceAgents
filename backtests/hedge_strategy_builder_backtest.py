"""hedge-strategy-builder Stage 2: real backtests, 3 strategies, stocks/ETFs 1D.

Costs: 5 bps per side. Data: yfinance daily adjusted, 2015-07-01..2026-07-01
(first ~6mo burn-in for indicators). Split: IS 2016-2021, OOS 2022-2026.
"""
import numpy as np
import pandas as pd
import yfinance as yf

COST = 0.0005  # per side
TICKERS = ["SPY", "QQQ", "IWM", "EFA", "TLT", "^VIX"]

px = yf.download(TICKERS, start="2015-07-01", end="2026-07-02", auto_adjust=True, progress=False)["Close"]
px = px.rename(columns={"^VIX": "VIX"}).dropna(how="all").ffill()
rets = px.drop(columns="VIX").pct_change()


def stats(eq, pos_changes, trade_rets, label, sub=None):
    eq = eq.dropna()
    if sub:
        eq = eq.loc[sub[0]:sub[1]]
        eq = eq / eq.iloc[0]
    r = eq.pct_change().dropna()
    yrs = (eq.index[-1] - eq.index[0]).days / 365.25
    cagr = eq.iloc[-1] ** (1 / yrs) - 1
    sharpe = r.mean() / r.std() * np.sqrt(252) if r.std() > 0 else 0
    dd = (eq / eq.cummax() - 1).min()
    wr = np.mean([t > 0 for t in trade_rets]) if trade_rets else np.nan
    return dict(label=label, cagr=cagr, sharpe=sharpe, maxdd=dd, ntr=len(trade_rets), win=wr)


results, oos_results = [], []


def record(eq, trades, name):
    results.append(stats(eq, None, trades, name))
    oos_results.append(stats(eq, None, trades, name, sub=("2022-01-01", "2026-07-01")))


# ---- S1: monthly dual-momentum rotation SPY/QQQ/IWM/EFA -> TLT ----
risk_assets = ["SPY", "QQQ", "IWM", "EFA"]
mom = px[risk_assets].pct_change(126)
ma200 = px[risk_assets].rolling(200).mean()
month_end = px.index.to_series().groupby(px.index.to_period("M")).max()
hold = pd.Series(index=px.index, dtype=object)
cur = None
for d in month_end:
    if pd.isna(mom.loc[d]).any():
        continue
    best = mom.loc[d].idxmax()
    cur = best if (mom.loc[d, best] > 0 and px.loc[d, best] > ma200.loc[d, best]) else "TLT"
    hold.loc[d] = cur
hold = hold.ffill().shift(1)  # act next day, no look-ahead
s1_ret = pd.Series(0.0, index=px.index)
for a in risk_assets + ["TLT"]:
    s1_ret[hold == a] = rets[a][hold == a]
switch = (hold != hold.shift(1)) & hold.notna() & hold.shift(1).notna()
s1_ret[switch] -= 2 * COST
s1_eq = (1 + s1_ret.loc["2016-01-01":]).cumprod()
# per-trade returns = per holding period
trades1 = []
seg = (hold != hold.shift(1)).cumsum()
for _, g in s1_ret.loc["2016-01-01":].groupby(seg.loc["2016-01-01":]):
    if len(g):
        trades1.append((1 + g).prod() - 1)
record(s1_eq, trades1, "S1 momentum rotation")

# ---- S2: RSI(2) mean reversion SPY, regime filter 200MA, exit close>MA5, 10d time stop ----
spy = px["SPY"]
delta = spy.diff()
up = delta.clip(lower=0).ewm(alpha=1 / 2, adjust=False).mean()
dn = (-delta.clip(upper=0)).ewm(alpha=1 / 2, adjust=False).mean()
rsi2 = 100 - 100 / (1 + up / dn)
ma200s, ma5 = spy.rolling(200).mean(), spy.rolling(5).mean()
pos = pd.Series(0, index=spy.index)
in_pos, days = False, 0
for i in range(200, len(spy)):
    d = spy.index[i]
    if in_pos:
        days += 1
        if spy.iloc[i] > ma5.iloc[i] or days >= 10:
            in_pos = False
        pos.iloc[i] = 1
    if not in_pos and rsi2.iloc[i] < 10 and spy.iloc[i] > ma200s.iloc[i]:
        in_pos, days = True, 0
pos = pos.shift(1).fillna(0)
s2_ret = rets["SPY"] * pos
s2_ret[(pos.diff() != 0)] -= COST
s2_eq = (1 + s2_ret.loc["2016-01-01":]).cumprod()
trades2 = []
seg2 = (pos.diff() != 0).cumsum()
for _, g in s2_ret.loc["2016-01-01":][pos.loc["2016-01-01":] == 1].groupby(seg2):
    if len(g):
        trades2.append((1 + g).prod() - 1)
record(s2_eq, trades2, "S2 RSI2 mean reversion")

# ---- S3: VIX spike fade: enter when VIX > 1.25*VIX20MA, exit VIX<20MA or 15d ----
vix = px["VIX"]
v20 = vix.rolling(20).mean()
pos3 = pd.Series(0, index=spy.index)
in_pos, days = False, 0
for i in range(20, len(spy)):
    if in_pos:
        days += 1
        if vix.iloc[i] < v20.iloc[i] or days >= 15:
            in_pos = False
        pos3.iloc[i] = 1
    if not in_pos and vix.iloc[i] > 1.25 * v20.iloc[i]:
        in_pos, days = True, 0
pos3 = pos3.shift(1).fillna(0)
s3_ret = rets["SPY"] * pos3
s3_ret[(pos3.diff() != 0)] -= COST
s3_eq = (1 + s3_ret.loc["2016-01-01":]).cumprod()
trades3 = []
seg3 = (pos3.diff() != 0).cumsum()
for _, g in s3_ret.loc["2016-01-01":][pos3.loc["2016-01-01":] == 1].groupby(seg3):
    if len(g):
        trades3.append((1 + g).prod() - 1)
record(s3_eq, trades3, "S3 VIX spike fade")

# ---- benchmark ----
bh = (1 + rets["SPY"].loc["2016-01-01":]).cumprod()
record(bh, [], "SPY buy&hold")

print("== FULL 2016-2026 ==")
print(pd.DataFrame(results).to_string(index=False, float_format=lambda x: f"{x:.3f}"))
print("\n== OOS 2022-2026 ==")
print(pd.DataFrame(oos_results).to_string(index=False, float_format=lambda x: f"{x:.3f}"))
print("\nexposure: S2", pos.loc['2016-01-01':].mean().round(3), " S3", pos3.loc['2016-01-01':].mean().round(3))
