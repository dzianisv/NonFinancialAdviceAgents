"""
XS_MOMENTUM — cross-sectional crypto momentum, long-only.

Universe: point-in-time top-30 by TRAILING 30d quote volume (core/universe.py), rebuilt
fresh at every Monday 00:00 UTC rebalance using only data with timestamp < that Monday
(no today-liquidity filtering, no look-ahead in membership -- see universe construction
note below). Signal: rank the eligible universe by trailing K-day momentum (K in
{7, 14, 28}, tuned IS-only), hold the top-N (N in {3, 5}, tuned IS-only) equal-weight,
rebalance weekly at the Monday 00:00 UTC boundary. Signal only -- no execution logic here;
the harness (core/gate.py for the flat-cost gate path, core/fills.py for the maker-fill-sim
report) owns all fills/costs.

--- Universe construction, stated honestly ---
core.universe.point_in_time_universe() ranks by TRAILING volume only (never same-day or
future volume), and gates entry to 90d of listed history -- this already avoids the classic
"rank on a volume spike that happened because the coin later mooned" look-ahead. BUT the
input `df_dict` to that function is whatever symbol set we historically DOWNLOADED, which is
itself a survivorship-biased sample: Binance Vision has no delisted-symbol registry (see
core/universe.py coverage_report() and the architect's build note), so any USDT pair that
was fully purged from data.binance.vision is invisible to this backtest -- it can never be
"discovered" as a top-30 member on some historical date even if it genuinely was one. We
partially mitigate this by including the handful of delisted/faded symbols we COULD still
fetch (SRMUSDT, BTSUSDT, COCOSUSDT genuinely delisted mid-timeline; LUNAUSDT/FTTUSDT/RAYUSDT
turned out to still be listed, see architect notes) in the candidate df_dict passed to the
gate, so they DO compete for top-30 slots on dates before their history ends. This is
"quantify but not eliminate" survivorship, exactly as core/universe.py's coverage_report()
documents -- it is NOT full survivorship-bias-free coverage, and the gap runs in the
optimistic direction (some dead coins we can never see at all).

--- Prior-bar-close discipline ---
Rebalance decisions at Monday 00:00 UTC bar t are based on:
  - universe membership computed from volume data strictly BEFORE bar t (point_in_time_universe
    is itself point-in-time correct: trailing_vol.rolling(...) at date d only uses days <= d,
    and we additionally shift the whole membership series by one bar so bar t's membership
    reflects date < t, never date == t or later)
  - momentum computed from close[t-1] vs close[t-1-K] (K-day pct_change of close, itself
    shifted by one more bar so bar t's ranking never touches bar t's own close)
Both membership and momentum ranks are independently shift(1)'d before being combined into
a target-weight Series, so bar t's target weight uses only information dated < t.

--- N=3 sensitivity / argmax-picking warning ---
Repo memory (scalable-alpha-mirage) already flagged N=1/N=3-style argmax stock-picking as a
dead idea for equities -- picking the single "best" name by a noisy in-sample rank statistic
tends to be fitting noise, not signal. At N=3 out of a top-30 universe we are one step above
argmax. PARAM_GRID below deliberately includes N=5 alongside N=3 so the report can compare
sensitivity, and results/xs_momentum.json additionally reports a "drop-top-1" ablation
(hold ranks 2-3 or 2-5 instead of 1-3 or 1-5) on the CHOSEN config to test whether the whole
edge (if any) is carried by a single name.
"""
from __future__ import annotations

import pandas as pd

from core.universe import point_in_time_universe

TOP_N_UNIVERSE = 30
TRAILING_VOL_DAYS = 30
MIN_LISTED_DAYS = 90


def _weekly_rebalance_mask(index: pd.DatetimeIndex) -> pd.Series:
    """True on the first bar of each Monday-00:00-UTC week present in `index` (house-rule
    weekly boundary, WEEK_START_DOW=0 == Monday, matches core.gate.week_start_utc)."""
    dow = index.dayofweek  # Monday = 0
    return pd.Series(dow == 0, index=index)


def _momentum_ranks(df_dict: dict, lookback_days: int) -> pd.DataFrame:
    """Per-symbol trailing `lookback_days` close-to-close momentum, aligned on the union of
    all symbols' daily UTC index, decided using close[t-1] / close[t-1-lookback] (i.e. the
    raw pct_change series is computed on each bar's OWN close, then the whole column is
    shift(1)'d by the caller before use -- kept as a separate raw computation here so the
    shift is applied exactly once, centrally, in `signals()`)."""
    cols = {sym: df["close"].pct_change(lookback_days) for sym, df in df_dict.items()}
    return pd.concat(cols, axis=1).sort_index()


