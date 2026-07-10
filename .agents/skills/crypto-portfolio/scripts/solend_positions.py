#!/usr/bin/env python3
"""Save (formerly Solend) obligation positions via raw Solana RPC + Save's public API.

Why this module exists: Solscan and Zerion do NOT surface Solend/Save deposits in a
clean summary. When a wallet deposits into Solend, its cTokens move OUT of the
wallet's own token account and into the protocol's pooled collateral-supply vault,
recorded only inside an on-chain "Obligation" account owned by the Solend program.
A naive wallet-balance scan sees nothing. Confirmed via manual audit 2026-07-10:
SOL.L1 held a live ~$16.6k USDC deposit invisible to both Solscan's token list and
Zerion's positions endpoint. This module reads it directly, no browser/manual step.

Method (all public, no API key):
  1. getProgramAccounts on the Solend/Save mainnet program, filtered by memcmp on
     the Obligation account's `owner` field, to find every obligation belonging to
     a wallet without needing to know/derive the obligation address up front.
  2. Decode each Obligation account's raw bytes per ObligationLayout (byte-for-byte
     offsets below) to pull out deposits (reserve pubkey + raw collateral amount)
     and borrows (reserve pubkey + raw borrowed-amount-wads).
  3. A wallet can hold more than one obligation (e.g. one on a long-abandoned
     market, one on the live "main" market) -- no special-casing is needed for
     this: empty obligations simply decode to depositsLen == borrowsLen == 0 and
     contribute no rows.
  4. For every reserve referenced by a non-empty deposit/borrow, call Save's public
     REST API (api.solend.fi/v1/reserves) to get the reserve's live cTokenExchangeRate
     and oracle-derived liquidity.marketPrice, and compute:
       underlying_amount = (raw_amount / 10**mintDecimals) * cTokenExchangeRate
       usd_value         = underlying_amount * marketPrice
     Both cTokenExchangeRate and marketPrice come from the SAME api.solend.fi response
     as the reserve's mintDecimals, so there is no decimals/precision mismatch risk.

Layout source (byte offsets below are transcribed 1:1, not guessed): Solend's own
open-source SDK, https://github.com/solendprotocol/solend-sdk
  - Program ID:      src/classes/constants.ts -> SOLEND_PRODUCTION_PROGRAM_ID
  - ObligationLayout: src/state/obligation.ts  -> ObligationLayout / ObligationCollateralLayout
                      / ObligationLiquidityLayout
  - LastUpdateLayout: src/state/lastUpdate.ts  (u64 slot + u8 stale = 9 bytes)
No SDK/package was installed or imported; the layout is re-implemented here in
plain Python (struct byte-slicing) so this module has zero new dependencies beyond
`requests` and `base58`.

Obligation byte layout (little-endian), span = 1300 bytes total:
  offset   0,   1B  version
  offset   1,   9B  lastUpdate (u64 slot @0, u8 stale @8)
  offset  10,  32B  lendingMarket (pubkey)
  offset  42,  32B  owner (pubkey)                 <- memcmp filter target
  offset  74,  16B  depositedValue   (u128, WAD 1e18)
  offset  90,  16B  borrowedValue    (u128, WAD 1e18)
  offset 106,  16B  allowedBorrowValue (u128, WAD 1e18)
  offset 122,  16B  unhealthyBorrowValue (u128, WAD 1e18)
  offset 138,  64B  _padding
  offset 202,   1B  depositsLen
  offset 203,   1B  borrowsLen
  offset 204, 1096B dataFlat: depositsLen * ObligationCollateral(88B), then
                     borrowsLen * ObligationLiquidity(112B)

ObligationCollateral (88B): reserve pubkey(32) + depositedAmount u64(8) +
  marketValue u128(16) + padding(32)
ObligationLiquidity (112B): reserve pubkey(32) + cumulativeBorrowRateWads u128(16)
  + borrowedAmountWads u128(16) + marketValue u128(16) + padding(32)
(marketValue in both is the on-chain cached USD value from the LAST refresh
instruction -- it goes stale/zero the moment nobody touches the obligation, which
is why this module recomputes value live from the reserve's current exchange rate
and oracle price rather than trusting that field.)

Run:
  /Users/engineer/.venv/bin/python3 solend_positions.py <label> <solana-address>
"""
from __future__ import annotations
import sys
import time

import base58
import requests

SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"
SOLEND_PROGRAM_ID = "So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo"  # solend-sdk constants.ts
SAVE_API_BASE = "https://api.solend.fi"

