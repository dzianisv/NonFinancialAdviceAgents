#!/usr/bin/env python3
"""Coverage + contract tests for triage.py.

The headline test is `test_input_space_is_total`: it ENUMERATES the
(drawdown x RSI x trend200 x trend50 x weight x gain x quote_type) input space
and asserts no input falls into a silent default. That is the specific bug class
that caused both NEM incidents — the old scorecard.py had an entire quadrant
({dd <= -25%} AND {RSI >= 40}) that matched no trend-break rule and fell through
to a confident "WAIT".

`test_old_scorecard_gap_is_now_covered` goes further: it re-implements the old
rule 0.5 / 0.7 predicates, finds the inputs that satisfied NEITHER, and asserts
every one of them is now covered. A fix that only widened a threshold window
would fail that test.

Run:  python3 .agents/skills/stocks-advisor/scripts/test_triage.py
"""
import json, os, re, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SKILL_MD = os.path.join(HERE, "..", "SKILL.md")

import triage as T  # noqa: E402
import smartmoney as SM  # noqa: E402


class TestSmartMoneyCompleteness(unittest.TestCase):
    """Smart-money may ORIGINATE a sell, so a partial read must never present
    itself as a complete one. Pure-function tests; no network."""

    @staticmethod
    def _txn(side, shares=100.0, price=10.0, plan=False, officer=True):
        code = "P" if side == "BUY" else "S"
        value = (shares * price) if (shares and price) else None
        return {"code": code, "side": side, "shares": shares, "price": price,
                "value": value, "date": "2026-07-01", "owner": "Doe John",
                "officer": officer, "director": False, "title": "CFO",
                "plan_10b5_1": plan}

    def test_unpriced_transaction_is_flagged_not_silently_zero(self):
        # An unparseable price must not quietly make a real sale worth $0. The
        # seat is required to cite a dollar amount; a fabricated 0 understates
        # exactly the evidence it has to weigh.
        s = SM.summarize_form4({"txns": [self._txn("SELL"),
                                         self._txn("SELL", price=None)]})
        self.assertEqual(s["sell_count"], 2)
        self.assertEqual(s["unpriced_txn_count"], 1)
        self.assertFalse(s["dollar_totals_complete"])
        self.assertIn("FLOOR", s["unpriced_note"])

    def test_fully_priced_reads_as_complete(self):
        s = SM.summarize_form4({"txns": [self._txn("SELL")]})
        self.assertEqual(s["unpriced_txn_count"], 0)
        self.assertTrue(s["dollar_totals_complete"])
        self.assertEqual(s["unpriced_note"], "")

    def test_10b5_1_sale_is_never_strong_evidence(self):
        s = SM.summarize_form4({"txns": [self._txn("SELL", plan=True)]})
        self.assertEqual(s["open_market_sell_count"], 0)
        self.assertIn("NONE", s["sell_evidence_quality"])

    def test_officer_open_market_sale_is_strong_evidence(self):
        s = SM.summarize_form4({"txns": [self._txn("SELL")]})
        self.assertIn("STRONG", s["sell_evidence_quality"])

    def test_form4_fetch_cap_is_high_enough_for_a_real_filer(self):
        # MRVL filed 43 Form 4s in a 120d window on 2026-07-24. At the old cap
        # of 25 the seat saw 1 open-market sale ($632k) instead of 5 ($4.64M)
        # and still reported status OK.
        self.assertGreaterEqual(SM.MAX_FORM4_FETCH, 50)

    def test_xsl_render_path_is_stripped_to_raw_xml(self):
        # `primaryDocument` is the XSL-rendered HTML view; fetching it yields a
        # styled table with zero transaction elements — a false negative.
        url = SM.raw_form4_url("1058057", "000105805726000123", "xslF345X06/form4.xml")
        self.assertNotIn("xslF345X06", url)
        self.assertTrue(url.endswith("form4.xml"), url)

    def test_html_body_is_rejected_rather_than_parsed_to_zero_rows(self):
        self.assertFalse(SM.looks_like_form4_xml("<!DOCTYPE html><html><body>..."))
        self.assertTrue(SM.looks_like_form4_xml("<ownershipDocument><x/></ownershipDocument>"))

