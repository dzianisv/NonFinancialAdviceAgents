#!/usr/bin/env python3
"""stocks-advisor TRIAGE — an ATTENTION RANKER. It never emits a verdict.

WHY THIS FILE REPLACED scorecard.py
-----------------------------------
`scorecard.py` was a static rule engine that emitted ACTIONS (HOLD/TRIM/EXIT/
ADD/WAIT). Two things were structurally wrong with it and both bit the same
ticker twice:

  1. UNREACHABLE STATES. Its rules were a first-match-wins tree whose branches
     were gated on *windows* of drawdown and RSI. On 2026-07-24 NEM — a +119%
     winner trading below BOTH its 50d and 200d MA — matched nothing:
       rule 0.5 (exhaustion HOLD) needed RSI < 40 ....... NEM RSI = 47.9  ✗
       rule 0.7 (early trend-break TRIM) needed dd > -25% NEM dd  = -29.6% ✗
     The position fell through into rule 4 and the script confidently printed
     WAIT ("do nothing"). The whole quadrant {dd <= -25% AND RSI >= 40} had NO
     trend-break coverage. Widening a threshold would not have fixed the class
     of bug — the tree was partial by construction.

  2. TECHNICALS ORIGINATING SELLS. Rule 3 emitted TRIM on "expensive + uptrend"
     — a pure price/multiple read. MRVL got a TRIM that no thesis seat had
     asked for.

The fix is not a better tree. The fix is that this script STOPS DECIDING.

WHAT THIS FILE DOES NOW
-----------------------
One job: guarantee that every position in the book gets screened, and rank
which ones deserve a full analyst panel. Its output vocabulary is:

    REVIEW_NOW  >  REVIEW  >  NO_ACTION

and nothing else. There is no HOLD, TRIM, EXIT, ADD, BUY, SELL or WAIT in this
file's output. Verdicts come from the panel seats (see SKILL.md §Step 2 and
§SELL ORIGINATION RULE).

TOTALITY (the anti-unreachable-state design)
--------------------------------------------
There is no decision tree and no first-match-wins ordering. Every CHECK in
CHECKS runs on every name, independently, and each returns EXACTLY ONE finding
with status FIRED | CLEAR | MISSING. Therefore:

  * len(record["findings"]) == len(CHECKS) for every possible input — proven by
    test_triage.py's enumeration of the (drawdown x RSI x trend x weight x gain
    x quote_type x missingness) grid.
  * NO_ACTION is not a fall-through: it is emitted only when every check
    explicitly returned CLEAR, and the basis string names how many checks were
    evaluated to get there.
  * A missing input can never be silently absorbed into a "neutral" score. It
    produces status=MISSING, names the absent field, and RAISES attention. The
    old file's `if fy is None: return 0, "valuation: no FCF data (neutral)"`
    is exactly the pattern that is now banned.

SELL-ORIGINATION METADATA
-------------------------
Each finding carries `may_originate_sell`. Only THESIS-class findings
(fundamental deterioration) are eligible, and even then this script only routes
the name to the seats that can adjudicate it — it does not itself conclude
anything. PRICE-class findings are hard-coded `may_originate_sell: False`; they
are timing/stop context only. This encodes SKILL.md's SELL ORIGINATION RULE in
machine-readable form so a downstream consumer cannot accidentally read a
trend break as a sell signal.

Usage:
  python3 triage.py [<fundamentals.out.json | dir_of_out_jsons>] \
      [--positions positions.csv] [--hold-only TICK1,TICK2] [--out-dir DIR] [--json]

  Target defaults to .cache/stocks-advisor/fundamentals/. --out-dir defaults to
  .cache/stocks-advisor/ and receives _triage.json. Neither ever writes into
  this scripts/ directory.

positions.csv (optional, gives concentration + gain context):
  Position,MarketValue,Unrealized_PnL,Type   (header flexible; ticker + MV used)
  A Type value tagged 'crypto-beta' / 'hold-only' marks the row hold-only. This
  script has no hardcoded ticker list and no asset-class preference.
"""
import json, sys, os, glob, csv

DEFAULT_TARGET_DIR = os.path.join(".cache", "stocks-advisor", "fundamentals")
DEFAULT_OUT_DIR = os.path.join(".cache", "stocks-advisor")
OUT_FILENAME = "_triage.json"

# ---- attention vocabulary (the ONLY vocabulary this script may emit) -------
# Ordinal, ascending urgency. These are ATTENTION levels, not actions: they say
# "how hard should a human/panel look at this", never "what should be done".
NO_ACTION = "NO_ACTION"
REVIEW = "REVIEW"
REVIEW_NOW = "REVIEW_NOW"
ATTENTION_ORDER = (NO_ACTION, REVIEW, REVIEW_NOW)

# Vocabulary this script is FORBIDDEN to emit. test_triage.py asserts none of
# these ever appears as an attention level, a finding status, or a severity,
# and that the source contains no `return "<verb>"`.
BANNED_DECISION_TOKENS = frozenset({
    "BUY", "SELL", "HOLD", "ADD", "TRIM", "EXIT", "WAIT", "SKIP",
    "REVIEW_THESIS", "PASS",
})

# finding statuses
FIRED, CLEAR, MISSING = "FIRED", "CLEAR", "MISSING"

