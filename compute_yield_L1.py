#!/usr/bin/env /Users/engineer/.venv/bin/python3
"""
compute_yield_L1.py — Realized stablecoin/LP yield for wallet L1.

Chains : Optimism, Base, Arbitrum
Windows: 1Y since 2025-06-25 (unix 1750809600)
         2Y since 2024-06-25 (unix 1719273600)

Data sources (keyless):
  - Blockscout tokentx API   → full ERC-20 transfer history
  - DefiLlama coins/block    → block numbers at window timestamps
  - EVM archive RPC          → balanceOf / convertToAssets / getPricePerFullShare
  - DefiLlama coins/prices   → historical USD price for EURC, wUSDR, etc.

Output:
  pnl_L1.md  (current working dir — /tmp writes forbidden by runtime policy)
  compact table + sanity report to stdout
"""

import json, csv, os, sys, time
from urllib.request import urlopen, Request
from urllib.error   import URLError, HTTPError
from collections    import defaultdict
from datetime       import datetime, timezone

# ── Wallet & Windows ──────────────────────────────────────────────────────────
WALLET   = "0x5c1b7a3ab7797e237cc9ec1e30a18048c364174a"
WALLET_L = WALLET.lower()
W1Y_TS   = 1750809600   # 2025-06-25 00:00:00 UTC
W2Y_TS   = 1719273600   # 2024-06-25 00:00:00 UTC
NOW_TS   = int(time.time())

CSV_PATH  = "/tmp/onchain_tokens.csv"          # read-only; may not exist
OUTPUT_MD = os.path.join(os.getcwd(), "pnl_L1.md")

# ── Chain config ──────────────────────────────────────────────────────────────
CHAINS = {
    "optimism": {
        "blockscout": "https://optimism.blockscout.com",
        "rpcs": ["https://mainnet.optimism.io"],
        "llama": "optimism",
    },
    "base": {
        "blockscout": "https://base.blockscout.com",
        "rpcs": ["https://mainnet.base.org",
                 "https://base-mainnet.public.blastapi.io"],
        "llama": "base",
    },
    "arbitrum": {
        "blockscout": "https://arbitrum.blockscout.com",
        "rpcs": ["https://arb1.arbitrum.io/rpc",
                 "https://arbitrum-one.public.blastapi.io"],
        "llama": "arbitrum",
    },
}

# ── Stablecoins per chain (addr_lower → (symbol, face_usd | None)) ─────────
# face_usd=None means we need a historical price lookup
STABLES = {
    "optimism": {
        "0x0b2c639c533813f4aa9d7837caf62653d097ff85": ("USDC",   1.0),
        "0x7f5c764cbc14f9669b88837ca1490cca17c31607": ("USDC.e", 1.0),
        "0x94b008aa00579c1307b0ef2c499ad98a8ce58e58": ("USDT",   1.0),
        "0xda10009cbd5d07dd0cecc66161fc93d7c9000da1": ("DAI",    1.0),
        "0x8c6f28f2f1a3c87f0f938b96d27520d9751ec8d9": ("sUSD",   1.0),
        "0x9485aca5bbbe1a179c7c8bf43aa4d2a1e595e9ab": ("BOB",    1.0),  # USD-pegged
        "0x0a9e2032e47b87bfcb87a31be54b73da7b8b4bc3": ("wUSDR",  None), # price lookup
    },
    "base": {
        "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913": ("USDC",   1.0),
        "0xd9aaec86b65d86f6a7b5b1b0c42ffa531710b6ca": ("USDbC",  1.0),
        "0x50c5725949a6f0c72e6c4a641f24049a917db0cb": ("DAI",    1.0),
        "0x60a3e35cc302bfa44cb288bc5a4f316fdb1adb42": ("EURC",   None), # price lookup
        "0x4200000000000000000000000000000000000006": ("WETH",   None), # not stable; skip
    },
    "arbitrum": {
        "0xaf88d065e77c8cc2239327c5edb3a432268e5831": ("USDC",   1.0),
        "0xff970a61a04b1ca14834a43f5de4533ebddb5cc8": ("USDC.e", 1.0),
        "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9": ("USDT",   1.0),
        "0xda10009cbd5d07dd0cecc66161fc93d7c9000da1": ("DAI",    1.0),
        "0x12275dcb9048680c4be40942ea4d92c74c63b844": ("eUSD",   1.0),  # Lybra eUSD
        "0xa0d69e286b938e21cbf7e51d71f6a4c8918f482f": ("eUSD",   1.0),  # alt addr
        "0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34": ("USDe",   1.0),  # Ethena USDe
    },
}

# Symbols considered non-stable emission rewards
EMISSION_SYMS = {"velo", "aero", "op", "morpho", "hop", "cow", "arb", "crv", "cvx",
                 "safe", "snx", "uni", "comp", "bal", "ldo"}

