#!/usr/bin/env bun
/**
 * portfolio_cache.ts — dated wallet-address + position cache for defi-portfolio-manager.
 *
 * WHY: a portfolio question should never start by asking "what's your address?". This file is
 * the durable registry of the investor's wallet addresses PLUS a dated snapshot of their positions,
 * so the skill can (a) discover which 0x wallets are the user's, and (b) diff the last snapshot
 * against a fresh live read. It is a CACHE, not a source of truth — always re-pull live before
 * acting on any number (APYs/balances move; addresses do not).
 *
 * Storage: a long-format CSV (one row per position per snapshot) at the repo root
 * `.crypto-portfolio.csv` (gitignored — wallet addresses must not be pushed to a public repo).
 * Override the path with --file <path> or the CRYPTO_PORTFOLIO_CSV env var.
 *
 * Columns (fixed order):
 *   snapshot_date,address,wallet_label,chain,protocol,position_type,symbol,amount,usd_value,apy_pct,in_range,source,notes
 *
 * Commands:
 *   wallets            List distinct wallet addresses with their latest label, last snapshot date,
 *                      and that snapshot's total USD. TSV. Use this FIRST to learn the user's wallets.
 *   latest [address]   Print the most-recent snapshot rows (CSV), optionally filtered to one address
 *                      (uses that address's own most-recent snapshot_date).
 *   dates              List distinct snapshot dates, newest first.
 *   append <json|->    Append rows from a JSON array (arg or stdin) of objects keyed by the columns
 *                      above. snapshot_date + address are required per row; missing fields -> "".
 *                      Creates the file with a header if absent.
 *
 * Examples:
 *   bun portfolio_cache.ts wallets
 *   bun portfolio_cache.ts latest 0x5D039ECe117073323ADE5057a516864F4c40e653
 *   echo '[{"snapshot_date":"2026-06-24","address":"0xabc","chain":"Base","protocol":"Morpho","position_type":"Yield","symbol":"USDC","usd_value":"29384"}]' | bun portfolio_cache.ts append -
 */