# finding classes — decides whether a finding may ORIGINATE a sell downstream
CLASS_THESIS = "THESIS"   # company fundamentals — MAY originate a sell (seats adjudicate)
CLASS_PRICE = "PRICE"     # price/technical — may NEVER originate a sell
CLASS_RISK = "RISK"       # sizing/risk control — a sizing action, not a thesis sell
CLASS_DATA = "DATA"       # data integrity — escalates attention, decides nothing

# quoteType values that are baskets, not operating companies.
FUND_QUOTE_TYPES = ("ETF", "MUTUALFUND", "INDEX", "CURRENCY", "COMMODITY")


def _num(d, *keys):
    """Numeric field or None. NOTE: callers must treat None as MISSING and say
    so — never as a neutral default. That conflation was the old file's bug."""
    for k in keys:
        v = d.get(k)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return float(v)
    return None


def _max_attention(levels):
    idx = max((ATTENTION_ORDER.index(l) for l in levels), default=0)
    return ATTENTION_ORDER[idx]


# ---------------------------------------------------------------------------
# Position relevance — used to GRADE attention, never to suppress a finding.
# ---------------------------------------------------------------------------
# Relevance answers "if this name is deteriorating, how much does it cost us?"
# It is deliberately incapable of turning a FIRED finding into CLEAR: the worst
# it can do is grade REVIEW_NOW down to REVIEW, and only when the position
# context is KNOWN. Unknown-but-expected context escalates instead (see below).
REL_HIGH = "HIGH"          # heavy weight and/or large locked-in gain
REL_LOW = "LOW"            # small position, small/no gain
REL_NONE = "NO_POSITION"   # watchlist candidate — no holdings context supplied
REL_UNKNOWN = "UNKNOWN"    # position exists but its MV/PnL could not be parsed


def position_relevance(weight_pct, gain_pct, position_context):
    """position_context: 'HELD' | 'NOT_HELD' | 'UNPARSEABLE'.

    Returns (relevance, note). UNPARSEABLE is a data failure, NOT a small
    position — it must escalate, which is why it maps to REL_UNKNOWN and never
    to REL_LOW."""
    if position_context == "NOT_HELD":
        return REL_NONE, "no holdings context (watchlist candidate)"
    if position_context == "UNPARSEABLE" or (weight_pct is None and gain_pct is None):
        return REL_UNKNOWN, "position held but weight/gain unparseable — cannot grade relevance"
    heavy = weight_pct is not None and weight_pct >= 5
    big_winner = gain_pct is not None and gain_pct >= 50
    sizeable_winner = (weight_pct is not None and weight_pct >= 3
                       and gain_pct is not None and gain_pct >= 25)
    bits = []
    if weight_pct is not None:
        bits.append(f"{weight_pct:.1f}% of book")
    if gain_pct is not None:
        bits.append(f"{gain_pct:+.0f}% unrealized")
    note = ", ".join(bits) if bits else "partial position context"
    if heavy or big_winner or sizeable_winner:
        return REL_HIGH, note
    return REL_LOW, note


# Findings that may NEVER be graded below REVIEW, no matter how small the
# position. These are the two that caused the NEM and MRVL incidents plus the
# two risk/data checks whose suppression would blind the whole run. Relevance
# grading exists to RANK, and it is not allowed to silence these.
SEVERITY_FLOOR = {
    "TREND_BREAK_200D": REVIEW,
    "THESIS_DETERIORATION": REVIEW,
    "CONCENTRATION": REVIEW,
    "PRICE_INTEGRITY": REVIEW_NOW,
}


def _grade(code, base_high, relevance):
    """Grade a FIRED finding's severity by position relevance, so triage RANKS
    instead of flagging everything equally.

    Three hard rules keep this from re-creating a blind spot:
      * REL_UNKNOWN grades UP to REVIEW_NOW — missing context never buys silence.
      * SEVERITY_FLOOR codes can never fall below their floor.
      * A graded-down finding is still FIRED and still printed in the record and
        the basis line. Grading changes URGENCY, never visibility.
    """
    floor = SEVERITY_FLOOR.get(code, NO_ACTION)

    def clamp(sev):
        return sev if ATTENTION_ORDER.index(sev) >= ATTENTION_ORDER.index(floor) else floor

    if relevance == REL_UNKNOWN:
        return clamp(REVIEW_NOW)
    if relevance == REL_HIGH:
        return clamp(base_high)
    if relevance == REL_LOW:
        # A held but immaterial position: noted, not urgent.
        return clamp(NO_ACTION if base_high == REVIEW else REVIEW)
    # REL_NONE — watchlist candidate, no size to grade by: keep the base level.
    return clamp(base_high)


# ---------------------------------------------------------------------------
# CHECKS — each returns exactly one finding for ANY input. No check may return
# None, and no check may short-circuit another. This is what makes the triage
# a TOTAL function over the input space.
# ---------------------------------------------------------------------------

def _finding(code, cls, status, severity, detail, missing_fields=None):
    return {
        "code": code,
        "class": cls,
        "status": status,
        "severity": severity,
        "detail": detail,
        "missing_fields": list(missing_fields or []),
        # Hard-encodes SKILL.md's SELL ORIGINATION RULE: only THESIS-class
        # evidence may originate a sell, and only once a seat confirms it.
        "may_originate_sell": (cls == CLASS_THESIS and status == FIRED),
        "risk_control": (cls == CLASS_RISK and status == FIRED),
    }


