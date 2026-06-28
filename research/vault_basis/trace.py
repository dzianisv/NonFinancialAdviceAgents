#!/usr/bin/env python3
"""Reconstruct cost basis + PnL for stablecoin/LP vault positions via Blockscout."""
import requests, time, warnings, json, sys
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

# Underlying stablecoins per chain (lower-case addr -> (symbol, decimals))
UNDERLYING = {
    "eth": {
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": ("USDC", 6),
        "0xdac17f958d2ee523a2206206994597c13d831ec7": ("USDT", 6),
        "0x4c9edd5852cd905f086c759e8383e09bff1e68b3": ("USDe", 18),
        "0x9d39a5de30e57443bff2a8307a4256c8797a3497": ("sUSDe", 18),
        "0x83f20f44975d03b1b09e64809b757c47f942beea": ("sDAI", 18),
        "0x6b175474e89094c44da98b954eedeac495271d0f": ("DAI", 18),
    },
    "base": {
        "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913": ("USDC", 6),
        "0xcfa3ef56d303ae4faaba0592388f19d7c3399fb4": ("eUSD", 18),
        "0xbb819d845b573b5d7c538f5b85057160cfb5f313": ("meUSD", 18),
    },
}

# (label, wallet, chain, share_token, share_decimals)
POSITIONS = [
    ("Maple syrupUSDC", "L3", "eth",  "0x80ac24aA929eaF5013f6436cdA2a7ba190f5Cc0b", 6),
    ("Maple syrupUSDC", "B3", "eth",  "0x80ac24aA929eaF5013f6436cdA2a7ba190f5Cc0b", 6),
    ("Fluid fUSDT",     "B3", "eth",  "0x5C20B550819128074FD538Edf79791733ccEdd18", 6),
    ("Avantis Jr USDC", "B3", "base", "0x944766f715b51967E56aFdE5f0Aa76cEaCc9E7f9", 6),
    ("sUSDe (Ethena)",  "L3", "eth",  "0x9D39A5DE30e57443BfF2A8307A4256c8797A3497", 18),
    ("eUSD/meUSD idle", "L3", "base", "0xbb819D845b573B5D7C538F5b85057160cfb5f313", 18),
    ("eUSD/meUSD idle", "L1", "base", "0xbb819D845b573B5D7C538F5b85057160cfb5f313", 18),
]

def get(url, params=None, tries=5):
    for i in range(tries):
        try:
            r = requests.get(url, params=params, timeout=40)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return None
            time.sleep(1.2 * (i + 1))
        except Exception:
            time.sleep(1.2 * (i + 1))
    return None

def all_transfers(chain, wallet, token):
    """Paginate token-transfers for wallet filtered to token."""
    base = CHAINS[chain]
    url = f"{base}/addresses/{wallet}/token-transfers"
    params = {"token": token}
    out, guard = [], 0
    while True:
        d = get(url, params=params)
        if not d:
            break
        out.extend(d.get("items", []))
        nxt = d.get("next_page_params")
        if not nxt or guard > 30:
            break
        params = {"token": token, **nxt}
        guard += 1
        time.sleep(0.4)
    return out

def tx_transfers(chain, txhash):
    base = CHAINS[chain]
    d = get(f"{base}/transactions/{txhash}/token-transfers", params={"type": "ERC-20"})
    items = d.get("items", []) if d else []
    # handle pagination inside tx (rare)
    if d:
        nxt = d.get("next_page_params")
        g = 0
        while nxt and g < 10:
            d2 = get(f"{base}/transactions/{txhash}/token-transfers", params={"type": "ERC-20", **nxt})
            if not d2:
                break
            items.extend(d2.get("items", []))
            nxt = d2.get("next_page_params")
            g += 1
    return items

def amt(total):
    return int(total["value"]) / (10 ** int(total["decimals"]))

