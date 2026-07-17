#!/usr/bin/env bun
/**
 * watchlist-alerts.ts
 *
 * Reads the "Watchlist" Google Sheet tab (canonical alert trigger registry),
 * fetches live market data per symbol from Yahoo Finance, evaluates each
 * ACTIVE alert's trigger condition, and for triggered alerts:
 *   (a) posts to a Telegram "Market Alerts" topic via bot API
 *   (b) writes the result back to the sheet (Status -> TRIGGERED)
 *
 * Designed to be run repeatedly by cron. Idempotent: a row already
 * TRIGGERED is never re-evaluated/re-posted -- the sheet Status IS the
 * dedup state.
 *
 * Usage:
 *   bun watchlist-alerts.ts [--dry-run] [--only SYMBOL]
 *
 * Env (all required for live Telegram posting + sheet write-back; if any
 * are missing the script auto-falls-back to DRY-RUN):
 *   TELEGRAM_BOT_TOKEN
 *   TELEGRAM_ALERTS_CHAT_ID
 *   TELEGRAM_ALERTS_THREAD_ID
 *
 * Requires the `gws` CLI (Google Workspace CLI) on PATH and authenticated.
 */

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

const SPREADSHEET_ID = "1aunLbpNGo85WqrMHiIsy6nFUija4Lnjot-rIhE-pGU8";
const SHEET_TAB = "Watchlist";
const READ_RANGE = `${SHEET_TAB}!A1:R500`;

const COL = {
  ALERT_ID: 0,
  SYMBOL: 1,
  DESK: 2,
  STATUS: 3,
  CONDITIONS: 4,
  MATCH: 5,
  ACTION_ENTRY: 6,
  REASON: 7,
  DATA_SOURCE: 8,
  INVALIDATION: 9,
} as const;

const YAHOO_USER_AGENT =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36 watchlist-alerts.ts/1.0";

// ---------------------------------------------------------------------------
// CLI args
// ---------------------------------------------------------------------------

interface CliArgs {
  dryRun: boolean;
  only: string | null;
}

function parseArgs(argv: string[]): CliArgs {
  let dryRun = false;
  let only: string | null = null;
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--dry-run") {
      dryRun = true;
    } else if (a === "--only") {
      only = (argv[i + 1] ?? "").toUpperCase() || null;
      i++;
    } else if (a.startsWith("--only=")) {
      only = a.slice("--only=".length).toUpperCase() || null;
    }
  }
  return { dryRun, only };
}

// ---------------------------------------------------------------------------
// Sheet I/O (backed by the `gws` CLI). Kept behind readWatchlist() /
// updateAlertRow() so the backend can be swapped later (e.g. direct Sheets
// API client) without touching evaluation logic.
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

interface WatchlistRow {
  rowIndex0: number; // 0-based sheet row index (0 == header row), matches Sheets API gridRange
  raw: string[];
  alertId: string;
  symbol: string;
  desk: string;
  status: string;
  conditions: string;
  match: string;
  actionEntry: string;
  reason: string;
  dataSource: string;
  invalidation: string;
}

/** Reads the full Watchlist tab and returns parsed data rows (header excluded). */
function readWatchlist(): WatchlistRow[] {
  const res = runGws([
    "sheets",
    "spreadsheets",
    "values",
    "get",
    "--params",
    JSON.stringify({
      spreadsheetId: SPREADSHEET_ID,
      range: READ_RANGE,
      valueRenderOption: "FORMULA",
    }),
  ]);
  if (!res.ok) {
    throw new Error(`gws read failed (exit ${res.code}): ${res.stderr || res.stdout}`);
  }
  let parsed: { values?: string[][] };
  try {
    parsed = JSON.parse(res.stdout);
  } catch (e) {
    throw new Error(`gws read returned non-JSON stdout: ${res.stdout.slice(0, 300)}`);
  }
  const values = parsed.values ?? [];
  const rows: WatchlistRow[] = [];
  // values[0] is the header row -> sheet row index 0
  for (let i = 1; i < values.length; i++) {
    const raw = values[i] ?? [];
    const alertId = (raw[COL.ALERT_ID] ?? "").trim();
    const status = (raw[COL.STATUS] ?? "").trim();
    // Skip blank rows / freeform notes that don't have the Alert ID + Status
    // shape of a real alert row (e.g. trailing scratch rows like
    // ["META", "Considered cheap"]).
    if (!alertId || !status) continue;
    rows.push({
      rowIndex0: i,
      raw,
      alertId,
      symbol: (raw[COL.SYMBOL] ?? "").trim(),
      desk: (raw[COL.DESK] ?? "").trim(),
      status,
      conditions: (raw[COL.CONDITIONS] ?? "").trim(),
      match: (raw[COL.MATCH] ?? "").trim(),
      actionEntry: (raw[COL.ACTION_ENTRY] ?? "").trim(),
      reason: (raw[COL.REASON] ?? "").trim(),
      dataSource: (raw[COL.DATA_SOURCE] ?? "").trim(),
      invalidation: (raw[COL.INVALIDATION] ?? "").trim(),
    });
  }
  return rows;
}

