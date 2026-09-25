#!/usr/bin/env python3
"""fetch_form4.py — EDGAR Form 4 + SC 13D/13G fetcher for the analyse-smartmoney-form4 spoke.

Moved here from stocks-advisor/scripts/smartmoney.py (retired 2026-09-21). This script
fetches only the two low-lag disclosed-flow sources this spoke owns:

  * Form 4 (insider open-market P/S transactions) — T+2 business days. PRIMARY.
  * SC 13D / 13G (activist / 5% stakes) via EDGAR full-text search — 13D T+5d.

13F, options, dark pool, short-interest are OTHER spokes of the analyse-smartmoney family
(analyse-smartmoney-13f / -options / -darkpool) and are not fetched or placeholdered here.

GUARDS (do not remove):
  (a) EDGAR `primaryDocument` for a Form 4 is the XSL-rendered HTML (`xslF345X06/form4.xml`).
      Fetching it yields HTML with zero <nonDerivativeTransaction> -> a FALSE NEGATIVE. The
      xsl*/ prefix is stripped and the body is asserted to be Form 4 XML before parsing.
  (b) PARTIAL reporting: `complete`, `filings_seen`, `filings_examined`, `filings_failed`;
      MAX_FORM4_FETCH=100; when a transaction's shares/price fail to parse the dollar totals
      are a FLOOR (`dollar_totals_complete=false`). PARTIAL is printed next to the status.
  * SEC fair-access UA must be the literal form "<name> <email>" (env SEC_UA); browser and
    parenthetical UAs get HTTP 403.
  * 10b5-1 sales are TAGGED (plan_10b5_1), never dropped and never cited as impairment.
  * Every source returns OK | NO_DATA | MISSING(named reason). MISSING is named, never silent.

Usage:
  python3 fetch_form4.py TICKER [TICKER ...] [--days 90] [--json] [--out-dir DIR]
"""
import os
import json
import sys
import re
import time
import datetime as dt
import urllib.request
import urllib.error

# SEC fair-access policy requires a UA of the literal form "<name> <email>".
# This is not cosmetic: the parenthetical form "tool/1.0 (contact ...)" and a
# browser UA are BOTH rejected with HTTP 403. Verified 2026-07-24:
#   "backtest-stocks-advisor/1.0 (research; contact via repo owner)" -> 403
#   "Mozilla/5.0"                                                    -> 403
#   "backtest-stocks-advisor research@backtest.local"                -> 200
# Override with SEC_UA to declare a real contact address.
UA = os.environ.get("SEC_UA", "backtest-stocks-advisor research@backtest.local")
SEC_TICKERS = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik10}.json"
SEC_ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc_nodash}/{doc}"
SEC_FTS = "https://efts.sec.gov/LATEST/search-index?q={q}&forms={forms}&dateRange=custom&startdt={start}&enddt={end}"

OK, NO_DATA, MISSING = "OK", "NO_DATA", "MISSING"

# Ceiling on Form 4 documents fetched per ticker. Was 25, which silently cut a
# real read in half — MRVL filed 43 Form 4s in a 120d window on 2026-07-24, so
# 18 filings went unexamined while the seat still reported status OK. At ~0.12s
# of enforced SEC rate-limit spacing this costs ~12s worst case, which is cheap
# for a seat that is allowed to originate a sell. Any truncation that still
# occurs is reported in `reason` and flips `complete` to false.
MAX_FORM4_FETCH = 100


def _get(url, timeout=20, retries=2):
    """Returns (body_bytes, error_string). Never raises, never returns a silent
    empty — an unreachable source must be reportable BY NAME."""
    last = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, headers={
            "User-Agent": UA,
            "Accept-Encoding": "gzip, deflate",
            "Accept": "application/json, text/html, */*",
        })
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    import gzip
                    body = gzip.decompress(body)
                return body, None
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code in (403, 404):
                break           # not transient — do not burn retries
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
        time.sleep(0.4 * (attempt + 1))
    return None, last or "unknown error"


