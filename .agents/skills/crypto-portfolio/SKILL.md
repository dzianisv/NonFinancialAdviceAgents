---
name: crypto-portfolio
description: >
  List the investor's DeFi assets and positions across all chains — EVM wallets read from
  DeBank in the browser (PRIMARY), cross-checked by the Zerion API pipeline; TON via the
  swap.coffee API, Solana via Zerion, Hyperliquid valued via HL's own info API — and produce
  a normalized position table (CSV + per-wallet totals). Use when asked to "list my defi
  positions", "refresh the DeFi snapshot", "what's in my wallets", or to update the DeFi
  tab of the portfolio Google Sheet. Read-only data retrieval: no signing, no execution,
  no advice — for managing/rebalancing the book use `defi-portfolio-manager`; for realized
  historical yield use `defi-pnl`.
license: MIT
compatibility: >
  Needs a browser session (claude-in-chrome / chrome-use) for debank.com, plus network
  access to api.zerion.io (key required), backend.swap.coffee + tokens.swap.coffee
  (public, ~1 req/s), tonapi.io, api.hyperliquid.xyz, lite-api.jup.ag, api.mainnet-beta.solana.com
  and api.solend.fi (all public, no key). Python 3 with `requests` + `PyYAML` + `base58`
  (venv: /Users/engineer/.venv).
metadata:
  author: engineer
  version: "2.1"
---

# crypto-portfolio — list DeFi assets & positions

Read-only snapshot of the investor's whole DeFi book, one normalized row per position:
`Wallet, Protocol, Type, Pool, Asset, Balance, USD Value, Note`.

