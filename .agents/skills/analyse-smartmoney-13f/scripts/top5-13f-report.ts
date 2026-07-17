#!/usr/bin/env bun
/**
 * top5-13f-report.ts
 *
 * Bun+TypeScript CLI that fetches LIVE SEC Form 13F-HR filings (via the official
 * data.sec.gov / www.sec.gov/Archives endpoints — no third-party aggregator) for a
 * roster of "top-5 AUM institutional-flow" hedge funds, aggregates their holdings,
 * computes quarter-over-quarter NEW/ADD/TRIM/EXIT actions, and writes a Markdown
 * report + JSON sidecar + hand-drawn SVG pie chart.
 *
 * Usage:
 *   bun .agents/skills/analyse-smartmoney-13f/scripts/top5-13f-report.ts [flags]
 *
 * Flags:
 *   --roster <path>       Roster JSON path, relative to repo root. Default:
 *                         .cache/analyst-smartmoney-13f/roster.json
 *   --managers k1,k2,...  Explicit roster keys to use (overrides default selection).
 *                         Errors loudly (nonzero exit) if any key is not in the roster.
 *   --universe <tag>      Override the `universe` tag filter used for default manager
 *                         selection. Default: top5-aum
 *   --out-dir <dir>       Output directory, relative to repo root. Default: research
 *   --top <n>             Row/slice cap for Top Buys/Sells tables and the pie chart.
 *                         Default: 10
 *   --date <YYYY-MM-DD>   Overrides the report's OWN filename/"as of" timestamp only.
 *                         Does NOT change which SEC filings are fetched — SEC EDGAR is
 *                         always queried for the manager's actual latest/prior 13F-HR
 *                         filings regardless of this flag. Useful for reproducible
 *                         filenames when re-running against the same live data.
 *   --user-agent <string> Custom User-Agent header sent to SEC EDGAR.
 *   --help                Print usage and exit 0.
 *
 * ── Methodology (also duplicated in the generated report's Methodology section) ──
 *
 * Instrument-type classification (applied per raw <infoTable> row before aggregation):
 *   - <putCall> present, "Call" (case-insensitive)  -> "call option"
 *   - <putCall> present, "Put"  (case-insensitive)  -> "put option"
 *   - else <titleOfClass> (case-insensitive, trimmed) contains "COM" or "ORD", or
 *     equals "SH"/"SHS"/"STK"                        -> "common/share"
 *   - else                                           -> "other" (preferred, notes,
 *     units, warrants — never misclassified as common)
 *
 * Quarter-over-quarter action definitions, computed per manager on the
 * (cusip, instrumentType) key, THEN aggregated cross-fund for the Top Buys/Sells
 * tables:
 *   - NEW       = present (aggregated value > 0) in current filing, absent/zero in
 *                 that manager's prior filing.
 *   - ADD       = present in both, current > prior (beyond 1% tolerance).
 *   - TRIM      = present in both, current < prior (beyond 1% tolerance), current > 0.
 *   - EXIT      = present (>0) in prior filing, absent/zero in current filing.
 *   - UNCHANGED = present in both, change within 1% tolerance — excluded from
 *                 Top Buys/Sells entirely (not reported as an action).
 * Top Buys ranking key  = sum of NEW+ADD dollar deltas across contributing managers.
 * Top Sells ranking key = sum of |TRIM delta| + |EXIT prior value| across contributing
 * managers (TRIM and EXIT are always shown as distinct actions per contributing fund,
 * never conflated into one label).
 *
 * Top Buys/Sells "Acting-Funds Current/Prior Value" columns (JSON:
 * acting_funds_current_value / acting_funds_prior_value) sum ONLY the funds that took a
 * NEW/ADD/TRIM/EXIT action on that position this quarter — funds holding it UNCHANGED are
 * excluded by definition. This is deliberately NOT the position's total consolidated
 * holding value across all funds (see ConsolidatedPosition.aggregate_value_usd /
 * "Consolidated Current Holdings" for that full cross-fund total) — never conflate the two.
 *
 * Manager-level partial-failure handling: the latest filing and prior (Q/Q) filing are
 * fetched/parsed independently per manager. Once a manager's LATEST filing fetch, parse,
 * and reconciliation succeed, that manager is `status: "ok"` and its current holdings are
 * always included in Consolidated Current Holdings and the pie chart — even if the PRIOR
 * filing then fails to fetch/parse. A prior-filing failure only sets `prior_available:
 * false` (with `prior_stage`/`prior_error` recorded and an explicit warning) and excludes
 * that manager from Top Buys/Sells for this run; it is never allowed to discard the
 * manager's already-successful current-holdings result, and never fabricates a Q/Q action.
 *
 * Never reclassify a PUT/CALL row's action as a directional stock call: option rows
 * keep their own instrument-type label and the options-notional caveat below always
 * applies; they are never converted to equivalent common-stock language.
 *
 * OPTIONS CAVEAT (verbatim, also in generated report):
 * "Options (PUT/CALL) values reported on Form 13F represent the market value of the
 * UNDERLYING shares (notional), not the option contract's own market value/premium —
 * do not use reported option 'value' to infer position size, risk, or directional
 * exposure. A PUT position is a bearish/hedging signal on the underlying and must
 * never be read as a bullish stock call; a CALL position must never be read as
 * equivalent to owning the same dollar amount of common stock."
 *
 * Zero npm dependencies — Bun/Node built-ins only (global fetch, node:fs, node:path).
 * XML is parsed with hand-rolled regex helpers (extractTagRaw/extractTagText/
 * extractBlocks below) that tolerate an optional `(\w+:)?` namespace-prefix on every
 * tag name, since real SEC filers are NOT consistent about this (confirmed live:
 * Bridgewater/Man Group use `ns1:`, Millennium uses `n1:`, Elliott/Citadel use no
 * prefix at all, on the exact same `infoTable` schema).
 */

import { resolve, join } from "node:path";
import { mkdirSync, writeFileSync, existsSync, readFileSync } from "node:fs";

// ── Constants ─────────────────────────────────────────────────────────────────

// NOTE (deviation from the originally-specified default UA): SEC EDGAR's Akamai WAF
// returns a hard 403 "Your Request Originates from an Undeclared Automated Tool" for
// ANY User-Agent string containing the substring "github.com" — verified live via
// curl against data.sec.gov during development (repeatable, not a rate-limit fluke;
// UAs without "github.com" succeed immediately, UAs with it fail every time). The
// spec's suggested default UA embeds a github.com URL, so it is unusable against the
// real endpoint. This default swaps in a UA that keeps the tool name + contact email
// (satisfying SEC's fair-access User-Agent policy: "Sample Company Name
// AdminContact@sample.com") but drops the offending substring.
const DEFAULT_UA = "analyse-smartmoney-13f-top5-report/1.0 (research@agentlabs.cc)";
const DEFAULT_UNIVERSE_TAG = "top5-aum";
const DEFAULT_TOP_N = 10;
const SEC_DELAY_MS = 300; // polite delay between requests to SEC endpoints

const PIE_PALETTE = [
  "#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F",
  "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F", "#BAB0AC",
  "#1F77B4", "#FF7F0E", "#2CA02C", "#D62728", "#9467BD",
];

const ACTION_TOLERANCE = 0.01; // 1% — within this band, treat as UNCHANGED

// ── Types ─────────────────────────────────────────────────────────────────────

interface RosterEntry {
  fund: string;
  cik: string;
  bucket?: string;
  universe?: string;
  note?: string;
}
type Roster = Record<string, RosterEntry | unknown>;

interface FilingMeta {
  form: string;
  filingDate: string;
  reportDate: string;
  accessionNumber: string;
  primaryDocument: string;
}

type InstrumentType = "common/share" | "call option" | "put option" | "other";

interface RawHoldingRow {
  nameOfIssuer: string;
  titleOfClass: string;
  cusip: string;
  value: number;
  shares: number;
  sshPrnamtType: string;
  putCall: string | null;
  investmentDiscretion: string;
  instrumentType: InstrumentType;
}

interface AggregatedPosition {
  cusip: string;
  instrumentType: InstrumentType;
  nameOfIssuer: string;
  titleOfClass: string;
  value: number;
  shares: number;
}

