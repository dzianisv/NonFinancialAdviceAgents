"""
Full gate + fill-model driver for the xs_momentum strategy candidate.

1. Runs core/gate.py's gate() over the declared PARAM_GRID (strategies/xs_momentum.PARAM_GRID)
   -> IS selection, OOS headline, walk-forward, deflated Sharpe, regimes, stress suite, verdict.
2. Runs sensitivity checks on IS: N=3 vs N=5 (already in PARAM_GRID) + a drop-top-1 ablation
   on the CHOSEN config (holds ranks 2..top_n+1 instead of 1..top_n) to test whether the whole
   edge is carried by a single argmax-style name.
3. Runs an HONEST bar-by-bar maker-fill simulation (core/fills.py) of the chosen config's
   weekly rebalance legs over the OOS window, including all 4 mandated stress tiers, reporting
   fill rate, skipped-entry opportunity cost, adverse drift, and whether the maker "win" is
   real (savings > adverse drift).
4. Benchmarks: hold-BTC and equal-weight-hold-universe over the same OOS window, net of one
   entry taker fee (see harness_self_test.py's buy-and-hold convention).
5. Writes intraday-bot/results/xs_momentum.json with everything above.

Universe for the gate/backtest: the 46 downloaded USDT-major 1d symbols (candidate pool from
which the point-in-time top-30 is drawn each week) -- see strategies/xs_momentum.py docstring
for the survivorship-honesty note on this candidate pool.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import data, gate, fills
from core.costs import CostConfig, STRESS_2X_FEES
from core.universe import point_in_time_universe, coverage_report
from strategies import xs_momentum as xm

INTERVAL = "1d"
BARS_PER_YEAR = gate.BARS_PER_YEAR[INTERVAL]
OOS_START = gate.OOS_START

CANDIDATE_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT",
    "LINKUSDT", "DOTUSDT", "LTCUSDT", "ATOMUSDT", "UNIUSDT", "NEARUSDT", "APTUSDT", "ARBUSDT",
    "OPUSDT", "FILUSDT", "INJUSDT", "TRXUSDT", "ETCUSDT", "XLMUSDT", "ALGOUSDT", "VETUSDT",
    "SANDUSDT", "MANAUSDT", "AXSUSDT", "AAVEUSDT", "GRTUSDT", "THETAUSDT", "XTZUSDT", "CHZUSDT",
    "ICPUSDT", "RUNEUSDT", "SUIUSDT", "SEIUSDT", "TIAUSDT", "LUNAUSDT", "FTTUSDT", "SRMUSDT",
    "RAYUSDT", "BTSUSDT", "COCOSUSDT", "MATICUSDT", "EOSUSDT", "FTMUSDT",
]
DELISTED_OR_FADED_ATTEMPTS = ["SRMUSDT", "BTSUSDT", "COCOSUSDT", "LUNAUSDT", "FTTUSDT", "RAYUSDT"]

TICKET_USD = 166.0  # $500 book / 3 legs ~ $166.67; used for fill-sim notional sizing


def _clean(obj):
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, (np.floating,)):
        return None if obj != obj else float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, float) and obj != obj:  # NaN
        return None
    if isinstance(obj, pd.Timestamp):
        return str(obj)
    return obj


def load_universe() -> dict:
    df_dict = {}
    missing = []
    for s in CANDIDATE_SYMBOLS:
        try:
            df_dict[s] = data.load(s, INTERVAL)
        except FileNotFoundError:
            missing.append(s)
    return df_dict, missing


# ---------------------------------------------------------------------------
# 1) core gate() run over the declared PARAM_GRID
# ---------------------------------------------------------------------------

def run_gate(df_dict: dict) -> dict:
    t0 = time.time()
    report = gate.gate(xm.signals, df_dict, xm.PARAM_GRID, interval=INTERVAL)
    report["_elapsed_sec"] = time.time() - t0
    return report


# ---------------------------------------------------------------------------
# 2) N-sensitivity + drop-top-1 ablation on the CHOSEN config
# ---------------------------------------------------------------------------

def sensitivity_report(df_dict: dict, best_params: dict) -> dict:
    """Compare the chosen config's OOS metrics against: (a) the same lookback with the
    OTHER top_n (3<->5), (b) a drop-top-1 ablation (hold ranks 2..N+1) at the SAME top_n
    and lookback as the chosen config. All scored on the same OOS window, net of costs."""
    lookback = best_params["lookback_days"]
    chosen_n = best_params["top_n"]
    other_n = 5 if chosen_n == 3 else 3

    out = {}
    for label, params in [
        ("chosen", {"lookback_days": lookback, "top_n": chosen_n}),
        (f"alt_top_n_{other_n}", {"lookback_days": lookback, "top_n": other_n}),
        ("drop_top1", {"lookback_days": lookback, "top_n": chosen_n, "drop_top1": True}),
    ]:
        net, w = gate.run_backtest(xm.signals, df_dict, params, CostConfig(), BARS_PER_YEAR, start=OOS_START)
        m = gate.compute_metrics(net, w, BARS_PER_YEAR) if net is not None else None
        out[label] = {"params": params, "oos_metrics": m.to_dict() if m else None}
    return out


# ---------------------------------------------------------------------------
# 3) Honest bar-by-bar maker-fill simulation of the weekly rebalance, chosen config, OOS
# ---------------------------------------------------------------------------

def _weekly_targets(df_dict: dict, params: dict) -> pd.DataFrame:
    """Re-derive, per rebalance Monday, the exact set of picked symbols (not the harness's
    N/top_n-scaled weight -- the real intended per-name weight of 1/top_n) for fill-sim use."""
    lookback = int(params.get("lookback_days", 14))
    top_n = int(params.get("top_n", 3))

    universe_tbl = point_in_time_universe(
        df_dict, top_n=xm.TOP_N_UNIVERSE, trailing_days=xm.TRAILING_VOL_DAYS,
        min_listed_days=xm.MIN_LISTED_DAYS,
    )
    members_by_date = universe_tbl["members"].shift(1)
    mom = xm._momentum_ranks(df_dict, lookback)
    mom_prior = mom.shift(1)
    full_index = mom_prior.index
    weekly_mask = xm._weekly_rebalance_mask(full_index)

    rows = []
    for dt in full_index[weekly_mask]:
        if dt not in members_by_date.index:
            continue
        eligible = members_by_date.loc[dt]
        if not isinstance(eligible, list) or len(eligible) == 0:
            continue
        row = mom_prior.loc[dt, eligible].dropna()
        if row.empty:
            continue
        ranked = row.sort_values(ascending=False)
        picks = ranked.iloc[:top_n].index.tolist()
        rows.append({"date": dt, "picks": picks})
    return pd.DataFrame(rows).set_index("date") if rows else pd.DataFrame(columns=["picks"])


def simulate_fills_oos(df_dict: dict, params: dict, notional_per_leg: float = TICKET_USD,
                        stress_fill_prob: bool = False, delay_bars: int = 0,
                        extra_slip_worst_vol: bool = False,
                        base_cost_cfg: CostConfig = CostConfig()) -> dict:
    """Bar-by-bar maker-fill simulation of the weekly cross-sectional rebalance over the OOS
    window. Each Monday, for each name entering the top-N portfolio: rest a BUY limit at
    Friday's (prior bar's) close, tried on the Monday bar, timeout_bars=1 -> forced market.
    For each name leaving the portfolio: rest a SELL limit at prior close, same timeout rule.
    Names that stay in the portfolio from one week to the next are NOT re-traded (no order,
    no cost) -- only entries/exits generate fill attempts, matching a real weekly-rebalance
    execution plan (not a full liquidate-and-rebuild every week)."""
    weekly = _weekly_targets(df_dict, params)
    if weekly.empty:
        return {"error": "no rebalance events (insufficient data / universe too small)"}

    # OOS-only rebalance dates
    weekly_oos = weekly[weekly.index >= pd.Timestamp(OOS_START, tz="UTC")]
    if weekly_oos.empty:
        return {"error": "no OOS rebalance events"}

    vpt_by_sym = {}
    for sym, df in df_dict.items():
        df_pos = df.reset_index(drop=True)
        vpt_by_sym[sym] = fills.vol_p95_threshold(df_pos)

    held: set[str] = set()
    fill_attempts = 0
    fill_successes = 0
    n_maker_fills = 0
    n_taker_timeout_fills = 0
    skipped_entries = 0
    skipped_opportunity_gross = []
    adverse_drifts = []
    total_fees = 0.0
    total_slippage = 0.0
    # per-symbol realized daily net-of-cost return series (only while actually held, i.e.
    # only bars where a maker fill (or forced taker) actually established the position --
    # opportunity cost from skipped entries is tracked separately, never counted as realized).
    realized = {sym: pd.Series(0.0, index=df_dict[sym].index) for sym in df_dict}
    intervals = {sym: [] for sym in df_dict}  # list of (start_bar_pos, end_bar_pos) per symbol
    open_start: dict[str, int] = {}

    rebalance_dates = list(weekly_oos.index)
    for dt in rebalance_dates:
        picks = set(weekly_oos.loc[dt, "picks"])
        to_enter = picks - held
        to_exit = held - picks
        # names staying held: no order, no cost -- continue accruing mark-to-market below.
        for sym in to_enter:
            df = df_dict[sym]
            df_pos = df.reset_index(drop=True)
            if dt not in df.index:
                continue
            bar_pos = df.index.get_loc(dt)
            if not isinstance(bar_pos, (int, np.integer)):
                continue
            prior_close = float(df["close"].iloc[bar_pos - 1]) if bar_pos > 0 else float(df["open"].iloc[bar_pos])
            fill_attempts += 1
            res = fills.simulate_entry(
                df_pos, bar_pos, "buy", prior_close, base_cost_cfg, notional_per_leg,
                stress_fill_prob=stress_fill_prob, delay_bars=delay_bars,
                extra_slip_worst_vol=extra_slip_worst_vol, vol_p95_threshold=vpt_by_sym[sym],
            )
            if res.filled:
                fill_successes += 1
                n_maker_fills += 1
                total_fees += res.fee_usd
                total_slippage += res.slippage_usd
                fill_bar = res.bar_index
                realized[sym].iloc[fill_bar] -= (res.fee_usd + res.slippage_usd) / notional_per_leg
                adv = fills.adverse_drift(df_pos, fill_bar, "buy")
                if adv is not None:
                    adverse_drifts.append(adv)
                held.add(sym)
                open_start[sym] = fill_bar
            else:
                skipped_entries += 1
                if bar_pos + 1 < len(df_pos):
                    c0 = float(df_pos["close"].iloc[bar_pos])
                    c1 = float(df_pos["close"].iloc[bar_pos + 1])
                    if c0:
                        skipped_opportunity_gross.append((c1 - c0) / c0)
                # not added to `held` -- signal skipped, no position carried

        for sym in to_exit:
            df = df_dict[sym]
            df_pos = df.reset_index(drop=True)
            if dt not in df.index or sym not in open_start:
                held.discard(sym)
                open_start.pop(sym, None)
                continue
            bar_pos = df.index.get_loc(dt)
            if not isinstance(bar_pos, (int, np.integer)):
                held.discard(sym)
                open_start.pop(sym, None)
                continue
            prior_close = float(df["close"].iloc[bar_pos - 1]) if bar_pos > 0 else float(df["open"].iloc[bar_pos])
            fill_attempts += 1
            res = fills.simulate_exit_with_timeout(
                df_pos, bar_pos, "sell", prior_close, timeout_bars=1, cost_cfg=base_cost_cfg,
                notional=notional_per_leg, stress_fill_prob=stress_fill_prob, delay_bars=delay_bars,
                extra_slip_worst_vol=extra_slip_worst_vol, vol_p95_threshold=vpt_by_sym[sym],
            )
            fill_successes += 1  # exit always resolves (maker or forced taker)
            fill_bar = res.bar_index
            total_fees += res.fee_usd
            total_slippage += res.slippage_usd
            realized[sym].iloc[fill_bar] -= (res.fee_usd + res.slippage_usd) / notional_per_leg
            adv = fills.adverse_drift(df_pos, fill_bar, "sell")
            if adv is not None:
                adverse_drifts.append(adv)
            if res.is_maker:
                n_maker_fills += 1
            else:
                n_taker_timeout_fills += 1
            intervals[sym].append((open_start[sym], fill_bar))
            held.discard(sym)
            del open_start[sym]

    # any still-open position at the end of the OOS window: mark held through the last bar
    for sym, start_bar in open_start.items():
        intervals[sym].append((start_bar, len(df_dict[sym]) - 1))

    for sym, ivs in intervals.items():
        df = df_dict[sym]
        close = df["close"].reset_index(drop=True)
        ret = close.pct_change().fillna(0.0)
        for (s, e) in ivs:
            if e <= s:
                continue
            # accrue close-to-close return for bars (s, e] -- entered on bar s (at fill price,
            # already priced into cost, not return), exited on bar e.
            realized[sym].iloc[s + 1: e + 1] = realized[sym].iloc[s + 1: e + 1].to_numpy() + ret.iloc[s + 1: e + 1].to_numpy()

    # portfolio return: equal-weight across the top_n slots (using the SAME intervals --
    # i.e. realized capital allocation, not the idealized target; a skipped entry leaves its
    # slot in cash for that stretch, contributing 0 return, which is the honest opportunity
    # cost of the no-fill fallback rather than a phantom position).
    top_n = int(params.get("top_n", 3))
    M = pd.concat(realized, axis=1)
    port_oos = M[M.index >= pd.Timestamp(OOS_START, tz="UTC")]
    port_net = port_oos.sum(axis=1) / top_n  # equal-weight across top_n slots (idle slot if skipped = cash, 0 return)

    fill_rate = fill_successes / fill_attempts if fill_attempts else float("nan")
    mean_adverse_drift = float(np.mean(adverse_drifts)) if adverse_drifts else None
    maker_saving_per_side = base_cost_cfg.taker_rate - base_cost_cfg.maker_rate

    m = gate.compute_metrics(port_net, port_net.abs(), BARS_PER_YEAR)

    return {
        "metrics": m.to_dict() if m else None,
        "n_rebalance_dates_oos": len(rebalance_dates),
        "n_fill_attempts": fill_attempts,
        "n_fill_successes": fill_successes,
        "fill_rate": fill_rate,
        "n_maker_fills": n_maker_fills,
        "n_taker_timeout_fills": n_taker_timeout_fills,
        "n_skipped_entries": skipped_entries,
        "skipped_entry_opportunity_mean_gross_ret": (
            float(np.mean(skipped_opportunity_gross)) if skipped_opportunity_gross else None),
        "mean_adverse_drift": mean_adverse_drift,
        "maker_saving_per_side_bps": maker_saving_per_side * 10_000,
        "maker_win_is_real": (mean_adverse_drift is not None and maker_saving_per_side > mean_adverse_drift),
        "total_fees_usd_per_leg_notional": total_fees,
        "total_slippage_usd_per_leg_notional": total_slippage,
        "notional_per_leg_usd": notional_per_leg,
    }


def fill_model_report(df_dict: dict, best_params: dict) -> dict:
    tiers = {
        "base": dict(stress_fill_prob=False, delay_bars=0, extra_slip_worst_vol=False, base_cost_cfg=CostConfig()),
        "stress_2x_fees": dict(stress_fill_prob=False, delay_bars=0, extra_slip_worst_vol=False, base_cost_cfg=STRESS_2X_FEES),
        "stress_delay_1bar": dict(stress_fill_prob=False, delay_bars=1, extra_slip_worst_vol=False, base_cost_cfg=CostConfig()),
        "stress_reduced_fill_prob": dict(stress_fill_prob=True, delay_bars=0, extra_slip_worst_vol=False, base_cost_cfg=CostConfig()),
        "stress_worst_vol_slippage": dict(stress_fill_prob=False, delay_bars=0, extra_slip_worst_vol=True, base_cost_cfg=CostConfig()),
    }
    out = {}
    for name, kwargs in tiers.items():
        out[name] = simulate_fills_oos(df_dict, best_params, notional_per_leg=TICKET_USD, **kwargs)
    return out


# ---------------------------------------------------------------------------
# 4) Benchmarks: hold-BTC, equal-weight-hold-universe, same OOS window
# ---------------------------------------------------------------------------

def benchmarks(df_dict: dict) -> dict:
    out = {}
    from core.costs import TAKER_RATE

    btc = df_dict["BTCUSDT"]
    oos_close = btc["close"]
    oos_close = oos_close[oos_close.index >= pd.Timestamp(OOS_START, tz="UTC")]
    ret = oos_close.pct_change().fillna(0.0)
    net_hold = ret.copy()
    net_hold.iloc[0] = net_hold.iloc[0] - TAKER_RATE
    w_hold = pd.Series(1.0, index=oos_close.index)
    m_hold = gate.compute_metrics(net_hold, w_hold, BARS_PER_YEAR)
    out["hold_btc"] = m_hold.to_dict() if m_hold else None

    # equal-weight hold of the full 46-symbol candidate universe, one entry fee per name,
    # rebalanced never (buy-and-hold basket) -- benchmark for "did stock-picking beat just
    # owning the whole candidate pool equally".
    rets = {}
    for sym, df in df_dict.items():
        c = df["close"]
        c = c[c.index >= pd.Timestamp(OOS_START, tz="UTC")]
        if len(c) < 5:
            continue
        r = c.pct_change().fillna(0.0)
        r.iloc[0] -= TAKER_RATE
        rets[sym] = r
    M = pd.concat(rets, axis=1).fillna(0.0)
    port = M.mean(axis=1)
    w = pd.Series(1.0, index=port.index)
    m_ew = gate.compute_metrics(port, w, BARS_PER_YEAR)
    out["equal_weight_hold_universe"] = m_ew.to_dict() if m_ew else None
    out["equal_weight_hold_universe_n_symbols"] = len(rets)

    return out


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    print("Loading candidate universe...")
    df_dict, missing = load_universe()
    print(f"  loaded {len(df_dict)} / {len(CANDIDATE_SYMBOLS)} symbols; missing: {missing}")

    cov = coverage_report(df_dict, DELISTED_OR_FADED_ATTEMPTS)

    print("\n=== Look-ahead canary + shift-collapse check (first grid config) ===")
    canary = gate.look_ahead_canary(xm.signals, df_dict, xm.PARAM_GRID[0])
    print(" canary:", canary)
    shift_check = gate.shift_collapse_check(xm.signals, df_dict, xm.PARAM_GRID[0], bars_per_year=BARS_PER_YEAR)
    print(" shift_check:", shift_check)

    print("\n=== Running gate() over declared PARAM_GRID ===")
    gate_report = run_gate(df_dict)
    print(f" verdict={gate_report['verdict']} elapsed={gate_report['_elapsed_sec']:.1f}s")
    print(f" best_params={gate_report['best_params']}")
    print(f" reasons={gate_report.get('reasons')}")

    best_params = gate_report["best_params"]

    print("\n=== N-sensitivity + drop-top-1 ablation (chosen config) ===")
    sens = sensitivity_report(df_dict, best_params)
    for k, v in sens.items():
        m = v["oos_metrics"]
        print(f"  {k}: params={v['params']} sharpe={m['sharpe'] if m else None}")

    print("\n=== Maker-fill-model simulation (chosen config, OOS, all stress tiers) ===")
    fillsim = fill_model_report(df_dict, best_params)
    for tier, r in fillsim.items():
        m = r.get("metrics")
        print(f"  [{tier}] sharpe={m['sharpe'] if m else None} fill_rate={r.get('fill_rate')} "
              f"skipped={r.get('n_skipped_entries')} adverse_drift={r.get('mean_adverse_drift')} "
              f"maker_win_is_real={r.get('maker_win_is_real')}")

    print("\n=== Benchmarks (hold-BTC, equal-weight-hold-universe), same OOS window ===")
    bm = benchmarks(df_dict)
    print("  hold_btc:", bm["hold_btc"]["sharpe"] if bm["hold_btc"] else None)
    print("  equal_weight_hold_universe:", bm["equal_weight_hold_universe"]["sharpe"] if bm["equal_weight_hold_universe"] else None)

    full_report = {
        "strategy": "xs_momentum",
        "config_grid_declared": xm.PARAM_GRID,
        "n_trials": len(xm.PARAM_GRID),
        "candidate_universe_n_symbols": len(df_dict),
        "candidate_universe_missing_symbols": missing,
        "universe_coverage_report": cov,
        "canary": canary,
        "shift_collapse_check": shift_check,
        "gate": {k: v for k, v in gate_report.items() if k != "_elapsed_sec"},
        "gate_elapsed_sec": gate_report["_elapsed_sec"],
        "sensitivity": sens,
        "fill_model_report": fillsim,
        "benchmarks": bm,
        "ticket_usd_per_leg": TICKET_USD,
    }

    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "xs_momentum.json")
    with open(out_path, "w") as f:
        json.dump(_clean(full_report), f, indent=2, default=str)
    print(f"\nWrote {out_path}")
    return full_report


if __name__ == "__main__":
    main()