def check_concentration(ctx):
    w = ctx["weight_pct"]
    if ctx["position_context"] == "NOT_HELD":
        return _finding("CONCENTRATION", CLASS_RISK, CLEAR, NO_ACTION,
                        "not a held position — concentration not applicable")
    if w is None:
        return _finding("CONCENTRATION", CLASS_RISK, MISSING, REVIEW_NOW,
                        "held position but weight could not be computed (MarketValue absent/unparseable) "
                        "— concentration risk CANNOT be ruled out", ["weight_pct"])
    if w >= 15:
        return _finding("CONCENTRATION", CLASS_RISK, FIRED, REVIEW_NOW,
                        f"single-name weight {w:.1f}% >= 15% cap — sizing review (risk control, "
                        f"not a thesis sell)")
    if w >= 10:
        return _finding("CONCENTRATION", CLASS_RISK, FIRED, REVIEW,
                        f"single-name weight {w:.1f}% in the 10-15% pre-cap band — sizing review")
    return _finding("CONCENTRATION", CLASS_RISK, CLEAR, NO_ACTION,
                    f"weight {w:.1f}% below the 10% pre-cap band")


def check_trend_break_200d(ctx):
    """THE NEM FIX. Fires on ANY close below the 200d MA, at ANY drawdown depth
    and ANY RSI. The old rule 0.7 gated this on -25% < dd <= -8%, which left the
    deep-drawdown-but-not-oversold quadrant with no coverage at all. There is no
    window here: below the 200d is below the 200d.

    PRICE class => may_originate_sell is False. A trend break is a WATCH plus an
    armed alert. It becomes an exit only if a thesis seat independently finds
    impairment (SKILL.md §SELL ORIGINATION RULE)."""
    v200 = ctx["vs_200d_ma"]
    if v200 is None:
        return _finding("TREND_BREAK_200D", CLASS_PRICE, MISSING, REVIEW_NOW,
                        "vs_200d_ma absent — trend state UNKNOWN, cannot screen for a trend break",
                        ["vs_200d_ma"])
    if v200 < 0:
        return _finding("TREND_BREAK_200D", CLASS_PRICE, FIRED,
                        _grade("TREND_BREAK_200D", REVIEW_NOW, ctx["relevance"]),
                        f"price {v200:+.1f}% vs 200d MA — below the long-term trend "
                        f"({ctx['relevance_note']}). WATCH + arm an exit alert; a sell requires a "
                        f"thesis seat to find impairment.")
    return _finding("TREND_BREAK_200D", CLASS_PRICE, CLEAR, NO_ACTION,
                    f"price {v200:+.1f}% vs 200d MA — long-term trend intact")


def check_trend_break_50d(ctx):
    v50 = ctx["vs_50d_ma"]
    if v50 is None:
        return _finding("TREND_BREAK_50D", CLASS_PRICE, MISSING, REVIEW,
                        "vs_50d_ma absent — near-term trend state UNKNOWN", ["vs_50d_ma"])
    if v50 < 0:
        return _finding("TREND_BREAK_50D", CLASS_PRICE, FIRED,
                        _grade("TREND_BREAK_50D", REVIEW, ctx["relevance"]),
                        f"price {v50:+.1f}% vs 50d MA — near-term rollover ({ctx['relevance_note']}). "
                        f"Early warning only; never a sell on its own.")
    return _finding("TREND_BREAK_50D", CLASS_PRICE, CLEAR, NO_ACTION,
                    f"price {v50:+.1f}% vs 50d MA — near-term trend intact")


def check_drawdown(ctx):
    """Graded, NOT windowed. Every drawdown value maps somewhere: the old file's
    (-25, -8] window is gone, so nothing can fall between two bands."""
    dd = ctx["dd_from_52wh"]
    if dd is None:
        return _finding("DRAWDOWN", CLASS_PRICE, MISSING, REVIEW,
                        "dd_from_52wh absent — drawdown UNKNOWN", ["dd_from_52wh"])
    if dd <= -25:
        return _finding("DRAWDOWN", CLASS_PRICE, FIRED, _grade("DRAWDOWN", REVIEW_NOW, ctx["relevance"]),
                        f"{dd:.1f}% from the 52w high — deep drawdown ({ctx['relevance_note']}). "
                        f"Context for the panel; selling into a washout is a timing decision, "
                        f"not a thesis one.")
    if dd <= -8:
        return _finding("DRAWDOWN", CLASS_PRICE, FIRED, _grade("DRAWDOWN", REVIEW, ctx["relevance"]),
                        f"{dd:.1f}% from the 52w high — moderate drawdown ({ctx['relevance_note']})")
    return _finding("DRAWDOWN", CLASS_PRICE, CLEAR, NO_ACTION,
                    f"{dd:.1f}% from the 52w high — near the highs")