interface ManagerFilingData {
  meta: FilingMeta;
  managerName: string;
  periodOfReport: string;
  tableEntryTotal: number;
  tableValueTotal: number;
  rawRowCount: number;
  rawValueSum: number;
  aggregatedRows: AggregatedPosition[];
  reconciliation_ok: boolean;
  reconciliation_note: string;
  filingIndexUrl: string;
  humanIndexUrl: string;
  infoTableUrl: string;
  primaryDocUrl: string;
}

interface ManagerResult {
  manager_key: string;
  fund: string;
  cik: string;
  status: "ok" | "failed";
  latest?: ManagerFilingData;
  prior?: ManagerFilingData;
  prior_available: boolean;
  error?: string;
  stage?: string;
  // Populated ONLY when the latest filing succeeded but the prior-filing fetch/parse
  // failed — distinguishes "no second period exists" from "second period exists but
  // errored", and lets the manager stay `status: "ok"` (usable current holdings) even
  // though Q/Q action data is unavailable for it this run. Never set when the manager
  // itself failed outright (that case uses top-level `error`/`stage` and `status: "failed"`).
  prior_stage?: string;
  prior_error?: string;
}

interface MissingDataEntry {
  manager_key: string;
  fund: string;
  stage: string;
  error: string;
}

interface TickerResolution {
  ticker: string | null;
  resolution: "exact-name-match" | "unresolved-issuer+cusip" | "unavailable";
  label: string;
}

interface ConsolidatedPosition {
  cusip: string;
  instrumentType: InstrumentType;
  nameOfIssuer: string;
  ticker: string | null;
  ticker_resolution: string;
  position_label: string;
  aggregate_value_usd: number;
  aggregate_shares: number;
  aggregate_weight_pct: number;
  funds: { manager_key: string; fund_name: string; value_usd: number; shares: number }[];
}

type Action = "NEW" | "ADD" | "TRIM" | "EXIT";

interface ActionEntry {
  manager_key: string;
  fund_name: string;
  action: Action;
  current_value: number;
  prior_value: number;
  delta_usd: number;
}

interface TopMoveEntry {
  cusip: string;
  instrumentType: InstrumentType;
  nameOfIssuer: string;
  ticker: string | null;
  ticker_resolution: string;
  position_label: string;
  // NOTE: these are NOT the position's total consolidated holding value (see
  // ConsolidatedPosition.aggregate_value_usd for that). They sum ONLY the funds that
  // took a NEW/ADD/TRIM/EXIT action on this position this quarter — funds holding the
  // position UNCHANGED are excluded by definition (see computeActions). Named
  // `acting_funds_*` deliberately so this can never be mistaken for the full
  // cross-fund consolidated total.
  acting_funds_current_value: number;
  acting_funds_prior_value: number;
  delta_usd: number;
  pct_delta: number | "NEW";
  ranking_key: number;
  dominant_action: string;
  contributing_funds: ActionEntry[];
}

// ── Small generic helpers ───────────────────────────────────────────────────────

const sleep = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

function unescapeXml(s: string): string {
  return s
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&apos;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/&amp;/g, "&");
}

/** Extracts the raw (still-escaped) inner text of the first `<tag>` or `<ns:tag>` match. */
function extractTagRaw(xml: string, tag: string): string | null {
  const re = new RegExp(`<(?:\\w+:)?${tag}(?:\\s[^>]*)?>([\\s\\S]*?)<\\/(?:\\w+:)?${tag}>`, "i");
  const m = xml.match(re);
  return m ? m[1] : null;
}

/** Extracts + unescapes + trims the inner text of the first `<tag>` or `<ns:tag>` match. */
function extractTagText(xml: string, tag: string): string | null {
  const raw = extractTagRaw(xml, tag);
  return raw !== null ? unescapeXml(raw.trim()) : null;
}

/** Extracts the raw inner content of every repeating `<tag>...</tag>` (or namespaced) block. */
function extractBlocks(xml: string, tag: string): string[] {
  const re = new RegExp(`<(?:\\w+:)?${tag}(?:\\s[^>]*)?>([\\s\\S]*?)<\\/(?:\\w+:)?${tag}>`, "gi");
  const blocks: string[] = [];
  let m: RegExpExecArray | null;
  while ((m = re.exec(xml)) !== null) {
    blocks.push(m[1]);
  }
  return blocks;
}

function normalizeTitle(s: string): string {
  let t = s.toUpperCase();
  t = t.replace(/[.,]/g, "");
  t = t.replace(/^THE\s+/, "");
  const suffixes = ["INCORPORATED", "INC", "CORPORATION", "CORP", "COMPANY", "CO", "LIMITED", "LTD", "LLC", "LP", "PLC"];
  let changed = true;
  while (changed) {
    changed = false;
    for (const suf of suffixes) {
      const re = new RegExp(`\\s+${suf}$`);
      if (re.test(t)) {
        t = t.replace(re, "");
        changed = true;
      }
    }
  }
  t = t.replace(/[^A-Z0-9\s]/g, " ");
  t = t.replace(/\s+/g, " ").trim();
  return t;
}

function formatUsd(n: number): string {
  return `$${Math.round(n).toLocaleString("en-US")}`;
}

function formatPct(n: number): string {
  return `${n >= 0 ? "+" : ""}${n.toFixed(1)}%`;
}

function formatDelta(n: number | "NEW"): string {
  if (n === "NEW") return "NEW";
  return formatPct(n);
}

// ── HTTP helpers ─────────────────────────────────────────────────────────────

async function fetchWithUA(url: string, ua: string, accept: string): Promise<Response> {
  const doFetch = () => fetch(url, { headers: { "User-Agent": ua, Accept: accept } });
  let res = await doFetch();
  if (res.status === 429 || res.status === 503) {
    await sleep(2000);
    res = await doFetch();
  }
  return res;
}

async function fetchJson(url: string, ua: string): Promise<any> {
  const res = await fetchWithUA(url, ua, "application/json");
  if (!res.ok) throw new Error(`HTTP ${res.status} fetching ${url}`);
  return res.json();
}

async function fetchText(url: string, ua: string): Promise<string> {
  const res = await fetchWithUA(url, ua, "application/xml,text/xml,*/*");
  if (!res.ok) throw new Error(`HTTP ${res.status} fetching ${url}`);
  return res.text();
}

// ── SEC filing discovery ─────────────────────────────────────────────────────

function extract13FPeriods(subsRecent: any): FilingMeta[] {
  const map = new Map<string, FilingMeta>();
  if (subsRecent && Array.isArray(subsRecent.form)) {
    for (let i = 0; i < subsRecent.form.length; i++) {
      const form = subsRecent.form[i];
      if (form === "13F-HR" || form === "13F-HR/A") {
        const reportDate = subsRecent.reportDate[i];
        const filingDate = subsRecent.filingDate[i];
        const existing = map.get(reportDate);
        if (!existing || filingDate > existing.filingDate) {
          map.set(reportDate, {
            form,
            filingDate,
            reportDate,
            accessionNumber: subsRecent.accessionNumber[i],
            primaryDocument: subsRecent.primaryDocument[i],
          });
        }
      }
    }
  }
  const periods = Array.from(map.values());
  periods.sort((a, b) => b.reportDate.localeCompare(a.reportDate));
  return periods;
}

async function ensureTwoPeriods(
  subs: any,
  ua: string,
  sources: Set<string>,
  warnings: string[],
  key: string
): Promise<FilingMeta[]> {
  let periods = extract13FPeriods(subs?.filings?.recent);
  if (periods.length >= 2) return periods;

  warnings.push(
    `${key}: fewer than 2 distinct 13F-HR periods found in filings.recent — checking filings.files[] pagination fallback`
  );
  const files: { name: string }[] = subs?.filings?.files || [];
  for (const f of files) {
    if (periods.length >= 2) break;
    try {
      const url = `https://data.sec.gov/submissions/${f.name}`;
      sources.add(url);
      const extra = await fetchJson(url, ua);
      await sleep(SEC_DELAY_MS);
      const morePeriods = extract13FPeriods(extra);
      for (const p of morePeriods) {
        if (!periods.find((pp) => pp.reportDate === p.reportDate)) periods.push(p);
      }
      periods.sort((a, b) => b.reportDate.localeCompare(a.reportDate));
    } catch (e: any) {
      warnings.push(`${key}: failed to fetch fallback filings file ${f.name}: ${e?.message ?? e}`);
    }
  }
  if (periods.length < 2) {
    warnings.push(`${key}: still fewer than 2 distinct 13F-HR periods found after fallback check`);
  }
  return periods;
}

