#!/usr/bin/env bun
/**
 * Hermetic regression tests for drawdown_basis.ts — NO NETWORK.
 *
 * The price series is dependency-injected, so every case runs offline and fast.
 * Each test encodes one of the real incidents this validator exists to prevent:
 *   TON −49.2% (wrong window) · TON −82.5% (ATH inside a 52w report) ·
 *   JUP −87% (ATH inside a 52w report) · LINK "52w low $7.00" (eyeballed).
 */

import { test, expect, describe } from "bun:test";
import {
  validateReport,
  parseClaims,
  parseArgs,
  parseExemptions,
  parseMarkerValues,
  staleExemptionErrors,
  valueMatches,
  resolveBasis,
  formatReport,
  productionFetcher,
  statusLabel,
  MIN_SERIES_POINTS,
  type CandlePoint,
  type SeriesFetcher,
  type SeriesPoint,
  type SeriesResult,
  type Status,
} from "./drawdown_basis";

// ─────────────────────────────────────────────────────────────────────────────
// Fixtures
// ─────────────────────────────────────────────────────────────────────────────

const DAY = 86_400_000;

/**
 * Builds a synthetic daily-close series of `n` points whose MAX is `high`, MIN is
 * `low`, and LAST close is `spot` — i.e. a series with exactly known 52w stats.
 */
function makeSeries(n: number, high: number, low: number, spot: number): SeriesPoint[] {
  const pts: SeriesPoint[] = [];
  const base = Date.UTC(2025, 6, 28);
  const mid = (high + low) / 2;
  for (let i = 0; i < n; i++) pts.push({ t: base + i * DAY, c: mid });
  pts[1] = { t: base + DAY, c: high };
  pts[2] = { t: base + 2 * DAY, c: low };
  pts[n - 1] = { t: base + (n - 1) * DAY, c: spot };
  return pts;
}

/** JUP as of the real report: 52w high $0.5586, 52w low $0.1418, ATH $2.00. */
const JUP_SPOT = 0.1944;
const JUP_52W_HIGH = 0.5586;
const JUP_ATH = 2.0;
// (0.1944 / 0.5586 - 1) * 100 = -65.20%   |   (0.1944 / 2.00 - 1) * 100 = -90.28%
const JUP_DD_52W = -65.2;

/** TON as of the real report: 52w high $3.5722, spot $1.4617 → −59.1%. */
const TON_SPOT = 1.4617;
const TON_52W_HIGH = 3.5722;

function fetcherFor(map: Record<string, SeriesResult>): SeriesFetcher {
  return async (symbol: string) =>
    map[symbol] ?? { ok: false, error: `no fixture for ${symbol}` };
}

const JUP_OK: SeriesResult = {
  ok: true,
  points: makeSeries(366, JUP_52W_HIGH, 0.1418, JUP_SPOT),
  ath: JUP_ATH,
};
const TON_OK: SeriesResult = {
  ok: true,
  points: makeSeries(366, TON_52W_HIGH, 1.2174, TON_SPOT),
  ath: 8.25,
};

/** Wraps a claim body in a token section so symbol attribution works. */
function report(symbol: string, body: string): string {
  return `# Test Report\n\n### 1. ${symbol} — Fixture Token\n\n${body}\n`;
}

function statuses(results: { status: Status }[]): Status[] {
  return results.map((r) => r.status);
}

// ─────────────────────────────────────────────────────────────────────────────
// RULE 1 — basis must be explicit
// ─────────────────────────────────────────────────────────────────────────────