let cachedSheetId: number | null = null;

/** Resolves the numeric sheetId for SHEET_TAB (needed for gridRange writes). */
function getSheetId(): number {
  if (cachedSheetId !== null) return cachedSheetId;
  const res = runGws([
    "sheets",
    "spreadsheets",
    "get",
    "--params",
    JSON.stringify({ spreadsheetId: SPREADSHEET_ID, fields: "sheets.properties" }),
  ]);
  if (!res.ok) {
    throw new Error(`gws sheetId lookup failed: ${res.stderr || res.stdout}`);
  }
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

/** Reads a single cell's current string value (used as a freshness check before writing). */
function readCell(a1Col: string, rowIndex0: number): string {
  const rowNum = rowIndex0 + 1; // 1-based for A1 notation
  const res = runGws([
    "sheets",
    "spreadsheets",
    "values",
    "get",
    "--params",
    JSON.stringify({
      spreadsheetId: SPREADSHEET_ID,
      range: `${SHEET_TAB}!${a1Col}${rowNum}:${a1Col}${rowNum}`,
    }),
  ]);
  if (!res.ok) throw new Error(`gws readCell failed: ${res.stderr || res.stdout}`);
  const parsed = JSON.parse(res.stdout) as { values?: string[][] };
  return (parsed.values?.[0]?.[0] ?? "").trim();
}

interface UpdateResult {
  written: boolean;
  skippedReason?: string;
}

/**
 * Sets Status (col D) -> "TRIGGERED" and Match (col F) -> the fired summary
 * for a single row. Idempotent: re-reads Status immediately before writing
 * and no-ops if it's already TRIGGERED (someone/something beat us to it).
 *
 * NOTE: exercised in dry-run mode only during this build's verification --
 * the batchUpdate call itself has not been run against the live sheet.
 * The gridRange/updateCells shape follows the project's documented
 * write convention (AGENTS.md: sheetId + numeric gridRange, never
 * values.update with A1 ranges) but flag as untested-until-live.
 */
function updateAlertRow(
  row: WatchlistRow,
  fields: { matchSummary: string },
): UpdateResult {
  const currentStatus = readCell("D", row.rowIndex0);
  if (currentStatus === "TRIGGERED") {
    return { written: false, skippedReason: "already TRIGGERED (race/rerun)" };
  }

  const sheetId = getSheetId();
  const body = {
    requests: [
      {
        updateCells: {
          range: {
            sheetId,
            startRowIndex: row.rowIndex0,
            endRowIndex: row.rowIndex0 + 1,
            startColumnIndex: COL.STATUS,
            endColumnIndex: COL.STATUS + 1,
          },
          rows: [{ values: [{ userEnteredValue: { stringValue: "TRIGGERED" } }] }],
          fields: "userEnteredValue",
        },
      },
      {
        updateCells: {
          range: {
            sheetId,
            startRowIndex: row.rowIndex0,
            endRowIndex: row.rowIndex0 + 1,
            startColumnIndex: COL.MATCH,
            endColumnIndex: COL.MATCH + 1,
          },
          rows: [{ values: [{ userEnteredValue: { stringValue: fields.matchSummary } }] }],
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
  if (!res.ok) {
    throw new Error(`gws write failed for ${row.alertId}: ${res.stderr || res.stdout}`);
  }

  // Verify per project convention: read back and confirm.
  const verifyStatus = readCell("D", row.rowIndex0);
  if (verifyStatus !== "TRIGGERED") {
    throw new Error(
      `Write verification failed for ${row.alertId}: expected Status=TRIGGERED, got "${verifyStatus}"`,
    );
  }
  return { written: true };
}

// ---------------------------------------------------------------------------
// Market data (Yahoo Finance chart API). Swappable via getQuote().
// ---------------------------------------------------------------------------

interface Quote {
  symbol: string;
  price: number;
  closes: number[]; // full daily close series, oldest -> newest, nulls dropped
  asOf: string; // ISO timestamp of the latest close used
  rsi14: number;
}

const quoteCache = new Map<string, Quote>();
const quoteErrors = new Map<string, string>();

async function fetchYahooChart(symbol: string): Promise<Quote> {
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(
    symbol,
  )}?interval=1d&range=6mo`;
  const resp = await fetch(url, {
    headers: { "User-Agent": YAHOO_USER_AGENT },
  });
  if (!resp.ok) {
    throw new Error(`HTTP ${resp.status} ${resp.statusText}`);
  }
  const json = await resp.json();
  const result = json?.chart?.result?.[0];
  if (!result) {
    const err = json?.chart?.error;
    throw new Error(err ? `Yahoo error: ${JSON.stringify(err)}` : "no chart result");
  }
  const timestamps: number[] = result.timestamp ?? [];
  const closesRaw: (number | null)[] = result.indicators?.quote?.[0]?.close ?? [];
  const closes: number[] = [];
  let lastTs = 0;
  for (let i = 0; i < closesRaw.length; i++) {
    const c = closesRaw[i];
    if (c === null || c === undefined || Number.isNaN(c)) continue;
    closes.push(c);
    lastTs = timestamps[i] ?? lastTs;
  }
  if (closes.length === 0) {
    throw new Error("no usable close prices returned");
  }
  const price = closes[closes.length - 1];
  const asOf = lastTs ? new Date(lastTs * 1000).toISOString() : new Date().toISOString();
  const rsi14 = computeRSI(closes, 14);
  return { symbol, price, closes, asOf, rsi14 };
}

/** Wilder's-smoothed RSI over `closes` (oldest -> newest) for the given period. */
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

/** Cached, once-per-run quote fetch. Throws (caller should catch) on failure. */
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

function getRSI(quote: Quote, period: number): number {
  return period === 14 ? quote.rsi14 : computeRSI(quote.closes, period);
}

// ---------------------------------------------------------------------------
// Condition grammar
// ---------------------------------------------------------------------------

type AtomicCondition =
  | { kind: "above"; value: number; raw: string }
  | { kind: "below"; value: number; raw: string }
  | { kind: "rsi_above"; period: number; value: number; raw: string }
  | { kind: "rsi_below"; period: number; value: number; raw: string }
  | { kind: "date"; label: "record" | "payment"; date: string; raw: string };

const MARKET_KINDS = new Set(["above", "below", "rsi_above", "rsi_below"]);

function parseAtomic(token: string): AtomicCondition {
  const t = token.trim();

  let m = t.match(/^above:(-?\d+(?:\.\d+)?)$/i);
  if (m) return { kind: "above", value: Number(m[1]), raw: t };

  m = t.match(/^below:(-?\d+(?:\.\d+)?)$/i);
  if (m) return { kind: "below", value: Number(m[1]), raw: t };

  m = t.match(/^rsi_above(?:\((\d+)\))?:(-?\d+(?:\.\d+)?)$/i);
  if (m) return { kind: "rsi_above", period: m[1] ? Number(m[1]) : 14, value: Number(m[2]), raw: t };

  m = t.match(/^rsi_below(?:\((\d+)\))?:(-?\d+(?:\.\d+)?)$/i);
  if (m) return { kind: "rsi_below", period: m[1] ? Number(m[1]) : 14, value: Number(m[2]), raw: t };

  m = t.match(/^(record|payment):(\d{4}-\d{2}-\d{2})$/i);
  if (m) return { kind: "date", label: m[1].toLowerCase() as "record" | "payment", date: m[2], raw: t };

  throw new Error(`unrecognized condition token: "${t}"`);
}

/** Parses the full Conditions cell (may be a single token or "A AND B ..."). */
function parseConditions(conditionsStr: string): AtomicCondition[] {
  const parts = conditionsStr.split(" AND ").map((s) => s.trim()).filter(Boolean);
  if (parts.length === 0) throw new Error("empty conditions cell");
  return parts.map(parseAtomic);
}

function describeAtomic(cond: AtomicCondition): string {
  switch (cond.kind) {
    case "above":
      return `above ${cond.value}`;
    case "below":
      return `below ${cond.value}`;
    case "rsi_above":
      return `RSI(${cond.period}) above ${cond.value}`;
    case "rsi_below":
      return `RSI(${cond.period}) below ${cond.value}`;
    case "date":
      return `${cond.label} date ${cond.date} reached`;
  }
}

interface AtomicEval {
  cond: AtomicCondition;
  met: boolean;
  actual: string;
}

function evaluateAtomic(cond: AtomicCondition, quote: Quote | null, todayISO: string): AtomicEval {
  switch (cond.kind) {
    case "above":
      return { cond, met: !!quote && quote.price >= cond.value, actual: quote ? quote.price.toFixed(2) : "n/a" };
    case "below":
      return { cond, met: !!quote && quote.price <= cond.value, actual: quote ? quote.price.toFixed(2) : "n/a" };
    case "rsi_above": {
      const rsi = quote ? getRSI(quote, cond.period) : NaN;
      return { cond, met: !Number.isNaN(rsi) && rsi >= cond.value, actual: Number.isNaN(rsi) ? "n/a" : rsi.toFixed(1) };
    }
    case "rsi_below": {
      const rsi = quote ? getRSI(quote, cond.period) : NaN;
      return { cond, met: !Number.isNaN(rsi) && rsi <= cond.value, actual: Number.isNaN(rsi) ? "n/a" : rsi.toFixed(1) };
    }
    case "date":
      return { cond, met: todayISO >= cond.date, actual: todayISO };
  }
}

// ---------------------------------------------------------------------------
// Telegram
// ---------------------------------------------------------------------------

interface TelegramConfig {
  token: string;
  chatId: string;
  threadId: string;
}

function loadTelegramConfig(): TelegramConfig | null {
  const token = process.env.TELEGRAM_BOT_TOKEN;
  const chatId = process.env.TELEGRAM_ALERTS_CHAT_ID;
  const threadId = process.env.TELEGRAM_ALERTS_THREAD_ID;
  if (!token || !chatId || !threadId) return null;
  return { token, chatId, threadId };
}

async function sendTelegramMessage(cfg: TelegramConfig, text: string): Promise<void> {
  const url = `https://api.telegram.org/bot${cfg.token}/sendMessage`;
  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: cfg.chatId,
      message_thread_id: Number(cfg.threadId),
      text,
    }),
  });
  if (!resp.ok) {
    const body = await resp.text();
    throw new Error(`Telegram sendMessage failed: HTTP ${resp.status} ${body}`);
  }
}