# ---------------------------------------------------------------------------
# The enumerated input space. Values are chosen to straddle EVERY threshold that
# appears anywhere in triage.py or in the old scorecard.py, plus the exact
# real-world values from the two incidents.
# ---------------------------------------------------------------------------
DDS = [None, -60.0, -50.0, -40.0, -39.6, -30.0, -29.6, -25.0, -24.9, -15.0,
       -8.0, -7.9, -2.0, 0.0]
RSIS = [None, 15.0, 30.0, 39.9, 40.0, 40.3, 47.9, 55.0, 70.0, 70.1, 85.0]
VS200S = [None, -30.0, -8.5, -0.1, 0.0, 0.1, 50.1]
VS50S = [None, -16.7, -5.7, 0.0, 5.0]
QUOTE_TYPES = [None, "EQUITY", "ETF"]

# (label, position dict) — covers held/not-held/unparseable and the size x gain
# relevance bands.
POSITIONS = [
    ("not_held", {"context": "NOT_HELD"}),
    ("held_small", {"context": "HELD", "weight": 0.7, "gain_pct": -30.0, "symbol": "X"}),
    ("held_midwinner", {"context": "HELD", "weight": 3.5, "gain_pct": 25.0, "symbol": "X"}),
    ("held_bigwinner", {"context": "HELD", "weight": 2.3, "gain_pct": 119.4, "symbol": "X"}),
    ("held_heavy", {"context": "HELD", "weight": 20.0, "gain_pct": 5.0, "symbol": "X"}),
    ("held_unparseable", {"context": "UNPARSEABLE", "weight": None, "gain_pct": None, "symbol": "X"}),
]

CHECK_CODES = {
    "PRICE_INTEGRITY", "UPSTREAM_DATA_ERROR", "NO_FUNDAMENTAL_BASIS", "CONCENTRATION",
    "TREND_BREAK_200D", "TREND_BREAK_50D", "DRAWDOWN", "MOMENTUM_STATE",
    "THESIS_DETERIORATION", "VALUATION_STRETCH", "SHORT_INTEREST", "EVENT_SOON",
}


class TestCheckRegistryIsInSync(unittest.TestCase):
    """The expected-code set above is hand-maintained; this makes a drifted
    registry a loud failure rather than a check that silently stops being
    asserted on."""

    def test_expected_codes_match_the_registry(self):
        rec = T.triage_one({"symbol": "X", "price": 1.0}, None)
        self.assertEqual({f["code"] for f in rec["findings"]}, CHECK_CODES)
        self.assertEqual(len(T.CHECKS), len(CHECK_CODES))


def make_input(dd, rsi, vs200, vs50, qt, fundamentals=True):
    d = {"symbol": "TEST", "price": 100.0, "dd_from_52wh": dd, "rsi14": rsi,
         "vs_200d_ma": vs200, "vs_50d_ma": vs50}
    if qt is not None:
        d["quote_type"] = qt
    if fundamentals and qt != "ETF":
        d.update({"earnings_growth": 11.4, "revenue_growth": 15.1,
                  "operating_margin": 51.6, "fcf_yield": 8.6, "forward_pe": 9.0,
                  "short_percent": 1.2, "days_to_earnings": 64})
    return d


def iter_grid():
    for dd in DDS:
        for rsi in RSIS:
            for vs200 in VS200S:
                for vs50 in VS50S:
                    for qt in QUOTE_TYPES:
                        for plabel, pos in POSITIONS:
                            yield dd, rsi, vs200, vs50, qt, plabel, pos


