import { test, expect } from "bun:test";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { mkdtempSync, readFileSync } from "node:fs";
import {
  parseCsvLine, appendRows, readRows, summarizeWallets, latestRows, distinctDates, resolveCachePath, COLUMNS,
} from "./portfolio_cache.ts";

function tmpFile(): string {
  return join(mkdtempSync(join(tmpdir(), "pcache-")), ".crypto-portfolio.csv");
}

test("parseCsvLine handles quotes, commas, and doubled quotes", () => {
  expect(parseCsvLine("a,b,c")).toEqual(["a", "b", "c"]);
  expect(parseCsvLine('a,"b,c",d')).toEqual(["a", "b,c", "d"]);
  expect(parseCsvLine('"he said ""hi""",x')).toEqual(['he said "hi"', "x"]);
  expect(parseCsvLine("a,,c")).toEqual(["a", "", "c"]);
});

test("append creates header then round-trips rows", () => {
  const f = tmpFile();
  const n = appendRows(f, [
    { snapshot_date: "2026-06-01", address: "0xAAA", chain: "Base", protocol: "Morpho", usd_value: "100" },
  ]);
  expect(n).toBe(1);
  expect(readFileSync(f, "utf8").split("\n")[0]).toBe(COLUMNS.join(","));
  const rows = readRows(f);
  expect(rows.length).toBe(1);
  expect(rows[0].address).toBe("0xAAA");
  expect(rows[0].protocol).toBe("Morpho");
});

test("append escapes fields containing commas/quotes", () => {
  const f = tmpFile();
  appendRows(f, [
    { snapshot_date: "2026-06-01", address: "0xAAA", notes: "rotate, then claim", symbol: 'a"b' },
  ]);
  const rows = readRows(f);
  expect(rows[0].notes).toBe("rotate, then claim");
  expect(rows[0].symbol).toBe('a"b');
});

test("append rejects a row missing required keys", () => {
  const f = tmpFile();
  expect(() => appendRows(f, [{ address: "0xAAA" } as any])).toThrow(/snapshot_date/);
});

test("dates lists snapshots newest-first; latest returns only newest", () => {
  const f = tmpFile();
  appendRows(f, [
    { snapshot_date: "2026-06-01", address: "0xAAA", usd_value: "100" },
    { snapshot_date: "2026-06-24", address: "0xAAA", usd_value: "120" },
    { snapshot_date: "2026-06-24", address: "0xBBB", usd_value: "50" },
  ]);
  const rows = readRows(f);
  expect(distinctDates(rows)).toEqual(["2026-06-24", "2026-06-01"]);
  const latest = latestRows(rows);
  expect(latest.length).toBe(2);
  expect(latest.every((r) => r.snapshot_date === "2026-06-24")).toBe(true);
});

test("latest filtered by address uses that address's own most-recent date", () => {
  const f = tmpFile();
  appendRows(f, [
    { snapshot_date: "2026-06-01", address: "0xAAA", usd_value: "100" },
    { snapshot_date: "2026-06-10", address: "0xAAA", usd_value: "110" },
    { snapshot_date: "2026-06-24", address: "0xBBB", usd_value: "50" },
  ]);
  const rows = readRows(f);
  const a = latestRows(rows, "0xaaa"); // case-insensitive
  expect(a.length).toBe(1);
  expect(a[0].snapshot_date).toBe("2026-06-10");
});

test("summarizeWallets returns distinct addresses with latest date + USD total, biggest first", () => {
  const f = tmpFile();
  appendRows(f, [
    { snapshot_date: "2026-06-01", address: "0xAAA", wallet_label: "old", usd_value: "100" },
    { snapshot_date: "2026-06-24", address: "0xAAA", wallet_label: "main", usd_value: "60" },
    { snapshot_date: "2026-06-24", address: "0xAAA", wallet_label: "main", usd_value: "40" },
    { snapshot_date: "2026-06-24", address: "0xBBB", wallet_label: "hot", usd_value: "500" },
  ]);
  const w = summarizeWallets(readRows(f));
  expect(w.map((x) => x.address)).toEqual(["0xBBB", "0xAAA"]); // sorted by usd_total desc
  const aaa = w.find((x) => x.address === "0xAAA")!;
  expect(aaa.last_date).toBe("2026-06-24");
  expect(aaa.label).toBe("main");      // latest label, not the old one
  expect(aaa.usd_total).toBeCloseTo(100); // 60+40 on the latest date, not the 2026-06-01 row
});

test("resolveCachePath honors --file then env then repo-root walk", () => {
  expect(resolveCachePath(["latest", "--file", "/x/y.csv"])).toBe("/x/y.csv");
  expect(resolveCachePath(["latest"], { CRYPTO_PORTFOLIO_CSV: "/e/v.csv" } as any)).toBe("/e/v.csv");
  const p = resolveCachePath(["wallets"], {} as any, "/Users/engineer/workspace/backtest/.agents/skills");
  expect(p).toBe("/Users/engineer/workspace/backtest/.crypto-portfolio.csv");
});