import { existsSync, readFileSync, appendFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";

export const COLUMNS = [
  "snapshot_date", "address", "wallet_label", "chain", "protocol", "position_type",
  "symbol", "amount", "usd_value", "apy_pct", "in_range", "source", "notes",
] as const;
export type Row = Partial<Record<(typeof COLUMNS)[number], string>>;

/** Resolve the cache file path: --file > CRYPTO_PORTFOLIO_CSV > <repo-root>/.crypto-portfolio.csv. */
export function resolveCachePath(argv: string[], env = process.env, startDir = process.cwd()): string {
  const i = argv.indexOf("--file");
  if (i >= 0 && argv[i + 1]) return argv[i + 1];
  if (env.CRYPTO_PORTFOLIO_CSV) return env.CRYPTO_PORTFOLIO_CSV;
  let dir = startDir;
  for (;;) {
    if (existsSync(join(dir, ".git"))) return join(dir, ".crypto-portfolio.csv");
    const parent = dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return join(startDir, ".crypto-portfolio.csv");
}

function escapeCsv(v: string): string {
  if (v === "") return "";
  return /[",\n\r]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v;
}

/** Parse one CSV line into fields, honoring quotes and escaped (doubled) quotes. */
export function parseCsvLine(line: string): string[] {
  const out: string[] = [];
  let cur = "";
  let inQ = false;
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (inQ) {
      if (c === '"') {
        if (line[i + 1] === '"') { cur += '"'; i++; } else inQ = false;
      } else cur += c;
    } else if (c === '"') inQ = true;
    else if (c === ",") { out.push(cur); cur = ""; }
    else cur += c;
  }
  out.push(cur);
  return out;
}

export function readRows(file: string): Row[] {
  if (!existsSync(file)) return [];
  const text = readFileSync(file, "utf8").replace(/\r\n/g, "\n").trim();
  if (!text) return [];
  const lines = text.split("\n");
  const header = parseCsvLine(lines[0]);
  return lines.slice(1).filter((l) => l.length > 0).map((line) => {
    const cells = parseCsvLine(line);
    const row: Row = {};
    header.forEach((h, idx) => { (row as Record<string, string>)[h] = cells[idx] ?? ""; });
    return row;
  });
}

export function appendRows(file: string, rows: Row[]): number {
  let written = 0;
  if (!existsSync(file)) writeFileSync(file, COLUMNS.join(",") + "\n");
  const body = rows.map((r) => {
    if (!r.snapshot_date || !r.address) {
      throw new Error(`each row needs snapshot_date + address: ${JSON.stringify(r)}`);
    }
    written++;
    return COLUMNS.map((c) => escapeCsv((r[c] ?? "").toString())).join(",");
  }).join("\n");
  if (body) appendFileSync(file, body + "\n");
  return written;
}

function num(s: string | undefined): number {
  const n = parseFloat((s ?? "").replace(/[$,]/g, ""));
  return Number.isFinite(n) ? n : 0;
}

/** Distinct addresses with latest label, last snapshot date, and that date's USD total. */
export function summarizeWallets(rows: Row[]) {
  const byAddr = new Map<string, Row[]>();
  for (const r of rows) {
    const a = (r.address ?? "").trim();
    if (!a) continue;
    (byAddr.get(a) ?? byAddr.set(a, []).get(a)!).push(r);
  }
  const out: { address: string; label: string; last_date: string; usd_total: number }[] = [];
  for (const [address, rs] of byAddr) {
    const last_date = rs.map((r) => r.snapshot_date ?? "").sort().at(-1) ?? "";
    const onDate = rs.filter((r) => r.snapshot_date === last_date);
    const label = onDate.find((r) => (r.wallet_label ?? "") !== "")?.wallet_label ?? "";
    const usd_total = onDate.reduce((s, r) => s + num(r.usd_value), 0);
    out.push({ address, label, last_date, usd_total });
  }
  return out.sort((a, b) => b.usd_total - a.usd_total);
}

export function latestRows(rows: Row[], address?: string): Row[] {
  const scope = address ? rows.filter((r) => (r.address ?? "").toLowerCase() === address.toLowerCase()) : rows;
  if (scope.length === 0) return [];
  const last = scope.map((r) => r.snapshot_date ?? "").sort().at(-1) ?? "";
  return scope.filter((r) => r.snapshot_date === last);
}

export function distinctDates(rows: Row[]): string[] {
  return [...new Set(rows.map((r) => r.snapshot_date ?? "").filter(Boolean))].sort().reverse();
}

function toCsv(rows: Row[]): string {
  return [COLUMNS.join(","), ...rows.map((r) => COLUMNS.map((c) => escapeCsv((r[c] ?? "").toString())).join(","))].join("\n");
}

async function readStdin(): Promise<string> {
  const chunks: Uint8Array[] = [];
  for await (const c of Bun.stdin.stream()) chunks.push(c);
  return Buffer.concat(chunks).toString("utf8");
}

async function main() {
  const argv = process.argv.slice(2);
  const cmd = argv[0];
  const file = resolveCachePath(argv);
  const positional = argv.slice(1).filter((a, i, arr) => a !== "--file" && arr[i - 1] !== "--file");

  if (cmd === "wallets") {
    const w = summarizeWallets(readRows(file));
    if (w.length === 0) { console.error(`(no cache yet at ${file})`); return; }
    console.log("address\tlabel\tlast_date\tusd_total");
    for (const r of w) console.log(`${r.address}\t${r.label}\t${r.last_date}\t${r.usd_total.toFixed(2)}`);
  } else if (cmd === "latest") {
    console.log(toCsv(latestRows(readRows(file), positional[0])));
  } else if (cmd === "dates") {
    for (const d of distinctDates(readRows(file))) console.log(d);
  } else if (cmd === "append") {
    const raw = positional[0] === "-" || !positional[0] ? await readStdin() : positional[0];
    const parsed = JSON.parse(raw);
    const rows: Row[] = Array.isArray(parsed) ? parsed : [parsed];
    const n = appendRows(file, rows);
    console.error(`appended ${n} row(s) -> ${file}`);
  } else {
    console.error("usage: portfolio_cache.ts <wallets|latest [address]|dates|append <json|->> [--file PATH]");
    process.exit(2);
  }
}

if (import.meta.main) main();
