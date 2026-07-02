"""
Honest maker-fill simulation driver for the regime_sma_maker strategy candidate.

Wires strategies/regime_sma_maker.py's target-position signal into core/fills.py's
bar-by-bar maker-fill simulator (trade-through-not-touch, queue-position haircut,
adverse selection, no-fill skip/timeout-to-market), on top of the flat-cost gate result
from core/gate.py.

Entry/exit limit price convention (declared, not tuned per-run):
  - BASE variant: resting limit AT prior bar's close (limit = close[t-1]) — the entry/exit
    price a maker order placed at the open of bar t, priced off the last known close, would
    rest at.
  - OFFSET variant: limit improved by 5bp in the favorable direction (BUY limit = prior close
    * (1 - 0.0005), SELL limit = prior close * (1 + 0.0005)) — tests whether a small give-up
    materially changes the realized fill rate / adverse-drift tradeoff.

Regime-flip signal only trades when the position CHANGES (long<->flat), so entries/exits are
rare (per the June README's low-turnover expectation) — each transition bar gets ONE limit
order attempt, timeout_bars=1 (transition bar itself), forced-market on timeout (house rule:
forced/timeout exits always pay taker). While flat between flips there is no order at all
(no cost, no fill risk) — this matches the signal's own "flat" target position.

Runs BASE + all 4 mandated stress tiers, for both BTC and ETH, on the OOS window
(2024-01-01 -> latest), using each symbol's IS-selected sma_window (from the flat-cost gate).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import data, gate, fills
from core.costs import CostConfig, STRESS_2X_FEES
from strategies.regime_sma_maker import signals

OOS_START = gate.OOS_START
OFFSET_BPS = 5.0  # offset variant: 5bp price improvement on the resting limit
TIMEOUT_BARS = 1  # try the maker limit on the transition bar itself; else forced market


def _transitions(pos: pd.Series) -> pd.Series:
    """Return the position series restricted to bars where it CHANGES vs the previous bar
    (long<->flat flips) -- these are the only bars that generate an order under this signal."""
    prev = pos.shift(1).fillna(0.0)
    changed = pos != prev
    return changed


def simulate(df: pd.DataFrame, pos: pd.Series, notional: float = 100.0,
             offset_bps: float = 0.0, stress_fill_prob: bool = False, delay_bars: int = 0,
             extra_slip_worst_vol: bool = False, base_cost_cfg: CostConfig = CostConfig()) -> dict:
    """Bar-by-bar maker-fill simulation of the regime-flip signal over df (already sliced to
    the OOS window), using core/fills.py primitives exactly. Returns a report dict with
    realized net-of-cost return series (dict, not concatenated), fill stats, adverse drift,
    and no-fill/opportunity-cost tracking."""
    df = df.reset_index(drop=False)  # positional iloc addressing required by core/fills.py
    pos = pos.reset_index(drop=True)
    n = len(df)
    vpt = fills.vol_p95_threshold(df.set_index(df.index))  # index irrelevant, uses columns only

    events = []  # each: dict with bar_pos, side, filled, is_maker, fee_usd, slippage_usd, adverse, timeout, skipped
    realized_returns = pd.Series(0.0, index=range(n))  # net return credited on FILL bar (simple: one-shot at fill, not carried as continuous exposure — see note below)

    current_side = None  # None=flat, "long"=holding
    entry_fill_price = None  # actual simulated fill price of the OPEN position (P0 fix: P&L
                              # must be computed from this, not from close-to-close alone)
    i = 1
    fill_rate_attempts = 0
    fill_rate_fills = 0
    skipped_entries = 0
    skipped_opportunity_gross = []
    adverse_drifts = []
    n_maker_fills = 0
    n_taker_timeout_fills = 0
    total_fees = 0.0
    total_slippage = 0.0

    while i < n:
        want_long = pos.iloc[i] >= 0.5
        is_long = current_side == "long"
        entry_this_bar = False
        exit_this_bar = False
        if want_long and not is_long:
            # ENTRY: resting BUY limit at prior close (± offset), tried for TIMEOUT_BARS
            prior_close = float(df["close"].iloc[i - 1])
            limit = prior_close * (1 - offset_bps / 10_000.0)
            fill_rate_attempts += 1
            res = fills.simulate_entry(
                df, i, "buy", limit, base_cost_cfg, notional,
                stress_fill_prob=stress_fill_prob, delay_bars=delay_bars,
                extra_slip_worst_vol=extra_slip_worst_vol, vol_p95_threshold=vpt,
            )
            if res.filled:
                fill_rate_fills += 1
                n_maker_fills += 1
                total_fees += res.fee_usd
                total_slippage += res.slippage_usd
                fill_bar = res.bar_index
                realized_returns.iloc[fill_bar] -= (res.fee_usd + res.slippage_usd) / notional
                # P0 FIX: price P&L from fill_bar's close to the ACTUAL simulated fill price
                # (res.fill_price), not close-to-close vs prior close. This is what makes a
                # limit-price offset/improvement actually show up in P&L.
                fill_price = float(res.fill_price)
                entry_close = float(df["close"].iloc[fill_bar])
                if fill_price:
                    realized_returns.iloc[fill_bar] += (entry_close - fill_price) / fill_price
                adv = fills.adverse_drift(df, fill_bar, "buy")
                if adv is not None:
                    adverse_drifts.append(adv)
                current_side = "long"
                entry_fill_price = fill_price
                entry_this_bar = True
                events.append({"type": "entry", "bar": fill_bar, "maker": True, "filled": True,
                                "fill_price": fill_price})
            else:
                # no-fill fallback: signal SKIPPED, tracked as opportunity cost only
                skipped_entries += 1
                if i + 1 < n:
                    would_be = (float(df["close"].iloc[i + 1]) - float(df["close"].iloc[i])) / float(df["close"].iloc[i])
                    skipped_opportunity_gross.append(would_be)
                events.append({"type": "entry", "bar": i, "maker": True, "filled": False, "skipped": True})
                # current_side stays flat/unchanged -- position NOT carried forward
        elif not want_long and is_long:
            # EXIT: resting SELL limit at prior close (± offset), timeout -> forced market (taker)
            prior_close = float(df["close"].iloc[i - 1])
            limit = prior_close * (1 + offset_bps / 10_000.0)
            fill_rate_attempts += 1
            res = fills.simulate_exit_with_timeout(
                df, i, "sell", limit, TIMEOUT_BARS, base_cost_cfg, notional,
                stress_fill_prob=stress_fill_prob, delay_bars=delay_bars,
                extra_slip_worst_vol=extra_slip_worst_vol, vol_p95_threshold=vpt,
            )
            fill_rate_fills += 1  # exit always resolves (maker or forced taker), never skipped
            fill_bar = res.bar_index
            total_fees += res.fee_usd
            total_slippage += res.slippage_usd
            realized_returns.iloc[fill_bar] -= (res.fee_usd + res.slippage_usd) / notional
            # P0 FIX: price P&L from the bar BEFORE the fill bar's close (last mark-to-market
            # point of the held position) to the ACTUAL simulated exit fill price, plus any
            # price move from the entry bar's close through fill_bar's prior close (this is
            # exactly what the "holding" mark-to-market loop below already accrued day-by-day
            # up to fill_bar - 1; the exit fill bar itself never went through that loop since
            # current_side flips to None below, so we must credit it here explicitly).
            exit_fill_price = float(res.fill_price)
            last_mark = float(df["close"].iloc[fill_bar - 1]) if fill_bar > 0 else exit_fill_price
            if last_mark:
                realized_returns.iloc[fill_bar] += (exit_fill_price - last_mark) / last_mark
            adv = fills.adverse_drift(df, fill_bar, "sell")
            if adv is not None:
                adverse_drifts.append(adv)
            if res.is_maker:
                n_maker_fills += 1
            else:
                n_taker_timeout_fills += 1
            current_side = None
            entry_fill_price = None
            exit_this_bar = True
            events.append({"type": "exit", "bar": fill_bar, "maker": res.is_maker,
                            "filled": True, "timeout": res.timeout_exit,
                            "fill_price": exit_fill_price})
        # while holding (current_side == "long" and want_long), no order this bar: mark-to-
        # market the HELD position's daily return. Skip bars where we just entered or exited
        # this iteration -- those bars' price P&L was already credited above from fill_price.
        if current_side == "long" and i > 0 and not entry_this_bar and not exit_this_bar:
            day_ret = (float(df["close"].iloc[i]) - float(df["close"].iloc[i - 1])) / float(df["close"].iloc[i - 1])
            realized_returns.iloc[i] += day_ret
        i += 1

    net = realized_returns.copy()
    net.index = df["open_time_utc"] if "open_time_utc" in df.columns else pd.RangeIndex(n)

    fill_rate = fill_rate_fills / fill_rate_attempts if fill_rate_attempts else float("nan")
    mean_adverse_drift = float(np.mean(adverse_drifts)) if adverse_drifts else None
    maker_saving_per_side = base_cost_cfg.taker_rate - base_cost_cfg.maker_rate  # 0.10% per side

    return {
        "net_returns": net,
        "n_transition_attempts": fill_rate_attempts,
        "n_transition_resolved": fill_rate_fills,
        "fill_rate": fill_rate,
        "n_maker_fills": n_maker_fills,
        "n_taker_timeout_fills": n_taker_timeout_fills,
        "n_skipped_entries": skipped_entries,
        "skipped_entry_opportunity_mean_gross_ret": (float(np.mean(skipped_opportunity_gross))
                                                       if skipped_opportunity_gross else None),
        "mean_adverse_drift": mean_adverse_drift,
        "maker_saving_per_side_bps": maker_saving_per_side * 10_000,
        "maker_win_is_real": (mean_adverse_drift is not None and
                               maker_saving_per_side > mean_adverse_drift),
        "total_fees_usd_per_100_notional": total_fees,
        "total_slippage_usd_per_100_notional": total_slippage,
    }


def metrics_from_net(net: pd.Series, bars_per_year: int = 365):
    w_proxy = (net != 0).astype(float)  # crude weight proxy for turnover/exposure metrics (not used for cost -- cost already baked into net)
    return gate.compute_metrics(net, w_proxy, bars_per_year)


def run_symbol(symbol: str, sma_window: int) -> dict:
    df_full = data.load(symbol, "1d")
    pos_full = signals({symbol: df_full}, {"sma_window": sma_window})[symbol]

    df_oos = df_full[df_full.index >= pd.Timestamp(OOS_START, tz="UTC")]
    pos_oos = pos_full.reindex(df_oos.index).fillna(0.0)

    out = {"symbol": symbol, "sma_window": sma_window, "oos_start": OOS_START, "n_bars_oos": len(df_oos)}

    tiers = {
        "base": dict(offset_bps=0.0, stress_fill_prob=False, delay_bars=0, extra_slip_worst_vol=False, base_cost_cfg=CostConfig()),
        "offset_5bp": dict(offset_bps=OFFSET_BPS, stress_fill_prob=False, delay_bars=0, extra_slip_worst_vol=False, base_cost_cfg=CostConfig()),
        "stress_2x_fees": dict(offset_bps=0.0, stress_fill_prob=False, delay_bars=0, extra_slip_worst_vol=False, base_cost_cfg=STRESS_2X_FEES),
        "stress_delay_1bar": dict(offset_bps=0.0, stress_fill_prob=False, delay_bars=1, extra_slip_worst_vol=False, base_cost_cfg=CostConfig()),
        "stress_reduced_fill_prob": dict(offset_bps=0.0, stress_fill_prob=True, delay_bars=0, extra_slip_worst_vol=False, base_cost_cfg=CostConfig()),
        "stress_worst_vol_slippage": dict(offset_bps=0.0, stress_fill_prob=False, delay_bars=0, extra_slip_worst_vol=True, base_cost_cfg=CostConfig()),
    }

    for name, kwargs in tiers.items():
        sim = simulate(df_oos, pos_oos, notional=100.0, **kwargs)
        m = metrics_from_net(sim["net_returns"])
        out[name] = {
            "sim": {k: v for k, v in sim.items() if k != "net_returns"},
            "metrics": m.to_dict() if m else None,
        }

    return out


if __name__ == "__main__":
    best_params = {"BTCUSDT": 50, "ETHUSDT": 200}  # from IS gate selection (see results/regime_sma_maker.json)
    results = {}
    for sym, w in best_params.items():
        print(f"=== {sym} sma_window={w} maker-fill simulation ===")
        r = run_symbol(sym, w)
        results[sym] = r
        for tier in ["base", "offset_5bp", "stress_2x_fees", "stress_delay_1bar",
                     "stress_reduced_fill_prob", "stress_worst_vol_slippage"]:
            m = r[tier]["metrics"]
            sim = r[tier]["sim"]
            print(f"  [{tier}] sharpe={m['sharpe'] if m else None:.3f} cagr={m['cagr'] if m else None:.2%} "
                  f"maxDD={m['max_dd'] if m else None:.2%} fill_rate={sim['fill_rate']:.2f} "
                  f"skipped={sim['n_skipped_entries']} adverse_drift={sim['mean_adverse_drift']}")
        print()

    out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "regime_sma_maker_fillsim.json")

    def _clean(obj):
        if isinstance(obj, dict):
            return {k: _clean(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [_clean(v) for v in obj]
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, float) and (obj != obj):  # NaN
            return None
        return obj

    with open(out_path, "w") as f:
        json.dump(_clean(results), f, indent=2, default=str)
    print(f"Wrote {out_path}")