**Hierarchy (owner's decision, 2026-07): DeBank owns COMPLETENESS for EVM; per-venue APIs
own VALUATION where they exist; the Zerion pipeline is the automated cross-check.** Zerion
missed Hyperliquid (~$21k) and Lighter ($584, DeBank-only); DeBank's per-venue adapters have
the widest EVM coverage, so the browser read is the primary position list, not the verifier.

## Workflow

1. **DeBank browser read (PRIMARY for EVM).** For each EVM wallet in `wallets.yaml`, open
   `https://debank.com/profile/<address>` via claude-in-chrome / chrome-use (NEVER
   api.debank.com — keyed + rate-limited, explicitly forbidden). Wait for the portfolio to
   load; capture per-protocol positions: protocol, type, pool, assets, balances, USD. This
   is the primary EVM position list.
2. **API pipeline cross-check + machine-readable balances.**
   ```bash
   cd <backtest repo>
   set -a; source .env; set +a   # provides ZERION_API_KEY (mirrored in Bitwarden 'dev')
   /Users/engineer/.venv/bin/python3 .agents/skills/crypto-portfolio/scripts/defi_positions.py
   ```
   Outputs to `.cache/crypto-portfolio/` (overwritten each run): `defi_positions.csv` +
   `defi_positions_totals.json` (per-wallet totals pre-dust-filter, honest against raw
   sources). Reconcile per-wallet totals against DeBank: ≤3% is price drift, ignore. A
   protocol present on DeBank but absent from the API read is a COVERAGE GAP — flag it
   (standing example: Lighter on L3 ≈ $584). Wire a module (like `hyperliquid_positions.py`)
   or list it under Known gaps with its DeBank value.
3. **Non-EVM stays API-primary.** TON = swap.coffee (DeBank has no TON coverage). Solana =
   Zerion (DeBank Solana coverage is partial).
4. **Hyperliquid: DeBank discovers, HL API values.** HL positions are VALUED from the HL
   info API (perp marks, vault equity, $0 for no-oracle dust) even though DeBank lists
   them — DeBank misprices HL illiquid spot (a 1.3M MAX bag at spot mid) and cannot see
   perp-account/vault state. Same principle everywhere: DeBank = discovery/completeness,
   per-venue API = valuation.

Per-wallet modules are runnable standalone for debugging:
`zerion_positions.py <label> <evm|solana> <addr>` · `ton_positions.py <label> <addr>` ·
`hyperliquid_positions.py <label> <0xaddr>` (each prints JSON rows).

## Source map — who owns which truth

| Chain / venue | Completeness (position list) | Valuation / machine-readable | Why |
|---|---|---|---|
| EVM wallets + protocols | **DeBank browser read** (`debank.com/profile/<addr>`) | Zerion `GET /v1/wallets/{addr}/positions/` (Basic auth: key as username, `filter[positions]=no_filter`) — cross-check | DeBank's adapters cover venues Zerion doesn't (Lighter, HL listing) |
| Solana | Zerion (same endpoint; `filter[positions]` unsupported) | + Jupiter `lite-api.jup.ag/price/v2` for tokens Zerion returns unpriced (fragSOL, jlUSDS); + `solend_positions.py` (raw Solana RPC `getProgramAccounts` + `api.solend.fi/v1/reserves`) for Save/Solend obligation deposits, invisible to both Zerion and Solscan | DeBank Solana coverage is partial |
| TON | swap.coffee: `backend.swap.coffee/v1/ton/wallet/{addr}/balance` + `tokens.swap.coffee/api/v3/accounts/{addr}/jettons` | same (jettons carry `market_stats.price_usd`) | DeBank has no TON; TON DeFi is held as receipt jettons, so jettons ARE the position list |
| Hyperliquid | DeBank lists it (and the investor names it) | HL info API `POST api.hyperliquid.xyz/info` (`spotClearinghouseState`, `clearinghouseState`, `userVaultEquities`, marks from `metaAndAssetCtxs`) | Zerion can't see HL at all (~$21k); DeBank misprices its illiquid spot |
| AsterDEX | **invisible to BOTH DeBank and Zerion** (off-chain engine, no adapter; verified 2026-07-08) | Aster V3 futures API `GET fapi.asterdex.com/fapi/v3/{balance,positionRisk}`, EIP-712-signed | **DISABLED by owner's choice for now**: no `asterdex:` flag in `wallets.yaml`, no `ASTER_*` creds. To activate: mint the API wallet at asterdex.com/en/api-wallet, set `ASTER_USER`/`ASTER_SIGNER`/`ASTER_SIGNER_PRIVATE_KEY` in `.env` (key can TRADE — hot), flag the wallet `asterdex: true`. Module skips with a warning when creds absent |

Wallet registry: `.cache/crypto-portfolio/wallets.yaml` — labels match the DeFi tab of the
Portfolio Google Sheet (`1aunLbpNGo85WqrMHiIsy6nFUija4Lnjot-rIhE-pGU8`).

## Data-integrity rules for the API pipeline (each one earned by a real corruption)

1. **Zerion is eventually-consistent** — the same request seconds apart returns different
   position sets (rewards flicker). Every wallet is fetched twice and unioned by position id.
2. **Receipt-token double count** — with `no_filter` Zerion may return the protocol position
   AND its wallet receipt token (Maple deposit + syrupUSDC = same money, observed +$9.2k
   phantom). Known receipts (`RECEIPT_TOKENS` in `zerion_positions.py`) are dropped when the
   protocol position is present, relabeled to their protocol when it is not.
3. **swap.coffee jetton prices can be stale on thin receipt tokens** (USDT-SLP quoted +8% vs
   TONAPI). Every jetton price is cross-checked against TONAPI; >5% divergence → TONAPI price
   wins and the row's `Note` says so. Never silently trust one price graph for LP receipts.
4. **HL spot tokens without a perp oracle fall back to their own HL spot-pair mark**
   (flagged in Note as spot-priced, more slippage risk than perp-quoted). Stables at $1,
   perp-listed tokens off perp marks. Only a token with no price anywhere (neither perp nor
   spot) is valued $0. Fixed 2026-07-10: a real, moderate position (UPUMP, ~$644 on L1) was
   being silently zeroed by the old blanket "no perp oracle = $0" rule. The fallback itself
   has one sharp edge, caught by testing against live balances before shipping: HL's
   `spotMetaAndAssetCtxs` returns `ctxs` indexed by each pair's `index` field, NOT by its
   position in the `universe` array — the two diverge once index gaps appear, so naively
   zipping `ctxs[i]` to `universe[i]` by enumeration silently prices a token off an unrelated
   pair (first draft priced UPUMP at $46,800 and MAX at $3.9M off the wrong markets before
   this was caught). `hyperliquid_positions.py`'s `_spot_marks()` indexes by `pair["index"]`.
5. **Dust filter** $0.50 (per `wallets.yaml`), except wallets in `keep_all_dust` where real
   sub-$0.50 balances are kept visible on purpose (documents wallet state — e.g. how the
   Save/Solend obligation-account deposit below was first spotted). This does NOT cover
   scam/spam jettons — see rule 6.
6. **TON scam/airdrop-spam suppression (added 2026-07-10).** swap.coffee returns every
   jetton ever airdropped to a wallet, including obvious spam (fake "GRAM Unlock" claim
   tokens, "$BLUM", "TONRAGE") and fantasy-priced scam jettons ("DOFA" quoted at a made-up
   price no other source confirms). `ton_positions.py` now drops any jetton that is BOTH
   unverified (`verification != "WHITELISTED"`) AND has no real price from any source
   (swap.coffee price rejected as fantasy, no TONAPI cross-check) — unconditionally, even
   for `keep_all_dust` wallets, since these rows carry zero economic and zero diagnostic
   value. A real but unverified token that has a confirmed price (TONAPI or swap.coffee
   agreeing) still passes through normally.

## Updating the DeFi tab of the Google Sheet

Build the tab from the MERGED view: DeBank-discovered EVM positions valued per the rules
above (HL from the HL API, everything else reconciled against the pipeline CSV) + API rows
for TON/Solana. Use `gws` (Sheets scope authorized), preserving the layout — title row 1
`DeFi Snapshot — <date> (sources)`, header row 2, position rows grouped by wallet, one
`<label> TOTAL (<address>)` row with a `=SUM()` formula per wallet block, and a GRAND TOTAL
row. Re-read the tab immediately before writing (row numbers shift); clear leftover old rows
after an update that shortens the table. **Mirror the GRAND TOTAL into the stable cell
`DeFi!I1`** (value in I1; a `GRAND TOTAL:` label in H1 helps) — `Totals!C7/C11` reference
`DeFi!I1`, so a snapshot that moves the grand-total row must not break Totals.

## Pricing infra (Apps Script price feed)

The Google Sheet's live crypto prices come from `quoteCoinmarketcap()`, a custom function in
a **separate** GitHub repo `dzianisv/GoogleAppScripts` (`GoogleScript/Crypto.gs`) — that repo
is the ONLY source of truth for this code, not this skill's Python pipeline. (A flat, hand-
copied `apps-script-source.txt` used to live in this repo as a second mirror; it drifted out
of sync with the real repo more than once, so it was retired 2026-07-09 — clone
`GoogleAppScripts` directly instead of trusting a local snapshot.)