def check_momentum_state(ctx):
    """RSI is CONTEXT for the panel's timing, never a trigger of its own action.
    Both tails are reported so the panel knows whether a trend break is a fresh
    rollover (RSI mid-range, still liquid to exit) or an already-washed-out
    crash (RSI < 40, where exiting is selling the bottom)."""
    rsi = ctx["rsi14"]
    if rsi is None:
        return _finding("MOMENTUM_STATE", CLASS_PRICE, MISSING, REVIEW,
                        "rsi14 absent — momentum state UNKNOWN", ["rsi14"])
    if rsi < 40:
        return _finding("MOMENTUM_STATE", CLASS_PRICE, FIRED,
                        _grade("MOMENTUM_STATE", REVIEW, ctx["relevance"]),
                        f"RSI(14) {rsi:.0f} — washed out. Timing note for the panel: an exit here "
                        f"sells into the hole; the actionable exit was earlier.")
    if rsi > 70:
        return _finding("MOMENTUM_STATE", CLASS_PRICE, FIRED,
                        _grade("MOMENTUM_STATE", REVIEW, ctx["relevance"]),
                        f"RSI(14) {rsi:.0f} — extended. Timing note only; being extended is not "
                        f"thesis impairment.")
    return _finding("MOMENTUM_STATE", CLASS_PRICE, CLEAR, NO_ACTION,
                    f"RSI(14) {rsi:.0f} — mid-range, no momentum extreme")


THESIS_FIELDS = ("earnings_growth", "revenue_growth", "operating_margin", "fcf_yield")


def check_thesis_deterioration(ctx):
    """The ONLY check in this file whose FIRED finding is sell-origination
    eligible — and even then it only routes the name to the fundamentals seat.
    The seat, not this script, decides whether the thesis is impaired."""
    if ctx["no_fundamental_basis"]:
        return _finding("THESIS_DETERIORATION", CLASS_THESIS, CLEAR, NO_ACTION,
                        "basket/fund instrument — no company fundamentals to deteriorate "
                        "(see NO_FUNDAMENTAL_BASIS)")
    d = ctx["raw"]
    present = {f: _num(d, f) for f in THESIS_FIELDS}
    absent = [f for f, v in present.items() if v is None]
    if len(absent) == len(THESIS_FIELDS):
        return _finding("THESIS_DETERIORATION", CLASS_THESIS, MISSING, REVIEW_NOW,
                        "an EQUITY with every fundamental input absent (" + ", ".join(absent) +
                        ") — the fundamental read is BLIND, not neutral", absent)
    bad = []
    if present["earnings_growth"] is not None and present["earnings_growth"] < 0:
        bad.append(f"EPS growth {present['earnings_growth']:.0f}%")
    if present["revenue_growth"] is not None and present["revenue_growth"] < 0:
        bad.append(f"revenue {present['revenue_growth']:.0f}%")
    if present["operating_margin"] is not None and present["operating_margin"] < 0:
        bad.append(f"op margin {present['operating_margin']:.0f}%")
    if present["fcf_yield"] is not None and present["fcf_yield"] < 0:
        bad.append(f"FCF yield {present['fcf_yield']:.1f}% (burning cash)")
    if bad:
        sev = _grade("THESIS_DETERIORATION", REVIEW_NOW, ctx["relevance"])
        detail = ("deteriorating fundamentals: " + "; ".join(bad) +
                  ". SELL-ORIGINATION ELIGIBLE — route to the fundamentals seat, which must "
                  "confirm or reject thesis impairment with evidence.")
        if absent:
            detail += " Partial data — absent: " + ", ".join(absent) + "."
        return _finding("THESIS_DETERIORATION", CLASS_THESIS, FIRED, sev, detail, absent)
    if absent:
        return _finding("THESIS_DETERIORATION", CLASS_THESIS, MISSING, REVIEW,
                        "no deterioration in the fundamentals present, but absent: " +
                        ", ".join(absent) + " — partial read, not a clean bill of health", absent)
    return _finding("THESIS_DETERIORATION", CLASS_THESIS, CLEAR, NO_ACTION,
                    "no negative EPS growth / revenue / op margin / FCF yield")


def check_no_fundamental_basis(ctx):
    """ETF / commodity / thematic basket detection.

    Split from the old file deliberately: the old `no_fundamental_basis()` also
    returned True for an EQUITY whose fundamentals all failed to load, which
    disguised a DATA FAILURE as an instrument-type classification. Here a fund
    quote_type is a routing fact; an equity with null fundamentals is a MISSING
    finding on check_thesis_deterioration instead."""
    qt = ctx["quote_type"]
    if qt is None or qt == "":
        return _finding("NO_FUNDAMENTAL_BASIS", CLASS_DATA, MISSING, REVIEW,
                        "quote_type absent — cannot confirm whether this is an operating company "
                        "or a basket", ["quote_type"])
    if qt in FUND_QUOTE_TYPES:
        return _finding("NO_FUNDAMENTAL_BASIS", CLASS_DATA, FIRED,
                        _grade("NO_FUNDAMENTAL_BASIS", REVIEW, ctx["relevance"]),
                        f"instrument type {qt} — a basket, not an operating company. The own/size "
                        f"question is a macro/sleeve call: route to tradfi-portfolio-manager or "
                        f"analyse-macro. No company-fundamental seat applies.")
    return _finding("NO_FUNDAMENTAL_BASIS", CLASS_DATA, CLEAR, NO_ACTION,
                    f"instrument type {qt} — operating company, normal seat routing")


