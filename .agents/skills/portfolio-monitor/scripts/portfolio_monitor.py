#!/usr/bin/env python3
"""
portfolio-monitor — living DISCIPLINE check over an already-reviewed book.

Not a screener, not prediction. It reads a book that already has theses + written triggers
(stocks/portfolio-review.csv), pulls LIVE prices, detects which triggers have FIRED, flags new
euphoria/extension + unactioned sells + concentration, and emits the DELTA — "what needs action
now". The materially-changed positions are then meant to go to multi-lens-quorum (agent step,
run separately) for the buy/sell/hold call. Discipline applied at scale = the validated agent edge.

Usage: python3 portfolio_monitor.py [--csv stocks/portfolio-review.csv] [--out stocks/]
Educational, not advice. Notification-only; never trades.
"""
import os, re, csv, sys, json, argparse, warnings
from datetime import datetime
warnings.filterwarnings("ignore")
import yfinance as yf

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(HERE, "..", "..", "..", "..", "stocks", "portfolio-review.csv")
PROXIES = {"BTC": "BTC-USD", "BITCOIN": "BTC-USD", "BRENT": "BZ=F", "OIL": "CL=F", "TON": "TON-USD"}


def load(csv_path):
    with open(csv_path, newline="") as f:
        return list(csv.DictReader(f))


def live(tickers):
    """Batch live close + 200d MA + 52wk high. Returns {ticker: {...}} (missing -> absent)."""
    out = {}
    data = yf.download(tickers, period="1y", interval="1d",
                       auto_adjust=True, progress=False, threads=True)
    close = data["Close"] if hasattr(data.columns, "levels") else data[["Close"]]
    if not hasattr(data.columns, "levels"):
        close.columns = [tickers[0]]
    for t in tickers:
        if t not in close.columns:
            continue
        s = close[t].dropna()
        if len(s) < 30:
            continue
        px = float(s.iloc[-1])
        ma200 = float(s.rolling(200).mean().iloc[-1]) if len(s) >= 200 else None
        hi = float(s.max())
        out[t] = {"px": px,
                  "ext_200d": (px / ma200 - 1) if ma200 else None,
                  "from_high": px / hi - 1}
    return out


def parse_triggers(text):
    """Extract (direction, level, asset) triggers from free-text. Best-effort, low-confidence."""
    if not text:
        return []
    trigs = []
    asset = None
    up = text.upper()
    for k, v in PROXIES.items():
        if k in up:
            asset = v; break
    # require a literal $ so bare numbers (percentages, years, share counts) don't false-fire
    for m in re.finditer(r'(below|under|<|above|over|>|reclaims?|reclaim)\s*\$\s*([\d][\d,\.]*)\s*([kK])?', text):
        direction = "above" if m.group(1).lower() in ("above", "over", ">", "reclaim", "reclaims") else "below"
        lvl = float(m.group(2).replace(",", "")) * (1000 if m.group(3) else 1)
        trigs.append({"dir": direction, "level": lvl, "asset": asset, "raw": m.group(0)})
    return trigs


def check(trig, self_px, proxy_px):
    px = proxy_px.get(trig["asset"]) if trig["asset"] else self_px
    if px is None:
        return "?", None
    near = abs(px / trig["level"] - 1) <= 0.05
    fired = (px <= trig["level"]) if trig["dir"] == "below" else (px >= trig["level"])
    return ("FIRED" if fired else "NEAR" if near else "no"), px


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=DEFAULT_CSV)
    ap.add_argument("--out", default=os.path.dirname(DEFAULT_CSV))
    args = ap.parse_args()
    if not os.path.exists(args.csv):
        sys.exit(f"ERROR: holdings csv not found: {args.csv}")

    rows = load(args.csv)
    tickers = sorted({r["Ticker"].split()[0].strip() for r in rows if r.get("Ticker")})
    px = live(tickers + list(set(PROXIES.values())))
    proxy_px = {v: px.get(v, {}).get("px") for v in PROXIES.values()}

    book_total = sum(float(r["Sheet_Value_USD"] or 0) for r in rows if r.get("Sheet_Value_USD"))
    deltas, lines = [], []
    for r in rows:
        tk = r["Ticker"].split()[0].strip()
        d = px.get(tk, {})
        val = float(r["Sheet_Value_USD"] or 0)
        flags = []
        # mechanical discipline flags
        ext = d.get("ext_200d")
        frag = (r.get("AI_Bubble_Fragility") or "").upper()
        if ext is not None and ext > 0.30 and "HIGH" in frag:
            flags.append(f"EUPHORIA: +{ext*100:.0f}% >200dMA & HIGH bubble-fragility")
        if "SELL" in (r.get("Action") or "").upper() and float(r.get("Shares") or 0) > 0:
            flags.append("UNACTIONED SELL: flagged SELL, still held")
        if book_total and val / book_total > 0.10:
            flags.append(f"CONCENTRATION: {val/book_total*100:.0f}% of book")
        # written-trigger checks
        fired = []
        for src in ("Price_Flag", "Next_Step"):
            for trig in parse_triggers(r.get(src, "")):
                status, p = check(trig, d.get("px"), proxy_px)
                if status in ("FIRED", "NEAR"):
                    a = trig["asset"] or tk
                    fired.append(f"{status}: '{trig['raw']}' ({a}={p:.2f})" if p else f"{status}: '{trig['raw']}'")
        if fired:
            flags.append("TRIGGER " + "; ".join(fired))
        pxs = f"${d['px']:.2f}" if d.get("px") else "no-data"
        ext_s = f"{ext*100:+.0f}%>MA" if ext is not None else "n/a"
        fh = f"{d['from_high']*100:+.0f}% from hi" if d.get("from_high") is not None else ""
        row_line = f"{tk:<6}{pxs:>10}  {ext_s:>9}  {fh:>14}  {r.get('Action','')}"
        if flags:
            deltas.append((tk, val, r, flags, row_line))
        lines.append(row_line + ("   ⚑ " + " | ".join(flags) if flags else ""))

    date = datetime.now().strftime("%Y-%m-%d")
    deltas.sort(key=lambda x: -x[1])
    L = [f"# portfolio-monitor — {date}", "",
         "_Discipline delta over the reviewed book. Notification-only; not advice. "
         "Hand the action list to multi-lens-quorum for the buy/sell/hold call._", "",
         f"## ⚑ WHAT NEEDS ACTION NOW ({len(deltas)} positions)", ""]
    if not deltas:
        L.append("_No fired triggers, euphoria, unactioned sells, or concentration changes._")
    for tk, val, r, flags, _ in deltas:
        L.append(f"- **{tk}** (${val:,.0f}, {r.get('Conviction','')}): " + " · ".join(flags))
    L += ["", "## Full live status", "", "```",
          f"{'TICKER':<6}{'PRICE':>10}  {'EXT':>9}  {'FROM HIGH':>14}  ACTION", *lines, "```", "",
          "_EXT = % above 200d MA (euphoria gauge). Trigger parse is best-effort — verify the "
          "quoted trigger text. Dead/merged tickers show no-data._"]
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, f"monitor-report-{date}.md")
    with open(path, "w") as f:
        f.write("\n".join(L))
    print(f"wrote {path}")
    print(f"action-now positions ({len(deltas)}): {[d[0] for d in deltas]}")


if __name__ == "__main__":
    main()