class TestTotality(unittest.TestCase):
    """Requirement 3: no unreachable states. Every input maps somewhere."""

    def test_input_space_is_total(self):
        n = 0
        silent_defaults = []
        for dd, rsi, vs200, vs50, qt, plabel, pos in iter_grid():
            d = make_input(dd, rsi, vs200, vs50, qt)
            rec = T.triage_one(d, pos)
            n += 1
            ctx = f"dd={dd} rsi={rsi} vs200={vs200} vs50={vs50} qt={qt} pos={plabel}"

            # 1. exactly one attention level, from the allowed vocabulary
            self.assertIn(rec["attention"], T.ATTENTION_ORDER, ctx)
            # 2. EVERY check produced EXACTLY ONE finding — no short-circuit,
            #    no first-match-wins, so no branch can be skipped.
            self.assertEqual(len(rec["findings"]), len(T.CHECKS), ctx)
            self.assertEqual({f["code"] for f in rec["findings"]}, CHECK_CODES, ctx)
            # 3. every finding has a real status, severity and explanation
            for f in rec["findings"]:
                self.assertIn(f["status"], (T.FIRED, T.CLEAR, T.MISSING), ctx + " " + f["code"])
                self.assertIn(f["severity"], T.ATTENTION_ORDER, ctx + " " + f["code"])
                self.assertTrue(f["detail"].strip(), ctx + " " + f["code"] + " has empty detail")
            # 4. the basis is always derived, never blank
            self.assertTrue(rec["basis"].strip(), ctx)
            # 5. THE SILENT-DEFAULT ASSERTION. NO_ACTION may never coexist with
            #    a MISSING input, and any FIRED check it does coexist with must
            #    be explicitly enumerated as INFORMATIONAL in `informational`
            #    AND named in the basis string. Nothing may vanish.
            if rec["attention"] == T.NO_ACTION:
                miss = [f["code"] for f in rec["findings"] if f["status"] == T.MISSING]
                if miss or rec["missing_fields"]:
                    silent_defaults.append((ctx, "MISSING absorbed into NO_ACTION",
                                            miss, rec["missing_fields"]))
                for f in rec["findings"]:
                    if f["status"] == T.FIRED:
                        if f["code"] not in rec["informational"]:
                            silent_defaults.append((ctx, "FIRED not marked informational",
                                                    f["code"], rec["informational"]))
                        elif f["code"] not in rec["basis"]:
                            silent_defaults.append((ctx, "FIRED absent from basis",
                                                    f["code"], rec["basis"]))
        self.assertEqual(silent_defaults, [],
                         f"NO_ACTION reached silently: {silent_defaults[:5]}")
        self.assertGreater(n, 10000, "grid too small to be meaningful")
        print(f"\n  [coverage] {n} enumerated inputs, 0 silent defaults, "
              f"{len(T.CHECKS)} checks evaluated on every one")

    def test_old_scorecard_gap_is_now_covered(self):
        """Re-implements the OLD rule 0.5 / 0.7 predicates, collects every input
        that satisfied NEITHER while price was below the 200d (the NEM hole),
        and asserts the new triage covers all of them.

        This is what makes the fix structural rather than a wider threshold: it
        is not asserting 'dd=-29.6 now works', it is asserting the whole
        uncovered region works."""
        gap, covered = 0, 0
        for dd in DDS:
            for rsi in RSIS:
                if dd is None or rsi is None:
                    continue
                old_rule_05 = (rsi < 40 and dd <= -25)      # exhaustion HOLD
                old_rule_07 = (-25 < dd <= -8)              # early trend-break TRIM
                if old_rule_05 or old_rule_07:
                    continue
                gap += 1
                # price below BOTH MAs, a +119% winner — the NEM signature
                d = make_input(dd, rsi, -8.5, -5.7, "EQUITY")
                rec = T.triage_one(d, {"context": "HELD", "weight": 2.3, "gain_pct": 119.4})
                tb = [f for f in rec["findings"] if f["code"] == "TREND_BREAK_200D"][0]
                self.assertEqual(tb["status"], T.FIRED, f"dd={dd} rsi={rsi} trend break not seen")
                self.assertEqual(rec["attention"], T.REVIEW_NOW, f"dd={dd} rsi={rsi} not escalated")
                covered += 1
        self.assertGreater(gap, 0, "the old rules had no gap — test is not exercising the bug")
        self.assertEqual(gap, covered)
        print(f"  [gap] {gap} (dd,RSI) inputs matched NEITHER old rule 0.5 nor 0.7; "
              f"all {covered} now surface as REVIEW_NOW")

    def test_trend_break_never_windowed_on_drawdown(self):
        """Below the 200d must fire at EVERY drawdown depth and EVERY RSI."""
        for dd in DDS:
            for rsi in RSIS:
                d = make_input(dd, rsi, -0.1, -5.7, "EQUITY")
                rec = T.triage_one(d, {"context": "HELD", "weight": 6.0, "gain_pct": 10.0})
                tb = [f for f in rec["findings"] if f["code"] == "TREND_BREAK_200D"][0]
                self.assertEqual(tb["status"], T.FIRED, f"dd={dd} rsi={rsi}")
                self.assertNotEqual(rec["attention"], T.NO_ACTION, f"dd={dd} rsi={rsi}")


