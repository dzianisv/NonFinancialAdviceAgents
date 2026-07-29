#!/usr/bin/env bun
/**
 * drawdown_basis.ts — drawdown-BASIS validator for published crypto/equity reports.
 *
 * WHY THIS EXISTS (three real incidents, all the same bug class):
 *   1. TON published as "−49.2% from high" — measured over a truncated ~37-week
 *      window; the 52w-basis figure was −59.1%.
 *   2. TON published as "−82.5% from high" — ATH basis ($8.25) inside a report whose
 *      every other figure was 52w basis.
 *   3. JUP published as "−87% from high" — ATH basis ($2.00) when the 52w-basis
 *      figure is −65.2%.
 *   Plus: LINK's "52w low $7.00" was an eyeballed round number; the series low is $7.19.
 *
 * Every one of those shipped because the BASIS was ambiguous and nobody recomputed
 * the number from a single canonical series. This validator makes both failures loud:
 *
 *   RULE 1 (basis)     — every drawdown claim MUST disambiguate to 52w or ATH.
 *                        A bare "from high"/"from highs" is a FAIL (BASIS_MISSING).
 *   RULE 2 (recompute) — every claim is recomputed from ONE canonical daily-close
 *                        series per token and FAILS on mismatch beyond a tolerance
 *                        (default 0.5 percentage points).
 *   RULE 3 (window)    — the series must be >= 360 daily points. A short series is a
 *                        LOUD FAIL (SHORT_SERIES), never a silent pass. That truncated
 *                        window is literally incident #1.
 *   RULE 4 (honesty)   — a fetch error is FETCH_FAILED and fails the run. Missing data
 *                        is [UNAVAILABLE] and loud (repo invariant #4), never a skip.
 *
 * Also validates stated 52w low / 52w high / 52w range levels against the same series.
 *
 * Usage:
 *   bun .agents/scripts/validate/drawdown_basis.ts research/crypto-portfolio-2026-07-24.md
 *   bun .agents/scripts/validate/drawdown_basis.ts REPORT.md --tolerance 0.5 --price-tolerance-pct 1.0
 *   bun .agents/scripts/validate/drawdown_basis.ts REPORT.md --basis-only   # no network; RULE 1 only
 *   bun .agents/scripts/validate/drawdown_basis.ts REPORT.md --json
 *
 * Exit code 0 = every claim OK; 1 = one or more claims failed; 2 = bad invocation.
 *
 * The price-series fetcher is DEPENDENCY-INJECTED (`validateReport(md, { fetcher })`)
 * so the unit tests are hermetic and need no network. See drawdown_basis.test.ts.
 */

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export type SeriesPoint = { t: number; c: number };

export type SeriesOk = {
  ok: true;
  /** Daily closes, oldest-first. Must be >= MIN_SERIES_POINTS or RULE 3 fails. */
  points: SeriesPoint[];
  /** All-time high in USD. Absent => any ATH-basis claim is [UNAVAILABLE] (loud). */
  ath?: number;
};
export type SeriesErr = { ok: false; error: string };
export type SeriesResult = SeriesOk | SeriesErr;

/** Injected so tests are hermetic. Keyed by report symbol (e.g. "TON"). */
export type SeriesFetcher = (symbol: string) => Promise<SeriesResult>;

export type Basis = "52w" | "ATH" | "UNKNOWN";
export type ClaimKind = "drawdown" | "low" | "high";

export type Claim = {
  line: number;
  /** Column span in the source line, used to de-duplicate overlapping matches. */
  start: number;
  end: number;
  symbol: string | null;
  raw: string;
  kind: ClaimKind;
  basis: Basis;
  /** Drawdown: signed percent (always <= 0). Low/high: a USD price level. */
  value: number;
};

export type Status =
  | "OK"
  | "BASIS_MISSING"
  | "MISMATCH"
  | "FETCH_FAILED"
  | "SHORT_SERIES"
  | "ATH_UNAVAILABLE"
  | "NO_TOKEN";

