#!/usr/bin/env python3
"""
Crypto portfolio tracker — single source of truth for value, live yield, and rebalance actions.

Replaces the broken spreadsheet (#VALUE!, syrupGlobals errors). Holdings are a snapshot you
maintain in POSITIONS below (or wire a wallet reader later); APY and collateral are pulled LIVE
from DefiLlama and the Morpho GraphQL API at runtime, so the blended yield is always real.

Run:   /Users/engineer/.venv/bin/python3 crypto/portfolio.py
Output: console report + crypto/report/portfolio.md + crypto/report/img/*.png

Educational tooling, not financial advice. Verify against your own wallet before acting.
"""
from __future__ import annotations
import json
import os
import sys
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.join(HERE, "report")
IMG = os.path.join(REPORT, "img")

CLEAN_FRONTIER = 4.5          # %: the honest no-shady stable yield (Maple/steakUSDC)
IDLE_THRESHOLD = 3.0          # %: stables below this are "lazy capital"
CONCENTRATION_CAP = 0.15      # max single-position share before we flag it

# Reflexive/synthetic-dollar & perp-LP collateral we treat as "not blue-chip".
RISKY_COLLATERAL = {
    "susde", "usde", "eusd", "stcusd", "wsrusd", "reusd", "sdeusd", "rlp",
    "pt-", "msusd", "apxusd", "susdai",
}

# ---------------------------------------------------------------------------
# 1) HOLDINGS SNAPSHOT  (value in USD, 2026-05-30). Edit values as they change.
#    resolution hint (pick one): dl=<DefiLlama poolId> | morpho=<vault 0xaddr,chainId>
#    | apy=<manual %>.  kind drives the allocation buckets.
# ---------------------------------------------------------------------------
@dataclass
class Pos:
    name: str
    chain: str
    asset: str            # underlying: USDC/USDT/ETH/SOL/gold/<token>
    kind: str             # stable | eth | sol | gold | directional | satellite
    value: float
    dl: str = ""          # DefiLlama poolId
    morpho: str = ""      # "0xaddr,chainId"
    msym: str = ""        # Morpho vault symbol fallback (e.g. "exmUSDC")
    apy: float | None = None   # manual fallback %
    note: str = ""
    # filled at runtime:
    live_apy: float = field(default=0.0, init=False)
    apy_src: str = field(default="manual", init=False)
    collateral: str = field(default="", init=False)