# Position label hints: (pattern_in_sym_or_name → label)
# More-specific patterns first — first match wins.
POS_HINTS = {
    "optimism": [
        ("mooAaveOpUSDC",       "Beefy mooAaveOpUSDC"),
        ("mooVeloV2BOB-USDC",   "Beefy mooVeloV2BOB-USDC"),
        ("mooVeloV2USDC-USDT",  "Beefy mooVeloV2USDC-USDT"),
        ("mooVeloV2USDC-wUSDR", "Beefy mooVeloV2USDC-wUSDR"),
        ("HOP-LP-USDC",         "Hop HOP-LP-USDC"),
        ("rcow",                "rcowUniswapOpUSDC-sUSD"),
        ("aUSDC",               "Aave aUSDC"),
        ("mooVelo",             "Beefy mooVelo (other)"),
    ],
    "base": [
        ("mooAlienBase",        "Beefy mooAlienBase DAI-USDbC"),
        ("mooAeroEURC",         "Beefy mooAeroEURC-USDC"),
        ("mooAero",             "Beefy mooAero (other)"),
        ("sUSDC",               "Silo sUSDC-wstETH"),
        ("UUSDC",               "Morpho UUSDC"),
        ("MEUSD",               "Morpho MEUSD"),
    ],
    "arbitrum": [
        ("mooCurveEUSD",        "Beefy mooCurveEUSD-USDC"),
        ("mooBeefyUniswapeUSD", "Beefy mooBeefyUniswapeUSD-USDC"),
        ("mooCurve",            "Beefy mooCurve (other)"),
        ("mooUniswap",          "Beefy mooUniswap (other)"),
    ],
}

# ── ABI selectors ─────────────────────────────────────────────────────────────
SEL_BALANCEOF       = "0x70a08231"   # balanceOf(address)
SEL_CONVERT_ASSETS  = "0x07a2d13a"   # convertToAssets(uint256) — ERC-4626
SEL_PRICE_PER_SHARE = "0x77c7b8fc"   # getPricePerFullShare()   — Beefy

# ── HTTP helpers ──────────────────────────────────────────────────────────────
_price_cache: dict = {}

def http_get(url: str, retries: int = 3):
    for attempt in range(retries):
        try:
            req = Request(url, headers={"User-Agent": "yield-calc/1.0"})
            with urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1.5 * (2 ** attempt))
            else:
                print(f"  [WARN] GET failed ({e}): {url[:80]}", file=sys.stderr)
    return None


def rpc_post(url: str, payload: dict, retries: int = 3):
    for attempt in range(retries):
        try:
            data = json.dumps(payload).encode()
            req  = Request(url, data=data,
                           headers={"Content-Type": "application/json",
                                    "User-Agent": "yield-calc/1.0"})
            with urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1.5 * (2 ** attempt))
            else:
                print(f"  [WARN] RPC failed ({e}): {url}", file=sys.stderr)
    return None


def llama_block(llama_chain: str, ts: int):
    data = http_get(f"https://coins.llama.fi/block/{llama_chain}/{ts}")
    return data["height"] if data and "height" in data else None


def llama_price(llama_chain: str, addr: str, ts: int):
    """Cached historical token price in USD from DefiLlama."""
    key = f"{llama_chain}:{addr.lower()}:{ts}"
    if key in _price_cache:
        return _price_cache[key]
    url  = f"https://coins.llama.fi/prices/historical/{ts}/{llama_chain}:{addr.lower()}"
    data = http_get(url)
    price = None
    if data and "coins" in data:
        coin = data["coins"].get(f"{llama_chain}:{addr.lower()}", {})
        price = coin.get("price")
    _price_cache[key] = price
    return price


def pad32(addr: str) -> str:
    return "000000000000000000000000" + addr.lower().replace("0x", "")


def eth_call(rpcs: list, to: str, data_hex: str, block: str):
    """Run eth_call across fallback RPCs; return hex result or None."""
    for rpc in rpcs:
        res = rpc_post(rpc, {"jsonrpc": "2.0", "method": "eth_call",
                             "params": [{"to": to, "data": data_hex}, block], "id": 1})
        if res and res.get("result") not in (None, "0x", "0x0", ""):
            return res["result"]
    return None


def eth_balanceof(rpcs, token, wallet, block_hex) -> int:
    raw = eth_call(rpcs, token, SEL_BALANCEOF + pad32(wallet), block_hex)
    if raw:
        try:
            return int(raw, 16)
        except ValueError:
            pass
    return 0


def eth_convert_assets(rpcs, token, shares: int, block_hex):
    """ERC-4626 convertToAssets(shares) → raw uint256 or None."""
    shares_hex = hex(shares)[2:].zfill(64)
    raw = eth_call(rpcs, token, SEL_CONVERT_ASSETS + shares_hex, block_hex)
    if raw:
        try:
            return int(raw, 16)
        except ValueError:
            pass
    return None