def check_short_interest(ctx):
    sp = _num(ctx["raw"], "short_percent")
    if sp is None:
        return _finding("SHORT_INTEREST", CLASS_DATA, MISSING, REVIEW,
                        "short_percent absent — crowding/squeeze risk unscreened", ["short_percent"])
    if sp >= 15:
        return _finding("SHORT_INTEREST", CLASS_DATA, FIRED,
                        _grade("SHORT_INTEREST", REVIEW, ctx["relevance"]),
                        f"short interest {sp:.1f}% of float — crowded short; the smart-money seat "
                        f"must read the CHANGE, not the level")
    return _finding("SHORT_INTEREST", CLASS_DATA, CLEAR, NO_ACTION,
                    f"short interest {sp:.1f}% of float — not crowded")


def check_event_soon(ctx):
    days = _num(ctx["raw"], "days_to_earnings")
    if days is None:
        return _finding("EVENT_SOON", CLASS_DATA, MISSING, REVIEW,
                        "days_to_earnings absent — cannot tell whether a print is imminent",
                        ["days_to_earnings"])
    if 0 <= days <= 10:
        edate = ctx["raw"].get("next_earnings_date") or "date unknown"
        return _finding("EVENT_SOON", CLASS_DATA, FIRED,
                        _grade("EVENT_SOON", REVIEW, ctx["relevance"]),
                        f"earnings in {int(days)}d ({edate}) — stage any action around the print")
    return _finding("EVENT_SOON", CLASS_DATA, CLEAR, NO_ACTION,
                    f"next print {int(days)}d out — no imminent event")


def check_valuation_stretch(ctx):
    """Reported so the panel sees it. Explicitly NOT sell-origination eligible:
    'expensive' is a price/multiple observation, and the old rule 3 turning it
    into a TRIM (the MRVL case) is precisely what the SELL ORIGINATION RULE
    forbids."""
    if ctx["no_fundamental_basis"]:
        return _finding("VALUATION_STRETCH", CLASS_PRICE, CLEAR, NO_ACTION,
                        "basket/fund instrument — no company valuation applies")
    fy = _num(ctx["raw"], "fcf_yield")
    fpe = _num(ctx["raw"], "forward_pe")
    if fy is None and fpe is None:
        return _finding("VALUATION_STRETCH", CLASS_PRICE, MISSING, REVIEW,
                        "fcf_yield and forward_pe both absent — valuation UNSCREENED, not 'fair'",
                        ["fcf_yield", "forward_pe"])
    bits = []
    if fy is not None and fy < 3:
        bits.append(f"FCF yield {fy:.1f}%")
    if fpe is not None and fpe > 40:
        bits.append(f"fwd P/E {fpe:.0f}")
    absent = [f for f, v in (("fcf_yield", fy), ("forward_pe", fpe)) if v is None]
    if bits:
        return _finding("VALUATION_STRETCH", CLASS_PRICE, FIRED,
                        _grade("VALUATION_STRETCH", REVIEW, ctx["relevance"]),
                        "richly valued (" + ", ".join(bits) + ") — context for sizing/entry only. "
                        "NOT sell-origination eligible: a high multiple is not thesis impairment.",
                        absent)
    if absent:
        return _finding("VALUATION_STRETCH", CLASS_PRICE, MISSING, REVIEW,
                        "partial valuation data — absent: " + ", ".join(absent), absent)
    return _finding("VALUATION_STRETCH", CLASS_PRICE, CLEAR, NO_ACTION,
                    f"valuation not stretched (FCF yield {fy:.1f}%)")


def check_price_integrity(ctx):
    """A name with no price is not a NO_ACTION name — it is an unscreened name."""
    px = ctx["price"]
    if px is None:
        return _finding("PRICE_INTEGRITY", CLASS_DATA, MISSING, REVIEW_NOW,
                        "price absent — the name was NOT screened; nothing below can be trusted",
                        ["price"])
    return _finding("PRICE_INTEGRITY", CLASS_DATA, CLEAR, NO_ACTION, f"price ${px:.2f} present")


def check_upstream_data_error(ctx):
    """fundamentals.py now records WHY a field is null (`data_errors`) instead of
    swallowing the exception. Surface it: a null caused by a broken fetch is a
    very different fact from a null the company genuinely has no value for, and
    collapsing the two is the silent-default bug class."""
    errs = ctx["raw"].get("data_errors")
    if isinstance(errs, list) and errs:
        return _finding("UPSTREAM_DATA_ERROR", CLASS_DATA, MISSING, REVIEW,
                        "fundamentals.py reported " + str(len(errs)) +
                        " upstream fetch error(s): " + " | ".join(str(e) for e in errs[:3]),
                        ["upstream:" + str(e).split(":")[0] for e in errs[:3]])
    if errs is None:
        # Older cache written before fundamentals.py recorded reasons. Say so
        # rather than pretending the fetch was clean.
        return _finding("UPSTREAM_DATA_ERROR", CLASS_DATA, CLEAR, NO_ACTION,
                        "no data_errors field (cache predates error recording) — "
                        "upstream fetch health unknown, not confirmed clean")
    return _finding("UPSTREAM_DATA_ERROR", CLASS_DATA, CLEAR, NO_ACTION,
                    "fundamentals.py reported no upstream fetch errors")


CHECKS = (
    check_price_integrity,
    check_upstream_data_error,
    check_no_fundamental_basis,
    check_concentration,
    check_trend_break_200d,
    check_trend_break_50d,
    check_drawdown,
    check_momentum_state,
    check_thesis_deterioration,
    check_valuation_stretch,
    check_short_interest,
    check_event_soon,
)

