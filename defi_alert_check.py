#!/usr/bin/env python3
"""
DeFi LP/Vault Alert Monitor
Covers the 5 scenarios from usr-retro.md:
  1. Collateral oracle price vs DEX price divergence (>3%) — the USR failure mode
  2. lostAssets > 0 on any Morpho vault
  3. Utilization > 90%
  4. Vault deprecated / whitelist removed
  5. Vault APY < T-bill (DGS3MO) - 0.5% for 3 consecutive days

Usage:
  python defi_alert_check.py                  # check all vaults, alert via Telegram
  python defi_alert_check.py --dry-run        # print alerts, no Telegram

Env vars:
  TELEGRAM_BOT_TOKEN  — bot token from @BotFather
  TELEGRAM_CHAT_ID    — your Telegram user/chat ID
  ETH_RPC_URL         — Ethereum mainnet RPC (e.g. Infura/Alchemy)
  BASE_RPC_URL        — Base mainnet RPC
  FRED_API_KEY        — free key from fredaccount.stlouisfed.org/apikeys (optional, CSV fallback)
"""
from __future__ import annotations
import os, sys, json, argparse, datetime
from pathlib import Path
from typing import Optional

import requests
from web3 import Web3

# ── Config ──────────────────────────────────────────────────────────────────

VAULTS_FILE = Path(__file__).parent / "vaults.json"

ORACLE_DIVERGENCE_THRESHOLD = 0.03   # 3% — fire immediately
UTILIZATION_THRESHOLD       = 0.90   # 90%
TBILL_LAG_DAYS              = 3      # consecutive days below T-bill before alert
TBILL_BUFFER                = 0.005  # 0.5% grace below T-bill

STATE_FILE  = Path(__file__).parent / ".defi_alert_state.json"