POSITIONS: list[Pos] = [
    # --- clean stable yield (already done right) ---
    Pos("Maple Syrup USDC (app)", "Ethereum", "USDC", "stable", 9005.24, dl="43641cf5-a92e-416b-bce9-27113d3c0db6"),
    Pos("Maple Syrup USDC (CB)",  "Ethereum", "USDC", "stable", 8269.00, dl="43641cf5-a92e-416b-bce9-27113d3c0db6"),
    # --- IDLE Morpho USDC (audit: genuinely ~0%, verify addresses!) ---
    Pos("Seamless USDC @ Morpho",   "Base", "USDC", "stable", 37770.00, msym="smUSDC", note="21% of book; verify not deprecated cp-smUSDC"),
    Pos("Extrafi XLend USDC @ Morpho","Base","USDC","stable", 10000.00, msym="exmUSDC"),
    Pos("Universal USDC @ Morpho L3","Base","USDC","stable", 10000.00, msym="uUSDC"),
    Pos("Universal USDC @ Morpho",  "Base", "USDC", "stable",  4093.65, msym="uUSDC"),
    Pos("Re7 eUSD @ Morpho",        "Base", "eUSD", "stable",  2805.96, apy=1.28, note="tracked vault may be empty/deprecated"),
    Pos("R7 USDe @ Morpho",         "Base", "USDe", "stable",  6148.84, apy=1.28, note="USDe = synthetic dollar"),
    # --- sub-frontier stables ---
    Pos("save.finance USDC", "Solana", "USDC", "stable", 16307.00, dl="dde4c16c-72cd-43d1-9c2e-4d3a7f5b8a91", apy=2.2),
    Pos("Woo.Fi USDC vault", "Avalanche","USDC","stable", 2054.00, apy=2.54),
    Pos("sUSDe @ ethena.fi", "Ethereum","USDe","stable", 2887.00, apy=3.77, note="synthetic dollar"),
    Pos("jup.ag USDC LP",    "Solana","USDC","stable", 1237.00, apy=5.07, note="sheet said 0.09% — tracking error"),
    Pos("Telegram Wallet USDT","TON","USDT","stable", 66.00, apy=4.0),
    # --- idle raw stables (zero yield, sweep) ---
    Pos("Hyperliquid USDC idle","Hyperliquid","USDC","stable", 5676.28, apy=0.0),
    Pos("USDC idle (Solana)",  "Solana","USDC","stable", 4000.00, apy=0.0),
    Pos("DeFi.app USDC idle",  "Base","USDC","stable", 1000.00, apy=0.0),
    Pos("USDC @ Asterdex idle","Asterdex","USDC","stable", 964.17, apy=0.0),
    # --- satellite / high-risk yield ---
    Pos("Avantis LP USDC", "Base","USDC","satellite", 1000.00, apy=11.0, note="perp-LP: you are the house; real but tail-risk"),
    Pos("HLP @ Hyperliquid","Hyperliquid","USDC","satellite", 5000.00, apy=0.0, note="market-maker vault; JELLY tail risk"),
    Pos("SOL farm @ lighter.xyz","Ethereum","USDC","satellite", 608.56, apy=0.0, note="48% sheet = airdrop/points, not income"),
    # --- TON perp-LP (audit: exit — counterparty to leveraged traders) ---
    Pos("USDT-SLPT @ Storm","TON","USDT","satellite", 8876.82, apy=6.68, note="EXIT: perp-LP counterparty risk"),
    Pos("TON-SLP @ Storm","TON","TON","directional", 8520.00, apy=5.53, note="EXIT: perp-LP + TON beta"),
    Pos("TON-USDT @ DeDust","TON","USDT","satellite", 6382.82, apy=0.01, note="EXIT: IL with ~0 yield"),
    Pos("TON wallet","TON","TON","directional", 140.58, apy=0.0),
    # --- blue-chip directional (keep) ---
    Pos("stETH","Ethereum","ETH","eth", 3141.04, apy=2.73),
    Pos("cbETH","Ethereum","ETH","eth", 233.24, apy=2.94),
    Pos("fragSOL","Solana","SOL","sol", 3935.32, apy=5.5, note="sheet 0.55% = tracking error; LST ~5.5%"),
    Pos("SOL @ Hyperliquid","Hyperliquid","SOL","sol", 1489.69, apy=0.0, note="prefer self-custody"),
    Pos("PAXG (gold)","Ethereum","gold","gold", 4359.00, apy=0.0, note="defensive; fully reserved"),
    # --- speculative / high-vol directional (trim/exit) ---
    Pos("HYPE @ Hyperliquid","Hyperliquid","HYPE","directional", 5174.77, apy=0.0, note="TRIM: ATH, ~100x rev, unlocks"),
    Pos("ASTER @ Asterdex","Asterdex","ASTER","directional", 3546.73, apy=0.0, note="EXIT: speculative, 8-mo-old venue"),
    Pos("LINEA","Ethereum","LINEA","directional", 997.28, apy=0.0),
    Pos("JUP / USDS","Solana","JUP","directional", 668.43, apy=0.0),
    Pos("STRK","Ethereum","STRK","directional", 485.77, apy=0.0),
    Pos("LINEA @ Asterdex","Asterdex","LINEA","directional", 102.81, apy=0.0),
    Pos("TRUMP @ Hyperliquid","Hyperliquid","TRUMP","directional", 104.12, apy=0.0, note="meme"),
    # --- dust (sweep) ---
    Pos("solana dust","Base","SOL","directional", 63.90, apy=0.0),
    Pos("avalanche dust","Base","AVAX","directional", 11.52, apy=0.0),
    Pos("POL","Ethereum","POL","directional", 9.39, apy=0.0),
    Pos("OP","Optimism","OP","directional", 8.65, apy=0.0),
]


