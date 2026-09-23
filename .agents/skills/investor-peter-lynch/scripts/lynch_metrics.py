#!/usr/bin/env python3
"""lynch_metrics.py — Peter Lynch metrics for one or more tickers.

Usage:
  python3 lynch_metrics.py TICKER [TICKER ...] [--json] [--no-insider] [--days 90]

Sources (every number carries source + as-of date):
  * yfinance (Yahoo Finance) — price, P/E, financial statements, dividends, holders, earnings date.
  * SEC EDGAR companyfacts (XBRL) — fallback for EPS / revenue / inventory / debt / equity / shares
    when yfinance lacks them. Needs User-Agent "<name> <email>" via env SEC_UA.
  * ../../analyse-smartmoney-form4/fetch_form4.py — insider open-market buys/sells (reused).

Rules: never fabricate. Unavailable => {"value": None, "status": "MISSING", "reason": "..."}.
Category suggestion is a HEURISTIC and labeled as such. Educational, not advice.
"""
import argparse
import datetime as dt
import json
import math
import os
import subprocess
import sys
import time
import urllib.request
import warnings

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
FORM4 = os.path.normpath(os.path.join(HERE, "..", "..", "analyse-smartmoney-form4", "fetch_form4.py"))
SEC_UA = os.environ.get("SEC_UA", "Dzianis Vashchuk dzianisvv@gmail.com")
TODAY = dt.date.today().isoformat()


# ----------------------------------------------------------------------------- helpers
def M(reason, source=None):
    return {"value": None, "status": "MISSING", "reason": reason, "source": source, "as_of": None}


def V(value, source, as_of=None, note=None):
    if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
        return M("null/NaN from source", source)
    d = {"value": value, "status": "OK", "source": source, "as_of": as_of or TODAY}
    if note:
        d["note"] = note
    return d


def val(m):
    return m.get("value") if isinstance(m, dict) else None


def pct(a, b):
    """percent change from b (old) to a (new)"""
    if a is None or b is None or b == 0:
        return None
    return (a / b - 1.0) * 100.0 if b > 0 else None


def cagr(new, old, years):
    if new is None or old is None or years <= 0 or old <= 0 or new <= 0:
        return None
    return ((new / old) ** (1.0 / years) - 1.0) * 100.0


def row(df, names):
    """first matching row (list of floats oldest->newest) from a yfinance statement DataFrame"""
    if df is None or getattr(df, "empty", True):
        return None, None
    for n in names:
        if n in df.index:
            s = df.loc[n].dropna()
            if len(s):
                s = s.sort_index()
                return [float(x) for x in s.values], [str(i.date()) for i in s.index]
    return None, None


# ----------------------------------------------------------------------------- SEC
_cik_cache = {}


def sec_get(url, retries=2):
    req = urllib.request.Request(url, headers={"User-Agent": SEC_UA, "Accept-Encoding": "gzip, deflate"})
    for i in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    import gzip
                    data = gzip.decompress(data)
                return json.loads(data)
        except Exception as e:  # noqa
            if i == retries:
                raise
            time.sleep(0.5)


def sec_cik(ticker):
    if not _cik_cache:
        try:
            j = sec_get("https://www.sec.gov/files/company_tickers.json")
            for v in j.values():
                _cik_cache[v["ticker"].upper()] = int(v["cik_str"])
        except Exception as e:
            _cik_cache["__err__"] = str(e)
    return _cik_cache.get(ticker.upper().replace("-", ""))


def sec_facts(ticker):
    cik = sec_cik(ticker)
    if not cik:
        return None, f"ticker not in SEC company_tickers.json (foreign/ADR or lookup failed: {_cik_cache.get('__err__','')})"
    try:
        return sec_get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"), None
    except Exception as e:
        return None, f"companyfacts fetch failed: {e}"


