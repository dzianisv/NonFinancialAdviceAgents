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
perp oracle and not a stable falls back to its own HL spot-pair mark (spot vs
USDC), noted as such since it may carry more slippage risk than a perp-quoted
price; only a token with no price anywhere is genuine illiquid dust valued $0.
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


def _spot_marks():
    """coin name -> its own HL spot-pair mark price (vs USDC), for tokens with no perp market.

    ctxs is indexed by each pair's `index` field, NOT by its position in the
    `universe` array -- the two diverge once index gaps appear, so ctxs[i] by
    enumeration order silently pulls the wrong pair's price (caught by feeding
    real balances through: UPUMP came back priced off an unrelated pair).
    """
    spot_meta, ctxs = _info({"type": "spotMetaAndAssetCtxs"})
    token_names = {t["index"]: t["name"] for t in spot_meta.get("tokens", [])}
    marks = {}
    for pair in spot_meta.get("universe", []):
        idx = pair["index"]
        ctx = ctxs[idx] if idx < len(ctxs) else {}
        px = ctx.get("markPx") or ctx.get("midPx")
        base_idx, quote_idx = pair.get("tokens", [None, None])
        quote_name = token_names.get(quote_idx)
        if px and quote_name == "USDC":
            marks[token_names.get(base_idx)] = float(px)
    return marks


def fetch_positions(label, address):
    """-> list of row dicts {wallet, protocol, type, pool, asset, balance, usd_value, note}."""
    marks = _perp_marks()
    spot_marks = None  # lazy: only fetched if a balance actually needs the fallback
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
            if spot_marks is None:
                spot_marks = _spot_marks()
            if coin in spot_marks:
                price = spot_marks[coin]
                note = "no perp oracle; priced off HL spot mark (may carry more slippage risk than perp-quoted tokens)"
            else:
                price, note = 0.0, "no perp oracle and no spot mark -> illiquid dust, $0"
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