# ---------------------------------------------------------------------------
# 2) LIVE DATA
# ---------------------------------------------------------------------------
def _get(url, data=None, headers=None, timeout=30):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def fetch_defillama():
    try:
        pools = _get("https://yields.llama.fi/pools")["data"]
        return {p["pool"]: p for p in pools}
    except Exception as e:
        print(f"  ! DefiLlama fetch failed ({e}); using manual APYs", file=sys.stderr)
        return {}


def fetch_morpho():
    """Return ({lower(addr): rec}, {lower(symbol): rec}) for chains 1 + 8453.
    rec = {apy, col, tvl}. Symbol index keeps the highest-TVL vault per symbol."""
    q = ('{ vaults(first:600, where:{chainId_in:[1,8453]}) { items { address symbol '
         'state { netApy totalAssetsUsd allocation { supplyAssetsUsd '
         'market { collateralAsset { symbol } } } } } } }')
    by_addr, by_sym = {}, {}
    try:
        body = json.dumps({"query": q}).encode()
        data = _get("https://api.morpho.org/graphql", data=body,
                    headers={"Content-Type": "application/json"})
        for v in data["data"]["vaults"]["items"]:
            st = v.get("state") or {}
            tot = st.get("totalAssetsUsd") or 0
            allocs = sorted((a for a in (st.get("allocation") or [])
                             if (a.get("supplyAssetsUsd") or 0) > 0 and a.get("market", {}).get("collateralAsset")),
                            key=lambda a: -a["supplyAssetsUsd"])
            col = ", ".join(f"{int(a['supplyAssetsUsd']/tot*100)}% {a['market']['collateralAsset']['symbol']}"
                            for a in allocs[:3]) if tot else "idle"
            rec = {"apy": (st.get("netApy") or 0) * 100, "col": col or "idle", "tvl": tot}
            by_addr[(v.get("address") or "").lower()] = rec
            sym = (v.get("symbol") or "").lower()
            if sym and rec["tvl"] >= by_sym.get(sym, {}).get("tvl", -1):
                by_sym[sym] = rec
    except Exception as e:
        print(f"  ! Morpho fetch failed ({e}); using manual APYs", file=sys.stderr)
    return by_addr, by_sym


def resolve(positions, dl, m_addr, m_sym):
    for p in positions:
        if p.morpho:
            addr = p.morpho.split(",")[0].lower()
            m = m_addr.get(addr)
            if m is not None and m["tvl"] > 100:   # ignore deprecated near-empty vaults
                p.live_apy, p.apy_src, p.collateral = m["apy"], "morpho:addr", m["col"]
                continue
        if p.msym and p.msym.lower() in m_sym:
            m = m_sym[p.msym.lower()]
            p.live_apy, p.apy_src, p.collateral = m["apy"], "morpho:sym", m["col"]
            continue
        if p.dl and p.dl in dl:
            row = dl[p.dl]
            p.live_apy, p.apy_src = row.get("apy") or 0.0, "defillama"
            continue
        p.live_apy = p.apy if p.apy is not None else 0.0
        p.apy_src = "manual"


# ---------------------------------------------------------------------------
# 3) ANALYTICS
# ---------------------------------------------------------------------------
def is_clean_stable(p):
    if p.kind != "stable":
        return False
    a = p.asset.lower()
    col = (p.collateral or "").lower()
    if any(r in a for r in RISKY_COLLATERAL):
        return False
    if col and any(r in col for r in RISKY_COLLATERAL):
        return False
    return True


def analyze(positions):
    total = sum(p.value for p in positions)
    income = sum(p.value * p.live_apy / 100 for p in positions)
    idle = [p for p in positions if p.kind in ("stable", "satellite")
            and p.asset.upper() in ("USDC", "USDT") and p.live_apy < IDLE_THRESHOLD]
    idle_sum = sum(p.value for p in idle)
    buckets = {}
    for p in positions:
        buckets[p.kind] = buckets.get(p.kind, 0) + p.value
    conc = [p for p in positions if p.value / total > CONCENTRATION_CAP]
    return dict(total=total, income=income, yield_pct=income / total * 100,
                idle=sorted(idle, key=lambda p: -p.value), idle_sum=idle_sum,
                buckets=buckets, conc=conc)


