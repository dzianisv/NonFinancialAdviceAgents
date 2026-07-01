#!/usr/bin/env bun
/**
 * dividend_watch.ts — daily payout monitor driven via the chrome-use CLI.
 *
 * Why chrome-use instead of curl: it drives the user's REAL running Chrome, so the
 * data pulls are same-origin fetch()es from inside a stockanalysis.com tab and never
 * get bot-blocked (datacenter-IP 403s that hit curl). The same transport can later be
 * pointed at Fidelity behind the user's login for the authoritative distribution record.
 *
 * What it watches (for liquidation stubs like SITC, where each special distribution can
 * re-price the stock by MORE or LESS than the payout — the only real edge in holding one):
 *   1. NEW distribution declared        → a history row we haven't seen before
 *   2. UPCOMING ex-date within N days    → last window to decide before you go ex
 *   3. POST-EX price reaction            → did the stock drop LESS than the payout?
 *      (dropping less than the cash you received = holding through the payout is accretive)
 *
 * Silent-unless-actionable: writes state + a log line every run, but only pings Telegram
 * when something changed or an ex-date is imminent. Pass --summary to force a status ping.
 *
 * Usage:
 *   bun dividend_watch.ts                 # default: SITC → Telegram "me"
 *   bun dividend_watch.ts SITC ARE O      # multiple tickers
 *   bun dividend_watch.ts --summary       # also send a no-change status line
 *   TG_TARGET=@somechat bun dividend_watch.ts
 *   CHROME=/path/to/chrome-use bun dividend_watch.ts
 */

import { homedir } from "os";
import { join } from "path";
import { mkdir } from "fs/promises";

const CHROME =
  process.env.CHROME ||
  join(homedir(), ".agents/skills/chrome-use/scripts/chrome-use");
const TG_CLI = join(homedir(), ".agents/skills/telegram-cli/telegram-cli.py");
const TG_TARGET = process.env.TG_TARGET || "me";
const STATE_DIR = join(homedir(), ".config/dividend-watch");
const UPCOMING_DAYS = Number(process.env.UPCOMING_DAYS || 14);

interface DivRow {
  dt: string; // ex-dividend date YYYY-MM-DD
  amt: string; // "$1.000"
  record: string;
  pay: string;
}
interface State {
  seenExDates: string[];
  priceLog: { date: string; price: number; prevClose: number; changePct: number }[];
  reactedExDates: string[]; // ex-dates we've already logged a post-ex reaction for
  lastRun: string;
}

const today = () => new Date().toISOString().slice(0, 10);
const amtNum = (a: string) => Number(String(a).replace(/[^0-9.]/g, "")) || 0;
const daysBetween = (a: string, b: string) =>
  Math.round((Date.parse(a) - Date.parse(b)) / 86_400_000);

/** Run one chrome-use subcommand, return trimmed stdout. */
async function cu(args: string[]): Promise<string> {
  const p = Bun.spawn([CHROME, ...args], { stdout: "pipe", stderr: "pipe" });
  const out = await new Response(p.stdout).text();
  await p.exited;
  return out.trim();
}

/**
 * eval an expression in the active tab. We JSON.stringify inside the page, so chrome-use
 * prints a JSON string literal; parse twice to recover the value. Returns null on failure.
 */
async function cuEvalJSON<T>(expr: string): Promise<T | null> {
  const raw = await cu(["eval", expr]);
  const line = raw.split("\n").map((l) => l.trim()).filter(Boolean).pop() || "";
  try {
    const inner = JSON.parse(line); // -> the JSON string we stringified in-page
    return typeof inner === "string" ? (JSON.parse(inner) as T) : (inner as T);
  } catch {
    return null;
  }
}

async function telegram(msg: string): Promise<void> {
  const p = Bun.spawn(["python3", TG_CLI, "send", TG_TARGET, msg], {
    stdout: "pipe",
    stderr: "pipe",
  });
  await p.exited;
  if (p.exitCode !== 0) console.error(`  telegram send failed (exit ${p.exitCode})`);
}

async function loadState(ticker: string): Promise<State> {
  const f = Bun.file(join(STATE_DIR, `${ticker}.json`));
  if (await f.exists()) {
    try {
      return (await f.json()) as State;
    } catch {}
  }
  return { seenExDates: [], priceLog: [], reactedExDates: [], lastRun: "" };
}
async function saveState(ticker: string, s: State): Promise<void> {
  await mkdir(STATE_DIR, { recursive: true });
  await Bun.write(join(STATE_DIR, `${ticker}.json`), JSON.stringify(s, null, 2));
}