_TICKER_MAP = {"loaded": False, "map": {}, "error": None}


def load_cik_map():
    if _TICKER_MAP["loaded"]:
        return _TICKER_MAP["map"], _TICKER_MAP["error"]
    body, err = _get(SEC_TICKERS)
    _TICKER_MAP["loaded"] = True
    if err:
        _TICKER_MAP["error"] = err
        return {}, err
    try:
        raw = json.loads(body)
    except Exception as e:
        _TICKER_MAP["error"] = f"parse: {e}"
        return {}, _TICKER_MAP["error"]
    m = {}
    for row in raw.values():
        t = str(row.get("ticker", "")).upper()
        if t:
            m[t] = (str(row["cik_str"]).zfill(10), row.get("title", ""))
    _TICKER_MAP["map"] = m
    return m, None


def _form4_docs(cik10, days):
    """Recent Form 4 accessions from the submissions API."""
    body, err = _get(SEC_SUBMISSIONS.format(cik10=cik10))
    if err:
        return None, f"EDGAR submissions {err}"
    try:
        sub = json.loads(body)
    except Exception as e:
        return None, f"EDGAR submissions parse: {e}"
    recent = (sub.get("filings") or {}).get("recent") or {}
    forms = recent.get("form") or []
    accs = recent.get("accessionNumber") or []
    dates = recent.get("filingDate") or []
    prim = recent.get("primaryDocument") or []
    cutoff = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    out = []
    for i, f in enumerate(forms):
        if f != "4":
            continue
        if i < len(dates) and dates[i] < cutoff:
            continue
        out.append({
            "accession": accs[i] if i < len(accs) else None,
            "filed": dates[i] if i < len(dates) else None,
            "doc": prim[i] if i < len(prim) else None,
        })
    return out, None


def _tag(xml, name):
    m = re.search(rf"<{name}>(.*?)</{name}>", xml, re.S)
    return m.group(1).strip() if m else None


def _val(xml, name):
    """<name><value>X</value></name> — EDGAR's nested value wrapper."""
    blk = _tag(xml, name)
    if blk is None:
        return None
    v = re.search(r"<value>(.*?)</value>", blk, re.S)
    return (v.group(1).strip() if v else blk.strip()) or None


def raw_form4_url(cik, acc_nodash, doc):
    """EDGAR's `primaryDocument` for a Form 4 is the XSL-RENDERED HTML view, e.g.
    `xslF345X06/form4.xml`. Fetching that path returns `<!DOCTYPE html ...>` — a
    styled table with NO <nonDerivativeTransaction> elements in it.

    This bit us on first run: every ticker parsed to zero transactions and the
    seat would have reported 'no insider activity' when it had in fact never
    read the data. That is a FALSE NEGATIVE on a sell-originating seat — exactly
    the silent-default class this rework exists to eliminate.

    The machine-readable XML sits in the same accession folder with the xsl*/
    prefix stripped."""
    doc = re.sub(r"^xsl[^/]*/", "", doc or "")
    return SEC_ARCHIVE.format(cik=cik, acc_nodash=acc_nodash, doc=doc)


def looks_like_form4_xml(text):
    """Guard against silently parsing the wrong document to zero rows."""
    return "<ownershipDocument" in text or "<nonDerivativeTransaction" in text