// ---------------------------------------------------------------------------
// Message formatting
// ---------------------------------------------------------------------------

function buildMessage(
  row: WatchlistRow,
  metAtomics: AtomicEval[],
  quote: Quote | null,
): string {
  const conditionMet = metAtomics.map((a) => describeAtomic(a.cond)).join(" AND ");
  const reasonSnippet = row.reason.slice(0, 140) + (row.reason.length > 140 ? "…" : "");

  let head: string;
  if (quote) {
    const rsi = getRSI(quote, 14);
    head = `🔔 ${row.symbol} ${conditionMet} @ ${quote.price.toFixed(2)} (RSI ${Number.isNaN(rsi) ? "n/a" : rsi.toFixed(1)})`;
  } else {
    head = `🔔 ${row.symbol} ${conditionMet}`;
  }

  const lines = [head];
  if (row.actionEntry && row.actionEntry !== "[UNAVAILABLE]") lines.push(row.actionEntry);
  if (reasonSnippet) lines.push(`Why: ${reasonSnippet}`);
  lines.push(`Alert: ${row.alertId}`);

  let msg = lines.join("\n");
  if (row.status.startsWith("ACTIVE_REVIEW_ONLY")) {
    msg = `⚠️ REVIEW ONLY — no auto-action.\n${msg}`;
  }
  return msg;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

interface SkipEntry {
  alertId: string;
  symbol: string;
  reason: string;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const telegramCfg = loadTelegramConfig();
  const dryRun = args.dryRun || telegramCfg === null;
  const dryRunReason = args.dryRun
    ? "explicit --dry-run"
    : telegramCfg === null
      ? "TELEGRAM_* env vars not fully set"
      : null;

  const todayISO = new Date().toISOString().slice(0, 10);

  console.log(`Watchlist Alert Check — ${new Date().toISOString()}`);
  console.log(`Mode: ${dryRun ? `DRY-RUN (${dryRunReason})` : "LIVE"}`);
  if (args.only) console.log(`Filter: --only ${args.only}`);
  console.log("");

  let allRows: WatchlistRow[];
  try {
    allRows = readWatchlist();
  } catch (e) {
    console.error(`FATAL: could not read watchlist sheet: ${e instanceof Error ? e.message : e}`);
    process.exitCode = 1;
    return;
  }

  let rows = allRows.filter((r) => r.status.startsWith("ACTIVE"));
  if (args.only) rows = rows.filter((r) => r.symbol.toUpperCase() === args.only);

  const skipped: SkipEntry[] = [];
  let fired = 0;

  // Pre-parse conditions for all candidate rows so we know which symbols
  // actually need market data (date-only conditions don't).
  interface ParsedRow {
    row: WatchlistRow;
    conds: AtomicCondition[];
    needsQuote: boolean;
  }
  const parsedRows: ParsedRow[] = [];
  for (const row of rows) {
    if (row.status === "TRIGGERED") {
      skipped.push({ alertId: row.alertId, symbol: row.symbol, reason: "already TRIGGERED" });
      continue;
    }
    try {
      const conds = parseConditions(row.conditions);
      const needsQuote = conds.some((c) => MARKET_KINDS.has(c.kind));
      parsedRows.push({ row, conds, needsQuote });
    } catch (e) {
      skipped.push({
        alertId: row.alertId,
        symbol: row.symbol,
        reason: `malformed condition: ${e instanceof Error ? e.message : e}`,
      });
    }
  }

  const neededSymbols = Array.from(
    new Set(parsedRows.filter((p) => p.needsQuote).map((p) => p.row.symbol)),
  );

  console.log(`Fetching quotes for ${neededSymbols.length} symbol(s): ${neededSymbols.join(", ")}`);
  for (const sym of neededSymbols) {
    try {
      const q = await getQuote(sym);
      console.log(
        `  ${sym.padEnd(10)} price=${q.price.toFixed(2).padStart(10)}  RSI14=${q.rsi14.toFixed(1).padStart(5)}  asOf=${q.asOf}`,
      );
    } catch (e) {
      console.log(`  ${sym.padEnd(10)} FETCH FAILED: ${e instanceof Error ? e.message : e}`);
    }
  }
  console.log("");

  console.log("--- Alert evaluation ---");
  for (const { row, conds, needsQuote } of parsedRows) {
    let quote: Quote | null = null;
    if (needsQuote) {
      if (quoteErrors.has(row.symbol)) {
        skipped.push({
          alertId: row.alertId,
          symbol: row.symbol,
          reason: `market data fetch failed: ${quoteErrors.get(row.symbol)}`,
        });
        console.log(`[SKIP ] ${row.alertId} (${row.symbol}) — fetch failed`);
        continue;
      }
      quote = quoteCache.get(row.symbol) ?? null;
    }

    const evals = conds.map((c) => evaluateAtomic(c, quote, todayISO));
    const allMet = evals.every((e) => e.met);
    const detail = evals
      .map((e) => `${describeAtomic(e.cond)} [actual=${e.actual}] -> ${e.met ? "MET" : "not met"}`)
      .join(" AND ");

    if (!allMet) {
      console.log(`[     ] ${row.alertId.padEnd(28)} ${row.symbol.padEnd(9)} ${detail} => NOT TRIGGERED`);
      continue;
    }

    console.log(`[FIRE ] ${row.alertId.padEnd(28)} ${row.symbol.padEnd(9)} ${detail} => TRIGGERED`);
    fired++;

    const message = buildMessage(row, evals, quote);

    if (dryRun) {
      console.log("--- would send to Telegram ---");
      console.log(message);
      console.log("--- would write to sheet: Status=TRIGGERED ---");
      console.log("-------------------------------");
      continue;
    }

    // LIVE path (exercised only when TELEGRAM_* env is fully set).
    try {
      await sendTelegramMessage(telegramCfg!, message);
      const priceStr = quote ? ` price=${quote.price.toFixed(2)}` : "";
      const rsiStr = quote ? ` rsi=${getRSI(quote, 14).toFixed(1)}` : "";
      const matchSummary = `FIRED ${new Date().toISOString()}${priceStr}${rsiStr}`;
      const result = updateAlertRow(row, { matchSummary });
      if (!result.written) {
        console.log(`  sheet write skipped for ${row.alertId}: ${result.skippedReason}`);
      }
    } catch (e) {
      console.error(`  ERROR posting/writing for ${row.alertId}: ${e instanceof Error ? e.message : e}`);
      skipped.push({ alertId: row.alertId, symbol: row.symbol, reason: `post/write error: ${e}` });
      fired--; // don't count it as a clean fire if we couldn't complete the action
    }
  }

  console.log("");
  console.log("=== Summary ===");
  console.log(`Checked: ${parsedRows.length}`);
  console.log(`Fired:   ${fired}`);
  console.log(`Skipped: ${skipped.length}`);
  for (const s of skipped) {
    console.log(`  - ${s.alertId} (${s.symbol}): ${s.reason}`);
  }
  console.log(`Dry-run: ${dryRun}${dryRunReason ? ` (${dryRunReason})` : ""}`);
}

main();
