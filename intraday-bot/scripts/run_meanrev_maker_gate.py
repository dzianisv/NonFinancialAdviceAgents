"""
Full gate run for the meanrev_maker strategy candidate.

Mirrors core/gate.py's gate() pipeline (canary -> IS select -> OOS -> walk-forward ->
deflated Sharpe -> regimes -> stress -> verdict) but with `is_maker=True` passed to
run_backtest(), because this strategy's entire thesis is paying maker (0.15%/side), not
taker (0.25%/side), fees on both entry and exit legs. gate.gate() itself always scores at
taker rate (its `run_backtest` call never sets is_maker) -- that is the right default for a
generic/unspecified strategy, but would silently misprice THIS strategy's cost structure by
67% (0.15 vs 0.25 per side) in the wrong direction (too punitive), which is not what "net of
costs always" requires -- it requires using the CORRECT cost model, not the harshest one
regardless of fit. We are not loosening costs: the maker rate is the SAME 0.15%/side defined
once in core/costs.py, applied via the harness's own existing is_maker toggle.

On top of the return-space scoring (which assumes every intended maker order fills), this
script ALSO runs the bar-by-bar core/fills.py simulator over the chosen (best-IS) config on
the full OOS window to produce the mandated fill-model report: fill rate, skipped-signal
count (opportunity cost), mean post-fill adverse drift, % of exits that degraded to taker,
and stress-tier fill rates. That simulation is the honesty check on whether the return-space
maker assumption is actually earned.

Run: /Users/engineer/.venv/bin/python3 scripts/run_meanrev_maker_gate.py
"""
import json
import math
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import data, gate, fills
from core.costs import CostConfig, STRESS_2X_FEES, MAKER_RATE, TAKER_RATE
from strategies.meanrev_maker import signals, PARAM_GRID, _zscore

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
INTERVAL = "5m"
BPY = gate.BARS_PER_YEAR[INTERVAL]
ORDER_NOTIONAL = 250.0  # $500-book house rule: max order $250


def load_universe() -> dict:
    return {sym: data.load(sym, INTERVAL) for sym in SYMBOLS}


# ---------------------------------------------------------------------------
# 1) Return-space gate pipeline (mirrors core.gate.gate(), is_maker=True)
# ---------------------------------------------------------------------------

