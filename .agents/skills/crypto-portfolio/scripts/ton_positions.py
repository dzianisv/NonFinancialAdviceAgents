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

Two receipt-jetton types swap.coffee's public price feed has NO market_stats for
at all (verified live, not just price_usd=0 — confirmed 2026-07-10):

  - swap.coffee's OWN "Coffee DEX" LP tokens (`Coffee DEX: <pair> LP`). Root cause:
    on swap.coffee, the pool contract itself IS the LP jetton master (confirmed via
    TONAPI: interfaces = ["coffee_pool", "jetton_master"]) — priced here from the
    pool's own reserves: `GET https://backend.swap.coffee/v1/dex/pools` lists every
    pool by that same address (converted to friendly base64 form) with human-
    readable `reserves` for its two `tokens` ("native" = TON, else a jetton address
    priced via TONAPI `/v2/rates`). LP fair value = pool TVL / total LP supply
    (supply from TONAPI `/v2/jettons/{addr}`).
  - Storm Trade "YT ..." tokens are not Storm's own — they're FIVA protocol
    (thefiva.com) Pendle-style yield tokens minted against Storm SLP. FIVA's own
    API `GET https://api2.thefiva.com/protocol_metrics` lists every YT jetton
    address with its `maturity_date`. FIVA's own FAQ (docs.thefiva.com/faq) states
    outright: "Maturity is ... the date until which you farm points and receive
    yield from YT. After that date YT is worth 0." A matured YT (per that feed) is
    priced $0 with a note citing this; an unmatured YT has no price feed here and
    is flagged as a manual-check gap rather than guessed.
