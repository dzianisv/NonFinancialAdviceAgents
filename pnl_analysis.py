#!/usr/bin/env python3
"""
PnL and cost basis analysis for Hyperliquid wallets + stETH.
Wallets:
  L1 = 0x5c1b7a3ab7797e237cc9ec1e30a18048c364174a
  L3 = 0x5d039ece117073323ade5057a516864f4c40e653
"""

import json
import sys
import time
from urllib.request import urlopen, Request
from urllib.error import URLError
from collections import defaultdict

# ─── helpers ──────────────────────────────────────────────────────────────────

HL_URL = "https://api.hyperliquid.xyz/info"
L1 = "0x5c1b7a3ab7797e237cc9ec1e30a18048c364174a"
L3 = "0x5d039ece117073323ade5057a516864f4c40e653"
STETH = "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84"

def hl_post(body: dict) -> any:
    data = json.dumps(body).encode()
    req = Request(HL_URL, data=data, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  [WARN] HL API error: {e}", file=sys.stderr)
        return None

def get_url(url: str) -> any:
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  [WARN] GET {url} error: {e}", file=sys.stderr)
        return None

# ─── Step 1: Fetch all fills for both wallets ─────────────────────────────────

def fetch_all_fills(wallet: str) -> list:
    fills = []
    start_time = 0
    while True:
        batch = hl_post({"type": "userFillsByTime", "user": wallet, "startTime": start_time})
        if not batch:
            break
        fills.extend(batch)
        if len(batch) < 2000:
            break
        # paginate: last fill's time + 1
        last_time = batch[-1].get("time", 0)
        if last_time <= start_time:
            break
        start_time = last_time + 1
    return fills

# ─── Step 2: Separate spot vs perp fills ──────────────────────────────────────

def separate_fills(fills: list):
    spot_fills = [f for f in fills if f.get("coin", "").startswith("@")]
    perp_fills = [f for f in fills if not f.get("coin", "").startswith("@")]
    return spot_fills, perp_fills

# ─── Step 3: Spot cost basis ──────────────────────────────────────────────────

def fetch_spot_meta() -> dict:
    """Returns dict: token_index -> coin_name"""
    meta = hl_post({"type": "spotMeta"})
    if not meta:
        return {}
    mapping = {}
    tokens = meta.get("tokens", [])
    for t in tokens:
        idx = t.get("index")
        name = t.get("name", f"@{idx}")
        if idx is not None:
            mapping[idx] = name
    return mapping

def fetch_all_mids() -> dict:
    mids = hl_post({"type": "allMids"})
    return mids if mids else {}

def fetch_spot_state(wallet: str) -> dict:
    return hl_post({"type": "spotClearinghouseState", "user": wallet}) or {}

def compute_spot_pnl(spot_fills: list, token_map: dict, all_mids: dict) -> dict:
    """
    Returns dict: coin_name -> {
        size, avg_cost, realized_pnl, current_px, current_usd, unrealized_pnl
    }
    """
    # group by coin
    by_coin = defaultdict(list)
    for f in spot_fills:
        by_coin[f["coin"]].append(f)

    results = {}
    for coin_key, fills in by_coin.items():
        # map @N → name
        if coin_key.startswith("@"):
            idx = int(coin_key[1:])
            name = token_map.get(idx, coin_key)
        else:
            name = coin_key

        # sort chronologically
        fills_sorted = sorted(fills, key=lambda x: x.get("time", 0))

        position = 0.0
        total_cost = 0.0
        realized_pnl = 0.0

        for f in fills_sorted:
            sz = float(f.get("sz", 0))
            px = float(f.get("px", 0))
            side = f.get("side", "")
            fee = float(f.get("fee", 0))

            if side == "B":  # buy
                position += sz
                total_cost += px * sz
            elif side == "A":  # sell
                if position > 0:
                    avg_cost = total_cost / position
                    realized_pnl += (px - avg_cost) * sz
                    total_cost -= avg_cost * sz
                    position -= sz
                    if position < 1e-10:
                        position = 0.0
                        total_cost = 0.0

        avg_cost = (total_cost / position) if position > 1e-10 else 0.0

        # current price from allMids
        current_px = 0.0
        mid_key = coin_key  # "@N" format
        if mid_key in all_mids:
            current_px = float(all_mids[mid_key])
        # also try name
        elif name in all_mids:
            current_px = float(all_mids[name])

        current_usd = position * current_px
        unrealized_pnl = (current_px - avg_cost) * position if position > 1e-10 else 0.0

        results[name] = {
            "coin_key": coin_key,
            "size": position,
            "avg_cost": avg_cost,
            "realized_pnl": realized_pnl,
            "current_px": current_px,
            "current_usd": current_usd,
            "unrealized_pnl": unrealized_pnl,
        }
    return results

# ─── Step 4: Perp PnL ─────────────────────────────────────────────────────────

def compute_perp_pnl(perp_fills: list) -> dict:
    realized_pnl = sum(float(f.get("closedPnl", 0)) for f in perp_fills)
    total_fees = sum(float(f.get("fee", 0)) for f in perp_fills)
    return {"realized_pnl": realized_pnl, "total_fees": total_fees}

def fetch_perp_state(wallet: str) -> dict:
    return hl_post({"type": "clearinghouseState", "user": wallet}) or {}

def get_open_unrealized_pnl(perp_state: dict) -> float:
    positions = perp_state.get("assetPositions", [])
    total = 0.0
    for p in positions:
        pos = p.get("position", {})
        upnl = float(pos.get("unrealizedPnl", 0))
        total += upnl
    return total

# ─── Step 5: stETH ────────────────────────────────────────────────────────────

def fetch_steth_transfers(wallet: str) -> list:
    url = (
        f"https://eth.blockscout.com/api/v2/addresses/{wallet}"
        f"/token-transfers?token={STETH}"
    )
    data = get_url(url)
    if not data:
        return []
    return data.get("items", [])

def fetch_steth_price() -> float:
    url = f"https://coins.llama.fi/prices/current/ethereum:{STETH}"
    data = get_url(url)
    if not data:
        return 0.0
    coins = data.get("coins", {})
    key = f"ethereum:{STETH}"
    return float(coins.get(key, {}).get("price", 0.0))

def compute_steth_pnl(transfers: list, wallet: str, current_price: float) -> list:
    """Returns list of rows per inbound transfer."""
    rows = []
    wallet_lower = wallet.lower()
    for t in transfers:
        to_addr = (t.get("to", {}) or {}).get("hash", "").lower()
        if to_addr != wallet_lower:
            continue
        total_val = t.get("total", {}) or {}
        raw_value = total_val.get("value", "0")
        decimals = int(total_val.get("decimals", "18") or 18)
        amount = int(raw_value) / (10 ** decimals)
        ts = t.get("timestamp", "")
        tx_hash = t.get("transaction_hash", "")
        proof_url = f"https://etherscan.io/tx/{tx_hash}" if tx_hash else "n/a"
        # use current price as proxy for cost basis (no historical price available)
        cost_usd = amount * current_price
        current_usd = amount * current_price
        pnl = current_usd - cost_usd  # 0 when using same price as proxy
        rows.append({
            "timestamp": ts,
            "amount": amount,
            "cost_usd": cost_usd,
            "current_usd": current_usd,
            "pnl": pnl,
            "proof_url": proof_url,
        })
    return rows

# ─── Step 6: Vault info ────────────────────────────────────────────────────────

def fetch_vault_equities(wallet: str) -> list:
    data = hl_post({"type": "userVaultEquities", "user": wallet})
    return data if isinstance(data, list) else []

# ─── Step 7: Print ────────────────────────────────────────────────────────────

def fmt(v: float, decimals: int = 4) -> str:
    if abs(v) < 1e-8:
        return "0.00"
    return f"{v:,.{decimals}f}"

def fmt2(v: float) -> str:
    return f"{v:,.2f}"

def main():
    wallets = {"L1": L1, "L3": L3}

    # ── fetch fills ──────────────────────────────────────────────────────────
    all_fills = {}
    for label, addr in wallets.items():
        fills = fetch_all_fills(addr)
        all_fills[label] = fills

    # ── spot meta + mids ─────────────────────────────────────────────────────
    token_map = fetch_spot_meta()
    all_mids = fetch_all_mids()

    # ── spot cost basis ───────────────────────────────────────────────────────
    spot_results = {}
    for label, fills in all_fills.items():
        spot_fills, _ = separate_fills(fills)
        spot_results[label] = compute_spot_pnl(spot_fills, token_map, all_mids)

    # ── also check spot state for current balances / prices ───────────────────
    spot_states = {}
    for label, addr in wallets.items():
        spot_states[label] = fetch_spot_state(addr)

    # Enrich spot results with current prices from spot state where allMids missed
    for label, state in spot_states.items():
        balances = state.get("balances", [])
        # build name→price from spot state if possible
        # spot state has entryNtl and total; price ≈ entryNtl/total (cost basis only)
        # better: use allMids already fetched
        pass

    # ── perp PnL ──────────────────────────────────────────────────────────────
    perp_summaries = {}
    perp_states = {}
    for label, fills in all_fills.items():
        _, perp_fills = separate_fills(fills)
        perp_summaries[label] = compute_perp_pnl(perp_fills)
    for label, addr in wallets.items():
        perp_states[label] = fetch_perp_state(addr)

    # ── stETH ─────────────────────────────────────────────────────────────────
    steth_price = fetch_steth_price()
    steth_transfers = fetch_steth_transfers(L3)
    steth_rows = compute_steth_pnl(steth_transfers, L3, steth_price)

    # aggregate stETH total inbound
    steth_total = sum(r["amount"] for r in steth_rows)
    steth_cost_total = sum(r["cost_usd"] for r in steth_rows)
    steth_current_total = steth_total * steth_price

    # ── vault equities ────────────────────────────────────────────────────────
    vault_equities = {}
    for label, addr in wallets.items():
        vault_equities[label] = fetch_vault_equities(addr)

    # ═══════════════════════════════════════════════════════════════════════════
    # OUTPUT
    # ═══════════════════════════════════════════════════════════════════════════

    print("\n=== SPOT TABLE ===")
    print(f"{'Wallet':<6} {'Coin':<12} {'Size':>14} {'Avg cost':>12} {'Current px':>12} {'Current USD':>14} {'Unrealized PnL':>16}")
    print("-" * 92)

    spot_unrealized = {"L1": 0.0, "L3": 0.0}
    for label in ["L1", "L3"]:
        rows = spot_results.get(label, {})
        if not rows:
            print(f"{label:<6} {'(no spot fills)'}")
            continue
        for coin, d in sorted(rows.items()):
            if d["size"] < 1e-8 and d["unrealized_pnl"] == 0:
                continue
            # USDC shown at $1
            if coin == "USDC":
                cp = 1.0
                cur_usd = d["size"]
                upnl = 0.0
            else:
                cp = d["current_px"]
                cur_usd = d["current_usd"]
                upnl = d["unrealized_pnl"]
            spot_unrealized[label] += upnl
            print(
                f"{label:<6} {coin:<12} {fmt(d['size'], 4):>14} "
                f"{fmt2(d['avg_cost']):>12} {fmt2(cp):>12} "
                f"{fmt2(cur_usd):>14} {fmt2(upnl):>16}"
            )

    print("\n=== PERP SUMMARY ===")
    print(f"{'Wallet':<6} {'Realized PnL':>16} {'Σ fees':>12} {'Open Unrealized':>18} {'Net (real-fees)':>18}")
    print("-" * 74)

    perp_realized = {"L1": 0.0, "L3": 0.0}
    perp_open_upnl = {"L1": 0.0, "L3": 0.0}
    for label in ["L1", "L3"]:
        s = perp_summaries.get(label, {})
        rpnl = s.get("realized_pnl", 0.0)
        fees = s.get("total_fees", 0.0)
        open_upnl = get_open_unrealized_pnl(perp_states.get(label, {}))
        net = rpnl - fees
        perp_realized[label] = rpnl
        perp_open_upnl[label] = open_upnl
        print(
            f"{label:<6} {fmt2(rpnl):>16} {fmt2(fees):>12} "
            f"{fmt2(open_upnl):>18} {fmt2(net):>18}"
        )

    print("\n=== HL VAULT ===")
    print(f"{'Wallet':<6} {'Vault':<42} {'Current USD':>14} {'Deposited':>12} {'Accrued':>12}")
    print("-" * 90)

    vault_total = {"L1": 0.0, "L3": 0.0}
    any_vault = False
    for label in ["L1", "L3"]:
        veq = vault_equities.get(label, [])
        if not veq:
            continue
        for v in veq:
            vault_addr = v.get("vault", "n/a")
            equity = float(v.get("equity", 0))
            deposited = float(v.get("deposited", 0))
            accrued = equity - deposited
            vault_total[label] += equity
            any_vault = True
            print(
                f"{label:<6} {vault_addr:<42} {fmt2(equity):>14} "
                f"{fmt2(deposited):>12} {fmt2(accrued):>12}"
            )
    if not any_vault:
        print("  (no vault positions found)")

    print("\n=== stETH (L3) ===")
    print(f"{'Acq. date':<22} {'stETH':>12} {'Cost basis USD':>16} {'Current USD':>14} {'PnL':>12} Proof URL")
    print("-" * 110)

    if steth_rows:
        for r in steth_rows:
            ts_short = r["timestamp"][:10] if r["timestamp"] else "unknown"
            print(
                f"{ts_short:<22} {fmt(r['amount'], 6):>12} {fmt2(r['cost_usd']):>16} "
                f"{fmt2(r['current_usd']):>14} {fmt2(r['pnl']):>12}  {r['proof_url']}"
            )
        print(f"  stETH price used: ${fmt2(steth_price)} (DefiLlama, current)")
        print(f"  Note: cost basis = current price proxy (no historical price lookup)")
    else:
        print("  (no inbound stETH transfers found for L3)")

    # ── Totals ────────────────────────────────────────────────────────────────

    print("\n=== TOTALS ===")
    for label in ["L1", "L3"]:
        s_upnl = spot_unrealized[label]
        p_rpnl = perp_realized[label]
        p_upnl = perp_open_upnl[label]
        p_fees = perp_summaries.get(label, {}).get("total_fees", 0.0)
        vt = vault_total[label]
        combined = s_upnl + p_rpnl + p_upnl - p_fees + vt
        print(f"{label}:")
        print(f"  Spot unrealized PnL  : ${fmt2(s_upnl)}")
        print(f"  Perp realized PnL    : ${fmt2(p_rpnl)}")
        print(f"  Perp open unrealized : ${fmt2(p_upnl)}")
        print(f"  Perp fees paid       : ${fmt2(p_fees)}")
        print(f"  Vault equity         : ${fmt2(vt)}")
        print(f"  Combined             : ${fmt2(combined)}")
        if label == "L3":
            print(f"  stETH held           : {fmt(steth_total, 6)} stETH = ${fmt2(steth_current_total)}")

    grand = (
        sum(spot_unrealized.values())
        + sum(perp_realized.values())
        + sum(perp_open_upnl.values())
        - sum(perp_summaries.get(l, {}).get("total_fees", 0) for l in ["L1", "L3"])
        + sum(vault_total.values())
        + steth_current_total
    )
    print(f"Grand total (excl. USDC principal): ${fmt2(grand)}")

    print("\n=== CAVEATS ===")
    caveats = [
        "1. Spot cost basis uses FIFO/avg-cost within each coin (buys accumulated, sells reduce avg).",
        "2. stETH cost basis uses CURRENT price as proxy — no historical ETH price fetched per tx.",
        "3. Perp realized PnL = Σ closedPnl from fills; fees = Σ fee field (may include funding).",
        "4. Current spot prices from HL allMids (mid-market); may differ from mark/last price.",
        "5. Vault equities from userVaultEquities endpoint; accrued = equity - deposited.",
        "6. Fills pagination: batches of 2000; very old fills may be missing if API limit applies.",
        "7. USDC spot position excluded from unrealized PnL (treated as $1.00 stablecoin).",
        "8. Open perp unrealized PnL from clearinghouseState (mark price at query time).",
    ]
    for c in caveats:
        print(c)


if __name__ == "__main__":
    main()
