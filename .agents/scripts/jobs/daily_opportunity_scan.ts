#!/usr/bin/env bun

import { $ } from "bun";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const REPO_ROOT = process.env.SCAN_REPO_ROOT ?? "/Users/engineer/workspace/backtest";
const PYTHON = process.env.SCAN_PYTHON ?? "/Users/engineer/.venv/bin/python3";
const DEFAULT_NTFY_TOPIC = "mkt-dz-wl-eb53ce91";
const UNIVERSE_PATH = resolve(
  REPO_ROOT,
  ".agents/skills/stocks-trend-screener/scripts/universe.txt",
);
const DEFAULT_WATCHLIST_LIMIT = 40;

type StepName = "regime" | "dip_scanner" | "narrative_velocity" | "convergence";
type StepState = "ok" | "degraded";

type StepStatus = {
  state: StepState;
  reason?: string;
};

type ShellLikeResult = {
  exitCode: number;
  stdout: Uint8Array | string;
  stderr: Uint8Array | string;
};

type JsonStepResult<T> =
  | { ok: true; data: T; stdout: string; stderr: string; exitCode: number }
  | { ok: false; reason: string; stdout: string; stderr: string; exitCode: number | null };

type CliOptions = {
  emitJson: boolean;
  noNotify: boolean;
  watchlistCsv?: string;
  minSources: number;
};

type RegimeOutput = {
  regime?: unknown;
  score?: unknown;
  [key: string]: unknown;
};

type DipOutput = {
  equity?: {
    hits?: unknown;
    fetch_misses?: unknown;
  };
  crypto?: {
    dips?: unknown;
    fear_greed?: unknown;
  };
  [key: string]: unknown;
};

type NarrativeOutput = unknown;

type ConvergenceOutput = {
  min_sources?: unknown;
  convergences?: unknown;
  [key: string]: unknown;
};

type EquityDipHit = {
  ticker: string;
  pct_from_high: number;
  sma200: number | null;
  conviction: string;
};

type CryptoDipHit = {
  ticker: string;
  pct_from_high: number;
  conviction: string;
};

type FearGreed = {
  value: number;
  label?: string;
};

type NarrativeRow = {
  ticker: string;
  mentions_now: number | null;
  spike: boolean;
  pool_fed: boolean;
  status?: string;
};

type ConvergenceHit = {
  ticker: string;
  sources: string[];
  n_sources: number;
  notes: string[];
};

type AlertDecision = {
  fired: boolean;
  reasons: string[];
};

const HARD_FALLBACK_WATCHLIST: string[] = [
  "NVDA",
  "AMD",
  "INTC",
  "AVGO",
  "TSM",
  "QCOM",
  "ARM",
  "AMAT",
  "KLAC",
  "LRCX",
  "MU",
  "MRVL",
  "SMCI",
  "CRDO",
  "ON",
  "TXN",
  "ASML",
  "MPWR",
  "ENPH",
  "WOLF",
  "IONQ",
  "RGTI",
  "QBTS",
  "AAPL",
  "MSFT",
  "GOOGL",
  "META",
  "AMZN",
  "ORCL",
  "CRM",
  "SNOW",
  "PLTR",
  "DDOG",
  "MDB",
  "NET",
  "CRWD",
  "PANW",
  "FTNT",
  "ZS",
  "LDOS",
];

function bytesToString(value: Uint8Array | string): string {
  return typeof value === "string" ? value : Buffer.from(value).toString("utf8");
}

function asString(value: unknown): string | null {
  if (typeof value === "string" && value.trim().length > 0) {
    return value.trim();
  }
  return null;
}

function asNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim().length > 0) {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }
  return null;
}

function parseTickerCsv(csv: string): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const raw of csv.split(",")) {
    const ticker = raw.trim().toUpperCase();
    if (!ticker || seen.has(ticker)) {
      continue;
    }
    seen.add(ticker);
    out.push(ticker);
  }
  return out;
}

function loadUniverseFallback(limit: number): string[] {
  try {
    const raw = readFileSync(UNIVERSE_PATH, "utf8");
    const parsed = parseTickerCsv(raw.replace(/\r?\n/g, ","));
    return parsed.slice(0, limit);
  } catch {
    return HARD_FALLBACK_WATCHLIST.slice(0, limit);
  }
}