"""
from __future__ import annotations
import base64
import sys
import time
from datetime import datetime, timezone

import requests

COFFEE_BACKEND = "https://backend.swap.coffee"
COFFEE_TOKENS = "https://tokens.swap.coffee"
TONAPI_BASE = "https://tonapi.io/v2"
FIVA_METRICS_URL = "https://api2.thefiva.com/protocol_metrics"

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


def _raw_to_friendly(raw_addr, bounceable=True):
    """'0:<hex>' raw TON address -> bounceable base64url friendly form (standard
    TON address encoding: 0x11 tag + workchain + 32-byte hash + CRC16/XMODEM,
    base64url). Verified against TONAPI's /v2/address/{addr}/parse for both
    addresses used below. Needed because tokens.swap.coffee returns jetton
    addresses in raw form while swap.coffee's pools endpoint and FIVA's
    protocol_metrics key everything by friendly address."""
    wc_str, hash_hex = raw_addr.split(":")
    payload = bytes([0x11 if bounceable else 0x51, int(wc_str) & 0xFF]) + bytes.fromhex(hash_hex)
    crc = 0
    for byte in payload:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return base64.b64encode(payload + crc.to_bytes(2, "big")).decode().replace("+", "-").replace("/", "_")


_coffee_pools_cache = None
_fiva_metrics_cache = None


def _coffee_pools():
    """GET /v1/dex/pools once per run (public, ~344 pools): [{address, amm_type,
    tokens: ["native"|jetton_address, ...], reserves: [float, ...]}, ...] —
    reserves are already human-readable (decimals applied)."""
    global _coffee_pools_cache
    if _coffee_pools_cache is None:
        try:
            _coffee_pools_cache = _get(f"{COFFEE_BACKEND}/v1/dex/pools").json()
        except Exception as e:
            print(f"WARN: swap.coffee pools list unavailable: {e}", file=sys.stderr)
            _coffee_pools_cache = []
    return _coffee_pools_cache


def _coffee_lp_value_usd(jetton_address, ton_price):
    """Fair value per unit of a swap.coffee 'Coffee DEX' LP jetton = pool TVL /
    total LP supply. The pool contract IS the LP jetton master on swap.coffee, so
    the LP jetton's own (friendly-form) address is the pool's address in
    /v1/dex/pools. Returns (price_per_lp_token, None) or (None, reason)."""
    friendly = _raw_to_friendly(jetton_address)
    pool = next((p for p in _coffee_pools() if p.get("address") == friendly), None)
    if not pool:
        return None, "pool not found in backend.swap.coffee/v1/dex/pools"
    tokens, reserves = pool.get("tokens", []), pool.get("reserves", [])
    if len(tokens) != 2 or len(reserves) != 2:
        return None, f"unexpected pool shape: {pool}"
    tvl = 0.0
    for tok, res in zip(tokens, reserves):
        if tok == "native":
            tvl += res * ton_price
            continue
        try:
            rates = _get(f"{TONAPI_BASE}/rates", params={"tokens": tok, "currencies": "usd"}).json()
            usd = rates.get("rates", {}).get(tok, {}).get("prices", {}).get("USD")
        except Exception as e:
            return None, f"no USD price for pool token {tok}: {e}"
        if not usd:
            return None, f"no USD price for pool token {tok}"
        tvl += res * usd
    try:
        jd = _get(f"{TONAPI_BASE}/jettons/{jetton_address}").json()
        total_supply = int(jd["total_supply"]) / (10 ** int(jd["metadata"]["decimals"]))
    except Exception as e:
        return None, f"could not read LP total supply from TONAPI: {e}"
    if total_supply <= 0:
        return None, "LP total supply is 0"
    return tvl / total_supply, None


def _fiva_metrics():
    global _fiva_metrics_cache
    if _fiva_metrics_cache is None:
        try:
            _fiva_metrics_cache = _get(FIVA_METRICS_URL).json()
        except Exception as e:
            print(f"WARN: FIVA protocol_metrics unavailable: {e}", file=sys.stderr)
            _fiva_metrics_cache = {"assets": []}
    return _fiva_metrics_cache


def _fiva_yt_status(jetton_address):
    """Match a 'YT ...' jetton against FIVA's (thefiva.com) own protocol_metrics
    feed by friendly address (FIVA tokenizes Storm SLP, tsTON, tsUSDe, etc. into
    PT/YT Pendle-style pairs; this jetton's master IS a FIVA market's yt address).
    Returns (matured: bool|None, maturity_date str|None). matured=None means no
    FIVA market matched this address at all (unrecognized YT, not this protocol)."""
    friendly = _raw_to_friendly(jetton_address)
    now = datetime.now(timezone.utc)
    for asset in _fiva_metrics().get("assets", []):
        yt = (asset.get("jettons") or {}).get("yt") or {}
        if yt.get("master_address") == friendly:
            maturity = asset.get("maturity_date")
            try:
                matured = datetime.fromisoformat(maturity.replace("Z", "+00:00")) <= now
            except Exception:
                matured = None
            return matured, maturity
    return None, None


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

        low = f"{name} {symbol}".lower()
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
        elif not price and not ta_price and "coffee dex" in low and "lp" in low:
            # swap.coffee's own DEX LP tokens have no price feed at all (the pool
            # contract IS the LP jetton master) — value from the pool's own
            # reserves instead. See _coffee_lp_value_usd docstring.
            lp_price, reason = _coffee_lp_value_usd(j.get("address"), ton_price)
            if lp_price:
                price = lp_price
                note = "priced via swap.coffee pool reserves (backend.swap.coffee/v1/dex/pools): pool TVL / total LP supply"
            else:
                note = f"Coffee DEX LP: no valuation available ({reason})"
        elif not price and not ta_price and low.startswith("yt "):
            # Storm/other "YT ..." receipt jettons are FIVA (thefiva.com) Pendle-
            # style yield tokens minted against the underlying SLP/tsTON/etc.
            # See _fiva_yt_status docstring.
            matured, maturity = _fiva_yt_status(j.get("address"))
            if matured is True:
                note = (
                    f"FIVA yield token matured {maturity[:10]} (api2.thefiva.com/protocol_metrics) — "
                    "FIVA FAQ: 'After that date YT is worth 0'; priced $0, verified not assumed"
                )
            elif matured is False:
                note = f"FIVA yield token matures {maturity[:10]}, not yet matured — no YT price feed available, needs manual valuation"
            else:
                note = "unrecognized YT jetton (no FIVA protocol_metrics match) — no price feed available"

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
