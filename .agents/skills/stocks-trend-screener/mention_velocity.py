#!/usr/bin/env python3
"""
mention_velocity.py — deterministic narrative-velocity counter (the SanDisk instrument).

trend-stock-research's SYNTHESIZE does prose/theme acceleration; this is the hard, testable backstop:
count how many RECENT-DATED headlines mention each watchlist ticker, compare to that ticker's OWN
trailing baseline, and FLAG a spike (e.g. 0→3+/week). Spikes feed ~/.openclaw/workspace/investor/pools/narrative.jsonl so
signal-convergence-alert can cross them with dips/13F/congress — catching a multi-week narrative
build (SanDisk Sept-2025) BEFORE it's obvious.

Data: fetched via `bun .agents/skills/read-news/scripts/read_news.ts --source googlenews` (a
subprocess call), NOT a direct stdlib urlopen — read_news.ts is the sole front door for all
Google News RSS fetches repo-wide, so no script raw-fetches Google News anymore. Its googlenews
adapter already day-filters server-side (`when:Nd` matching --days) and restricts results via
`site:` clauses to 5 whitelisted outlets (bloomberg.com, reuters.com, businessinsider.com,
cnbc.com, investors.com/IBD). This means counts are now bounded to that 5-outlet whitelist,
NOT the fully unrestricted "all outlets" headline volume the old raw urlopen approach captured —
an intentional, documented consequence of centralization. It changes the ABSOLUTE SCALE of the
velocity metric (likely lower counts, especially for smaller-cap/less-covered tickers, since
coverage is now 5 large financial-media outlets instead of everything Google indexes). The
ratio-vs-baseline design still works despite this: each ticker is compared ONLY against its OWN
trailing history under the SAME restricted source, so a constant scale-down from outlet
restriction mostly cancels out in the ratio — though it does lower the chance smaller/
less-covered names clear MIN_BASELINE_OBS/--min-spike thresholds at all.
NEVER fabricates a headline; a failed fetch → that ticker is [unavailable], not invented.

Ledger: $NARRATIVE_LEDGER or <repo_root>/.cache/stocks-trend-screener/narrative_ledger.jsonl

Usage:
    python3 mention_velocity.py --tickers NVDA,WDC,STX,MU,AVGO --days 7
    python3 mention_velocity.py --json            # uses a default large-cap watchlist
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path


def _find_repo_root() -> Path:
    """Walk up from this file's location until a .git directory is found."""
    p = Path(__file__).resolve()
    for parent in [p] + list(p.parents):
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Could not find repo root (no .git found up from %s)" % __file__)


_CACHE_DIR = _find_repo_root() / ".cache" / "stocks-trend-screener"

