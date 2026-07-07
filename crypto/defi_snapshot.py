#!/usr/bin/env python3
"""
DeFi portfolio snapshot: pulls live positions for a fixed wallet list via
Zerion (EVM + Solana) and TONAPI (TON), writes crypto/report/defi_snapshot.csv.

Run:   ZERION_API_KEY=... /Users/engineer/.venv/bin/python3 crypto/defi_snapshot.py
Output: crypto/report/defi_snapshot.csv, crypto/report/defi_snapshot_totals.json
"""
from __future__ import annotations
import base64
import json
import os
import sys
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR = os.path.join(HERE, "report")
RAW_DIR = os.environ.get("DEFI_SNAPSHOT_RAW_DIR", "/tmp/defi_snapshot_raw")

ZERION_BASE = "https://api.zerion.io/v1"
TONAPI_BASE = "https://tonapi.io/v2"

DUST_FLOOR = 0.50
KEEP_ALL_DUST = {"T1", "S1", "S2"}  # never dust-filtered

WALLET_ORDER = ["L1", "L3", "B1", "B3", "B5", "T1", "S1", "S2"]
WALLETS = [
    ("L1", "evm", "0x5c1b7a3ab7797e237cc9ec1e30a18048c364174a"),
    ("L3", "evm", "0x5d039ece117073323ade5057a516864f4c40e653"),
    ("B1", "evm", "0x9945Ba0a781200B90b4c28528cced309aBB90871"),
    ("B3", "evm", "0xd6b5587944a2bf537ef9cf04695ed093f4805e75"),
    ("B5", "evm", "0xaefdc2b58f5a15b6e5e3d6d7ac707c76967ab4ae"),
    ("T1", "ton", "UQBkT-XTPTbYeVNsWmC5Dxnw6DUygKOgTMTooA7SIz7BE19N"),
    ("S1", "solana", "jetmpL3H387ck44FNiAZsyGNNRad3mvHgSs1mbppqdG"),
    ("S2", "solana", "6iQHaQyTwZHqXKcVMoBUWELvRQTD2bXJ5AJouJjx8jRD"),
]

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

DEFI_JETTON_MARKERS = ["storm", "dedust", "coffee dex", "-slp", " lp", "pool"]


def get_with_retry(url, **kwargs):
    """GET with one retry on 429/5xx, short backoff."""
    resp = requests.get(url, timeout=30, **kwargs)
    if resp.status_code == 429 or resp.status_code >= 500:
        time.sleep(4)
        resp = requests.get(url, timeout=30, **kwargs)
    return resp


def _fetch_zerion_once(chain, address, auth):
    params = {"currency": "usd", "filter[trash]": "only_non_trash", "sort": "value"}
    if chain == "evm":
        params["filter[positions]"] = "no_filter"
    # solana: filter[positions] is not supported; default already returns wallet+locked etc.
    headers = {"accept": "application/json"}
    resp = get_with_retry(f"{ZERION_BASE}/wallets/{address}/positions/", headers=headers, auth=auth, params=params)
    if resp.status_code in (401, 403):
        print(f"STOP: Zerion auth failed ({resp.status_code}) for {address}: {resp.text[:300]}", file=sys.stderr)
        sys.exit(1)
    resp.raise_for_status()
    return resp.json()


def fetch_zerion(chain, address, auth):
    """Zerion's positions endpoint is eventually-consistent: identical requests a few
    seconds apart can return a different position count (observed: reward positions
    intermittently missing). Fetch twice and union by position id to reduce misses."""
    first = _fetch_zerion_once(chain, address, auth)
    time.sleep(2)
    second = _fetch_zerion_once(chain, address, auth)
    by_id = {p["id"]: p for p in first.get("data", [])}
    for p in second.get("data", []):
        by_id[p["id"]] = p
    merged = dict(first)
    merged["data"] = list(by_id.values())
    return merged


def zerion_rows(label, data):
    rows = []
    for p in data.get("data", []):
        a = p["attributes"]
        ptype = a.get("position_type") or "wallet"
        fi = a.get("fungible_info") or {}
        symbol = fi.get("symbol") or "?"
        qty = (a.get("quantity") or {}).get("float")
        value = a.get("value")
        if qty is None:
            continue
        if ptype == "wallet":
            protocol = "Wallet tokens"
            pool = "—"
        else:
            protocol = a.get("protocol") or a.get("name") or "Unknown"
            pool = a.get("name") or "—"
        type_label = TYPE_MAP.get(ptype, ptype.title() if ptype else "—")
        rows.append({
            "wallet": label,
            "protocol": protocol,
            "type": type_label,
            "pool": pool,
            "asset": symbol,
            "balance": qty,
            "usd_value": value if value is not None else 0.0,
        })
    return rows


def fetch_ton_native(address):
    resp = get_with_retry(f"{TONAPI_BASE}/accounts/{address}", headers={"accept": "application/json"})
    resp.raise_for_status()
    acct = resp.json()
    time.sleep(4)
    resp2 = get_with_retry(f"{TONAPI_BASE}/rates", headers={"accept": "application/json"}, params={"tokens": "ton", "currencies": "usd"})
    resp2.raise_for_status()
    rates = resp2.json()
    price = rates.get("rates", {}).get("TON", {}).get("prices", {}).get("USD", 0.0)
    balance_ton = acct["balance"] / 1e9
    return acct, rates, balance_ton, price


