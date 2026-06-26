---
name: dip-scanner
description: "Unified dip scanner for BOTH equity (S&P 100) and crypto (BTC/ETH/SOL/BNB/AVAX/LINK) universes. Screens for assets trading >= 20%/25%/30% below their 52-week intraday high. Equity dips are gated on regime-detection (RISK_ON required for alerts). Crypto dips are gated on Fear & Greed < 25 (extreme fear). Fires immediate alerts on HIGH-conviction dips when the respective gate is satisfied. Use when asked \"what's on sale\", \"any dips\", \"what fell from highs\", \"is crypto cheap\", \"BTC dip opportunity\", \"catch the next Google dip\", \"should I buy the crypto dip\", \"crypto fear and greed\", \"fallen angels\", \"quality stocks on sale\", or on the daily proactive schedule."
license: MIT
compatibility: opencode
metadata:
  audience: investors
  domain: dip-screening
  role: unified-dip-detector
---

# Dip Scanner (Equity + Crypto — unified)

Scans **two universes daily** for assets meaningfully below their 52-week intraday high:

1. **Equity (S&P 100)** — catch the next Google -30%, Meta -40%. Gated on regime-detection (RISK_ON).
2. **Crypto (BTC/ETH/SOL/BNB/AVAX/LINK)** — catch the next BTC at $61k. Gated on Fear & Greed < 25.

Both emit to the **convergence pool** consumed by `signal-convergence-alert`.

## Hard rule

**RECOMMEND ONLY.** No trades, no orders. Output = candidates for quorum review. Educational analysis, not advice.

## Usage

```bash
# Scan both universes (default)
python3 .agents/skills/dip-scanner/dip_scanner.py --universe all

# Equity only (S&P 100)
python3 .agents/skills/dip-scanner/dip_scanner.py --universe equity

# Crypto only
python3 .agents/skills/dip-scanner/dip_scanner.py --universe crypto

# Custom threshold, JSON output
python3 .agents/skills/dip-scanner/dip_scanner.py --universe all --threshold 25 --json

# Emit to convergence pool (HIGH + MEDIUM hits only)
python3 .agents/skills/dip-scanner/dip_scanner.py --universe all --emit-pool

# Price-ground arbitrary tickers (no dip threshold, no universe scan)
python3 .agents/skills/dip-scanner/dip_scanner.py --tickers LEU,KGS,POWL,BTC-USD
```

## Conviction tiers

### Equity
| Tier | Threshold | Action |
|------|-----------|--------|
| HIGH | >= -30% from 52w high | Immediate alert if RISK_ON |
| MEDIUM | -25% to -30% | Add to weekly pool |
| WATCH | -20% to -25% | Note, don't alert |

### Crypto
| Tier | Threshold | Action |
|------|-----------|--------|
| HIGH | >= -40% from 52w high | Immediate alert if F&G < 25 |
| MEDIUM | -30% to -40% | Add to weekly pool |
| WATCH | -20% to -30% | Note, don't alert |

## Gate logic (per universe)

### Equity gate: regime-detection

```bash
python3 .agents/skills/regime-detection/regime_monitor.py --json
```
- **RISK_ON** → HIGH hits fire immediate DM.
- **RISK_OFF** → no new buys. Still run screener to build watchlist for recovery.

### Crypto gate: Fear & Greed + optional funding

**PRIMARY trigger** (immediate DM) when BOTH hold:
1. Any coin >= -30% from 52w high, AND
2. Fear & Greed < 25 (extreme fear)

**BTC funding rate** is BONUS confirmation (OKX primary, dYdX fallback). Never suppress a valid dip+fear alert because funding is unavailable. If funding IS available and < 0% (shorts dominant), add to alert as extra weight.

**TradFi regime cross-check:** a lightweight SPY vs 200d-MA check is printed inline (self-contained). If SPY < 200d-MA (RISK_OFF), the crypto dip is likely correlated with an equity sell-off — note in alert.

## Alert formats

### Equity (HIGH + RISK_ON)
```
DIP ALERT — [TICKER] [pct]% below 52w high
  52w high: $[high_52w]  Now: $[price]  200dMA: $[sma] ([pct_vs_200d]% [above/below])
  Regime: RISK_ON (score [score])
  -> Route to /multi-lens-quorum for verdict? Reply YES.
```

### Crypto (HIGH + F&G < 25)
```
CRYPTO DIP ALERT — [COIN] [pct]% below 52w high
  52w high: $[high_52w]  Now: $[price]  200dMA: $[sma]
  Fear & Greed: [n]/100 ([label]) <- EXTREME FEAR
  BTC Funding: [rate]% (OKX/dYdX) [or "unavailable"]
  Historical context: extreme-fear zones (F&G<25) historically net-positive over 6-12m. NOT a guarantee.
  -> Run /multi-lens-quorum on [COIN]? Reply YES.
```

## Two execution paths (pick by backend)