def sec_annual(facts, tags, units=("USD", "USD/shares", "shares")):
    """annual (10-K FY, form 10-K/20-F) series oldest->newest: [(end, val)]"""
    if not facts:
        return None, None
    gaap = facts.get("facts", {}).get("us-gaap", {})
    gaap.update(facts.get("facts", {}).get("ifrs-full", {}))
    for t in tags:
        if t not in gaap:
            continue
        for u, arr in gaap[t].get("units", {}).items():
            if u not in units:
                continue
            best = {}
            for x in arr:
                if x.get("fp") != "FY" or x.get("form") not in ("10-K", "10-K/A", "20-F", "20-F/A"):
                    continue
                if x.get("start") and x.get("end"):
                    d0 = dt.date.fromisoformat(x["start"]); d1 = dt.date.fromisoformat(x["end"])
                    if (d1 - d0).days < 300:  # skip quarterly-in-FY
                        continue
                fy = x.get("fy")
                end = x["end"]
                # keep the latest-filed value per fiscal year end
                if end not in best or x.get("filed", "") > best[end][1]:
                    best[end] = (x["val"], x.get("filed", ""), fy)
            if best:
                ser = sorted(best.items())
                return [(e, v[0]) for e, v in ser], t
    return None, None


# ----------------------------------------------------------------------------- yfinance
def yf_pull(ticker):
    import yfinance as yf
    t = yf.Ticker(ticker)
    out = {"errors": {}}
    for name, fn in [
        ("info", lambda: t.info or {}),
        ("fast", lambda: dict(t.fast_info) if t.fast_info else {}),
        ("income", lambda: t.income_stmt),
        ("balance", lambda: t.balance_sheet),
        ("cashflow", lambda: t.cashflow),
        ("dividends", lambda: t.dividends),
        ("calendar", lambda: t.calendar),
    ]:
        try:
            out[name] = fn()
        except Exception as e:
            out[name] = None
            out["errors"][name] = f"{type(e).__name__}: {str(e)[:120]}"
    return out


# ----------------------------------------------------------------------------- insiders
def insiders(ticker, days):
    if not os.path.exists(FORM4):
        return M(f"fetch_form4.py not found at {FORM4}")
    try:
        env = dict(os.environ, SEC_UA=SEC_UA)
        p = subprocess.run([sys.executable, FORM4, ticker, "--days", str(days), "--json"],
                           capture_output=True, text=True, timeout=240, env=env)
        txt = p.stdout
        start = txt.find("[") if txt.find("[") >= 0 else txt.find("{")
        recs = json.loads(txt[start:])
        rec = recs[0] if isinstance(recs, list) else recs
        f4 = rec.get("sources", {}).get("form4", {})
        s = f4.get("summary", {})
        return V({
            "status": f4.get("status"), "complete": f4.get("complete"),
            "buy_count": s.get("buy_count"), "buy_value_usd": s.get("buy_value"),
            "distinct_buyers": s.get("distinct_buyers"), "officer_buyers": s.get("officer_buyers"),
            "open_market_sell_count": s.get("open_market_sell_count"),
            "open_market_sell_value_usd": s.get("open_market_sell_value"),
            "planned_10b5_1_sell_count": s.get("planned_10b5_1_sell_count"),
            "dollar_totals_complete": s.get("dollar_totals_complete"),
            "reason": f4.get("reason"),
        }, f"SEC Form 4 via fetch_form4.py --days {days}", TODAY)
    except Exception as e:
        return M(f"fetch_form4.py failed: {type(e).__name__}: {str(e)[:150]}", "fetch_form4.py")


