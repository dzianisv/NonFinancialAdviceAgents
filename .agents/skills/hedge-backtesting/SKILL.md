---
name: hedge-backtesting
description: Translates a strategy's mechanical rules (from hedge-strategy-generation or pasted directly) into an executable Python backtest against real yfinance data, runs it, and reports ONLY numbers that came out of that run's stdout — CAGR, Sharpe, max drawdown, win rate, trade count, exposure, buy&hold comparison, an in-sample/out-of-sample split, and a regime breakdown. Use this whenever the user wants a strategy backtested, asks "test this strategy", "run the numbers on X", or hands you strategy rules to validate. Never fabricates a metric — if data or execution is unavailable it outputs INSUFFICIENT, not an estimate. Second stage of a 3-skill pipeline (hedge-strategy-generation -> hedge-backtesting -> hedge-risk-reward); for a full walk-forward + deflated-Sharpe + stress verdict it hands off to strategy-discovery-backtest. No leverage. Educational, not financial advice.
license: MIT
compatibility: opencode
metadata:
  audience: systematic-traders
  domain: quantitative-finance
  role: backtest-engineer
  pipeline: "2 of 3 — hedge-strategy-generation -> hedge-backtesting -> hedge-risk-reward"
---

# Hedge Backtesting

Turns mechanical strategy rules into a real, executed backtest. **No number in this skill's output may be
estimated, guessed, or recalled from memory or training data — every metric must be traceable to the stdout
of a script that actually ran against actually-downloaded data.** If the data can't be pulled or the script
can't run, the honest output is `INSUFFICIENT`, never a plausible-looking guess.

This mirrors the project's harder-edged law: `strategy-discovery-backtest` is the final gate before capital
moves; this skill is the fast, iterative loop that gets a strategy into good enough shape to be worth
sending there. **This skill's author-agent must never also be the strategy's grader** — if the strategy
came out of `hedge-strategy-generation` in the same session, that's fine (generation ≠ grading), but the
PASS/FAIL verdict on whether to trust the edge is `strategy-discovery-backtest`'s call, not this skill's.

## Input
Strategy rules — ideally the structured output of `hedge-strategy-generation` (indicators, entry/exit,
stops/targets, sizing), or pasted rules from the user. If any rule is not mechanically codeable (requires
discretion), stop and ask for a codeable rewrite before writing any script — do not silently interpret an
ambiguous rule your own way, that's a hidden assumption the backtest result can't be trusted against.

## Process

### 1. Translate rules -> Python script
Write to `.cache/hedge-backtesting/<slug>/backtest_<slug>.py`, where `<slug>` is a short kebab-case name for
the strategy (e.g. `sma-cross-spy`). Use the venv interpreter: `/Users/engineer/.venv/bin/python3`
(`yfinance`, `pandas`, `numpy` available — verify with `python3 -c "import yfinance, pandas, numpy"` first
if unsure).

