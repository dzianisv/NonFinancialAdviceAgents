#!/usr/bin/env bun
/**
 * OKX public-API OHLCV + indicator pull (TradingView MCP fallback).
 *
 * Why: crypto-advisor normally reads RSI/BB/MACD/OHLCV from the TradingView MCP,
 * but that MCP is orchestrator-only and is not always attached. Binance is
 * geo-blocked from the US. OKX's public market endpoints are keyless and open,
 * so they are the fallback data source. Indicators are computed locally with the
 * SAME standard lengths TradingView uses (RSI 14 Wilder, BB 20/2, MACD 12/26/9).
 *
 * Usage:
 *   bun .agents/scripts/crypto/ohlcv.ts BTC ETH SOL ...
 *   bun .agents/scripts/crypto/ohlcv.ts --out .cache/run/tv.json BTC ETH
 *
 * Output: JSON array, one object per token (tv_data_package shape).
 */

type Bar = { t: number; o: number; h: number; l: number; c: number; v: number };

const OKX = "https://www.okx.com";

async function fetchCandles(instId: string, bar: string, want: number): Promise<Bar[]> {
  const out: Bar[] = [];
  let after: string | undefined;
  for (let i = 0; i < 20 && out.length < want; i++) {
    const url = new URL(`${OKX}/api/v5/market/history-candles`);
    url.searchParams.set("instId", instId);
    url.searchParams.set("bar", bar);
    url.searchParams.set("limit", "100");
    if (after) url.searchParams.set("after", after);
    const r = await fetch(url.toString());
    const j: any = await r.json();
    if (j.code !== "0" || !Array.isArray(j.data) || j.data.length === 0) break;
    for (const row of j.data) {
      out.push({
        t: Number(row[0]), o: Number(row[1]), h: Number(row[2]),
        l: Number(row[3]), c: Number(row[4]), v: Number(row[5]),
      });
    }
    after = String(j.data[j.data.length - 1][0]);
    await new Promise((s) => setTimeout(s, 120));
  }
  // OKX returns newest-first; return oldest-first
  out.sort((a, b) => a.t - b.t);
  return out;
}

/**
 * Coinbase Exchange fallback for tokens OKX does not list (TON, AERO).
 * Coinbase only serves granularity <= 1d, so weekly bars are resampled from daily.
 */
async function fetchCoinbaseDaily(product: string, days: number): Promise<Bar[]> {
  const out: Bar[] = [];
  const day = 86400;
  let end = Math.floor(Date.now() / 1000);
  for (let i = 0; i < 8 && out.length < days; i++) {
    const start = end - day * 300;
    const url = `https://api.exchange.coinbase.com/products/${product}/candles?granularity=86400&start=${start}&end=${end}`;
    const r = await fetch(url, { headers: { "User-Agent": "Mozilla/5.0" } });
    if (!r.ok) break;
    const j: any = await r.json();
    if (!Array.isArray(j) || j.length === 0) break;
    // Coinbase rows: [time, low, high, open, close, volume]
    for (const row of j) {
      out.push({ t: Number(row[0]) * 1000, l: Number(row[1]), h: Number(row[2]), o: Number(row[3]), c: Number(row[4]), v: Number(row[5]) });
    }
    end = start;
    await new Promise((s) => setTimeout(s, 250));
  }
  const seen = new Set<number>();
  return out.filter((b) => (seen.has(b.t) ? false : (seen.add(b.t), true))).sort((a, b) => a.t - b.t);
}

/** Resample daily bars into weekly bars (Mon-anchored buckets). */
function toWeekly(daily: Bar[]): Bar[] {
  const buckets = new Map<number, Bar[]>();
  for (const b of daily) {
    const d = new Date(b.t);
    const dow = (d.getUTCDay() + 6) % 7; // Mon=0
    const wk = Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate() - dow);
    if (!buckets.has(wk)) buckets.set(wk, []);
    buckets.get(wk)!.push(b);
  }
  return [...buckets.entries()].sort((a, b) => a[0] - b[0]).map(([t, bars]) => ({
    t, o: bars[0].o, c: bars[bars.length - 1].c,
    h: Math.max(...bars.map((x) => x.h)), l: Math.min(...bars.map((x) => x.l)),
    v: bars.reduce((s, x) => s + x.v, 0),
  }));
}

const sma = (a: number[], n: number) =>
  a.length < n ? null : a.slice(-n).reduce((x, y) => x + y, 0) / n;

function ema(a: number[], n: number): number | null {
  if (a.length < n) return null;
  const k = 2 / (n + 1);
  let e = a.slice(0, n).reduce((x, y) => x + y, 0) / n;
  for (let i = n; i < a.length; i++) e = a[i] * k + e * (1 - k);
  return e;
}

function emaSeries(a: number[], n: number): number[] {
  const k = 2 / (n + 1);
  const out: number[] = [];
  let e = a[0];
  for (let i = 0; i < a.length; i++) {
    e = i === 0 ? a[0] : a[i] * k + e * (1 - k);
    out.push(e);
  }
  return out;
}