# Seats a finding routes to. PRICE-class findings deliberately route to the
# technical seat for TIMING ONLY — never as the originator of an action.
ROUTING = {
    "THESIS_DETERIORATION": ["fundamentals", "narrative", "smartmoney"],
    "NO_FUNDAMENTAL_BASIS": ["macro/sleeve (tradfi-portfolio-manager)"],
    "CONCENTRATION": ["risk/sizing (stock-chair)"],
    "TREND_BREAK_200D": ["technical (timing only)", "narrative", "smartmoney"],
    "TREND_BREAK_50D": ["technical (timing only)"],
    "DRAWDOWN": ["technical (timing only)", "narrative"],
    "MOMENTUM_STATE": ["technical (timing only)"],
    "VALUATION_STRETCH": ["fundamentals (context)"],
    "SHORT_INTEREST": ["smartmoney"],
    "EVENT_SOON": ["fundamentals", "sellside"],
    "PRICE_INTEGRITY": ["data — re-run fundamentals.py"],
    "UPSTREAM_DATA_ERROR": ["data — re-run fundamentals.py"],
}


def triage_one(d, position=None, hold_only=False):
    """Evaluate every check. Returns one record. Total over the input space:
    every input produces len(CHECKS) findings and exactly one attention level."""
    d = d or {}
    position = position or {}
    position_context = position.get("context", "NOT_HELD")
    weight_pct = position.get("weight")
    gain_pct = position.get("gain_pct")
    relevance, relevance_note = position_relevance(weight_pct, gain_pct, position_context)
    qt = d.get("quote_type")
    qt = str(qt).upper() if qt is not None else None
    ctx = {
        "raw": d,
        "symbol": d.get("symbol") or position.get("symbol") or "?",
        "price": _num(d, "price"),
        "vs_200d_ma": _num(d, "vs_200d_ma"),
        "vs_50d_ma": _num(d, "vs_50d_ma"),
        "dd_from_52wh": _num(d, "dd_from_52wh"),
        "rsi14": _num(d, "rsi14"),
        "quote_type": qt,
        "no_fundamental_basis": qt in FUND_QUOTE_TYPES if qt else False,
        "weight_pct": weight_pct,
        "gain_pct": gain_pct,
        "position_context": position_context,
        "relevance": relevance,
        "relevance_note": relevance_note,
    }

    findings = [chk(ctx) for chk in CHECKS]
    # Structural invariant: one finding per check, always. Enforced here so a
    # future check that forgets to return cannot silently shrink the coverage.
    assert len(findings) == len(CHECKS), "a check failed to return a finding"
    for f in findings:
        assert f["status"] in (FIRED, CLEAR, MISSING), f"illegal status {f['status']}"
        assert f["severity"] in ATTENTION_ORDER, f"illegal severity {f['severity']}"

    fired = [f for f in findings if f["status"] == FIRED]
    missing = [f for f in findings if f["status"] == MISSING]
    attention = _max_attention([f["severity"] for f in findings])

    missing_fields = sorted({m for f in missing for m in f["missing_fields"]})
    if missing and attention == NO_ACTION:
        # Unreachable by construction (every MISSING severity is >= REVIEW), but
        # asserted rather than assumed: a missing input must never buy silence.
        attention = REVIEW

    # A FIRED finding graded to NO_ACTION is INFORMATIONAL, not suppressed. It is
    # always named in `fired`, in `informational`, and in the basis string, so the
    # record can never read as "nothing was found" when something was.
    informational = [f for f in fired if f["severity"] == NO_ACTION]
    escalating = [f for f in fired if f["severity"] != NO_ACTION]

    if fired or missing:
        parts = []
        if escalating:
            parts.append(f"{len(escalating)} check(s) fired: " +
                         ", ".join(f["code"] for f in escalating))
        if missing:
            parts.append(f"{len(missing)} check(s) MISSING data: " +
                         ", ".join(f"{f['code']}({','.join(f['missing_fields']) or 'n/a'})"
                                   for f in missing))
        if informational:
            parts.append(f"{len(informational)} check(s) fired but INFORMATIONAL at this "
                         f"position size ({relevance_note}) — recorded, not escalated: " +
                         ", ".join(f["code"] for f in informational))
        basis = " | ".join(parts)
    else:
        basis = (f"all {len(CHECKS)} triage checks evaluated and CLEAR with complete inputs "
                 f"— no attention warranted this run")

    routes = []
    for f in fired + missing:
        for r in ROUTING.get(f["code"], []):
            if r not in routes:
                routes.append(r)

    sell_eligible = [f["code"] for f in findings if f["may_originate_sell"]]

    return {
        "symbol": ctx["symbol"],
        "price": ctx["price"],
        "attention": attention,
        "basis": basis,
        "weight_pct": weight_pct,
        "gain_pct": gain_pct,
        "position_context": position_context,
        "relevance": relevance,
        "hold_only": bool(hold_only),
        "checks_evaluated": len(findings),
        "fired": [f["code"] for f in fired],
        "informational": [f["code"] for f in informational],
        "missing": [f["code"] for f in missing],
        "missing_fields": missing_fields,
        "data_status": "MISSING" if missing else "OK",
        "sell_origination_eligible": sell_eligible,
        "route_to_seats": routes,
        "findings": findings,
        "disclaimer": ("TRIAGE ONLY — this is an attention level, not a verdict. No BUY/SELL/HOLD/"
                       "TRIM/EXIT/ADD/WAIT may be derived from this record. Verdicts come from the "
                       "panel seats; a SELL additionally requires thesis impairment found by the "
                       "fundamentals, narrative or smart-money seat (SKILL.md §SELL ORIGINATION RULE)."),
    }