def eth_price_per_share(rpcs, token, block_hex):
    """Beefy getPricePerFullShare() → uint256 (1e18-scaled) or None."""
    raw = eth_call(rpcs, token, SEL_PRICE_PER_SHARE, block_hex)
    if raw:
        try:
            return int(raw, 16)
        except ValueError:
            pass
    return None


def eth_block_number(rpcs) -> int | None:
    for rpc in rpcs:
        res = rpc_post(rpc, {"jsonrpc": "2.0", "method": "eth_blockNumber",
                             "params": [], "id": 1})
        if res and "result" in res:
            try:
                return int(res["result"], 16)
            except ValueError:
                pass
    return None


# ── Transfer fetching ─────────────────────────────────────────────────────────
def fetch_transfers(chain: str) -> list:
    base = CHAINS[chain]["blockscout"]
    url  = (f"{base}/api?module=account&action=tokentx"
            f"&address={WALLET}&sort=asc&page=1&offset=10000")
    data = http_get(url)
    if not data or data.get("status") != "1":
        print(f"  [WARN] tokentx empty for {chain}: {data}", file=sys.stderr)
        return []
    rows = data.get("result", [])
    print(f"  {chain}: {len(rows)} token-transfer rows")
    return rows


# ── Receipt token discovery ───────────────────────────────────────────────────
def load_csv_tokens(wallet_l: str) -> dict:
    """chain → {addr_lower → (label, decimals_str)}"""
    result: dict = {}
    if not os.path.exists(CSV_PATH):
        return result
    print(f"  Reading {CSV_PATH}…")
    with open(CSV_PATH, newline="") as f:
        for row in csv.DictReader(f):
            if row.get("wallet", "").lower() != wallet_l:
                continue
            ch    = row.get("chain", "").lower()
            addr  = row.get("token_address", row.get("contract_address", "")).lower()
            label = row.get("label", row.get("symbol", addr[:10]))
            dec   = row.get("decimals", "18")
            result.setdefault(ch, {})[addr] = (label, dec)
    n = sum(len(v) for v in result.values())
    print(f"  CSV: {n} tokens loaded for {wallet_l}")
    return result


def discover_receipt_tokens(chain: str, transfers: list,
                             stables_map: dict, csv_map: dict) -> dict:
    """
    Returns {addr_lower → (label, decimals_str)} for receipt/LP tokens on chain.
    Priority: CSV > symbol/name pattern matching.
    """
    rt: dict = {}

    # CSV-sourced first
    for addr, (label, dec) in csv_map.get(chain, {}).items():
        if addr not in stables_map:
            rt[addr] = (label, dec)

    hints = POS_HINTS.get(chain, [])

    # Build seen-token index from transfer rows
    seen: dict = {}  # addr → (sym, name, dec)
    for tx in transfers:
        a = tx["contractAddress"].lower()
        if a not in seen:
            seen[a] = (tx.get("tokenSymbol", ""),
                       tx.get("tokenName", ""),
                       tx.get("tokenDecimal", "18"))

    for addr, (sym, name, dec) in seen.items():
        if addr in stables_map or addr in rt:
            continue
        sym_l  = sym.lower()
        name_l = name.lower()
        for pattern, label in hints:
            if pattern.lower() in sym_l or pattern.lower() in name_l:
                rt[addr] = (label, dec)
                print(f"    discovered: {addr[:14]}… = {label} ({sym})")
                break

    return rt


# ── USD value helpers ─────────────────────────────────────────────────────────
def stable_usd(chain: str, addr_l: str, raw: int, dec: int,
               ts: int, stables_map: dict) -> tuple:
    """(usd_float | None, symbol | None, note)"""
    if addr_l not in stables_map:
        return None, None, "not a known stable"
    sym, face = stables_map[addr_l]
    if sym in ("WETH", "cbBTC"):            # non-stable — skip
        return None, sym, "non-stable asset"
    amt = raw / 10 ** dec
    if face is not None:
        return amt * face, sym, "face"
    price = llama_price(CHAINS[chain]["llama"], addr_l, ts)
    if price:
        return amt * price, sym, f"llama@{datetime.utcfromtimestamp(ts).date()}"
    return None, sym, "UNPRICED"


