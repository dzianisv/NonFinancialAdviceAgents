#!/usr/bin/env python3
"""Locate share-token contract addresses for each wallet on Base + Ethereum."""
import requests, json, time, warnings
warnings.filterwarnings("ignore")

CHAINS = {
    "base": "https://base.blockscout.com/api/v2",
    "eth":  "https://eth.blockscout.com/api/v2",
}
WALLETS = {
    "L3": "0x5d039ece117073323ade5057a516864f4c40e653",
    "B3": "0xd6b5587944a2bf537ef9cf04695ed093f4805e75",
    "L1": "0x5c1b7a3ab7797e237cc9ec1e30a18048c364174a",
}

def get(url, params=None, tries=4):
    for i in range(tries):
        try:
            r = requests.get(url, params=params, timeout=30)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return None
            time.sleep(1.5 * (i + 1))
        except Exception:
            time.sleep(1.5 * (i + 1))
    return None

for wname, addr in WALLETS.items():
    for cname, base in CHAINS.items():
        data = get(f"{base}/addresses/{addr}/tokens", params={"type": "ERC-20"})
        if not data or not data.get("items"):
            continue
        print(f"\n===== {wname} ({addr}) on {cname} =====")
        for it in data["items"]:
            t = it["token"]
            dec = int(t.get("decimals") or 0)
            val = int(it.get("value") or 0)
            amt = val / (10 ** dec) if dec else val
            xr = t.get("exchange_rate")
            usd = amt * float(xr) if xr else None
            usd_s = f"${usd:,.2f}" if usd is not None else "n/a"
            print(f"  {t['symbol']:<12} {t['name'][:30]:<30} {t['address_hash']} dec={dec} bal={amt:,.4f} usd={usd_s}")
