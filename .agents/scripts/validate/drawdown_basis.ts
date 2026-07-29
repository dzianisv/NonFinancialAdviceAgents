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
 *   RULE 2 (recompute) — every claim is recomputed and FAILS on mismatch beyond a
 *                        tolerance (default 0.5pp / 1.0% for price levels).
 *   RULE 3 (window)    — the series must be >= 360 daily points. A short series is a
 *                        LOUD FAIL (SHORT_SERIES), never a silent pass. That truncated
 *                        window is literally incident #1.
 *   RULE 4 (honesty)   — a fetch error is FETCH_FAILED and fails the run. Missing data
 *                        is [UNAVAILABLE] and loud (repo invariant #4), never a skip.
 *   RULE 5 (like-for-like) — reports quote INTRADAY extremes (TradingView/exchange
 *                        candles). CoinGecko's market_chart returns daily CLOSES ONLY.
 *                        Comparing an intraday claim against a close-only series
 *                        produced systematic FALSE POSITIVES: SOL's true 52w intraday
 *                        low is $60.11 (report said $60.13 — correct) but the close-only
 *                        low is $62.18, so the validator wrongly cried MISMATCH. Same for
 *                        AAVE ($57.82 intraday vs $60.79 close; report said $57.83).
 *                        So: recompute BOTH conventions, pass on EITHER, and always SAY
 *                        which one matched (`OK[intraday]` / `OK[close]`). A claim that
 *                        matches NEITHER is a genuine MISMATCH and reports both values —
 *                        which is how the real out-of-window errors stay caught (BTC low
 *                        $52,550 vs $57,717.55 intraday; ETH low $1,385 vs $1,505.00;
 *                        SOL high $295.83 vs $253.61 — all stated from OUTSIDE the 52w
 *                        window). When no intraday source exists for a token the result
 *                        is labelled `close-only, intraday unverified`, never silently
 *                        treated as authoritative.
 *
 * Price sources: Coinbase Exchange daily candles (PRIMARY — carries true intraday
 * low/high) with CoinGecko daily closes as the close-basis series and the fallback.
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

/** One daily candle carrying TRUE intraday extremes (Coinbase Exchange). */
export type CandlePoint = { t: number; l: number; h: number; c: number };

export type SeriesOk = {
  ok: true;
  /** Daily closes, oldest-first. Must be >= MIN_SERIES_POINTS or RULE 3 fails. */
  points: SeriesPoint[];
  /** All-time high in USD. Absent => any ATH-basis claim is [UNAVAILABLE] (loud). */
  ath?: number;
  /**
   * Daily candles with intraday low/high, oldest-first. PRIMARY yardstick: reports
   * quote intraday extremes (TradingView/exchange candles), so validating them
   * against a close-only series produces systematic FALSE POSITIVES.
   * Absent => intraday could not be verified; every result derived from closes alone
   * is labelled `close-only, intraday unverified` (repo invariant #4: honest degradation).
   */
  candles?: CandlePoint[];
  /** Why intraday data is missing, when it is. Surfaced in the result detail. */
  intradayError?: string;
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
  /**
   * Set when the line names MORE THAN ONE known token, so no single attribution is
   * defensible. An explicit AMBIGUOUS_TOKEN failure beats a confident wrong PASS.
   */
  ambiguousTokens?: string[];
};

export type Status =
  | "OK"
  | "BASIS_MISSING"
  | "MISMATCH"
  | "FETCH_FAILED"
  | "SHORT_SERIES"
  | "ATH_UNAVAILABLE"
  | "AMBIGUOUS_TOKEN"
  | "NO_TOKEN";

/**
 * Which price convention actually backed an OK verdict.
 *   "intraday"  — matched the true intraday extreme (candle low/high). Authoritative.
 *   "close"     — matched the daily-close extreme, intraday data WAS available and
 *                 disagreed; the claim is close-basis.
 *   "close-only"— no usable intraday data; the claim is UNVERIFIED against intraday.
 */
export type Verification = "intraday" | "close" | "close-only";

export type ClaimResult = {
  claim: Claim;
  status: Status;
  /** The value that matched (or, on MISMATCH, the intraday-basis recompute). */
  recomputed?: number;
  /** Intraday-basis recompute, when intraday data was available. */
  recomputedIntraday?: number;
  /** Close-basis recompute. Always present once a series was fetched. */
  recomputedClose?: number;
  verification?: Verification;
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

/**
 * Report symbol → Coinbase Exchange product id. This is the INTRADAY source: its daily
 * candles carry true session low/high, which is the convention reports actually quote.
 * A symbol absent from this map degrades to close-only (labelled), never silent.
 */
export const COINBASE_PRODUCTS: Readonly<Record<string, string>> = {
  BTC: "BTC-USD",
  ETH: "ETH-USD",
  SOL: "SOL-USD",
  TON: "TON-USD",
  HYPE: "HYPE-USD",
  AAVE: "AAVE-USD",
  JUP: "JUP-USD",
  UNI: "UNI-USD",
  AERO: "AERO-USD",
  PUMP: "PUMP-USD",
  LINK: "LINK-USD",
};

/** Unicode minus (U+2212), ASCII hyphen, en-dash — all appear in real reports. */
const MINUS = "[−\\-–]";
/**
 * A USD/percent numeric token, with or without thousands separators, with or without
 * a decimal tail. BOTH must compose: the old `\d+(?:[.,]\d+)?` matched `126,200` and
 * `1505.00` but NOT `1,505.00` — on `$1,505.00` it stopped after `1,505`, so RE_RANGE
 * never saw the `↔` and the entire range claim was DROPPED WITH NO WARNING (a claim
 * that is not extracted is silently trusted — the worst failure mode of this tool).
 *
 * The grouped form is tried first but REQUIRES at least one comma group, so a plain
 * `4956.78` cannot be mis-split into `495`; it falls through to the plain alternative.
 */
const NUM = "\\d{1,3}(?:,\\d{3})+(?:\\.\\d+)?|\\d+(?:\\.\\d+)?";

/**
 * Markdown emphasis / code-span delimiters that may sit BETWEEN the tokens of a claim.
 *
 * WHY: `**−62.8%** from its 52w high` bolds only the NUMBER, so a `**` lands between the
 * `%` and the word `from`. The old prose regex demanded `%\s+(?:from|off|…)`, so that
 * closing `**` killed the match and the claim was NEVER EXTRACTED — which means it was
 * silently TRUSTED. Live in the shipped report, including a bare `(**−61.0%** from high)`
 * that RULE 1 must reject; the gate instead announced "all 66 passed".
 * Every existing test bolded the WHOLE phrase (`**−62.8% from 52w high**`), which leaves
 * no delimiter mid-claim — which is exactly why this survived review.
 */
const EMPH = "[*_`]*";
/** One-or-more separator run: whitespace and/or emphasis delimiters, in any order. */
const SEP = "[*_`\\s]+";

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

const RE_HEADING_TOKEN = new RegExp(
  `^#{1,6}\\s*(?:\\d+\\.\\s*)?${EMPH}\\s*([A-Z]{2,6})\\s*${EMPH}\\s*[—–-]`,
);
/**
 * A ticker occupying a WHOLE table cell, in ANY column — not just the first.
 *
 * WHY not first-cell-only: the report's own signal table is `| 1 | **BTC** | … |` (an
 * index column), and peer-comparison rows put the ticker mid-row too. With a first-cell
 * anchor those rows never re-attributed, so `sectionSymbol` leaked and a LINK claim
 * sitting inside the SOL section was recomputed against SOL's series and stamped OK
 * (−70.8% vs −70.5%, inside tolerance) — a CONFIDENT WRONG PASS, the worst outcome here.
 */
const RE_CELL_TOKEN = new RegExp(`\\|\\s*${EMPH}\\s*([A-Z]{2,6})\\s*${EMPH}\\s*(?=\\|)`, "g");
/**
 * A ticker as a standalone word, for PROSE lines (no table cells). Same purpose as
 * RE_CELL_TOKEN: a claim on a line about LINK must never be recomputed against the
 * enclosing section's SOL series.
 */
const RE_WORD_TOKEN = /\b([A-Z]{2,6})\b/g;

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
 * Every inter-token gap accepts markdown emphasis (`**`, `*`, `_`, backtick) as well as
 * whitespace, because bolding ONLY the number (`**−61.0%** from high`) is common in real
 * reports and used to make the whole claim invisible. See EMPH/SEP above.
 */
const RE_PROSE_PCT = new RegExp(
  `(${MINUS})?\\s*${EMPH}\\s*(${NUM})\\s*${EMPH}\\s*%${SEP}(?:from|off|below|under)${SEP}` +
    `((?:its|the|their|true|standard|current|prior|recent|a)${SEP})*([^%.,;:)\\n]{0,28}?)(highs?|ath)\\b`,
  "gi",
);

/**
 * `| 52w Low | $52,550 |`, `| 52w High | $126,200 ... |`,
 * `| 52w Low (intraday) | $57,717.55 |`, `| ATH (corrected) — RESOLVED | $8.25 |`
 *
 * The label cell must still NAME a 52w/365d/ATH level, but a trailing qualifier
 * (`(intraday)`, `(close)`, `(corrected)`, `(intraday, 3-venue)`, `— RESOLVED …`) is
 * tolerated: previously `| 52w Low (intraday) |` made the whole row INVISIBLE, so the
 * claim was never checked and silently trusted.
 */
const RE_TABLE_LEVEL = new RegExp(
  `\\|\\s*\\*{0,2}\\s*(52\\s*-?\\s*w(?:eek)?|365\\s*-?\\s*d|ath|all\\s*-?\\s*time)\\s*(low|high)?[^|]*\\|\\s*\\*{0,2}\\s*\\$(${NUM})`,
  "gi",
);

/**
 * `| 52w Range | $1,385 ↔ $4,957 |`, prose `52w range $7.19–$26.73`,
 * `| 52w Range (intraday) | **$1,505.00 ↔ $4,956.78** — … |`
 * The gap allowance between `range` and the first `$` is wide enough for a
 * parenthetical qualifier plus the cell boundary and bold markers.
 */
const RE_RANGE = new RegExp(
  `(52\\s*-?\\s*w(?:eek)?|365\\s*-?\\s*d)\\s*range[^$\\n]{0,48}\\$\\*{0,2}(${NUM})\\*{0,2}\\s*(?:↔|–|—|-|to)\\s*\\*{0,2}\\$?(${NUM})`,
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
    // A row/line naming a token re-attributes ONLY that line, not the section. The token
    // may sit in any column (`| 1 | **BTC** | …`), not just the first. Table cells win
    // over a bare word match, because a cell IS the row's subject.
    const cellTokens = [
      ...new Set(
        [...line.matchAll(RE_CELL_TOKEN)].map((m) => m[1]!).filter((t) => COINGECKO_IDS[t]),
      ),
    ];
    const lineTokens = cellTokens.length
      ? cellTokens
      : [...new Set([...line.matchAll(RE_WORD_TOKEN)].map((m) => m[1]!).filter((t) => COINGECKO_IDS[t]))];
    // Two different tokens on one line => no defensible attribution. Refuse, loudly:
    // an explicit AMBIGUOUS_TOKEN failure is far better than a confident wrong PASS.
    const ambiguousTokens = lineTokens.length > 1 ? lineTokens : undefined;
    const symbol = ambiguousTokens ? null : (lineTokens[0] ?? sectionSymbol);

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
        ...(ambiguousTokens ? { ambiguousTokens } : {}),
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
      // Claim ONLY the `(−49.4%)` parenthetical, not the whole row. Claiming the full
      // span made this drawdown swallow the PRICE LEVEL in the same row (`$126,296`),
      // so the level was never extracted and therefore never checked — the same
      // silent-trust failure, one layer down.
      const parenRel = m[0].lastIndexOf("(");
      push(idx + (parenRel === -1 ? 0 : parenRel), idx + m[0].length, "drawdown", basis, -Math.abs(num(m[3]!)));
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
      // overlap each other (an overlap would silently drop one of them). The separator
      // is searched AFTER the first `$` so a hyphen in the label ("52-week Range") or
      // in a qualifier cannot be mistaken for the range separator and skew the split.
      const dollarRel = m[0].indexOf("$");
      const sepRel = dollarRel === -1
        ? m[0].search(/↔|–|—|-|\bto\b/)
        : (() => {
            const r = m[0].slice(dollarRel + 1).search(/↔|–|—|-|\bto\b/);
            return r === -1 ? -1 : dollarRel + 1 + r;
          })();
      const mid = sepRel === -1 ? idx + Math.floor(m[0].length / 2) : idx + sepRel;
      const basis = resolveBasis(m[1]!);
      push(idx, mid, lo <= hi ? "low" : "high", basis, lo);
      push(mid, end, lo <= hi ? "high" : "low", basis, hi);
    }
    for (const m of line.matchAll(RE_TABLE_LEVEL)) {
      const idx = m.index ?? 0;
      const basis = resolveBasis(m[1]!);
      let which = (m[2] ?? "").toLowerCase();
      if (which !== "low" && which !== "high") {
        // `| ATH | $8.25 |` names no low/high word, yet an ATH *is* a high. The old code
        // `continue`d here, so the report's TON ATH $8.25 and HYPE ATH $76.87 were never
        // extracted and therefore silently trusted — the same silent-trust failure mode.
        // A bare `| 52w | $x |` stays skipped: without low/high it is genuinely ambiguous.
        if (basis !== "ATH") continue;
        which = "high";
      }
      push(idx, idx + m[0].length, which as ClaimKind, basis, num(m[3]!));
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

/** True intraday extremes from daily candles. */
export function candleHigh(candles: CandlePoint[]): number {
  return Math.max(...candles.map((p) => p.h));
}
export function candleLow(candles: CandlePoint[]): number {
  return Math.min(...candles.map((p) => p.l));
}

/**
 * Returns the usable intraday candles for a series, or undefined with the reason.
 * A short candle window is NOT usable — a truncated intraday series would understate
 * the true 52w extreme and turn a genuine out-of-window error into a false PASS.
 */
function usableCandles(
  s: SeriesOk,
  minPoints: number,
): { candles?: CandlePoint[]; reason?: string } {
  if (!s.candles || s.candles.length === 0) {
    return { reason: s.intradayError ?? "no intraday source for this token" };
  }
  if (s.candles.length < minPoints) {
    return {
      reason: `intraday series has ${s.candles.length} candles, need >= ${minPoints}`,
    };
  }
  return { candles: s.candles };
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
    if (claim.ambiguousTokens) {
      results.push({
        claim,
        status: "AMBIGUOUS_TOKEN",
        detail:
          `[UNAVAILABLE] this line names ${claim.ambiguousTokens.join(" and ")} — refusing to ` +
          `attribute the claim to one of them. Recomputing it against the wrong token's series ` +
          `produces a CONFIDENT WRONG PASS; split the line or name the token explicitly.`,
      });
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

    const intraday = usableCandles(s, minPoints);
    const unverifiedNote = intraday.reason
      ? ` [close-only, intraday unverified: ${intraday.reason}]`
      : "";

    if (claim.kind === "drawdown") {
      // ATH basis has a single scalar peak — there is no close-vs-intraday choice.
      if (claim.basis === "ATH") {
        if (typeof s.ath !== "number" || !(s.ath > 0)) {
          results.push({
            claim,
            status: "ATH_UNAVAILABLE",
            detail: `[UNAVAILABLE] no ATH for ${claim.symbol} — cannot verify an ATH-basis drawdown`,
          });
          continue;
        }
        const rec = drawdownFrom(s.points, s.ath);
        const d = Math.abs(rec - claim.value);
        results.push(
          d <= tolerance
            ? { claim, status: "OK", recomputed: rec, detail: `OK[ATH] stated ${claim.value.toFixed(1)}% vs recomputed ${rec.toFixed(1)}% (Δ${d.toFixed(2)}pp)` }
            : { claim, status: "MISMATCH", recomputed: rec, detail: `stated ${claim.value.toFixed(1)}% vs recomputed ${rec.toFixed(1)}% (Δ${d.toFixed(2)}pp > ${tolerance}pp)` },
        );
        continue;
      }

      // 52w basis: the peak differs by convention, so recompute BOTH and pass on either.
      const ddClose = drawdownFrom(s.points, seriesHigh(s.points));
      const ddIntra = intraday.candles
        ? drawdownFrom(s.points, candleHigh(intraday.candles))
        : undefined;
      const dClose = Math.abs(ddClose - claim.value);
      const dIntra = ddIntra === undefined ? Infinity : Math.abs(ddIntra - claim.value);

      if (dIntra <= tolerance) {
        results.push({
          claim, status: "OK", recomputed: ddIntra, recomputedIntraday: ddIntra,
          recomputedClose: ddClose, verification: "intraday",
          detail: `OK[intraday] stated ${claim.value.toFixed(1)}% vs intraday-basis ${ddIntra!.toFixed(1)}% (Δ${dIntra.toFixed(2)}pp)`,
        });
      } else if (dClose <= tolerance) {
        results.push({
          claim, status: "OK", recomputed: ddClose, recomputedIntraday: ddIntra,
          recomputedClose: ddClose,
          verification: intraday.candles ? "close" : "close-only",
          detail: intraday.candles
            ? `OK[close] stated ${claim.value.toFixed(1)}% vs close-basis ${ddClose.toFixed(1)}% (Δ${dClose.toFixed(2)}pp); intraday-basis is ${ddIntra!.toFixed(1)}%`
            : `OK[close-only, intraday unverified] stated ${claim.value.toFixed(1)}% vs close-basis ${ddClose.toFixed(1)}% (Δ${dClose.toFixed(2)}pp)${unverifiedNote}`,
        });
      } else {
        results.push({
          claim, status: "MISMATCH",
          recomputed: ddIntra ?? ddClose, recomputedIntraday: ddIntra, recomputedClose: ddClose,
          detail:
            `stated ${claim.value.toFixed(1)}% matches NEITHER convention — ` +
            `intraday-basis ${ddIntra === undefined ? "[UNAVAILABLE]" : `${ddIntra.toFixed(1)}% (Δ${dIntra.toFixed(2)}pp)`}, ` +
            `close-basis ${ddClose.toFixed(1)}% (Δ${dClose.toFixed(2)}pp); tolerance ${tolerance}pp${unverifiedNote}`,
        });
      }
      continue;
    }

    // Price levels (52w low / 52w high) — same like-for-like rule.
    //
    // ATH-basis levels FIRST: `claim.basis` was honoured for drawdowns but IGNORED here,
    // so `| All-Time High | $8.25 |` was silently checked against the 52-WEEK high. A
    // fixture with a 52w high of 8.25 and a true ATH of 100 PASSED — off by 12×. `s.ath`
    // was fetched and never read. There is no close/intraday distinction for a scalar ATH.
    if (claim.basis === "ATH" && claim.kind === "high") {
      if (typeof s.ath !== "number" || !(s.ath > 0)) {
        results.push({
          claim,
          status: "ATH_UNAVAILABLE",
          detail: `[UNAVAILABLE] no ATH for ${claim.symbol} — cannot verify an ATH-basis level (never fall back to the 52w series)`,
        });
        continue;
      }
      const rel = (Math.abs(s.ath - claim.value) / s.ath) * 100;
      results.push(
        rel <= priceTol
          ? { claim, status: "OK", recomputed: s.ath, detail: `OK[ATH] stated $${claim.value} vs ATH $${s.ath.toPrecision(6)} (${rel.toFixed(2)}%)` }
          : { claim, status: "MISMATCH", recomputed: s.ath, detail: `stated $${claim.value} vs ATH $${s.ath.toPrecision(6)} (${rel.toFixed(2)}% > ${priceTol}%)` },
      );
      continue;
    }

    const lvlClose = claim.kind === "low" ? seriesLow(s.points) : seriesHigh(s.points);
    const lvlIntra = intraday.candles
      ? (claim.kind === "low" ? candleLow(intraday.candles) : candleHigh(intraday.candles))
      : undefined;
    const relClose = Math.abs(lvlClose - claim.value) / lvlClose * 100;
    const relIntra = lvlIntra === undefined ? Infinity : Math.abs(lvlIntra - claim.value) / lvlIntra * 100;

    if (relIntra <= priceTol) {
      results.push({
        claim, status: "OK", recomputed: lvlIntra, recomputedIntraday: lvlIntra,
        recomputedClose: lvlClose, verification: "intraday",
        detail: `OK[intraday] stated $${claim.value} vs intraday ${claim.kind} $${lvlIntra!.toPrecision(6)} (${relIntra.toFixed(2)}%)`,
      });
    } else if (relClose <= priceTol) {
      results.push({
        claim, status: "OK", recomputed: lvlClose, recomputedIntraday: lvlIntra,
        recomputedClose: lvlClose,
        verification: intraday.candles ? "close" : "close-only",
        detail: intraday.candles
          ? `OK[close] stated $${claim.value} vs close ${claim.kind} $${lvlClose.toPrecision(6)} (${relClose.toFixed(2)}%); intraday ${claim.kind} is $${lvlIntra!.toPrecision(6)}`
          : `OK[close-only, intraday unverified] stated $${claim.value} vs close ${claim.kind} $${lvlClose.toPrecision(6)} (${relClose.toFixed(2)}%)${unverifiedNote}`,
      });
    } else {
      results.push({
        claim, status: "MISMATCH",
        recomputed: lvlIntra ?? lvlClose, recomputedIntraday: lvlIntra, recomputedClose: lvlClose,
        detail:
          `stated $${claim.value} matches NEITHER convention — ` +
          `intraday ${claim.kind} ${lvlIntra === undefined ? "[UNAVAILABLE]" : `$${lvlIntra.toPrecision(6)} (${relIntra.toFixed(2)}%)`}, ` +
          `close ${claim.kind} $${lvlClose.toPrecision(6)} (${relClose.toFixed(2)}%); tolerance ${priceTol}%${unverifiedNote}`,
      });
    }
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

/**
 * The PRODUCTION fetcher: Coinbase daily candles (intraday extremes) layered onto the
 * CoinGecko close series. Coinbase failing is NOT fatal — the close series still
 * validates — but the failure reason is carried through so every affected result is
 * labelled `close-only, intraday unverified` instead of silently passing as verified.
 */
export function productionFetcher(
  closes: SeriesFetcher = coingeckoFetcher(),
  products: Record<string, string> = COINBASE_PRODUCTS,
  candles: (product: string) => Promise<CandlePoint[]> = fetchCoinbaseCandles,
): SeriesFetcher {
  return async (symbol: string): Promise<SeriesResult> => {
    const base = await closes(symbol);
    if (!base.ok) return base;

    const product = products[symbol];
    if (!product) {
      return { ...base, intradayError: `no Coinbase product mapped for symbol ${symbol}` };
    }
    try {
      const rows = await candles(product);
      if (rows.length === 0) {
        // The product exists but Coinbase served no candles (delisted / never traded
        // over this window). Loud + specific, so nobody reads it as "verified".
        return { ...base, intradayError: `Coinbase returned 0 candles for ${product}` };
      }
      return { ...base, candles: rows };
    } catch (e) {
      return {
        ...base,
        intradayError: `Coinbase candles for ${product}: ${e instanceof Error ? e.message : String(e)}`,
      };
    }
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Coinbase Exchange fetcher (the INTRADAY yardstick)
// ─────────────────────────────────────────────────────────────────────────────

const CB = "https://api.exchange.coinbase.com";

/** Coinbase caps a candles response at ~300 rows, so 365 days needs two windows. */
const CB_MAX_CANDLES_PER_REQ = 300;

/** Fetches one window of daily candles. Rows are `[time, low, high, open, close, volume]`. */
async function coinbaseWindow(product: string, startMs: number, endMs: number): Promise<CandlePoint[]> {
  const url =
    `${CB}/products/${product}/candles?granularity=86400` +
    `&start=${new Date(startMs).toISOString()}&end=${new Date(endMs).toISOString()}`;
  const r = await fetch(url, { headers: { accept: "application/json", "user-agent": "drawdown-basis-validator" } });
  if (!r.ok) throw new Error(`HTTP ${r.status} ${r.statusText} for ${product}`);
  const rows = (await r.json()) as unknown;
  if (!Array.isArray(rows)) throw new Error(`unexpected candles payload for ${product}`);
  return (rows as number[][]).map((row) => ({
    t: row[0]! * 1000,
    l: row[1]!,
    h: row[2]!,
    c: row[4]!,
  }));
}

/**
 * 365 days of daily candles with TRUE intraday low/high, paged over two windows to
 * stay under Coinbase's ~300-candle response cap (verified: n=367 this way).
 */
export async function fetchCoinbaseCandles(
  product: string,
  now: number = Date.now(),
): Promise<CandlePoint[]> {
  const DAY_MS = 86_400_000;
  const start = now - 366 * DAY_MS;
  const split = start + CB_MAX_CANDLES_PER_REQ * DAY_MS - DAY_MS;
  const [a, b] = await Promise.all([
    coinbaseWindow(product, start, split),
    coinbaseWindow(product, split, now),
  ]);
  const byTime = new Map<number, CandlePoint>();
  for (const c of [...a, ...b]) byTime.set(c.t, c);
  return [...byTime.values()].sort((x, y) => x.t - y.t);
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
  AMBIGUOUS_TOKEN: "✗",
  NO_TOKEN: "✗",
};

/** Display label: an OK verdict must SAY which price convention backed it. */
export function statusLabel(r: ClaimResult): string {
  if (r.status !== "OK") return r.status;
  if (r.verification === "intraday") return "OK[intraday]";
  if (r.verification === "close") return "OK[close]";
  if (r.verification === "close-only") return "OK[close-only]";
  return "OK";
}

export function formatReport(rep: ValidationReport, path: string): string {
  const out: string[] = [`drawdown-basis validation — ${path}`, ""];
  for (const r of rep.results) {
    const sym = r.claim.symbol ?? "?";
    out.push(
      `${ICON[r.status]} ${statusLabel(r).padEnd(15)} L${String(r.claim.line).padStart(4)} ` +
        `${sym.padEnd(5)} [${r.claim.basis}] ${r.claim.kind}  «${r.claim.raw.slice(0, 72)}»`,
    );
    if (r.status !== "OK" || r.verification === "close-only") out.push(`    → ${r.detail}`);
  }
  out.push("");
  const unverified = rep.results.filter((r) => r.status === "OK" && r.verification === "close-only").length;
  out.push(
    rep.ok
      ? `✓ all ${rep.results.length} claim(s) passed`
      : `✗ ${rep.failures.length} of ${rep.results.length} claim(s) FAILED`,
  );
  if (unverified > 0) {
    out.push(`⚠ ${unverified} claim(s) passed on CLOSE data only — intraday unverified`);
  }
  return out.join("\n");
}

/** Flags that consume the NEXT argv entry as their value. */
const VALUE_FLAGS = new Set(["tolerance", "price-tolerance-pct"]);

export type ParsedArgs = {
  files: string[];
  flags: Record<string, string | true>;
};

/**
 * Splits argv into positional files and flags.
 *
 * WHY not `argv.filter(a => !a.startsWith("--"))`: that treats a flag's VALUE as a
 * filename, so the documented `REPORT.md --tolerance 0.5` produced files=["REPORT.md",
 * "0.5"], failed the `length !== 1` check and exited 2. Both documented tuning flags were
 * therefore unusable — the tool could only ever run at its defaults.
 * `--name=value` is accepted too.
 */
export function parseArgs(argv: string[]): ParsedArgs {
  const files: string[] = [];
  const flags: Record<string, string | true> = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]!;
    if (!a.startsWith("--")) {
      files.push(a);
      continue;
    }
    const body = a.slice(2);
    const eq = body.indexOf("=");
    if (eq !== -1) {
      flags[body.slice(0, eq)] = body.slice(eq + 1);
      continue;
    }
    if (VALUE_FLAGS.has(body)) {
      const v = argv[i + 1];
      if (v === undefined || v.startsWith("--")) {
        flags[body] = true; // missing value → surfaced as NaN below, never silently default
      } else {
        flags[body] = v;
        i++; // consume the value so it is NOT mistaken for a filename
      }
      continue;
    }
    flags[body] = true;
  }
  return { files, flags };
}

async function main(argv: string[]): Promise<number> {
  const { files, flags } = parseArgs(argv);
  const numFlag = (name: string): number | undefined => {
    const v = flags[name];
    if (v === undefined) return undefined;
    if (v === true) throw new Error(`--${name} requires a numeric value`);
    const n = Number(v);
    if (!Number.isFinite(n)) throw new Error(`--${name} must be numeric, got "${v}"`);
    return n;
  };
  if (files.length !== 1) {
    console.error("usage: bun drawdown_basis.ts <report.md> [--tolerance 0.5] [--price-tolerance-pct 1.0] [--basis-only] [--json]");
    return 2;
  }
  const path = files[0]!;
  const md = await Bun.file(path).text();

  const basisOnly = flags["basis-only"] === true;
  let tolerance: number | undefined;
  let priceTolerancePct: number | undefined;
  try {
    tolerance = numFlag("tolerance");
    priceTolerancePct = numFlag("price-tolerance-pct");
  } catch (e) {
    console.error(e instanceof Error ? e.message : String(e));
    return 2;
  }

  const rep = await validateReport(md, {
    fetcher: basisOnly ? undefined : productionFetcher(),
    basisOnly,
    tolerance,
    priceTolerancePct,
  });

  console.log(flags["json"] === true ? JSON.stringify(rep, null, 2) : formatReport(rep, path));
  return rep.ok ? 0 : 1;
}

if (import.meta.main) {
  process.exit(await main(process.argv.slice(2)));
}