def parse_form4(xml):
    """Returns a list of open-market transactions. 10b5-1 auto-sales are FLAGGED,
    not dropped — the seat needs to know a sale was pre-scheduled, because a
    scheduled sale is much weaker evidence of thesis impairment."""
    owner = _val(xml, "rptOwnerName") or _tag(xml, "rptOwnerName")
    is_officer = (_tag(xml, "isOfficer") or "").strip() in ("1", "true")
    is_director = (_tag(xml, "isDirector") or "").strip() in ("1", "true")
    title = _val(xml, "officerTitle") or _tag(xml, "officerTitle")
    # 10b5-1 flag lives in a footnote or the explicit element depending on vintage
    plan = bool(re.search(r"10b5-1", xml, re.I))
    txns = []
    for blk in re.findall(r"<nonDerivativeTransaction>(.*?)</nonDerivativeTransaction>", xml, re.S):
        code = _val(blk, "transactionCode")
        if code not in ("P", "S"):
            continue          # A=grant, M=option exercise, F=tax withholding — noise
        shares = _val(blk, "transactionShares")
        price = _val(blk, "transactionPricePerShare")
        date = _val(blk, "transactionDate")
        try:
            shares_f = float(shares) if shares else None
        except ValueError:
            shares_f = None
        try:
            price_f = float(price) if price else None
        except ValueError:
            price_f = None
        txns.append({
            "code": code,
            "side": "BUY" if code == "P" else "SELL",
            "shares": shares_f,
            "price": price_f,
            "value": (shares_f * price_f) if (shares_f and price_f) else None,
            "date": date,
            "owner": owner,
            "officer": is_officer,
            "director": is_director,
            "title": title,
            "plan_10b5_1": plan,
        })
    return txns


def fetch_form4(cik10, days):
    """PRIMARY source. T+2 lag."""
    docs, err = _form4_docs(cik10, days)
    if err:
        return {"status": MISSING, "reason": err, "lag": "T+2 business days", "txns": []}
    if not docs:
        return {"status": NO_DATA,
                "reason": f"no Form 4 filed in the last {days}d",
                "lag": "T+2 business days", "txns": []}
    cik = str(int(cik10))
    txns, fetch_errors, urls = [], [], []
    # The newest-25 cap is a rate-limit concession, not a statement about the
    # window. If it bites, SAY SO — an unexamined filing must never be absorbed
    # into a confident "no insider selling" on a sell-originating seat.
    considered = docs[:MAX_FORM4_FETCH]
    truncated = len(docs) - len(considered)
    if truncated > 0:
        fetch_errors.append(f"TRUNCATED: {len(docs)} Form 4s in window, only the newest "
                            f"{len(considered)} were fetched — {truncated} NOT examined")
    for d in considered:
        if not (d["accession"] and d["doc"]):
            # Was a silent `continue`: a filing we could not address vanished
            # without trace and the seat still reported a clean read.
            fetch_errors.append(f"{d.get('accession') or '<no accession>'}: "
                                "filing index incomplete (missing accession or document "
                                "name) — filing NOT examined")
            continue
        url = raw_form4_url(cik, d["accession"].replace("-", ""), d["doc"])
        body, e = _get(url)
        if e:
            fetch_errors.append(f"{d['accession']}: {e}")
            continue
        urls.append(url)
        text = body.decode("utf-8", "replace")
        if not looks_like_form4_xml(text):
            # Do NOT fall through to a zero-row parse — that would read as
            # "no insider activity" when we simply fetched the wrong document.
            fetch_errors.append(f"{d['accession']}: not Form 4 XML (got "
                                f"{'HTML render' if '<html' in text[:200].lower() else 'unknown body'})")
            continue
        try:
            for t in parse_form4(text):
                t["filed"] = d["filed"]
                t["source_url"] = url
                txns.append(t)
        except Exception as e:
            fetch_errors.append(f"{d['accession']}: parse {type(e).__name__}: {e}")
        time.sleep(0.12)                      # SEC fair-access rate limit
    status = OK if txns else (MISSING if fetch_errors else NO_DATA)
    return {
        "status": status,
        # PARTIAL is not OK. If some filings parsed and others failed, an "OK"
        # with the failures buried in `reason` invites the seat to read the
        # result as a complete picture. Name the incompleteness in the status.
        "complete": not fetch_errors,
        "reason": ("; ".join(fetch_errors) if fetch_errors else
                   ("" if txns else f"{len(docs)} Form 4s filed but no open-market P/S transactions")),
        "lag": "T+2 business days",
        "filings_seen": len(docs),
        "filings_examined": len(urls),
        "filings_failed": len(fetch_errors),
        "txns": txns,
        "urls": urls,
    }