# ---- positions loading -----------------------------------------------------
HOLD_ONLY_TYPES = ("crypto-beta", "hold-only", "hold only")


def _parse_float(s):
    """Returns (value, error). Never silently swallows a parse failure — the old
    file's bare `except: pass` turned a malformed row into a None that then read
    as 'no position context'."""
    if s is None:
        return None, "absent"
    s = str(s).strip().replace(",", "").replace("$", "")
    if s == "":
        return None, "empty"
    try:
        return float(s), None
    except ValueError:
        return None, f"unparseable value {s!r}"


def load_positions(path, hold_only_arg=None):
    """Returns (positions_dict, load_errors). Every row that fails to parse is
    reported, never dropped."""
    out, errors = {}, []
    hold_only_arg = hold_only_arg or set()
    if not path:
        return out, errors
    if not os.path.exists(path):
        errors.append(f"positions file not found: {path}")
        return out, errors
    with open(path) as f:
        rows = list(csv.reader(f))
    if not rows:
        errors.append(f"positions file empty: {path}")
        return out, errors
    hdr = [h.strip().lower() for h in rows[0]]

    def idx(*names):
        for n in names:
            if n in hdr:
                return hdr.index(n)
        return None

    ti = idx("position", "ticker", "symbol")
    mi = idx("marketvalue", "market_value", "mv")
    pi = idx("unrealized_pnl", "pnl", "unrealized")
    tyi = idx("type")
    if ti is None:
        errors.append(f"positions file {path}: no ticker column (looked for position/ticker/symbol)")
        return out, errors
    if mi is None:
        errors.append(f"positions file {path}: no MarketValue column — every weight will be MISSING")
    for lineno, r in enumerate(rows[1:], start=2):
        if ti >= len(r):
            errors.append(f"{path}:{lineno}: short row, no ticker")
            continue
        t = r[ti].strip().upper()
        if not t:
            errors.append(f"{path}:{lineno}: blank ticker")
            continue
        mv, mv_err = _parse_float(r[mi] if (mi is not None and mi < len(r)) else None)
        pnl, pnl_err = _parse_float(r[pi] if (pi is not None and pi < len(r)) else None)
        if mv_err:
            errors.append(f"{path}:{lineno} [{t}]: MarketValue {mv_err}")
        row_type = (r[tyi].strip().lower() if (tyi is not None and tyi < len(r)) else "")
        out[t] = {
            "symbol": t, "mv": mv, "pnl": pnl,
            "mv_error": mv_err, "pnl_error": pnl_err,
            "hold_only": (row_type in HOLD_ONLY_TYPES) or (t in hold_only_arg),
            "context": "UNPARSEABLE" if mv_err else "HELD",
        }
    total = sum(v["mv"] for v in out.values() if v["mv"]) or None
    for v in out.values():
        v["weight"] = (100.0 * v["mv"] / total) if (total and v["mv"] is not None) else None
        v["gain_pct"] = _gain_pct(v["mv"], v["pnl"])
    return out, errors


def _gain_pct(mv, pnl):
    if mv is None or pnl is None:
        return None
    cost = mv - pnl
    if cost <= 0:
        return None
    return round(pnl / cost * 100.0, 1)


# ---- driver ----------------------------------------------------------------