class TestUpstreamDataError(unittest.TestCase):
    """A null caused by a BROKEN FETCH and a null the company genuinely has no
    value for are different facts. fundamentals.py now records the reason in
    `data_errors`; collapsing the two states here would re-introduce the bug."""

    def _finding(self, d):
        rec = T.triage_one(d, None)
        return [f for f in rec["findings"] if f["code"] == "UPSTREAM_DATA_ERROR"][0]

    def test_recorded_fetch_error_is_missing_not_clear(self):
        f = self._finding({"symbol": "X", "price": 1.0,
                           "data_errors": ["history: HTTPError 503"]})
        self.assertEqual(f["status"], T.MISSING)
        self.assertNotEqual(f["severity"], T.NO_ACTION)
        self.assertIn("503", f["detail"])

    def test_empty_error_list_is_clear_and_says_so(self):
        f = self._finding({"symbol": "X", "price": 1.0, "data_errors": []})
        self.assertEqual(f["status"], T.CLEAR)
        self.assertIn("no upstream fetch errors", f["detail"])

    def test_absent_field_is_not_reported_as_confirmed_clean(self):
        # Cache predating the field. CLEAR (nothing to escalate on) but the
        # detail must NOT claim the fetch was verified healthy.
        f = self._finding({"symbol": "X", "price": 1.0})
        self.assertEqual(f["status"], T.CLEAR)
        self.assertIn("not confirmed clean", f["detail"])

    def test_never_originates_a_sell(self):
        for d in ({"symbol": "X", "price": 1.0, "data_errors": ["boom"]},
                  {"symbol": "X", "price": 1.0, "data_errors": []},
                  {"symbol": "X", "price": 1.0}):
            self.assertFalse(self._finding(d)["may_originate_sell"])