def receipt_usd(chain: str, token_addr: str, decimals: int,
                rpcs: list, block_hex: str) -> tuple:
    """
    Best-effort USD value of wallet's receipt-token balance at block_hex.
    Returns (usd, method_note).

    Priority:
      1. ERC-4626 convertToAssets(balance) — result in underlying asset raw units.
         Sane underlying decimals probed: 6 then 18.
      2. Beefy getPricePerFullShare() — 1e18-scaled LP per share.
         Beefy moo tokens are ALWAYS 18-dec; balance/1e18 = share count.
         LP units treated as $1 (stable pool assumption).
      3. Balance × $1 face-value fallback (uses declared `decimals`).
    """
    balance = eth_balanceof(rpcs, token_addr, WALLET, block_hex)
    if balance == 0:
        return 0.0, "balance=0"

    # --- ERC-4626 convertToAssets ---
    assets_raw = eth_convert_assets(rpcs, token_addr, balance, block_hex)
    if assets_raw and assets_raw > 0:
        for d in (6, 18):
            v = assets_raw / 10 ** d
            if 1e-4 <= v <= 1e9:
                return v, f"convertToAssets/{d}dec"

    # --- Beefy getPricePerFullShare ---
    # Beefy moo tokens are ALWAYS 18 decimals; getPricePerFullShare() returns
    # uint256 scaled 1e18 meaning "1e18 units = 1 LP token".
    pps = eth_price_per_share(rpcs, token_addr, block_hex)
    if pps and pps > 0:
        shares_float = balance / 1e18          # correct for all Beefy moo tokens
        lp_amount    = shares_float * (pps / 1e18)
        if 1e-4 <= lp_amount <= 1e9:
            return lp_amount, "getPricePerFullShare×$1(est)"

    # --- Fallback: face value ---
    return balance / 10 ** decimals, "balance×$1(fallback)"