def find_underlying(chain, txhash, wallet, share_token):
    """Return list of (symbol, signed_amount) for known underlying stablecoins
    moved by wallet in this tx. +ve = wallet received, -ve = wallet sent."""
    w = wallet.lower()
    st = share_token.lower()
    res = []
    for it in tx_transfers(chain, txhash):
        tok = it.get("token", {}) or {}
        caddr = (tok.get("address_hash") or tok.get("address") or "").lower()
        if caddr == st:
            continue  # skip the share token leg itself
        frm = (it.get("from", {}) or {}).get("hash", "").lower()
        to  = (it.get("to", {}) or {}).get("hash", "").lower()
        if w not in (frm, to):
            continue
        known = UNDERLYING.get(chain, {}).get(caddr)
        sym = known[0] if known else (tok.get("symbol") or caddr[:10])
        a = amt(it["total"])
        signed = a if to == w else -a
        res.append((sym, signed, caddr))
    return res

def main():
    print("# Cost-basis reconstruction\n")
    results = []
    for label, wkey, chain, share, sdec in POSITIONS:
        wallet = WALLETS[wkey]
        print(f"\n{'='*70}\n{label}  [{wkey} {wallet}] on {chain}\n  share token {share}\n{'='*70}")
        xfers = all_transfers(chain, wallet, share)
        print(f"  share-token transfers: {len(xfers)}")
        deposits = []   # underlying sent in to acquire shares
        withdraws = []  # underlying received on redemption
        share_in = 0.0
        share_out = 0.0
        first_dt = None
        rows = []
        for it in xfers:
            frm = (it.get("from", {}) or {}).get("hash", "").lower()
            to  = (it.get("to", {}) or {}).get("hash", "").lower()
            w = wallet.lower()
            sa = amt(it["total"])
            tx = it.get("transaction_hash")
            ts = it.get("timestamp")
            direction = "IN " if to == w else ("OUT" if frm == w else "?  ")
            if to == w:
                share_in += sa
                if first_dt is None or (ts and ts < first_dt):
                    first_dt = ts
            elif frm == w:
                share_out += sa
            paired = find_underlying(chain, tx, wallet, share)
            rows.append((ts, direction, sa, tx, paired, it.get("method")))
            time.sleep(0.25)
        # aggregate underlying flows
        dep_usd = {}
        wd_usd = {}
        for ts, direction, sa, tx, paired, method in rows:
            for sym, signed, caddr in paired:
                if direction == "IN ":      # acquiring shares -> wallet should SEND underlying (signed<0)
                    if signed < 0:
                        dep_usd[sym] = dep_usd.get(sym, 0) + (-signed)
                elif direction == "OUT":    # redeeming shares -> wallet RECEIVES underlying (signed>0)
                    if signed > 0:
                        wd_usd[sym] = wd_usd.get(sym, 0) + signed
        for ts, direction, sa, tx, paired, method in rows:
            ps = ", ".join(f"{s}{'+' if v>0 else ''}{v:,.2f}" for s, v, _ in paired) or "(none found)"
            print(f"   {ts}  {direction}  shares={sa:,.4f}  method={method}")
            print(f"        tx={tx}")
            print(f"        underlying moved by wallet: {ps}")
        print(f"  --- share IN={share_in:,.4f} OUT={share_out:,.4f} net={share_in-share_out:,.4f}")
        print(f"  --- deposited underlying: {dep_usd}")
        print(f"  --- withdrawn underlying: {wd_usd}")
        results.append((label, wkey, chain, share, dep_usd, wd_usd, first_dt, share_in, share_out))
    # dump structured
    with open("research/vault_basis/results.json", "w") as f:
        json.dump([{
            "label": r[0], "wallet": r[1], "chain": r[2], "share": r[3],
            "deposited": r[4], "withdrawn": r[5], "first_deposit": r[6],
            "share_in": r[7], "share_out": r[8],
        } for r in results], f, indent=2)
    print("\nWROTE research/vault_basis/results.json")

if __name__ == "__main__":
    main()