class TestMissingInputs(unittest.TestCase):
    """Requirement 4: a default may never mask a missing input."""

    def test_missing_input_always_says_missing_and_escalates(self):
        offenders = []
        for dd, rsi, vs200, vs50, qt, plabel, pos in iter_grid():
            if not any(v is None for v in (dd, rsi, vs200, vs50, qt)):
                continue
            d = make_input(dd, rsi, vs200, vs50, qt)
            rec = T.triage_one(d, pos)
            ctx = f"dd={dd} rsi={rsi} vs200={vs200} vs50={vs50} qt={qt} pos={plabel}"
            if rec["data_status"] != "MISSING":
                offenders.append(("no MISSING status", ctx))
            elif rec["attention"] == T.NO_ACTION:
                offenders.append(("missing data but NO_ACTION", ctx))
            elif not rec["missing_fields"]:
                offenders.append(("MISSING with no named field", ctx))
        self.assertEqual(offenders[:5], [], f"{len(offenders)} inputs masked a missing value")

    def test_every_absent_field_is_named(self):
        """MISSING must NAME the field, so the report can say what is absent."""
        for field in ("price", "vs_200d_ma", "vs_50d_ma", "dd_from_52wh", "rsi14",
                      "short_percent", "days_to_earnings", "quote_type"):
            d = make_input(-12.0, 55.0, -1.0, -1.0, "EQUITY")
            d.pop(field, None)
            rec = T.triage_one(d, {"context": "HELD", "weight": 2.0, "gain_pct": 10.0})
            self.assertEqual(rec["data_status"], "MISSING", field)
            self.assertIn(field, rec["missing_fields"], f"{field} absent but not named")

    def test_equity_with_all_fundamentals_null_is_missing_not_a_basket(self):
        """The old file classified an EQUITY with null fundamentals as
        'no fundamental basis' (an ETF-style routing verdict), disguising a DATA
        FAILURE as an instrument-type fact."""
        d = make_input(-12.0, 55.0, -1.0, -1.0, "EQUITY", fundamentals=False)
        rec = T.triage_one(d, {"context": "HELD", "weight": 6.0, "gain_pct": 10.0})
        nb = [f for f in rec["findings"] if f["code"] == "NO_FUNDAMENTAL_BASIS"][0]
        th = [f for f in rec["findings"] if f["code"] == "THESIS_DETERIORATION"][0]
        self.assertEqual(nb["status"], T.CLEAR)
        self.assertEqual(th["status"], T.MISSING)
        self.assertEqual(rec["attention"], T.REVIEW_NOW)

    def test_unparseable_position_escalates_never_downgrades(self):
        d = make_input(-12.0, 55.0, -1.0, -1.0, "EQUITY")
        rec = T.triage_one(d, {"context": "UNPARSEABLE", "weight": None, "gain_pct": None})
        self.assertEqual(rec["relevance"], T.REL_UNKNOWN)
        self.assertEqual(rec["attention"], T.REVIEW_NOW)

    def test_held_position_with_no_screen_output_is_not_dropped(self):
        """The flagship-exclusion bug class: a held name whose fundamentals.py
        run failed simply never appeared in the old scorecard's output."""
        with tempfile.TemporaryDirectory() as td:
            fdir = os.path.join(td, "fundamentals"); os.makedirs(fdir)
            json.dump({"symbol": "AAA", "price": 10.0, "quote_type": "EQUITY",
                       "vs_200d_ma": 5.0, "vs_50d_ma": 5.0, "dd_from_52wh": -1.0,
                       "rsi14": 55.0, "earnings_growth": 5.0, "revenue_growth": 5.0,
                       "operating_margin": 20.0, "fcf_yield": 6.0, "forward_pe": 15.0,
                       "short_percent": 1.0, "days_to_earnings": 40},
                      open(os.path.join(fdir, "AAA.out.json"), "w"))
            open(os.path.join(fdir, "BROKEN.out.json"), "w").write("{not json")
            pcsv = os.path.join(td, "p.csv")
            open(pcsv, "w").write("Position,MarketValue,Unrealized_PnL\n"
                                  "AAA,1000,100\nGHOST,5000,2500\nBROKEN,900,10\n")
            out = subprocess.run([sys.executable, os.path.join(HERE, "triage.py"), fdir,
                                  "--positions", pcsv, "--out-dir", td, "--json"],
                                 capture_output=True, text=True, cwd=td)
            self.assertEqual(out.returncode, 0, out.stderr)
            payload = json.loads(out.stdout)
            by = {r["symbol"]: r for r in payload["results"]}
            self.assertIn("GHOST", by, "held position with no screen output was DROPPED")
            self.assertEqual(by["GHOST"]["attention"], T.REVIEW_NOW)
            self.assertIn("NO_SCREEN_OUTPUT", by["GHOST"]["missing"])
            self.assertIn("BROKEN", by, "unreadable screen output was DROPPED")
            self.assertEqual(by["BROKEN"]["attention"], T.REVIEW_NOW)

    def test_positions_parse_errors_are_reported_not_swallowed(self):
        with tempfile.TemporaryDirectory() as td:
            fdir = os.path.join(td, "f"); os.makedirs(fdir)
            pcsv = os.path.join(td, "p.csv")
            open(pcsv, "w").write("Position,MarketValue,Unrealized_PnL\nAAA,not-a-number,100\n")
            pos, errors = T.load_positions(pcsv)
            self.assertTrue(any("unparseable" in e for e in errors), errors)
            self.assertEqual(pos["AAA"]["context"], "UNPARSEABLE")


