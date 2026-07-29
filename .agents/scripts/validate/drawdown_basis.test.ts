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
   * that silently disappears — only a COUNT can. This fixture holds exactly 12 known
   * claims across every supported form; if any future edit makes one invisible, this
   * test fails even though every other assertion in the file still passes.
   */
  test("GUARD: a fixture with 12 known claims extracts EXACTLY 12 (silent-drop canary)", () => {
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
      "| ATH | $4,891.70 (−23.0%) |", //  8 drawdown
      "| % from ATH | −23.0% |", //  9 drawdown
      "",
      "### 3. PUMP — Pump.fun",
      "",
      "| 52w Low | $0.001199 |", // 10 low
      "| 52w High (close) | $0.017 |", // 11 high
      "PUMP is down 93% from highs.", // 12 drawdown (BASIS_MISSING, still a claim)
    ].join("\n");

    const claims = parseClaims(md);
    const summary = claims.map((c) => `L${c.line}:${c.symbol}:${c.kind}:${c.value}`);
    expect({ n: claims.length, summary }).toEqual({ n: 12, summary });
    expect(claims).toHaveLength(12);
    expect(claims.filter((c) => c.kind === "low")).toHaveLength(3);
    expect(claims.filter((c) => c.kind === "high")).toHaveLength(3);
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