# ── Core PnL engine ───────────────────────────────────────────────────────────
def compute_pnl(chain: str, label: str, token_addr: str, decimals_str: str,
                tbh: dict,        # transfers_by_hash[chain]
                stables_map: dict, rpcs: list, blocks: dict) -> dict | None:
    """
    Compute realized + unrealized PnL for one receipt token.

    blocks = {"w1y": int|None, "w2y": int|None, "now": int|None}
    Returns rich result dict or None if token has no transfers for L1.
    """
    token_l  = token_addr.lower()
    decimals = int(decimals_str)

    # Collect all L1-relevant transfers of this token (flatten tbh)
    my_txs = [tx for txs in tbh.values() for tx in txs
              if tx["contractAddress"].lower() == token_l
              and (tx["to"].lower() == WALLET_L or tx["from"].lower() == WALLET_L)]
    my_txs.sort(key=lambda x: int(x["blockNumber"]))

    if not my_txs:
        return None

    entries: list = []
    exits:   list = []

    for tx in my_txs:
        ts_   = int(tx["timeStamp"])
        h     = tx["hash"].lower()
        blk   = int(tx["blockNumber"])
        dstr  = datetime.fromtimestamp(ts_, tz=timezone.utc).strftime("%Y-%m-%d")
        is_in = tx["to"].lower() == WALLET_L
        same  = tbh.get(h, [])

        if is_in:
            # ── ENTRY: find stable outflows from L1 in same tx ──────────────
            cost_usd, matched, has_match = 0.0, [], False
            for oth in same:
                if oth["from"].lower() != WALLET_L:
                    continue
                a = oth["contractAddress"].lower()
                if a == token_l:
                    continue
                usd, sym, note = stable_usd(chain, a, int(oth["value"]),
                                            int(oth["tokenDecimal"]), ts_, stables_map)
                if sym is None:
                    continue
                if usd is not None:
                    cost_usd += usd
                    matched.append(f"{int(oth['value'])/10**int(oth['tokenDecimal']):.4f} {sym} (${usd:.2f}) [{note}]")
                    has_match = True
                else:
                    matched.append(f"UNPRICED {int(oth['value'])/10**int(oth['tokenDecimal']):.4f} {sym}")
            entries.append({"hash": h, "date": dstr, "ts": ts_, "block": blk,
                            "cost_in": cost_usd, "matched": matched,
                            "unmatched": not has_match})
        else:
            # ── EXIT: find stable inflows to L1 in same tx ──────────────────
            proc_usd, matched, has_match = 0.0, [], False
            for oth in same:
                if oth["to"].lower() != WALLET_L:
                    continue
                a = oth["contractAddress"].lower()
                if a == token_l:
                    continue
                usd, sym, note = stable_usd(chain, a, int(oth["value"]),
                                            int(oth["tokenDecimal"]), ts_, stables_map)
                if sym is None:
                    continue
                if usd is not None:
                    proc_usd += usd
                    matched.append(f"{int(oth['value'])/10**int(oth['tokenDecimal']):.4f} {sym} (${usd:.2f}) [{note}]")
                    has_match = True
                else:
                    matched.append(f"UNPRICED {int(oth['value'])/10**int(oth['tokenDecimal']):.4f} {sym}")
            exits.append({"hash": h, "date": dstr, "ts": ts_, "block": blk,
                          "proceeds_out": proc_usd, "matched": matched,
                          "unmatched": not has_match})

    pos_hashes = {e["hash"] for e in entries} | {e["hash"] for e in exits}

    # ── Harvest / reward detection ────────────────────────────────────────────
    # Stable inflows NOT in entry/exit hashes, where the sender is the receipt
    # token contract itself OR the same tx contains a transfer of this receipt
    # token (i.e., the transaction is protocol-originated, not a swap/bridge).
    rewards:   list = []
    emissions: list = []

    for h, txs in tbh.items():
        if h in pos_hashes:
            continue
        # Check if this tx involves our receipt token at all
        tx_has_rt = any(t["contractAddress"].lower() == token_l for t in txs)

        for tx in txs:
            if tx["to"].lower() != WALLET_L:
                continue
            sender_l = tx["from"].lower()
            # Only count if associated with our protocol
            if sender_l != token_l and not tx_has_rt:
                continue

            a      = tx["contractAddress"].lower()
            ts_    = int(tx["timeStamp"])
            dstr   = datetime.fromtimestamp(ts_, tz=timezone.utc).strftime("%Y-%m-%d")
            usd, sym, note = stable_usd(chain, a, int(tx["value"]),
                                        int(tx["tokenDecimal"]), ts_, stables_map)
            if sym is not None:
                rewards.append({"hash": h, "date": dstr, "ts": ts_,
                                "symbol": sym, "amount": int(tx["value"])/10**int(tx["tokenDecimal"]),
                                "usd": usd, "note": note, "from": sender_l})
            else:
                sym_tx = tx.get("tokenSymbol", "").strip()
                if sym_tx.lower() in EMISSION_SYMS or sender_l == token_l or tx_has_rt:
                    dec_ = int(tx.get("tokenDecimal", "18"))
                    emissions.append({"hash": h, "date": dstr, "ts": ts_,
                                      "symbol": sym_tx,
                                      "amount": int(tx["value"]) / 10 ** dec_,
                                      "addr": a, "from": sender_l})

    # ── Current (open-position) value ─────────────────────────────────────────
    now_hex = hex(blocks["now"]) if blocks.get("now") else "latest"
    cur_val, cur_meth = receipt_usd(chain, token_addr, decimals, rpcs, now_hex)
    is_open = cur_val > 0

    # ── Basis at each window start ────────────────────────────────────────────
    # Compute provisional total cost so we can threshold-detect archive failures
    _pre_cost = sum(e["cost_in"] for e in entries)

    def basis_at(key, window_ts):
        blk = blocks.get(key)
        if not blk:
            return 0.0, "no block", False
        v, m = receipt_usd(chain, token_addr, decimals, rpcs, hex(blk))
        # Was this position open at window_ts?
        entries_before  = [e for e in entries if e["ts"] < window_ts]
        exits_before    = [e for e in exits   if e["ts"] < window_ts]
        exits_in_or_aft = [e for e in exits   if e["ts"] >= window_ts]
        expected_open   = bool(entries_before) and (
            not exits_before or bool(exits_in_or_aft)
        )
        # Archive failure: either returned $0 exactly, or returned a suspiciously
        # tiny value (< $1) when we paid > $100 for the position.
        archive_suspect = expected_open and (
            v == 0.0 or (v < 1.0 and _pre_cost > 100)
        )
        return v, m, archive_suspect

    basis_1y, meth_1y, archive_1y = basis_at("w1y", W1Y_TS)
    basis_2y, meth_2y, archive_2y = basis_at("w2y", W2Y_TS)

    # ── PnL ───────────────────────────────────────────────────────────────────
    total_cost     = sum(e["cost_in"]     for e in entries)
    total_proceeds = sum(e["proceeds_out"]for e in exits)
    total_rewards  = sum(r["usd"] for r in rewards if r["usd"] is not None)

    lifetime_pnl = total_proceeds + total_rewards + cur_val - total_cost

    def windowed_pnl(window_ts: int, basis: float) -> float:
        c = sum(e["cost_in"]      for e in entries if e["ts"] >= window_ts)
        p = sum(e["proceeds_out"] for e in exits   if e["ts"] >= window_ts)
        r = sum(rw["usd"] for rw in rewards
                if rw["ts"] >= window_ts and rw["usd"] is not None)
        return p + r + cur_val - c - basis

    pnl_1y = windowed_pnl(W1Y_TS, basis_1y)
    pnl_2y = windowed_pnl(W2Y_TS, basis_2y)

    first_in = min((e["date"] for e in entries), default="N/A")
    all_exit_dates = [e["date"] for e in exits]
    if all_exit_dates:
        last_out = max(all_exit_dates)
    elif is_open:
        last_out = "OPEN"
    else:
        last_out = "N/A"

    return {
        "chain": chain, "label": label, "token_addr": token_addr,
        "decimals": decimals, "entries": entries, "exits": exits,
        "rewards": rewards, "emissions": emissions,
        "is_open": is_open, "cur_val": cur_val, "cur_meth": cur_meth,
        "basis_1y": basis_1y, "meth_1y": meth_1y, "archive_1y": archive_1y,
        "basis_2y": basis_2y, "meth_2y": meth_2y, "archive_2y": archive_2y,
        "total_cost": total_cost, "total_proceeds": total_proceeds,
        "total_rewards": total_rewards,
        "lifetime_pnl": lifetime_pnl, "pnl_1y": pnl_1y, "pnl_2y": pnl_2y,
        "first_in": first_in, "last_out": last_out,
    }