class TestNoVerdicts(unittest.TestCase):
    """Requirement 1: the script may never emit a verdict."""

    def test_output_vocabulary_has_no_decision_tokens(self):
        for dd, rsi, vs200, vs50, qt, plabel, pos in iter_grid():
            rec = T.triage_one(make_input(dd, rsi, vs200, vs50, qt), pos)
            self.assertNotIn(rec["attention"], T.BANNED_DECISION_TOKENS)
            for f in rec["findings"]:
                self.assertNotIn(f["code"], T.BANNED_DECISION_TOKENS)
                self.assertNotIn(f["status"], T.BANNED_DECISION_TOKENS)
                self.assertNotIn(f["severity"], T.BANNED_DECISION_TOKENS)
            for key in ("action", "verdict", "decision"):
                self.assertNotIn(key, rec, f"record still exposes a '{key}' field")

    def test_source_returns_no_decision_verb(self):
        src = open(os.path.join(HERE, "triage.py")).read()
        hits = re.findall(r'return\s+"(%s)"' % "|".join(sorted(T.BANNED_DECISION_TOKENS)), src)
        self.assertEqual(hits, [], f"triage.py still returns decision verbs: {hits}")

    def test_price_findings_can_never_originate_a_sell(self):
        """Requirement 2, machine-encoded: technicals may not originate a sell."""
        for dd, rsi, vs200, vs50, qt, plabel, pos in iter_grid():
            rec = T.triage_one(make_input(dd, rsi, vs200, vs50, qt), pos)
            for f in rec["findings"]:
                if f["class"] == T.CLASS_PRICE:
                    self.assertFalse(f["may_originate_sell"],
                                     f"PRICE-class {f['code']} claimed sell origination")
            for code in rec["sell_origination_eligible"]:
                fin = [f for f in rec["findings"] if f["code"] == code][0]
                self.assertEqual(fin["class"], T.CLASS_THESIS)

    def test_scorecard_shim_refuses_to_run(self):
        out = subprocess.run([sys.executable, os.path.join(HERE, "scorecard.py")],
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 2)
        self.assertEqual(out.stdout.strip(), "", "shim printed to stdout — a caller could parse it")
        self.assertIn("triage.py", out.stderr)


