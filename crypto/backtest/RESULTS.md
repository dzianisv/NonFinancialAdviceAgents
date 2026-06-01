# Agent-in-the-loop backtest — results

The test the deeper mission demanded: drop the **agent** into 2024 with only the data it would have
had, let it manage a $100k book quarter by quarter, and compare to deterministic baselines.

## Method
- **Point-in-time, no look-ahead.** `fetch_history.py` builds a daily APY/TVL panel; a pool is only
  investable once it has history. `simulate.py dump` writes each quarter's `world(t)` (the pools that
  existed then + their as-of APY/30d-APY) to `agent_worlds.json`.
- **The agent decides.** For each of the 8 quarters, an independent LLM agent saw ONLY that quarter's
  `world(t)` (no future data) and returned target weights under a moderate, no-shitty-assets brief.
  Decisions in `agent_decisions.json`. Carried forward between quarters; the simulator rebalances
  monthly with a 5bps turnover cost.
- **Price layer** (`fetch_prices.py`): directional assets (ETH via stETH) earn **price return + staking
  yield**, not just yield — otherwise the directional sleeve's upside/downside is invisible.
- Window **2024-07 → 2026-05**. Realized = the quoted APY earned each month. Universe: Aave/Compound/
  Steakhouse USDC (+USDT, sUSDS) stables, stETH (directional), **sUSDe (the synthetic trap, on the menu
  on purpose)**.

## Results

| Strategy | Return/yr | Max DD | Turnover | Note |
|---|---|---|---|---|
| do_nothing | 0.00% | 0% | 0× | idle cash |
| all_aave | 4.58% | 0% | 1× | one blue-chip lender |
| **chase_max** | **7.70%** | 0% | **21×** | **held sUSDe**; churned every month |
| equal_clean (rules) | **5.02%** | 0% | 1.4× | all-stable, never synthetic |
| **AGENT** (moderate, LLM) | **2.44%** | **−18.5%** | 4.2× | avoided sUSDe; ~30% stETH rode ETH −33% |

Window asset moves: **ETH −33%, SOL −43%, BTC +24%.** (chart: `agent_backtest.png`)

## Honest conclusions

1. **Risk discipline worked.** Every one of the 8 quarterly agents *rejected sUSDe* — even when it
   flashed the highest APY on the menu (9–12%). `chase_max`, the naive yield-maximizer, held it.
2. **But moderate LOST to conservative in this window.** The agent earned 2.44% with a −18.5% drawdown
   vs the all-stable `equal_clean` at 5.02% with ~0 drawdown. The cause is the moderate mandate itself:
   ~30% directional (stETH), and ETH fell 33% over 2024–26. The directional sleeve is a bet on crypto
   going up; it didn't.
3. **`chase_max`'s 7.70% is a mirage.** It "won" only by holding the synthetic dollar (tail risk that
   never triggered in-window) and churning 21× — not a strategy, a coin flip that landed.
4. **The lesson:** "moderate" = a crypto-direction bet that wins in bulls and loses in bears. For
   *this* window the conservative, all-clean-stable book (~5%, no drawdown) was the right risk-adjusted
   call — which is what the earlier conservative work concluded. The agent's *discipline* (no synthetic,
   diversified, capped) was sound; its *mandate* (take directional beta) was the wrong bet for 2024–26.

## Caveats (so the numbers aren't over-trusted)
- **Stables are modeled flat at $1** (yield only) → the all-stable strategies show an artificial 0%
  drawdown; real smart-contract/depeg tail risk (which the rules exist to avoid) is NOT captured. So
  `chase_max`'s sUSDe looks free here only because it didn't depeg in-window.
- **One window, small universe.** A single 2024–26 path; BTC (+24%) wasn't in the eligible universe, so
  the directional sleeve was all-ETH. A bull window would flip conclusion #2.
- APY = DefiLlama's quoted forward rate as the earned rate — a standard but imperfect proxy.

## Reproduce
```bash
py=/Users/engineer/.venv/bin/python3
$py crypto/backtest/fetch_history.py     # panel (data/*.json)
$py crypto/backtest/fetch_prices.py      # price layer (data/prices.json)
$py crypto/backtest/simulate.py dump     # agent_worlds.json
# spawn one agent per quarter on each world(t) → agent_decisions.json
$py crypto/backtest/simulate.py agent crypto/backtest/agent_decisions.json
```