def fetch_ton_jettons(address):
    resp = get_with_retry(
        f"{TONAPI_BASE}/accounts/{address}/jettons",
        headers={"accept": "application/json"},
        params={"currencies": "usd"},
    )
    resp.raise_for_status()
    return resp.json()


def classify_ton_jetton(name, symbol):
    low = f"{name} {symbol}".lower()
    if any(marker in low for marker in DEFI_JETTON_MARKERS):
        return name, "Deposit", "—"
    return "Wallet tokens", "—", "—"


def ton_rows(label, acct, balance_ton, ton_price, jettons):
    rows = []
    ton_value = balance_ton * ton_price
    rows.append({
        "wallet": label, "protocol": "Wallet tokens", "type": "—", "pool": "—",
        "asset": "TON", "balance": balance_ton, "usd_value": ton_value,
    })
    for b in jettons.get("balances", []):
        j = b["jetton"]
        decimals = j.get("decimals", 9)
        bal = int(b["balance"]) / (10 ** decimals)
        if bal == 0:
            continue
        price = (b.get("price") or {}).get("prices", {}).get("USD", 0.0) or 0.0
        value = bal * price
        name = j.get("name") or j.get("symbol") or "?"
        symbol = j.get("symbol") or name
        protocol, type_label, pool = classify_ton_jetton(name, symbol)
        rows.append({
            "wallet": label, "protocol": protocol, "type": type_label, "pool": pool,
            "asset": symbol, "balance": bal, "usd_value": value,
        })
    return rows


def main():
    api_key = os.environ.get("ZERION_API_KEY")
    if not api_key:
        print("STOP: ZERION_API_KEY env var not set.", file=sys.stderr)
        sys.exit(1)
    auth = (api_key, "")

    os.makedirs(REPORT_DIR, exist_ok=True)
    os.makedirs(RAW_DIR, exist_ok=True)

    all_rows = []
    wallet_totals = {}

    for label, chain, address in WALLETS:
        print(f"Fetching {label} ({chain}) {address} ...")
        if chain in ("evm", "solana"):
            data = fetch_zerion(chain, address, auth)
            with open(os.path.join(RAW_DIR, f"{label}.json"), "w") as f:
                json.dump(data, f)
            rows = zerion_rows(label, data)
            time.sleep(1.5)  # be polite between wallets
        elif chain == "ton":
            acct, rates, balance_ton, ton_price = fetch_ton_native(address)
            time.sleep(4)
            jettons = fetch_ton_jettons(address)
            with open(os.path.join(RAW_DIR, f"{label}_account.json"), "w") as f:
                json.dump(acct, f)
            with open(os.path.join(RAW_DIR, f"{label}_rates.json"), "w") as f:
                json.dump(rates, f)
            with open(os.path.join(RAW_DIR, f"{label}_jettons.json"), "w") as f:
                json.dump(jettons, f)
            rows = ton_rows(label, acct, balance_ton, ton_price, jettons)
        else:
            raise ValueError(f"unknown chain {chain}")

        # wallet total = sum of ALL fetched positions (pre dust-filter), for honest comparison
        wallet_totals[label] = round(sum(r["usd_value"] for r in rows), 2)

        keep_all = label in KEEP_ALL_DUST
        for r in rows:
            if not keep_all and r["usd_value"] < DUST_FLOOR:
                continue
            all_rows.append(r)

    # sort: wallet order, then USD desc within wallet
    order_index = {w: i for i, w in enumerate(WALLET_ORDER)}
    all_rows.sort(key=lambda r: (order_index.get(r["wallet"], 99), -r["usd_value"]))

    csv_path = os.path.join(REPORT_DIR, "defi_snapshot.csv")
    with open(csv_path, "w", newline="") as f:
        f.write("Wallet,Protocol,Type,Pool,Asset,Balance,USD Value\n")
        for r in all_rows:
            def esc(v):
                v = str(v)
                if "," in v or '"' in v:
                    v = '"' + v.replace('"', '""') + '"'
                return v
            bal = f"{r['balance']:.6f}".rstrip("0").rstrip(".") if r["balance"] else "0"
            usd = f"{r['usd_value']:.2f}"
            f.write(",".join([
                esc(r["wallet"]), esc(r["protocol"]), esc(r["type"]),
                esc(r["pool"]), esc(r["asset"]), esc(bal), esc(usd),
            ]) + "\n")

    grand_total = round(sum(wallet_totals.values()), 2)
    totals_path = os.path.join(REPORT_DIR, "defi_snapshot_totals.json")
    with open(totals_path, "w") as f:
        json.dump({**wallet_totals, "GRAND_TOTAL": grand_total}, f, indent=2)

    print("\n=== Per-wallet totals ===")
    for label in WALLET_ORDER:
        print(f"  {label}: ${wallet_totals.get(label, 0):,.2f}")
    print(f"  GRAND TOTAL: ${grand_total:,.2f}")
    print(f"\nCSV: {csv_path}")
    print(f"Totals JSON: {totals_path}")


if __name__ == "__main__":
    main()
