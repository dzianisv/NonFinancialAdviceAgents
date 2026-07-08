#!/usr/bin/env python3
"""AsterDEX perp positions via Aster's V3 futures API (fapi.asterdex.com).

Aster's matching engine is off-chain (own L1) — NEITHER Zerion NOR DeBank can see
these positions (verified 2026-07-08: DeBank showed zero Aster rows on wallets that
hold Aster positions). Aster has no keyless read-by-address; V3 auth = "API Wallet"
model: every USER_DATA request carries user (master wallet), signer (API wallet),
a microsecond nonce, and an EIP-712 signature made with the API-wallet private key
(domain AsterSignTransaction, chainId 1666, message = urlencoded params).
Docs: github.com/asterdex/api-docs → V3(Recommended)/EN/aster-finance-futures-api-v3.md
(V1 HMAC keys are closed to new creation since 2026-03-25.)

Credentials (create at https://www.asterdex.com/en/api-wallet, store in Bitwarden
'dev' + repo .env — the API wallet key can TRADE, treat it as hot):
  ASTER_USER                master account wallet address (0x...)
  ASTER_SIGNER              API wallet address (0x...)
  ASTER_SIGNER_PRIVATE_KEY  API wallet private key (0x...)

Reads: GET /fapi/v3/balance (account balances) + GET /fapi/v3/positionRisk (open
perps). Row convention matches hyperliquid_positions.py: perp rows value = MARGIN,
unrealized P&L shown in the Asset label, not added to value.
"""
from __future__ import annotations
import os
import sys
import time
import urllib.parse

import requests

HOST = "https://fapi.asterdex.com"

TYPED_DATA_TEMPLATE = {
    "types": {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "version", "type": "string"},
            {"name": "chainId", "type": "uint256"},
            {"name": "verifyingContract", "type": "address"},
        ],
        "Message": [{"name": "msg", "type": "string"}],
    },
    "primaryType": "Message",
    "domain": {
        "name": "AsterSignTransaction",
        "version": "1",
        "chainId": 1666,
        "verifyingContract": "0x0000000000000000000000000000000000000000",
    },
    "message": {"msg": ""},
}


def creds_available():
    return all(os.environ.get(k) for k in ("ASTER_USER", "ASTER_SIGNER", "ASTER_SIGNER_PRIVATE_KEY"))


def _sign_params(params):
    """Append nonce/signer/user, sign the urlencoded string EIP-712-style, return query."""
    from eth_account import Account
    from eth_account.messages import encode_typed_data

    params = dict(params)
    params["nonce"] = str(time.time_ns() // 1000)
    params["signer"] = os.environ["ASTER_SIGNER"]
    params["user"] = os.environ["ASTER_USER"]
    query = urllib.parse.urlencode(params)

    typed = {**TYPED_DATA_TEMPLATE, "message": {"msg": query}}
    signed = Account.sign_message(encode_typed_data(full_message=typed),
                                  private_key=os.environ["ASTER_SIGNER_PRIVATE_KEY"])
    sig = signed.signature.hex()
    if not sig.startswith("0x"):
        sig = "0x" + sig
    return query + "&signature=" + sig


def _get(path, params=None):
    url = f"{HOST}{path}?{_sign_params(params or {})}"
    headers = {"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "crypto-portfolio/1.0"}
    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code == 429 or resp.status_code >= 500:
        time.sleep(4)
        url = f"{HOST}{path}?{_sign_params(params or {})}"  # fresh nonce+signature
        resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_positions(label):
    """-> list of row dicts {wallet, protocol, type, pool, asset, balance, usd_value, note}.
    Empty list (with a stderr warning) when credentials are not configured."""
    if not creds_available():
        print("WARN: AsterDEX skipped — ASTER_USER/ASTER_SIGNER/ASTER_SIGNER_PRIVATE_KEY not set "
              "(create an API wallet at https://www.asterdex.com/en/api-wallet).", file=sys.stderr)
        return []

    rows = []

    for b in _get("/fapi/v3/balance"):
        balance = float(b.get("balance", 0) or 0)
        if balance == 0:
            continue
        asset = b.get("asset", "?")
        cross_upnl = float(b.get("crossUnPnl", 0) or 0)
        note = f"cross uPnL {cross_upnl:+.2f}" if cross_upnl else ""
        # stables at $1 (USDT/USDC/USDF); other collateral left unpriced with a note
        if asset.upper() in ("USDT", "USDC", "USDF", "USD1"):
            value = balance
        else:
            value, note = 0.0, (note + "; " if note else "") + "non-stable collateral, priced $0 — extend if held"
        rows.append({
            "wallet": label, "protocol": "AsterDEX", "type": "Deposit",
            "pool": "Futures Account", "asset": asset, "balance": balance,
            "usd_value": value, "note": note,
        })

    for p in _get("/fapi/v3/positionRisk"):
        amt = float(p.get("positionAmt", 0) or 0)
        if amt == 0:
            continue
        symbol = p.get("symbol", "?")
        upnl = float(p.get("unRealizedProfit", 0) or 0)
        lev = p.get("leverage", "?")
        margin_type = p.get("marginType", "")
        side = p.get("positionSide", "BOTH")
        if side == "BOTH":
            side = "Long" if amt > 0 else "Short"
        # isolated: margin is explicit; cross: margin lives in the account balance rows
        # (already counted above) — value the position row at 0 to avoid double count.
        if margin_type == "isolated":
            margin = float(p.get("isolatedMargin", 0) or 0)
            note = ""
        else:
            margin = 0.0
            note = "cross-margined: margin counted in Futures Account row"
        rows.append({
            "wallet": label, "protocol": "AsterDEX", "type": "Perpetuals",
            "pool": f"{symbol} ({side} {lev}x)",
            "asset": f"margin (P&L {upnl:+.2f})", "balance": abs(amt),
            "usd_value": margin, "note": note,
        })

    return rows


if __name__ == "__main__":
    import json
    label = sys.argv[1] if len(sys.argv) > 1 else "ASTER"
    print(json.dumps(fetch_positions(label), indent=2))