def fetch_13dg(ticker, days):
    """13D/13G via EDGAR full-text search. 13D lag T+5."""
    end = dt.date.today()
    start = end - dt.timedelta(days=days)
    url = SEC_FTS.format(q=f'%22{ticker}%22', forms="SC+13D,SC+13G",
                         start=start.isoformat(), end=end.isoformat())
    body, err = _get(url)
    if err:
        return {"status": MISSING, "reason": f"EDGAR full-text search {err}",
                "lag": "13D T+5d; 13G varies", "hits": [], "url": url}
    try:
        j = json.loads(body)
    except Exception as e:
        return {"status": MISSING, "reason": f"parse: {e}",
                "lag": "13D T+5d; 13G varies", "hits": [], "url": url}
    hits = (j.get("hits") or {}).get("hits") or []
    out = []
    for h in hits[:20]:
        src = h.get("_source") or {}
        out.append({
            "form": src.get("root_form") or src.get("file_type"),
            "filed": src.get("file_date"),
            "filer": (src.get("display_names") or [None])[0],
        })
    return {
        "status": OK if out else NO_DATA,
        "reason": "" if out else f"no 13D/13G in the last {days}d",
        "lag": "13D T+5d; 13G varies (quarterly to T+5 by filer class)",
        "hits": out,
        "url": url,
    }


def summarize_form4(f4):
    """Evidence summary. Deliberately does NOT emit ACCUMULATING/DISTRIBUTING —
    that is the seat's call, and a sell additionally needs a stated thesis."""
    txns = f4.get("txns") or []
    buys = [t for t in txns if t["side"] == "BUY"]
    sells = [t for t in txns if t["side"] == "SELL"]
    open_sells = [t for t in sells if not t["plan_10b5_1"]]
    plan_sells = [t for t in sells if t["plan_10b5_1"]]

    def _v(ts):
        return sum(t["value"] for t in ts if t["value"]) or 0.0

    def _unpriced(ts):
        """Transactions whose shares or price would not parse. Their dollars are
        NOT in the sums above. The seat is required to cite a dollar amount, so a
        silently-$0 sale would understate exactly the evidence it must weigh."""
        return len([t for t in ts if not t["value"]])

    unpriced_total = _unpriced(buys) + _unpriced(sells)
    return {
        "buy_count": len(buys), "buy_value": _v(buys),
        "distinct_buyers": len({t["owner"] for t in buys if t["owner"]}),
        "sell_count": len(sells), "sell_value": _v(sells),
        "open_market_sell_count": len(open_sells),
        "open_market_sell_value": _v(open_sells),
        "planned_10b5_1_sell_count": len(plan_sells),
        "officer_buyers": sorted({t["title"] or t["owner"] for t in buys if t["officer"]}),
        "officer_open_market_sellers": sorted({t["title"] or t["owner"] for t in open_sells if t["officer"]}),
        "unpriced_txn_count": unpriced_total,
        "dollar_totals_complete": unpriced_total == 0,
        "unpriced_note": ("" if unpriced_total == 0 else
                          f"{unpriced_total} transaction(s) had unparseable shares/price and "
                          "contribute $0 to the totals above — the dollar figures are a FLOOR, "
                          "not the full amount"),
        # The sell-origination note. An insider SELL is evidence, not a verdict,
        # and a 10b5-1 scheduled sale is materially weaker evidence.
        "sell_evidence_quality": (
            "NONE — no open-market insider selling" if not open_sells else
            "STRONG — officer open-market selling" if any(t["officer"] for t in open_sells) else
            "MODERATE — non-officer open-market selling"),
    }