function resolveWatchlist(cliWatchlist?: string): string[] {
  if (cliWatchlist && cliWatchlist.trim().length > 0) {
    const parsed = parseTickerCsv(cliWatchlist);
    if (parsed.length > 0) return parsed;
  }
  const envWatchlist = process.env.SCAN_WATCHLIST;
  if (envWatchlist && envWatchlist.trim().length > 0) {
    const parsed = parseTickerCsv(envWatchlist);
    if (parsed.length > 0) return parsed;
  }
  return loadUniverseFallback(DEFAULT_WATCHLIST_LIMIT);
}

function parseArgs(argv: string[]): CliOptions {
  let emitJson = false;
  let noNotify = false;
  let watchlistCsv: string | undefined;
  let minSources = 2;

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--json") {
      emitJson = true;
      continue;
    }
    if (arg === "--no-notify") {
      noNotify = true;
      continue;
    }
    if (arg === "--watchlist") {
      const next = argv[i + 1];
      if (!next || next.startsWith("--")) {
        throw new Error("Missing value for --watchlist");
      }
      watchlistCsv = next;
      i += 1;
      continue;
    }
    if (arg === "--min-sources") {
      const next = argv[i + 1];
      if (!next || next.startsWith("--")) {
        throw new Error("Missing value for --min-sources");
      }
      const parsed = Number.parseInt(next, 10);
      if (!Number.isInteger(parsed) || parsed < 1) {
        throw new Error(`Invalid --min-sources value: ${next}`);
      }
      minSources = parsed;
      i += 1;
      continue;
    }
    throw new Error(`Unknown argument: ${arg}`);
  }

  return { emitJson, noNotify, watchlistCsv, minSources };
}

function clip(text: string, limit = 240): string {
  const clean = text.replace(/\s+/g, " ").trim();
  if (clean.length <= limit) return clean;
  return `${clean.slice(0, limit)}…`;
}

async function runJsonStep<T>(
  step: StepName,
  timeoutMs: number,
  run: () => Promise<ShellLikeResult>,
): Promise<JsonStepResult<T>> {
  try {
    const pending = run();
    const outcome = await Promise.race([
      pending.then((result) => ({ kind: "done" as const, result })),
      Bun.sleep(timeoutMs).then(() => ({ kind: "timeout" as const })),
    ]);

    if (outcome.kind === "timeout") {
      return {
        ok: false,
        reason: `timeout after ${Math.round(timeoutMs / 1000)}s`,
        stdout: "",
        stderr: "",
        exitCode: null,
      };
    }

    const stdout = bytesToString(outcome.result.stdout);
    const stderr = bytesToString(outcome.result.stderr);
    const exitCode = outcome.result.exitCode;

    if (exitCode !== 0) {
      const why = stderr.trim() || stdout.trim() || `non-zero exit code ${exitCode}`;
      return { ok: false, reason: `exit ${exitCode}: ${clip(why)}`, stdout, stderr, exitCode };
    }

    const body = stdout.trim();
    if (!body) {
      return { ok: false, reason: "empty stdout", stdout, stderr, exitCode };
    }

    try {
      const data = JSON.parse(body) as T;
      return { ok: true, data, stdout, stderr, exitCode };
    } catch (error) {
      const msg = error instanceof Error ? error.message : String(error);
      return {
        ok: false,
        reason: `invalid JSON: ${msg}; stdout=${clip(body)}`,
        stdout,
        stderr,
        exitCode,
      };
    }
  } catch (error) {
    const msg = error instanceof Error ? error.message : String(error);
    return { ok: false, reason: `threw error: ${msg}`, stdout: "", stderr: "", exitCode: null };
  }
}

function normalizeEquityHits(value: unknown): EquityDipHit[] {
  if (!Array.isArray(value)) return [];
  const hits: EquityDipHit[] = [];
  for (const row of value) {
    if (!row || typeof row !== "object") continue;
    const ticker = asString((row as Record<string, unknown>).ticker);
    const pctFromHigh = asNumber((row as Record<string, unknown>).pct_from_high);
    const sma200Raw = asNumber((row as Record<string, unknown>).sma200);
    const conviction = asString((row as Record<string, unknown>).conviction) ?? "UNKNOWN";
    if (!ticker || pctFromHigh === null) continue;
    hits.push({
      ticker,
      pct_from_high: pctFromHigh,
      sma200: sma200Raw,
      conviction,
    });
  }
  return hits;
}