**A. Local backend (Python + yfinance present):** use the unified script.
```bash
python3 .agents/skills/dip-scanner/dip_scanner.py --universe all --emit-pool
```

**B. openclaw pod (NO Python — node+curl only):** the `.py` won't run. Use `web_fetch` sequentially:

For **equity** — scan the curated quality watchlist (25 names, not full 100):
`GOOGL MSFT AAPL AMZN META NVDA AVGO ADBE CRM NOW ORCL ACN NFLX TMO DHR ABT ISRG ZTS LLY UNH V MA COST HD LOW`
```
web_fetch https://query2.finance.yahoo.com/v8/finance/chart/<T>?range=1y&interval=1d
```

For **crypto**:
```
1. F&G:   web_fetch https://api.alternative.me/fng/?limit=1
2. BTC:   web_fetch https://query2.finance.yahoo.com/v8/finance/chart/BTC-USD?range=1y&interval=1d
3. ETH:   .../ETH-USD?range=1y&interval=1d
4. SOL:   .../SOL-USD?range=1y&interval=1d
5. BNB:   .../BNB-USD?range=1y&interval=1d
6. AVAX:  .../AVAX-USD?range=1y&interval=1d
7. LINK:  .../LINK-USD?range=1y&interval=1d
```
Funding rate: `web_fetch https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USD-SWAP`
Fallback: `https://indexer.dydx.trade/v4/perpetualMarkets?ticker=BTC-USD`
Do NOT use `fapi.binance.com` (HTTP 451) or Bybit (403).

429 -> retry once, then mark `[UNAVAILABLE]`, continue. Never fabricate.

## Price-ground mode (`--tickers`)

Ground an ARBITRARY list of tickers (no universe scan, no dip threshold). Returns every ticker's live 52w-high / 200dMA metrics regardless of distance from high. Used by the hedge-fund-committee workflow to attach paywall-independent pricing to narrative names. Example:
```bash
python3 .agents/skills/dip-scanner/dip_scanner.py --tickers LEU,KGS,POWL,MSFT,BTC-USD
```

## Convergence pool

Run with `--emit-pool` to deterministically append HIGH+MEDIUM rows:
```bash
python3 .agents/skills/dip-scanner/dip_scanner.py --universe all --emit-pool
# writes to ~/.openclaw/workspace/investor/pools/dip_candidates.jsonl (durable, not /tmp)
```
That path is read by `signal-convergence-alert` at 08:30 UTC.

## Cross-checks

- **Equity:** if a HIGH/MEDIUM ticker also appears in recent FT/WSJ coverage -> CONVERGENCE signal (elevate conviction via `stocks-trend-screener`).
- **Crypto:** if a HIGH/MEDIUM coin + extreme fear + negative funding -> triple convergence. Strongest signal.
- **Cross-universe:** if BOTH equity and crypto are dipping simultaneously + VIX elevated -> systemic de-risk event (note as correlated, not independent signals).

## Output fields

### Equity
`ticker`, `current`, `high_52w`, `pct_from_high`, `sma200`, `pct_vs_200d`, `as_of`, `conviction`

### Crypto
`ticker`, `current_usd`, `high_52w_usd`, `pct_from_high`, `sma200_usd`, `pct_vs_200d`, `conviction`

### Metadata (crypto)
`fear_greed` ({value, label}), `btc_funding` ({rate_pct, venue, timestamp, interval_h}), `tradfi_regime` ({ticker, price, sma200, pct_vs_200d, regime})

## JSON output structure

```json
{
  "equity": {"hits": [...], "fetch_misses": [...]},
  "crypto": {"dips": [...], "fear_greed": {...}, "btc_funding": {...}, "tradfi_regime": {...}},
  "grounded": [...]  // only when --tickers used
}
```

## Success criteria

- [ ] Script ran and produced output (or confirmed no hits) for the selected universe(s).
- [ ] Equity: regime checked before any alert. No alert sent for RISK_OFF (watchlist only).
- [ ] Crypto: F&G fetched. No immediate alert unless F&G < 25 AND a coin is >= -30% down.
- [ ] HIGH hits with gate satisfied: DM sent immediately.
- [ ] MEDIUM hits: written to candidate pool (if `--emit-pool`).
- [ ] No fabricated prices — all from yfinance / public APIs.
- [ ] fetch_misses reported honestly (never silently dropped).

## Schedule

- **07:45 UTC (Mon-Fri):** `--universe equity --emit-pool` (before US market open)
- **07:50 UTC (daily):** `--universe crypto --emit-pool` (crypto is 24/7)
- Or run `--universe all` once at 07:45 UTC if a single job is preferred.

## Honesty notes

- "52w high" = max trailing-1y INTRADAY HIGH (yfinance 'High', auto_adjust=False), not a closing max, not all-time.
- sma200 is null when <200 trading days of history exist.
- Single-source yfinance (no reliable second source from agent sandbox). Known limitation.
- Funding rate conventions differ by venue: OKX = 8h; dYdX = 1h normalized to 8h (x8).