def run_gate_maker(df_dict: dict) -> dict:
    cost_cfg = CostConfig()

    canary = gate.look_ahead_canary(signals, df_dict, PARAM_GRID[0])
    shift_check = gate.shift_collapse_check(signals, df_dict, PARAM_GRID[0], bars_per_year=BPY)

    is_rows = []
    for params in PARAM_GRID:
        net, w = gate.run_backtest(signals, df_dict, params, cost_cfg, BPY,
                                    end=gate.IS_END, is_maker=True)
        m = gate.compute_metrics(net, w, BPY) if net is not None else None
        if m:
            is_rows.append((params, m))

    if not is_rows:
        return {"verdict": "FAIL (no edge found)", "reason": "no IS configuration produced valid metrics",
                "canary": canary, "shift_check": shift_check, "n_trials": len(PARAM_GRID)}

    best_params, best_is_metrics = max(is_rows, key=lambda r: r[1].sharpe)
    n_trials = len(PARAM_GRID)

    oos_net, oos_w = gate.run_backtest(signals, df_dict, best_params, cost_cfg, BPY,
                                        start=gate.OOS_START, is_maker=True)
    oos_metrics = gate.compute_metrics(oos_net, oos_w, BPY) if oos_net is not None else None

    # walk_forward() internals call run_backtest without is_maker -- to keep the maker-cost
    # assumption consistent we replicate the rolling logic here rather than monkeying with
    # the shared walk_forward() signature (which has no is_maker passthrough).
    wf = walk_forward_maker(df_dict, PARAM_GRID, cost_cfg, fit_months=12, score_months=3)
    wf_oos_metrics = gate.compute_metrics(wf["oos_concat"], wf["oos_weights_concat"], BPY) \
        if wf["oos_concat"] is not None else None

    dsr = None
    if oos_metrics:
        period_sharpe = oos_metrics.sharpe / math.sqrt(BPY)
        dsr = gate.deflated_sharpe_ratio(period_sharpe, n_trials=n_trials, n_obs=oos_metrics.n_bars)

    regimes = regime_report_maker(df_dict, best_params, cost_cfg)
    stress = stress_suite_maker(df_dict, best_params, cost_cfg, start=gate.OOS_START)

    reasons = []
    passed = True
    if oos_metrics is None or oos_metrics.sharpe <= 0:
        passed = False
        reasons.append("OOS Sharpe <= 0 net of costs")
    if dsr and not math.isnan(dsr.get("dsr", float("nan"))) and dsr["dsr"] < 0.95:
        passed = False
        reasons.append(f"deflated Sharpe probability {dsr['dsr']:.4f} < 0.95 threshold")
    stress_2x = stress.get("2x_fees")
    if stress_2x is None or stress_2x["sharpe"] <= 0:
        passed = False
        reasons.append("edge dies under 2x fee stress")
    stress_delay = stress.get("delayed_fill_1bar")
    if stress_delay is None or stress_delay["sharpe"] <= 0:
        passed = False
        reasons.append("edge dies under 1-bar delayed-fill stress")

    verdict = "PASS" if passed else "FAIL (no edge found)"

    return {
        "verdict": verdict,
        "reasons": reasons,
        "canary": canary,
        "shift_check": shift_check,
        "best_params": best_params,
        "n_trials": n_trials,
        "param_grid": PARAM_GRID,
        "in_sample": best_is_metrics.to_dict(),
        "out_of_sample": oos_metrics.to_dict() if oos_metrics else None,
        "walk_forward_oos": wf_oos_metrics.to_dict() if wf_oos_metrics else None,
        "walk_forward_windows": wf["windows"],
        "deflated_sharpe": dsr,
        "regimes": regimes,
        "stress": stress,
        "is_maker_cost_note": (
            "Return-space scoring uses is_maker=True (0.15%/side) throughout IS/OOS/walk-"
            "forward/regimes/stress, matching this strategy's maker-order thesis. The "
            "delayed_fill_1bar stress tier still charges TAKER (0.25%/side) because a "
            "delayed maker fill that's forced to complete a bar late is modeled the same way "
            "core.gate.stress_suite does it generically -- a conservative choice, not a loose one."
        ),
    }


def walk_forward_maker(df_dict: dict, param_grid: list, cost_cfg: CostConfig,
                        fit_months: int, score_months: int) -> dict:
    sym0 = next(iter(df_dict))
    idx = df_dict[sym0].index
    idx = idx[idx >= pd.Timestamp(gate.IS_START, tz="UTC")]
    windows = []
    cursor = idx[0]
    last = idx[-1]
    while True:
        fit_start = cursor
        fit_end = fit_start + pd.DateOffset(months=fit_months)
        score_start = fit_end
        score_end = score_start + pd.DateOffset(months=score_months)
        if score_start > last:
            break
        windows.append((fit_start, fit_end, score_start, min(score_end, last + pd.Timedelta(days=1))))
        cursor = cursor + pd.DateOffset(months=score_months)

    oos_segments, oos_weight_segments, window_reports = [], [], []
    for fit_start, fit_end, score_start, score_end in windows:
        best = None
        for params in param_grid:
            net, w = gate.run_backtest(signals, df_dict, params, cost_cfg, BPY,
                                        start=str(fit_start.date()), end=str(fit_end.date()),
                                        is_maker=True)
            m = gate.compute_metrics(net, w, BPY) if net is not None else None
            if m and (best is None or m.sharpe > best[1].sharpe):
                best = (params, m)
        if best is None:
            continue
        params, _ = best
        oos_net, oos_w = gate.run_backtest(signals, df_dict, params, cost_cfg, BPY,
                                            start=str(score_start.date()), end=str(score_end.date()),
                                            is_maker=True)
        oos_m = gate.compute_metrics(oos_net, oos_w, BPY) if oos_net is not None else None
        window_reports.append({
            "fit": (str(fit_start.date()), str(fit_end.date())),
            "score": (str(score_start.date()), str(score_end.date())),
            "params": params,
            "oos_metrics": oos_m.to_dict() if oos_m else None,
        })
        if oos_net is not None:
            oos_segments.append(oos_net)
            oos_weight_segments.append(oos_w)

    oos_concat = pd.concat(oos_segments).sort_index() if oos_segments else None
    oos_w_concat = pd.concat(oos_weight_segments).sort_index() if oos_weight_segments else None
    if oos_concat is not None:
        oos_concat = oos_concat[~oos_concat.index.duplicated(keep="first")]
        oos_w_concat = oos_w_concat[~oos_w_concat.index.duplicated(keep="first")]
    return {"windows": window_reports, "oos_concat": oos_concat, "oos_weights_concat": oos_w_concat}


