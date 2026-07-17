#!/usr/bin/env python3
"""
dcf_pull.py — pull the REAL historical financial series a DCF needs for ONE ticker
via yfinance, so the hedgefund-morgan-stanley-dcf skill can ground every assumption
in pulled history instead of inventing it.

WHY THIS EXISTS (and why it is separate from stocks-advisor/fundamentals.py):
  fundamentals.py returns a CURRENT point-in-time snapshot (today's price, PE, one
  revenue-growth number). A DCF needs the multi-year SERIES — revenue, operating
  margin, FCF, capex, share count over the last ~4-5 fiscal years — plus the CAPM
  inputs (beta, shares, net debt). This script pulls exactly that series and NOTHING
  derived: it does not project, forecast, or assume. Projection/WACC/terminal value
  are the skill's job (shown as auditable arithmetic), built ON TOP of this real data.

NO FABRICATION: every number emitted here comes from yfinance for the requested
ticker. Any field yfinance does not provide is emitted as null — never invented. If
the core series (revenue) is missing, the skill must output INSUFFICIENT, not a DCF.

POINT-IN-TIME UNSAFE: like fundamentals.py, this is today's reported history (with
restatements). Correct for a CURRENT valuation; never feed it into a backtest.

INPUT (JSON file as argv[1]):   {"symbol": "ORCL"}
OUTPUT (to {out-dir}/{symbol}.dcf.json and stdout):
  symbol, company, currency, price, shares_outstanding, market_cap, beta,
  total_debt, total_cash, net_debt,
  fiscal_years: [ "2026-05-31", ... ]            # most-recent first
  revenue:            [..]                         # Total Revenue, per fiscal year
  operating_income:   [..]                         # Operating Income
  operating_margin:   [..]  (%)                     # operating_income / revenue
  free_cash_flow:     [..]                          # reported Free Cash Flow
  operating_cash_flow:[..]
  capex:              [..]                          # Capital Expenditure (negative = outflow)
  diluted_shares:     [..]                          # Diluted Average Shares per year
  effective_tax_rate: [..]  (%)                      # Tax Provision / Pretax Income
  rev_cagr_pct, rev_yoy_pct:[..], avg_op_margin_pct  # descriptive only, from the series above
  notes: []                                          # any gap / caveat the skill must surface

USAGE:
  python3 dcf_pull.py /path/to/ORCL.json [--out-dir DIR]
"""
import json
import os
import sys


def _series(df, key):
    """Return a plain float list for a row of a yfinance statement frame, or None.
    NaNs -> None (never 0, never invented)."""
    try:
        if df is None or df.empty or key not in df.index:
            return None
        out = []
        for v in df.loc[key].values:
            try:
                f = float(v)
                out.append(None if f != f else round(f, 2))  # f!=f catches NaN
            except (TypeError, ValueError):
                out.append(None)
        return out
    except Exception:
        return None


def _first_present(df, keys):
    for k in keys:
        s = _series(df, k)
        if s is not None:
            return s
    return None


def _ratio_series(num, den, dp=1):
    """Elementwise num/den*100; None where either side missing/zero."""
    if num is None or den is None:
        return None
    out = []
    for a, b in zip(num, den):
        if a is None or b in (None, 0):
            out.append(None)
        else:
            out.append(round(a / b * 100, dp))
    return out