function normalizeCryptoHits(value: unknown): CryptoDipHit[] {
  if (!Array.isArray(value)) return [];
  const hits: CryptoDipHit[] = [];
  for (const row of value) {
    if (!row || typeof row !== "object") continue;
    const ticker = asString((row as Record<string, unknown>).ticker);
    const pctFromHigh = asNumber((row as Record<string, unknown>).pct_from_high);
    const conviction = asString((row as Record<string, unknown>).conviction) ?? "UNKNOWN";
    if (!ticker || pctFromHigh === null) continue;
    hits.push({
      ticker,
      pct_from_high: pctFromHigh,
      conviction,
    });
  }
  return hits;
}

function normalizeFearGreed(value: unknown): FearGreed | null {
  if (!value || typeof value !== "object") return null;
  const fgValue = asNumber((value as Record<string, unknown>).value);
  if (fgValue === null) return null;
  const label = asString((value as Record<string, unknown>).label) ?? undefined;
  return { value: fgValue, label };
}

function normalizeNarrativeRows(value: NarrativeOutput): NarrativeRow[] {
  if (!Array.isArray(value)) return [];
  const rows: NarrativeRow[] = [];
  for (const row of value) {
    if (!row || typeof row !== "object") continue;
    const rec = row as Record<string, unknown>;
    const ticker = asString(rec.ticker);
    if (!ticker) continue;
    rows.push({
      ticker,
      mentions_now: asNumber(rec.mentions_now),
      spike: rec.spike === true,
      pool_fed: rec.pool_fed === true,
      status: asString(rec.status) ?? undefined,
    });
  }
  return rows;
}

function normalizeConvergences(value: unknown): ConvergenceHit[] {
  if (!Array.isArray(value)) return [];
  const hits: ConvergenceHit[] = [];
  for (const row of value) {
    if (!row || typeof row !== "object") continue;
    const rec = row as Record<string, unknown>;
    const ticker = asString(rec.ticker);
    const nSources = asNumber(rec.n_sources);
    const sourceList = Array.isArray(rec.sources)
      ? rec.sources
          .map((source) => (typeof source === "string" ? source.trim() : ""))
          .filter((source): source is string => source.length > 0)
      : [];
    const notes = Array.isArray(rec.notes)
      ? rec.notes
          .map((note) => (typeof note === "string" ? note.trim() : ""))
          .filter((note): note is string => note.length > 0)
      : [];
    if (!ticker || nSources === null) continue;
    hits.push({
      ticker,
      sources: sourceList,
      n_sources: nSources,
      notes,
    });
  }
  return hits;
}

function decideAlert(
  minSources: number,
  regimeLabel: string,
  equityHits: EquityDipHit[],
  cryptoHits: CryptoDipHit[],
  fearGreed: FearGreed | null,
  convergences: ConvergenceHit[],
): AlertDecision {
  const reasons: string[] = [];

  const hasConvergence = convergences.some((hit) => hit.n_sources >= minSources);
  if (hasConvergence) {
    reasons.push(`convergence>=${minSources}`);
  }

  const highRiskOnDip = regimeLabel === "RISK_ON"
    && equityHits.some((hit) => hit.conviction === "HIGH" && hit.pct_from_high <= -30);
  if (highRiskOnDip) {
    reasons.push("risk_on_high_equity_dip");
  }

  const cryptoFearDip = !!fearGreed
    && fearGreed.value < 25
    && cryptoHits.some((hit) => Number.isFinite(hit.pct_from_high));
  if (cryptoFearDip) {
    reasons.push("crypto_fear_greed_below_25");
  }

  return { fired: reasons.length > 0, reasons };
}