export type ClaimResult = {
  claim: Claim;
  status: Status;
  recomputed?: number;
  detail: string;
};

export type ValidationReport = {
  results: ClaimResult[];
  failures: ClaimResult[];
  ok: boolean;
};

export type ValidateOptions = {
  fetcher?: SeriesFetcher;
  /** Drawdown tolerance in PERCENTAGE POINTS. Default 0.5. */
  tolerance?: number;
  /** Price-level tolerance as a RELATIVE percent of the recomputed level. Default 1.0. */
  priceTolerancePct?: number;
  /** RULE 1 only: skip every recompute (no network). Default false. */
  basisOnly?: boolean;
  /** Minimum acceptable daily-close count. Default 360. */
  minSeriesPoints?: number;
};

// ─────────────────────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────────────────────

export const MIN_SERIES_POINTS = 360;
export const DEFAULT_TOLERANCE_PP = 0.5;
export const DEFAULT_PRICE_TOLERANCE_PCT = 1.0;

/** Report symbol → CoinGecko coin id. Extend as the book changes. */
export const COINGECKO_IDS: Readonly<Record<string, string>> = {
  BTC: "bitcoin",
  ETH: "ethereum",
  SOL: "solana",
  TON: "the-open-network",
  HYPE: "hyperliquid",
  AAVE: "aave",
  JUP: "jupiter-exchange-solana",
  UNI: "uniswap",
  AERO: "aerodrome-finance",
  PUMP: "pump-fun",
  LINK: "chainlink",
};

/** Unicode minus (U+2212), ASCII hyphen, en-dash — all appear in real reports. */
const MINUS = "[−\\-–]";
const NUM = "\\d+(?:[.,]\\d+)?";

// ─────────────────────────────────────────────────────────────────────────────
// Small helpers
// ─────────────────────────────────────────────────────────────────────────────

/** Normalizes a numeric token: strips thousands separators and unicode minus. */
function num(raw: string): number {
  return Number(raw.replace(/,/g, "").replace(/[−–]/g, "-"));
}

