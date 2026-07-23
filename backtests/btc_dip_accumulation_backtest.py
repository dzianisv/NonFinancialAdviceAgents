#!/usr/bin/env python3
"""
BTC Dip-Accumulation v1 — cost-aware backtest (Law #0 gate).

Mirrors the TradingView Pine strategy .pine/strategy_BTC_dip_accumulation.pine:
  - Bollinger Bands(20, 2.0) on close, RSI(14)
  - Long entry:  close crosses OVER lower band AND RSI <= 40
  - Long exit:   close crosses OVER upper band OR RSI >= 70 OR -12% stop
  - 100% of equity per trade, no pyramiding
  - 0.15% commission per side (entry + exit)
  - Signals evaluated on prior close; fills next bar open (no look-ahead)

Compares vs Buy & Hold. Prints net-of-cost metrics + max drawdown.
Saves equity chart to report/img/.
"""
import os
import numpy as np
import pandas as pd

try:
    import yfinance as yf
except Exception as e:
    raise SystemExit(f"yfinance required: {e}")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CAPITAL = 100_000.0
COMMISSION = 0.0015          # 0.15% per side
RSI_LEN, RSI_BUY, RSI_EXIT = 14, 40.0, 70.0
BB_LEN, BB_MULT = 20, 2.0
STOP_PCT = 0.12
RF = 0.04                    # risk-free for Sharpe (annual)


def rsi(series, length):
    delta = series.diff()
    up = delta.clip(lower=0.0)
    down = -delta.clip(upper=0.0)
    # Wilder's smoothing (matches TradingView ta.rsi)
    roll_up = up.ewm(alpha=1.0 / length, adjust=False).mean()
    roll_down = down.ewm(alpha=1.0 / length, adjust=False).mean()
    rs = roll_up / roll_down
    return 100.0 - (100.0 / (1.0 + rs))


def max_drawdown(equity):
    peak = equity.cummax()
    dd = equity / peak - 1.0
    return dd.min()


def sharpe(returns, periods=365):
    if returns.std() == 0 or len(returns) < 2:
        return 0.0
    excess = returns - (RF / periods)
    return np.sqrt(periods) * excess.mean() / returns.std()