// ── Instrument classification ───────────────────────────────────────────────

function classifyInstrumentType(titleOfClass: string, putCall: string | null): InstrumentType {
  if (putCall) {
    const pc = putCall.trim().toLowerCase();
    if (pc === "call") return "call option";
    if (pc === "put") return "put option";
  }
  const t = titleOfClass.trim().toUpperCase();
  if (t.includes("COM") || t.includes("ORD") || t === "SH" || t === "SHS" || t === "STK") return "common/share";
  return "other";
}

// ── XML document parsing ────────────────────────────────────────────────────

function parsePrimaryDoc(xml: string): {
  managerName: string;
  tableEntryTotal: number;
  tableValueTotal: number;
  periodOfReport: string;
} {
  const filingManagerBlock = extractTagRaw(xml, "filingManager") ?? "";
  const managerName = extractTagText(filingManagerBlock, "name") ?? "";
  const summaryBlock = extractTagRaw(xml, "summaryPage") ?? "";
  const tableEntryTotal = parseInt(extractTagText(summaryBlock, "tableEntryTotal") ?? "0", 10) || 0;
  const tableValueTotal = parseFloat(extractTagText(summaryBlock, "tableValueTotal") ?? "0") || 0;
  const filerInfoBlock = extractTagRaw(xml, "filerInfo") ?? "";
  const periodOfReport = extractTagText(filerInfoBlock, "periodOfReport") ?? "";
  return { managerName, tableEntryTotal, tableValueTotal, periodOfReport };
}

function parseInfoTable(xml: string): RawHoldingRow[] {
  const blocks = extractBlocks(xml, "infoTable");
  const rows: RawHoldingRow[] = [];
  for (const block of blocks) {
    const nameOfIssuer = extractTagText(block, "nameOfIssuer") ?? "";
    const titleOfClass = extractTagText(block, "titleOfClass") ?? "";
    const cusip = extractTagText(block, "cusip") ?? "";
    const valueRaw = extractTagText(block, "value");
    const value = valueRaw ? parseFloat(valueRaw) : 0;
    const sshPrnamtRaw = extractTagText(block, "sshPrnamt");
    const shares = sshPrnamtRaw ? parseFloat(sshPrnamtRaw) : 0;
    const sshPrnamtType = extractTagText(block, "sshPrnamtType") ?? "";
    const putCall = extractTagText(block, "putCall");
    const investmentDiscretion = extractTagText(block, "investmentDiscretion") ?? "";
    const instrumentType = classifyInstrumentType(titleOfClass, putCall);
    if (!cusip) continue; // malformed row guard — never crash on a bad row, just skip
    rows.push({
      nameOfIssuer,
      titleOfClass,
      cusip,
      value,
      shares,
      sshPrnamtType,
      putCall,
      investmentDiscretion,
      instrumentType,
    });
  }
  return rows;
}

// ── Per-manager fetch + parse pipeline ──────────────────────────────────────

async function fetchAndParseFiling(
  cikNoLeading: string,
  period: FilingMeta,
  ua: string,
  sources: Set<string>,
  warnings: string[],
  key: string
): Promise<ManagerFilingData> {
  const accessionNoDashes = period.accessionNumber.replace(/-/g, "");
  const indexUrl = `https://www.sec.gov/Archives/edgar/data/${cikNoLeading}/${accessionNoDashes}/index.json`;
  // Human-browsable filing index page (SEC serves this as `{accession-with-dashes}-index.html`
  // alongside index.json in the same directory) — used only for the report's clickable link,
  // never fetched by this script (index.json is the machine-readable source actually fetched).
  const humanIndexUrl = `https://www.sec.gov/Archives/edgar/data/${cikNoLeading}/${accessionNoDashes}/${period.accessionNumber}-index.html`;
  sources.add(indexUrl);
  const indexJson = await fetchJson(indexUrl, ua);
  await sleep(SEC_DELAY_MS);

  const items: { name: string; size?: string }[] = indexJson?.directory?.item ?? [];
  const xmlFiles = items.filter((i) => /\.xml$/i.test(i.name));
  const nonPrimary = xmlFiles.filter((i) => i.name.toLowerCase() !== "primary_doc.xml");
  if (nonPrimary.length === 0) {
    throw new Error(`No information-table XML found in filing directory ${indexUrl}`);
  }
  nonPrimary.sort((a, b) => (parseInt(b.size || "0", 10) || 0) - (parseInt(a.size || "0", 10) || 0));
  const infoTableFile = nonPrimary[0].name;
  const primaryDocFile = xmlFiles.find((i) => i.name.toLowerCase() === "primary_doc.xml")?.name ?? "primary_doc.xml";

  const baseUrl = `https://www.sec.gov/Archives/edgar/data/${cikNoLeading}/${accessionNoDashes}`;
  const infoTableUrl = `${baseUrl}/${infoTableFile}`;
  const primaryDocUrl = `${baseUrl}/${primaryDocFile}`;
  sources.add(infoTableUrl);
  sources.add(primaryDocUrl);

  const primaryXml = await fetchText(primaryDocUrl, ua);
  await sleep(SEC_DELAY_MS);
  const infoXml = await fetchText(infoTableUrl, ua);
  await sleep(SEC_DELAY_MS);

  const primaryParsed = parsePrimaryDoc(primaryXml);
  const rawRows = parseInfoTable(infoXml);
  if (rawRows.length === 0) {
    throw new Error(`Parsed 0 infoTable rows from ${infoTableUrl} — parser likely failed on this filer's XML shape`);
  }

  for (const row of rawRows) {
    if (row.sshPrnamtType === "SH" && row.shares > 0) {
      const impliedPrice = row.value / row.shares;
      // Upper bound set above BRK.A (~$700-800k/share, a real, frequently-held security)
      // to avoid a recurring false-positive warning on a legitimate holding.
      if (impliedPrice < 0.01 || impliedPrice > 2000000) {
        warnings.push(
          `${key} (${period.reportDate}): implausible per-share price ($${impliedPrice.toFixed(2)}) for ` +
            `"${row.nameOfIssuer}" (CUSIP ${row.cusip}) — verify units`
        );
      }
    }
  }

  const rawValueSum = rawRows.reduce((s, r) => s + r.value, 0);
  const rawRowCount = rawRows.length;

  const aggMap = new Map<string, AggregatedPosition>();
  for (const row of rawRows) {
    const k = `${row.cusip}|${row.instrumentType}`;
    const existing = aggMap.get(k);
    if (existing) {
      existing.value += row.value;
      existing.shares += row.shares;
    } else {
      aggMap.set(k, {
        cusip: row.cusip,
        instrumentType: row.instrumentType,
        nameOfIssuer: row.nameOfIssuer,
        titleOfClass: row.titleOfClass,
        value: row.value,
        shares: row.shares,
      });
    }
  }
  const aggregatedRows = Array.from(aggMap.values());

  const entryTolOk = Math.abs(rawRowCount - primaryParsed.tableEntryTotal) <= 1;
  const valueTolOk =
    primaryParsed.tableValueTotal > 0
      ? Math.abs(rawValueSum - primaryParsed.tableValueTotal) / primaryParsed.tableValueTotal <= 0.005
      : true;
  const reconciliation_ok = entryTolOk && valueTolOk;
  const reconciliation_note = `computed ${rawRowCount} rows / ${formatUsd(rawValueSum)} vs filer summary ${primaryParsed.tableEntryTotal} rows / ${formatUsd(primaryParsed.tableValueTotal)}`;
  if (!reconciliation_ok) {
    warnings.push(`${key} (${period.reportDate}): reconciliation MISMATCH — ${reconciliation_note}`);
  }

  return {
    meta: period,
    managerName: primaryParsed.managerName,
    periodOfReport: primaryParsed.periodOfReport,
    tableEntryTotal: primaryParsed.tableEntryTotal,
    tableValueTotal: primaryParsed.tableValueTotal,
    rawRowCount,
    rawValueSum,
    aggregatedRows,
    reconciliation_ok,
    reconciliation_note,
    filingIndexUrl: indexUrl,
    humanIndexUrl,
    infoTableUrl,
    primaryDocUrl,
  };
}