def signals(df_dict: dict, params: dict) -> dict:
    """params: {"lookback_days": int in {7,14,28}, "top_n": int in {3,5},
    "drop_top1": bool (ablation: exclude the single highest-momentum name, hold next top_n)}.

    Returns {symbol: pd.Series} of target weight, decided on PRIOR bar close only. Weight
    for a held symbol on a rebalance-effective bar is `len(df_dict) / top_n` (NOT 1/top_n) --
    this is a deliberate scaling to work correctly with core.gate.run_backtest's
    `M.mean(axis=1)` portfolio aggregation, which averages returns across ALL symbols in
    df_dict, not just the held subset. Algebra: w_i = N/k for k held names (0 for the rest)
    -> mean_i(w_i * ret_i) over N symbols = (1/N)*(N/k)*sum_held(ret_i) = mean_held(ret_i),
    i.e. exactly the intended equal-weight top-k portfolio return. Positions are held flat
    between Monday rebalances (forward-filled), matching the weekly-rebalance mandate."""
    lookback = int(params.get("lookback_days", 14))
    top_n = int(params.get("top_n", 3))
    drop_top1 = bool(params.get("drop_top1", False))

    n_universe = len(df_dict)
    if n_universe == 0 or top_n <= 0:
        return {sym: pd.Series(0.0, index=df.index) for sym, df in df_dict.items()}

    # point-in-time top-30 membership by trailing 30d quote volume, 90d listing gate.
    universe_tbl = point_in_time_universe(
        df_dict, top_n=TOP_N_UNIVERSE, trailing_days=TRAILING_VOL_DAYS,
        min_listed_days=MIN_LISTED_DAYS,
    )
    # shift membership by one bar: bar t's eligible set is the membership computed as of
    # date t-1 (point_in_time_universe's row for date d already only uses volume <= d, but
    # using row d itself for bar d would be same-bar information -- shift once more here).
    members_by_date = universe_tbl["members"].shift(1)

    mom = _momentum_ranks(df_dict, lookback)
    # shift momentum by one bar for the same reason: row d's pct_change uses close[d], so
    # the RANK usable at bar d must come from row d-1.
    mom_prior = mom.shift(1)

    full_index = mom_prior.index
    weekly_mask = _weekly_rebalance_mask(full_index)

    target_weight = pd.DataFrame(0.0, index=full_index, columns=list(df_dict.keys()))

    hold_n = top_n + 1 if drop_top1 else top_n
    scale = n_universe / top_n

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
        if drop_top1:
            picks = ranked.iloc[1:1 + top_n].index.tolist()
        else:
            picks = ranked.iloc[:top_n].index.tolist()
        if not picks:
            continue
        target_weight.loc[dt, picks] = scale

    # forward-fill target weight between weekly rebalance bars (position held flat all week).
    # Each Monday row of `target_weight` is a COMPLETE rebalance decision (including the 0.0
    # entries for names dropped from the portfolio) -- mask out non-rebalance rows entirely
    # (not just zero cells) so ffill correctly carries a drop-to-0 forward, not just the last
    # nonzero value ever seen per symbol. Bars before the first rebalance decision stay 0.
    held_weight = target_weight.where(weekly_mask, other=pd.NA)
    held_weight = held_weight.ffill().fillna(0.0).astype(float)

    out = {}
    for sym in df_dict:
        out[sym] = held_weight[sym].reindex(full_index).fillna(0.0)
    return out


# ---------------------------------------------------------------------------
# Config grid (declared BEFORE running, per house rule -- every entry here counts toward
# n_trials in the deflated Sharpe calc). IS-only tuning selects the best config by IS
# Sharpe; ONE walk-forward/OOS evaluation is then run on the chosen config.
# ---------------------------------------------------------------------------
PARAM_GRID = [
    {"lookback_days": 7, "top_n": 3},
    {"lookback_days": 7, "top_n": 5},
    {"lookback_days": 14, "top_n": 3},
    {"lookback_days": 14, "top_n": 5},
    {"lookback_days": 28, "top_n": 3},
    {"lookback_days": 28, "top_n": 5},
]