def run_ticker(ticker, days=90):
    ticker = ticker.upper().strip()
    cmap, cerr = load_cik_map()
    rec = {
        "ticker": ticker,
        "as_of": dt.date.today().isoformat(),
        "sources": {},
        "contract": ("Every source reports OK | NO_DATA | MISSING(named reason). The seat may NOT "
                     "abstain silently: report the named source status. Smart-money is a "
                     "sell-ORIGINATING seat, so a MISSING primary source must be stated in the "
                     "verdict line, not omitted."),
    }
    if cerr or ticker not in cmap:
        rec["cik"] = None
        rec["company"] = None
        reason = cerr or f"ticker {ticker} not in SEC company_tickers.json (ADR/foreign/delisted?)"
        for name in ("form4", "sc_13dg"):
            rec["sources"][name] = {"status": MISSING, "reason": f"CIK unresolved — {reason}"}
    else:
        cik10, name = cmap[ticker]
        rec["cik"], rec["company"] = cik10, name
        f4 = fetch_form4(cik10, days)
        rec["sources"]["form4"] = f4
        rec["sources"]["form4"]["summary"] = summarize_form4(f4)
        rec["sources"]["sc_13dg"] = fetch_13dg(ticker, days)

    rec["fetched_ok"] = [k for k, v in rec["sources"].items() if v.get("status") == OK]
    rec["named_missing"] = [f"{k}: {v.get('reason', '')}" for k, v in rec["sources"].items()
                            if v.get("status") == MISSING]
    return rec


def _fmt(rec):
    L = [f"{rec['ticker']}  {rec.get('company') or '(CIK unresolved)'}  as_of={rec['as_of']}"]
    f4 = rec["sources"].get("form4", {})
    s = f4.get("summary") or {}
    # PARTIAL is printed next to the status, never left only in the JSON: an
    # incomplete read must not look like a clean one at a glance.
    partial = "" if f4.get("complete", True) else "/PARTIAL"
    L.append(f"  Form 4 [{f4.get('status')}{partial}] lag={f4.get('lag')}  {f4.get('reason','')}".rstrip())
    if f4.get("filings_seen") is not None:
        L.append(f"    filings: {f4.get('filings_seen')} in window, "
                 f"{f4.get('filings_examined', 0)} examined, {f4.get('filings_failed', 0)} failed")
    if s:
        L.append(f"    buys: {s['buy_count']} (${s['buy_value']:,.0f}) from {s['distinct_buyers']} insiders"
                 f" | open-market sells: {s['open_market_sell_count']} (${s['open_market_sell_value']:,.0f})"
                 f" | 10b5-1 sells: {s['planned_10b5_1_sell_count']}")
        if s.get("unpriced_note"):
            L.append(f"    ⚠ {s['unpriced_note']}")
        L.append(f"    sell evidence quality: {s['sell_evidence_quality']}")
    d = rec["sources"].get("sc_13dg", {})
    L.append(f"  13D/G  [{d.get('status')}] lag={d.get('lag')}  {d.get('reason','')}".rstrip())
    for h in (d.get("hits") or [])[:5]:
        L.append(f"    {h.get('filed')} {h.get('form')} — {h.get('filer')}")
    L.append(f"  named MISSING: {len(rec['named_missing'])} — " +
             ", ".join(k.split(':')[0] for k in rec["named_missing"]))
    return "\n".join(L)


def main(argv):
    args = [a for a in argv[1:]]
    days, out_dir, as_json, tickers = 90, None, False, []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--days":
            days = int(args[i + 1]); i += 2
        elif a == "--out-dir":
            out_dir = args[i + 1]; i += 2
        elif a == "--json":
            as_json = True; i += 1
        elif a.startswith("--"):
            sys.stderr.write(f"unknown flag {a}\n"); return 2
        else:
            tickers.append(a); i += 1
    if not tickers:
        sys.stderr.write(__doc__ + "\n"); return 2
    recs = []
    for t in tickers:
        rec = run_ticker(t, days)
        recs.append(rec)
        if not as_json:
            print(_fmt(rec))
    if as_json:
        print(json.dumps(recs, indent=2))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        for rec in recs:
            p = os.path.join(out_dir, f"{rec['ticker']}.form4.json")
            with open(p, "w") as fh:
                json.dump(rec, fh, indent=2)
        print(f"wrote {len(recs)} file(s) to {out_dir}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