function stripMarkup(s: string): string {
  return s.replace(/\*\*/g, "").replace(/`/g, "").trim();
}

/**
 * Resolves the basis from a text fragment. Recognises 52w / 52-week / 52 week /
 * 365d / 1y-high phrasing as 52w, and ATH / all-time / all time as ATH.
 * Anything else is UNKNOWN — which is a FAIL, by design (RULE 1).
 */
export function resolveBasis(fragment: string): Basis {
  const f = fragment.toLowerCase();
  const is52w = /\b(52\s*-?\s*w(?:eek)?|365\s*-?\s*d(?:ay)?|1\s*-?\s*y(?:ear)?)\b/.test(f);
  const isAth = /\b(ath|all\s*-?\s*time)\b/.test(f);
  // Both mentioned in one fragment is still ambiguous → treat the nearer, explicit
  // "from ATH"/"from 52w high" phrasing as authoritative; fall through to 52w only
  // when ATH is absent.
  if (isAth && !is52w) return "ATH";
  if (is52w && !isAth) return "52w";
  if (is52w && isAth) {
    // Prefer whichever qualifier directly precedes the word "high".
    const m = f.match(/(ath|all\s*-?\s*time|52\s*-?\s*w(?:eek)?|365\s*-?\s*d|1\s*-?\s*y)[^a-z0-9]{0,12}high/);
    if (m) return /ath|all/.test(m[1]!) ? "ATH" : "52w";
    return "52w";
  }
  return "UNKNOWN";
}

/**
 * The context a basis qualifier may legally live in. Inside a markdown table this is
 * the ENCLOSING CELL (a basis stated in a different column is not this claim's basis).
 * Outside a table it is the enclosing sentence — so "On the 52w-high basis, ... = −59.1%
 * from high" correctly resolves, while a bare sentence does not.
 */
export function contextFor(line: string, start: number, end: number): string {
  if (line.trimStart().startsWith("|")) {
    const left = line.lastIndexOf("|", start);
    const right = line.indexOf("|", end);
    const a = left === -1 ? 0 : left + 1;
    const b = right === -1 ? line.length : right;
    // A `| label | value |` pair: the label cell carries the basis for the value cell.
    const prevLeft = a > 1 ? line.lastIndexOf("|", a - 2) : -1;
    const labelCell = prevLeft === -1 ? "" : line.slice(prevLeft + 1, a - 1);
    return `${labelCell} ${line.slice(a, b)}`;
  }
  // Sentence scope: split on ". " / "! " / "? " but not on "$1.44" or "(2025-08-02)".
  const before = line.slice(0, start);
  const after = line.slice(end);
  const bStart = Math.max(
    before.lastIndexOf(". "),
    before.lastIndexOf("! "),
    before.lastIndexOf("? "),
    before.lastIndexOf("; "),
  );
  const aEndRel = Math.min(
    ...[after.indexOf(". "), after.indexOf("! "), after.indexOf("? ")]
      .map((i) => (i === -1 ? after.length : i)),
  );
  return before.slice(bStart + 1) + line.slice(start, end) + after.slice(0, aEndRel);
}

// ─────────────────────────────────────────────────────────────────────────────
// Parsing
// ─────────────────────────────────────────────────────────────────────────────

const RE_HEADING_TOKEN = /^#{1,6}\s*(?:\d+\.\s*)?([A-Z]{2,6})\s*[—–-]/;
const RE_ROW_TOKEN = /^\|\s*\*{0,2}([A-Z]{2,6})\*{0,2}\s*\|/;

/**
 * `| % from 52w High | −62.6% |`, `| % from ATH | −23% |`, `| % from High | −73% |`
 * The label cell must mention a peak (`high` or `ATH`) — note `from ATH` has no
 * literal "high", which is exactly how the JUP/TON ATH figures slipped past review.
 */
const RE_TABLE_PCT = new RegExp(
  `\\|\\s*%?\\s*(?:change\\s+)?from\\s+([^|]*(?:high|ath|all[\\s-]?time)[^|]*)\\|\\s*\\*{0,2}\\s*(${MINUS})?\\s*(${NUM})\\s*%`,
  "gi",
);

/** `| 52w High | $126,200 (−49.3%) |`, `| ATH | $8.25 (−82.5%) |` */
const RE_TABLE_LEVEL_PCT = new RegExp(
  `\\|\\s*\\*{0,2}([^|]*?high[^|]*?|[^|]*?ath[^|]*?)\\*{0,2}\\s*\\|[^|]*?\\((${MINUS})\\s*(${NUM})\\s*%\\)`,
  "gi",
);

/**
 * Prose: `−87% from high`, `down 87% from highs`, `−59.1% from true 52w high`,
 * `(−23% from ATH)`, `−72% from 52-week highs`, `-65.2% off its all-time high`.
 * The peak word is `high(s)` OR a bare `ATH` — "from ATH" contains no literal "high",
 * and that phrasing is precisely how ATH-basis figures got mixed into 52w reports.
 * The qualifier group is deliberately permissive (its/the/true/standard/current/…)
 * so a missed claim — the silent failure we are fixing — cannot happen quietly.
 */
const RE_PROSE_PCT = new RegExp(
  `(${MINUS})?\\s*(${NUM})\\s*%\\s+(?:from|off|below|under)\\s+((?:its|the|their|true|standard|current|prior|recent|a)\\s+)*([^%.,;:)\\n]{0,28}?)(highs?|ath)\\b`,
  "gi",
);

/** `| 52w Low | $52,550 |`, `| 52w High | $126,200 ... |` */
const RE_TABLE_LEVEL = new RegExp(
  `\\|\\s*\\*{0,2}\\s*(52\\s*-?\\s*w(?:eek)?|365\\s*-?\\s*d|ath|all\\s*-?\\s*time)\\s*(low|high)?\\s*\\*{0,2}\\s*\\|\\s*\\*{0,2}\\s*\\$(${NUM})`,
  "gi",
);

/** `| 52w Range | $1,385 ↔ $4,957 |` and prose `52w range $7.19–$26.73` */
const RE_RANGE = new RegExp(
  `(52\\s*-?\\s*w(?:eek)?|365\\s*-?\\s*d)\\s*range[^$\\n]{0,24}\\$\\*{0,2}(${NUM})\\*{0,2}\\s*(?:↔|–|—|-|to)\\s*\\*{0,2}\\$?(${NUM})`,
  "gi",
);

function overlaps(claims: Claim[], line: number, start: number, end: number): boolean {
  return claims.some((c) => c.line === line && start < c.end && end > c.start);
}

/**
 * Extracts EVERY drawdown / 52w-level claim from a markdown report.
 * Token attribution: the nearest preceding `### N. SYM — Name` heading, overridden
 * per-line by a `| **SYM** | …` summary-table row (the CIO synthesis table).
 */
export function parseClaims(markdown: string): Claim[] {
  const lines = markdown.split(/\r?\n/);
  const claims: Claim[] = [];
  let sectionSymbol: string | null = null;

  lines.forEach((line, i) => {
    const lineNo = i + 1;
    const h = line.match(RE_HEADING_TOKEN);
    if (h && COINGECKO_IDS[h[1]!]) {
      sectionSymbol = h[1]!;
    } else if (/^#{1,6}\s/.test(line)) {
      // A heading that names no token ENDS the previous token's section. Letting the
      // symbol leak into a later prose section (correction logs, skeptic gates) would
      // silently validate one token's figure against another token's series — a
      // false PASS, which is worse than an honest NO_TOKEN failure.
      sectionSymbol = null;
    }
    const rowTok = line.match(RE_ROW_TOKEN);
    // A `| **JUP** | …` row re-attributes only that line, not the section.
    const symbol =
      rowTok && COINGECKO_IDS[rowTok[1]!] ? rowTok[1]! : sectionSymbol;

    const push = (start: number, end: number, kind: ClaimKind, basis: Basis, value: number) => {
      if (overlaps(claims, lineNo, start, end)) return;
      claims.push({
        line: lineNo,
        start,
        end,
        symbol,
        raw: stripMarkup(line.slice(start, end)),
        kind,
        basis,
        value,
      });
    };

    // Order matters: the most specific (table) patterns claim their spans first, so a
    // later generic prose match cannot double-count the same text.
    for (const m of line.matchAll(RE_TABLE_PCT)) {
      const idx = m.index ?? 0;
      const basis = resolveBasis(`${m[1] ?? ""} high`);
      push(idx, idx + m[0].length, "drawdown", basis, -Math.abs(num(m[3]!)));
    }
    for (const m of line.matchAll(RE_TABLE_LEVEL_PCT)) {
      const idx = m.index ?? 0;
      const basis = resolveBasis(m[1] ?? "");
      push(idx, idx + m[0].length, "drawdown", basis, -Math.abs(num(m[3]!)));
    }
    for (const m of line.matchAll(RE_PROSE_PCT)) {
      const idx = m.index ?? 0;
      const end = idx + m[0].length;
      // Basis may be stated in the qualifier itself OR earlier in the same cell/sentence.
      const inline = `${m[3] ?? ""}${m[4] ?? ""} ${m[5] ?? "high"}`;
      let basis = resolveBasis(inline);
      if (basis === "UNKNOWN") basis = resolveBasis(contextFor(line, idx, end));
      push(idx, end, "drawdown", basis, -Math.abs(num(m[2]!)));
    }
    for (const m of line.matchAll(RE_RANGE)) {
      const idx = m.index ?? 0;
      const end = idx + m[0].length;
      const lo = num(m[2]!);
      const hi = num(m[3]!);
      // Split the span so the low and the high are two INDEPENDENT claims that do not
      // overlap each other (an overlap would silently drop one of them).
      const sepRel = m[0].search(/↔|–|—|-|\bto\b/);
      const mid = sepRel === -1 ? idx + Math.floor(m[0].length / 2) : idx + sepRel;
      const basis = resolveBasis(m[1]!);
      push(idx, mid, lo <= hi ? "low" : "high", basis, lo);
      push(mid, end, lo <= hi ? "high" : "low", basis, hi);
    }
    for (const m of line.matchAll(RE_TABLE_LEVEL)) {
      const idx = m.index ?? 0;
      const which = (m[2] ?? "").toLowerCase();
      if (which !== "low" && which !== "high") continue;
      push(idx, idx + m[0].length, which as ClaimKind, resolveBasis(m[1]!), num(m[3]!));
    }
  });

  return claims.sort((a, b) => a.line - b.line || a.start - b.start);
}

// ─────────────────────────────────────────────────────────────────────────────
// Recompute + validate
// ─────────────────────────────────────────────────────────────────────────────

export function drawdownFrom(points: SeriesPoint[], peak: number): number {
  const spot = points[points.length - 1]!.c;
  return (spot / peak - 1) * 100;
}

export function seriesHigh(points: SeriesPoint[]): number {
  return Math.max(...points.map((p) => p.c));
}
export function seriesLow(points: SeriesPoint[]): number {
  return Math.min(...points.map((p) => p.c));
}

/**
 * Validates a markdown report. All recomputation for a given token comes from ONE
 * fetched series (fetched at most once per token per run) — that single-source rule is
 * what makes the TON truncated-window incident impossible to repeat.
 */
export async function validateReport(
  markdown: string,
  opts: ValidateOptions = {},
): Promise<ValidationReport> {
  const tolerance = opts.tolerance ?? DEFAULT_TOLERANCE_PP;
  const priceTol = opts.priceTolerancePct ?? DEFAULT_PRICE_TOLERANCE_PCT;
  const minPoints = opts.minSeriesPoints ?? MIN_SERIES_POINTS;
  const fetcher = opts.fetcher;

  const claims = parseClaims(markdown);
  const results: ClaimResult[] = [];
  const cache = new Map<string, SeriesResult>();

  async function series(symbol: string): Promise<SeriesResult> {
    const hit = cache.get(symbol);
    if (hit) return hit;
    if (!fetcher) {
      const r: SeriesResult = { ok: false, error: "no fetcher injected" };
      cache.set(symbol, r);
      return r;
    }
    let r: SeriesResult;
    try {
      r = await fetcher(symbol);
    } catch (e) {
      r = { ok: false, error: e instanceof Error ? e.message : String(e) };
    }
    cache.set(symbol, r);
    return r;
  }

  for (const claim of claims) {
    // RULE 1 — basis first, and it applies to drawdowns whether or not we have data.
    if (claim.kind === "drawdown" && claim.basis === "UNKNOWN") {
      results.push({
        claim,
        status: "BASIS_MISSING",
        detail:
          'drawdown stated without an explicit basis — say "from 52w high" or "from ATH"',
      });
      continue;
    }
    if (opts.basisOnly) {
      results.push({ claim, status: "OK", detail: "basis explicit (recompute skipped: --basis-only)" });
      continue;
    }
    if (!claim.symbol) {
      results.push({
        claim,
        status: "NO_TOKEN",
        detail: "[UNAVAILABLE] could not attribute this claim to a token — cannot recompute",
      });
      continue;
    }

    const s = await series(claim.symbol);
    if (!s.ok) {
      results.push({
        claim,
        status: "FETCH_FAILED",
        detail: `[UNAVAILABLE] price series for ${claim.symbol}: ${s.error}`,
      });
      continue;
    }
    // RULE 3 — a short window is exactly the TON bug. Loud, never silent.
    if (s.points.length < minPoints) {
      results.push({
        claim,
        status: "SHORT_SERIES",
        detail: `series for ${claim.symbol} has ${s.points.length} daily points, need >= ${minPoints} (truncated window)`,
      });
      continue;
    }

    let recomputed: number;
    if (claim.kind === "drawdown") {
      if (claim.basis === "ATH") {
        if (typeof s.ath !== "number" || !(s.ath > 0)) {
          results.push({
            claim,
            status: "ATH_UNAVAILABLE",
            detail: `[UNAVAILABLE] no ATH for ${claim.symbol} — cannot verify an ATH-basis drawdown`,
          });
          continue;
        }
        recomputed = drawdownFrom(s.points, s.ath);
      } else {
        recomputed = drawdownFrom(s.points, seriesHigh(s.points));
      }
      const delta = Math.abs(recomputed - claim.value);
      results.push(
        delta <= tolerance
          ? { claim, status: "OK", recomputed, detail: `stated ${claim.value.toFixed(1)}% vs recomputed ${recomputed.toFixed(1)}% (Δ${delta.toFixed(2)}pp)` }
          : { claim, status: "MISMATCH", recomputed, detail: `stated ${claim.value.toFixed(1)}% vs recomputed ${recomputed.toFixed(1)}% (Δ${delta.toFixed(2)}pp > ${tolerance}pp)` },
      );
      continue;
    }

    // Price levels (52w low / 52w high).
    recomputed = claim.kind === "low" ? seriesLow(s.points) : seriesHigh(s.points);
    const relPct = Math.abs(recomputed - claim.value) / recomputed * 100;
    results.push(
      relPct <= priceTol
        ? { claim, status: "OK", recomputed, detail: `stated $${claim.value} vs series $${recomputed.toPrecision(6)} (${relPct.toFixed(2)}%)` }
        : { claim, status: "MISMATCH", recomputed, detail: `stated $${claim.value} vs series $${recomputed.toPrecision(6)} (${relPct.toFixed(2)}% > ${priceTol}%)` },
    );
  }

  const failures = results.filter((r) => r.status !== "OK");
  return { results, failures, ok: failures.length === 0 };
}

// ─────────────────────────────────────────────────────────────────────────────
// CoinGecko fetcher (the production series source)
// ─────────────────────────────────────────────────────────────────────────────

const CG = "https://api.coingecko.com/api/v3";

/** CoinGecko's keyless tier is ~5-15 req/min. Serialize + pace to avoid self-DoS. */
const MIN_REQUEST_GAP_MS = 3_000;
const MAX_429_RETRIES = 6;
let requestChain: Promise<unknown> = Promise.resolve();
let lastRequestAt = 0;

/** Serializes every CoinGecko call and enforces a minimum inter-request gap. */
function paced<T>(fn: () => Promise<T>): Promise<T> {
  const run = requestChain.then(async () => {
    const wait = lastRequestAt + MIN_REQUEST_GAP_MS - Date.now();
    if (wait > 0) await new Promise((s) => setTimeout(s, wait));
    lastRequestAt = Date.now();
    return fn();
  });
  requestChain = run.catch(() => undefined);
  return run;
}

async function getJson(url: string, attempt = 0): Promise<unknown> {
  const r = await paced(() => fetch(url, { headers: { accept: "application/json" } }));
  if (r.status === 429) {
    // CoinGecko's free tier rate-limits aggressively. Exponential backoff, then give
    // up LOUDLY — a rate-limit must never degrade into a silent pass.
    if (attempt >= MAX_429_RETRIES) {
      throw new Error(`HTTP 429 rate-limited by CoinGecko after ${MAX_429_RETRIES + 1} attempts`);
    }
    const waitMs = 5_000 * 2 ** attempt;
    console.error(`   … HTTP 429 from CoinGecko, backing off ${waitMs}ms (attempt ${attempt + 1}/${MAX_429_RETRIES + 1})`);
    await new Promise((s) => setTimeout(s, waitMs));
    return getJson(url, attempt + 1);
  }
  if (!r.ok) throw new Error(`HTTP ${r.status} ${r.statusText}`);
  return r.json();
}

/** Production fetcher: 366 daily closes + the coin's all-time high, from CoinGecko. */
export function coingeckoFetcher(ids: Record<string, string> = COINGECKO_IDS): SeriesFetcher {
  return async (symbol: string): Promise<SeriesResult> => {
    const id = ids[symbol];
    if (!id) return { ok: false, error: `no CoinGecko id mapped for symbol ${symbol}` };
    try {
      const chart = (await getJson(
        `${CG}/coins/${id}/market_chart?vs_currency=usd&days=365&interval=daily`,
      )) as { prices?: [number, number][] };
      const prices = chart.prices ?? [];
      const points: SeriesPoint[] = prices.map(([t, c]) => ({ t, c }));

      let ath: number | undefined;
      try {
        const meta = (await getJson(
          `${CG}/coins/${id}?localization=false&tickers=false&community_data=false&developer_data=false&sparkline=false`,
        )) as { market_data?: { ath?: { usd?: number } } };
        const v = meta.market_data?.ath?.usd;
        if (typeof v === "number" && v > 0) ath = v;
      } catch {
        // ATH lookup failed → leave undefined so ATH claims report ATH_UNAVAILABLE
        // (loud), rather than silently validating against the 52w high.
      }
      return { ok: true, points, ath };
    } catch (e) {
      return { ok: false, error: e instanceof Error ? e.message : String(e) };
    }
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// CLI
// ─────────────────────────────────────────────────────────────────────────────

const ICON: Record<Status, string> = {
  OK: "✓",
  BASIS_MISSING: "✗",
  MISMATCH: "✗",
  FETCH_FAILED: "✗",
  SHORT_SERIES: "✗",
  ATH_UNAVAILABLE: "✗",
  NO_TOKEN: "✗",
};

export function formatReport(rep: ValidationReport, path: string): string {
  const out: string[] = [`drawdown-basis validation — ${path}`, ""];
  for (const r of rep.results) {
    const sym = r.claim.symbol ?? "?";
    out.push(
      `${ICON[r.status]} ${r.status.padEnd(15)} L${String(r.claim.line).padStart(4)} ` +
        `${sym.padEnd(5)} [${r.claim.basis}] ${r.claim.kind}  «${r.claim.raw.slice(0, 72)}»`,
    );
    if (r.status !== "OK") out.push(`    → ${r.detail}`);
  }
  out.push("");
  out.push(
    rep.ok
      ? `✓ all ${rep.results.length} claim(s) passed`
      : `✗ ${rep.failures.length} of ${rep.results.length} claim(s) FAILED`,
  );
  return out.join("\n");
}

async function main(argv: string[]): Promise<number> {
  const files = argv.filter((a) => !a.startsWith("--"));
  const flag = (name: string): string | undefined => {
    const i = argv.indexOf(`--${name}`);
    return i === -1 ? undefined : argv[i + 1];
  };
  if (files.length !== 1) {
    console.error("usage: bun drawdown_basis.ts <report.md> [--tolerance 0.5] [--price-tolerance-pct 1.0] [--basis-only] [--json]");
    return 2;
  }
  const path = files[0]!;
  const md = await Bun.file(path).text();

  const basisOnly = argv.includes("--basis-only");
  const rep = await validateReport(md, {
    fetcher: basisOnly ? undefined : coingeckoFetcher(),
    basisOnly,
    tolerance: flag("tolerance") ? Number(flag("tolerance")) : undefined,
    priceTolerancePct: flag("price-tolerance-pct") ? Number(flag("price-tolerance-pct")) : undefined,
  });

  console.log(argv.includes("--json") ? JSON.stringify(rep, null, 2) : formatReport(rep, path));
  return rep.ok ? 0 : 1;
}

if (import.meta.main) {
  process.exit(await main(process.argv.slice(2)));
}