async function processManager(
  key: string,
  entry: RosterEntry,
  ua: string,
  warnings: string[],
  sources: Set<string>,
  missingData: MissingDataEntry[]
): Promise<ManagerResult> {
  const cikPadded = String(entry.cik).padStart(10, "0");
  const cikNoLeading = String(parseInt(cikPadded, 10));
  let stage = "init";
  let latest: ManagerFilingData;
  try {
    stage = "fetch-submissions";
    const subsUrl = `https://data.sec.gov/submissions/CIK${cikPadded}.json`;
    sources.add(subsUrl);
    const subs = await fetchJson(subsUrl, ua);
    await sleep(SEC_DELAY_MS);

    stage = "find-13F-HR-periods";
    const periods = await ensureTwoPeriods(subs, ua, sources, warnings, key);
    if (periods.length === 0) {
      throw new Error("No 13F-HR / 13F-HR/A filings found for this CIK");
    }

    stage = "fetch-latest-filing";
    latest = await fetchAndParseFiling(cikNoLeading, periods[0], ua, sources, warnings, key);

    // ── Latest filing fetch/parse/reconciliation succeeded — the manager is now a usable
    // current-holdings result no matter what happens below. The prior (Q/Q comparison)
    // filing is fetched in its OWN try/catch so a failure there never discards `latest`:
    // it only disables this manager's contribution to Top Buys/Sells (computeActions
    // already requires `prior_available` before using a manager), while `latest` keeps
    // the manager in consolidated current positions and the pie chart via `buildConsolidated`.
    let prior: ManagerFilingData | undefined;
    let priorAvailable = false;
    let priorStage: string | undefined;
    let priorError: string | undefined;

    if (periods.length >= 2) {
      try {
        prior = await fetchAndParseFiling(cikNoLeading, periods[1], ua, sources, warnings, key);
        priorAvailable = true;
      } catch (e: any) {
        priorStage = "fetch-prior-filing";
        priorError = e?.message ?? String(e);
        warnings.push(
          `${key}: prior-filing fetch/parse FAILED at stage="${priorStage}" (${priorError}) — Q/Q action data ` +
            `(NEW/ADD/TRIM/EXIT) is UNAVAILABLE for this manager this run. Current holdings from the latest ` +
            `filing remain included in Consolidated Current Holdings and the pie chart; no buy/sell action is ` +
            `reported for this manager (never inferred without a real prior filing).`
        );
        console.error(`[QOQ-UNAVAILABLE] ${key} (${entry.fund}) at stage="${priorStage}": ${priorError}`);
      }
    } else {
      warnings.push(`${key}: only one distinct 13F-HR period found — QoQ comparison unavailable (no prior data)`);
    }

    return {
      manager_key: key,
      fund: entry.fund,
      cik: cikPadded,
      status: "ok",
      latest,
      prior,
      prior_available: priorAvailable,
      prior_stage: priorStage,
      prior_error: priorError,
    };
  } catch (e: any) {
    const errMsg = e?.message ?? String(e);
    missingData.push({ manager_key: key, fund: entry.fund, stage, error: errMsg });
    console.error(`[FAILED] ${key} (${entry.fund}) at stage="${stage}": ${errMsg}`);
    return {
      manager_key: key,
      fund: entry.fund,
      cik: cikPadded,
      status: "failed",
      prior_available: false,
      error: errMsg,
      stage,
    };
  }
}

// ── Ticker resolution ────────────────────────────────────────────────────────

async function buildTickerIndex(
  ua: string,
  sources: Set<string>,
  warnings: string[]
): Promise<Map<string, Set<string>> | null> {
  try {
    const url = "https://www.sec.gov/files/company_tickers.json";
    sources.add(url);
    const data = await fetchJson(url, ua);
    const idx = new Map<string, Set<string>>();
    for (const k of Object.keys(data)) {
      const entry = data[k];
      if (!entry?.title || !entry?.ticker) continue;
      const norm = normalizeTitle(entry.title);
      if (!idx.has(norm)) idx.set(norm, new Set());
      idx.get(norm)!.add(entry.ticker);
    }
    return idx;
  } catch (e: any) {
    warnings.push(`Ticker resolution unavailable this run — company_tickers.json fetch failed: ${e?.message ?? e}`);
    return null;
  }
}

function resolveTicker(
  idx: Map<string, Set<string>> | null,
  nameOfIssuer: string,
  cusip: string
): TickerResolution {
  // Some filers (e.g. Millennium) embed literal repeated spaces inside XML text nodes
  // (e.g. "1   800  FLOWERS    COM    INC") — collapse for a readable display label.
  // This does NOT affect the normalized matching key used for ticker resolution.
  const fallbackLabel = `${nameOfIssuer.replace(/\s+/g, " ").trim()} (CUSIP ${cusip})`;
  if (!idx) return { ticker: null, resolution: "unavailable", label: fallbackLabel };
  const norm = normalizeTitle(nameOfIssuer);
  const matches = idx.get(norm);
  if (matches && matches.size === 1) {
    const ticker = Array.from(matches)[0];
    return { ticker, resolution: "exact-name-match", label: ticker };
  }
  return { ticker: null, resolution: "unresolved-issuer+cusip", label: fallbackLabel };
}

// ── Cross-manager aggregation ────────────────────────────────────────────────

function buildConsolidated(
  okResults: ManagerResult[],
  tickerIdx: Map<string, Set<string>> | null
): ConsolidatedPosition[] {
  const map = new Map<string, ConsolidatedPosition>();
  for (const mr of okResults) {
    if (!mr.latest) continue;
    for (const row of mr.latest.aggregatedRows) {
      const k = `${row.cusip}|${row.instrumentType}`;
      let pos = map.get(k);
      if (!pos) {
        const resolved = resolveTicker(tickerIdx, row.nameOfIssuer, row.cusip);
        pos = {
          cusip: row.cusip,
          instrumentType: row.instrumentType,
          nameOfIssuer: row.nameOfIssuer,
          ticker: resolved.ticker,
          ticker_resolution: resolved.resolution,
          position_label: resolved.label,
          aggregate_value_usd: 0,
          aggregate_shares: 0,
          aggregate_weight_pct: 0,
          funds: [],
        };
        map.set(k, pos);
      }
      pos.aggregate_value_usd += row.value;
      pos.aggregate_shares += row.shares;
      pos.funds.push({ manager_key: mr.manager_key, fund_name: mr.fund, value_usd: row.value, shares: row.shares });
    }
  }
  const positions = Array.from(map.values());
  const total = positions.reduce((s, p) => s + p.aggregate_value_usd, 0);
  for (const p of positions) p.aggregate_weight_pct = total > 0 ? (p.aggregate_value_usd / total) * 100 : 0;
  positions.sort((a, b) => b.aggregate_value_usd - a.aggregate_value_usd);
  return positions;
}