Script conventions (match `backtests/backtest.py` and `backtests/momentum_backtest.py` in this repo):
- `yf.Ticker(symbol).history(...)` or `yf.download(...)`, `auto_adjust=True`.
- **Daily bars, 5-10 years** for stocks/forex; **max available** for crypto (most majors only have
  reliable daily data back to ~2015-2018 on yfinance — say so if the asset's history is shorter).
- Signal on bar close, fill on next bar open — no look-ahead. If the rules say otherwise, implement exactly
  as specified but flag the look-ahead risk in the output.
- **Transaction costs are mandatory, never optional:**
  | Asset class | Default cost | Note |
  |---|---|---|
  | Stocks / ETFs | 10 bps/side | matches typical retail/Robinhood-style spread+fee; use this unless the user specifies a different venue |
  | Crypto | 20 bps/side | plus a stated slippage note — crypto spreads widen sharply in stress; if the strategy trades illiquid alts, widen this |
  | Forex (`yfinance` `EURUSD=X` style) | 5-10 bps/side | wider on minor pairs; this repo has no dedicated forex feed, treat coverage/liquidity as unverified |

  If the resulting strategy's edge doesn't survive **double** these costs, that's a finding to report, not
  a reason to quietly lower the cost assumption (matches `strategy-discovery-backtest`'s stress stage).
- **Position sizing from the stated risk-per-trade**: `shares = (capital * risk_pct) / (entry_price - stop_price)`,
  capped so no position exceeds 100% of capital (no leverage, house rule). Implement exactly as
  `hedge-strategy-generation` specified sizing, or ask if sizing wasn't specified.

### 2. Execute it
Run the script with the venv python, capture **all** stdout to
`.cache/hedge-backtesting/<slug>/run.log`. This log is the source of truth — every number quoted in the
final report must appear in this file. Do not paraphrase or round in a way that loses traceability; copy
numbers out of the log verbatim.

```bash
/Users/engineer/.venv/bin/python3 .cache/hedge-backtesting/<slug>/backtest_<slug>.py 2>&1 | tee .cache/hedge-backtesting/<slug>/run.log
```

### 3. Metrics table (every cell traceable to run.log)
| Metric | Value | Source |
|---|---|---|
| CAGR | | strategy vs buy&hold, same period/asset |
| Sharpe (rf=0) | | state explicitly that rf=0 was used unless a real risk-free series was applied |
| Max drawdown | | |
| Win rate | | % of trades closed positive |
| Trade count | | total round-trips |
| Exposure | | % of time in a position |
| Buy & hold CAGR/Sharpe/MaxDD | | same asset, same period, for comparison |

### 4. Mandatory in-sample / out-of-sample split
Split the data chronologically — fit/tune any parameters on the **first 70%** (in-sample), report the
**last 30%** (out-of-sample) as a fully separate metrics block. Never tune on the OOS slice. If the script
only reports one blended number across the whole period, label the whole result **`IS-ONLY, UNVALIDATED`**
in the output — do not present a blended or IS-only number as if it were OOS.

### 5. Regime breakdown
From the actual equity curve (not narrative): best year, worst year, performance in known stress windows
that overlap the data (2018 crypto winter, 2020-03 COVID crash, 2022 rate-hike bear, 2025 crypto draw —
whichever apply to the asset and period), and a one-line diagnosis of what condition breaks the strategy
(e.g. "flat/choppy price action whipsaws the SMA cross — N losing trades in Q_ 20__ with no net trend").

### 6. Verdict
- **PASS** — OOS Sharpe or OOS return beats buy&hold for the same asset/period after costs, OR the strategy
  adds genuine diversification (e.g. low/negative correlation to buy&hold with a comparable Sharpe) — state
  which.
- **FAIL** — OOS edge doesn't clear buy&hold and doesn't diversify.
- **INSUFFICIENT** — yfinance download failed, returned empty/partial data, or usable history is under 3
  years. State exactly what failed (ticker, error, date range actually returned) — never substitute a
  plausible-sounding number for missing data.

This skill's PASS is a **local, fast-loop signal only** — it is not the project's final word. For a
strategy that will actually size real capital, chain to `strategy-discovery-backtest` for the full
walk-forward, deflated-Sharpe (multiple-testing haircut), and stress-test (doubled costs, delayed fills,
crisis windows) treatment before any order is placed.

## Anti-fabrication guardrails (read before writing the report)
- If the script errors, hangs, or is skipped for any reason -> the output is `INSUFFICIENT`, not a filled-in
  metrics table with placeholder or remembered-looking numbers.
- If yfinance returns fewer than 3 years of usable daily bars for the asset -> `INSUFFICIENT`, state exactly
  how many years were available.
- Every number in the final report must be `grep`-able in that run's `run.log`. If you cannot point to the
  line, do not print the number.
- Do not average, extrapolate, or "round to what it's probably close to." If the script didn't compute it,
  it doesn't go in the table.

## Artifacts
- `.cache/hedge-backtesting/<slug>/backtest_<slug>.py` — the script.
- `.cache/hedge-backtesting/<slug>/run.log` — full stdout, the source of truth for every number reported.
- Never write scratch scripts or logs into this skill's own directory — artifacts live under `.cache/` only.

## Hand-off
- Input from `hedge-strategy-generation` (or pasted rules).
- Output feeds `hedge-risk-reward` (needs the trade list / equity curve produced here) and, for anything
  approaching real capital, `strategy-discovery-backtest` for the binding PASS/FAIL gate (see `GOAL.md`
  law #0 — no untested idea reaches a live order).

---
Educational, not financial advice. No leverage.
