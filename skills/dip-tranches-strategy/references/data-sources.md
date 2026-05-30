# Live Data Sources for Tax-Loss Harvesting

TLH requires different data than dip-buying. You don't just need current prices — you need **cost basis per lot** and **unrealized P/L by lot**, plus visibility into all accounts that could trigger wash sales. Most of this data lives in the user's brokerage account, not on public APIs.

## What data is actually needed for TLH

| Data point | Purpose | Where to get it |
|---|---|---|
| Current market price | Compute unrealized loss | Public market data (yfinance, etc.) |
| Cost basis per lot | Identify highest-cost lots to sell first | Broker only |
| Lot acquisition dates | Distinguish short-term vs long-term | Broker only |
| Recent purchase activity (60 days) | Detect potential wash sales | Broker(s), spouse's broker(s), 401(k) admin |
| Dividend reinvestment history | Detect partial wash sales from DRIP | Broker statements |
| Realized YTD gains/losses | Determine offset value | Broker tax reports |

The first item is the only one with a clean public API. The rest require broker integration or manual entry.

## Source 1: Broker APIs (the right way for production)

If the user wants automated TLH detection, the broker API is the only viable source for cost basis data.

### Alpaca
- Free for users. REST + WebSocket.
- `pip install alpaca-py`
- Exposes positions with cost basis, unrealized P/L, and order history.
- Limitation: only US equities/ETFs; not a fit if user holds elsewhere.

### Interactive Brokers (IBKR)
- TWS API or IBKR Client Portal Web API.
- More setup (TWS gateway must run locally, or use the web gateway).
- Comprehensive: lot-level cost basis, all account types, multi-currency.
- Python wrappers: `ib_insync` (community), `ibapi` (official).

### Charles Schwab
- Developer API (post-TD Ameritrade migration, late 2024+).
- Requires application/approval. Has lot-level data.

### Fidelity, Vanguard
- No official retail developer API as of 2026.
- Workaround: manual CSV export of positions/transactions, parse with pandas.

### Robinhood, E*Trade, etc.
- No supported public API. Unofficial libraries exist but break frequently.

## Source 2: Manual CSV export (works for any broker)

Most brokers let you download positions and transactions as CSV. This is the universal fallback:

```python
import pandas as pd

# Example: parse a typical positions export
positions = pd.read_csv("schwab_positions_export.csv")
# Common columns: Symbol, Quantity, Cost Basis Total, Market Value, Gain/Loss $, Gain/Loss %
# Cost basis per lot usually requires a separate "tax lots" export

# Identify TLH candidates
candidates = positions[
    (positions["Gain/Loss $"] < -500) &
    (positions["Gain/Loss %"] < -2.0)
]
print(candidates[["Symbol", "Quantity", "Cost Basis Total", "Gain/Loss $"]])
```

For lot-level analysis (which is what HIFO sales need), you'll usually need a separate "Tax Lots" or "Unrealized Gain/Loss Detail" export. Schwab, Fidelity, and Vanguard all offer this in their account statements section.

## Source 3: Public price data (only for valuation, not for cost basis)

To value a position you already know the cost basis for, the same data sources from the dip-tranches skill apply: yfinance, xfinance, Alpha Vantage, Twelve Data, Polygon.io. Reuse the patterns from that skill's `references/data-sources.md`.

```python
import yfinance as yf

def current_price(ticker: str) -> float:
    t = yf.Ticker(ticker)
    hist = t.history(period="5d", interval="1d")
    return float(hist["Close"].iloc[-1])

# Combine with broker cost basis
ticker = "VOO"
shares = 500
cost_basis_per_share = 705.00
current = current_price(ticker)
unrealized = (current - cost_basis_per_share) * shares
print(f"{ticker}: {shares} shares @ ${cost_basis_per_share} -> unrealized ${unrealized:,.2f}")
```

## Wash-sale detection across accounts (the hard part)

The wash sale rule applies across **all** of the user's accounts, including spouse and IRAs. No single API exposes this cross-account view. Options:

1. **Per-broker scan, manual reconciliation.** Pull transaction history from each broker for the last 60 days, plus any 401(k) statements. Tedious but reliable.

2. **Aggregator services.** Plaid, Yodlee, MX, etc. can read transaction data across accounts, but they need each broker's credentials and don't always expose lot-level data. Usually overkill for personal use.

3. **Spreadsheet of recent buys.** Many DIY investors keep a simple log of every ETF purchase across all accounts (taxable, IRA, 401(k), spouse). A 30-day check against this log catches most issues. This is the lowest-tech option that actually works.

Example spreadsheet structure:

| Date | Account | Ticker | Shares | Price | Type |
|---|---|---|---|---|---|
| 2026-05-15 | Fidelity Taxable | VOO | 10 | $688.00 | Manual buy |
| 2026-05-20 | Schwab 401(k) | VTSAX | 2.5 | $145.30 | Auto payroll |
| 2026-05-22 | Spouse IRA | VOO | 5 | $691.00 | Manual buy |

Before any TLH harvest, filter to last 30 days and same ticker (or "substantially identical"). Even a single match means partial wash sale risk.

## Identifying TLH opportunities programmatically

Once you have lot-level cost basis and current prices, a simple scan reveals harvestable lots:

```python
import pandas as pd
from datetime import datetime, timedelta

# Hypothetical lot-level dataframe from broker export
# Columns: ticker, acquired_date, shares, cost_per_share, current_price
df = pd.read_csv("tax_lots.csv", parse_dates=["acquired_date"])

df["unrealized_per_share"] = df["current_price"] - df["cost_per_share"]
df["unrealized_total"] = df["unrealized_per_share"] * df["shares"]
df["pct_loss"] = df["unrealized_per_share"] / df["cost_per_share"] * 100

# Holding period
df["days_held"] = (datetime.now() - df["acquired_date"]).dt.days
df["term"] = df["days_held"].apply(lambda d: "long" if d > 365 else "short")

# TLH candidates: at least 2% loss and at least $500 total loss
candidates = df[
    (df["unrealized_total"] < -500) &
    (df["pct_loss"] < -2.0)
].sort_values("unrealized_total")  # biggest losses first (HIFO)

print(candidates)
print(f"\nTotal harvestable loss: ${candidates['unrealized_total'].sum():,.2f}")
```

## Useful tools / libraries

- **pandas** — universal for parsing broker CSVs and computing P/L.
- **`alpaca-py`** — Alpaca's Python SDK; cleanest broker API for prototyping.
- **`ib_insync`** — community wrapper for Interactive Brokers' API.
- **`yfinance` / `xfinance`** — current prices for unrealized P/L computation.
- **`gnucash` or `beancount`** — if the user wants a personal accounting system that tracks tax lots over time without depending on a broker UI.

## Recommended setup by user scale

### Casual ($0 budget, occasional TLH)
- Manual CSV export from broker once per quarter
- Compute candidates in a spreadsheet
- Use the broker's web interface to execute (specific-lot ID built into most modern brokers)

### DIY automated ($0-50/month)
- Broker with an API (Alpaca, IBKR, Schwab)
- Daily Python script that flags new TLH opportunities >$500
- Manual review and execution; no auto-trading

### Robo-advised
- Wealthfront, Betterment, Fidelity Go, etc. do TLH automatically
- Track which ETFs the robo holds — avoid those same tickers in your self-managed accounts to prevent cross-account wash sales

## Data quality warnings for TLH

- **Broker cost basis can be wrong after a transfer (ACATS)** between brokerages. Verify against original purchase records.
- **Wash sale adjustments** show up after the fact in 1099-B forms. The broker's running cost basis already reflects them, but pre-trade analysis may not.
- **Corporate actions** (splits, mergers, spinoffs) adjust cost basis in ways that public price data won't reflect. Always trust the broker's cost basis over a recomputed one.
- **The IRS doesn't get lot-level detail** unless the broker reports it (covered shares, post-2011 for stocks/ETFs). The user is responsible for accurate lot ID on the tax return.
