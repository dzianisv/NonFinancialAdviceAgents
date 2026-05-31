# crypto/

Managing a live ~$177k multi-chain crypto book — a conservative, capital-preservation-first crypto
treasury: real yield on principal, idiosyncratic crypto risks (smart-contract, depeg, bridge, custody,
liquidity) capped, directional beta kept small. (Separate from the tradfi book in [`../GOAL.md`](../GOAL.md).)

| File | What it is |
|------|------------|
| [GOAL.md](GOAL.md) | **The goal (read first):** the optimal-allocation problem stated formally — objective, constraints, success criteria, required investor inputs, roadmap |
| [STRATEGY.md](STRATEGY.md) | **The strategy:** policy defaults, target allocation + venue menu, the 5-job control loop, cash-deployment waterfall, transition plan, crash validation |
| [portfolio.py](portfolio.py) | Live tracker — pulls APY + collateral from DefiLlama + Morpho, reports value/yield/idle/concentration + rebalance model |
| [usdt.md](usdt.md) | Earlier USDT deposit notes |
| report/ | Generated output: `portfolio.md` + `img/alloc.png`, `img/uplift.png` |

## Run the tracker

```bash
/Users/engineer/.venv/bin/python3 crypto/portfolio.py
```

Holdings (USD values) are a manual snapshot in `POSITIONS` inside `portfolio.py` — edit them as
balances change. **APYs and collateral are pulled live** from `yields.llama.fi/pools` and
`api.morpho.org/graphql` each run, so the blended yield and idle-capital report are always real.
Each position resolves its rate by Morpho vault symbol/address, DefiLlama poolId, or manual
fallback (shown as `[morpho:sym]` / `[defillama]` / `[manual]` in the output).

## Current headline (2026-05-30)

- **$177k total, 69% stables, blended yield only ~1.7%** because ~$104k of stables sit below 3%.
- **$37.8k Seamless USDC @ Morpho earns 0.00% live** (21% of the book, idle — confirmed via API).
- **Model:** reallocate ~$113k of lazy/exit-able stables to the ~4.5% clean frontier →
  **~$7.1k/yr (3.98%), +$4.1k/yr, gas-only, lower risk.**

See [GOAL.md](GOAL.md) for the goal and roadmap. Read-only research tooling — never custody/signing.
