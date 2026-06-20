#!/usr/bin/env python3
"""
Fetch live APYs for DeFi protocols in the crypto portfolio, plus the best
available stablecoin pools from DeFiLlama for the agent to reason about.
No API key required. Sources:
  - Morpho Blue: blue-api.morpho.org/graphql      (Base + ETH vaults)
  - DeFiLlama:  yields.llama.fi/pools             (Maple Syrup, LIDO, ExtraFi XLend, Avantis + pool discovery)
  - Ethena:     ethena.fi/api/yields/...           (sUSDe staking yield)
  - Hyperliquid: api.hyperliquid.xyz/info          (HLP vault APR via userVaultEquities)

Output:
  1. Live portfolio APYs (Morpho, DeFiLlama, Ethena, Hyperliquid)
  2. Top ~20 trusted, single-asset, no-IL USDC/stablecoin pools on Base and
     Ethereum from DeFiLlama, sorted by APY descending — for the agent to do
     recommendation reasoning (it knows gas costs, positions, risk tolerance, etc.)

Usage:
  python3 fetch_apys.py
"""

import json
import sys
import urllib.request

# Trusted protocols — audited, battle-tested, won't rug.
# Exact-match against DeFiLlama project slug (no substring matching).
TRUSTED_PROTOCOLS = {
    "morpho-blue", "morpho", "aave-v3", "aave", "maple",
    "fluid", "fluid-lending",
    "compound-v3", "spark", "avantis",
    "euler-v2", "moonwell", "seamless-protocol",
    "extra-finance-xlend", "steakhouse",
}

# Projects excluded from AVAILABLE POOLS even if in a trusted protocol family.
# These are C3/C4 risk-tier or otherwise DO NOT RECOMMEND per SKILL.md.
EXCLUDED_PROJECTS = {
    "fluid-lite",  # leveraged loop on synthetics; $21M bad debt March 2026
}

# Minimum TVL to surface a pool in the available-pools table
MIN_TVL_M = 1

# How many pools to show per chain
TOP_N = 20

def fetch(url, method="GET", data=None, headers=None, timeout=30):
    req = urllib.request.Request(url, method=method)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    if data:
        req.data = json.dumps(data).encode()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

def morpho_apys():
    """Query Morpho Blue GraphQL for vault APYs (Base + ETH mainnet)."""
    query = {
        "query": "{ vaults(first:1000, where:{chainId_in:[1,8453]}) { items { name chain { id } address state { netApy } } } }"
    }
    result = fetch(
        "https://blue-api.morpho.org/graphql",
        method="POST",
        data=query,
        headers={"Content-Type": "application/json"}
    )
    if "error" in result or "data" not in result:
        return {"error": result.get("error", "unknown")}

    # ExtraFi XLend is NOT a MetaMorpho vault — sourced from DeFiLlama instead.
    name_map = {
        "seamless usdc vault": "morpho_seamless_usdc_base",
        "universal usdc": "morpho_universal_usdc_base",
        "morpho eusd": "morpho_eusd_base",
        "gauntlet eusd core": "morpho_eusd_eth",
    }
    out = {}
    for v in result["data"]["vaults"]["items"]:
        name_lower = v["name"].lower().strip()
        state = v.get("state") or {}
        raw_apy = state.get("netApy")  # None = missing data; 0.0 = genuinely idle
        for pattern, key in name_map.items():
            if pattern in name_lower:
                out[key] = None if raw_apy is None else round(raw_apy * 100, 2)
                break
    return out

def defi_llama_apys():
    """Single DeFiLlama fetch for portfolio APYs + pool discovery data."""
    result = fetch("https://yields.llama.fi/pools", timeout=45)
    if "error" in result or "data" not in result:
        return {"error": result.get("error", "fetch failed")}, []

    portfolio_apys = {}
    all_pools = []

    for p in result["data"]:
        proj = (p.get("project") or "").lower()
        sym = (p.get("symbol") or "").lower()
        chain = (p.get("chain") or "").lower()
        meta = (p.get("poolMeta") or "").lower()
        apy = round(p.get("apy") or 0, 2)
        tvl = p.get("tvlUsd") or 0

        # --- Portfolio positions ---
        if "maple" in proj and "usdc" in sym and "syrup" in meta:
            portfolio_apys["maple_syrup_usdc"] = apy
        elif "maple" in proj and "usdt" in sym and "syrup" in meta:
            portfolio_apys["maple_syrup_usdt"] = apy
        elif "lido" in proj and "steth" in sym and chain == "ethereum":
            portfolio_apys["lido_steth"] = apy
        elif proj == "extra-finance-xlend" and "usdc" in sym and chain == "base":
            portfolio_apys["extrafi_xlend_usdc_base"] = apy
        elif "avantis" in proj and "usdc" in sym and chain == "base":
            portfolio_apys["avantis_junior_usdc"] = apy

        # --- Pool discovery candidates (stable, single-asset, no-IL, trusted, Base or ETH) ---
        # Exact-match on slug (not substring) to prevent "fluid" matching "fluid-lite", etc.
        is_trusted = proj in TRUSTED_PROTOCOLS and proj not in EXCLUDED_PROJECTS
        # Normalize chain to title-case so print_pools_section comparison ("Base"/"Ethereum") works
        chain_display = {"base": "Base", "ethereum": "Ethereum"}.get(chain, p.get("chain", ""))
        if (chain in ["base", "ethereum"]
                and p.get("stablecoin")
                and p.get("ilRisk") == "no"
                and p.get("exposure") == "single"
                and apy > 0
                and tvl >= MIN_TVL_M * 1e6
                and is_trusted):
            all_pools.append({
                "chain": chain_display,
                "project": p["project"],
                "symbol": p["symbol"],
                "apy": apy,
                "tvl_m": round(tvl / 1e6, 1),
                "meta": (p.get("poolMeta") or ""),
                "pool_id": p.get("pool", ""),
                "url": f"https://defillama.com/yields/pool/{p.get('pool', '')}",
            })

    return portfolio_apys, all_pools

