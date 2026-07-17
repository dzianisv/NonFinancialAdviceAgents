---
name: hedge-risk-reward
description: Analyzes a strategy's REAL risk/reward profile from its hedge-backtesting artifacts (trade list, equity curve) — actual risk per trade vs stated, realized reward:risk / expectancy, drawdown depth/duration/clustering/recovery — then proposes concrete, re-backtestable improvements to reduce risk and separately to increase returns without increasing risk, each tagged with its mechanism, never a fabricated expected number. Use this whenever the user wants a strategy's risk profile analyzed, asks "how risky is this strategy really", "how do I improve this without adding risk", or wants drawdown/expectancy analysis on a backtested strategy. Refuses to analyze from vibes — if no hedge-backtesting artifacts exist, it demands that skill be run first. Third and final analysis stage of a 3-skill pipeline (hedge-strategy-generation -> hedge-backtesting -> hedge-risk-reward). No leverage. Educational, not financial advice.
license: MIT
compatibility: opencode
metadata:
  audience: systematic-traders
  domain: quantitative-finance
  role: risk-analyst
  pipeline: "3 of 3 — hedge-strategy-generation -> hedge-backtesting -> hedge-risk-reward"
---

# Hedge Risk/Reward Analysis

Takes a strategy that has already been through `hedge-backtesting` and answers: **what is this strategy's
real risk/reward shape, and how could it be improved without guessing?** This skill computes from the
actual trade list and equity curve produced by the backtest — it does not narrate, estimate, or vibe-check
a strategy's risk profile from the rules alone.

## Hard gate: no artifacts, no analysis
If `.cache/hedge-backtesting/<slug>/` doesn't exist, or contains no `run.log` / no trade-level data to
compute from, **stop and say so** — instruct the user to run `hedge-backtesting` first. Do not produce a
plausible-sounding risk breakdown from the strategy's stated rules alone; "the stop is 2x ATR so risk per
trade is probably around X%" is exactly the kind of fabricated number this project bans. If the backtest
script didn't print a trade list, that is itself a finding — flag it back to `hedge-backtesting` as missing
the granularity this skill needs, rather than approximating around the gap.

## Input
A strategy + its `hedge-backtesting` artifacts: `.cache/hedge-backtesting/<slug>/backtest_<slug>.py`,
`run.log`, and whatever trade-list/equity-curve data the script emitted (stdout table, CSV, or an in-memory
structure the script can be re-run to dump — if the original script didn't save a trade list, re-run it
with a small addition that does, rather than reconstructing one from memory).

## Process

### 1. Risk-per-trade: actual vs stated
From the trade list, compute the real observed loss-per-losing-trade as a % of capital at entry, and
compare against the risk-per-trade the strategy stated (e.g. "1% per trade"). Sizing bugs, gap-through-stop
slippage, and multi-position overlap all cause these to diverge — report the actual number and the gap, not
just the stated target.

### 2. Realized reward:risk and expectancy
From the trade list: average win size, average loss size, win rate, and
`expectancy = win_rate * avg_win - (1 - win_rate) * avg_loss` (in R-multiples and in $ terms). This is the
single most important number for "is this strategy's asymmetry real" — report it plainly, don't bury it.

### 3. Drawdown pattern analysis (from the real equity curve)
- **Depth** — max drawdown, and the distribution of drawdown depths (not just the single worst one).
- **Duration** — time-in-drawdown for the worst few episodes, and typical/median.
- **Clustering** — do drawdowns bunch in specific periods/regimes (matches the regime breakdown from
  `hedge-backtesting`) or are they scattered independently through the equity curve?
- **Recovery time** — bars/days from trough back to prior equity high, for the worst episodes.

All four computed directly from the equity curve array in the backtest artifacts — if the equity curve
wasn't saved, re-run the backtest script with that addition rather than estimating from the summary metrics.

## Output: risk profile table
| Dimension | Value | Source |
|---|---|---|
| Stated risk/trade | | strategy spec |
| Actual risk/trade (realized) | | trade list |
| Win rate | | trade list |
| Avg win / avg loss (R) | | trade list |
| Expectancy | | computed |
| Max drawdown | | equity curve |
| Longest drawdown duration | | equity curve |
| Drawdown clustering | | equity curve + regime overlap |
| Worst-case recovery time | | equity curve |

## Improvements to REDUCE risk (3 required, each re-backtestable)
Pick 3 concrete, mechanically-specifiable changes from candidates like: vol-targeted position sizing (scale
size inversely to trailing realized vol), a regime filter (only trade when a higher-timeframe trend/vol
condition is met), a correlation cap (reduce size when the position is highly correlated to other book
exposure), a time-stop (exit after N bars regardless of P&L if the thesis hasn't played out), or tighter
structural stops. For each: name the exact mechanism, state which risk-profile dimension above it should
improve and why, and instruct explicitly: **"re-run `hedge-backtesting` with this change applied and
compare the metrics table — do not assert this is an improvement until the re-test confirms it."** Never
state an expected numeric delta (e.g. "should cut max DD by ~5pp") — that is a fabricated number with no
backtest behind it yet.

## Ways to INCREASE returns WITHOUT increasing risk (2 required, same re-verify rule)
Pick 2 from candidates like: reduce costs/turnover (fewer round-trips, wider filters, or a cheaper venue),
deploy idle/flat-period cash into T-bills or a money-market sweep instead of sitting in 0%-yield cash,
diversify into an uncorrelated instrument at the same total risk budget (frees return without raising the
book's risk), or improve fill assumptions only if they're currently unrealistically conservative (never
loosen a cost assumption to manufacture an improvement — that's reward-hacking the same gate
`strategy-discovery-backtest` explicitly bans). Same rule: name the mechanism, name what re-test would prove
it, no fabricated expected delta.

## Output format
```
<risk-reward-analysis slug="...">
  <risk_profile>...table above...</risk_profile>
  <reduce_risk>
    <item rank="1" mechanism="vol-targeted sizing | regime filter | correlation cap | time-stop | ...">
      why: ... / verify: re-run hedge-backtesting with this change, compare metrics table
    </item>
    <!-- 3 items -->
  </reduce_risk>
  <increase_return_same_risk>
    <item rank="1" mechanism="reduce turnover | idle-cash yield | uncorrelated diversification | ...">
      why: ... / verify: re-run hedge-backtesting with this change, compare metrics table
    </item>
    <!-- 2 items -->
  </increase_return_same_risk>
</risk-reward-analysis>
```

## Hand-off
- Input: a strategy + its `hedge-backtesting` artifacts (`.cache/hedge-backtesting/<slug>/`).
- Any proposed change must be **re-run through `hedge-backtesting`** before it's believed — this skill
  never grades its own proposed improvements, it only proposes and specifies the verification.
- For a strategy heading toward real capital, the improved version still needs to clear
  `strategy-discovery-backtest`'s full walk-forward/deflation/stress gate — improving risk/reward here does
  not substitute for that gate.

---
Educational, not financial advice. No leverage.