describe("RULE 1 — explicit basis required", () => {
  test('bare "−87% from high" FAILS with BASIS_MISSING (the real JUP incident)', async () => {
    const md = report("JUP", "**Assessment:** JUP in free-fall territory, **−87% from high**.");
    const rep = await validateReport(md, { fetcher: fetcherFor({ JUP: JUP_OK }) });

    expect(rep.ok).toBe(false);
    expect(statuses(rep.results)).toContain("BASIS_MISSING");
    expect(rep.failures[0]!.claim.value).toBe(-87);
  });

  test('bare "down 87% from highs" (prose, plural, no sign) FAILS with BASIS_MISSING', async () => {
    const md = report("JUP", "JUP is down 87% from highs on declining volume.");
    const rep = await validateReport(md, { fetcher: fetcherFor({ JUP: JUP_OK }) });

    expect(rep.ok).toBe(false);
    expect(statuses(rep.results)).toEqual(["BASIS_MISSING"]);
  });

  test("BASIS_MISSING fires even with --basis-only (no network at all)", async () => {
    const md = report("JUP", "| **JUP** | ❌ (−87% from high) | AVOID |");
    const rep = await validateReport(md, { basisOnly: true });

    expect(rep.ok).toBe(false);
    expect(statuses(rep.results)).toEqual(["BASIS_MISSING"]);
  });

  test("resolveBasis maps the vocabulary that appears in real reports", () => {
    expect(resolveBasis("52w high")).toBe("52w");
    expect(resolveBasis("52-week high")).toBe("52w");
    expect(resolveBasis("365d high")).toBe("52w");
    expect(resolveBasis("ATH")).toBe("ATH");
    expect(resolveBasis("all-time high")).toBe("ATH");
    expect(resolveBasis("high")).toBe("UNKNOWN");
    expect(resolveBasis("its recent high")).toBe("UNKNOWN");
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// RULE 2 — recompute and fail on mismatch
// ─────────────────────────────────────────────────────────────────────────────

describe("RULE 2 — recompute against one canonical series", () => {
  test('explicit "−65.2% from 52w high" matching the series PASSES', async () => {
    const md = report("JUP", "JUP is **−65.2% from 52w high**.");
    const rep = await validateReport(md, { fetcher: fetcherFor({ JUP: JUP_OK }) });

    expect(statuses(rep.results)).toEqual(["OK"]);
    expect(rep.ok).toBe(true);
    expect(rep.results[0]!.recomputed).toBeCloseTo(JUP_DD_52W, 1);
  });

  test('explicit "−90.3% from ATH" matching the injected ATH PASSES', async () => {
    const md = report("JUP", "JUP is **−90.3% from ATH** ($2.00).");
    const rep = await validateReport(md, { fetcher: fetcherFor({ JUP: JUP_OK }) });

    expect(statuses(rep.results)).toEqual(["OK"]);
    expect(rep.results[0]!.claim.basis).toBe("ATH");
    expect(rep.results[0]!.recomputed).toBeCloseTo(-90.28, 1);
  });

  test('stated "−49.2% from 52w high" vs a −59.1% series FAILS with MISMATCH (the real TON incident)', async () => {
    const md = report("TON", "TON is **−49.2% from 52w high**.");
    const rep = await validateReport(md, { fetcher: fetcherFor({ TON: TON_OK }) });

    expect(rep.ok).toBe(false);
    expect(statuses(rep.results)).toEqual(["MISMATCH"]);
    expect(rep.results[0]!.recomputed).toBeCloseTo(-59.08, 1);
    expect(rep.results[0]!.detail).toContain("49.2");
    expect(rep.results[0]!.detail).toContain("59.1");
  });

  test('a right-basis-wrong-number "−82.5% from ATH" on a 8.25 ATH is caught too', async () => {
    // TON spot 1.4617 vs ATH 8.25 => -82.28%; a stated -75% must MISMATCH.
    const md = report("TON", "TON is **−75.0% from ATH**.");
    const rep = await validateReport(md, { fetcher: fetcherFor({ TON: TON_OK }) });

    expect(statuses(rep.results)).toEqual(["MISMATCH"]);
  });

  test("tolerance is configurable in percentage points", async () => {
    const md = report("JUP", "JUP is **−65.9% from 52w high**."); // 0.7pp off
    const tight = await validateReport(md, { fetcher: fetcherFor({ JUP: JUP_OK }) });
    const loose = await validateReport(md, { fetcher: fetcherFor({ JUP: JUP_OK }), tolerance: 1.0 });

    expect(statuses(tight.results)).toEqual(["MISMATCH"]);
    expect(statuses(loose.results)).toEqual(["OK"]);
  });

  test("stated 52w low/high levels are validated against the same series (the LINK $7.00 incident)", async () => {
    const link: SeriesResult = { ok: true, points: makeSeries(366, 26.73, 7.19, 8.28), ath: 52.7 };
    const md = report("LINK", "| 52w Low | $7.00 |\n| 52w High | $26.73 |");
    const rep = await validateReport(md, { fetcher: fetcherFor({ LINK: link }) });

    const low = rep.results.find((r) => r.claim.kind === "low")!;
    const high = rep.results.find((r) => r.claim.kind === "high")!;
    expect(low.status).toBe("MISMATCH"); // $7.00 eyeballed vs $7.19 actual
    expect(high.status).toBe("OK");
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// RULE 3 — a truncated window fails loudly
// ─────────────────────────────────────────────────────────────────────────────

describe("RULE 3 — short/truncated series fails loudly", () => {
  test("a 260-point series FAILS with SHORT_SERIES and never silently passes", async () => {
    // 260 points ≈ the ~37-week truncated window behind the TON −49.2% figure.
    const truncated: SeriesResult = { ok: true, points: makeSeries(260, 2.88, 1.2174, TON_SPOT) };
    const md = report("TON", "TON is **−49.2% from 52w high**.");
    const rep = await validateReport(md, { fetcher: fetcherFor({ TON: truncated }) });

    expect(rep.ok).toBe(false);
    expect(statuses(rep.results)).toEqual(["SHORT_SERIES"]);
    expect(rep.failures[0]!.detail).toContain("260");
    expect(rep.failures[0]!.detail).toContain("truncated");
  });

  test("the minimum window is 360 points; 359 fails, 360 does not", async () => {
    expect(MIN_SERIES_POINTS).toBe(360);
    const md = report("JUP", "JUP is **−65.2% from 52w high**.");

    const short: SeriesResult = { ok: true, points: makeSeries(359, JUP_52W_HIGH, 0.1418, JUP_SPOT) };
    const just: SeriesResult = { ok: true, points: makeSeries(360, JUP_52W_HIGH, 0.1418, JUP_SPOT) };

    expect(statuses((await validateReport(md, { fetcher: fetcherFor({ JUP: short }) })).results)).toEqual(["SHORT_SERIES"]);
    expect(statuses((await validateReport(md, { fetcher: fetcherFor({ JUP: just }) })).results)).toEqual(["OK"]);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// RULE 4 — missing data is loud, never a skip
// ─────────────────────────────────────────────────────────────────────────────

describe("RULE 4 — missing data is [UNAVAILABLE] and loud", () => {
  test("a network error FAILS as FETCH_FAILED, never a silent skip", async () => {
    const md = report("JUP", "JUP is **−65.2% from 52w high**.");
    const rep = await validateReport(md, {
      fetcher: async () => ({ ok: false, error: "getaddrinfo ENOTFOUND api.coingecko.com" }),
    });

    expect(rep.ok).toBe(false);
    expect(statuses(rep.results)).toEqual(["FETCH_FAILED"]);
    expect(rep.failures[0]!.detail).toContain("[UNAVAILABLE]");
  });

  test("a THROWN fetcher error is captured as FETCH_FAILED, not an unhandled crash", async () => {
    const md = report("JUP", "JUP is **−65.2% from 52w high**.");
    const rep = await validateReport(md, {
      fetcher: async () => { throw new Error("HTTP 429 rate-limited by CoinGecko after 5 attempts"); },
    });

    expect(statuses(rep.results)).toEqual(["FETCH_FAILED"]);
    expect(rep.failures[0]!.detail).toContain("429");
  });

  test("an ATH-basis claim with no ATH available is ATH_UNAVAILABLE, not silently 52w-validated", async () => {
    const noAth: SeriesResult = { ok: true, points: makeSeries(366, JUP_52W_HIGH, 0.1418, JUP_SPOT) };
    const md = report("JUP", "JUP is **−90.3% from ATH**.");
    const rep = await validateReport(md, { fetcher: fetcherFor({ JUP: noAth }) });

    expect(rep.ok).toBe(false);
    expect(statuses(rep.results)).toEqual(["ATH_UNAVAILABLE"]);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Parsing coverage — a missed claim is a silent failure, the exact bug class
// ─────────────────────────────────────────────────────────────────────────────

describe("parsing", () => {
  test("Unicode minus (U+2212) and ASCII hyphen both parse to the same claim", async () => {
    const uni = report("JUP", "JUP is \u221265.2% from 52w high.");
    const ascii = report("JUP", "JUP is -65.2% from 52w high.");

    const cu = parseClaims(uni);
    const ca = parseClaims(ascii);
    expect(cu).toHaveLength(1);
    expect(ca).toHaveLength(1);
    expect(cu[0]!.value).toBe(-65.2);
    expect(ca[0]!.value).toBe(-65.2);
    expect(cu[0]!.basis).toBe("52w");
    expect(ca[0]!.basis).toBe("52w");
  });

  test("table-row forms are extracted with their basis", () => {
    const md = report(
      "ETH",
      ["| % from 52w High | −62.6% |", "| % from ATH | −23% |", "| ATH | $8.25 (−82.5%) |", "| 52w High | $126,200 (−49.3%) |"].join("\n"),
    );
    const claims = parseClaims(md).filter((c) => c.kind === "drawdown");

    expect(claims.map((c) => [c.basis, c.value])).toEqual([
      ["52w", -62.6],
      ["ATH", -23],
      ["ATH", -82.5],
      ["52w", -49.3],
    ]);
  });

  test("a summary row re-attributes the claim to its own token, not the section heading", () => {
    const md = "### 1. BTC — Bitcoin\n\n| **JUP** | ⚠️ | ❌ (−87% from 52w high) | AVOID |\n";
    const claims = parseClaims(md);
    expect(claims[0]!.symbol).toBe("JUP");
  });

  test("thousands separators parse ($126,200 not 126)", () => {
    const md = report("BTC", "| 52w High | $126,200 |");
    const claims = parseClaims(md).filter((c) => c.kind === "high");
    expect(claims[0]!.value).toBe(126200);
  });

  test("a 52w range row yields BOTH a low and a high claim", () => {
    const md = report("ETH", "| 52w Range | $1,385 ↔ $4,957 |");
    const claims = parseClaims(md);
    expect(claims.find((c) => c.kind === "low")!.value).toBe(1385);
    expect(claims.find((c) => c.kind === "high")!.value).toBe(4957);
  });

  test("a basis stated earlier in the same sentence counts (no false BASIS_MISSING)", () => {
    const md = report("TON", "On the standard 52w-high basis, TON is −59.1% from high.");
    expect(parseClaims(md)[0]!.basis).toBe("52w");
  });

  test("a basis stated in a DIFFERENT table cell does NOT count", () => {
    const md = report("TON", "| 52w High | $3.57 | −49.2% from high |");
    const dd = parseClaims(md).find((c) => c.kind === "drawdown")!;
    expect(dd.basis).toBe("UNKNOWN");
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// SILENT NON-EXTRACTION — the worst failure mode: a claim the parser never sees
// is a claim that is silently TRUSTED. Both defects below shipped live.
// ─────────────────────────────────────────────────────────────────────────────

describe("silent non-extraction regressions", () => {
  // DEFECT 1 — NUM could not parse a thousands separator TOGETHER WITH decimals.
  // On `$1,505.00` it stopped after `1,505`, so RE_RANGE never saw the `↔` and the
  // ENTIRE range claim vanished with no warning. Confirmed live: this exact report
  // line produced ZERO extracted claims.
  test("DEFECT 1: `$1,505.00 ↔ $4,956.78` extracts TWO level claims with full precision", () => {
    const md = report(
      "ETH",
      "| 52w Range (intraday) | **$1,505.00 ↔ $4,956.78** — corrected 2026-07-24 |",
    );
    const claims = parseClaims(md);

    const low = claims.find((c) => c.kind === "low");
    const high = claims.find((c) => c.kind === "high");
    expect(low).toBeDefined();
    expect(high).toBeDefined();
    expect(low!.value).toBe(1505.0);
    expect(high!.value).toBe(4956.78);
    expect(low!.basis).toBe("52w");
    expect(high!.basis).toBe("52w");
  });

  test("DEFECT 1: `1,505.00` is NOT mis-parsed as 1 or 505 (no greedy mis-split)", () => {
    const md = report("ETH", "| 52w Low | $1,505.00 |");
    const claims = parseClaims(md).filter((c) => c.kind === "low");

    expect(claims).toHaveLength(1);
    expect(claims[0]!.value).toBe(1505.0);
    expect(claims[0]!.value).not.toBe(1);
    expect(claims[0]!.value).not.toBe(505);
  });

  test("DEFECT 1: comma+decimal values recompute correctly end-to-end", async () => {
    const eth: SeriesResult = {
      ok: true,
      points: makeSeries(366, 4900, 1600, 3800),
      candles: makeCandles(366, 4956.78, 1505.0, 4900, 1600, 3800),
    };
    const md = report("ETH", "| 52w Range | $1,505.00 ↔ $4,956.78 |");
    const rep = await validateReport(md, { fetcher: fetcherFor({ ETH: eth }) });

    expect(statuses(rep.results)).toEqual(["OK", "OK"]);
    expect(rep.results.every((r) => r.verification === "intraday")).toBe(true);
  });

  // DEFECT 2 — the level-row label had to be EXACTLY `52w Low`; a parenthetical made
  // the row invisible. Confirmed live: the BTC `| 52w Low (intraday) |` row extracted
  // nothing at all.
  test("DEFECT 2: `| 52w Low (intraday) | $57,717.55 |` extracts ONE claim at full precision", () => {
    const md = report("BTC", "| 52w Low (intraday) | $57,717.55 |");
    const claims = parseClaims(md);

    expect(claims).toHaveLength(1);
    expect(claims[0]!.kind).toBe("low");
    expect(claims[0]!.value).toBe(57717.55);
    expect(claims[0]!.basis).toBe("52w");
  });

  test("DEFECT 2: every real-world label qualifier keeps the row visible", () => {
    const variants: [string, number][] = [
      ["| 52w Low (intraday) | $57,717.55 |", 57717.55],
      ["| 52w Low (close) | $60,000 |", 60000],
      ["| 52w High (corrected) | $126,296 |", 126296],
      ["| 52w Low (intraday, 3-venue) | $57,717.55 |", 57717.55],
      ["| 52w High — RESOLVED 2026-07-24 | $126,296 |", 126296],
      ["| **52w Low (intraday)** | **$57,717.55** |", 57717.55],
      ["| 365d High (intraday) | $126,296 |", 126296],
    ];
    for (const [row, expected] of variants) {
      const claims = parseClaims(report("BTC", row)).filter(
        (c) => c.kind === "low" || c.kind === "high",
      );
      expect({ row, n: claims.length }).toEqual({ row, n: 1 });
      expect({ row, v: claims[0]!.value }).toEqual({ row, v: expected });
    }
  });

  test("DEFECT 2: `| 52w High (intraday) | $126,296 (−49.4%) |` yields BOTH level and drawdown", () => {
    const md = report("BTC", "| 52w High (intraday) | $126,296 (−49.4%) |");
    const claims = parseClaims(md);

    const high = claims.find((c) => c.kind === "high");
    const dd = claims.find((c) => c.kind === "drawdown");
    expect(high).toBeDefined();
    expect(dd).toBeDefined();
    expect(high!.value).toBe(126296);
    expect(dd!.value).toBe(-49.4);
    expect(dd!.basis).toBe("52w");
  });

  test("no regression: plain forms ($126,200 · $60.11 · 0.001199 · $4,957) still extract", () => {
    expect(parseClaims(report("BTC", "| 52w High | $126,200 |"))[0]!.value).toBe(126200);
    expect(parseClaims(report("SOL", "| 52w Low | $60.11 |"))[0]!.value).toBe(60.11);
    expect(parseClaims(report("PUMP", "| 52w Low | $0.001199 |"))[0]!.value).toBe(0.001199);
    expect(parseClaims(report("ETH", "| 52w Range | $1,385 ↔ $4,957 |")).map((c) => c.value))
      .toEqual([1385, 4957]);
    expect(parseClaims(report("JUP", "JUP is −65.2% from 52w high."))[0]!.value).toBe(-65.2);
  });

  /**
   * THE GUARD FOR THE WHOLE CLASS. Individual value assertions cannot catch a claim
   * that silently disappears — only a COUNT can. This fixture holds exactly 13 known
   * claims across every supported form; if any future edit makes one invisible, this
   * test fails even though every other assertion in the file still passes.
   */
  test("GUARD: a fixture with 13 known claims extracts EXACTLY 13 (silent-drop canary)", () => {
    const md = [
      "# Guard Fixture",
      "",
      "### 1. BTC — Bitcoin",
      "",
      "| 52w Low (intraday) | $57,717.55 |", //  1 low
      "| 52w High (intraday) | $126,296 (−49.4%) |", //  2 high, 3 drawdown
      "| % from 52w High | −49.4% |", //  4 drawdown
      "BTC is −49.4% from 52w high today.", //  5 drawdown
      "",
      "### 2. ETH — Ethereum",
      "",
      "| 52w Range (intraday) | **$1,505.00 ↔ $4,956.78** |", //  6 low, 7 high
      "| ATH | $4,891.70 (−23.0%) |", //  8 high (ATH LEVEL), 9 drawdown
      "| % from ATH | −23.0% |", // 10 drawdown
      "",
      "### 3. PUMP — Pump.fun",
      "",
      "| 52w Low | $0.001199 |", // 11 low
      "| 52w High (close) | $0.017 |", // 12 high
      "PUMP is down 93% from highs.", // 13 drawdown (BASIS_MISSING, still a claim)
    ].join("\n");

    const claims = parseClaims(md);
    // The expected list is written out LITERALLY. It used to be
    // `expect({ n, summary }).toEqual({ n: 12, summary })` — with `summary` on BOTH
    // sides, which asserted nothing beyond the length the next line already asserted.
    expect(claims.map((c) => `L${c.line}:${c.symbol}:${c.kind}:${c.value}`)).toEqual([
      "L5:BTC:low:57717.55",
      "L6:BTC:high:126296",
      "L6:BTC:drawdown:-49.4",
      "L7:BTC:drawdown:-49.4",
      "L8:BTC:drawdown:-49.4",
      "L12:ETH:low:1505",
      "L12:ETH:high:4956.78",
      "L13:ETH:high:4891.7",
      "L13:ETH:drawdown:-23",
      "L14:ETH:drawdown:-23",
      "L18:PUMP:low:0.001199",
      "L19:PUMP:high:0.017",
      "L20:PUMP:drawdown:-93",
    ]);
    expect(claims).toHaveLength(13);
    expect(claims.filter((c) => c.kind === "low")).toHaveLength(3);
    expect(claims.filter((c) => c.kind === "high")).toHaveLength(4);
    expect(claims.filter((c) => c.kind === "drawdown")).toHaveLength(6);
    // Every claim must be attributed to a token — an unattributed claim cannot be
    // recomputed, which is a different flavour of the same silent-trust problem.
    expect(claims.every((c) => c.symbol !== null)).toBe(true);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// RULE 5 — compare like with like (intraday vs close)
//
// Reports quote INTRADAY extremes (TradingView/exchange candles); CoinGecko's
// market_chart returns daily CLOSES only. Validating one against the other produced
// systematic FALSE POSITIVES — measured on the real book:
//   SOL  report 52w low $60.13 | Coinbase intraday $60.11 (CORRECT) | close-only $62.18
//   AAVE report 52w low $57.83 | Coinbase intraday $57.82 (CORRECT) | close-only $60.79
// while the genuine out-of-window errors must still fail:
//   BTC low $52,550 vs intraday $57,717.55 · ETH low $1,385 vs $1,505 · SOL high
//   $295.83 vs $253.61.
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Builds daily candles whose intraday MIN/MAX are `lo`/`hi` while the CLOSE min/max
 * are the tighter `closeLo`/`closeHi` — exactly the real-world gap that caused the
 * false positives.
 */
function makeCandles(
  n: number,
  hi: number,
  lo: number,
  closeHi: number,
  closeLo: number,
  spot: number,
): CandlePoint[] {
  const base = Date.UTC(2025, 6, 28);
  const mid = (closeHi + closeLo) / 2;
  const pts: CandlePoint[] = [];
  for (let i = 0; i < n; i++) pts.push({ t: base + i * DAY, l: mid, h: mid, c: mid });
  pts[1] = { t: base + DAY, l: closeHi, h: hi, c: closeHi };
  pts[2] = { t: base + 2 * DAY, l: lo, h: closeLo, c: closeLo };
  pts[n - 1] = { t: base + (n - 1) * DAY, l: spot, h: spot, c: spot };
  return pts;
}

/** SOL as measured: intraday low $60.11, close-only low $62.18, spot $184.00. */
const SOL_SPOT = 184.0;
const SOL_INTRADAY_LOW = 60.11;
const SOL_CLOSE_LOW = 62.18;
const SOL_INTRADAY_HIGH = 253.61;
const SOL_CLOSE_HIGH = 250.0;

const SOL_WITH_INTRADAY: SeriesResult = {
  ok: true,
  points: makeSeries(366, SOL_CLOSE_HIGH, SOL_CLOSE_LOW, SOL_SPOT),
  candles: makeCandles(366, SOL_INTRADAY_HIGH, SOL_INTRADAY_LOW, SOL_CLOSE_HIGH, SOL_CLOSE_LOW, SOL_SPOT),
  ath: 293.31,
};

describe("RULE 5 — intraday vs close, compared like with like", () => {
  test("an INTRADAY-sourced 52w low that matches intraday but NOT close PASSES as OK[intraday] (the real SOL false positive)", async () => {
    // $60.13 is 0.03% off the intraday low but 3.3% off the close-only low — the old
    // close-only validator cried MISMATCH on a CORRECT report figure.
    const md = report("SOL", "| 52w Low | $60.13 |");
    const rep = await validateReport(md, { fetcher: fetcherFor({ SOL: SOL_WITH_INTRADAY }) });

    expect(rep.ok).toBe(true);
    expect(statuses(rep.results)).toEqual(["OK"]);
    const r = rep.results[0]!;
    expect(r.verification).toBe("intraday");
    expect(r.recomputedIntraday).toBeCloseTo(SOL_INTRADAY_LOW, 2);
    expect(r.recomputedClose).toBeCloseTo(SOL_CLOSE_LOW, 2);
    expect(r.detail).toContain("OK[intraday]");
  });

  test("the same AAVE low ($57.83 vs intraday $57.82 / close $60.79) also stops being a false positive", async () => {
    const aave: SeriesResult = {
      ok: true,
      points: makeSeries(366, 350, 60.79, 240),
      candles: makeCandles(366, 371.5, 57.82, 350, 60.79, 240),
    };
    const md = report("AAVE", "| 52w Low | $57.83 |");
    const rep = await validateReport(md, { fetcher: fetcherFor({ AAVE: aave }) });

    expect(statuses(rep.results)).toEqual(["OK"]);
    expect(rep.results[0]!.verification).toBe("intraday");
  });

  test("a claim matching NEITHER convention is a MISMATCH and reports BOTH recomputed values (the real SOL high $295.83 out-of-window error)", async () => {
    const md = report("SOL", "| 52w High | $295.83 |");
    const rep = await validateReport(md, { fetcher: fetcherFor({ SOL: SOL_WITH_INTRADAY }) });

    expect(rep.ok).toBe(false);
    expect(statuses(rep.results)).toEqual(["MISMATCH"]);
    const r = rep.results[0]!;
    expect(r.detail).toContain("NEITHER");
    // A human must be able to see the gap on BOTH conventions from the message alone.
    expect(r.detail).toContain("253.61");
    expect(r.detail).toContain("250.000");
    expect(r.recomputedIntraday).toBeCloseTo(SOL_INTRADAY_HIGH, 2);
    expect(r.recomputedClose).toBeCloseTo(SOL_CLOSE_HIGH, 2);
  });

  test("an out-of-window LOW (BTC $52,550 vs intraday $57,717.55) still FAILS — real errors stay caught", async () => {
    const btc: SeriesResult = {
      ok: true,
      points: makeSeries(366, 126200, 60000, 118000),
      candles: makeCandles(366, 126296, 57717.55, 126200, 60000, 118000),
    };
    const md = report("BTC", "| 52w Low | $52,550 |");
    const rep = await validateReport(md, { fetcher: fetcherFor({ BTC: btc }) });

    expect(statuses(rep.results)).toEqual(["MISMATCH"]);
    expect(rep.results[0]!.detail).toContain("57717.6");
  });

  test("a close-basis claim still passes, but is labelled OK[close] and names the intraday figure", async () => {
    const md = report("SOL", "| 52w Low | $62.18 |");
    const rep = await validateReport(md, { fetcher: fetcherFor({ SOL: SOL_WITH_INTRADAY }) });

    expect(statuses(rep.results)).toEqual(["OK"]);
    expect(rep.results[0]!.verification).toBe("close");
    expect(rep.results[0]!.detail).toContain("OK[close]");
    expect(rep.results[0]!.detail).toContain("60.11");
  });

  test("a drawdown matching the intraday peak but not the close peak PASSES as OK[intraday]", async () => {
    // spot 184.00 / intraday high 253.61 - 1 = -27.45%  |  / close high 250 - 1 = -26.40%
    const md = report("SOL", "SOL is **−27.5% from 52w high**.");
    const rep = await validateReport(md, { fetcher: fetcherFor({ SOL: SOL_WITH_INTRADAY }) });

    expect(statuses(rep.results)).toEqual(["OK"]);
    expect(rep.results[0]!.verification).toBe("intraday");
    expect(rep.results[0]!.recomputedIntraday).toBeCloseTo(-27.45, 1);
    expect(rep.results[0]!.recomputedClose).toBeCloseTo(-26.4, 1);
  });

  test("a truncated INTRADAY window is not used as authoritative (it would understate the true extreme)", async () => {
    const shortCandles: SeriesResult = {
      ok: true,
      points: makeSeries(366, SOL_CLOSE_HIGH, SOL_CLOSE_LOW, SOL_SPOT),
      candles: makeCandles(120, SOL_INTRADAY_HIGH, SOL_INTRADAY_LOW, SOL_CLOSE_HIGH, SOL_CLOSE_LOW, SOL_SPOT),
    };
    const md = report("SOL", "| 52w Low | $60.13 |");
    const rep = await validateReport(md, { fetcher: fetcherFor({ SOL: shortCandles }) });

    // Falls back to close, which $60.13 does NOT match → honest MISMATCH, not a pass
    // on a 120-day intraday window that cannot represent a 52-week extreme.
    expect(statuses(rep.results)).toEqual(["MISMATCH"]);
    expect(rep.results[0]!.detail).toContain("120 candles");
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// RULE 5 + RULE 4 — honest degradation when intraday data is unavailable
// ─────────────────────────────────────────────────────────────────────────────

describe("RULE 5 — close-only degradation is labelled, never silently authoritative", () => {
  const CG_ONLY: SeriesFetcher = async () => ({
    ok: true,
    points: makeSeries(366, SOL_CLOSE_HIGH, SOL_CLOSE_LOW, SOL_SPOT),
  });

  test("a token with NO Coinbase product falls back to close and is labelled close-only", async () => {
    const fetcher = productionFetcher(CG_ONLY, {} /* no products */, async () => {
      throw new Error("must not be called");
    });
    const md = report("SOL", "| 52w Low | $62.18 |");
    const rep = await validateReport(md, { fetcher });

    const r = rep.results[0]!;
    expect(r.status).toBe("OK");
    // NOT "close" — close data must never be presented as having verified intraday.
    expect(r.verification).toBe("close-only");
    expect(r.detail).toContain("intraday unverified");
    expect(r.detail).toContain("no Coinbase product mapped");
    expect(r.recomputedIntraday).toBeUndefined();
    expect(statusLabel(r)).toBe("OK[close-only]");
  });

  test("a Coinbase FETCH FAILURE with CoinGecko succeeding must NOT silently pass as fully verified", async () => {
    const fetcher = productionFetcher(CG_ONLY, { SOL: "SOL-USD" }, async () => {
      throw new Error("HTTP 503 Service Unavailable for SOL-USD");
    });
    const md = report("SOL", "| 52w Low | $62.18 |");
    const rep = await validateReport(md, { fetcher });

    const r = rep.results[0]!;
    expect(r.status).toBe("OK");
    expect(r.verification).toBe("close-only");
    // The failure REASON must be visible, per repo invariant #4 (loud degradation).
    expect(r.detail).toContain("intraday unverified");
    expect(r.detail).toContain("503");
    expect(r.detail).toContain("SOL-USD");
  });

  test("close-only claims are surfaced in the human-readable report, not hidden among the passes", async () => {
    const fetcher = productionFetcher(CG_ONLY, {}, async () => { throw new Error("nope"); });
    const md = report("SOL", "| 52w Low | $62.18 |");
    const rep = await validateReport(md, { fetcher });

    const text = formatReport(rep, "fixture.md");
    expect(text).toContain("OK[close-only]");
    expect(text).toContain("intraday unverified");
    expect(text).toContain("1 claim(s) passed on CLOSE data only");
  });

  test("a CoinGecko (close) failure is still a hard FETCH_FAILED even though Coinbase would work", async () => {
    const fetcher = productionFetcher(
      async () => ({ ok: false, error: "getaddrinfo ENOTFOUND api.coingecko.com" }),
      { SOL: "SOL-USD" },
      async () => makeCandles(366, SOL_INTRADAY_HIGH, SOL_INTRADAY_LOW, SOL_CLOSE_HIGH, SOL_CLOSE_LOW, SOL_SPOT),
    );
    const md = report("SOL", "| 52w Low | $60.13 |");
    const rep = await validateReport(md, { fetcher });

    expect(statuses(rep.results)).toEqual(["FETCH_FAILED"]);
    expect(rep.failures[0]!.detail).toContain("[UNAVAILABLE]");
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// ADVERSARIAL-REVIEW REGRESSIONS (PR #95)
//
// Every case below was REPRODUCED against the shipped validator. Each one is a
// SILENT failure — a claim the tool never saw, or worse, a confident WRONG PASS.
// ─────────────────────────────────────────────────────────────────────────────

describe("B2 — a bold/italic/code-span percentage must still be extracted", () => {
  // The old regex demanded `%\s+(?:from|off|…)`. A closing `**` between the `%` and the
  // `from` killed the match, so the claim was never extracted and therefore silently
  // trusted. Live at ~L133/137/391 of research/crypto-portfolio-2026-07-24.md.
  // Every pre-existing test bolded the WHOLE phrase, which leaves no mid-claim
  // delimiter — which is exactly why this survived review.
  const cases: [string, number, string][] = [
    ["TON is **−62.8%** from its 52w high", -62.8, "52w"],
    ["TON is −62.8% from its 52w high", -62.8, "52w"], // control: unbolded
    ["HYPE sits (**−61.0%** from 52w high) today", -61.0, "52w"],
    ["JUP is *−90.3%* from ATH", -90.3, "ATH"],
    ["JUP is _−90.3%_ from ATH", -90.3, "ATH"],
    ["JUP is `−90.3%` from ATH", -90.3, "ATH"],
    ["AAVE is **−23.0%** off its all-time high", -23.0, "ATH"],
  ];

  for (const [body, value, basis] of cases) {
    test(`bolding ONLY the number still yields a claim: «${body}»`, () => {
      const claims = parseClaims(report("TON", body)).filter((c) => c.kind === "drawdown");
      expect({ body, n: claims.length }).toEqual({ body, n: 1 });
      expect({ body, v: claims[0]!.value }).toEqual({ body, v: value });
      expect({ body, b: claims[0]!.basis }).toEqual({ body, b: basis });
    });
  }

  test("the shipped `(**−61.0%** from high)` is now CAUGHT as BASIS_MISSING", async () => {
    // THE headline defect: a BARE "from high" — precisely what RULE 1 exists to reject —
    // sat in the report while the gate announced "all 66 passed", because bolding the
    // number made it invisible to the parser.
    const md = report("TON", "| HYPE | Overbought (**−61.0%** from high) | TRIM |");
    const rep = await validateReport(md, { basisOnly: true });

    expect(rep.ok).toBe(false);
    expect(statuses(rep.results)).toEqual(["BASIS_MISSING"]);
    expect(rep.failures[0]!.claim.value).toBe(-61);
  });

  test("a bolded number does NOT double-count against the unbolded form", () => {
    // The emphasis allowance must not make one claim match twice at overlapping spans.
    expect(parseClaims(report("TON", "TON is **−62.8%** from its 52w high."))).toHaveLength(1);
  });
});

describe("M8 — `| ATH | $8.25 |` level rows must extract", () => {
  // `(low|high)?` was optional but a non-low/high match hit a bare `continue`, so the
  // report's TON ATH $8.25 and HYPE ATH $76.87 were never verified. The GUARD fixture
  // even baked the drop in (it counted `| ATH | $4,891.70 (−23.0%) |` as 1 claim).
  test("`| ATH | $8.25 |` yields ONE high claim on the ATH basis", () => {
    const claims = parseClaims(report("TON", "| ATH | $8.25 |"));
    expect(claims).toHaveLength(1);
    expect(claims[0]!.kind).toBe("high");
    expect(claims[0]!.basis).toBe("ATH");
    expect(claims[0]!.value).toBe(8.25);
  });

  test("every ATH label spelling extracts (HYPE $76.87 and friends)", () => {
    const variants: [string, number][] = [
      ["| ATH | $76.87 |", 76.87],
      ["| All-Time High | $8.25 |", 8.25],
      ["| all time | $8.25 |", 8.25],
      ["| **ATH** | **$76.87** |", 76.87],
      ["| ATH (corrected) — RESOLVED | $8.25 |", 8.25],
    ];
    for (const [row, expected] of variants) {
      const claims = parseClaims(report("TON", row)).filter((c) => c.kind === "high");
      expect({ row, n: claims.length }).toEqual({ row, n: 1 });
      expect({ row, v: claims[0]!.value }).toEqual({ row, v: expected });
      expect({ row, b: claims[0]!.basis }).toEqual({ row, b: "ATH" });
    }
  });

  test("`| ATH | $8.25 (−82.5%) |` yields BOTH the level and the drawdown", () => {
    const claims = parseClaims(report("TON", "| ATH | $8.25 (−82.5%) |"));
    expect(claims.filter((c) => c.kind === "high")).toHaveLength(1);
    expect(claims.filter((c) => c.kind === "drawdown")).toHaveLength(1);
  });

  test("a 52w row with NO low/high word stays skipped (genuinely ambiguous, not a guess)", () => {
    expect(parseClaims(report("TON", "| 52w | $8.25 |"))).toHaveLength(0);
  });
});

describe("M5 — an ATH-basis LEVEL must be checked against the ATH, not the 52w series", () => {
  // `claim.basis` was honoured for drawdowns and IGNORED for low/high, and `s.ath` was
  // fetched but never read — so an ATH level was silently validated against the 52-WEEK
  // high. This fixture is off by 12× and used to PASS.
  const ATH_TRAP: SeriesResult = { ok: true, points: makeSeries(366, 8.25, 1.0, 1.5), ath: 100 };

  test("`| All-Time High | $8.25 |` on a series whose 52w high is 8.25 but ATH is 100 FAILS", async () => {
    const md = report("TON", "| All-Time High | $8.25 |");
    const rep = await validateReport(md, { fetcher: fetcherFor({ TON: ATH_TRAP }) });

    expect(rep.ok).toBe(false);
    expect(statuses(rep.results)).toEqual(["MISMATCH"]);
    expect(rep.failures[0]!.recomputed).toBe(100);
    expect(rep.failures[0]!.detail).toContain("ATH");
  });

  test("a CORRECT ATH level passes and says it was the ATH that backed it", async () => {
    const md = report("TON", "| ATH | $100.00 |");
    const rep = await validateReport(md, { fetcher: fetcherFor({ TON: ATH_TRAP }) });

    expect(statuses(rep.results)).toEqual(["OK"]);
    expect(rep.results[0]!.detail).toContain("OK[ATH]");
  });

  test("no ATH data => ATH_UNAVAILABLE, never a silent fallback to the 52w series", async () => {
    const noAth: SeriesResult = { ok: true, points: makeSeries(366, 8.25, 1.0, 1.5) };
    const md = report("TON", "| ATH | $8.25 |");
    const rep = await validateReport(md, { fetcher: fetcherFor({ TON: noAth }) });

    expect(rep.ok).toBe(false);
    expect(statuses(rep.results)).toEqual(["ATH_UNAVAILABLE"]);
    expect(rep.failures[0]!.detail).toContain("[UNAVAILABLE]");
  });

  test("a 52w-basis level is UNAFFECTED by the presence of an ATH", async () => {
    const md = report("TON", "| 52w High | $8.25 |");
    const rep = await validateReport(md, { fetcher: fetcherFor({ TON: ATH_TRAP }) });
    expect(statuses(rep.results)).toEqual(["OK"]);
  });
});

describe("M4 — wrong-token attribution must never produce a confident PASS", () => {
  // `sectionSymbol` leaked to every line until the next heading, and the row-token regex
  // only fired when the ticker was the FIRST cell. So the report's own signal table
  // (`| 1 | **BTC** | …`) and peer rows never re-attributed, and a LINK claim inside the
  // SOL section was recomputed against SOL's series and stamped OK (−70.8% vs −70.5%).
  test("a ticker in a NON-first cell re-attributes the row (`| 1 | **BTC** | …`)", () => {
    const md = "### 1. SOL — Solana\n\n| 1 | **BTC** | −49.4% from 52w high | HOLD |\n";
    const claims = parseClaims(md);
    expect(claims).toHaveLength(1);
    expect(claims[0]!.symbol).toBe("BTC");
  });

  test("a peer row for LINK inside the SOL section is attributed to LINK, not SOL", async () => {
    const sol: SeriesResult = { ok: true, points: makeSeries(366, 250, 62.18, 73.5) }; // -70.6%
    const link: SeriesResult = { ok: true, points: makeSeries(366, 26.73, 7.19, 8.28) }; // -69.0%
    const md = "### 1. SOL — Solana\n\n| 3 | LINK | −70.8% from 52w high |\n";

    const rep = await validateReport(md, { fetcher: fetcherFor({ SOL: sol, LINK: link }) });
    expect(rep.results[0]!.claim.symbol).toBe("LINK");
    // Against LINK's own series −70.8% is wrong; against SOL's it sneaks inside tolerance.
    // The old code silently passed it. It must now FAIL.
    expect(statuses(rep.results)).toEqual(["MISMATCH"]);
  });

  test("TWO different tickers on one line => AMBIGUOUS_TOKEN, never a coin-flip attribution", async () => {
    const md = "### 1. SOL — Solana\n\n| **SOL** | vs | **LINK** | −70.8% from 52w high |\n";
    const rep = await validateReport(md, {
      fetcher: fetcherFor({ SOL: { ok: true, points: makeSeries(366, 250, 62.18, 73.5) } }),
    });

    expect(rep.ok).toBe(false);
    expect(statuses(rep.results)).toEqual(["AMBIGUOUS_TOKEN"]);
    expect(rep.failures[0]!.claim.symbol).toBeNull();
    expect(rep.failures[0]!.detail).toContain("SOL");
    expect(rep.failures[0]!.detail).toContain("LINK");
  });

  test("a PROSE line naming a foreign token re-attributes too (leak-proof outside tables)", () => {
    const md = "### 1. SOL — Solana\n\nLINK is −70.8% from 52w high.\n";
    expect(parseClaims(md)[0]!.symbol).toBe("LINK");
  });

  test("no regression: a line naming NO token still inherits the section symbol", () => {
    const md = "### 1. SOL — Solana\n\n| 52w Low | $60.13 |\n";
    expect(parseClaims(md)[0]!.symbol).toBe("SOL");
  });
});

describe("m10 — an emphasised heading must still attribute its section", () => {
  // `### 4. **TON** — Toncoin` yielded symbol=null, so EVERY claim in that section
  // became NO_TOKEN — an entire token's figures went unverified.
  const headings = [
    "### 4. **TON** — Toncoin",
    "### 4. TON — Toncoin",
    "## *TON* — Toncoin",
    "### 4. `TON` — Toncoin",
    "#### **TON** – Toncoin",
  ];
  for (const h of headings) {
    test(`«${h}» attributes its section`, () => {
      const claims = parseClaims(`${h}\n\n| 52w Low | $1.00 |\n`);
      expect({ h, s: claims[0]!.symbol }).toEqual({ h, s: "TON" });
    });
  }
});

describe("m9 — --tolerance / --price-tolerance-pct must be usable", () => {
  // `argv.filter(a => !a.startsWith("--"))` treated a flag's VALUE as a filename, so the
  // documented `REPORT.md --tolerance 0.5` gave files=["REPORT.md","0.5"] and exited 2.
  test("a flag VALUE is not mistaken for a filename", () => {
    const { files, flags } = parseArgs(["REPORT.md", "--tolerance", "0.5"]);
    expect(files).toEqual(["REPORT.md"]);
    expect(flags["tolerance"]).toBe("0.5");
  });

  test("both documented value flags parse together with boolean flags", () => {
    const { files, flags } = parseArgs([
      "REPORT.md", "--tolerance", "0.5", "--price-tolerance-pct", "1.0", "--basis-only", "--json",
    ]);
    expect(files).toEqual(["REPORT.md"]);
    expect(flags).toEqual({
      tolerance: "0.5",
      "price-tolerance-pct": "1.0",
      "basis-only": true,
      json: true,
    });
  });

  test("--name=value form works", () => {
    const { files, flags } = parseArgs(["REPORT.md", "--tolerance=0.5"]);
    expect(files).toEqual(["REPORT.md"]);
    expect(flags["tolerance"]).toBe("0.5");
  });

  test("a value flag with a missing value does not swallow the next flag", () => {
    const { files, flags } = parseArgs(["REPORT.md", "--tolerance", "--json"]);
    expect(files).toEqual(["REPORT.md"]);
    expect(flags["tolerance"]).toBe(true);
    expect(flags["json"]).toBe(true);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// RETRACTION EXEMPTION MARKER — `<!-- retracted -->`
//
// The appendix correction table quotes each wrong figure AS DRAFTED so the error stays
// auditable; the validator used to flag those quotes as MISMATCHes forever. The marker
// exempts them — but it is a SUPPRESSION mechanism, so every test below is really a test
// that the suppression cannot be applied broadly, silently, or with ambiguous scope.
// ─────────────────────────────────────────────────────────────────────────────

describe("retraction exemption marker", () => {
  /** UNI fixture: 52w intraday range $2.316 ↔ $12.285 — the drafted $2.00 ↔ $19.47 is wrong. */
  const UNI_OK: SeriesResult = {
    ok: true,
    points: makeSeries(366, 12.285, 2.316, 3.81),
    ath: 44.97,
  };
  const uniFetcher = fetcherFor({ UNI: UNI_OK });

  test("inline marker exempts ONLY its own line; the next line is still validated", async () => {
    const md = report(
      "UNI",
      [
        "| UNI 52w range $2.00 ↔ $19.47 | corrected above | <!-- retracted -->",
        "| Live | 52w Range $2.00 ↔ $19.47 |",
      ].join("\n"),
    );
    const rep = await validateReport(md, { fetcher: uniFetcher });

    const exempt = rep.results.filter((r) => r.status === "RETRACTED");
    const failed = rep.failures;
    expect(exempt.length).toBe(2); // low + high on the marked line
    expect(exempt.every((r) => r.claim.line === 5)).toBe(true);
    // The UNMARKED line right after is still recomputed and still fails.
    expect(failed.length).toBe(2);
    expect(failed.every((r) => r.claim.line === 6 && r.status === "MISMATCH")).toBe(true);
    expect(rep.ok).toBe(false);
  });

  test("block marker exempts claims between start/end; claims AFTER end are validated again", async () => {
    const md = report(
      "UNI",
      [
        "<!-- retracted:start -->",
        "| UNI 52w range $2.00 ↔ $19.47 | as drafted |",
        "<!-- retracted:end -->",
        "| Live | 52w Range $2.00 ↔ $19.47 |",
      ].join("\n"),
    );
    const rep = await validateReport(md, { fetcher: uniFetcher });

    expect(rep.markerErrors).toEqual([]);
    expect(rep.results.filter((r) => r.status === "RETRACTED").map((r) => r.claim.line)).toEqual([6, 6]);
    expect(rep.failures.map((r) => r.claim.line)).toEqual([8, 8]);
    expect(rep.failures.every((r) => r.status === "MISMATCH")).toBe(true);
  });

  test("UNCLOSED retracted:start is a HARD ERROR, not exempt-to-EOF", async () => {
    const md = report(
      "UNI",
      [
        "<!-- retracted:start -->",
        "| UNI 52w range $2.00 ↔ $19.47 | as drafted |",
        "| Live | 52w Range $2.00 ↔ $19.47 |",
      ].join("\n"),
    );
    const rep = await validateReport(md, { fetcher: uniFetcher });

    expect(rep.ok).toBe(false);
    expect(rep.markerErrors.length).toBe(1);
    expect(rep.markerErrors[0]).toContain("unclosed");
    // Nothing is exempted: the rest of the file is STILL validated, so a forgotten
    // closing comment cannot silently suppress every remaining claim.
    expect(rep.exempted).toBe(0);
    expect(rep.results.filter((r) => r.status === "RETRACTED").length).toBe(0);
    expect(rep.failures.length).toBe(4);
  });

  test("nested/duplicate retracted:start is a hard error and does not widen the scope", async () => {
    const md = report(
      "UNI",
      [
        "<!-- retracted:start -->",
        "| UNI 52w range $2.00 ↔ $19.47 | as drafted |",
        "<!-- retracted:start -->",
        "<!-- retracted:end -->",
        "| Live | 52w Range $2.00 ↔ $19.47 |",
      ].join("\n"),
    );
    const rep = await validateReport(md, { fetcher: uniFetcher });

    expect(rep.ok).toBe(false);
    expect(rep.markerErrors.length).toBe(1);
    expect(rep.markerErrors[0]).toContain("nested");
    // Defined behaviour: the duplicate start is IGNORED, the FIRST end closes the block,
    // so the line after `end` is validated normally (the scope never widens silently).
    expect(rep.results.filter((r) => r.status === "RETRACTED").map((r) => r.claim.line)).toEqual([6, 6]);
    expect(rep.failures.map((r) => r.claim.line)).toEqual([9, 9]);
  });

  test("stray retracted:end (no open block) is a hard error", async () => {
    const md = report("UNI", ["<!-- retracted:end -->", "| Live | 52w Range $2.00 ↔ $19.47 |"].join("\n"));
    const rep = await validateReport(md, { fetcher: uniFetcher });

    expect(rep.ok).toBe(false);
    expect(rep.markerErrors[0]).toContain("stray");
    expect(rep.exempted).toBe(0);
  });

  test("an exempted claim still APPEARS in results with RETRACTED status — never dropped", async () => {
    const marked = report("UNI", "| UNI 52w range $2.00 ↔ $19.47 | quoted | <!-- retracted: quoted as drafted -->");
    const unmarked = report("UNI", "| UNI 52w range $2.00 ↔ $19.47 | quoted |");

    const a = await validateReport(marked, { fetcher: uniFetcher });
    const b = await validateReport(unmarked, { fetcher: uniFetcher });

    // Same CLAIM COUNT with and without the marker: exemption changes STATUS, not visibility.
    expect(a.results.length).toBe(b.results.length);
    expect(a.results.length).toBe(2);
    expect(statuses(a.results)).toEqual(["RETRACTED", "RETRACTED"]);
    expect(statuses(b.results)).toEqual(["MISMATCH", "MISMATCH"]);
    expect(a.exempted).toBe(2);
    // The reason and the marker provenance are carried through to the output.
    expect(a.results[0]!.detail).toContain("quoted as drafted");
    expect(a.results[0]!.claim.exemption).toMatchObject({ scope: "inline", markerLine: 5 });
    // And the retracted rows are PRINTED, not hidden.
    expect(formatReport(a, "R.md")).toContain("RETRACTED");
  });

  test("exempted claims do not fail the run when everything else is clean", async () => {
    const md = report("UNI", "| UNI 52w range $2.00 ↔ $19.47 | quoted | <!-- retracted -->");
    const rep = await validateReport(md, { fetcher: uniFetcher });
    expect(rep.ok).toBe(true);
    expect(rep.failures).toEqual([]);
  });

  test("the summary reports the exemption count", async () => {
    const md = report(
      "UNI",
      [
        "| UNI 52w range $2.00 ↔ $19.47 | quoted | <!-- retracted -->",
        "| 52w Low | $2.316 |",
        "| 52w High | $12.285 |",
        "| 52w Range | $2.316 ↔ $12.285 |",
        "| ATH | $44.97 |",
        "| 52w Range | $2.316 ↔ $12.285 |",
      ].join("\n"),
    );
    const rep = await validateReport(md, { fetcher: uniFetcher });
    const out = formatReport(rep, "R.md");

    expect(rep.exempted).toBe(2);
    expect(out).toContain(`⊘ ${rep.exempted} of ${rep.results.length} claim(s) EXEMPTED`);
    // 2/9 = 22% — under the ceiling, so NO abuse warning here.
    expect(out).not.toContain("WARNING");
  });

  test("the >25% abuse warning fires when exemptions dominate", async () => {
    const md = report(
      "UNI",
      [
        "| UNI 52w range $2.00 ↔ $19.47 | quoted | <!-- retracted -->",
        "| 52w Low | $2.316 |",
        "| 52w High | $12.285 |",
      ].join("\n"),
    );
    const rep = await validateReport(md, { fetcher: uniFetcher });
    const out = formatReport(rep, "R.md");

    expect(rep.exempted).toBe(2);
    expect(rep.results.length).toBe(4); // 50% exempted
    expect(out).toContain("⚠ WARNING");
    expect(out).toContain("50% of claims are exempted");
  });

  test("marker errors fail the run even when every claim passes", async () => {
    const md = report("UNI", ["| 52w Low | $2.316 |", "<!-- retracted:end -->"].join("\n"));
    const rep = await validateReport(md, { fetcher: uniFetcher });

    expect(rep.failures).toEqual([]);
    expect(rep.ok).toBe(false);
    expect(formatReport(rep, "R.md")).toContain("MARKER_ERROR");
  });

  test("the marker also bypasses RULE 1 (basis) — a quoted retraction is verbatim", async () => {
    const md = report("UNI", "UNI was drafted as **−80.4% from high** <!-- retracted: quoted as drafted -->");
    const rep = await validateReport(md, { fetcher: uniFetcher });

    expect(statuses(rep.results)).toEqual(["RETRACTED"]);
    expect(rep.ok).toBe(true);
    // …and the same text WITHOUT the marker still fails RULE 1, proving the bypass is
    // the marker's doing and not a regression in the basis rule.
    const bare = await validateReport(report("UNI", "UNI was drafted as **−80.4% from high**"), {
      fetcher: uniFetcher,
    });
    expect(statuses(bare.results)).toEqual(["BASIS_MISSING"]);
  });

  test("the marker applies under --basis-only too (the pre-commit path)", async () => {
    const md = report("UNI", "UNI was drafted as **−80.4% from high** <!-- retracted -->");
    const rep = await validateReport(md, { basisOnly: true });
    expect(statuses(rep.results)).toEqual(["RETRACTED"]);
    expect(rep.ok).toBe(true);
  });

  test("parseExemptions maps scopes precisely and start/end are not read as inline", () => {
    const { byLine, errors } = parseExemptions(
      ["a", "<!-- retracted:start -->", "b", "<!-- retracted:end -->", "c <!-- retracted -->", "d"].join("\n"),
    );
    expect(errors).toEqual([]);
    expect([...byLine.keys()].sort((x, y) => x - y)).toEqual([2, 3, 4, 5]);
    expect(byLine.get(3)).toMatchObject({ scope: "block", markerLine: 2 });
    expect(byLine.get(5)).toMatchObject({ scope: "inline", markerLine: 5 });
    expect(byLine.has(6)).toBe(false);
  });

  test("a report with no markers is completely unaffected", async () => {
    const md = report("UNI", "| 52w Range | $2.316 ↔ $12.285 |");
    const rep = await validateReport(md, { fetcher: uniFetcher });
    expect(rep.exempted).toBe(0);
    expect(rep.markerErrors).toEqual([]);
    expect(rep.ok).toBe(true);
    expect(formatReport(rep, "R.md")).not.toContain("EXEMPTED");
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// VALUE-SCOPED RETRACTION MARKER — `<!-- retracted: $0.410, $0.518 -->`
//
// Line scope proved TOO BLUNT on the real document: the AERO appendix row carries the
// CORRECTED range ($0.3018 ↔ $1.4907) in the SAME table row as the drafted one
// ($0.410 ↔ $0.518), so a whole-line marker suppressed 6 claims when only 4 were quoted
// retractions — silently switching OFF verification of two values that were correct.
// Every test below is a test that a suppression marker cannot cost coverage it was not
// explicitly asked to cost.
// ─────────────────────────────────────────────────────────────────────────────

describe("value-scoped retraction marker", () => {
  /** AERO as of the real report: 365d range $0.3018 ↔ $1.4907, spot $0.416 (−72.1%). */
  const AERO_OK: SeriesResult = {
    ok: true,
    points: makeSeries(366, 1.4907, 0.3018, 0.416),
    ath: 2.32,
  };
  const aeroFetcher = fetcherFor({ AERO: AERO_OK });

  /** The exact shape of the real appendix row: drafted AND corrected range, one line. */
  const AERO_ROW =
    "| AERO 52w range $0.410 ↔ $0.518 | corrected: 365d range $0.3018 ↔ $1.4907 |";

  test("REGRESSION: value scope exempts ONLY the drafted values — the corrected value on the SAME line is still verified", async () => {
    const md = report(
      "AERO",
      `${AERO_ROW} <!-- retracted: $0.410, $0.518 — drafted values quoted verbatim -->`,
    );
    const rep = await validateReport(md, { fetcher: aeroFetcher });

    // Four claims parsed from the row; only the two DRAFTED ones are suppressed.
    expect(rep.results.length).toBe(4);
    expect(rep.exempted).toBe(2);
    const retracted = rep.results.filter((r) => r.status === "RETRACTED").map((r) => r.claim.value);
    expect(retracted.sort((a, b) => a - b)).toEqual([0.41, 0.518]);

    // THE POINT OF THIS CHANGE: the corrected values were NOT suppressed — they were
    // recomputed and they PASS. Under whole-line scope both of these vanished.
    const checked = rep.results.filter((r) => r.status !== "RETRACTED");
    expect(checked.map((r) => r.claim.value).sort((a, b) => a - b)).toEqual([0.3018, 1.4907]);
    expect(statuses(checked)).toEqual(["OK", "OK"]);
    expect(rep.ok).toBe(true);
  });

  test("a corrected value that is WRONG still fails, even though the line carries a marker", async () => {
    // Same row, but the "corrected" high is bogus. A marker naming only the drafted
    // values must not launder it — otherwise value scope is just line scope with extra
    // steps.
    const md = report(
      "AERO",
      "| AERO 52w range $0.410 ↔ $0.518 | corrected: 365d range $0.3018 ↔ $9.9999 |" +
        " <!-- retracted: $0.410, $0.518 -->",
    );
    const rep = await validateReport(md, { fetcher: aeroFetcher });

    expect(rep.exempted).toBe(2);
    expect(rep.failures.length).toBe(1);
    expect(rep.failures[0]!.status).toBe("MISMATCH");
    expect(rep.failures[0]!.claim.value).toBe(9.9999);
    expect(rep.ok).toBe(false);
  });

  test("a listed value matching NOTHING on the line is a HARD ERROR (stale exemption)", async () => {
    const md = report("AERO", `${AERO_ROW} <!-- retracted: $0.410, $0.777 -->`);
    const rep = await validateReport(md, { fetcher: aeroFetcher });

    expect(rep.markerErrors.length).toBe(1);
    expect(rep.markerErrors[0]).toContain("0.777");
    expect(rep.markerErrors[0]).toContain("stale exemption");
    // Only the value that DID match is exempted; $0.518 is no longer covered by the
    // marker, so it is validated normally and fails — which is the correct, loud
    // consequence of a marker that stopped naming it.
    expect(rep.exempted).toBe(1);
    expect(rep.failures.map((r) => r.claim.value)).toEqual([0.518]);
    expect(rep.ok).toBe(false);
    expect(formatReport(rep, "R.md")).toContain("MARKER_ERROR");
  });

  test("marker errors fail the run even when the stale value costs no coverage", async () => {
    // Every real claim passes and every listed value that matters matched — the ONLY
    // problem is the leftover $7.77. The run must still be red.
    const md = report(
      "AERO",
      "| AERO 52w range $0.3018 ↔ $1.4907 | <!-- retracted: $7.77 -->",
    );
    const rep = await validateReport(md, { fetcher: aeroFetcher });

    expect(rep.failures).toEqual([]);
    expect(rep.exempted).toBe(0);
    expect(rep.markerErrors.length).toBe(1);
    expect(rep.ok).toBe(false);
  });

  test("a stale value in a BLOCK marker is an error; the block's other values still work", async () => {
    const md = report(
      "AERO",
      [
        "<!-- retracted:start — $0.410, $0.518, $7.77 -->",
        "| AERO 52w range $0.410 ↔ $0.518 |",
        "<!-- retracted:end -->",
        "| AERO 365d range $0.3018 ↔ $1.4907 |",
      ].join("\n"),
    );
    const rep = await validateReport(md, { fetcher: aeroFetcher });

    expect(rep.markerErrors.length).toBe(1);
    expect(rep.markerErrors[0]).toContain("7.77");
    expect(rep.exempted).toBe(2);
    // The line AFTER the block is untouched and still verified.
    expect(rep.results.filter((r) => r.status === "OK").length).toBe(2);
    expect(rep.ok).toBe(false);
  });

  test("FALLBACK PRESERVED: a bare marker still exempts the WHOLE line, correct values included", async () => {
    const md = report("AERO", `${AERO_ROW} <!-- retracted -->`);
    const rep = await validateReport(md, { fetcher: aeroFetcher });

    // This is the blunt behaviour, retained deliberately — and it is exactly the
    // over-suppression the value form exists to avoid: 4 exempted, 0 verified.
    expect(rep.exempted).toBe(4);
    expect(rep.results.every((r) => r.status === "RETRACTED")).toBe(true);
    expect(rep.markerErrors).toEqual([]);
    expect(rep.ok).toBe(true);
  });

  test("a prose-only reason stays WHOLE-LINE — an incidental number does not silently narrow the scope", async () => {
    const md = report(
      "AERO",
      `${AERO_ROW} <!-- retracted: drafted range quoted verbatim; only 2 weekly bars were claimed -->`,
    );
    const rep = await validateReport(md, { fetcher: aeroFetcher });

    // "2" carries no $ or %, so it is prose, not a listed value. Scope stays whole-line
    // (and, crucially, no bogus stale-value MARKER_ERROR is raised for it).
    expect(rep.exempted).toBe(4);
    expect(rep.markerErrors).toEqual([]);
    expect(rep.results[0]!.claim.exemption?.values).toBeUndefined();
  });

  test("the output DISTINGUISHES value-scoped from whole-line exemptions", async () => {
    const scoped = await validateReport(
      report("AERO", `${AERO_ROW} <!-- retracted: $0.410, $0.518 -->`),
      { fetcher: aeroFetcher },
    );
    const blunt = await validateReport(report("AERO", `${AERO_ROW} <!-- retracted -->`), {
      fetcher: aeroFetcher,
    });

    const a = formatReport(scoped, "R.md");
    const b = formatReport(blunt, "R.md");

    expect(a).toContain("RETRACTED[value]");
    expect(a).not.toContain("RETRACTED[line]");
    expect(b).toContain("RETRACTED[line]");
    expect(b).not.toContain("RETRACTED[value]");

    // Per-claim detail names the matched value / says the suppression was blunt.
    expect(scoped.results.find((r) => r.status === "RETRACTED")!.detail).toContain("value-scoped to 0.41");
    expect(blunt.results[0]!.detail).toContain("whole-line (blunt");

    // …and the summary line breaks the count down by scope.
    expect(a).toContain("(2 value-scoped, 0 whole-line)");
    expect(b).toContain("(0 value-scoped, 4 whole-line)");

    expect(statusLabel(scoped.results.find((r) => r.status === "RETRACTED")!)).toBe("RETRACTED[value]");
    expect(statusLabel(blunt.results[0]!)).toBe("RETRACTED[line]");
  });

  test("value parsing survives thousands separators, unicode minus, percent and emphasis", () => {
    expect(parseMarkerValues("$1,505.00")).toEqual([1505]);
    expect(parseMarkerValues("−80.4%")).toEqual([-80.4]);          // U+2212
    expect(parseMarkerValues("-80.4%")).toEqual([-80.4]);          // ASCII hyphen
    expect(parseMarkerValues("–80.4%")).toEqual([-80.4]);          // en-dash
    expect(parseMarkerValues("**$19.47**")).toEqual([19.47]);
    expect(parseMarkerValues("$0.410, $0.518")).toEqual([0.41, 0.518]);
    expect(parseMarkerValues("$1,505.00 ↔ $4,956.78")).toEqual([1505, 4956.78]);
    expect(parseMarkerValues("−80.4%, $2.00, $19.47 — drafted values quoted verbatim")).toEqual([
      -80.4, 2, 19.47,
    ]);
    // Values are read ONLY from the head, before the first — / – / ;. Prose that quotes
    // a number must not widen the marker's own scope — this is the real bug found when
    // applying the markers to the shipped report.
    expect(parseMarkerValues("$0.410, $0.518 — the corrected $0.3018 ↔ $1.4907 stays verified")).toEqual([
      0.41, 0.518,
    ]);
    expect(parseMarkerValues("drafted range quoted verbatim; corrected value is $0.3018")).toBeUndefined();
    // No sigil ⇒ not a value ⇒ whole-line fallback.
    expect(parseMarkerValues("quoted as drafted, corrected above")).toBeUndefined();
    expect(parseMarkerValues("only 2 weekly bars available")).toBeUndefined();
    expect(parseMarkerValues(undefined)).toBeUndefined();
  });

  test("a leading dash is a SIGN when a digit follows it and a SEPARATOR when one does not", () => {
    // En-dash plays both roles in real documents, so the distinction must be positional.
    expect(parseMarkerValues("–80.4%")).toEqual([-80.4]);        // sign, glued to digits
    expect(parseMarkerValues("— $0.410, $0.518")).toEqual([0.41, 0.518]); // separator
    expect(parseMarkerValues("- $0.410")).toEqual([0.41]);
    expect(parseMarkerValues("−80.4% — quoted as drafted")).toEqual([-80.4]);
  });

  test("matching is on the PARSED NUMBER and on absolute value (drawdowns are stored signed)", () => {
    expect(valueMatches(1505, 1505.0)).toBe(true);
    expect(valueMatches(-80.4, -80.4)).toBe(true);
    expect(valueMatches(80.4, -80.4)).toBe(true);   // marker may omit the sign
    expect(valueMatches(-80.4, 80.4)).toBe(true);
    expect(valueMatches(0.41, 0.410)).toBe(true);
    expect(valueMatches(0.41, 0.42)).toBe(false);
    expect(valueMatches(1505, 1506)).toBe(false);
  });

  test("a `$1,505.00`-style marker matches a `$1,505.00`-style claim end to end", async () => {
    const ETH_OK: SeriesResult = { ok: true, points: makeSeries(366, 4956.78, 1505.0, 3800), ath: 4956.78 };
    const md = report(
      "ETH",
      "| ETH drafted 52w range $1,385.00 ↔ $4,957.00 | true 52w range $1,505.00 ↔ $4,956.78 |" +
        " <!-- retracted: $1,385.00, $4,957.00 -->",
    );
    const rep = await validateReport(md, { fetcher: fetcherFor({ ETH: ETH_OK }) });

    expect(rep.markerErrors).toEqual([]);
    expect(rep.exempted).toBe(2);
    expect(
      rep.results.filter((r) => r.status === "RETRACTED").map((r) => r.claim.value).sort((a, b) => a - b),
    ).toEqual([1385, 4957]);
    expect(statuses(rep.results.filter((r) => r.status !== "RETRACTED"))).toEqual(["OK", "OK"]);
    expect(rep.ok).toBe(true);
  });

  test("a value-scoped marker exempts a DRAWDOWN and leaves the corrected drawdown checked", async () => {
    const md = report(
      "AERO",
      "AERO was drafted at **−19.6% from high**; the true figure is **−72.1% from its 52w high**." +
        " <!-- retracted: -19.6% -->",
    );
    const rep = await validateReport(md, { fetcher: aeroFetcher });

    expect(rep.exempted).toBe(1);
    const retracted = rep.results.find((r) => r.status === "RETRACTED")!;
    expect(retracted.claim.value).toBe(-19.6);
    // The bare "from high" on the drafted quote is exempt from RULE 1 as well…
    expect(retracted.status).toBe("RETRACTED");
    // …while the corrected, basis-explicit figure is recomputed and passes.
    const live = rep.results.filter((r) => r.status !== "RETRACTED");
    expect(live.map((r) => r.claim.value)).toEqual([-72.1]);
    expect(statuses(live)).toEqual(["OK"]);
    expect(rep.ok).toBe(true);
  });

  test("staleExemptionErrors is silent when every listed value matches", () => {
    const md = report("AERO", `${AERO_ROW} <!-- retracted: $0.410, $0.518 -->`);
    expect(staleExemptionErrors(parseExemptions(md), parseClaims(md))).toEqual([]);
  });

  test("parseExemptions carries the listed values through to the exemption", () => {
    const { byLine, errors } = parseExemptions("a <!-- retracted: $0.410, $0.518 -->");
    expect(errors).toEqual([]);
    expect(byLine.get(1)).toMatchObject({ scope: "inline", markerLine: 1, values: [0.41, 0.518] });
  });
});
