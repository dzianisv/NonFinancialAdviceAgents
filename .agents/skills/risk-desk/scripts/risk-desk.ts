#!/usr/bin/env bun
/**
 * risk-desk.ts
 *
 * The ALWAYS-ON risk layer, modeled on Citadel/Millennium central-risk-desk
 * mechanics. Runs deterministic risk rules over HELD positions -- independent
 * of any alpha/picker view (stocks-advisor's scorecard.py decide()). Risk
 * overrides alpha: a stock the picker calls WAIT ("cheap, don't add") can
 * still be a TRIM from here if it's oversized, trending down, or a winner
 * rolling over.
 *
 * Origin story: NEM was 8.3% of book, +112% unrealized gain, and had broken
 * below its 200d MA for weeks. scorecard.py's decide() correctly scored it
 * WAIT under the picker's val/trend logic ("cheap, downtrending -- don't
 * catch the knife") -- a fine answer to "should I buy more?" and a useless
 * one to "should I still hold this much?". Nothing ever asked the second
 * question. risk-desk asks only the second question, continuously.
 *
 * Conventions mirrored from watchlist-alerts.ts (Yahoo v8 chart fetch w/
 * User-Agent, Wilder RSI, gws sheet read/write via batchUpdate + numeric
 * gridRange, dry-run-by-default CLI style). A small amount of duplication
 * vs watchlist-alerts.ts is intentional -- this script does not import from
 * or modify it.
 *
 * Usage:
 *   bun risk-desk.ts [--positions <csv>] [--arm] [--json]
 *
 *   --positions <csv>  Defaults to the newest
 *                       .cache/stocks-daily/positions_live_*.csv, falling
 *                       back to .cache/stocks-daily/positions.csv.
 *   --arm              Upsert ACTIVE rows into the Watchlist sheet for
 *                       R1/R2/R4 breaches (report-only without this flag).
 *   --json              Also print a machine-readable JSON summary.
 *
 * Requires the `gws` CLI on PATH (only touched when --arm is passed).
 */

import { readdirSync, existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

const SPREADSHEET_ID = "1aunLbpNGo85WqrMHiIsy6nFUija4Lnjot-rIhE-pGU8";
const SHEET_TAB = "Watchlist";

const YAHOO_USER_AGENT =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36 risk-desk.ts/1.0";

const POSITIONS_DIR = ".cache/stocks-daily";
const POSITIONS_LIVE_RE = /^positions_live_(\d{4}-\d{2}-\d{2})\.csv$/;
const POSITIONS_FALLBACK = "positions.csv";

// Yahoo ticker remapping for symbols whose broker/portfolio ticker differs
// from Yahoo's chart symbol.
const SYMBOL_MAP: Record<string, string> = {
  "BRK.B": "BRK-B",
  BTC: "BTC-USD",
};

// Rows that are book value but not fetchable market instruments. Matched
// against the Position name (case-insensitive) or a Type column if present.
const NON_EQUITY_RE = /^(cash|cash holdings|t-?bills?|money\s*market|sweep)$/i;

// Crypto-beta names the user has an explicit standing mandate to hold
// through drawdowns -- risk-desk still reports breaches on them (never
// silently suppresses risk), it just tags the directive as a tripwire
// instead of an instruction to trim.
const HOLD_ONLY = new Set(["COIN", "TONX"]);

// Static correlation sleeves for R5 (portfolio-level concentration by theme,
// not just by single name).
const CLUSTERS: Record<string, string[]> = {
  gold: ["NEM", "GDX", "PHYS", "GLD", "PSLV"],
  crypto_beta: ["COIN", "TONX", "CRCL", "HOOD", "BTC"],
  ai_semis: ["MRVL", "AVGO", "QCOM", "TSM", "MU", "SNDK", "INTC", "AMD", "ASML", "NVDA"],
};

const CLUSTER_BREACH_PCT = 12;
const MANDATE_CLAMP_TAG = "[MANDATE-CLAMPED — surfaced, not auto-trimmed; tripwire]";

// ---------------------------------------------------------------------------
// CLI args
// ---------------------------------------------------------------------------

interface CliArgs {
  positions: string | null;
  arm: boolean;
  json: boolean;
}

function parseArgs(argv: string[]): CliArgs {
  let positions: string | null = null;
  let arm = false;
  let json = false;
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--positions") {
      positions = argv[i + 1] ?? null;
      i++;
    } else if (a.startsWith("--positions=")) {
      positions = a.slice("--positions=".length);
    } else if (a === "--arm") {
      arm = true;
    } else if (a === "--json") {
      json = true;
    }
  }
  return { positions, arm, json };
}