class TestIncidentRegressions(unittest.TestCase):
    """The two real incidents, with their real 2026-07-24 numbers."""

    NEM = {"symbol": "NEM", "quote_type": "EQUITY", "price": 94.94, "ma50": 100.66,
           "ma200": 103.75, "forward_pe": 8.97, "revenue_growth": 15.1,
           "earnings_growth": 11.4, "operating_margin": 51.6, "roe": 25.9,
           "fcf_yield": 8.62, "dd_from_52wh": -29.6, "vs_200d_ma": -8.5,
           "vs_50d_ma": -5.7, "rsi14": 47.9, "short_percent": 1.4,
           "days_to_earnings": 64}
    NEM_POS = {"context": "HELD", "weight": 2.34, "gain_pct": 119.4}

    MRVL = {"symbol": "MRVL", "quote_type": "EQUITY", "price": 199.26, "ma50": 239.2,
            "ma200": 132.75, "forward_pe": 31.93, "revenue_growth": 27.6,
            "earnings_growth": -80.4, "operating_margin": 14.5, "roe": 16.0,
            "fcf_yield": 1.27, "dd_from_52wh": -39.6, "vs_200d_ma": 50.1,
            "vs_50d_ma": -16.7, "rsi14": 40.3, "short_percent": 4.7,
            "days_to_earnings": 24}
    MRVL_POS = {"context": "HELD", "weight": 0.75, "gain_pct": 128.2}

    def test_nem_surfaces_as_review_now(self):
        rec = T.triage_one(self.NEM, self.NEM_POS)
        self.assertEqual(rec["attention"], T.REVIEW_NOW,
                         "NEM silently fell through again — this is incident #3")
        self.assertIn("TREND_BREAK_200D", rec["fired"])
        self.assertIn("TREND_BREAK_50D", rec["fired"])
        self.assertIn("DRAWDOWN", rec["fired"])
        self.assertNotIn(rec["attention"], T.BANNED_DECISION_TOKENS)

    def test_nem_trend_break_alone_does_not_authorize_a_sell(self):
        rec = T.triage_one(self.NEM, self.NEM_POS)
        # NEM's fundamentals are healthy (EPS +11%, FCF yield 8.6%): no THESIS
        # finding fires, so nothing in the record may originate a sell.
        self.assertEqual(rec["sell_origination_eligible"], [],
                         "a healthy-fundamentals name became sell-eligible on price alone")
        self.assertIn("narrative", " ".join(rec["route_to_seats"]))

    def test_mrvl_produces_no_sell_from_technicals(self):
        rec = T.triage_one(self.MRVL, self.MRVL_POS)
        val = [f for f in rec["findings"] if f["code"] == "VALUATION_STRETCH"][0]
        # The old rule 3 turned exactly this state (rich + above the 200d) into
        # a TRIM. It is now an attention flag that cannot originate a sell.
        self.assertEqual(val["status"], T.FIRED)
        self.assertFalse(val["may_originate_sell"])
        self.assertNotIn("VALUATION_STRETCH", rec["sell_origination_eligible"])
        # MRVL's EPS -80% IS a legitimate thesis flag — it routes to the
        # fundamentals seat, which decides. The script still decides nothing.
        self.assertIn("THESIS_DETERIORATION", rec["sell_origination_eligible"])
        self.assertIn("fundamentals", rec["route_to_seats"])
        self.assertNotIn(rec["attention"], T.BANNED_DECISION_TOKENS)


class TestSkillContract(unittest.TestCase):
    """The doc-level constraints the script cannot enforce alone."""

    def setUp(self):
        self.md = open(SKILL_MD).read()

    def test_hierarchy_default_still_panel(self):
        self.assertIn("HIERARCHY_FLAG:-panel}", self.md,
                      "the panel default (flipped from bsc 2026-07-09) was reverted")

    def test_sell_origination_rule_is_documented(self):
        self.assertIn("SELL ORIGINATION RULE", self.md)
        for phrase in ("may NOT originate", "thesis impaired", "WATCH"):
            self.assertIn(phrase, self.md, f"missing: {phrase}")

    def test_skill_does_not_call_the_removed_scorecard(self):
        # Naming scorecard.py in the HISTORY prose is fine and wanted — future
        # readers need to know why it went. INVOKING it is the defect.
        invocations = re.findall(r"^[^\n]*python3[^\n]*scorecard\.py[^\n]*$",
                                 self.md, re.MULTILINE)
        self.assertEqual(invocations, [],
                         f"SKILL.md still invokes the removed verdict engine: {invocations}")
        self.assertIn("scripts/triage.py", self.md,
                      "SKILL.md must invoke the triage ranker")

    def test_skill_forbids_script_emitted_verdicts(self):
        self.assertIn("No script may emit a verdict", self.md)
        for tok in ("REVIEW_NOW", "NO_ACTION"):
            self.assertIn(tok, self.md, f"attention vocabulary missing: {tok}")

    def test_13f_lag_is_stated(self):
        self.assertIn("45", self.md)
        self.assertIn("13F", self.md)


if __name__ == "__main__":
    unittest.main(verbosity=2)