# ----------------------------------------------------------------------------- main compute
def analyze(ticker, days=90, do_insider=True):
    r = {"ticker": ticker.upper(), "as_of": TODAY, "metrics": {}, "flags": [], "notes": []}
    m = r["metrics"]
    try:
        y = yf_pull(ticker)
    except Exception as e:
        y = {"errors": {"all": str(e)}, "info": {}, "fast": {}, "income": None, "balance": None, "cashflow": None,
             "dividends": None, "calendar": None}
    if y["errors"]:
        r["notes"].append({"yfinance_errors": y["errors"]})
    info = y.get("info") or {}
    fast = y.get("fast") or {}
    YF = "yfinance"

    # --- price / cap / PE
    price = info.get("currentPrice") or info.get("regularMarketPrice") or fast.get("lastPrice") or fast.get("last_price")
    m["price"] = V(price, YF) if price else M("no price from yfinance (rate limit or bad ticker)", YF)
    mcap = info.get("marketCap") or fast.get("marketCap") or fast.get("market_cap")
    m["market_cap"] = V(mcap, YF) if mcap else M("no marketCap", YF)
    m["pe_trailing"] = V(info.get("trailingPE"), YF) if info.get("trailingPE") else M("trailingPE absent (negative EPS or not provided)", YF)
    m["pe_forward"] = V(info.get("forwardPE"), YF) if info.get("forwardPE") else M("forwardPE absent", YF)
    m["price_to_book"] = V(info.get("priceToBook"), YF, note="Lynch: book value is often a trap; brands/land hidden, plant/goodwill overstated") if info.get("priceToBook") else M("priceToBook absent", YF)
    shares = info.get("sharesOutstanding") or fast.get("shares")

    # --- statements
    inc, bal, cf = y.get("income"), y.get("balance"), y.get("cashflow")
    fin_ccy = info.get("financialCurrency"); px_ccy = info.get("currency")
    ccy_mismatch = bool(fin_ccy and px_ccy and fin_ccy != px_ccy)
    if ccy_mismatch:
        r["flags"].append(f"CURRENCY MISMATCH: statements in {fin_ccy}, price in {px_ccy} (ADR) — per-share cash/CF vs price figures below are NOT comparable")
        r["notes"].append({"currency": f"financials {fin_ccy}; price {px_ccy}; per-share-vs-price metrics marked MISSING"})
    eps, eps_d = row(inc, ["Diluted EPS", "Basic EPS"])
    rev, rev_d = row(inc, ["Total Revenue", "Operating Revenue"])
    inv, inv_d = row(bal, ["Inventory"])
    debt, debt_d = row(bal, ["Total Debt"])
    ltd, _ = row(bal, ["Long Term Debt", "Long Term Debt And Capital Lease Obligation"])
    curdebt, _ = row(bal, ["Current Debt", "Current Debt And Capital Lease Obligation"])
    eq, eq_d = row(bal, ["Stockholders Equity", "Common Stock Equity", "Total Equity Gross Minority Interest"])
    cash, cash_d = row(bal, ["Cash Cash Equivalents And Short Term Investments", "Cash And Cash Equivalents"])
    shs, shs_d = row(bal, ["Ordinary Shares Number", "Share Issued"])
    ocf, ocf_d = row(cf, ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"])
    fcf, fcf_d = row(cf, ["Free Cash Flow"])
    capex, _ = row(cf, ["Capital Expenditure"])

    # --- SEC fallback
    facts = None
    sec_err = None
    need_sec = any(x is None for x in (eps, rev, inv, debt, eq, shs))
    if need_sec:
        facts, sec_err = sec_facts(ticker)
        if sec_err:
            r["notes"].append({"sec_edgar": sec_err})

    def sec_fill(cur, cur_d, tags, units=("USD",)):
        if cur is not None:
            return cur, cur_d, YF
        ser, tag = sec_annual(facts, tags, units)
        if ser:
            return [v for _, v in ser], [e for e, _ in ser], f"SEC XBRL {tag}"
        return None, None, None

    eps, eps_d, eps_src = sec_fill(eps, eps_d, ["EarningsPerShareDiluted", "EarningsPerShareBasic"], ("USD/shares",))
    rev, rev_d, rev_src = sec_fill(rev, rev_d, ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet"])
    inv, inv_d, inv_src = sec_fill(inv, inv_d, ["InventoryNet", "Inventories"])
    debt, debt_d, debt_src = sec_fill(debt, debt_d, ["LongTermDebt", "DebtCurrent"])
    eq, eq_d, eq_src = sec_fill(eq, eq_d, ["StockholdersEquity", "Equity"])
    shs, shs_d, shs_src = sec_fill(shs, shs_d, ["dei:EntityCommonStockSharesOutstanding", "CommonStockSharesOutstanding", "WeightedAverageNumberOfDilutedSharesOutstanding"], ("shares",))
    if shares is None and shs:
        shares = shs[-1]

    # --- EPS growth
    def growth_block(series, dates, src, label):
        if not series or len(series) < 2:
            m[f"{label}_growth_ttm_yoy_pct"] = M(f"<2 annual {label} points", src)
            m[f"{label}_cagr_pct"] = M(f"<2 annual {label} points", src)
            return None, None
        yoy = pct(series[-1], series[-2])
        n = min(len(series) - 1, 5)
        c = cagr(series[-1], series[-1 - n], n)
        m[f"{label}_growth_ttm_yoy_pct"] = V(round(yoy, 2), src, dates[-1], note=f"FY{dates[-2]}→FY{dates[-1]}") if yoy is not None else M(f"base ≤0 (FY{dates[-2]}={series[-2]})", src)
        m[f"{label}_cagr_pct"] = V(round(c, 2), src, dates[-1], note=f"{n}y CAGR FY{dates[-1-n]}→FY{dates[-1]}") if c is not None else M(f"negative/zero endpoints over {n}y", src)
        return yoy, c

    eps_yoy, eps_cagr = growth_block(eps, eps_d, eps_src or YF, "eps")
    rev_yoy, rev_cagr = growth_block(rev, rev_d, rev_src or YF, "revenue")
    m["eps_annual_series"] = V([dict(fy=d, eps=round(e, 3)) for d, e in zip(eps_d, eps)], eps_src, eps_d[-1], note=f"currency {fin_ccy}" if fin_ccy else None) if eps else M("no annual EPS from yfinance or SEC", "yfinance+SEC")

    # --- PEG
    pe = val(m["pe_trailing"])
    g = eps_cagr if eps_cagr is not None else eps_yoy
    gbasis = "3-5y CAGR" if eps_cagr is not None else "TTM YoY"
    # yfinance (>=0.2.5x) returns dividendYield already in percent (0.25 == 0.25%). Cross-check
    # with dividendRate/price so a fraction-style value (0.0025) is caught either way.
    dy = info.get("dividendYield")
    drate = info.get("dividendRate") or info.get("trailingAnnualDividendRate")
    if drate and price:
        dy = drate / price * 100.0
    elif dy is not None and dy < 0.02 and dy > 0:
        dy = dy * 100.0
    if pe and g and g > 0:
        peg = pe / g
        m["peg"] = V(round(peg, 2), "computed: trailing P/E ÷ EPS growth", note=f"growth basis {gbasis}={g:.1f}%; Lynch: <1 great, ~1 fair, >2 avoid")
        if dy:
            m["peg_dividend_adjusted"] = V(round(pe / (g + dy), 2), "computed: P/E ÷ (growth + yield)", note=f"Lynch ratio (growth+yield)/PE={(g+dy)/pe:.2f} (<1 poor, 1.5 ok, ≥2 great)")
        else:
            m["peg_dividend_adjusted"] = V(round(peg, 2), "computed", note="no dividend → same as PEG")
        if peg < 1: r["flags"].append("PEG<1 (Lynch: bargain if growth is durable)")
        elif peg > 2: r["flags"].append("PEG>2 (Lynch: avoid / overpriced vs growth)")
    else:
        why = "no trailing P/E" if not pe else f"EPS growth not positive ({g}) — PEG not meaningful (check if cyclical/turnaround)"
        m["peg"] = M(why, "computed")
        m["peg_dividend_adjusted"] = M(why, "computed")
    if pe and g and g > 0 and pe > 2 * g:
        r["flags"].append(f"P/E {pe:.1f} > 2× growth {g:.1f}% (very negative per Lynch Ch.10)")
    if g is not None and g > 25:
        r["flags"].append(f"EPS growth {g:.1f}% >25% — Lynch: suspicious, hard to sustain")
    if pe and pe > 40:
        r["flags"].append(f"trailing P/E {pe:.1f} — compare to own history (5y range: MANUAL_CHECK)")
    m["pe_vs_own_history"] = M("historical P/E range not in yfinance/SEC feeds — check 10-K/StockAnalysis manually", "n/a")

    # --- inventory vs sales
    if inv and rev and len(inv) >= 2 and len(rev) >= 2 and inv_d[-1][:4] != rev_d[-1][:4]:
        m["inventory_growth_yoy_pct"] = M(f"latest inventory point is FY{inv_d[-1][:4]} (stale vs revenue FY{rev_d[-1][:4]}) — yfinance dropped recent rows", inv_src)
    elif inv and rev and len(inv) >= 2 and len(rev) >= 2:
        iy = pct(inv[-1], inv[-2])
        m["inventory_growth_yoy_pct"] = V(round(iy, 2), inv_src, inv_d[-1]) if iy is not None else M("inventory base 0", inv_src)
        if iy is not None and rev_yoy is not None:
            m["inventory_vs_revenue_gap_pct"] = V(round(iy - rev_yoy, 2), "computed", note="inventory% − revenue%; >5 = red flag")
            if iy - rev_yoy > 5:
                r["flags"].append(f"INVENTORY_OUTPACING_SALES: inventory {iy:+.1f}% vs revenue {rev_yoy:+.1f}%")
    else:
        m["inventory_growth_yoy_pct"] = M("no inventory line (asset-light/financial) or <2 points", inv_src or "yfinance+SEC")

    # --- debt / equity / net cash
    D = debt[-1] if debt else None
    E = eq[-1] if eq else None
    C = cash[-1] if cash else None
    if D is not None and E:
        de = D / E
        m["debt_to_equity"] = V(round(de, 2), debt_src, debt_d[-1], note="Lynch: ~0.33 (75/25) normal; turnaround gate = cash vs debt + debt type")
        if de > 1:
            r["flags"].append(f"debt/equity {de:.2f} > 1 (leveraged; check debt type)")
    else:
        m["debt_to_equity"] = M("debt or equity missing", debt_src or "yfinance+SEC")
    if ltd or curdebt:
        m["debt_type"] = V({"long_term": ltd[-1] if ltd else None, "current": curdebt[-1] if curdebt else None}, YF, debt_d[-1] if debt_d else None,
                           note="Lynch: short/bank debt due on demand is the dangerous kind")
    else:
        m["debt_type"] = M("no debt split from yfinance", YF)
    if ccy_mismatch:
        m["net_cash_per_share"] = M(f"statements in {fin_ccy} vs price in {px_ccy}; convert manually", "yfinance")
        m["fcf_yield_pct"] = M(f"FCF in {fin_ccy} vs market cap in {px_ccy}", "yfinance")
    elif C is not None and D is not None and shares:
        nc = (C - D) / shares
        m["net_cash_per_share"] = V(round(nc, 2), "computed (cash+ST inv − total debt)/shares", cash_d[-1])
        if price:
            m["price_ex_net_cash"] = V(round(price - nc, 2), "computed price − net cash/share", note="what you pay for the operating business")
    else:
        m["net_cash_per_share"] = M("cash, debt or share count missing", "yfinance")

    # --- cash flow
    if fcf is None and ocf and capex:
        fcf = [o + c for o, c in zip(ocf[-len(capex):], capex)]
        fcf_d = ocf_d[-len(capex):]
    if fcf:
        m["fcf"] = V(fcf[-1], YF, fcf_d[-1], note=f"currency {fin_ccy}" if fin_ccy else None)
        if mcap and not ccy_mismatch:
            m["fcf_yield_pct"] = V(round(fcf[-1] / mcap * 100, 2), "computed FCF/market cap", fcf_d[-1])
    else:
        m["fcf"] = M("no cash-flow statement", YF)
        m["fcf_yield_pct"] = M("no FCF", YF)
    if ccy_mismatch:
        m["cash_flow_per_share"] = M(f"OCF in {fin_ccy} vs price in {px_ccy}", "yfinance")
        m["price_to_cash_flow_per_share"] = M(f"currency mismatch {fin_ccy}/{px_ccy}", "yfinance")
    elif ocf and shares and price:
        cfps = ocf[-1] / shares
        ratio = price / cfps if cfps > 0 else None
        m["cash_flow_per_share"] = V(round(cfps, 2), "computed OCF/shares", ocf_d[-1])
        m["price_to_cash_flow_per_share"] = V(round(ratio, 1), "computed", ocf_d[-1], note="Lynch 10x rule: 10 standard, 5 exciting, >20 rich") if ratio else M("OCF ≤ 0", YF)
        if ratio and ratio <= 5: r["flags"].append(f"price/CFPS {ratio:.1f}x ≤5 (Lynch: exciting)")
        if ratio and ratio > 20: r["flags"].append(f"price/CFPS {ratio:.1f}x >20 (rich vs Lynch 10x rule)")
    else:
        m["cash_flow_per_share"] = M("OCF, shares or price missing", YF)

    # --- dividends
    m["dividend_yield_pct"] = V(round(dy, 2), YF) if dy else V(0.0, YF, note="no dividend")
    divs = y.get("dividends")
    try:
        if divs is not None and len(divs):
            byyear = {}
            for ts, v in divs.items():
                byyear[ts.year] = byyear.get(ts.year, 0.0) + float(v)
            yrs = sorted(byyear)
            cur = dt.date.today().year
            yrs = [yy for yy in yrs if yy < cur]  # exclude partial current year
            streak = 0
            for i in range(len(yrs) - 1, 0, -1):
                if byyear[yrs[i]] > byyear[yrs[i - 1]] + 1e-9:
                    streak += 1
                else:
                    break
            m["dividend_consecutive_increase_years"] = V(streak, YF, note=f"from annual totals {yrs[0]}–{yrs[-1]} (yfinance history; split-adjusted)") if yrs else M("no full-year history", YF)
        else:
            m["dividend_consecutive_increase_years"] = V(0, YF, note="no dividends paid")
    except Exception as e:
        m["dividend_consecutive_increase_years"] = M(f"dividend history parse failed: {e}", YF)

    # --- institutions
    hi = info.get("heldPercentInstitutions")
    if hi is not None:
        hi *= 100
        m["institutional_ownership_pct"] = V(round(hi, 1), YF, note="script heuristic: <30 low (Lynch positive), >80 crowded")
        if hi > 80: r["flags"].append(f"institutional ownership {hi:.0f}% — crowded/discovered")
        if hi < 30: r["flags"].append(f"institutional ownership {hi:.0f}% — low (Lynch positive)")
    else:
        m["institutional_ownership_pct"] = M("heldPercentInstitutions absent", YF)

    # --- share count trend
    if shs and len(shs) >= 2:
        n = min(len(shs) - 1, 4)
        chg = pct(shs[-1], shs[-1 - n])
        m["share_count_change_pct"] = V(round(chg, 2), shs_src, shs_d[-1], note=f"{n}y change {shs_d[-1-n]}→{shs_d[-1]}; negative = buybacks")
        if chg is not None and chg < -2: r["flags"].append(f"share count {chg:+.1f}% over {n}y — buybacks (Lynch positive)")
        if chg is not None and chg > 5: r["flags"].append(f"share count {chg:+.1f}% over {n}y — dilution")
    else:
        m["share_count_change_pct"] = M("<2 share-count points", shs_src or "yfinance+SEC")

    # --- next earnings
    cal = y.get("calendar")
    ed = None
    try:
        if isinstance(cal, dict) and cal.get("Earnings Date"):
            ed = [str(getattr(x, "date", lambda: x)()) for x in cal["Earnings Date"]]
    except Exception:
        ed = None
    m["next_earnings_date"] = V(ed, YF) if ed else M("calendar/Earnings Date absent from yfinance", YF)

    # --- manual checks
    m["hidden_assets"] = M("not computable from feeds — MANUAL_CHECK (real estate at cost, NOLs, stakes, brands)", "n/a")
    m["percent_of_sales_key_product"] = M("segment data not in feeds — MANUAL_CHECK 10-K segments", "n/a")

    # --- insiders
    m["insider_form4_90d"] = insiders(ticker, days) if do_insider else M("skipped (--no-insider)")
    ins = val(m["insider_form4_90d"])
    if ins:
        if (ins.get("buy_count") or 0) > 0:
            r["flags"].append(f"INSIDER OPEN-MARKET BUYING: {ins['buy_count']} buys ≈ ${ins.get('buy_value_usd') or 0:,.0f} (Lynch: strong positive)")
        if (ins.get("open_market_sell_count") or 0) >= 3:
            r["flags"].append(f"insider open-market selling: {ins['open_market_sell_count']} sells ≈ ${ins.get('open_market_sell_value_usd') or 0:,.0f} (Lynch: weak signal unless many insiders)")

    # --- category heuristic
    cat, why = "UNCLASSIFIED", []
    beta = info.get("beta")
    sector = info.get("sector") or ""
    ind = info.get("industry") or ""
    cyc_words = ("Auto", "Steel", "Chemical", "Airline", "Semiconductor", "Oil", "Metal", "Mining", "Paper", "Homebuild", "Aluminum", "Machinery")
    is_cyc = any(w.lower() in (sector + ind).lower() for w in cyc_words)
    if eps and len(eps) >= 2 and eps[-1] < 0 or (eps_yoy is not None and eps_yoy < -30):
        cat = "TURNAROUND?"; why.append("EPS negative or down >30%")
    elif is_cyc:
        cat = "CYCLICAL"; why.append(f"industry '{ind}' is cyclical; PEG/low-PE logic inverts")
    elif g is not None and g >= 20:
        cat = "FAST GROWER"; why.append(f"EPS growth {g:.0f}% ≥20%")
    elif g is not None and g >= 10:
        cat = "STALWART"; why.append(f"EPS growth {g:.0f}% in 10-20% band" + (", large cap" if mcap and mcap > 1e11 else ""))
    elif g is not None:
        cat = "SLOW GROWER"; why.append(f"EPS growth {g:.0f}% <10%" + (f", yield {dy:.1f}%" if dy else ""))
    else:
        why.append("no growth figure")
    if val(m.get("net_cash_per_share")) and price and val(m["net_cash_per_share"]) > 0.3 * price:
        why.append("net cash >30% of price → also ASSET PLAY angle")
    m["lynch_category_heuristic"] = V(cat, "heuristic from growth/dividend/industry — override with judgment", note="; ".join(why))
    return r


# ----------------------------------------------------------------------------- output
def fmt(mv):
    if not isinstance(mv, dict):
        return str(mv)
    if mv["status"] != "OK":
        return f"MISSING — {mv['reason']}"
    v = mv["value"]
    if isinstance(v, float):
        s = f"{v:,.2f}" if abs(v) < 1e6 else f"{v/1e9:,.2f}B"
    elif isinstance(v, int) and abs(v) >= 1e6:
        s = f"{v/1e9:,.2f}B"
    elif isinstance(v, (list, dict)):
        s = json.dumps(v, default=str)[:110]
    else:
        s = str(v)
    src = mv.get("source") or ""
    tail = f" [{src}; {mv.get('as_of')}]"
    if mv.get("note"):
        tail += f" ({mv['note']})"
    return s + tail


ORDER = ["price", "market_cap", "pe_trailing", "pe_forward", "pe_vs_own_history", "eps_growth_ttm_yoy_pct", "eps_cagr_pct",
         "peg", "peg_dividend_adjusted", "revenue_growth_ttm_yoy_pct", "revenue_cagr_pct", "inventory_growth_yoy_pct",
         "inventory_vs_revenue_gap_pct", "debt_to_equity", "debt_type", "net_cash_per_share", "price_ex_net_cash", "fcf",
         "fcf_yield_pct", "cash_flow_per_share", "price_to_cash_flow_per_share", "dividend_yield_pct",
         "dividend_consecutive_increase_years", "institutional_ownership_pct", "share_count_change_pct", "price_to_book",
         "next_earnings_date", "insider_form4_90d", "lynch_category_heuristic", "hidden_assets", "percent_of_sales_key_product"]


def print_table(r):
    print(f"\n=== {r['ticker']}  (as of {r['as_of']}; educational, not advice) ===")
    for k in ORDER:
        if k in r["metrics"]:
            print(f"  {k:<38} {fmt(r['metrics'][k])}")
    for k in r["metrics"]:
        if k not in ORDER and k != "eps_annual_series":
            print(f"  {k:<38} {fmt(r['metrics'][k])}")
    es = r["metrics"].get("eps_annual_series")
    if es and es["status"] == "OK":
        print(f"  {'eps_annual_series':<38} " + ", ".join(f"{x['fy'][:4]}:{x['eps']}" for x in es["value"]) + f" [{es['source']}]")
    print("  FLAGS:")
    for f in r["flags"] or ["(none)"]:
        print(f"    - {f}")
    missing = [k for k, v in r["metrics"].items() if v.get("status") == "MISSING"]
    print(f"  MISSING ({len(missing)}): {', '.join(missing) or 'none'}")
    for n in r["notes"]:
        print(f"  NOTE: {json.dumps(n)[:300]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tickers", nargs="+")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-insider", action="store_true")
    ap.add_argument("--days", type=int, default=90)
    a = ap.parse_args()
    try:
        import yfinance  # noqa
    except ImportError:
        print("yfinance not installed: pip3 install --user yfinance", file=sys.stderr)
        sys.exit(2)
    res = [analyze(t, a.days, not a.no_insider) for t in a.tickers]
    if a.json:
        print(json.dumps(res, indent=2, default=str))
    else:
        for r in res:
            print_table(r)


if __name__ == "__main__":
    main()
