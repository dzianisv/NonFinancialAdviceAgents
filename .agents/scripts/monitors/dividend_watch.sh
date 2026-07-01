#!/bin/zsh
# dividend_watch.sh — cron wrapper for the daily payout monitor.
# Runs the chrome-use-driven watcher. Requires Chrome running (autoConnect) + Telethon session.
# Tickers can be overridden by passing args; defaults to SITC.
export PATH="$HOME/.bun/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export CHROME="$HOME/.agents/skills/chrome-use/scripts/chrome-use"
REPO="/Users/engineer/workspace/backtest"
TICKERS="${@:-SITC}"
echo "===== $(date) ====="
cd "$REPO" && bun .agents/scripts/monitors/dividend_watch.ts $TICKERS