// ---------------------------------------------------------------------------
// Positions CSV
// ---------------------------------------------------------------------------

interface PositionRow {
  symbol: string; // as written in the CSV (e.g. "BRK.B")
  yahooSymbol: string; // remapped for market data fetch
  mv: number;
  pnl: number | null; // null = missing/unreliable
  weightPct: number; // % of total book MV (all rows, incl. non-equity)
  isEquityLike: boolean;
}

function resolvePositionsFile(explicit: string | null): string {
  if (explicit) {
    if (!existsSync(explicit)) throw new Error(`--positions file not found: ${explicit}`);
    return explicit;
  }
  if (existsSync(POSITIONS_DIR)) {
    const candidates = readdirSync(POSITIONS_DIR)
      .map((f) => {
        const m = f.match(POSITIONS_LIVE_RE);
        return m ? { file: join(POSITIONS_DIR, f), date: m[1] } : null;
      })
      .filter((x): x is { file: string; date: string } => x !== null)
      .sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0));
    if (candidates.length > 0) return candidates[0].file;
  }
  const fallback = join(POSITIONS_DIR, POSITIONS_FALLBACK);
  if (existsSync(fallback)) return fallback;
  throw new Error(
    `No positions_live_*.csv found under ${POSITIONS_DIR}/ and no fallback ${fallback}`,
  );
}

/** Minimal CSV line splitter -- handles quoted fields with embedded commas. */
function splitCsvLine(line: string): string[] {
  const out: string[] = [];
  let cur = "";
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (inQuotes) {
      if (c === '"' && line[i + 1] === '"') {
        cur += '"';
        i++;
      } else if (c === '"') {
        inQuotes = false;
      } else {
        cur += c;
      }
    } else if (c === '"') {
      inQuotes = true;
    } else if (c === ",") {
      out.push(cur);
      cur = "";
    } else {
      cur += c;
    }
  }
  out.push(cur);
  return out;
}

function parseNum(s: string | undefined): number | null {
  if (s === undefined) return null;
  const cleaned = s.replace(/,/g, "").replace(/\$/g, "").trim();
  if (cleaned === "") return null;
  const n = Number(cleaned);
  return Number.isFinite(n) ? n : null;
}

interface LoadedPositions {
  rows: PositionRow[];
  totalMV: number;
  skippedNonEquity: string[];
  skippedNoMV: string[];
}

function loadPositions(path: string): LoadedPositions {
  const text = readFileSync(path, "utf8");
  const lines = text.split(/\r?\n/).filter((l) => l.trim() !== "");
  if (lines.length === 0) throw new Error(`${path} is empty`);
  const hdr = splitCsvLine(lines[0]).map((h) => h.trim().toLowerCase());
  const idx = (...names: string[]) => {
    for (const n of names) {
      const i = hdr.indexOf(n);
      if (i !== -1) return i;
    }
    return -1;
  };
  const posI = idx("position", "ticker", "symbol");
  const mvI = idx("marketvalue", "market_value", "mv");
  const pnlI = idx("unrealized_pnl", "pnl", "unrealized");
  const typeI = idx("type");
  if (posI === -1) throw new Error(`${path}: no Position/Ticker/Symbol column found`);

  interface Raw {
    symbol: string;
    mv: number | null;
    pnl: number | null;
    type: string;
  }
  const raws: Raw[] = [];
  for (let i = 1; i < lines.length; i++) {
    const cells = splitCsvLine(lines[i]);
    const symbol = (cells[posI] ?? "").trim();
    if (!symbol) continue;
    raws.push({
      symbol,
      mv: mvI !== -1 ? parseNum(cells[mvI]) : null,
      pnl: pnlI !== -1 ? parseNum(cells[pnlI]) : null,
      type: typeI !== -1 ? (cells[typeI] ?? "").trim() : "",
    });
  }

  // Total book MV = every row with a usable MV, equity or not -- weight% is
  // "share of the book", and cash/T-bills are part of the book.
  const totalMV = raws.reduce((sum, r) => sum + (r.mv && Number.isFinite(r.mv) ? r.mv : 0), 0);

  const rows: PositionRow[] = [];
  const skippedNonEquity: string[] = [];
  const skippedNoMV: string[] = [];

  for (const r of raws) {
    const nonEquity = NON_EQUITY_RE.test(r.symbol) || NON_EQUITY_RE.test(r.type);
    if (r.mv === null) {
      skippedNoMV.push(r.symbol);
      continue;
    }
    if (nonEquity) {
      skippedNonEquity.push(r.symbol);
      continue;
    }
    const weightPct = totalMV > 0 ? (100 * r.mv) / totalMV : 0;
    rows.push({
      symbol: r.symbol,
      yahooSymbol: SYMBOL_MAP[r.symbol] ?? r.symbol,
      mv: r.mv,
      pnl: r.pnl,
      weightPct,
      isEquityLike: true,
    });
  }

  return { rows, totalMV, skippedNonEquity, skippedNoMV };
}

