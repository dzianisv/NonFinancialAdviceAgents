#!/usr/bin/env python3
"""
DeFi Alerter Telegram Bot — single-owner vault management.

Commands (owner only):
  /start                          — register as owner (first sender only)
  /add <address> <chain> [label]  — add vault to vaults.json
  /remove <label_or_address>      — remove vault from vaults.json
  /list                           — show all vaults
  /run                            — trigger manual alert check (live data)
  /test                           — smoke test: inject 99% divergence, send alert

Owner config:
  Priority: TELEGRAM_CHAT_ID env var → owner.json (written by /start)
  First /start from anyone registers them as owner if none is configured.

Env vars:
  TELEGRAM_BOT_TOKEN  — bot token from @BotFather
  TELEGRAM_CHAT_ID    — (optional) owner chat ID; if missing, use /start to register

Requires: python-telegram-bot==13.15  (sync Updater API, no async)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from telegram import Update
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

VAULTS_FILE = Path(__file__).parent / "vaults.json"
OWNER_FILE  = Path(__file__).parent / "owner.json"
ALERT_SCRIPT = Path(__file__).parent / "defi_alert_check.py"

VALID_CHAINS = {"ethereum", "base"}
CHAIN_IDS = {"ethereum": 1, "base": 8453}


# ── Owner management ──────────────────────────────────────────────────────────

def _get_owner_id() -> int | None:
    """Return configured owner chat ID, or None if not yet registered."""
    # Env var takes priority
    val = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if val and val.lstrip("-").isdigit():
        return int(val)
    # Fallback: owner.json (written by /start)
    if OWNER_FILE.exists():
        try:
            return int(json.loads(OWNER_FILE.read_text()).get("chat_id", ""))
        except (ValueError, KeyError):
            pass
    return None


def _set_owner_id(chat_id: int) -> None:
    OWNER_FILE.write_text(json.dumps({"chat_id": chat_id}, indent=2))


def _is_owner(update: Update) -> bool:
    oid = _get_owner_id()
    return oid is not None and update.effective_chat.id == oid


# ── Vault store ───────────────────────────────────────────────────────────────

def _load() -> list[dict]:
    if VAULTS_FILE.exists():
        return json.loads(VAULTS_FILE.read_text())
    return []


def _save(vaults: list[dict]) -> None:
    VAULTS_FILE.write_text(json.dumps(vaults, indent=2))


# ── Handlers ──────────────────────────────────────────────────────────────────

def cmd_start(update: Update, context) -> None:
    chat_id = update.effective_chat.id
    owner_id = _get_owner_id()

    if owner_id is not None:
        if chat_id == owner_id:
            update.message.reply_text(
                f"Already registered as owner (chat_id={chat_id}).\n"
                "Commands: /add /remove /list /run /test"
            )
        # Silently drop non-owner /start
        return

    # No owner yet — register first sender
    _set_owner_id(chat_id)
    update.message.reply_text(
        f"Owner registered.\n"
        f"Your chat ID: {chat_id}\n\n"
        f"Add this to your .env on the VM:\n"
        f"TELEGRAM_CHAT_ID={chat_id}\n\n"
        "Commands: /add /remove /list /run /test"
    )
    print(f"[INFO] Owner registered: chat_id={chat_id}")


def cmd_add(update: Update, context) -> None:
    if not _is_owner(update):
        return

    args = context.args
    if len(args) < 2:
        update.message.reply_text(
            "Usage: /add <address> <chain> [label]\n"
            "chain must be: ethereum | base"
        )
        return

    address = args[0]
    chain = args[1].lower()
    label = " ".join(args[2:]) if len(args) > 2 else address[:10] + "…"

    if not (address.startswith("0x") and len(address) == 42):
        update.message.reply_text(f"Invalid address: {address!r} — must be 0x-prefixed, 42 chars")
        return

    if chain not in VALID_CHAINS:
        update.message.reply_text(f"Invalid chain: {chain!r} — must be one of: {', '.join(sorted(VALID_CHAINS))}")
        return

    vaults = _load()
    for v in vaults:
        if v["address"].lower() == address.lower() and v["chain"] == chain:
            update.message.reply_text(f"Already tracked: {v['label']} ({address})")
            return

    entry = {"label": label, "address": address, "chain_id": CHAIN_IDS[chain], "chain": chain}
    vaults.append(entry)
    _save(vaults)

    update.message.reply_text(
        f"Added vault:\n"
        f"  label:   {label}\n"
        f"  address: {address}\n"
        f"  chain:   {chain} (chain_id={CHAIN_IDS[chain]})\n"
        f"Total vaults: {len(vaults)}"
    )


def cmd_remove(update: Update, context) -> None:
    if not _is_owner(update):
        return

    if not context.args:
        update.message.reply_text("Usage: /remove <label_or_address>")
        return

    query = " ".join(context.args).lower()
    vaults = _load()
    removed = [v for v in vaults if v["label"].lower() == query or v["address"].lower() == query]
    remaining = [v for v in vaults if v not in removed]

    if not removed:
        update.message.reply_text(f"No vault matched: {query!r}\nUse /list to see current vaults.")
        return

    _save(remaining)
    lines = "\n".join(f"  • {v['label']} ({v['address']}, {v['chain']})" for v in removed)
    update.message.reply_text(f"Removed {len(removed)} vault(s):\n{lines}\nRemaining: {len(remaining)}")


def cmd_list(update: Update, context) -> None:
    if not _is_owner(update):
        return

    vaults = _load()
    if not vaults:
        update.message.reply_text("No vaults tracked yet. Use /add to add one.")
        return

    lines = []
    for i, v in enumerate(vaults, 1):
        lines.append(f"{i}. {v['label']}\n   {v['address']} ({v['chain']})")
    update.message.reply_text("Tracked vaults:\n\n" + "\n\n".join(lines))


def cmd_run(update: Update, context) -> None:
    if not _is_owner(update):
        return

    update.message.reply_text("Running alert check…")
    try:
        result = subprocess.run(
            [sys.executable, str(ALERT_SCRIPT)],
            capture_output=True, text=True, timeout=120,
        )
        output = result.stdout + (("\nSTDERR:\n" + result.stderr) if result.stderr.strip() else "")
        output = output.strip() or "(no output)"
        if len(output) > 4000:
            output = "…(truncated)\n" + output[-4000:]
        update.message.reply_text(f"Check complete (exit {result.returncode}):\n\n{output}")
    except subprocess.TimeoutExpired:
        update.message.reply_text("Alert check timed out after 120s.")
    except Exception as e:
        update.message.reply_text(f"Error running check: {e}")


def cmd_test(update: Update, context) -> None:
    """Smoke test: inject 99% divergence, confirm full alert chain fires."""
    if not _is_owner(update):
        return

    update.message.reply_text("Smoke test: injecting 99% oracle divergence…")
    try:
        result = subprocess.run(
            [sys.executable, str(ALERT_SCRIPT), "--inject-divergence"],
            capture_output=True, text=True, timeout=60,
        )
        output = result.stdout + (("\nSTDERR:\n" + result.stderr) if result.stderr.strip() else "")
        output = output.strip() or "(no output)"
        if len(output) > 4000:
            output = "…(truncated)\n" + output[-4000:]
        update.message.reply_text(
            f"Smoke test complete (exit {result.returncode}):\n\n{output}\n\n"
            "If you received a CRITICAL alert above, the full chain works."
        )
    except subprocess.TimeoutExpired:
        update.message.reply_text("Smoke test timed out.")
    except Exception as e:
        update.message.reply_text(f"Smoke test error: {e}")


def drop_unknown(update: Update, context) -> None:
    pass


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        sys.exit("TELEGRAM_BOT_TOKEN env var not set")

    owner_id = _get_owner_id()
    if owner_id:
        print(f"Bot started. Owner chat_id={owner_id}")
    else:
        print("Bot started. No owner registered — send /start to @cryptoscamalert_bot to register.")

    updater = Updater(token=token)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start",  cmd_start))
    dp.add_handler(CommandHandler("add",    cmd_add,    pass_args=True))
    dp.add_handler(CommandHandler("remove", cmd_remove, pass_args=True))
    dp.add_handler(CommandHandler("list",   cmd_list))
    dp.add_handler(CommandHandler("run",    cmd_run))
    dp.add_handler(CommandHandler("test",   cmd_test))
    dp.add_handler(MessageHandler(Filters.all, drop_unknown))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
