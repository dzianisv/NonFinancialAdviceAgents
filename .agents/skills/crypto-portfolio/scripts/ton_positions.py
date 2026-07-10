#!/usr/bin/env python3
"""TON positions via the swap.coffee API (primary), TONAPI as price cross-check.

swap.coffee endpoints (public, no key; ~1 req/s — https://docs.swap.coffee):
  GET https://backend.swap.coffee/v1/ton/wallet/{address}/balance   -> nanotons (string)
  GET https://tokens.swap.coffee/api/v3/accounts/{address}/jettons  -> jettons incl. market_stats.price_usd

DeFi receipt jettons (Storm SLP, DeDust/Coffee LP, Pendle-style YT) show up as
jettons with a price — that's how TON DeFi positions are read here; there is no
public "all user yield positions" endpoint (the per-pool one needs a pool address).

Price discipline: swap.coffee jetton prices come from its own pool graph and can be
stale for thin-liquidity receipt tokens (observed: USDT-SLP $1.44 vs TONAPI $1.33,
+8%). Each jetton price is cross-checked against TONAPI; on >5% divergence the
TONAPI price wins and the row is flagged in `note`. Native TON is priced via
TONAPI /v2/rates.
"""
from __future__ import annotations
import sys
import time

import requests

COFFEE_BACKEND = "https://backend.swap.coffee"
COFFEE_TOKENS = "https://tokens.swap.coffee"
TONAPI_BASE = "https://tonapi.io/v2"

DIVERGENCE_LIMIT = 0.05
DEFI_JETTON_MARKERS = ["storm", "dedust", "coffee dex", "-slp", " lp", "pool", "yt "]


def _get(url, **kwargs):
    resp = requests.get(url, timeout=30, **kwargs)
    if resp.status_code == 429 or resp.status_code >= 500:
        time.sleep(4)
        resp = requests.get(url, timeout=30, **kwargs)
    resp.raise_for_status()
    return resp


def _ton_price_usd():
    rates = _get(f"{TONAPI_BASE}/rates", params={"tokens": "ton", "currencies": "usd"}).json()
    return rates.get("rates", {}).get("TON", {}).get("prices", {}).get("USD", 0.0)


def _tonapi_jetton_prices(address):
    """jetton master address (raw 0:... form) -> TONAPI USD price."""
    try:
        data = _get(f"{TONAPI_BASE}/accounts/{address}/jettons", params={"currencies": "usd"}).json()
    except Exception as e:
        print(f"WARN: TONAPI cross-check unavailable: {e}", file=sys.stderr)
        return {}
    prices = {}
    for b in data.get("balances", []):
        j = b.get("jetton") or {}
        price = ((b.get("price") or {}).get("prices") or {}).get("USD")
        if j.get("address") and price:
            prices[j["address"]] = float(price)
    return prices


def _classify(name, symbol):
    low = f"{name} {symbol}".lower()
    if any(m in low for m in DEFI_JETTON_MARKERS):
        return name, "Deposit", "—"
    return "Wallet tokens", "—", "—"


def fetch_positions(label, address):
    """-> list of row dicts {wallet, protocol, type, pool, asset, balance, usd_value, note}."""
    rows = []

    nanotons = int(_get(f"{COFFEE_BACKEND}/v1/ton/wallet/{address}/balance").json())
    ton_balance = nanotons / 1e9
    ton_price = _ton_price_usd()
    rows.append({
        "wallet": label, "protocol": "Wallet tokens", "type": "—", "pool": "—",
        "asset": "TON", "balance": ton_balance, "usd_value": ton_balance * ton_price,
        "note": "",
    })

    time.sleep(1.1)  # swap.coffee public tier: ~1 req/s
    jettons = _get(f"{COFFEE_TOKENS}/api/v3/accounts/{address}/jettons").json()
    tonapi_prices = _tonapi_jetton_prices(address)

    for item in jettons.get("items", []):
        j = item.get("jetton") or {}
        decimals = j.get("decimals", 9)
        balance = int(item["balance"]) / (10 ** decimals)
        if balance == 0:
            continue
        symbol = j.get("symbol") or j.get("name") or "?"
        name = j.get("name") or symbol
        verification = (j.get("verification") or "").upper()
        price = (j.get("market_stats") or {}).get("price_usd") or 0.0
        note = ""

        ta_price = tonapi_prices.get(j.get("address"))
        if ta_price and price and abs(price - ta_price) / ta_price > DIVERGENCE_LIMIT:
            note = f"price divergence: swap.coffee ${price:.4f} vs TONAPI ${ta_price:.4f}, using TONAPI"
            price = ta_price
        elif not price and ta_price:
            note = "priced via TONAPI (no swap.coffee price)"
            price = ta_price
        elif price and not ta_price and verification != "WHITELISTED":
            # swap.coffee quotes fantasy prices for scam jettons TONAPI won't price
            # (observed: "SWPG" 1 unit = $1,829). Unverified + no second source = $0.
            note = f"swap.coffee ${price:.4f} rejected: unverified jetton with no TONAPI price (likely scam)"
            price = 0.0

        protocol, type_label, pool = _classify(name, symbol)

        if protocol == "Wallet tokens" and verification != "WHITELISTED" and price == 0:
            # Unverified + no real price from ANY source = airdrop spam/scam jetton
            # (fake "GRAM Unlock" claim tokens, $BLUM, TONRAGE, etc.), not real dust.
            # Recognized DeFi receipt jettons (Storm/DeDust/Coffee LP, YT, ...) are
            # NEVER suppressed here even if currently unpriced — real user deposits
            # stay visible regardless of price-feed gaps. Drop unconditionally, even
            # for keep_all_dust wallets — zero economic and zero diagnostic value.
            print(f"SKIP scam/spam jetton: {symbol} ({name}) in {label}", file=sys.stderr)
            continue
        rows.append({
            "wallet": label, "protocol": protocol, "type": type_label, "pool": pool,
            "asset": symbol, "balance": balance, "usd_value": balance * price,
            "note": note,
        })
    return rows


if __name__ == "__main__":
    import json
    if len(sys.argv) != 3:
        print("usage: ton_positions.py <label> <address>", file=sys.stderr)
        sys.exit(2)
    print(json.dumps(fetch_positions(sys.argv[1], sys.argv[2]), indent=2))