/** Wilder-smoothed RSI — the standard TradingView RSI(14). */
function rsi(a: number[], n = 14): number | null {
  if (a.length < n + 1) return null;
  let g = 0, l = 0;
  for (let i = 1; i <= n; i++) {
    const d = a[i] - a[i - 1];
    d >= 0 ? (g += d) : (l -= d);
  }
  g /= n; l /= n;
  for (let i = n + 1; i < a.length; i++) {
    const d = a[i] - a[i - 1];
    g = (g * (n - 1) + (d > 0 ? d : 0)) / n;
    l = (l * (n - 1) + (d < 0 ? -d : 0)) / n;
  }
  if (l === 0) return 100;
  return 100 - 100 / (1 + g / l);
}

function macd(a: number[]) {
  if (a.length < 35) return { macd: null, signal: null, hist: null };
  const f = emaSeries(a, 12), s = emaSeries(a, 26);
  const line = a.map((_, i) => f[i] - s[i]);
  const sig = emaSeries(line.slice(25), 9);
  const m = line[line.length - 1], g = sig[sig.length - 1];
  return { macd: m, signal: g, hist: m - g };
}

function bollinger(a: number[], n = 20, k = 2) {
  if (a.length < n) return { upper: null, mid: null, lower: null };
  const s = a.slice(-n);
  const mid = s.reduce((x, y) => x + y, 0) / n;
  const sd = Math.sqrt(s.reduce((x, y) => x + (y - mid) ** 2, 0) / n);
  return { upper: mid + k * sd, mid, lower: mid - k * sd };
}

// Tokens OKX does not list — served from Coinbase instead.
const COINBASE_ONLY: Record<string, string> = { TON: "TON-USD", AERO: "AERO-USD" };

async function analyze(token: string) {
  let instId = `${token}-USDT`;
  let daily: Bar[] = [];
  let weekly: Bar[] = [];
  let source = "OKX public market API (keyless)";

  if (COINBASE_ONLY[token]) {
    instId = COINBASE_ONLY[token];
    daily = await fetchCoinbaseDaily(instId, 1500);
    weekly = toWeekly(daily);
    source = "Coinbase Exchange public API (keyless); weekly resampled from daily";
  } else {
    daily = await fetchCandles(instId, "1D", 420);
    weekly = await fetchCandles(instId, "1W", 260);
  }
  if (daily.length === 0) return { token, error: `NO_DATA: ${instId}` };

  const dc = daily.map((b) => b.c);
  const wc = weekly.map((b) => b.c);
  const price = dc[dc.length - 1];

  const last365 = daily.slice(-365);
  const high52 = Math.max(...last365.map((b) => b.h));
  const low52 = Math.min(...last365.map((b) => b.l));
  const ath = Math.max(...daily.map((b) => b.h), ...weekly.map((b) => b.h));

  const sma50 = sma(dc, 50), sma200 = sma(dc, 200);
  const ma200w = sma(wc, 200);
  const m = macd(dc);
  const bb = bollinger(dc);

  return {
    token,
    instId,
    price_usd: price,
    bars: { daily: daily.length, weekly: weekly.length },
    change: {
      d1: ((price / dc[dc.length - 2] - 1) * 100),
      d7: dc.length > 7 ? ((price / dc[dc.length - 8] - 1) * 100) : null,
      d30: dc.length > 30 ? ((price / dc[dc.length - 31] - 1) * 100) : null,
    },
    range: {
      high_52w: high52, low_52w: low52, ath_available_history: ath,
      pct_from_52w_high: ((price / high52 - 1) * 100),
      pct_from_ath_hist: ((price / ath - 1) * 100),
    },
    indicators: {
      rsi14: rsi(dc),
      macd: m.macd, macd_signal: m.signal, macd_hist: m.hist,
      bb_upper: bb.upper, bb_mid: bb.mid, bb_lower: bb.lower,
      volume_24h_base: daily[daily.length - 1].v,
    },
    moving_averages: {
      ema20: ema(dc, 20), sma50, sma200, ma200w,
      death_cross: sma50 !== null && sma200 !== null ? sma50 < sma200 : null,
      pct_vs_sma200: sma200 ? ((price / sma200 - 1) * 100) : null,
      pct_vs_ma200w: ma200w ? ((price / ma200w - 1) * 100) : null,
      weekly_closes: wc.length,
      ma200w_status: wc.length >= 200 ? "OK" : "INSUFFICIENT",
    },
    source,
    fetched_at: new Date().toISOString(),
  };
}

const args = process.argv.slice(2);
let outPath: string | null = null;
const oi = args.indexOf("--out");
if (oi >= 0) { outPath = args[oi + 1]; args.splice(oi, 2); }
const tokens = args.length ? args : ["BTC"];

const results = [];
for (const t of tokens) results.push(await analyze(t));

const json = JSON.stringify(results, null, 2);
if (outPath) { await Bun.write(outPath, json); console.error(`wrote ${outPath}`); }
console.log(json);
