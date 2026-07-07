---
name: crypto-portfolio
description: >
  List the investor's DeFi assets and positions across all chains — EVM + Solana via the
  Zerion API, TON via the swap.coffee API, Hyperliquid via HL's own info API — and produce
  a normalized position table (CSV + per-wallet totals). Use when asked to "list my defi
  positions", "refresh the DeFi snapshot", "what's in my wallets", or to update the DeFi
  tab of the portfolio Google Sheet. Read-only data retrieval: no signing, no execution,
  no advice — for managing/rebalancing the book use `defi-portfolio-manager`; for realized
  historical yield use `defi-pnl`.
license: MIT
compatibility: >
  Needs network access to api.zerion.io (key required), backend.swap.coffee +
  tokens.swap.coffee (public, ~1 req/s), tonapi.io, api.hyperliquid.xyz and
  lite-api.jup.ag (all public). Python 3 with `requests` (venv: /Users/engineer/.venv).
metadata:
  author: engineer
  version: "1.0"
---

# crypto-portfolio — list DeFi assets & positions

Read-only snapshot of the investor's whole DeFi book, one normalized row per position:
`Wallet, Protocol, Type, Pool, Asset, Balance, USD Value, Note`.

## Run

```bash
cd <backtest repo>
set -a; source .env; set +a   # provides ZERION_API_KEY (mirrored in Bitwarden 'dev')
/Users/engineer/.venv/bin/python3 .agents/skills/crypto-portfolio/scripts/defi_positions.py
```

Outputs to `.cache/crypto-portfolio/` (gitignored): `defi_positions.csv` +
`defi_positions_totals.json` (per-wallet totals computed pre-dust-filter, so they are
honest against the raw sources). Wallet registry: `scripts/wallets.json` — labels match
the DeFi tab of the Porfolio Google Sheet (`1aunLbpNGo85WqrMHiIsy6nFUija4Lnjot-rIhE-pGU8`).

Per-wallet modules are runnable standalone for debugging:
`zerion_positions.py <label> <evm|solana> <addr>` · `ton_positions.py <label> <addr>` ·
`hyperliquid_positions.py <label> <0xaddr>` (each prints JSON rows).

## Source map — which API owns which truth

| Chain / venue | Source | Why |
|---|---|---|
| EVM wallets + protocol positions | Zerion `GET /v1/wallets/{addr}/positions/` (Basic auth: key as username, `filter[positions]=no_filter`) | one call covers all EVM chains incl. LP/lending/rewards |
| Solana | Zerion (same endpoint; `filter[positions]` unsupported) + Jupiter `lite-api.jup.ag/price/v2` for tokens Zerion returns unpriced (fragSOL, jlUSDS) | |
| TON | swap.coffee: `backend.swap.coffee/v1/ton/wallet/{addr}/balance` (native) + `tokens.swap.coffee/api/v3/accounts/{addr}/jettons` (jettons incl. DeFi receipt tokens with `market_stats.price_usd`) | TON DeFi (Storm SLP, DeDust/Coffee LP, YT) is held as receipt jettons; no per-user "all yield positions" endpoint exists, so jettons ARE the position list |
| Hyperliquid | HL info API `POST api.hyperliquid.xyz/info` (`spotClearinghouseState`, `clearinghouseState`, `userVaultEquities`, marks from `metaAndAssetCtxs`) | **Zerion cannot see Hyperliquid at all** (~$21k of book, 2026-07) |

## Data-integrity rules (each one earned by a real corruption)

1. **Zerion is eventually-consistent** — the same request seconds apart returns different
   position sets (rewards flicker). Every wallet is fetched twice and unioned by position id.
2. **Receipt-token double count** — with `no_filter` Zerion may return the protocol position
   AND its wallet receipt token (Maple deposit + syrupUSDC = same money, observed +$9.2k
   phantom). Known receipts (`RECEIPT_TOKENS` in `zerion_positions.py`) are dropped when the
   protocol position is present, relabeled to their protocol when it is not.
3. **swap.coffee jetton prices can be stale on thin receipt tokens** (USDT-SLP quoted +8% vs
   TONAPI). Every jetton price is cross-checked against TONAPI; >5% divergence → TONAPI price
   wins and the row's `Note` says so. Never silently trust one price graph for LP receipts.
4. **HL spot tokens without a perp oracle are dust valued $0** (flagged in Note) — HL's thin
   spot mid quotes unrealizable values (a 1.3M MAX bag ≈ "$8.65M"). Stables at $1, everything
   else off perp marks.
5. **Dust filter** $0.50 (per `wallets.json`), except wallets in `keep_all_dust` where scam/
   zero-value jettons are kept visible on purpose (they document the wallet's state).

## Updating the DeFi tab of the Google Sheet

Use `gws` (Sheets scope authorized): write the CSV rows into the `DeFi` tab preserving its
layout — title row 1 `DeFi Snapshot — <date> (sources)`, header row 2, position rows grouped
by wallet, one `<label> TOTAL (<address>)` row with a `=SUM()` formula per wallet block, and
a GRAND TOTAL row. Re-read the tab immediately before writing (row numbers shift). Clear
leftover old rows after an update that shortens the table.

## Known gaps (state them, don't hide them)

- **Lighter** (zkSync perp DEX): no public read API wired up — its deposits (~$600, 2026-07)
  are invisible here; note it when reporting totals.
- swap.coffee staking balances endpoint needs a TON-proof header (wallet signature) — liquid
  staking read that way is out; staked TON appears only if held as a receipt jetton.
- Perp rows report **margin** as the position value (matches the sheet convention), with
  unrealized P&L in the Asset label, not added to value.
