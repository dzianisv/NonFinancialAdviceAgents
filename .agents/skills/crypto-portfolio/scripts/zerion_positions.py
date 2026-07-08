#!/usr/bin/env python3
"""EVM + Solana positions via the Zerion API.

Role: automated CROSS-CHECK and machine-readable balance source — the PRIMARY truth for
EVM positions is the DeBank browser read (see SKILL.md); Zerion does not index every
protocol (missed Hyperliquid, Lighter).

Returns a list of normalized position rows for one wallet:
  {wallet, protocol, type, pool, asset, balance, usd_value, note}

Handles three Zerion quirks that corrupt a naive read:
  1. Eventual consistency — identical requests seconds apart can return different
     position sets (reward positions intermittently missing). Fetch twice, union by id.
  2. Receipt-token double count — with filter[positions]=no_filter Zerion can return
     BOTH the protocol position (e.g. Maple "Syrup USDC" deposit) AND the receipt
     token sitting in the wallet (syrupUSDC) for the same money. Known receipts are
     dropped when the matching protocol position is present, relabeled otherwise.
  3. Unpriced Solana tokens (fragSOL, jlUSDS, ...) — value comes back null; price
     them via the Jupiter price API by mint address.

Auth: ZERION_API_KEY env var (Basic auth, key as username, empty password).
"""
from __future__ import annotations
import os
import sys
import time

import requests

ZERION_BASE = "https://api.zerion.io/v1"
JUPITER_PRICE_URL = "https://lite-api.jup.ag/price/v3"

TYPE_MAP = {
    "wallet": "—",
    "deposit": "Deposit",
    "staked": "Staked",
    "locked": "Locked",
    "loan": "Loan",
    "reward": "Rewards",
    "margin": "Perpetuals",
    "perpetual": "Perpetuals",
    "airdrop": "Rewards",
}

# Receipt tokens that Zerion may ALSO report as a protocol position (same money twice).
# symbol -> (protocol, type) of the position the receipt represents.
RECEIPT_TOKENS = {
    "syrupUSDC": ("Maple", "Yield"),
    "syrupUSDT": ("Maple", "Yield"),
    "jUSDC": ("Avantis", "Yield"),
    "fUSDT": ("Fluid", "Yield"),
    "fUSDC": ("Fluid", "Yield"),
    "sUSDe": ("Ethena", "Staked"),
    "stETH": ("Lido", "Staked"),
    "wstETH": ("Lido", "Staked"),
    "xGRAIL": ("Camelot", "Staked"),
}


def _get_with_retry(url, **kwargs):
    resp = requests.get(url, timeout=30, **kwargs)
    if resp.status_code == 429 or resp.status_code >= 500:
        time.sleep(4)
        resp = requests.get(url, timeout=30, **kwargs)
    return resp


def _fetch_once(chain, address, auth):
    params = {"currency": "usd", "filter[trash]": "only_non_trash", "sort": "value"}
    if chain == "evm":
        params["filter[positions]"] = "no_filter"
    resp = _get_with_retry(
        f"{ZERION_BASE}/wallets/{address}/positions/",
        headers={"accept": "application/json"}, auth=auth, params=params,
    )
    if resp.status_code in (401, 403):
        print(f"STOP: Zerion auth failed ({resp.status_code}): {resp.text[:300]}", file=sys.stderr)
        sys.exit(1)
    resp.raise_for_status()
    return resp.json()


def _fetch_union(chain, address, auth):
    first = _fetch_once(chain, address, auth)
    time.sleep(2)
    second = _fetch_once(chain, address, auth)
    by_id = {p["id"]: p for p in first.get("data", [])}
    for p in second.get("data", []):
        by_id[p["id"]] = p
    return list(by_id.values())


def _solana_mint(attrs):
    for impl in (attrs.get("fungible_info") or {}).get("implementations", []):
        if impl.get("chain_id") == "solana" and impl.get("address"):
            return impl["address"]
    return None


def _jupiter_prices(mints):
    """mint -> USD price; missing/unpriced mints absent from the result."""
    if not mints:
        return {}
    try:
        resp = _get_with_retry(JUPITER_PRICE_URL, params={"ids": ",".join(mints)})
        resp.raise_for_status()
        return {m: float(v["usdPrice"]) for m, v in resp.json().items() if v and v.get("usdPrice")}
    except Exception as e:
        print(f"WARN: Jupiter price lookup failed: {e}", file=sys.stderr)
        return {}


def fetch_positions(label, chain, address):
    """-> list of row dicts for one EVM or Solana wallet."""
    api_key = os.environ.get("ZERION_API_KEY")
    if not api_key:
        print("STOP: ZERION_API_KEY env var not set.", file=sys.stderr)
        sys.exit(1)
    auth = (api_key, "")

    positions = _fetch_union(chain, address, auth)

    rows = []
    complex_protocols = set()  # protocols present as non-wallet positions
    unpriced_solana = []       # (row, mint) needing a Jupiter price

    for p in positions:
        a = p["attributes"]
        ptype = a.get("position_type") or "wallet"
        fi = a.get("fungible_info") or {}
        symbol = fi.get("symbol") or "?"
        qty = (a.get("quantity") or {}).get("float")
        value = a.get("value")
        if qty is None:
            continue
        if ptype == "wallet":
            protocol, pool = "Wallet tokens", "—"
        else:
            protocol = a.get("protocol") or a.get("name") or "Unknown"
            pool = a.get("name") or "—"
            complex_protocols.add(protocol.lower())
        row = {
            "wallet": label,
            "protocol": protocol,
            "type": TYPE_MAP.get(ptype, ptype.title()),
            "pool": pool,
            "asset": symbol,
            "balance": qty,
            "usd_value": value if value is not None else 0.0,
            "note": "",
            "_ptype": ptype,
        }
        if chain == "solana" and (value is None or value == 0) and qty > 0:
            mint = _solana_mint(a)
            if mint:
                unpriced_solana.append((row, mint))
        rows.append(row)

    # Jupiter fallback for unpriced Solana tokens
    prices = _jupiter_prices([m for _, m in unpriced_solana])
    for row, mint in unpriced_solana:
        price = prices.get(mint)
        if price:
            row["usd_value"] = row["balance"] * price
            row["note"] = "priced via Jupiter"

    # Receipt-token dedup / relabel
    deduped = []
    for row in rows:
        if row["_ptype"] == "wallet" and row["asset"] in RECEIPT_TOKENS:
            protocol, type_label = RECEIPT_TOKENS[row["asset"]]
            if protocol.lower() in complex_protocols:
                continue  # protocol position already counted this money
            row["protocol"], row["type"] = protocol, type_label
            row["pool"] = row["asset"]
            row["note"] = (row["note"] + "; " if row["note"] else "") + "receipt token"
        row.pop("_ptype")
        deduped.append(row)
    return deduped


if __name__ == "__main__":
    import json
    if len(sys.argv) != 4 or sys.argv[2] not in ("evm", "solana"):
        print("usage: zerion_positions.py <label> <evm|solana> <address>", file=sys.stderr)
        sys.exit(2)
    print(json.dumps(fetch_positions(sys.argv[1], sys.argv[2], sys.argv[3]), indent=2))