async function fetchTicker(ticker: string) {
  // Dedicated throwaway tab so we never disturb the user's active browsing.
  await cu(["tab", "new", `https://stockanalysis.com/stocks/${ticker}/dividend/`]);
  await Bun.sleep(2500);
  const div = await cuEvalJSON<{ history: DivRow[]; infoTable: any }>(
    `fetch('/api/symbol/s/${ticker}/dividend').then(r=>r.json()).then(j=>JSON.stringify({history:j.data.history, infoTable:j.data.infoTable}))`
  );
  const quote = await cuEvalJSON<{ p: number; cl: number; cp: number; td: string }>(
    `fetch('/api/quotes/s/${ticker}').then(r=>r.json()).then(j=>JSON.stringify({p:j.data.p, cl:j.data.cl, cp:j.data.cp, td:j.data.td}))`
  );
  await cu(["tab", "close"]);
  return { div, quote };
}

async function processTicker(ticker: string, forceSummary: boolean): Promise<void> {
  const { div, quote } = await fetchTicker(ticker);
  if (!div || !quote) {
    console.error(`[${ticker}] fetch failed (div=${!!div} quote=${!!quote})`);
    await telegram(`⚠️ dividend-watch ${ticker}: data fetch failed on ${today()} — check chrome-use.`);
    return;
  }

  const st = await loadState(ticker);
  const seen = new Set(st.seenExDates);
  const reacted = new Set(st.reactedExDates);
  const alerts: string[] = [];
  const now = today();
  const history = div.history || [];

  // 1) NEW distributions (rows not seen before). Skip on very first run — we don't want to
  //    fire the entire multi-year backlog as "new"; just seed the baseline.
  const firstRun = st.seenExDates.length === 0;
  const fresh = history.filter((r) => !seen.has(r.dt));
  if (!firstRun) {
    for (const r of fresh) {
      alerts.push(
        `🆕 ${ticker} NEW distribution: ${r.amt} | ex ${r.dt} | record ${r.record} | pay ${r.pay}`
      );
    }
  }
  for (const r of history) seen.add(r.dt);

  // 2) UPCOMING ex-date within the window (future or today).
  for (const r of history) {
    const d = daysBetween(r.dt, now);
    if (d >= 0 && d <= UPCOMING_DAYS) {
      alerts.push(
        `⏰ ${ticker} ex-date in ${d}d (${r.dt}): ${r.amt}. Last window to decide before you go ex — you keep this payout if you hold through the record date, then can sell.`
      );
    }
  }

  // 3) POST-EX price reaction: for the most recent PAST ex-date, compare the price drop to
  //    the payout. Uses today's prev-close vs price as the observed daily move around ex.
  const past = history
    .filter((r) => daysBetween(now, r.dt) >= 0)
    .sort((a, b) => Date.parse(b.dt) - Date.parse(a.dt));
  const lastEx = past[0];
  if (lastEx && Math.abs(daysBetween(now, lastEx.dt)) <= 1 && !reacted.has(lastEx.dt)) {
    const payout = amtNum(lastEx.amt);
    const drop = quote.cl - quote.p; // prev close minus current
    if (payout > 0) {
      const capturedPct = (((payout - drop) / payout) * 100).toFixed(0);
      const verdict =
        drop < payout
          ? `dropped $${drop.toFixed(2)} vs $${payout.toFixed(2)} payout → held ${capturedPct}% of the cash (accretive to hold through it)`
          : `dropped $${drop.toFixed(2)} vs $${payout.toFixed(2)} payout → full/over-adjust (no edge from holding)`;
      alerts.push(`📉 ${ticker} post-ex reaction (${lastEx.dt}): ${verdict}. Price $${quote.p}.`);
    }
    reacted.add(lastEx.dt);
  }

  // Persist state + price log (dedupe by date).
  if (!st.priceLog.some((p) => p.date === quote.td)) {
    st.priceLog.push({ date: quote.td, price: quote.p, prevClose: quote.cl, changePct: quote.cp });
  }
  st.priceLog = st.priceLog.slice(-400);
  st.seenExDates = [...seen].sort();
  st.reactedExDates = [...reacted].sort();
  st.lastRun = now;
  await saveState(ticker, st);

  const info = div.infoTable || {};
  const summary = `${ticker} $${quote.p} (${quote.cp >= 0 ? "+" : ""}${quote.cp}%) | last ex ${info.exdiv || "?"} | annual ${info.annual || "?"} | ${history.length} distributions on record`;
  console.log(`[${now}] ${summary}`);
  if (firstRun) console.log(`  seeded baseline (${history.length} rows) — no backlog alerts.`);

  if (alerts.length) {
    const msg = `🔔 dividend-watch ${now}\n${summary}\n\n${alerts.join("\n\n")}`;
    console.log(alerts.map((a) => "  " + a).join("\n"));
    await telegram(msg);
  } else if (forceSummary) {
    await telegram(`ℹ️ dividend-watch ${now} — no change.\n${summary}`);
  }
}

async function main() {
  const argv = process.argv.slice(2);
  const forceSummary = argv.includes("--summary");
  const tickers = argv.filter((a) => !a.startsWith("--")).map((t) => t.toUpperCase());
  if (tickers.length === 0) tickers.push("SITC");

  for (const t of tickers) {
    try {
      await processTicker(t, forceSummary);
    } catch (e) {
      console.error(`[${t}] error:`, e);
    }
  }
}

main();