def main():
    args = sys.argv[1:]
    pos_path, out_dir, as_json = None, None, False
    hold_only_arg = set()
    if "--positions" in args:
        i = args.index("--positions"); pos_path = args[i + 1]; del args[i:i + 2]
    if "--hold-only" in args:
        i = args.index("--hold-only")
        hold_only_arg = {t.strip().upper() for t in args[i + 1].split(",") if t.strip()}
        del args[i:i + 2]
    if "--out-dir" in args:
        i = args.index("--out-dir"); out_dir = args[i + 1]; del args[i:i + 2]
    if "--json" in args:
        as_json = True; args.remove("--json")

    # An UNRECOGNISED flag must never fall through to the positional target. A
    # typo'd `--research-dir <path>` used to become the screen directory, glob
    # zero files, and still print a confident "1 names screened" summary over a
    # book of ~80 — a bad invocation that reads like a clean run. Same bug class
    # as a default masking a missing input: fail loudly instead.
    unknown = [a for a in args if a.startswith("-")]
    if unknown:
        sys.exit("triage.py: unrecognised option(s): %s\n"
                 "usage: triage.py [SCREEN_DIR] [--positions CSV] [--hold-only T1,T2] "
                 "[--out-dir DIR] [--json]" % ", ".join(unknown))
    if len(args) > 1:
        sys.exit("triage.py: expected at most one screen directory, got: %s" % ", ".join(args))
    target = args[0] if args else DEFAULT_TARGET_DIR

    positions, load_errors = load_positions(pos_path, hold_only_arg)

    if not os.path.exists(target):
        sys.exit("triage.py: screen path does not exist: %s\n"
                 "Nothing was screened. Run fundamentals.py first, or pass the correct "
                 "directory. Refusing to print an empty ranking that reads like a clean book."
                 % target)

    files = sorted(glob.glob(os.path.join(target, "*.out.json"))) if os.path.isdir(target) else [target]
    if os.path.isdir(target) and not files and not positions:
        sys.exit("triage.py: no *.out.json under %s and no positions loaded — nothing to "
                 "triage. Refusing to write an empty ranking." % target)

    results, seen = [], set()
    for f in files:
        try:
            d = json.load(open(f))
        except Exception as e:
            # NEVER silently drop. An unreadable screen output is a screening
            # FAILURE for that ticker and must surface at the top of the list.
            sym = os.path.basename(f).replace(".out.json", "").upper()
            rec = triage_one({"symbol": sym}, positions.get(sym, {"context": "NOT_HELD"}),
                             positions.get(sym, {}).get("hold_only", False))
            rec["attention"] = REVIEW_NOW
            rec["data_status"] = "MISSING"
            rec["basis"] = f"screen output UNREADABLE ({f}: {type(e).__name__}: {e}) — NOT screened"
            results.append(rec); seen.add(sym)
            continue
        sym = str(d.get("symbol") or os.path.basename(f).replace(".out.json", "")).upper()
        d.setdefault("symbol", sym)
        p = positions.get(sym, {"context": "NOT_HELD"})
        results.append(triage_one(d, p, p.get("hold_only", False)))
        seen.add(sym)

    # Held positions with NO screen output at all. The old file simply never saw
    # them — a held name could vanish from the whole review. That is the
    # flagship-exclusion bug class; it now surfaces as REVIEW_NOW.
    for sym, p in sorted(positions.items()):
        if sym in seen:
            continue
        rec = triage_one({"symbol": sym}, p, p.get("hold_only", False))
        rec["attention"] = REVIEW_NOW
        rec["data_status"] = "MISSING"
        rec["basis"] = ("HELD POSITION WITH NO SCREEN OUTPUT — fundamentals.py produced no "
                        f"{sym}.out.json under {target}. The position was NOT screened this run; "
                        "it is not 'nothing to do'.")
        rec["missing"] = sorted(set(rec["missing"] + ["NO_SCREEN_OUTPUT"]))
        results.append(rec)

    rank = {REVIEW_NOW: 0, REVIEW: 1, NO_ACTION: 2}
    results.sort(key=lambda r: (rank[r["attention"]], -(r["weight_pct"] or 0), r["symbol"]))

    out_dir = out_dir or DEFAULT_OUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    out_json = os.path.join(out_dir, OUT_FILENAME)
    payload = {
        "kind": "stocks-advisor-triage",
        "contract": "attention levels only (REVIEW_NOW/REVIEW/NO_ACTION) — never a verdict",
        "checks": [c.__name__ for c in CHECKS],
        "positions_load_errors": load_errors,
        "results": results,
    }
    json.dump(payload, open(out_json, "w"), indent=1, default=str)

    if as_json:
        print(json.dumps(payload, indent=1, default=str))
        return

    print("TRIAGE — attention ranking only. This script emits NO verdicts.")
    print("Verdicts come from the panel seats. A SELL requires thesis impairment found by the")
    print("fundamentals, narrative or smart-money seat — technicals may not originate a sell.")
    print()
    if load_errors:
        print("POSITIONS LOAD ERRORS:")
        for e in load_errors:
            print(f"  ! {e}")
        print()
    print(f"{'TICKER':8} {'PX':>9} {'WT%':>6} {'GAIN%':>7}  {'ATTENTION':11} {'DATA':8} FIRED / MISSING")
    print("-" * 132)
    for r in results:
        wt = f"{r['weight_pct']:.1f}" if r["weight_pct"] is not None else "-"
        gp = f"{r['gain_pct']:+.0f}" if r["gain_pct"] is not None else "-"
        px = f"{r['price']:.2f}" if r["price"] is not None else "-"
        ho = " [hold-only]" if r["hold_only"] else ""
        fired = ",".join(r["fired"]) or "-"
        miss = ("  MISSING:" + ",".join(r["missing"])) if r["missing"] else ""
        print(f"{r['symbol']:8} {px:>9} {wt:>6} {gp:>7}  {r['attention']:11} {r['data_status']:8} "
              f"{fired}{miss}{ho}")
    print("-" * 132)
    counts = {lvl: sum(1 for r in results if r["attention"] == lvl) for lvl in ATTENTION_ORDER}
    nmiss = sum(1 for r in results if r["data_status"] == "MISSING")
    print(f"{len(results)} names screened | REVIEW_NOW {counts[REVIEW_NOW]} | "
          f"REVIEW {counts[REVIEW]} | NO_ACTION {counts[NO_ACTION]} | data MISSING {nmiss}")
    print(f"wrote {out_json}")
    print()
    print("NEXT: run the panel on the REVIEW_NOW names. Only the fundamentals / narrative /")
    print("smart-money seats may originate a TRIM or EXIT, and only with stated evidence of")
    print("thesis impairment. A price break with no thesis impairment = WATCH + armed alert.")


if __name__ == "__main__":
    main()