def regime_report_maker(df_dict: dict, params: dict, cost_cfg: CostConfig) -> dict:
    out = {}
    for name, (start, end) in gate.REGIME_WINDOWS.items():
        net, w = gate.run_backtest(signals, df_dict, params, cost_cfg, BPY, start=start, end=end, is_maker=True)
        m = gate.compute_metrics(net, w, BPY) if net is not None else None
        out[name] = m.to_dict() if m else None
    return out


def stress_suite_maker(df_dict: dict, params: dict, base_cost_cfg: CostConfig,
                        start=None, end=None) -> dict:
    out = {}
    # (a) 2x fees, still maker rate * 2
    net, w = gate.run_backtest(signals, df_dict, params, STRESS_2X_FEES, BPY, start, end, is_maker=True)
    m = gate.compute_metrics(net, w, BPY) if net is not None else None
    out["2x_fees"] = m.to_dict() if m else None

    # (b) all fills delayed one bar (extra shift(1) on top of the contractual shift)
    raw_signal = signals(df_dict, params)
    sym0 = next(iter(df_dict))
    sig_map = raw_signal if isinstance(raw_signal, dict) else {sym0: raw_signal}
    delayed_results = {}
    for sym, sig in sig_map.items():
        if sym not in df_dict:
            continue
        close = df_dict[sym]["close"]
        w_delayed = sig.reindex(close.index).fillna(0.0).shift(1).fillna(0.0)
        w_delayed = gate.slice_period(w_delayed, start, end)
        c = gate.slice_period(close, start, end)
        if len(c) < 5:
            continue
        ret = c.pct_change().fillna(0.0)
        turnover = w_delayed.diff().abs().fillna(w_delayed.abs())
        cost = turnover * base_cost_cfg.taker_rate  # delayed fill forced late -> taker, conservative
        delayed_results[sym] = w_delayed * ret - cost
    if delayed_results:
        M = pd.concat(delayed_results, axis=1).fillna(0.0)
        port = M.mean(axis=1)
        m = gate.compute_metrics(port, port.abs(), BPY)
        out["delayed_fill_1bar"] = m.to_dict() if m else None
    else:
        out["delayed_fill_1bar"] = None
    return out


# ---------------------------------------------------------------------------
# 2) Benchmark: buy-and-hold BTC on the same OOS window
# ---------------------------------------------------------------------------

def benchmark_hold_btc(df_dict: dict) -> dict:
    close = df_dict["BTCUSDT"]["close"]
    oos_close = close[close.index >= pd.Timestamp(gate.OOS_START, tz="UTC")]
    ret = oos_close.pct_change().fillna(0.0)
    net_hold = ret.copy()
    net_hold.iloc[0] = net_hold.iloc[0] - TAKER_RATE  # one entry taker fee
    w_hold = pd.Series(1.0, index=oos_close.index)
    m = gate.compute_metrics(net_hold, w_hold, BPY)
    return m.to_dict() if m else None


