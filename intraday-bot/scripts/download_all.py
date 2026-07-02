"""
Download all data specified in the intraday-bot build spec.

- 1d klines 2020-01..now: ~40 USDT pairs (majors + some delisted/faded attempts)
- 1h klines 2020-01..now: BTC, ETH, SOL
- 5m klines 2022-01..now: BTC, ETH, SOL

Run: /Users/engineer/.venv/bin/python3 scripts/download_all.py
"""
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import data

NOW_MONTH = datetime.now(timezone.utc).strftime("%Y-%m")

MAJORS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT",
    "AVAXUSDT", "LINKUSDT", "DOTUSDT", "MATICUSDT", "LTCUSDT", "ATOMUSDT", "UNIUSDT",
    "NEARUSDT", "APTUSDT", "ARBUSDT", "OPUSDT", "FILUSDT", "INJUSDT",
    "TRXUSDT", "ETCUSDT", "XLMUSDT", "ALGOUSDT", "VETUSDT", "SANDUSDT", "MANAUSDT",
    "AXSUSDT", "AAVEUSDT", "GRTUSDT", "EOSUSDT", "THETAUSDT", "XTZUSDT", "CHZUSDT",
    "FTMUSDT", "ICPUSDT", "RUNEUSDT", "SUIUSDT", "SEIUSDT", "TIAUSDT",
]

# Delisted / faded Binance USDT pairs — attempted honestly. Some of these were delisted
# from binance.com spot trading; whether their historical klines remain on data.binance.vision
# is unknown until we try. Report exact hit/miss in the coverage report (do not assume).
DELISTED_OR_FADED_ATTEMPTS = [
    "LUNAUSDT",     # Terra Luna (classic) — collapsed May 2022, still tradeable as LUNC now
    "FTTUSDT",      # FTX Token — FTX collapse Nov 2022
    "SRMUSDT",      # Serum — FTX-ecosystem, faded post-FTX
    "RAYUSDT",      # (kept as a live-but-faded-interest control, not delisted)
    "BTSUSDT",      # BitShares — delisted from many venues over the years
    "COCOSUSDT",    # COCOS-BCX — had a notorious 2019 price glitch on Binance
]

BTC_ETH_SOL = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]


def main():
    all_1d_symbols = MAJORS + DELISTED_OR_FADED_ATTEMPTS
    print(f"=== 1d klines, 2020-01 -> {NOW_MONTH}, {len(all_1d_symbols)} symbols ===")
    data.download(all_1d_symbols, "1d", "2020-01", NOW_MONTH, workers=8)

    print(f"\n=== 1h klines, 2020-01 -> {NOW_MONTH}, {BTC_ETH_SOL} ===")
    data.download(BTC_ETH_SOL, "1h", "2020-01", NOW_MONTH, workers=8)

    print(f"\n=== 5m klines, 2022-01 -> {NOW_MONTH}, {BTC_ETH_SOL} ===")
    data.download(BTC_ETH_SOL, "5m", "2022-01", NOW_MONTH, workers=8)

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
