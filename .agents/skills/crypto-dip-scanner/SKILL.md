---
name: crypto-dip-scanner
description: Daily crypto dip scanner — checks BTC/ETH/SOL/BNB/AVAX for % below 52-week ATH, cross-referenced with Fear & Greed index and BTC funding rates. Fires immediate alert when extreme fear (F&G < 25) coincides with a major dip (>= -30% from ATH). Use when asked "is crypto cheap", "BTC dip opportunity", "should I buy the crypto dip", "crypto fear and greed", "when to buy crypto", or on the daily proactive schedule.
license: MIT
compatibility: opencode
metadata:
  audience: crypto-investors
  domain: crypto-dip-detection
  role: crypto-opportunity-scanner
---

# Crypto Dip Scanner

Monitors BTC, ETH, SOL, BNB, AVAX daily for dip opportunities. The goal: never miss a **BTC at $61k** (April 2025) because you weren't watching. This scanner runs before you wake up.

## Why this matters

BTC dropped -43% from its ATH to $61k in Spring 2025. Fear & Greed was sub-20 (extreme fear). Funding rates were negative (shorts dominant). Every historical metric screamed "accumulation zone." No proactive alert existed. This skill fixes that.

## Hard rule

**RECOMMEND ONLY.** No trades. Educational analysis, not advice.

## Run the scanner

```bash
python3 .agents/skills/crypto-dip-scanner/crypto_dip_scanner.py --threshold 20
```

Output fields per coin: `pct_from_ath`, `current_usd`, `ath_52w_usd`, `sma200_usd`, `pct_vs_200d`, `conviction`.

Also outputs:
- **Fear & Greed index** (0–100): < 25 = Extreme Fear = historically good entry
- **BTC funding rate**: negative = shorts dominant = squeeze setup

Conviction tiers:
- `HIGH`: >= -40% from ATH
- `MEDIUM`: -30% to -40%
- `WATCH`: -20% to -30%

## Alert logic

**PRIMARY trigger = IMMEDIATE DM (don't wait for weekly brief).** Fire when BOTH hold:
1. Any coin is >= -30% from 52w ATH, AND
2. Fear & Greed < 25 (extreme fear)

These two are the reliable, always-available signals. **Funding rate is a BONUS confirmation, not a requirement** — `fapi.binance.com` is geo-blocked from many networks (incl. the openclaw pod), so the script prints no funding line when it can't fetch. NEVER suppress a valid dip+fear alert just because funding is missing. If funding IS available and < 0% (shorts dominant), add it to the alert as extra weight.

Fire:
```
🚨 CRYPTO DIP ALERT — [COIN] [pct]% below ATH
  ATH: $[ath]  Now: $[price]  200dMA: $[sma]
  Fear & Greed: [n]/100 ([label])  ← EXTREME FEAR
  BTC Funding: [rate]% [or "unavailable — Binance geo-blocked"]
  Historical context: BTC/ETH extreme-fear zones (F&G<25) have historically been net-positive
    entry points over 6-12m horizons. NOT a guarantee — regime can stay fearful for weeks.
  → Run /multi-lens-quorum on [COIN]? Reply YES.
```

**Single signal (dip without extreme fear, OR fear without a -30% dip):** add to weekly brief as WATCH — do not fire an immediate DM.

## Macro cross-check

After firing alert: check TradFi regime (`regime_monitor.py`). If TradFi is also RISK_OFF (equity sell-off), crypto dip may be correlated → note this. If TradFi recovers first, crypto often follows → heightens urgency.

## Success criteria

- [ ] Script ran, output includes F&G + funding rate.
- [ ] Three-signal convergence: immediate DM sent.
- [ ] Single/double signal: added to weekly pool.
- [ ] No fabricated prices — all from yfinance.

## Schedule

Run **daily 07:50 UTC** — 5 minutes after dip-screener, before US pre-market.