def model(positions, a):
    """Target: idle+sub-frontier+exit-able stables -> clean frontier; keep good earners."""
    move = [p for p in positions
            if (p.kind in ("stable", "satellite"))
            and p.asset.upper() in ("USDC", "USDT")
            and (p.live_apy < CLEAN_FRONTIER or "EXIT" in p.note)]
    move_sum = sum(p.value for p in move)
    keep_income = sum(p.value * p.live_apy / 100 for p in positions if p not in move)
    tgt_income = move_sum * (CLEAN_FRONTIER / 100) + keep_income
    return dict(move=sorted(move, key=lambda p: -p.value), move_sum=move_sum,
                tgt_income=tgt_income, tgt_yield=tgt_income / a["total"] * 100,
                uplift=tgt_income - a["income"])


# ---------------------------------------------------------------------------
# 4) RENDER
# ---------------------------------------------------------------------------
def fmt(x):
    return f"${x:,.0f}"


def console(positions, a, m):
    W = 78
    print("=" * W)
    print(f" CRYPTO PORTFOLIO — live {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}")
    print("=" * W)
    print(f" Total value      {fmt(a['total'])}")
    print(f" Annual income    {fmt(a['income'])}   blended yield {a['yield_pct']:.2f}%")
    print(f" Idle USDC/USDT   {fmt(a['idle_sum'])}  ({len(a['idle'])} positions < {IDLE_THRESHOLD}%)")
    print("-" * W)
    print(" ALLOCATION")
    for k, v in sorted(a["buckets"].items(), key=lambda x: -x[1]):
        bar = "#" * int(v / a["total"] * 40)
        print(f"   {k:11} {fmt(v):>10}  {v/a['total']*100:5.1f}%  {bar}")
    if a["conc"]:
        print("-" * W)
        print(" ⚠ CONCENTRATION (> {:.0f}% in one position)".format(CONCENTRATION_CAP * 100))
        for p in a["conc"]:
            print(f"   {fmt(p.value):>10}  {p.value/a['total']*100:.1f}%  {p.name}")
    print("-" * W)
    print(" 💤 IDLE / SUB-FRONTIER STABLES (reactivate these)")
    for p in a["idle"]:
        print(f"   {fmt(p.value):>10}  {p.live_apy:5.2f}%  {p.name}  [{p.apy_src}]")
    print("-" * W)
    print(" 📈 IMPROVEMENT MODEL")
    print(f"   Reallocate {fmt(m['move_sum'])} of lazy/exit-able stables -> {CLEAN_FRONTIER:.1f}% clean frontier")
    print(f"   Now:    {fmt(a['income'])}/yr   {a['yield_pct']:.2f}%")
    print(f"   Target: {fmt(m['tgt_income'])}/yr   {m['tgt_yield']:.2f}%")
    print(f"   UPLIFT: +{fmt(m['uplift'])}/yr   (+{m['tgt_yield']-a['yield_pct']:.2f} pts), gas-only, lower risk")
    print("=" * W)