def pull(symbol):
    import yfinance as yf

    t = yf.Ticker(symbol)
    info = t.info or {}
    notes = []

    fin = t.financials          # annual income statement
    cf = t.cashflow             # annual cash flow
    bs = t.balance_sheet        # annual balance sheet

    cols = []
    try:
        if fin is not None and not fin.empty:
            cols = [str(c.date()) for c in fin.columns]
    except Exception:
        cols = []

    revenue = _first_present(fin, ["Total Revenue", "Operating Revenue"])
    op_income = _first_present(fin, ["Operating Income", "Total Operating Income As Reported"])
    pretax = _series(fin, "Pretax Income")
    tax_prov = _series(fin, "Tax Provision")
    diluted_sh = _first_present(fin, ["Diluted Average Shares", "Basic Average Shares"])

    fcf = _series(cf, "Free Cash Flow")
    ocf = _first_present(cf, ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"])
    capex = _series(cf, "Capital Expenditure")

    if fcf is None and ocf is not None and capex is not None:
        # Reconstruct FCF = OCF + capex (capex already negative) only if not reported.
        fcf = [None if (a is None or b is None) else round(a + b, 2) for a, b in zip(ocf, capex)]
        notes.append("free_cash_flow reconstructed as OCF + capex (reported FCF row absent)")

    op_margin = _ratio_series(op_income, revenue)
    eff_tax = _ratio_series(tax_prov, pretax)

    # CAPM / bridge inputs
    beta = info.get("beta")
    shares = info.get("sharesOutstanding")
    mcap = info.get("marketCap")
    total_debt = info.get("totalDebt")
    total_cash = info.get("totalCash")
    if total_debt is None:
        td = _series(bs, "Total Debt")
        total_debt = td[0] if td else None
    if total_cash is None:
        tc = _first_present(bs, ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"])
        total_cash = tc[0] if tc else None
    net_debt = None
    if total_debt is not None and total_cash is not None:
        net_debt = round(total_debt - total_cash, 2)

    price = info.get("currentPrice") or info.get("regularMarketPrice")

    # descriptive stats (NOT forecasts) — earliest vs latest revenue for a realized CAGR
    rev_cagr = None
    rev_yoy = None
    avg_op_margin = None
    if revenue:
        clean = [(i, v) for i, v in enumerate(revenue) if v is not None and v > 0]
        if len(clean) >= 2:
            # columns are most-recent first
            latest_i, latest_v = clean[0]
            oldest_i, oldest_v = clean[-1]
            yrs = oldest_i - latest_i  # positive
            if yrs > 0 and oldest_v > 0:
                rev_cagr = round(((latest_v / oldest_v) ** (1.0 / yrs) - 1) * 100, 1)
        rev_yoy = []
        for i in range(len(revenue) - 1):
            a, b = revenue[i], revenue[i + 1]
            rev_yoy.append(None if (a is None or b in (None, 0)) else round((a / b - 1) * 100, 1))
    if op_margin:
        vals = [v for v in op_margin if v is not None]
        if vals:
            avg_op_margin = round(sum(vals) / len(vals), 1)

    if not revenue:
        notes.append("CRITICAL: no revenue series returned by yfinance — skill must output INSUFFICIENT, not a DCF")
    if beta is None:
        notes.append("beta missing — WACC cost-of-equity cannot be computed from CAPM; state assumption explicitly or output INSUFFICIENT")
    if fcf and all(v is not None and v < 0 for v in fcf[:2]):
        notes.append("recent FCF is negative (heavy capex phase) — a naive FCF-growth DCF will misprice this; project from a normalized/mid-cycle FCF and SAY SO")

    return {
        "symbol": symbol,
        "company": info.get("longName") or info.get("shortName") or symbol,
        "currency": info.get("financialCurrency") or info.get("currency"),
        "price": round(price, 2) if price is not None else None,
        "shares_outstanding": shares,
        "market_cap": mcap,
        "beta": beta,
        "total_debt": total_debt,
        "total_cash": total_cash,
        "net_debt": net_debt,
        "fiscal_years": cols,
        "revenue": revenue,
        "operating_income": op_income,
        "operating_margin": op_margin,
        "free_cash_flow": fcf,
        "operating_cash_flow": ocf,
        "capex": capex,
        "diluted_shares": diluted_sh,
        "effective_tax_rate": eff_tax,
        "rev_cagr_pct": rev_cagr,
        "rev_yoy_pct": rev_yoy,
        "avg_op_margin_pct": avg_op_margin,
        "notes": notes,
    }


DEFAULT_OUT_DIR = os.path.join(".cache", "hedgefund-dcf")


def main():
    args = sys.argv[1:]
    usage = 'usage: dcf_pull.py <input.json> [--out-dir DIR]   (input: {"symbol":"ORCL"})'

    out_dir = None
    if "--out-dir" in args:
        i = args.index("--out-dir")
        if i + 1 >= len(args):
            sys.exit(usage)
        out_dir = args[i + 1]
        del args[i:i + 2]

    if not args:
        sys.exit(usage)

    with open(args[0]) as f:
        spec = json.load(f)
    symbol = spec["symbol"].upper().strip()
    if not symbol or any(ch.isspace() for ch in symbol) or "," in symbol:
        sys.exit(f"error: symbol {symbol!r} looks like multiple tickers — run once per ticker.")

    try:
        out = pull(symbol)
    except Exception as e:
        out = {"symbol": symbol, "error": f"{type(e).__name__}: {e}",
               "notes": ["data pull failed — skill must output INSUFFICIENT, not a DCF"]}

    out_dir = out_dir or DEFAULT_OUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{symbol}.dcf.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