LEDGER = os.environ.get("NARRATIVE_LEDGER", str(_CACHE_DIR / "narrative_ledger.jsonl"))
# DURABLE pool (NOT /tmp — convergence runs in a separate cron session that can't see this job's /tmp).
NARRATIVE_POOL = os.environ.get("NARRATIVE_POOL", os.path.expanduser("~/.openclaw/workspace/investor/pools/narrative.jsonl"))
MIN_BASELINE_OBS = 3  # need this many prior daily observations before a spike may FEED convergence (cold-start guard)
DEFAULT = ["NVDA", "WDC", "STX", "MU", "AVGO", "AMD", "TSM", "ASML", "ANET", "VRT",
           "SMCI", "MRVL", "KLAC", "LRCX", "DELL"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def fetch_recent_count(ticker: str, days: int) -> tuple[int, list[str]] | None:
    """Return (count_within_window, sample_headlines) or None on fetch failure (never fabricate).

    Goes through read-news's CLI front door (bun read_news.ts --source googlenews) instead of
    raw-fetching Google News RSS directly — see module docstring for why. `fetched` is the raw,
    day-filtered, 5-outlet-whitelisted item count and is the direct analog of the old code's raw
    <item> iteration count. `sample_headlines` is best-effort, pulled from the (often empty)
    `events` array; it's fine and expected for this to come back as [] most of the time.
    """
    repo_root = _find_repo_root()
    script = repo_root / ".agents" / "skills" / "read-news" / "scripts" / "read_news.ts"
    try:
        result = subprocess.run(
            ["bun", str(script), "--source", "googlenews", "--query", f"{ticker} stock",
             "--days", str(days)],
            capture_output=True, text=True, timeout=30, cwd=str(repo_root),
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    if "fetched" not in data:
        return None
    # read_news.ts never emits a bare "googlenews" string in `unavailable` -- entries are always
    # prefixed, e.g. "googlenews:HTTP 500 for query ..." or "googlenews:googlenews: HTTP ...". The
    # exact-membership check this replaced (`"googlenews" in unavailable`) could never match any
    # real entry, so a failed fetch silently fell through to `count = data["fetched"]` (0) and got
    # recorded as a legitimate zero-mention day instead of [unavailable]. Match by prefix instead.
    unavailable = data.get("unavailable") or []
    if any(isinstance(u, str) and u.startswith("googlenews") for u in unavailable):
        return None
    count = data["fetched"]
    samples = [e.get("title") for e in (data.get("events") or []) if e.get("title")][:3]
    return count, samples


def trailing_stats(ticker: str, exclude_today: bool = True) -> tuple[float, int]:
    """(mean, n_observations) of prior logged counts for this ticker — its own baseline + maturity."""
    if not os.path.exists(LEDGER):
        return 0.0, 0
    today = _now().date().isoformat()
    vals = []
    with open(LEDGER) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("ticker") != ticker:
                continue
            if exclude_today and str(r.get("date", "")).startswith(today):
                continue
            c = r.get("mentions")
            if isinstance(c, (int, float)):
                vals.append(float(c))
    return (round(sum(vals) / len(vals), 2) if vals else 0.0), len(vals)


def record(ticker: str, mentions: int) -> None:
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "a") as f:
        f.write(json.dumps({"ticker": ticker, "date": _now().isoformat(), "mentions": mentions}) + "\n")


def feed_convergence(ticker: str, reason: str) -> None:
    try:
        os.makedirs(os.path.dirname(NARRATIVE_POOL) or ".", exist_ok=True)
        with open(NARRATIVE_POOL, "a") as f:
            f.write(json.dumps({"ticker": ticker, "reason": reason, "date": _now().date().isoformat()}) + "\n")
    except OSError:
        pass


def run(tickers: list[str], days: int, min_spike: int, ratio: float) -> list[dict]:
    out = []
    for t in tickers:
        res = fetch_recent_count(t, days)
        if res is None:
            out.append({"ticker": t, "mentions_now": None, "status": "[unavailable]"})
            continue
        now_n, samples = res
        base, n_obs = trailing_stats(t)
        record(t, now_n)  # persist AFTER reading baseline so today doesn't pollute its own avg
        vr = round(now_n / base, 2) if base > 0 else (float("inf") if now_n >= min_spike else 0.0)
        spike = now_n >= min_spike and (base == 0 or now_n >= ratio * base)
        mature = n_obs >= MIN_BASELINE_OBS               # cold-start guard: don't feed convergence yet
        pool_fed = bool(spike and mature)
        row = {"ticker": t, "mentions_now": now_n, "trailing_avg": base, "baseline_obs": n_obs,
               "velocity_ratio": (None if vr == float("inf") else vr), "spike": spike,
               "pool_fed": pool_fed, "sample_headlines": samples}
        if pool_fed:
            feed_convergence(t, f"narrative velocity spike: {now_n} mentions/{days}d vs trailing {base} ({n_obs}obs)")
        out.append(row)
    out.sort(key=lambda r: (r.get("spike") is True, r.get("mentions_now") or 0), reverse=True)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", default=",".join(DEFAULT))
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--min-spike", type=int, default=3, help="min recent mentions to qualify as a spike")
    ap.add_argument("--ratio", type=float, default=2.0, help="current must be >= ratio x trailing baseline")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    tickers = [t.strip().upper() for t in a.tickers.split(",") if t.strip()]
    rows = run(tickers, a.days, a.min_spike, a.ratio)

    if a.json:
        print(json.dumps(rows, indent=2))
        return
    spikes = [r for r in rows if r.get("spike")]
    print(f"\n=== NARRATIVE VELOCITY ({a.days}d window) ===\n")
    if not spikes:
        print("  No mention-velocity spikes. (Baselines build over a few days of runs.)")
    for r in spikes:
        vr = r["velocity_ratio"]
        print(f"  [SPIKE] {r['ticker']:5s}  {r['mentions_now']} mentions vs trailing {r['trailing_avg']}"
              f"  (x{vr if vr is not None else '∞'})")
        for h in r["sample_headlines"]:
            print(f"          - {h}")
    print("\n  Educational only — not advice. Spikes appended to the convergence pool.\n")


if __name__ == "__main__":
    main()