function buildAlertText(input: {
  date: string;
  minSources: number;
  regimeLabel: string;
  regimeScore: number | null;
  convergences: ConvergenceHit[];
  equityHits: EquityDipHit[];
  cryptoHits: CryptoDipHit[];
  fearGreed: FearGreed | null;
  narrativeRows: NarrativeRow[];
}): string {
  const lines: string[] = [];
  const scorePart = input.regimeScore === null ? "score n/a" : `score ${input.regimeScore.toFixed(3)}`;
  const regimePart =
    input.regimeLabel === "UNKNOWN"
      ? "regime UNKNOWN (degraded)"
      : `regime ${input.regimeLabel}`;
  lines.push(`DAILY OPPORTUNITY SCAN — ${input.date} — ${regimePart} (${scorePart})`);

  const dipByTicker = new Map<string, number>();
  for (const hit of input.equityHits) {
    dipByTicker.set(hit.ticker, hit.pct_from_high);
  }
  for (const hit of input.cryptoHits) {
    dipByTicker.set(hit.ticker, hit.pct_from_high);
  }
  const narrativeByTicker = new Map<string, NarrativeRow>();
  for (const row of input.narrativeRows) {
    narrativeByTicker.set(row.ticker, row);
  }

  const convergenceHits = input.convergences.filter((hit) => hit.n_sources >= input.minSources);
  if (convergenceHits.length > 0) {
    lines.push(`CONVERGENCE (>=${input.minSources} sources, may be correlated):`);
    for (const hit of convergenceHits) {
      const extras: string[] = [];
      const dipPct = dipByTicker.get(hit.ticker);
      if (dipPct !== undefined) {
        extras.push(`dip ${dipPct.toFixed(1)}% / 52w`);
      }
      const narrative = narrativeByTicker.get(hit.ticker);
      if (narrative && narrative.mentions_now !== null) {
        extras.push(`${narrative.mentions_now} narrative mentions`);
      }
      const extraText = extras.length > 0 ? ` — ${extras.join(" / ")}` : "";
      lines.push(`  ${hit.ticker} — sources: [${hit.sources.join(", ")}]${extraText}`);
    }
  }

  const riskOnHighDips = input.regimeLabel === "RISK_ON"
    ? input.equityHits.filter((hit) => hit.conviction === "HIGH" && hit.pct_from_high <= -30)
    : [];
  if (riskOnHighDips.length > 0) {
    lines.push("DIPS (RISK_ON):");
    for (const hit of riskOnHighDips) {
      const maText = hit.sma200 === null ? "200d n/a" : `200d $${hit.sma200.toFixed(2)}`;
      lines.push(`  ${hit.ticker} ${hit.pct_from_high.toFixed(1)}% from 52w high (${maText})`);
    }
  }

  if (input.fearGreed && input.fearGreed.value < 25 && input.cryptoHits.length > 0) {
    lines.push("CRYPTO:");
    for (const hit of input.cryptoHits) {
      lines.push(
        `  ${hit.ticker} ${hit.pct_from_high.toFixed(1)}% from 52w high (F&G ${input.fearGreed!.value})`,
      );
    }
  }

  lines.push(
    "Entry = buy quality weakness in the dip zone; route to /multi-lens-quorum + skeptic before any order. Not advice.",
  );
  return lines.join("\n");
}

async function postNotification(topic: string, title: string, body: string): Promise<void> {
  try {
    const response = await fetch(`https://ntfy.sh/${encodeURIComponent(topic)}`, {
      method: "POST",
      headers: {
        "X-Title": title,
        "Content-Type": "text/plain; charset=utf-8",
      },
      body,
    });
    if (!response.ok) {
      console.error(`[NOTIFY-FAILED] ntfy.sh responded ${response.status} ${response.statusText}`);
    }
  } catch (error) {
    const msg = error instanceof Error ? error.message : String(error);
    console.error(`[NOTIFY-FAILED] ${msg}`);
  }
}