/**
 * gain% = PnL / costBasis * 100, costBasis = MV - PnL.
 * A PnL of exactly 0 is treated as "unknown/not tracked" (many rows in the
 * live snapshot carry a hard 0 because the source hasn't been reconciled
 * for that lot) rather than a genuine 0% gain -- reporting a false "flat"
 * gain would silently suppress R2/R4 on real winners. Guards divide-by-zero
 * and a degenerate/negative cost basis the same way.
 */
function computeGainPct(mv: number, pnl: number | null): number | null {
  if (pnl === null || pnl === 0) return null;
  const costBasis = mv - pnl;
  if (!Number.isFinite(costBasis) || costBasis <= 0) return null;
  return (pnl / costBasis) * 100;
}

// ---------------------------------------------------------------------------
// Market data (Yahoo v8 chart) -- same fetch shape as watchlist-alerts.ts,
// extended with SMA200.
// ---------------------------------------------------------------------------

interface Quote {
  symbol: string;
  price: number;
  ma200: number | null;
  high52: number;
  rsi14: number;
  closesCount: number;
  asOf: string;
}

const quoteCache = new Map<string, Quote>();
const quoteErrors = new Map<string, string>();

async function fetchYahooChart(symbol: string): Promise<Quote> {
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(
    symbol,
  )}?interval=1d&range=1y`;
  const resp = await fetch(url, { headers: { "User-Agent": YAHOO_USER_AGENT } });
  if (!resp.ok) throw new Error(`HTTP ${resp.status} ${resp.statusText}`);
  const json = await resp.json();
  const result = json?.chart?.result?.[0];
  if (!result) {
    const err = json?.chart?.error;
    throw new Error(err ? `Yahoo error: ${JSON.stringify(err)}` : "no chart result");
  }
  const timestamps: number[] = result.timestamp ?? [];
  const closesRaw: (number | null)[] = result.indicators?.quote?.[0]?.close ?? [];
  const highsRaw: (number | null)[] = result.indicators?.quote?.[0]?.high ?? [];

  const closes: number[] = [];
  let lastTs = 0;
  for (let i = 0; i < closesRaw.length; i++) {
    const c = closesRaw[i];
    if (c === null || c === undefined || Number.isNaN(c)) continue;
    closes.push(c);
    lastTs = timestamps[i] ?? lastTs;
  }
  if (closes.length === 0) throw new Error("no usable close prices returned");

  let high52 = -Infinity;
  for (const h of highsRaw) {
    if (h === null || h === undefined || Number.isNaN(h)) continue;
    if (h > high52) high52 = h;
  }
  if (!Number.isFinite(high52)) high52 = Math.max(...closes);

  const price = closes[closes.length - 1];
  const ma200 = closes.length >= 200 ? avg(closes.slice(-200)) : null;
  const rsi14 = computeRSI(closes, 14);
  const asOf = lastTs ? new Date(lastTs * 1000).toISOString() : new Date().toISOString();

  return { symbol, price, ma200, high52, rsi14, closesCount: closes.length, asOf };
}

function avg(xs: number[]): number {
  return xs.reduce((a, b) => a + b, 0) / xs.length;
}

/** Wilder's-smoothed RSI over `closes` (oldest -> newest) for `period`. */
function computeRSI(closes: number[], period: number): number {
  if (closes.length < period + 1) return NaN;
  const deltas: number[] = [];
  for (let i = 1; i < closes.length; i++) deltas.push(closes[i] - closes[i - 1]);

  let avgGain = 0;
  let avgLoss = 0;
  for (let i = 0; i < period; i++) {
    const d = deltas[i];
    if (d > 0) avgGain += d;
    else avgLoss += -d;
  }
  avgGain /= period;
  avgLoss /= period;

  for (let i = period; i < deltas.length; i++) {
    const d = deltas[i];
    const gain = d > 0 ? d : 0;
    const loss = d < 0 ? -d : 0;
    avgGain = (avgGain * (period - 1) + gain) / period;
    avgLoss = (avgLoss * (period - 1) + loss) / period;
  }

  if (avgLoss === 0) return avgGain === 0 ? 50 : 100;
  const rs = avgGain / avgLoss;
  return 100 - 100 / (1 + rs);
}

async function getQuote(symbol: string): Promise<Quote> {
  if (quoteCache.has(symbol)) return quoteCache.get(symbol)!;
  if (quoteErrors.has(symbol)) throw new Error(quoteErrors.get(symbol)!);
  try {
    const q = await fetchYahooChart(symbol);
    quoteCache.set(symbol, q);
    return q;
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    quoteErrors.set(symbol, msg);
    throw e;
  }
}

// ---------------------------------------------------------------------------
// Risk rules
// ---------------------------------------------------------------------------

type RuleId = "R1" | "R2" | "R3" | "R4";

interface RuleFire {
  rule: RuleId;
  label: string; // e.g. TREND_BREAK
  directive: string; // trim/review instruction (pre-clamp)
}

interface EvaluatedPosition {
  symbol: string;
  weightPct: number;
  gainPct: number | null;
  price: number;
  ma200: number | null;
  vs200dPct: number | null; // (price - ma200) / ma200 * 100
  high52: number;
  fires: RuleFire[];
  clamped: boolean;
}

function evaluatePosition(pos: PositionRow, q: Quote): EvaluatedPosition {
  const { weightPct, symbol } = pos;
  const gainPct = computeGainPct(pos.mv, pos.pnl);
  const { price, ma200, high52 } = q;
  const vs200dPct = ma200 !== null && ma200 !== 0 ? ((price - ma200) / ma200) * 100 : null;
  const belowMa200 = ma200 !== null && price < ma200;

  const fires: RuleFire[] = [];

  // R1 TREND_BREAK
  if (weightPct >= 3 && belowMa200) {
    fires.push({
      rule: "R1",
      label: "TREND_BREAK",
      directive: "TRIM-REVIEW: trend broken on a meaningful position",
    });
  }

  // R2 GIVE_BACK (gave back >=30% from 52wk high on a big winner)
  if (gainPct !== null && gainPct >= 50 && price <= high52 * 0.7) {
    fires.push({
      rule: "R2",
      label: "GIVE_BACK",
      directive: "TRIM: winner giving back gains",
    });
  }

  // R3 CONCENTRATION tiers (first match wins)
  if (weightPct >= 15) {
    fires.push({ rule: "R3", label: "CONCENTRATION_HARD_CAP", directive: "HARD CAP: trim to 15%" });
  } else if (weightPct >= 10 && belowMa200) {
    fires.push({
      rule: "R3",
      label: "CONCENTRATION_TRIM",
      directive: "TRIM: oversized + trend broken",
    });
  } else if (weightPct >= 5 && belowMa200) {
    fires.push({
      rule: "R3",
      label: "CONCENTRATION_REVIEW",
      directive: "REVIEW: sizeable position below trend",
    });
  }

  // R4 WINNER_ROLLOVER (the NEM rule)
  if (weightPct >= 5 && gainPct !== null && gainPct >= 50 && belowMa200) {
    fires.push({
      rule: "R4",
      label: "WINNER_ROLLOVER",
      directive: "TRIM: large locked-in winner rolling over — protect the gain",
    });
  }

  return {
    symbol,
    weightPct,
    gainPct,
    price,
    ma200,
    vs200dPct,
    high52,
    fires,
    clamped: HOLD_ONLY.has(symbol.toUpperCase()),
  };
}

interface ClusterBreach {
  name: string;
  weightPct: number;
  members: string[]; // members actually held (subset of the static sleeve)
  directive: string;
}

function evaluateClusters(byWeight: Map<string, number>): ClusterBreach[] {
  const breaches: ClusterBreach[] = [];
  for (const [name, members] of Object.entries(CLUSTERS)) {
    const held = members.filter((m) => byWeight.has(m));
    const weightPct = held.reduce((sum, m) => sum + (byWeight.get(m) ?? 0), 0);
    if (weightPct > CLUSTER_BREACH_PCT) {
      breaches.push({
        name,
        weightPct,
        members: held,
        directive: `CLUSTER REVIEW: ${name} sleeve at ${weightPct.toFixed(1)}%`,
      });
    }
  }
  return breaches;
}

// ---------------------------------------------------------------------------
// Output
// ---------------------------------------------------------------------------

function fmtPct(n: number | null, digits = 1): string {
  return n === null ? "n/a" : `${n.toFixed(digits)}%`;
}

function fmtVs200d(n: number | null): string {
  if (n === null) return "n/a (< 200 closes)";
  return `${n >= 0 ? "+" : ""}${n.toFixed(1)}%`;
}

function directiveFor(ep: EvaluatedPosition): string {
  if (ep.fires.length === 0) return "";
  if (ep.clamped) return MANDATE_CLAMP_TAG;
  return ep.fires.map((f) => f.directive).join(" | ");
}

function printTable(evaluated: EvaluatedPosition[]) {
  const breached = evaluated.filter((e) => e.fires.length > 0);
  if (breached.length === 0) {
    console.log("No position-level risk breaches.");
    return;
  }
  const headers = ["SYMBOL", "WEIGHT%", "GAIN%", "PRICE", "VS 200D", "RULES", "DIRECTIVE"];
  const rows = breached.map((e) => [
    e.symbol,
    e.weightPct.toFixed(1) + "%",
    fmtPct(e.gainPct),
    e.price.toFixed(2),
    fmtVs200d(e.vs200dPct),
    e.fires.map((f) => f.rule).join(","),
    directiveFor(e),
  ]);
  const widths = headers.map((h, i) => Math.max(h.length, ...rows.map((r) => r[i].length)));
  const line = (cells: string[]) => cells.map((c, i) => c.padEnd(widths[i])).join("  ");
  console.log(line(headers));
  console.log(widths.map((w) => "-".repeat(w)).join("  "));
  for (const r of rows) console.log(line(r));
}

function printClusters(clusters: ClusterBreach[]) {
  if (clusters.length === 0) {
    console.log("No cluster/sleeve concentration breaches.");
    return;
  }
  for (const c of clusters) {
    console.log(
      `  ${c.name.padEnd(14)} weight=${c.weightPct.toFixed(1).padStart(5)}%  members=[${c.members.join(", ")}]  -> ${c.directive}`,
    );
  }
}

// ---------------------------------------------------------------------------
// Sheet I/O (gws CLI) -- only touched under --arm. Mirrors watchlist-alerts.ts
// conventions: batchUpdate + numeric gridRange, never values.update.
// ---------------------------------------------------------------------------

interface GwsResult {
  ok: boolean;
  stdout: string;
  stderr: string;
  code: number;
}

function runGws(args: string[]): GwsResult {
  const proc = Bun.spawnSync(["gws", ...args], {
    env: { ...process.env, GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND: "file" },
    stdout: "pipe",
    stderr: "pipe",
  });
  return {
    ok: proc.exitCode === 0,
    stdout: proc.stdout.toString(),
    stderr: proc.stderr.toString(),
    code: proc.exitCode,
  };
}

/** Returns { alertIds: Set<string>, nextRowIndex0: number }. */
function readWatchlistForArm(): { alertIds: Set<string>; nextRowIndex0: number } {
  const res = runGws([
    "sheets",
    "spreadsheets",
    "values",
    "get",
    "--params",
    JSON.stringify({
      spreadsheetId: SPREADSHEET_ID,
      range: `${SHEET_TAB}!A1:R500`,
      valueRenderOption: "FORMULA",
    }),
  ]);
  if (!res.ok) throw new Error(`gws read failed (exit ${res.code}): ${res.stderr || res.stdout}`);
  const parsed = JSON.parse(res.stdout) as { values?: string[][] };
  const values = parsed.values ?? [];
  const alertIds = new Set<string>();
  for (let i = 1; i < values.length; i++) {
    const id = (values[i]?.[0] ?? "").trim();
    if (id) alertIds.add(id.toLowerCase());
  }
  // Sheets omits fully-empty trailing rows from the returned values array,
  // so the next writable row is simply one past the last returned row --
  // this correctly lands after freeform scratch rows at the bottom too.
  return { alertIds, nextRowIndex0: values.length };
}

let cachedSheetId: number | null = null;
function getSheetId(): number {
  if (cachedSheetId !== null) return cachedSheetId;
  const res = runGws([
    "sheets",
    "spreadsheets",
    "get",
    "--params",
    JSON.stringify({ spreadsheetId: SPREADSHEET_ID, fields: "sheets.properties" }),
  ]);
  if (!res.ok) throw new Error(`gws sheetId lookup failed: ${res.stderr || res.stdout}`);
  const parsed = JSON.parse(res.stdout) as {
    sheets?: { properties: { sheetId: number; title: string } }[];
  };
  const match = (parsed.sheets ?? []).find(
    (s) => s.properties.title.toLowerCase() === SHEET_TAB.toLowerCase(),
  );
  if (!match) throw new Error(`Could not find sheet tab titled "${SHEET_TAB}"`);
  cachedSheetId = match.properties.sheetId;
  return cachedSheetId;
}

interface ArmRowFields {
  alertId: string;
  symbol: string;
  status: "ACTIVE" | "ACTIVE_REVIEW_ONLY";
  conditions: string;
  actionEntry: string;
  reason: string;
  dataSource: string;
  invalidation: string;
}

function appendWatchlistRow(rowIndex0: number, f: ArmRowFields): void {
  const sheetId = getSheetId();
  const nowIso = new Date().toISOString();
  // 18 columns A:R, in order:
  // Alert ID, Symbol, Desk, Status, Conditions, Match, Action/Entry,
  // Reason/Thesis, Data Source, Invalidation/Re-evaluate,
  // Position Target/Cap, Channel, Created At, Last Reviewed, Expiry,
  // Analysis Link, Last Fired, Notes
  const values: string[] = [
    f.alertId,
    f.symbol,
    "risk",
    f.status,
    f.conditions,
    "all",
    f.actionEntry,
    f.reason,
    f.dataSource,
    f.invalidation,
    "[UNAVAILABLE]",
    "telegram:@CryptoAiInvestor",
    nowIso,
    nowIso,
    "[UNAVAILABLE]",
    "[UNAVAILABLE]",
    "[UNAVAILABLE]",
    "risk-desk auto-generated — .agents/skills/risk-desk/scripts/risk-desk.ts",
  ];
  const body = {
    requests: [
      {
        updateCells: {
          range: {
            sheetId,
            startRowIndex: rowIndex0,
            endRowIndex: rowIndex0 + 1,
            startColumnIndex: 0,
            endColumnIndex: values.length,
          },
          rows: [{ values: values.map((v) => ({ userEnteredValue: { stringValue: v } })) }],
          fields: "userEnteredValue",
        },
      },
    ],
  };
  const res = runGws([
    "sheets",
    "spreadsheets",
    "batchUpdate",
    "--params",
    JSON.stringify({ spreadsheetId: SPREADSHEET_ID }),
    "--json",
    JSON.stringify(body),
  ]);
  if (!res.ok) throw new Error(`gws write failed for ${f.alertId}: ${res.stderr || res.stdout}`);
}

/** Builds the arm candidate for one position (only R1/R2/R4 breaches count). */
function buildArmCandidate(ep: EvaluatedPosition): ArmRowFields | null {
  const armable = ep.fires.filter((f) => f.rule === "R1" || f.rule === "R2" || f.rule === "R4");
  if (armable.length === 0) return null;

  // ID/condition template per spec: risk-<sym>-below-<ma200 rounded>. Falls
  // back to a high52-based tripwire if ma200 is unavailable (only possible
  // when R2 fires alone without R1/R4, since those two require ma200).
  const sym = ep.symbol.toLowerCase().replace(/[^a-z0-9]/g, "");
  let conditions: string;
  let idSuffix: string;
  if (ep.ma200 !== null) {
    const level = Math.round(ep.ma200);
    conditions = `below:${level}`;
    idSuffix = `below-${level}`;
  } else {
    const level = Math.round(ep.high52 * 0.7);
    conditions = `below:${level}`;
    idSuffix = `giveback-${level}`;
  }
  const alertId = `risk-${sym}-${idSuffix}`;

  const ruleLines = armable
    .map((f) => `${f.rule} ${f.label}: ${f.directive}`)
    .join("; ");
  const numbers = `weight=${ep.weightPct.toFixed(1)}% gain=${fmtPct(ep.gainPct)} price=${ep.price.toFixed(2)} ma200=${ep.ma200 !== null ? ep.ma200.toFixed(2) : "n/a"} high52=${ep.high52.toFixed(2)}`;

  const clamped = ep.clamped;
  return {
    alertId,
    symbol: ep.symbol,
    status: clamped ? "ACTIVE_REVIEW_ONLY" : "ACTIVE",
    conditions,
    actionEntry: clamped
      ? "RISK DESK: MANDATE-CLAMPED — review only, no auto-trim"
      : "RISK DESK: trim/review — trend break",
    reason: `WHY SET (risk-desk, auto): ${ruleLines}. ${numbers}.${
      clamped ? ` ${MANDATE_CLAMP_TAG}` : ""
    }`,
    dataSource: `risk-desk.ts (Yahoo v8 chart) ${new Date().toISOString().slice(0, 10)}: ${numbers}`,
    invalidation: "Re-evaluate when price reclaims the level above, or when weight/gain drop below the firing thresholds.",
  };
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  const args = parseArgs(process.argv.slice(2));

  console.log(`risk-desk — ${new Date().toISOString()}`);
  console.log(`Mode: ${args.arm ? "ARM (will write ACTIVE alerts to sheet)" : "REPORT-ONLY (--arm not set)"}`);
  console.log("");

  const positionsFile = resolvePositionsFile(args.positions);
  console.log(`Positions file: ${positionsFile}`);

  const { rows, totalMV, skippedNonEquity, skippedNoMV } = loadPositions(positionsFile);
  console.log(`Total book MV: $${totalMV.toLocaleString()}`);
  console.log(`Positions loaded: ${rows.length}`);
  if (skippedNonEquity.length > 0) {
    console.log(`Skipped (non-equity: cash/t-bills/etc): ${skippedNonEquity.join(", ")}`);
  }
  if (skippedNoMV.length > 0) {
    console.log(`Skipped (no MarketValue): ${skippedNoMV.join(", ")}`);
  }
  console.log("");

  const uniqueYahooSymbols = Array.from(new Set(rows.map((r) => r.yahooSymbol)));
  console.log(`Fetching market data for ${uniqueYahooSymbols.length} unique symbol(s)...`);
  const fetchFailures: { symbol: string; reason: string }[] = [];
  for (const sym of uniqueYahooSymbols) {
    try {
      const q = await getQuote(sym);
      console.log(
        `  ${sym.padEnd(10)} price=${q.price.toFixed(2).padStart(10)}  ma200=${q.ma200 !== null ? q.ma200.toFixed(2).padStart(10) : "n/a".padStart(10)}  high52=${q.high52.toFixed(2).padStart(10)}  rsi14=${q.rsi14.toFixed(1).padStart(5)}  closes=${q.closesCount}`,
      );
    } catch (e) {
      const reason = e instanceof Error ? e.message : String(e);
      fetchFailures.push({ symbol: sym, reason });
      console.log(`  ${sym.padEnd(10)} FETCH FAILED: ${reason}`);
    }
  }
  console.log("");

  const evaluated: EvaluatedPosition[] = [];
  const weightBySymbol = new Map<string, number>();
  for (const pos of rows) {
    weightBySymbol.set(pos.symbol.toUpperCase(), pos.weightPct);
    if (quoteErrors.has(pos.yahooSymbol)) continue; // already logged above
    const q = quoteCache.get(pos.yahooSymbol);
    if (!q) continue;
    evaluated.push(evaluatePosition(pos, q));
  }

  console.log("--- Position-level breaches (R1 TREND_BREAK, R2 GIVE_BACK, R3 CONCENTRATION, R4 WINNER_ROLLOVER) ---");
  printTable(evaluated);
  console.log("");

  console.log("--- Cluster/sleeve breaches (R5 CONCENTRATION, portfolio-level; not price-conditional) ---");
  const clusterBreaches = evaluateClusters(weightBySymbol);
  printClusters(clusterBreaches);
  console.log("");

  const positionBreaches = evaluated.filter((e) => e.fires.length > 0);
  const clampedBreaches = positionBreaches.filter((e) => e.clamped);

  console.log("=== Summary ===");
  console.log(`Positions evaluated: ${evaluated.length} (of ${rows.length} loaded, ${fetchFailures.length} fetch failure(s))`);
  console.log(`Position-level breaches: ${positionBreaches.length} (${clampedBreaches.length} mandate-clamped)`);
  console.log(`Cluster/sleeve breaches: ${clusterBreaches.length}`);
  if (fetchFailures.length > 0) {
    for (const f of fetchFailures) console.log(`  - ${f.symbol}: ${f.reason}`);
  }

  // -------------------------------------------------------------------------
  // Arming
  // -------------------------------------------------------------------------
  const armCandidates = positionBreaches
    .map((ep) => ({ ep, fields: buildArmCandidate(ep) }))
    .filter((c): c is { ep: EvaluatedPosition; fields: ArmRowFields } => c.fields !== null);

  console.log("");
  console.log(`--- Arming (R1/R2/R4 breaches only; R3/R5 are portfolio-level, never armed) ---`);
  if (armCandidates.length === 0) {
    console.log("No R1/R2/R4 breaches to arm.");
  } else if (!args.arm) {
    console.log("--arm not set — would arm:");
    for (const { fields } of armCandidates) {
      console.log(`  WOULD UPSERT ${fields.alertId} (${fields.symbol}) status=${fields.status} conditions=${fields.conditions}`);
      console.log(`    Action: ${fields.actionEntry}`);
      console.log(`    Reason: ${fields.reason}`);
    }
  } else {
    const { alertIds, nextRowIndex0 } = readWatchlistForArm();
    let writeRow = nextRowIndex0;
    let armed = 0;
    let skipped = 0;
    for (const { fields } of armCandidates) {
      if (alertIds.has(fields.alertId.toLowerCase())) {
        console.log(`  SKIP (already exists): ${fields.alertId}`);
        skipped++;
        continue;
      }
      appendWatchlistRow(writeRow, fields);
      console.log(`  ARMED (row ${writeRow + 1}): ${fields.alertId} (${fields.symbol}) status=${fields.status}`);
      alertIds.add(fields.alertId.toLowerCase());
      writeRow++;
      armed++;
    }
    console.log(`Armed: ${armed}, skipped (duplicate): ${skipped}`);
  }

  // -------------------------------------------------------------------------
  // JSON output
  // -------------------------------------------------------------------------
  if (args.json) {
    const json = {
      generatedAt: new Date().toISOString(),
      positionsFile,
      totalMV,
      positionsLoaded: rows.length,
      positionsEvaluated: evaluated.length,
      skippedNonEquity,
      skippedNoMV,
      fetchFailures,
      positionBreaches: positionBreaches.map((e) => ({
        symbol: e.symbol,
        weightPct: e.weightPct,
        gainPct: e.gainPct,
        price: e.price,
        ma200: e.ma200,
        vs200dPct: e.vs200dPct,
        high52: e.high52,
        rulesFired: e.fires.map((f) => ({ rule: f.rule, label: f.label, directive: f.directive })),
        clamped: e.clamped,
        directive: directiveFor(e),
      })),
      clusterBreaches,
      armCandidates: armCandidates.map((c) => c.fields),
      armed: args.arm,
    };
    console.log("");
    console.log("--- JSON ---");
    console.log(JSON.stringify(json, null, 2));
  }
}

main();