- **Past "CoinMarketCap-throttle" bug reports (see memory `portfolio-sheet-structure.md`)
  were mislabeled.** Despite the function's name, it was actually calling CoinGecko's
  anonymous public API (~5-15 req/min, shared across all Apps Script users on Google's IPs).
  A 429 throttle response body ("Throttled", plaintext) was fed straight into `JSON.parse()`
  with no status check, crashing and cascading into `#VALUE!`/$0 on `Crypto!F89` and
  `Totals!C6/C7/C11`. Root-caused 2026-07-09 — not a sheet-formula bug, all rows already used
  the correct VLOOKUP pattern. Don't assume the old label was accurate.
- **Fixed (2026-07-09):** rewritten to hit CMC's own internal, no-API-key website endpoint —
  `GET api.coinmarketcap.com/data-api/v3/cryptocurrency/quote/latest?id=<ids>&convertId=2781`
  — batching ALL tracked symbols into one request per cache miss (not one call per cell), with
  retry+backoff and a persisted last-known-good price so a transient failure degrades to
  stale-but-real instead of N/A/#VALUE!. No auth/cookies/key needed; just send a non-empty
  `User-Agent` header.
- **ASTER was mismapped** to CoinGecko's "astar" (Astar — an unrelated chain, not the Aster
  DEX/BSC token the sheet tracks). Fixed to CMC id 36341. Don't revert this to Astar.