async function main(): Promise<number> {
  const options = parseArgs(process.argv.slice(2));
  const date = new Date().toISOString().slice(0, 10);
  const watchlist = resolveWatchlist(options.watchlistCsv);

  if (watchlist.length === 0) {
    throw new Error("Watchlist resolved to zero tickers");
  }

  const stepStatus: Record<StepName, StepStatus> = {
    regime: { state: "ok" },
    dip_scanner: { state: "ok" },
    narrative_velocity: { state: "ok" },
    convergence: { state: "ok" },
  };

  const markDegraded = (step: StepName, reason: string) => {
    stepStatus[step] = { state: "degraded", reason };
    console.error(`[DEGRADED] ${step} failed: ${reason}`);
  };

  let regimeLabel = "UNKNOWN";
  let regimeScore: number | null = null;

  let equityHits: EquityDipHit[] = [];
  let cryptoHits: CryptoDipHit[] = [];
  let fearGreed: FearGreed | null = null;
  let narrativeRows: NarrativeRow[] = [];
  let convergenceHits: ConvergenceHit[] = [];

  const regimeStep = await runJsonStep<RegimeOutput>("regime", 120_000, () =>
    $`${PYTHON} .agents/skills/regime-detection/regime_monitor.py --json`.quiet().nothrow(),
  );
  if (!regimeStep.ok) {
    markDegraded("regime", regimeStep.reason);
  } else {
    const label = asString(regimeStep.data.regime);
    const score = asNumber(regimeStep.data.score);
    if (!label) {
      markDegraded("regime", "missing regime label in JSON");
    } else {
      regimeLabel = label;
    }
    if (score === null) {
      markDegraded("regime", "missing numeric score in JSON");
    } else {
      regimeScore = score;
    }
  }

  const dipStep = await runJsonStep<DipOutput>("dip_scanner", 240_000, () =>
    $`${PYTHON} .agents/skills/dip-scanner/dip_scanner.py --universe all --emit-pool --json`
      .quiet()
      .nothrow(),
  );
  if (!dipStep.ok) {
    markDegraded("dip_scanner", dipStep.reason);
  } else {
    equityHits = normalizeEquityHits(dipStep.data?.equity?.hits);
    cryptoHits = normalizeCryptoHits(dipStep.data?.crypto?.dips);
    fearGreed = normalizeFearGreed(dipStep.data?.crypto?.fear_greed);
  }

  const tickerCsv = watchlist.join(",");
  const narrativeStep = await runJsonStep<NarrativeOutput>("narrative_velocity", 300_000, () =>
    $`${PYTHON} .agents/skills/stocks-trend-screener/mention_velocity.py --tickers ${tickerCsv} --days 7 --json`
      .quiet()
      .nothrow(),
  );
  if (!narrativeStep.ok) {
    markDegraded("narrative_velocity", narrativeStep.reason);
  } else if (!Array.isArray(narrativeStep.data)) {
    markDegraded("narrative_velocity", "JSON root was not an array");
  } else {
    narrativeRows = normalizeNarrativeRows(narrativeStep.data);
  }

  const convergenceStep = await runJsonStep<ConvergenceOutput>("convergence", 120_000, () =>
    $`${PYTHON} .agents/skills/signal-convergence-alert/convergence.py --min-sources ${String(options.minSources)} --json`
      .quiet()
      .nothrow(),
  );
  if (!convergenceStep.ok) {
    markDegraded("convergence", convergenceStep.reason);
  } else {
    convergenceHits = normalizeConvergences(convergenceStep.data.convergences);
  }

  const decision = decideAlert(
    options.minSources,
    regimeLabel,
    equityHits,
    cryptoHits,
    fearGreed,
    convergenceHits,
  );

  const result = {
    date,
    regime: { label: regimeLabel, score: regimeScore },
    dips: {
      equity_hits: equityHits,
      crypto_dips: cryptoHits,
      fear_greed: fearGreed,
    },
    narrative: {
      watchlist,
      rows: narrativeRows,
      spikes: narrativeRows.filter((row) => row.spike),
    },
    convergence: {
      min_sources: options.minSources,
      hits: convergenceHits,
    },
    alert: decision,
    step_status: stepStatus,
  };

  if (!decision.fired) {
    console.log(`[SILENT] no actionable convergence ${date}`);
    if (options.emitJson) {
      console.log(JSON.stringify(result, null, 2));
    }
    return 0;
  }

  const alertText = buildAlertText({
    date,
    minSources: options.minSources,
    regimeLabel,
    regimeScore,
    convergences: convergenceHits,
    equityHits,
    cryptoHits,
    fearGreed,
    narrativeRows,
  });

  console.log(alertText);

  const topicFromEnv = process.env.NTFY_TOPIC;
  const topic = topicFromEnv === undefined ? DEFAULT_NTFY_TOPIC : topicFromEnv.trim();
  if (!options.noNotify && topic.length > 0) {
    const title = `Daily Opportunity Scan ${date}`;
    await postNotification(topic, title, alertText);
  }

  if (options.emitJson) {
    console.log(JSON.stringify(result, null, 2));
  }

  return 0;
}

main()
  .then((code) => {
    process.exit(code);
  })
  .catch((error) => {
    const msg = error instanceof Error ? error.message : String(error);
    console.error(`[FATAL] ${msg}`);
    process.exit(1);
  });
