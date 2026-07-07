#!/usr/bin/env python3
"""Hyperliquid positions via HL's own info API (public, no key).

Zerion does not index Hyperliquid at all — without this module an EVM wallet's HL
book (spot, perp margin, vault deposits) silently disappears from the snapshot.

POST https://api.hyperliquid.xyz/info with:
  {"type": "metaAndAssetCtxs"}                 -> perp universe + oracle/mark prices
  {"type": "spotClearinghouseState", "user"}   -> spot balances
  {"type": "clearinghouseState", "user"}       -> perp account: positions, withdrawable
  {"type": "userVaultEquities", "user"}        -> vault deposits (incl. HLP)

Pricing discipline (same as defi-portfolio-manager/hyperliquid_status.ts): spot
tokens are priced off the PERP mark oracle; stables at $1; a spot token with no
perp oracle and not a stable is illiquid dust valued $0 and flagged — HL's thin
spot mid would quote unrealizable millions for it.
"""
from __future__ import annotations
import sys
import time

import requests

INFO_URL = "https://api.hyperliquid.xyz/info"
STABLES = {"USDC", "USDT", "USDH"}

# HL spot wrappers of majors -> the perp oracle that prices them (USOL is real SOL,
# not dust; without this alias the dust rule zeroes a liquid position).
SPOT_PERP_ALIAS = {"USOL": "SOL", "UBTC": "BTC", "UETH": "ETH"}


def _info(payload):
    resp = requests.post(INFO_URL, json=payload, timeout=30)
    if resp.status_code == 429 or resp.status_code >= 500:
        time.sleep(4)
        resp = requests.post(INFO_URL, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _perp_marks():
    meta, ctxs = _info({"type": "metaAndAssetCtxs"})
    marks = {}
    for i, asset in enumerate(meta.get("universe", [])):
        ctx = ctxs[i] if i < len(ctxs) else {}
        px = ctx.get("oraclePx") or ctx.get("markPx")
        if px:
            marks[asset["name"]] = float(px)
    return marks


def fetch_positions(label, address):
    """-> list of row dicts {wallet, protocol, type, pool, asset, balance, usd_value, note}."""
    marks = _perp_marks()
    spot = _info({"type": "spotClearinghouseState", "user": address})
    perp = _info({"type": "clearinghouseState", "user": address})
    vaults = _info({"type": "userVaultEquities", "user": address})

    rows = []

    for b in spot.get("balances", []):
        coin, total = b.get("coin", "?"), float(b.get("total", 0) or 0)
        if total == 0:
            continue
        mark_coin = SPOT_PERP_ALIAS.get(coin, coin)
        if coin in STABLES:
            price, note = 1.0, ""
        elif mark_coin in marks:
            price, note = marks[mark_coin], "priced off perp mark"
        else:
            price, note = 0.0, "no perp oracle + not a stable -> illiquid dust, $0"
        rows.append({
            "wallet": label, "protocol": "Hyperliquid", "type": "Deposit",
            "pool": "Spot", "asset": coin, "balance": total,
            "usd_value": total * price, "note": note,
        })

    withdrawable = float(perp.get("withdrawable", 0) or 0)
    if withdrawable > 0:
        rows.append({
            "wallet": label, "protocol": "Hyperliquid", "type": "Deposit",
            "pool": "Perps Withdrawable", "asset": "USDC", "balance": withdrawable,
            "usd_value": withdrawable, "note": "",
        })

    for ap in perp.get("assetPositions", []):
        pos = ap.get("position") or {}
        szi = float(pos.get("szi", 0) or 0)
        if szi == 0:
            continue
        coin = pos.get("coin", "?")
        margin = float(pos.get("marginUsed", 0) or 0)
        upnl = float(pos.get("unrealizedPnl", 0) or 0)
        lev = (pos.get("leverage") or {}).get("value", "?")
        side = "Long" if szi > 0 else "Short"
        rows.append({
            "wallet": label, "protocol": "Hyperliquid", "type": "Perpetuals",
            "pool": f"{coin}/USDC ({side} {lev}x)",
            "asset": f"USDC margin (P&L {upnl:+.2f})", "balance": margin,
            "usd_value": margin, "note": "",
        })

    for v in vaults or []:
        equity = float(v.get("equity", 0) or 0)
        if equity == 0:
            continue
        rows.append({
            "wallet": label, "protocol": "Hyperliquid", "type": "Yield",
            "pool": "Vaults", "asset": "USDC", "balance": equity,
            "usd_value": equity, "note": v.get("vaultAddress", ""),
        })

    return rows


if __name__ == "__main__":
    import json
    if len(sys.argv) != 3:
        print("usage: hyperliquid_positions.py <label> <0xaddress>", file=sys.stderr)
        sys.exit(2)
    print(json.dumps(fetch_positions(sys.argv[1], sys.argv[2]), indent=2))