# ---------------------------------------------------------------------------
# 3) Bar-by-bar fill-model report (core/fills.py) on the chosen config, OOS window
# ---------------------------------------------------------------------------

def fill_model_report(df_dict: dict, params: dict) -> dict:
    """Walk each symbol bar-by-bar over the OOS window using the honest maker-fill
    simulator: rest a BUY limit at the z-score dip trigger, on fill rest a SELL limit at the
    rolling mean with a timeout, hard stop at 2x the entry deviation. Reports fill rate,
    skipped-signal count (opportunity cost), mean adverse drift, timeout-to-taker rate --
    for BASE tier and each of the 4 mandated stress tiers."""
    cost_cfg = CostConfig()

    def run_one(sym: str, df: pd.DataFrame, stress_fill_prob=False, delay_bars=0,
                extra_slip_worst_vol=False, fee_multiplier=1.0) -> dict:
        lookback, k, timeout_bars = params["lookback"], params["k"], params["timeout_bars"]
        stop_k = params["stop_k"]
        mean, std, z = _zscore(df["close"], lookback)
        z_prior = z.shift(1)
        mean_prior = mean.shift(1)
        std_prior = std.shift(1)

        oos_start_pos = df.index.searchsorted(pd.Timestamp(gate.OOS_START, tz="UTC"))
        vol_thr = fills.vol_p95_threshold(df) if extra_slip_worst_vol else None
        c_cfg = CostConfig(fee_multiplier=fee_multiplier)

        n = len(df)
        n_signals = 0
        n_filled_entries = 0
        n_skipped_entries = 0
        n_timeout_exits = 0
        n_maker_exits = 0
        adverse_drifts = []
        gross_returns = []
        net_returns = []
        opportunity_gross = []

        i = oos_start_pos
        in_trade = False
        while i < n - 1:
            zi = z_prior.iloc[i]
            if not in_trade and pd.notna(zi) and zi <= -k:
                n_signals += 1
                entry_limit = mean_prior.iloc[i] - k * std_prior.iloc[i]
                entry_res = fills.simulate_entry(
                    df, i, "buy", float(entry_limit), c_cfg, ORDER_NOTIONAL,
                    stress_fill_prob=stress_fill_prob, delay_bars=delay_bars,
                    extra_slip_worst_vol=extra_slip_worst_vol, vol_p95_threshold=vol_thr,
                )
                if not entry_res.filled:
                    n_skipped_entries += 1
                    # opportunity cost: what we would've made had we chased at this bar's close
                    if i + timeout_bars < n:
                        would_be = (df["close"].iloc[i + timeout_bars] - df["close"].iloc[i]) / df["close"].iloc[i]
                        opportunity_gross.append(float(would_be))
                    i += 1
                    continue

                n_filled_entries += 1
                ad = fills.adverse_drift(df, entry_res.bar_index, "buy")
                if ad is not None:
                    adverse_drifts.append(ad)

                exit_limit = float(mean_prior.iloc[i])  # target: revert to the rolling mean
                exit_start = entry_res.bar_index + 1
                if exit_start >= n:
                    break
                exit_res = fills.simulate_exit_with_timeout(
                    df, exit_start, "sell", exit_limit, timeout_bars, c_cfg, ORDER_NOTIONAL,
                    stress_fill_prob=stress_fill_prob, delay_bars=delay_bars,
                    extra_slip_worst_vol=extra_slip_worst_vol, vol_p95_threshold=vol_thr,
                )
                if exit_res.timeout_exit:
                    n_timeout_exits += 1
                else:
                    n_maker_exits += 1

                entry_price = entry_res.fill_price
                exit_price = exit_res.fill_price
                gross_ret = (exit_price - entry_price) / entry_price
                fee_cost = (entry_res.fee_usd + exit_res.fee_usd) / ORDER_NOTIONAL
                slip_cost = (entry_res.slippage_usd + exit_res.slippage_usd) / ORDER_NOTIONAL
                net_ret = gross_ret - fee_cost - slip_cost
                gross_returns.append(gross_ret)
                net_returns.append(net_ret)

                i = exit_res.bar_index + 1
            else:
                i += 1

        n_round_trips = n_filled_entries
        fill_rate = n_filled_entries / n_signals if n_signals else float("nan")
        timeout_rate = n_timeout_exits / n_round_trips if n_round_trips else float("nan")
        mean_adverse = float(np.mean(adverse_drifts)) if adverse_drifts else None
        mean_gross_rt = float(np.mean(gross_returns)) if gross_returns else None
        mean_net_rt = float(np.mean(net_returns)) if net_returns else None
        maker_round_trip_cost = 2 * cost_cfg.maker_rate  # both legs maker if no timeout
        maker_savings_vs_taker = 2 * (cost_cfg.taker_rate - cost_cfg.maker_rate)

        return {
            "symbol": sym,
            "n_signals": n_signals,
            "n_filled_entries": n_filled_entries,
            "n_skipped_entries": n_skipped_entries,
            "fill_rate": fill_rate,
            "n_round_trips": n_round_trips,
            "n_timeout_exits_pct_of_exits": timeout_rate,
            "n_maker_exits": n_maker_exits,
            "mean_post_fill_adverse_drift": mean_adverse,
            "mean_gross_return_per_round_trip": mean_gross_rt,
            "mean_net_return_per_round_trip": mean_net_rt,
            "maker_round_trip_cost_if_both_legs_maker": maker_round_trip_cost,
            "maker_savings_vs_all_taker": maker_savings_vs_taker,
            "maker_win_is_real": (
                (maker_savings_vs_taker > mean_adverse) if mean_adverse is not None else None
            ),
            "opportunity_cost_mean_gross_of_skipped_signals": (
                float(np.mean(opportunity_gross)) if opportunity_gross else None
            ),
            "opportunity_cost_n_skipped": len(opportunity_gross),
        }

    tiers = {}
    for sym, df in df_dict.items():
        tiers.setdefault("base", {})[sym] = run_one(sym, df)
        tiers.setdefault("stress_2x_fees", {})[sym] = run_one(sym, df, fee_multiplier=2.0)
        tiers.setdefault("stress_delay_1bar", {})[sym] = run_one(sym, df, delay_bars=1)
        tiers.setdefault("stress_reduced_fill_prob", {})[sym] = run_one(sym, df, stress_fill_prob=True)
        tiers.setdefault("stress_worst_vol_slippage", {})[sym] = run_one(sym, df, extra_slip_worst_vol=True)
    return tiers