OBLIGATION_SIZE = 1300
OWNER_OFFSET = 42
COLLATERAL_SPAN = 88   # ObligationCollateralLayout.span
LIQUIDITY_SPAN = 112   # ObligationLiquidityLayout.span
WAD = 10 ** 18

_mint_symbol_cache = None  # populated lazily, once per process, by _mint_symbol()


def _mint_symbol(mint):
    """mint pubkey -> ticker symbol (e.g. "USDC"), via Save's own market config.

    /v1/reserves (used for pricing) doesn't carry a symbol field, only the mint
    pubkey; /v1/markets/configs does, keyed by liquidityToken.mint. Fetched once
    per process and cached -- falls back to a truncated mint address if a reserve
    somehow isn't listed (e.g. a delisted/deprecated market), never raises.
    """
    global _mint_symbol_cache
    if _mint_symbol_cache is None:
        _mint_symbol_cache = {}
        try:
            resp = requests.get(
                f"{SAVE_API_BASE}/v1/markets/configs",
                params={"deployment": "production", "scope": "all"},
                timeout=30,
            )
            resp.raise_for_status()
            for market in resp.json():
                for r in market.get("reserves", []):
                    tok = r.get("liquidityToken") or {}
                    if tok.get("mint") and tok.get("symbol"):
                        _mint_symbol_cache[tok["mint"]] = tok["symbol"]
        except Exception:
            pass  # symbol resolution is cosmetic; pricing still works without it
    return _mint_symbol_cache.get(mint, f"{mint[:6]}...{mint[-4:]}")


def _rpc(method, params):
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    resp = requests.post(SOLANA_RPC_URL, json=payload, timeout=30)
    if resp.status_code == 429 or resp.status_code >= 500:
        time.sleep(4)
        resp = requests.post(SOLANA_RPC_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"RPC error for {method}: {data['error']}")
    return data["result"]


def _read_pubkey(buf, off):
    return base58.b58encode(buf[off:off + 32]).decode()


def _read_u128(buf, off):
    return int.from_bytes(buf[off:off + 16], "little")


def _read_u64(buf, off):
    return int.from_bytes(buf[off:off + 8], "little")


def find_obligations(owner_address):
    """getProgramAccounts filtered by memcmp on the Obligation.owner field.

    Returns raw base64-decoded account bytes for every Obligation account (any
    account owned by the Solend program whose `owner` field, at byte offset 42,
    matches this wallet -- dataSize is NOT filtered here so a future layout
    version with a different span still gets caught; callers should still guard
    on len(data) == OBLIGATION_SIZE before decoding with these fixed offsets).
    """
    result = _rpc("getProgramAccounts", [
        SOLEND_PROGRAM_ID,
        {
            "encoding": "base64",
            "filters": [
                {"memcmp": {"offset": OWNER_OFFSET, "bytes": owner_address}},
            ],
        },
    ])
    accounts = []
    import base64
    for entry in result:
        raw_b64, _enc = entry["account"]["data"]
        accounts.append({
            "pubkey": entry["pubkey"],
            "data": base64.b64decode(raw_b64),
        })
    return accounts


def decode_obligation(data):
    """-> dict with lendingMarket, owner, lastUpdateSlot, stale, deposits[], borrows[].

    deposits/borrows entries: {"reserve": pubkey, "raw_amount": int}. raw_amount
    is depositedAmount (deposits) or borrowedAmountWads (borrows, still WAD-scaled
    1e18 on top of the token's own decimals -- callers dealing with borrows must
    divide by WAD before applying token decimals).
    """
    if len(data) != OBLIGATION_SIZE:
        return None  # not a (recognized-version) Obligation account; skip

    last_update_slot = _read_u64(data, 1)
    stale = data[9]
    lending_market = _read_pubkey(data, 10)
    owner = _read_pubkey(data, 42)
    deposits_len = data[202]
    borrows_len = data[203]

    deposits, borrows = [], []
    off = 204
    for _ in range(deposits_len):
        reserve = _read_pubkey(data, off)
        deposited_amount = _read_u64(data, off + 32)
        deposits.append({"reserve": reserve, "raw_amount": deposited_amount})
        off += COLLATERAL_SPAN
    for _ in range(borrows_len):
        reserve = _read_pubkey(data, off)
        borrowed_amount_wads = _read_u128(data, off + 48)
        borrows.append({"reserve": reserve, "raw_amount": borrowed_amount_wads})
        off += LIQUIDITY_SPAN

    return {
        "lending_market": lending_market,
        "owner": owner,
        "last_update_slot": last_update_slot,
        "stale": bool(stale),
        "deposits": deposits,
        "borrows": borrows,
    }