def write_markdown(positions, a, m):
    os.makedirs(REPORT, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    L = []
    L.append(f"# Portfolio Report — {ts}\n")
    L.append("*Auto-generated by `crypto/portfolio.py`. APYs live from DefiLlama + Morpho. "
             "Not advice; verify against your wallet.*\n")
    L.append(f"| Metric | Value |\n|---|---|")
    L.append(f"| Total | **{fmt(a['total'])}** |")
    L.append(f"| Annual income | **{fmt(a['income'])}** |")
    L.append(f"| Blended yield | **{a['yield_pct']:.2f}%** |")
    L.append(f"| Idle USDC/USDT (<{IDLE_THRESHOLD}%) | **{fmt(a['idle_sum'])}** |")
    L.append("")
    L.append("## Improvement model")
    L.append(f"Reallocate **{fmt(m['move_sum'])}** of idle / sub-frontier / exit-able stables to the "
             f"~{CLEAN_FRONTIER:.1f}% clean frontier (Maple Syrup USDC, Morpho steakUSDC/gtUSDCp).\n")
    L.append("| | Income/yr | Yield |")
    L.append("|---|---|---|")
    L.append(f"| Now | {fmt(a['income'])} | {a['yield_pct']:.2f}% |")
    L.append(f"| **Target** | **{fmt(m['tgt_income'])}** | **{m['tgt_yield']:.2f}%** |")
    L.append(f"| Uplift | **+{fmt(m['uplift'])}** | +{m['tgt_yield']-a['yield_pct']:.2f} pts |")
    L.append("")
    L.append("## Reactivate (idle / sub-frontier stables)")
    L.append("| Value | Live APY | Source | Position |")
    L.append("|---|---|---|---|")
    for p in a["idle"]:
        L.append(f"| {fmt(p.value)} | {p.live_apy:.2f}% | {p.apy_src} | {p.name} |")
    L.append("")
    L.append("## Full holdings (live)")
    L.append("| Value | Asset | Live APY | Src | Collateral | Bucket | Position | Note |")
    L.append("|---|---|---|---|---|---|---|---|")
    for p in sorted(positions, key=lambda x: -x.value):
        L.append(f"| {fmt(p.value)} | {p.asset} | {p.live_apy:.2f}% | {p.apy_src} | "
                 f"{p.collateral or '—'} | {p.kind} | {p.name} | {p.note} |")
    path = os.path.join(REPORT, "portfolio.md")
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")
    return path


def charts(positions, a, m):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as e:
        print(f"  ! charts skipped ({e})", file=sys.stderr)
        return
    os.makedirs(IMG, exist_ok=True)
    plt.rcParams.update({"figure.dpi": 130, "font.size": 10, "axes.grid": True,
                         "grid.color": "#eee", "axes.axisbelow": True})
    # allocation donut
    fig, ax = plt.subplots(figsize=(6.4, 5.2))
    items = sorted(a["buckets"].items(), key=lambda x: -x[1])
    cols = {"stable": "#1f8a4c", "eth": "#6c5ce7", "sol": "#00b894", "gold": "#e8a020",
            "satellite": "#d4341f", "directional": "#888"}
    ax.pie([v for _, v in items], labels=[f"{k}\n{v/a['total']*100:.0f}%" for k, v in items],
           colors=[cols.get(k, "#bbb") for k, v in items], startangle=90,
           wedgeprops=dict(width=0.42, edgecolor="w"))
    ax.set_title(f"Allocation — {fmt(a['total'])} total", fontweight="bold")
    fig.tight_layout(); fig.savefig(os.path.join(IMG, "alloc.png"), bbox_inches="tight"); plt.close(fig)
    # now vs target income
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    bars = ax.bar(["Now", "Target"], [a["income"], m["tgt_income"]],
                  color=["#bbbbbb", "#1f8a4c"], width=0.55, zorder=3)
    for b, val, y in zip(bars, [a["income"], m["tgt_income"]], [a["yield_pct"], m["tgt_yield"]]):
        ax.text(b.get_x() + b.get_width()/2, val, f"${val:,.0f}\n{y:.2f}%",
                ha="center", va="bottom", fontweight="bold")
    ax.set_ylabel("Annual income (USD)")
    ax.set_title("Income: now vs reallocation target", fontweight="bold", loc="left")
    ax.set_ylim(0, m["tgt_income"] * 1.25)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig(os.path.join(IMG, "uplift.png"), bbox_inches="tight"); plt.close(fig)
    print(f"  charts -> {IMG}/alloc.png, uplift.png")


def main():
    print("Fetching live APY/collateral (DefiLlama + Morpho)...", file=sys.stderr)
    dl = fetch_defillama()
    m_addr, m_sym = fetch_morpho()
    resolve(POSITIONS, dl, m_addr, m_sym)
    a = analyze(POSITIONS)
    m = model(POSITIONS, a)
    console(POSITIONS, a, m)
    md = write_markdown(POSITIONS, a, m)
    charts(POSITIONS, a, m)
    print(f"  report -> {md}", file=sys.stderr)


if __name__ == "__main__":
    main()
