#!/usr/bin/env python3
"""DeFi portfolio snapshot orchestrator: all wallets -> CSV + totals JSON.

Sources: Zerion (EVM + Solana), swap.coffee (TON), Hyperliquid info API (HL book —
Zerion can't see it). Wallet list lives in <repo>/.cache/crypto-portfolio/wallets.yaml.

Run:
  ZERION_API_KEY=... /Users/engineer/.venv/bin/python3 defi_positions.py [--out DIR]

Outputs (default DIR = <repo>/.cache/crypto-portfolio/):
  defi_positions.csv         one row per position (Wallet,Protocol,Type,Pool,Asset,Balance,USD Value,Note)
  defi_positions_totals.json per-wallet + grand totals (pre-dust-filter, honest comparison)
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import aster_positions
import hyperliquid_positions
import ton_positions
import zerion_positions


CACHE_DIR = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".cache", "crypto-portfolio"))


def load_config():
    import yaml
    with open(os.path.join(CACHE_DIR, "wallets.yaml")) as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=CACHE_DIR, help="output directory")
    args = parser.parse_args()
    os.makedirs(args.out, exist_ok=True)

    cfg = load_config()
    dust_floor = cfg.get("dust_floor_usd", 0.5)
    keep_all_dust = set(cfg.get("keep_all_dust", []))

    all_rows, wallet_totals = [], {}
    for w in cfg["wallets"]:
        label, chain, address = w["label"], w["chain"], w["address"]
        print(f"Fetching {label} ({chain}) {address} ...", file=sys.stderr)
        if chain in ("evm", "solana"):
            rows = zerion_positions.fetch_positions(label, chain, address)
            if w.get("hyperliquid"):
                rows += hyperliquid_positions.fetch_positions(label, address)
            if w.get("asterdex"):
                # Aster's account is keyed by ASTER_USER env creds, not this address;
                # the flag marks which wallet row the positions belong to on the sheet.
                rows += aster_positions.fetch_positions(label)
        elif chain == "ton":
            rows = ton_positions.fetch_positions(label, address)
        else:
            raise ValueError(f"unknown chain {chain}")
        wallet_totals[label] = round(sum(r["usd_value"] for r in rows), 2)
        keep_all = label in keep_all_dust
        all_rows += [r for r in rows if keep_all or r["usd_value"] >= dust_floor]
        time.sleep(1.5)

    order = {w["label"]: i for i, w in enumerate(cfg["wallets"])}
    all_rows.sort(key=lambda r: (order.get(r["wallet"], 99), -r["usd_value"]))

    csv_path = os.path.join(args.out, "defi_positions.csv")
    with open(csv_path, "w", newline="") as f:
        f.write("Wallet,Protocol,Type,Pool,Asset,Balance,USD Value,Note\n")
        for r in all_rows:
            def esc(v):
                v = str(v)
                return '"' + v.replace('"', '""') + '"' if ("," in v or '"' in v) else v
            bal = f"{r['balance']:.6f}".rstrip("0").rstrip(".") if r["balance"] else "0"
            f.write(",".join([
                esc(r["wallet"]), esc(r["protocol"]), esc(r["type"]), esc(r["pool"]),
                esc(r["asset"]), esc(bal), f"{r['usd_value']:.2f}", esc(r.get("note", "")),
            ]) + "\n")

    totals = {**wallet_totals, "GRAND_TOTAL": round(sum(wallet_totals.values()), 2)}
    totals_path = os.path.join(args.out, "defi_positions_totals.json")
    with open(totals_path, "w") as f:
        json.dump(totals, f, indent=2)

    print("\n=== Per-wallet totals ===", file=sys.stderr)
    for w in cfg["wallets"]:
        print(f"  {w['label']}: ${wallet_totals.get(w['label'], 0):,.2f}", file=sys.stderr)
    print(f"  GRAND TOTAL: ${totals['GRAND_TOTAL']:,.2f}", file=sys.stderr)
    print(csv_path)
    print(totals_path)


if __name__ == "__main__":
    main()