def fetch_reserve_info(reserve_address):
    """GET api.solend.fi/v1/reserves?ids=<reserve_address> -> live exchange rate + price.

    Returns dict: {symbol_mint, decimals, ctoken_exchange_rate, market_price_usd}
    or None if the reserve isn't found / API call fails.
    """
    resp = requests.get(
        f"{SAVE_API_BASE}/v1/reserves",
        params={"ids": reserve_address},
        timeout=30,
    )
    if resp.status_code == 429 or resp.status_code >= 500:
        time.sleep(4)
        resp = requests.get(f"{SAVE_API_BASE}/v1/reserves", params={"ids": reserve_address}, timeout=30)
    resp.raise_for_status()
    results = resp.json().get("results") or []
    if not results:
        return None
    r = results[0]
    reserve = r["reserve"]
    liquidity = reserve["liquidity"]
    return {
        "mint": liquidity["mintPubkey"],
        "decimals": int(liquidity["mintDecimals"]),
        "ctoken_exchange_rate": float(r["cTokenExchangeRate"]),
        "market_price_usd": int(liquidity["marketPrice"]) / WAD,
    }


def fetch_positions(label, address):
    """-> list of row dicts {wallet, protocol, type, pool, asset, balance, usd_value, note}.

    Deposits become "Deposit" rows priced in the underlying liquidity token.
    Borrows become "Loan" rows with a negative usd_value (liability), matching
    Zerion's convention for loan positions elsewhere in this pipeline.
    """
    rows = []
    reserve_cache = {}

    def reserve(addr):
        if addr not in reserve_cache:
            reserve_cache[addr] = fetch_reserve_info(addr)
        return reserve_cache[addr]

    for acct in find_obligations(address):
        ob = decode_obligation(acct["data"])
        if ob is None:
            continue

        for dep in ob["deposits"]:
            if dep["raw_amount"] <= 0:
                continue
            info = reserve(dep["reserve"])
            if info is None:
                rows.append({
                    "wallet": label, "protocol": "Save (Solend)", "type": "Deposit",
                    "pool": ob["lending_market"], "asset": f"cToken {dep['reserve'][:6]}...",
                    "balance": dep["raw_amount"], "usd_value": 0.0,
                    "note": f"reserve {dep['reserve']} not found via api.solend.fi/v1/reserves",
                })
                continue
            underlying_amount = (dep["raw_amount"] / (10 ** info["decimals"])) * info["ctoken_exchange_rate"]
            usd_value = underlying_amount * info["market_price_usd"]
            rows.append({
                "wallet": label, "protocol": "Save (Solend)", "type": "Deposit",
                "pool": f"obligation {acct['pubkey'][:8]}...",
                "asset": _mint_symbol(info["mint"]), "balance": underlying_amount,
                "usd_value": usd_value,
                "note": (
                    f"cTokenExchangeRate={info['ctoken_exchange_rate']:.6f}; "
                    f"price=${info['market_price_usd']:.6f}"
                    + ("; obligation stale (not refreshed recently)" if ob["stale"] else "")
                ),
            })

        for bor in ob["borrows"]:
            if bor["raw_amount"] <= 0:
                continue
            info = reserve(bor["reserve"])
            if info is None:
                rows.append({
                    "wallet": label, "protocol": "Save (Solend)", "type": "Loan",
                    "pool": ob["lending_market"], "asset": f"reserve {bor['reserve'][:6]}...",
                    "balance": bor["raw_amount"] / WAD, "usd_value": 0.0,
                    "note": f"reserve {bor['reserve']} not found via api.solend.fi/v1/reserves",
                })
                continue
            underlying_amount = (bor["raw_amount"] / WAD) / (10 ** info["decimals"])
            usd_value = underlying_amount * info["market_price_usd"]
            rows.append({
                "wallet": label, "protocol": "Save (Solend)", "type": "Loan",
                "pool": f"obligation {acct['pubkey'][:8]}...",
                "asset": _mint_symbol(info["mint"]), "balance": underlying_amount,
                "usd_value": -usd_value,  # liability, negative like Zerion's loan convention
                "note": f"price=${info['market_price_usd']:.6f}",
            })

    return rows


if __name__ == "__main__":
    import json
    if len(sys.argv) != 3:
        print("usage: solend_positions.py <label> <solana-address>", file=sys.stderr)
        sys.exit(2)
    print(json.dumps(fetch_positions(sys.argv[1], sys.argv[2]), indent=2))