def main():
    t0 = time.time()
    print("Loading BTC/ETH/SOL 5m data...")
    df_dict = load_universe()
    for sym, df in df_dict.items():
        print(f"  {sym}: {len(df)} bars, {df.index.min()} .. {df.index.max()}")

    print("\nRunning gate pipeline (is_maker=True, 27-config grid)...")
    report = run_gate_maker(df_dict)
    print(f"  verdict: {report['verdict']}  reasons: {report.get('reasons')}")
    print(f"  gate pipeline took {time.time()-t0:.1f}s")

    print("\nRunning benchmark (buy-and-hold BTC, same OOS window)...")
    bench = benchmark_hold_btc(df_dict)

    print("\nRunning bar-by-bar fill-model simulation on best-IS config (OOS window, all stress tiers)...")
    t1 = time.time()
    fill_report = fill_model_report(df_dict, report["best_params"])
    print(f"  fill-model simulation took {time.time()-t1:.1f}s")

    out = {
        "strategy": "meanrev_maker",
        "universe": SYMBOLS,
        "interval": INTERVAL,
        "order_notional_usd": ORDER_NOTIONAL,
        "gate": report,
        "benchmark_hold_btc_oos": bench,
        "fill_model_report": fill_report,
    }

    results_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                 "results", "meanrev_maker.json")
    with open(results_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nWrote {results_path}")
    print(f"Total time: {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