# ── Formatting ────────────────────────────────────────────────────────────────
def fusd(v) -> str:
    if v is None:
        return "  N/A    "
    return f"${v:+10,.2f}" if v != 0 else "  $0.00   "


# ── Markdown report ───────────────────────────────────────────────────────────
def write_md(results: list, unmatched_all: list, path: str):
    L = []
    L.append("# Realized Yield — L1 Wallet PnL Trace\n\n")
    L.append(f"**Wallet:** `{WALLET}`  \n")
    L.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}  \n")
    L.append(f"**1Y window start:** 2025-06-25 (unix {W1Y_TS})  \n")
    L.append(f"**2Y window start:** 2024-06-25 (unix {W2Y_TS})  \n\n")
    L.append("---\n\n")

    for r in results:
        L.append(f"## {r['label']} — {r['chain']}\n\n")
        L.append(f"- **Token:** `{r['token_addr']}`  \n")
        L.append(f"- **Status:** {'OPEN' if r['is_open'] else 'CLOSED'}  \n")
        L.append(f"- **First entry:** {r['first_in']}  |  **Last exit:** {r['last_out']}  \n")
        L.append(f"- **Current value:** ${r['cur_val']:,.2f} ({r['cur_meth']})  \n\n")

        # Entries
        L.append("### Entries\n\n")
        if not r["entries"]:
            L.append("_none_\n\n")
        for e in r["entries"]:
            flag  = " ⚠️ UNMATCHED" if e["unmatched"] else ""
            strs  = "; ".join(e["matched"]) if e["matched"] else "none"
            L.append(f"- `{e['hash'][:18]}…` {e['date']} | "
                     f"cost_in: ${e['cost_in']:,.2f} | stable_out: {strs}{flag}\n")
        L.append("\n")

        # Exits
        L.append("### Exits\n\n")
        if not r["exits"]:
            L.append("_none (position still open)_\n\n")
        for e in r["exits"]:
            flag = " ⚠️ UNMATCHED" if e["unmatched"] else ""
            strs = "; ".join(e["matched"]) if e["matched"] else "none"
            L.append(f"- `{e['hash'][:18]}…` {e['date']} | "
                     f"proceeds: ${e['proceeds_out']:,.2f} | stable_in: {strs}{flag}\n")
        L.append("\n")

        # Harvest rewards
        if r["rewards"]:
            L.append("### Harvest Rewards (stable)\n\n")
            for rw in r["rewards"]:
                usd_s = f"${rw['usd']:,.2f}" if rw["usd"] is not None else "UNPRICED"
                L.append(f"- `{rw['hash'][:18]}…` {rw['date']} | "
                         f"{rw['amount']:.4f} {rw['symbol']} = {usd_s} [{rw['note']}] "
                         f"| from `{rw['from'][:16]}…`\n")
            L.append("\n")

        # Emissions
        if r["emissions"]:
            L.append("### Emission Rewards (non-stable — UNPRICED unless swapped)\n\n")
            for em in r["emissions"]:
                L.append(f"- `{em['hash'][:18]}…` {em['date']} | "
                         f"{em['amount']:.4f} {em['symbol']} "
                         f"(`{em['addr'][:16]}…`) | from `{em['from'][:16]}…`\n")
            L.append("\n")

        # PnL table
        L.append("### PnL Summary\n\n")
        L.append("| Metric | Value |\n|---|---|\n")
        L.append(f"| Total cost_in        | ${r['total_cost']:,.2f} |\n")
        L.append(f"| Total proceeds_out   | ${r['total_proceeds']:,.2f} |\n")
        L.append(f"| Stable harvest total | ${r['total_rewards']:,.2f} |\n")
        L.append(f"| Current value (open) | ${r['cur_val']:,.2f} ({r['cur_meth']}) |\n")
        L.append(f"| **Lifetime PnL**     | **${r['lifetime_pnl']:+,.2f}** |\n")
        L.append(f"| Basis @ 1Y start     | ${r['basis_1y']:,.2f} ({r['meth_1y']})"
                 f"{'  ⚠️ ARCHIVE SUSPECT' if r['archive_1y'] else ''} |\n")
        L.append(f"| **1Y PnL**           | **${r['pnl_1y']:+,.2f}**"
                 f"{'  ← likely overstated' if r['archive_1y'] else ''} |\n")
        L.append(f"| Basis @ 2Y start     | ${r['basis_2y']:,.2f} ({r['meth_2y']})"
                 f"{'  ⚠️ ARCHIVE SUSPECT' if r['archive_2y'] else ''} |\n")
        L.append(f"| **2Y PnL**           | **${r['pnl_2y']:+,.2f}**"
                 f"{'  ← likely overstated' if r['archive_2y'] else ''} |\n")
        L.append("\n---\n\n")

    # Unmatched events appendix
    if unmatched_all:
        L.append("## Appendix: Unmatched Entry / Exit Events\n\n")
        L.append("No stablecoin was found leaving/entering L1 in the same tx.  \n")
        L.append("Likely cause: zap via router, ETH→stable→deposit, or multi-hop.  \n")
        L.append("cost_in recorded as $0 for these; review manually.\n\n")
        L.append("| Chain | Position | Hash | Date | Direction |\n|---|---|---|---|---|\n")
        for u in unmatched_all:
            L.append(f"| {u['chain']} | {u['label']} | `{u['hash'][:20]}…` "
                     f"| {u['date']} | {u['dir']} |\n")
        L.append("\n")

    with open(path, "w") as f:
        f.write("".join(L))
    print(f"\n  [✓] Detailed trace → {path}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    sep = "=" * 78
    print(sep)
    print(f"  Realized Yield Calculator — {WALLET}")
    print(sep)

    # ── 1. Window block numbers ───────────────────────────────────────────────
    print("\n[1/5] Fetching window block numbers…")
    chain_blocks: dict = {}

    for chain, cfg in CHAINS.items():
        llama = cfg["llama"]
        b1y   = llama_block(llama, W1Y_TS)
        b2y   = llama_block(llama, W2Y_TS)
        now   = eth_block_number(cfg["rpcs"])
        chain_blocks[chain] = {"w1y": b1y, "w2y": b2y, "now": now}
        print(f"  {chain:12s}: 1Y={b1y}  2Y={b2y}  now={now}")
        time.sleep(0.3)

    # Spec hint: Base 1Y ≈ 32_010_127
    if not chain_blocks["base"].get("w1y"):
        chain_blocks["base"]["w1y"] = 32_010_127
        print("  base: using hint 1Y=32010127")

    # ── 2. Token transfer history ─────────────────────────────────────────────
    print("\n[2/5] Fetching ERC-20 transfer history…")
    all_txs: dict = {}
    for chain in CHAINS:
        all_txs[chain] = fetch_transfers(chain)
        time.sleep(0.8)

    # Build hash → [rows] index per chain
    tbh: dict = {}   # chain → {hash_lower → [rows]}
    for chain, rows in all_txs.items():
        idx: dict = defaultdict(list)
        for tx in rows:
            idx[tx["hash"].lower()].append(tx)
        tbh[chain] = dict(idx)

    # ── 3. Identify receipt tokens ────────────────────────────────────────────
    print("\n[3/5] Identifying receipt tokens…")
    csv_map = load_csv_tokens(WALLET_L)

    receipt: dict = {}   # chain → {addr → (label, dec_str)}
    for chain in CHAINS:
        stables_map = STABLES.get(chain, {})
        receipt[chain] = discover_receipt_tokens(
            chain, all_txs[chain], stables_map, csv_map)
        n = len(receipt[chain])
        if n:
            print(f"  {chain}: {n} receipt token(s) identified")
        else:
            print(f"  {chain}: 0 receipt tokens — nothing to compute")

    # ── 4. Compute PnL per position ───────────────────────────────────────────
    print("\n[4/5] Computing PnL per position (RPC calls may take a minute)…")
    results:       list = []
    unmatched_all: list = []

    for chain, rt in receipt.items():
        stables_map = STABLES.get(chain, {})
        rpcs        = CHAINS[chain]["rpcs"]
        blks        = chain_blocks[chain]

        for token_addr, (label, dec_str) in rt.items():
            print(f"  {chain:10s} {label}")
            r = compute_pnl(chain, label, token_addr, dec_str,
                            tbh[chain], stables_map, rpcs, blks)
            if r is None:
                print(f"           → no L1 transfers found; skipping")
                continue
            results.append(r)

            for e in r["entries"]:
                if e["unmatched"]:
                    unmatched_all.append({"chain": chain, "label": label,
                                          "hash": e["hash"], "date": e["date"],
                                          "dir": "ENTRY"})
            for e in r["exits"]:
                if e["unmatched"]:
                    unmatched_all.append({"chain": chain, "label": label,
                                          "hash": e["hash"], "date": e["date"],
                                          "dir": "EXIT"})
            time.sleep(0.2)

    # ── 5. Output ─────────────────────────────────────────────────────────────
    print("\n[5/5] Writing output…")
    write_md(results, unmatched_all, OUTPUT_MD)

    # ── Compact table ─────────────────────────────────────────────────────────
    print()
    print(sep)
    hdr = (f"{'Position':<36} {'Chain':<10} {'First In':<11} {'Last Out':<11} "
           f"{'St':<6} {'Lifetime':>12} {'1Y PnL':>14} {'2Y PnL':>14}")
    print(hdr)
    print("-" * 85)

    total_1y = total_2y = 0.0
    archive_flags = []
    for r in sorted(results, key=lambda x: (x["chain"], x["label"])):
        label_s  = (r["label"][:33] + "…") if len(r["label"]) > 34 else r["label"]
        status   = "OPEN" if r["is_open"] else "CLSD"
        flag_1y  = "⚠" if r["archive_1y"] else " "
        flag_2y  = "⚠" if r["archive_2y"] else " "
        pnl_1y_s = f"{r['pnl_1y']:>+12,.2f}{flag_1y}"
        pnl_2y_s = f"{r['pnl_2y']:>+12,.2f}{flag_2y}"
        line = (f"{label_s:<36} {r['chain']:<10} {r['first_in']:<11} {r['last_out']:<11} "
                f"{status:<6} {r['lifetime_pnl']:>+12,.2f} {pnl_1y_s:>14} {pnl_2y_s:>14}")
        print(line)
        total_1y += r["pnl_1y"]
        total_2y += r["pnl_2y"]
        if r["archive_1y"]:
            archive_flags.append((r["label"], r["chain"], "1Y", r["pnl_1y"],
                                  r["total_cost"], r["first_in"]))
        if r["archive_2y"]:
            archive_flags.append((r["label"], r["chain"], "2Y", r["pnl_2y"],
                                  r["total_cost"], r["first_in"]))

    print("-" * 85)
    print(f"{'SUBTOTAL':<36} {'':10} {'':11} {'':11} {'':6} "
          f"{'':>12} {total_1y:>+12,.2f}{'':>2} {total_2y:>+12,.2f}")
    print(sep)
    print("⚠ = archive RPC failure suspected (basis=$0 but position was open at window start)")
    print("  Windowed PnL for ⚠ rows equals gross proceeds — subtract entry cost to correct.")

    # ── Unpriced emissions ────────────────────────────────────────────────────
    all_emissions = [{"chain": r["chain"], "label": r["label"], **em}
                     for r in results for em in r["emissions"]]
    if all_emissions:
        print("\nUNPRICED EMISSION REWARDS (not counted in PnL unless swapped to stable):")
        for em in all_emissions:
            print(f"  {em['label']} ({em['chain']}): "
                  f"{em['amount']:.4f} {em['symbol']}  on {em['date']}")
    else:
        print("\nNo unpriced emission rewards detected.")

    # ── Sanity checks ─────────────────────────────────────────────────────────
    print("\n[SANITY]")
    issues = []
    for r in results:
        # Archive failure: basis=$0 but position was provably open
        if r["archive_1y"]:
            issues.append(
                f"  ARCHIVE FAIL  {r['label']} ({r['chain']}) 1Y: basis=$0 but "
                f"position open {r['first_in']}→{r['last_out']}. "
                f"1Y PnL ({r['pnl_1y']:+,.2f}) = gross proceeds; "
                f"true 1Y ≈ lifetime ({r['lifetime_pnl']:+,.2f})."
            )
        if r["archive_2y"]:
            issues.append(
                f"  ARCHIVE FAIL  {r['label']} ({r['chain']}) 2Y: basis=$0 but "
                f"position open at 2Y start. "
                f"2Y PnL ({r['pnl_2y']:+,.2f}) overstated; "
                f"true 2Y ≈ lifetime ({r['lifetime_pnl']:+,.2f})."
            )
        # Legitimate 1Y > lifetime (pre-window loss, not an archive failure)
        if (r["pnl_1y"] > r["lifetime_pnl"] + 0.01
                and not r["archive_1y"] and not r["archive_2y"]):
            issues.append(
                f"  NOTE (legit)  {r['label']}: 1Y PnL ({r['pnl_1y']:+,.2f}) > "
                f"lifetime ({r['lifetime_pnl']:+,.2f}) — position lost value before "
                f"1Y start; basis is lower than original cost."
            )
        # All entries unmatched
        if r["total_cost"] == 0 and r["entries"]:
            issues.append(
                f"  WARN UNMATCHED {r['label']} ({r['chain']}): cost_in=$0 — "
                f"all {len(r['entries'])} entries unmatched (zap/router). "
                f"Lifetime PnL unreliable."
            )

    if unmatched_all:
        print(f"  UNMATCHED ({len(unmatched_all)} events — cost/proceeds recorded as $0):")
        for u in unmatched_all:
            print(f"    {u['chain']:10s} {u['label']:35s} `{u['hash'][:22]}…` "
                  f"{u['date']}  {u['dir']}")
    if issues:
        for i in issues:
            print(i)
    if not issues and not unmatched_all:
        print("  All checks pass — no anomalies.")

    print(f"\n[DONE] {len(results)} positions processed. "
          f"Report: {OUTPUT_MD}")


if __name__ == "__main__":
    main()