def ethena_apy():
    """Fetch Ethena sUSDe staking yield."""
    result = fetch("https://ethena.fi/api/yields/protocol-and-staking-yield")
    if "error" in result or "stakingYield" not in result:
        return {"error": result.get("error", "fetch failed")}
    staking = result.get("stakingYield") or {}
    value = staking.get("value")
    if value is None:
        return {"error": "stakingYield.value missing in API response"}
    return {"ethena_susde": round(value, 2)}

def hyperliquid_vault_apr(user_addr, vault_addr=None):
    """Fetch Hyperliquid HLP vault APR for a given user address."""
    equities = fetch(
        "https://api.hyperliquid.xyz/info",
        method="POST",
        data={"type": "userVaultEquities", "user": user_addr},
        headers={"Content-Type": "application/json"}
    )
    if "error" in equities or not isinstance(equities, list) or not equities:
        return {"error": f"no vault equities for {user_addr}"}

    target = vault_addr or equities[0].get("vaultAddress")
    if not target:
        return {"error": "no vaultAddress in equities"}

    details = fetch(
        "https://api.hyperliquid.xyz/info",
        method="POST",
        data={"type": "vaultDetails", "vaultAddress": target},
        headers={"Content-Type": "application/json"}
    )
    if "error" in details or "apr" not in details:
        return {"error": f"no APR for vault {target}"}

    apr_pct = round((details["apr"] or 0) * 100, 2)
    return {"hyperliquid_hlp_vault": apr_pct, "_vault_name": details.get("name", target)}

def print_apy_section(results):
    """Print the LIVE APYs section."""
    print("\n--- LIVE APYs ---")
    for k, v in results.items():
        if k == "sources" or k.startswith("_"):
            continue
        label = k
        if v is None:
            print(f"  {label}: [UNAVAILABLE — API returned no data]")
        elif isinstance(v, str):
            print(f"  {label}: {v}")
        elif isinstance(v, (int, float)) and v == 0.0 and "morpho" in k:
            print(f"  {label}: 0.0%  [IDLE]")
        else:
            print(f"  {label}: {v}%")

def print_pools_section(all_pools):
    """Print available pools tables for Base and Ethereum, top N each, sorted by APY desc."""
    for chain_name in ["Base", "Ethereum"]:
        chain_pools = sorted(
            [p for p in all_pools if p["chain"] == chain_name],
            key=lambda x: -x["apy"]
        )[:TOP_N]

        print(f"\n--- AVAILABLE POOLS ({chain_name}) ---")
        if not chain_pools:
            print("  [NONE — DeFiLlama unavailable or no matching pools]")
            continue

        header = f"{'Rank':<5}  {'APY':>7}  {'Project':<25}  {'Symbol':<18}  {'TVL($M)':>7}  URL"
        print(header)
        for i, p in enumerate(chain_pools, 1):
            meta = f" [{p['meta']}]" if p["meta"] else ""
            sym = p["symbol"] + meta
            print(f"{i:<5}  {p['apy']:>6.2f}%  {p['project']:<25}  {sym:<18}  {p['tvl_m']:>7.1f}  {p['url']}")

def main():
    results = {"sources": {}}

    print("Fetching Morpho Blue vaults...", file=sys.stderr, flush=True)
    morpho = morpho_apys()
    if "error" in morpho:
        results["sources"]["morpho"] = f"[UNAVAILABLE: {morpho['error']}]"
    else:
        results.update(morpho)
        results["sources"]["morpho"] = "blue-api.morpho.org/graphql"

    print("Fetching DeFiLlama (Maple/LIDO/ExtraFi/Avantis + pool discovery)...", file=sys.stderr, flush=True)
    llama_apys, all_pools = defi_llama_apys()
    if "error" in llama_apys:
        results["sources"]["defi_llama"] = f"[UNAVAILABLE: {llama_apys['error']}]"
        all_pools = []
    else:
        results.update(llama_apys)
        results["sources"]["defi_llama"] = f"yields.llama.fi/pools ({len(all_pools)} trusted pools indexed)"

    print("Fetching Ethena sUSDe...", file=sys.stderr, flush=True)
    ethena = ethena_apy()
    if "error" in ethena:
        results["sources"]["ethena"] = f"[UNAVAILABLE: {ethena['error']}]"
    else:
        results.update(ethena)
        results["sources"]["ethena"] = "ethena.fi/api/yields"

    print("Fetching Hyperliquid HLP vault (L3)...", file=sys.stderr, flush=True)
    hlp = hyperliquid_vault_apr("0x5d039ece117073323ade5057a516864f4c40e653")
    if "error" in hlp:
        results["hyperliquid_hlp_vault"] = None
        results["sources"]["hyperliquid"] = f"[UNAVAILABLE: {hlp['error']}]"
    else:
        results["hyperliquid_hlp_vault"] = hlp["hyperliquid_hlp_vault"]
        results["_hyperliquid_vault_name"] = hlp.get("_vault_name", "")
        results["sources"]["hyperliquid"] = f"api.hyperliquid.xyz ({hlp.get('_vault_name', '')})"

    print_apy_section(results)
    print_pools_section(all_pools)

    print("\n--- SOURCES ---")
    for k, v in results["sources"].items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