- **TON/Toncoin gap, resolved — owner decision made 2026-07-09.** CMC's old Toncoin id
  (11419) now resolves to symbol "GRAM" / "Gram (prev. Toncoin)"; owner decided to accept it
  as the same asset continued under CMC's new label. TON now maps to id 11419 in the id map.

## Known gaps (state them, don't hide them)

- **Lighter** (zkSync perp DEX): no public read API wired up — its deposits (~$595 on L3,
  negligible <$0.01 dust on B3, 2026-07-10) are visible ONLY on DeBank; the browser read
  (step 1) is currently the only way to read it. Lighter does have a public read endpoint
  (`GET mainnet.zklighter.elliot.ai/api/v1/account?by=l1_address&value=<addr>`) but its
  cross-margin accounting (separate `available_balance`/`collateral`/per-position
  `cross_initial_margin_requirement` fields whose exact relationship to "how much is really
  the investor's money" isn't fully pinned down) risks a wrong auto-computed total worse than
  a manual, DeBank-verified carry-forward — don't wire it up until that's resolved.
- swap.coffee staking balances endpoint needs a TON-proof header (wallet signature) — liquid
  staking read that way is out; staked TON appears only if held as a receipt jetton.
- Perp rows report **margin** as the position value (matches the sheet convention), with
  unrealized P&L in the Asset label, not added to value. Aster cross-margined positions
  value at $0 on the position row (margin already counted in the Futures Account row).
- **Neither DeBank nor Zerion can catch AsterDEX** — no adapter on either side, module
  disabled (see Source map). The only signal is the investor naming the venue: when they
  do, wire its own API module (Aster, HL) — never trust "DeBank shows everything".
- **FIVA yield-token (YT) positions may carry separate unclaimed yield, invisible to this
  pipeline.** A matured YT jetton (e.g. T1's "YT USDT-SLP (01Sep2025)") is correctly priced
  $0 as a token — FIVA's own docs confirm YT value is genuinely zero at/after maturity — but
  FIVA's protocol separately lets holders manually claim accrued pre-maturity yield via the
  FIVA dashboard (`app.thefiva.com`), and that claimable balance is NOT exposed by any public
  REST endpoint found so far (`api2.thefiva.com/{user,users,rewards,claimable,account}/<addr>`
  all 404). If a YT position matured without the owner manually claiming first, there could be
  real unclaimed value this pipeline cannot see. Requires a wallet-connected dashboard check,
  not resolvable via curl. Flagged, not resolved, 2026-07-10.
- **TRUMP token has no reliable price feed** — CoinMarketCap and GOOGLEFINANCE both fail or
  are unreliable for this symbol; manually verify against multiple sources before trusting any
  single quote (this is why the sheet now hardcodes a confirmed price rather than a live
  formula for it).

## Resolved gaps

- **Save/Solend (Solana lending)** — was invisible to both Zerion and Solscan's summary views
  (deposits live in a program-owned "Obligation" account, not a wallet token balance).
  Automated 2026-07-10 via `solend_positions.py`: `getProgramAccounts` memcmp-filtered on the
  Obligation account's `owner` field (offset 42) finds every obligation for a wallet with no
  address to derive up front; byte layout transcribed from `solendprotocol/solend-sdk`
  (`src/state/obligation.ts`); value computed live from `api.solend.fi/v1/reserves`'
  `cTokenExchangeRate` + oracle `marketPrice`, never from the obligation's own cached
  (frequently-stale) `marketValue` field. Wired into `defi_positions.py` for every `solana`
  wallet unconditionally — empty obligations just decode to zero rows, no per-wallet flag
  needed. Confirmed materially correct: $16,648.23 live vs. $16,647.74 prior manual figure
  (the ~$0.50 gap is ~2 weeks of accrued interest, not error).
