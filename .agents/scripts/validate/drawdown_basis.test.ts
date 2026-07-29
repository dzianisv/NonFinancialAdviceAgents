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
  MIN_SERIES_POINTS,
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