function computeActions(
  okResults: ManagerResult[],
  tickerIdx: Map<string, Set<string>> | null
): { buys: TopMoveEntry[]; sells: TopMoveEntry[] } {
  const buyMap = new Map<string, TopMoveEntry>();
  const sellMap = new Map<string, TopMoveEntry>();

  for (const mr of okResults) {
    if (!mr.prior_available || !mr.latest || !mr.prior) continue;
    const currentMap = new Map(mr.latest.aggregatedRows.map((r) => [`${r.cusip}|${r.instrumentType}`, r]));
    const priorMap = new Map(mr.prior.aggregatedRows.map((r) => [`${r.cusip}|${r.instrumentType}`, r]));
    const allKeys = new Set([...currentMap.keys(), ...priorMap.keys()]);

    for (const k of allKeys) {
      const cur = currentMap.get(k);
      const pri = priorMap.get(k);
      const curVal = cur?.value ?? 0;
      const priVal = pri?.value ?? 0;

      let action: Action | "UNCHANGED";
      if (curVal > 0 && priVal <= 0) action = "NEW";
      else if (curVal > 0 && priVal > 0) {
        if (curVal > priVal * (1 + ACTION_TOLERANCE)) action = "ADD";
        else if (curVal < priVal * (1 - ACTION_TOLERANCE)) action = "TRIM";
        else action = "UNCHANGED";
      } else if (curVal <= 0 && priVal > 0) action = "EXIT";
      else continue; // both zero/absent — nothing to report

      if (action === "UNCHANGED") continue;

      const delta = curVal - priVal;
      const refRow = cur ?? pri!;
      const actionEntry: ActionEntry = {
        manager_key: mr.manager_key,
        fund_name: mr.fund,
        action,
        current_value: curVal,
        prior_value: priVal,
        delta_usd: delta,
      };

      const targetMap = action === "NEW" || action === "ADD" ? buyMap : sellMap;
      let entry = targetMap.get(k);
      if (!entry) {
        const resolved = resolveTicker(tickerIdx, refRow.nameOfIssuer, refRow.cusip);
        entry = {
          cusip: refRow.cusip,
          instrumentType: refRow.instrumentType,
          nameOfIssuer: refRow.nameOfIssuer,
          ticker: resolved.ticker,
          ticker_resolution: resolved.resolution,
          position_label: resolved.label,
          acting_funds_current_value: 0,
          acting_funds_prior_value: 0,
          delta_usd: 0,
          pct_delta: 0,
          ranking_key: 0,
          dominant_action: "",
          contributing_funds: [],
        };
        targetMap.set(k, entry);
      }
      entry.acting_funds_current_value += curVal;
      entry.acting_funds_prior_value += priVal;
      entry.delta_usd += delta;
      entry.ranking_key += Math.abs(delta);
      entry.contributing_funds.push(actionEntry);
    }
  }

  for (const entry of buyMap.values()) {
    entry.pct_delta = entry.acting_funds_prior_value <= 0 ? "NEW" : ((entry.acting_funds_current_value - entry.acting_funds_prior_value) / entry.acting_funds_prior_value) * 100;
    const actions = new Set(entry.contributing_funds.map((f) => f.action));
    entry.dominant_action = actions.size === 1 ? Array.from(actions)[0] : Array.from(actions).sort().join("+");
  }
  for (const entry of sellMap.values()) {
    entry.pct_delta = entry.acting_funds_current_value <= 0 ? -100 : ((entry.acting_funds_current_value - entry.acting_funds_prior_value) / entry.acting_funds_prior_value) * 100;
    const actions = new Set(entry.contributing_funds.map((f) => f.action));
    entry.dominant_action = actions.size === 1 ? Array.from(actions)[0] : Array.from(actions).sort().join("+");
  }

  const buys = Array.from(buyMap.values()).sort((a, b) => b.ranking_key - a.ranking_key);
  const sells = Array.from(sellMap.values()).sort((a, b) => b.ranking_key - a.ranking_key);
  return { buys, sells };
}

// ── SVG pie chart (hand-written, zero deps) ─────────────────────────────────