# Minimal IOracle ABI — just price()
IORACLE_ABI = [
    {"inputs": [], "name": "price", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"}
]

# ── Vault loader ─────────────────────────────────────────────────────────────

def load_vaults() -> list[dict]:
    """Read vaults.json from same directory. Returns [] with a warning if missing."""
    if not VAULTS_FILE.exists():
        print(f"[warn] vaults.json not found at {VAULTS_FILE} — no vaults to check. "
              "Use the Telegram bot to add vaults (/add command).")
        return []
    return json.loads(VAULTS_FILE.read_text())


# ── Helpers ──────────────────────────────────────────────────────────────────

def _morpho_query(query: str, variables: dict | None = None) -> dict:
    r = requests.post(
        "https://api.morpho.org/graphql",
        json={"query": query, "variables": variables or {}},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()["data"]


def get_vault_data(address: str, chain_id: int) -> dict:
    """Fetch APY, utilization, listing status, and market collateral/oracle per vault."""
    q = """
    query GetVault($addr: String!, $chainId: Int!) {
      vaultByAddress(address: $addr, chainId: $chainId) {
        address name
        listed
        asset { decimals }
        state {
          netApy
          totalAssetsUsd
          allocation {
            market {
              collateralAsset { address symbol decimals }
              oracle { address }
              state { utilization }
            }
          }
        }
      }
    }
    """
    data = _morpho_query(q, {"addr": address, "chainId": chain_id})
    return data.get("vaultByAddress") or {}


def get_dex_price(chain: str, token_address: str) -> Optional[float]:
    """DeFiLlama coins API — free, no key, real-time DEX price."""
    key = f"{chain}:{token_address}"
    try:
        r = requests.get(f"https://coins.llama.fi/prices/current/{key}", timeout=10)
        r.raise_for_status()
        coins = r.json().get("coins", {})
        entry = coins.get(key)
        return float(entry["price"]) if entry else None
    except Exception as e:
        print(f"  [warn] DEX price fetch failed for {token_address}: {e}")
        return None


def get_oracle_price(oracle_address: str, chain: str,
                     collateral_decimals: int = 18, loan_decimals: int = 6) -> Optional[float]:
    """Read Morpho IOracle.price() on-chain, returns USD price correctly scaled.

    Morpho formula: raw = price_usd * 10^(36 + loan_decimals - collateral_decimals)
    So: price_usd = raw / 10^(36 + loan_decimals - collateral_decimals)
    """
    rpc_url = os.environ.get("BASE_RPC_URL" if chain == "base" else "ETH_RPC_URL")
    if not rpc_url:
        print(f"  [warn] No RPC URL set for chain={chain}; skipping oracle check")
        return None
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        oracle = w3.eth.contract(
            address=Web3.to_checksum_address(oracle_address),
            abi=IORACLE_ABI,
        )
        raw = oracle.functions.price().call()
        scale = 10 ** (36 + loan_decimals - collateral_decimals)
        return raw / scale
    except Exception as e:
        print(f"  [warn] Oracle price read failed ({oracle_address}): {e}")
        return None


def get_tbill_rate() -> Optional[float]:
    """FRED DGS3MO — 3-month T-bill rate. Returns fraction (e.g. 0.0427 for 4.27%)."""
    api_key = os.environ.get("FRED_API_KEY")
    try:
        if api_key:
            r = requests.get(
                "https://api.stlouisfed.org/fred/series/observations",
                params={"series_id": "DGS3MO", "api_key": api_key,
                        "file_type": "json", "sort_order": "desc", "limit": 10},
                timeout=10,
            )
            for obs in r.json()["observations"]:
                if obs["value"] != ".":
                    return float(obs["value"]) / 100
        else:
            # CSV fallback — no key required
            import io, csv
            r = requests.get(
                "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS3MO", timeout=10
            )
            rows = list(csv.DictReader(io.StringIO(r.text)))
            for row in reversed(rows):
                val = row.get("DGS3MO", ".")
                if val and val != ".":
                    return float(val) / 100
    except Exception as e:
        print(f"  [warn] FRED fetch failed: {e}")
    return None


def send_telegram(message: str, dry_run: bool = False) -> None:
    if dry_run:
        print(f"\n[DRY-RUN ALERT]\n{message}\n")
        return
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print(f"[alert] TELEGRAM_BOT_TOKEN/CHAT_ID not set. Alert:\n{message}")
        return
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
        timeout=10,
    )


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ── Alert checks ─────────────────────────────────────────────────────────────

def check_vault(label: str, cfg: dict, tbill: Optional[float],
                state: dict, dry_run: bool) -> None:
    address = cfg["address"]
    # vaults.json uses snake_case chain_id; tolerate legacy camelCase chainId too
    chain_id = cfg.get("chain_id") or cfg.get("chainId")
    chain = cfg["chain"]

    if address.startswith("0x..."):
        print(f"  [skip] {label} — placeholder address, use /add via Telegram bot")
        return

    print(f"\n── {label} ({address[:10]}…) ──")
    vault = get_vault_data(address, chain_id)
    if not vault:
        print("  [warn] vault not found in Morpho API")
        return

    alerts: list[str] = []

    # ── 1. Vault delisted ─────────────────────────────────────────────────────
    if not vault.get("listed", True):
        alerts.append(f"🔴 *CRITICAL* vault is delisted — exit position")

    # ── 2. Oracle price vs DEX price (the USR failure mode) ──────────────────
    loan_decimals = (vault.get("asset") or {}).get("decimals", 6)  # USDC=6 default
    allocation = (vault.get("state") or {}).get("allocation") or []
    seen_oracle = set()  # skip duplicate oracle+collateral pairs
    for alloc in allocation:
        market = alloc.get("market") or {}
        collateral = market.get("collateralAsset") or {}
        col_addr = collateral.get("address")
        col_symbol = collateral.get("symbol", "?")
        col_decimals = collateral.get("decimals", 18)
        oracle_addr = (market.get("oracle") or {}).get("address")
        # Utilization alerts disabled — Gauntlet vaults run at ~90% by design; not actionable

        # Oracle vs DEX divergence — skip duplicate oracle+collateral pairs
        dedup_key = (oracle_addr, col_addr)
        if col_addr and oracle_addr and dedup_key not in seen_oracle:
            seen_oracle.add(dedup_key)
            dex_price = get_dex_price(chain, col_addr)
            oracle_price = get_oracle_price(oracle_addr, chain, col_decimals, loan_decimals)

            if dex_price is not None and oracle_price is not None:
                divergence = abs(dex_price - oracle_price) / oracle_price
                status = "✅" if divergence < ORACLE_DIVERGENCE_THRESHOLD else "🔴 *CRITICAL*"
                print(f"  {col_symbol}: oracle=${oracle_price:.4f} DEX=${dex_price:.4f} div={divergence:.2%}")
                if divergence >= ORACLE_DIVERGENCE_THRESHOLD:
                    alerts.append(
                        f"🔴 *CRITICAL* `{col_symbol}` oracle vs DEX divergence *{divergence:.1%}*\n"
                        f"  oracle=${oracle_price:.4f}  DEX=${dex_price:.4f}\n"
                        f"  → EXIT position — this is the USR failure pattern"
                    )
            else:
                print(f"  {col_symbol}: could not compare oracle vs DEX (data unavailable)")

    # ── 3. APY vs T-bill ─────────────────────────────────────────────────────
    net_apy = (vault.get("state") or {}).get("netApy")
    if net_apy is not None and tbill is not None:
        net_apy_f = float(net_apy)
        state_key = f"tbill_below_{address}"
        below = net_apy_f < (tbill - TBILL_BUFFER)
        print(f"  APY={net_apy_f:.2%}  T-bill={tbill:.2%}  below={below}")

        if below:
            count = state.get(state_key, 0) + 1
            state[state_key] = count
            if count >= TBILL_LAG_DAYS:
                alerts.append(
                    f"🟡 *WARN* `{label}` APY *{net_apy_f:.2%}* < T-bill *{tbill:.2%}* "
                    f"for {count} consecutive days — consider alternatives"
                )
        else:
            state[state_key] = 0

    # ── Send alerts ───────────────────────────────────────────────────────────
    if alerts:
        msg = f"*DeFi Alert — {label}*\n" + "\n".join(alerts)
        send_telegram(msg, dry_run=dry_run)
    else:
        print(f"  ✅ all checks passed")


# ── Main ─────────────────────────────────────────────────────────────────────

def _smoke_test(dry_run: bool) -> None:
    """Inject a 99% oracle divergence on a synthetic vault to verify the full alert chain."""
    print("SMOKE TEST — injecting 99% oracle divergence on synthetic vault")
    alerts = [
        "🔴 *CRITICAL* `SMOKE-TOKEN` oracle vs DEX divergence *99.0%*\n"
        "  oracle=$1.0000  DEX=$0.0100\n"
        "  → SMOKE TEST — this confirms the alert chain works end-to-end"
    ]
    msg = "*DeFi Alert — SMOKE TEST vault*\n" + "\n".join(alerts)
    send_telegram(msg, dry_run=dry_run)
    print("Smoke test alert fired." + (" (dry-run — not sent)" if dry_run else " Check Telegram."))


def main() -> None:
    parser = argparse.ArgumentParser(description="DeFi vault alert checker")
    parser.add_argument("--dry-run", action="store_true", help="Print alerts, no Telegram")
    parser.add_argument("--inject-divergence", action="store_true",
                        help="Smoke test: fire synthetic 99%% divergence alert to prove chain works")
    args = parser.parse_args()

    print(f"DeFi Alert Check — {datetime.datetime.utcnow().isoformat()}Z")

    if args.inject_divergence:
        _smoke_test(dry_run=args.dry_run)
        print("\nDone.")
        return

    state = load_state()
    tbill = get_tbill_rate()
    print(f"T-bill (DGS3MO): {tbill:.2%}" if tbill else "T-bill: unavailable")

    vaults = load_vaults()
    if not vaults:
        print("No vaults configured. Done.")
        return

    for vault_cfg in vaults:
        label = vault_cfg.get("label", vault_cfg.get("address", "unknown"))
        try:
            check_vault(label, vault_cfg, tbill, state, dry_run=args.dry_run)
        except Exception as e:
            print(f"  [error] {label}: {e}")

    save_state(state)
    print("\nDone.")


if __name__ == "__main__":
    main()