def run():
    df = yf.download("BTC-USD", start="2015-01-01", auto_adjust=True, progress=False)
    if df.empty:
        raise SystemExit("No BTC-USD data returned.")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df[["Open", "High", "Low", "Close"]].dropna()
    close = df["Close"]

    basis = close.rolling(BB_LEN).mean()
    dev = BB_MULT * close.rolling(BB_LEN).std(ddof=0)
    upper = basis + dev
    lower = basis - dev
    r = rsi(close, RSI_LEN)

    cross_up_lower = (close > lower) & (close.shift(1) <= lower.shift(1))
    cross_up_upper = (close > upper) & (close.shift(1) <= upper.shift(1))

    entry_sig = cross_up_lower & (r <= RSI_BUY)
    exit_sig = cross_up_upper | (r >= RSI_EXIT)

    df = df.assign(entry=entry_sig.fillna(False), exit=exit_sig.fillna(False))
    df = df.dropna(subset=["Close"])

    # Event-driven sim: signal on close of bar t, fill at open of bar t+1.
    cash = CAPITAL
    coins = 0.0
    entry_price = None
    in_pos = False
    equity_curve = []
    trades = []
    idx = df.index
    opens = df["Open"].values
    highs = df["High"].values
    lows = df["Low"].values
    closes = df["Close"].values
    ent = df["entry"].values
    ext = df["exit"].values

    pending_entry = False
    pending_exit = False

    for i in range(len(df)):
        o = opens[i]
        # --- execute pending orders at today's open ---
        if pending_entry and not in_pos:
            coins = (cash * (1 - COMMISSION)) / o
            entry_price = o
            cash = 0.0
            in_pos = True
            trades.append({"type": "BUY", "date": idx[i], "price": o})
            pending_entry = False
        if pending_exit and in_pos:
            cash = coins * o * (1 - COMMISSION)
            trades.append({"type": "SELL", "date": idx[i], "price": o,
                           "ret": o / entry_price - 1})
            coins = 0.0
            in_pos = False
            entry_price = None
            pending_exit = False

        # --- intrabar stop check while in position ---
        if in_pos and entry_price is not None:
            stop_price = entry_price * (1 - STOP_PCT)
            if lows[i] <= stop_price:
                fill = min(o, stop_price) if o < stop_price else stop_price
                cash = coins * fill * (1 - COMMISSION)
                trades.append({"type": "STOP", "date": idx[i], "price": fill,
                               "ret": fill / entry_price - 1})
                coins = 0.0
                in_pos = False
                entry_price = None
                pending_exit = False

        # --- mark equity ---
        equity = cash + coins * closes[i]
        equity_curve.append(equity)

        # --- set next-bar orders from today's close signal ---
        if not in_pos and ent[i]:
            pending_entry = True
        if in_pos and ext[i]:
            pending_exit = True

    eq = pd.Series(equity_curve, index=idx)
    strat_ret = eq.pct_change().dropna()

    bh = CAPITAL * (closes / closes[0])
    bh = pd.Series(bh, index=idx)
    bh_ret = bh.pct_change().dropna()

    years = (idx[-1] - idx[0]).days / 365.25
    strat_cagr = (eq.iloc[-1] / CAPITAL) ** (1 / years) - 1
    bh_cagr = (bh.iloc[-1] / CAPITAL) ** (1 / years) - 1

    sells = [t for t in trades if t["type"] in ("SELL", "STOP")]
    wins = [t for t in sells if t.get("ret", 0) > 0]
    win_rate = (len(wins) / len(sells) * 100) if sells else 0.0
    gross_win = sum(t["ret"] for t in sells if t.get("ret", 0) > 0)
    gross_loss = -sum(t["ret"] for t in sells if t.get("ret", 0) < 0)
    pf = (gross_win / gross_loss) if gross_loss > 0 else float("inf")

    print("=" * 64)
    print("BTC Dip-Accumulation v1 — cost-aware backtest (net of 0.15%/side)")
    print(f"Data: BTC-USD  {idx[0].date()} → {idx[-1].date()}  ({years:.1f}y, {len(df)} bars)")
    print("=" * 64)
    print(f"{'Metric':<26}{'Strategy':>16}{'Buy & Hold':>18}")
    print("-" * 60)
    print(f"{'Final equity':<26}{eq.iloc[-1]:>16,.0f}{bh.iloc[-1]:>18,.0f}")
    print(f"{'Total return':<26}{eq.iloc[-1]/CAPITAL-1:>15.1%}{bh.iloc[-1]/CAPITAL-1:>17.1%}")
    print(f"{'CAGR':<26}{strat_cagr:>15.1%}{bh_cagr:>17.1%}")
    print(f"{'Max drawdown':<26}{max_drawdown(eq):>15.1%}{max_drawdown(bh):>17.1%}")
    print(f"{'Sharpe (daily->ann)':<26}{sharpe(strat_ret):>16.2f}{sharpe(bh_ret):>18.2f}")
    print("-" * 60)
    print(f"Trades: {len(sells)} closed | Win rate: {win_rate:.0f}% | Profit factor: {pf:.2f}")
    print(f"Time in market: {(coins>0)}. Last 6 trades:")
    for t in trades[-6:]:
        rr = f"  ret {t['ret']:+.1%}" if "ret" in t else ""
        print(f"  {t['date'].date()}  {t['type']:<5} @ {t['price']:>10,.0f}{rr}")

    # --- last-3-year view (recent regime the chart shows) ---
    recent = eq[eq.index >= (idx[-1] - pd.Timedelta(days=365))]
    if len(recent) > 2:
        rec_trades = [t for t in sells if t["date"] >= (idx[-1] - pd.Timedelta(days=365))]
        print("-" * 60)
        print(f"Last 12 months: {len(rec_trades)} trades. "
              f"Strategy in position now: {coins>0}")

    os.makedirs("report/img", exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(eq.index, eq.values, label="Dip-Accumulation v1", lw=1.5)
    ax.plot(bh.index, bh.values, label="Buy & Hold BTC", lw=1.0, alpha=0.7)
    ax.set_yscale("log")
    ax.set_title("BTC Dip-Accumulation v1 vs Buy & Hold (net of 0.15%/side)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    out = "report/img/btc_dip_accumulation_backtest.png"
    fig.tight_layout()
    fig.savefig(out, dpi=110)
    print(f"\nChart saved: {out}")


if __name__ == "__main__":
    run()