function polarToCartesian(cx: number, cy: number, r: number, angleDeg: number) {
  const rad = ((angleDeg - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

function arcPath(cx: number, cy: number, r: number, startAngle: number, endAngle: number): string {
  const startPt = polarToCartesian(cx, cy, r, startAngle);
  const endPt = polarToCartesian(cx, cy, r, endAngle);
  const largeArc = endAngle - startAngle > 180 ? 1 : 0;
  return `M ${cx},${cy} L ${startPt.x.toFixed(2)},${startPt.y.toFixed(2)} A ${r},${r} 0 ${largeArc} 1 ${endPt.x.toFixed(2)},${endPt.y.toFixed(2)} Z`;
}

function escapeXmlText(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function buildPieSvg(
  slices: { label: string; value: number; pct: number }[],
  reportDate: string,
  managerCount: number
): string {
  const cx = 260;
  const cy = 280;
  const r = 200;

  // Legend geometry — kept dynamic so an exaggerated `--top` (many pie slices) can never
  // clip a legend row off the bottom of the canvas. Rows are capped per column at
  // LEGEND_MAX_ROWS_PER_COLUMN; once a single column would exceed that, the legend wraps
  // into additional columns (extending width) instead of an unbounded single column
  // (extending height indefinitely) or a fixed canvas that truncates rows.
  const LEGEND_X = 540;
  const LEGEND_TOP = 40;
  const LEGEND_ROW_HEIGHT = 24;
  const LEGEND_BOTTOM_PAD = 20;
  const LEGEND_COL_WIDTH = 260;
  const LEGEND_MAX_ROWS_PER_COLUMN = 25;

  const sliceCount = slices.length;
  const legendColumns = Math.max(1, Math.ceil(sliceCount / LEGEND_MAX_ROWS_PER_COLUMN));
  const rowsPerColumn = legendColumns > 0 ? Math.ceil(sliceCount / legendColumns) : 0;

  const width = LEGEND_X + legendColumns * LEGEND_COL_WIDTH;
  const pieBottom = cy + r + 40;
  const legendBottom = LEGEND_TOP + rowsPerColumn * LEGEND_ROW_HEIGHT + LEGEND_BOTTOM_PAD;
  const height = Math.max(pieBottom, legendBottom);

  let cumulativeAngle = 0;
  const paths: string[] = [];
  const legendItems: string[] = [];

  slices.forEach((slice, i) => {
    const angle = slice.pct * 3.6; // pct of 100 -> degrees
    const color = PIE_PALETTE[i % PIE_PALETTE.length];
    if (slices.length === 1) {
      // Full circle — arc path degenerates, draw as circle instead.
      paths.push(`<circle cx="${cx}" cy="${cy}" r="${r}" fill="${color}" stroke="#fff" stroke-width="1"/>`);
    } else if (angle > 0) {
      const path = arcPath(cx, cy, r, cumulativeAngle, cumulativeAngle + angle);
      paths.push(`<path d="${path}" fill="${color}" stroke="#fff" stroke-width="1"/>`);
    }
    cumulativeAngle += angle;

    const col = Math.floor(i / rowsPerColumn);
    const rowInCol = i % rowsPerColumn;
    const itemX = LEGEND_X + col * LEGEND_COL_WIDTH;
    const legendY = LEGEND_TOP + rowInCol * LEGEND_ROW_HEIGHT;
    legendItems.push(
      `<rect x="${itemX}" y="${legendY - 12}" width="14" height="14" fill="${color}"/>` +
        `<text x="${itemX + 20}" y="${legendY}" font-family="Arial, sans-serif" font-size="12" fill="#222">` +
        `${escapeXmlText(slice.label)} — ${slice.pct.toFixed(1)}%</text>`
    );
  });

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  <title>Top-5 AUM institutional-flow managers — consolidated common/share holdings (${reportDate})</title>
  <desc>Pie chart of aggregate CURRENT common/share holdings only (excludes call/put/other instrument types) across ${managerCount} managers. Percentages are relative to the common-share-only total and sum to 100% within this chart — they are NOT relative to the combined common+options total used elsewhere in the report.</desc>
  <rect width="${width}" height="${height}" fill="#ffffff"/>
  <text x="20" y="24" font-family="Arial, sans-serif" font-size="15" font-weight="bold" fill="#111">Top holdings — common/share only (${reportDate})</text>
  <text x="20" y="42" font-family="Arial, sans-serif" font-size="11" fill="#555">% of common-only aggregate value across ${managerCount} managers. Excludes call/put/other instrument types.</text>
  ${paths.join("\n  ")}
  ${legendItems.join("\n  ")}
</svg>
`;
}

// ── CLI parsing ──────────────────────────────────────────────────────────────

function parseArgs(argv: string[]): { args: Record<string, string>; help: boolean } {
  const args: Record<string, string> = {};
  let help = false;
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--help" || a === "-h") {
      help = true;
      continue;
    }
    if (a.startsWith("--")) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next !== undefined && !next.startsWith("--")) {
        args[key] = next;
        i++;
      } else {
        args[key] = "true";
      }
    }
  }
  return { args, help };
}

function printHelp(): void {
  console.log(`top5-13f-report.ts — Top-5 AUM institutional-flow 13F aggregation report

Usage:
  bun .agents/skills/analyse-smartmoney-13f/scripts/top5-13f-report.ts [flags]

Flags:
  --roster <path>       Roster JSON path, relative to repo root.
                         Default: .cache/analyst-smartmoney-13f/roster.json
  --managers k1,k2,...   Explicit roster keys (overrides default bucket/universe filter).
  --universe <tag>       Universe tag filter for default manager selection. Default: top5-aum
  --out-dir <dir>        Output directory, relative to repo root. Default: research
  --top <n>              Row/slice cap for Top Buys/Sells tables and pie chart. Default: 10
  --date <YYYY-MM-DD>    Overrides report filename/"as of" timestamp only — does NOT change
                         which SEC filings are fetched (always the real latest/prior).
  --user-agent <string>  Custom SEC EDGAR User-Agent header.
  --help                 Print this usage and exit 0.
`);
}

// ── Report builders ──────────────────────────────────────────────────────────

const OPTIONS_CAVEAT =
  "Options (PUT/CALL) values reported on Form 13F represent the market value of the UNDERLYING shares " +
  "(notional), not the option contract's own market value/premium — do not use reported option 'value' to " +
  "infer position size, risk, or directional exposure. A PUT position is a bearish/hedging signal on the " +
  "underlying and must never be read as a bullish stock call; a CALL position must never be read as " +
  "equivalent to owning the same dollar amount of common stock.";

const UNITS_CAVEAT =
  "Per SEC Form 13F rule amendment effective for filings after Jan 2023 (Release No. 34-95064), reported " +
  "<value> figures are in WHOLE U.S. DOLLARS, not thousands (the pre-2023 convention).";

const LAG_CAVEAT =
  "Form 13F filings have a 45-day filing lag after quarter-end — holdings reflect stale positions, not " +
  "real-time exposure.";

const SCOPE_CAVEAT =
  "Form 13F only covers US-exchange-listed equity securities (and certain equity options) — it excludes " +
  "non-US securities, most fixed income, cash, and short positions. This report reflects a long-only, " +
  "US-equity-listed slice of each manager's actual book.";

const ACTING_FUNDS_CAVEAT =
  "'Acting-Funds Current/Prior Value' below sum ONLY the funds that took a NEW/ADD/TRIM/EXIT action on that " +
  "position this quarter — funds holding the position UNCHANGED are excluded by definition. This is NOT the " +
  "position's total consolidated holding value across all funds; see the Aggregate Value column in " +
  "Consolidated Current Holdings above for that full cross-fund total.";

function buildMarkdownReport(ctx: {
  reportDate: string;
  generatedAt: string;
  managerKeys: string[];
  roster: Roster;
  managerResults: ManagerResult[];
  consolidated: ConsolidatedPosition[];
  topBuys: TopMoveEntry[];
  topSells: TopMoveEntry[];
  topN: number;
  svgFilename: string;
  pieCommonTotal: number;
  warnings: string[];
  missingData: MissingDataEntry[];
  sources: Set<string>;
  status: string;
}): string {
  const {
    reportDate,
    generatedAt,
    managerKeys,
    roster,
    managerResults,
    consolidated,
    topBuys,
    topSells,
    topN,
    svgFilename,
    pieCommonTotal,
    warnings,
    missingData,
    sources,
    status,
  } = ctx;

  const lines: string[] = [];

  if (status === "failed") {
    lines.push("# ❌ NO DATA — SEC EDGAR FETCH FAILED FOR ALL MANAGERS", "");
  }

  lines.push(`# Top-5 AUM Institutional-Flow Managers — 13F Holdings Report`);
  lines.push("");
  lines.push(`**Report date:** ${reportDate}  `);
  lines.push(
    `**Universe (${managerKeys.length} funds):** ${managerKeys
      .map((k) => `${(roster[k] as RosterEntry).fund} (CIK ${(roster[k] as RosterEntry).cik})`)
      .join("; ")}  `
  );
  lines.push(`**Generated at:** ${generatedAt}  `);
  lines.push(`**Status:** ${status}`);
  lines.push("");
  lines.push(
    "> Educational analysis only — not financial advice. This report aggregates PUBLIC SEC Form 13F filings; " +
      "it is not a recommendation and does not constitute a signal from any single manager."
  );
  lines.push("");

  // ── Data Sources & Provenance ──────────────────────────────────────────
  lines.push("## Data Sources & Provenance");
  lines.push("");
  lines.push(
    "Primary source: SEC EDGAR (data.sec.gov / www.sec.gov/Archives) — no third-party aggregator used. " +
      `${UNITS_CAVEAT}`
  );
  lines.push("");
  for (const mr of managerResults) {
    lines.push(`### ${mr.fund} (CIK ${mr.cik})`);
    if (mr.status !== "ok") {
      lines.push("");
      lines.push(`❌ **FETCH FAILED** at stage \`${mr.stage}\`: ${mr.error}`);
      lines.push("");
      continue;
    }
    const l = mr.latest!;
    lines.push("");
    lines.push(
      `- **Latest filing:** accession \`${l.meta.accessionNumber}\`, report period ${l.meta.reportDate}, filed ${l.meta.filingDate} — ` +
        `[filing index](${l.humanIndexUrl})`
    );
    lines.push(
      `  - Reconciliation: ${l.reconciliation_ok ? "✅ OK" : "⚠️ MISMATCH"} — ${l.reconciliation_note}`
    );
    if (mr.prior_available && mr.prior) {
      const p = mr.prior;
      lines.push(
        `- **Prior filing:** accession \`${p.meta.accessionNumber}\`, report period ${p.meta.reportDate}, filed ${p.meta.filingDate} — ` +
          `[filing index](${p.humanIndexUrl})`
      );
      lines.push(`  - Reconciliation: ${p.reconciliation_ok ? "✅ OK" : "⚠️ MISMATCH"} — ${p.reconciliation_note}`);
    } else if (mr.prior_stage) {
      // Latest filing succeeded (this manager is `status: "ok"` and IS in Consolidated
      // Current Holdings / the pie chart above) but the prior filing itself errored out —
      // distinct from "no second period exists". Q/Q action data is unavailable, never
      // fabricated.
      lines.push(
        `- **Prior filing:** ⚠️ **UNAVAILABLE — fetch/parse FAILED** at stage \`${mr.prior_stage}\`: ${mr.prior_error}. ` +
          `Q/Q action data (NEW/ADD/TRIM/EXIT) is unavailable for this manager this run — current holdings above ` +
          `remain included in Consolidated Current Holdings and the pie chart.`
      );
    } else {
      lines.push(`- **Prior filing:** unavailable — no second distinct 13F-HR period found for this manager`);
    }
    lines.push("");
  }

  // ── Methodology ────────────────────────────────────────────────────────
  lines.push("## Methodology");
  lines.push("");
  lines.push("**Instrument-type classification** (applied per raw `<infoTable>` row before aggregation):");
  lines.push("");
  lines.push('- `<putCall>` present, "Call" (case-insensitive) → `call option`');
  lines.push('- `<putCall>` present, "Put" (case-insensitive) → `put option`');
  lines.push(
    '- else `<titleOfClass>` (case-insensitive, trimmed) contains "COM" or "ORD", or equals "SH"/"SHS"/"STK" → `common/share`'
  );
  lines.push("- else → `other` (preferred stock, notes, units, warrants — never misclassified as common)");
  lines.push("");
  lines.push("**Quarter-over-quarter action definitions** (per manager, on the `(cusip, instrumentType)` key):");
  lines.push("");
  lines.push(
    "- `NEW` = present in current filing for a manager (aggregated value > 0), absent/zero in that manager's prior filing."
  );
  lines.push("- `ADD` = present in both, current > prior (beyond 1% tolerance).");
  lines.push("- `TRIM` = present in both, current < prior (beyond 1% tolerance), current still > 0.");
  lines.push("- `EXIT` = present (>0) in manager's PRIOR filing, absent/zero in CURRENT filing.");
  lines.push(
    "- `UNCHANGED` = present in both, change within tolerance (<1%) — excluded from Top Buys/Sells, not reported as an action."
  );
  lines.push(
    "- Top Buys ranking key = aggregate cross-fund positive dollar delta (sum of NEW+ADD deltas). " +
      "Top Sells ranking key = aggregate cross-fund negative dollar magnitude (sum of |TRIM delta| + |EXIT prior value|); " +
      "TRIM and EXIT are always shown as distinct actions per contributing fund, never conflated."
  );
  lines.push("");
  lines.push(
    "**Weight calculation:** `aggregate_weight_pct` = position's aggregate current value ÷ SUM of aggregate value " +
      "across ALL consolidated positions (all instrument types combined) in the current report."
  );
  lines.push("");
  lines.push(
    "**Ticker resolution:** issuer names are matched against SEC's official `company_tickers.json` map after " +
      "normalizing both sides (uppercase; strip trailing corporate suffixes INC/CORP/CO/LTD/LLC/LP/PLC/THE; strip " +
      "punctuation; collapse whitespace). Exactly one match → resolved with `ticker_resolution: exact-name-match`. " +
      "Zero or multiple matches → rendered as `Issuer Name (CUSIP xxxxxxxxx)` with `ticker: null` and " +
      "`ticker_resolution: unresolved-issuer+cusip` — never fuzzy-matched or hardcoded."
  );
  lines.push("");
  lines.push(`> ${OPTIONS_CAVEAT}`);
  lines.push("");
  lines.push(`> ${LAG_CAVEAT}`);
  lines.push("");
  lines.push(`> ${SCOPE_CAVEAT}`);
  lines.push("");

  // ── Consolidated Current Holdings ──────────────────────────────────────
  lines.push("## Consolidated Current Holdings");
  lines.push("");
  const MAX_DISPLAY = 50;
  const displayPositions = consolidated.slice(0, MAX_DISPLAY);
  lines.push("| Position | Instrument Type | Aggregate Value (USD) | Aggregate Weight % | Funds Holding |");
  lines.push("|---|---|---|---|---|");
  for (const p of displayPositions) {
    lines.push(
      `| ${p.position_label} | ${p.instrumentType} | ${formatUsd(p.aggregate_value_usd)} | ${p.aggregate_weight_pct.toFixed(2)}% | ${p.funds
        .map((f) => f.fund_name)
        .join(", ")} |`
    );
  }
  if (consolidated.length > MAX_DISPLAY) {
    lines.push("");
    lines.push(`_${consolidated.length - MAX_DISPLAY} more positions in the JSON sidecar._`);
  }
  lines.push("");

  // ── Top Buys ────────────────────────────────────────────────────────────
  lines.push(`## Top Buys (Q/Q) — top ${topN}`);
  lines.push("");
  lines.push(`> ${ACTING_FUNDS_CAVEAT}`);
  lines.push("");
  if (topBuys.length === 0) {
    lines.push("_No QoQ buy data available (no managers had both a latest and prior filing)._");
  } else {
    lines.push(
      "| Position | Instrument Type | Acting-Funds Current Value | Acting-Funds Prior Value | $ Delta | % Delta | Contributing Funds |"
    );
    lines.push("|---|---|---|---|---|---|---|");
    for (const b of topBuys) {
      const fundsStr = b.contributing_funds
        .map((f) => `${f.fund_name}: ${f.action} (${formatUsd(f.delta_usd)})`)
        .join("; ");
      lines.push(
        `| ${b.position_label} | ${b.instrumentType} | ${formatUsd(b.acting_funds_current_value)} | ${formatUsd(b.acting_funds_prior_value)} | ${formatUsd(b.delta_usd)} | ${formatDelta(b.pct_delta)} | ${fundsStr} |`
      );
    }
  }
  lines.push("");

  // ── Top Sells ───────────────────────────────────────────────────────────
  lines.push(`## Top Sells (Q/Q) — top ${topN}`);
  lines.push("");
  lines.push(`> ${ACTING_FUNDS_CAVEAT}`);
  lines.push("");
  if (topSells.length === 0) {
    lines.push("_No QoQ sell data available (no managers had both a latest and prior filing)._");
  } else {
    lines.push(
      "| Position | Instrument Type | Acting-Funds Current Value | Acting-Funds Prior Value | $ Delta | % Delta | Contributing Funds |"
    );
    lines.push("|---|---|---|---|---|---|---|");
    for (const s of topSells) {
      const fundsStr = s.contributing_funds
        .map((f) => `${f.fund_name}: ${f.action} (${formatUsd(f.delta_usd)})`)
        .join("; ");
      lines.push(
        `| ${s.position_label} | ${s.instrumentType} | ${formatUsd(s.acting_funds_current_value)} | ${formatUsd(s.acting_funds_prior_value)} | ${formatUsd(s.delta_usd)} | ${formatDelta(s.pct_delta)} | ${fundsStr} |`
      );
    }
  }
  lines.push("");

  // ── Pie chart ───────────────────────────────────────────────────────────
  lines.push("## Pie Chart — Top Holdings (common/share only)");
  lines.push("");
  lines.push(
    `Common/share only, top-${topN} + Other, % of common-only total (${formatUsd(pieCommonTotal)}) across ${managerKeys.length} funds, as of ${reportDate}.`
  );
  lines.push("");
  lines.push(`![Top holdings pie chart](./${svgFilename})`);
  lines.push("");

  // ── Missing Data / Warnings ─────────────────────────────────────────────
  lines.push("## Missing Data / Warnings");
  lines.push("");
  if (missingData.length === 0 && warnings.length === 0) {
    lines.push("_None — all managers fetched successfully with no reconciliation issues or fallback flags._");
  } else {
    if (missingData.length > 0) {
      lines.push("**Manager fetch failures:**");
      lines.push("");
      for (const m of missingData) {
        lines.push(`- \`${m.manager_key}\` (${m.fund}) — stage: \`${m.stage}\` — ${m.error}`);
      }
      lines.push("");
    }
    if (warnings.length > 0) {
      lines.push("**Warnings:**");
      lines.push("");
      for (const w of warnings) {
        lines.push(`- ${w}`);
      }
    }
  }
  lines.push("");

  // ── Sources ─────────────────────────────────────────────────────────────
  lines.push("## Sources");
  lines.push("");
  for (const s of Array.from(sources).sort()) {
    lines.push(`- ${s}`);
  }
  lines.push("");

  return lines.join("\n");
}

function buildJsonReport(ctx: {
  reportDate: string;
  generatedAt: string;
  managerKeys: string[];
  roster: Roster;
  universeTag: string;
  managerResults: ManagerResult[];
  consolidated: ConsolidatedPosition[];
  topBuys: TopMoveEntry[];
  topSells: TopMoveEntry[];
  pieSlices: { label: string; value: number; pct: number }[];
  svgPath: string;
  warnings: string[];
  missingData: MissingDataEntry[];
  sources: Set<string>;
  status: string;
}): unknown {
  const meta = (ctx.roster as any)._meta;
  return {
    generated_at: ctx.generatedAt,
    report_date: ctx.reportDate,
    universe: {
      criterion: meta?.top5_aum_selection_criterion ?? null,
      universe_tag: ctx.universeTag,
      managers: ctx.managerKeys.map((k) => ({
        key: k,
        fund: (ctx.roster[k] as RosterEntry).fund,
        cik: (ctx.roster[k] as RosterEntry).cik,
      })),
    },
    managers: ctx.managerResults.map((mr) => ({
      manager_key: mr.manager_key,
      fund: mr.fund,
      cik: mr.cik,
      status: mr.status,
      error: mr.error ?? null,
      stage: mr.stage ?? null,
      latest_filing: mr.latest
        ? {
            accession_number: mr.latest.meta.accessionNumber,
            report_date: mr.latest.meta.reportDate,
            filing_date: mr.latest.meta.filingDate,
            filing_index_url: mr.latest.filingIndexUrl,
            human_index_url: mr.latest.humanIndexUrl,
            info_table_url: mr.latest.infoTableUrl,
            primary_doc_url: mr.latest.primaryDocUrl,
            table_entry_total: mr.latest.tableEntryTotal,
            table_value_total: mr.latest.tableValueTotal,
            computed_row_count: mr.latest.rawRowCount,
            computed_value_sum: mr.latest.rawValueSum,
            reconciliation_ok: mr.latest.reconciliation_ok,
            reconciliation_note: mr.latest.reconciliation_note,
          }
        : null,
      prior_filing:
        mr.prior_available && mr.prior
          ? {
              accession_number: mr.prior.meta.accessionNumber,
              report_date: mr.prior.meta.reportDate,
              filing_date: mr.prior.meta.filingDate,
              filing_index_url: mr.prior.filingIndexUrl,
              human_index_url: mr.prior.humanIndexUrl,
              info_table_url: mr.prior.infoTableUrl,
              primary_doc_url: mr.prior.primaryDocUrl,
              table_entry_total: mr.prior.tableEntryTotal,
              table_value_total: mr.prior.tableValueTotal,
              computed_row_count: mr.prior.rawRowCount,
              computed_value_sum: mr.prior.rawValueSum,
              reconciliation_ok: mr.prior.reconciliation_ok,
              reconciliation_note: mr.prior.reconciliation_note,
            }
          : null,
      prior_available: mr.prior_available,
      // Set only when latest succeeded but the prior (Q/Q) filing fetch/parse itself
      // errored — null when prior_available is true, and also null (not an error) when
      // there simply was no second 13F-HR period for this manager.
      prior_stage: mr.prior_stage ?? null,
      prior_error: mr.prior_error ?? null,
    })),
    consolidated_current: ctx.consolidated,
    top_buys: ctx.topBuys,
    top_sells: ctx.topSells,
    pie_chart: {
      file_path: ctx.svgPath,
      slices: ctx.pieSlices,
    },
    missing_data: ctx.missingData,
    warnings: ctx.warnings,
    caveats: [OPTIONS_CAVEAT, UNITS_CAVEAT, LAG_CAVEAT, SCOPE_CAVEAT, ACTING_FUNDS_CAVEAT],
    sources: Array.from(ctx.sources).sort(),
    status: ctx.status,
  };
}

// ── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  const { args, help } = parseArgs(process.argv.slice(2));
  if (help) {
    printHelp();
    process.exit(0);
  }

  const repoRoot = resolve(import.meta.dir, "..", "..", "..", "..");

  const rosterPath = args["roster"] ? resolve(repoRoot, args["roster"]) : join(repoRoot, ".cache/analyst-smartmoney-13f/roster.json");
  const outDir = args["out-dir"] ? resolve(repoRoot, args["out-dir"]) : join(repoRoot, "research");
  const topN = args["top"] ? parseInt(args["top"], 10) : DEFAULT_TOP_N;
  const reportDate = args["date"] || new Date().toISOString().slice(0, 10);
  const ua = args["user-agent"] || DEFAULT_UA;
  const universeTag = args["universe"] || DEFAULT_UNIVERSE_TAG;

  if (!existsSync(rosterPath)) {
    console.error(`FATAL: roster file not found at ${rosterPath}`);
    process.exit(1);
  }
  const roster: Roster = JSON.parse(readFileSync(rosterPath, "utf8"));

  let managerKeys: string[];
  if (args["managers"]) {
    managerKeys = args["managers"]
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    for (const k of managerKeys) {
      if (k.startsWith("_") || !(k in roster)) {
        console.error(`FATAL: manager key "${k}" not found in roster ${rosterPath}`);
        process.exit(1);
      }
    }
  } else {
    managerKeys = Object.keys(roster).filter((k) => {
      if (k.startsWith("_")) return false;
      const e = roster[k] as RosterEntry;
      return e.bucket === "institutional-flow" && e.universe === universeTag;
    });
  }

  if (managerKeys.length === 0) {
    console.error(
      `FATAL: no managers selected (roster=${rosterPath}, universe=${universeTag}). Check roster filters or --managers flag.`
    );
    process.exit(1);
  }

  console.error(`Repo root resolved to: ${repoRoot}`);
  console.error(`Selected managers (${managerKeys.length}): ${managerKeys.join(", ")}`);

  mkdirSync(outDir, { recursive: true });

  const warnings: string[] = [];
  const missingData: MissingDataEntry[] = [];
  const sources = new Set<string>();

  const managerResults: ManagerResult[] = [];
  for (const key of managerKeys) {
    const entry = roster[key] as RosterEntry;
    console.error(`\n=== Fetching ${key} (${entry.fund}, CIK ${entry.cik}) ===`);
    const result = await processManager(key, entry, ua, warnings, sources, missingData);
    managerResults.push(result);
    await sleep(SEC_DELAY_MS);
  }

  const okResults = managerResults.filter((r) => r.status === "ok");

  let status: "ok" | "partial" | "failed";
  if (okResults.length === 0) status = "failed";
  else if (okResults.length < managerResults.length) status = "partial";
  else status = "ok";

  let tickerIdx: Map<string, Set<string>> | null = null;
  if (okResults.length > 0) {
    tickerIdx = await buildTickerIndex(ua, sources, warnings);
  }

  const consolidated = buildConsolidated(okResults, tickerIdx);
  const { buys, sells } = computeActions(okResults, tickerIdx);
  const topBuys = buys.slice(0, topN);
  const topSells = sells.slice(0, topN);

  const commonPositions = consolidated.filter((p) => p.instrumentType === "common/share");
  const commonTotal = commonPositions.reduce((s, p) => s + p.aggregate_value_usd, 0);
  const pieTop = commonPositions.slice(0, topN);
  const pieOtherValue = commonPositions.slice(topN).reduce((s, p) => s + p.aggregate_value_usd, 0);
  const pieSlices = pieTop.map((p) => ({
    label: p.position_label,
    value: p.aggregate_value_usd,
    pct: commonTotal > 0 ? (p.aggregate_value_usd / commonTotal) * 100 : 0,
  }));
  if (pieOtherValue > 0) {
    pieSlices.push({ label: "Other", value: pieOtherValue, pct: commonTotal > 0 ? (pieOtherValue / commonTotal) * 100 : 0 });
  }

  const svgFilename = `analyse-smartmoney-13f-top5-${reportDate}.svg`;
  const svgPath = join(outDir, svgFilename);
  const svg = buildPieSvg(pieSlices, reportDate, managerKeys.length);

  const jsonPath = join(outDir, `analyse-smartmoney-13f-top5-${reportDate}.json`);
  const mdPath = join(outDir, `analyse-smartmoney-13f-top5-${reportDate}.md`);
  const generatedAt = new Date().toISOString();

  const reportJson = buildJsonReport({
    reportDate,
    generatedAt,
    managerKeys,
    roster,
    universeTag,
    managerResults,
    consolidated,
    topBuys,
    topSells,
    pieSlices,
    svgPath,
    warnings,
    missingData,
    sources,
    status,
  });

  const md = buildMarkdownReport({
    reportDate,
    generatedAt,
    managerKeys,
    roster,
    managerResults,
    consolidated,
    topBuys,
    topSells,
    topN,
    svgFilename,
    pieCommonTotal: commonTotal,
    warnings,
    missingData,
    sources,
    status,
  });

  writeFileSync(svgPath, svg, "utf8");
  writeFileSync(jsonPath, JSON.stringify(reportJson, null, 2), "utf8");
  writeFileSync(mdPath, md, "utf8");

  console.error(`\n=== DONE: status=${status} ===`);
  console.error(`Report: ${mdPath}`);
  console.error(`JSON:   ${jsonPath}`);
  console.error(`SVG:    ${svgPath}`);
  if (missingData.length > 0) {
    console.error(`Missing data for ${missingData.length} manager(s):`);
    for (const m of missingData) {
      console.error(`  - ${m.manager_key}: [${m.stage}] ${m.error}`);
    }
  }

  if (status === "failed") process.exit(1);
  if (status === "partial") process.exit(2);
  process.exit(0);
}

main().catch((e) => {
  console.error("FATAL unhandled error:", e);
  process.exit(1);
});
